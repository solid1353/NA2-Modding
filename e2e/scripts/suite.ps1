$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'config.ps1')
$script:E2eCaptureTiers = [ordered]@{
    Reference = 'reference'
    Current = 'current'
}
$script:E2eGeneratedMovesetSuiteName = 'movesets'
$script:E2eGeneratedIdleSuiteName = 'characters/idle'
$script:E2eGeneratedSuiteNames = @(
    $script:E2eGeneratedMovesetSuiteName,
    $script:E2eGeneratedIdleSuiteName
)
$script:E2eScreenshotKinds = [ordered]@{
    Reference = [pscustomobject]@{ Order = 'a'; Label = 'reference' }
    Current = [pscustomobject]@{ Order = 'b'; Label = 'current' }
    Blend = [pscustomobject]@{ Order = 'c'; Label = 'blend' }
    Diff = [pscustomobject]@{ Order = 'd'; Label = 'diff' }
    Pair = [pscustomobject]@{ Order = 'e'; Label = 'pair' }
}
$script:E2eAllGridDirectory = 'all'
$script:E2eCaptureRepositoryMetadataNames = @('.git', '.gitattributes', '.gitignore')
$script:E2eScreenshotGridDirectory = 'screenshots'
$script:E2ePairGridDirectory = 'pairs'
$script:E2eBlendGridDirectory = 'blends'
$script:E2eDiffGridDirectory = 'diffs'
$script:E2eStableCaptureDirectories = @(
    $script:E2eScreenshotGridDirectory,
    $script:E2ePairGridDirectory,
    $script:E2eBlendGridDirectory,
    $script:E2eDiffGridDirectory
)

