[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Suite,
    [Parameter(Mandatory)][string]$NewSuite
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$source = Get-VisualRegressionContext -Suite $Suite
$destination = Get-VisualRegressionContext -Suite $NewSuite

if ($source.GeneratedNamespace -or $destination.GeneratedNamespace) {
    throw "The generated E2E suite '$($script:E2eGeneratedSuiteName)' cannot be renamed."
}
if ($source.Suite -ceq $destination.Suite) {
    throw 'The source and destination suite names are identical.'
}
if (-not (Test-Path -LiteralPath $source.SuitePath -PathType Leaf)) {
    throw "E2E suite does not exist: $($source.Suite)"
}
if ((Test-Path -LiteralPath $destination.SuitePath) -or
    (Test-Path -LiteralPath $destination.DescendantSuiteRoot) -or
    (Test-Path -LiteralPath $destination.CaptureRoot)) {
    throw "E2E suite destination already exists: $($destination.Suite)"
}

[void](New-Item -ItemType Directory -Path (
    [IO.Path]::GetDirectoryName($destination.SuitePath)
) -Force)
Move-Item -LiteralPath $source.SuitePath -Destination $destination.SuitePath
if (Test-Path -LiteralPath $source.DescendantSuiteRoot -PathType Container) {
    [void](New-Item -ItemType Directory -Path (
        [IO.Path]::GetDirectoryName($destination.DescendantSuiteRoot)
    ) -Force)
    Move-Item `
        -LiteralPath $source.DescendantSuiteRoot `
        -Destination $destination.DescendantSuiteRoot
}
if (Test-Path -LiteralPath $source.CaptureRoot -PathType Container) {
    [void](New-Item -ItemType Directory -Path (
        [IO.Path]::GetDirectoryName($destination.CaptureRoot)
    ) -Force)
    Move-Item -LiteralPath $source.CaptureRoot -Destination $destination.CaptureRoot
}
Remove-VisualRegressionEmptyParents `
    -Path $source.SuitePath `
    -Boundary $source.RecordingRepository
Remove-VisualRegressionEmptyParents `
    -Path $source.CaptureRoot `
    -Boundary $source.CaptureRepository
Write-Host "Renamed E2E suite: $($source.Suite) -> $($destination.Suite)" -ForegroundColor Green
