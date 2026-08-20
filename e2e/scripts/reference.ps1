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
    [string]$ConcurrencyPoolRoot,
    [ValidateRange(1, 64)]
    [int]$ConcurrencyLimit = 16
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
    throw 'MovesetRange is valid only for a generated character suite.'
}
if ($context.Generated) {
    if ($PSCmdlet.ParameterSetName -ceq 'Capture') {
        $generatedArguments = @{
            Game = $Game
            Tier = 'reference'
            OutputRoot = $CaptureOutputRoot
            ThrottleLimit = $ConcurrencyLimit
            ConcurrencyPoolRoot = $ConcurrencyPoolRoot
            ProjectRoot = $context.Repository
        }
        if (-not [string]::IsNullOrWhiteSpace($MovesetRange)) {
            $generatedArguments.MovesetRange = $MovesetRange
        }
        $generatedArguments.MovesetFamily = $context.GeneratedFamily
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
                ThrottleLimit = $ConcurrencyLimit
                ConcurrencyPoolRoot = $(
                    if ([string]::IsNullOrWhiteSpace($ConcurrencyPoolRoot)) {
                        Join-Path $generatedTransaction 'concurrency'
                    }
                    else {
                        $ConcurrencyPoolRoot
                    }
                )
                ProjectRoot = $context.Repository
            }
            if (-not [string]::IsNullOrWhiteSpace($MovesetRange)) {
                $generatedArguments.MovesetRange = $MovesetRange
            }
            $generatedArguments.MovesetFamily = $context.GeneratedFamily
            & $context.GeneratedScript @generatedArguments
        }
        $generatedPublishRoot = Join-Path `
            (Join-Path $generatedTransaction 'publish') `
            $context.SuiteRelativePath
        New-VisualRegressionGeneratedArtifactStage `
            -ExistingDirectory $context.Capture.ScreenshotGrids `
            -CapturedDirectory (Join-Path `
                $generatedRuntimeCapture `
                $script:E2eScreenshotGridDirectory) `
            -OutputRoot $generatedPublishRoot `
            -Comparator $context.Comparator `
            -CapturedTier Reference `
            -PreserveCapturedTier:(-not (
                    Test-VisualRegressionGeneratedSuiteRoot -Suite $context.Suite
                ) -or
                -not [string]::IsNullOrWhiteSpace($MovesetRange))
        Publish-VisualRegressionTransaction `
            -Replacements ([ordered]@{ ($context.CaptureRoot) = $generatedPublishRoot }) `
            -TransactionRoot $generatedTransaction `
            -AfterPublish {
                Publish-VisualRegressionAggregateViews `
                    -Context @($context) `
                    -TransactionRoot $generatedTransaction
            }
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
    if ([string]::IsNullOrWhiteSpace($ConcurrencyPoolRoot)) {
        $ConcurrencyPoolRoot = Join-Path `
            ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($CaptureOutputRoot))) `
            'concurrency'
    }
    Invoke-VisualRegressionPooledReplay `
        -Repository $context.Repository `
        -SharedRecordingRoot $paths.pcsx2_input_recordings `
        -RecordingPath $recordingPath `
        -Game $Game `
        -CaptureRoot $CaptureOutputRoot `
        -PracticeMovesetRow $context.PracticeMovesetRow `
        -ConcurrencyPoolRoot $ConcurrencyPoolRoot `
        -ConcurrencyLimit $ConcurrencyLimit
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
$publishRoot = if ($initializeCapture) { $suiteCaptureStage } else { $stageRoot }
$screenshotGridStage = Join-Path $publishRoot $script:E2eScreenshotGridDirectory
$pairGridStage = Join-Path $publishRoot $script:E2ePairGridDirectory
$blendGridStage = Join-Path $publishRoot $script:E2eBlendGridDirectory
$diffGridStage = Join-Path $publishRoot $script:E2eDiffGridDirectory

try {
    if ($PSCmdlet.ParameterSetName -ceq 'Replay') {
        if ([string]::IsNullOrWhiteSpace($ConcurrencyPoolRoot)) {
            $ConcurrencyPoolRoot = Join-Path $transaction 'concurrency'
        }
        Invoke-VisualRegressionPooledReplay `
            -Repository $context.Repository `
            -SharedRecordingRoot $paths.pcsx2_input_recordings `
            -RecordingPath $recordingPath `
            -Game $Game `
            -CaptureRoot $runtimeCapture `
            -PracticeMovesetRow $context.PracticeMovesetRow `
            -ConcurrencyPoolRoot $ConcurrencyPoolRoot `
            -ConcurrencyLimit $ConcurrencyLimit
    }
    $capturedScreenshots = Join-Path $runtimeCapture 'screenshots'
    if (@(Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File).Count -eq 0) {
        throw 'Reference replay completed without captured screenshots.'
    }
    New-VisualRegressionPagedScreenshotGridStage `
        -Suite $Suite `
        -ExistingDirectory $context.Capture.ScreenshotGrids `
        -CapturedScreenshotDirectory $capturedScreenshots `
        -OutputDirectory $screenshotGridStage `
        -CapturedTier Reference
    $hasCurrent = @(
        Get-ChildItem `
            -LiteralPath $screenshotGridStage `
            -Filter 'page_*_b_current.png' `
            -File `
            -ErrorAction SilentlyContinue
    ).Count -gt 0
    if ($hasCurrent) {
        & $context.Comparator `
            -PairedGridDirectory $screenshotGridStage `
            -OutputDirectory $publishRoot `
            -Kind All
        if ($LASTEXITCODE -ne 0) {
            throw "Comparison grid generation failed with exit code $LASTEXITCODE."
        }
    }
    $replacements = if ($initializeCapture) {
        [ordered]@{ ($context.CaptureRoot) = $suiteCaptureStage }
    }
    else {
        $existingReplacements = [ordered]@{
            ($context.Capture.ScreenshotGrids) = $screenshotGridStage
        }
        if ($hasCurrent) {
            $existingReplacements[$context.Capture.PairGrids] = $pairGridStage
            $existingReplacements[$context.Capture.BlendGrids] = $blendGridStage
            $existingReplacements[$context.Capture.DiffGrids] = $diffGridStage
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
    Write-Host 'Reference screenshot and comparison grids were published atomically.' -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
