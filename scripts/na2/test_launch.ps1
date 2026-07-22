[CmdletBinding()]
param(
    [string]$IsoPath,
    [Parameter(Mandatory = $true)][string]$WorkerRoot,
    [ValidateRange(1, 300)][int]$WaitSeconds = 5,
    [ValidateRange(1, 300)][int]$ReadyTimeoutSeconds = 60,
    [string]$AgentName = 'Codex',
    [string]$TaskIdentity
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\run_log.ps1')
. (Join-Path $PSScriptRoot 'process.ps1')
. (Join-Path $PSScriptRoot 'iso_identity.ps1')
. (Join-Path $PSScriptRoot 'worker_paths.ps1')
. (Join-Path $PSScriptRoot 'pine.ps1')
. (Join-Path $PSScriptRoot 'test_runtime.ps1')
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

$resolvedPcsx2Exe = [IO.Path]::GetFullPath($projectPaths.files.pcsx2_exe)
$pcsx2Ini = $projectPaths.files.pcsx2_ini
$launchScript = Join-Path $PSScriptRoot 'launch.ps1'
$runtimeLayout = $null
$runtimeContext = $null
$configurationLock = $null
$testProcess = $null
$processStartTime = $null
$descriptorPath = $null
$settingsRestoredAfterLaunch = $false

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
    if (-not (Test-Path -LiteralPath $pcsx2Ini -PathType Leaf)) {
        throw "PCSX2 configuration does not exist: $pcsx2Ini"
    }

    $isoIdentity = Get-Na2IsoPcsx2Identity -Path $resolvedIsoPath
    $runtimeLayout = New-Na2TestRuntimeLayout -Worker $worker
    $configurationLock = Enter-Na2Pcsx2ConfigurationLock -IniPath $pcsx2Ini
    $runtimeContext = Enter-Na2TestRuntimeConfiguration `
        -ProjectPaths $projectPaths `
        -Layout $runtimeLayout `
        -IsoIdentity $isoIdentity `
        -AgentName $AgentName `
        -TaskIdentity $TaskIdentity

    $foregroundBeforeLaunch = [Na2TestWindow]::GetForegroundWindow()
    $cardAction = if ($runtimeContext.MemoryCard.TaskCardCreated) { 'created' } else { 'reused' }
    Write-Host (
        "[na2] Agent test launch: hidden, muted, non-activating; " +
        "$cardAction worker card $($runtimeContext.MemoryCard.TaskCardName); " +
        "PINE $($runtimeContext.PinePort)"
    ) -ForegroundColor Cyan

    $testProcess = & $launchScript `
        -IsoPath $resolvedIsoPath `
        -WindowStyle Hidden `
        -KeepExistingInstance `
        -PassThru
    if ($null -eq $testProcess) { throw 'PCSX2 launch did not return a process.' }
    $testProcess.Refresh()
    $processStartTime = $testProcess.StartTime

    $pineIdentity = Wait-Na2PineIdentity `
        -Port $runtimeContext.PinePort `
        -Serial $isoIdentity.Serial `
        -CRC $isoIdentity.CRC `
        -ProcessId $testProcess.Id `
        -TimeoutSeconds $ReadyTimeoutSeconds

    $windowDeadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
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

    $descriptorPath = Join-Path $runtimeLayout.LogDirectory 'pcsx2-instance.json'
    $descriptor = [ordered]@{
        schema_version = 1
        worker = $worker.WorkerName
        iso = ConvertTo-Na2ProjectPath -Path $resolvedIsoPath -ProjectPaths $projectPaths
        serial = $isoIdentity.Serial
        crc = $isoIdentity.CRC
        process_id = $testProcess.Id
        process_start_utc = $processStartTime.ToUniversalTime().ToString('o')
        window_handle = ('0x{0:X}' -f $window.ToInt64())
        pine_port = $runtimeContext.PinePort
        memory_card = ConvertTo-Na2ProjectPath `
            -Path $runtimeContext.MemoryCard.TaskCardPath `
            -ProjectPaths $projectPaths
        log_directory = ConvertTo-Na2ProjectPath `
            -Path $runtimeLayout.LogDirectory `
            -ProjectPaths $projectPaths
        settings_restored_after_game_load = $true
    }
    Set-Na2Utf8FileAtomic `
        -Path $descriptorPath `
        -Content (($descriptor | ConvertTo-Json -Depth 4) + "`n")

    Write-Host (
        "[na2] PCSX2 instance ready: PID $($testProcess.Id), " +
        "window $('0x{0:X}' -f $window.ToInt64()), " +
        "$($pineIdentity.Serial)/$($pineIdentity.CRC); shared settings restored; " +
        "closing after $WaitSeconds second(s)."
    ) -ForegroundColor Cyan

    $closeDeadline = [DateTime]::UtcNow.AddSeconds($WaitSeconds)
    do {
        $testProcess.Refresh()
        if ($testProcess.HasExited) { break }
        $foregroundWindow = [Na2TestWindow]::GetForegroundWindow()
        $window = Get-Na2OwnedWindow -Process $testProcess
        if (Test-Na2OwnedWindow -Window $window -ProcessId $testProcess.Id) {
            [Na2TestWindow]::ShowWindowAsync($window, 0) | Out-Null
            if ($window -eq $foregroundWindow -and $foregroundBeforeLaunch -ne [IntPtr]::Zero) {
                [Na2TestWindow]::SetForegroundWindow($foregroundBeforeLaunch) | Out-Null
            }
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $closeDeadline)
}
finally {
    $cleanupErrors = [Collections.Generic.List[object]]::new()
    try {
        if ($null -ne $testProcess -and $null -ne $processStartTime) {
            Stop-Na2Pcsx2Process `
                -Executable $resolvedPcsx2Exe `
                -ProcessId $testProcess.Id `
                -ExpectedStartTime $processStartTime
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
        if ($null -ne $descriptorPath -and (Test-Path -LiteralPath $descriptorPath)) {
            Remove-Item -LiteralPath $descriptorPath -Force
        }
        if ($null -ne $runtimeLayout) {
            Remove-Na2TestRuntimeLayout `
                -Layout $runtimeLayout `
                -Worker $worker `
                -WorkRoot $projectPaths.work
        }
    }
    catch { $cleanupErrors.Add($_) }

    if ($null -ne $testProcess) { $testProcess.Dispose() }
    if ($cleanupErrors.Count -gt 0) {
        throw "PCSX2 test cleanup failed: $($cleanupErrors[0].Exception.Message)"
    }
    if ($null -ne $runtimeContext) {
        Write-Host '[na2] Owned PCSX2 instance closed; shared settings verified; worker artifacts retained' -ForegroundColor Cyan
    }
}
