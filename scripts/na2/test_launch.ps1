[CmdletBinding()]
param(
    [string]$IsoPath,
    [ValidateRange(1, 300)]
    [int]$WaitSeconds = 5
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'process.ps1')
$projectPaths = Get-Na2ProjectPaths

if ([string]::IsNullOrWhiteSpace($IsoPath)) {
    $IsoPath = $projectPaths.files.current_iso
}
$resolvedPcsx2Exe = [IO.Path]::GetFullPath((Join-Path $projectPaths.pcsx2 'pcsx2-qt.exe'))
$pcsx2Ini = Join-Path $projectPaths.pcsx2 'inis\PCSX2.ini'
$launchScript = Join-Path $PSScriptRoot 'launch.ps1'
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

    & $launchScript -IsoPath $IsoPath -WindowStyle Hidden

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
    Stop-Na2Pcsx2 -Executable $resolvedPcsx2Exe
    if ($null -ne $originalIniBytes) {
        [IO.File]::WriteAllBytes($pcsx2Ini, $originalIniBytes)
        Write-Host '[na2] PCSX2 closed; original audio setting restored' -ForegroundColor Cyan
    }
}
