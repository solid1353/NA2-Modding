[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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

    $canonicalCheats = Join-Path $cheats 'NA228.pnach'
    $canonicalGameSettings = Join-Path $gameSettings 'NA228.ini'
    [IO.File]::WriteAllText(
        $canonicalCheats,
        "// [Intro skips]`npatch=1,EE,00100000,word,00000000`n",
        [Text.UTF8Encoding]::new($false)
    )
    [IO.File]::WriteAllText(
        $canonicalGameSettings,
        (
            "[EmuCore]`nInputProfileName = Comparison`n`n" +
            "[MemoryCards]`nSlot1_Filename = Base.ps2`n"
        ),
        [Text.UTF8Encoding]::new($false)
    )
    [IO.File]::WriteAllBytes(
        (Join-Path $memoryCards 'Base.ps2'),
        [byte[]](1, 2, 3, 4)
    )

    $currentIso = Join-Path $build 'Current.iso'
    $previousIso = Join-Path $build 'Previous.iso'
    $candidateIso = Join-Path $build 'Candidate.iso'
    $labStatePath = Join-Path $repository 'injection_lab\build\test-install.json'
    [IO.File]::WriteAllText($currentIso, 'current')
    [IO.File]::WriteAllText($previousIso, 'previous')
    [IO.File]::WriteAllText($candidateIso, 'candidate')

    $projectPaths = [pscustomobject]@{
        pcsx2_files = $pcsx2Files
        pcsx2_cheats = $cheats
        pcsx2_game_settings = $gameSettings
        pcsx2_memory_cards = $memoryCards
        files = [pscustomobject]@{
            canonical_cheats = $canonicalCheats
            canonical_gamesettings = $canonicalGameSettings
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
        -IdentityResolver $identityResolver `
        -InjectionLabStatePath $labStatePath

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
        $shouldKeepMemoryCard = $role.GameSettingsName -ceq $currentSettingsName
        Assert-Na2ActualizeTest `
            -Condition (
                ($settingsText -match '(?m)^\[MemoryCards\]$') -eq
                $shouldKeepMemoryCard
            ) `
            -Message "GameSettings memory-card block is wrong: $($role.Role)"
        Assert-Na2ActualizeTest `
            -Condition (Test-Path -LiteralPath $cheatPath -PathType Leaf) `
            -Message "Cheat symlink is broken: $($role.PnachName)"
        Assert-Na2ActualizeTest `
            -Condition (
                [IO.File]::ReadAllText($cheatPath) -ceq
                [IO.File]::ReadAllText($canonicalCheats)
            ) `
            -Message "Cheat symlink target is wrong: $($role.PnachName)"
    }

    Assert-Na2ActualizeTest `
        -Condition (-not (Test-Path -LiteralPath (
            Join-Path $memoryCards 'Base - Current.ps2'
        ))) `
        -Message 'Current role memory card was unexpectedly created.'
    Assert-Na2ActualizeTest `
        -Condition (-not (Test-Path -LiteralPath (
            Join-Path $memoryCards 'Base - Previous.ps2'
        ))) `
        -Message 'Previous role memory card was unexpectedly created.'
    Assert-Na2ActualizeTest `
        -Condition (-not (Test-Path -LiteralPath (
            Join-Path $memoryCards 'Base - Candidate.ps2'
        ))) `
        -Message 'Candidate role memory card was unexpectedly created.'

    [IO.File]::AppendAllText(
        $canonicalCheats,
        "// link identity probe`n",
        [Text.UTF8Encoding]::new($false)
    )
    foreach ($role in $first.Roles) {
        $cheatPath = Join-Path $cheats $role.PnachName
        Assert-Na2ActualizeTest `
            -Condition (
                [IO.File]::ReadAllText($cheatPath) -ceq
                [IO.File]::ReadAllText($canonicalCheats)
            ) `
            -Message "Cheat symlink does not track its canonical PNACH: $($role.PnachName)"
    }

    $currentRole = $first.Roles |
        Where-Object Role -CEQ 'Current' |
        Select-Object -First 1
    $labTarget = Join-Path $cheats $currentRole.PnachName
    Remove-Item -LiteralPath $labTarget -Force
    $labText = (
        "// Auto-generated injection lab PNACH`n" +
        "patch=1,EE,208F0000,extended,00000000`n"
    )
    [IO.File]::WriteAllText(
        $labTarget,
        $labText,
        [Text.UTF8Encoding]::new($false)
    )
    $labStateDirectory = [IO.Path]::GetDirectoryName($labStatePath)
    New-Item -ItemType Directory -Path $labStateDirectory -Force | Out-Null
    $labHash = (Get-FileHash -LiteralPath $labTarget -Algorithm SHA256).Hash
    [pscustomobject]@{
        target = $labTarget
        previous_kind = 'symbolic_link'
        previous_target = ''
        installed_sha256 = $labHash
        current_crc = $currentRole.CRC
        build_id = '0x12345678'
    } | ConvertTo-Json | Set-Content `
        -LiteralPath $labStatePath `
        -Encoding UTF8

    $withLab = & $actualizer `
        -ProjectPaths $projectPaths `
        -IdentityResolver $identityResolver `
        -InjectionLabStatePath $labStatePath
    Assert-Na2ActualizeTest `
        -Condition (
            [string]::IsNullOrWhiteSpace(
                [string](Get-Item -LiteralPath $labTarget -Force).LinkType
            )
        ) `
        -Message 'Actualization replaced the active injection-lab regular PNACH.'
    Assert-Na2ActualizeTest `
        -Condition ([IO.File]::ReadAllText($labTarget) -ceq $labText) `
        -Message 'Actualization changed the active injection-lab PNACH.'
    Assert-Na2ActualizeTest `
        -Condition (@($withLab.PreservedInjectionLabPnach).Count -eq 1) `
        -Message 'Actualization did not report the preserved injection-lab PNACH.'

    [IO.File]::AppendAllText($labTarget, "// external change`n")
    $withChangedLab = & $actualizer `
        -ProjectPaths $projectPaths `
        -IdentityResolver $identityResolver `
        -InjectionLabStatePath $labStatePath
    Assert-Na2ActualizeTest `
        -Condition (
            [IO.File]::ReadAllText($labTarget) -match 'external change'
        ) `
        -Message 'Actualization replaced an installed lab PNACH after a rewrite.'
    Assert-Na2ActualizeTest `
        -Condition (@($withChangedLab.PreservedInjectionLabPnach).Count -eq 1) `
        -Message 'Actualization did not preserve a rewritten lab PNACH.'

    Remove-Item -LiteralPath $labStatePath -Force
    $withoutLabState = & $actualizer `
        -ProjectPaths $projectPaths `
        -IdentityResolver $identityResolver `
        -InjectionLabStatePath $labStatePath
    $repairedLabTarget = Get-Item -LiteralPath $labTarget -Force
    Assert-Na2ActualizeTest `
        -Condition ($repairedLabTarget.LinkType -ceq 'SymbolicLink') `
        -Message 'Actualization did not repair an orphaned regular PNACH.'
    foreach ($invalidLabState in '{ invalid json', 'null', '{}') {
        [IO.File]::WriteAllText(
            $labStatePath,
            $invalidLabState,
            [Text.UTF8Encoding]::new($false)
        )
        $withInvalidLabState = & $actualizer `
            -ProjectPaths $projectPaths `
            -IdentityResolver $identityResolver `
            -InjectionLabStatePath $labStatePath
        Assert-Na2ActualizeTest `
            -Condition (
                @($withInvalidLabState.PreservedInjectionLabPnach).Count -eq 0
            ) `
            -Message 'Invalid lab state was incorrectly treated as an installation.'
        Assert-Na2ActualizeTest `
            -Condition (
                (Get-Item -LiteralPath $labTarget -Force).LinkType -ceq
                    'SymbolicLink'
            ) `
            -Message 'Invalid lab state blocked canonical PNACH actualization.'
    }
    Remove-Item -LiteralPath $labStatePath -Force

    Remove-Item -LiteralPath $candidateIso -Force

    $second = & $actualizer `
        -ProjectPaths $projectPaths `
        -IdentityResolver $identityResolver `
        -InjectionLabStatePath $labStatePath
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
    Assert-Na2ActualizeTest `
        -Condition (
            [IO.File]::ReadAllBytes(
                (Join-Path $memoryCards 'Base.ps2')
            )[0] -eq 1
        ) `
        -Message 'Configured base memory card was modified.'

    [IO.File]::WriteAllBytes($canonicalCheats, [byte[]]@())
    Remove-Item -LiteralPath $labTarget -Force
    [IO.File]::WriteAllText(
        $labTarget,
        $labText,
        [Text.UTF8Encoding]::new($false)
    )
    $staleRegularPnach = Join-Path $cheats 'SLOP-NA228_AAAAAAAA.pnach'
    [IO.File]::WriteAllText(
        $staleRegularPnach,
        $labText,
        [Text.UTF8Encoding]::new($false)
    )
    $null = & $actualizer `
        -ProjectPaths $projectPaths `
        -IdentityResolver $identityResolver `
        -InjectionLabStatePath $labStatePath
    $remainingPnach = @(
        Get-ChildItem -LiteralPath $cheats -Filter '*.pnach' -File -Force
    )
    Assert-Na2ActualizeTest `
        -Condition (
            $remainingPnach.Count -eq 1 -and
            [IO.Path]::Equals(
                $remainingPnach[0].FullName,
                $canonicalCheats
            ) -and
            $remainingPnach[0].Length -eq 0
        ) `
        -Message 'Empty canonical PNACH did not remove every managed alias.'

    Write-Host 'NA2 actualization tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
