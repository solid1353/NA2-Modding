[CmdletBinding()]
param(
    [Parameter(Mandatory)][string[]]$SelectionToken,
    [switch]$NoReference
)

$ErrorActionPreference = 'Stop'
$creationStopwatch = [Diagnostics.Stopwatch]::StartNew()
try {
. (Join-Path $PSScriptRoot 'suite.ps1')
$state = Get-VisualRegressionRepositoryState
$root = $state.Root
$recordingRoot = [IO.Path]::GetFullPath($state.RecordingRepository)
$referenceGame = 'nun5'
$captureRepository = $state.CaptureRepository

if (-not (Test-Path -LiteralPath $recordingRoot -PathType Container)) {
    throw "Shared recording root does not exist: $recordingRoot"
}

$selection = Resolve-VisualRegressionSuiteSelection `
    -Token $SelectionToken `
    -RecordingRepository $recordingRoot
$All = [bool]$selection.All
$recordings = @(
    foreach ($request in $selection.Requests) {
        $context = Get-VisualRegressionContext -Suite $request.Suite
        [pscustomobject]@{
            Context = $context
            Suite = $context.Suite
            Arguments = [string[]]@($request.Arguments)
            MovesetRange = $request.MovesetRange
            Generated = [bool]$context.Generated
            PartialGenerated = [bool]$context.Generated -and (
                -not [string]::IsNullOrWhiteSpace([string]$request.MovesetRange) -or
                -not (Test-VisualRegressionGeneratedSuiteRoot -Suite $context.Suite)
            )
        }
    }
)
if ($recordings.Count -eq 0) {
    throw "No shared E2E recordings exist under: $recordingRoot"
}
$resumeKey = Get-VisualRegressionResumeKey `
    -Request ([ordered]@{
        command = 'create'
        all = [bool]$All
        no_reference = $NoReference.IsPresent
        capture_mode = 'screenshots'
    }) `
    -SuiteRequest $recordings `
    -OrdinaryInput @(
        foreach ($recording in @($recordings | Where-Object { -not $_.Generated })) {
            [ordered]@{
                path = $recording.Suite
                sha256 = (Get-FileHash `
                    -LiteralPath $recording.Context.SuitePath `
                    -Algorithm SHA256).Hash
            }
        }
    )
$transaction = New-VisualRegressionTransaction `
    -Root $root `
    -Prefix 'create' `
    -ResumeKey $resumeKey
$captureStageRoot = Join-Path $transaction 'capture-history'
$referenceCaptureRoot = Join-Path $transaction 'reference-captures'
$captureBackupRoot = Join-Path $transaction 'previous-capture-history'
$concurrencyPoolRoot = Join-Path $transaction 'concurrency'
$concurrencyLimit = 16
$referenceJobs = [Collections.Generic.List[object]]::new()
$allCapturesPublished = $false
$completed = $false

function Restore-E2eCaptureHistory {
    param([Parameter(Mandatory)][bool]$ClearPublished)

    if ($ClearPublished) {
        Clear-VisualRegressionCaptureRepository -CaptureRepository $captureRepository
    }
    foreach ($item in @(Get-ChildItem -LiteralPath $captureBackupRoot -Force)) {
        Move-Item `
            -LiteralPath $item.FullName `
            -Destination (Join-Path $captureRepository $item.Name)
    }
}

function Test-E2eCreateRunStageComplete {
    foreach ($recording in $recordings) {
        $stagedGrids = Join-Path `
            (Join-Path $captureStageRoot $recording.Context.SuiteRelativePath) `
            $script:E2eScreenshotGridDirectory
        if ((Get-VisualRegressionPngCount -Directory $stagedGrids) -eq 0) {
            return $false
        }
    }
    return $true
}

try {
    foreach ($recording in @($recordings | Where-Object PartialGenerated)) {
        $sourceCapture = $recording.Context.CaptureRoot
        $stagedCapture = Join-Path $captureStageRoot $recording.Context.SuiteRelativePath
        if (-not (Test-Path -LiteralPath $stagedCapture)) {
            if (Test-Path -LiteralPath $sourceCapture -PathType Container) {
                [void](New-Item `
                    -ItemType Directory `
                    -Path ([IO.Path]::GetDirectoryName($stagedCapture)) `
                    -Force)
                Copy-Item `
                    -LiteralPath $sourceCapture `
                    -Destination $stagedCapture `
                    -Recurse `
                    -Force
            }
        }
    }

    if (-not $NoReference.IsPresent) {
        foreach ($recording in $recordings) {
            $context = $recording.Context
            $referenceCapture = Join-Path $referenceCaptureRoot $context.SuiteRelativePath
            $referenceArtifacts = if ($context.Generated) {
                Join-Path $referenceCapture 'screenshots'
            }
            else { $referenceCapture }
            if ((Test-Path -LiteralPath (Join-Path $referenceCapture 'complete.json') -PathType Leaf) -and
                (Get-VisualRegressionPngCount -Directory $referenceArtifacts) -gt 0) {
                continue
            }
            $referenceJob = Start-ThreadJob -Name "reference/$($context.Suite)" -ScriptBlock {
                param(
                    $Script,
                    $SuiteScript,
                    $Suite,
                    $Game,
                    $CaptureOutputRoot,
                    $ConcurrencyLimit,
                    $ConcurrencyPoolRoot,
                    $MovesetRange
                )
                $ErrorActionPreference = 'Stop'
                $arguments = @{
                    Suite = $Suite
                    Game = $Game
                    CaptureOutputRoot = $CaptureOutputRoot
                    ConcurrencyLimit = $ConcurrencyLimit
                    ConcurrencyPoolRoot = $ConcurrencyPoolRoot
                }
                if (-not [string]::IsNullOrWhiteSpace($MovesetRange)) {
                    $arguments.MovesetRange = $MovesetRange
                }
                & $Script @arguments
                . $SuiteScript
                Write-VisualRegressionJson `
                    -Path (Join-Path $CaptureOutputRoot 'complete.json') `
                    -Value ([ordered]@{
                        suite = $Suite
                        game = $Game
                        completed_utc = (Get-Date).ToUniversalTime().ToString('O')
                    })
            } -ArgumentList (
                Join-Path $PSScriptRoot 'reference.ps1'
            ), (
                Join-Path $PSScriptRoot 'suite.ps1'
            ), $context.Suite, $referenceGame, $referenceCapture, (
                $concurrencyLimit
            ), $concurrencyPoolRoot, $recording.MovesetRange
            $referenceJobs.Add($referenceJob)
        }
        if ($referenceJobs.Count -gt 0) {
            Write-Host (
                "Reference replays and the E2E test pipeline started concurrently for " +
                "$($referenceJobs.Count) unfinished suite(s)."
            ) -ForegroundColor Cyan
        }
    }

    $runArguments = @{
        SelectionToken = [string[]]$SelectionToken
        CaptureRepository = $captureStageRoot
        ConcurrencyLimit = $concurrencyLimit
        ConcurrencyPoolRoot = $concurrencyPoolRoot
    }
    if ($referenceJobs.Count -gt 0) {
        $runArguments.SupervisedJob = [object[]]$referenceJobs
    }
    $runComplete = Join-Path $transaction 'run-complete.json'
    $reuseCompletedRun = (Test-Path -LiteralPath $runComplete -PathType Leaf) -and
        (Test-E2eCreateRunStageComplete)
    if (-not $reuseCompletedRun) {
        $null = & (Join-Path $PSScriptRoot 'run.ps1') @runArguments
        Write-VisualRegressionJson -Path $runComplete -Value ([ordered]@{
            suites = [string[]]@($recordings.Suite)
            completed_utc = (Get-Date).ToUniversalTime().ToString('O')
        })
    }
    else {
        Write-Host 'Continuing with completed NA228 suite captures.' -ForegroundColor Cyan
    }

    if (-not $NoReference.IsPresent) {
        if ($referenceJobs.Count -gt 0) {
            Wait-VisualRegressionJobs `
                -Job ([object[]]$referenceJobs) `
                -FailurePrefix 'Reference replay job'
        }
        $referencePublishComplete = Join-Path $transaction 'reference-publish-complete.json'
        if (-not (Test-Path -LiteralPath $referencePublishComplete -PathType Leaf)) {
            & (Join-Path $PSScriptRoot 'publish_references.ps1') `
                -Suite ([string[]]@($recordings.Suite)) `
                -CapturedRepository $referenceCaptureRoot `
                -CaptureRepository $captureStageRoot `
                -PreserveGeneratedSuite ([string[]]@(
                    $recordings | Where-Object PartialGenerated | ForEach-Object Suite
                ))
            Write-VisualRegressionJson `
                -Path $referencePublishComplete `
                -Value ([ordered]@{
                    completed_utc = (Get-Date).ToUniversalTime().ToString('O')
                })
        }
    }

    if ($All) {
        [void](New-Item -ItemType Directory -Path `
            $captureRepository, `
            $captureBackupRoot `
            -Force)
        $oldCaptureMoveCompleted = $false
        try {
            foreach ($item in @(Get-ChildItem -LiteralPath $captureRepository -Force)) {
                if ($script:E2eCaptureRepositoryMetadataNames -ccontains $item.Name) {
                    continue
                }
                Move-Item `
                    -LiteralPath $item.FullName `
                    -Destination (Join-Path $captureBackupRoot $item.Name)
            }
            $oldCaptureMoveCompleted = $true
            foreach ($item in @(Get-ChildItem -LiteralPath $captureStageRoot -Force)) {
                Copy-Item `
                    -LiteralPath $item.FullName `
                    -Destination (Join-Path $captureRepository $item.Name) `
                    -Recurse `
                    -Force
            }
            $allCapturesPublished = $true
        }
        catch {
            Restore-E2eCaptureHistory -ClearPublished $oldCaptureMoveCompleted
            throw
        }
    }
    else {
        $replacements = [ordered]@{}
        foreach ($recording in $recordings) {
            $replacements[$recording.Context.CaptureRoot] = Join-Path `
                $captureStageRoot `
                $recording.Context.SuiteRelativePath
        }
        Publish-VisualRegressionTransaction `
            -Replacements $replacements `
            -TransactionRoot $transaction
    }
    $completed = $true
    if ($All) {
        Write-Host "Regenerated all E2E capture suites: $($recordings.Count)" -ForegroundColor Green
    }
    else {
        Write-Host (
            "Regenerated E2E captures: $(Get-VisualRegressionSelectionLabel -Request $recordings)"
        ) -ForegroundColor Green
    }
}
finally {
    Remove-VisualRegressionJobs -Job $referenceJobs
    if (-not $completed -and $All -and $allCapturesPublished) {
        try {
            Restore-E2eCaptureHistory -ClearPublished $true
        }
        catch {
            Write-Warning "E2E create rollback failed; retained transaction still contains recovery data: $($_.Exception.Message)"
        }
    }
    Complete-VisualRegressionTransaction `
        -Transaction $transaction `
        -Root $root `
        -Succeeded $completed `
        -Command 'E2E create'
}
}
finally {
    $creationStopwatch.Stop()
    Write-Host (
        'E2E creation elapsed: {0:hh\:mm\:ss\.fff}' -f $creationStopwatch.Elapsed
    )
}
