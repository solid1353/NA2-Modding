param(
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$CatalogArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$pythonRunner = Join-Path $repository 'scripts\lib\run_python.ps1'
$pythonScript = Join-Path $PSScriptRoot 'catalog.py'
$forwardedArguments = @(
    $CatalogArguments | Where-Object { -not [string]::IsNullOrEmpty($_) }
)

& $pythonRunner `
    -PackageSet builder `
    -Script $pythonScript `
    -ArgumentList $forwardedArguments `
    -NoBytecode
exit $LASTEXITCODE
