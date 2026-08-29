$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
. (Join-Path ([string]$paths.scripts) 'na228\task_paths.ps1')
. (Join-Path ([string]$paths.scripts) 'na228\launch_settings.ps1')
. (Join-Path ([string]$paths.scripts) 'na228\launch_profile.ps1')
. (Join-Path ([string]$paths.scripts) 'na228\build_targets.ps1')
. (Join-Path ([string]$paths.pcsx2_scripts) 'launch_arguments.ps1')

trap {
    if ([bool]$_.Exception.Data['Na2ConfigurationError']) {
        Write-Host "[na228] Build failed: $($_.Exception.Message)" -ForegroundColor Red
        $global:LASTEXITCODE = 1
        return
    }
    break
}

$gameAliases = @(
    $paths.games.Aliases.PSObject.Properties |
        Where-Object { [string]$_.Name -cne [string]$_.Value } |
        ForEach-Object { "$($_.Name)=$($_.Value)" }
)

function Write-Na2Stage {
    param([string]$Message)
    Write-Host "[na228] $Message" -ForegroundColor Cyan
}

function Get-Na228WatchArguments {
    param([string]$Target)

    if ([string]::IsNullOrWhiteSpace($Target)) {
        return @{ SourcePath = 'src' }
    }
    if ($Target -ceq 'injection_test') {
        return @{ SourcePath = 'src/hot_reload_message.c' }
    }
    if ([IO.Path]::GetExtension($Target) -ieq '.json') {
        return @{ OverlayPlan = $Target }
    }
    return @{ SourcePath = $Target }
}

$commandTokens = @($args)
$forceTokens = @($commandTokens | Where-Object { $_ -ieq '-f' })
if ($forceTokens.Count -gt 1) {
    throw '-f may be specified only once.'
}
$forceBuild = $forceTokens.Count -eq 1
$commandTokens = @($commandTokens | Where-Object { $_ -ine '-f' })
$turboTokens = @($commandTokens | Where-Object { $_ -ieq '-t' })
if ($turboTokens.Count -gt 1) {
    throw '-t may be specified only once.'
}
$turbo = $turboTokens.Count -eq 1
$commandTokens = @($commandTokens | Where-Object { $_ -ine '-t' })
$unlimitedTokens = @($commandTokens | Where-Object { $_ -ieq '-u' })
if ($unlimitedTokens.Count -gt 1) {
    throw '-u may be specified only once.'
}
$unlimited = $unlimitedTokens.Count -eq 1
$commandTokens = @($commandTokens | Where-Object { $_ -ine '-u' })
if ($turbo -and $unlimited) {
    throw 'Use only one of -t or -u.'
}
$mode = if ($commandTokens.Count -gt 0) {
    $commandTokens[0].ToLowerInvariant()
}
else {
    ''
}
$arguments = @(
    if ($commandTokens.Count -gt 1) {
        $commandTokens[1..($commandTokens.Count - 1)]
    }
)

if ($mode -eq 'worker') {
    throw 'Use na228 build -c <configuration>.'
}

if (($turbo -or $unlimited) -and $mode -in @(
    'help',
    'test',
    'e2e',
    'release',
    'build',
    'w'
)) {
    throw '-t and -u are valid only when launching one or two games.'
}

