[CmdletBinding(DefaultParameterSetName = 'Replay')]
param(
    [Parameter(Mandatory)][string]$Suite,
    [Parameter(Mandatory, ParameterSetName = 'Replay')]
    [Parameter(Mandatory, ParameterSetName = 'Capture')]
    [string]$Game,
    [Parameter(Mandatory, ParameterSetName = 'Capture')]
    [string]$CaptureOutputRoot,
    [Parameter(Mandatory, ParameterSetName = 'Publish')]
    [string]$CapturedRoot,
    [Parameter(Mandatory, ParameterSetName = 'Publish')]
    [string]$CaptureRoot
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$context = if ($PSCmdlet.ParameterSetName -ceq 'Publish') {
    Get-VisualRegressionContext -Suite $Suite -CaptureRoot $CaptureRoot
}
else {
    Get-VisualRegressionContext -Suite $Suite
}
$captureRootExists = Test-Path -LiteralPath $context.CaptureRoot -PathType Container
$captureRootEmpty = $captureRootExists -and
    @(Get-ChildItem -LiteralPath $context.CaptureRoot -Force).Count -eq 0
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

if ($PSCmdlet.ParameterSetName -ceq 'Capture') {
    Invoke-VisualRegressionReplay `
        -Repository $context.Repository `
        -SharedRecordingRoot $paths.pcsx2_input_recordings `
        -RecordingPath $recordingPath `
        -Game $Game `
        -CaptureRoot $CaptureOutputRoot
    $capturedScreenshots = Join-Path $CaptureOutputRoot 'screenshots'
    if (@(Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File).Count -eq 0) {
        throw 'Reference replay completed without captured screenshots.'
    }
    Write-Host 'Reference replay captured for coordinated publication.' -ForegroundColor Green
    return
}

$transaction = New-VisualRegressionTransaction `
    -Root $context.Root `
    -Prefix 'reference'
$runtimeCapture = if ($PSCmdlet.ParameterSetName -ceq 'Publish') {
    [IO.Path]::GetFullPath($CapturedRoot)
}
else {
    Join-Path $transaction 'capture'
}
$suiteCaptureStage = Join-Path $transaction 'suite-captures'
$stageRoot = Join-Path $transaction 'stages'
$referenceStage = Join-Path $stageRoot $script:E2eCaptureTiers.Reference
$currentStage = Join-Path $stageRoot $script:E2eCaptureTiers.Current
$reportStage = Join-Path $stageRoot 'report'
$screenshotStage = if ($initializeCapture) {
    Join-Path $suiteCaptureStage $script:E2eScreenshotDirectory
}
else {
    Join-Path $stageRoot $script:E2eScreenshotDirectory
}
$gridStage = if ($initializeCapture) {
    Join-Path $suiteCaptureStage $script:E2eGridDirectory
}
else {
    Join-Path $stageRoot $script:E2eGridDirectory
}
$statesStage = if ($initializeCapture) {
    Join-Path $suiteCaptureStage 'sstates'
}
else {
    Join-Path $stageRoot 'sstates'
}
$scratch = Join-Path $transaction 'scratch'

try {
    [void](New-Item -ItemType Directory -Path $referenceStage, $currentStage, $scratch -Force)
    New-VisualRegressionTierStage `
        -ScreenshotDirectory $context.Capture.Screenshots `
        -StageDirectory $currentStage `
        -Kind Current
    if ($PSCmdlet.ParameterSetName -ceq 'Replay') {
        Invoke-VisualRegressionReplay `
            -Repository $context.Repository `
            -SharedRecordingRoot $paths.pcsx2_input_recordings `
            -RecordingPath $recordingPath `
            -Game $Game `
            -CaptureRoot $runtimeCapture
    }
    $capturedScreenshots = Join-Path $runtimeCapture 'screenshots'
    if (@(Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File).Count -eq 0) {
        throw 'Reference replay completed without captured screenshots.'
    }
    Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File |
        Copy-Item -Destination $referenceStage
    $capturedStates = Join-Path $runtimeCapture 'sstates'
    if (Test-Path -LiteralPath $capturedStates -PathType Container) {
        New-VisualRegressionStateStage `
            -ExistingRoot $context.Capture.States `
            -StageRoot $statesStage `
            -Tier $script:E2eCaptureTiers.Reference `
            -CapturedDirectory $capturedStates `
            -CaptureRepository $context.CaptureRepository `
            -ExistingScreenshotDirectory $context.Capture.Screenshots `
            -ExistingScreenshotKind Reference `
            -CapturedScreenshotDirectory $capturedScreenshots `
            -PythonRunner $context.PythonRunner
    }

    $hasCurrent = @(Get-NumericPngSlots -Directory $currentStage).Count -gt 0
    if ($hasCurrent) {
        New-VisualRegressionReport `
            -Suite $Suite `
            -ReferenceDirectory $referenceStage `
            -CurrentDirectory $currentStage `
            -OutputRoot $reportStage
    }
    New-VisualRegressionScreenshotStage `
        -ReferenceDirectory $referenceStage `
        -CurrentDirectory $currentStage `
        -ReportDirectory $(if ($hasCurrent) { $reportStage } else { $null }) `
        -OutputDirectory $screenshotStage
    if ($hasCurrent) {
        [void](New-Item -ItemType Directory -Path $gridStage -Force)
        $generatedGrids = Join-Path $reportStage 'grids'
        if (Test-Path -LiteralPath $generatedGrids -PathType Container) {
            Get-ChildItem -LiteralPath $generatedGrids -File |
                Copy-Item -Destination $gridStage
        }
    }

    $replacements = if ($initializeCapture) {
        [ordered]@{ ($context.CaptureRoot) = $suiteCaptureStage }
    }
    else {
        $existingReplacements = [ordered]@{
            ($context.Capture.Screenshots) = $screenshotStage
        }
        if ($hasCurrent) {
            $existingReplacements[$context.Capture.Grids] = $gridStage
        }
        if (Test-Path -LiteralPath $statesStage -PathType Container) {
            $existingReplacements[$context.Capture.States] = $statesStage
        }
        $existingReplacements
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction
    Write-Host 'Reference screenshots, savestates, and comparison artifacts were published atomically.' -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
