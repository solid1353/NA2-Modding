[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'test_memory_card.ps1')

function Assert-Na2TestMemoryCard {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

function Test-Na2BytesEqual {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Left,
        [Parameter(Mandatory = $true)][byte[]]$Right
    )
    return [Convert]::ToHexString($Left) -ceq [Convert]::ToHexString($Right)
}

$testRoot = Join-Path ([IO.Path]::GetTempPath()) "na2-test-card-$PID-$([guid]::NewGuid().ToString('N'))"
try {
    $inis = Join-Path $testRoot 'inis'
    $gameSettings = Join-Path $testRoot 'gamesettings'
    $sourceMemcards = Join-Path $testRoot 'source-memcards'
    $taskMemcards = Join-Path $testRoot 'task-memcards'
    New-Item -ItemType Directory -Force -Path $inis, $gameSettings, $sourceMemcards | Out-Null

    $globalIni = Join-Path $inis 'PCSX2.ini'
    $globalText = "[MemoryCards]`r`nSlot1_Enable = true`r`nSlot1_Filename = Mcd001.ps2`r`n"
    [IO.File]::WriteAllText($globalIni, $globalText)
    [IO.File]::WriteAllBytes((Join-Path $sourceMemcards 'Mcd001.ps2'), [byte[]](1, 2, 3))
    [IO.File]::WriteAllBytes((Join-Path $sourceMemcards 'Mcd001_NA2.ps2'), [byte[]](4, 5, 6))

    $gameIni = Join-Path $gameSettings 'SLOP-NA228_12345678.ini'
    $originalGameText = "[EmuCore/GS]`r`nAspectRatio = 4:3`r`n`r`n[MemoryCards]`r`nSlot1_Enable = true`r`nSlot1_Filename = Mcd001_NA2.ps2`r`n"
    $originalGameBytes = [Text.UTF8Encoding]::new($false).GetBytes($originalGameText)
    [IO.File]::WriteAllBytes($gameIni, $originalGameBytes)

    $context = Enter-Na2TestMemoryCard `
        -GlobalIniPath $globalIni `
        -GameSettingsDirectory $gameSettings `
        -SourceMemoryCardsDirectory $sourceMemcards `
        -TaskMemoryCardsDirectory $taskMemcards `
        -Serial 'SLOP-NA228' `
        -CRC '12345678' `
        -AgentName 'Codex' `
        -TaskIdentity '019f-test'
    Assert-Na2TestMemoryCard -Condition $context.TaskCardCreated -Message 'First use did not create a private card.'
    Assert-Na2TestMemoryCard `
        -Condition ($context.TaskCardName -ceq 'Mcd001_NA2_Codex_019f-test.ps2') `
        -Message "Unexpected private-card name: $($context.TaskCardName)"
    Assert-Na2TestMemoryCard `
        -Condition (Test-Na2BytesEqual -Left ([IO.File]::ReadAllBytes($context.TaskCardPath)) -Right ([byte[]](4, 5, 6))) `
        -Message 'Private card was not cloned from the game-specific base card.'
    $temporaryGameText = [IO.File]::ReadAllText($gameIni)
    Assert-Na2TestMemoryCard `
        -Condition ($temporaryGameText -match 'Slot1_Filename = Mcd001_NA2_Codex_019f-test\.ps2') `
        -Message 'Temporary per-game selection does not point to the private card.'
    Exit-Na2TestMemoryCard -Context $context | Out-Null
    Assert-Na2TestMemoryCard `
        -Condition (Test-Na2BytesEqual -Left ([IO.File]::ReadAllBytes($gameIni)) -Right $originalGameBytes) `
        -Message 'Existing per-game settings were not restored byte-for-byte.'

    [IO.File]::WriteAllBytes($context.TaskCardPath, [byte[]](7, 8, 9))
    $reused = Enter-Na2TestMemoryCard `
        -GlobalIniPath $globalIni `
        -GameSettingsDirectory $gameSettings `
        -SourceMemoryCardsDirectory $sourceMemcards `
        -TaskMemoryCardsDirectory $taskMemcards `
        -Serial 'SLOP-NA228' `
        -CRC '12345678' `
        -AgentName 'Codex' `
        -TaskIdentity '019f-test'
    Assert-Na2TestMemoryCard -Condition (-not $reused.TaskCardCreated) -Message 'Existing task card was not reused.'
    Assert-Na2TestMemoryCard `
        -Condition (Test-Na2BytesEqual -Left ([IO.File]::ReadAllBytes($reused.TaskCardPath)) -Right ([byte[]](7, 8, 9))) `
        -Message 'Reusing a private card overwrote its task progress.'
    Exit-Na2TestMemoryCard -Context $reused | Out-Null

    $fallback = Enter-Na2TestMemoryCard `
        -GlobalIniPath $globalIni `
        -GameSettingsDirectory $gameSettings `
        -SourceMemoryCardsDirectory $sourceMemcards `
        -TaskMemoryCardsDirectory $taskMemcards `
        -Serial 'SLPS-25837' `
        -CRC '87654321' `
        -AgentName 'Agent:One' `
        -TaskIdentity 'fallback/task'
    Assert-Na2TestMemoryCard `
        -Condition ($fallback.BaseCardName -ceq 'Mcd001.ps2') `
        -Message 'Missing per-game settings did not fall back to the global card.'
    Assert-Na2TestMemoryCard `
        -Condition ($fallback.TaskCardName -ceq 'Mcd001_Agent_One_fallback_task.ps2') `
        -Message "Unsafe filename components were not sanitized: $($fallback.TaskCardName)"
    Exit-Na2TestMemoryCard -Context $fallback | Out-Null
    Assert-Na2TestMemoryCard `
        -Condition (-not (Test-Path -LiteralPath $fallback.GameSettingsPath)) `
        -Message 'Synthetic per-game settings were not removed during restoration.'

    Write-Host 'NA2 private test-memory-card tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
