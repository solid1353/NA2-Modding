[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$sourceRepository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
. (Join-Path $sourceRepository 'scripts\lib\build_log.ps1')

function Assert-Na2Test {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

$testRoot = Join-Path (
    [IO.Path]::GetTempPath()
) "na2-run-log-tests-$PID-$([guid]::NewGuid().ToString('N'))"

try {
    $repository = Join-Path $testRoot 'repo'
    $logs = Join-Path $repository 'logs'
    $build = Join-Path $repository 'build'
    $paths = [pscustomobject]@{
        repository = $repository
        source = Join-Path $testRoot 'source'
        build = $build
        logs = $logs
        builder = Join-Path $repository 'na228_builder'
        pcsx2_stable = Join-Path $testRoot 'pcsx2_stable'
        scripts = Join-Path $repository 'scripts'
        files = [pscustomobject]@{
            latest_iso = Join-Path $build 'NA2.28 - Latest.iso'
            previous_iso = Join-Path $build 'NA2.28 - Previous.iso'
            e2e_test_iso = Join-Path $build 'NA2.28 - E2E Test.iso'
            e2e_test_padded_iso = Join-Path $build 'NA2.28 - E2E Test Padded.iso'
        }
    }
    New-Item -ItemType Directory -Force -Path $logs, $build | Out-Null
    $externalPath = 'C{0}{1}Private{1}outside.txt' -f `
        [IO.Path]::VolumeSeparatorChar, [IO.Path]::DirectorySeparatorChar

    $portable = ConvertTo-Na2PortableText `
        -Text "ISO: $build\NA2.28 - Latest.iso`nExternal: $externalPath" `
        -Paths $paths
    Assert-Na2Test `
        -Condition ($portable -match 'ISO: @build/NA2\.28 - Latest\.iso') `
        -Message 'Configured build path was not converted to @build.'
    Assert-Na2Test `
        -Condition ($portable -match 'Redacted output containing an external absolute path') `
        -Message 'External absolute path was not redacted.'
    Assert-Na2Test `
        -Condition (-not (Test-Na2WindowsAbsolutePath -Text $portable)) `
        -Message 'Portable text retained a Windows absolute path.'

    foreach ($index in 1..22) {
        $context = Start-Na2RunLog `
            -Mode "test-$index" `
            -Paths $paths `
            -MaxRollingSections 20
        Write-Host "run-marker-$index $build\NA2.28 - Latest.iso"
        Complete-Na2RunLog -Context $context -Outcome succeeded
    }

    $latest = [IO.File]::ReadAllText((Join-Path $logs 'na228\latest.log'))
    $rolling = [IO.File]::ReadAllText((Join-Path $logs 'na228\rolling.log'))
    $sections = [regex]::Matches(
        $rolling,
        '(?ms)^--- NA2 RUN BEGIN ---\n.*?^--- NA2 RUN END ---\n?'
    )
    Assert-Na2Test -Condition ($sections.Count -eq 20) -Message 'rolling.log was not capped at 20 runs.'
    Assert-Na2Test -Condition ($latest -match '(?m)^mode: test-22$') -Message 'latest.log is not the newest run.'
    Assert-Na2Test -Condition ($rolling -notmatch '(?m)^run-marker-1 ') -Message 'rolling.log retained an expired run.'
    Assert-Na2Test -Condition ($rolling -match '(?m)^run-marker-3 ') -Message 'rolling.log lost the oldest retained run.'
    Assert-Na2Test -Condition ($rolling -match '(?m)^run-marker-22 ') -Message 'rolling.log lost the newest run.'
    Assert-Na2Test -Condition ($rolling -notmatch 'PowerShell transcript') -Message 'Transcript boilerplate was retained.'
    Assert-Na2Test -Condition (-not (Test-Na2WindowsAbsolutePath -Text $rolling)) -Message 'rolling.log contains an absolute path.'
    foreach ($field in 'mode:', 'start:', 'end:', 'outcome:', 'duration_ms:') {
        Assert-Na2Test -Condition ($latest.Contains($field)) -Message "latest.log is missing $field"
    }

    $failurePaths = $paths.PSObject.Copy()
    $failurePaths.logs = Join-Path $repository 'failure-logs'
    $failureContext = Start-Na2RunLog -Mode failure-test -Paths $failurePaths
    Write-Host "failure marker $build\NA2.28 - Latest.iso"
    $failureExternalPath = 'C{0}{1}Private{1}failure.txt' -f `
        [IO.Path]::VolumeSeparatorChar, [IO.Path]::DirectorySeparatorChar
    Complete-Na2RunLog `
        -Context $failureContext `
        -Outcome failed `
        -FailureMessage "Configured: $build\NA2.28 - Latest.iso`nExternal: $failureExternalPath"
    $failureLog = [IO.File]::ReadAllText((Join-Path $failurePaths.logs 'na228\latest.log'))
    Assert-Na2Test -Condition ($failureLog -match '(?m)^outcome: failed$') -Message 'Failed outcome was not recorded.'
    Assert-Na2Test -Condition ($failureLog -match '@build/NA2\.28 - Latest\.iso') -Message 'Failure path was not made portable.'
    Assert-Na2Test -Condition (-not (Test-Na2WindowsAbsolutePath -Text $failureLog)) -Message 'Failure log contains an absolute path.'

    $fakeRepository = Join-Path $testRoot 'help-project'
    New-Item -ItemType Directory -Force -Path (Join-Path $fakeRepository 'scripts\lib') | Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'na228.ps1') -Destination $fakeRepository
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'scripts\lib\paths.ps1') `
        -Destination (Join-Path $fakeRepository 'scripts\lib')
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'scripts\lib\run_log.ps1') `
        -Destination (Join-Path $fakeRepository 'scripts\lib')
    $fakeNa2Scripts = Join-Path $fakeRepository 'scripts\na228'
    New-Item -ItemType Directory -Force -Path $fakeNa2Scripts | Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'scripts\na228\run.ps1') `
        -Destination $fakeNa2Scripts
    $fakePcsx2Scripts = Join-Path $fakeRepository 'scripts\pcsx2'
    New-Item -ItemType Directory -Force -Path $fakePcsx2Scripts | Out-Null
    $fakeReleaseScripts = Join-Path $fakeRepository 'scripts\release'
    New-Item -ItemType Directory -Force -Path $fakeReleaseScripts | Out-Null
    $fakeInjectionScripts = Join-Path $fakeRepository 'scripts\injection'
    New-Item -ItemType Directory -Force -Path $fakeInjectionScripts | Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'scripts\na228\worker_paths.ps1') `
        -Destination $fakeNa2Scripts
    $manifest = @'
{
  "schema_version": 1,
  "roots": {
    "repository": ".",
    "source": "source",
    "utils": "utils",
    "build": "build",
    "logs": "logs",
    "builder": "na228_builder",
    "pcsx2_stable": "pcsx2_stable",
    "pcsx2_files": "pcsx2_files",
    "pcsx2_cheats": "@pcsx2_files/cheats",
    "pcsx2_game_settings": "@pcsx2_files/game_settings",
    "pcsx2_input_profiles": "@pcsx2_files/input_profiles",
    "pcsx2_memory_cards": "@pcsx2_files/memory_cards",
    "scripts": "scripts",
    "pcsx2_scripts": "@scripts/pcsx2",
    "work": "work"
  },
  "files": {
    "game_catalog": "@repository/games.json",
    "product_config": "@repository/product.json",
    "game_resolver": "@scripts/lib/resolve_game.py",
    "pcsx2_launch_command": "@scripts/pcsx2/launch.ps1",
    "pcsx2_game_launch_command": "@scripts/pcsx2/launch_games.ps1",
    "workshop_command": "@repository/workshop.ps1",
    "release_publish_command": "@scripts/release/publish_release.ps1"
  }
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeRepository 'paths.json') -Content $manifest
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeRepository 'games.json') -Content @'
{
  "schema_version": 1,
  "sources": {
    "NA2": {
      "serial": "SLPS-25837",
      "crc": "C0659AD1"
    },
    "NUN5": {
      "serial": "SLES-55605",
      "crc": "C071D4C1"
    }
  }
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeRepository 'product.json') -Content @'
{
  "schema_version": 1,
  "title": "NA v2.28",
  "serial": "SLOP-NA228",
  "builds": {
    "latest": { "aliases": ["l"], "postfix": "Latest" },
    "previous": { "aliases": ["p"], "postfix": "Previous" },
    "manual_test": { "aliases": ["mt"], "postfix": "Manual Test" },
    "e2e_test": { "postfix": "E2E Test" },
    "e2e_test_padded": { "postfix": "E2E Test Padded" }
  }
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeRepository 'scripts\lib\resolve_game.py') -Content @'
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("selector")
parser.add_argument("--project-root", type=Path, required=True)
args = parser.parse_args()
root = args.project_root.resolve()
name = args.selector
builds = {
    "latest": "Latest",
    "previous": "Previous",
    "manual_test": "Manual Test",
}
aliases = {"l": "latest", "p": "previous", "mt": "manual_test"}
name = aliases.get(name.casefold(), name)
if name in builds:
    title = "NA v2.28"
    result = {
        "iso": str(root / "build" / f"{title} - {builds[name]}.iso"),
        "cheats": str(root / "pcsx2_files" / "cheats" / "SLOP-NA228.pnach"),
        "game_settings": str(root / "pcsx2_files" / "game_settings" / "SLOP-NA228.ini"),
        "memory_card": str(root / "pcsx2_files" / "memory_cards" / f"{title} - {builds[name]}.ps2"),
        "input_profile": str(root / "pcsx2_files" / "input_profiles" / "Default_Base.ini"),
    }
