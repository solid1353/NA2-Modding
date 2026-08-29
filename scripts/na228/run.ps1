[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('configuration-build')][string]$Action,
    [Parameter(Mandatory)][string]$Configuration,
    [string]$LogDirectory
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\run_log.ps1')
$paths = Get-Na2Paths

$runLog = $null
try {
    $runLogArguments = @{
        Mode = $Action
        Paths = $paths
    }
    if (-not [string]::IsNullOrWhiteSpace($LogDirectory)) {
        $runLogArguments.LogDirectory = $LogDirectory
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
    $buildArguments = @{
        Configuration = $Configuration
    }
    if (-not [string]::IsNullOrWhiteSpace($LogDirectory)) {
        $buildArguments.LogDirectory = $LogDirectory
    }
    $buildResult = & (Join-Path $PSScriptRoot 'build.ps1') @buildArguments
    if ($null -eq $buildResult -or
        $buildResult.Status -notin @('built', 'reused')) {
        throw 'Configuration build returned no valid result.'
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
            Complete-Na2RunLog -Context $runLog -Outcome $runOutcome `
                -FailureMessage $runFailure -TechnicalDetails $runTechnicalDetails
        }
        catch {
            Write-Warning "Could not finalize NA2 logs: $($_.Exception.Message)"
        }
    }
}

return $buildResult
