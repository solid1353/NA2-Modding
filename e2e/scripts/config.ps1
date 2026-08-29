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
    $configurationProperty = $configuration.PSObject.Properties['configuration']
    if ($null -eq $configurationProperty -or
        $configurationProperty.Value -isnot [string] -or
        [string]$configurationProperty.Value -cnotmatch '^[a-z][a-z0-9_-]*$') {
        throw "E2E requires a valid build configuration: $configurationPath"
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
        Configuration = [string]$configurationProperty.Value
        MemoryCard = [string]$memoryCardProperty.Value
        SuiteOverrides = $suiteOverrides
    }
}
