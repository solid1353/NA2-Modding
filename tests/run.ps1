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
$workspaceTempRoot = Join-Path $workspaceRoot 'temp'
$testTempParent = Join-Path $workspaceTempRoot 'tests'
$testTemp = Join-Path $testTempParent ("run-$PID-$([Guid]::NewGuid().ToString('N'))")
$originalTemp = [Environment]::GetEnvironmentVariable('TEMP', 'Process')
$originalTmp = [Environment]::GetEnvironmentVariable('TMP', 'Process')
$originalTestPowerShell = [Environment]::GetEnvironmentVariable(
    'NA228_TEST_POWERSHELL',
    'Process'
)
$workspaceTempExisted = Test-Path -LiteralPath $workspaceTempRoot -PathType Container

[void](New-Item -ItemType Directory -Path $testTemp -Force)
$env:TEMP = $testTemp
$env:TMP = $testTemp
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

    Remove-Item -LiteralPath $testTemp -Recurse -Force -ErrorAction SilentlyContinue
    if ((Test-Path -LiteralPath $testTempParent -PathType Container) -and
        @(Get-ChildItem -LiteralPath $testTempParent -Force).Count -eq 0) {
        Remove-Item -LiteralPath $testTempParent -Force
    }
    if (-not $workspaceTempExisted -and
        (Test-Path -LiteralPath $workspaceTempRoot -PathType Container) -and
        @(Get-ChildItem -LiteralPath $workspaceTempRoot -Force).Count -eq 0) {
        Remove-Item -LiteralPath $workspaceTempRoot -Force
    }
    if ($usesSharedTestRoot -and
        -not $workspaceExisted -and
        (Test-Path -LiteralPath $workspaceRoot -PathType Container) -and
        @(Get-ChildItem -LiteralPath $workspaceRoot -Force).Count -eq 0) {
        Remove-Item -LiteralPath $workspaceRoot -Force
    }
}

Write-Host 'All project tests passed.'
