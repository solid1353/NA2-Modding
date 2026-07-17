param(
    [Parameter(Mandatory = $true)]
    [string]$CvmPath,

    [string]$OutDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

$sectorSize = 2048

function Read-UInt32BE {
    param([byte[]]$Data, [int]$Offset)
    return ([uint32]$Data[$Offset] -shl 24) -bor
        ([uint32]$Data[$Offset + 1] -shl 16) -bor
        ([uint32]$Data[$Offset + 2] -shl 8) -bor
        [uint32]$Data[$Offset + 3]
}

function Read-UInt64BE {
    param([byte[]]$Data, [int]$Offset)
    $value = [uint64]0
    for ($i = 0; $i -lt 8; $i++) {
        $value = ($value -shl 8) -bor [uint64]$Data[$Offset + $i]
    }
    return $value
}

function Copy-Range {
    param(
        [IO.FileStream]$InputStream,
        [string]$OutPath,
        [int64]$Offset,
        [int64]$Length
    )

    if (Test-Path -LiteralPath $OutPath) {
        throw "Output file already exists: $OutPath"
    }

    $InputStream.Position = $Offset
    $out = [IO.File]::Create($OutPath)

    try {
        $remaining = $Length
        $buffer = [byte[]]::new(1024 * 1024)

        while ($remaining -gt 0) {
            $want = [int][Math]::Min($buffer.Length, $remaining)
            $read = $InputStream.Read($buffer, 0, $want)
            if ($read -le 0) {
                throw "Unexpected EOF while writing $OutPath"
            }
            $out.Write($buffer, 0, $read)
            $remaining -= $read
        }
    }
    finally {
        $out.Dispose()
    }
}

function Read-ChunkHeader {
    param([IO.FileStream]$Stream)

    $buf = [byte[]]::new(12)
    if ($Stream.Read($buf, 0, $buf.Length) -ne $buf.Length) {
        throw "Could not read CVM chunk header."
    }

    return [pscustomobject]@{
        Id = [Text.Encoding]::ASCII.GetString($buf, 0, 4)
        Length = Read-UInt64BE -Data $buf -Offset 4
        Offset = $Stream.Position - 12
    }
}

if (-not (Test-Path -LiteralPath $CvmPath)) {
    throw "CVM not found: $CvmPath"
}

$CvmPath = (Resolve-Path -LiteralPath $CvmPath).Path
$cvmItem = Get-Item -LiteralPath $CvmPath

if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $OutDir = Join-Path $cvmItem.DirectoryName ($cvmItem.Name + ".files")
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

$fs = [IO.File]::OpenRead($CvmPath)

try {
    $cvmh = Read-ChunkHeader -Stream $fs
    if ($cvmh.Id -ne "CVMH") {
        throw "Expected CVMH chunk at start, found '$($cvmh.Id)'."
    }

    $cvmhData = [byte[]]::new([int]$cvmh.Length)
    if ($fs.Read($cvmhData, 0, $cvmhData.Length) -ne $cvmhData.Length) {
        throw "Could not read CVMH data."
    }

    $flags30 = Read-UInt32BE -Data $cvmhData -Offset 0x24
    $isEncrypted = (($flags30 -band 0x10) -ne 0)
    if ($isEncrypted) {
        throw "CVM has encrypted TOC flag set. This script does not decrypt encrypted CVM TOCs."
    }

    $isoStartSector = Read-UInt32BE -Data $cvmhData -Offset 0x84

    $zone = Read-ChunkHeader -Stream $fs
    if ($zone.Id -ne "ZONE") {
        throw "Expected ZONE chunk after CVMH, found '$($zone.Id)'."
    }

    $zoneInfo = [byte[]]::new(0x30)
    if ($fs.Read($zoneInfo, 0, $zoneInfo.Length) -ne $zoneInfo.Length) {
        throw "Could not read ZONE info."
    }

    $isoSector = Read-UInt32BE -Data $zoneInfo -Offset 0x20
    $isoLength = Read-UInt64BE -Data $zoneInfo -Offset 0x24

    if ($isoSector -ne $isoStartSector) {
        Write-Warning "CVMH ISO start sector ($isoStartSector) differs from ZONE ISO sector ($isoSector). Using ZONE value."
    }

    $isoOffset = [int64]$isoSector * $sectorSize
    $headerLength = $isoOffset
    $endOffset = $isoOffset + [int64]$isoLength

    if ($endOffset -gt $fs.Length) {
        throw "CVM ISO range exceeds file length."
    }

    $base = $cvmItem.Name
    $headerOut = Join-Path $OutDir ($base + ".hdr")
    $isoOut = Join-Path $OutDir ($base + ".iso")
    $manifestOut = Join-Path $OutDir "cvm_manifest.tsv"

    Copy-Range -InputStream $fs -OutPath $headerOut -Offset 0 -Length $headerLength
    Copy-Range -InputStream $fs -OutPath $isoOut -Offset $isoOffset -Length ([int64]$isoLength)

    $rows = @(
        [pscustomobject]@{
            Item = "SourceCVM"
            Path = $CvmPath
            Offset = ""
            Size = $fs.Length
        },
        [pscustomobject]@{
            Item = "Header"
            Path = $headerOut
            Offset = "0x0"
            Size = $headerLength
        },
        [pscustomobject]@{
            Item = "InnerISO"
            Path = $isoOut
            Offset = ("0x{0:X}" -f $isoOffset)
            Size = $isoLength
        }
    )
    $rows | Export-Csv -LiteralPath $manifestOut -Delimiter "`t" -NoTypeInformation -Encoding UTF8
}
finally {
    $fs.Dispose()
}

$isoExtractor = Join-Path $projectPaths.scripts 'media\extract_iso.ps1'
if (Test-Path -LiteralPath $isoExtractor) {
    & $isoExtractor -IsoPath $isoOut
}

$readonlyScript = Join-Path $projectPaths.scripts 'project\set_source_readonly.ps1'
if ($OutDir.StartsWith($projectPaths.source, [StringComparison]::OrdinalIgnoreCase) -and
    (Test-Path -LiteralPath $readonlyScript)) {
    & $readonlyScript -SourceDir $OutDir | Out-Null
}

Write-Host "Extracted CVM:"
Write-Host $CvmPath
Write-Host "Output:"
Write-Host $OutDir
Write-Host "Header:"
Write-Host $headerOut
Write-Host "Inner ISO:"
Write-Host $isoOut