function Test-VisualRegressionGeneratedSuite {
    param([Parameter(Mandatory)][string]$Suite)

    $normalized = $Suite.Replace('\', '/').TrimEnd('/')
    return (
        $normalized -imatch '^movesets(?:/(?:base|specials))?$' -or
        $normalized -ieq $script:E2eGeneratedIdleSuiteName
    )
}

function Get-VisualRegressionGeneratedSuiteFamily {
    param([Parameter(Mandatory)][string]$Suite)

    $normalized = $Suite.Replace('\', '/').TrimEnd('/')
    if (-not (Test-VisualRegressionGeneratedSuite -Suite $normalized)) {
        return $null
    }
    if ($normalized -ieq $script:E2eGeneratedIdleSuiteName) {
        return 'idle'
    }
    if ($normalized -ieq $script:E2eGeneratedMovesetSuiteName) {
        return 'movesets'
    }
    return @($normalized.Split('/'))[-1].ToLowerInvariant()
}

function Test-VisualRegressionGeneratedSuiteRoot {
    param([Parameter(Mandatory)][string]$Suite)

    $normalized = $Suite.Replace('\', '/').TrimEnd('/')
    return $script:E2eGeneratedSuiteNames -icontains $normalized
}

function Resolve-VisualRegressionMovesetRange {
    param(
        [Parameter(Mandatory)][string]$Range,
        [Parameter(Mandatory)][ValidateRange(2, [int]::MaxValue)]
        [int]$LastAvailableRow
    )

    $rangeMatch = [regex]::Match($Range, '^(\d+)(?:-(\d+))?$')
    if (-not $rangeMatch.Success) {
        throw (
            'Moveset range must be one character_data.tsv row or an inclusive ' +
            'row range, for example 8 or 8-18.'
        )
    }
    $firstRow = 0
    $lastRow = 0
    if (-not [int]::TryParse($rangeMatch.Groups[1].Value, [ref]$firstRow)) {
        throw "Moveset range is outside the supported integer range: $Range"
    }
    if ($rangeMatch.Groups[2].Success) {
        if (-not [int]::TryParse($rangeMatch.Groups[2].Value, [ref]$lastRow)) {
            throw "Moveset range is outside the supported integer range: $Range"
        }
    }
    else {
        $lastRow = $firstRow
    }
    if ($firstRow -gt $lastRow) {
        throw "Moveset range starts after it ends: $Range"
    }
    if ($firstRow -lt 2 -or $lastRow -gt $LastAvailableRow) {
        throw (
            "Moveset range $Range must stay within character_data.tsv rows " +
            "2-$LastAvailableRow."
        )
    }

    [pscustomobject]@{
        FirstRow = $firstRow
        LastRow = $lastRow
        Value = $(if ($firstRow -eq $lastRow) {
            [string]$firstRow
        }
        else {
            "$firstRow-$lastRow"
        })
    }
}

function Get-VisualRegressionIdlePagePlans {
    param(
        [Parameter(Mandatory)][ValidateRange(2, [int]::MaxValue)]
        [int]$FirstRow,
        [Parameter(Mandatory)][ValidateRange(2, [int]::MaxValue)]
        [int]$LastRow,
        [Parameter(Mandatory)][ValidateRange(1, [int]::MaxValue)]
        [int]$CharacterCount
    )

    if ($FirstRow -gt $LastRow -or $LastRow -gt $CharacterCount + 1) {
        throw 'Idle page rows must be an ascending range within character_data.tsv.'
    }
    [int]$firstPage = [Math]::Floor(($FirstRow - 2) / 6) + 1
    [int]$lastPage = [Math]::Floor(($LastRow - 2) / 6) + 1
    for ($page = $firstPage; $page -le $lastPage; $page++) {
        [pscustomobject]@{
            Page = [int]$page
            FirstCharacterIndex = [int](($page - 1) * 6)
            LastCharacterIndex = [int][Math]::Min(
                ($page * 6) - 1,
                $CharacterCount - 1
            )
        }
    }
}

function Test-VisualRegressionGeneratedSuiteNamespace {
    param([Parameter(Mandatory)][string]$Suite)

    $normalized = $Suite.Replace('\', '/').TrimEnd('/')
    return (
        $normalized -ieq $script:E2eGeneratedIdleSuiteName -or
        $normalized.StartsWith(
            $script:E2eGeneratedIdleSuiteName + '/',
            [StringComparison]::OrdinalIgnoreCase
        ) -or
        $normalized -ieq $script:E2eGeneratedMovesetSuiteName -or
        $normalized.StartsWith(
            $script:E2eGeneratedMovesetSuiteName + '/',
            [StringComparison]::OrdinalIgnoreCase
        )
    )
}

function Get-VisualRegressionGeneratedSuiteScript {
    param([Parameter(Mandatory)][string]$Root)

    Join-Path (Join-Path $Root 'scripts') 'movesets.ps1'
}

function Get-VisualRegressionPracticeConfiguration {
    param(
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string[]]$MovesetCaseId,
        [Parameter(Mandatory)][string[]]$Game
    )

    . (Join-Path $Repository 'scripts\lib\paths.ps1')
    $paths = Get-Na2Paths -ManifestPath (Join-Path $Repository 'paths.json')
    . (Join-Path ([string]$paths.scripts) 'na228\launch_profile.ps1')
    $profile = Resolve-Na2LaunchProfile -Name 'practice' -Paths $paths
    foreach ($caseId in $MovesetCaseId) {
        Invoke-Na2LaunchProfile `
            -Profile $profile `
            -Arguments @($caseId) `
            -Games $Game `
            -ProjectRoot $Repository
    }
}

function Get-VisualRegressionGeneratedInputPaths {
    param(
        [Parameter(Mandatory)][string]$RecordingRepository,
        [Parameter(Mandatory)][string]$Suite
    )

    $family = Get-VisualRegressionGeneratedSuiteFamily -Suite $Suite
    [string[]]@(
        if ($family -cin @('movesets', 'base')) {
            Join-Path $RecordingRepository 'movesets\base.p2m2'
        }
        if ($family -cin @('movesets', 'specials')) {
            Join-Path $RecordingRepository 'movesets\specials.p2m2'
        }
        if ($family -ceq 'idle') {
            Join-Path $RecordingRepository 'characters\idle.p2m2'
        }
    )
}

function Test-VisualRegressionSuiteExists {
    param([Parameter(Mandatory)][object]$Context)

    if ($Context.Generated) {
        if (-not (Test-Path -LiteralPath $Context.GeneratedScript -PathType Leaf)) {
            return $false
        }
        return @(
            Get-VisualRegressionGeneratedInputPaths `
                -RecordingRepository $Context.RecordingRepository `
                -Suite $Context.Suite |
                Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) }
        ).Count -eq 0
    }
    if ($Context.GeneratedNamespace) {
        return $false
    }
    Test-Path -LiteralPath $Context.SuitePath -PathType Leaf
}

function Wait-VisualRegressionJobs {
    param(
        [Parameter(Mandatory)][object[]]$Job,
        [Parameter(Mandatory)][string]$FailurePrefix,
        [scriptblock]$OnPoll
    )

    $activeStates = @('NotStarted', 'Running')
    $terminalStates = @('Completed', 'Failed', 'Stopped')
    $receivedFailure = @{}
    $receiveOutput = {
        param([Parameter(Mandatory)][object]$CurrentJob)

        $receivedErrors = @()
        Receive-Job `
            -Job $CurrentJob `
            -ErrorAction SilentlyContinue `
            -ErrorVariable +receivedErrors |
            ForEach-Object { Write-Output $_ }
        foreach ($receivedError in $receivedErrors) {
            $receivedFailure[$CurrentJob.Id] = [string]$receivedError
            Write-Error -ErrorRecord $receivedError -ErrorAction Continue
        }
    }
    while ($true) {
        foreach ($currentJob in $Job) {
            . $receiveOutput -CurrentJob $currentJob
        }

        $failedJob = @(
            $Job | Where-Object State -NotIn @(
                'NotStarted',
                'Running',
                'Completed'
            )
        ) | Select-Object -First 1
        if ($null -ne $failedJob) {
            $jobsToStop = @($Job | Where-Object State -NotIn $terminalStates)
            foreach ($activeJob in $jobsToStop) {
                Stop-Job -Job $activeJob -ErrorAction SilentlyContinue
            }
            foreach ($activeJob in $jobsToStop) {
                Wait-Job -Job $activeJob -Timeout 5 | Out-Null
            }
            foreach ($currentJob in $Job) {
                . $receiveOutput -CurrentJob $currentJob
            }
            $reasonMessage = if ($receivedFailure.ContainsKey($failedJob.Id)) {
                $receivedFailure[$failedJob.Id]
            }
            elseif ($null -ne $failedJob.JobStateInfo.Reason) {
                $failedJob.JobStateInfo.Reason.Message
            }
            else {
                'unknown failure'
            }
            throw "$FailurePrefix $($failedJob.Name) failed: $reasonMessage"
        }

        if (@($Job | Where-Object State -In $activeStates).Count -eq 0) {
            break
        }
        if ($null -ne $OnPoll) {
            . $OnPoll
        }
        Start-Sleep -Milliseconds 200
    }

    foreach ($currentJob in $Job) {
        . $receiveOutput -CurrentJob $currentJob
    }
}

function Get-VisualRegressionTaskThrottleLimit {
    $logicalProcessors = [Environment]::ProcessorCount
    return [Math]::Max(1, [Math]::Min(8, $logicalProcessors))
}

function Invoke-VisualRegressionFileOperation {
    param(
        [Parameter(Mandatory)][scriptblock]$Operation,
        [Parameter(Mandatory)][string]$Description,
        [ValidateRange(1, 100)][int]$AttemptCount = 50,
        [ValidateRange(1, 1000)][int]$RetryDelayMilliseconds = 100
    )

    for ($attempt = 1; $attempt -le $AttemptCount; $attempt++) {
        try {
            & $Operation
            return
        }
        catch [IO.IOException], [UnauthorizedAccessException] {
            if ($attempt -eq $AttemptCount) {
                throw "$Description failed after $AttemptCount attempts: $($_.Exception.Message)"
            }
            Start-Sleep -Milliseconds $RetryDelayMilliseconds
        }
    }
}

function Invoke-VisualRegressionTaskGraph {
    param(
        [Parameter(Mandatory)][object[]]$Task,
        [object[]]$SupervisedJob = @(),
        [ValidateRange(1, 64)]
        [int]$ThrottleLimit = (Get-VisualRegressionTaskThrottleLimit),
        [string]$FailurePrefix = 'E2E task',
        [scriptblock]$OnPoll
    )

    $pending = [ordered]@{}
    foreach ($currentTask in $Task) {
        $key = [string]$currentTask.Key
        if ([string]::IsNullOrWhiteSpace($key)) {
            throw 'An E2E task has no key.'
        }
        if ($pending.Contains($key)) {
            throw "Duplicate E2E task key: $key"
        }
        $pending[$key] = $currentTask
    }

    $completed = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $running = [ordered]@{}
    $taskJobs = [Collections.Generic.List[object]]::new()
    $receivedFailure = @{}
    $activeStates = @('NotStarted', 'Running')
    $terminalStates = @('Completed', 'Failed', 'Stopped')
    $receiveOutput = {
        param([Parameter(Mandatory)][object]$CurrentJob)

        $receivedErrors = @()
        Receive-Job `
            -Job $CurrentJob `
            -ErrorAction SilentlyContinue `
            -ErrorVariable +receivedErrors |
            ForEach-Object { Write-Output $_ }
        foreach ($receivedError in $receivedErrors) {
            $receivedFailure[$CurrentJob.Id] = [string]$receivedError
            Write-Error -ErrorRecord $receivedError -ErrorAction Continue
        }
    }
    $stopAll = {
        foreach ($job in @($SupervisedJob) + @($taskJobs)) {
            if ($job.State -notin $terminalStates) {
                Stop-Job -Job $job -ErrorAction SilentlyContinue
                Wait-Job -Job $job -Timeout 5 | Out-Null
            }
        }
    }

    try {
        while ($true) {
            $allJobs = @($SupervisedJob) + @($taskJobs)
            foreach ($job in $allJobs) {
                . $receiveOutput -CurrentJob $job
            }

            $failedJob = @(
                $allJobs | Where-Object State -NotIn @(
                    'NotStarted',
                    'Running',
                    'Completed'
                )
            ) | Select-Object -First 1
            if ($null -ne $failedJob) {
                & $stopAll
                foreach ($job in $allJobs) {
                    . $receiveOutput -CurrentJob $job
                }
                $reasonMessage = if ($receivedFailure.ContainsKey($failedJob.Id)) {
                    $receivedFailure[$failedJob.Id]
                }
                elseif ($null -ne $failedJob.JobStateInfo.Reason) {
                    $failedJob.JobStateInfo.Reason.Message
                }
                else {
                    'unknown failure'
                }
                throw "$FailurePrefix $($failedJob.Name) failed: $reasonMessage"
            }

            foreach ($key in @($running.Keys)) {
                if ($running[$key].State -eq 'Completed') {
                    [void]$completed.Add($key)
                    $running.Remove($key)
                }
            }

            $startedTask = $true
            while ($running.Count -lt $ThrottleLimit -and $startedTask) {
                $startedTask = $false
                foreach ($key in @(
                    $pending.Keys |
                        Sort-Object {
                            $taskToOrder = $pending[$_]
                            if ($taskToOrder.PSObject.Properties.Name -contains 'Priority') {
                                [int]$taskToOrder.Priority
                            }
                            else {
                                0
                            }
                        } -Descending
                )) {
                    $currentTask = $pending[$key]
                    $dependencies = @($currentTask.DependsOn)
                    if (@(
                        $dependencies | Where-Object { -not $completed.Contains([string]$_) }
                    ).Count -gt 0) {
                        continue
                    }
                    if ($null -ne $currentTask.Ready -and -not (& $currentTask.Ready)) {
                        continue
                    }
                    $job = & $currentTask.Start
                    if ($null -eq $job -or $job -isnot [Management.Automation.Job]) {
                        throw "E2E task $key did not start a PowerShell job."
                    }
                    $running[$key] = $job
                    $taskJobs.Add($job)
                    $pending.Remove($key)
                    $startedTask = $true
                    if ($running.Count -ge $ThrottleLimit) { break }
                }
            }

            $supervisedActive = @(
                $SupervisedJob | Where-Object State -In $activeStates
            ).Count
            if ($supervisedActive -eq 0 -and $pending.Count -eq 0 -and $running.Count -eq 0) {
                break
            }
            if (
                $supervisedActive -eq 0 -and
                $running.Count -eq 0 -and
                -not $startedTask -and
                $pending.Count -gt 0
            ) {
                throw (
                    'E2E task graph has unresolved dependencies or inputs: ' +
                    (@($pending.Keys) -join ', ')
                )
            }
            if ($null -ne $OnPoll) {
                & $OnPoll ([pscustomobject]@{
                    TaskTotal = $Task.Count
                    TaskCompleted = $completed.Count
                    TaskRunning = $running.Count
                    TaskWaiting = $pending.Count
                    SupervisedActive = $supervisedActive
                })
            }
            Start-Sleep -Milliseconds 200
        }
    }
    catch {
        & $stopAll
        throw
    }
    finally {
        foreach ($job in $taskJobs) {
            if ($job.State -in $activeStates) {
                Stop-Job -Job $job -ErrorAction SilentlyContinue
            }
            Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        }
    }
}

function Get-VisualRegressionContext {
    param(
        [Parameter(Mandatory)][string]$Suite,
        [string]$CaptureRoot
    )

    if ([string]::IsNullOrWhiteSpace($Suite) -or [IO.Path]::IsPathRooted($Suite)) {
        throw 'Suite must be a relative path.'
    }
    $normalizedSuite = $Suite.Replace('\', '/')
    if ($normalizedSuite.EndsWith('.p2m2', [StringComparison]::OrdinalIgnoreCase)) {
        $normalizedSuite = $normalizedSuite.Substring(0, $normalizedSuite.Length - 5)
    }
    $segments = @($normalizedSuite.Split('/'))
    if ($segments.Count -eq 0 -or @(
        $segments | Where-Object {
            [string]::IsNullOrWhiteSpace($_) -or
            $_ -in @('.', '..') -or
            $_.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0
        }
    ).Count -gt 0) {
        throw "Suite contains an invalid path component: $Suite"
    }
    $suiteName = $segments -join '/'
    $suiteRelativePath = $segments -join [IO.Path]::DirectorySeparatorChar
    $root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    $repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
    . (Join-Path $repository 'scripts\lib\paths.ps1')
    $paths = Get-Na2Paths
    $generated = Test-VisualRegressionGeneratedSuite -Suite $suiteName
    $generatedNamespace = Test-VisualRegressionGeneratedSuiteNamespace -Suite $suiteName
    $generatedFamily = if ($generated) {
        Get-VisualRegressionGeneratedSuiteFamily -Suite $suiteName
    }
    else { $null }
    $configuration = Get-E2eConfiguration -Root $root
    $suiteSettings = Resolve-E2eSuiteSettings `
        -Configuration $configuration `
        -Suite $suiteName
    $recordingRepository = Join-Path ([string]$paths.pcsx2_input_recordings) 'e2e'
    $storageRelativePath = if ($generated) {
        if ($generatedFamily -ceq 'idle') {
            $script:E2eGeneratedIdleSuiteName.Replace(
                '/',
                [IO.Path]::DirectorySeparatorChar
            )
        }
        else {
            $script:E2eGeneratedMovesetSuiteName.Replace(
                '/',
                [IO.Path]::DirectorySeparatorChar
            )
        }
    }
    else {
        $suiteRelativePath
    }
    $suitePath = Join-Path $recordingRepository ($suiteRelativePath + '.p2m2')
    $captureRoot = if ([string]::IsNullOrWhiteSpace($CaptureRoot)) {
        Join-Path (Join-Path $root 'captures') $storageRelativePath
    }
    else {
        [IO.Path]::GetFullPath($CaptureRoot)
    }
    [pscustomobject]@{
        Root = $root
        CaptureRepository = Join-Path $root 'captures'
        RecordingRepository = $recordingRepository
        Suite = $suiteName
        SuiteRelativePath = $storageRelativePath
        SuitePath = $suitePath
        Generated = $generated
        GeneratedNamespace = $generatedNamespace
        GeneratedFamily = $generatedFamily
        GeneratedScript = Get-VisualRegressionGeneratedSuiteScript -Root $root
        MemoryCard = $suiteSettings.MemoryCard
        LaunchProfile = $suiteSettings.LaunchProfile
        DescendantSuiteRoot = Join-Path $recordingRepository $suiteRelativePath
        CaptureRoot = $captureRoot
        Capture = [pscustomobject]@{
            AllGrids = Join-Path $captureRoot $script:E2eAllGridDirectory
            ScreenshotGrids = Join-Path $captureRoot $script:E2eScreenshotGridDirectory
            PairGrids = Join-Path $captureRoot $script:E2ePairGridDirectory
            BlendGrids = Join-Path $captureRoot $script:E2eBlendGridDirectory
            DiffGrids = Join-Path $captureRoot $script:E2eDiffGridDirectory
        }
        Repository = $repository
        Comparator = Join-Path ([string]$paths.scripts) 'research\localization\compare_font_capture_sets.ps1'
    }
}

function Get-VisualRegressionSuiteNames {
    param([Parameter(Mandatory)][string]$RecordingRepository)

    [string[]]@(
        if (Test-Path -LiteralPath $RecordingRepository -PathType Container) {
            Get-ChildItem -LiteralPath $RecordingRepository -Filter '*.p2m2' -File -Recurse |
                ForEach-Object {
                    $relative = [IO.Path]::GetRelativePath($RecordingRepository, $_.FullName)
                    $suite = $relative.Substring(0, $relative.Length - 5).Replace('\', '/')
                    if (-not (Test-VisualRegressionGeneratedSuiteNamespace -Suite $suite)) {
                        $suite
                    }
                }
        }
        $root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
        $generatedScript = Get-VisualRegressionGeneratedSuiteScript -Root $root
        if (Test-Path -LiteralPath $generatedScript -PathType Leaf) {
            foreach ($generatedSuite in $script:E2eGeneratedSuiteNames) {
                $missingInputs = @(
                    Get-VisualRegressionGeneratedInputPaths `
                        -RecordingRepository $RecordingRepository `
                        -Suite $generatedSuite |
                        Where-Object {
                            -not (Test-Path -LiteralPath $_ -PathType Leaf)
                        }
                )
                if ($missingInputs.Count -eq 0) {
                    $generatedSuite
                }
            }
        }
    ) | Sort-Object -Unique
}

function Get-VisualRegressionSelectableSuiteNames {
    param([Parameter(Mandatory)][string]$RecordingRepository)

    $available = @(
        Get-VisualRegressionSuiteNames -RecordingRepository $RecordingRepository
    )
    [string[]]@(
        $available
        if ($available -icontains $script:E2eGeneratedMovesetSuiteName) {
            "$($script:E2eGeneratedMovesetSuiteName)/base"
            "$($script:E2eGeneratedMovesetSuiteName)/specials"
        }
    ) | Sort-Object -Unique
}

function Resolve-VisualRegressionSuiteArguments {
    param(
        [Parameter(Mandatory)][object]$Context,
        [AllowEmptyCollection()][string[]]$Argument = @()
    )

    $arguments = [string[]]@($Argument)
    if (-not $Context.Generated) {
        if ($arguments.Count -gt 0) {
            throw "E2E suite $($Context.Suite) accepts no arguments."
        }
        return [pscustomobject]@{
            Arguments = $arguments
            MovesetRange = $null
        }
    }
    if ($arguments.Count -gt 1) {
        throw "E2E suite $($Context.Suite) accepts at most one character row range."
    }
    if ($arguments.Count -eq 0) {
        return [pscustomobject]@{
            Arguments = $arguments
            MovesetRange = $null
        }
    }

    . (Join-Path $Context.Repository 'scripts\lib\paths.ps1')
    $paths = Get-Na2Paths -ManifestPath (Join-Path $Context.Repository 'paths.json')
    $characterDataPath = Join-Path ([string]$paths.resources) 'character_data.tsv'
    $characterData = @(Import-Csv -LiteralPath $characterDataPath -Delimiter "`t")
    $resolvedRange = Resolve-VisualRegressionMovesetRange `
        -Range $arguments[0] `
        -LastAvailableRow ($characterData.Count + 1)
    [pscustomobject]@{
        Arguments = [string[]]@($resolvedRange.Value)
        MovesetRange = $resolvedRange.Value
    }
}

function Resolve-VisualRegressionSuiteSelection {
    param(
        [Parameter(Mandatory)][string[]]$Token,
        [Parameter(Mandatory)][string]$RecordingRepository
    )

    $tokens = [string[]]@($Token)
    if ($tokens.Count -eq 0) {
        throw 'Select all or at least one E2E suite.'
    }
    if (@($tokens | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count -gt 0) {
        throw 'E2E suite selection cannot contain an empty token.'
    }
    $allTokens = @($tokens | Where-Object { $_ -ieq 'all' })
    if ($allTokens.Count -gt 0) {
        if ($tokens.Count -ne 1) {
            throw 'E2E all cannot be combined with suites or suite arguments.'
        }
        $allRequests = @(
            Get-VisualRegressionSuiteNames -RecordingRepository $RecordingRepository |
                ForEach-Object {
                    $context = Get-VisualRegressionContext -Suite $_
                    [pscustomobject]@{
                        Suite = $context.Suite
                        Arguments = [string[]]@()
                        MovesetRange = $null
                        Generated = [bool]$context.Generated
                        GeneratedFamily = $context.GeneratedFamily
                    }
                }
        )
        if ($allRequests.Count -eq 0) {
            throw 'No E2E suites are available.'
        }
        return [pscustomobject]@{
            All = $true
            Requests = [object[]]$allRequests
        }
    }

    $suiteLookup = [Collections.Generic.Dictionary[string, string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($suiteName in @(
        Get-VisualRegressionSelectableSuiteNames -RecordingRepository $RecordingRepository
    )) {
        $suiteLookup[$suiteName] = $suiteName
    }
    $requests = [Collections.Generic.List[object]]::new()
    $selected = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $captureOwners = [Collections.Generic.Dictionary[string, string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $currentSuite = $null
    $currentArguments = [Collections.Generic.List[string]]::new()
    $completeRequest = {
        if ($null -ne $currentSuite) {
            $context = Get-VisualRegressionContext -Suite $currentSuite
            $resolved = Resolve-VisualRegressionSuiteArguments `
                -Context $context `
                -Argument ([string[]]$currentArguments)
            if (-not $selected.Add($context.Suite)) {
                throw "Duplicate E2E suite selection: $($context.Suite)"
            }
            $captureKey = [IO.Path]::GetFullPath($context.CaptureRoot)
            if ($captureOwners.ContainsKey($captureKey)) {
                throw (
                    "E2E suites $($captureOwners[$captureKey]) and $($context.Suite) " +
                    'share capture history and cannot be selected together.'
                )
            }
            $captureOwners[$captureKey] = $context.Suite
            $requests.Add([pscustomobject]@{
                Suite = $context.Suite
                Arguments = [string[]]@($resolved.Arguments)
                MovesetRange = $resolved.MovesetRange
                Generated = [bool]$context.Generated
                GeneratedFamily = $context.GeneratedFamily
            })
        }
    }

    foreach ($tokenValue in $tokens) {
        $normalized = $tokenValue.Replace('\', '/')
        if ($normalized.EndsWith('.p2m2', [StringComparison]::OrdinalIgnoreCase)) {
            $normalized = $normalized.Substring(0, $normalized.Length - 5)
        }
        if ($suiteLookup.ContainsKey($normalized)) {
            . $completeRequest
            $currentSuite = $suiteLookup[$normalized]
            $currentArguments = [Collections.Generic.List[string]]::new()
            continue
        }
        if ($null -eq $currentSuite) {
            throw "E2E suite does not exist: $tokenValue"
        }
        $currentArguments.Add($tokenValue)
    }
    . $completeRequest
    if ($requests.Count -eq 0) {
        throw 'Select all or at least one E2E suite.'
    }
    [pscustomobject]@{
        All = $false
        Requests = [object[]]$requests
    }
}

function Assert-VisualRegressionCaptureGitBaseline {
    param([Parameter(Mandatory)][string]$CaptureRepository)

    $captureRoot = [IO.Path]::GetFullPath($CaptureRepository)
    if (-not (Test-Path -LiteralPath $captureRoot -PathType Container)) {
        throw "E2E capture repository does not exist: $captureRoot"
    }
    $topLevelOutput = @(
        & git -C $captureRoot rev-parse --show-toplevel 2>&1
    )
    if ($LASTEXITCODE -ne 0 -or $topLevelOutput.Count -ne 1) {
        throw "E2E capture Git baseline is unavailable: $($topLevelOutput -join ' ')"
    }
    $topLevel = [IO.Path]::GetFullPath([string]$topLevelOutput[0])
    if (-not [string]::Equals(
        $topLevel,
        $captureRoot,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        throw "E2E captures are not their own Git repository: $captureRoot"
    }
    $headOutput = @(& git -C $captureRoot rev-parse --verify HEAD 2>&1)
    if ($LASTEXITCODE -ne 0 -or $headOutput.Count -ne 1) {
        throw "E2E capture Git HEAD is unavailable: $($headOutput -join ' ')"
    }
}

function Get-VisualRegressionCaptureGitChanges {
    param([Parameter(Mandatory)][string]$CaptureRepository)

    $captureRoot = [IO.Path]::GetFullPath($CaptureRepository)
    $changes = [Collections.Generic.List[object]]::new()
    $trackedOutput = @(
        & git -C $captureRoot -c core.quotepath=false `
            diff --name-status --no-renames HEAD -- . 2>&1
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to read E2E capture changes: $($trackedOutput -join ' ')"
    }
    foreach ($line in $trackedOutput) {
        $separator = ([string]$line).IndexOf("`t")
        if ($separator -lt 1) {
            throw "Git returned an invalid E2E capture change: $line"
        }
        $status = ([string]$line).Substring(0, $separator)
        $path = ([string]$line).Substring($separator + 1).Replace('\', '/')
        $kind = if ($status.StartsWith('A', [StringComparison]::Ordinal)) {
            'Added'
        }
        elseif ($status.StartsWith('D', [StringComparison]::Ordinal)) {
            'Deleted'
        }
        else { 'Modified' }
        $changes.Add([pscustomobject]@{
            Path = $path
            Kind = $kind
        })
    }
    $untrackedOutput = @(
        & git -C $captureRoot -c core.quotepath=false `
            ls-files --others --exclude-standard -- . 2>&1
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to read untracked E2E captures: $($untrackedOutput -join ' ')"
    }
    foreach ($path in $untrackedOutput) {
        $changes.Add([pscustomobject]@{
            Path = ([string]$path).Replace('\', '/')
            Kind = 'Added'
        })
    }
    return [object[]]$changes
}

function Get-VisualRegressionRequestCaptureFilter {
    param([Parameter(Mandatory)][object]$Request)

    $suite = [string]$Request.Suite
    $generated = [bool]$Request.Generated
    $family = [string]$Request.GeneratedFamily
    $storagePath = if ($generated) {
        if ($family -ceq 'idle') {
            $script:E2eGeneratedIdleSuiteName
        }
        else { $script:E2eGeneratedMovesetSuiteName }
    }
    else { $suite }
    $rangePrefixes = $null
    if ($generated -and
        -not [string]::IsNullOrWhiteSpace([string]$Request.MovesetRange)) {
        $rangeMatch = [regex]::Match(
            [string]$Request.MovesetRange,
            '^(\d+)(?:-(\d+))?$'
        )
        $firstRow = [int]$rangeMatch.Groups[1].Value
        $lastRow = if ($rangeMatch.Groups[2].Success) {
            [int]$rangeMatch.Groups[2].Value
        }
        else { $firstRow }
        if ($family -ceq 'idle') {
            $repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
            . (Join-Path $repository 'scripts\lib\paths.ps1')
            $paths = Get-Na2Paths
            $characterData = @(
                Import-Csv `
                    -LiteralPath (Join-Path ([string]$paths.resources) 'character_data.tsv') `
                    -Delimiter "`t"
            )
            $rangePrefixes = [string[]]@(
                Get-VisualRegressionIdlePagePlans `
                    -FirstRow $firstRow `
                    -LastRow $lastRow `
                    -CharacterCount $characterData.Count |
                    ForEach-Object { 'page_{0:D2}_' -f $_.Page }
            )
        }
        else {
            $rangePrefixes = [string[]]@(
                for ($row = $firstRow; $row -le $lastRow; $row++) {
                    '{0:D3}_' -f $row
                }
            )
        }
    }
    $movesetSubfamily = if ($suite -ceq "$($script:E2eGeneratedMovesetSuiteName)/base") {
        'base'
    }
    elseif ($suite -ceq "$($script:E2eGeneratedMovesetSuiteName)/specials") {
        'specials'
    }
    else { $null }
    [pscustomobject]@{
        Suite = $suite
        PathPrefix = $storagePath.Trim('/') + '/'
        Generated = $generated
        ArtifactDirectories = [string[]]$script:E2eStableCaptureDirectories
        RangePrefixes = $rangePrefixes
        MovesetSubfamily = $movesetSubfamily
    }
}

function Test-VisualRegressionCaptureChangeSelected {
    param(
        [Parameter(Mandatory)][object]$Change,
        [Parameter(Mandatory)][object]$Filter
    )

    $path = [string]$Change.Path
    if (-not $path.StartsWith(
        [string]$Filter.PathPrefix,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        return $false
    }
    $relativePath = $path.Substring(([string]$Filter.PathPrefix).Length)
    $artifactDirectory = @($relativePath.Split('/'))[0]
    if ($Filter.ArtifactDirectories -inotcontains $artifactDirectory) {
        return $false
    }
    if (-not $Filter.Generated) {
        return $true
    }
    $name = [IO.Path]::GetFileName($path)
    if ($null -ne $Filter.RangePrefixes -and @(
        $Filter.RangePrefixes | Where-Object {
            $name.StartsWith($_, [StringComparison]::OrdinalIgnoreCase)
        }
    ).Count -eq 0) {
        return $false
    }
    if ($Filter.MovesetSubfamily -ceq 'base') {
        return $name -match '_(?:base|mode_[^_]+)(?:_|\.png$)'
    }
    if ($Filter.MovesetSubfamily -ceq 'specials') {
        return $name -match '_specials(?:_|\.png$)'
    }
    return $true
}

function Get-VisualRegressionCaptureRegression {
    param(
        [Parameter(Mandatory)][object[]]$Request,
        [Parameter(Mandatory)][string]$CaptureRepository
    )

    $changes = @(Get-VisualRegressionCaptureGitChanges `
        -CaptureRepository $CaptureRepository)
    $suiteChanges = [Collections.Generic.List[object]]::new()
    $added = 0
    $modified = 0
    $deleted = 0
    foreach ($suiteRequest in $Request) {
        $filter = Get-VisualRegressionRequestCaptureFilter -Request $suiteRequest
        $selected = @(
            $changes | Where-Object {
                Test-VisualRegressionCaptureChangeSelected `
                    -Change $_ `
                    -Filter $filter
            }
        )
        if ($selected.Count -eq 0) {
            continue
        }
        $suiteChange = [pscustomobject]@{
            Suite = [string]$suiteRequest.Suite
            Added = @($selected | Where-Object Kind -CEQ 'Added').Count
            Modified = @($selected | Where-Object Kind -CEQ 'Modified').Count
            Deleted = @($selected | Where-Object Kind -CEQ 'Deleted').Count
        }
        $suiteChanges.Add($suiteChange)
        $added += $suiteChange.Added
        $modified += $suiteChange.Modified
        $deleted += $suiteChange.Deleted
    }
    [pscustomobject]@{
        Regression = $(if ($suiteChanges.Count -gt 0) { 'changed' } else { 'unchanged' })
        Suites = $Request.Count
        ChangedSuites = $suiteChanges.Count
        Added = $added
        Modified = $modified
        Deleted = $deleted
        SuiteChanges = [object[]]$suiteChanges
    }
}

function New-VisualRegressionGeneratedGridStage {
    param(
        [Parameter(Mandatory)][string]$ExistingDirectory,
        [Parameter(Mandatory)][string]$CapturedDirectory,
        [Parameter(Mandatory)][string]$OutputDirectory,
        [Parameter(Mandatory)]
        [ValidateSet('Reference', 'Current')]
        [string]$CapturedTier,
        [switch]$PreserveCapturedTier
    )

    $capturedDefinition = Get-VisualRegressionScreenshotDefinition -Kind $CapturedTier
    $preservedTier = if ($CapturedTier -ieq 'Reference') { 'Current' } else { 'Reference' }
    $preservedDefinition = Get-VisualRegressionScreenshotDefinition -Kind $preservedTier
    $capturedSuffix = "_$($capturedDefinition.Order)_$($capturedDefinition.Label).png"
    $preservedSuffix = "_$($preservedDefinition.Order)_$($preservedDefinition.Label).png"

    if (-not (Test-Path -LiteralPath $CapturedDirectory -PathType Container)) {
        throw "Generated E2E grid capture does not exist: $CapturedDirectory"
    }
    $capturedFiles = @(
        Get-ChildItem -LiteralPath $CapturedDirectory -Filter '*.png' -File |
            Where-Object { $_.Name.EndsWith($capturedSuffix, [StringComparison]::Ordinal) }
    )
    if ($capturedFiles.Count -eq 0) {
        throw "Generated E2E capture contains no $CapturedTier grids: $CapturedDirectory"
    }
    $unexpectedFiles = @(
        Get-ChildItem -LiteralPath $CapturedDirectory -Filter '*.png' -File |
            Where-Object { -not $_.Name.EndsWith($capturedSuffix, [StringComparison]::Ordinal) }
    )
    if ($unexpectedFiles.Count -gt 0) {
        throw (
            "Generated E2E $CapturedTier capture contains an unexpected grid: " +
            $unexpectedFiles[0].Name
        )
    }

    if (Test-Path -LiteralPath $OutputDirectory) {
        Remove-Item -LiteralPath $OutputDirectory -Recurse -Force
    }
    [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
    if (Test-Path -LiteralPath $ExistingDirectory -PathType Container) {
        Get-ChildItem -LiteralPath $ExistingDirectory -Filter '*.png' -File |
            Where-Object {
                $_.Name.EndsWith($preservedSuffix, [StringComparison]::Ordinal) -or
                    ($PreserveCapturedTier.IsPresent -and
                        $_.Name.EndsWith($capturedSuffix, [StringComparison]::Ordinal))
            } |
            Copy-Item -Destination $OutputDirectory
    }
    $capturedFiles | Copy-Item -Destination $OutputDirectory -Force

    [pscustomobject]@{
        CapturedTier = $CapturedTier.ToLowerInvariant()
        Captured = $capturedFiles.Count
        Preserved = @(
            Get-ChildItem -LiteralPath $OutputDirectory -Filter '*.png' -File |
                Where-Object { $_.Name.EndsWith($preservedSuffix, [StringComparison]::Ordinal) }
        ).Count
    }
}

function New-VisualRegressionGeneratedArtifactStage {
    param(
        [Parameter(Mandatory)][string]$ExistingDirectory,
        [Parameter(Mandatory)][string]$CapturedDirectory,
        [Parameter(Mandatory)][string]$OutputRoot,
        [Parameter(Mandatory)][string]$Comparator,
        [Parameter(Mandatory)]
        [ValidateSet('Reference', 'Current')]
        [string]$CapturedTier,
        [switch]$PreserveCapturedTier
    )

    $screenshotGridDirectory = Join-Path `
        $OutputRoot `
        $script:E2eScreenshotGridDirectory
    New-VisualRegressionGeneratedGridStage `
        -ExistingDirectory $ExistingDirectory `
        -CapturedDirectory $CapturedDirectory `
        -OutputDirectory $screenshotGridDirectory `
        -CapturedTier $CapturedTier `
        -PreserveCapturedTier:$PreserveCapturedTier.IsPresent

    & $Comparator `
        -PairedGridDirectory $screenshotGridDirectory `
        -OutputDirectory $OutputRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Generated grid comparison failed with exit code $LASTEXITCODE."
    }
}

function Remove-VisualRegressionEmptyParents {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Boundary
    )

    $boundaryPath = [IO.Path]::GetFullPath($Boundary).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $current = [IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Path))
    while (
        -not [string]::IsNullOrWhiteSpace($current) -and
        -not $current.Equals($boundaryPath, [StringComparison]::OrdinalIgnoreCase)
    ) {
        $parent = [IO.Path]::GetDirectoryName($current)
        if (
            -not $current.StartsWith(
                $boundaryPath + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase
            ) -or
            -not (Test-Path -LiteralPath $current -PathType Container) -or
            @(Get-ChildItem -LiteralPath $current -Force).Count -ne 0
        ) {
            break
        }
        Remove-Item -LiteralPath $current -Force
        $current = $parent
    }
}

function Get-VisualRegressionScreenshotDefinition {
    param([Parameter(Mandatory)][string]$Kind)

    if (-not $script:E2eScreenshotKinds.Contains($Kind)) {
        throw "Unknown screenshot kind: $Kind"
    }
    return $script:E2eScreenshotKinds[$Kind]
}

function Get-VisualRegressionScreenshotName {
    param(
        [Parameter(Mandatory)][int]$Slot,
        [Parameter(Mandatory)][string]$Kind
    )

    $definition = Get-VisualRegressionScreenshotDefinition -Kind $Kind
    return '{0:D3}_{1}_{2}.png' -f $Slot, $definition.Order, $definition.Label
}

function New-VisualRegressionScreenshotInputStage {
    param(
        [Parameter(Mandatory)][string]$ReferenceDirectory,
        [Parameter(Mandatory)][string]$CurrentDirectory,
        [Parameter(Mandatory)][string]$OutputDirectory
    )

    [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
    foreach ($source in @(
        [pscustomobject]@{ Kind = 'Reference'; Directory = $ReferenceDirectory },
        [pscustomobject]@{ Kind = 'Current'; Directory = $CurrentDirectory }
    )) {
        if (-not (Test-Path -LiteralPath $source.Directory -PathType Container)) {
            continue
        }
        foreach ($file in Get-ChildItem -LiteralPath $source.Directory -Filter '*.png' -File) {
            if ($file.BaseName -notmatch '^\d+$') {
                throw "Non-numeric screenshot name: $($file.FullName)"
            }
            $name = Get-VisualRegressionScreenshotName `
                -Slot ([int]$file.BaseName) `
                -Kind $source.Kind
            Copy-Item `
                -LiteralPath $file.FullName `
                -Destination (Join-Path $OutputDirectory $name)
        }
    }
}

function New-VisualRegressionPagedScreenshotGridStage {
    param(
        [Parameter(Mandatory)][string]$Suite,
        [Parameter(Mandatory)][string]$ExistingDirectory,
        [Parameter(Mandatory)][string]$CapturedScreenshotDirectory,
        [Parameter(Mandatory)][string]$OutputDirectory,
        [Parameter(Mandatory)]
        [ValidateSet('Reference', 'Current')]
        [string]$CapturedTier
    )

    $capturedDefinition = Get-VisualRegressionScreenshotDefinition -Kind $CapturedTier
    $preservedTier = if ($CapturedTier -ieq 'Reference') { 'Current' } else { 'Reference' }
    $preservedDefinition = Get-VisualRegressionScreenshotDefinition -Kind $preservedTier
    $capturedSuffix = "_$($capturedDefinition.Order)_$($capturedDefinition.Label).png"
    $preservedSuffix = "_$($preservedDefinition.Order)_$($preservedDefinition.Label).png"
    $workRoot = Join-Path `
        ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($OutputDirectory))) `
        ('.screenshot-grid-' + [guid]::NewGuid().ToString('N'))
    $inputRoot = Join-Path $workRoot 'input'
    $capturedGridRoot = Join-Path $workRoot 'captured'
    try {
        $emptyRoot = Join-Path $workRoot 'empty'
        [void](New-Item -ItemType Directory -Path $emptyRoot -Force)
        New-VisualRegressionScreenshotInputStage `
            -ReferenceDirectory $(if ($CapturedTier -ieq 'Reference') {
                $CapturedScreenshotDirectory
            } else { $emptyRoot }) `
            -CurrentDirectory $(if ($CapturedTier -ieq 'Current') {
                $CapturedScreenshotDirectory
            } else { $emptyRoot }) `
            -OutputDirectory $inputRoot
        New-VisualRegressionScreenshotGridStage `
            -Suite $Suite `
            -ScreenshotDirectory $inputRoot `
            -OutputDirectory $capturedGridRoot

        $capturedFiles = @(
            Get-ChildItem -LiteralPath $capturedGridRoot -Filter '*.png' -File |
                Where-Object {
                    $_.Name.EndsWith($capturedSuffix, [StringComparison]::Ordinal)
                }
        )
        if ($capturedFiles.Count -eq 0) {
            throw "Captured $CapturedTier screenshots produced no grids."
        }
        if (Test-Path -LiteralPath $OutputDirectory) {
            Remove-Item -LiteralPath $OutputDirectory -Recurse -Force
        }
        [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
        if (Test-Path -LiteralPath $ExistingDirectory -PathType Container) {
            Get-ChildItem -LiteralPath $ExistingDirectory -Filter '*.png' -File |
                Where-Object {
                    $_.Name.EndsWith($preservedSuffix, [StringComparison]::Ordinal)
                } |
                Copy-Item -Destination $OutputDirectory
        }
        $capturedFiles | Copy-Item -Destination $OutputDirectory -Force
    }
    finally {
        if (Test-Path -LiteralPath $workRoot) {
            Remove-Item -LiteralPath $workRoot -Recurse -Force
        }
    }
}

function New-VisualRegressionAggregateLinkStage {
    param(
        [Parameter(Mandatory)][object[]]$Source,
        [Parameter(Mandatory)][string]$OutputDirectory
    )

    [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
    foreach ($item in $Source) {
        $sourceDirectory = [string]$item.Directory
        if (-not (Test-Path -LiteralPath $sourceDirectory -PathType Container)) {
            continue
        }
        foreach ($file in Get-ChildItem -LiteralPath $sourceDirectory -Filter '*.png' -File) {
            $suffix = [string]$item.Suffix
            $name = if ([string]::IsNullOrWhiteSpace($suffix)) {
                $file.Name
            }
            else {
                $file.BaseName + '_' + $suffix + $file.Extension
            }
            $target = Join-Path $OutputDirectory $name
            if (Test-Path -LiteralPath $target) {
                throw "Duplicate aggregate view name: $name"
            }
            $linkPath = [IO.Path]::GetFullPath($target)
            $sourcePath = [IO.Path]::GetFullPath($file.FullName)
            if ([IO.Path]::DirectorySeparatorChar -ceq '\') {
                $linkPath = if ($linkPath.StartsWith('\\')) {
                    '\\?\UNC\' + $linkPath.Substring(2)
                }
                else {
                    '\\?\' + $linkPath
                }
                $sourcePath = if ($sourcePath.StartsWith('\\')) {
                    '\\?\UNC\' + $sourcePath.Substring(2)
                }
                else {
                    '\\?\' + $sourcePath
                }
            }
            try {
                [void](New-Item -ItemType HardLink -Path $linkPath -Target $sourcePath)
            }
            catch {
                throw "Cannot hardlink aggregate view '$target' to '$($file.FullName)': $($_.Exception.Message)"
            }
        }
    }
}

function New-VisualRegressionScreenshotGridStage {
    param(
        [Parameter(Mandatory)][string]$Suite,
        [Parameter(Mandatory)][string]$ScreenshotDirectory,
        [Parameter(Mandatory)][string]$OutputDirectory
    )

    $context = Get-VisualRegressionContext -Suite $Suite
    & $context.Comparator `
        -ScreenshotDirectory $ScreenshotDirectory `
        -OutputDirectory $OutputDirectory
    if ($LASTEXITCODE -ne 0) {
        throw "Screenshot grid generation failed with exit code $LASTEXITCODE."
    }
}

function Publish-VisualRegressionAggregateViews {
    param(
        [Parameter(Mandatory)][object[]]$Context,
        [Parameter(Mandatory)][string]$TransactionRoot
    )

    $aggregateTransaction = Join-Path $TransactionRoot 'aggregate-views'
    [void](New-Item -ItemType Directory -Path $aggregateTransaction -Force)
    $suiteScript = Join-Path $PSScriptRoot 'suite.ps1'
    $tasks = @(
        foreach ($currentContext in $Context) {
            $taskContext = $currentContext
            $stageRoot = Join-Path `
                (Join-Path $aggregateTransaction 'stages') `
                $taskContext.SuiteRelativePath
            $taskName = "aggregate/$($taskContext.SuiteRelativePath.Replace('\', '/'))"
            [pscustomobject]@{
                Key = $taskName
                Priority = 10
                DependsOn = @()
                Ready = $null
                Start = {
                    Start-ThreadJob `
                        -Name $taskName `
                        -ScriptBlock {
                            param($Script, $CurrentContext, $OutputRoot)
                            $ErrorActionPreference = 'Stop'
                            . $Script
                            New-VisualRegressionAggregateViewStage `
                                -Context $CurrentContext `
                                -OutputRoot $OutputRoot
                        } `
                        -ArgumentList $suiteScript, $taskContext, $stageRoot
                }.GetNewClosure()
            }
        }
    )
    Invoke-VisualRegressionTaskGraph `
        -Task $tasks `
        -FailurePrefix 'E2E aggregate preparation task'

    $replacements = [ordered]@{}
    foreach ($currentContext in $Context) {
        $stageRoot = Join-Path `
            (Join-Path $aggregateTransaction 'stages') `
            $currentContext.SuiteRelativePath
        $replacements[$currentContext.Capture.AllGrids] = Join-Path `
            $stageRoot `
            $script:E2eAllGridDirectory
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $aggregateTransaction
}

function New-VisualRegressionAggregateViewStage {
    param(
        [Parameter(Mandatory)][object]$Context,
        [Parameter(Mandatory)][string]$OutputRoot
    )

    if (Test-Path -LiteralPath $OutputRoot) {
        Remove-Item -LiteralPath $OutputRoot -Recurse -Force
    }
    New-VisualRegressionAggregateLinkStage `
        -Source @(
            [pscustomobject]@{
                Directory = $Context.Capture.ScreenshotGrids
                Suffix = ''
            },
            [pscustomobject]@{
                Directory = $Context.Capture.BlendGrids
                Suffix = 'c_blend'
            },
            [pscustomobject]@{
                Directory = $Context.Capture.DiffGrids
                Suffix = 'd_diff'
            }
        ) `
        -OutputDirectory (Join-Path $OutputRoot $script:E2eAllGridDirectory)
}

function Test-VisualRegressionTransactionOwnerLive {
    param([Parameter(Mandatory)][string]$Transaction)

    $ownerPath = Join-Path $Transaction 'owner.json'
    if (-not (Test-Path -LiteralPath $ownerPath -PathType Leaf)) {
        return $false
    }
    try {
        $owner = Get-Content -Raw -LiteralPath $ownerPath | ConvertFrom-Json
        $ownerProcess = [Diagnostics.Process]::GetProcessById([int]$owner.pid)
        if ($null -ne $owner.process_start_file_time_utc) {
            return (
                $ownerProcess.StartTime.ToFileTimeUtc() -eq
                [long]$owner.process_start_file_time_utc
            )
        }
        $ownerStart = [DateTime]::Parse(
            [string]$owner.process_start_utc,
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::RoundtripKind
        ).ToUniversalTime()
        return $ownerProcess.StartTime.ToUniversalTime() -eq $ownerStart
    }
    catch [ArgumentException] { return $false }
    catch [InvalidOperationException] { return $false }
    catch { return $false }
}

function Set-VisualRegressionTransactionOwner {
    param([Parameter(Mandatory)][string]$Transaction)

    $process = Get-Process -Id $PID
    $owner = [ordered]@{
        pid = $PID
        process_start_file_time_utc = $process.StartTime.ToFileTimeUtc()
        created_utc = (Get-Date).ToUniversalTime().ToString('O')
    } | ConvertTo-Json
    $ownerPath = Join-Path $Transaction 'owner.json'
    $ownerTemporary = "$ownerPath.tmp-$([guid]::NewGuid().ToString('N'))"
    try {
        [IO.File]::WriteAllText(
            $ownerTemporary,
            $owner + "`n",
            [Text.UTF8Encoding]::new($false)
        )
        [IO.File]::Move($ownerTemporary, $ownerPath, $true)
    }
    finally {
        if (Test-Path -LiteralPath $ownerTemporary -PathType Leaf) {
            Remove-Item -LiteralPath $ownerTemporary -Force
        }
    }
}

function Set-VisualRegressionTransactionRequest {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string]$Prefix,
        [Parameter(Mandatory)][string]$ResumeKey,
        [Parameter(Mandatory)][int]$ResumeCount,
        [string]$CreatedUtc
    )

    if ([string]::IsNullOrWhiteSpace($CreatedUtc)) {
        $CreatedUtc = (Get-Date).ToUniversalTime().ToString('O')
    }
    $request = [ordered]@{
        prefix = $Prefix
        resume_key = $ResumeKey
        resume_count = $ResumeCount
        created_utc = $CreatedUtc
        resumed_utc = if ($ResumeCount -gt 0) {
            (Get-Date).ToUniversalTime().ToString('O')
        }
        else { $null }
    } | ConvertTo-Json
    $requestPath = Join-Path $Transaction 'request.json'
    $temporary = "$requestPath.tmp-$([guid]::NewGuid().ToString('N'))"
    try {
        [IO.File]::WriteAllText(
            $temporary,
            $request + "`n",
            [Text.UTF8Encoding]::new($false)
        )
        [IO.File]::Move($temporary, $requestPath, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Test-VisualRegressionTransactionResumed {
    param([Parameter(Mandatory)][string]$Transaction)

    $requestPath = Join-Path $Transaction 'request.json'
    if (-not (Test-Path -LiteralPath $requestPath -PathType Leaf)) {
        return $false
    }
    $request = Get-Content -Raw -LiteralPath $requestPath | ConvertFrom-Json
    return [int]$request.resume_count -gt 0
}

function Move-VisualRegressionTransactionItemsToAttempt {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string[]]$RelativePath,
        [string]$Label = 'resume'
    )

    $transactionRoot = [IO.Path]::GetFullPath($Transaction).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $transactionPrefix = $transactionRoot + [IO.Path]::DirectorySeparatorChar
    foreach ($relative in $RelativePath) {
        if ([IO.Path]::IsPathRooted($relative) -or $relative -match '(^|[\\/])\.\.([\\/]|$)') {
            throw "Attempt artifact path must remain relative: $relative"
        }
        $resolved = [IO.Path]::GetFullPath((Join-Path $transactionRoot $relative))
        if (-not $resolved.StartsWith($transactionPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Attempt artifact path escapes its transaction: $relative"
        }
    }
    $existing = @(
        $RelativePath | Where-Object {
            Test-Path -LiteralPath (Join-Path $transactionRoot $_)
        }
    )
    if ($existing.Count -eq 0) {
        return $null
    }
    $attempt = Join-Path `
        (Join-Path $transactionRoot '.attempts') `
        ("$Label-$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfff'))-" +
            [guid]::NewGuid().ToString('N'))
    [void](New-Item -ItemType Directory -Path $attempt -Force)
    foreach ($relative in $existing) {
        $source = Join-Path $transactionRoot $relative
        $destination = Join-Path $attempt $relative
        [void](New-Item `
            -ItemType Directory `
            -Path ([IO.Path]::GetDirectoryName($destination)) `
            -Force)
        if (Test-Path -LiteralPath $source -PathType Container) {
            [IO.Directory]::Move($source, $destination)
        }
        else {
            [IO.File]::Move($source, $destination)
        }
    }
    return $attempt
}

function New-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Prefix,
        [string]$ResumeKey
    )

    $transactions = [IO.Path]::GetFullPath((Join-Path $Root '.transactions'))
    [void](New-Item -ItemType Directory -Path $transactions -Force)
    if (-not [string]::IsNullOrWhiteSpace($ResumeKey)) {
        $candidates = @(
            Get-ChildItem -LiteralPath $transactions -Directory -Force |
                Where-Object {
                    $_.Name.StartsWith("$Prefix-", [StringComparison]::Ordinal)
                } |
                Sort-Object LastWriteTimeUtc -Descending
        )
        foreach ($candidate in $candidates) {
            $retainedPath = Join-Path $candidate.FullName 'retained.json'
            $isRetained = Test-Path -LiteralPath $retainedPath -PathType Leaf
            if (-not $isRetained -and
                (Test-VisualRegressionTransactionOwnerLive -Transaction $candidate.FullName)) {
                continue
            }
            $claim = $null
            try {
                $claim = [IO.FileStream]::new(
                    (Join-Path $candidate.FullName '.resume-claim'),
                    [IO.FileMode]::CreateNew,
                    [IO.FileAccess]::ReadWrite,
                    [IO.FileShare]::None,
                    1,
                    [IO.FileOptions]::DeleteOnClose
                )
            }
            catch [IO.IOException] {
                continue
            }
            try {
                $isRetained = Test-Path -LiteralPath $retainedPath -PathType Leaf
                if (-not $isRetained -and
                    (Test-VisualRegressionTransactionOwnerLive -Transaction $candidate.FullName)) {
                    continue
                }
                $requestPath = Join-Path $candidate.FullName 'request.json'
                if (-not (Test-Path -LiteralPath $requestPath -PathType Leaf)) {
                    continue
                }
                try {
                    $request = Get-Content -Raw -LiteralPath $requestPath |
                        ConvertFrom-Json
                }
                catch {
                    continue
                }
                if ([string]$request.resume_key -cne $ResumeKey) {
                    continue
                }
                $resumeCount = [int]$request.resume_count + 1
                $createdUtc = [string]$request.created_utc
                Set-VisualRegressionTransactionOwner -Transaction $candidate.FullName
                Set-VisualRegressionTransactionRequest `
                    -Transaction $candidate.FullName `
                    -Prefix $Prefix `
                    -ResumeKey $ResumeKey `
                    -ResumeCount $resumeCount `
                    -CreatedUtc $createdUtc
                if ($isRetained) {
                    Remove-Item -LiteralPath $retainedPath -Force
                }
                Write-Host (
                    "Continuing failed E2E transaction: $($candidate.FullName)"
                ) -ForegroundColor Cyan
                return $candidate.FullName
            }
            finally {
                $claim.Dispose()
            }
        }
    }
    $transaction = Join-Path $transactions (
        $Prefix + '-' + [guid]::NewGuid().ToString('N')
    )
    [void](New-Item -ItemType Directory -Path $transaction)
    Set-VisualRegressionTransactionOwner -Transaction $transaction
    if (-not [string]::IsNullOrWhiteSpace($ResumeKey)) {
        Set-VisualRegressionTransactionRequest `
            -Transaction $transaction `
            -Prefix $Prefix `
            -ResumeKey $ResumeKey `
            -ResumeCount 0
    }
    return $transaction
}

function Set-VisualRegressionTransactionRetained {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string]$Root
    )

    $transactions = [IO.Path]::GetFullPath((Join-Path $Root '.transactions'))
    $resolvedTransaction = [IO.Path]::GetFullPath($Transaction)
    $transactionPrefix = $transactions.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $resolvedTransaction.StartsWith($transactionPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to mark a transaction outside $transactions"
    }
    if (-not (Test-Path -LiteralPath $resolvedTransaction -PathType Container)) {
        throw "Transaction does not exist: $resolvedTransaction"
    }
    $marker = [ordered]@{
        status = 'failed'
        completed_utc = (Get-Date).ToUniversalTime().ToString('O')
    } | ConvertTo-Json
    $markerPath = Join-Path $resolvedTransaction 'retained.json'
    $temporary = "$markerPath.tmp-$([guid]::NewGuid().ToString('N'))"
    try {
        [IO.File]::WriteAllText($temporary, $marker + "`n", [Text.UTF8Encoding]::new($false))
        [IO.File]::Move($temporary, $markerPath, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Remove-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string]$Root
    )

    $transactions = [IO.Path]::GetFullPath((Join-Path $Root '.transactions'))
    $resolvedTransaction = [IO.Path]::GetFullPath($Transaction)
    $transactionPrefix = $transactions.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $resolvedTransaction.StartsWith($transactionPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a transaction outside $transactions"
    }
    if (Test-Path -LiteralPath $resolvedTransaction) {
        Remove-Item -LiteralPath $resolvedTransaction -Recurse -Force
    }
    if ((Test-Path -LiteralPath $transactions -PathType Container) -and
        @(Get-ChildItem -LiteralPath $transactions -Force).Count -eq 0) {
        Remove-Item -LiteralPath $transactions -Force
    }
}

function Invoke-VisualRegressionReplay {
    param(
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string]$SharedRecordingRoot,
        [Parameter(Mandatory)][string]$RecordingPath,
        [Parameter(Mandatory)][string]$Game,
        [Parameter(Mandatory)][string]$CaptureRoot,
        [string]$MemoryCard,
        [AllowNull()][psobject]$LaunchProfile
    )

    $resolvedRecordingRoot = [IO.Path]::GetFullPath($SharedRecordingRoot)
    $resolvedRecordingPath = [IO.Path]::GetFullPath($RecordingPath)
    $recordingPrefix = $resolvedRecordingRoot.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $resolvedRecordingPath.StartsWith(
        $recordingPrefix,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        throw "E2E recording must be inside $resolvedRecordingRoot."
    }
    $recordingName = [IO.Path]::GetRelativePath(
        $resolvedRecordingRoot,
        $resolvedRecordingPath
    )

    Write-Host "[e2e] Replaying $Game"
    . (Join-Path $Repository 'scripts\lib\paths.ps1')
    $paths = Get-Na2Paths -ManifestPath (Join-Path $Repository 'paths.json')
    $launchArguments = @{
        Games = $Game
        Play = $recordingName
        Snapshots = $true
        InputRecordingCaptureMode = 'screenshots'
        CaptureDirectory = $CaptureRoot
        InputRecordingsRoot = $SharedRecordingRoot
        ProjectRoot = $Repository
    }
    Add-VisualRegressionSuiteLaunchSettings `
        -Target $launchArguments `
        -Repository $Repository `
        -Game $Game `
        -MemoryCard $MemoryCard `
        -LaunchProfile $LaunchProfile `
        -Paths $paths
    & $paths.files.pcsx2_game_launch_command @launchArguments
}

function Add-VisualRegressionSuiteLaunchSettings {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][hashtable]$Target,
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string]$Game,
        [string]$MemoryCard,
        [AllowNull()][psobject]$LaunchProfile,
        [AllowNull()][psobject]$Paths
    )

    if (-not [string]::IsNullOrWhiteSpace($MemoryCard)) {
        $Target.MemoryCard = $MemoryCard
    }
    if ($null -ne $LaunchProfile) {
        if ($null -eq $Paths) {
            . (Join-Path $Repository 'scripts\lib\paths.ps1')
            $Paths = Get-Na2Paths -ManifestPath (Join-Path $Repository 'paths.json')
        }
        . (Join-Path $Repository 'scripts\na228\launch_profile.ps1')
        $profile = Resolve-Na2LaunchProfile `
            -Name ([string]$LaunchProfile.Name) `
            -Paths $Paths
        $profileResults = @(
            Invoke-Na2LaunchProfile `
                -Profile $profile `
                -Arguments ([string[]]@($LaunchProfile.Arguments)) `
                -Games @($Game) `
                -ProjectRoot $Repository
        )
        if ($profileResults.Count -ne 1) {
            throw (
                "E2E suite launch profile $($profile.Name) must return exactly " +
                "one configuration; got $($profileResults.Count)."
            )
        }
        $Target.ReadOnlySettings = $true
        Merge-Na2LaunchProfileParameters `
            -Target $Target `
            -Profile $profile `
            -Result $profileResults[0]
    }
}

function Enter-VisualRegressionConcurrencyPool {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][ValidateRange(1, 64)][int]$Capacity
    )

    $resolvedRoot = [IO.Path]::GetFullPath($Root)
    [void](New-Item -ItemType Directory -Path $resolvedRoot -Force)
    while ($true) {
        for ($slot = 1; $slot -le $Capacity; $slot++) {
            $slotPath = Join-Path $resolvedRoot ('slot-{0:D2}.lock' -f $slot)
            try {
                return [IO.File]::Open(
                    $slotPath,
                    [IO.FileMode]::OpenOrCreate,
                    [IO.FileAccess]::ReadWrite,
                    [IO.FileShare]::None
                )
            }
            catch [IO.IOException] {
                # Another replay owns this slot. Try the next one.
            }
        }
        Start-Sleep -Milliseconds 50
    }
}

function Invoke-VisualRegressionPooledReplay {
    param(
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string]$SharedRecordingRoot,
        [Parameter(Mandatory)][string]$RecordingPath,
        [Parameter(Mandatory)][string]$Game,
        [Parameter(Mandatory)][string]$CaptureRoot,
        [Parameter(Mandatory)][string]$ConcurrencyPoolRoot,
        [Parameter(Mandatory)][ValidateRange(1, 64)][int]$ConcurrencyLimit,
        [string]$MemoryCard,
        [AllowNull()][psobject]$LaunchProfile
    )

    $permit = Enter-VisualRegressionConcurrencyPool `
        -Root $ConcurrencyPoolRoot `
        -Capacity $ConcurrencyLimit
    try {
        Invoke-VisualRegressionReplay `
            -Repository $Repository `
            -SharedRecordingRoot $SharedRecordingRoot `
            -RecordingPath $RecordingPath `
            -Game $Game `
            -CaptureRoot $CaptureRoot `
            -MemoryCard $MemoryCard `
            -LaunchProfile $LaunchProfile
    }
    finally {
        $permit.Dispose()
    }
}

