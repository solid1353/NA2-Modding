[CmdletBinding()]
param([Parameter(Mandatory)][string]$Suite)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$context = Get-VisualRegressionContext -Suite $Suite

if (-not (Test-Path -LiteralPath $context.SuiteRoot -PathType Container)) {
    throw "E2E suite does not exist: $($context.Suite)"
}

Remove-Item -LiteralPath $context.SuiteRoot -Recurse -Force
if (Test-Path -LiteralPath $context.CaptureRoot -PathType Container) {
    Remove-Item -LiteralPath $context.CaptureRoot -Recurse -Force
}
Remove-VisualRegressionEmptyParents `
    -Path $context.SuiteRoot `
    -Boundary (Join-Path $context.Root 'suites')
Remove-VisualRegressionEmptyParents `
    -Path $context.CaptureRoot `
    -Boundary $context.CaptureRepository
Write-Host "Deleted E2E suite: $($context.Suite)" -ForegroundColor Green
