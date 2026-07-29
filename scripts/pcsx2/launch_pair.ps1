[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Games,

    [ValidateRange(5, 120)]
    [int]$WindowWaitSeconds = 30
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'process.ps1')
$projectPaths = Get-Na2ProjectPaths

$supportedGames = @(
    'current',
    'previous',
    'candidate',
    'na2s',
    'nun3',
    'nun5',
    'nun6'
)
$selectedGames = @(
    if ($null -eq $Games -or $Games.Count -eq 0) {
        'nun5', 'current'
    }
    else {
        $Games | ForEach-Object { $_.Trim().ToLowerInvariant() }
    }
)

$invalidGames = @($selectedGames | Where-Object { $_ -notin $supportedGames })
if ($invalidGames.Count -gt 0) {
    throw "Unknown game name(s): $($invalidGames -join ', '). Supported names: $($supportedGames -join ', ')."
}
$seenGames = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$duplicateGames = [Collections.Generic.List[string]]::new()
foreach ($game in $selectedGames) {
    if (-not $seenGames.Add($game)) {
        $duplicateGames.Add($game)
    }
}
if ($duplicateGames.Count -gt 0) {
    throw "Each game may be listed only once: $($duplicateGames -join ', ')."
}

$pcsx2Exe = [IO.Path]::GetFullPath($projectPaths.files.pcsx2_user_exe)
$pcsx2Launcher = [IO.Path]::GetFullPath(
    $projectPaths.files.pcsx2_launch_command
)
$directIsoFiles = @{
    candidate = 'candidate_iso'
    na2s = 'na2_iso'
    nun3 = 'nun3_iso'
    nun5 = 'nun5_iso'
    nun6 = 'nun6_iso'
}
$selectedIsoPaths = @{}
foreach ($game in $selectedGames) {
    $selectedIsoPaths[$game] = switch ($game) {
        'current' { [IO.Path]::GetFullPath($projectPaths.files.current_iso) }
        'previous' { [IO.Path]::GetFullPath($projectPaths.files.previous_iso) }
        default {
            [IO.Path]::GetFullPath(
                $projectPaths.files.($directIsoFiles[$game])
            )
        }
    }
}

$requiredFiles = @($pcsx2Exe, $pcsx2Launcher)
$requiredFiles += @($selectedIsoPaths.Values)
foreach ($requiredFile in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required file does not exist: $requiredFile"
    }
}

Add-Type -AssemblyName System.Windows.Forms
if (-not ('Na2LaunchWindow' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class Na2LaunchWindow
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

$workingArea = [Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$gameList = $selectedGames -join ', '
$action = "close existing PCSX2 instances, launch $gameList, and tile their windows"
if (-not $PSCmdlet.ShouldProcess($pcsx2Exe, $action)) {
    return
}

$launchedGames = [Collections.Generic.List[object]]::new()
try {
    & $projectPaths.files.actualize_command na2
    Stop-Na2Pcsx2 -Executable $pcsx2Exe

    foreach ($game in $selectedGames) {
        $process = & $pcsx2Launcher `
            -Target stable `
            -IsoPath $selectedIsoPaths[$game] `
            -PassThru

        $launchedGames.Add([pscustomobject]@{
            Game = $game
            Process = $process
        })
    }

    $deadline = [DateTime]::UtcNow.AddSeconds($WindowWaitSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        foreach ($launch in $launchedGames) {
            $launch.Process.Refresh()
            if ($launch.Process.HasExited) {
                throw "PCSX2 process $($launch.Process.Id) for $($launch.Game) exited before creating a window."
            }
        }

        $missingWindows = @(
            $launchedGames |
                Where-Object { $_.Process.MainWindowHandle -eq [IntPtr]::Zero }
        )
        if ($missingWindows.Count -eq 0) {
            break
        }
        Start-Sleep -Milliseconds 100
    }

    $missingWindows = @(
        $launchedGames |
            Where-Object { $_.Process.MainWindowHandle -eq [IntPtr]::Zero }
    )
    if ($missingWindows.Count -gt 0) {
        throw "PCSX2 did not create every window within $WindowWaitSeconds seconds: $($missingWindows.Game -join ', ')."
    }

    $gameCount = $launchedGames.Count
    if ($gameCount -le 3) {
        $columns = $gameCount
        $rows = 1
    }
    else {
        $columns = [int][Math]::Ceiling([Math]::Sqrt($gameCount))
        $rows = [int][Math]::Ceiling($gameCount / $columns)
    }

    foreach ($launch in $launchedGames) {
        [Na2LaunchWindow]::ShowWindowAsync($launch.Process.MainWindowHandle, 9) | Out-Null
    }
    Start-Sleep -Milliseconds 100

    $results = for ($index = 0; $index -lt $gameCount; $index++) {
        $launch = $launchedGames[$index]
        $column = $index % $columns
        $row = [Math]::Floor($index / $columns)
        $left = $workingArea.X + [Math]::Floor($workingArea.Width * $column / $columns)
        $right = $workingArea.X + [Math]::Floor($workingArea.Width * ($column + 1) / $columns)
        $top = $workingArea.Y + [Math]::Floor($workingArea.Height * $row / $rows)
        $bottom = $workingArea.Y + [Math]::Floor($workingArea.Height * ($row + 1) / $rows)
        $moved = [Na2LaunchWindow]::MoveWindow(
            $launch.Process.MainWindowHandle,
            $left,
            $top,
            $right - $left,
            $bottom - $top,
            $true
        )
        if (-not $moved) {
            throw "Windows rejected the PCSX2 window-placement request for $($launch.Game)."
        }

        [pscustomobject]@{
            Game = $launch.Game
            ProcessId = $launch.Process.Id
            GridCell = "$(1 + $row),$(1 + $column)"
        }
    }
    $results
}
catch {
    foreach ($launch in $launchedGames) {
        try {
            if (-not $launch.Process.HasExited) {
                Stop-Process -Id $launch.Process.Id -Force -ErrorAction SilentlyContinue
            }
        }
        catch {
            # Preserve the original launch or placement failure.
        }
    }
    throw
}
