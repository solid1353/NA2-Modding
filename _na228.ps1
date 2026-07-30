[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments)]
    [string[]]$Tokens = @()
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'scripts\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'scripts\na228\worker_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$currentIsoName = [IO.Path]::GetFileName($projectPaths.files.current_iso)
$candidateIsoName = [IO.Path]::GetFileName($projectPaths.files.candidate_iso)
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
        "  na228       Build the pinned current profile, conditionally rotate, then run $currentIsoName"
        "  na228 b     Build and conditionally rotate $currentIsoName without launching PCSX2"
        "  na228 t     Build build/$candidateIsoName without changing Current/Previous"
        '  na228 validate  Compose and conflict-check the pinned profile without producing an ISO'
        '  na228 w     Watch src/ and hot-reload saved C changes into dev PCSX2'
        '  na228 <recipe> [games...]  Compose b or t, game launch, and optional final w'
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
        -Action build-and-launch
    return
}

$recipe = if ($mode -cmatch '^[btw]+$') { $mode } else { '' }
if ($recipe) {
    $duplicateStep = $recipe.ToCharArray() |
        Group-Object |
        Where-Object Count -gt 1 |
        Select-Object -First 1
    if ($null -ne $duplicateStep) {
        throw "Recipe '$recipe' repeats step '$($duplicateStep.Name)'."
    }
    if ($recipe.Contains('b') -and $recipe.Contains('t')) {
        throw "Recipe '$recipe' cannot combine Current and Candidate builds."
    }
    if ($recipe.Contains('w') -and -not $recipe.EndsWith('w')) {
        throw "Recipe '$recipe' must place blocking watcher step 'w' last."
    }
}
$gameTokens = @(
    if ($recipe) { $arguments } else { $commandTokens }
)

if (-not $recipe) {
    & $projectPaths.files.na228_game_launch_command @gameTokens
    return
}

if ($recipe.Length -gt 1) {
    Write-Na2Stage "Run recipe $recipe"
}

$built = $false
if ($recipe.Contains('b')) {
    & (Join-Path $projectPaths.scripts 'na228\run.ps1') -Action build-only
    $built = $true
}
elseif ($recipe.Contains('t')) {
    & (Join-Path $projectPaths.scripts 'na228\run.ps1') -Action candidate-build
    $built = $true
}

if ($gameTokens.Count -gt 0) {
    $launchArguments = @{ Games = $gameTokens }
    if ($built) {
        $launchArguments.SkipActualization = $true
    }
    & $projectPaths.files.na228_game_launch_command @launchArguments
}

if ($recipe.EndsWith('w')) {
    & (Join-Path $projectPaths.scripts 'injection\watch.ps1')
}
