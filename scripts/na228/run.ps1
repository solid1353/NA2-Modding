[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet(
        'worker-build',
        'test-build',
        'validate',
        'latest-build',
        'latest-build-and-launch'
    )]
    [string]$Action,

    [string]$WorkerOutputIso,
    [string]$WorkerLogDirectory
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\run_log.ps1')
$projectPaths = Get-Na2ProjectPaths
$latestIsoName = [IO.Path]::GetFileName($projectPaths.files.latest_iso)
$testIsoName = [IO.Path]::GetFileName($projectPaths.files.test_iso)

function Write-Na2Stage {
    param([string]$Message)
    Write-Host "[na228] $Message" -ForegroundColor Cyan
}

function Invoke-Na2Actualization {
    param([string[]]$Roles)

    if ($null -eq $Roles -or $Roles.Count -eq 0) {
        return
    }
    & $projectPaths.files.actualize_command `
        na228 `
        -Roles $Roles `
        -NoRunLog
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
    'test-build' { 'test-build' }
    'validate' { 'validate' }
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
        'validate' {
            Write-Na2Stage 'Validate full current-profile composition without staging an ISO'
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') -ComposeOnly
            if (-not $buildResult -or $buildResult.Status -ne 'validated') {
                throw 'Profile composition did not return a valid result.'
            }
        }
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
        'test-build' {
            Write-Na2Stage "Build $testIsoName"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') -TestOnly
            if (-not $buildResult -or $buildResult.Status -ne 'test') {
                throw 'Test build did not return a valid result.'
            }
            Invoke-Na2Actualization -Roles $buildResult.ChangedRoles
        }
        'latest-build' {
            Write-Na2Stage "Build $latestIsoName without launching PCSX2"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1')
            if (
                -not $buildResult -or
                $buildResult.Status -notin @('unchanged', 'updated')
            ) {
                throw 'Profile build did not return a valid promotion result.'
            }
            Invoke-Na2Actualization -Roles $buildResult.ChangedRoles
        }
        'latest-build-and-launch' {
            Write-Na2Stage '1/2 Build pinned current profile'
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1')
            if (
                -not $buildResult -or
                $buildResult.Status -notin @('unchanged', 'updated')
            ) {
                throw 'Profile build did not return a valid promotion result.'
            }
            Invoke-Na2Actualization -Roles $buildResult.ChangedRoles
            Write-Na2Stage "2/2 Launch $latestIsoName"
            & $projectPaths.files.pcsx2_launch_command `
                -IsoPath $projectPaths.files.latest_iso
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