function Publish-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][Collections.IDictionary]$Replacements,
        [Parameter(Mandatory)][string]$TransactionRoot,
        [scriptblock]$AfterPublish
    )

    function Clear-PublishedFiles {
        param([Parameter(Mandatory)][string]$Root)

        if (Test-Path -LiteralPath $Root -PathType Container) {
            foreach ($file in Get-ChildItem -LiteralPath $Root -Recurse -File -Force) {
                $path = $file.FullName
                Invoke-VisualRegressionFileOperation `
                    -Description "Removing published file '$path'" `
                    -Operation {
                        Remove-Item -LiteralPath $path -Force -ErrorAction Stop
                    }.GetNewClosure()
            }
        }
    }

    function Copy-PublishedFiles {
        param(
            [Parameter(Mandatory)][string]$Source,
            [Parameter(Mandatory)][string]$Destination
        )

        [void](New-Item -ItemType Directory -Path $Destination -Force)
        foreach ($file in Get-ChildItem -LiteralPath $Source -Recurse -File -Force) {
            $relative = [IO.Path]::GetRelativePath($Source, $file.FullName)
            $target = Join-Path $Destination $relative
            [void](New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force)
            $temporary = "$target.publishing-$([guid]::NewGuid().ToString('N'))"
            try {
                $sourcePath = $file.FullName
                Invoke-VisualRegressionFileOperation `
                    -Description "Copying staged file '$sourcePath'" `
                    -Operation {
                        [IO.File]::Copy($sourcePath, $temporary, $true)
                    }.GetNewClosure()
                Invoke-VisualRegressionFileOperation `
                    -Description "Publishing file '$target'" `
                    -Operation {
                        [IO.File]::Move($temporary, $target, $true)
                    }.GetNewClosure()
            }
            finally {
                if (Test-Path -LiteralPath $temporary -PathType Leaf) {
                    Invoke-VisualRegressionFileOperation `
                        -Description "Removing temporary publication file '$temporary'" `
                        -Operation {
                            Remove-Item -LiteralPath $temporary -Force -ErrorAction Stop
                        }.GetNewClosure()
                }
            }
        }
    }

    function Link-PublishedFiles {
        param(
            [Parameter(Mandatory)][string]$Source,
            [Parameter(Mandatory)][string]$Destination
        )

        [void](New-Item -ItemType Directory -Path $Destination -Force)
        foreach ($file in Get-ChildItem -LiteralPath $Source -Recurse -File -Force) {
            $relative = [IO.Path]::GetRelativePath($Source, $file.FullName)
            $target = Join-Path $Destination $relative
            [void](New-Item `
                -ItemType Directory `
                -Path ([IO.Path]::GetDirectoryName($target)) `
                -Force)
            $linkPath = [IO.Path]::GetFullPath($target)
            $sourcePath = [IO.Path]::GetFullPath($file.FullName)
            if ([IO.Path]::DirectorySeparatorChar -ceq '\') {
                $linkPath = if ($linkPath.StartsWith('\\')) {
                    '\\?\UNC\' + $linkPath.Substring(2)
                }
                else {
                    '\\?\' + $linkPath
                }
                $sourcePath = if ($sourcePath.StartsWith('\\')) {
                    '\\?\UNC\' + $sourcePath.Substring(2)
                }
                else {
                    '\\?\' + $sourcePath
                }
            }
            Invoke-VisualRegressionFileOperation `
                -Description "Hardlinking staged file '$($file.FullName)'" `
                -Operation {
                    [void](New-Item `
                        -ItemType HardLink `
                        -Path $linkPath `
                        -Target $sourcePath `
                        -ErrorAction Stop)
                }.GetNewClosure()
        }
    }

    function Sync-PublishedFiles {
        param(
            [Parameter(Mandatory)][string]$Source,
            [Parameter(Mandatory)][string]$Destination
        )

        [void](New-Item -ItemType Directory -Path $Destination -Force)
        $sourceFiles = @(Get-ChildItem -LiteralPath $Source -Recurse -File -Force)
        $relativePaths = [Collections.Generic.HashSet[string]]::new(
            [StringComparer]::OrdinalIgnoreCase
        )
        foreach ($file in $sourceFiles) {
            $relative = [IO.Path]::GetRelativePath($Source, $file.FullName)
            [void]$relativePaths.Add($relative)
            $target = Join-Path $Destination $relative
            [void](New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force)
            $temporary = "$target.publishing-$([guid]::NewGuid().ToString('N'))"
            try {
                $sourcePath = $file.FullName
                Invoke-VisualRegressionFileOperation `
                    -Description "Copying staged file '$sourcePath'" `
                    -Operation {
                        [IO.File]::Copy($sourcePath, $temporary, $true)
                    }.GetNewClosure()
                Invoke-VisualRegressionFileOperation `
                    -Description "Publishing file '$target'" `
                    -Operation {
                        [IO.File]::Move($temporary, $target, $true)
                    }.GetNewClosure()
            }
            finally {
                if (Test-Path -LiteralPath $temporary -PathType Leaf) {
                    Invoke-VisualRegressionFileOperation `
                        -Description "Removing temporary publication file '$temporary'" `
                        -Operation {
                            Remove-Item -LiteralPath $temporary -Force -ErrorAction Stop
                        }.GetNewClosure()
                }
            }
        }
        foreach ($file in @(Get-ChildItem -LiteralPath $Destination -Recurse -File -Force)) {
            $relative = [IO.Path]::GetRelativePath($Destination, $file.FullName)
            if (-not $relativePaths.Contains($relative)) {
                $path = $file.FullName
                Invoke-VisualRegressionFileOperation `
                    -Description "Removing stale published file '$path'" `
                    -Operation {
                        Remove-Item -LiteralPath $path -Force -ErrorAction Stop
                    }.GetNewClosure()
            }
        }
    }

    function Remove-EmptyPublishedDirectories {
        param([Parameter(Mandatory)][string]$Root)

        if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return }
        foreach ($directory in @(
            Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force |
                Sort-Object { $_.FullName.Length } -Descending
        )) {
            if (@(Get-ChildItem -LiteralPath $directory.FullName -Force).Count -ne 0) {
                continue
            }
            try {
                [IO.Directory]::Delete($directory.FullName)
            }
            catch [IO.IOException] {}
            catch [UnauthorizedAccessException] {}
        }
    }

    $published = [Collections.Generic.List[object]]::new()
    $backupRoot = Join-Path `
        (Join-Path $TransactionRoot '.backups') `
        ('publish-' + [guid]::NewGuid().ToString('N'))
    [void](New-Item -ItemType Directory -Path $backupRoot -Force)
    $backupIndex = 0
    try {
        foreach ($destination in $Replacements.Keys) {
            $source = $Replacements[$destination]
            $backup = Join-Path $backupRoot ('{0:D4}' -f $backupIndex)
            $backupIndex++
            $stableDirectoryNames = $script:E2eStableCaptureDirectories
            if ($stableDirectoryNames -ccontains [IO.Path]::GetFileName($destination)) {
                if (Test-Path -LiteralPath $destination -PathType Container) {
                    Copy-PublishedFiles -Source $destination -Destination $backup
                }
                try {
                    Sync-PublishedFiles -Source $source -Destination $destination
                    Remove-EmptyPublishedDirectories -Root $destination
                    $published.Add([pscustomobject]@{
                        Destination = $destination
                        Backup = $backup
                        Stable = $true
                    })
                }
                catch {
                    Clear-PublishedFiles -Root $destination
                    if (Test-Path -LiteralPath $backup -PathType Container) {
                        Copy-PublishedFiles -Source $backup -Destination $destination
                    }
                    throw
                }
                continue
            }
            if (-not (Test-Path -LiteralPath $source -PathType Container)) {
                throw "Staged publication directory does not exist: $source"
            }
            $destinationParent = [IO.Path]::GetDirectoryName($destination)
            [void](New-Item -ItemType Directory -Path $destinationParent -Force)
            if (Test-Path -LiteralPath $destination) {
                [IO.Directory]::Move($destination, $backup)
            }
            $temporaryDestination = Join-Path `
                $destinationParent `
                ('.' + [IO.Path]::GetFileName($destination) +
                    '.publishing-' + [guid]::NewGuid().ToString('N'))
            try {
                Link-PublishedFiles `
                    -Source $source `
                    -Destination $temporaryDestination
                [IO.Directory]::Move($temporaryDestination, $destination)
                $published.Add([pscustomobject]@{
                    Destination = $destination
                    Backup = $backup
                    Stable = $false
                })
            }
            catch {
                if (Test-Path -LiteralPath $temporaryDestination) {
                    Remove-Item -LiteralPath $temporaryDestination -Recurse -Force
                }
                if (Test-Path -LiteralPath $backup) {
                    [IO.Directory]::Move($backup, $destination)
                }
                throw
            }
        }
        if ($null -ne $AfterPublish) {
            & $AfterPublish
        }
    }
    catch {
        for ($index = $published.Count - 1; $index -ge 0; $index--) {
            $item = $published[$index]
            if ($item.Stable) {
                Clear-PublishedFiles -Root $item.Destination
                if (Test-Path -LiteralPath $item.Backup -PathType Container) {
                    Copy-PublishedFiles -Source $item.Backup -Destination $item.Destination
                }
                Remove-EmptyPublishedDirectories -Root $item.Destination
                continue
            }
            if (Test-Path -LiteralPath $item.Destination) {
                Remove-Item -LiteralPath $item.Destination -Recurse -Force
            }
            if (Test-Path -LiteralPath $item.Backup) {
                [IO.Directory]::Move($item.Backup, $item.Destination)
            }
        }
        throw
    }
    foreach ($item in $published) {
        if (Test-Path -LiteralPath $item.Backup) {
            Remove-Item -LiteralPath $item.Backup -Recurse -Force
        }
    }
    if (Test-Path -LiteralPath $backupRoot) {
        Remove-Item -LiteralPath $backupRoot -Recurse -Force
    }
}
