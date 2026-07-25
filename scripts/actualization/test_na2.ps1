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

function Get-Na2TestLinkTarget {
    param([Parameter(Mandatory)][string]$Path)

    $item = Get-Item -LiteralPath $Path -Force
    $target = [string]$item.LinkTarget
    if (-not [IO.Path]::IsPathRooted($target)) {
        $target = Join-Path $item.DirectoryName $target
    }
    return [IO.Path]::GetFullPath($target)
}

$testRoot = Join-Path (
    [IO.Path]::GetTempPath()
) ('na2-actualization-test-{0}' -f [guid]::NewGuid().ToString('N'))

try {
    $build = Join-Path $testRoot 'build'
    $pcsx2Files = Join-Path $testRoot 'pcsx2_files'
    $pcsx2 = Join-Path $testRoot 'pcsx2'
    $cheats = Join-Path $pcsx2 'cheats'
    $gameSettings = Join-Path $pcsx2 'gamesettings'
    $memoryCards = Join-Path $pcsx2 'memcards'
    New-Item -ItemType Directory -Force `
        -Path $build, $pcsx2Files, $cheats, $gameSettings, $memoryCards |
        Out-Null

    $canonicalCheats = Join-Path $pcsx2Files 'cheats.pnach'
    $canonicalGameSettings = Join-Path $pcsx2Files 'gamesettings.ini'
    [IO.File]::WriteAllText(
        $canonicalCheats,
        "// [Intro skips]`npatch=1,EE,00100000,word,00000000`n",
        [Text.UTF8Encoding]::new($false)
    )
    [IO.File]::WriteAllText(
        $canonicalGameSettings,
        "[MemoryCards]`nSlot1_Filename = Base.ps2`n",
        [Text.UTF8Encoding]::new($false)
    )
    [IO.File]::WriteAllBytes(
        (Join-Path $memoryCards 'Base.ps2'),
        [byte[]](1, 2, 3, 4)
    )

    $currentIso = Join-Path $build 'Current.iso'
    $previousIso = Join-Path $build 'Previous.iso'
    $candidateIso = Join-Path $build 'Candidate.iso'
    [IO.File]::WriteAllText($currentIso, 'current')
    [IO.File]::WriteAllText($previousIso, 'previous')
    [IO.File]::WriteAllText($candidateIso, 'candidate')

    $projectPaths = [pscustomobject]@{
        pcsx2_user = $pcsx2
        pcsx2_files = $pcsx2Files
        pcsx2_user_gamesettings = $gameSettings
        pcsx2_user_memcards = $memoryCards
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
                [pscustomobject]@{ Serial = 'SLUS-NA228'; CRC = '22222222' }
            }
            'Candidate' {
                [pscustomobject]@{ Serial = 'SLPS-22228'; CRC = '33333333' }
            }
            default {
                throw "Unexpected ISO: $Path"
            }
        }
    }

    $actualizer = Join-Path $PSScriptRoot 'na2.ps1'
    $first = & $actualizer `
        -ProjectPaths $projectPaths `
        -IdentityResolver $identityResolver

    Assert-Na2ActualizeTest `
        -Condition ($first.Roles.Count -eq 3) `
        -Message 'First run did not actualize all three built images.'
    Assert-Na2ActualizeTest `
        -Condition (@($first.EnabledCheats) -contains 'Intro skips') `
        -Message 'Enabled cheat reporting was lost.'

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
        Assert-Na2ActualizeTest `
            -Condition (
                [IO.File]::ReadAllText($settingsPath) -match
                [regex]::Escape($role.MemoryCardName)
            ) `
            -Message "GameSettings has the wrong memory card: $($role.Role)"
        Assert-Na2ActualizeTest `
            -Condition ([IO.Path]::Equals(
                (Get-Na2TestLinkTarget -Path $cheatPath),
                $canonicalCheats
            )) `
            -Message "Cheat symlink target is wrong: $($role.PnachName)"
        Assert-Na2ActualizeTest `
            -Condition (Test-Path -LiteralPath $role.MemoryCard -PathType Leaf) `
            -Message "Missing role memory card: $($role.MemoryCardName)"
    }

    $currentCard = Join-Path $memoryCards 'Base - Current.ps2'
    [IO.File]::WriteAllBytes($currentCard, [byte[]](9, 9, 9))
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
    Assert-Na2ActualizeTest `
        -Condition (Test-Path -LiteralPath (
            Join-Path $memoryCards 'Base - Candidate.ps2'
        ) -PathType Leaf) `
        -Message 'Candidate memory card was incorrectly deleted.'
    Assert-Na2ActualizeTest `
        -Condition (
            [IO.File]::ReadAllBytes($currentCard)[0] -eq 9
        ) `
        -Message 'Existing Current memory card was overwritten.'

    [IO.File]::WriteAllBytes($canonicalCheats, [byte[]]@())
    $null = & $actualizer `
        -ProjectPaths $projectPaths `
        -IdentityResolver $identityResolver
    Assert-Na2ActualizeTest `
        -Condition (@(
            Get-ChildItem -LiteralPath $cheats -Filter '*.pnach' -Force
        ).Count -eq 0) `
        -Message 'Empty canonical PNACH did not remove managed symlinks.'

    Write-Host 'NA2 actualization tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