if ($mode -eq 'help') {
    if ($arguments.Count -gt 0) {
        throw 'na228 help accepts no arguments.'
    }
    @(
        'NA2.28'
        ''
        '  na228 [-f]                 Build and run Latest with accelerated startup'
        '  na228 w [C path|plan]      Watch all registered C by default'
        '  na228 w injection_test     Watch only the reload-message smoke test'
        '  na228 <token> [token] [-l <profile> [args]]  Run one or two games'
        '  l | p | m                  Latest | Previous | Manual'
        '  bl | bm [-f]               Build and run Latest | Manual'
        '  <token>w [C path|plan]     Watch that game; selection follows its token'
        '  -f                          Bypass non-critical validation errors during an ordinary build'
        '  -l <profile> [args]        Select a configured launch profile and its own arguments'
        '  additional launch arguments  See workshop help'
        ''
        '  na228 build l|m [-f]        Build Latest or Manual without running it'
        '  na228 build -c <configuration>  Build or reuse a cached ISO'
        '  na228 test                  Run unit tests'
        ''
        '  na228 e2e <all|suite [args...] ...>  Run selected suites'
        '  na228 e2e create <all|suite [args...] ...> [-noref]  Rebuild with NUN5 reference by default'
        '  suite args                  Passed to that suite; generated suites accept row or rows: 8 or 8-18'
        '  na228 e2e rename <suite> <new-suite>  Rename a recording-backed suite and its capture history'
        '  na228 e2e delete <all|suite [args...] ...>  Delete capture history'
        '  na228 e2e commit [-p]                  Commit captures; -p preserves capture commits'
        ''
        '  na228 release [version]     Publish a GitHub release'
        '  na228 help                  Show this help'
        ''
        "  games: $($paths.games.Names -join ', ')"
        "  aliases: $($gameAliases -join ', ')"
        ''
    ) | Write-Output
    return
}

if ($mode -eq 'test') {
    if ($forceBuild) {
        throw '-f is valid only for ordinary Latest or Manual builds.'
    }
    if ($arguments.Count -gt 0) {
        throw 'Usage: na228 test'
    }
    $testRun = Join-Path $PSScriptRoot 'tests\run.ps1'
    if (-not (Test-Path -LiteralPath $testRun -PathType Leaf)) {
        throw "The unit-test infrastructure is unavailable: $testRun"
    }
    & $testRun
    return
}

if ($mode -eq 'e2e') {
    if ($forceBuild) {
        throw '-f is valid only for ordinary Latest or Manual builds.'
    }
    $visualScripts = Join-Path $PSScriptRoot 'e2e\scripts'
    $visualRun = Join-Path $visualScripts 'run.ps1'
    $visualCreate = Join-Path $visualScripts 'create_suite.ps1'
    $visualRename = Join-Path $visualScripts 'rename_suite.ps1'
    $visualDelete = Join-Path $visualScripts 'delete_suites.ps1'
    $visualCommit = Join-Path $visualScripts 'commit_captures.ps1'
    foreach ($required in $visualRun, $visualCreate, $visualRename, $visualDelete, $visualCommit) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "The E2E infrastructure is unavailable: $required"
        }
    }

    $runUsage = 'Usage: na228 e2e <all|suite [args...] ...>'
    $createUsage = 'Usage: na228 e2e create <all|suite [args...] ...> [-noref]'
    $deleteUsage = 'Usage: na228 e2e delete <all|suite [args...] ...>'
    if ($arguments.Count -eq 0) {
        throw $runUsage
    }
    $testCommand = $arguments[0].ToLowerInvariant()
    if ($testCommand -cnotin @('create', 'rename', 'delete', 'commit')) {
        $null = & $visualRun -SelectionToken ([string[]]$arguments)
        return
    }
    if ($testCommand -ceq 'create') {
        $noReferenceCount = @($arguments | Where-Object { $_ -ceq '-noref' }).Count
        $createOperands = @(
            $arguments | Select-Object -Skip 1 | Where-Object { $_ -cne '-noref' }
        )
        if ($noReferenceCount -gt 1 -or $createOperands.Count -eq 0) {
            throw $createUsage
        }
        $createArguments = @{
            SelectionToken = [string[]]$createOperands
        }
        if ($noReferenceCount -eq 1) {
            $createArguments.NoReference = $true
        }
        & $visualCreate @createArguments
        return
    }
    if ($testCommand -ceq 'rename') {
        if ($arguments.Count -ne 3) {
            throw 'Usage: na228 e2e rename <suite> <new-suite>'
        }
        & $visualRename -Suite $arguments[1] -NewSuite $arguments[2]
        return
    }
    if ($testCommand -ceq 'delete') {
        $deleteOperands = @($arguments | Select-Object -Skip 1)
        if ($deleteOperands.Count -eq 0 -or
            @($deleteOperands | Where-Object { $_ -in @('-noref', '-p') }).Count -gt 0) {
            throw $deleteUsage
        }
        & $visualDelete -SelectionToken ([string[]]$deleteOperands)
        return
    }
    if ($testCommand -ceq 'commit') {
        if (
            $arguments.Count -notin 1, 2 -or
            ($arguments.Count -eq 2 -and $arguments[1] -cne '-p')
        ) {
            throw 'Usage: na228 e2e commit [-p]'
        }
        & $visualCommit -Preserve:($arguments.Count -eq 2)
        return
    }
    throw "$runUsage | $createUsage | na228 e2e rename <suite> <new-suite> | $deleteUsage | na228 e2e commit [-p]"
}

