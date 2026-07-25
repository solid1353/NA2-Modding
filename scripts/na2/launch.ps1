[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$IsoPath,
    [ValidateSet('Normal', 'Minimized', 'Hidden')]
    [string]$WindowStyle = 'Normal',
    [string]$WorkerPcsx2Executable,
    [switch]$KeepExistingInstance,
    [switch]$PassThru
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\run_log.ps1')
. (Join-Path $PSScriptRoot 'ini.ps1')
. (Join-Path $PSScriptRoot 'process.ps1')
. (Join-Path $PSScriptRoot 'worker_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

$resolvedIso = if ([IO.Path]::IsPathRooted($IsoPath)) {
    [IO.Path]::GetFullPath($IsoPath)
}
else {
    [IO.Path]::GetFullPath((Join-Path $projectPaths.repository $IsoPath))
}
$resolvedPcsx2Exe = if ([string]::IsNullOrWhiteSpace($WorkerPcsx2Executable)) {
    [IO.Path]::GetFullPath($projectPaths.files.pcsx2_user_exe)
}
else {
    $candidate = [IO.Path]::GetFullPath($WorkerPcsx2Executable)
    $cloneRoot = [IO.Path]::GetDirectoryName($candidate)
    $workerRoot = [IO.Path]::GetDirectoryName($cloneRoot)
    try {
        $worker = Get-Na2WorkerContext `
            -WorkerRoot $workerRoot `
            -ProjectPaths $projectPaths
    }
    catch {
        throw "Invalid worker PCSX2 override: $($_.Exception.Message)"
    }
    if (-not $KeepExistingInstance -or
        [IO.Path]::GetFileName($candidate) -cne 'pcsx2-qt.exe' -or
        -not [IO.Path]::Equals($cloneRoot, $worker.Pcsx2)) {
        throw (
            'A worker PCSX2 override must be the exact ' +
            'work/<task title>/pcsx2/pcsx2-qt.exe and keep existing instances.'
        )
    }
    $candidate
}

if (-not $KeepExistingInstance) {
    Stop-Na2Pcsx2 -Executable $resolvedPcsx2Exe
    $pcsx2Ini = [IO.Path]::GetFullPath($projectPaths.files.pcsx2_user_ini)
    if (-not (Test-Path -LiteralPath $pcsx2Ini -PathType Leaf)) {
        throw "PCSX2 configuration does not exist: $pcsx2Ini"
    }
    $iniText = [IO.File]::ReadAllText($pcsx2Ini)
    $runningIniText = Set-Na2IniValue `
        -Text $iniText `
        -Section 'UI' `
        -Key 'StartPaused' `
        -Value 'false'
    if ($runningIniText -cne $iniText) {
        [IO.File]::WriteAllText(
            $pcsx2Ini,
            $runningIniText,
            [Text.UTF8Encoding]::new($false)
        )
    }
}

if (-not (Test-Path -LiteralPath $resolvedIso -PathType Leaf)) {
    throw "ISO does not exist: $resolvedIso"
}
if (-not (Test-Path -LiteralPath $resolvedPcsx2Exe -PathType Leaf)) {
    throw "PCSX2 executable does not exist: $resolvedPcsx2Exe"
}

$startArguments = @{
    FilePath = $resolvedPcsx2Exe
    WorkingDirectory = [IO.Path]::GetDirectoryName($resolvedPcsx2Exe)
    ArgumentList = @('-batch', "`"$resolvedIso`"")
}
if ($WindowStyle -ne 'Normal') {
    $startArguments.WindowStyle = $WindowStyle
}
if ($PassThru) {
    $startArguments.PassThru = $true
}
Start-Process @startArguments
