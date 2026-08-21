param(
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$CatalogArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$pythonRunner = Join-Path ([string]$paths.scripts) 'lib\run_python.ps1'
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
