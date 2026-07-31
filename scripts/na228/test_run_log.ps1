[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\build_log.ps1')

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
        }
    }
    New-Item -ItemType Directory -Force -Path $logs, $build | Out-Null
    $externalPath = 'C{0}{1}Private{1}outside.txt' -f `
        [IO.Path]::VolumeSeparatorChar, [IO.Path]::DirectorySeparatorChar

    $portable = ConvertTo-Na2PortableText `
        -Text "ISO: $build\NA2.28 - Latest.iso`nExternal: $externalPath" `
        -ProjectPaths $paths
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
            -ProjectPaths $paths `
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
    $failureContext = Start-Na2RunLog -Mode failure-test -ProjectPaths $failurePaths
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
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\..\na228.ps1') -Destination $fakeRepository
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\lib\project_paths.ps1') `
        -Destination (Join-Path $fakeRepository 'scripts\lib')
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\lib\run_log.ps1') `
        -Destination (Join-Path $fakeRepository 'scripts\lib')
    $fakeNa2Scripts = Join-Path $fakeRepository 'scripts\na228'
    New-Item -ItemType Directory -Force -Path $fakeNa2Scripts | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'run.ps1') `
        -Destination $fakeNa2Scripts
    $fakePcsx2Scripts = Join-Path $fakeRepository 'scripts\pcsx2'
    New-Item -ItemType Directory -Force -Path $fakePcsx2Scripts | Out-Null
    $fakeReleaseScripts = Join-Path $fakeRepository 'scripts\release'
    New-Item -ItemType Directory -Force -Path $fakeReleaseScripts | Out-Null
    $fakeInjectionScripts = Join-Path $fakeRepository 'scripts\injection'
    New-Item -ItemType Directory -Force -Path $fakeInjectionScripts | Out-Null
    $fakeSettings = Join-Path $fakeRepository 'settings'
    New-Item -ItemType Directory -Force -Path $fakeSettings | Out-Null
    Copy-Item `
        -LiteralPath (Join-Path $PSScriptRoot '..\injection\watch_targets.ps1') `
        -Destination $fakeInjectionScripts
    $fakeActualizationScripts = Join-Path $fakePcsx2Scripts 'actualization'
    New-Item -ItemType Directory -Force -Path $fakeActualizationScripts | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\pcsx2\actualization\act.ps1') `
        -Destination $fakeActualizationScripts
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'worker_paths.ps1') `
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
    "pcsx2_memory_cards": "@pcsx2_files/memory_cards",
    "scripts": "scripts",
    "pcsx2_scripts": "@scripts/pcsx2",
    "work": "work"
  },
  "files": {
    "game_catalog": "@repository/settings/games.json",
    "watch_catalog": "@repository/settings/watchers.json",
    "pcsx2_launch_command": "@scripts/pcsx2/launch.ps1",
    "na228_game_launch_command": "@scripts/na228/launch_games.ps1",
    "release_publish_command": "@scripts/release/publish_release.ps1",
    "actualize_command": "@pcsx2_scripts/actualization/act.ps1",
    "actualize_na228_command": "@pcsx2_scripts/actualization/sync_game_files.ps1",
    "actualize_input_command": "@pcsx2_scripts/actualization/sync_input.ps1"
  }
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeSettings 'watchers.json') -Content @'
{
  "schema_version": 1,
  "default_target": "font",
  "targets": {
    "font": {
      "overlay_plan": "scripts/injection/targets/font.json",
      "whole_source": true
    },
    "injection_test": {
      "source_id": "hot_reload_message",
      "entry": "project.hot_reload_message"
    }
  }
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeRepository 'project-paths.json') -Content $manifest
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeSettings 'games.json') -Content @'
{
  "schema_version": 1,
  "builds": {
    "title": "NA2.28",
    "memory_card": "@pcsx2_memory_cards/NA228.ps2",
    "entries": {
      "latest": { "aliases": ["l"], "postfix": "Latest" },
      "previous": { "aliases": ["p"], "postfix": "Previous" },
      "test": { "aliases": ["t"], "postfix": "Test" }
    }
  },
  "sources": {
    "na2": {
      "iso": "@source/NA2.iso",
      "extracted": "@source/NA2.iso.files"
    },
    "nun5": {
      "iso": "@source/NUN5.iso",
      "extracted": "@source/NUN5.iso.files"
    }
  }
}
'@
    foreach ($directory in @(
        'source', 'utils', 'build', 'logs', 'na228_builder', 'pcsx2_stable',
        'pcsx2_files\memory_cards', 'scripts', 'source\NA2.iso.files',
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
        -Condition ($helpText -match '(?m)^\s*na228 validate\s') `
        -Message 'Root help omitted the compose-only validation command.'
    Assert-Na2Test `
        -Condition ($helpText -match '(?m)^\s*na228 build l\|t\s') `
        -Message 'Root help omitted the explicit build-only command.'
    Assert-Na2Test `
        -Condition ($helpText -notmatch '(?m)^\s*na228 -[btcpwh]\b') `
        -Message 'Root help still exposes a retired dashed mode.'
    Assert-Na2Test `
        -Condition ($helpText -notmatch '(?m)^\s*na228 launch\b') `
        -Message 'Root help still exposes the retired launch subcommand.'
    $actHelpText = (
        & (Join-Path $fakeActualizationScripts 'act.ps1') help
    ) -join "`n"
    $actShortHelpText = (
        & (Join-Path $fakeActualizationScripts 'act.ps1') -h
    ) -join "`n"
    foreach ($expectedCommand in 'act na228', 'act input') {
        Assert-Na2Test `
            -Condition ($actHelpText.Contains($expectedCommand)) `
            -Message "Actualization help omitted $expectedCommand."
    }
    Assert-Na2Test `
        -Condition ($actShortHelpText -ceq $actHelpText) `
        -Message 'act -h does not match act help.'
    Assert-Na2Test `
        -Condition (-not (Test-Path -LiteralPath (
            Join-Path $fakeRepository 'logs\na228'
        ))) `
        -Message 'Actualization help created run logs.'

    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeActualizationScripts 'sync_game_files.ps1') -Content @'
