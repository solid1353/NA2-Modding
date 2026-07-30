[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Mode,

    [Parameter(Position = 1)]
    [string]$Version,

    [Alias('b')]
    [switch]$Build,
    [Alias('t')]
    [switch]$Test,
    [Alias('c')]
    [switch]$Current,
    [Alias('p')]
    [switch]$Previous,
    [Alias('w')]
    [switch]$Watch,
    [Alias('h')]
    [switch]$Help
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

$workerBuild = if ($Test -and -not [string]::IsNullOrWhiteSpace($Mode)) {
    Get-Na2WorkerBuildContext `
        -OutputPath $Mode `
        -ProjectPaths $projectPaths `
        -RequireRelative
}
else {
    $null
}
$compactRecipe = if (
    $Mode -and
    -not $Test -and
    $Mode -cmatch '^[bBtTcCpPwW]+$'
) {
    $Mode.ToLowerInvariant()
}
else {
    ''
}
$command = if ($Mode -and -not $Test -and -not $compactRecipe) {
    $Mode.ToLowerInvariant()
}
else {
    ''
}
$runSelected = $Current -or $Previous

if (@($Build, $Test, $Current, $Previous, $Watch).Where({ $_ }).Count -gt 1) {
    throw '-Build / -b, -Test / -t, -Current / -c, -Previous / -p, and -Watch / -w are mutually exclusive.'
}
if ($compactRecipe -and ($Build -or $Test -or $runSelected -or $Watch -or $Help)) {
    throw 'A compact recipe cannot be combined with build/launch/help switches.'
}
if ($command -and ($Build -or $Test -or $runSelected -or $Watch)) {
    throw 'Build/launch switches cannot be combined with a command mode.'
}
if ($command -and $command -ne 'release') {
    throw "Unknown NA2.28 builder command: $Mode"
}
if ($Version -and $command -ne 'release') {
    throw 'A version argument is accepted only by na228 release.'
}
if ($compactRecipe) {
    $duplicateStep = $compactRecipe.ToCharArray() |
        Group-Object |
        Where-Object Count -gt 1 |
        Select-Object -First 1
    if ($null -ne $duplicateStep) {
        throw "Compact recipe '$compactRecipe' repeats step '$($duplicateStep.Name)'."
    }
    if ($compactRecipe.Contains('w') -and -not $compactRecipe.EndsWith('w')) {
        throw "Compact recipe '$compactRecipe' must place blocking watcher step 'w' last."
    }
}
if ($Help) {
    @(
        'NA2.28 builder commands:'
        "  na228       Build the pinned current profile, conditionally rotate, then run $currentIsoName"
        "  na228 -b    Build and conditionally rotate $currentIsoName without launching PCSX2"
        "  na228 -t    Build build/$candidateIsoName without changing Current/Previous"
        '  na228 -t work/<worker>/build/<name>.iso  Build an isolated worker ISO and worker-owned logs'
        "  na228 -c    Run build/$currentIsoName without rebuilding"
        "  na228 -p    Run build/$previousIsoName without rebuilding"
        '  na228 -w    Watch src/ and hot-reload saved C changes into dev PCSX2'
        '  na228 <recipe>  Run unique b/t/c/p/w steps left-to-right; w must be last (example: na228 bpw)'
        '  na228 release [version]  Validate, commit, tag, and publish a GitHub release'
        ''
    ) | Write-Output
    return
}

if ($command -eq 'release') {
    $releaseArguments = @{}
    if ($Version) {
        $releaseArguments.Version = $Version
    }
    & $projectPaths.files.release_publish_command @releaseArguments
    return
}

if ($compactRecipe) {
    Write-Na2Stage "Run compact recipe $compactRecipe"
    $recipeSwitches = @{
        b = 'Build'
        t = 'Test'
        c = 'Current'
        p = 'Previous'
        w = 'Watch'
    }
    foreach ($step in $compactRecipe.ToCharArray()) {
        $stepName = [string]$step
        Write-Na2Stage "Recipe step $stepName"
        $stepArguments = @{}
        $stepArguments[$recipeSwitches[$stepName]] = $true
        & $PSCommandPath @stepArguments
    }
    return
}

if ($Watch) {
    & (Join-Path $projectPaths.scripts 'injection\watch.ps1')
    return
}

$runAction = if ($Test) {
    if ($null -ne $workerBuild) { 'worker-build' } else { 'candidate-build' }
}
elseif ($Previous) {
    'previous'
}
elseif ($Current) {
    'current'
}
elseif ($Build) {
    'build-only'
}
else {
    'build-and-launch'
}
$runArguments = @{ Action = $runAction }
if ($null -ne $workerBuild) {
    $runArguments.WorkerOutputIso = $workerBuild.OutputIso
    $runArguments.WorkerLogDirectory = $workerBuild.Logs
}
& (Join-Path $projectPaths.scripts 'na228\run.ps1') @runArguments
