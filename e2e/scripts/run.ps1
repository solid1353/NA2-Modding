[CmdletBinding()]
param(
    [string[]]$Suite,
    [string]$CaptureRoot,
    [string]$CaptureRepository,
    [switch]$Shifted,
    [object[]]$SupervisedJob = @(),
    [string]$MovesetRange,
    [string]$ConcurrencyPoolRoot,
    [ValidateRange(1, 64)]
    [int]$ConcurrencyLimit = 16
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
. (Join-Path $PSScriptRoot 'config.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$configuration = Get-E2eConfiguration -Root $root
$recordingRoot = Join-Path ([string]$paths.pcsx2_input_recordings) 'e2e'
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
    Get-VisualRegressionSuiteNames -RecordingRepository $recordingRoot
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
            if (-not (Test-VisualRegressionSuiteExists -Context $requestedContext)) {
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
$movesetRangeSpecified = -not [string]::IsNullOrWhiteSpace($MovesetRange)
if ($movesetRangeSpecified -and
    ($suites.Count -ne 1 -or -not (Test-VisualRegressionGeneratedSuite -Suite $suites[0]))) {
    throw 'MovesetRange requires one generated character suite.'
}
if ($movesetRangeSpecified) {
    $characterData = @(
        Import-Csv `
            -LiteralPath (Join-Path ([string]$paths.resources) 'character_data.tsv') `
            -Delimiter "`t"
    )
    $resolvedMovesetRange = Resolve-VisualRegressionMovesetRange `
        -Range $MovesetRange `
        -LastAvailableRow ($characterData.Count + 1)
    $MovesetRange = $resolvedMovesetRange.Value
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
foreach ($comparisonVariant in $comparisonVariants) {
    if ([string]$comparisonVariant.compare_against -cne $publishedVariant) {
        throw "Comparison variant $($comparisonVariant.name) must compare against $publishedVariant."
    }
}

$inputIdentity = [Collections.Generic.List[object]]::new()
$hasGeneratedSuite = $false
foreach ($suiteName in $suites) {
    $context = Get-E2eRunContext -Name $suiteName
    if ($context.Generated) {
        $hasGeneratedSuite = $true
        continue
    }
    $inputIdentity.Add([ordered]@{
        path = [IO.Path]::GetRelativePath($repository, $context.SuitePath).Replace('\', '/')
        sha256 = (Get-FileHash -LiteralPath $context.SuitePath -Algorithm SHA256).Hash
    })
}
if ($hasGeneratedSuite) {
    $generatedInputPaths = @(
        Join-Path ([string]$paths.resources) 'character_data.tsv'
        Join-Path ([string]$paths.resources) 'movesets.tsv'
        foreach ($generatedSuite in @($suites | Where-Object {
            Test-VisualRegressionGeneratedSuite -Suite $_
        })) {
            Get-VisualRegressionGeneratedInputPaths `
                -RecordingRepository $recordingRoot `
                -Suite $generatedSuite
        }
    ) | Sort-Object -Unique
    foreach ($path in $generatedInputPaths) {
        $inputIdentity.Add([ordered]@{
            path = [IO.Path]::GetRelativePath($repository, $path).Replace('\', '/')
            sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
        })
    }
}
$resumeRequest = [ordered]@{
    schema_version = 1
    command = 'run'
    shifted = $Shifted.IsPresent
    capture_mode = 'screenshots'
}
if ($movesetRangeSpecified) {
    $resumeRequest['moveset_range'] = $MovesetRange
}
$generatedSelection = @($suites | Where-Object {
    Test-VisualRegressionGeneratedSuite -Suite $_
})
if ($generatedSelection.Count -eq 1) {
    $resumeRequest['moveset_family'] = Get-VisualRegressionGeneratedSuiteFamily `
        -Suite $generatedSelection[0]
}
$resumeRequest['suites'] = [string[]]@($suites | Sort-Object)
$resumeRequest['inputs'] = [object[]]@($inputIdentity | Sort-Object path)
$resumeKey = $resumeRequest | ConvertTo-Json -Compress -Depth 6
$transaction = New-VisualRegressionTransaction `
    -Root $root `
    -Prefix 'run' `
    -ResumeKey $resumeKey `
    -LegacySuite $(if ($movesetRangeSpecified) { $null } else { $suites }) `
    -LegacyShifted $Shifted.IsPresent
if ([string]::IsNullOrWhiteSpace($ConcurrencyPoolRoot)) {
    $ConcurrencyPoolRoot = Join-Path $transaction 'concurrency'
}
else {
    $ConcurrencyPoolRoot = [IO.Path]::GetFullPath($ConcurrencyPoolRoot)
}
if (Test-VisualRegressionTransactionResumed -Transaction $transaction) {
    $resumeArtifacts = [Collections.Generic.List[string]]::new()
    foreach ($relative in @('publish', 'stages', 'comparisons', 'evidence', '.backups')) {
        $resumeArtifacts.Add($relative)
    }
    foreach ($variant in $runVariants) {
        $resumeArtifacts.Add("jobs\$([string]$variant.name)\ready.json")
        $resumeArtifacts.Add("jobs\$([string]$variant.name)\result.json")
    }
    Move-VisualRegressionTransactionItemsToAttempt `
        -Transaction $transaction `
        -RelativePath ([string[]]$resumeArtifacts) `
        -Label 'resume' |
        Out-Null
}
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
    $normalReady = Join-Path (Join-Path $transaction "jobs\$publishedVariant") 'ready.json'
    $prepareKey = "prepare/$taskSuite"
    $taskCaptureRoot = $context.CaptureRoot
    if ($context.Generated) {
        $preserveGeneratedTier = $movesetRangeSpecified -or
            -not (Test-VisualRegressionGeneratedSuiteRoot -Suite $context.Suite)
        $capturedGridDirectory = Join-Path $normalSuite 'capture\screenshots'
        $existingGridDirectory = $context.Capture.ScreenshotGrids
        $outputRoot = Join-Path `
            (Join-Path $transaction 'publish') `
            $context.SuiteRelativePath
        $comparator = $context.Comparator
        $tasks.Add([pscustomobject]@{
            Key = $prepareKey
            Priority = 80
            DependsOn = @()
            Ready = {
                (Test-Path -LiteralPath $normalReady -PathType Leaf) -and
                    (Test-Path -LiteralPath $normalComplete -PathType Leaf)
            }.GetNewClosure()
            Start = {
                Start-ThreadJob -Name $prepareKey -ScriptBlock {
                    param(
                        $Script,
                        $ExistingDirectory,
                        $CapturedDirectory,
                        $OutputRoot,
                        $Comparator,
                        $PreserveCapturedTier
                    )
                    $ErrorActionPreference = 'Stop'
                    . $Script
                    New-VisualRegressionGeneratedArtifactStage `
                        -ExistingDirectory $ExistingDirectory `
                        -CapturedDirectory $CapturedDirectory `
                        -OutputRoot $OutputRoot `
                        -Comparator $Comparator `
                        -CapturedTier Current `
                        -PreserveCapturedTier:$PreserveCapturedTier
                } -ArgumentList (
                    $suiteScript,
                    $existingGridDirectory,
                    $capturedGridDirectory,
                    $outputRoot,
                    $comparator,
                    $preserveGeneratedTier
                )
            }.GetNewClosure()
        })
    }
    else {
        $tasks.Add([pscustomobject]@{
            Key = $prepareKey
            Priority = 80
            DependsOn = @()
            Ready = {
                (Test-Path -LiteralPath $normalReady -PathType Leaf) -and
                    (Test-Path -LiteralPath $normalComplete -PathType Leaf)
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
        $artifactKey = "artifact/$taskSuite/all"
        $tasks.Add([pscustomobject]@{
            Key = $artifactKey
            Priority = 10
            DependsOn = @($prepareKey)
            Ready = $null
            Start = {
                Start-ThreadJob -Name $artifactKey -ScriptBlock {
                    param($Script, $Suite, $Transaction, $CaptureRoot)
                    $ErrorActionPreference = 'Stop'
                    & $Script `
                        -Action All `
                        -Suite $Suite `
                        -Transaction $Transaction `
                        -CaptureRoot $CaptureRoot
                } -ArgumentList (
                    $postprocessScript,
                    $taskSuite,
                    $transaction,
                    $taskCaptureRoot
                )
            }.GetNewClosure()
        })
    }
    foreach ($comparisonVariant in $comparisonVariants) {
        $candidateName = [string]$comparisonVariant.name
        $candidateSuite = Join-Path `
            (Join-Path (Join-Path (Join-Path $transaction 'jobs') $candidateName) 'suites') `
            $context.SuiteRelativePath
        $candidateComplete = Join-Path $candidateSuite 'complete.json'
        $candidateReady = Join-Path (Join-Path $transaction "jobs\$candidateName") 'ready.json'
        $comparisonRoot = Join-Path `
            (Join-Path (Join-Path $transaction 'comparisons') $candidateName) `
            $context.SuiteRelativePath
        $comparisonKey = "compare/$candidateName/$taskSuite"
        $baselineArtifactDirectory = Join-Path `
            $normalSuite `
            'capture\screenshots'
        $candidateArtifactDirectory = Join-Path `
            $candidateSuite `
            'capture\screenshots'
        $comparisonTask = [pscustomobject]@{
            Key = $comparisonKey
            Priority = 100
            Candidate = $candidateName
            Suite = $taskSuite
            Result = Join-Path $comparisonRoot 'result.json'
            DependsOn = @()
            Ready = {
                (Test-Path -LiteralPath $normalReady -PathType Leaf) -and
                    (Test-Path -LiteralPath $candidateReady -PathType Leaf) -and
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
                    $baselineArtifactDirectory,
                    $candidateArtifactDirectory,
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
    Write-Host (
        "E2E pipeline started for $($suites -join ', '): " +
        "build/replay lanes $($replayNames -join ', ') run concurrently."
    ) -ForegroundColor Cyan
    foreach ($variant in $runVariants) {
        $variantName = [string]$variant.name
        $variantJob = Start-Job -Name $variantName -ScriptBlock {
            param(
                $Script,
                $Variant,
                $Transaction,
                $SuiteSelectionJson,
                $ConcurrencyLimit,
                $ConcurrencyPoolRoot,
                $MovesetRange
            )
            $ErrorActionPreference = 'Stop'
            $variantArguments = @{
                Variant = $Variant
                Transaction = $Transaction
                Suite = [string[]]@($SuiteSelectionJson | ConvertFrom-Json)
                ConcurrencyLimit = $ConcurrencyLimit
                ConcurrencyPoolRoot = $ConcurrencyPoolRoot
            }
            if (-not [string]::IsNullOrWhiteSpace($MovesetRange)) {
                $variantArguments.MovesetRange = $MovesetRange
            }
            & $Script @variantArguments
        } -ArgumentList (
            Join-Path $PSScriptRoot 'variant.ps1'
        ), $variantName, $transaction, $suiteSelectionJson, $ConcurrencyLimit, (
            $ConcurrencyPoolRoot
        ), $MovesetRange
        $jobs.Add($variantJob)
    }
    Write-Host (
        "E2E ISO build jobs running: " +
        "$(@($runVariants.name) -join ', ')."
    ) -ForegroundColor Cyan

    $progressState = [pscustomobject]@{
        Next = [DateTime]::UtcNow
    }
    $pollJobs = {
        param([Parameter(Mandatory)][object]$Progress)

        $now = [DateTime]::UtcNow
        if ($now -ge $progressState.Next) {
            $replayCompleted = @(
                $jobs | Where-Object State -EQ 'Completed'
            ).Count
            $status = [Collections.Generic.List[string]]::new()
            $status.Add("replays $replayCompleted/$($jobs.Count) completed")
            $status.Add(
                "tasks $($Progress.TaskCompleted)/$($Progress.TaskTotal) completed, " +
                "$($Progress.TaskRunning) running, $($Progress.TaskWaiting) waiting"
            )
            if ($SupervisedJob.Count -gt 0) {
                $referenceCompleted = @(
                    $SupervisedJob | Where-Object State -EQ 'Completed'
                ).Count
                $status.Add(
                    "references $referenceCompleted/$($SupervisedJob.Count) completed"
                )
            }
            Write-Host "E2E pipeline running: $($status -join '; ')"
            $progressState.Next = $now.AddSeconds(10)
        }
    }.GetNewClosure()
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
                -ComparisonVariant ([string[]]@($comparisonVariants.name))
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
            -ComparisonVariant ([string[]]@($comparisonVariants.name))
        throw (
            'E2E capture comparison failed for case(s): ' +
            ($comparisonFailures -join ', ')
        )
    }

    $replacements = [ordered]@{}
    foreach ($suiteName in $suites) {
        $context = Get-E2eRunContext -Name $suiteName
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
        $screenshotGridStage = Join-Path `
            $suitePublish `
            $script:E2eScreenshotGridDirectory
        $replacements[$context.Capture.ScreenshotGrids] = $screenshotGridStage
        if ($metadata.has_reference -and $metadata.has_current) {
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
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction `
        -AfterPublish {
            $aggregateContexts = @(
                $suites |
                    ForEach-Object { Get-E2eRunContext -Name $_ }
            )
            if ($aggregateContexts.Count -gt 0) {
                Publish-VisualRegressionAggregateViews `
                    -Context $aggregateContexts `
                    -TransactionRoot $transaction
            }
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
        Write-Warning "Failed E2E transaction retained for continuation: $transaction"
        Write-Warning 'Rerun the same e2e command to continue completed suites.'
    }
}
