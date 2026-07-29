[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\ini.ps1')

function Assert-Na2ActualizeTest {
    param(
        [Parameter(Mandatory)][bool]$Condition,
        [Parameter(Mandatory)][string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

$testRoot = Join-Path (
    [IO.Path]::GetTempPath()
) ('na2-actualization-test-{0}' -f [guid]::NewGuid().ToString('N'))

try {
    $repository = Join-Path $testRoot 'repository'
    $build = Join-Path $repository 'build'
    $pcsx2Files = Join-Path $repository 'pcsx2_files'
    $cheats = Join-Path $pcsx2Files 'cheats'
    $gameSettings = Join-Path $pcsx2Files 'game_settings'
    $memoryCards = Join-Path $pcsx2Files 'memory_cards'
    New-Item -ItemType Directory -Force `
        -Path (
            $build,
            $cheats,
            $gameSettings,
            $memoryCards
        ) |
        Out-Null

    $cheatTemplate = Join-Path $cheats 'SLOP-NA228.pnach'
    $gameSettingsTemplate = Join-Path $gameSettings 'SLOP-NA228.ini'
    [IO.File]::WriteAllText(
        $cheatTemplate,
        "// [Intro skips]`npatch=1,EE,00100000,word,00000000`n",
        [Text.UTF8Encoding]::new($false)
    )
    [IO.File]::WriteAllText(
        $gameSettingsTemplate,
        (
            "[EmuCore]`nInputProfileName = Comparison`n`n" +
            "[MemoryCards]`nSlot1_Filename = Base.ps2`n"
        ),
        [Text.UTF8Encoding]::new($false)
    )
    $currentMemoryCard = Join-Path $memoryCards 'NA228 - Current.ps2'
    $previousMemoryCard = Join-Path $memoryCards 'NA228 - Previous.ps2'
    $candidateMemoryCard = Join-Path $memoryCards 'NA228 - Candidate.ps2'
    $memoryCardInputs = @(
        [pscustomobject]@{
            Path = $currentMemoryCard
            Bytes = [byte[]](1, 2, 3, 4)
        }
        [pscustomobject]@{
            Path = $previousMemoryCard
            Bytes = [byte[]](5, 6, 7, 8)
        }
        [pscustomobject]@{
            Path = $candidateMemoryCard
            Bytes = [byte[]](9, 10, 11, 12)
        }
    )
    foreach ($memoryCardInput in $memoryCardInputs) {
        [IO.File]::WriteAllBytes(
            $memoryCardInput.Path,
            $memoryCardInput.Bytes
        )
    }

    $currentIso = Join-Path $build 'Current.iso'
    $previousIso = Join-Path $build 'Previous.iso'
    $candidateIso = Join-Path $build 'Candidate.iso'
    [IO.File]::WriteAllText($currentIso, 'current')
    [IO.File]::WriteAllText($previousIso, 'previous')
    [IO.File]::WriteAllText($candidateIso, 'candidate')

    $projectPaths = [pscustomobject]@{
        pcsx2_files = $pcsx2Files
        pcsx2_cheats = $cheats
        pcsx2_game_settings = $gameSettings
        pcsx2_memory_cards = $memoryCards
        files = [pscustomobject]@{
            cheat_template = $cheatTemplate
            gamesettings_template = $gameSettingsTemplate
            current_memory_card = $currentMemoryCard
            previous_memory_card = $previousMemoryCard
            candidate_memory_card = $candidateMemoryCard
            current_iso = $currentIso
            previous_iso = $previousIso
            candidate_iso = $candidateIso
        }
    }
    $identityResolver = {
        param([string]$Path)
        switch ([IO.Path]::GetFileNameWithoutExtension($Path)) {
            'Current' {
                [pscustomobject]@{ Serial = 'SLOP-NA228'; CRC = '11111111' }
            }
            'Previous' {
                [pscustomobject]@{ Serial = 'SLOP-NA228'; CRC = '11111111' }
            }
            'Candidate' {
                [pscustomobject]@{ Serial = 'SLPS-22228'; CRC = '33333333' }
            }
            default {
                throw "Unexpected ISO: $Path"
            }
        }
    }

    $actualizer = Join-Path $PSScriptRoot 'sync_game_files.ps1'
    $first = & $actualizer `
        -ProjectPaths $projectPaths `
        -IdentityResolver $identityResolver

    Assert-Na2ActualizeTest `
        -Condition ($first.Roles.Count -eq 3) `
        -Message 'First run did not actualize all three built images.'
    Assert-Na2ActualizeTest `
        -Condition (@($first.EnabledCheats) -contains 'Intro skips') `
        -Message 'Enabled cheat reporting was lost.'
    Assert-Na2ActualizeTest `
        -Condition (@($first.CreatedGameSettings).Count -eq 2) `
        -Message 'Shared Current/Previous identity was not deduplicated.'
    $currentSettingsName = (
        $first.Roles |
            Where-Object Role -CEQ 'Current' |
            Select-Object -First 1
    ).GameSettingsName

    foreach ($role in $first.Roles) {
        $settingsPath = Join-Path $gameSettings $role.GameSettingsName
        $cheatPath = Join-Path $cheats $role.PnachName
        Assert-Na2ActualizeTest `
            -Condition (Test-Path -LiteralPath $settingsPath -PathType Leaf) `
            -Message "Missing GameSettings: $($role.GameSettingsName)"
        Assert-Na2ActualizeTest `
            -Condition ([string]::IsNullOrWhiteSpace(
                [string](Get-Item -LiteralPath $settingsPath -Force).LinkType
            )) `
            -Message "GameSettings is not a real file: $($role.GameSettingsName)"
        $settingsText = [IO.File]::ReadAllText($settingsPath)
        $settingsOwner = if (
            $role.GameSettingsName -ceq $currentSettingsName
        ) {
            'Current'
        }
        else {
            $role.Role
        }
        $expectedMemoryCard = "NA228 - $settingsOwner.ps2"
        Assert-Na2ActualizeTest `
            -Condition (
                (Get-Na2IniValue `
                    -Text $settingsText `
                    -Section 'MemoryCards' `
                    -Key 'Slot1_Filename') -ceq
                $expectedMemoryCard
            ) `
            -Message "GameSettings memory card is wrong: $($role.Role)"
        Assert-Na2ActualizeTest `
            -Condition (Test-Path -LiteralPath $cheatPath -PathType Leaf) `
            -Message "Cheat symlink is broken: $($role.PnachName)"
        Assert-Na2ActualizeTest `
            -Condition (
                [IO.File]::ReadAllText($cheatPath) -ceq
                [IO.File]::ReadAllText($cheatTemplate)
            ) `
            -Message "Cheat symlink target is wrong: $($role.PnachName)"
    }

    [IO.File]::AppendAllText(
        $cheatTemplate,
        "// link identity probe`n",
        [Text.UTF8Encoding]::new($false)
    )
    foreach ($role in $first.Roles) {
        $cheatPath = Join-Path $cheats $role.PnachName
        Assert-Na2ActualizeTest `
            -Condition (
                [IO.File]::ReadAllText($cheatPath) -ceq
                [IO.File]::ReadAllText($cheatTemplate)
            ) `
            -Message "Cheat symlink does not track its template: $($role.PnachName)"
    }

    Remove-Item -LiteralPath $candidateIso -Force

    $second = & $actualizer `
        -ProjectPaths $projectPaths `
        -IdentityResolver $identityResolver
    Assert-Na2ActualizeTest `
        -Condition ($second.Roles.Count -eq 2) `
        -Message 'Second run retained a missing Candidate image.'
    Assert-Na2ActualizeTest `
        -Condition (-not (Test-Path -LiteralPath (
            Join-Path $gameSettings 'SLPS-22228_33333333.ini'
        ))) `
        -Message 'Obsolete managed Candidate GameSettings was not removed.'
    Assert-Na2ActualizeTest `
        -Condition (-not (Test-Path -LiteralPath (
            Join-Path $cheats 'SLPS-22228_33333333.pnach'
        ))) `
        -Message 'Obsolete managed Candidate cheat symlink was not removed.'
    foreach ($memoryCardInput in $memoryCardInputs) {
        Assert-Na2ActualizeTest `
            -Condition (
                [Convert]::ToHexString(
                    [IO.File]::ReadAllBytes($memoryCardInput.Path)
                ) -ceq [Convert]::ToHexString($memoryCardInput.Bytes)
            ) `
            -Message "Configured memory card was modified: $($memoryCardInput.Path)"
    }

    [IO.File]::WriteAllBytes($cheatTemplate, [byte[]]@())
    $currentPnach = Join-Path $cheats $first.Roles[0].PnachName
    Remove-Item -LiteralPath $currentPnach -Force
    $staleText = (
        "// Stale managed runtime PNACH`n" +
        "patch=1,EE,208F0000,extended,00000000`n"
    )
    [IO.File]::WriteAllText(
        $currentPnach,
        $staleText,
        [Text.UTF8Encoding]::new($false)
    )
    $staleRegularPnach = Join-Path $cheats 'SLOP-NA228_AAAAAAAA.pnach'
    [IO.File]::WriteAllText(
        $staleRegularPnach,
        $staleText,
        [Text.UTF8Encoding]::new($false)
    )
    $null = & $actualizer `
        -ProjectPaths $projectPaths `
        -IdentityResolver $identityResolver
    $remainingPnach = @(
        Get-ChildItem -LiteralPath $cheats -Filter '*.pnach' -File -Force
    )
    Assert-Na2ActualizeTest `
        -Condition (
            $remainingPnach.Count -eq 1 -and
            [IO.Path]::Equals(
                $remainingPnach[0].FullName,
                $cheatTemplate
            ) -and
            $remainingPnach[0].Length -eq 0
        ) `
        -Message 'Empty cheat template did not remove every managed alias.'

    Write-Host 'NA2 actualization tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
