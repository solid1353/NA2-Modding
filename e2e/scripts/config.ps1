Set-StrictMode -Version Latest

function Get-E2eConfiguration {
    [CmdletBinding()]
    param(
        [string]$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    )

    $configurationPath = Join-Path $Root 'config.json'
    if (-not (Test-Path -LiteralPath $configurationPath -PathType Leaf)) {
        throw "E2E configuration does not exist: $configurationPath"
    }
    try {
        $configuration = Get-Content -Raw -LiteralPath $configurationPath |
            ConvertFrom-Json
    }
    catch {
        throw "Invalid E2E configuration JSON: $configurationPath"
    }
    if ([int]$configuration.schema_version -ne 1) {
        throw "Unsupported E2E configuration schema: $($configuration.schema_version)"
    }
    $variants = @($configuration.build_variants)
    if ($variants.Count -lt 1) {
        throw 'E2E configuration requires at least one build variant.'
    }
    $names = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($variant in $variants) {
        $name = [string]$variant.name
        $build = [string]$variant.build
        $shift = [int]$variant.payload_shift_bytes
        $ignoredProperty = $variant.PSObject.Properties['ignored']
        if (
            [string]::IsNullOrWhiteSpace($name) -or
            $name -cnotmatch '^[a-z][a-z0-9_-]*$' -or
            -not $names.Add($name)
        ) {
            throw "Invalid or duplicate E2E build variant name: $name"
        }
        if ([string]::IsNullOrWhiteSpace($build) -or $build -cnotmatch '^[a-z][a-z0-9_]*$') {
            throw "Invalid E2E build selector for variant ${name}: $build"
        }
        if ($shift -lt 0 -or $shift -gt 65536 -or $shift % 16 -ne 0) {
            throw "Variant $name payload shift must be a 16-byte multiple through 65536."
        }
        if ($null -ne $ignoredProperty -and $ignoredProperty.Value -isnot [bool]) {
            throw "Variant $name ignored must be a boolean."
        }
    }
    $activeVariants = @(
        $variants | Where-Object {
            $null -eq $_.PSObject.Properties['ignored'] -or $_.ignored -eq $false
        }
    )
    if ($activeVariants.Count -lt 1) {
        throw 'E2E configuration has no active build variants.'
    }
    $published = @(
        $activeVariants | Where-Object {
            $null -ne $_.PSObject.Properties['publish'] -and
            $_.publish -eq $true
        }
    )
    if ($published.Count -ne 1) {
        throw 'E2E configuration requires exactly one published build variant.'
    }
    $publishedName = [string]$published[0].name
    $activeNames = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $activeNames.UnionWith([string[]]@($activeVariants.name))
    foreach ($variant in $activeVariants) {
        $comparison = if ($null -ne $variant.PSObject.Properties['compare_against']) {
            [string]$variant.compare_against
        }
        else {
            ''
        }
        if ([string]::IsNullOrWhiteSpace($comparison)) {
            if ([string]$variant.name -cne $publishedName) {
                throw "Variant $($variant.name) must declare compare_against."
            }
            continue
        }
        if (-not $activeNames.Contains($comparison) -or $comparison -ieq [string]$variant.name) {
            throw "Invalid compare_against target for variant $($variant.name): $comparison"
        }
    }
    return [pscustomobject]@{
        Path = $configurationPath
        Variants = $activeVariants
        AllVariants = $variants
        PublishedVariant = $published[0]
    }
}

function Get-E2eBuildVariant {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Name,
        [string]$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    )

    $configuration = Get-E2eConfiguration -Root $Root
    $matches = @(
        $configuration.AllVariants |
            Where-Object { [string]$_.name -ieq $Name }
    )
    if ($matches.Count -ne 1) {
        throw "Unknown E2E build variant: $Name"
    }
    return $matches[0]
}
