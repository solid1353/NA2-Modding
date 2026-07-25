[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'worker_paths.ps1')
. (Join-Path $PSScriptRoot 'test_runtime.ps1')

function Assert-Na2RuntimeTest {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

$testRoot = Join-Path ([IO.Path]::GetTempPath()) (
    "na2-runtime-tests-$PID-$([guid]::NewGuid().ToString('N'))"
)
try {
    $repository = Join-Path $testRoot 'repository'
    $workRoot = Join-Path $repository 'work'
    $workerRoot = Join-Path $workRoot 'General'
    $pcsx2 = Join-Path $workerRoot 'pcsx2'
    $inis = Join-Path $pcsx2 'inis'
    $gameSettings = Join-Path $pcsx2 'gamesettings'
    $memoryCards = Join-Path $pcsx2 'memcards'
    New-Item -ItemType Directory -Force -Path @(
        $repository
        $workRoot
        $workerRoot
        $pcsx2
        $inis
        $gameSettings
        $memoryCards
    ) | Out-Null

    $iniPath = Join-Path $inis 'PCSX2.ini'
    $originalIni = @'
[Folders]
Snapshots = snaps
Savestates = sstates
SaveStates = obsolete-artifact-path
MemoryCards = memcards
Logs = logs
Cache = cache
Videos = videos

[EmuCore]
EnablePINE = true
PINESlot = 28011
BlockDumpSaveDirectory =

[EmuCore/GS]
HWDumpDirectory =
SWDumpDirectory =

[SPU2/Output]
OutputMuted = false

[UI]
StartPaused = false

[MemoryCards]
Slot1_Enable = true
Slot1_Filename = Mcd001.ps2
'@
    [IO.File]::WriteAllText($iniPath, $originalIni)
    [IO.File]::WriteAllBytes(
        (Join-Path $memoryCards 'Mcd001.ps2'),
        [byte[]](1, 2, 3)
    )
    [IO.File]::WriteAllBytes(
        (Join-Path $memoryCards 'Mcd001_NA2.ps2'),
        [byte[]](4, 5, 6)
    )
    $identity = [pscustomobject]@{
        Serial = 'SLOP-NA228'
        CRC = '12345678'
    }
    $gameSettingsPath = Join-Path (
        $gameSettings
    ) "$($identity.Serial)_$($identity.CRC).ini"
    $gameSettingsText = @'
[MemoryCards]
Slot1_Filename = Mcd001_NA2.ps2

[EmuCore/GS]
VsyncEnable = 1
'@
    [IO.File]::WriteAllText($gameSettingsPath, $gameSettingsText)

    $projectPaths = [pscustomobject]@{
        repository = $repository
        work = $workRoot
    }
    $pcsx2Context = [pscustomobject]@{
        Root = $pcsx2
        Ini = $iniPath
        GameSettings = $gameSettings
        MemoryCards = $memoryCards
        SaveStates = Join-Path $pcsx2 'sstates'
        Snapshots = Join-Path $pcsx2 'snaps'
    }
    $worker = Get-Na2WorkerContext `
        -WorkerRoot $workerRoot `
        -ProjectPaths $projectPaths
    $layout = New-Na2TestRuntimeLayout -Worker $worker
    $context = Set-Na2TestRuntimeConfiguration `
        -Pcsx2 $pcsx2Context `
        -Layout $layout `
        -IsoIdentity $identity `
        -StartPaused $true
    $configured = [IO.File]::ReadAllText($iniPath)

    Assert-Na2RuntimeTest `
        -Condition ((Get-Na2IniValue -Text $configured -Section 'Folders' -Key 'Logs') -ceq $layout.LogDirectory) `
        -Message 'Runtime logs were not redirected to the worker.'
    Assert-Na2RuntimeTest `
        -Condition ((Get-Na2IniValue -Text $configured -Section 'Folders' -Key 'Savestates') -ceq 'sstates') `
        -Message 'Runtime savestates do not use the clone persistent directory.'
    Assert-Na2RuntimeTest `
        -Condition ($null -eq (Get-Na2IniValue -Text $configured -Section 'Folders' -Key 'SaveStates')) `
        -Message 'The obsolete incorrectly-cased SaveStates setting was retained.'
    Assert-Na2RuntimeTest `
        -Condition ((Get-Na2IniValue -Text $configured -Section 'Folders' -Key 'Snapshots') -ceq 'snaps') `
        -Message 'Runtime screenshots do not use the clone persistent directory.'
    Assert-Na2RuntimeTest `
        -Condition ((Get-Na2IniValue -Text $configured -Section 'Folders' -Key 'MemoryCards') -ceq 'memcards') `
        -Message 'Runtime configuration rewrote the clone memory-card directory.'
    Assert-Na2RuntimeTest `
        -Condition ((Get-Na2IniValue -Text $configured -Section 'SPU2/Output' -Key 'OutputMuted') -ceq 'true') `
        -Message 'Runtime audio was not muted.'
    Assert-Na2RuntimeTest `
        -Condition ((Get-Na2IniValue -Text $configured -Section 'UI' -Key 'StartPaused') -ceq 'true') `
        -Message 'Requested paused-start state was not retained in the clone.'
    Assert-Na2RuntimeTest `
        -Condition ((Get-Na2IniValue -Text $configured -Section 'Hotkeys' -Key 'Screenshot') -ceq 'Keyboard/F8') `
        -Message 'The maintained frame-screenshot hotkey was not configured.'
    Assert-Na2RuntimeTest `
        -Condition ((Get-Na2IniValue -Text $configured -Section 'EmuCore/GS' -Key 'ScreenshotFormat') -ceq '0') `
        -Message 'The maintained frame-screenshot format was not configured as PNG.'
    Assert-Na2RuntimeTest `
        -Condition ((Get-Na2IniValue -Text $configured -Section 'EmuCore/GS' -Key 'OrganizeScreenshotsByGame') -ceq 'false') `
        -Message 'The maintained frame-screenshot output was not kept in the clone snapshot directory.'
    Assert-Na2RuntimeTest `
        -Condition ($context.MemoryCardName -ceq 'Mcd001_NA2.ps2') `
        -Message 'Runtime configuration did not honor the clone per-game card selection.'
    Assert-Na2RuntimeTest `
        -Condition ($context.MemoryCardPath -ceq (Join-Path $memoryCards 'Mcd001_NA2.ps2')) `
        -Message 'Runtime configuration did not resolve the clone card in place.'
    Assert-Na2RuntimeTest `
        -Condition ($context.SaveStates -ceq (Join-Path $pcsx2 'sstates')) `
        -Message 'Runtime operations do not target the clone persistent savestate directory.'
    Assert-Na2RuntimeTest `
        -Condition ($context.Snapshots -ceq (Join-Path $pcsx2 'snaps')) `
        -Message 'Runtime operations do not target the clone persistent screenshot directory.'
    Assert-Na2RuntimeTest `
        -Condition ([IO.File]::ReadAllText($gameSettingsPath) -ceq $gameSettingsText) `
        -Message 'Runtime configuration rewrote the clone per-game settings.'
    Assert-Na2RuntimeTest `
        -Condition (-not (Test-Path -LiteralPath (Join-Path $worker.Artifacts 'memcards'))) `
        -Message 'Runtime configuration created an obsolete task memory-card copy.'

    $fallbackIdentity = [pscustomobject]@{
        Serial = 'SLOP-NA228'
        CRC = '87654321'
    }
    $fallback = Set-Na2TestRuntimeConfiguration `
        -Pcsx2 $pcsx2Context `
        -Layout $layout `
        -IsoIdentity $fallbackIdentity
    Assert-Na2RuntimeTest `
        -Condition ($fallback.MemoryCardName -ceq 'Mcd001.ps2') `
        -Message 'Runtime configuration did not fall back to the clone global card selection.'

    Remove-Na2TestRuntimeLayout `
        -Layout $layout `
        -Worker $worker `
        -WorkRoot $workRoot
    Assert-Na2RuntimeTest `
        -Condition (-not (Test-Path -LiteralPath $layout.TempRoot)) `
        -Message 'Runtime cleanup retained disposable cache directories.'
    Assert-Na2RuntimeTest `
        -Condition (Test-Path -LiteralPath $context.MemoryCardPath -PathType Leaf) `
        -Message 'Runtime cleanup removed the persistent clone memory card.'
    Assert-Na2RuntimeTest `
        -Condition ((Get-Na2IniValue -Text ([IO.File]::ReadAllText($iniPath)) -Section 'Folders' -Key 'Logs') -ceq $layout.LogDirectory) `
        -Message 'Runtime cleanup unexpectedly restored persistent clone settings.'

    Write-Host 'NA2 isolated PCSX2 runtime tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
