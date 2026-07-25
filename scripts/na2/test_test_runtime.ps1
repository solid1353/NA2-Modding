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

$testRoot = Join-Path ([IO.Path]::GetTempPath()) "na2-runtime-tests-$PID-$([guid]::NewGuid().ToString('N'))"
try {
    $repository = Join-Path $testRoot 'repository'
    $workRoot = Join-Path $repository 'work'
    $workerRoot = Join-Path $workRoot 'General'
    $pcsx2 = Join-Path $testRoot 'pcsx2'
    $inis = Join-Path $pcsx2 'inis'
    $gameSettings = Join-Path $pcsx2 'gamesettings'
    $sourceMemcards = Join-Path $pcsx2 'memcards'
    New-Item -ItemType Directory -Force -Path @(
        $repository, $workRoot, $inis, $gameSettings, $sourceMemcards
    ) | Out-Null

    $iniPath = Join-Path $inis 'PCSX2.ini'
    $originalIni = @'
[Folders]
Snapshots = snaps
SaveStates = sstates
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
    [IO.File]::WriteAllBytes((Join-Path $sourceMemcards 'Mcd001.ps2'), [byte[]](1, 2, 3))
    $projectPaths = [pscustomobject]@{
        repository = $repository
        work = $workRoot
    }
    $pcsx2Context = [pscustomobject]@{
        Ini = $iniPath
        GameSettings = $gameSettings
        MemoryCards = $sourceMemcards
    }
    $worker = Get-Na2WorkerContext -WorkerRoot $workerRoot -ProjectPaths $projectPaths
    $layout = New-Na2TestRuntimeLayout -Worker $worker
    $identity = [pscustomobject]@{ Serial = 'SLOP-NA228'; CRC = '12345678' }

    $mutex = Enter-Na2Pcsx2ConfigurationLock -IniPath $iniPath
    try {
        $context = Enter-Na2TestRuntimeConfiguration `
            -Pcsx2 $pcsx2Context `
            -Layout $layout `
            -IsoIdentity $identity `
            -AgentName 'Codex' `
            -TaskIdentity 'runtime-test' `
            -StartPaused $true
        $injected = [IO.File]::ReadAllText($iniPath)
        Assert-Na2RuntimeTest `
            -Condition ((Get-Na2IniValue -Text $injected -Section 'Folders' -Key 'Logs') -ceq $layout.LogDirectory) `
            -Message 'Runtime logs were not redirected to the worker.'
        Assert-Na2RuntimeTest `
            -Condition ((Get-Na2IniValue -Text $injected -Section 'Folders' -Key 'SaveStates') -ceq $layout.SaveStates) `
            -Message 'Runtime savestates were not redirected to the worker.'
        Assert-Na2RuntimeTest `
            -Condition ((Get-Na2IniValue -Text $injected -Section 'SPU2/Output' -Key 'OutputMuted') -ceq 'true') `
            -Message 'Runtime audio was not muted.'
        Assert-Na2RuntimeTest `
            -Condition ((Get-Na2IniValue -Text $injected -Section 'UI' -Key 'StartPaused') -ceq 'true') `
            -Message 'Requested paused-start state was not isolated under the worker runtime.'
        Assert-Na2RuntimeTest `
            -Condition (Test-Path -LiteralPath $context.MemoryCard.TaskCardPath -PathType Leaf) `
            -Message 'Worker memory card was not created under the worker root.'
        Assert-Na2RuntimeTest `
            -Condition ($context.MemoryCard.TaskCardPath.StartsWith($workerRoot, [StringComparison]::OrdinalIgnoreCase)) `
            -Message 'Worker memory card escaped the worker root.'

        Restore-Na2TestRuntimeConfiguration -Context $context
        Assert-Na2RuntimeTest `
            -Condition ([IO.File]::ReadAllText($iniPath) -ceq $originalIni) `
            -Message 'Shared PCSX2 settings were not restored immediately.'
        Assert-Na2RuntimeTest `
            -Condition (-not (Test-Path -LiteralPath $context.MemoryCard.GameSettingsPath)) `
            -Message 'Synthetic per-game memory-card settings were not restored.'

        $guarded = [IO.File]::ReadAllText($iniPath)
        $guarded = Set-Na2IniValue -Text $guarded -Section 'Folders' -Key 'Logs' -Value 'user-change'
        [IO.File]::WriteAllText($iniPath, $guarded)
        Restore-Na2TestRuntimeConfiguration -Context $context -OnlyIfInjected
        Assert-Na2RuntimeTest `
            -Condition ((Get-Na2IniValue -Text ([IO.File]::ReadAllText($iniPath)) -Section 'Folders' -Key 'Logs') -ceq 'user-change') `
            -Message 'Exit-time safety restoration overwrote a non-agent setting change.'
    }
    finally {
        Exit-Na2Pcsx2ConfigurationLock -Mutex $mutex
    }

    Remove-Na2TestRuntimeLayout -Layout $layout -Worker $worker -WorkRoot $workRoot
    Assert-Na2RuntimeTest `
        -Condition (-not (Test-Path -LiteralPath $layout.TempRoot)) `
        -Message 'Runtime cleanup retained disposable cache directories.'
    Write-Host 'NA2 isolated PCSX2 runtime tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
