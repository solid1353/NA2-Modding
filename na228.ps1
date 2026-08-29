$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
. (Join-Path ([string]$paths.scripts) 'na228\task_paths.ps1')
. (Join-Path ([string]$paths.scripts) 'na228\launch_settings.ps1')
. (Join-Path ([string]$paths.scripts) 'na228\launch_profile.ps1')
. (Join-Path ([string]$paths.scripts) 'na228\build_configurations.ps1')
. (Join-Path ([string]$paths.scripts) 'na228\build_registry.ps1')
. (Join-Path ([string]$paths.pcsx2_scripts) 'launch_arguments.ps1')
$buildConfigurations = Get-Na2BuildConfigurations -Paths $paths

trap {
    if ([bool]$_.Exception.Data['Na2ConfigurationError']) {
        Write-Host "[na228] Build failed: $($_.Exception.Message)" -ForegroundColor Red
        $global:LASTEXITCODE = 1
        return
    }
    break
}

$configurationSelectors = @(
    foreach ($selector in $buildConfigurations.BySelector.Keys) {
        $name = [string]$buildConfigurations.BySelector[$selector]
        if ([string]$selector -ceq $name) {
            $name
        }
        else {
            "$selector=$name"
        }
    }
)

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

function Get-Na228ConfigurationSelection {
    param([Parameter(Mandatory)][string]$Token)

    $candidate = $Token.Trim().ToLowerInvariant()
    $configurationName = $buildConfigurations.BySelector[$candidate]
    if ($null -ne $configurationName) {
        return [pscustomobject]@{
            Configuration = [string]$configurationName
            Build = $false
            Watch = $false
        }
    }

    $watch = $candidate.Length -gt 1 -and $candidate.EndsWith('w')
    if ($watch) {
        $candidate = $candidate.Substring(0, $candidate.Length - 1)
        $configurationName = $buildConfigurations.BySelector[$candidate]
        if ($null -ne $configurationName) {
            return [pscustomobject]@{
                Configuration = [string]$configurationName
                Build = $false
                Watch = $true
            }
        }
    }

    if ($candidate.Length -gt 1 -and $candidate.StartsWith('b')) {
        $candidate = $candidate.Substring(1)
        $configurationName = $buildConfigurations.BySelector[$candidate]
        if ($null -ne $configurationName) {
            return [pscustomobject]@{
                Configuration = [string]$configurationName
                Build = $true
                Watch = $watch
            }
        }
    }
    return $null
}

function Test-Na228GameToken {
    param([Parameter(Mandatory)][string]$Token)

    if ($null -ne (Get-Na228ConfigurationSelection -Token $Token)) {
        return $true
    }
    $candidate = $Token.ToLowerInvariant()
    if ($candidate.Length -gt 1 -and $candidate.EndsWith('w')) {
        $candidate = $candidate.Substring(0, $candidate.Length - 1)
    }
    return $null -ne $paths.games.Aliases.PSObject.Properties[$candidate]
}

$commandTokens = @($args)
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
    throw 'Use na228 build <configuration>.'
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
        '  na228                     Build or reuse base configuration, then launch it'
        '  na228 <token> [token]     Launch one or two games through Workshop'
        '                            token: <source>[w] | [b]<config>[w]'
        '                            b = build or reuse before launch; w [C path|plan] = watch'
        '  -l <profile> [args]       Select a configured launch profile and its own arguments'
        '  other launch arguments    See Workshop help'
        ''
        '  na228 build <config>      Build or reuse a configuration without launching'
        '  na228 test                Run unit tests'
        ''
        '  na228 e2e <all|suite [args...] ...>                  Run selected suites'
        '  na228 e2e create <all|suite [args...] ...> [-noref]  Rebuild with NUN5 reference by default'
        '  na228 e2e delete <all|suite [args...] ...>           Delete capture history'
        '  suite args                                           Passed to that suite; generated suites accept row or rows: 8 or 8-18'
        '  na228 e2e rename <suite> <new-suite>                 Rename a recording-backed suite and its capture history'
        '  na228 e2e commit [-p]                                Commit captures; -p preserves capture commits'
        ''
        '  na228 release [version]   Publish a GitHub release'
        '  na228 help                Show this help'
        ''
        "  sources: $($paths.games.Names -join ', ')"
        "  configurations: $($configurationSelectors -join ', ')"
        ''
    ) | Write-Output
    return
}

