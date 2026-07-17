param(
    [string]$ProjectRoot = "",
    [string]$OutPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot 'project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = $projectPaths.repository
}

if ([string]::IsNullOrWhiteSpace($OutPath)) {
    $OutPath = Join-Path $projectPaths.work "translation_compare\reports\changed_string_slots.tsv"
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutPath) | Out-Null
$encoding = [Text.Encoding]::GetEncoding(932)

$pairs = @(
    @{ Name = "BTL.BIN"; Source = Join-Path $projectPaths.source "NA2.iso.files\PRG\BTL.BIN"; Build = Join-Path $projectPaths.work "translation_compare\build_current\BTL.BIN" },
    @{ Name = "ETC.BIN"; Source = Join-Path $projectPaths.source "NA2.iso.files\PRG\ETC.BIN"; Build = Join-Path $projectPaths.work "translation_compare\build_current\ETC.BIN" },
    @{ Name = "SLPS_258.37"; Source = Join-Path $projectPaths.source "NA2.iso.files\SLPS_258.37"; Build = Join-Path $projectPaths.work "translation_compare\build_current\SLPS_258.37" }
)

function Find-StringStart([byte[]]$Bytes, [int]$Offset) {
    $i = $Offset
    while ($i -gt 0 -and $Bytes[$i - 1] -ne 0) { $i-- }
    $i
}

function Find-StringEnd([byte[]]$Bytes, [int]$Offset) {
    $i = $Offset
    while ($i -lt $Bytes.Length -and $Bytes[$i] -ne 0) { $i++ }
    $i
}

function Decode-Bytes([byte[]]$Bytes, [int]$Start, [int]$End, [Text.Encoding]$Encoding) {
    if ($End -le $Start) { return "" }
    $slice = [byte[]]::new($End - $Start)
    [Array]::Copy($Bytes, $Start, $slice, 0, $slice.Length)
    $text = $Encoding.GetString($slice)
    $text = $text -replace "\p{C}", "."
    $text.Trim()
}

$rows = [System.Collections.Generic.List[object]]::new()
foreach ($pair in $pairs) {
    $sourcePath = $pair.Source
    $buildPath = $pair.Build
    $source = [IO.File]::ReadAllBytes($sourcePath)
    $build = [IO.File]::ReadAllBytes($buildPath)
    $seen = @{}
    $limit = [Math]::Min($source.Length, $build.Length)

    for ($i = 0; $i -lt $limit; $i++) {
        if ($source[$i] -eq $build[$i]) { continue }
        $start = Find-StringStart $build $i
        $end = Find-StringEnd $build $i
        if (($end - $start) -le 1 -or ($end - $start) -gt 160) { continue }
        $key = "$($pair.Name):$start"
        if ($seen.ContainsKey($key)) { continue }
        $seen[$key] = $true

        $sourceStart = Find-StringStart $source $i
        $sourceEnd = Find-StringEnd $source $i
        $sourceText = Decode-Bytes $source $sourceStart $sourceEnd $encoding
        $buildText = Decode-Bytes $build $start $end $encoding
        if ($buildText -notmatch '[A-Za-z]') { continue }

        $rows.Add([pscustomobject]@{
            File = $pair.Name
            OffsetHex = "0x{0:X}" -f $start
            OffsetDec = $start
            CapacityBytes = ($end - $start)
            SourceOffsetHex = "0x{0:X}" -f $sourceStart
            SourceBytes = ($sourceEnd - $sourceStart)
            BuildBytes = ($end - $start)
            SourceText = $sourceText
            BuildText = $buildText
        })
    }
}

$rows | Sort-Object File,OffsetDec | Export-Csv -LiteralPath $OutPath -Delimiter "`t" -NoTypeInformation -Encoding UTF8
[pscustomobject]@{ OutPath = $OutPath; Rows = $rows.Count }
