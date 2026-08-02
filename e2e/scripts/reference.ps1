[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Suite,
    [switch]$f
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$context = Get-VisualRegressionContext -Suite $Suite
$captureRootExists = Test-Path -LiteralPath $context.CaptureRoot -PathType Container
$captureRootEmpty = $captureRootExists -and
    @(Get-ChildItem -LiteralPath $context.CaptureRoot -Force).Count -eq 0
$referenceScreenshotsRoot = Join-Path $context.CaptureRoot 'references'
$referenceExists = @(
    Get-ChildItem -LiteralPath $referenceScreenshotsRoot -Filter '*.png' -File -ErrorAction SilentlyContinue
).Count -gt 0
if ($referenceExists -and -not $f) {
    throw 'Capture suite already exists; rerun with -f to overwrite its references.'
}
if (-not (Test-Path -LiteralPath $context.SuiteRoot -PathType Container)) {
    throw "Visual-regression suite does not exist: $Suite"
}
$recordingPath = Join-Path $context.SuiteRoot 'input.p2m2'
if (-not (Test-Path -LiteralPath $recordingPath -PathType Leaf)) {
    throw "Suite recording does not exist: $recordingPath"
}

. (Join-Path $context.Repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$initializeCapture = -not $captureRootExists -or $captureRootEmpty

$transaction = New-VisualRegressionTransaction `
    -Root $context.Root `
    -Prefix 'reference'
$captureRoot = Join-Path $transaction 'capture'
$suiteCaptureStage = Join-Path $transaction 'suite-captures'
$referenceStage = if (-not $initializeCapture) {
    Join-Path $transaction 'references'
}
else {
    Join-Path $suiteCaptureStage 'references'
}
$referenceScreenshots = $referenceStage
$reportsStage = if (-not $initializeCapture) {
    Join-Path $transaction 'reports'
}
else {
    Join-Path $suiteCaptureStage 'reports'
}
$scratch = Join-Path $transaction 'scratch'

try {
    [void](New-Item -ItemType Directory -Path $referenceScreenshots, $scratch -Force)
    if ($initializeCapture) {
        [void](New-Item -ItemType Directory -Path `
            (Join-Path $suiteCaptureStage 'approved'), `
            (Join-Path $suiteCaptureStage 'pending') `
            -Force)
    }
    Invoke-VisualRegressionReplay `
        -Repository $context.Repository `
        -SharedRecordingRoot $paths.pcsx2_input_recordings `
        -RecordingPath $recordingPath `
        -Game nun5 `
        -CaptureRoot $captureRoot
    $capturedScreenshots = Join-Path $captureRoot 'screenshots'
    if (@(Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File).Count -eq 0) {
        throw 'NUN5 reference replay completed without captured screenshots.'
    }
    Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File |
        Copy-Item -Destination $referenceScreenshots

    New-VisualRegressionReports `
        -Suite $Suite `
        -ReferenceDirectory $referenceStage `
        -PendingDirectory (Join-Path $context.CaptureRoot 'pending') `
        -OutputRoot $reportsStage `
        -ScratchRoot $scratch
    $replacements = if (-not $initializeCapture) {
        [ordered]@{
            (Join-Path $context.CaptureRoot 'references') = $referenceScreenshots
            (Join-Path $context.CaptureRoot 'reports') = $reportsStage
        }
    }
    else {
        [ordered]@{ $context.CaptureRoot = $suiteCaptureStage }
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction
    Write-Host 'Reference screenshots and reports were replaced atomically.' -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
