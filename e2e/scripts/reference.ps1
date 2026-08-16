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
    [string]$CaptureRoot,
    [string]$MovesetRange,
    [ValidateRange(1, 64)]
    [int]$MovesetThrottleLimit = 16
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
if (-not (Test-VisualRegressionSuiteExists -Context $context)) {
    throw "Visual-regression suite does not exist: $Suite"
}
if (-not [string]::IsNullOrWhiteSpace($MovesetRange) -and -not $context.Generated) {
    throw 'MovesetRange is valid only for the movesets suite.'
}
if ($context.Generated) {
    if ($PSCmdlet.ParameterSetName -ceq 'Capture') {
        $generatedArguments = @{
            Game = $Game
            Tier = 'reference'
            OutputRoot = $CaptureOutputRoot
            ThrottleLimit = $MovesetThrottleLimit
            ProjectRoot = $context.Repository
        }
        if (-not [string]::IsNullOrWhiteSpace($MovesetRange)) {
            $generatedArguments.MovesetRange = $MovesetRange
        }
        & $context.GeneratedScript @generatedArguments
        $capturedGrids = Join-Path $CaptureOutputRoot $script:E2eScreenshotGridDirectory
        if (@(Get-ChildItem -LiteralPath $capturedGrids -Filter '*.png' -File).Count -eq 0) {
            throw 'Generated reference replay completed without captured grids.'
        }
        Write-Host 'Generated reference grids captured for coordinated publication.' -ForegroundColor Green
        return
    }

    $generatedTransaction = New-VisualRegressionTransaction `
        -Root $context.Root `
        -Prefix 'reference'
    try {
        $generatedRuntimeCapture = if ($PSCmdlet.ParameterSetName -ceq 'Publish') {
            [IO.Path]::GetFullPath($CapturedRoot)
        }
        else {
            Join-Path $generatedTransaction 'capture'
        }
        if ($PSCmdlet.ParameterSetName -ceq 'Replay') {
            $generatedArguments = @{
                Game = $Game
                Tier = 'reference'
                OutputRoot = $generatedRuntimeCapture
                ThrottleLimit = $MovesetThrottleLimit
                ProjectRoot = $context.Repository
            }
            if (-not [string]::IsNullOrWhiteSpace($MovesetRange)) {
                $generatedArguments.MovesetRange = $MovesetRange
            }
            & $context.GeneratedScript @generatedArguments
        }
        $generatedPublishRoot = Join-Path `
            (Join-Path $generatedTransaction 'publish') `
            $context.SuiteRelativePath
        New-VisualRegressionGeneratedGridStage `
            -ExistingDirectory $context.Capture.ScreenshotGrids `
            -CapturedDirectory (Join-Path `
                $generatedRuntimeCapture `
                $script:E2eScreenshotGridDirectory) `
            -OutputDirectory (Join-Path `
                $generatedPublishRoot `
                $script:E2eScreenshotGridDirectory) `
            -CapturedTier Reference `
            -PreserveCapturedTier:(-not [string]::IsNullOrWhiteSpace($MovesetRange))
        Publish-VisualRegressionTransaction `
            -Replacements ([ordered]@{ ($context.CaptureRoot) = $generatedPublishRoot }) `
            -TransactionRoot $generatedTransaction
        Write-Host 'Generated reference grids were published atomically.' -ForegroundColor Green
    }
    finally {
        Remove-VisualRegressionTransaction `
            -Transaction $generatedTransaction `
            -Root $context.Root
    }
    return
}
$recordingPath = $context.SuitePath

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
$pairStage = Join-Path `
    $(if ($initializeCapture) { $suiteCaptureStage } else { $stageRoot }) `
    $script:E2ePairDirectory
$blendStage = Join-Path `
    $(if ($initializeCapture) { $suiteCaptureStage } else { $stageRoot }) `
    $script:E2eBlendDirectory
$diffStage = Join-Path `
    $(if ($initializeCapture) { $suiteCaptureStage } else { $stageRoot }) `
    $script:E2eDiffDirectory
$screenshotGridStage = Join-Path `
    $(if ($initializeCapture) { $suiteCaptureStage } else { $stageRoot }) `
    $script:E2eScreenshotGridDirectory
$pairGridStage = Join-Path `
    $(if ($initializeCapture) { $suiteCaptureStage } else { $stageRoot }) `
    $script:E2ePairGridDirectory
$blendGridStage = Join-Path `
    $(if ($initializeCapture) { $suiteCaptureStage } else { $stageRoot }) `
    $script:E2eBlendGridDirectory
$diffGridStage = Join-Path `
    $(if ($initializeCapture) { $suiteCaptureStage } else { $stageRoot }) `
    $script:E2eDiffGridDirectory
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
        -OutputDirectory $screenshotStage
    New-VisualRegressionScreenshotGridStage `
        -Suite $Suite `
        -ScreenshotDirectory $screenshotStage `
        -OutputDirectory $screenshotGridStage
    if ($hasCurrent) {
        foreach ($comparison in @(
            [pscustomobject]@{ Kind = 'Pair'; Output = $pairStage },
            [pscustomobject]@{ Kind = 'Blend'; Output = $blendStage },
            [pscustomobject]@{ Kind = 'Diff'; Output = $diffStage }
        )) {
            New-VisualRegressionComparisonStage `
                -ReportDirectory $reportStage `
                -OutputDirectory $comparison.Output `
                -Kind $comparison.Kind
        }
        New-VisualRegressionGridStage `
            -ReportDirectory $reportStage `
            -GridDirectory $script:E2ePairGridDirectory `
            -OutputDirectory $pairGridStage
        New-VisualRegressionGridStage `
            -ReportDirectory $reportStage `
            -GridDirectory $script:E2eBlendGridDirectory `
            -OutputDirectory $blendGridStage
        New-VisualRegressionGridStage `
            -ReportDirectory $reportStage `
            -GridDirectory $script:E2eDiffGridDirectory `
            -OutputDirectory $diffGridStage
    }
    $replacements = if ($initializeCapture) {
        [ordered]@{ ($context.CaptureRoot) = $suiteCaptureStage }
    }
    else {
        $existingReplacements = [ordered]@{
            ($context.Capture.Screenshots) = $screenshotStage
            ($context.Capture.ScreenshotGrids) = $screenshotGridStage
        }
        if ($hasCurrent) {
            $existingReplacements[$context.Capture.Pairs] = $pairStage
            $existingReplacements[$context.Capture.Blends] = $blendStage
            $existingReplacements[$context.Capture.Diffs] = $diffStage
            $existingReplacements[$context.Capture.PairGrids] = $pairGridStage
            $existingReplacements[$context.Capture.BlendGrids] = $blendGridStage
            $existingReplacements[$context.Capture.DiffGrids] = $diffGridStage
        }
        if (Test-Path -LiteralPath $statesStage -PathType Container) {
            $existingReplacements[$context.Capture.States] = $statesStage
        }
        $existingReplacements
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction `
        -AfterPublish {
            Publish-VisualRegressionAggregateViews `
                -Context @($context) `
                -TransactionRoot $transaction
        }
    Write-Host 'Reference screenshots, savestates, and comparison artifacts were published atomically.' -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
