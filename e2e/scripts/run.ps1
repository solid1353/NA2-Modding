[CmdletBinding()]
param(
    [Parameter(Mandatory)][string[]]$SelectionToken,
    [string]$CaptureRepository,
    [object[]]$SupervisedJob = @(),
    [string]$ConcurrencyPoolRoot,
    [ValidateRange(1, 64)]
    [int]$ConcurrencyLimit = 16
)

$ErrorActionPreference = 'Stop'
$runStopwatch = [Diagnostics.Stopwatch]::StartNew()
try {
. (Join-Path $PSScriptRoot 'suite.ps1')
$state = Get-VisualRegressionRepositoryState
$root = $state.Root
$selection = Resolve-VisualRegressionSuiteSelection `
    -Token $SelectionToken `
    -RecordingRepository $state.RecordingRepository
$suiteRequests = [object[]]@($selection.Requests)
$suites = [string[]]@($suiteRequests.Suite)
$reportRegression = [string]::IsNullOrWhiteSpace($CaptureRepository)
if ($reportRegression) {
    Assert-VisualRegressionCaptureGitBaseline `
        -CaptureRepository $state.CaptureRepository
}
$contexts = [object[]]@(
    foreach ($request in $suiteRequests) {
        $context = Get-VisualRegressionContext -Suite $request.Suite
        if ([string]::IsNullOrWhiteSpace($CaptureRepository)) {
            $context
        }
        else {
            Get-VisualRegressionContext `
                -Suite $request.Suite `
                -CaptureRoot (Join-Path $CaptureRepository $context.SuiteRelativePath)
        }
    }
)
$jobName = 'current'

$resumeKey = Get-VisualRegressionResumeKey `
    -Request ([ordered]@{
        command = 'run'
        capture_mode = 'screenshots'
    }) `
    -SuiteRequest $suiteRequests `
    -OrdinaryInput @(
        foreach ($context in @($contexts | Where-Object { -not $_.Generated })) {
            [ordered]@{
                path = [IO.Path]::GetRelativePath(
                    $state.Repository,
                    $context.SuitePath
                ).Replace('\', '/')
                sha256 = (Get-FileHash -LiteralPath $context.SuitePath -Algorithm SHA256).Hash
            }
        }
    )
$transaction = New-VisualRegressionTransaction `
    -Root $root `
    -Prefix 'run' `
    -ResumeKey $resumeKey
if ([string]::IsNullOrWhiteSpace($ConcurrencyPoolRoot)) {
    $ConcurrencyPoolRoot = Join-Path $transaction 'concurrency'
}
else {
    $ConcurrencyPoolRoot = [IO.Path]::GetFullPath($ConcurrencyPoolRoot)
}
if (Test-VisualRegressionTransactionResumed -Transaction $transaction) {
    Move-VisualRegressionTransactionItemsToAttempt `
        -Transaction $transaction `
        -RelativePath @(
            'publish',
            'stages',
            '.backups',
            "jobs\$jobName\ready.json",
            "jobs\$jobName\result.json"
        ) `
        -Label 'resume' |
        Out-Null
}
$jobs = [Collections.Generic.List[object]]::new()
$tasks = [Collections.Generic.List[object]]::new()
$currentReady = Join-Path (Join-Path $transaction "jobs\$jobName") 'ready.json'
for ($index = 0; $index -lt $suiteRequests.Count; $index++) {
    $context = $contexts[$index]
    $currentSuite = Join-Path `
        (Join-Path (Join-Path (Join-Path $transaction 'jobs') $jobName) 'suites') `
        $context.SuiteRelativePath
    $currentComplete = Join-Path $currentSuite 'complete.json'
    foreach ($task in @(
        New-VisualRegressionArtifactTasks `
            -Context $context `
            -Transaction $transaction `
            -CapturedRoot (Join-Path $currentSuite 'capture') `
            -CapturedTier Current `
            -PreserveCapturedTier (
                -not [string]::IsNullOrWhiteSpace(
                    [string]$suiteRequests[$index].MovesetRange
                ) -or
                -not (Test-VisualRegressionGeneratedSuiteRoot -Suite $context.Suite)
            ) `
            -Ready ({
                (Test-Path -LiteralPath $currentReady -PathType Leaf) -and
                    (Test-Path -LiteralPath $currentComplete -PathType Leaf)
            }.GetNewClosure())
    )) {
        $tasks.Add($task)
    }
}
$pipelineCompleted = $false
try {
    $suiteRequestJson = ConvertTo-Json `
        -Compress `
        -Depth 4 `
        -InputObject ([object[]]@($suiteRequests | ForEach-Object {
            [ordered]@{
                Suite = [string]$_.Suite
                Arguments = [string[]]@($_.Arguments)
                MovesetRange = $_.MovesetRange
                Generated = [bool]$_.Generated
                GeneratedFamily = $_.GeneratedFamily
            }
        }))
    Write-Host (
        "E2E pipeline started for $($suites -join ', '): " +
        'build, replay, and post-processing run concurrently.'
    ) -ForegroundColor Cyan
    $currentJob = Start-Job -Name $jobName -ScriptBlock {
        param(
            $Script,
            $Transaction,
            $SuiteRequestJson,
            $ConcurrencyLimit,
            $ConcurrencyPoolRoot
        )
        $ErrorActionPreference = 'Stop'
        & $Script `
            -Transaction $Transaction `
            -SuiteRequestJson $SuiteRequestJson `
            -ConcurrencyLimit $ConcurrencyLimit `
            -ConcurrencyPoolRoot $ConcurrencyPoolRoot
    } -ArgumentList (
        Join-Path $PSScriptRoot 'current.ps1'
    ), $transaction, $suiteRequestJson, $ConcurrencyLimit, $ConcurrencyPoolRoot
    $jobs.Add($currentJob)
    Write-Host 'E2E ISO build job running.' -ForegroundColor Cyan

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
    Invoke-VisualRegressionTaskGraph `
        -Task ([object[]]$tasks) `
        -SupervisedJob ([object[]](@($jobs) + @($SupervisedJob))) `
        -FailurePrefix 'E2E pipeline task' `
        -OnPoll $pollJobs

    Publish-VisualRegressionArtifacts -Context $contexts -Transaction $transaction
    if ($reportRegression) {
        $regression = Get-VisualRegressionCaptureRegression `
            -Request $suiteRequests `
            -CaptureRepository $state.CaptureRepository
        Write-Host "E2E completed: $($regression.Suites) suite(s)." -ForegroundColor Green
        if ($regression.Regression -ceq 'changed') {
            $fileCount = $regression.Added + $regression.Modified + $regression.Deleted
            Write-Host (
                "Regression: CHANGED - $($regression.ChangedSuites)/" +
                "$($regression.Suites) suites, $fileCount files."
            ) -ForegroundColor Yellow
            $labelWidth = [Math]::Max(
                5,
                [int](($regression.SuiteChanges |
                    ForEach-Object { $_.Suite.Length } |
                    Measure-Object -Maximum).Maximum)
            )
            foreach ($suiteChange in $regression.SuiteChanges) {
                $parts = @(
                    if ($suiteChange.Modified -gt 0) {
                        "$($suiteChange.Modified) modified"
                    }
                    if ($suiteChange.Added -gt 0) {
                        "$($suiteChange.Added) added"
                    }
                    if ($suiteChange.Deleted -gt 0) {
                        "$($suiteChange.Deleted) deleted"
                    }
                )
                Write-Host (
                    ("  {0,-$labelWidth}  {1}" -f $suiteChange.Suite, ($parts -join ', '))
                )
            }
            Write-Host (
                ("  {0,-$labelWidth}  {1} modified, {2} added, {3} deleted" -f
                    'total',
                    $regression.Modified,
                    $regression.Added,
                    $regression.Deleted)
            )
        }
        else {
            Write-Host (
                'Regression: UNCHANGED - selected captures match the accepted Git baseline.'
            ) -ForegroundColor Green
        }
        [pscustomobject]@{
            Execution = 'completed'
            Regression = $regression.Regression
            Suites = $regression.Suites
            ChangedSuites = $regression.ChangedSuites
            Added = $regression.Added
            Modified = $regression.Modified
            Deleted = $regression.Deleted
        }
    }
    else {
        Write-Host "E2E execution completed: $($suites.Count) suite(s)." -ForegroundColor Green
    }
    $pipelineCompleted = $true
}
finally {
    Remove-VisualRegressionJobs -Job $jobs
    Complete-VisualRegressionTransaction `
        -Transaction $transaction `
        -Root $root `
        -Succeeded $pipelineCompleted `
        -Command 'E2E'
}
}
finally {
    $runStopwatch.Stop()
    Write-Host (
        'E2E run elapsed: {0:hh\:mm\:ss\.fff}' -f $runStopwatch.Elapsed
    )
}
