[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        'run-log',
        'build-records',
        'command-routing',
        'game-launch',
        'build-launch',
        'build-options'
    )]
    [string]$Group
)

$ErrorActionPreference = 'Stop'
$sourceRepository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$originalTaskWorkRoot = $env:NA228_TASK_WORK_ROOT
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
) "na2-$Group-tests-$PID-$([guid]::NewGuid().ToString('N'))"

try {
    if ($Group -in @('run-log', 'build-records')) {
    $repository = Join-Path $testRoot 'repo'
    $logs = Join-Path $repository 'logs'
    $build = Join-Path $repository 'build'
    $paths = [pscustomobject]@{
        repository = $repository
        source = Join-Path $testRoot 'source'
        build = $build
        logs = $logs
        builder = Join-Path $repository 'na228_builder'
        pcsx2_dev = Join-Path $testRoot 'pcsx2_dev'
        scripts = Join-Path $repository 'scripts'
        files = [pscustomobject]@{
            latest_iso = Join-Path $build 'NA2.28 - Latest.iso'
            previous_iso = Join-Path $build 'NA2.28 - Previous.iso'
            e2e_test_iso = Join-Path $build 'NA2.28 - E2E Test.iso'
            e2e_test_shifted_iso = Join-Path $build 'NA2.28 - E2E Test Shifted.iso'
        }
    }
    New-Item -ItemType Directory -Force -Path $logs, $build | Out-Null
    }

    if ($Group -ceq 'run-log') {
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

    $parsedConfigurationFailure = Get-Na2ConfigurationFailure -Output @(
        'Traceback (most recent call last):'
        '  File "builder.py", line 1, in main'
        'na228_builder.scripts.catalog.ConfigurationError: Invalid config value at features.example.value: got 0.1; expected int'
    )
    Assert-Na2Test `
        -Condition (
            $null -ne $parsedConfigurationFailure -and
            $parsedConfigurationFailure.Message -ceq (
                'Invalid config value at features.example.value: got 0.1; expected int'
            ) -and
            $parsedConfigurationFailure.TechnicalDetails -match '^Traceback'
        ) `
        -Message 'Python configuration failure was not separated into user and technical details.'

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
    }

    if ($Group -in @('command-routing', 'game-launch', 'build-launch', 'build-options')) {
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
    Set-Na2Utf8FileAtomic `
        -Path (Join-Path $fakeNa2Scripts 'launch_settings.ps1') `
        -Content @'
function Get-Na2StartupFastForwardFrames {
    param([string]$Configuration, [psobject]$Paths)
    if ($Configuration -ceq 'test') { return [UInt64]222 }
    return [UInt64]321
}
'@
    $fakePcsx2Scripts = Join-Path $fakeRepository 'scripts\pcsx2'
    New-Item -ItemType Directory -Force -Path $fakePcsx2Scripts | Out-Null
    $fakeReleaseScripts = Join-Path $fakeRepository 'scripts\release'
    New-Item -ItemType Directory -Force -Path $fakeReleaseScripts | Out-Null
    $fakeInjectionScripts = Join-Path $fakeRepository 'scripts\injection'
    New-Item -ItemType Directory -Force -Path $fakeInjectionScripts | Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'scripts\na228\task_paths.ps1') `
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
    "pcsx2_dev": "pcsx2_dev",
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
    "settings": "@repository/settings.json",
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
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeRepository 'settings.json') -Content @'
{
  "schema_version": 1,
  "title": "Narutimate Accel v2.28",
  "serial": "SLOP-NA228",
  "output_boot_path": "SLOP_NA2.28",
  "startup_fast_forward_frames": 321,
  "builds": {
    "latest": { "aliases": ["l"] },
    "previous": { "aliases": ["p"] },
    "manual": { "aliases": ["m"] },
    "e2e_test": {},
    "e2e_test_shifted": {}
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
    "manual": "Manual",
    "e2e_test": "E2E Test",
    "e2e_test_shifted": "E2E Test Shifted",
}
aliases = {"l": "latest", "p": "previous", "m": "manual"}
name = aliases.get(name.casefold(), name)
if name in builds:
    title = "Narutimate Accel v2.28"
    result = {
        "iso": str(root / "build" / f"{title} - {builds[name]}.iso"),
        "postfix": builds[name],
        "cheats": str(root / "pcsx2_files" / "cheats" / "SLOP-NA228.pnach"),
        "game_settings": str(root / "pcsx2_files" / "game_settings" / "SLOP-NA228.ini"),
        "memory_card": str(root / "pcsx2_files" / "memory_cards" / f"NA v2.28 - {builds[name]}.ps2"),
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
        'source', 'utils', 'build', 'logs', 'na228_builder', 'pcsx2_dev',
        'pcsx2_files\cheats', 'pcsx2_files\game_settings',
        'pcsx2_files\input_profiles', 'pcsx2_files\memory_cards', 'scripts', 'source\NA2.iso.files',
        'source\NUN5.iso.files', 'tests', 'work'
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $fakeRepository $directory) | Out-Null
    }
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeRepository 'tests\run.ps1') -Content @'
param()
Add-Content `
    -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') `
    -Value 'run'
Write-Output '[fake] unit tests'
'@
    if ($Group -ceq 'command-routing') {
    $helpText = (& (Join-Path $fakeRepository 'na228.ps1') help) -join "`n"
    Assert-Na2Test `
        -Condition (-not (Test-Path -LiteralPath (Join-Path $fakeRepository 'logs\na228'))) `
        -Message 'Help invocation created run logs.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 <token> \[token\] \[-t\|-u\]') `
        -Message 'Root help omitted the ordered token grammar.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 \[-f\] \[-t\|-u\]\s+') `
        -Message 'Root help omitted the default build-and-launch signature.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 build -c <configuration>\s+') `
        -Message 'Root help omitted the canonical cache-build command.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 build l\|m\s') `
        -Message 'Root help omitted the explicit build-only command.'
    Assert-Na2Test `
        -Condition ($helpText -notmatch '(?m)^\s*na228 build -d\s+') `
        -Message 'Root help retained the retired development dry-run command.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 test\s+') `
        -Message 'Root help omitted the unit-test command.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 e2e \[-s\]\s+') `
        -Message 'Root help omitted the global E2E command.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 e2e create <all\|suite> \[-noref\]\s+') `
        -Message 'Root help omitted default NUN5 reference creation and its opt-out.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 e2e rename <suite> <new-suite>\s+') `
        -Message 'Root help omitted suite rename.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 e2e delete <all\|suite>\s+') `
        -Message 'Root help omitted suite deletion.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 e2e commit \[-p\]\s+') `
        -Message 'Root help omitted the coordinated E2E commit command.'
    Assert-Na2Test `
        -Condition (
            $helpText -match '(?m)^\s*na228 build l\|m[^\r\n]*\r?\n\s*na228 build -c[^\r\n]*\r?\n\s*na228 test' -and
            $helpText -match '(?m)^\s*na228 test[^\r\n]*\r?\n\r?\n\s*na228 e2e' -and
            $helpText -match '(?m)^\s*na228 e2e commit[^\r\n]*\r?\n\r?\n\s*na228 release' -and
            $helpText -match '(?m)^\s*na228 help[^\r\n]*\r?\n\r?\n\s*games:'
        ) `
        -Message 'Root help did not group build commands or visually separate the E2E command block.'
    }
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakePcsx2Scripts 'launch.ps1') -Content @'
param(
    [string]$Target = 'dev',
    [string]$IsoPath,
    [switch]$Turbo,
    [switch]$Unlimited,
    [UInt64]$UnlimitedForFrames
)
Write-Host "[fake] launch $Target $IsoPath turbo=$($Turbo.IsPresent) unlimited=$($Unlimited.IsPresent) frames=$UnlimitedForFrames"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakePcsx2Scripts 'launch_games.ps1') -Content @'
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Games,
    [string]$Play,
    [string]$Record,
    [switch]$Snapshots,
    [string]$MemoryCard,
    [switch]$DiscardMemoryCardWrites,
    [switch]$Turbo,
    [switch]$Unlimited,
    [UInt64]$UnlimitedForFrames,
    [string]$ProjectRoot
)
$aliases = @{
    l = 'latest'
    p = 'previous'
    m = 'manual'
}
$canonical = @($Games | ForEach-Object {
    if ($aliases.ContainsKey($_)) { $aliases[$_] } else { $_ }
})
if (@($canonical | Where-Object { $_ -notin @(
    'latest', 'previous', 'manual', 'na2', 'nun5'
) }).Count -gt 0) {
    throw "Unknown game name: $($Games -join ',')"
}
Write-Output (
    "[fake] multi-game launch $($canonical -join ',') " +
    "play=$Play record=$Record snapshots=$($Snapshots.IsPresent) " +
    "memory=$MemoryCard discard=$($DiscardMemoryCardWrites.IsPresent) " +
    "turbo=$($Turbo.IsPresent) unlimited=$($Unlimited.IsPresent) " +
    "frames=$UnlimitedForFrames project=$ProjectRoot"
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
    [switch]$ManualOnly,
    [string]$CacheConfiguration,
    [string]$CacheLogDirectory,
    [switch]$Force
)
if ($env:NA228_TEST_CONFIG_ERROR -ceq '1') {
    $exception = [InvalidOperationException]::new(
        'Invalid config value at features.example.value: got 0.1; expected int'
    )
    $exception.Data['Na2ConfigurationError'] = $true
    $exception.Data['Na2TechnicalDetails'] = (
        "Traceback (most recent call last):`n" +
        "  File `"$PSScriptRoot\builder.py`", line 1, in main`n" +
        'na228_builder.scripts.catalog.ConfigurationError: Invalid config value at features.example.value: got 0.1; expected int'
    )
    throw $exception
}
if ($CacheConfiguration) {
    Write-Host "[fake] cache configuration=$CacheConfiguration"
    Write-Host '[na228] ISO result: cache (reused); rotation: no; PCSX2 left running.'
    [pscustomobject]@{
        Status = 'cache'
        OutputIso = 'work\cache\isos\FAKE.iso'
        ChangedRoles = [string[]]@()
    }
}
elseif ($ManualOnly) {
    Write-Host "[na228] ISO result: manual; rotation: no; PCSX2 left running; force=$($Force.IsPresent)."
    [pscustomobject]@{ Status = 'manual'; ChangedRoles = [string[]]@('manual') }
}
else {
    Write-Host "[na228] ISO result: updated; rotation: yes; force=$($Force.IsPresent)."
    [pscustomobject]@{
        Status = 'updated'
        ChangedRoles = [string[]]@('latest', 'previous')
        LaunchIso = if ($Force) { 'force-output.iso' } else { $null }
    }
}
'@
    $fakeVisualRoot = Join-Path $fakeRepository 'e2e'
    $fakeVisualScripts = Join-Path $fakeVisualRoot 'scripts'
    New-Item -ItemType Directory -Force -Path `
        $fakeVisualScripts, `
        (Join-Path $fakeVisualRoot 'suites\font') | Out-Null
    foreach ($suiteDefinition in 'alpha', 'beta', 'font\load_save') {
        Set-Na2Utf8FileAtomic `
            -Path (Join-Path $fakeVisualRoot "suites\$suiteDefinition.p2m2") `
            -Content 'recording'
    }
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeVisualScripts 'run.ps1') -Content @'
param([string]$Suite, [switch]$Shifted)
Add-Content `
    -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') `
    -Value "run suite=$Suite shifted=$($Shifted.IsPresent)"
