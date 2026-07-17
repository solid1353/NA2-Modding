param(
    [Parameter(Mandatory = $true)]
    [string]$AfsPath,

    [string]$OutDir = "",

    [switch]$NoLog,

    [switch]$SkipReadOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

function Test-AsciiContains {
    param(
        [byte[]]$Data,
        [string]$Text
    )

    if ($Data.Length -eq 0) {
        return $false
    }

    $textData = [Text.Encoding]::ASCII.GetString($Data, 0, $Data.Length)
    return $textData.Contains($Text)
}

function Get-GuessedExtension {
    param([byte[]]$Data)

    if ($Data.Length -ge 4) {
        if ($Data[0] -eq 0x41 -and $Data[1] -eq 0x46 -and $Data[2] -eq 0x53 -and $Data[3] -eq 0x00) { return ".afs" }
        if ($Data[0] -eq 0x52 -and $Data[1] -eq 0x49 -and $Data[2] -eq 0x46 -and $Data[3] -eq 0x46) { return ".wav" }
        if ($Data[0] -eq 0x54 -and $Data[1] -eq 0x49 -and $Data[2] -eq 0x4D -and $Data[3] -eq 0x32) { return ".tm2" }
        if ($Data[0] -eq 0x00 -and $Data[1] -eq 0x00 -and $Data[2] -eq 0x01 -and $Data[3] -eq 0xBA) { return ".pss" }
    }

    if ($Data.Length -ge 3) {
        if ($Data[0] -eq 0x41 -and $Data[1] -eq 0x48 -and $Data[2] -eq 0x58) { return ".ahx" }
    }

    if ($Data.Length -ge 2) {
        if ($Data[0] -eq 0x80 -and $Data[1] -eq 0x00) { return ".adx" }
    }

    if (Test-AsciiContains -Data $Data -Text "(c)CRI") { return ".adx" }
    if (Test-AsciiContains -Data $Data -Text "CRI") { return ".adx" }

    return ".bin"
}

function Read-AfsMetadata {
    param(
        [IO.BinaryReader]$Reader,
        [int]$Count,
        [int64]$ArchiveLength
    )

    $result = @()
    if ($Reader.BaseStream.Position + 8 -gt $ArchiveLength) {
        return $result
    }

    $metadataOffset = [int64]$Reader.ReadUInt32()
    $metadataSize = [int64]$Reader.ReadUInt32()
    $requiredSize = [int64]$Count * 48
    if ($metadataOffset -le 0 -or
        $metadataSize -lt $requiredSize -or
        $metadataOffset + $requiredSize -gt $ArchiveLength) {
        return $result
    }

    $Reader.BaseStream.Position = $metadataOffset
    for ($i = 0; $i -lt $Count; $i++) {
        $nameBytes = $Reader.ReadBytes(32)
        if ($nameBytes.Length -ne 32) {
            throw "Unexpected EOF in AFS metadata row $i"
        }
        $zero = [Array]::IndexOf($nameBytes, [byte]0)
        $nameLength = if ($zero -ge 0) { $zero } else { $nameBytes.Length }
        $originalName = [Text.Encoding]::ASCII.GetString($nameBytes, 0, $nameLength)
        $year = [int]$Reader.ReadUInt16()
        $month = [int]$Reader.ReadUInt16()
        $day = [int]$Reader.ReadUInt16()
        $hour = [int]$Reader.ReadUInt16()
        $minute = [int]$Reader.ReadUInt16()
        $second = [int]$Reader.ReadUInt16()
        [void]$Reader.ReadUInt32()

        $recordedAt = $null
        try {
            $recordedAt = [DateTime]::new($year, $month, $day, $hour, $minute, $second, [DateTimeKind]::Unspecified)
        }
        catch {
            $recordedAt = $null
        }
        $result += [pscustomobject]@{
            OriginalName = $originalName
            RecordedAt = $recordedAt
        }
    }

    return $result
}

function Set-AfsRecordedTime {
    param(
        [string]$Path,
        [DateTime]$RecordedAt
    )

    if ((Get-Item -LiteralPath $Path).PSIsContainer) {
        [IO.Directory]::SetCreationTime($Path, $RecordedAt)
        [IO.Directory]::SetLastWriteTime($Path, $RecordedAt)
    }
    else {
        [IO.File]::SetCreationTime($Path, $RecordedAt)
        [IO.File]::SetLastWriteTime($Path, $RecordedAt)
    }
}

if (-not (Test-Path -LiteralPath $AfsPath)) {
    throw "AFS not found: $AfsPath"
}

$AfsPath = (Resolve-Path -LiteralPath $AfsPath).Path
$afsItem = Get-Item -LiteralPath $AfsPath
$fallbackTime = $afsItem.LastWriteTime

if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $parent = Split-Path -Parent $AfsPath
    $base = [IO.Path]::GetFileName($AfsPath)
    $OutDir = Join-Path $parent ($base + ".files")
}

