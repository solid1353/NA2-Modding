[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Suite,
    [Parameter(Mandatory)][string]$NewSuite
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$source = Get-VisualRegressionContext -Suite $Suite
$destination = Get-VisualRegressionContext -Suite $NewSuite

if ($source.Suite -ceq $destination.Suite) {
    throw 'The source and destination suite names are identical.'
}
if (-not (Test-Path -LiteralPath $source.SuiteRoot -PathType Container)) {
    throw "E2E suite does not exist: $($source.Suite)"
}
if ((Test-Path -LiteralPath $destination.SuiteRoot) -or
    (Test-Path -LiteralPath $destination.CaptureRoot)) {
    throw "E2E suite destination already exists: $($destination.Suite)"
}

[void](New-Item -ItemType Directory -Path (
    [IO.Path]::GetDirectoryName($destination.SuiteRoot)
) -Force)
Move-Item -LiteralPath $source.SuiteRoot -Destination $destination.SuiteRoot
if (Test-Path -LiteralPath $source.CaptureRoot -PathType Container) {
    [void](New-Item -ItemType Directory -Path (
        [IO.Path]::GetDirectoryName($destination.CaptureRoot)
    ) -Force)
    Move-Item -LiteralPath $source.CaptureRoot -Destination $destination.CaptureRoot
}
Remove-VisualRegressionEmptyParents `
    -Path $source.SuiteRoot `
    -Boundary (Join-Path $source.Root 'suites')
Remove-VisualRegressionEmptyParents `
    -Path $source.CaptureRoot `
    -Boundary $source.CaptureRepository
Write-Host "Renamed E2E suite: $($source.Suite) -> $($destination.Suite)" -ForegroundColor Green
