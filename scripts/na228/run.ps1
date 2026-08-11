[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet(
        'worker-build',
        'manual-build',
        'latest-build',
        'latest-build-and-launch'
    )]
    [string]$Action,

    [string]$WorkerOutputIso,
    [string]$WorkerLogDirectory,
    [switch]$WorkerEphemeral,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\run_log.ps1')
$paths = Get-Na2Paths
$latestIsoName = [IO.Path]::GetFileName($paths.files.latest_iso)
$manualIsoName = [IO.Path]::GetFileName($paths.files.manual_iso)

function Write-Na2Stage {
    param([string]$Message)
    Write-Host "[na228] $Message" -ForegroundColor Cyan
}

if ($Action -eq 'worker-build') {
    if (
        [string]::IsNullOrWhiteSpace($WorkerOutputIso) -or
        [string]::IsNullOrWhiteSpace($WorkerLogDirectory)
    ) {
        throw 'Worker build action requires its output ISO and log directory.'
    }
}
elseif ($WorkerOutputIso -or $WorkerLogDirectory -or $WorkerEphemeral) {
    throw 'Worker output arguments are valid only for worker-build.'
}
if ($Force -and $Action -notin @(
    'manual-build',
    'latest-build',
    'latest-build-and-launch'
)) {
    throw 'Force mode is valid only for ordinary Latest or Manual builds.'
}

$runMode = switch ($Action) {
    'worker-build' { 'worker-build' }
    'manual-build' { 'manual-build' }
    default { 'build' }
}
$runLog = $null
try {
    $runLogArguments = @{
        Mode = $runMode
        Paths = $paths
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
$runTechnicalDetails = ''
try {
    switch ($Action) {
        'worker-build' {
            $portableOutput = ConvertTo-Na2ProjectPath `
                -Path $WorkerOutputIso `
                -Paths $paths
            $workerKind = if ($WorkerEphemeral) { 'ephemeral worker' } else { 'isolated worker' }
            Write-Na2Stage "Build $workerKind ISO $portableOutput"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') `
                -WorkerOutputIso $WorkerOutputIso `
                -WorkerEphemeral:$WorkerEphemeral
            if (-not $buildResult -or $buildResult.Status -ne 'worker') {
                throw 'Worker build did not return a valid result.'
            }
        }
        'manual-build' {
            Write-Na2Stage "Build $manualIsoName"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') `
                -ManualOnly `
                -Force:$Force
            if (-not $buildResult -or $buildResult.Status -ne 'manual') {
                throw 'Manual build did not return a valid result.'
            }
        }
        'latest-build' {
            Write-Na2Stage "Build $latestIsoName"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') -Force:$Force
            if (
                -not $buildResult -or
                $buildResult.Status -notin @('unchanged', 'updated')
            ) {
                throw 'Configuration build did not return a valid promotion result.'
            }
        }
        'latest-build-and-launch' {
            Write-Na2Stage '1/2 Build development configuration'
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') -Force:$Force
            if (
                -not $buildResult -or
                $buildResult.Status -notin @('unchanged', 'updated', 'forced-staged')
            ) {
                throw 'Configuration build did not return a valid promotion result.'
            }
            $launchIso = if (
                $null -ne $buildResult.PSObject.Properties['LaunchIso'] -and
                -not [string]::IsNullOrWhiteSpace([string]$buildResult.LaunchIso)
            ) {
                [string]$buildResult.LaunchIso
            }
            else {
                $paths.files.latest_iso
            }
            Write-Na2Stage "2/2 Launch $([IO.Path]::GetFileName($launchIso))"
            & $paths.files.pcsx2_launch_command `
                -IsoPath $launchIso `
                -Turbo
        }
    }
    $runOutcome = 'succeeded'
}
catch {
    $runFailure = $_.Exception.Message
    if ([bool]$_.Exception.Data['Na2ConfigurationError']) {
        $runTechnicalDetails = [string]$_.Exception.Data['Na2TechnicalDetails']
    }
    throw
}
finally {
    if ($null -ne $runLog) {
        try {
            Complete-Na2RunLog `
                -Context $runLog `
                -Outcome $runOutcome `
                -FailureMessage $runFailure `
                -TechnicalDetails $runTechnicalDetails
        }
        catch {
            Write-Warning "Could not finalize NA2 logs: $($_.Exception.Message)"
        }
    }
}
