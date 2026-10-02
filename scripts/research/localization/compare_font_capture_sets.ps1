[CmdletBinding()]
param(
    [Parameter(Mandatory, ParameterSetName = 'ScreenshotGrid')]
    [string]$ScreenshotDirectory,

    [Parameter(Mandatory, ParameterSetName = 'PairedGridComparison')]
    [string]$PairedGridDirectory,

    [Parameter(Mandatory)]
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
. (Join-Path $repositoryRoot 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$pythonScript = Join-Path $PSScriptRoot 'compare_font_capture_sets.py'
$arguments = @('--output', [IO.Path]::GetFullPath($OutputDirectory))
if ($PSCmdlet.ParameterSetName -ceq 'ScreenshotGrid') {
    $arguments += @('--screenshots', [IO.Path]::GetFullPath($ScreenshotDirectory))
}
else {
    $arguments += @('--paired-grids', [IO.Path]::GetFullPath($PairedGridDirectory))
}

& (Join-Path ([string]$paths.scripts) 'lib\run_python.ps1') `
    -PackageSet imaging `
    -Script $pythonScript `
    -ArgumentList $arguments `
    -NoBytecode
exit $LASTEXITCODE
