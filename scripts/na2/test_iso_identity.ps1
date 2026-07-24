[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'iso_identity.ps1')

if ((Get-Na2DiscSerialFromBootPath 'SLPS_258.37') -cne 'SLPS-25837') {
    throw 'Numeric boot-path serial parsing regressed.'
}
if ((Get-Na2DiscSerialFromBootPath 'SLOP_NA2.28') -cne 'SLOP-NA228') {
    throw 'Alphanumeric boot-path serial parsing failed.'
}

$rejected = $false
try {
    $null = Get-Na2DiscSerialFromBootPath 'INVALID.ELF'
}
catch {
    $rejected = $true
}
if (-not $rejected) {
    throw 'Invalid boot-path serial was accepted.'
}

Write-Host 'ISO identity tests passed.'
