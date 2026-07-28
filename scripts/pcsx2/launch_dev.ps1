[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

& (Join-Path $PSScriptRoot 'launch_configured.ps1') -Target dev @Arguments
