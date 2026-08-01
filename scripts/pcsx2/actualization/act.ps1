[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('input', 'help')]
    [string]$Mode,

    [Parameter(Position = 1)]
    [string]$InputProfile,

    [Alias('h')]
    [switch]$Help,

    [Parameter(DontShow)]
    [switch]$NoRunLog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($Help -or $Mode -ceq 'help') {
    @(
        'Input-profile commands:'
        '  act                  Generate the Default input profiles'
        '  act input [profile]  Generate the selected input profiles'
        '  act help             Show this help'
        ''
    ) | Write-Output
    return
}

. (Join-Path $PSScriptRoot '..\..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\..\lib\run_log.ps1')

$projectPaths = Get-Na2ProjectPaths
$runLog = $null
if (-not $NoRunLog) {
    try {
        $runLog = Start-Na2RunLog `
            -Mode 'actualize-input' `
            -ProjectPaths $projectPaths
    }
    catch {
        Write-Warning "Could not start actualization log: $($_.Exception.Message)"
    }
}

$runOutcome = 'failed'
$runFailure = ''
try {
    $inputArguments = @{ PassThru = $true }
    if (-not [string]::IsNullOrWhiteSpace($InputProfile)) {
        $inputArguments.Profile = $InputProfile
    }
    Write-Host '[act] Generate input profiles and update GameSettings' `
        -ForegroundColor Cyan
    $output = @(
        & $projectPaths.files.actualize_input_command @inputArguments
    )
    if ($output.Count -ne 1) {
        throw (
            'Input synchronization returned {0} results; expected one.' -f
            $output.Count
        )
    }
    Write-Host (
        "[act] Input profile $($output[0].Profile): " +
        "generated $($output[0].GeneratedProfiles.Count), " +
        "removed $($output[0].RemovedProfiles.Count), " +
        "updated GameSettings $($output[0].UpdatedGameSettings.Count)."
    ) -ForegroundColor Cyan
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
            Write-Warning "Could not finalize input-profile logs: $($_.Exception.Message)"
        }
    }
}
