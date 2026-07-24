param(
    [Parameter(Mandatory = $true)]
    [string]$IsoPath,

    [string]$OutDir = "",

    [switch]$NoLog,

    [switch]$SkipReadOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

$sectorSize = 2048

function Read-UInt32LE {
    param(
        [byte[]]$Data,
        [int]$Offset
    )

    return [BitConverter]::ToUInt32($Data, $Offset)
}

function Read-IsoRecordingTime {
    param(
        [byte[]]$Data,
        [int]$Offset,
        [string]$Context
    )

    $year = 1900 + [int]$Data[$Offset]
    $month = [int]$Data[$Offset + 1]
    $day = [int]$Data[$Offset + 2]
    $hour = [int]$Data[$Offset + 3]
    $minute = [int]$Data[$Offset + 4]
    $second = [int]$Data[$Offset + 5]
    $offsetByte = [int]$Data[$Offset + 6]
    $offsetQuarters = if ($offsetByte -ge 128) { $offsetByte - 256 } else { $offsetByte }

    if ($year -eq 1900 -and $month -eq 0 -and $day -eq 0 -and
        $hour -eq 0 -and $minute -eq 0 -and $second -eq 0 -and
        $offsetQuarters -eq 0) {
        return $null
    }

    if ($offsetQuarters -lt -48 -or $offsetQuarters -gt 52) {
        throw "Invalid ISO timezone offset in ${Context}: $offsetQuarters quarter-hours"
    }

    try {
        $timezoneOffset = [TimeSpan]::FromMinutes($offsetQuarters * 15)
        return [DateTimeOffset]::new($year, $month, $day, $hour, $minute, $second, $timezoneOffset)
    }
    catch {
        throw "Invalid ISO recording time in ${Context}: $year-$month-$day $hour`:$minute`:$second (UTC quarter offset $offsetQuarters)"
    }
}

function Set-IsoRecordedTime {
    param(
        [string]$Path,
        [object]$RecordedAt,
        [DateTimeOffset]$FallbackRecordedAt
    )

    $effectiveTime = if ($null -ne $RecordedAt) { [DateTimeOffset]$RecordedAt } else { $FallbackRecordedAt }

    if ((Get-Item -LiteralPath $Path).PSIsContainer) {
        [IO.Directory]::SetCreationTimeUtc($Path, $effectiveTime.UtcDateTime)
        [IO.Directory]::SetLastWriteTimeUtc($Path, $effectiveTime.UtcDateTime)
    }
    else {
        [IO.File]::SetCreationTimeUtc($Path, $effectiveTime.UtcDateTime)
        [IO.File]::SetLastWriteTimeUtc($Path, $effectiveTime.UtcDateTime)
    }
}

function Read-DirectoryRecord {
    param(
        [byte[]]$Data,
        [int]$Offset
    )

    $length = [int]$Data[$Offset]

    if ($length -eq 0) {
        return $null
    }

    $extent = Read-UInt32LE -Data $Data -Offset ($Offset + 2)
    $size = Read-UInt32LE -Data $Data -Offset ($Offset + 10)
    $flags = [int]$Data[$Offset + 25]
    $recordedAt = Read-IsoRecordingTime -Data $Data -Offset ($Offset + 18) -Context "directory record at byte $Offset"
    $nameLength = [int]$Data[$Offset + 32]
    $nameBytes = [byte[]]::new($nameLength)
    [Array]::Copy($Data, $Offset + 33, $nameBytes, 0, $nameLength)

    if ($nameLength -eq 1 -and $nameBytes[0] -eq 0) {
        $name = "."
    }
    elseif ($nameLength -eq 1 -and $nameBytes[0] -eq 1) {
        $name = ".."
    }
    else {
        $name = [Text.Encoding]::ASCII.GetString($nameBytes)
        $name = ($name -replace ';[0-9]+$', '')
    }

    return [pscustomobject]@{
        Length = $length
        Extent = [uint32]$extent
        Size = [uint32]$size
        Flags = $flags
        Name = $name
        IsDirectory = (($flags -band 0x02) -ne 0)
        RecordedAt = $recordedAt
    }
}

function Copy-ExtentToFile {
    param(
        [IO.FileStream]$IsoStream,
        [uint32]$Extent,
        [uint32]$Size,
        [string]$OutPath,
        [object]$RecordedAt,
        [DateTimeOffset]$FallbackRecordedAt
    )

    if (Test-Path -LiteralPath $OutPath) {
        throw "Output file already exists: $OutPath"
    }

    $IsoStream.Position = [int64]$Extent * $sectorSize
    $out = [IO.File]::Create($OutPath)

    try {
        $remaining = [int64]$Size
        $buffer = [byte[]]::new(1024 * 1024)

        while ($remaining -gt 0) {
            $want = [int][Math]::Min($buffer.Length, $remaining)
            $read = $IsoStream.Read($buffer, 0, $want)

            if ($read -le 0) {
                throw "Unexpected EOF while extracting $OutPath"
            }

            $out.Write($buffer, 0, $read)
            $remaining -= $read
        }
    }
    finally {
        $out.Dispose()
    }

    Set-IsoRecordedTime -Path $OutPath -RecordedAt $RecordedAt -FallbackRecordedAt $FallbackRecordedAt
}

function Extract-Directory {
    param(
        [IO.FileStream]$IsoStream,
        [object]$DirRecord,
        [string]$OutPath,
        [System.Collections.Generic.List[object]]$LogRows,
        [string]$RelativePrefix,
        [DateTimeOffset]$FallbackRecordedAt
    )

    if (-not (Test-Path -LiteralPath $OutPath)) {
        New-Item -ItemType Directory -Path $OutPath | Out-Null
    }

    $dirData = [byte[]]::new([int]$DirRecord.Size)
    $IsoStream.Position = [int64]$DirRecord.Extent * $sectorSize
    $readTotal = 0

    while ($readTotal -lt $dirData.Length) {
        $read = $IsoStream.Read($dirData, $readTotal, $dirData.Length - $readTotal)
        if ($read -le 0) {
            throw "Unexpected EOF while reading directory $RelativePrefix"
        }
        $readTotal += $read
    }

    $offset = 0
    while ($offset -lt $dirData.Length) {
        $length = [int]$dirData[$offset]

        if ($length -eq 0) {
            $offset++
            continue
        }

        $record = Read-DirectoryRecord -Data $dirData -Offset $offset
        $offset += $length

        if ($null -eq $record -or $record.Name -eq "." -or $record.Name -eq "..") {
            continue
        }

        $childRelative = if ([string]::IsNullOrWhiteSpace($RelativePrefix)) {
            $record.Name
        }
        else {
            Join-Path $RelativePrefix $record.Name
        }

        $childOut = Join-Path $OutPath $record.Name

        $effectiveRecordedAt = if ($null -ne $record.RecordedAt) { [DateTimeOffset]$record.RecordedAt } else { $FallbackRecordedAt }
        $LogRows.Add([pscustomobject]@{
            Path = $childRelative
            Type = if ($record.IsDirectory) { "dir" } else { "file" }
            Extent = $record.Extent
            OffsetHex = ("0x{0:X}" -f ([int64]$record.Extent * $sectorSize))
            Size = $record.Size
            RecordedAt = $effectiveRecordedAt.ToString("o")
            TimestampSource = if ($null -ne $record.RecordedAt) { "iso9660_recording_time" } else { "container_fallback" }
        })

        if ($record.IsDirectory) {
            Extract-Directory -IsoStream $IsoStream -DirRecord $record -OutPath $childOut -LogRows $LogRows -RelativePrefix $childRelative -FallbackRecordedAt $FallbackRecordedAt
        }
        else {
            Copy-ExtentToFile -IsoStream $IsoStream -Extent $record.Extent -Size $record.Size -OutPath $childOut -RecordedAt $record.RecordedAt -FallbackRecordedAt $FallbackRecordedAt
        }
    }


    Set-IsoRecordedTime -Path $OutPath -RecordedAt $DirRecord.RecordedAt -FallbackRecordedAt $FallbackRecordedAt
}

if (-not (Test-Path -LiteralPath $IsoPath)) {
    throw "ISO not found: $IsoPath"
}

$IsoPath = (Resolve-Path -LiteralPath $IsoPath).Path
$isoFile = Get-Item -LiteralPath $IsoPath
$fallbackRecordedAt = [DateTimeOffset]$isoFile.LastWriteTime

if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $OutDir = Join-Path $isoFile.DirectoryName ($isoFile.Name + ".files")
}

