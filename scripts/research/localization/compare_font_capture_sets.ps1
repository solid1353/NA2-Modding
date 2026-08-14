[CmdletBinding(DefaultParameterSetName = 'Comparison')]
param(
    [Parameter(Mandatory, ParameterSetName = 'Comparison')]
    [string]$ReferenceDirectory,

    [Parameter(Mandatory, ParameterSetName = 'Comparison')]
    [string]$CurrentDirectory,

    [Parameter(Mandatory, ParameterSetName = 'ScreenshotGrid')]
    [string]$ScreenshotDirectory,

    [Parameter(Mandatory)]
    [string]$OutputDirectory,

    [Parameter(ParameterSetName = 'Comparison')]
    [string]$ReferenceLabel = 'Reference',

    [Parameter(ParameterSetName = 'Comparison')]
    [string]$CurrentLabel = 'Current',

    [Parameter(ParameterSetName = 'Comparison')]
    [string]$Slots,

    [Parameter(ParameterSetName = 'Comparison')]
    [ValidateSet('All', 'Pair', 'Blend', 'Diff')]
    [string]$Kind = 'All',

    [ValidateRange(1, 8)]
    [int]$GridColumns = 2,

    [ValidateRange(1, 32)]
    [int]$GridItemsPerPage = 4
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$pythonScript = Join-Path $PSScriptRoot 'compare_font_capture_sets.py'
$arguments = @(
    '--output', [IO.Path]::GetFullPath($OutputDirectory)
    '--grid-columns', [string]$GridColumns
    '--grid-items-per-page', [string]$GridItemsPerPage
)
if ($PSCmdlet.ParameterSetName -ceq 'ScreenshotGrid') {
    $arguments += @('--screenshots', [IO.Path]::GetFullPath($ScreenshotDirectory))
}
else {
    $arguments += @(
        '--reference', [IO.Path]::GetFullPath($ReferenceDirectory)
        '--current', [IO.Path]::GetFullPath($CurrentDirectory)
        '--reference-label', $ReferenceLabel
        '--current-label', $CurrentLabel
        '--kind', $Kind.ToLowerInvariant()
    )
    if (-not [string]::IsNullOrWhiteSpace($Slots)) {
        $arguments += @('--slots', $Slots)
    }
}

& (Join-Path $repositoryRoot 'scripts\lib\run_python.ps1') `
    -PackageSet imaging `
    -Script $pythonScript `
    -ArgumentList $arguments `
    -NoBytecode
exit $LASTEXITCODE
