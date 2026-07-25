[CmdletBinding()]
param(
    [string]$IsoPath,
    [Parameter(Mandatory = $true)][string]$WorkerRoot,
    [ValidateRange(1, 300)][int]$WaitSeconds = 5,
    [ValidateRange(1, 300)][int]$ReadyTimeoutSeconds = 60,
    [string]$AgentName = 'Codex',
    [string]$TaskIdentity,
    [string]$OperationPlan,
    [switch]$StartPaused
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\run_log.ps1')
. (Join-Path $PSScriptRoot 'process.ps1')
. (Join-Path $PSScriptRoot 'iso_identity.ps1')
. (Join-Path $PSScriptRoot 'worker_paths.ps1')
. (Join-Path $PSScriptRoot 'worker_pcsx2.ps1')
. (Join-Path $PSScriptRoot 'pine.ps1')
. (Join-Path $PSScriptRoot 'test_runtime.ps1')
. (Join-Path $PSScriptRoot 'test_operation.ps1')
$projectPaths = Get-Na2ProjectPaths
$worker = Get-Na2WorkerContext `
    -WorkerRoot $WorkerRoot `
    -ProjectPaths $projectPaths `
    -RequireRelative

if ([string]::IsNullOrWhiteSpace($IsoPath)) {
    $IsoPath = $projectPaths.files.current_iso
}
$resolvedIsoPath = if ([IO.Path]::IsPathRooted($IsoPath)) {
    [IO.Path]::GetFullPath($IsoPath)
}
else {
    [IO.Path]::GetFullPath((Join-Path $projectPaths.repository $IsoPath))
}
if (-not (Test-Path -LiteralPath $resolvedIsoPath -PathType Leaf)) {
    throw "ISO does not exist: $resolvedIsoPath"
}
if ([string]::IsNullOrWhiteSpace($TaskIdentity)) {
    $TaskIdentity = if (-not [string]::IsNullOrWhiteSpace($env:CODEX_THREAD_ID)) {
        $env:CODEX_THREAD_ID
    }
    else {
        $worker.WorkerName
    }
}

$pcsx2Context = Get-Na2WorkerPcsx2Context `
    -Worker $worker `
    -ProjectPaths $projectPaths
$resolvedPcsx2Exe = [IO.Path]::GetFullPath($pcsx2Context.Executable)
$portablePcsx2Exe = ConvertTo-Na2ProjectPath `
    -Path $resolvedPcsx2Exe `
    -ProjectPaths $projectPaths
$pcsx2Ini = $pcsx2Context.Ini
$launchScript = Join-Path $PSScriptRoot 'launch.ps1'
$runtimeLayout = $null
$runtimeContext = $null
$workerPcsx2Lock = $null
$configurationLock = $null
$testProcess = $null
$processStartTime = $null
$descriptorPath = $null
$ownershipCapability = $null
$stopResult = $null
$ownershipLossReason = $null
$stopFailureReason = $null
$safeToRemoveRuntime = $false
$settingsRestoredAfterLaunch = $false
$resolvedOperationPlan = $null
$parsedOperationPlan = $null
if (-not [string]::IsNullOrWhiteSpace($OperationPlan)) {
    $resolvedOperationPlan = Resolve-Na2TaskOwnedFile `
        -Path $OperationPlan `
        -Worker $worker `
        -Repository $projectPaths.repository `
        -RequiredExtension '.json'
    $parsedOperationPlan = Get-Na2TestOperationPlan -Path $resolvedOperationPlan
    if (-not [string]::IsNullOrWhiteSpace($parsedOperationPlan.ResultPath)) {
        $parsedOperationPlan | Add-Member `
            -NotePropertyName ResolvedResultPath `
            -NotePropertyValue (Resolve-Na2TaskOwnedOutputPath `
                -Path $parsedOperationPlan.ResultPath `
                -Worker $worker `
                -Repository $projectPaths.repository `
                -RequiredExtension '.json')
    }
}

if (-not ('Na2TestWindow' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class Na2TestWindow {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern IntPtr GetWindow(IntPtr hWnd, uint command);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    public static IntPtr FindTopLevelWindow(uint wantedProcessId) {
        IntPtr best = IntPtr.Zero;
        int bestScore = -1;
        EnumWindows(delegate(IntPtr window, IntPtr state) {
            uint ownerProcessId;
            GetWindowThreadProcessId(window, out ownerProcessId);
            if (ownerProcessId != wantedProcessId)
                return true;
            int score = GetWindowTextLength(window);
            if (GetWindow(window, 4) == IntPtr.Zero)
                score += 10000;
            if (IsWindowVisible(window))
                score += 1000;
            if (score > bestScore) {
                best = window;
                bestScore = score;
            }
            return true;
        }, IntPtr.Zero);
        return best;
    }
}
'@
}

function Test-Na2OwnedWindow {
    param(
        [Parameter(Mandatory = $true)][IntPtr]$Window,
        [Parameter(Mandatory = $true)][int]$ProcessId
    )

    if ($Window -eq [IntPtr]::Zero) { return $false }
    [uint32]$owner = 0
    [void][Na2TestWindow]::GetWindowThreadProcessId($Window, [ref]$owner)
    return $owner -eq [uint32]$ProcessId
}

function Get-Na2OwnedWindow {
    param([Parameter(Mandatory = $true)][Diagnostics.Process]$Process)

    $Process.Refresh()
    $window = $Process.MainWindowHandle
    if (Test-Na2OwnedWindow -Window $window -ProcessId $Process.Id) {
        return $window
    }
    return [Na2TestWindow]::FindTopLevelWindow([uint32]$Process.Id)
}

try {
    $workerPcsx2Lock = Enter-Na2WorkerPcsx2Lock `
        -CloneRoot $pcsx2Context.Root
    $pcsx2Context = Initialize-Na2WorkerPcsx2 `
        -Worker $worker `
        -ProjectPaths $projectPaths
    Assert-Na2WorkerPcsx2NotBlocked -Context $pcsx2Context
    if (-not (Test-Path -LiteralPath $pcsx2Ini -PathType Leaf)) {
        throw "PCSX2 configuration does not exist: $pcsx2Ini"
    }

    $isoIdentity = Get-Na2IsoPcsx2Identity -Path $resolvedIsoPath
    $runtimeLayout = New-Na2TestRuntimeLayout -Worker $worker
    $configurationLock = Enter-Na2Pcsx2ConfigurationLock -IniPath $pcsx2Ini
    $runtimeContext = Enter-Na2TestRuntimeConfiguration `
        -Pcsx2 $pcsx2Context `
        -Layout $runtimeLayout `
        -IsoIdentity $isoIdentity `
        -AgentName $AgentName `
        -TaskIdentity $TaskIdentity `
        -StartPaused:$StartPaused

    $foregroundBeforeLaunch = [Na2TestWindow]::GetForegroundWindow()
    $cardAction = if ($runtimeContext.MemoryCard.TaskCardCreated) { 'created' } else { 'reused' }
    Write-Host (
        "[na2] Agent test launch: hidden, muted, non-activating; " +
        "$cardAction worker card $($runtimeContext.MemoryCard.TaskCardName); " +
        "PINE $($runtimeContext.PinePort)"
    ) -ForegroundColor Cyan

    $testProcess = & $launchScript `
        -IsoPath $resolvedIsoPath `
        -WorkerPcsx2Executable $resolvedPcsx2Exe `
        -WindowStyle Hidden `
        -KeepExistingInstance `
        -PassThru
    if ($null -eq $testProcess) { throw 'PCSX2 launch did not return a process.' }
    $testProcess.Refresh()
    $processStartTime = $testProcess.StartTime
    $descriptorPath = Join-Path $runtimeLayout.LogDirectory 'pcsx2-instance.json'
    $ownershipCapability = New-Na2Pcsx2OwnershipCapability
    $descriptor = [ordered]@{
        schema_version = 2
        state = 'launching'
        worker = $worker.WorkerName
        iso = ConvertTo-Na2ProjectPath -Path $resolvedIsoPath -ProjectPaths $projectPaths
        serial = $isoIdentity.Serial
        crc = $isoIdentity.CRC
        executable = $portablePcsx2Exe
        process_id = $testProcess.Id
        process_start_utc = $processStartTime.ToUniversalTime().ToString('o')
        window_handle = $null
        pine_port = $runtimeContext.PinePort
        memory_card = ConvertTo-Na2ProjectPath `
            -Path $runtimeContext.MemoryCard.TaskCardPath `
            -ProjectPaths $projectPaths
        log_directory = ConvertTo-Na2ProjectPath `
            -Path $runtimeLayout.LogDirectory `
            -ProjectPaths $projectPaths
        settings_restored_after_game_load = $false
    }
    Write-Na2Pcsx2OwnershipDescriptor `
        -Path $descriptorPath `
        -Descriptor $descriptor `
        -OwnershipCapability $ownershipCapability
    $getOwnership = {
        Get-Na2Pcsx2OwnershipState `
            -DescriptorPath $descriptorPath `
            -OwnershipCapability $ownershipCapability
    }

    $pineIdentity = Wait-Na2PineIdentity `
        -Port $runtimeContext.PinePort `
        -Serial $isoIdentity.Serial `
        -CRC $isoIdentity.CRC `
        -ProcessId $testProcess.Id `
        -OwnershipValidator $getOwnership `
        -TimeoutSeconds $ReadyTimeoutSeconds

    $windowDeadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        $ownership = & $getOwnership
        if (-not $ownership.Valid) {
            throw "PCSX2 ownership lost while discovering its window: $($ownership.Reason)."
        }
        $window = Get-Na2OwnedWindow -Process $testProcess
        if (Test-Na2OwnedWindow -Window $window -ProcessId $testProcess.Id) { break }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $windowDeadline)
    if (-not (Test-Na2OwnedWindow -Window $window -ProcessId $testProcess.Id)) {
        throw "PCSX2 process $($testProcess.Id) did not create an owned window."
    }

    Restore-Na2TestRuntimeConfiguration -Context $runtimeContext
    $settingsRestoredAfterLaunch = $true
    Exit-Na2Pcsx2ConfigurationLock -Mutex $configurationLock
    $configurationLock = $null

    $descriptor['state'] = 'ready'
    $descriptor['window_handle'] = ('0x{0:X}' -f $window.ToInt64())
    $descriptor['settings_restored_after_game_load'] = $true
    Write-Na2Pcsx2OwnershipDescriptor `
        -Path $descriptorPath `
        -Descriptor $descriptor `
        -OwnershipCapability $ownershipCapability

    $invokeOwnedPine = {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory = $true)]
            [ValidateSet(
                'Identity',
                'LoadState',
                'SaveState',
                'CaptureState',
                'ReadMemory',
                'PatchMemory',
                'Wait'
            )]
            [string]$Action,
            [string]$StatePath,
            [string]$ScreenshotPath,
            [ValidateRange(0, 99)][int]$Slot = 0,
            [uint32]$Address = 0,
            [byte[]]$Expected,
            [byte[]]$Replacement,
            [ValidateRange(0, 300000)][int]$Milliseconds = 0,
            [ValidateRange(1, 300)][int]$TimeoutSeconds = 30
        )

        $ownedState = Get-Na2Pcsx2OwnershipState `
            -DescriptorPath $descriptorPath `
            -OwnershipCapability $ownershipCapability `
            -KeepDescriptorOpen
        if (-not $ownedState.Valid) {
            $script:ownershipLossReason = $ownedState.Reason
            throw "PCSX2 ownership lost before ${Action}: $($ownedState.Reason)."
        }

        try {
            $slotPath = $null
            $previousSignature = $null
            if ($Action -ceq 'LoadState') {
                if ([string]::IsNullOrWhiteSpace($StatePath)) {
                    throw 'LoadState requires -StatePath.'
                }
                $sourceState = Resolve-Na2TaskOwnedFile `
                    -Path $StatePath `
                    -Worker $worker `
                    -Repository $projectPaths.repository
                $slotPath = Get-Na2Pcsx2StateSlotPath `
                    -StateDirectory $runtimeLayout.SaveStates `
                    -Serial $isoIdentity.Serial `
                    -CRC $isoIdentity.CRC `
                    -Slot $Slot
                Copy-Na2Pcsx2StateToSlot `
                    -SourcePath $sourceState `
                    -DestinationPath $slotPath | Out-Null
            }
            elseif ($Action -in @('SaveState', 'CaptureState')) {
                $slotPath = Get-Na2Pcsx2StateSlotPath `
                    -StateDirectory $runtimeLayout.SaveStates `
                    -Serial $isoIdentity.Serial `
                    -CRC $isoIdentity.CRC `
                    -Slot $Slot
                $previousSignature = Get-Na2Pcsx2StateSignature -Path $slotPath
                if ($Action -ceq 'CaptureState') {
                    if ([string]::IsNullOrWhiteSpace($ScreenshotPath)) {
                        throw 'CaptureState requires -ScreenshotPath.'
                    }
                    $resolvedScreenshot = Resolve-Na2TaskOwnedOutputPath `
                        -Path $ScreenshotPath `
                        -Worker $worker `
                        -Repository $projectPaths.repository `
                        -RequiredExtension '.png'
                }
            }
            elseif ($Action -ceq 'Wait') {
                Start-Sleep -Milliseconds $Milliseconds
                return [pscustomobject]@{
                    Milliseconds = $Milliseconds
                }
            }

            try {
                $result = Invoke-Na2PineOwnedSession `
                    -Port ([int]$ownedState.Descriptor.pine_port) `
                    -Serial ([string]$ownedState.Descriptor.serial) `
                    -CRC ([string]$ownedState.Descriptor.crc) `
                    -Operation $Action `
                    -Slot $Slot `
                    -Address $Address `
                    -Expected $Expected `
                    -Replacement $Replacement
            }
            catch {
                if ($_.Exception.Data['Na2OwnershipLost'] -eq $true) {
                    $script:ownershipLossReason = $_.Exception.Message
                }
                throw
            }

            if ($Action -ceq 'LoadState') {
                return $slotPath
            }
            if ($Action -in @('SaveState', 'CaptureState')) {
                $capturedState = Wait-Na2Pcsx2StateCapture `
                    -Path $slotPath `
                    -PreviousSignature $previousSignature `
                    -TimeoutSeconds $TimeoutSeconds
                if ($Action -ceq 'CaptureState') {
                    $capturedScreenshot = Export-Na2Pcsx2StateScreenshot `
                        -StatePath $capturedState `
                        -OutputPath $resolvedScreenshot
                    return [pscustomobject]@{
                        StatePath = $capturedState
                        ScreenshotPath = $capturedScreenshot
                    }
                }
                return $capturedState
            }
            return $result
        }
        finally {
            $ownedState.DescriptorHandle.Dispose()
        }
    }

    if ($null -ne $resolvedOperationPlan) {
        Write-Host (
            "[na2] Running task-owned operation plan " +
            "$(ConvertTo-Na2ProjectPath -Path $resolvedOperationPlan -ProjectPaths $projectPaths)."
        ) -ForegroundColor Cyan

        $operationResults = [Collections.Generic.List[object]]::new()
        $actionIndex = 0
        foreach ($plannedAction in $parsedOperationPlan.Actions) {
            $actionIndex += 1
            $actionName = ([string]$plannedAction.action).Trim()
            $normalizedAction = $actionName.ToLowerInvariant()
            $actionResult = switch ($normalizedAction) {
                'identity' {
                    $identity = & $invokeOwnedPine -Action Identity
                    [ordered]@{
                        status = $identity.Status
                        version = $identity.Version
                        title = $identity.Title
                        serial = $identity.Serial
                        crc = $identity.CRC
                        game_version = $identity.GameVersion
                    }
                    break
                }
                'load_state' {
                    $statePath = [string](Get-Na2OperationProperty `
                        -Object $plannedAction `
                        -Name 'state_path')
                    $slot = Get-Na2OperationInteger `
                        -Value (Get-Na2OperationProperty -Object $plannedAction -Name 'slot') `
                        -FieldName 'slot' `
                        -Minimum 0 `
                        -Maximum 99 `
                        -Default 0
                    $loaded = & $invokeOwnedPine `
                        -Action LoadState `
                        -StatePath $statePath `
                        -Slot $slot
                    [ordered]@{
                        slot = $slot
                        state_path = ConvertTo-Na2ProjectPath `
                            -Path $loaded `
                            -ProjectPaths $projectPaths
                    }
                    break
                }
                'read_memory' {
                    $address = ConvertTo-Na2OperationAddress `
                        -Value (Get-Na2OperationProperty -Object $plannedAction -Name 'address') `
                        -FieldName 'address'
                    $expected = ConvertFrom-Na2OperationHexBytes `
                        -Value ([string](Get-Na2OperationProperty `
                            -Object $plannedAction `
                            -Name 'expected_hex')) `
                        -FieldName 'expected_hex'
                    $live = & $invokeOwnedPine `
                        -Action ReadMemory `
                        -Address $address `
                        -Expected $expected
                    [ordered]@{
                        address = ('0x{0:X8}' -f $address)
                        bytes = [Convert]::ToHexString($live)
                        exact_match = $true
                    }
                    break
                }
                'patch_memory' {
                    $address = ConvertTo-Na2OperationAddress `
                        -Value (Get-Na2OperationProperty -Object $plannedAction -Name 'address') `
                        -FieldName 'address'
                    $expected = ConvertFrom-Na2OperationHexBytes `
                        -Value ([string](Get-Na2OperationProperty `
                            -Object $plannedAction `
                            -Name 'expected_hex')) `
                        -FieldName 'expected_hex'
                    $replacement = ConvertFrom-Na2OperationHexBytes `
                        -Value ([string](Get-Na2OperationProperty `
                            -Object $plannedAction `
                            -Name 'replacement_hex')) `
                        -FieldName 'replacement_hex'
                    & $invokeOwnedPine `
                        -Action PatchMemory `
                        -Address $address `
                        -Expected $expected `
                        -Replacement $replacement
                    break
                }
                'save_state' {
                    $slot = Get-Na2OperationInteger `
                        -Value (Get-Na2OperationProperty -Object $plannedAction -Name 'slot') `
                        -FieldName 'slot' `
                        -Minimum 0 `
                        -Maximum 99 `
                        -Default 0
                    $timeout = Get-Na2OperationInteger `
                        -Value (Get-Na2OperationProperty -Object $plannedAction -Name 'timeout_seconds') `
                        -FieldName 'timeout_seconds' `
                        -Minimum 1 `
                        -Maximum 300 `
                        -Default 30
                    $saved = & $invokeOwnedPine `
                        -Action SaveState `
                        -Slot $slot `
                        -TimeoutSeconds $timeout
                    [ordered]@{
                        slot = $slot
                        state_path = ConvertTo-Na2ProjectPath `
                            -Path $saved `
                            -ProjectPaths $projectPaths
                    }
                    break
                }
                'capture_state' {
                    $slot = Get-Na2OperationInteger `
                        -Value (Get-Na2OperationProperty -Object $plannedAction -Name 'slot') `
                        -FieldName 'slot' `
                        -Minimum 0 `
                        -Maximum 99 `
                        -Default 0
                    $timeout = Get-Na2OperationInteger `
                        -Value (Get-Na2OperationProperty -Object $plannedAction -Name 'timeout_seconds') `
                        -FieldName 'timeout_seconds' `
                        -Minimum 1 `
                        -Maximum 300 `
                        -Default 30
                    $screenshotPath = [string](Get-Na2OperationProperty `
                        -Object $plannedAction `
                        -Name 'screenshot_path')
                    $captured = & $invokeOwnedPine `
                        -Action CaptureState `
                        -Slot $slot `
                        -ScreenshotPath $screenshotPath `
                        -TimeoutSeconds $timeout
                    [ordered]@{
                        slot = $slot
                        state_path = ConvertTo-Na2ProjectPath `
                            -Path $captured.StatePath `
                            -ProjectPaths $projectPaths
                        screenshot_path = ConvertTo-Na2ProjectPath `
                            -Path $captured.ScreenshotPath `
                            -ProjectPaths $projectPaths
                    }
                    break
                }
                'wait' {
                    $milliseconds = Get-Na2OperationInteger `
                        -Value (Get-Na2OperationProperty -Object $plannedAction -Name 'milliseconds') `
                        -FieldName 'milliseconds' `
                        -Minimum 0 `
                        -Maximum 300000 `
                        -Default 0
                    & $invokeOwnedPine -Action Wait -Milliseconds $milliseconds
                    break
                }
                default {
                    throw "Unsupported task operation action at index ${actionIndex}: $actionName"
                }
            }
            $operationResults.Add([ordered]@{
                index = $actionIndex
                action = $normalizedAction
                result = $actionResult
            })
        }

        $operationResult = [ordered]@{
            schema_version = 1
            operation_plan = ConvertTo-Na2ProjectPath `
                -Path $resolvedOperationPlan `
                -ProjectPaths $projectPaths
            serial = $isoIdentity.Serial
            crc = $isoIdentity.CRC
            actions = $operationResults
        }
        if ($null -ne $parsedOperationPlan.PSObject.Properties['ResolvedResultPath']) {
            Write-Na2TestOperationResult `
                -Path $parsedOperationPlan.ResolvedResultPath `
                -Value $operationResult
        }
        Write-Output $operationResult
    }

    Write-Host (
        "[na2] PCSX2 instance ready: PID $($testProcess.Id), " +
        "window $('0x{0:X}' -f $window.ToInt64()), " +
        "$($pineIdentity.Serial)/$($pineIdentity.CRC); clone settings restored; " +
        "closing after $WaitSeconds second(s)."
    ) -ForegroundColor Cyan

    $closeDeadline = [DateTime]::UtcNow.AddSeconds($WaitSeconds)
    do {
        $ownership = & $getOwnership
        if (-not $ownership.Valid) {
            $ownershipLossReason = $ownership.Reason
            break
        }
        $testProcess.Refresh()
        if ($testProcess.HasExited) { break }
        $foregroundWindow = [Na2TestWindow]::GetForegroundWindow()
        $window = [IntPtr]([Convert]::ToInt64(
            ([string]$ownership.Descriptor.window_handle).Substring(2),
            16
        ))
        if (Test-Na2OwnedWindow -Window $window -ProcessId $testProcess.Id) {
            [Na2TestWindow]::ShowWindowAsync($window, 0) | Out-Null
            if ($window -eq $foregroundWindow -and $foregroundBeforeLaunch -ne [IntPtr]::Zero) {
                [Na2TestWindow]::SetForegroundWindow($foregroundBeforeLaunch) | Out-Null
            }
        }
        else {
            $ownershipLossReason = 'the recorded PCSX2 window no longer belongs to the recorded process'
            break
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $closeDeadline)
}
finally {
    $cleanupErrors = [Collections.Generic.List[object]]::new()
    try {
        if ($null -ne $testProcess) {
            if (-not [string]::IsNullOrWhiteSpace($ownershipLossReason)) {
                $stopResult = [pscustomobject]@{
                    Status = 'LostOwnership'
                    Reason = $ownershipLossReason
                }
            }
            elseif ($null -eq $descriptorPath -or $null -eq $ownershipCapability) {
                $stopResult = [pscustomobject]@{
                    Status = 'LostOwnership'
                    Reason = 'the launch did not establish a descriptor and ownership capability'
                }
            }
            else {
                $stopResult = Stop-Na2Pcsx2Process `
                    -DescriptorPath $descriptorPath `
                    -OwnershipCapability $ownershipCapability `
                    -Executable $resolvedPcsx2Exe `
                    -ExecutableIdentity $portablePcsx2Exe
            }
            if ($stopResult.Status -eq 'LostOwnership') {
                if ([string]::IsNullOrWhiteSpace($ownershipLossReason)) {
                    $ownershipLossReason = $stopResult.Reason
                }
            }
            elseif ($stopResult.Status -notin @('Stopped', 'AlreadyExited')) {
                $stopFailureReason = $stopResult.Reason
            }
        }
    }
    catch { $cleanupErrors.Add($_) }

    try {
        if ($null -ne $runtimeContext) {
            if ($null -eq $configurationLock) {
                $configurationLock = Enter-Na2Pcsx2ConfigurationLock -IniPath $pcsx2Ini
            }
            Restore-Na2TestRuntimeConfiguration `
                -Context $runtimeContext `
                -OnlyIfInjected:$settingsRestoredAfterLaunch
        }
    }
    catch { $cleanupErrors.Add($_) }
    finally {
        if ($null -ne $configurationLock) {
            try { Exit-Na2Pcsx2ConfigurationLock -Mutex $configurationLock } catch { $cleanupErrors.Add($_) }
            $configurationLock = $null
        }
    }

    try {
        $safeToRemoveRuntime = (
            $null -eq $testProcess -or
            (
                $null -ne $stopResult -and
                $stopResult.Status -in @('Stopped', 'AlreadyExited')
            )
        )
        if ($safeToRemoveRuntime -and
            $null -ne $descriptorPath -and
            (Test-Path -LiteralPath $descriptorPath)) {
            Remove-Item -LiteralPath $descriptorPath -Force
        }
        if ($safeToRemoveRuntime -and $null -ne $runtimeLayout) {
            Remove-Na2TestRuntimeLayout `
                -Layout $runtimeLayout `
                -Worker $worker `
                -WorkRoot $projectPaths.work
        }
    }
    catch { $cleanupErrors.Add($_) }

    if ($null -ne $testProcess -and -not $safeToRemoveRuntime) {
        $blockReason = if (-not [string]::IsNullOrWhiteSpace($ownershipLossReason)) {
            $ownershipLossReason
        }
        elseif (-not [string]::IsNullOrWhiteSpace($stopFailureReason)) {
            $stopFailureReason
        }
        elseif ($cleanupErrors.Count -gt 0) {
            $cleanupErrors[0].Exception.Message
        }
        else {
            'the owned runtime could not be verified stopped'
        }
        $runtimePath = if ($null -ne $runtimeLayout) {
            ConvertTo-Na2ProjectPath `
                -Path $runtimeLayout.LogDirectory `
                -ProjectPaths $projectPaths
        }
        else {
            '@work/' + $worker.WorkerName
        }
        try {
            Set-Na2WorkerPcsx2Blocked `
                -Context $pcsx2Context `
                -Reason $blockReason `
                -RuntimePath $runtimePath
        }
        catch { $cleanupErrors.Add($_) }
    }

    if ($null -ne $ownershipCapability) {
        $ownershipCapability.Token = $null
        $ownershipCapability.DescriptorMac = $null
    }
    if ($null -ne $testProcess) { $testProcess.Dispose() }
    if ($null -ne $workerPcsx2Lock) {
        try { Exit-Na2WorkerPcsx2Lock -Mutex $workerPcsx2Lock } catch { $cleanupErrors.Add($_) }
        $workerPcsx2Lock = $null
    }
    if ($cleanupErrors.Count -gt 0) {
        throw "PCSX2 test cleanup failed: $($cleanupErrors[0].Exception.Message)"
    }
    if (-not [string]::IsNullOrWhiteSpace($ownershipLossReason)) {
        $retainedRuntime = if ($null -ne $runtimeLayout) {
            ConvertTo-Na2ProjectPath `
                -Path $runtimeLayout.LogDirectory `
                -ProjectPaths $projectPaths
        }
        else {
            'no runtime path was established'
        }
        throw (
            "PCSX2 ownership lost; the process was left running and its runtime files were retained " +
            "at ${retainedRuntime}: $ownershipLossReason."
        )
    }
    if (-not [string]::IsNullOrWhiteSpace($stopFailureReason)) {
        $retainedRuntime = if ($null -ne $runtimeLayout) {
            ConvertTo-Na2ProjectPath `
                -Path $runtimeLayout.LogDirectory `
                -ProjectPaths $projectPaths
        }
        else {
            'no runtime path was established'
        }
        throw (
            "Owned PCSX2 did not stop; its descriptor and runtime files were retained " +
            "at ${retainedRuntime}: $stopFailureReason."
        )
    }
    if ($null -ne $runtimeContext) {
        Write-Host '[na2] Owned PCSX2 instance closed; clone settings verified; worker artifacts retained' -ForegroundColor Cyan
    }
}
