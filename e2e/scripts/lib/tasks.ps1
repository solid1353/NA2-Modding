function Remove-VisualRegressionJobs {
    param([AllowEmptyCollection()][object[]]$Job = @())

    foreach ($currentJob in $Job) {
        if ($currentJob.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $currentJob -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $currentJob -Force -ErrorAction SilentlyContinue
    }
}

function Wait-VisualRegressionJobs {
    param(
        [Parameter(Mandatory)][object[]]$Job,
        [Parameter(Mandatory)][string]$FailurePrefix,
        [scriptblock]$OnPoll
    )

    $terminalStates = @('Completed', 'Failed', 'Stopped')
    $receivedFailure = @{}
    while ($true) {
        foreach ($currentJob in $Job) {
            Receive-VisualRegressionJobOutput -Job $currentJob -Failure $receivedFailure
        }

        $failedJob = Get-VisualRegressionFailedJob -Job $Job
        if ($null -ne $failedJob) {
            $jobsToStop = @($Job | Where-Object State -NotIn $terminalStates)
            foreach ($activeJob in $jobsToStop) {
                Stop-Job -Job $activeJob -ErrorAction SilentlyContinue
            }
            foreach ($activeJob in $jobsToStop) {
                Wait-Job -Job $activeJob -Timeout 5 | Out-Null
            }
            foreach ($currentJob in $Job) {
                Receive-VisualRegressionJobOutput -Job $currentJob -Failure $receivedFailure
            }
            throw (Get-VisualRegressionJobFailureMessage `
                -Job $failedJob `
                -Failure $receivedFailure `
                -FailurePrefix $FailurePrefix)
        }

        if (@($Job | Where-Object State -In @('NotStarted', 'Running')).Count -eq 0) {
            break
        }
        if ($null -ne $OnPoll) {
            . $OnPoll
        }
        Start-Sleep -Milliseconds 200
    }

    foreach ($currentJob in $Job) {
        Receive-VisualRegressionJobOutput -Job $currentJob -Failure $receivedFailure
    }
}

function Receive-VisualRegressionJobOutput {
    param(
        [Parameter(Mandatory)][object]$Job,
        [Parameter(Mandatory)][hashtable]$Failure
    )

    $receivedErrors = @()
    Receive-Job `
        -Job $Job `
        -ErrorAction SilentlyContinue `
        -ErrorVariable +receivedErrors |
        ForEach-Object { Write-Output $_ }
    foreach ($receivedError in $receivedErrors) {
        $Failure[$Job.Id] = [string]$receivedError
        Write-Error -ErrorRecord $receivedError -ErrorAction Continue
    }
}

function Get-VisualRegressionFailedJob {
    param([AllowEmptyCollection()][object[]]$Job = @())

    return @(
        $Job | Where-Object State -NotIn @('NotStarted', 'Running', 'Completed')
    ) | Select-Object -First 1
}

function Get-VisualRegressionJobFailureMessage {
    param(
        [Parameter(Mandatory)][object]$Job,
        [Parameter(Mandatory)][hashtable]$Failure,
        [Parameter(Mandatory)][string]$FailurePrefix
    )

    $reasonMessage = if ($Failure.ContainsKey($Job.Id)) {
        $Failure[$Job.Id]
    }
    elseif ($null -ne $Job.JobStateInfo.Reason) {
        $Job.JobStateInfo.Reason.Message
    }
    else {
        'unknown failure'
    }
    return "$FailurePrefix $($Job.Name) failed: $reasonMessage"
}

function Invoke-VisualRegressionTaskGraph {
    param(
        [Parameter(Mandatory)][object[]]$Task,
        [object[]]$SupervisedJob = @(),
        [ValidateRange(1, 64)]
        [int]$ThrottleLimit = [Math]::Max(1, [Math]::Min(8, [Environment]::ProcessorCount)),
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
                Receive-VisualRegressionJobOutput -Job $job -Failure $receivedFailure
            }

            $failedJob = Get-VisualRegressionFailedJob -Job $allJobs
            if ($null -ne $failedJob) {
                & $stopAll
                foreach ($job in $allJobs) {
                    Receive-VisualRegressionJobOutput -Job $job -Failure $receivedFailure
                }
                throw (Get-VisualRegressionJobFailureMessage `
                    -Job $failedJob `
                    -Failure $receivedFailure `
                    -FailurePrefix $FailurePrefix)
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
                        Sort-Object { [int]$pending[$_].Priority } -Descending
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
        Remove-VisualRegressionJobs -Job $taskJobs
    }
}
