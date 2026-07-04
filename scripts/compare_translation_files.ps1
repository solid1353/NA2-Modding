param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$OutDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $OutDir = Join-Path $ProjectRoot "work\translation_compare\reports"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$encoding = [Text.Encoding]::GetEncoding(932)
$pairs = @(
    @{ Name = "BTL.BIN"; Source = "source\NA2.iso.files\PRG\BTL.BIN"; Build = "work\translation_compare\build_current\BTL.BIN" },
    @{ Name = "ETC.BIN"; Source = "source\NA2.iso.files\PRG\ETC.BIN"; Build = "work\translation_compare\build_current\ETC.BIN" },
    @{ Name = "SLPS_258.37"; Source = "source\NA2.iso.files\SLPS_258.37"; Build = "work\translation_compare\build_current\SLPS_258.37" }
)

function Get-Sha256([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Format-HexBytes([byte[]]$Bytes, [int]$Start, [int]$Length) {
    $end = [Math]::Min($Bytes.Length, $Start + $Length)
    if ($Start -ge $end) { return "" }
    (($Start..($end - 1)) | ForEach-Object { "{0:X2}" -f $Bytes[$_] }) -join " "
}

function Decode-Window([byte[]]$Bytes, [int]$Start, [int]$Length, [Text.Encoding]$Encoding) {
    $end = [Math]::Min($Bytes.Length, $Start + $Length)
    if ($Start -ge $end) { return "" }
    $slice = [byte[]]::new($end - $Start)
    [Array]::Copy($Bytes, $Start, $slice, 0, $slice.Length)
    $text = $Encoding.GetString($slice)
    $text = $text -replace "`0", "\\0"
    $text = $text -replace "\p{C}", "."
    $text.Trim()
}

$summary = [System.Collections.Generic.List[object]]::new()
$regions = [System.Collections.Generic.List[object]]::new()

foreach ($pair in $pairs) {
    $sourcePath = Join-Path $ProjectRoot $pair.Source
    $buildPath = Join-Path $ProjectRoot $pair.Build
    if (-not (Test-Path -LiteralPath $sourcePath)) { throw "Missing source: $sourcePath" }
    if (-not (Test-Path -LiteralPath $buildPath)) { throw "Missing build: $buildPath" }

    $sourceBytes = [IO.File]::ReadAllBytes($sourcePath)
    $buildBytes = [IO.File]::ReadAllBytes($buildPath)
    $minLen = [Math]::Min($sourceBytes.Length, $buildBytes.Length)
    $diffCount = 0
    $hunkCount = 0
    $firstDiff = $null
    $lastDiff = $null
    $inHunk = $false
    $hunkStart = 0
    $lastChanged = 0
    $gapLimit = 8

    for ($i = 0; $i -lt $minLen; $i++) {
        if ($sourceBytes[$i] -ne $buildBytes[$i]) {
            $diffCount++
            if ($null -eq $firstDiff) { $firstDiff = $i }
            $lastDiff = $i
            if (-not $inHunk) {
                $inHunk = $true
                $hunkStart = $i
                $hunkCount++
            }
            elseif (($i - $lastChanged) -gt $gapLimit) {
                $start = [Math]::Max(0, $hunkStart - 16)
                $length = [Math]::Min($sourceBytes.Length, $lastChanged + 17) - $start
                $regions.Add([pscustomobject]@{
                    File = $pair.Name
                    OffsetHex = "0x{0:X}" -f $hunkStart
                    OffsetDec = $hunkStart
                    LastChangedHex = "0x{0:X}" -f $lastChanged
                    ChangedSpan = ($lastChanged - $hunkStart + 1)
                    SourceText = Decode-Window $sourceBytes $start $length $encoding
                    BuildText = Decode-Window $buildBytes $start $length $encoding
                    SourceHex = Format-HexBytes $sourceBytes $hunkStart ([Math]::Min(32, $lastChanged - $hunkStart + 1))
                    BuildHex = Format-HexBytes $buildBytes $hunkStart ([Math]::Min(32, $lastChanged - $hunkStart + 1))
                })
                $hunkStart = $i
                $hunkCount++
            }
            $lastChanged = $i
        }
    }

    if ($inHunk) {
        $start = [Math]::Max(0, $hunkStart - 16)
        $length = [Math]::Min($sourceBytes.Length, $lastChanged + 17) - $start
        $regions.Add([pscustomobject]@{
            File = $pair.Name
            OffsetHex = "0x{0:X}" -f $hunkStart
            OffsetDec = $hunkStart
            LastChangedHex = "0x{0:X}" -f $lastChanged
            ChangedSpan = ($lastChanged - $hunkStart + 1)
            SourceText = Decode-Window $sourceBytes $start $length $encoding
            BuildText = Decode-Window $buildBytes $start $length $encoding
            SourceHex = Format-HexBytes $sourceBytes $hunkStart ([Math]::Min(32, $lastChanged - $hunkStart + 1))
            BuildHex = Format-HexBytes $buildBytes $hunkStart ([Math]::Min(32, $lastChanged - $hunkStart + 1))
        })
    }

    $summary.Add([pscustomobject]@{
        File = $pair.Name
        SourceSize = $sourceBytes.Length
        BuildSize = $buildBytes.Length
        SameSize = ($sourceBytes.Length -eq $buildBytes.Length)
        DiffBytes = $diffCount + [Math]::Abs($sourceBytes.Length - $buildBytes.Length)
        DiffRegions = $hunkCount
        FirstDiffHex = if ($null -eq $firstDiff) { "" } else { "0x{0:X}" -f $firstDiff }
        LastDiffHex = if ($null -eq $lastDiff) { "" } else { "0x{0:X}" -f $lastDiff }
        SourceSha256 = Get-Sha256 $sourcePath
        BuildSha256 = Get-Sha256 $buildPath
    })
}

$summaryPath = Join-Path $OutDir "translation_compare_summary.tsv"
$regionsPath = Join-Path $OutDir "translation_compare_regions.tsv"
$summary | Export-Csv -LiteralPath $summaryPath -Delimiter "`t" -NoTypeInformation -Encoding UTF8
$regions | Export-Csv -LiteralPath $regionsPath -Delimiter "`t" -NoTypeInformation -Encoding UTF8

[pscustomobject]@{
    Summary = $summaryPath
    Regions = $regionsPath
    RegionCount = $regions.Count
}
