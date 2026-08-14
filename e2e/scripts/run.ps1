[CmdletBinding()]
param(
    [string[]]$Suite,
    [string]$CaptureRoot,
    [string]$CaptureRepository,
    [switch]$Shifted,
    [switch]$RepeatNormal,
    [object[]]$SupervisedJob = @()
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
. (Join-Path $PSScriptRoot 'config.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$configuration = Get-E2eConfiguration -Root $root
$suiteRoot = Join-Path $root 'suites'
$suiteWasSpecified = $PSBoundParameters.ContainsKey('Suite')
$requestedSuites = @(
    Get-VisualRegressionRequestedSuiteNames `
        -Suite $Suite `
        -WasSpecified $suiteWasSpecified
)
if (-not [string]::IsNullOrWhiteSpace($CaptureRoot) -and
    -not [string]::IsNullOrWhiteSpace($CaptureRepository)) {
    throw 'CaptureRoot and CaptureRepository cannot be combined.'
}
if (-not [string]::IsNullOrWhiteSpace($CaptureRoot) -and
    $requestedSuites.Count -ne 1) {
    throw 'CaptureRoot requires one selected suite.'
}
if (-not [string]::IsNullOrWhiteSpace($CaptureRepository) -and
    $requestedSuites.Count -eq 0) {
    throw 'CaptureRepository requires selected suites.'
}
if ($RepeatNormal.IsPresent -and $requestedSuites.Count -eq 0) {
    throw 'RepeatNormal requires selected suites.'
}
function Get-E2eRunContext {
    param([Parameter(Mandatory)][string]$Name)

    if (-not [string]::IsNullOrWhiteSpace($CaptureRoot)) {
        return Get-VisualRegressionContext -Suite $Name -CaptureRoot $CaptureRoot
    }
    if (-not [string]::IsNullOrWhiteSpace($CaptureRepository)) {
        $defaultContext = Get-VisualRegressionContext -Suite $Name
        return Get-VisualRegressionContext `
            -Suite $Name `
            -CaptureRoot (Join-Path $CaptureRepository $defaultContext.SuiteRelativePath)
    }
    return Get-VisualRegressionContext -Suite $Name
}
$availableSuites = @(
    Get-VisualRegressionSuiteNames -SuiteRepository $suiteRoot
)
$suites = @(
    if ($requestedSuites.Count -eq 0) {
        $availableSuites
    }
    else {
        $selected = [Collections.Generic.HashSet[string]]::new(
            [StringComparer]::OrdinalIgnoreCase
        )
        foreach ($requestedSuite in $requestedSuites) {
            $requestedContext = Get-E2eRunContext -Name $requestedSuite
            if (-not (Test-Path -LiteralPath $requestedContext.SuitePath -PathType Leaf)) {
                throw "E2E suite does not exist: $($requestedContext.Suite)"
            }
            if (-not $selected.Add($requestedContext.Suite)) {
                throw "Duplicate E2E suite selection: $($requestedContext.Suite)"
            }
            $requestedContext.Suite
        }
    }
)
if ($suites.Count -eq 0) {
    throw 'No E2E suites are available.'
}
$publishedVariant = [string]$configuration.PublishedVariant.name
$runVariants = @(
    if ($Shifted.IsPresent) {
        $configuration.Variants
    }
    else {
        $configuration.PublishedVariant
    }
)
$comparisonVariants = @(
    $runVariants |
        Where-Object { [string]$_.name -cne $publishedVariant }
)
$comparisonRuns = @(
    if ($RepeatNormal.IsPresent) {
        [pscustomobject]@{
            name = "$publishedVariant-repeat"
            compare_against = $publishedVariant
        }
    }
    $comparisonVariants
)
foreach ($comparisonVariant in $comparisonRuns) {
    if ([string]$comparisonVariant.compare_against -cne $publishedVariant) {
        throw "Comparison variant $($comparisonVariant.name) must compare against $publishedVariant."
    }
}

$transaction = New-VisualRegressionTransaction -Root $root -Prefix 'run'
$jobs = [Collections.Generic.List[object]]::new()
$tasks = [Collections.Generic.List[object]]::new()
$comparisonTasks = [Collections.Generic.List[object]]::new()
$comparisonFailures = [Collections.Generic.List[string]]::new()
$postprocessScript = Join-Path $PSScriptRoot 'postprocess.ps1'
$suiteScript = Join-Path $PSScriptRoot 'suite.ps1'
foreach ($suiteName in $suites) {
    $taskSuite = $suiteName
    $context = Get-E2eRunContext -Name $taskSuite
    $normalSuite = Join-Path `
        (Join-Path (Join-Path (Join-Path $transaction 'jobs') $publishedVariant) 'suites') `
        $context.SuiteRelativePath
    $normalComplete = Join-Path $normalSuite 'complete.json'
    $prepareKey = "prepare/$taskSuite"
    $taskCaptureRoot = $context.CaptureRoot
    $tasks.Add([pscustomobject]@{
        Key = $prepareKey
        Priority = 80
        DependsOn = @()
        Ready = {
            Test-Path -LiteralPath $normalComplete -PathType Leaf
        }.GetNewClosure()
        Start = {
            Start-ThreadJob -Name $prepareKey -ScriptBlock {
                param($Script, $Suite, $Transaction, $CaptureRoot, $Variant)
                $ErrorActionPreference = 'Stop'
                & $Script `
                    -Action CurrentPrepare `
                    -Suite $Suite `
                    -Transaction $Transaction `
                    -CaptureRoot $CaptureRoot `
                    -PublishedVariant $Variant
            } -ArgumentList (
                $postprocessScript,
                $taskSuite,
                $transaction,
                $taskCaptureRoot,
                $publishedVariant
            )
        }.GetNewClosure()
    })
    foreach ($action in @('ScreenshotGrid', 'Pair', 'Blend', 'Diff')) {
        $taskAction = $action
        $taskKey = "artifact/$taskSuite/$($taskAction.ToLowerInvariant())"
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
    foreach ($comparisonVariant in $comparisonRuns) {
        $candidateName = [string]$comparisonVariant.name
        $candidateSuite = Join-Path `
            (Join-Path (Join-Path (Join-Path $transaction 'jobs') $candidateName) 'suites') `
            $context.SuiteRelativePath
        $candidateComplete = Join-Path $candidateSuite 'complete.json'
        $comparisonRoot = Join-Path `
            (Join-Path (Join-Path $transaction 'comparisons') $candidateName) `
            $context.SuiteRelativePath
        $comparisonKey = "compare/$candidateName/$taskSuite"
        $comparisonTask = [pscustomobject]@{
            Key = $comparisonKey
            Priority = 100
            Candidate = $candidateName
            Suite = $taskSuite
            Result = Join-Path $comparisonRoot 'result.json'
            DependsOn = @()
            Ready = {
                (Test-Path -LiteralPath $normalComplete -PathType Leaf) -and
                    (Test-Path -LiteralPath $candidateComplete -PathType Leaf)
            }.GetNewClosure()
            Start = {
                Start-ThreadJob -Name $comparisonKey -ScriptBlock {
                    param(
                        $Script,
                        $Suite,
                        $BaselineDirectory,
                        $CandidateDirectory,
                        $CandidateName,
                        $OutputRoot
                    )
                    $ErrorActionPreference = 'Stop'
                    . $Script
                    $comparison = Compare-VisualRegressionVariants `
                        -Suite $Suite `
                        -BaselineDirectory $BaselineDirectory `
                        -CandidateDirectory $CandidateDirectory `
                        -CandidateName $CandidateName `
                        -OutputRoot $OutputRoot
                    if ($comparison.status -cne 'passed') {
                        throw (
                            "$CandidateName/$Suite comparison found " +
                            "$(@($comparison.mismatches).Count) differing capture(s)."
                        )
                    }
                    $comparison
                } -ArgumentList (
                    $suiteScript,
                    $taskSuite,
                    (Join-Path $normalSuite 'capture\screenshots'),
                    (Join-Path $candidateSuite 'capture\screenshots'),
                    $candidateName,
                    $comparisonRoot
                )
            }.GetNewClosure()
        }
        $tasks.Add($comparisonTask)
        $comparisonTasks.Add($comparisonTask)
    }
}
$pipelineCompleted = $false
try {
    $suiteSelectionJson = ConvertTo-Json -Compress -InputObject ([string[]]$suites)
    $replayNames = @($runVariants.name)
    if ($RepeatNormal.IsPresent) {
        $replayNames += "$publishedVariant-repeat"
    }
    Write-Host (
        "E2E pipeline started for $($suites -join ', '): " +
        "build/replay lanes $($replayNames -join ', ') run concurrently."
    ) -ForegroundColor Cyan
    foreach ($variant in $runVariants) {
        $variantName = [string]$variant.name
        $variantJob = Start-Job -Name $variantName -ScriptBlock {
            param($Script, $Variant, $Transaction, $SuiteSelectionJson, $Repeat)
            $ErrorActionPreference = 'Stop'
            $variantArguments = @{
                Variant = $Variant
                Transaction = $Transaction
                Suite = [string[]]@($SuiteSelectionJson | ConvertFrom-Json)
            }
            if ($Repeat) {
                $variantArguments.Repeat = $true
            }
            & $Script @variantArguments
        } -ArgumentList (
            Join-Path $PSScriptRoot 'variant.ps1'
        ), $variantName, $transaction, $suiteSelectionJson, (
            $RepeatNormal.IsPresent -and $variantName -ceq $publishedVariant
        )
        $jobs.Add($variantJob)
    }
    Write-Host (
        "E2E ISO build jobs running: " +
        "$(@($runVariants.name) -join ', ')."
    ) -ForegroundColor Cyan

    $nextProgress = [DateTime]::UtcNow
    $pollJobs = {
        if ([DateTime]::UtcNow -ge $nextProgress) {
            $jobState = @(
                $jobs | ForEach-Object { "$($_.Name)=$($_.State)" }
            ) -join ', '
            Write-Host "E2E pipeline running: $jobState"
            $nextProgress = [DateTime]::UtcNow.AddSeconds(10)
        }
    }
    try {
        Invoke-VisualRegressionTaskGraph `
            -Task ([object[]]$tasks) `
            -SupervisedJob ([object[]](@($jobs) + @($SupervisedJob))) `
            -FailurePrefix 'E2E pipeline task' `
            -OnPoll $pollJobs
    }
    catch {
        $failedComparison = @(
            $comparisonTasks | Where-Object {
                if (-not (Test-Path -LiteralPath $_.Result -PathType Leaf)) {
                    return $false
                }
                (Get-Content -Raw -LiteralPath $_.Result | ConvertFrom-Json).status -cne 'passed'
            }
        ).Count -gt 0
        if ($failedComparison) {
            Preserve-VisualRegressionMismatchEvidence `
                -Transaction $transaction `
                -ComparisonVariant ([string[]]@($comparisonRuns.name))
        }
        throw
    }

    foreach ($comparisonTask in $comparisonTasks) {
        if (-not (Test-Path -LiteralPath $comparisonTask.Result -PathType Leaf)) {
            throw "Missing E2E comparison result: $($comparisonTask.Candidate)/$($comparisonTask.Suite)"
        }
        $comparison = Get-Content -Raw -LiteralPath $comparisonTask.Result | ConvertFrom-Json
        if ($comparison.status -cne 'passed') {
            $failure = "$($comparisonTask.Candidate)/$($comparisonTask.Suite)"
            $comparisonFailures.Add($failure)
            Write-Warning (
                "$publishedVariant/$($comparisonTask.Candidate) comparison failed for " +
                "$($comparisonTask.Suite) with $(@($comparison.mismatches).Count) differing capture(s)."
            )
        }
    }
    if ($comparisonFailures.Count -gt 0) {
        Preserve-VisualRegressionMismatchEvidence `
            -Transaction $transaction `
            -ComparisonVariant ([string[]]@($comparisonRuns.name))
        throw (
            'E2E capture comparison failed for case(s): ' +
            ($comparisonFailures -join ', ')
        )
    }

    $replacements = [ordered]@{}
    foreach ($suiteName in $suites) {
        $context = Get-E2eRunContext -Name $suiteName
        $suiteStage = Join-Path (Join-Path $transaction 'stages') $context.SuiteRelativePath
        $metadata = Get-Content `
            -Raw `
            -LiteralPath (Join-Path $suiteStage 'postprocess.json') |
            ConvertFrom-Json
        $suitePublish = Join-Path (Join-Path $transaction 'publish') $context.SuiteRelativePath
        $screenshotStage = Join-Path $suitePublish $script:E2eScreenshotDirectory
        $screenshotGridStage = Join-Path `
            $suitePublish `
            $script:E2eScreenshotGridDirectory
        $replacements[$context.Capture.Screenshots] = $screenshotStage
        $replacements[$context.Capture.ScreenshotGrids] = $screenshotGridStage
        if ($metadata.has_reference -and $metadata.has_current) {
            foreach ($comparison in @(
                [pscustomobject]@{
                    Name = $script:E2ePairDirectory
                    Kind = 'Pair'
                    Destination = $context.Capture.Pairs
                },
                [pscustomobject]@{
                    Name = $script:E2eBlendDirectory
                    Kind = 'Blend'
                    Destination = $context.Capture.Blends
                },
                [pscustomobject]@{
                    Name = $script:E2eDiffDirectory
                    Kind = 'Diff'
                    Destination = $context.Capture.Diffs
                }
            )) {
                $replacements[$comparison.Destination] = Join-Path `
                    $suitePublish `
                    $comparison.Name
            }
            foreach ($grid in @(
                [pscustomobject]@{
                    Name = $script:E2ePairGridDirectory
                    Destination = $context.Capture.PairGrids
                },
                [pscustomobject]@{
                    Name = $script:E2eBlendGridDirectory
                    Destination = $context.Capture.BlendGrids
                },
                [pscustomobject]@{
                    Name = $script:E2eDiffGridDirectory
                    Destination = $context.Capture.DiffGrids
                }
            )) {
                $replacements[$grid.Destination] = Join-Path $suitePublish $grid.Name
            }
        }
        if ($metadata.has_states) {
            $replacements[$context.Capture.States] = Join-Path $suitePublish 'sstates'
        }
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction `
        -AfterPublish {
            $aggregateContexts = @(
                $suites | ForEach-Object { Get-E2eRunContext -Name $_ }
            )
            Publish-VisualRegressionAggregateViews `
                -Context $aggregateContexts `
                -TransactionRoot $transaction
        }
    Write-Host (
        "E2E pipeline passed: $($suites.Count) suite(s), " +
        "build variant(s) $(@($runVariants.name) -join ', '), " +
        "$publishedVariant captures published."
    ) -ForegroundColor Green
    [pscustomobject]@{
        Status = 'passed'
        Suites = $suites.Count
        Variants = $runVariants.Count
    }
    $pipelineCompleted = $true
}
finally {
    foreach ($job in $jobs) {
        if ($job.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
    if ($pipelineCompleted) {
        Remove-VisualRegressionTransaction -Transaction $transaction -Root $root
    }
    else {
        try {
            Set-VisualRegressionTransactionRetained -Transaction $transaction -Root $root
        }
        catch {
            Write-Warning "Failed to mark the retained E2E transaction inactive: $($_.Exception.Message)"
        }
        Write-Warning "Failed E2E transaction retained for inspection: $transaction"
    }
}
