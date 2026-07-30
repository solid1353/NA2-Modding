[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Mode,

    [Parameter(Position = 1)]
    [string]$Version,

    [Alias('b')]
    [switch]$Build,
    [Alias('t')]
    [switch]$Test,
    [Alias('c')]
    [switch]$Current,
    [Alias('p')]
    [switch]$Previous,
    [Alias('w')]
    [switch]$Watch,
    [Alias('h')]
    [switch]$Help
)

$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'scripts\na228\command.ps1') @PSBoundParameters
