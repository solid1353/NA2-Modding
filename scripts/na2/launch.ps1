[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$IsoPath,
    [ValidateSet('Normal', 'Minimized', 'Hidden')]
    [string]$WindowStyle = 'Normal'
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'pnach_state.ps1')
. (Join-Path $PSScriptRoot 'process.ps1')
$projectPaths = Get-Na2ProjectPaths

$resolvedIso = if ([IO.Path]::IsPathRooted($IsoPath)) {
    [IO.Path]::GetFullPath($IsoPath)
}
else {
    [IO.Path]::GetFullPath((Join-Path $projectPaths.repository $IsoPath))
}
$resolvedPcsx2Exe = [IO.Path]::GetFullPath((Join-Path $projectPaths.pcsx2 'pcsx2-qt.exe'))

Stop-Na2Pcsx2 -Executable $resolvedPcsx2Exe

if (-not (Test-Path -LiteralPath $resolvedIso -PathType Leaf)) {
    throw "ISO does not exist: $resolvedIso"
}
if (-not (Test-Path -LiteralPath $resolvedPcsx2Exe -PathType Leaf)) {
    throw "PCSX2 executable does not exist: $resolvedPcsx2Exe"
}

$global:LASTEXITCODE = 0
try {
    & (Join-Path $PSScriptRoot 'actualize_pnach.ps1') -IsoPath $resolvedIso
}
catch {
    throw "PNACH actualization failed: $($_.Exception.Message)"
}
if ($LASTEXITCODE -ne 0) {
    throw "PNACH actualization failed (exit $LASTEXITCODE)."
}

$canonicalPnach = Join-Path $projectPaths.pcsx2_files 'SLPS-25837_C0659AD1.pnach'
$pnachState = Get-Na2PnachState -Path $canonicalPnach
$enabledCheats = if ($pnachState.EnabledCheats.Count -eq 0) {
    'none'
}
else {
    $pnachState.EnabledCheats -join ', '
}
Write-Host "[na2] Enabled cheats: $enabledCheats" -ForegroundColor Cyan

$startArguments = @{
    FilePath = $resolvedPcsx2Exe
    ArgumentList = @('-batch', "`"$resolvedIso`"")
}
if ($WindowStyle -ne 'Normal') {
    $startArguments.WindowStyle = $WindowStyle
}
Start-Process @startArguments