else:
    canonical = name.upper()
    result = {
        "iso": str(root / "source" / f"{canonical}.iso"),
        "extracted": str(root / "source" / f"{canonical}.iso.files"),
        "cheats": str(root / "pcsx2_files" / "cheats" / "source" / f"{canonical}.pnach"),
        "game_settings": str(root / "pcsx2_files" / "game_settings" / "source" / f"{canonical}.ini"),
        "memory_card": str(root / "pcsx2_files" / "memory_cards" / f"{canonical}.ps2"),
        "input_profile": str(root / "pcsx2_files" / "input_profiles" / "Default_Base.ini"),
    }
print(json.dumps(result))
'@
    foreach ($directory in @(
        'source', 'utils', 'build', 'logs', 'na228_builder', 'pcsx2_stable',
        'pcsx2_files\cheats', 'pcsx2_files\game_settings',
        'pcsx2_files\input_profiles', 'pcsx2_files\memory_cards', 'scripts', 'source\NA2.iso.files',
        'source\NUN5.iso.files', 'work'
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $fakeRepository $directory) | Out-Null
    }
    $helpText = (& (Join-Path $fakeRepository 'na228.ps1') help) -join "`n"
    Assert-Na2Test `
        -Condition (-not (Test-Path -LiteralPath (Join-Path $fakeRepository 'logs\na228'))) `
        -Message 'Help invocation created run logs.'
    Assert-Na2Test `
        -Condition ($helpText -notmatch '(?m)^\s*na228 act\b') `
        -Message 'Root help still exposes the retired na228 act command.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 <token> \[token\]') `
        -Message 'Root help omitted the ordered token grammar.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 worker work/') `
        -Message 'Root help omitted the explicit worker-build command.'
    Assert-Na2Test `
        -Condition ($helpText -notmatch '(?m)^\s*na228 validate\s') `
        -Message 'Root help still exposes the retired separate validation command.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 build l\|mt\s') `
        -Message 'Root help omitted the explicit build-only command.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 test \[suite\]\s+Run unit tests; prepare and validate normal/padded E2E Test ISOs; replay and compare all or one E2E suite and update captures$') `
        -Message 'Root help omitted the complete one-command E2E pipeline.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 test create <suite> <recording> \[game\]\s+Create or replace a suite, optionally capture its reference, then run it$') `
        -Message 'Root help omitted suite replacement with an optional reference game.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 test rename <suite> <new-suite>\s+Rename a suite and its capture history$') `
        -Message 'Root help omitted suite rename.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 test delete <suite>\s+Delete a suite and its capture history$') `
        -Message 'Root help omitted suite deletion.'
    Assert-Na2Test `
        -Condition ($helpText -notmatch '(?m)^\s*na228 test new\b') `
        -Message 'Root help still exposes the retired test new command.'
    Assert-Na2Test `
        -Condition ($helpText -notmatch '(?m)^\s*na228 test reference\b') `
        -Message 'Root help still exposes the retired reference command.'
    Assert-Na2Test `
        -Condition ($helpText -notmatch '(?m)^\s*na228 -[btcpwh]\b') `
        -Message 'Root help still exposes a retired dashed mode.'
    Assert-Na2Test `
        -Condition ($helpText -notmatch '(?m)^\s*na228 launch\b') `
        -Message 'Root help still exposes the retired launch subcommand.'
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakePcsx2Scripts 'launch.ps1') -Content @'
param([string]$Target = 'dev', [string]$IsoPath)
Write-Host "[fake] launch $Target $IsoPath"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakePcsx2Scripts 'launch_games.ps1') -Content @'
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Games,
    [string]$Play,
    [string]$Record,
    [switch]$Test,
    [string]$ProjectRoot
)
$aliases = @{
    l = 'latest'
    p = 'previous'
    mt = 'manual_test'
}
$canonical = @($Games | ForEach-Object {
    if ($aliases.ContainsKey($_)) { $aliases[$_] } else { $_ }
})
if (@($canonical | Where-Object { $_ -notin @(
    'latest', 'previous', 'manual_test', 'na2', 'nun5'
) }).Count -gt 0) {
    throw "Unknown game name: $($Games -join ',')"
}
Write-Output (
    "[fake] multi-game launch $($canonical -join ',') " +
    "play=$Play record=$Record test=$Test project=$ProjectRoot"
)
$port = 28014
foreach ($game in $canonical) {
    [pscustomobject]@{
        Game = $game
        ProcessId = 1000 + $port
        PinePort = $port
        GridCell = '1,1'
    }
    $port++
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeRepository 'workshop.ps1') -Content @'
$tokens = @($args)
Write-Output "[fake] workshop args=$($tokens -join '|')"
$games = [Collections.Generic.List[string]]::new()
$play = ''
$record = ''
$test = $false
for ($index = 0; $index -lt $tokens.Count; $index++) {
    switch ($tokens[$index]) {
        '-p' { $play = $tokens[++$index] }
        '-r' { $record = $tokens[++$index] }
        '-t' {
            $play = $tokens[++$index]
            $test = $true
        }
        default {
            if (-not $tokens[$index].StartsWith('-')) {
                $games.Add($tokens[$index])
            }
            elseif ($index + 1 -lt $tokens.Count) {
                $index++
            }
        }
    }
}
$aliases = @{ l = 'latest'; p = 'previous'; mt = 'manual_test' }
$canonical = @($games | ForEach-Object {
    if ($aliases.ContainsKey($_)) { $aliases[$_] } else { $_ }
})
if ($canonical.Count -eq 0) {
    throw 'Workshop launch requires at least one game.'
}
if (@($canonical | Where-Object { $_ -notin @(
    'latest', 'previous', 'manual_test', 'na2', 'nun5'
) }).Count -gt 0) {
    throw "Unknown game name: $($games -join ',')"
}
Write-Output (
    "[fake] multi-game launch $($canonical -join ',') " +
    "play=$play record=$record test=$test"
)
$port = 28014
foreach ($game in $canonical) {
    [pscustomobject]@{
        Game = $game
        ProcessId = 1000 + $port
        PinePort = $port
        GridCell = '1,1'
    }
    $port++
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeInjectionScripts 'watch.ps1') -Content @'
param(
    [int]$PinePort,
    [string]$SourceId,
    [string]$Entry,
    [string]$SourcePath,
    [string]$OverlayPlan
)
Write-Output (
    "[fake] watch $PinePort source=$SourceId entry=$Entry " +
    "sourcePath=$SourcePath plan=$OverlayPlan"
)
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeReleaseScripts 'publish_release.ps1') -Content @'
param([string]$Version)
Write-Output "[fake] release $Version"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeNa2Scripts 'build.ps1') -Content @'
param(
    [switch]$ManualTestOnly,
    [string]$WorkerOutputIso
)
if ($WorkerOutputIso) {
    Write-Host '[na228] ISO result: worker; rotation: no; PCSX2 left running.'
    [pscustomobject]@{ Status = 'worker'; ChangedRoles = [string[]]@() }
}
elseif ($ManualTestOnly) {
    Write-Host '[na228] ISO result: manual-test; rotation: no; PCSX2 left running.'
    [pscustomobject]@{ Status = 'manual-test'; ChangedRoles = [string[]]@('manual_test') }
}
else {
    Write-Host '[na228] ISO result: updated; rotation: yes.'
    [pscustomobject]@{
        Status = 'updated'
        ChangedRoles = [string[]]@('latest', 'previous')
    }
}
'@
    $fakeVisualRoot = Join-Path $fakeRepository 'e2e'
    $fakeVisualScripts = Join-Path $fakeVisualRoot 'scripts'
    New-Item -ItemType Directory -Force -Path `
        $fakeVisualScripts, `
        (Join-Path $fakeVisualRoot 'suites\alpha'), `
        (Join-Path $fakeVisualRoot 'suites\beta'), `
        (Join-Path $fakeVisualRoot 'suites\font\load_save') | Out-Null
    foreach ($suiteDefinition in 'alpha', 'beta', 'font\load_save') {
        Set-Na2Utf8FileAtomic `
            -Path (Join-Path $fakeVisualRoot "suites\$suiteDefinition\input.p2m2") `
            -Content 'recording'
    }
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeVisualScripts 'run.ps1') -Content @'
param([string]$Suite)
Add-Content -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') -Value "run suite=$Suite"
[pscustomobject]@{ Status = 'passed' }
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeVisualScripts 'create_suite.ps1') -Content @'
param(
    [Parameter(Mandatory)][string]$Suite,
    [Parameter(Mandatory)][string]$Recording,
    [string]$Game
)
Add-Content `
    -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') `
    -Value "create suite=$Suite recording=$Recording game=$Game"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeVisualScripts 'rename_suite.ps1') -Content @'
