Set-StrictMode -Version Latest

function Invoke-Na2BuilderModule {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Repository,
        [Parameter(Mandatory = $true)][string]$Module,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList
    )

    Push-Location -LiteralPath $Repository
    try {
        $output = @(
            & (Join-Path $PSScriptRoot 'run_python.ps1') -PackageSet builder `
                -Module "na228_builder.infrastructure.orchestration.$Module" `
                -ArgumentList $ArgumentList -NoBytecode 2>&1
        )
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    return [pscustomobject]@{
        Output = [string[]]@($output | ForEach-Object { [string]$_ })
        ExitCode = $exitCode
    }
}

function Get-Na2ConfigurationFailure {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][AllowEmptyCollection()][AllowEmptyString()][string[]]$Output)

    $message = $null
    foreach ($line in $Output) {
        if ($line -match '(?:^|\.)ConfigurationError:\s*(?<message>.+)$') {
            $message = $Matches.message.Trim()
        }
    }
    if ($null -eq $message) {
        return $null
    }
    return [pscustomobject]@{
        Message = $message
        TechnicalDetails = $Output -join "`n"
    }
}

function Assert-Na2BuilderModuleSucceeded {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][psobject]$Execution,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )

    if ($Execution.ExitCode -eq 0) {
        return
    }
    $configurationFailure = Get-Na2ConfigurationFailure -Output $Execution.Output
    if ($null -ne $configurationFailure) {
        $exception = [InvalidOperationException]::new($configurationFailure.Message)
        $exception.Data['Na2ConfigurationError'] = $true
        $exception.Data['Na2TechnicalDetails'] = $configurationFailure.TechnicalDetails
        throw $exception
    }
    $Execution.Output | ForEach-Object { Write-Host $_ }
    throw $FailureMessage
}
