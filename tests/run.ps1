[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pythonRunner = Join-Path $repository 'scripts\lib\run_python.ps1'
$powershell = (Get-Process -Id $PID).Path

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
}

Write-Host 'All project tests passed.'
