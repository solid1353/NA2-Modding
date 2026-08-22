[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$pythonRunner = Join-Path ([string]$paths.scripts) 'lib\run_python.ps1'
$powershell = (Get-Process -Id $PID).Path
$usesSharedTestRoot = [string]::IsNullOrWhiteSpace($env:NA228_TASK_WORK_ROOT)
$workspaceRoot = if ($usesSharedTestRoot) {
    [string]$paths.work
}
else {
    [IO.Path]::GetFullPath($env:NA228_TASK_WORK_ROOT)
}
$workspaceExisted = Test-Path -LiteralPath $workspaceRoot -PathType Container
$unitTestRoot = Join-Path $workspaceRoot 'unit-tests'
$unitTestRunRoot = Join-Path $unitTestRoot ("run-$PID-$([Guid]::NewGuid().ToString('N'))")
$originalTemp = [Environment]::GetEnvironmentVariable('TEMP', 'Process')
$originalTmp = [Environment]::GetEnvironmentVariable('TMP', 'Process')
$originalTestPowerShell = [Environment]::GetEnvironmentVariable(
    'NA228_TEST_POWERSHELL',
    'Process'
)

[void](New-Item -ItemType Directory -Path $unitTestRunRoot -Force)
$env:TEMP = $unitTestRunRoot
$env:TMP = $unitTestRunRoot
$env:NA228_TEST_POWERSHELL = $powershell

Push-Location $repository
try {
    & $powershell -NoProfile -File $pythonRunner `
        -PackageSet builder `
        -Script (Join-Path $PSScriptRoot 'run.py') `
        -NoBytecode
    if ($LASTEXITCODE -ne 0) {
        throw "Unit tests failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
    if ($null -eq $originalTemp) {
        Remove-Item Env:TEMP -ErrorAction SilentlyContinue
    }
    else {
        $env:TEMP = $originalTemp
    }
    if ($null -eq $originalTmp) {
        Remove-Item Env:TMP -ErrorAction SilentlyContinue
    }
    else {
        $env:TMP = $originalTmp
    }
    if ($null -eq $originalTestPowerShell) {
        Remove-Item Env:NA228_TEST_POWERSHELL -ErrorAction SilentlyContinue
    }
    else {
        $env:NA228_TEST_POWERSHELL = $originalTestPowerShell
    }

    if (Test-Path -LiteralPath $unitTestRunRoot -PathType Container) {
        Remove-Item -LiteralPath $unitTestRunRoot -Recurse -Force
    }
    if ((Test-Path -LiteralPath $unitTestRoot -PathType Container) -and
        @(Get-ChildItem -LiteralPath $unitTestRoot -Force).Count -eq 0) {
        Remove-Item -LiteralPath $unitTestRoot -Force
    }
    if ($usesSharedTestRoot -and
        -not $workspaceExisted -and
        (Test-Path -LiteralPath $workspaceRoot -PathType Container) -and
        @(Get-ChildItem -LiteralPath $workspaceRoot -Force).Count -eq 0) {
        Remove-Item -LiteralPath $workspaceRoot -Force
    }
}

Write-Host 'All project tests passed.'
