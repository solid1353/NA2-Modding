$ErrorActionPreference = 'Stop'
$script:E2eCaptureTiers = [ordered]@{
    Reference = 'reference'
    Current = 'current'
}
$script:E2eScreenshotKinds = [ordered]@{
    Reference = [pscustomobject]@{ Order = 'a'; Label = 'reference' }
    Current = [pscustomobject]@{ Order = 'b'; Label = 'current' }
    Blend = [pscustomobject]@{ Order = 'c'; Label = 'blend' }
    Diff = [pscustomobject]@{ Order = 'd'; Label = 'diff' }
    Pair = [pscustomobject]@{ Order = 'e'; Label = 'pair' }
}
$script:E2eIndividualDirectoryPrefix = 'base-'
$script:E2eScreenshotDirectory = 'base-screenshots'
$script:E2ePairDirectory = 'base-pairs'
$script:E2eBlendDirectory = 'base-blends'
$script:E2eDiffDirectory = 'base-diffs'
$script:E2eAllDirectory = 'base-all'
$script:E2eAllGridDirectory = 'grid-all'
$script:E2eCaptureRepositoryMetadataNames = @('.git', '.gitattributes', '.gitignore')
$script:E2eScreenshotGridDirectory = 'grid-screenshots'
$script:E2ePairGridDirectory = 'grid-pairs'
$script:E2eBlendGridDirectory = 'grid-blends'
$script:E2eDiffGridDirectory = 'grid-diffs'
$script:E2eStableCaptureDirectories = @(
    $script:E2eScreenshotDirectory,
    $script:E2ePairDirectory,
    $script:E2eBlendDirectory,
    $script:E2eDiffDirectory,
    $script:E2eScreenshotGridDirectory,
    $script:E2ePairGridDirectory,
    $script:E2eBlendGridDirectory,
    $script:E2eDiffGridDirectory,
    'sstates'
)

