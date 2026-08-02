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
        '  na228 test [suite] [-b]     Run one or all E2E suites; -b builds once first'
        '  na228 test new <recording>  Create a NUN5 reference suite'
        '  na228 test reference <suite> -f  Regenerate NUN5 reference screenshots'
        '  na228 test approve <suite> -s <slots> | -a'
        '  na228 validate              Validate the complete build without producing an ISO'
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
    $visualRoot = Join-Path $PSScriptRoot 'e2e'
    $visualScripts = Join-Path $visualRoot 'scripts'
    $visualRun = Join-Path $visualScripts 'run.ps1'
    $visualNew = Join-Path $visualScripts 'new_suite.ps1'
    $visualReference = Join-Path $visualScripts 'reference.ps1'
    $visualApprove = Join-Path $visualScripts 'approve.ps1'
    foreach ($required in $visualRun, $visualNew, $visualReference, $visualApprove) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw (
                'The E2E infrastructure is unavailable. ' +
                "Expected: $visualRoot"
            )
        }
    }

    $testCommand = if ($arguments.Count -gt 0) {
        $arguments[0].ToLowerInvariant()
    }
    else {
        'run'
    }
    if ($testCommand -eq 'new') {
        if ($arguments.Count -ne 2) {
            throw 'Usage: na228 test new <recording>'
        }
        & $visualNew -Recording $arguments[1]
        return
    }
    if ($testCommand -eq 'approve') {
        if ($arguments.Count -lt 3) {
            throw 'Usage: na228 test approve <suite> -s <slots> | -a'
        }
        $suite = $arguments[1]
        $selector = $arguments[2]
        if ($selector -ceq '-a' -and $arguments.Count -eq 3) {
            & $visualApprove -Suite $suite -All
            return
        }
        if ($selector -ceq '-s' -and $arguments.Count -eq 4) {
            & $visualApprove -Suite $suite -Slots $arguments[3]
            return
        }
        throw 'Usage: na228 test approve <suite> -s <slots> | -a'
    }
    if ($testCommand -eq 'reference') {
        if ($arguments.Count -ne 3 -or $arguments[2] -cne '-f') {
            throw 'Usage: na228 test reference <suite> -f'
        }
        & $visualReference -Suite $arguments[1] -f
        return
    }

    $runArguments = @(
        if ($testCommand -eq 'run') {
            if ($arguments.Count -gt 1) { $arguments[1..($arguments.Count - 1)] }
        }
        else {
            $arguments
        }
    )
    $buildFirst = $false
    $suite = $null
    foreach ($argument in $runArguments) {
        if ($argument -ceq '-b') {
            if ($buildFirst) { throw 'na228 test accepts -b only once.' }
            $buildFirst = $true
        }
        elseif ($argument.StartsWith('-')) {
            throw "Unknown na228 test option: $argument"
        }
        elseif ($null -eq $suite) {
            $suite = $argument
        }
        else {
            throw 'Usage: na228 test [run] [suite] [-b]'
        }
    }

    $suiteRoot = Join-Path $visualRoot 'suites'
    $suites = if ($null -ne $suite) {
        $selected = Join-Path $suiteRoot $suite
        if (-not (Test-Path -LiteralPath $selected -PathType Container)) {
            throw "Unknown E2E suite: $suite"
        }
        @($suite)
    }
    else {
        @(
            Get-ChildItem -LiteralPath $suiteRoot -Directory -ErrorAction SilentlyContinue |
                Sort-Object Name |
                ForEach-Object Name
        )
    }
    $suites = @($suites)
    if ($suites.Count -eq 0) {
        throw 'No E2E suites are available.'
    }

    $reviewRequired = $false
    for ($index = 0; $index -lt $suites.Count; $index++) {
        $runOutput = @(
            & $visualRun `
                -Suite $suites[$index] `
                -b:($buildFirst -and $index -eq 0)
        )
        $result = @(
            $runOutput | Where-Object {
                $_.PSObject.Properties.Name -contains 'Status' -and
                $_.Status -in @('clean', 'review-required')
            }
        ) | Select-Object -Last 1
        if ($null -eq $result -or $result.Status -notin @('clean', 'review-required')) {
            throw "E2E suite returned no valid result: $($suites[$index])"
        }
        if ($result.Status -eq 'review-required') {
            $reviewRequired = $true
        }
    }
    if ($reviewRequired) {
        Write-Host 'E2E tests completed; review is required.' -ForegroundColor Yellow
        exit 2
    }
    Write-Host 'E2E tests clean.' -ForegroundColor Green
    return
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

if ($mode -eq 'validate') {
    if ($arguments.Count -gt 0) {
        throw 'na228 validate accepts no arguments.'
    }
    & (Join-Path $paths.scripts 'na228\run.ps1') -Action validate
    return
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
