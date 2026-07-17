[CmdletBinding()]
param(
    [string]$IsoPath,
    [string]$Pcsx2Exe,
    [switch]$SkipActualize,
    [ValidateSet('Normal', 'Minimized', 'Hidden')]
    [string]$WindowStyle = 'Normal'
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'project_paths.ps1')
. (Join-Path $PSScriptRoot 'pnach_state.ps1')
$projectPaths = Get-Na2ProjectPaths

if ([string]::IsNullOrWhiteSpace($IsoPath)) {
    $IsoPath = Join-Path $projectPaths.build 'Current.iso'
}
if ([string]::IsNullOrWhiteSpace($Pcsx2Exe)) {
    $Pcsx2Exe = Join-Path $projectPaths.pcsx2 'pcsx2-qt.exe'
}

$resolvedIso = if ([IO.Path]::IsPathRooted($IsoPath)) {
    [IO.Path]::GetFullPath($IsoPath)
}
else {
    [IO.Path]::GetFullPath((Join-Path $projectPaths.repository $IsoPath))
}
$resolvedPcsx2Exe = [IO.Path]::GetFullPath($Pcsx2Exe)
$processName = [IO.Path]::GetFileNameWithoutExtension($resolvedPcsx2Exe)

Stop-Process -Name $processName -Force -ErrorAction SilentlyContinue

if (-not (Test-Path -LiteralPath $resolvedIso -PathType Leaf)) {
    throw "ISO does not exist: $resolvedIso"
}
if (-not (Test-Path -LiteralPath $resolvedPcsx2Exe -PathType Leaf)) {
    throw "PCSX2 executable does not exist: $resolvedPcsx2Exe"
}

if (-not $SkipActualize) {
    $global:LASTEXITCODE = 0
    try {
        & (Join-Path $PSScriptRoot 'actualize_cheats_for_build_iso.ps1') -IsoPath $resolvedIso
    }
    catch {
        throw "PNACH actualization failed: $($_.Exception.Message)"
    }
    if ($LASTEXITCODE -ne 0) {
        throw "PNACH actualization failed (exit $LASTEXITCODE)."
    }
}

$enabledCheats = if ($SkipActualize) {
    'not checked (-SkipActualize)'
}
else {
    $canonicalPnach = Join-Path $projectPaths.pcsx2_files 'SLPS-25837_C0659AD1.pnach'
    $pnachState = Get-Na2PnachState -Path $canonicalPnach
    if ($pnachState.EnabledCheats.Count -eq 0) {
        'none'
    }
    else {
        $pnachState.EnabledCheats -join ', '
    }
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
