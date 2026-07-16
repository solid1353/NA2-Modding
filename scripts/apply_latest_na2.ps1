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
    [string]$Profile,
    [string]$ProfileLogDirectory,
    [string]$TranslationTsv,
    [string]$RawPatchPackage,
    [string[]]$RawPatches,
    [string[]]$RawRoots,
    [switch]$RawDefaults,
    [string]$RawLogDirectory,
    [switch]$AllowSizeChanges,
    [Alias('e')]
    [string]$Pcsx2Exe,
    [Alias('p')]
    [string[]]$Packages,
    [Alias('b')]
    [switch]$BuildOnly,
    [Alias('r')]
    [switch]$RunOnly,
    [switch]$SkipActualize,
    [Alias('h')]
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

function Stop-PortablePcsx2 {
    $portableExe = if ($Pcsx2Exe) {
        $Pcsx2Exe
    } else {
        Join-Path (Split-Path $PSScriptRoot -Parent) 'pcsx2\pcsx2-qt.exe'
    }

    $processName = [System.IO.Path]::GetFileNameWithoutExtension($portableExe)
    Stop-Process -Name $processName -Force -ErrorAction SilentlyContinue
}

function Promote-VerifiedIso {
    param([Parameter(Mandatory = $true)][string]$CurrentIso)

    $current = [System.IO.Path]::GetFullPath($CurrentIso)
    $candidate = "$current.building"
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Verified staged ISO does not exist: $candidate"
    }

    $directory = [System.IO.Path]::GetDirectoryName($current)
    $isStandardCurrent = [System.IO.Path]::GetFileName($current) -ieq 'Current.iso'
    $previous = if ($isStandardCurrent) { Join-Path $directory 'Previous.iso' } else { $null }
    $rotatedCurrent = $false

    try {
        if ($previous -and (Test-Path -LiteralPath $current -PathType Leaf)) {
            [System.IO.File]::Move($current, $previous, $true)
            $rotatedCurrent = $true
        }
        [System.IO.File]::Move($candidate, $current, $true)
    }
    catch {
        if ($rotatedCurrent -and
            -not (Test-Path -LiteralPath $current) -and
            (Test-Path -LiteralPath $previous -PathType Leaf)) {
            [System.IO.File]::Move($previous, $current, $true)
        }
        throw
    }
    finally {
        if (Test-Path -LiteralPath $candidate) {
            Remove-Item -Force -LiteralPath $candidate
        }
    }
}

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
        '  Optional raw patch composition runs after ZIP packages and before Translation.'
        '  File-size changes are rejected unless -AllowSizeChanges is explicitly supplied.'
        '  Use -RawPatchPackage with -RawDefaults or -RawPatches, plus -RawRoots and'
        '  a new task-specific -RawLogDirectory.'
        '  Preferred: use -Profile with a pinned modular profile directory and a new'
        '  task-specific -ProfileLogDirectory. Profile mode rejects legacy package options.'
        '  A verified Current.iso.building is promoted only after PCSX2 is closed:'
        '  Current.iso replaces Previous.iso, then the candidate becomes Current.iso.'
        ''
        'Modes:'
        '  (none)          Build from selected sources, then run'
        '  -b, -BuildOnly  Build from selected sources; do not run'
        '  -r, -RunOnly    Run the existing output ISO without rebuilding'
        '  -SkipActualize  Explicit no-PNACH isolation mode; otherwise actualize before handoff/launch'
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

$workspaceRoot = Split-Path $PSScriptRoot -Parent
$resolvedOutputIso = if ([System.IO.Path]::IsPathRooted($OutputIso)) {
    [System.IO.Path]::GetFullPath($OutputIso)
}
else {
    [System.IO.Path]::GetFullPath((Join-Path $workspaceRoot $OutputIso))
}

