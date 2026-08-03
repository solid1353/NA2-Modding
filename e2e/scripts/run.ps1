[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Suite,
    [switch]$b
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$context = Get-VisualRegressionContext -Suite $Suite
if (-not (Test-Path -LiteralPath $context.SuiteRoot -PathType Container)) {
    throw "Visual-regression suite does not exist: $Suite"
}
$stabilityPath = Join-Path $context.SuiteRoot 'stability.json'
if (Test-Path -LiteralPath $stabilityPath -PathType Leaf) {
    & (Join-Path $PSScriptRoot 'stability.ps1') -Suite $Suite
    return
}
$recordingPath = Join-Path $context.SuiteRoot 'input.p2m2'
if (-not (Test-Path -LiteralPath $recordingPath -PathType Leaf)) {
    throw "Suite recording does not exist: $recordingPath"
}
. (Join-Path $context.Repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$transaction = New-VisualRegressionTransaction `
    -Root $context.Root `
    -Prefix 'run'
$captureRoot = Join-Path $transaction 'capture'
$currentStage = Join-Path $transaction $script:E2eCaptureTiers.Current
$statesStage = Join-Path $transaction 'sstates'
$reportStage = Join-Path $transaction $script:E2eReportDirectory
$scratch = Join-Path $transaction 'scratch'

try {
    [void](New-Item -ItemType Directory -Path $currentStage, $scratch -Force)

    if ($b) {
        $build = & (Join-Path $context.Repository 'scripts\na228\build.ps1') -ScreenshotTestOnly
        if (-not $build -or $build.Status -ne 'screenshot-test') {
            throw 'Screenshot Test build did not return a valid result.'
        }
    }
    elseif (-not (Test-Path -LiteralPath $paths.files.screenshot_test_iso -PathType Leaf)) {
        throw 'Screenshot Test.iso does not exist; rerun with -b.'
    }

    Invoke-VisualRegressionReplay `
        -Repository $context.Repository `
        -SharedRecordingRoot $paths.pcsx2_input_recordings `
        -RecordingPath $recordingPath `
        -Game st `
        -CaptureRoot $captureRoot
    if (-not (Test-Path -LiteralPath $captureRoot -PathType Container)) {
        throw "Replay completed without a capture directory: $captureRoot"
    }
    $capturedScreenshots = Join-Path $captureRoot 'screenshots'
    if (@(Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File).Count -eq 0) {
        throw 'Replay completed without captured screenshots.'
    }
    Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File |
        Copy-Item -Destination $currentStage
    [void](Restore-IgnoredCurrentScreenshots `
        -CurrentDirectory $currentStage `
        -ExistingDirectory $context.Capture.Current `
        -IgnoreFile (Join-Path $context.SuiteRoot 'ignore.txt'))
    $capturedStates = Join-Path $captureRoot 'sstates'
    if (Test-Path -LiteralPath $capturedStates -PathType Container) {
        New-VisualRegressionStateStage `
            -ExistingRoot $context.Capture.States `
            -StageRoot $statesStage `
            -Tier $script:E2eCaptureTiers.Current `
            -CapturedDirectory $capturedStates `
            -CaptureRepository $context.CaptureRepository `
            -ExistingScreenshotDirectory $context.Capture.Current `
            -CapturedScreenshotDirectory $capturedScreenshots `
            -PythonRunner $context.PythonRunner `
            -IgnoreFile (Join-Path $context.SuiteRoot 'ignore.txt')
    }

    $replacements = [ordered]@{
        ($context.Capture.Current) = $currentStage
    }
    if (@(Get-NumericPngSlots -Directory $context.Capture.Reference).Count -gt 0) {
        New-VisualRegressionReport `
            -Suite $Suite `
            -CurrentDirectory $currentStage `
            -OutputRoot $reportStage
        $replacements[$context.Capture.Report] = $reportStage
    }
    if (Test-Path -LiteralPath $statesStage -PathType Container) {
        $replacements[$context.Capture.States] = $statesStage
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction
    $capturedSlots = @(Get-NumericPngSlots -Directory $context.Capture.Current)
    Write-Host (
        'E2E current captures and changed-screen savestates were published atomically.'
    ) -ForegroundColor Green
    [pscustomobject]@{
        Suite = $Suite
        Status = 'captured'
        Screenshots = $capturedSlots.Count
    }
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
