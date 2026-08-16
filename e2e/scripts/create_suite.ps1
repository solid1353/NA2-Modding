[CmdletBinding(DefaultParameterSetName = 'Suite')]
param(
    [Parameter(Mandatory, ParameterSetName = 'Suite')][string]$Suite,
    [Parameter(Mandatory, ParameterSetName = 'All')][switch]$All,
    [string]$MovesetRange,
    [switch]$NoReference
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$recordingRoot = [IO.Path]::GetFullPath($paths.pcsx2_input_recordings)
$referenceGame = 'nun5'
$suiteRepository = Join-Path $root 'suites'
$captureRepository = Join-Path $root 'captures'

if (-not (Test-Path -LiteralPath $recordingRoot -PathType Container)) {
    throw "Shared recording root does not exist: $recordingRoot"
}

$recordings = @(
    if ($All) {
        Get-ChildItem -LiteralPath $recordingRoot -Filter '*.p2m2' -File -Recurse |
            Where-Object {
                $relative = [IO.Path]::GetRelativePath($recordingRoot, $_.FullName)
                $relativeDirectory = [IO.Path]::GetDirectoryName($relative)
                $segments = $relative.Split([IO.Path]::DirectorySeparatorChar)
                $segments[0] -ine $script:E2eGeneratedSuiteName -and
                    (
                        [string]::IsNullOrEmpty($relativeDirectory) -or
                        @(
                        $relativeDirectory.Split([IO.Path]::DirectorySeparatorChar) |
                            Where-Object {
                                $_.StartsWith('__', [StringComparison]::Ordinal)
                            }
                        ).Count -eq 0
                    )
            } |
            Sort-Object FullName |
            ForEach-Object {
                $relative = [IO.Path]::GetRelativePath($recordingRoot, $_.FullName)
                [pscustomobject]@{
                    Path = $_.FullName
                    Suite = $relative.Substring(0, $relative.Length - 5).Replace('\', '/')
                    Generated = $false
                }
            }
        $generatedContext = Get-VisualRegressionContext -Suite $script:E2eGeneratedSuiteName
        if (Test-VisualRegressionSuiteExists -Context $generatedContext) {
            [pscustomobject]@{
                Path = $null
                Suite = $generatedContext.Suite
                Generated = $true
            }
        }
    }
    else {
        $context = Get-VisualRegressionContext -Suite $Suite
        if ($context.GeneratedNamespace -and -not $context.Generated) {
            throw "The '$($script:E2eGeneratedSuiteName)' E2E suite namespace is generated."
        }
        if ($context.Generated) {
            if (-not (Test-VisualRegressionSuiteExists -Context $context)) {
                throw "Generated E2E suite does not exist: $($context.Suite)"
            }
            [pscustomobject]@{
                Path = $null
                Suite = $context.Suite
                Generated = $true
            }
        }
        else {
            $recordingPath = [IO.Path]::GetFullPath((Join-Path `
                $recordingRoot `
                ($context.SuiteRelativePath + '.p2m2')
            ))
            if (-not (Test-Path -LiteralPath $recordingPath -PathType Leaf)) {
                throw "Input recording does not exist: $recordingPath"
            }
            [pscustomobject]@{
                Path = $recordingPath
                Suite = $context.Suite
                Generated = $false
            }
        }
    }
)
if ($recordings.Count -eq 0) {
    throw "No shared E2E recordings exist under: $recordingRoot"
}
$movesetRangeSpecified = -not [string]::IsNullOrWhiteSpace($MovesetRange)
if ($movesetRangeSpecified -and
    ($All.IsPresent -or $recordings.Count -ne 1 -or -not $recordings[0].Generated)) {
    throw 'MovesetRange requires the movesets suite to be selected by itself.'
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
            Get-ChildItem `
                -LiteralPath (Join-Path $recordingRoot $script:E2eGeneratedSuiteName) `
                -Filter '*.p2m2' `
                -File `
                -ErrorAction SilentlyContinue |
                Select-Object -ExpandProperty FullName
        )
        foreach ($path in $generatedInputs) {
            [ordered]@{
                path = [IO.Path]::GetRelativePath($repository, $path).Replace('\', '/')
                sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
            }
        }
    }
)
$resumeRequest = [ordered]@{
    schema_version = 1
    command = 'create'
    all = [bool]$All
    no_reference = $NoReference.IsPresent
}
if ($movesetRangeSpecified) {
    $resumeRequest['moveset_range'] = $MovesetRange
}
$resumeRequest['suites'] = [string[]]@($recordings.Suite | Sort-Object)
$resumeRequest['inputs'] = [object[]]@($inputIdentity | Sort-Object path)
$resumeKey = $resumeRequest | ConvertTo-Json -Compress -Depth 6
$transaction = New-VisualRegressionTransaction `
    -Root $root `
    -Prefix 'create' `
    -ResumeKey $resumeKey
$definitionStageRoot = Join-Path $transaction 'suite-definitions'
$definitionBackupRoot = Join-Path $transaction 'previous-suite-definitions'
$captureStageRoot = Join-Path $transaction 'capture-history'
$referenceCaptureRoot = Join-Path $transaction 'reference-captures'
$referenceJobs = [Collections.Generic.List[object]]::new()
$installed = [Collections.Generic.List[object]]::new()
$allDefinitionsBackedUp = $false
$allDefinitionsInstalled = $false
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

    $artifactDirectory = Join-Path `
        $CaptureRoot `
        $(if ($Context.Generated) { 'grid-screenshots' } else { 'screenshots' })
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
        $artifactDirectory = if ($context.Generated) {
            $stagedContext.Capture.ScreenshotGrids
        }
        else {
            $stagedContext.Capture.Screenshots
        }
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
    [void](New-Item -ItemType Directory -Path $definitionStageRoot -Force)
    foreach ($recording in $recordings) {
        $context = Get-VisualRegressionContext -Suite $recording.Suite
        $suiteStage = Join-Path $definitionStageRoot ($context.SuiteRelativePath + '.p2m2')
        $suiteBackup = Join-Path $definitionBackupRoot ($context.SuiteRelativePath + '.p2m2')
        $entry = [pscustomobject]@{
            Context = $context
            Backup = $suiteBackup
            Installed = $false
            BackedUp = $false
            Generated = [bool]$recording.Generated
        }
        $installed.Add($entry)

        if ($entry.Generated) {
            continue
        }

        [void](New-Item -ItemType Directory -Path (
            [IO.Path]::GetDirectoryName($suiteStage)
        ) -Force)
        Copy-Item -LiteralPath $recording.Path -Destination $suiteStage -Force
        if (-not $All) {
            [void](New-Item -ItemType Directory -Path @(
                [IO.Path]::GetDirectoryName($context.SuitePath)
                [IO.Path]::GetDirectoryName($context.CaptureRoot)
            ) -Force)
            if (Test-Path -LiteralPath $context.SuitePath -PathType Leaf) {
                [void](New-Item -ItemType Directory -Path (
                    [IO.Path]::GetDirectoryName($suiteBackup)
                ) -Force)
                [IO.File]::Move($context.SuitePath, $suiteBackup)
                $entry.BackedUp = $true
            }
            Copy-Item -LiteralPath $suiteStage -Destination $context.SuitePath -Force
            $entry.Installed = $true
        }
    }

    if ($movesetRangeSpecified) {
        $sourceCapture = $installed[0].Context.CaptureRoot
        $stagedCapture = Join-Path `
            $captureStageRoot `
            $installed[0].Context.SuiteRelativePath
        if (-not (Test-Path -LiteralPath $stagedCapture) -and
            (Test-Path -LiteralPath $sourceCapture -PathType Container)) {
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

    if ($All) {
        if (Test-Path -LiteralPath $suiteRepository) {
            [IO.Directory]::Move($suiteRepository, $definitionBackupRoot)
            $allDefinitionsBackedUp = $true
        }
        [void](New-Item -ItemType Directory -Path $suiteRepository -Force)
        foreach ($item in Get-ChildItem -LiteralPath $definitionStageRoot -Force) {
            Copy-Item `
                -LiteralPath $item.FullName `
                -Destination (Join-Path $suiteRepository $item.Name) `
                -Recurse `
                -Force
        }
        $allDefinitionsInstalled = $true
    }

    if (-not $NoReference.IsPresent) {
        $movesetLaneCount = 2
        $movesetThrottleLimit = [Math]::Max(1, [Math]::Floor(16 / $movesetLaneCount))
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
                    $ThrottleLimit,
                    $MovesetRange
                )
                $ErrorActionPreference = 'Stop'
                $arguments = @{
                    Suite = $Suite
                    Game = $Game
                    CaptureOutputRoot = $CaptureOutputRoot
                }
                if ($Generated) {
                    $arguments.MovesetThrottleLimit = $ThrottleLimit
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
            ), $movesetThrottleLimit, $MovesetRange
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
        Suite = [string[]]@($recordings.Suite)
        CaptureRepository = $captureStageRoot
    }
    if (@($recordings | Where-Object Generated).Count -gt 0) {
        $movesetLaneCount = if ($NoReference.IsPresent) { 1 } else { 2 }
        $runArguments.MovesetThrottleLimit = [Math]::Max(
            1,
            [Math]::Floor(16 / $movesetLaneCount)
        )
        if ($movesetRangeSpecified) {
            $runArguments.MovesetRange = $MovesetRange
        }
    }
    if ($referenceJobs.Count -gt 0) {
        $runArguments.SupervisedJob = [object[]]$referenceJobs
    }
    $runComplete = Join-Path $transaction 'run-complete.json'
    $reuseCompletedRun = (Test-Path -LiteralPath $runComplete -PathType Leaf) -and
        (Test-E2eCreateRunStageComplete)
    if (-not $reuseCompletedRun) {
        & (Join-Path $PSScriptRoot 'run.ps1') @runArguments
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
                -PreserveGeneratedTier:$movesetRangeSpecified
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
        Write-Host "Created or replaced all E2E suites: $($recordings.Count)" -ForegroundColor Green
    }
    else {
        $rangeLabel = if ($movesetRangeSpecified) { " rows $MovesetRange" } else { '' }
        Write-Host (
            "Created or replaced E2E suite: $($recordings[0].Suite)$rangeLabel"
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
                if ($allDefinitionsInstalled) {
                    if (Test-Path -LiteralPath $suiteRepository) {
                        Remove-Item -LiteralPath $suiteRepository -Recurse -Force
                    }
                }
                if ($allDefinitionsBackedUp -and (Test-Path -LiteralPath $definitionBackupRoot)) {
                    [IO.Directory]::Move($definitionBackupRoot, $suiteRepository)
                }
            }
            else {
                for ($index = $installed.Count - 1; $index -ge 0; $index--) {
                    $entry = $installed[$index]
                    $context = $entry.Context
                    if ($entry.Generated) {
                        continue
                    }
                    if ($entry.Installed -and (Test-Path -LiteralPath $context.SuitePath -PathType Leaf)) {
                        Remove-Item -LiteralPath $context.SuitePath -Force
                    }
                    if ($entry.BackedUp -and (Test-Path -LiteralPath $entry.Backup -PathType Leaf)) {
                        [void](New-Item -ItemType Directory -Path (
                            [IO.Path]::GetDirectoryName($context.SuitePath)
                        ) -Force)
                        [IO.File]::Move($entry.Backup, $context.SuitePath)
                    }
                    Remove-VisualRegressionEmptyParents `
                        -Path $context.SuitePath `
                        -Boundary $context.SuiteRepository
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
