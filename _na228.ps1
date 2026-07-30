[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments)]
    [string[]]$Tokens = @()
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'scripts\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'scripts\na228\worker_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$gameAliases = @(
    $projectPaths.games.Aliases.PSObject.Properties |
        Where-Object { [string]$_.Name -cne [string]$_.Value } |
        ForEach-Object { "$($_.Name)=$($_.Value)" }
)

function Write-Na2Stage {
    param([string]$Message)
    Write-Host "[na228] $Message" -ForegroundColor Cyan
}

$commandTokens = @($Tokens)
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
        '  na228 w                    Watch src/ and hot-reload saved C changes'
        '  na228 <token> [token]      Run one or two games in window order'
        '  l | p | t                  Latest | Previous | Test'
        '  bl | bt                    Build and run Latest | Test'
        '  <token>w                   Watch that game'
        ''
        '  na228 build l|t             Build Latest or Test without running it'
        '  na228 validate              Validate the complete build without producing an ISO'
        '  na228 worker work/<worker>/build/<name>.iso  Build an isolated worker ISO'
        '  na228 release [version]     Publish a GitHub release'
        '  na228 help                  Show this help'
        "  games: $($projectPaths.games.Names -join ', ')"
        "  aliases: $($gameAliases -join ', ')"
        ''
    ) | Write-Output
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
    & $projectPaths.files.release_publish_command @releaseArguments
    return
}

if ($mode -eq 'build') {
    if ($arguments.Count -ne 1) {
        throw 'na228 build requires exactly one target: l or t.'
    }
    $target = $arguments[0].ToLowerInvariant()
    switch ($target) {
        { $_ -in @('l', 'latest') } {
            & (Join-Path $projectPaths.scripts 'na228\run.ps1') `
                -Action latest-build
            return
        }
        { $_ -in @('t', 'test') } {
            & (Join-Path $projectPaths.scripts 'na228\run.ps1') `
                -Action test-build
            return
        }
        default {
            throw "na228 build target must be l or t: $target"
        }
    }
}

if ($mode -eq 'validate') {
    if ($arguments.Count -gt 0) {
        throw 'na228 validate accepts no arguments.'
    }
    & (Join-Path $projectPaths.scripts 'na228\run.ps1') -Action validate
    return
}

if ($mode -eq 'worker') {
    if ($arguments.Count -ne 1) {
        throw 'na228 worker requires exactly one worker ISO output path.'
    }
    $workerBuild = Get-Na2WorkerBuildContext `
        -OutputPath $arguments[0] `
        -ProjectPaths $projectPaths `
        -RequireRelative
    & (Join-Path $projectPaths.scripts 'na228\run.ps1') `
        -Action worker-build `
        -WorkerOutputIso $workerBuild.OutputIso `
        -WorkerLogDirectory $workerBuild.Logs
    return
}

if (-not $mode) {
    & (Join-Path $projectPaths.scripts 'na228\run.ps1') `
        -Action latest-build-and-launch
    return
}

if ($mode -eq 'w') {
    if ($arguments.Count -gt 0) {
        throw 'na228 w accepts no arguments.'
    }
    & (Join-Path $projectPaths.scripts 'injection\watch.ps1')
    return
}

$runTokens = @($commandTokens | ForEach-Object { $_.ToLowerInvariant() })
if ($runTokens.Count -gt 2) {
    throw 'na228 accepts at most two game tokens.'
}

$games = [Collections.Generic.List[string]]::new()
$buildActions = [Collections.Generic.List[string]]::new()
$watchIndex = $null
for ($index = 0; $index -lt $runTokens.Count; $index++) {
    $token = $runTokens[$index]
    $watch = $token.Length -gt 1 -and $token.EndsWith('w')
    if ($watch) {
        if ($null -ne $watchIndex) {
            throw 'Only one game token may request watching.'
        }
        $watchIndex = $index
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
        'bt' {
            $games.Add('test')
            $buildActions.Add('test-build')
        }
        'l' { $games.Add('latest') }
        'p' { $games.Add('previous') }
        't' { $games.Add('test') }
        default { $games.Add($token) }
    }
}

foreach ($buildAction in @($buildActions | Select-Object -Unique)) {
    & (Join-Path $projectPaths.scripts 'na228\run.ps1') -Action $buildAction
}

$launchArguments = @{ Games = @($games) }
if ($buildActions.Count -gt 0) {
    $launchArguments.SkipActualization = $true
}
$launchResults = @(
    & $projectPaths.files.na228_game_launch_command @launchArguments
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
    & (Join-Path $projectPaths.scripts 'injection\watch.ps1') `
        -PinePort ([int]$gameLaunchResults[$watchIndex].PinePort)
}