param([string]$Suite, [string]$NewSuite)
Add-Content `
    -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') `
    -Value "rename suite=$Suite newSuite=$NewSuite"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeVisualScripts 'delete_suite.ps1') -Content @'
param([string]$Suite)
Add-Content `
    -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') `
    -Value "delete suite=$Suite"
'@
    $visualCalls = Join-Path $fakeVisualScripts 'calls.txt'
    & (Join-Path $fakeRepository 'na228.ps1') test
    $calls = @(Get-Content -LiteralPath $visualCalls)
    Assert-Na2Test -Condition (($calls -join ',') -ceq 'run suite=') `
        -Message 'Bare na228 test did not dispatch the complete E2E pipeline exactly once.'
    Remove-Item -LiteralPath $visualCalls
    & (Join-Path $fakeRepository 'na228.ps1') test alpha
    & (Join-Path $fakeRepository 'na228.ps1') test create font/character_select font_full
    & (Join-Path $fakeRepository 'na228.ps1') test create font/with_reference font_full nun5
    & (Join-Path $fakeRepository 'na228.ps1') test rename font/character_select font/characters
    & (Join-Path $fakeRepository 'na228.ps1') test delete font/characters
    $calls = @(Get-Content -LiteralPath $visualCalls)
    Assert-Na2Test `
        -Condition ($calls.Count -eq 5 -and
            $calls[0] -ceq 'run suite=alpha' -and
            $calls[1] -ceq 'create suite=font/character_select recording=font_full game=' -and
            $calls[2] -ceq 'create suite=font/with_reference recording=font_full game=nun5' -and
            $calls[3] -ceq 'rename suite=font/character_select newSuite=font/characters' -and
            $calls[4] -ceq 'delete suite=font/characters') `
        -Message 'Suite selection or lifecycle-command dispatch was incorrect.'
    $retiredReferenceRejected = $false
    try {
        & (Join-Path $fakeRepository 'na228.ps1') test reference alpha nun5
    }
    catch {
        $retiredReferenceRejected = $_.Exception.Message -match '^Usage: na228 test'
    }
    Assert-Na2Test -Condition $retiredReferenceRejected `
        -Message 'The retired reference command was accepted.'
    $na2ActRejected = $false
    try {
        & (Join-Path $fakeRepository 'na228.ps1') act
    }
    catch {
        $na2ActRejected = $_.Exception.Message -match 'Unknown game name: act'
    }
    Assert-Na2Test `
        -Condition $na2ActRejected `
        -Message 'The retired na228 act route was not rejected.'
    $dashedModeRejected = $false
    try {
        & (Join-Path $fakeRepository 'na228.ps1') -b
    }
    catch {
        $dashedModeRejected = $true
    }
    Assert-Na2Test `
        -Condition $dashedModeRejected `
        -Message 'The retired dashed build mode was not rejected.'
    $launchSubcommandRejected = $false
    try {
        & (Join-Path $fakeRepository 'na228.ps1') launch na2 nun5
    }
    catch {
        $launchSubcommandRejected = $true
    }
    Assert-Na2Test `
        -Condition $launchSubcommandRejected `
        -Message 'The retired launch subcommand was not rejected.'
    $launchLogPath = Join-Path $fakeRepository 'logs\na228\rolling.log'
    $launchLogSectionsBefore = if (Test-Path -LiteralPath $launchLogPath) {
        [regex]::Matches(
            [IO.File]::ReadAllText($launchLogPath),
            '(?m)^--- NA2 RUN BEGIN ---$'
        ).Count
    }
    else {
        0
    }
    $multiGameLaunch = (
        & (Join-Path $fakeRepository 'na228.ps1') na2 nun5
    ) -join "`n"
    Assert-Na2Test `
        -Condition ($multiGameLaunch -match '\[fake\] multi-game launch na2,nun5') `
        -Message 'Unified multi-game launch did not preserve ordered selectors.'
    $pairedPlayback = (
        & (Join-Path $fakeRepository 'na228.ps1') `
            nun5 `
            l `
            -p `
            'practice-menu'
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $pairedPlayback -match (
                'multi-game launch nun5,latest ' +
                'play=practice-menu record='
            )
        ) `
        -Message "Paired playback was not forwarded to the shared launcher: $pairedPlayback"
    $pairedRecording = (
        & (Join-Path $fakeRepository 'na228.ps1') `
            nun5 `
            l `
            -r `
            'practice-menu'
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $pairedRecording -match (
                'multi-game launch nun5,latest ' +
                'play= record=practice-menu'
            )
        ) `
        -Message 'Rightmost recording was not forwarded to the shared launcher.'
    $regressionPlayback = (
        & (Join-Path $fakeRepository 'na228.ps1') `
            nun5 `
            -t `
            'practice-menu'
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $regressionPlayback -match (
                'multi-game launch nun5 ' +
                'play=practice-menu record= test=True'
            )
        ) `
        -Message 'Regression playback was not forwarded to the shared launcher.'
    $futureLaunchArguments = (
        & (Join-Path $fakeRepository 'na228.ps1') `
            nun5 `
            l `
            -future-option `
            'future-value'
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $futureLaunchArguments -match (
                '\[fake\] workshop args=nun5\|latest\|' +
                '-future-option\|future-value'
            )
        ) `
        -Message 'Unknown trailing launch arguments were not forwarded unchanged to Workshop.'
    $launchLogSectionsAfter = if (Test-Path -LiteralPath $launchLogPath) {
        [regex]::Matches(
            [IO.File]::ReadAllText($launchLogPath),
            '(?m)^--- NA2 RUN BEGIN ---$'
        ).Count
    }
    else {
        0
    }
    Assert-Na2Test `
        -Condition ($launchLogSectionsAfter -eq $launchLogSectionsBefore) `
        -Message 'Unified multi-game launch changed builder run logs.'
    $release = (
        & (Join-Path $fakeRepository 'na228.ps1') release 1.2.3
    ) -join "`n"
    Assert-Na2Test `
        -Condition ($release -match '\[fake\] release 1\.2\.3') `
        -Message 'Release dispatch did not preserve its optional version.'
    $extraReleaseArgumentRejected = $false
    try {
        & (Join-Path $fakeRepository 'na228.ps1') release 1.2.3 extra
    }
    catch {
        $extraReleaseArgumentRejected = (
            $_.Exception.Message -match 'accepts at most one version argument'
        )
    }
    Assert-Na2Test `
        -Condition $extraReleaseArgumentRejected `
        -Message 'Release dispatch accepted more than one version argument.'
    $latestLaunch = (
        & (Join-Path $fakeRepository 'na228.ps1') l
    ) -join "`n"
    $previousLaunch = (
        & (Join-Path $fakeRepository 'na228.ps1') p
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $latestLaunch -match 'multi-game launch latest'
        ) `
        -Message 'Latest selector alias did not resolve through game launch.'
    Assert-Na2Test `
        -Condition (
            $previousLaunch -match 'multi-game launch previous'
        ) `
        -Message 'Previous selector alias did not resolve through game launch.'
    $testLaunch = (
        & (Join-Path $fakeRepository 'na228.ps1') mt
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $testLaunch -match 'multi-game launch manual_test'
        ) `
        -Message 'Manual Test selector alias did not resolve through game launch.'
    & (Join-Path $fakeRepository 'na228.ps1') worker 'work\General\build\agent.iso'
    & (Join-Path $fakeRepository 'na228.ps1') build l
    & (Join-Path $fakeRepository 'na228.ps1') build mt
    $composedRecipe = (
        & (Join-Path $fakeRepository 'na228.ps1') nun5 bmtw
    ) -join "`n"
    Assert-Na2Test `
        -Condition ($composedRecipe -match 'multi-game launch nun5,manual_test') `
        -Message 'Trailing build/watch token did not preserve window order.'
    Assert-Na2Test `
        -Condition ($composedRecipe -match '\[fake\] watch 28015') `
        -Message 'Trailing watch suffix did not select the second game PINE port.'
    $leadingBuildWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') blw nun5
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $leadingBuildWatch -match 'multi-game launch latest,nun5' -and
            $leadingBuildWatch -match '\[fake\] watch 28014'
        ) `
        -Message 'Leading build/watch token did not preserve window order.'
    $scopedBuildWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') `
            blw `
            'src/localization' `
            nun5
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $scopedBuildWatch -match 'multi-game launch latest,nun5' -and
            $scopedBuildWatch -match (
                '\[fake\] watch 28014 .*sourcePath=src/localization'
            )
        ) `
        -Message 'C-folder watch did not preserve launch order or selection.'
    $directPlanWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') `
            nun5 `
            bmtw `
            'work\Font\operations\jutsu_names_overlay.json'
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $directPlanWatch -match 'multi-game launch nun5,manual_test' -and
            $directPlanWatch -match (
                'plan=work\\Font\\operations\\jutsu_names_overlay\.json'
            )
        ) `
        -Message 'Direct overlay-plan watch target was not forwarded.'
    $standaloneScopedWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') `
            w `
            'src/localization/font/font_numeric.c'
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $standaloneScopedWatch -match (
                '\[fake\] watch 0 .*' +
                'sourcePath=src/localization/font/font_numeric\.c'
            )
        ) `
        -Message 'Standalone C-file watch target was not forwarded.'
    $standaloneDefaultWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') w
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $standaloneDefaultWatch -match (
                '\[fake\] watch 0 .*sourcePath=src'
            )
        ) `
        -Message 'Bare watch command did not select the complete source tree.'
    $standaloneInjectionTestWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') w injection_test
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $standaloneInjectionTestWatch -match (
                '\[fake\] watch 0 .*' +
                'sourcePath=src/hot_reload_message\.c'
            )
        ) `
        -Message 'Injection-test watch target did not select the smoke message.'
    $latestWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') lw
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $latestWatch -match 'multi-game launch latest' -and
            $latestWatch -match '\[fake\] watch 28014'
        ) `
        -Message 'Latest watch token did not launch and watch Latest.'
    & (Join-Path $fakeRepository 'na228.ps1')
    $fakeLatest = [IO.File]::ReadAllText((Join-Path $fakeRepository 'logs\na228\latest.log'))
    $fakeRolling = [IO.File]::ReadAllText((Join-Path $fakeRepository 'logs\na228\rolling.log'))
    Assert-Na2Test -Condition ($fakeLatest -match '(?m)^mode: build$') -Message 'Root build mode was not logged.'
    foreach ($mode in (
        'manual-test-build',
        'build'
    )) {
        Assert-Na2Test `
            -Condition ($fakeRolling -match "(?m)^mode: $mode$") `
            -Message "$mode dispatch was not logged."
    }
    $rollingSectionCount = [regex]::Matches(
        $fakeRolling,
        '(?m)^--- NA2 RUN BEGIN ---$'
    ).Count
    Assert-Na2Test `
        -Condition ($rollingSectionCount -eq 7) `
        -Message (
            'Root dispatch test produced the wrong rolling-log section count: ' +
            $rollingSectionCount
        )
    Assert-Na2Test `
        -Condition (-not (Test-Na2WindowsAbsolutePath -Text $fakeRolling)) `
        -Message 'Root dispatch persisted an absolute path.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, '(?m)^\[fake\] launch .+$').Count -eq 1) `
        -Message 'Root build-and-launch produced the wrong direct launch count.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, '(?m)^\[fake\] launch dev .+$').Count -eq 1) `
        -Message 'Root dispatch did not preserve the configured development-launch default.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, 'ISO result: manual-test').Count -eq 3) `
        -Message 'Manual Test build recipes did not dispatch exactly three times.'
    $workerLatest = [IO.File]::ReadAllText((Join-Path $fakeRepository 'work\General\logs\latest.log'))
    Assert-Na2Test `
        -Condition ($workerLatest -match '(?m)^mode: worker-build$') `
        -Message 'Explicit worker build was not logged under the worker root.'
    Assert-Na2Test `
        -Condition ($workerLatest -match 'ISO result: worker') `
        -Message 'Explicit worker build did not dispatch to worker-output mode.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, 'ISO result: updated').Count -eq 4) `
        -Message 'Build-only and build-and-launch did not use the standard build pipeline.'
    $structuredLog = Join-Path $logs 'na228'
    $buildRecords = Join-Path $structuredLog 'builds'
    foreach ($buildId in 'old-previous', 'old-latest', 'new-latest', 'orphan') {
        New-Item -ItemType Directory -Force -Path (Join-Path $buildRecords $buildId) | Out-Null
    }
    Set-Content -NoNewline -LiteralPath $paths.files.latest_iso -Value 'latest'
    Set-Content -NoNewline -LiteralPath $paths.files.previous_iso -Value 'previous'
    Set-Na2Utf8FileAtomic `
        -Path (Join-Path $structuredLog 'builds.tsv') `
        -Content (
            "iso`tbuild_record`n" +
            "@build/NA2.28 - Current.iso`t@logs/na228/builds/old-latest`n" +
            "@build/NA2.28 - Previous.iso`t@logs/na228/builds/old-previous`n"
        )
    $renamedPaths = $paths.PSObject.Copy()
    $renamedFiles = $paths.files.PSObject.Copy()
    $renamedFiles.latest_iso = Join-Path $build 'NA v2.28 - Latest.iso'
    $renamedFiles.previous_iso = Join-Path $build 'NA v2.28 - Previous.iso'
    $renamedPaths.files = $renamedFiles
    $migratedMap = Read-Na2BuildMap `
        -LogDirectory $structuredLog `
        -Paths $renamedPaths
    Assert-Na2Test `
        -Condition ($migratedMap.LatestBuildId -eq 'old-latest') `
        -Message 'Renamed Latest ISO key lost its retained build record.'
    Assert-Na2Test `
        -Condition ($migratedMap.PreviousBuildId -eq 'old-previous') `
        -Message 'Renamed Previous ISO key lost its retained build record.'
    $migratedMapText = [IO.File]::ReadAllText((Join-Path $structuredLog 'builds.tsv'))
    Assert-Na2Test `
        -Condition ($migratedMapText -match '@build/NA v2\.28 - Latest\.iso') `
        -Message 'Renamed Latest ISO key was not migrated in builds.tsv.'
    Assert-Na2Test `
        -Condition ($migratedMapText -notmatch '@build/NA2\.28 - Current\.iso') `
        -Message 'The stale Current ISO key remained in builds.tsv.'
    Set-Na2BuildMap `
        -LogDirectory $structuredLog `
        -LatestBuildId 'old-latest' `
        -PreviousBuildId 'old-previous' `
        -Paths $paths
    $record = Complete-Na2BuildRecord `
        -LogDirectory $structuredLog `
        -BuildId 'new-latest' `
        -Result updated `
        -Rotated $true `
        -LatestIso $paths.files.latest_iso `
        -PreviousIso $paths.files.previous_iso `
        -Profile (Join-Path $paths.builder 'profiles\default.tsv') `
        -Paths $paths
    Assert-Na2Test -Condition ($record.BuildId -eq 'new-latest') -Message 'Updated build was not retained.'
    $updatedBuildMap = Read-Na2BuildMap `
        -LogDirectory $structuredLog `
        -Paths $paths
    Assert-Na2Test `
        -Condition ($updatedBuildMap.LatestBuildId -eq 'new-latest') `
        -Message 'Latest build mapping was not advanced.'
    Assert-Na2Test `
        -Condition ($updatedBuildMap.PreviousBuildId -eq 'old-latest') `
        -Message 'Previous build mapping was not rotated.'
    $buildMapText = [IO.File]::ReadAllText((Join-Path $structuredLog 'builds.tsv'))
    Assert-Na2Test `
        -Condition ($buildMapText -ceq (
            "iso`tbuild_record`n" +
            "@build/NA2.28 - Latest.iso`t@logs/na228/builds/new-latest`n" +
            "@build/NA2.28 - Previous.iso`t@logs/na228/builds/old-latest`n" +
            "@build/NA2.28 - E2E Test.iso`t`n" +
            "@build/NA2.28 - E2E Test Padded.iso`t`n"
        )) `
        -Message 'builds.tsv does not contain the exact atomic four-role mapping.'
    $remainingRecords = @(Get-ChildItem -LiteralPath $buildRecords -Directory).Name
    Assert-Na2Test -Condition ($remainingRecords.Count -eq 2) -Message 'Unreferenced build records were not pruned.'
    $buildResult = [IO.File]::ReadAllText((Join-Path $buildRecords 'new-latest\build_result.tsv'))
    Assert-Na2Test -Condition ($buildResult -match "updated`tyes") -Message 'build_result.tsv lacks result/rotation.'
    Assert-Na2Test -Condition ($buildResult -match '@build/NA2\.28 - Latest\.iso') -Message 'build_result.tsv lacks a portable ISO path.'
    Assert-Na2Test -Condition (-not (Test-Na2WindowsAbsolutePath -Text $buildResult)) -Message 'build_result.tsv contains an absolute path.'

    New-Item -ItemType Directory -Path (Join-Path $buildRecords 'duplicate') | Out-Null
    $unchanged = Complete-Na2BuildRecord `
        -LogDirectory $structuredLog `
        -BuildId duplicate `
        -Result unchanged `
        -Rotated $false `
        -LatestIso $paths.files.latest_iso `
        -PreviousIso $paths.files.previous_iso `
        -Profile 'na228_builder/profiles/default.tsv' `
        -Paths $paths
    Assert-Na2Test `
        -Condition ($unchanged.BuildId -eq 'duplicate') `
        -Message 'Unchanged full build did not become the latest provenance record.'
    Assert-Na2Test `
        -Condition (Test-Path -LiteralPath (Join-Path $buildRecords 'duplicate')) `
        -Message 'Unchanged full build record was not retained.'
    Assert-Na2Test `
        -Condition (-not (Test-Path -LiteralPath (Join-Path $buildRecords 'new-latest'))) `
        -Message 'Superseded latest build record was not pruned.'

    $freshStructuredLog = Join-Path $logs 'fresh-na228'
    $firstBuildId = 'first-unchanged'
    New-Item -ItemType Directory -Force `
        -Path (Join-Path $freshStructuredLog "builds\$firstBuildId") | Out-Null
    $firstUnchanged = Complete-Na2BuildRecord `
        -LogDirectory $freshStructuredLog `
        -BuildId $firstBuildId `
        -Result unchanged `
        -Rotated $false `
        -LatestIso $paths.files.latest_iso `
        -PreviousIso $null `
        -Profile 'na228_builder/profiles/default.tsv' `
        -Paths $paths
    Assert-Na2Test `
        -Condition ($firstUnchanged.BuildId -eq $firstBuildId) `
        -Message 'First unchanged build was incorrectly discarded.'
    $firstBuildMap = Read-Na2BuildMap `
        -LogDirectory $freshStructuredLog `
        -Paths $paths
    Assert-Na2Test `
        -Condition ($firstBuildMap.LatestBuildId -eq $firstBuildId) `
        -Message 'First unchanged build did not establish the latest mapping.'
    Assert-Na2Test `
        -Condition ([string]::IsNullOrWhiteSpace($firstBuildMap.PreviousBuildId)) `
        -Message 'Unavailable previous ISO record was not left empty.'
    $firstBuildMapText = [IO.File]::ReadAllText((Join-Path $freshStructuredLog 'builds.tsv'))
    Assert-Na2Test `
        -Condition ($firstBuildMapText -match "(?m)^@build/NA2\.28 - Previous\.iso`t$") `
        -Message 'builds.tsv omitted the empty previous ISO row.'
    $firstBuildResult = [IO.File]::ReadAllText(
        (Join-Path $freshStructuredLog "builds\$firstBuildId\build_result.tsv")
    )
    Assert-Na2Test `
        -Condition ($firstBuildResult -match "unchanged`tno") `
        -Message 'First unchanged build result was not recorded.'

    Write-Host 'NA2 run-log tests passed.' -ForegroundColor Green
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {
    }
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
