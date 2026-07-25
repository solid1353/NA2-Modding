# Loads a task-owned PCSX2 state, saves a fresh state through PINE, and
# extracts the embedded Screenshot.png without focusing the emulator.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$WorkerRoot,
    [Parameter(Mandatory = $true)][string]$IsoPath,
    [Parameter(Mandatory = $true)][string]$StatePath,
    [Parameter(Mandatory = $true)][string]$GameStatePrefix,
    [Parameter(Mandatory = $true)][string]$ScreenshotPath,
    [ValidateRange(0, 9)][int]$LoadSlot = 0,
    [ValidateRange(0, 9)][int]$CaptureSlot = 1,
    [ValidateRange(1, 120)][int]$TimeoutSeconds = 30,
    [ValidateRange(0, 5000)][int]$RenderMilliseconds = 500
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($LoadSlot -eq $CaptureSlot) {
    throw 'LoadSlot and CaptureSlot must differ.'
}
if ($GameStatePrefix.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0) {
    throw 'GameStatePrefix contains invalid filename characters.'
}

$repository = [IO.Path]::GetFullPath((Get-Location).Path)

function Resolve-RepositoryPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if ([IO.Path]::IsPathRooted($Path)) {
        throw "$Label must be repository-relative."
    }
    $resolved = [IO.Path]::GetFullPath((Join-Path $repository $Path))
    if (-not $resolved.StartsWith(
        $repository + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        throw "$Label escapes the repository."
    }
    return $resolved
}

function Read-Exact {
    param(
        [Parameter(Mandatory = $true)][IO.Stream]$Stream,
        [Parameter(Mandatory = $true)][int]$Size
    )

    $result = [byte[]]::new($Size)
    $offset = 0
    while ($offset -lt $Size) {
        $read = $Stream.Read($result, $offset, $Size - $offset)
        if ($read -le 0) {
            throw 'PINE closed the connection during a reply.'
        }
        $offset += $read
    }
    Write-Output -NoEnumerate $result
}

function Save-PineState {
    param(
        [Parameter(Mandatory = $true)][int]$Port,
        [Parameter(Mandatory = $true)][int]$Slot,
        [Parameter(Mandatory = $true)][DateTime]$Deadline
    )

    $client = $null
    while ([DateTime]::UtcNow -lt $Deadline) {
        try {
            $client = [Net.Sockets.TcpClient]::new()
            $client.Connect('127.0.0.1', $Port)
            break
        }
        catch {
            if ($null -ne $client) {
                $client.Dispose()
                $client = $null
            }
            Start-Sleep -Milliseconds 100
        }
    }
    if ($null -eq $client -or -not $client.Connected) {
        throw "Could not connect to the task-owned PINE port $Port."
    }

    try {
        $stream = $client.GetStream()
        $remaining = [Math]::Max(
            1,
            [int][Math]::Ceiling(($Deadline - [DateTime]::UtcNow).TotalMilliseconds)
        )
        $stream.ReadTimeout = $remaining
        $stream.WriteTimeout = $remaining
        $payload = [byte[]]@(0x09, [byte]$Slot)
        $header = [BitConverter]::GetBytes([int]($payload.Length + 4))
        $stream.Write($header, 0, $header.Length)
        $stream.Write($payload, 0, $payload.Length)
        $stream.Flush()

        $replyHeader = Read-Exact -Stream $stream -Size 4
        $replySize = [BitConverter]::ToInt32($replyHeader, 0)
        if ($replySize -lt 5 -or $replySize -gt 450000) {
            throw "PINE returned an invalid reply size: $replySize."
        }
        $reply = Read-Exact -Stream $stream -Size ($replySize - 4)
        if ($reply[0] -ne 0) {
            throw 'PCSX2 rejected the PINE save-state request.'
        }
        if ($reply.Length -ne 1) {
            throw 'PINE save-state reply contained unexpected data.'
        }
    }
    finally {
        $client.Dispose()
    }
}

function Get-FileSignature {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }
    $item = Get-Item -LiteralPath $Path
    return "$($item.Length):$($item.LastWriteTimeUtc.Ticks)"
}

$worker = Resolve-RepositoryPath -Path $WorkerRoot -Label 'WorkerRoot'
$workerPrefix = $worker + [IO.Path]::DirectorySeparatorChar
$iso = Resolve-RepositoryPath -Path $IsoPath -Label 'IsoPath'
$state = Resolve-RepositoryPath -Path $StatePath -Label 'StatePath'
$screenshot = Resolve-RepositoryPath `
    -Path $ScreenshotPath `
    -Label 'ScreenshotPath'