$selectedPackages = @($Packages | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
$profileSelected = -not [string]::IsNullOrWhiteSpace($Profile)

if ($RunOnly -and $selectedPackages.Count -gt 0) {
    throw '-Packages does not apply to -r / -RunOnly.'
}
if ($RunOnly -and $profileSelected) {
    throw '-Profile does not apply to -r / -RunOnly.'
}

if (-not $RunOnly) {
    # Required before any rebuild, and repeated immediately before promotion.
    Stop-PortablePcsx2
    if (-not $profileSelected -and $selectedPackages.Count -eq 0) {
        throw 'Select at least one package with -Packages or -p.'
    }
    if (-not $InputIso) {
        throw 'Required argument missing: -i / -InputIso'
    }
    if (-not $profileSelected -and -not $PackageDirectory) {
        throw 'Required argument missing: -d / -PackageDirectory'
    }
    if ($profileSelected -and [string]::IsNullOrWhiteSpace($ProfileLogDirectory)) {
        throw '-ProfileLogDirectory is required with -Profile.'
    }
    if ($profileSelected -and ($selectedPackages.Count -gt 0 -or $PackageDirectory -or $TranslationTsv -or $RawPatchPackage)) {
        throw '-Profile cannot be combined with legacy package/raw/translation options.'
    }

    $arguments = @(
        (Join-Path $PSScriptRoot 'apply_latest_na2.py')
        '--workspace', $workspaceRoot
        '--source', $InputIso
        '--output', $OutputIso
        '--stage-only'
    )
    if ($AllowSizeChanges) {
        $arguments += '--allow-size-changes'
    }
    if ($profileSelected) {
        $arguments += @('--profile', $Profile, '--profile-log-directory', $ProfileLogDirectory)
    }
    else {
        $arguments += @('--package-directory', $PackageDirectory)
        foreach ($package in $selectedPackages) {
            $arguments += @('--package', $package)
        }
        if (-not [string]::IsNullOrWhiteSpace($TranslationTsv)) {
            $arguments += @('--translation-tsv', $TranslationTsv)
        }
        if (-not [string]::IsNullOrWhiteSpace($RawPatchPackage)) {
            $arguments += @('--raw-patch-package', $RawPatchPackage)
            foreach ($root in @($RawRoots | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })) {
                $arguments += @('--raw-root', $root)
            }
            foreach ($patch in @($RawPatches | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })) {
                $arguments += @('--raw-patch', $patch)
            }
            if ($RawDefaults) {
                $arguments += '--raw-defaults'
            }
            if (-not [string]::IsNullOrWhiteSpace($RawLogDirectory)) {
                $arguments += @('--raw-log-directory', $RawLogDirectory)
            }
        }
    }

    $candidateIso = "${resolvedOutputIso}.building"
    try {
        & python -B @arguments
        if ($LASTEXITCODE -ne 0) {
            throw "NA2 ISO build failed (exit $LASTEXITCODE)."
        }

        Stop-PortablePcsx2
        Promote-VerifiedIso -CurrentIso $resolvedOutputIso
    }
    finally {
        if (Test-Path -LiteralPath $candidateIso) {
            Remove-Item -Force -LiteralPath $candidateIso
        }
    }
}
else {
    Stop-PortablePcsx2
}

if (-not (Test-Path -LiteralPath $resolvedOutputIso -PathType Leaf)) {
    throw "ISO does not exist: $resolvedOutputIso"
}

if (-not $SkipActualize) {
    $global:LASTEXITCODE = 0
    try {
        & (Join-Path $PSScriptRoot 'actualize_cheats_for_build_iso.ps1') -IsoPath $resolvedOutputIso
    }
    catch {
        throw "PNACH actualization failed: $($_.Exception.Message)"
    }
    if ($LASTEXITCODE -ne 0) {
        throw "PNACH actualization failed (exit $LASTEXITCODE)."
    }
}

if (-not $BuildOnly) {
    if (-not $Pcsx2Exe) {
        throw 'Required argument missing: -e / -Pcsx2Exe'
    }
    if (-not (Test-Path -LiteralPath $Pcsx2Exe -PathType Leaf)) {
        throw "PCSX2 executable does not exist: $Pcsx2Exe"
    }

    Start-Process -FilePath $Pcsx2Exe -ArgumentList @('-batch', "`"$resolvedOutputIso`"")
}
