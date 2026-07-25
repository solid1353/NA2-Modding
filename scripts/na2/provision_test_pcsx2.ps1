[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$WorkerRoot
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'worker_paths.ps1')
. (Join-Path $PSScriptRoot 'worker_pcsx2.ps1')

$projectPaths = Get-Na2ProjectPaths
$worker = Get-Na2WorkerContext `
    -WorkerRoot $WorkerRoot `
    -ProjectPaths $projectPaths `
    -RequireRelative
$context = Initialize-Na2WorkerPcsx2 `
    -Worker $worker `
    -ProjectPaths $projectPaths
Assert-Na2WorkerPcsx2NotBlocked -Context $context

Write-Host (
    '[na2] Workstream PCSX2 clone ready: ' +
    (ConvertTo-Na2ProjectPath -Path $context.Root -ProjectPaths $projectPaths)
) -ForegroundColor Green
return $context