if (Test-Path -LiteralPath $OutDir) {
    $existing = @(Get-ChildItem -Force -LiteralPath $OutDir)
    if ($existing.Count -ne 0) {
        throw "Output directory already exists and is not empty; refusing to merge or overwrite: $OutDir"
    }
}

$iso = [IO.File]::OpenRead($IsoPath)

try {
    $pvd = [byte[]]::new($sectorSize)
    $iso.Position = 16 * $sectorSize
    [void]$iso.Read($pvd, 0, $pvd.Length)

    $magic = [Text.Encoding]::ASCII.GetString($pvd, 1, 5)
    if ($pvd[0] -ne 1 -or $magic -ne "CD001") {
        throw "Primary Volume Descriptor not found at sector 16."
    }

    $rootRecord = Read-DirectoryRecord -Data $pvd -Offset 156
    $logRows = [System.Collections.Generic.List[object]]::new()

    if (-not (Test-Path -LiteralPath $OutDir)) {
        New-Item -ItemType Directory -Path $OutDir | Out-Null
    }

    Extract-Directory -IsoStream $iso -DirRecord $rootRecord -OutPath $OutDir -LogRows $logRows -RelativePrefix "" -FallbackRecordedAt $fallbackRecordedAt
}
finally {
    $iso.Dispose()
}

$logPath = ""
if (-not $NoLog) {
    $logDir = Join-Path $projectPaths.workstream_logs "Scripting\extraction"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
    $logPath = Join-Path $logDir ("extract_iso9660_" + $stamp + "_pid" + $PID + ".tsv")
    $logRows | Export-Csv -LiteralPath $logPath -Delimiter "`t" -NoTypeInformation -Encoding UTF8
}

$readonlyScript = Join-Path $projectPaths.scripts 'project\set_source_readonly.ps1'
if (-not $SkipReadOnly -and
    $OutDir.StartsWith($projectPaths.source, [StringComparison]::OrdinalIgnoreCase) -and
    (Test-Path -LiteralPath $readonlyScript)) {
    & $readonlyScript -SourceDir $OutDir | Out-Null
}

Write-Host "Extracted ISO:"
Write-Host $IsoPath
Write-Host "Output:"
Write-Host $OutDir
Write-Host "Entries:"
Write-Host $logRows.Count
if ($logPath) {
    Write-Host "Log:"
    Write-Host $logPath
}
