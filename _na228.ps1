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
$previousIsoName = [IO.Path]::GetFileName($projectPaths.files.previous_iso)
$candidateIsoName = [IO.Path]::GetFileName($projectPaths.files.candidate_iso)

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
        '  na228 t work/<worker>/build/<name>.iso  Build an isolated worker ISO and worker-owned logs'
        "  na228 c     Run build/$currentIsoName without rebuilding"
        "  na228 p     Run build/$previousIsoName without rebuilding"
        '  na228 w     Watch src/ and hot-reload saved C changes into dev PCSX2'
        '  na228 <recipe>  Run unique b/t/c/p/w steps left-to-right; w must be last (example: na228 bpw)'
        '  na228 <game> [games...]  Launch and tile selected games'
        '  na228 release [version]  Validate, commit, tag, and publish a GitHub release'
        '  na228 help  Show this help'
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

if ($mode -and $mode -cnotmatch '^[btcpw]+$') {
    & $projectPaths.files.na228_game_launch_command @commandTokens
    return
}

$recipe = $mode
if ($recipe) {
    $duplicateStep = $recipe.ToCharArray() |
        Group-Object |
        Where-Object Count -gt 1 |
        Select-Object -First 1
    if ($null -ne $duplicateStep) {
        throw "Compact recipe '$recipe' repeats step '$($duplicateStep.Name)'."
    }
    if ($recipe.Contains('w') -and -not $recipe.EndsWith('w')) {
        throw "Compact recipe '$recipe' must place blocking watcher step 'w' last."
    }
    if ($arguments.Count -gt 0 -and ($recipe -ne 't' -or $arguments.Count -gt 1)) {
        throw 'Only recipe t accepts one worker output path.'
    }
}

$workerBuild = if ($recipe -eq 't' -and $arguments.Count -eq 1) {
    Get-Na2WorkerBuildContext `
        -OutputPath $arguments[0] `
        -ProjectPaths $projectPaths `
        -RequireRelative
}
else {
    $null
}

[string[]]$actionCodes = @(
    if ($recipe) {
        $recipe.ToCharArray() | ForEach-Object { [string]$_ }
    }
    else { 'default' }
)

if ($recipe.Length -gt 1) {
    Write-Na2Stage "Run compact recipe $recipe"
}

foreach ($actionCode in $actionCodes) {
    if ($recipe.Length -gt 1) {
        Write-Na2Stage "Recipe step $actionCode"
    }
    if ($actionCode -eq 'w') {
        & (Join-Path $projectPaths.scripts 'injection\watch.ps1')
        continue
    }

    $runAction = switch ($actionCode) {
        'b' { 'build-only' }
        't' {
            if ($null -ne $workerBuild) { 'worker-build' }
            else { 'candidate-build' }
        }
        'c' { 'current' }
        'p' { 'previous' }
        default { 'build-and-launch' }
    }
    $runArguments = @{ Action = $runAction }
    if ($runAction -eq 'worker-build') {
        $runArguments.WorkerOutputIso = $workerBuild.OutputIso
        $runArguments.WorkerLogDirectory = $workerBuild.Logs
    }
    & (Join-Path $projectPaths.scripts 'na228\run.ps1') @runArguments
}
