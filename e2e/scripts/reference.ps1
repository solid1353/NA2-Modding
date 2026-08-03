[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Suite,
    [Parameter(Mandatory)][string]$Reference,
    [switch]$f
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$context = Get-VisualRegressionContext -Suite $Suite
$captureRootExists = Test-Path -LiteralPath $context.CaptureRoot -PathType Container
$captureRootEmpty = $captureRootExists -and
    @(Get-ChildItem -LiteralPath $context.CaptureRoot -Force).Count -eq 0
$referenceScreenshotsRoot = $context.Capture.Reference
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
    Join-Path $transaction $script:E2eCaptureTiers.Reference
}
else {
    Join-Path $suiteCaptureStage $script:E2eCaptureTiers.Reference
}
$referenceScreenshots = $referenceStage
$reportStage = if (-not $initializeCapture) {
    Join-Path $transaction $script:E2eReportDirectory
}
else {
    Join-Path $suiteCaptureStage $script:E2eReportDirectory
}
$statesStage = if ($initializeCapture) {
    Join-Path $suiteCaptureStage 'sstates'
}
else {
    Join-Path $transaction 'sstates'
}
$scratch = Join-Path $transaction 'scratch'

try {
    [void](New-Item -ItemType Directory -Path $referenceScreenshots, $scratch -Force)
    if ($initializeCapture) {
        [void](New-Item -ItemType Directory -Path `
            (Join-Path $suiteCaptureStage $script:E2eCaptureTiers.Current) `
            -Force)
    }
    Invoke-VisualRegressionReplay `
        -Repository $context.Repository `
        -SharedRecordingRoot $paths.pcsx2_input_recordings `
        -RecordingPath $recordingPath `
        -Game $Reference `
        -CaptureRoot $captureRoot
    $capturedScreenshots = Join-Path $captureRoot 'screenshots'
    if (@(Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File).Count -eq 0) {
        throw 'Reference replay completed without captured screenshots.'
    }
    Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File |
        Copy-Item -Destination $referenceScreenshots
    $capturedStates = Join-Path $captureRoot 'sstates'
    if (Test-Path -LiteralPath $capturedStates -PathType Container) {
        New-VisualRegressionStateStage `
            -ExistingRoot $context.Capture.States `
            -StageRoot $statesStage `
            -Tier $script:E2eCaptureTiers.Reference `
            -CapturedDirectory $capturedStates `
            -ExistingScreenshotDirectory $context.Capture.Reference `
            -CapturedScreenshotDirectory $capturedScreenshots `
            -PythonRunner $context.PythonRunner
    }

    $currentScreenshots = if ($initializeCapture) {
        Join-Path $suiteCaptureStage $script:E2eCaptureTiers.Current
    }
    else {
        $context.Capture.Current
    }
    $replacements = if (-not $initializeCapture) {
        $existingReplacements = [ordered]@{
            ($context.Capture.Reference) = $referenceScreenshots
        }
        if (@(Get-NumericPngSlots -Directory $currentScreenshots).Count -gt 0) {
            New-VisualRegressionReport `
                -Suite $Suite `
                -ReferenceDirectory $referenceStage `
                -CurrentDirectory $currentScreenshots `
                -OutputRoot $reportStage
            $existingReplacements[$context.Capture.Report] = $reportStage
        }
        if (Test-Path -LiteralPath $statesStage -PathType Container) {
            $existingReplacements[$context.Capture.States] = $statesStage
        }
        $existingReplacements
    }
    else {
        if (@(Get-NumericPngSlots -Directory $currentScreenshots).Count -gt 0) {
            New-VisualRegressionReport `
                -Suite $Suite `
                -ReferenceDirectory $referenceStage `
                -CurrentDirectory $currentScreenshots `
                -OutputRoot $reportStage
        }
        [ordered]@{ ($context.CaptureRoot) = $suiteCaptureStage }
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction
    Write-Host 'Reference screenshots, changed-screen savestates, and report were published atomically.' -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