[pscustomobject]@{ Status = 'passed' }
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeVisualScripts 'create_suite.ps1') -Content @'
param(
    [string]$Suite,
    [switch]$All,
    [switch]$NoReference
)
Add-Content `
    -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') `
    -Value "create suite=$Suite all=$($All.IsPresent) noref=$($NoReference.IsPresent)"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeVisualScripts 'rename_suite.ps1') -Content @'
param([string]$Suite, [string]$NewSuite)
Add-Content `
    -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') `
    -Value "rename suite=$Suite newSuite=$NewSuite"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeVisualScripts 'delete_suite.ps1') -Content @'
param([string]$Suite, [switch]$All)
Add-Content `
    -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') `
    -Value "delete suite=$Suite all=$($All.IsPresent)"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeVisualScripts 'commit_captures.ps1') -Content @'
param([switch]$Preserve)
Add-Content `
    -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') `
    -Value "commit preserve=$($Preserve.IsPresent)"
'@
    }

    if ($Group -ceq 'command-routing') {
    $unitTestCallsPath = Join-Path $fakeRepository 'tests\calls.txt'
    $visualCalls = Join-Path $fakeVisualScripts 'calls.txt'
    & (Join-Path $fakeRepository 'na228.ps1') test
    $testCalls = @(Get-Content -LiteralPath $unitTestCallsPath)
    Assert-Na2Test `
        -Condition (
            ($testCalls -join ',') -ceq 'run' -and
            -not (Test-Path -LiteralPath $visualCalls)
        ) `
        -Message 'Bare na228 test did not dispatch only the unit-test runner.'
    $testArgumentsRejected = $false
    try {
        & (Join-Path $fakeRepository 'na228.ps1') test alpha
    }
    catch {
        $testArgumentsRejected = $_.Exception.Message -ceq 'Usage: na228 test'
    }
    Assert-Na2Test `
        -Condition $testArgumentsRejected `
        -Message 'na228 test accepted an argument after the command split.'
    & (Join-Path $fakeRepository 'na228.ps1') e2e
    & (Join-Path $fakeRepository 'na228.ps1') e2e -s
    & (Join-Path $fakeRepository 'na228.ps1') e2e create font/character_select
    & (Join-Path $fakeRepository 'na228.ps1') e2e create font/no_reference -noref
    & (Join-Path $fakeRepository 'na228.ps1') e2e create all
    & (Join-Path $fakeRepository 'na228.ps1') e2e rename font/character_select font/characters
    & (Join-Path $fakeRepository 'na228.ps1') e2e delete font/characters
    & (Join-Path $fakeRepository 'na228.ps1') e2e delete all
    & (Join-Path $fakeRepository 'na228.ps1') e2e commit
    & (Join-Path $fakeRepository 'na228.ps1') e2e commit -p
    $calls = @(Get-Content -LiteralPath $visualCalls)
    Assert-Na2Test `
        -Condition ($calls.Count -eq 10 -and
            $calls[0] -ceq 'run suite= shifted=False' -and
            $calls[1] -ceq 'run suite= shifted=True' -and
            $calls[2] -ceq 'create suite=font/character_select all=False noref=False' -and
            $calls[3] -ceq 'create suite=font/no_reference all=False noref=True' -and
            $calls[4] -ceq 'create suite= all=True noref=False' -and
            $calls[5] -ceq 'rename suite=font/character_select newSuite=font/characters' -and
            $calls[6] -ceq 'delete suite=font/characters all=False' -and
            $calls[7] -ceq 'delete suite= all=True' -and
            $calls[8] -ceq 'commit preserve=False' -and
            $calls[9] -ceq 'commit preserve=True') `
        -Message 'Global E2E or lifecycle-command dispatch was incorrect.'
    $customReferenceRejected = $false
    try {
        & (Join-Path $fakeRepository 'na228.ps1') e2e create font/with_reference nun6
    }
    catch {
        $customReferenceRejected = $_.Exception.Message -ceq (
            'Usage: na228 e2e create <all|suite> [-noref]'
        )
    }
    Assert-Na2Test `
        -Condition $customReferenceRejected `
        -Message 'The public E2E create command accepted a custom reference game.'
    $suiteSelectionRejected = $false
    try {
        & (Join-Path $fakeRepository 'na228.ps1') e2e alpha
    }
    catch {
        $suiteSelectionRejected = $_.Exception.Message -match '^Usage: na228 e2e'
    }
    Assert-Na2Test `
        -Condition $suiteSelectionRejected `
        -Message 'The public E2E command accepted a single-suite execution.'
    }

    if ($Group -ceq 'game-launch') {
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
    $callerLocation = [IO.Path]::GetFullPath((Get-Location).Path)
    $multiGameLaunch = (
        & (Join-Path $fakeRepository 'na228.ps1') na2 nun5
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $multiGameLaunch -match (
                '\[fake\] multi-game launch na2,nun5 .*' +
                'turbo=False unlimited=False frames=321'
            )
        ) `
        -Message 'Unified multi-game launch did not preserve ordered selectors and timed startup acceleration.'
    Assert-Na2Test `
        -Condition ([IO.Path]::GetFullPath((Get-Location).Path) -ceq $callerLocation) `
        -Message 'Root game launch did not restore the caller working directory.'
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
    $snapshotPlayback = (
        & (Join-Path $fakeRepository 'na228.ps1') `
            nun5 `
            -s `
            'practice-menu'
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $snapshotPlayback -match (
                'multi-game launch nun5 ' +
                'play=practice-menu record= snapshots=True .*frames=0'
            )
        ) `
        -Message 'Snapshot playback was not forwarded to the shared launcher.'
    $unlimitedLaunch = (
        & (Join-Path $fakeRepository 'na228.ps1') nun5 -u
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $unlimitedLaunch -match (
                'multi-game launch nun5 .*' +
                'turbo=False unlimited=True frames=0'
            )
        ) `
        -Message 'Permanent Unlimited was not routed to the shared launcher.'
    $memoryCardLaunch = (
        & (Join-Path $fakeRepository 'na228.ps1') `
            nun5 `
            l `
            -mc `
            'Shared.ps2' `
            -dw
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $memoryCardLaunch -match (
                'multi-game launch nun5,latest .*' +
                'memory=Shared\.ps2 discard=True'
            )
        ) `
        -Message 'Memory-card and discard-write options were not bound for the shared launcher.'
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
        & (Join-Path $fakeRepository 'na228.ps1') m
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $testLaunch -match 'multi-game launch manual' -and
            $testLaunch -match 'frames=222'
        ) `
        -Message 'Manual selector did not use the test catalog launch settings.'
    }

    if ($Group -ceq 'build-launch') {
    $env:NA228_TASK_WORK_ROOT = 'work\General'
    $cacheDispatch = (
        & (Join-Path $fakeRepository 'na228.ps1') build -c test *>&1
    ) -join "`n"
    $env:NA228_TASK_WORK_ROOT = 'work\Equivalence'
    $configuredCacheDispatch = (
        & (Join-Path $fakeRepository 'na228.ps1') build -c dev *>&1
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $configuredCacheDispatch -match '\[fake\] cache configuration=dev' -and
            $configuredCacheDispatch -match 'work\\cache\\isos\\FAKE\.iso'
        ) `
        -Message 'Root cache-build command did not return the selected configuration cache path.'
    & (Join-Path $fakeRepository 'na228.ps1') build l
    & (Join-Path $fakeRepository 'na228.ps1') build m
    $composedRecipe = (
        & (Join-Path $fakeRepository 'na228.ps1') nun5 bmw
    ) -join "`n"
    Assert-Na2Test `
        -Condition ($composedRecipe -match 'multi-game launch nun5,manual') `
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
            bmw `
            'work\Font\operations\jutsu_names_overlay.json'
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $directPlanWatch -match 'multi-game launch nun5,manual' -and
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
    $fakeRolling = [IO.File]::ReadAllText((Join-Path $fakeRepository 'logs\na228\rolling.log'))
    foreach ($mode in (
        'manual-build',
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
        -Condition ($rollingSectionCount -eq 6) `
        -Message (
            'Build/watch routing produced the wrong rolling-log section count: ' +
            $rollingSectionCount
        )
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, 'ISO result: manual').Count -eq 3) `
        -Message 'Manual build/watch recipes did not dispatch exactly three times.'
    $cacheLatest = [IO.File]::ReadAllText((Join-Path $fakeRepository 'work\General\logs\latest.log'))
    Assert-Na2Test `
        -Condition ($cacheLatest -match '(?m)^mode: cache-build$') `
        -Message 'Cache build was not logged under the task root.'
    Assert-Na2Test `
        -Condition ($cacheLatest -match 'ISO result: cache') `
        -Message 'Cache build did not dispatch to cache mode.'
    $configuredCacheLatest = [IO.File]::ReadAllText((Join-Path $fakeRepository 'work\Equivalence\logs\latest.log'))
    Assert-Na2Test `
        -Condition (
            $configuredCacheLatest -match '(?m)^mode: cache-build$' -and
            $configuredCacheLatest -match 'ISO result: cache'
        ) `
        -Message 'Configured cache-build evidence was not retained in its task run log.'
    }

    if ($Group -ceq 'build-options') {
    $forceLaunch = (& (Join-Path $fakeRepository 'na228.ps1') -f *>&1) -join "`n"
    Assert-Na2Test `
        -Condition (
            $forceLaunch -match 'force=True' -and
            $forceLaunch -match (
                '\[fake\] launch dev force-output\.iso ' +
                'turbo=False unlimited=False frames=321'
            )
        ) `
        -Message 'Force mode and timed startup acceleration were not routed through build-and-launch.'
    $turboBuildRejected = $false
    try {
        & (Join-Path $fakeRepository 'na228.ps1') build l -t
    }
    catch {
        $turboBuildRejected = (
            $_.Exception.Message -match '-t and -u are valid only when launching one or two games'
        )
    }
    Assert-Na2Test `
        -Condition $turboBuildRejected `
        -Message 'Turbo mode was accepted by a build-only command.'
    $forcedManualBuild = (
        & (Join-Path $fakeRepository 'na228.ps1') build m -f *>&1
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $forcedManualBuild -match 'ISO result: manual.*force=True' -and
            $forcedManualBuild -notmatch '\[fake\] workshop'
        ) `
        -Message 'Force mode was not routed through the build-only Manual command.'
    $forcedManualLaunch = (
        & (Join-Path $fakeRepository 'na228.ps1') bm -f *>&1
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $forcedManualLaunch -match 'ISO result: manual.*force=True' -and
            $forcedManualLaunch -match 'multi-game launch manual'
        ) `
        -Message 'Force mode was not consumed by the build-and-run Manual command.'
    $turboLaunch = (& (Join-Path $fakeRepository 'na228.ps1') -t *>&1) -join "`n"
    Assert-Na2Test `
        -Condition (
            $turboLaunch -match (
                '\[fake\] launch dev .+ ' +
                'turbo=True unlimited=False frames=321'
            )
        ) `
        -Message 'Turbo fallback was not routed through default build-and-launch.'
    $fakeLatest = [IO.File]::ReadAllText((Join-Path $fakeRepository 'logs\na228\latest.log'))
    $fakeRolling = [IO.File]::ReadAllText((Join-Path $fakeRepository 'logs\na228\rolling.log'))
    $rollingSectionCount = [regex]::Matches(
        $fakeRolling,
        '(?m)^--- NA2 RUN BEGIN ---$'
    ).Count
    Assert-Na2Test `
        -Condition (
            $fakeLatest -match '(?m)^mode: build$' -and
            $rollingSectionCount -eq 4
        ) `
        -Message (
            'Build-option routing did not retain the latest build log or produced ' +
            'the wrong rolling-log section count: ' +
            $rollingSectionCount
        )
    Assert-Na2Test `
        -Condition (-not (Test-Na2WindowsAbsolutePath -Text $fakeRolling)) `
        -Message 'Root dispatch persisted an absolute path.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, '(?m)^\[fake\] launch .+$').Count -eq 2) `
        -Message 'Root build-and-launch produced the wrong direct launch count.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, '(?m)^\[fake\] launch dev .+$').Count -eq 2) `
        -Message 'Root dispatch did not preserve the configured development-launch default.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, 'ISO result: updated').Count -eq 2) `
        -Message 'Forced and turbo launches did not use the standard build pipeline.'
    $oldLastExitCode = $global:LASTEXITCODE
    try {
        $env:NA228_TEST_CONFIG_ERROR = '1'
        $global:LASTEXITCODE = 0
        $configurationFailureOutput = (
            & (Join-Path $fakeRepository 'na228.ps1') build l *>&1
        ) -join "`n"
        $configurationFailureExitCode = $LASTEXITCODE
    }
    finally {
        Remove-Item Env:NA228_TEST_CONFIG_ERROR -ErrorAction SilentlyContinue
        $global:LASTEXITCODE = $oldLastExitCode
    }
    Assert-Na2Test `
        -Condition (
            $configurationFailureExitCode -eq 1 -and
            $configurationFailureOutput -match (
                '\[na228\] Build failed: Invalid config value at ' +
                'features\.example\.value: got 0\.1; expected int'
            ) -and
            $configurationFailureOutput -notmatch 'Traceback'
        ) `
        -Message 'Development config failure was not concise or returned the wrong exit code.'
    $configurationFailureLog = [IO.File]::ReadAllText(
        (Join-Path $fakeRepository 'logs\na228\latest.log')
    )
    Assert-Na2Test `
        -Condition (
            $configurationFailureLog -match '(?m)^outcome: failed$' -and
            $configurationFailureLog -match '(?m)^error: Invalid config value at ' -and
            $configurationFailureLog -match '(?m)^technical_details:$' -and
            $configurationFailureLog -match 'Traceback \(most recent call last\):' -and
            $configurationFailureLog -match '@scripts/na228/builder\.py'
        ) `
        -Message 'Development config traceback was not retained in the portable run log.'
    }

    if ($Group -ceq 'build-records') {
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
    $renamedFiles.latest_iso = Join-Path $build 'Narutimate Accel v2.28 - Latest.iso'
    $renamedFiles.previous_iso = Join-Path $build 'Narutimate Accel v2.28 - Previous.iso'
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
        -Condition ($migratedMapText -match '@build/Narutimate Accel v2\.28 - Latest\.iso') `
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
        -Configuration (Join-Path $paths.builder 'configurations\dev.json') `
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
            "@build/NA2.28 - E2E Test Shifted.iso`t`n"
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
        -Configuration 'na228_builder/configurations/dev.json' `
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
        -Configuration 'na228_builder/configurations/dev.json' `
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
    }

    Write-Host "NA2 $Group tests passed." -ForegroundColor Green
}
finally {
    if ($null -eq $originalTaskWorkRoot) {
        Remove-Item Env:NA228_TASK_WORK_ROOT -ErrorAction SilentlyContinue
    }
    else {
        $env:NA228_TASK_WORK_ROOT = $originalTaskWorkRoot
    }
    try {
        Stop-Transcript | Out-Null
    }
    catch {
    }
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
