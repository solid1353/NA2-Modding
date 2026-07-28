[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

$executable = [IO.Path]::GetFullPath($projectPaths.files.pcsx2_dev_exe)
$workingDirectory = [IO.Path]::GetFullPath($projectPaths.pcsx2_dev)

Push-Location $workingDirectory
try {
    & $executable @Arguments
}
finally {
    Pop-Location
}
