[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Games,

    [ValidateRange(5, 120)]
    [int]$WindowWaitSeconds = 30
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\..\pcsx2\process.ps1')
$projectPaths = Get-Na2ProjectPaths

$supportedGames = @('current', 'previous', 'candidate', 'na2s', 'nun3', 'nun5', 'nun6')
$selectedGames = @(
    if ($null -eq $Games -or $Games.Count -eq 0) {
        'current', 'nun5'
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
$na2Command = [IO.Path]::GetFullPath($projectPaths.files.na2_command)
$directIsoFiles = @{
    candidate = 'candidate_iso'
    na2s = 'na2_iso'
    nun3 = 'nun3_iso'
    nun5 = 'nun5_iso'
    nun6 = 'nun6_iso'
}
$selectedIsoPaths = @{}
foreach ($game in $selectedGames) {
    $fileName = switch ($game) {
        'current' { 'current_iso' }
        'previous' { 'previous_iso' }
        default { $directIsoFiles[$game] }
    }
    $selectedIsoPaths[$game] = [IO.Path]::GetFullPath($projectPaths.files.$fileName)
}

$requiredFiles = @($pcsx2Exe)
if ($selectedGames -contains 'current' -or $selectedGames -contains 'previous') {
    $requiredFiles += $na2Command
}
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

function Wait-Na2LaunchProcess {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][int[]]$ExcludedProcessIds,
        [Parameter(Mandatory = $true)][DateTime]$Deadline
    )

    do {
        $candidate = @(
            Get-Na2Pcsx2Process -Executable $Executable |
                Where-Object { $_.Id -notin $ExcludedProcessIds } |
                Sort-Object StartTime -Descending
        ) | Select-Object -First 1
        if ($null -ne $candidate) {
            return $candidate
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $Deadline)

    throw 'PCSX2 did not create the expected process before the timeout.'
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
        $process = if ($game -eq 'current' -or $game -eq 'previous') {
            $knownProcessIds = @($launchedGames | ForEach-Object { $_.Process.Id })
            if ($game -eq 'current') {
                & $na2Command -c | Out-Host
            }
            else {
                & $na2Command -p | Out-Host
            }
            Wait-Na2LaunchProcess `
                -Executable $pcsx2Exe `
                -ExcludedProcessIds $knownProcessIds `
                -Deadline ([DateTime]::UtcNow.AddSeconds($WindowWaitSeconds))
        }
        else {
            Start-Process -FilePath $pcsx2Exe `
                -WorkingDirectory $projectPaths.pcsx2_user `
                -ArgumentList @('-batch', "`"$($selectedIsoPaths[$game])`"") `
                -PassThru
        }

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
