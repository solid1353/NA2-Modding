param(
    [Parameter(Mandatory = $true)]
    [string]$IsoPath,

    [string]$OutDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sectorSize = 2048

function Read-UInt32LE {
    param(
        [byte[]]$Data,
        [int]$Offset
    )

    return [BitConverter]::ToUInt32($Data, $Offset)
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
    }
}

function Copy-ExtentToFile {
    param(
        [IO.FileStream]$IsoStream,
        [uint32]$Extent,
        [uint32]$Size,
        [string]$OutPath
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
}

function Extract-Directory {
    param(
        [IO.FileStream]$IsoStream,
        [object]$DirRecord,
        [string]$OutPath,
        [System.Collections.Generic.List[object]]$LogRows,
        [string]$RelativePrefix
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

        $LogRows.Add([pscustomobject]@{
            Path = $childRelative
            Type = if ($record.IsDirectory) { "dir" } else { "file" }
            Extent = $record.Extent
            OffsetHex = ("0x{0:X}" -f ([int64]$record.Extent * $sectorSize))
            Size = $record.Size
        })

        if ($record.IsDirectory) {
            Extract-Directory -IsoStream $IsoStream -DirRecord $record -OutPath $childOut -LogRows $LogRows -RelativePrefix $childRelative
        }
        else {
            Copy-ExtentToFile -IsoStream $IsoStream -Extent $record.Extent -Size $record.Size -OutPath $childOut
        }
    }
}

if (-not (Test-Path -LiteralPath $IsoPath)) {
    throw "ISO not found: $IsoPath"
}

$IsoPath = (Resolve-Path -LiteralPath $IsoPath).Path
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $isoFile = Get-Item -LiteralPath $IsoPath
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

    Extract-Directory -IsoStream $iso -DirRecord $rootRecord -OutPath $OutDir -LogRows $logRows -RelativePrefix ""
}
finally {
    $iso.Dispose()
}

$logDir = Join-Path $root "logs\extraction"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logDir ("extract_iso9660_" + $stamp + ".tsv")
$logRows | Export-Csv -LiteralPath $logPath -Delimiter "`t" -NoTypeInformation -Encoding UTF8

$readonlyScript = Join-Path $PSScriptRoot "set_original_readonly.ps1"
if ($OutDir.StartsWith((Join-Path $root "source"), [StringComparison]::OrdinalIgnoreCase) -and
    (Test-Path -LiteralPath $readonlyScript)) {
    & $readonlyScript | Out-Null
}

Write-Host "Extracted ISO:"
Write-Host $IsoPath
Write-Host "Output:"
Write-Host $OutDir
Write-Host "Entries:"
Write-Host $logRows.Count
Write-Host "Log:"
Write-Host $logPath

