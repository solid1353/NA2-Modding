param(
    [Parameter(Mandatory)]
    [ValidateRange(1, 65535)]
    [int]$Port,

    [Parameter(ValueFromRemainingArguments)]
    [string[]]$CommandArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$pythonRunner = Join-Path $repository 'scripts\lib\run_python.ps1'
$pythonScript = Join-Path $PSScriptRoot 'agent_lab.py'
$pythonArguments = @('--port', [string]$Port) + @($CommandArguments)

& $pythonRunner `
    -PackageSet builder `
    -Script $pythonScript `
    -ArgumentList $pythonArguments `
    -NoBytecode
exit $LASTEXITCODE
