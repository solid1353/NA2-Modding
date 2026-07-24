[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputIso
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$buildScript = Join-Path $projectPaths.scripts 'na2\build.ps1'

$result = & $buildScript `
    -WorkerOutputIso $OutputIso `
    -TranslationDisplay mapping_ids

if ($null -eq $result -or $result.Status -ne 'worker') {
    throw 'Mapping-ID diagnostic build did not return a verified worker result.'
}

$result
