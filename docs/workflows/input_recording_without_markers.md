# Input-recording workflow without markers

The agent chooses how to investigate a markerless replay using these commands.

Set `$exactChatTitle` to the exact chat title and `$recordingName` to the
task's recording. Set `$game` to the user-supplied ISO path, or `'b'` to reuse
the latest cached base ISO without building. Set `$launchOptions` to an array
of the requested launch options, or `@()` when none were requested.

```powershell
. .\scripts\lib\paths.ps1
$paths = Get-Na2Paths
$taskRoot = Join-Path $paths.work $exactChatTitle
$logs = Join-Path $taskRoot 'logs'
$env:NA228_TASK_WORK_ROOT = $taskRoot
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$launch = & .\na228.ps1 $game -p $recordingName -agent-replay `
    @launchOptions -logfile (Join-Path $logs 'pcsx2.log')
$process = $launch.Process
$pinePort = $launch.PinePort
```

Agent replay starts paused at frame zero, surfaceless and muted, with settings
writes disabled and memory-card writes discarded. The launcher allocates the
PINE port and writes the requested log file.

```powershell
$runner = Join-Path $paths.scripts 'lib/run_python.ps1'
$pine = @{
    PackageSet = 'builder'
    Script = $paths.files.pcsx2_pine_command
    NoBytecode = $true
}
$endpoint = @('--port', [string]$pinePort)

& $runner @pine -ArgumentList ($endpoint + @('status'))
& $runner @pine -ArgumentList ($endpoint + @('replay-status'))
& $runner @pine -ArgumentList ($endpoint + @('replay-step', '1'))
& $runner @pine -ArgumentList ($endpoint + @(
    'replay-screenshot', (Join-Path $logs 'frame.png')))
& $runner @pine -ArgumentList ($endpoint + @('read', '0x00100000', '16'))
& $runner @pine -ArgumentList ($endpoint + @(
    'read-batch', '0x00100000:16', '0x00100040:16'))
& $runner @pine -ArgumentList ($endpoint + @('resume'))
& $runner @pine -ArgumentList ($endpoint + @('pause'))
```

Stepping and screenshots require paused playback. `replay-step` advances exact
replay frames, only forward, and cannot pass the replay endpoint. Use multiple calls
when a requested interval exceeds the client's three-second timeout. Restart
the replay to inspect an earlier position.

To capture and replay a GS dump:

```powershell
$dumpFrames = 4
$dumpBase = Join-Path $logs 'frame.png'
& $runner @pine -ArgumentList ($endpoint + @(
    'replay-gs-dump', $dumpBase, [string]$dumpFrames))
& $runner @pine -ArgumentList ($endpoint + @(
    'replay-step', [string]($dumpFrames + 5)))

$gsRunner = Join-Path $paths.pcsx2_dev 'pcsx2-gsrunnerx64-avx2-dev.exe'
$dump = Join-Path $logs 'frame.gs.zst'
& $gsRunner -surfaceless -renderer dx12 `
    -dumpdir (Join-Path $logs 'gs-dx12') -- $dump
& $gsRunner -surfaceless -renderer sw `
    -dumpdir (Join-Path $logs 'gs-sw') -- $dump
```

The frame count is the number of GS frames recorded. Five additional replay
frames ensure that the dump starts and is flushed before inspection. The GS
runner accepts the same dump under different renderers without replaying the
game.

```powershell
& $runner @pine -ArgumentList ($endpoint + @('replay-shutdown'))
Wait-Process -InputObject $process -ErrorAction SilentlyContinue
```