function Get-VisualRegressionRequestedSuiteNames {
    param(
        [AllowNull()][string[]]$Suite,
        [Parameter(Mandatory)][bool]$WasSpecified
    )

    if (-not $WasSpecified) {
        return
    }
    $providedSuites = @($Suite)
    $requestedSuites = @(
        $providedSuites |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
    if ($providedSuites.Count -ne $requestedSuites.Count) {
        throw 'Suite cannot contain an empty name.'
    }
    $requestedSuites
}

function Wait-VisualRegressionJobs {
    param(
        [Parameter(Mandatory)][object[]]$Job,
        [Parameter(Mandatory)][string]$FailurePrefix,
        [scriptblock]$OnPoll
    )

    $activeStates = @('NotStarted', 'Running')
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
            foreach ($activeJob in $Job | Where-Object State -In $activeStates) {
                Stop-Job -Job $activeJob -ErrorAction SilentlyContinue
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
            if ($job.State -in $activeStates) {
                Stop-Job -Job $job -ErrorAction SilentlyContinue
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

            if ($null -ne $OnPoll) {
                & $OnPoll
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
    $suiteRepository = Join-Path $root 'suites'
    $suitePath = Join-Path $suiteRepository ($suiteRelativePath + '.p2m2')
    $captureRoot = if ([string]::IsNullOrWhiteSpace($CaptureRoot)) {
        Join-Path (Join-Path $root 'captures') $suiteRelativePath
    }
    else {
        [IO.Path]::GetFullPath($CaptureRoot)
    }
    $statesRoot = Join-Path $captureRoot 'sstates'
    [pscustomobject]@{
        Root = $root
        CaptureRepository = Join-Path $root 'captures'
        SuiteRepository = $suiteRepository
        Suite = $suiteName
        SuiteRelativePath = $suiteRelativePath
        SuitePath = $suitePath
        DescendantSuiteRoot = Join-Path $suiteRepository $suiteRelativePath
        CaptureRoot = $captureRoot
        Capture = [pscustomobject]@{
            Screenshots = Join-Path $captureRoot $script:E2eScreenshotDirectory
            Pairs = Join-Path $captureRoot $script:E2ePairDirectory
            Blends = Join-Path $captureRoot $script:E2eBlendDirectory
            Diffs = Join-Path $captureRoot $script:E2eDiffDirectory
            All = Join-Path $captureRoot $script:E2eAllDirectory
            AllGrids = Join-Path $captureRoot $script:E2eAllGridDirectory
            ScreenshotGrids = Join-Path $captureRoot $script:E2eScreenshotGridDirectory
            PairGrids = Join-Path $captureRoot $script:E2ePairGridDirectory
            BlendGrids = Join-Path $captureRoot $script:E2eBlendGridDirectory
            DiffGrids = Join-Path $captureRoot $script:E2eDiffGridDirectory
            States = $statesRoot
            ReferenceStates = Join-Path $statesRoot $script:E2eCaptureTiers.Reference
            CurrentStates = Join-Path $statesRoot $script:E2eCaptureTiers.Current
        }
        Repository = $repository
        Comparator = Join-Path $repository 'scripts\research\localization\compare_font_capture_sets.ps1'
        PythonRunner = Join-Path $repository 'scripts\lib\run_python.ps1'
    }
}

function Get-VisualRegressionSuiteNames {
    param([Parameter(Mandatory)][string]$SuiteRepository)

    if (-not (Test-Path -LiteralPath $SuiteRepository -PathType Container)) {
        return [string[]]@()
    }
    [string[]]@(
        Get-ChildItem -LiteralPath $SuiteRepository -Filter '*.p2m2' -File -Recurse |
            ForEach-Object {
                $relative = [IO.Path]::GetRelativePath($SuiteRepository, $_.FullName)
                $relative.Substring(0, $relative.Length - 5).Replace('\', '/')
            } |
            Sort-Object -Unique
    )
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

function New-VisualRegressionTierStage {
    param(
        [Parameter(Mandatory)][string]$ScreenshotDirectory,
        [Parameter(Mandatory)][string]$StageDirectory,
        [Parameter(Mandatory)][string]$Kind
    )

    $definition = Get-VisualRegressionScreenshotDefinition -Kind $Kind
    [void](New-Item -ItemType Directory -Path $StageDirectory -Force)
    if (-not (Test-Path -LiteralPath $ScreenshotDirectory -PathType Container)) {
        return
    }
    $suffix = "_$($definition.Order)_$($definition.Label)"
    foreach ($file in Get-ChildItem -LiteralPath $ScreenshotDirectory -Filter "*$suffix.png" -File) {
        if ($file.BaseName -notmatch "^(\d+)$([regex]::Escape($suffix))$") {
            throw "Invalid canonical screenshot name: $($file.FullName)"
        }
        $slot = [int]$Matches[1]
        Copy-Item -LiteralPath $file.FullName -Destination (
            Join-Path $StageDirectory ('{0:D4}.png' -f $slot)
        )
    }
}

function New-VisualRegressionScreenshotStage {
    param(
        [Parameter(Mandatory)][string]$ReferenceDirectory,
        [Parameter(Mandatory)][string]$CurrentDirectory,
        [Parameter(Mandatory)][string]$OutputDirectory
    )

    [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
    $sources = @(
        [pscustomobject]@{ Kind = 'Reference'; Directory = $ReferenceDirectory },
        [pscustomobject]@{ Kind = 'Current'; Directory = $CurrentDirectory }
    )
    foreach ($source in $sources) {
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
            Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $OutputDirectory $name)
        }
    }
}

function New-VisualRegressionComparisonStage {
    param(
        [Parameter(Mandatory)][string]$ReportDirectory,
        [Parameter(Mandatory)][string]$OutputDirectory,
        [Parameter(Mandatory)][string]$Kind
    )

    $definition = Get-VisualRegressionScreenshotDefinition -Kind $Kind
    [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
    $sourceDirectory = Join-Path $ReportDirectory (
        $script:E2eIndividualDirectoryPrefix + $definition.Label + 's'
    )
    if (-not (Test-Path -LiteralPath $sourceDirectory -PathType Container)) {
        return
    }
    foreach ($file in Get-ChildItem -LiteralPath $sourceDirectory -Filter '*.png' -File) {
        if ($file.BaseName -notmatch '^\d+$') {
            throw "Non-numeric $($definition.Label) name: $($file.FullName)"
        }
        $name = Get-VisualRegressionScreenshotName `
            -Slot ([int]$file.BaseName) `
            -Kind $Kind
        Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $OutputDirectory $name)
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

function New-VisualRegressionGridStage {
    param(
        [Parameter(Mandatory)][string]$ReportDirectory,
        [Parameter(Mandatory)][string]$GridDirectory,
        [Parameter(Mandatory)][string]$OutputDirectory
    )

    [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
    $sourceDirectory = Join-Path $ReportDirectory $GridDirectory
    if (Test-Path -LiteralPath $sourceDirectory -PathType Container) {
        Get-ChildItem -LiteralPath $sourceDirectory -Filter '*.png' -File |
            Copy-Item -Destination $OutputDirectory
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
        $replacements[$currentContext.Capture.All] = Join-Path `
            $stageRoot `
            $script:E2eAllDirectory
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

    New-VisualRegressionAggregateLinkStage `
        -Source @(
            [pscustomobject]@{
                Directory = $Context.Capture.Screenshots
                Suffix = ''
            },
            [pscustomobject]@{ Directory = $Context.Capture.Blends; Suffix = '' },
            [pscustomobject]@{ Directory = $Context.Capture.Diffs; Suffix = '' }
        ) `
        -OutputDirectory (Join-Path $OutputRoot $script:E2eAllDirectory)
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

function New-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Prefix
    )

    $transactions = [IO.Path]::GetFullPath((Join-Path $Root '.transactions'))
    [void](New-Item -ItemType Directory -Path $transactions -Force)
    $ownerlessGraceCutoff = [DateTime]::UtcNow.AddMinutes(-1)
    foreach ($candidate in Get-ChildItem -LiteralPath $transactions -Directory -Force) {
        if (Test-Path -LiteralPath (Join-Path $candidate.FullName 'retained.json') -PathType Leaf) {
            Remove-Item -LiteralPath $candidate.FullName -Recurse -Force
            continue
        }
        $ownerPath = Join-Path $candidate.FullName 'owner.json'
        if (-not (Test-Path -LiteralPath $ownerPath -PathType Leaf)) {
            if ($candidate.LastWriteTimeUtc -lt $ownerlessGraceCutoff) {
                Remove-Item -LiteralPath $candidate.FullName -Recurse -Force
            }
            continue
        }
        try {
            $owner = Get-Content -Raw -LiteralPath $ownerPath | ConvertFrom-Json
            $ownerProcess = [Diagnostics.Process]::GetProcessById([int]$owner.pid)
            if ($null -ne $owner.process_start_file_time_utc) {
                $isLive = (
                    $ownerProcess.StartTime.ToFileTimeUtc() -eq
                    [long]$owner.process_start_file_time_utc
                )
            }
            else {
                $ownerStart = [DateTime]::Parse(
                    [string]$owner.process_start_utc,
                    [Globalization.CultureInfo]::InvariantCulture,
                    [Globalization.DateTimeStyles]::RoundtripKind
                ).ToUniversalTime()
                $isLive = (
                    $ownerProcess.StartTime.ToUniversalTime() -eq $ownerStart
                )
            }
        }
        catch [ArgumentException] {
            $isLive = $false
        }
        catch [InvalidOperationException] {
            $isLive = $false
        }
        catch {
            $isLive = $candidate.LastWriteTimeUtc -ge $ownerlessGraceCutoff
        }
        if ($isLive) {
            continue
        }
        Remove-Item -LiteralPath $candidate.FullName -Recurse -Force
    }
    $transaction = Join-Path $transactions (
        $Prefix + '-' + [guid]::NewGuid().ToString('N')
    )
    [void](New-Item -ItemType Directory -Path $transaction)
    $process = Get-Process -Id $PID
    $owner = [ordered]@{
        schema_version = 2
        pid = $PID
        process_start_file_time_utc = $process.StartTime.ToFileTimeUtc()
        created_utc = (Get-Date).ToUniversalTime().ToString('O')
    } | ConvertTo-Json
    $ownerPath = Join-Path $transaction 'owner.json'
    $ownerTemporary = "$ownerPath.tmp-$([guid]::NewGuid().ToString('N'))"
    [IO.File]::WriteAllText($ownerTemporary, $owner + "`n", [Text.UTF8Encoding]::new($false))
    [IO.File]::Move($ownerTemporary, $ownerPath, $true)
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
        schema_version = 1
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
        [Parameter(Mandatory)][string]$CaptureRoot
    )

    $generatedRecordingRoot = Join-Path $SharedRecordingRoot '__generated'
    [void](New-Item -ItemType Directory -Path $generatedRecordingRoot -Force)
    $stagedName = Join-Path `
        '__generated' `
        ('e2e-' + [guid]::NewGuid().ToString('N') + '.p2m2')
    $stagedPath = Join-Path $SharedRecordingRoot $stagedName
    try {
        Copy-Item -LiteralPath $RecordingPath -Destination $stagedPath
        Write-Host "[e2e] Replaying $Game"
        . (Join-Path $Repository 'scripts\lib\paths.ps1')
        $paths = Get-Na2Paths -ManifestPath (Join-Path $Repository 'paths.json')
        & $paths.files.pcsx2_game_launch_command `
            -Games $Game `
            -Play $stagedName `
            -Snapshots `
            -CaptureDirectory $CaptureRoot `
            -InputRecordingsRoot $SharedRecordingRoot `
            -ProjectRoot $Repository
    }
    finally {
        if (Test-Path -LiteralPath $stagedPath -PathType Leaf) {
            Remove-Item -LiteralPath $stagedPath -Force
        }
    }
}

function New-VisualRegressionStateStage {
    param(
        [Parameter(Mandatory)][string]$ExistingRoot,
        [Parameter(Mandatory)][string]$StageRoot,
        [Parameter(Mandatory)][string]$Tier,
        [Parameter(Mandatory)][string]$CapturedDirectory,
        [Parameter(Mandatory)][string]$CaptureRepository,
        [Parameter(Mandatory)][string]$ExistingScreenshotDirectory,
        [Parameter(Mandatory)][string]$ExistingScreenshotKind,
        [Parameter(Mandatory)][string]$CapturedScreenshotDirectory,
        [Parameter(Mandatory)][string]$PythonRunner
    )

    if ($Tier -cnotin $script:E2eCaptureTiers.Values) {
        throw "Unknown capture tier: $Tier"
    }
    [void](New-Item -ItemType Directory -Path $StageRoot -Force)
    foreach ($preservedTier in $script:E2eCaptureTiers.Values) {
        if ($preservedTier -ceq $Tier) { continue }
        $source = Join-Path $ExistingRoot $preservedTier
        if (Test-Path -LiteralPath $source -PathType Container) {
            Copy-Item -LiteralPath $source -Destination $StageRoot -Recurse -Force
        }
    }
    $destination = Join-Path $StageRoot $Tier
    [void](New-Item -ItemType Directory -Path $destination -Force)
    $existingStates = Join-Path $ExistingRoot $Tier
    $committedStates = Join-Path $StageRoot '.committed-states'
    [void](New-Item -ItemType Directory -Path $committedStates -Force)
    $identicalScreenshots = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $screenshotDefinition = Get-VisualRegressionScreenshotDefinition `
        -Kind $ExistingScreenshotKind
    if (Test-Path -LiteralPath $ExistingScreenshotDirectory -PathType Container) {
        $comparison = @(
            & $PythonRunner `
                -PackageSet imaging `
                -Script (Join-Path $PSScriptRoot 'find_identical_pngs.py') `
                -ArgumentList @(
                    '--repository', $CaptureRepository,
                    '--existing-prefix', [IO.Path]::GetRelativePath(
                        $CaptureRepository,
                        $ExistingScreenshotDirectory
                    ).Replace('\', '/'),
                    '--existing-order', $screenshotDefinition.Order,
                    '--existing-label', $screenshotDefinition.Label,
                    '--captured', $CapturedScreenshotDirectory,
                    '--state-prefix', [IO.Path]::GetRelativePath(
                        $CaptureRepository,
                        $existingStates
                    ).Replace('\', '/'),
                    '--state-output', $committedStates
                ) `
                -NoBytecode
        )
        if ($LASTEXITCODE -ne 0) {
            throw "PNG comparison failed with exit code $LASTEXITCODE."
        }
        foreach ($name in $comparison) {
            if (-not [string]::IsNullOrWhiteSpace($name)) {
                [void]$identicalScreenshots.Add($name)
            }
        }
    }

    foreach ($capturedState in Get-ChildItem -LiteralPath $CapturedDirectory -Filter '*.p2s' -File) {
        $screenshotName = $capturedState.BaseName + '.png'
        $existingState = Join-Path $committedStates $capturedState.Name
        $sourceState = if (
            $identicalScreenshots.Contains($screenshotName) -and
            (Test-Path -LiteralPath $existingState -PathType Leaf)
        ) {
            $existingState
        }
        else {
            $capturedState.FullName
        }
        Copy-Item -LiteralPath $sourceState -Destination $destination
    }
    Remove-Item -LiteralPath $committedStates -Recurse -Force
}

function Get-NumericPngSlots {
    param([Parameter(Mandatory)][string]$Directory)

    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) {
        return [int[]]@()
    }
    [int[]]@(
        Get-ChildItem -LiteralPath $Directory -Filter '*.png' -File |
            ForEach-Object {
                if ($_.BaseName -notmatch '(\d+)$') {
                    throw "PNG name has no numeric suffix: $($_.FullName)"
                }
                [int]$Matches[1]
            } |
            Sort-Object -Unique
    )
}

function Get-CommonSlots {
    param([Parameter(Mandatory)][string[]]$Directories)

    $common = $null
    foreach ($directory in $Directories) {
        $slots = [Collections.Generic.HashSet[int]]::new()
        $numericSlots = @(Get-NumericPngSlots -Directory $directory)
        if ($numericSlots.Count -gt 0) {
            $slots.UnionWith([int[]]$numericSlots)
        }
        if ($null -eq $common) {
            $common = $slots
        }
        else {
            $common.IntersectWith($slots)
        }
    }
    if ($null -eq $common) {
        return [int[]]@()
    }
    [int[]]@($common | Sort-Object)
}

function New-VisualRegressionReport {
    param(
        [Parameter(Mandatory)][string]$Suite,
        [Parameter(Mandatory)][string]$CurrentDirectory,
        [Parameter(Mandatory)][string]$OutputRoot,
        [Parameter(Mandatory)][string]$ReferenceDirectory,
        [ValidateSet('All', 'Pair', 'Blend', 'Diff')][string]$Kind = 'All'
    )

    $context = Get-VisualRegressionContext -Suite $Suite
    $slots = @(Get-CommonSlots -Directories @($ReferenceDirectory, $CurrentDirectory))
    if ($slots.Count -eq 0) {
        return
    }
    [void](New-Item -ItemType Directory -Path $OutputRoot -Force)
    & $context.Comparator `
        -ReferenceDirectory $ReferenceDirectory `
        -CurrentDirectory $CurrentDirectory `
        -OutputDirectory $OutputRoot `
        -ReferenceLabel 'Reference' `
        -CurrentLabel 'Current' `
        -Kind $Kind
    if ($LASTEXITCODE -ne 0) {
        throw "Reference/current comparison failed with exit code $LASTEXITCODE."
    }
}

function Compare-VisualRegressionVariants {
    param(
        [Parameter(Mandatory)][string]$Suite,
        [Parameter(Mandatory)][string]$BaselineDirectory,
        [Parameter(Mandatory)][string]$CandidateDirectory,
        [Parameter(Mandatory)][string]$CandidateName,
        [Parameter(Mandatory)][string]$OutputRoot
    )

    $baseline = @{}
    $candidate = @{}
    foreach ($file in Get-ChildItem -LiteralPath $BaselineDirectory -Filter '*.png' -File) {
        $baseline[$file.Name] = $file.FullName
    }
    foreach ($file in Get-ChildItem -LiteralPath $CandidateDirectory -Filter '*.png' -File) {
        $candidate[$file.Name] = $file.FullName
    }
    $names = @($baseline.Keys + $candidate.Keys | Sort-Object -Unique)
    $mismatches = [Collections.Generic.List[object]]::new()
    $differenceRoot = Join-Path $OutputRoot 'differences'
    foreach ($name in $names) {
        $kind = if (-not $baseline.ContainsKey($name)) {
            'missing-in-normal'
        }
        elseif (-not $candidate.ContainsKey($name)) {
            "missing-in-$CandidateName"
        }
        elseif (
            (Get-FileHash -LiteralPath $baseline[$name] -Algorithm SHA256).Hash -cne
            (Get-FileHash -LiteralPath $candidate[$name] -Algorithm SHA256).Hash
        ) {
            'content'
        }
        else {
            $null
        }
        if ($null -eq $kind) { continue }
        $mismatches.Add([ordered]@{ name = $name; kind = $kind })
        foreach ($side in @(
            [pscustomobject]@{ Name = 'normal'; Files = $baseline },
            [pscustomobject]@{ Name = $CandidateName; Files = $candidate }
        )) {
            if (-not $side.Files.ContainsKey($name)) { continue }
            $sideRoot = Join-Path $differenceRoot $side.Name
            [void](New-Item -ItemType Directory -Path $sideRoot -Force)
            Copy-Item -LiteralPath $side.Files[$name] -Destination (Join-Path $sideRoot $name)
        }
    }
    [void](New-Item -ItemType Directory -Path $OutputRoot -Force)
    $result = [ordered]@{
        schema_version = 1
        suite = $Suite
        status = if ($mismatches.Count -eq 0) { 'passed' } else { 'failed' }
        compared = $names.Count
        mismatches = @($mismatches)
    }
    $resultPath = Join-Path $OutputRoot 'result.json'
    [IO.File]::WriteAllText(
        $resultPath,
        (($result | ConvertTo-Json -Depth 5) + "`n"),
        [Text.UTF8Encoding]::new($false)
    )
    return [pscustomobject]$result
}

function Preserve-VisualRegressionMismatchEvidence {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string[]]$ComparisonVariant
    )

    $evidenceStage = Join-Path $Transaction '.retained-evidence'
    [void](New-Item -ItemType Directory -Path $evidenceStage -Force)
    foreach ($comparisonName in $ComparisonVariant) {
        $comparisonRoot = Join-Path `
            (Join-Path $Transaction 'comparisons') `
            $comparisonName
        foreach ($resultFile in Get-ChildItem `
            -LiteralPath $comparisonRoot `
            -Filter 'result.json' `
            -File `
            -Recurse
        ) {
            $result = Get-Content -Raw -LiteralPath $resultFile.FullName |
                ConvertFrom-Json
            if ([string]$result.status -cne 'failed') {
                continue
            }
            $suite = [string]$result.suite
            $context = Get-VisualRegressionContext -Suite $suite
            $caseRoot = Join-Path `
                (Join-Path $evidenceStage $comparisonName) `
                $context.SuiteRelativePath
            $screenshotsRoot = Join-Path $caseRoot 'screenshots'
            $statesRoot = Join-Path $caseRoot 'sstates'
            $reportRoot = Join-Path $caseRoot 'report'
            $comparisonCaseRoot = $resultFile.DirectoryName
            foreach ($mismatch in @($result.mismatches)) {
                $name = [string]$mismatch.name
                $stateName = [IO.Path]::ChangeExtension($name, '.p2s')
                foreach ($variant in @('normal', $comparisonName)) {
                    $screenshot = Join-Path `
                        (Join-Path $comparisonCaseRoot "differences\$variant") `
                        $name
                    if (Test-Path -LiteralPath $screenshot -PathType Leaf) {
                        $screenshotDestination = Join-Path $screenshotsRoot $variant
                        [void](New-Item `
                            -ItemType Directory `
                            -Path $screenshotDestination `
                            -Force)
                        Copy-Item `
                            -LiteralPath $screenshot `
                            -Destination (Join-Path $screenshotDestination $name)
                    }
                    $state = Join-Path `
                        (Join-Path `
                            (Join-Path `
                                (Join-Path `
                                    (Join-Path $Transaction "jobs\$variant\suites") `
                                    $context.SuiteRelativePath) `
                                'capture') `
                            'sstates') `
                        $stateName
                    if (Test-Path -LiteralPath $state -PathType Leaf) {
                        $stateDestination = Join-Path $statesRoot $variant
                        [void](New-Item `
                            -ItemType Directory `
                            -Path $stateDestination `
                            -Force)
                        Copy-Item `
                            -LiteralPath $state `
                            -Destination (Join-Path $stateDestination $stateName)
                    }
                }
            }
            [void](New-Item -ItemType Directory -Path $reportRoot -Force)
            Copy-Item `
                -LiteralPath $resultFile.FullName `
                -Destination (Join-Path $reportRoot 'result.json')
        }
    }
    foreach ($item in Get-ChildItem -LiteralPath $Transaction -Force) {
        if ($item.FullName -ceq $evidenceStage) {
            continue
        }
        Remove-Item -LiteralPath $item.FullName -Recurse -Force
    }
    foreach ($item in Get-ChildItem -LiteralPath $evidenceStage -Force) {
        [IO.Directory]::Move($item.FullName, (Join-Path $Transaction $item.Name))
    }
    Remove-Item -LiteralPath $evidenceStage -Force
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
    $backupRoot = Join-Path $TransactionRoot '.backups'
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
            if (Test-Path -LiteralPath $destination) {
                [IO.Directory]::Move($destination, $backup)
            }
            try {
                [IO.Directory]::Move($source, $destination)
                $published.Add([pscustomobject]@{
                    Destination = $destination
                    Backup = $backup
                    Stable = $false
                })
            }
            catch {
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
}
