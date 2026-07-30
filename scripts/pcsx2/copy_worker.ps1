[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$WorkerRoot
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\na228\worker_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$worker = Get-Na2WorkerContext `
    -WorkerRoot $WorkerRoot `
    -ProjectPaths $projectPaths `
    -RequireRelative

$template = [IO.Path]::GetFullPath($projectPaths.pcsx2_clean)
$sharedBios = [IO.Path]::GetFullPath($projectPaths.pcsx2_bios)
if (-not (Test-Path -LiteralPath $template -PathType Container)) {
    throw "Worker PCSX2 template does not exist: $template"
}
if (-not (Test-Path -LiteralPath $sharedBios -PathType Container)) {
    throw "Shared PCSX2 BIOS directory does not exist: $sharedBios"
}
if (@(Get-ChildItem -LiteralPath $sharedBios -File -Filter '*.bin').Count -eq 0) {
    throw "Shared PCSX2 BIOS directory contains no BIOS image: $sharedBios"
}
if (Test-Path -LiteralPath $worker.Pcsx2) {
    throw (
        "Worker PCSX2 destination already exists: $($worker.Pcsx2). " +
        'Audit and remove the old task-owned runtime before copying a fresh one.'
    )
}

if (-not $PSCmdlet.ShouldProcess(
    $worker.Pcsx2,
    "copy the clean PCSX2 template and shared BIOS for $($worker.WorkerName)"
)) {
    return
}

New-Item -ItemType Directory -Force -Path $worker.Root | Out-Null
Copy-Item -LiteralPath $template -Destination $worker.Pcsx2 -Recurse
$workerBios = Join-Path $worker.Pcsx2 'bios'
New-Item -ItemType Directory -Force -Path $workerBios | Out-Null
Get-ChildItem -LiteralPath $sharedBios -Force | Copy-Item `
    -Destination $workerBios `
    -Recurse `
    -Force

Write-Host "[pcsx2] Worker runtime created: $($worker.Pcsx2)"
Write-Host "[pcsx2] BIOS copied from: $sharedBios"