if ($mode -eq 'release') {
    if ($forceBuild) {
        throw '-f is valid only for ordinary Latest or Manual builds.'
    }
    if ($arguments.Count -gt 1) {
        throw 'na228 release accepts at most one version argument.'
    }
    $releaseArguments = @{}
    if ($arguments.Count -eq 1) {
        $releaseArguments.Version = $arguments[0]
    }
    & $paths.files.publish_release_command @releaseArguments
    return
}

if ($mode -eq 'build') {
    if ($arguments.Count -eq 2 -and $arguments[0] -ceq '-c') {
        if ($forceBuild) {
            throw '-f is valid only for ordinary Latest or Manual builds.'
        }
        $configuration = $arguments[1]
        if ($configuration -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]*$') {
            throw "Invalid configuration ID: $configuration"
        }
        $cacheArguments = @{
            Action = 'cache-build'
            CacheConfiguration = $configuration
        }
        if (-not [string]::IsNullOrWhiteSpace($env:NA228_TASK_WORK_ROOT)) {
            $task = Get-Na2TaskContext `
                -TaskRoot $env:NA228_TASK_WORK_ROOT `
                -Paths $paths
            $cacheArguments.CacheLogDirectory = $task.Logs
        }
        $cacheResult = & (Join-Path $paths.scripts 'na228\run.ps1') @cacheArguments
        if (-not $cacheResult -or $cacheResult.Status -ne 'cache') {
            throw 'Cache build did not return a valid result.'
        }
        Write-Output $cacheResult.OutputIso
        return
    }
    if ($arguments.Count -ne 1) {
        throw 'Usage: na228 build l|m [-f] | na228 build -c <configuration>'
    }
    $target = $arguments[0].ToLowerInvariant()
    switch ($target) {
        { $_ -in @('l', 'latest') } {
            & (Join-Path $paths.scripts 'na228\run.ps1') `
                -Action latest-build `
                -Force:$forceBuild
            return
        }
        { $_ -in @('m', 'manual') } {
            & (Join-Path $paths.scripts 'na228\run.ps1') `
                -Action manual-build `
                -Force:$forceBuild
            return
        }
        default {
            throw 'Usage: na228 build l|m [-f] | na228 build -c <configuration>'
        }
    }
}

if (-not $mode) {
    $runArguments = @{
        Action = 'latest-build-and-launch'
        Force = $forceBuild
    }
    if ($turbo) { $runArguments.Turbo = $true }
    if ($unlimited) { $runArguments.Unlimited = $true }
    & (Join-Path $paths.scripts 'na228\run.ps1') @runArguments
    return
}

