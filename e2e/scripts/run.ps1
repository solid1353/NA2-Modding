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
$pendingStage = Join-Path $transaction 'pending'
$statesStage = Join-Path $transaction 'sstates'
$reportsStage = Join-Path $transaction 'reports'
$scratch = Join-Path $transaction 'scratch'

try {
    [void](New-Item -ItemType Directory -Path $pendingStage, $scratch -Force)

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
        Copy-Item -Destination $pendingStage
    $capturedStates = Join-Path $captureRoot 'sstates'
    if (Test-Path -LiteralPath $capturedStates -PathType Container) {
        Copy-Item -LiteralPath $capturedStates -Destination $statesStage -Recurse
    }

    New-VisualRegressionReports `
        -Suite $Suite `
        -PendingDirectory $pendingStage `
        -OutputRoot $reportsStage `
        -ScratchRoot $scratch
    $approvedSummary = Join-Path $reportsStage 'approved-vs-pending\summary.tsv'
    $removedIdentical = Remove-ApprovedIdenticalPendingScreenshots `
        -PendingDirectory $pendingStage `
        -Summary $approvedSummary
    if ($removedIdentical -gt 0) {
        Remove-Item -LiteralPath $reportsStage -Recurse -Force
        New-VisualRegressionReports `
            -Suite $Suite `
            -PendingDirectory $pendingStage `
            -OutputRoot $reportsStage `
            -ScratchRoot $scratch
    }
    $replacements = [ordered]@{
        (Join-Path $context.CaptureRoot 'pending') = $pendingStage
        (Join-Path $context.CaptureRoot 'reports') = $reportsStage
    }
    if (Test-Path -LiteralPath $statesStage -PathType Container) {
        $replacements[(Join-Path $context.CaptureRoot 'sstates')] = $statesStage
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction
    $pendingSlots = @(Get-NumericPngSlots -Directory (Join-Path $context.CaptureRoot 'pending'))
    $approvedDirectory = Join-Path $context.CaptureRoot 'approved'
    $approvedSlots = @(Get-NumericPngSlots -Directory $approvedDirectory)
    $clean = $pendingSlots.Count -eq 0
    $status = if ($clean) { 'clean' } else { 'review-required' }
    Write-Host (
        "Visual-regression batch completed ($status). " +
        'Pending differences, suite-level savestates, and reports were replaced atomically.'
    ) -ForegroundColor $(if ($clean) { 'Green' } else { 'Yellow' })
    [pscustomobject]@{
        Suite = $Suite
        Status = $status
        PendingScreenshots = $pendingSlots.Count
        ApprovedScreenshots = $approvedSlots.Count
    }
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
