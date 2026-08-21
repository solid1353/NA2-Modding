[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$agentLab = Join-Path ([string]$paths.scripts) 'research\substitution\agent_lab.ps1'
$helpText = (& $agentLab -Port 28014 --help | Out-String)
if ($LASTEXITCODE -ne 0) {
    throw "Agent-lab help failed with exit code $LASTEXITCODE."
}
if ($helpText -notmatch 'Frame-exact NA2 control') {
    throw 'Agent-lab help did not reach the Python command.'
}

Write-Host 'Substitution agent-lab entrypoint test passed.'
