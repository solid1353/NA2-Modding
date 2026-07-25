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

function Get-Na2ActualizeTestLinkTarget {
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
) ('na2-actualize-test-{0}' -f [guid]::NewGuid().ToString('N'))

try {
    $pcsx2 = Join-Path $testRoot 'pcsx2'
    $cheats = Join-Path $pcsx2 'cheats'
    $gameSettings = Join-Path $pcsx2 'gamesettings'
    $memcards = Join-Path $pcsx2 'memcards'
    $canonical = Join-Path $testRoot 'pcsx2_files'
    $build = Join-Path $testRoot 'build'
    foreach ($directory in $cheats, $gameSettings, $memcards, $canonical, $build) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    $canonicalCheats = Join-Path $canonical 'cheats.pnach'
    $canonicalSettings = Join-Path $canonical 'gamesettings.ini'
    $baseCard = Join-Path $memcards 'Mcd001_NA228.ps2'
    [IO.File]::WriteAllText(
        $canonicalCheats,
        "// [Test]`npatch=1,EE,00100000,word,00000000`n"
    )
    [IO.File]::WriteAllText(
        $canonicalSettings,
        "[EmuCore]`nInputProfileName = Comparison`n`n[MemoryCards]`nSlot1_Filename = Mcd001_NA228.ps2`n"
    )
    [IO.File]::WriteAllBytes($baseCard, [byte[]](1, 2, 3, 4))

    $currentIso = Join-Path $build 'Current.iso'
    $previousIso = Join-Path $build 'Previous.iso'
    $candidateIso = Join-Path $build 'Candidate.iso'
    foreach ($iso in $currentIso, $previousIso, $candidateIso) {
        [IO.File]::WriteAllBytes($iso, [byte[]](0))
    }

    $managedSettings = Join-Path $gameSettings '.na2'
    $paths = [pscustomobject]@{
        pcsx2_user = $pcsx2
        pcsx2_files = $canonical
        pcsx2_user_gamesettings = $gameSettings
        files = [pscustomobject]@{
            canonical_cheats = $canonicalCheats
            canonical_gamesettings = $canonicalSettings
            current_gamesettings = Join-Path $managedSettings 'Current.ini'
            previous_gamesettings = Join-Path $managedSettings 'Previous.ini'
            candidate_gamesettings = Join-Path $managedSettings 'Candidate.ini'
            na228_base_memcard = $baseCard
            na228_current_memcard = Join-Path $memcards 'Mcd001_NA228_Current.ps2'
            na228_previous_memcard = Join-Path $memcards 'Mcd001_NA228_Previous.ps2'
            na228_candidate_memcard = Join-Path $memcards 'Mcd001_NA228_Candidate.ps2'
            current_iso = $currentIso
            previous_iso = $previousIso
            candidate_iso = $candidateIso
        }
    }
    $identityResolver = {
        param([string]$Path)
        if ([IO.Path]::GetFileName($Path) -ceq 'Candidate.iso') {
            return [pscustomobject]@{ Serial = 'SLOP-NA228'; CRC = 'BBBBBBBB' }
        }
        return [pscustomobject]@{ Serial = 'SLOP-NA228'; CRC = 'AAAAAAAA' }
    }

    $legacyPnach = Join-Path $canonical 'SLPS-25837_C0659AD1.pnach'
    New-Item `
        -ItemType SymbolicLink `
        -Path (Join-Path $cheats 'SLPS-22228_11111111.pnach') `
        -Target ([IO.Path]::GetRelativePath($cheats, $legacyPnach)) |
        Out-Null
    New-Item `
        -ItemType SymbolicLink `
        -Path (Join-Path $gameSettings 'SLPS-22228_11111111.ini') `
        -Target ([IO.Path]::GetRelativePath($gameSettings, $canonicalSettings)) |
        Out-Null

    $first = & (Join-Path $PSScriptRoot 'actualize.ps1') `
        -ActiveRole Current `
        -ProjectPaths $paths `
        -IdentityResolver $identityResolver
    Assert-Na2ActualizeTest `
        ($first.CreatedMemoryCards.Count -eq 3) `
        'First actualization did not create all three role cards.'
    foreach ($card in @(
        $paths.files.na228_current_memcard
        $paths.files.na228_previous_memcard
        $paths.files.na228_candidate_memcard
    )) {
        Assert-Na2ActualizeTest `
            ([Convert]::ToHexString([IO.File]::ReadAllBytes($card)) -ceq '01020304') `
            "New role card does not match the base: $card"
    }
    Assert-Na2ActualizeTest `
        (-not (Test-Path -LiteralPath (Join-Path $cheats 'SLPS-22228_11111111.pnach'))) `
        'Stale PNACH alias was not deleted.'
    Assert-Na2ActualizeTest `
        (-not (Test-Path -LiteralPath (Join-Path $gameSettings 'SLPS-22228_11111111.ini'))) `
        'Stale GameSettings alias was not deleted.'

    $sharedSettingsAlias = Join-Path $gameSettings 'SLOP-NA228_AAAAAAAA.ini'
    Assert-Na2ActualizeTest `
        ([IO.Path]::Equals(
            (Get-Na2ActualizeTestLinkTarget $sharedSettingsAlias),
            $paths.files.current_gamesettings
        )) `
        'Current did not win the shared identity alias.'
    Assert-Na2ActualizeTest `
        ([IO.File]::ReadAllText($paths.files.current_gamesettings) -match
            'Slot1_Filename = Mcd001_NA228_Current\.ps2') `
        'Current generated settings use the wrong card.'

    [IO.File]::WriteAllBytes(
        $paths.files.na228_current_memcard,
        [byte[]](9, 8, 7, 6)
    )
    $second = & (Join-Path $PSScriptRoot 'actualize.ps1') `
        -ActiveRole Previous `
        -ProjectPaths $paths `
        -IdentityResolver $identityResolver
    Assert-Na2ActualizeTest `
        ($second.CreatedMemoryCards.Count -eq 0) `
        'Existing role cards were recreated.'
    Assert-Na2ActualizeTest `
        ([Convert]::ToHexString(
            [IO.File]::ReadAllBytes($paths.files.na228_current_memcard)
        ) -ceq '09080706') `
        'Existing Current card progress was overwritten.'
    Assert-Na2ActualizeTest `
        ([IO.Path]::Equals(
            (Get-Na2ActualizeTestLinkTarget $sharedSettingsAlias),
            $paths.files.previous_gamesettings
        )) `
        'Previous did not take over the shared identity alias when active.'

    [IO.File]::WriteAllBytes($canonicalCheats, [byte[]]::new(0))
    $null = & (Join-Path $PSScriptRoot 'actualize.ps1') `
        -ActiveRole Candidate `
        -ProjectPaths $paths `
        -IdentityResolver $identityResolver
    Assert-Na2ActualizeTest `
        (@(Get-ChildItem -LiteralPath $cheats -Filter '*.pnach').Count -eq 0) `
        'Empty canonical PNACH did not remove managed aliases.'

    Write-Host 'PCSX2 actualization tests passed.'
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
