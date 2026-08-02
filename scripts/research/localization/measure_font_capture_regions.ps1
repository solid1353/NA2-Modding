[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ReferenceDirectory,

    [Parameter(Mandatory)]
    [string]$CurrentDirectory,

    [Parameter(Mandatory)]
    [string]$Regions,

    [Parameter(Mandatory)]
    [string]$OutputDirectory,

    [string]$ReferenceLabel = 'Reference',

    [string]$CurrentLabel = 'Current'
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$pythonScript = Join-Path $PSScriptRoot 'measure_font_capture_regions.py'
$arguments = @(
    '--reference', [IO.Path]::GetFullPath($ReferenceDirectory)
    '--current', [IO.Path]::GetFullPath($CurrentDirectory)
    '--regions', [IO.Path]::GetFullPath($Regions)
    '--output', [IO.Path]::GetFullPath($OutputDirectory)
    '--reference-label', $ReferenceLabel
    '--current-label', $CurrentLabel
)

& (Join-Path $repositoryRoot 'scripts\lib\run_python.ps1') `
    -PackageSet imaging `
    -Script $pythonScript `
    -ArgumentList $arguments `
    -NoBytecode
exit $LASTEXITCODE