if (Test-Path -LiteralPath $OutDir) {
    $existing = @(Get-ChildItem -Force -LiteralPath $OutDir)
    if ($existing.Count -ne 0) {
        throw "Output directory already exists and is not empty; refusing to merge or overwrite: $OutDir"
    }
}
else {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

$fs = [IO.File]::OpenRead($AfsPath)

try {
    $br = [IO.BinaryReader]::new($fs)

    $magic = $br.ReadBytes(4)
    if ($magic.Length -ne 4 -or $magic[0] -ne 0x41 -or $magic[1] -ne 0x46 -or $magic[2] -ne 0x53 -or $magic[3] -ne 0x00) {
        throw "Not an AFS archive: $AfsPath"
    }

    $count = $br.ReadUInt32()
    $entries = New-Object System.Collections.Generic.List[object]

    for ($i = 0; $i -lt $count; $i++) {
        $offset = $br.ReadUInt32()
        $size = $br.ReadUInt32()

        $entries.Add([pscustomobject]@{
            Index = $i
            Offset = $offset
            Size = $size
        })
    }

    $metadata = @(Read-AfsMetadata -Reader $br -Count $count -ArchiveLength $fs.Length)

    $logRows = New-Object System.Collections.Generic.List[object]

    foreach ($entry in $entries) {
        $end = [int64]$entry.Offset + [int64]$entry.Size
        if ($end -gt $fs.Length) {
            throw ("Invalid AFS entry {0:D3}: offset=0x{1:X}, size=0x{2:X}" -f $entry.Index, $entry.Offset, $entry.Size)
        }

        $sampleLen = [Math]::Min([int64]$entry.Size, [int64]512)
        $sample = [byte[]]::new([int]$sampleLen)
        $fs.Position = [int64]$entry.Offset
        [void]$fs.Read($sample, 0, $sample.Length)

        $ext = Get-GuessedExtension -Data $sample
        $name = "{0:D3}{1}" -f $entry.Index, $ext
        $outPath = Join-Path $OutDir $name

        $fs.Position = [int64]$entry.Offset
        $out = [IO.File]::Create($outPath)

        try {
            $left = [int64]$entry.Size
            $buffer = [byte[]]::new(1024 * 1024)

            while ($left -gt 0) {
                $want = [int][Math]::Min($buffer.Length, $left)
                $read = $fs.Read($buffer, 0, $want)

                if ($read -le 0) {
                    throw "Unexpected EOF while writing $outPath"
                }

                $out.Write($buffer, 0, $read)
                $left -= $read
            }
        }
        finally {
            $out.Dispose()
        }

        $metadataRow = if ($metadata.Count -eq $count) { $metadata[$entry.Index] } else { $null }
        $recordedAt = if ($null -ne $metadataRow -and $null -ne $metadataRow.RecordedAt) {
            [DateTime]$metadataRow.RecordedAt
        }
        else {
            $fallbackTime
        }
        $timestampSource = if ($null -ne $metadataRow -and $null -ne $metadataRow.RecordedAt) { "afs_metadata" } else { "container_fallback" }
        Set-AfsRecordedTime -Path $outPath -RecordedAt $recordedAt

        $logRows.Add([pscustomobject]@{
            Index = $entry.Index
            OffsetHex = ("0x{0:X}" -f $entry.Offset)
            SizeHex = ("0x{0:X}" -f $entry.Size)
            Size = $entry.Size
            Extension = $ext
            OriginalName = if ($null -ne $metadataRow) { $metadataRow.OriginalName } else { "" }
            RecordedAt = $recordedAt.ToString("yyyy-MM-ddTHH:mm:ss")
            TimestampSource = $timestampSource
            Output = $outPath
        })
    }
}
finally {
    $fs.Dispose()
}

$logPath = ""
if (-not $NoLog) {
    $logDir = Join-Path $projectPaths.logs "extraction"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
    $logPath = Join-Path $logDir ("extract_afs_" + $stamp + "_pid" + $PID + ".tsv")
    $persistedRows = foreach ($row in $logRows) {
        [pscustomobject]@{
            Container = ConvertTo-Na2ProjectPath -Path $AfsPath -ProjectPaths $projectPaths
            ExtractedDir = ConvertTo-Na2ProjectPath -Path $OutDir -ProjectPaths $projectPaths
            Index = $row.Index
            OffsetHex = $row.OffsetHex
            SizeHex = $row.SizeHex
            Size = $row.Size
            Extension = $row.Extension
            OriginalName = $row.OriginalName
            RecordedAt = $row.RecordedAt
            TimestampSource = $row.TimestampSource
            Output = ConvertTo-Na2ProjectPath -Path $row.Output -ProjectPaths $projectPaths
        }
    }
    $persistedRows | Export-Csv -LiteralPath $logPath -Delimiter "`t" -NoTypeInformation -Encoding UTF8
}

Write-Host "AFS entries: $count"
Write-Host "Extracted to:"
Write-Host $OutDir
if ($logPath) {
    Write-Host "Log:"
    Write-Host $logPath
}
Write-Host ""

Get-ChildItem -LiteralPath $OutDir -File |
    Group-Object Extension |
    Sort-Object Name |
    Select-Object Name, Count |
    Format-Table -AutoSize

Set-AfsRecordedTime -Path $OutDir -RecordedAt $fallbackTime

$readonlyScript = Join-Path $projectPaths.scripts 'project\set_source_readonly.ps1'
if (-not $SkipReadOnly -and
    $OutDir.StartsWith($projectPaths.source, [StringComparison]::OrdinalIgnoreCase) -and
    (Test-Path -LiteralPath $readonlyScript)) {
    & $readonlyScript -SourceDir $OutDir | Out-Null
}
