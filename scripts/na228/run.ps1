[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet(
        'worker-build',
        'manual-test-build',
        'latest-build',
        'latest-build-and-launch'
    )]
    [string]$Action,

    [string]$WorkerOutputIso,
    [string]$WorkerLogDirectory
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\run_log.ps1')
$paths = Get-Na2Paths
$latestIsoName = [IO.Path]::GetFileName($paths.files.latest_iso)
$manualTestIsoName = [IO.Path]::GetFileName($paths.files.manual_test_iso)

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
elseif ($WorkerOutputIso -or $WorkerLogDirectory) {
    throw 'Worker output arguments are valid only for worker-build.'
}

$runMode = switch ($Action) {
    'worker-build' { 'worker-build' }
    'manual-test-build' { 'manual-test-build' }
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
            Write-Na2Stage "Build isolated worker ISO $portableOutput"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') `
                -WorkerOutputIso $WorkerOutputIso
            if (-not $buildResult -or $buildResult.Status -ne 'worker') {
                throw 'Worker build did not return a valid result.'
            }
        }
        'manual-test-build' {
            Write-Na2Stage "Build $manualTestIsoName"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') -ManualTestOnly
            if (-not $buildResult -or $buildResult.Status -ne 'manual-test') {
                throw 'Manual Test build did not return a valid result.'
            }
        }
        'latest-build' {
            Write-Na2Stage "Build $latestIsoName"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1')
            if (
                -not $buildResult -or
                $buildResult.Status -notin @('unchanged', 'updated')
            ) {
                throw 'Configuration build did not return a valid promotion result.'
            }
        }
        'latest-build-and-launch' {
            Write-Na2Stage '1/2 Build development configuration'
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1')
            if (
                -not $buildResult -or
                $buildResult.Status -notin @('unchanged', 'updated')
            ) {
                throw 'Configuration build did not return a valid promotion result.'
            }
            Write-Na2Stage "2/2 Launch $latestIsoName"
            & $paths.files.pcsx2_launch_command `
                -IsoPath $paths.files.latest_iso
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
