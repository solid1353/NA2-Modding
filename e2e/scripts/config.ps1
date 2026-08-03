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
    if ($variants.Count -lt 2) {
        throw 'E2E configuration requires at least two build variants.'
    }
    $names = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($variant in $variants) {
        $name = [string]$variant.name
        $build = [string]$variant.build
        $padding = [int]$variant.payload_padding_bytes
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
        if ($padding -lt 0 -or $padding -gt 65536 -or $padding % 16 -ne 0) {
            throw "Variant $name payload padding must be a 16-byte multiple through 65536."
        }
    }
    $published = @(
        $variants | Where-Object {
            $null -ne $_.PSObject.Properties['publish'] -and
            $_.publish -eq $true
        }
    )
    if ($published.Count -ne 1) {
        throw 'E2E configuration requires exactly one published build variant.'
    }
    $publishedName = [string]$published[0].name
    foreach ($variant in $variants) {
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
        if (-not $names.Contains($comparison) -or $comparison -ieq [string]$variant.name) {
            throw "Invalid compare_against target for variant $($variant.name): $comparison"
        }
    }
    return [pscustomobject]@{
        Path = $configurationPath
        Variants = $variants
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
        $configuration.Variants |
            Where-Object { [string]$_.name -ieq $Name }
    )
    if ($matches.Count -ne 1) {
        throw "Unknown E2E build variant: $Name"
    }
    return $matches[0]
}
