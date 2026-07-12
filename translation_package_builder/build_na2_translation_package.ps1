param(
    [string]$Na2Iso = 'C:\Games\Modding\UN Modding\NA2 Modding\source\NA2.iso',
    [string]$OutputDirectory = 'C:\Users\solid\Downloads',
    [string]$BtlApplyTsv,
    [string]$EtcApplyTsv,
    [switch]$NoStrictHash
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$builder = Join-Path $scriptDir 'scripts\build_translation_package.py'

if ([string]::IsNullOrWhiteSpace($BtlApplyTsv)) {
    $BtlApplyTsv = Join-Path $scriptDir 'translations\apply\btl_apply.tsv'
}
if ([string]::IsNullOrWhiteSpace($EtcApplyTsv)) {
    $EtcApplyTsv = Join-Path $scriptDir 'translations\apply\etc_apply.tsv'
}

$argsList = @(
    $builder,
    '--na2-iso', $Na2Iso,
    '--output-directory', $OutputDirectory,
    '--btl-tsv', $BtlApplyTsv,
    '--etc-tsv', $EtcApplyTsv
)
if ($NoStrictHash) {
    $argsList += '--no-strict-hash'
}

& python @argsList
if ($LASTEXITCODE -ne 0) {
    throw "Translation package builder failed with exit code $LASTEXITCODE."
}
