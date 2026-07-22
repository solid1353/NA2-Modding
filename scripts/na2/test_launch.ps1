[CmdletBinding()]
param(
    [string]$IsoPath,
    [ValidateRange(1, 300)]
    [int]$WaitSeconds = 5,
    [string]$AgentName = 'Codex',
    [string]$TaskIdentity
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'process.ps1')
. (Join-Path $PSScriptRoot 'iso_identity.ps1')
. (Join-Path $PSScriptRoot 'test_memory_card.ps1')
$projectPaths = Get-Na2ProjectPaths

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
        [guid]::NewGuid().ToString()
    }
}

$resolvedPcsx2Exe = [IO.Path]::GetFullPath($projectPaths.files.pcsx2_exe)
$pcsx2Ini = $projectPaths.files.pcsx2_ini
$launchScript = Join-Path $PSScriptRoot 'launch.ps1'
$originalIniBytes = $null
$memoryCardContext = $null

if (-not ('Na2TestWindow' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class Na2TestWindow {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}
'@
}

try {
    if (-not (Test-Path -LiteralPath $pcsx2Ini -PathType Leaf)) {
        throw "PCSX2 configuration does not exist: $pcsx2Ini"
    }

    $isoIdentity = Get-Na2IsoPcsx2Identity -Path $resolvedIsoPath
    $memoryCardContext = Enter-Na2TestMemoryCard `
        -GlobalIniPath $pcsx2Ini `
        -GameSettingsDirectory $projectPaths.pcsx2_gamesettings `
        -MemoryCardsDirectory $projectPaths.pcsx2_memcards `
        -Serial $isoIdentity.Serial `
        -CRC $isoIdentity.CRC `
        -AgentName $AgentName `
        -TaskIdentity $TaskIdentity

    $originalIniBytes = [IO.File]::ReadAllBytes($pcsx2Ini)
    $iniText = [IO.File]::ReadAllText($pcsx2Ini)
    $mutePattern = '(?m)^([ \t]*OutputMuted[ \t]*=[ \t]*)[^\r\n]*(\r?)$'
    $muteMatches = [regex]::Matches($iniText, $mutePattern)
    if ($muteMatches.Count -ne 1) {
        throw "Expected exactly one OutputMuted setting in: $pcsx2Ini"
    }

    $mutedIniText = [regex]::Replace(
        $iniText,
        $mutePattern,
        { param($match) $match.Groups[1].Value + 'true' + $match.Groups[2].Value }
    )
    [IO.File]::WriteAllText($pcsx2Ini, $mutedIniText, [Text.UTF8Encoding]::new($false))
    $foregroundBeforeLaunch = [Na2TestWindow]::GetForegroundWindow()
    $cardAction = if ($memoryCardContext.TaskCardCreated) { 'created' } else { 'reused' }
    Write-Host (
        "[na2] Agent test launch: hidden, muted, non-activating; " +
        "$cardAction private card $($memoryCardContext.TaskCardName)"
    ) -ForegroundColor Cyan

    & $launchScript -IsoPath $resolvedIsoPath -WindowStyle Hidden

    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        $testProcesses = @(Get-Na2Pcsx2Process -Executable $resolvedPcsx2Exe)
        if ($testProcesses.Count -gt 0) {
            break
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)

    if ($testProcesses.Count -eq 0) {
        throw 'PCSX2 did not remain running after launch.'
    }

    Write-Host "[na2] PCSX2 test process started; closing after $WaitSeconds second(s)" -ForegroundColor Cyan
    $closeDeadline = [DateTime]::UtcNow.AddSeconds($WaitSeconds)
    do {
        $foregroundWindow = [Na2TestWindow]::GetForegroundWindow()
        foreach ($process in @(Get-Na2Pcsx2Process -Executable $resolvedPcsx2Exe)) {
            $process.Refresh()
            $window = $process.MainWindowHandle
            if ($window -ne [IntPtr]::Zero) {
                [Na2TestWindow]::ShowWindowAsync($window, 0) | Out-Null
                if ($window -eq $foregroundWindow -and $foregroundBeforeLaunch -ne [IntPtr]::Zero) {
                    [Na2TestWindow]::SetForegroundWindow($foregroundBeforeLaunch) | Out-Null
                }
            }
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $closeDeadline)
}
finally {
    $cleanupErrors = [Collections.Generic.List[object]]::new()
    try {
        Stop-Na2Pcsx2 -Executable $resolvedPcsx2Exe
    }
    catch {
        $cleanupErrors.Add($_)
    }
    try {
        if ($null -ne $originalIniBytes) {
            [IO.File]::WriteAllBytes($pcsx2Ini, $originalIniBytes)
        }
    }
    catch {
        $cleanupErrors.Add($_)
    }
    try {
        if ($null -ne $memoryCardContext) {
            Exit-Na2TestMemoryCard -Context $memoryCardContext
        }
    }
    catch {
        $cleanupErrors.Add($_)
    }
    if ($cleanupErrors.Count -gt 0) {
        throw "PCSX2 test cleanup failed: $($cleanupErrors[0].Exception.Message)"
    }
    if ($null -ne $originalIniBytes -or $null -ne $memoryCardContext) {
        Write-Host '[na2] PCSX2 closed; original audio and memory-card settings restored' -ForegroundColor Cyan
    }
}
