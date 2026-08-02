[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$IsoPath,

    [Parameter(Mandatory = $true)]
    [string]$BuildRecordDirectory,

    [Parameter(Mandatory = $true)]
    [string]$BootElf,

    [Parameter(Mandatory = $true)]
    [string]$Serial,

    [Parameter(Mandatory = $true)]
    [string]$Crc,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [string]$RequiredSymbols = ''
)

$ErrorActionPreference = 'Stop'
$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$arguments = @(
    '--iso', [IO.Path]::GetFullPath($IsoPath),
    '--build-record', [IO.Path]::GetFullPath($BuildRecordDirectory),
    '--boot-elf', $BootElf,
    '--serial', $Serial,
    '--crc', $Crc,
    '--output', [IO.Path]::GetFullPath($OutputPath)
)
foreach ($symbol in @(
    $RequiredSymbols -split ';' |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
)) {
    $arguments += @('--required-symbol', $symbol)
}

& (Join-Path $repository 'scripts\lib\run_python.ps1') `
    -PackageSet builder `
    -Script (Join-Path $PSScriptRoot 'verify_font_replay_bundle.py') `
    -ArgumentList $arguments `
    -NoBytecode