if ($mode -eq 'w') {
    if ($forceBuild) {
        throw '-f is valid only for ordinary Latest or Manual builds.'
    }
    if ($arguments.Count -gt 1) {
        throw 'na228 w accepts at most one watch target or overlay-plan path.'
    }
    $watchArguments = Get-Na228WatchArguments `
        -Target $(if ($arguments.Count -eq 1) { $arguments[0] } else { '' })
    & (Join-Path $paths.scripts 'injection\watch.ps1') @watchArguments
    return
}

function Test-Na228GameToken {
    param([Parameter(Mandatory)][string]$Token)

    $candidate = $Token.ToLowerInvariant()
    if ($candidate.Length -gt 1 -and $candidate.EndsWith('w')) {
        $candidate = $candidate.Substring(0, $candidate.Length - 1)
    }
    if ($candidate -in @('b', 'bl', 'bm', 'l', 'p', 'm')) {
        return $true
    }
    return $null -ne $paths.games.Aliases.PSObject.Properties[$candidate]
}

$launchArgumentIndex = 0
while (
    $launchArgumentIndex -lt $commandTokens.Count -and
    -not $commandTokens[$launchArgumentIndex].StartsWith('-')
) {
    $launchArgumentIndex++
}
$runTokens = @(
    if ($launchArgumentIndex -gt 0) {
        $commandTokens[0..($launchArgumentIndex - 1)]
    }
)
$forwardedLaunchArguments = @(
    if ($launchArgumentIndex -lt $commandTokens.Count) {
        $commandTokens[$launchArgumentIndex..($commandTokens.Count - 1)]
    }
)
$games = [Collections.Generic.List[string]]::new()
$buildActions = [Collections.Generic.List[string]]::new()
$watchIndex = $null
$watchTarget = ''
for ($index = 0; $index -lt $runTokens.Count; $index++) {
    $token = $runTokens[$index].ToLowerInvariant()
    $watch = $token.Length -gt 1 -and $token.EndsWith('w')
    if ($watch) {
        if ($null -ne $watchIndex) {
            throw 'Only one game token may request watching.'
        }
        $watchIndex = $games.Count
        $token = $token.Substring(0, $token.Length - 1)
    }
    switch ($token) {
        'b' {
            $games.Add('latest')
            $buildActions.Add('latest-build')
        }
        'bl' {
            $games.Add('latest')
            $buildActions.Add('latest-build')
        }
        'bm' {
            $games.Add('manual')
            $buildActions.Add('manual-build')
        }
        'l' { $games.Add('latest') }
        'p' { $games.Add('previous') }
        'm' { $games.Add('manual') }
        default { $games.Add($token) }
    }
    if (
        $watch -and
        $index + 1 -lt $runTokens.Count -and
        -not (Test-Na228GameToken -Token $runTokens[$index + 1])
    ) {
        $watchTarget = $runTokens[$index + 1]
        $index++
    }
}
if ($games.Count -gt 2) {
    throw 'na228 accepts at most two game tokens.'
}
if ($forceBuild -and $buildActions.Count -eq 0) {
    throw '-f requires an ordinary Latest or Manual build token.'
}

foreach ($buildAction in @($buildActions | Select-Object -Unique)) {
    & (Join-Path $paths.scripts 'na228\run.ps1') `
        -Action $buildAction `
        -Force:$forceBuild
}

$launchParameters = @{
    Games = @($games)
    ProjectRoot = $paths.repository
    InputRecordingsRoot = $paths.pcsx2_input_recordings
}
$workshopLaunchArguments = [Collections.Generic.List[string]]::new()
$launchProfile = $null
$launchProfileArguments = [Collections.Generic.List[string]]::new()
for ($index = 0; $index -lt $forwardedLaunchArguments.Count; $index++) {
    $option = $forwardedLaunchArguments[$index].ToLowerInvariant()
    if ($option -eq '-l') {
        if ($null -ne $launchProfile) {
            throw '-l may be specified only once.'
        }
        if ($index + 1 -ge $forwardedLaunchArguments.Count) {
            throw '-l requires a launch profile.'
        }
        $profileName = $forwardedLaunchArguments[++$index].ToLowerInvariant()
        $launchProfile = Resolve-Na2LaunchProfile `
            -Name $profileName `
            -Paths $paths
        while ($index + 1 -lt $forwardedLaunchArguments.Count) {
            $nextArgument = [string]$forwardedLaunchArguments[$index + 1]
            $nextOption = $nextArgument.ToLowerInvariant()
            if ($nextOption -eq '-l' -or
                (Test-UnWorkshopLaunchOption -Token $nextOption)) {
                break
            }
            $launchProfileArguments.Add(
                [string]$forwardedLaunchArguments[++$index]
            )
        }
        continue
    }
    $workshopLaunchArguments.Add(
        [string]$forwardedLaunchArguments[$index]
    )
}
$workshopLaunch = ConvertFrom-UnWorkshopLaunchArguments `
    -Tokens @($workshopLaunchArguments) `
    -OptionsOnly
foreach ($entry in $workshopLaunch.LaunchParameters.GetEnumerator()) {
    if ($launchParameters.ContainsKey([string]$entry.Key)) {
        throw "Launch parameter '$($entry.Key)' was already selected."
    }
    $launchParameters[[string]$entry.Key] = $entry.Value
}
$selectedLaunchModes = @(
    @('Play', 'Record', 'Snapshots') |
        Where-Object { $launchParameters.ContainsKey($_) }
)
if ($selectedLaunchModes.Count -gt 1) {
    throw 'Use only one of -p, -r, or -s.'
}
if ($null -ne $launchProfile) {
    $profileResults = @(
        Invoke-Na2LaunchProfile `
            -Profile $launchProfile `
            -Arguments @($launchProfileArguments) `
            -Games @($games) `
            -ProjectRoot $paths.repository
    )
    if ($profileResults.Count -gt 1) {
        throw "Launch profile '$($launchProfile.Name)' returned multiple results."
    }
    if ($profileResults.Count -eq 1) {
        Merge-Na2LaunchProfileParameters `
            -Target $launchParameters `
            -Profile $launchProfile `
            -Result $profileResults[0]
    }
}
if ($launchParameters.ContainsKey('Snapshots')) {
    if ($turbo -or $unlimited) {
        throw '-s owns its permanent Unlimited speed mode.'
    }
    $snapshotRecording = [string]$launchParameters.Snapshots
    $launchParameters.Snapshots = $true
    $launchParameters.Play = $snapshotRecording
}
elseif ($unlimited) {
    $launchParameters.Unlimited = $true
}
else {
    $launchConfigurations = @(
        $games | ForEach-Object {
            $alias = $paths.games.Aliases.PSObject.Properties[[string]$_]
            $canonical = if ($null -ne $alias) {
                [string]$alias.Value
            }
            else {
                [string]$_
            }
            $entry = $paths.games.Entries.PSObject.Properties[$canonical]
            if ($null -ne $entry -and
                [string]$entry.Value.Category -ceq 'builds') {
                Get-Na2BuildTargetConfiguration `
                    -Name $canonical `
                    -Paths $paths
            }
        } | Select-Object -Unique
    )
    $launchFrameCounts = @(
        @(
            if ($launchConfigurations.Count -eq 0) {
                Get-Na2StartupFastForwardFrames `
                    -Paths $paths `
                    -LaunchProfile $(
                        if ($null -eq $launchProfile) {
                            $null
                        }
                        else {
                            [string]$launchProfile.Name
                        }
                    )
            }
            else {
                $launchConfigurations | ForEach-Object {
                    Get-Na2StartupFastForwardFrames `
                        -Configuration $_ `
                        -Paths $paths `
                        -LaunchProfile $(
                            if ($null -eq $launchProfile) {
                                $null
                            }
                            else {
                                [string]$launchProfile.Name
                            }
                        )
                }
            }
        ) | Select-Object -Unique
    )
    if ($launchFrameCounts.Count -gt 1) {
        throw (
            'Selected games require different startup fast-forward frame counts: ' +
            ($launchFrameCounts -join ', ')
        )
    }
    if ($launchFrameCounts.Count -eq 1 -and $launchFrameCounts[0] -gt 0) {
        $launchParameters.UnlimitedForFrames = [UInt64]$launchFrameCounts[0]
    }
    if ($turbo) {
        $launchParameters.Turbo = $true
    }
}
$launchResults = @(
    & $paths.files.pcsx2_game_launch_command @launchParameters
)
$launchResults

if ($null -ne $watchIndex) {
    $gameLaunchResults = @(
        $launchResults |
            Where-Object {
                $null -ne $_.PSObject.Properties['Game'] -and
                $null -ne $_.PSObject.Properties['PinePort']
            }
    )
    if ($gameLaunchResults.Count -le $watchIndex) {
        throw "Launch result did not expose the PINE port for game token $($watchIndex + 1)."
    }
    $watchArguments = Get-Na228WatchArguments -Target $watchTarget
    $watchArguments.PinePort = [int]$gameLaunchResults[$watchIndex].PinePort
    & (Join-Path $paths.scripts 'injection\watch.ps1') @watchArguments
}