foreach ($path in @($iso, $state, $screenshot)) {
    if (-not $path.StartsWith(
        $workerPrefix,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Task path escapes WorkerRoot: $path"
    }
}

$pcsx2 = Join-Path $worker 'pcsx2'
$executable = Join-Path $pcsx2 'pcsx2-qt.exe'
$ini = Join-Path $pcsx2 'inis\PCSX2.ini'
$stateDirectory = Join-Path $pcsx2 'sstates'
$log = Join-Path $pcsx2 'logs\emulog.txt'
foreach ($required in @($executable, $ini, $iso, $state)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required file does not exist: $required"
    }
}

$iniText = Get-Content -Raw -LiteralPath $ini
if ($iniText -notmatch '(?m)^\s*EnablePINE\s*=\s*true\s*$') {
    throw 'PINE is not enabled in the task-owned PCSX2 configuration.'
}
if ($iniText -notmatch '(?m)^\s*PINESlot\s*=\s*(\d+)\s*$') {
    throw 'The task-owned PCSX2 configuration has no valid PINESlot.'
}
$pinePort = [int]$Matches[1]

New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
New-Item `
    -ItemType Directory `
    -Path (Split-Path -Parent $screenshot) `
    -Force | Out-Null
if (Test-Path -LiteralPath $screenshot -PathType Leaf) {
    Remove-Item -LiteralPath $screenshot -Force
}

$loadState = Join-Path (
    $stateDirectory
) ('{0}.{1:D2}.p2s' -f $GameStatePrefix, $LoadSlot)
$capturedState = Join-Path (
    $stateDirectory
) ('{0}.{1:D2}.p2s' -f $GameStatePrefix, $CaptureSlot)
Copy-Item -LiteralPath $state -Destination $loadState -Force
$previousCaptureSignature = Get-FileSignature -Path $capturedState

$process = $null
try {
    if (Test-Path -LiteralPath $log -PathType Leaf) {
        Remove-Item -LiteralPath $log -Force
    }
    $process = Start-Process `
        -FilePath $executable `
        -WorkingDirectory $pcsx2 `
        -ArgumentList @('-batch', '-state', "$LoadSlot", "`"$iso`"") `
        -WindowStyle Hidden `
        -PassThru

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $stateLoaded = $false
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($process.HasExited) {
            throw "Owned PCSX2 exited with code $($process.ExitCode)."
        }
        if (Test-Path -LiteralPath $log -PathType Leaf) {
            $logText = Get-Content -Raw -LiteralPath $log
            $stateLoaded = (
                $logText.Contains('Loading SPU2') -and
                $logText.Contains('Loading GS')
            )
        }
        if ($stateLoaded) {
            break
        }
        Start-Sleep -Milliseconds 100
    }
    if (-not $stateLoaded) {
        throw 'Owned PCSX2 did not confirm the savestate load.'
    }

    Start-Sleep -Milliseconds $RenderMilliseconds
    Save-PineState `
        -Port $pinePort `
        -Slot $CaptureSlot `
        -Deadline $deadline

    $lastSignature = $null
    $stableSamples = 0
    while ([DateTime]::UtcNow -lt $deadline) {
        $signature = Get-FileSignature -Path $capturedState
        if (
            $null -ne $signature -and
            $signature -cne $previousCaptureSignature
        ) {
            if ($signature -ceq $lastSignature) {
                $stableSamples += 1
            }
            else {
                $lastSignature = $signature
                $stableSamples = 1
            }
            if ($stableSamples -ge 3) {
                break
            }
        }
        Start-Sleep -Milliseconds 200
    }
    if ($stableSamples -lt 3) {
        throw 'PCSX2 did not create a stable PINE savestate.'
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($capturedState)
    try {
        $entry = $archive.Entries |
            Where-Object {
                $_.FullName -ceq 'Screenshot.png' -and $_.Length -gt 0
            } |
            Select-Object -First 1
        if ($null -eq $entry) {
            throw 'The fresh PINE savestate has no Screenshot.png.'
        }
        $temporary = "$screenshot.$PID.tmp"
        try {
            $input = $entry.Open()
            try {
                $output = [IO.File]::Open(
                    $temporary,
                    [IO.FileMode]::Create,
                    [IO.FileAccess]::Write,
                    [IO.FileShare]::None
                )
                try {
                    $input.CopyTo($output)
                }
                finally {
                    $output.Dispose()
                }
            }
            finally {
                $input.Dispose()
            }
            [IO.File]::Move($temporary, $screenshot, $true)
        }
        finally {
            if (Test-Path -LiteralPath $temporary) {
                Remove-Item -LiteralPath $temporary -Force
            }
        }
    }
    finally {
        $archive.Dispose()
    }

    Get-Item -LiteralPath $screenshot |
        Select-Object FullName, Length, LastWriteTime
}
finally {
    if ($null -ne $process -and -not $process.HasExited) {
        [void]$process.CloseMainWindow()
        if (-not $process.WaitForExit(3000)) {
            Stop-Process -Id $process.Id -Force
            $process.WaitForExit()
        }
    }
}
