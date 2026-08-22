Set-StrictMode -Version Latest

function ConvertTo-E2eSuiteOverrides {
    param(
        [Parameter(Mandatory)][psobject]$Configuration,
        [Parameter(Mandatory)][string]$ConfigurationPath
    )

    $result = @{}
    $suiteOverridesProperty = $Configuration.PSObject.Properties['suite_overrides']
    if ($null -eq $suiteOverridesProperty) {
        return $result
    }
    if ($suiteOverridesProperty.Value -isnot [pscustomobject]) {
        throw "E2E suite_overrides must be an object: $ConfigurationPath"
    }

    foreach ($suiteProperty in $suiteOverridesProperty.Value.PSObject.Properties) {
        $suite = [string]$suiteProperty.Name
        $segments = [string[]]@($suite.Split('/'))
        if (
            [string]::IsNullOrWhiteSpace($suite) -or
            $suite.Contains('\') -or
            @($segments | Where-Object { $_ -cnotmatch '^[a-z0-9][a-z0-9_-]*$' }).Count -gt 0 -or
            $result.ContainsKey($suite)
        ) {
            throw "Invalid or duplicate E2E suite override name: $suite"
        }

        $override = $suiteProperty.Value
        if ($override -isnot [pscustomobject]) {
            throw "E2E suite override $suite must be an object."
        }
        foreach ($field in $override.PSObject.Properties) {
            if ([string]$field.Name -notin @('memory_card', 'launch_profile')) {
                throw "Unknown E2E suite override field for ${suite}: $($field.Name)"
            }
        }

        $memoryCard = $null
        $memoryCardProperty = $override.PSObject.Properties['memory_card']
        if ($null -ne $memoryCardProperty) {
            if ($memoryCardProperty.Value -isnot [string] -or
                [string]::IsNullOrWhiteSpace([string]$memoryCardProperty.Value)) {
                throw "E2E suite override $suite memory_card must be a nonblank string."
            }
            $memoryCard = [string]$memoryCardProperty.Value
        }

        $launchProfile = $null
        $launchProfileProperty = $override.PSObject.Properties['launch_profile']
        if ($null -ne $launchProfileProperty) {
            if ($launchProfileProperty.Value -isnot [pscustomobject]) {
                throw "E2E suite override $suite launch_profile must be an object."
            }
            foreach ($field in $launchProfileProperty.Value.PSObject.Properties) {
                if ([string]$field.Name -notin @('name', 'arguments')) {
                    throw (
                        "Unknown E2E launch_profile field for ${suite}: " +
                        [string]$field.Name
                    )
                }
            }
            $nameProperty = $launchProfileProperty.Value.PSObject.Properties['name']
            if ($null -eq $nameProperty -or
                $nameProperty.Value -isnot [string] -or
                [string]$nameProperty.Value -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]*$') {
                throw "E2E suite override $suite launch_profile requires a valid name."
            }
            $argumentsProperty = $launchProfileProperty.Value.PSObject.Properties['arguments']
            if ($null -eq $argumentsProperty -or $argumentsProperty.Value -isnot [array]) {
                throw "E2E suite override $suite launch_profile arguments must be an array."
            }
            $arguments = [string[]]@()
            foreach ($argument in @($argumentsProperty.Value)) {
                if ($argument -isnot [string]) {
                    throw (
                        "E2E suite override $suite launch_profile arguments " +
                        'must contain only strings.'
                    )
                }
                $arguments += [string]$argument
            }
            $launchProfile = [pscustomobject]@{
                Name = [string]$nameProperty.Value
                Arguments = $arguments
            }
        }

        if ($null -eq $memoryCard -and $null -eq $launchProfile) {
            throw "E2E suite override $suite must declare at least one setting."
        }
        $result[$suite] = [pscustomobject]@{
            MemoryCard = $memoryCard
            LaunchProfile = $launchProfile
        }
    }
    return $result
}

function Resolve-E2eSuiteSettings {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][psobject]$Configuration,
        [Parameter(Mandatory)][string]$Suite
    )

    $override = $Configuration.SuiteOverrides[$Suite]
    $memoryCard = [string]$Configuration.MemoryCard
    $launchProfile = $null
    if ($null -ne $override) {
        if (-not [string]::IsNullOrWhiteSpace([string]$override.MemoryCard)) {
            $memoryCard = [string]$override.MemoryCard
        }
        $launchProfile = $override.LaunchProfile
    }
    return [pscustomobject]@{
        MemoryCard = $memoryCard
        LaunchProfile = $launchProfile
    }
}

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
    $variantNames = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $variantNames.UnionWith([string[]]@($variants.name))
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
        if (-not $variantNames.Contains($comparison) -or $comparison -ieq [string]$variant.name) {
            throw "Invalid compare_against target for variant $($variant.name): $comparison"
        }
    }
    $memoryCardProperty = $configuration.PSObject.Properties['memory_card']
    if ($null -eq $memoryCardProperty -or
        $memoryCardProperty.Value -isnot [string] -or
        [string]::IsNullOrWhiteSpace([string]$memoryCardProperty.Value)) {
        throw "E2E configuration memory_card must be a nonblank string: $configurationPath"
    }
    $suiteOverrides = ConvertTo-E2eSuiteOverrides `
        -Configuration $configuration `
        -ConfigurationPath $configurationPath
    return [pscustomobject]@{
        Path = $configurationPath
        Variants = $variants
        PublishedVariant = $published[0]
        MemoryCard = [string]$memoryCardProperty.Value
        SuiteOverrides = $suiteOverrides
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
