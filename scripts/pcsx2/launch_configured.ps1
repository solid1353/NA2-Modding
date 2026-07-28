[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('user', 'dev')]
    [string]$Target,

    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

$executableFile = "pcsx2_${Target}_exe"
$workingDirectoryRoot = "pcsx2_$Target"
$executable = [IO.Path]::GetFullPath($projectPaths.files.$executableFile)
$workingDirectory = [IO.Path]::GetFullPath($projectPaths.$workingDirectoryRoot)

Push-Location $workingDirectory
try {
    & $executable @Arguments
}
finally {
    Pop-Location
}
