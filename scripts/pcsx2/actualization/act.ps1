[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('na228', 'input', 'help')]
    [string]$Mode,

    [Parameter(Position = 1)]
    [string]$InputProfile,

    [Alias('h')]
    [switch]$Help,

    [Parameter(DontShow)]
    [ValidateSet('latest', 'previous', 'test')]
    [string[]]$Roles,

    [Parameter(DontShow)]
    [switch]$NoRunLog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($Help -or $Mode -ceq 'help') {
    @(
        'Actualization commands:'
        '  act        Run na228, then input'
        '  act na228    Actualize built NA2.28 GameSettings and cheat aliases'
        '  act input [profile]  Generate input profiles and update GameSettings'
        '  act help   Show this help'
        ''
    ) | Write-Output
    return
}

. (Join-Path $PSScriptRoot '..\..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\..\lib\run_log.ps1')

$projectPaths = Get-Na2ProjectPaths
$selectedModes = @(
    if ([string]::IsNullOrWhiteSpace($Mode)) {
        'na228'
        'input'
    }
    else {
        $Mode
    }
)
if ($null -ne $Roles -and $Roles.Count -gt 0 -and (
    $selectedModes.Count -ne 1 -or
    $selectedModes[0] -ne 'na228'
)) {
    throw 'Role-scoped actualization is valid only for act na228.'
}
if (-not [string]::IsNullOrWhiteSpace($InputProfile) -and
    ($selectedModes.Count -ne 1 -or $selectedModes[0] -ne 'input')) {
    throw 'An input profile may be selected only with act input.'
}
$runLog = $null
if (-not $NoRunLog) {
    try {
        $logMode = if ($selectedModes.Count -eq 1) {
            "actualize-$($selectedModes[0])"
        }
        else {
            'actualize'
        }
        $runLog = Start-Na2RunLog `
            -Mode $logMode `
            -ProjectPaths $projectPaths
    }
    catch {
        Write-Warning "Could not start actualization log: $($_.Exception.Message)"
    }
}

$runOutcome = 'failed'
$runFailure = ''
try {
    foreach ($selectedMode in $selectedModes) {
        switch ($selectedMode) {
            'na228' {
                Write-Host '[act] Actualize built NA2.28 images' `
                    -ForegroundColor Cyan
                $syncArguments = @{}
                if ($null -ne $Roles -and $Roles.Count -gt 0) {
                    $syncArguments.Roles = $Roles
                }
                $output = @(
                    & $projectPaths.files.actualize_na228_command @syncArguments
                )
                if ($output.Count -ne 1) {
                    throw (
                        'NA2 actualization returned {0} results; expected one.' -f
                        $output.Count
                    )
                }
                Write-Host (
                    Format-Na2ActualizeStatus `
                        -Result $output[0] `
                        -ProjectPaths $projectPaths
                ) -ForegroundColor Cyan
            }
            'input' {
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
                        'Input actualization returned {0} results; expected one.' -f
                        $output.Count
                    )
                }
                Write-Host (
                    "[act] Input profile $($output[0].Profile): " +
                    "generated $($output[0].GeneratedProfiles.Count), " +
                    "removed $($output[0].RemovedProfiles.Count), " +
                    "updated GameSettings " +
                    "$($output[0].UpdatedGameSettings.Count)."
                ) `
                    -ForegroundColor Cyan
            }
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
            Write-Warning "Could not finalize actualization logs: $($_.Exception.Message)"
        }
    }
}
