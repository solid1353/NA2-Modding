[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$SourceId,
    [Parameter(Mandatory)]
    [string]$Entry,
    [string]$OverlayPlan,
    [string]$Output,
    [string]$CurrentIso,
    [Parameter(Mandatory)]
    [ValidateRange(0, 255)]
    [int]$StateSlot,
    [Parameter(Mandatory)]
    [ValidateRange(1, 65535)]
    [int]$PinePort
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$buildScript = Join-Path $PSScriptRoot 'build.py'
$applyScript = Join-Path $PSScriptRoot 'apply.py'
$pineScript = Join-Path $repository 'scripts\pcsx2\pine.py'
$resolvedOutput = if ($Output) {
    [IO.Path]::GetFullPath((Join-Path $repository $Output))
}
else {
    Join-Path $repository "build\injection\$SourceId"
}

$buildArguments = @(
    '-B',
    $buildScript,
    '--source-id',
    $SourceId,
    '--entry',
    $Entry,
    '--output',
    $resolvedOutput
)
if ($OverlayPlan) {
    $buildArguments += @('--overlay-plan', $OverlayPlan)
}
if ($CurrentIso) {
    $buildArguments += @('--iso', $CurrentIso)
}

& python @buildArguments
if ($LASTEXITCODE -ne 0) {
    throw "Injection build failed with exit code $LASTEXITCODE."
}

& python -B $pineScript --port $PinePort load-state $StateSlot
if ($LASTEXITCODE -ne 0) {
    throw "Savestate reload failed with exit code $LASTEXITCODE."
}

& python -B $applyScript `
    --input $resolvedOutput `
    --port $PinePort `
    --resume
if ($LASTEXITCODE -ne 0) {
    throw "Injection apply failed with exit code $LASTEXITCODE."
}
