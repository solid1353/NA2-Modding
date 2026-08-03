[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ReferenceDirectory,

    [Parameter(Mandatory)]
    [string]$CurrentDirectory,

    [Parameter(Mandatory)]
    [string]$OutputDirectory,

    [string]$ReferenceLabel = 'Reference',

    [string]$CurrentLabel = 'Current',

    [string]$Slots,

    [ValidateRange(1, 8)]
    [int]$GridColumns = 2,

    [ValidateRange(1, 32)]
    [int]$GridItemsPerPage = 4
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$pythonScript = Join-Path $PSScriptRoot 'compare_font_capture_sets.py'
$arguments = @(
    '--reference', [IO.Path]::GetFullPath($ReferenceDirectory)
    '--current', [IO.Path]::GetFullPath($CurrentDirectory)
    '--output', [IO.Path]::GetFullPath($OutputDirectory)
    '--reference-label', $ReferenceLabel
    '--current-label', $CurrentLabel
    '--grid-columns', [string]$GridColumns
    '--grid-items-per-page', [string]$GridItemsPerPage
)
if (-not [string]::IsNullOrWhiteSpace($Slots)) {
    $arguments += @('--slots', $Slots)
}

& (Join-Path $repositoryRoot 'scripts\lib\run_python.ps1') `
    -PackageSet imaging `
    -Script $pythonScript `
    -ArgumentList $arguments `
    -NoBytecode
exit $LASTEXITCODE
