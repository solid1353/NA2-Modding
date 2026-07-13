<#
.SYNOPSIS
Builds and/or launches an NA2 test ISO from explicitly selected package sources.
#>
param(
    [Alias('i')]
    [string]$InputIso,
    [Alias('o')]
    [string]$OutputIso,
    [Alias('d')]
    [string]$PackageDirectory,
    [string]$TranslationTsv,
    [Alias('e')]
    [string]$Pcsx2Exe,
    [Alias('p')]
    [string[]]$Packages,
    [Alias('b')]
    [switch]$BuildOnly,
    [Alias('r')]
    [switch]$RunOnly,
    [Alias('h')]
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    $scriptName = $MyInvocation.MyCommand.Name
    @(
        "Usage: $scriptName -Packages SOURCE[,SOURCE...] -i INPUT.iso -o OUTPUT.iso -d PACKAGE_DIR -e PCSX2.exe"
        "       $scriptName -b -Packages SOURCE[,SOURCE...] -i INPUT.iso -o OUTPUT.iso -d PACKAGE_DIR"
        "       $scriptName -r -o OUTPUT.iso -e PCSX2.exe"
        "       $scriptName -h"
        ''
        'Package-source selection:'
        '  -Packages, -p SOURCE[,SOURCE...]'
        '      Non-Translation sources select the newest NA2_APPLY__<SOURCE>__*.zip.'
        '      Examples:'
        '        -Packages Translation'
        '        -Packages Font'
        '        -Packages Translation,Font'
        '      Translation selects the newest NA2_APPLY__TRANSLATION__*.tsv.'
        '      Source names and package filename matching are case-insensitive.'
        '      Source names are generic and are not hard-coded in this script.'
        ''
        'Build behavior:'
        '  At least one package source is required for a build.'
        '  Every build validates all selected ZIP packages and the translation TSV,'
        '  recreates the output from a complete source ISO copy, applies ZIP packages,'
        '  then applies the translation TSV last.'
        '  Package source names control selection only; package contents may target'
        '  any valid source-ISO files. ZIP-to-ZIP path overlap is rejected.'
        '  Selected packages are applied in the exact order provided.'
        ''
        'Modes:'
        '  (none)          Build from selected sources, then run'
        '  -b, -BuildOnly  Build from selected sources; do not run'
        '  -r, -RunOnly    Run the existing output ISO without rebuilding'
        '  -h, -Help       Show this help'
    ) -join [Environment]::NewLine | Write-Output
    return
}

if ($BuildOnly -and $RunOnly) {
    throw '-b and -r cannot be used together.'
}

if (-not $OutputIso) {
    throw 'Required argument missing: -o / -OutputIso'
}

$selectedPackages = @($Packages | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })

if ($RunOnly -and $selectedPackages.Count -gt 0) {
    throw '-Packages does not apply to -r / -RunOnly.'
}

if (-not $RunOnly) {
    if ($selectedPackages.Count -eq 0) {
        throw 'Select at least one package with -Packages or -p.'
    }
    if (-not $InputIso) {
        throw 'Required argument missing: -i / -InputIso'
    }
    if (-not $PackageDirectory) {
        throw 'Required argument missing: -d / -PackageDirectory'
    }

    $arguments = @(
        (Join-Path $PSScriptRoot 'apply_latest_na2.py')
        '--source', $InputIso
        '--output', $OutputIso
        '--downloads', $PackageDirectory
    )
    foreach ($package in $selectedPackages) {
        $arguments += @('--package', $package)
    }
    if (-not [string]::IsNullOrWhiteSpace($TranslationTsv)) {
        $arguments += @('--translation-tsv', $TranslationTsv)
    }

    & python -B @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "NA2 ISO build failed (exit $LASTEXITCODE)."
    }
}

if (-not $BuildOnly) {
    if (-not $Pcsx2Exe) {
        throw 'Required argument missing: -e / -Pcsx2Exe'
    }
    if (-not (Test-Path -LiteralPath $OutputIso -PathType Leaf)) {
        throw "ISO does not exist: $OutputIso"
    }
    if (-not (Test-Path -LiteralPath $Pcsx2Exe -PathType Leaf)) {
        throw "PCSX2 executable does not exist: $Pcsx2Exe"
    }

    Start-Process -FilePath $Pcsx2Exe -ArgumentList @('-batch', "`"$OutputIso`"")
}