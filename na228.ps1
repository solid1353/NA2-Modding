$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'scripts\lib\paths.ps1')
. (Join-Path $PSScriptRoot 'scripts\na228\worker_paths.ps1')
$paths = Get-Na2Paths
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

if ($mode -eq 'help') {
    if ($arguments.Count -gt 0) {
        throw 'na228 help accepts no arguments.'
    }
    @(
        'NA2.28'
        ''
        '  na228                      Build and run Latest'
        '  na228 w [C path|plan]      Watch all registered C by default'
        '  na228 w injection_test     Watch only the reload-message smoke test'
        '  na228 <token> [token]      Run one or two games in window order'
        '  l | p | mt                 Latest | Previous | Manual Test'
        '  bl | bmt                   Build and run Latest | Manual Test'
        '  <token>w [C path|plan]     Watch that game; selection follows its token'
        '  additional launch arguments  See workshop help'
        ''
        '  na228 build l|mt            Build Latest or Manual Test without running it'
        '  na228 test                              Run unit tests; prepare and validate normal/padded E2E Test ISOs; replay and compare all E2E suites and update captures'
        '  na228 test new <suite> <recording>      Create an E2E suite from a shared recording'
        '  na228 test reference <suite> <game>     Create or replace reference captures'
        '  na228 worker work/<worker>/build/<name>.iso  Build an isolated worker ISO'
        '  na228 release [version]     Publish a GitHub release'
        '  na228 help                  Show this help'
        "  games: $($paths.games.Names -join ', ')"
        "  aliases: $($gameAliases -join ', ')"
        ''
    ) | Write-Output
    return
}

if ($mode -eq 'test') {
    $visualScripts = Join-Path $PSScriptRoot 'e2e\scripts'
    $visualRun = Join-Path $visualScripts 'run.ps1'
    $visualNew = Join-Path $visualScripts 'new_suite.ps1'
    $visualReference = Join-Path $visualScripts 'reference.ps1'
    foreach ($required in $visualRun, $visualNew, $visualReference) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "The E2E infrastructure is unavailable: $required"
        }
    }

    if ($arguments.Count -eq 0) {
        & $visualRun
        return
    }
    $testCommand = $arguments[0].ToLowerInvariant()
    if ($testCommand -ceq 'new') {
        if ($arguments.Count -ne 3) {
            throw 'Usage: na228 test new <suite> <recording>'
        }
        & $visualNew -Suite $arguments[1] -Recording $arguments[2]
        return
    }
    if ($testCommand -ceq 'reference') {
        if ($arguments.Count -ne 3) {
            throw 'Usage: na228 test reference <suite> <game>'
        }
        & $visualReference -Suite $arguments[1] -Game $arguments[2]
        return
    }
    throw 'Usage: na228 test | na228 test new <suite> <recording> | na228 test reference <suite> <game>'
}

if ($mode -eq 'release') {
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
        throw 'na228 build requires exactly one target: l or mt.'
    }
    $target = $arguments[0].ToLowerInvariant()
    switch ($target) {
        { $_ -in @('l', 'latest') } {
            & (Join-Path $paths.scripts 'na228\run.ps1') `
                -Action latest-build
            return
        }
        { $_ -in @('mt', 'manual_test') } {
            & (Join-Path $paths.scripts 'na228\run.ps1') `
                -Action manual-test-build
            return
        }
        default {
            throw "na228 build target must be l or mt: $target"
        }
    }
}

if ($mode -eq 'worker') {
    if ($arguments.Count -ne 1) {
        throw 'na228 worker requires exactly one worker ISO output path.'
    }
    $workerBuild = Get-Na2WorkerBuildContext `
        -OutputPath $arguments[0] `
        -Paths $paths `
        -RequireRelative
    & (Join-Path $paths.scripts 'na228\run.ps1') `
        -Action worker-build `
        -WorkerOutputIso $workerBuild.OutputIso `
        -WorkerLogDirectory $workerBuild.Logs
    return
}

if (-not $mode) {
    & (Join-Path $paths.scripts 'na228\run.ps1') `
        -Action latest-build-and-launch
    return
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

function Test-Na228GameToken {
    param([Parameter(Mandatory)][string]$Token)

    $candidate = $Token.ToLowerInvariant()
    if ($candidate.Length -gt 1 -and $candidate.EndsWith('w')) {
        $candidate = $candidate.Substring(0, $candidate.Length - 1)
    }
    if ($candidate -in @('b', 'bl', 'bmt', 'l', 'p', 'mt')) {
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
        'bmt' {
            $games.Add('manual_test')
            $buildActions.Add('manual-test-build')
        }
        'l' { $games.Add('latest') }
        'p' { $games.Add('previous') }
        'mt' { $games.Add('manual_test') }
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

foreach ($buildAction in @($buildActions | Select-Object -Unique)) {
    & (Join-Path $paths.scripts 'na228\run.ps1') -Action $buildAction
}

$workshopArguments = @($games) + $forwardedLaunchArguments
$launchResults = @(
    & $paths.files.workshop_command @workshopArguments
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
