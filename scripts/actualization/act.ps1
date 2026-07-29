[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('na2', 'input', 'help')]
    [string]$Mode,

    [Alias('h')]
    [switch]$Help,

    [Parameter(DontShow)]
    [switch]$NoRunLog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($Help -or $Mode -ceq 'help') {
    @(
        'Actualization commands:'
        '  act        Run na2, then input'
        '  act na2    Actualize built NA2.28 GameSettings and cheat aliases'
        '  act input  Regenerate the Comparison_NA2 input profile'
        '  act help   Show this help'
        ''
    ) | Write-Output
    return
}

. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\run_log.ps1')

$projectPaths = Get-Na2ProjectPaths
$selectedModes = @(
    if ([string]::IsNullOrWhiteSpace($Mode)) {
        'na2'
        'input'
    }
    else {
        $Mode
    }
)
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
            'na2' {
                Write-Host '[act] Actualize built NA2.28 images' `
                    -ForegroundColor Cyan
                $output = @(
                    & $projectPaths.files.actualize_na2_command
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
                Write-Host '[act] Actualize Comparison_NA2 input profile' `
                    -ForegroundColor Cyan
                $output = @(
                    & $projectPaths.files.actualize_input_command -PassThru
                )
                if ($output.Count -ne 1) {
                    throw (
                        'Input actualization returned {0} results; expected one.' -f
                        $output.Count
                    )
                }
                $state = if ($output[0].Changed) {
                    'updated'
                }
                else {
                    'already current'
                }
                Write-Host "[act] Comparison_NA2: $state." `
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
