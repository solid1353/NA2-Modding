[CmdletBinding()]
param(
    [string]$IsoPath,
    [string]$Pcsx2Exe,
    [ValidateRange(1, 300)]
    [int]$WaitSeconds = 5
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

if ([string]::IsNullOrWhiteSpace($IsoPath)) {
    $IsoPath = Join-Path $projectPaths.build 'Current.iso'
}
if ([string]::IsNullOrWhiteSpace($Pcsx2Exe)) {
    $Pcsx2Exe = Join-Path $projectPaths.pcsx2 'pcsx2-qt.exe'
}

$resolvedPcsx2Exe = [IO.Path]::GetFullPath($Pcsx2Exe)
$pcsx2Ini = Join-Path $projectPaths.pcsx2 'inis\PCSX2.ini'
$applyScript = Join-Path $PSScriptRoot 'apply_latest_na2.ps1'
$processName = [IO.Path]::GetFileNameWithoutExtension($resolvedPcsx2Exe)
$originalIniBytes = $null

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

function Get-TestPcsx2Processes {
    @(Get-Process -Name $processName -ErrorAction SilentlyContinue | Where-Object {
        try {
            [IO.Path]::Equals([IO.Path]::GetFullPath($_.Path), $resolvedPcsx2Exe)
        }
        catch {
            $false
        }
    })
}

function Stop-TestPcsx2Processes {
    $processes = @(Get-TestPcsx2Processes)
    foreach ($process in $processes) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
    foreach ($process in $processes) {
        try {
            $process.WaitForExit(5000) | Out-Null
        }
        catch {
            # A process that already exited needs no further cleanup.
        }
    }
}

try {
    if (-not (Test-Path -LiteralPath $pcsx2Ini -PathType Leaf)) {
        throw "PCSX2 configuration does not exist: $pcsx2Ini"
    }

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
    Write-Host '[na2] Agent test launch: hidden, muted, and non-activating' -ForegroundColor Cyan

    & $applyScript -RunOnly -OutputIso $IsoPath -Pcsx2Exe $resolvedPcsx2Exe -StartHidden

    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        $testProcesses = @(Get-TestPcsx2Processes)
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
        foreach ($process in @(Get-TestPcsx2Processes)) {
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
    Stop-TestPcsx2Processes
    if ($null -ne $originalIniBytes) {
        [IO.File]::WriteAllBytes($pcsx2Ini, $originalIniBytes)
        Write-Host '[na2] PCSX2 closed; original audio setting restored' -ForegroundColor Cyan
    }
}
