[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments)]
    [string[]]$Tokens = @()
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'scripts\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'scripts\na228\worker_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$latestIsoName = [IO.Path]::GetFileName($projectPaths.files.latest_iso)
$testIsoName = [IO.Path]::GetFileName($projectPaths.files.test_iso)
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
        'NA2.28 commands:'
        "  na228       Build and run $latestIsoName"
        '  na228 l|p|t [games...]  Run Latest, Previous, or Test with optional comparisons'
        "  na228 bl [games...]  Build and run $latestIsoName with optional comparisons"
        "  na228 bt [games...]  Build and run $testIsoName with optional comparisons"
        '  na228 <recipe>w [games...]  Run a compact recipe, then watch src/'
        '  na228 build l|t  Build Latest or Test without running it'
        '  na228 validate  Compose and conflict-check the pinned profile without producing an ISO'
        '  na228 w     Watch src/ and hot-reload saved C changes into dev PCSX2'
        '  na228 <game> [games...]  Launch and tile selected games'
        '  na228 worker work/<worker>/build/<name>.iso  Build an isolated worker ISO'
        '  na228 release [version]  Validate, commit, tag, and publish a GitHub release'
        '  na228 help  Show this help'
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
        throw 'na228 w accepts no game arguments; put w at the end of a run recipe.'
    }
    & (Join-Path $projectPaths.scripts 'injection\watch.ps1')
    return
}

$recipeMode = switch -Regex ($mode) {
    '^b$' { 'bl'; break }
    '^bw$' { 'blw'; break }
    '^(?:b?[lt]|p)w?$' { $mode; break }
    default { '' }
}
if (-not $recipeMode) {
    & $projectPaths.files.na228_game_launch_command @commandTokens
    return
}

$watch = $recipeMode.EndsWith('w')
$coreRecipe = if ($watch) {
    $recipeMode.Substring(0, $recipeMode.Length - 1)
}
else {
    $recipeMode
}
$build = $coreRecipe.StartsWith('b')
$targetAlias = if ($build) { $coreRecipe.Substring(1) } else { $coreRecipe }
$target = switch ($targetAlias) {
    'l' { 'latest' }
    'p' { 'previous' }
    't' { 'test' }
    default { throw "Invalid NA2.28 recipe target: $targetAlias" }
}

if ($build) {
    $buildAction = if ($target -eq 'latest') {
        'latest-build'
    }
    else {
        'test-build'
    }
    & (Join-Path $projectPaths.scripts 'na228\run.ps1') -Action $buildAction
}

$gameTokens = @($target) + @($arguments)
$launchArguments = @{ Games = $gameTokens }
if ($build) {
    $launchArguments.SkipActualization = $true
}
$launchResults = @(
    & $projectPaths.files.na228_game_launch_command @launchArguments
)
$launchResults

if ($watch) {
    $primaryLaunch = @(
        $launchResults |
            Where-Object {
                $null -ne $_.PSObject.Properties['Game'] -and
                [string]$_.Game -ceq $target
            }
    )
    if ($primaryLaunch.Count -ne 1 -or
        $null -eq $primaryLaunch[0].PSObject.Properties['PinePort']) {
        throw "Launch result did not expose the PINE port for primary target '$target'."
    }
    & (Join-Path $projectPaths.scripts 'injection\watch.ps1') `
        -PinePort ([int]$primaryLaunch[0].PinePort)
}
