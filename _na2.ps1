[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('act')]
    [string]$Mode,

    [Alias('c')]
    [switch]$Current,
    [Alias('p')]
    [switch]$Previous,
    [Alias('h')]
    [switch]$Help
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'scripts\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'scripts\lib\run_log.ps1')
$projectPaths = Get-Na2ProjectPaths
$currentIsoName = [IO.Path]::GetFileName($projectPaths.files.current_iso)
$previousIsoName = [IO.Path]::GetFileName($projectPaths.files.previous_iso)

function Write-Na2Stage {
    param([string]$Message)
    Write-Host "[na2] $Message" -ForegroundColor Cyan
}

$command = if ($Mode) { $Mode.ToLowerInvariant() } else { '' }
$runSelected = $Current -or $Previous

if ($Current -and $Previous) {
    throw '-Current / -c and -Previous / -p cannot be used together.'
}
if ($command -and $runSelected) {
    throw '-Current / -c and -Previous / -p cannot be combined with a command mode.'
}
if ($Help) {
    @(
        'NA2 commands:'
        "  na2       Build the pinned current profile, conditionally rotate, then run $currentIsoName"
        "  na2 -c    Run build/$currentIsoName without rebuilding"
        "  na2 -p    Run build/$previousIsoName without rebuilding"
        "  na2 act   Actualize the PNACH symlink for build/$currentIsoName without launching"
        ''
    ) | Write-Output
    return
}

$runMode = if ($command -eq 'act') {
    'actualize'
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
    $runLog = Start-Na2RunLog -Mode $runMode -ProjectPaths $projectPaths
}
catch {
    Write-Warning "Could not start NA2 log: $($_.Exception.Message)"
}

$runOutcome = 'failed'
$runFailure = ''
try {
    if ($command -eq 'act') {
        Write-Na2Stage "Actualize PNACH symlink for $currentIsoName CRC"
        $actualizeOutput = @(
            & (Join-Path $projectPaths.scripts 'na2\actualize_pnach.ps1')
        )
        if ($actualizeOutput.Count -ne 1) {
            throw "PNACH actualization returned $($actualizeOutput.Count) results; expected one."
        }
        Write-Host (
            Format-Na2ActualizeStatus `
                -Result $actualizeOutput[0] `
                -ProjectPaths $projectPaths
        ) -ForegroundColor Cyan
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
        & (Join-Path $projectPaths.scripts 'na2\launch.ps1') `
            -IsoPath $isoPath
    }
    else {
        Write-Na2Stage '1/2 Build pinned current profile'
        $buildResult = & (Join-Path $projectPaths.scripts 'na2\build.ps1')
        if (-not $buildResult -or $buildResult.Status -notin @('unchanged', 'updated')) {
            throw 'Profile build did not return a valid promotion result.'
        }

        Write-Na2Stage "2/2 Actualize PNACH and launch $currentIsoName"
        & (Join-Path $projectPaths.scripts 'na2\launch.ps1') `
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
