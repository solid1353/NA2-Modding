[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Games,

    [ValidateRange(5, 120)]
    [int]$WindowWaitSeconds = 30,

    [switch]$SkipActualization
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

function Get-Na2ConfiguredDevelopmentPinePort {
    $iniPath = Join-Path $projectPaths.pcsx2_dev 'inis\PCSX2.ini'
    if (-not (Test-Path -LiteralPath $iniPath -PathType Leaf)) {
        throw "Development PCSX2 configuration was not found: $iniPath"
    }
    $match = Select-String `
        -LiteralPath $iniPath `
        -Pattern '^\s*PINESlot\s*=\s*(\d+)\s*$' |
        Select-Object -First 1
    if ($null -eq $match) {
        throw "Development PCSX2 PINESlot is not configured in $iniPath"
    }
    $port = [int]$match.Matches[0].Groups[1].Value
    if ($port -lt 1024 -or $port -gt 65535) {
        throw "Development PCSX2 PINESlot is invalid: $port"
    }
    return $port
}

$requestedGames = @(
    if ($null -eq $Games -or $Games.Count -eq 0) {
        'nun5', 'latest'
    }
    else {
        $Games | ForEach-Object { $_.Trim().ToLowerInvariant() }
    }
)

$seenGames = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$selectedGames = [Collections.Generic.List[string]]::new()
$duplicateGames = [Collections.Generic.List[string]]::new()
foreach ($requestedGame in $requestedGames) {
    $aliasProperty = $projectPaths.games.Aliases.PSObject.Properties[$requestedGame]
    if ($null -eq $aliasProperty) {
        throw (
            "Unknown game name: $requestedGame. Supported names: " +
            "$($projectPaths.games.Names -join ', ')."
        )
    }
    $game = [string]$aliasProperty.Value
    if (-not $seenGames.Add($game)) {
        $duplicateGames.Add($requestedGame)
    }
    else {
        $selectedGames.Add($game)
    }
}
if ($duplicateGames.Count -gt 0) {
    throw "Each game may be listed only once: $($duplicateGames -join ', ')."
}

$pcsx2Exe = [IO.Path]::GetFullPath($projectPaths.files.pcsx2_dev_exe)
$pcsx2Launcher = [IO.Path]::GetFullPath(
    $projectPaths.files.pcsx2_launch_command
)
$selectedIsoPaths = @{}
foreach ($game in $selectedGames) {
    $entry = $projectPaths.games.Entries.PSObject.Properties[$game].Value
    $selectedIsoPaths[$game] = [IO.Path]::GetFullPath($entry.IsoPath)
}

$requiredFiles = @($pcsx2Exe, $pcsx2Launcher)
$requiredFiles += @($selectedIsoPaths.Values)
foreach ($requiredFile in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required file does not exist: $requiredFile"
    }
}
$pinePortBase = Get-Na2ConfiguredDevelopmentPinePort
if ($pinePortBase + $selectedGames.Count - 1 -gt 65535) {
    throw "Not enough PINE ports remain after configured port $pinePortBase."
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
$action = "launch $gameList and tile their windows"
if (-not $PSCmdlet.ShouldProcess($pcsx2Exe, $action)) {
    return
}

$usedPinePorts = [Collections.Generic.HashSet[int]]::new()
foreach ($endpoint in [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()) {
    [void]$usedPinePorts.Add($endpoint.Port)
}

$launchedGames = [Collections.Generic.List[object]]::new()
try {
    $usesNa228Build = @(
        $selectedGames |
            Where-Object {
                $projectPaths.games.Entries.PSObject.Properties[$_].Value.Category -eq 'builds'
            }
    ).Count -gt 0
    if ($usesNa228Build -and -not $SkipActualization) {
        & $projectPaths.files.actualize_command na228
    }

    $nextPinePort = $pinePortBase
    for ($index = 0; $index -lt $selectedGames.Count; $index++) {
        $game = $selectedGames[$index]
        while ($usedPinePorts.Contains($nextPinePort)) {
            $nextPinePort++
        }
        if ($nextPinePort -gt 65535) {
            throw 'No free PINE port remains in the configured range.'
        }
        $pinePort = $nextPinePort
        [void]$usedPinePorts.Add($pinePort)
        $nextPinePort++
        $process = & $pcsx2Launcher `
            -IsoPath $selectedIsoPaths[$game] `
            -Arguments @('-pine-port', [string]$pinePort) `
            -PassThru

        $launchedGames.Add([pscustomobject]@{
            Game = $game
            Process = $process
            PinePort = $pinePort
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
            PinePort = $launch.PinePort
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
