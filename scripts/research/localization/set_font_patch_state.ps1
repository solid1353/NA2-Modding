[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [ValidateSet('GlobalOnly', 'AllEnabled')]
    [string]$Preset,

    [string[]]$EnablePatch = @(),

    [string[]]$DisablePatch = @()
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$tables = @(
    Join-Path $repositoryRoot 'na228_builder\features\localization\runtime_injector\patches.tsv'
    Join-Path $repositoryRoot 'na228_builder\features\localization\binary_patcher\patches.tsv'
)
$globalPatchIds = [Collections.Generic.HashSet[string]]::new(
    [string[]]@(
        'font_glyphs_native'
        'font_glyphs_metrics'
        'font_layout_core'
        'font_layout_global_selected_style'
    ),
    [StringComparer]::Ordinal
)
$enableIds = [Collections.Generic.HashSet[string]]::new(
    [string[]]$EnablePatch,
    [StringComparer]::Ordinal
)
$disableIds = [Collections.Generic.HashSet[string]]::new(
    [string[]]$DisablePatch,
    [StringComparer]::Ordinal
)

foreach ($patchId in $enableIds) {
    if ($disableIds.Contains($patchId)) {
        throw "Patch cannot be both enabled and disabled: $patchId"
    }
}

$knownFontIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$pendingWrites = [Collections.Generic.List[object]]::new()

foreach ($table in $tables) {
    $originalText = [IO.File]::ReadAllText($table)
    $newline = if ($originalText.Contains("`r`n")) { "`r`n" } else { "`n" }
    $lines = [IO.File]::ReadAllLines($table)
    if ($lines.Count -lt 2) {
        throw "Patch table is empty: $table"
    }

    $header = $lines[0].Split("`t")
    if ($header.Count -lt 3 -or $header[0] -cne 'patch_id' -or $header[2] -cne 'enabled') {
        throw "Unexpected patch-table schema: $table"
    }

    $changed = $false
    for ($index = 1; $index -lt $lines.Count; $index++) {
        if ([string]::IsNullOrWhiteSpace($lines[$index])) {
            continue
        }

        $columns = $lines[$index].Split("`t")
        if ($columns.Count -ne $header.Count) {
            throw "Malformed row $($index + 1) in $table"
        }

        $patchId = $columns[0]
        if (-not $patchId.StartsWith('font_', [StringComparison]::Ordinal)) {
            continue
        }

        [void]$knownFontIds.Add($patchId)
        $enabled = switch ($Preset) {
            'GlobalOnly' { $globalPatchIds.Contains($patchId) }
            'AllEnabled' { $true }
        }
        if ($enableIds.Contains($patchId)) {
            $enabled = $true
        }
        if ($disableIds.Contains($patchId)) {
            $enabled = $false
        }

        $newValue = if ($enabled) { '1' } else { '0' }
        if ($columns[2] -cne $newValue) {
            $columns[2] = $newValue
            $lines[$index] = $columns -join "`t"
            $changed = $true
        }
    }

    $pendingWrites.Add([pscustomobject]@{
        Path = $table
        Lines = $lines
        Newline = $newline
        Changed = $changed
    })
}

foreach ($requestedId in @($enableIds) + @($disableIds)) {
    if (-not $knownFontIds.Contains($requestedId)) {
        throw "Unknown Font patch ID: $requestedId"
    }
}

foreach ($write in $pendingWrites) {
    if (-not $write.Changed) {
        continue
    }
    if (-not $PSCmdlet.ShouldProcess($write.Path, "Apply Font patch preset $Preset")) {
        continue
    }

    $temporaryPath = "$($write.Path).font3.tmp"
    try {
        [IO.File]::WriteAllText(
            $temporaryPath,
            (($write.Lines -join $write.Newline) + $write.Newline),
            [Text.UTF8Encoding]::new($false)
        )
        Move-Item -LiteralPath $temporaryPath -Destination $write.Path -Force
    }
    finally {
        if (Test-Path -LiteralPath $temporaryPath) {
            Remove-Item -LiteralPath $temporaryPath -Force
        }
    }
}

$effective = foreach ($table in $tables) {
    Import-Csv -LiteralPath $table -Delimiter "`t" |
        Where-Object { $_.patch_id.StartsWith('font_', [StringComparison]::Ordinal) } |
        Select-Object @{Name = 'table'; Expression = { Split-Path -Leaf (Split-Path -Parent $table) }}, patch_id, enabled
}

$effective |
    Sort-Object table, patch_id |
    Format-Table -AutoSize
