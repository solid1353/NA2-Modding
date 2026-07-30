[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$SourceId,
    [Parameter(Mandatory)]
    [string]$Entry,
    [string]$OverlayPlan,
    [Parameter(Mandatory)]
    [string]$IsoPath,
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
if ([IO.Path]::IsPathRooted($IsoPath)) {
    throw 'Worker ISO paths must be repository-relative.'
}
$resolvedIso = [IO.Path]::GetFullPath((Join-Path $repository $IsoPath))
$relativeIso = [IO.Path]::GetRelativePath($repository, $resolvedIso)
if ($relativeIso -notmatch (
    '^work[\\/][^\\/]+[\\/]inputs[\\/]isos[\\/][^\\/]+\.iso$'
)) {
    throw (
        'Worker ISO must be an independent copy under ' +
        'work/<task>/inputs/isos/.'
    )
}
if (-not (Test-Path -LiteralPath $resolvedIso -PathType Leaf)) {
    throw "Worker ISO does not exist: $resolvedIso"
}
$taskName = ($relativeIso -split '[\\/]')[1]
$resolvedOutput = Join-Path $repository "work\$taskName\injection"

$buildArguments = @(
    '-B',
    $buildScript,
    '--source-id',
    $SourceId,
    '--entry',
    $Entry,
    '--iso',
    $resolvedIso,
    '--output',
    $resolvedOutput
)
if ($OverlayPlan) {
    $buildArguments += @('--overlay-plan', $OverlayPlan)
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
