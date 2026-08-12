$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'scripts\lib\paths.ps1')
. (Join-Path $PSScriptRoot 'scripts\na228\worker_paths.ps1')
$paths = Get-Na2Paths

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

if (($turbo -or $unlimited) -and $mode -in @(
    'help',
    'test',
    'e2e',
    'release',
    'build',
    'worker',
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
        '  na228 [-f] [-t|-u]         Build and run Latest with accelerated startup'
        '  na228 w [C path|plan]      Watch all registered C by default'
        '  na228 w injection_test     Watch only the reload-message smoke test'
        '  na228 <token> [token] [-t|-u]  Run one or two games with accelerated startup'
        '  l | p | m                  Latest | Previous | Manual'
        '  bl | bm [-f]               Build and run Latest | Manual'
        '  <token>w [C path|plan]     Watch that game; selection follows its token'
        '  -t                          Continue in Turbo after startup acceleration'
        '  -u                          Launch in Unlimited'
        '  -f                          Bypass non-critical validation errors during an ordinary build'
        '  additional launch arguments  See workshop help'
        ''
        '  na228 build l|m [-f]        Build Latest or Manual without running it'
        '  na228 build -d              Validate development composition without creating an ISO'
        '  na228 test                  Run unit tests'
        '  na228 e2e [-s]              Run all E2E suites; -s also qualifies against shifted'
        '  na228 e2e create <suite> [game]       Create or replace a suite from its matching shared recording; optionally capture a reference game'
        '  na228 e2e rename <suite> <new-suite>  Rename a suite and its capture history'
        '  na228 e2e delete <suite>               Delete a suite and its capture history'
        '  na228 e2e commit [-s]                  Commit captures; -s consolidates and compacts history'
        '  na228 worker [--ephemeral] work/<worker>/build/<name>.iso  Build a worker ISO; ephemeral verifies its hash without writing it'
        '  na228 release [version]     Publish a GitHub release'
        '  na228 help                  Show this help'
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
    $visualDelete = Join-Path $visualScripts 'delete_suite.ps1'
    $visualCommit = Join-Path $visualScripts 'commit_captures.ps1'
    foreach ($required in $visualRun, $visualCreate, $visualRename, $visualDelete, $visualCommit) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "The E2E infrastructure is unavailable: $required"
        }
    }

    if ($arguments.Count -eq 0) {
        & $visualRun
        return
    }
    if ($arguments.Count -eq 1 -and $arguments[0] -ceq '-s') {
        & $visualRun -Shifted
        return
    }
    $testCommand = $arguments[0].ToLowerInvariant()
    if (
        $testCommand -cne 'commit' -and
        @($arguments | Where-Object { $_ -ceq '-s' }).Count -gt 0
    ) {
        throw 'Usage: na228 e2e [-s]'
    }
    if ($testCommand -ceq 'create') {
        if ($arguments.Count -notin 2, 3) {
            throw 'Usage: na228 e2e create <suite> [game]'
        }
        $createArguments = @{
            Suite = $arguments[1]
        }
        if ($arguments.Count -eq 3) {
            $createArguments.Game = $arguments[2]
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
        if ($arguments.Count -ne 2) {
            throw 'Usage: na228 e2e delete <suite>'
        }
        & $visualDelete -Suite $arguments[1]
        return
    }
    if ($testCommand -ceq 'commit') {
        if (
            $arguments.Count -notin 1, 2 -or
            ($arguments.Count -eq 2 -and $arguments[1] -cne '-s')
        ) {
            throw 'Usage: na228 e2e commit [-s]'
        }
        & $visualCommit -Squash:($arguments.Count -eq 2)
        return
    }
    throw 'Usage: na228 e2e [-s] | na228 e2e create <suite> [game] | na228 e2e rename <suite> <new-suite> | na228 e2e delete <suite> | na228 e2e commit [-s]'
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
    & $paths.files.release_publish_command @releaseArguments
    return
}

if ($mode -eq 'build') {
    if ($arguments.Count -ne 1) {
        throw 'na228 build requires exactly one target: l, m, or -d.'
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
        '-d' {
            if ($forceBuild) {
                throw '-f cannot be used with build -d.'
            }
            & (Join-Path $paths.scripts 'na228\build.ps1') -DryRun
            return
        }
        default {
            throw "na228 build target must be l, m, or -d: $target"
        }
    }
}

if ($mode -eq 'worker') {
    if ($forceBuild) {
        throw '-f is valid only for ordinary Latest or Manual builds.'
    }
    $workerEphemeral = $false
    $workerOutputArgument = $null
    if ($arguments.Count -eq 1) {
        $workerOutputArgument = $arguments[0]
    }
    elseif ($arguments.Count -eq 2 -and $arguments[0] -ieq '--ephemeral') {
        $workerEphemeral = $true
        $workerOutputArgument = $arguments[1]
    }
    else {
        throw 'Usage: na228 worker [--ephemeral] work/<worker>/build/<name>.iso'
    }
    $workerBuild = Get-Na2WorkerBuildContext `
        -OutputPath $workerOutputArgument `
        -Paths $paths `
        -RequireRelative
    & (Join-Path $paths.scripts 'na228\run.ps1') `
        -Action worker-build `
        -WorkerOutputIso $workerBuild.OutputIso `
        -WorkerLogDirectory $workerBuild.Logs `
        -WorkerEphemeral:$workerEphemeral
    return
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
}
$valuedLaunchOptions = @{
    '-p' = 'Play'
    '-r' = 'Record'
    '-s' = 'Snapshots'
    '-mc' = 'MemoryCard'
}
for ($index = 0; $index -lt $forwardedLaunchArguments.Count; $index++) {
    $option = $forwardedLaunchArguments[$index].ToLowerInvariant()
    if ($option -eq '-dw') {
        if ($launchParameters.ContainsKey('DiscardMemoryCardWrites')) {
            throw '-dw may be specified only once.'
        }
        $launchParameters.DiscardMemoryCardWrites = $true
        continue
    }
    if (-not $valuedLaunchOptions.ContainsKey($option)) {
        throw "Unknown Workshop launch option: $($forwardedLaunchArguments[$index])"
    }
    if ($index + 1 -ge $forwardedLaunchArguments.Count) {
        throw "$($forwardedLaunchArguments[$index]) requires a value."
    }
    $index++
    $parameterName = $valuedLaunchOptions[$option]
    if ($launchParameters.ContainsKey($parameterName)) {
        throw "$option may be specified only once."
    }
    $launchParameters[$parameterName] = $forwardedLaunchArguments[$index]
}
$selectedLaunchModes = @(
    @('Play', 'Record', 'Snapshots') |
        Where-Object { $launchParameters.ContainsKey($_) }
)
if ($selectedLaunchModes.Count -gt 1) {
    throw 'Use only one of -p, -r, or -s.'
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
    $launchParameters.UnlimitedForFrames = [UInt64](
        $paths.settings.startup_fast_forward_frames
    )
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
