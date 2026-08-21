[CmdletBinding()]
param(
    [Parameter(Mandatory)][string[]]$SelectionToken,
    [switch]$NoReference
)

$ErrorActionPreference = 'Stop'
$creationStopwatch = [Diagnostics.Stopwatch]::StartNew()
try {
. (Join-Path $PSScriptRoot 'suite.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$recordingRoot = [IO.Path]::GetFullPath(
    (Join-Path ([string]$paths.pcsx2_input_recordings) 'e2e')
)
$referenceGame = 'nun5'
$captureRepository = Join-Path $root 'captures'

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
            Path = $(if ($context.Generated) { $null } else { $context.SuitePath })
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
$inputIdentity = @(
    foreach ($recording in $recordings) {
        if (-not $recording.Generated) {
            [ordered]@{
                path = $recording.Suite
                sha256 = (Get-FileHash -LiteralPath $recording.Path -Algorithm SHA256).Hash
            }
        }
    }
    if (@($recordings | Where-Object Generated).Count -gt 0) {
        $generatedInputs = @(
            Join-Path ([string]$paths.resources) 'character_data.tsv'
            Join-Path ([string]$paths.resources) 'movesets.tsv'
            foreach ($generatedRecording in @($recordings | Where-Object Generated)) {
                Get-VisualRegressionGeneratedInputPaths `
                    -RecordingRepository $recordingRoot `
                    -Suite $generatedRecording.Suite
            }
        ) | Sort-Object -Unique
        foreach ($path in $generatedInputs) {
            [ordered]@{
                path = [IO.Path]::GetRelativePath($repository, $path).Replace('\', '/')
                sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
            }
        }
    }
)
$resumeRequest = [ordered]@{
    schema_version = 2
    command = 'create'
    all = [bool]$All
    no_reference = $NoReference.IsPresent
    capture_mode = 'screenshots'
}
$resumeRequest['suite_requests'] = [object[]]@(
    $recordings |
        Sort-Object Suite |
        ForEach-Object {
            [ordered]@{
                suite = [string]$_.Suite
                arguments = [string[]]@($_.Arguments)
            }
        }
)
$resumeRequest['inputs'] = [object[]]@($inputIdentity | Sort-Object path)
$resumeKey = $resumeRequest | ConvertTo-Json -Compress -Depth 6
$transaction = New-VisualRegressionTransaction `
    -Root $root `
    -Prefix 'create' `
    -ResumeKey $resumeKey
$captureStageRoot = Join-Path $transaction 'capture-history'
$referenceCaptureRoot = Join-Path $transaction 'reference-captures'
$concurrencyPoolRoot = Join-Path $transaction 'concurrency'
$concurrencyLimit = 16
$referenceJobs = [Collections.Generic.List[object]]::new()
$installed = [Collections.Generic.List[object]]::new()
$allCapturesPublished = $false
$completed = $false

function Write-E2eCreateMarker {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Value
    )

    [void](New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($Path)) -Force)
    $temporary = "$Path.tmp-$([guid]::NewGuid().ToString('N'))"
    try {
        [IO.File]::WriteAllText(
            $temporary,
            (($Value | ConvertTo-Json -Depth 6) + "`n"),
            [Text.UTF8Encoding]::new($false)
        )
        [IO.File]::Move($temporary, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Test-E2eCreateRawCaptureComplete {
    param(
        [Parameter(Mandatory)]$Context,
        [Parameter(Mandatory)][string]$CaptureRoot
    )

    $artifactDirectory = Join-Path $CaptureRoot 'screenshots'
    return @(
        Get-ChildItem `
            -LiteralPath $artifactDirectory `
            -Filter '*.png' `
            -File `
            -ErrorAction SilentlyContinue
    ).Count -gt 0
}

function Test-E2eCreateRunStageComplete {
    foreach ($entry in $installed) {
        $context = $entry.Context
        $stagedContext = Get-VisualRegressionContext `
            -Suite $context.Suite `
            -CaptureRoot (Join-Path $captureStageRoot $context.SuiteRelativePath)
        $artifactDirectory = $stagedContext.Capture.ScreenshotGrids
        if (@(
            Get-ChildItem `
                -LiteralPath $artifactDirectory `
                -Filter '*.png' `
                -File `
                -ErrorAction SilentlyContinue
        ).Count -eq 0) {
            return $false
        }
    }
    return $true
}

try {
    foreach ($recording in $recordings) {
        $context = Get-VisualRegressionContext -Suite $recording.Suite
        $entry = [pscustomobject]@{
            Context = $context
            Generated = [bool]$recording.Generated
            Recording = $recording
        }
        $installed.Add($entry)
    }

    foreach ($entry in @($installed | Where-Object { $_.Recording.PartialGenerated })) {
        $sourceCapture = $entry.Context.CaptureRoot
        $stagedCapture = Join-Path $captureStageRoot $entry.Context.SuiteRelativePath
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
        foreach ($entry in $installed) {
            $context = $entry.Context
            $referenceCapture = Join-Path $referenceCaptureRoot $context.SuiteRelativePath
            $referenceComplete = Join-Path $referenceCapture 'complete.json'
            if ((Test-Path -LiteralPath $referenceComplete -PathType Leaf) -and
                (Test-E2eCreateRawCaptureComplete `
                    -Context $context `
                    -CaptureRoot $referenceCapture)) {
                continue
            }
            $referenceJob = Start-ThreadJob -Name "reference/$($context.Suite)" -ScriptBlock {
                param(
                    $Script,
                    $Suite,
                    $Game,
                    $CaptureOutputRoot,
                    $CompletePath,
                    $Generated,
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
                if ($Generated) {
                    if (-not [string]::IsNullOrWhiteSpace($MovesetRange)) {
                        $arguments.MovesetRange = $MovesetRange
                    }
                }
                & $Script @arguments
                $complete = [ordered]@{
                    schema_version = 1
                    suite = $Suite
                    game = $Game
                    completed_utc = (Get-Date).ToUniversalTime().ToString('O')
                } | ConvertTo-Json
                $temporary = "$CompletePath.tmp-$([guid]::NewGuid().ToString('N'))"
                [IO.File]::WriteAllText(
                    $temporary,
                    $complete + "`n",
                    [Text.UTF8Encoding]::new($false)
                )
                [IO.File]::Move($temporary, $CompletePath, $true)
            } -ArgumentList (
                Join-Path $PSScriptRoot 'reference.ps1'
            ), $context.Suite, $referenceGame, $referenceCapture, $referenceComplete, (
                [bool]$context.Generated
            ), $concurrencyLimit, $concurrencyPoolRoot, $entry.Recording.MovesetRange
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
        Write-E2eCreateMarker -Path $runComplete -Value ([ordered]@{
            schema_version = 1
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
                -Suite ([string[]]@($installed.Context.Suite)) `
                -CapturedRepository $referenceCaptureRoot `
                -CaptureRepository $captureStageRoot `
                -PreserveGeneratedSuite ([string[]]@(
                    $installed |
                        Where-Object { $_.Recording.PartialGenerated } |
                        ForEach-Object { $_.Context.Suite }
                ))
            Write-E2eCreateMarker `
                -Path $referencePublishComplete `
                -Value ([ordered]@{
                    schema_version = 1
                    completed_utc = (Get-Date).ToUniversalTime().ToString('O')
                })
        }
    }

    if ($All) {
        $captureBackupRoot = Join-Path $transaction 'previous-capture-history'
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
            if ($oldCaptureMoveCompleted) {
                foreach ($item in @(Get-ChildItem -LiteralPath $captureRepository -Force)) {
                    if ($script:E2eCaptureRepositoryMetadataNames -ccontains $item.Name) {
                        continue
                    }
                    Remove-Item -LiteralPath $item.FullName -Recurse -Force
                }
            }
            foreach ($item in @(Get-ChildItem -LiteralPath $captureBackupRoot -Force)) {
                Move-Item `
                    -LiteralPath $item.FullName `
                    -Destination (Join-Path $captureRepository $item.Name)
            }
            throw
        }
    }
    else {
        $replacements = [ordered]@{}
        foreach ($entry in $installed) {
            $context = $entry.Context
            $replacements[$context.CaptureRoot] = Join-Path `
                $captureStageRoot `
                $context.SuiteRelativePath
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
        $selectionLabel = @(
            $recordings | ForEach-Object {
                if ($_.Arguments.Count -eq 0) {
                    $_.Suite
                }
                else {
                    "$($_.Suite) $($_.Arguments -join ' ')"
                }
            }
        ) -join ', '
        Write-Host (
            "Regenerated E2E captures: $selectionLabel"
        ) -ForegroundColor Green
    }
}
finally {
    foreach ($job in $referenceJobs) {
        if ($job.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
    if (-not $completed) {
        try {
            if ($All) {
                if ($allCapturesPublished) {
                    foreach ($item in @(Get-ChildItem -LiteralPath $captureRepository -Force)) {
                        if ($script:E2eCaptureRepositoryMetadataNames -ccontains $item.Name) {
                            continue
                        }
                        Remove-Item -LiteralPath $item.FullName -Recurse -Force
                    }
                    $captureBackupRoot = Join-Path $transaction 'previous-capture-history'
                    foreach ($item in @(Get-ChildItem -LiteralPath $captureBackupRoot -Force)) {
                        Move-Item `
                            -LiteralPath $item.FullName `
                            -Destination (Join-Path $captureRepository $item.Name)
                    }
                }
            }
        }
        catch {
            Write-Warning "E2E create rollback failed; retained transaction still contains recovery data: $($_.Exception.Message)"
        }
    }
    if ($completed) {
        Remove-VisualRegressionTransaction -Transaction $transaction -Root $root
    }
    else {
        try {
            Set-VisualRegressionTransactionRetained -Transaction $transaction -Root $root
        }
        catch {
            Write-Warning "Failed to mark the retained E2E create transaction inactive: $($_.Exception.Message)"
        }
        Write-Warning "Failed E2E create transaction retained for continuation: $transaction"
        Write-Warning 'Rerun the same e2e create command to continue completed suites.'
    }
}
}
finally {
    $creationStopwatch.Stop()
    Write-Host (
        'E2E creation elapsed: {0:hh\:mm\:ss\.fff}' -f $creationStopwatch.Elapsed
    )
}