param([string[]]$Roles)
$resolvedRoles = @(
    if ($null -eq $Roles -or $Roles.Count -eq 0) {
        'latest'
    }
    else {
        $Roles
    }
)
$callLog = [IO.Path]::GetFullPath(
    (Join-Path $PSScriptRoot '..\..\..\actualization_calls.txt')
)
Add-Content `
    -LiteralPath $callLog `
    -Value ($resolvedRoles -join ',') `
    -Encoding utf8
Write-Host "[fake] actualize na228 roles=$($resolvedRoles -join ',')"
[pscustomobject]@{
    Roles = @(
        foreach ($role in $resolvedRoles) {
            [pscustomobject]@{
                Role = (Get-Culture).TextInfo.ToTitleCase($role)
                Serial = 'SLOP-NA228'
                CRC = '12345678'
            }
        }
    )
    CheatAliases = @('pcsx2_files/cheats/SLOP-NA228_12345678.pnach')
    RemovedCheatSymlinks = @()
    EnabledCheats = @()
    CreatedGameSettings = @()
    UpdatedGameSettings = @()
    PreservedGameSettings = @('SLOP-NA228_12345678.ini')
    RemovedGameSettings = @()
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeActualizationScripts 'sync_input.ps1') -Content @'
param([switch]$PassThru)
$result = [pscustomobject]@{ Changed = $false }
if ($PassThru) { $result }
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakePcsx2Scripts 'launch.ps1') -Content @'
param([string]$Target = 'dev', [string]$IsoPath)
Write-Host "[fake] launch $Target $IsoPath"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeNa2Scripts 'launch_games.ps1') -Content @'
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Games
)
$aliases = @{
    l = 'latest'
    p = 'previous'
    t = 'test'
}
$canonical = @($Games | ForEach-Object {
    if ($aliases.ContainsKey($_)) { $aliases[$_] } else { $_ }
})
if (@($canonical | Where-Object { $_ -notin @(
    'latest', 'previous', 'test', 'na2', 'nun5'
) }).Count -gt 0) {
    throw "Unknown game name: $($Games -join ',')"
}
Write-Output "[fake] multi-game launch $($canonical -join ',')"
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
    [string]$OverlayPlan,
    [switch]$WholeSource
)
Write-Output (
    "[fake] watch $PinePort source=$SourceId entry=$Entry " +
    "sourcePath=$SourcePath plan=$OverlayPlan wholeSource=$($WholeSource.IsPresent)"
)
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeReleaseScripts 'publish_release.ps1') -Content @'
param([string]$Version)
Write-Output "[fake] release $Version"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeNa2Scripts 'build.ps1') -Content @'
param(
    [switch]$TestOnly,
    [switch]$ComposeOnly,
    [string]$WorkerOutputIso
)
if ($WorkerOutputIso) {
    Write-Host '[na228] ISO result: worker; rotation: no; PCSX2 left running.'
    [pscustomobject]@{ Status = 'worker'; ChangedRoles = [string[]]@() }
}
elseif ($TestOnly) {
    Write-Host '[na228] ISO result: test; rotation: no; PCSX2 left running.'
    [pscustomobject]@{ Status = 'test'; ChangedRoles = [string[]]@('test') }
}
elseif ($ComposeOnly) {
    Write-Host '[na228] Profile composition valid; no ISO produced.'
    [pscustomobject]@{ Status = 'validated'; ChangedRoles = [string[]]@() }
}
else {
    Write-Host '[na228] ISO result: updated; rotation: yes.'
    [pscustomobject]@{
        Status = 'updated'
        ChangedRoles = [string[]]@('latest', 'previous')
    }
}
'@
    & (Join-Path $fakeActualizationScripts 'act.ps1')
    & (Join-Path $fakeActualizationScripts 'act.ps1') na228
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
    $actualizationCallLog = Join-Path $fakeRepository 'actualization_calls.txt'
    $launchActualizationCountBefore = @(
        if (Test-Path -LiteralPath $actualizationCallLog) {
            Get-Content -LiteralPath $actualizationCallLog
        }
    ).Count
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
        & (Join-Path $fakeRepository 'na228.ps1') t
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $testLaunch -match 'multi-game launch test'
        ) `
        -Message 'Test selector alias did not resolve through game launch.'
    $launchActualizationCountAfter = @(
        if (Test-Path -LiteralPath $actualizationCallLog) {
            Get-Content -LiteralPath $actualizationCallLog
        }
    ).Count
    Assert-Na2Test `
        -Condition (
            $launchActualizationCountAfter -eq
            $launchActualizationCountBefore
        ) `
        -Message 'Launch-only selectors invoked actualization.'
    & (Join-Path $fakeRepository 'na228.ps1') worker 'work\General\build\agent.iso'
    & (Join-Path $fakeRepository 'na228.ps1') validate
    & (Join-Path $fakeRepository 'na228.ps1') build l
    $latestBuildRoles = Get-Content -LiteralPath $actualizationCallLog -Tail 1
    & (Join-Path $fakeRepository 'na228.ps1') build t
    $testBuildRoles = Get-Content -LiteralPath $actualizationCallLog -Tail 1
    Assert-Na2Test `
        -Condition ($latestBuildRoles -ceq 'latest,previous') `
        -Message 'Latest build did not actualize only its changed roles.'
    Assert-Na2Test `
        -Condition ($testBuildRoles -ceq 'test') `
        -Message 'Test build did not actualize only Test.'
    $composedRecipe = (
        & (Join-Path $fakeRepository 'na228.ps1') nun5 btw
    ) -join "`n"
    Assert-Na2Test `
        -Condition ($composedRecipe -match 'multi-game launch nun5,test') `
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
    $namedBuildWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') blw font nun5
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $namedBuildWatch -match 'multi-game launch latest,nun5' -and
            $namedBuildWatch -match (
                '\[fake\] watch 28014 .*' +
                'plan=scripts/injection/targets/font\.json wholeSource=True'
            )
        ) `
        -Message 'Whole-Font watch target did not preserve launch order or selection.'
    $directPlanWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') `
            nun5 `
            btw `
            'work\Font\operations\jutsu_names_overlay.json'
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $directPlanWatch -match 'multi-game launch nun5,test' -and
            $directPlanWatch -match (
                'plan=work\\Font\\operations\\jutsu_names_overlay\.json'
            )
        ) `
        -Message 'Direct overlay-plan watch target was not forwarded.'
    $standaloneNamedWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') w font
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $standaloneNamedWatch -match (
                '\[fake\] watch 0 .*' +
                'plan=scripts/injection/targets/font\.json wholeSource=True'
            )
        ) `
        -Message 'Standalone whole-Font watch target was not forwarded.'
    $standaloneDefaultWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') w
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $standaloneDefaultWatch -match (
                '\[fake\] watch 0 .*' +
                'plan=scripts/injection/targets/font\.json wholeSource=True'
            )
        ) `
        -Message 'Bare watch command did not select the default whole-Font target.'
    $standaloneInjectionTestWatch = (
        & (Join-Path $fakeRepository 'na228.ps1') w injection_test
    ) -join "`n"
    Assert-Na2Test `
        -Condition (
            $standaloneInjectionTestWatch -match (
                '\[fake\] watch 0 source=hot_reload_message ' +
                'entry=project\.hot_reload_message'
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
        'actualize',
        'actualize-na228',
        'test-build',
        'validate',
        'build'
    )) {
        Assert-Na2Test `
            -Condition ($fakeRolling -match "(?m)^mode: $mode$") `
            -Message "$mode dispatch was not logged."
    }
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, '(?m)^--- NA2 RUN BEGIN ---$').Count -eq 10) `
        -Message 'Root dispatch test produced the wrong rolling-log section count.'
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
        -Condition ([regex]::Matches($fakeRolling, 'ISO result: test').Count -eq 3) `
        -Message 'Test build recipes did not dispatch exactly three times to Test.'
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
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, '\[fake\] actualize na228').Count -eq 9) `
        -Message 'Standalone and user-owned workflows did not preserve NA2 actualization.'
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
        -ProjectPaths $renamedPaths
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
        -ProjectPaths $paths
    $record = Complete-Na2BuildRecord `
        -LogDirectory $structuredLog `
        -BuildId 'new-latest' `
        -Result updated `
        -Rotated $true `
        -LatestIso $paths.files.latest_iso `
        -PreviousIso $paths.files.previous_iso `
        -Profile (Join-Path $paths.builder 'profiles\current') `
        -ProjectPaths $paths
    Assert-Na2Test -Condition ($record.BuildId -eq 'new-latest') -Message 'Updated build was not retained.'
    $updatedBuildMap = Read-Na2BuildMap `
        -LogDirectory $structuredLog `
        -ProjectPaths $paths
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
            "@build/NA2.28 - Previous.iso`t@logs/na228/builds/old-latest`n"
        )) `
        -Message 'builds.tsv does not contain the exact atomic two-ISO mapping.'
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
        -Profile 'na228_builder/profiles/current' `
        -ProjectPaths $paths
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
        -Profile 'na228_builder/profiles/current' `
        -ProjectPaths $paths
    Assert-Na2Test `
        -Condition ($firstUnchanged.BuildId -eq $firstBuildId) `
        -Message 'First unchanged build was incorrectly discarded.'
    $firstBuildMap = Read-Na2BuildMap `
        -LogDirectory $freshStructuredLog `
        -ProjectPaths $paths
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

    $status = Format-Na2ActualizeStatus `
        -Result ([pscustomobject]@{
            Roles = @(
                [pscustomobject]@{
                    Role = 'Latest'
                    Serial = 'SLOP-NA228'
                    CRC = 'C0659AD1'
                }
            )
            CheatAliases = @('alias')
            RemovedCheatSymlinks = @('old-link')
            EnabledCheats = @('Intro skips')
            CreatedGameSettings = @()
            UpdatedGameSettings = @()
            PreservedGameSettings = @('SLOP-NA228_C0659AD1.ini')
            RemovedGameSettings = @('old-settings')
        }) `
        -ProjectPaths $paths
    Assert-Na2Test -Condition ($status -match 'Latest=SLOP-NA228_C0659AD1') -Message 'Actualize status omitted the role identity.'
    Assert-Na2Test -Condition ($status -match 'Intro skips') -Message 'Actualize status omitted enabled cheats.'
    Assert-Na2Test -Condition ($status -match 'GameSettings') -Message 'Actualize status omitted GameSettings.'

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