if ($mode -eq 'test') {
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
    if ($arguments.Count -ne 1) {
        throw 'Usage: na228 build <config>'
    }
    $configuration = Resolve-Na2BuildConfiguration `
        -Selector $arguments[0] -Configurations $buildConfigurations
    $runArguments = @{
        Action = 'configuration-build'
        Configuration = [string]$configuration.Name
    }
    if (-not [string]::IsNullOrWhiteSpace($env:NA228_TASK_WORK_ROOT)) {
        $task = Get-Na2TaskContext -TaskRoot $env:NA228_TASK_WORK_ROOT -Paths $paths
        $runArguments.LogDirectory = $task.Logs
    }
    $result = & (Join-Path $paths.scripts 'na228\run.ps1') @runArguments
    Write-Output $result.OutputIso
    return
}

if (-not $mode) {
    $mode = 'bb'
    $commandTokens = @('bb')
}

if ($mode -eq 'w') {
    if ($arguments.Count -gt 1) {
        throw 'na228 w accepts at most one watch target or overlay-plan path.'
    }
    $watchArguments = Get-Na228WatchArguments `
        -Target $(if ($arguments.Count -eq 1) { $arguments[0] } else { '' })
    & (Join-Path $paths.scripts 'injection\watch.ps1') @watchArguments
    return
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
$gameSelections = [Collections.Generic.List[object]]::new()
$watchIndex = $null
$watchTarget = ''
for ($index = 0; $index -lt $runTokens.Count; $index++) {
    $token = $runTokens[$index].ToLowerInvariant()
    $configurationSelection = Get-Na228ConfigurationSelection -Token $token
    $watch = if ($null -ne $configurationSelection) {
        [bool]$configurationSelection.Watch
    }
    else {
        $token.Length -gt 1 -and $token.EndsWith('w')
    }
    if ($watch) {
        if ($null -ne $watchIndex) {
            throw 'Only one game token may request watching.'
        }
        $watchIndex = $gameSelections.Count
        if ($null -eq $configurationSelection) {
            $token = $token.Substring(0, $token.Length - 1)
        }
    }
    $gameSelections.Add([pscustomobject]@{
        Token = $token
        Configuration = if ($null -ne $configurationSelection) {
            [string]$configurationSelection.Configuration
        }
        else { '' }
        Build = $null -ne $configurationSelection -and
            [bool]$configurationSelection.Build
    })
    if (
        $watch -and
        $index + 1 -lt $runTokens.Count -and
        -not (Test-Na228GameToken -Token $runTokens[$index + 1])
    ) {
        $watchTarget = $runTokens[$index + 1]
        $index++
    }
}
if ($gameSelections.Count -gt 2) {
    throw 'na228 accepts at most two game tokens.'
}
$games = [Collections.Generic.List[string]]::new()
$launchConfigurations = [Collections.Generic.List[string]]::new()
foreach ($selection in $gameSelections) {
    if ([string]::IsNullOrWhiteSpace([string]$selection.Configuration)) {
        $games.Add([string]$selection.Token)
        continue
    }
    $configuration = [string]$selection.Configuration
    $image = if ([bool]$selection.Build) {
        $runArguments = @{
            Action = 'configuration-build'
            Configuration = $configuration
        }
        if (-not [string]::IsNullOrWhiteSpace($env:NA228_TASK_WORK_ROOT)) {
            $task = Get-Na2TaskContext `
                -TaskRoot $env:NA228_TASK_WORK_ROOT -Paths $paths
            $runArguments.LogDirectory = $task.Logs
        }
        $buildResult = & (Join-Path $paths.scripts 'na228\run.ps1') @runArguments
        [string]$buildResult.OutputIso
    }
    else {
        [string](Resolve-Na2CachedBuild `
            -Configuration $configuration -Paths $paths).image
    }
    $games.Add($image)
    $launchConfigurations.Add($configuration)
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
    $launchFrameCounts = @(
        @(
            if ($launchConfigurations.Count -eq 0) {
                Get-Na2StartupFastForwardFrames `
                    -Paths $paths `
                    -LaunchProfile $(
                        if ($null -eq $launchProfile) { $null }
                        else { [string]$launchProfile.Name }
                    )
            }
            else {
                $launchConfigurations | Select-Object -Unique | ForEach-Object {
                    Get-Na2StartupFastForwardFrames `
                        -Configuration $_ `
                        -Paths $paths `
                        -LaunchProfile $(
                            if ($null -eq $launchProfile) { $null }
                            else { [string]$launchProfile.Name }
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
