[CmdletBinding()]
param(
    [Parameter(Mandatory)][string[]]$Suite,
    [Parameter(Mandatory)][string]$CapturedRepository,
    [Parameter(Mandatory)][string]$CaptureRepository,
    [switch]$PreserveGeneratedTier
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$capturedRepository = [IO.Path]::GetFullPath($CapturedRepository)
$captureRepository = [IO.Path]::GetFullPath($CaptureRepository)
$postprocessScript = Join-Path $PSScriptRoot 'postprocess.ps1'
$suiteScript = Join-Path $PSScriptRoot 'suite.ps1'
$transaction = New-VisualRegressionTransaction -Root $root -Prefix 'reference-publish'
$tasks = [Collections.Generic.List[object]]::new()
$contexts = [Collections.Generic.List[object]]::new()

try {
    foreach ($suiteName in $Suite) {
        $taskSuite = $suiteName
        $defaultContext = Get-VisualRegressionContext -Suite $taskSuite
        $taskCaptureRoot = Join-Path $captureRepository $defaultContext.SuiteRelativePath
        $taskCapturedRoot = Join-Path $capturedRepository $defaultContext.SuiteRelativePath
        $context = Get-VisualRegressionContext `
            -Suite $taskSuite `
            -CaptureRoot $taskCaptureRoot
        $contexts.Add($context)
        $prepareKey = "reference-prepare/$taskSuite"
        if ($context.Generated) {
            $existingGridDirectory = $context.Capture.ScreenshotGrids
            $capturedGridDirectory = Join-Path `
                $taskCapturedRoot `
                $script:E2eScreenshotGridDirectory
            $outputGridDirectory = Join-Path `
                (Join-Path `
                    (Join-Path $transaction 'publish') `
                    $context.SuiteRelativePath) `
                $script:E2eScreenshotGridDirectory
            $tasks.Add([pscustomobject]@{
                Key = $prepareKey
                Priority = 80
                DependsOn = @()
                Ready = $null
                Start = {
                    Start-ThreadJob -Name $prepareKey -ScriptBlock {
                        param(
                            $Script,
                            $ExistingDirectory,
                            $CapturedDirectory,
                            $OutputDirectory,
                            $PreserveCapturedTier
                        )
                        $ErrorActionPreference = 'Stop'
                        . $Script
                        New-VisualRegressionGeneratedGridStage `
                            -ExistingDirectory $ExistingDirectory `
                            -CapturedDirectory $CapturedDirectory `
                            -OutputDirectory $OutputDirectory `
                            -CapturedTier Reference `
                            -PreserveCapturedTier:$PreserveCapturedTier
                    } -ArgumentList (
                        $suiteScript,
                        $existingGridDirectory,
                        $capturedGridDirectory,
                        $outputGridDirectory,
                        $PreserveGeneratedTier.IsPresent
                    )
                }.GetNewClosure()
            })
            continue
        }
        $tasks.Add([pscustomobject]@{
            Key = $prepareKey
            Priority = 80
            DependsOn = @()
            Ready = $null
            Start = {
                Start-ThreadJob -Name $prepareKey -ScriptBlock {
                    param($Script, $Suite, $Transaction, $CaptureRoot, $CapturedRoot)
                    $ErrorActionPreference = 'Stop'
                    & $Script `
                        -Action ReferencePrepare `
                        -Suite $Suite `
                        -Transaction $Transaction `
                        -CaptureRoot $CaptureRoot `
                        -CapturedRoot $CapturedRoot
                } -ArgumentList (
                    $postprocessScript,
                    $taskSuite,
                    $transaction,
                    $taskCaptureRoot,
                    $taskCapturedRoot
                )
            }.GetNewClosure()
        })
        foreach ($action in @('ScreenshotGrid', 'Pair', 'Blend', 'Diff')) {
            $taskAction = $action
            $taskKey = "reference-artifact/$taskSuite/$($taskAction.ToLowerInvariant())"
            $tasks.Add([pscustomobject]@{
                Key = $taskKey
                Priority = 10
                DependsOn = @($prepareKey)
                Ready = $null
                Start = {
                    Start-ThreadJob -Name $taskKey -ScriptBlock {
                        param($Script, $Action, $Suite, $Transaction, $CaptureRoot)
                        $ErrorActionPreference = 'Stop'
                        & $Script `
                            -Action $Action `
                            -Suite $Suite `
                            -Transaction $Transaction `
                            -CaptureRoot $CaptureRoot
                    } -ArgumentList (
                        $postprocessScript,
                        $taskAction,
                        $taskSuite,
                        $transaction,
                        $taskCaptureRoot
                    )
                }.GetNewClosure()
            })
        }
    }

    Invoke-VisualRegressionTaskGraph `
        -Task ([object[]]$tasks) `
        -FailurePrefix 'Reference publication task'

    $replacements = [ordered]@{}
    foreach ($context in $contexts) {
        $suitePublish = Join-Path (Join-Path $transaction 'publish') $context.SuiteRelativePath
        if ($context.Generated) {
            $replacements[$context.CaptureRoot] = $suitePublish
            continue
        }
        $suiteStage = Join-Path (Join-Path $transaction 'stages') $context.SuiteRelativePath
        $metadata = Get-Content `
            -Raw `
            -LiteralPath (Join-Path $suiteStage 'postprocess.json') |
            ConvertFrom-Json
        $replacements[$context.Capture.Screenshots] = Join-Path `
            $suitePublish `
            $script:E2eScreenshotDirectory
        $replacements[$context.Capture.ScreenshotGrids] = Join-Path `
            $suitePublish `
            $script:E2eScreenshotGridDirectory
        if ($metadata.has_reference -and $metadata.has_current) {
            $replacements[$context.Capture.Pairs] = Join-Path `
                $suitePublish `
                $script:E2ePairDirectory
            $replacements[$context.Capture.Blends] = Join-Path `
                $suitePublish `
                $script:E2eBlendDirectory
            $replacements[$context.Capture.Diffs] = Join-Path `
                $suitePublish `
                $script:E2eDiffDirectory
            $replacements[$context.Capture.PairGrids] = Join-Path `
                $suitePublish `
                $script:E2ePairGridDirectory
            $replacements[$context.Capture.BlendGrids] = Join-Path `
                $suitePublish `
                $script:E2eBlendGridDirectory
            $replacements[$context.Capture.DiffGrids] = Join-Path `
                $suitePublish `
                $script:E2eDiffGridDirectory
        }
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction `
        -AfterPublish {
            $aggregateContexts = @($contexts | Where-Object { -not $_.Generated })
            if ($aggregateContexts.Count -gt 0) {
                Publish-VisualRegressionAggregateViews `
                    -Context ([object[]]$aggregateContexts) `
                    -TransactionRoot $transaction
            }
        }
    Write-Host "Published NUN5 reference artifacts for $($contexts.Count) suite(s)." -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $root
}
