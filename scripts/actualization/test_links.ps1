[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-Na2LinkTest {
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
) ('na2-links-test-{0}' -f [guid]::NewGuid().ToString('N'))

try {
    $project = Join-Path $testRoot 'project'
    $user = Join-Path $testRoot 'user'
    $pairs = @(
        [pscustomobject]@{
            Name = 'game_settings'
            Source = Join-Path $project 'game_settings'
            Destination = Join-Path $user 'gamesettings'
        }
        [pscustomobject]@{
            Name = 'input_profiles'
            Source = Join-Path $project 'input_profiles'
            Destination = Join-Path $user 'inputprofiles'
        }
        [pscustomobject]@{
            Name = 'input_recordings'
            Source = Join-Path $project 'input_recordings'
            Destination = Join-Path $user 'inputrecordings'
        }
    )
    foreach ($pair in $pairs) {
        New-Item -ItemType Directory -Force `
            -Path $pair.Source, $pair.Destination |
            Out-Null
        [IO.File]::WriteAllText(
            (Join-Path $pair.Source "$($pair.Name).dat"),
            $pair.Name,
            [Text.UTF8Encoding]::new($false)
        )
    }

    $projectPaths = [pscustomobject]@{
        pcsx2_game_settings = $pairs[0].Source
        pcsx2_user_gamesettings = $pairs[0].Destination
        pcsx2_input_profiles = $pairs[1].Source
        pcsx2_user_inputprofiles = $pairs[1].Destination
        pcsx2_input_recordings = $pairs[2].Source
        pcsx2_user_inputrecordings = $pairs[2].Destination
    }
    $actualizer = Join-Path $PSScriptRoot 'links.ps1'
    $first = & $actualizer -ProjectPaths $projectPaths -PassThru
    Assert-Na2LinkTest `
        -Condition ($first.Created.Count -eq 3) `
        -Message 'First run did not create all three configured hardlinks.'

    $second = & $actualizer -ProjectPaths $projectPaths -PassThru
    Assert-Na2LinkTest `
        -Condition (
            $second.Created.Count -eq 0 -and
            $second.Verified.Count -eq 3
        ) `
        -Message 'Second run did not verify the existing hardlinks.'

    $extra = Join-Path $pairs[1].Destination 'user-only.ini'
    [IO.File]::WriteAllText($extra, 'preserve')
    $null = & $actualizer -ProjectPaths $projectPaths -PassThru
    Assert-Na2LinkTest `
        -Condition (Test-Path -LiteralPath $extra -PathType Leaf) `
        -Message 'An unrelated user-only file was removed.'

    $occupiedSource = Join-Path $pairs[0].Source 'occupied.ini'
    $occupiedDestination = Join-Path $pairs[0].Destination 'occupied.ini'
    [IO.File]::WriteAllText($occupiedSource, 'project')
    [IO.File]::WriteAllText($occupiedDestination, 'user')
    $refused = $false
    try {
        $null = & $actualizer -ProjectPaths $projectPaths -PassThru
    }
    catch {
        $refused = $_.Exception.Message -match (
            'Refusing differing occupied PCSX2 counterpart'
        )
    }
    Assert-Na2LinkTest `
        -Condition $refused `
        -Message 'A differing occupied counterpart was not refused.'

    Write-Host 'PCSX2 hardlink actualization tests passed.' `
        -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
