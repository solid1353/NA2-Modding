[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$IsoPath,
    [ValidateSet('Normal', 'Minimized', 'Hidden')]
    [string]$WindowStyle = 'Normal',
    [switch]$KeepExistingInstance,
    [switch]$PassThru
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\run_log.ps1')
. (Join-Path $PSScriptRoot 'ini.ps1')
. (Join-Path $PSScriptRoot 'process.ps1')
$projectPaths = Get-Na2ProjectPaths

$resolvedIso = if ([IO.Path]::IsPathRooted($IsoPath)) {
    [IO.Path]::GetFullPath($IsoPath)
}
else {
    [IO.Path]::GetFullPath((Join-Path $projectPaths.repository $IsoPath))
}
$resolvedPcsx2Exe = [IO.Path]::GetFullPath($projectPaths.files.pcsx2_exe)

if (-not $KeepExistingInstance) {
    Stop-Na2Pcsx2 -Executable $resolvedPcsx2Exe
    $pcsx2Ini = [IO.Path]::GetFullPath($projectPaths.files.pcsx2_ini)
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
    ArgumentList = @('-batch', "`"$resolvedIso`"")
}
if ($WindowStyle -ne 'Normal') {
    $startArguments.WindowStyle = $WindowStyle
}
if ($PassThru) {
    $startArguments.PassThru = $true
}
Start-Process @startArguments
