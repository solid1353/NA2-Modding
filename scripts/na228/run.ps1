[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet(
        'cache-build',
        'manual-build',
        'latest-build',
        'latest-build-and-launch'
    )]
    [string]$Action,

    [string]$CacheConfiguration,
    [string]$CacheLogDirectory,
    [switch]$Force,
    [switch]$Turbo,
    [switch]$Unlimited
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

if ($Action -eq 'cache-build') {
    if ([string]::IsNullOrWhiteSpace($CacheConfiguration)) {
        throw 'Cache build action requires a configuration.'
    }
}
elseif ($CacheConfiguration -or $CacheLogDirectory) {
    throw 'Cache arguments are valid only for cache-build.'
}
if ($Force -and $Action -notin @(
    'manual-build',
    'latest-build',
    'latest-build-and-launch'
)) {
    throw 'Force mode is valid only for ordinary Latest or Manual builds.'
}
if (($Turbo -or $Unlimited) -and $Action -ne 'latest-build-and-launch') {
    throw 'Speed mode is valid only for a build-and-launch action.'
}
if ($Turbo -and $Unlimited) {
    throw 'Use only one of Turbo or Unlimited.'
}

$runMode = switch ($Action) {
    'cache-build' { 'cache-build' }
    'manual-build' { 'manual-build' }
    default { 'build' }
}
$runLog = $null
try {
    $runLogArguments = @{
        Mode = $runMode
        Paths = $paths
    }
    if (-not [string]::IsNullOrWhiteSpace($CacheLogDirectory)) {
        $runLogArguments.LogDirectory = $CacheLogDirectory
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
        'cache-build' {
            Write-Na2Stage "Build or reuse cached ISO for $CacheConfiguration"
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') `
                -CacheConfiguration $CacheConfiguration `
                -CacheLogDirectory $CacheLogDirectory
            if (-not $buildResult -or $buildResult.Status -ne 'cache') {
                throw 'Cache build did not return a valid result.'
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
                $buildResult.Status -notin @('unchanged', 'updated', 'pending')
            ) {
                throw 'Configuration build did not return a valid promotion result.'
            }
        }
        'latest-build-and-launch' {
            Write-Na2Stage '1/2 Build development configuration'
            $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') -Force:$Force
            if (
                -not $buildResult -or
                $buildResult.Status -notin @('unchanged', 'updated', 'pending')
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
            $launchArguments = @{ IsoPath = $launchIso }
            if ($Unlimited) {
                $launchArguments.Unlimited = $true
            }
            else {
                $launchArguments.UnlimitedForFrames = [UInt64](
                    $paths.settings.startup_fast_forward_frames
                )
                if ($Turbo) {
                    $launchArguments.Turbo = $true
                }
            }
            & $paths.files.pcsx2_launch_command @launchArguments
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

if ($Action -eq 'cache-build') {
    return $buildResult
}
