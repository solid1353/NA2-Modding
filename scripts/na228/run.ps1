[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet(
        'worker-build',
        'candidate-build',
        'build-only',
        'current',
        'previous',
        'build-and-launch'
    )]
    [string]$Action,

    [string]$WorkerOutputIso,
    [string]$WorkerLogDirectory
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\run_log.ps1')
$projectPaths = Get-Na2ProjectPaths
$currentIsoName = [IO.Path]::GetFileName($projectPaths.files.current_iso)
$candidateIsoName = [IO.Path]::GetFileName($projectPaths.files.candidate_iso)

function Write-Na2Stage {
    param([string]$Message)
    Write-Host "[na228] $Message" -ForegroundColor Cyan
}

function Invoke-Na2Actualization {
    & $projectPaths.files.actualize_command na228 -NoRunLog
}

if ($Action -eq 'worker-build') {
    if (
        [string]::IsNullOrWhiteSpace($WorkerOutputIso) -or
        [string]::IsNullOrWhiteSpace($WorkerLogDirectory)
    ) {
        throw 'Worker build action requires its output ISO and log directory.'
    }
}
elseif ($WorkerOutputIso -or $WorkerLogDirectory) {
    throw 'Worker output arguments are valid only for worker-build.'
}

$runMode = switch ($Action) {
    'worker-build' { 'worker-build' }
    'candidate-build' { 'candidate-build' }
    'current' { 'current' }
    'previous' { 'previous' }
    default { 'build' }
}
$runLog = $null
try {
    $runLogArguments = @{
        Mode = $runMode
        ProjectPaths = $projectPaths
    }
    if ($Action -eq 'worker-build') {
        $runLogArguments.LogDirectory = $WorkerLogDirectory
    }
    $runLog = Start-Na2RunLog @runLogArguments
}
catch {
    Write-Warning "Could not start NA2 log: $($_.Exception.Message)"
}

$runOutcome = 'failed'
$runFailure = ''
try {
    switch ($Action) {
        'worker-build' {
            $portableOutput = ConvertTo-Na2ProjectPath `
                -Path $WorkerOutputIso `
                -ProjectPaths $projectPaths
            Write-Na2Stage "Build isolated worker ISO $portableOutput"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') `
                -WorkerOutputIso $WorkerOutputIso
            if (-not $buildResult -or $buildResult.Status -ne 'worker') {
                throw 'Worker build did not return a valid result.'
            }
        }
        'candidate-build' {
            Write-Na2Stage "Build $candidateIsoName"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') -CandidateOnly
            if (-not $buildResult -or $buildResult.Status -ne 'candidate') {
                throw 'Candidate build did not return a valid result.'
            }
            Invoke-Na2Actualization
        }
        'build-only' {
            Write-Na2Stage "Build $currentIsoName without launching PCSX2"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1')
            if (
                -not $buildResult -or
                $buildResult.Status -notin @('unchanged', 'updated')
            ) {
                throw 'Profile build did not return a valid promotion result.'
            }
            Invoke-Na2Actualization
        }
        { $_ -in @('current', 'previous') } {
            $isoPath = if ($Action -eq 'previous') {
                $projectPaths.files.previous_iso
            }
            else {
                $projectPaths.files.current_iso
            }
            $isoName = [IO.Path]::GetFileName($isoPath)
            Write-Na2Stage "Run $isoName without rebuilding"
            Invoke-Na2Actualization
            & $projectPaths.files.pcsx2_launch_command -IsoPath $isoPath
        }
        'build-and-launch' {
            Write-Na2Stage '1/2 Build pinned current profile'
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1')
            if (
                -not $buildResult -or
                $buildResult.Status -notin @('unchanged', 'updated')
            ) {
                throw 'Profile build did not return a valid promotion result.'
            }
            Invoke-Na2Actualization
            Write-Na2Stage "2/2 Launch $currentIsoName"
            & $projectPaths.files.pcsx2_launch_command `
                -IsoPath $projectPaths.files.current_iso
        }
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
