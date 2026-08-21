[CmdletBinding(DefaultParameterSetName = 'Comparison')]
param(
    [Parameter(Mandatory, ParameterSetName = 'Comparison')]
    [string]$ReferenceDirectory,

    [Parameter(Mandatory, ParameterSetName = 'Comparison')]
    [string]$CurrentDirectory,

    [Parameter(Mandatory, ParameterSetName = 'ScreenshotGrid')]
    [string]$ScreenshotDirectory,

    [Parameter(Mandatory, ParameterSetName = 'PairedGridComparison')]
    [string]$PairedGridDirectory,

    [Parameter(Mandatory)]
    [string]$OutputDirectory,

    [Parameter(ParameterSetName = 'Comparison')]
    [string]$Slots,

    [Parameter(ParameterSetName = 'Comparison')]
    [Parameter(ParameterSetName = 'PairedGridComparison')]
    [ValidateSet('All', 'Pair', 'Blend', 'Diff')]
    [string]$Kind = 'All'
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
elseif ($PSCmdlet.ParameterSetName -ceq 'PairedGridComparison') {
    $arguments += @(
        '--paired-grids',
        [IO.Path]::GetFullPath($PairedGridDirectory),
        '--kind',
        $Kind.ToLowerInvariant()
    )
}
else {
    $arguments += @(
        '--reference', [IO.Path]::GetFullPath($ReferenceDirectory)
        '--current', [IO.Path]::GetFullPath($CurrentDirectory)
        '--kind', $Kind.ToLowerInvariant()
    )
    if (-not [string]::IsNullOrWhiteSpace($Slots)) {
        $arguments += @('--slots', $Slots)
    }
}

& (Join-Path ([string]$paths.scripts) 'lib\run_python.ps1') `
    -PackageSet imaging `
    -Script $pythonScript `
    -ArgumentList $arguments `
    -NoBytecode
exit $LASTEXITCODE
