[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pythonRunner = Join-Path $repository 'scripts\lib\run_python.ps1'
$powershell = (Get-Process -Id $PID).Path
$taskWorkRoot = if ([string]::IsNullOrWhiteSpace($env:NA228_TASK_WORK_ROOT)) {
    Join-Path $repository 'work\General'
}
else {
    [IO.Path]::GetFullPath($env:NA228_TASK_WORK_ROOT)
}
$taskTempRoot = Join-Path $taskWorkRoot 'temp'
$testTempParent = Join-Path $taskTempRoot 'tests'
$testTemp = Join-Path $testTempParent ("run-$PID-$([Guid]::NewGuid().ToString('N'))")
$originalTemp = [Environment]::GetEnvironmentVariable('TEMP', 'Process')
$originalTmp = [Environment]::GetEnvironmentVariable('TMP', 'Process')
$taskTempExisted = Test-Path -LiteralPath $taskTempRoot -PathType Container

[void](New-Item -ItemType Directory -Path $testTemp -Force)
$env:TEMP = $testTemp
$env:TMP = $testTemp

Push-Location $repository
try {
    & $powershell -NoProfile -File $pythonRunner `
        -PackageSet builder `
        -Script (Join-Path $PSScriptRoot 'run.py') `
        -NoBytecode
    if ($LASTEXITCODE -ne 0) {
        throw "Python tests failed with exit code $LASTEXITCODE."
    }

    $powershellTests = @(
        Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File -Filter 'test_*.ps1' |
            Sort-Object FullName
    )
    foreach ($test in $powershellTests) {
        Write-Host "[tests] $([IO.Path]::GetRelativePath($repository, $test.FullName))"
        & $test.FullName
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

    Remove-Item -LiteralPath $testTemp -Recurse -Force -ErrorAction SilentlyContinue
    if ((Test-Path -LiteralPath $testTempParent -PathType Container) -and
        @(Get-ChildItem -LiteralPath $testTempParent -Force).Count -eq 0) {
        Remove-Item -LiteralPath $testTempParent -Force
    }
    if (-not $taskTempExisted -and
        (Test-Path -LiteralPath $taskTempRoot -PathType Container) -and
        @(Get-ChildItem -LiteralPath $taskTempRoot -Force).Count -eq 0) {
        Remove-Item -LiteralPath $taskTempRoot -Force
    }
}

Write-Host 'All project tests passed.'
