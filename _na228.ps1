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
. (Join-Path $PSScriptRoot 'scripts\lib\run_log.ps1')
. (Join-Path $PSScriptRoot 'scripts\na228\worker_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$currentIsoName = [IO.Path]::GetFileName($projectPaths.files.current_iso)
$previousIsoName = [IO.Path]::GetFileName($projectPaths.files.previous_iso)
$candidateIsoName = [IO.Path]::GetFileName($projectPaths.files.candidate_iso)

function Write-Na2Stage {
    param([string]$Message)
    Write-Host "[na228] $Message" -ForegroundColor Cyan
}

function Invoke-Na2Actualization {
    & $projectPaths.files.actualize_command na228 -NoRunLog
}

function Get-Na2DevPinePort {
    $iniPath = Join-Path $projectPaths.pcsx2_dev 'inis\PCSX2.ini'
    if (-not (Test-Path -LiteralPath $iniPath -PathType Leaf)) {
        throw "Development PCSX2 configuration was not found: $iniPath"
    }
    $match = Select-String `
        -LiteralPath $iniPath `
        -Pattern '^\s*PINESlot\s*=\s*(\d+)\s*$' |
        Select-Object -First 1
    if ($null -eq $match) {
        throw "Development PCSX2 PINESlot is not configured in $iniPath"
    }
    $port = [int]$match.Matches[0].Groups[1].Value
    if ($port -lt 1 -or $port -gt 65535) {
        throw "Development PCSX2 PINESlot is invalid: $port"
    }
    return $port
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
$command = if ($Mode -and -not $Test) { $Mode.ToLowerInvariant() } else { '' }
$runSelected = $Current -or $Previous

if (@($Build, $Test, $Current, $Previous, $Watch).Where({ $_ }).Count -gt 1) {
    throw '-Build / -b, -Test / -t, -Current / -c, -Previous / -p, and -Watch / -w are mutually exclusive.'
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

if ($Watch) {
    $pinePort = Get-Na2DevPinePort
    Write-Na2Stage "Watch src/ and hot-reload through PINE port $pinePort"
    & (Join-Path $projectPaths.scripts 'injection\watch.ps1') `
        -PinePort $pinePort
    return
}

$runMode = if ($Test) {
    if ($null -ne $workerBuild) { 'worker-build' } else { 'candidate-build' }
}
elseif ($Previous) {
    'previous'
}
elseif ($Current) {
    'current'
}
else {
    'build'
}
$runLog = $null
try {
    $runLogArguments = @{
        Mode = $runMode
        ProjectPaths = $projectPaths
    }
    if ($null -ne $workerBuild) {
        $runLogArguments.LogDirectory = $workerBuild.Logs
    }
    $runLog = Start-Na2RunLog @runLogArguments
}
catch {
    Write-Warning "Could not start NA2 log: $($_.Exception.Message)"
}

$runOutcome = 'failed'
$runFailure = ''
try {
    if ($Test) {
        if ($null -ne $workerBuild) {
            $portableOutput = ConvertTo-Na2ProjectPath `
                -Path $workerBuild.OutputIso `
                -ProjectPaths $projectPaths
            Write-Na2Stage "Build isolated worker ISO $portableOutput"
            $buildResult = & (Join-Path $projectPaths.scripts 'na228\build.ps1') `
                -WorkerOutputIso $workerBuild.OutputIso
            if (-not $buildResult -or $buildResult.Status -ne 'worker') {
                throw 'Worker build did not return a valid result.'
            }
        }
        else {
            Write-Na2Stage "Build $candidateIsoName"
            $buildResult = & (Join-Path $projectPaths.scripts 'na228\build.ps1') -CandidateOnly
            if (-not $buildResult -or $buildResult.Status -ne 'candidate') {
                throw 'Candidate build did not return a valid result.'
            }
            Invoke-Na2Actualization
        }
    }
    elseif ($Build) {
        Write-Na2Stage "Build $currentIsoName without launching PCSX2"
        $buildResult = & (Join-Path $projectPaths.scripts 'na228\build.ps1')
        if (-not $buildResult -or $buildResult.Status -notin @('unchanged', 'updated')) {
            throw 'Profile build did not return a valid promotion result.'
        }
        Invoke-Na2Actualization
    }
    elseif ($runSelected) {
        $isoPath = if ($Previous) {
            $projectPaths.files.previous_iso
        }
        else {
            $projectPaths.files.current_iso
        }
        $isoName = [IO.Path]::GetFileName($isoPath)
        Write-Na2Stage "Run $isoName without rebuilding"
        Invoke-Na2Actualization
        & $projectPaths.files.pcsx2_launch_command `
            -IsoPath $isoPath
    }
    else {
        Write-Na2Stage '1/2 Build pinned current profile'
        $buildResult = & (Join-Path $projectPaths.scripts 'na228\build.ps1')
        if (-not $buildResult -or $buildResult.Status -notin @('unchanged', 'updated')) {
            throw 'Profile build did not return a valid promotion result.'
        }
        Invoke-Na2Actualization
        Write-Na2Stage "2/2 Launch $currentIsoName"
        & $projectPaths.files.pcsx2_launch_command `
            -IsoPath $projectPaths.files.current_iso
    }
    $runOutcome = 'succeeded'
}
catch {
    $runFailure = $_.Exception.Message
    throw
}
finally {
    if ($null -ne $runLog) {
        try {
            Complete-Na2RunLog `
                -Context $runLog `
                -Outcome $runOutcome `
                -FailureMessage $runFailure
        }
        catch {
            Write-Warning "Could not finalize NA2 logs: $($_.Exception.Message)"
        }
    }
}
