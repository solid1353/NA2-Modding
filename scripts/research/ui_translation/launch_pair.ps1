[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateRange(5, 120)]
    [int]$WindowWaitSeconds = 30
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\..\na2\process.ps1')
$projectPaths = Get-Na2ProjectPaths

$pcsx2Exe = [IO.Path]::GetFullPath($projectPaths.files.pcsx2_exe)
$na2Command = [IO.Path]::GetFullPath($projectPaths.files.na2_command)
$currentIso = [IO.Path]::GetFullPath($projectPaths.files.current_iso)
$nun5Iso = [IO.Path]::GetFullPath($projectPaths.files.nun5_iso)

foreach ($requiredFile in @($pcsx2Exe, $na2Command, $currentIso, $nun5Iso)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required file does not exist: $requiredFile"
    }
}

Add-Type -AssemblyName System.Windows.Forms
if (-not ('Na2PairWindow' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class Na2PairWindow
{
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool ShowWindowAsync(IntPtr window, int command);

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool MoveWindow(
        IntPtr window,
        int x,
        int y,
        int width,
        int height,
        [MarshalAs(UnmanagedType.Bool)] bool repaint
    );
}
'@
}

function Wait-Na2PairProcess {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][int[]]$ExcludedProcessIds,
        [Parameter(Mandatory = $true)][DateTime]$Deadline
    )

    do {
        $candidate = @(
            Get-Na2Pcsx2Process -Executable $Executable |
                Where-Object { $_.Id -notin $ExcludedProcessIds }
        ) | Select-Object -First 1
        if ($null -ne $candidate) {
            return $candidate
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $Deadline)

    throw 'PCSX2 did not create the expected process before the timeout.'
}

$workingArea = [Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$leftWidth = [Math]::Floor($workingArea.Width / 2)
$rightWidth = $workingArea.Width - $leftWidth
$action = 'close existing PCSX2 instances, run na2 -c, launch NUN5, and tile both windows'

if (-not $PSCmdlet.ShouldProcess($pcsx2Exe, $action)) {
    return
}

$startedProcesses = [Collections.Generic.List[Diagnostics.Process]]::new()
try {
    Stop-Na2Pcsx2 -Executable $pcsx2Exe

    & $na2Command -c
    $currentProcess = Wait-Na2PairProcess `
        -Executable $pcsx2Exe `
        -ExcludedProcessIds @() `
        -Deadline ([DateTime]::UtcNow.AddSeconds($WindowWaitSeconds))
    $startedProcesses.Add($currentProcess)

    $nun5Process = Start-Process -FilePath $pcsx2Exe `
        -WorkingDirectory $projectPaths.pcsx2 `
        -ArgumentList @('-batch', "`"$nun5Iso`"") `
        -PassThru
    $startedProcesses.Add($nun5Process)

    $deadline = [DateTime]::UtcNow.AddSeconds($WindowWaitSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        foreach ($process in $startedProcesses) {
            $process.Refresh()
            if ($process.HasExited) {
                throw "PCSX2 process $($process.Id) exited before creating a window."
            }
        }

        if ($currentProcess.MainWindowHandle -ne [IntPtr]::Zero -and
            $nun5Process.MainWindowHandle -ne [IntPtr]::Zero) {
            break
        }
        Start-Sleep -Milliseconds 100
    }

    if ($currentProcess.MainWindowHandle -eq [IntPtr]::Zero -or
        $nun5Process.MainWindowHandle -eq [IntPtr]::Zero) {
        throw "PCSX2 did not create both windows within $WindowWaitSeconds seconds."
    }

    [Na2PairWindow]::ShowWindowAsync($currentProcess.MainWindowHandle, 9) | Out-Null
    [Na2PairWindow]::ShowWindowAsync($nun5Process.MainWindowHandle, 9) | Out-Null
    Start-Sleep -Milliseconds 100

    $currentMoved = [Na2PairWindow]::MoveWindow(
        $currentProcess.MainWindowHandle,
        $workingArea.X,
        $workingArea.Y,
        $leftWidth,
        $workingArea.Height,
        $true
    )
    $nun5Moved = [Na2PairWindow]::MoveWindow(
        $nun5Process.MainWindowHandle,
        $workingArea.X + $leftWidth,
        $workingArea.Y,
        $rightWidth,
        $workingArea.Height,
        $true
    )
    if (-not $currentMoved -or -not $nun5Moved) {
        throw 'Windows rejected one or both PCSX2 window-placement requests.'
    }

    [pscustomobject]@{
        Left = "Current NA2 via na2 -c (PID $($currentProcess.Id))"
        Right = "NUN5 (PID $($nun5Process.Id))"
    } | Format-List
}
catch {
    foreach ($process in $startedProcesses) {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
    throw
}
