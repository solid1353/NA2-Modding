[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$WorkerRoot,
    [Parameter(Mandatory = $true)][string]$IsoPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\na2\worker_paths.ps1')

$projectPaths = Get-Na2ProjectPaths
$worker = Get-Na2WorkerContext `
    -WorkerRoot $WorkerRoot `
    -ProjectPaths $projectPaths `
    -RequireRelative
$iso = if ([IO.Path]::IsPathRooted($IsoPath)) {
    throw 'ISO paths must be repository-relative.'
}
else {
    [IO.Path]::GetFullPath((Join-Path $projectPaths.repository $IsoPath))
}
$executable = Join-Path $worker.Pcsx2 'pcsx2-qt.exe'

if (-not (Test-Path -LiteralPath $iso -PathType Leaf)) {
    throw "ISO does not exist: $IsoPath"
}
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw (
        'The workstream PCSX2 copy does not exist. Copy pcsx2_clean to ' +
        "work/$($worker.WorkerName)/pcsx2 before launching."
    )
}

Start-Process `
    -FilePath $executable `
    -WorkingDirectory $worker.Pcsx2 `
    -ArgumentList @('-batch', "`"$iso`"") `
    -WindowStyle Hidden
