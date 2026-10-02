[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Suite,
    [Parameter(Mandatory)][string]$Game,
    [Parameter(Mandatory)][string]$CaptureOutputRoot,
    [string]$MovesetRange,
    [string]$ConcurrencyPoolRoot,
    [ValidateRange(1, 64)]
    [int]$ConcurrencyLimit = 16
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$context = Get-VisualRegressionContext -Suite $Suite
if (-not (Test-VisualRegressionSuiteExists -Context $context)) {
    throw "Visual-regression suite does not exist: $Suite"
}
if ($context.Generated) {
    Invoke-VisualRegressionGeneratedCapture `
        -Context $context `
        -Game $Game `
        -Tier 'reference' `
        -OutputRoot $CaptureOutputRoot `
        -ThrottleLimit $ConcurrencyLimit `
        -ConcurrencyPoolRoot $ConcurrencyPoolRoot `
        -MovesetRange $MovesetRange
    $capturedGrids = Join-Path $CaptureOutputRoot $script:E2eScreenshotGridDirectory
    if ((Get-VisualRegressionPngCount -Directory $capturedGrids) -eq 0) {
        throw 'Generated reference replay completed without captured grids.'
    }
    Write-Host 'Generated reference grids captured for coordinated publication.' -ForegroundColor Green
    return
}

Invoke-VisualRegressionPooledReplay `
    -Repository $context.Repository `
    -SharedRecordingRoot (Get-VisualRegressionRepositoryState).Paths.pcsx2_input_recordings `
    -RecordingPath $context.SuitePath `
    -Game $Game `
    -CaptureRoot $CaptureOutputRoot `
    -MemoryCard $context.MemoryCard `
    -LaunchProfile $context.LaunchProfile `
    -ConcurrencyPoolRoot $ConcurrencyPoolRoot `
    -ConcurrencyLimit $ConcurrencyLimit
if ((Get-VisualRegressionPngCount -Directory $CaptureOutputRoot) -eq 0) {
    throw 'Reference replay completed without captured screenshots.'
}
Write-Host 'Reference replay captured for coordinated publication.' -ForegroundColor Green
