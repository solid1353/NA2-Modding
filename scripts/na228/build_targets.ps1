Set-StrictMode -Version Latest

function Find-Na2BuildTarget {
    param(
        [Parameter(Mandatory)][Collections.IDictionary]$Targets,
        [Parameter(Mandatory)][string]$Name
    )

    foreach ($key in $Targets.Keys) {
        if ([string]$key -ieq $Name) {
            return $Targets[$key]
        }
    }
    return $null
}

function Get-Na2BuildTargetRegistry {
    [CmdletBinding()]
    param([Parameter(Mandatory)][psobject]$Paths)

    $definitions = $Paths.settings.PSObject.Properties['builds']
    if ($null -eq $definitions -or $definitions.Value -isnot [pscustomobject]) {
        throw 'Project builds must be an object.'
    }
    $targets = [ordered]@{}
    $rotationSources = [ordered]@{}
    foreach ($definition in $definitions.Value.PSObject.Properties) {
        $name = [string]$definition.Name
        $entry = $Paths.games.Entries.PSObject.Properties[$name]
        if ($null -eq $entry -or [string]$entry.Value.Category -cne 'builds') {
            throw "Build target '$name' has no resolved build entry."
        }
        $configurationProperty = $definition.Value.PSObject.Properties[
            'configuration'
        ]
        $configuration = if ($null -eq $configurationProperty) {
            $null
        }
        else {
            if ($configurationProperty.Value -isnot [string]) {
                throw "Build target '$name' has invalid configuration."
            }
            [string]$configurationProperty.Value
        }
        if ($null -ne $configuration) {
            if ($configuration -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]*$') {
                throw "Build target '$name' has invalid configuration: $configuration"
            }
            $configurationPath = Join-Path ([string]$Paths.builder) (
                "configurations\$configuration.json"
            )
            if (-not (Test-Path -LiteralPath $configurationPath -PathType Leaf)) {
                throw (
                    "Build target '$name' references a missing configuration: " +
                    $configuration
                )
            }
        }

        $rotationProperty = $definition.Value.PSObject.Properties['rotate_to']
        $rotateTo = if ($null -eq $rotationProperty) {
            $null
        }
        else {
            if ($rotationProperty.Value -isnot [string]) {
                throw "Build target '$name' has invalid rotate_to target."
            }
            [string]$rotationProperty.Value
        }
        if ($null -ne $rotateTo) {
            if ($rotateTo -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_]*$' -or
                $rotateTo -ieq $name) {
                throw "Build target '$name' has invalid rotate_to target: $rotateTo"
            }
            if ($rotationSources.Contains($rotateTo.ToLowerInvariant())) {
                throw "Multiple build targets rotate to '$rotateTo'."
            }
            $rotationSources[$rotateTo.ToLowerInvariant()] = $name
        }
        $targets[$name] = [pscustomobject]@{
            Name = $name
            Entry = $entry.Value
            Configuration = $configuration
            RotateTo = $rotateTo
        }
    }

    foreach ($target in $targets.Values) {
        if ($null -ne $target.RotateTo) {
            if ($null -eq $target.Configuration) {
                throw "Buildable target '$($target.Name)' requires a configuration."
            }
            $destination = Find-Na2BuildTarget `
                -Targets $targets `
                -Name $target.RotateTo
            if ($null -eq $destination) {
                throw (
                    "Build target '$($target.Name)' references an unknown " +
                    "rotate_to target: $($target.RotateTo)"
                )
            }
            if ($null -ne $destination.Configuration) {
                throw (
                    "Rotation target '$($destination.Name)' must not define " +
                    'a configuration.'
                )
            }
        }
        elseif ($null -eq $target.Configuration -and
            -not $rotationSources.Contains($target.Name.ToLowerInvariant())) {
            throw "Buildable target '$($target.Name)' requires a configuration."
        }
    }
    return $targets
}

function Get-Na2BuildTargetConfiguration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][psobject]$Paths
    )

    $targets = Get-Na2BuildTargetRegistry -Paths $Paths
    $target = Find-Na2BuildTarget -Targets $targets -Name $Name
    if ($null -eq $target) {
        throw "Unknown build target: $Name"
    }
    if ($null -ne $target.Configuration) {
        return [string]$target.Configuration
    }
    $source = @(
        $targets.Values | Where-Object { $_.RotateTo -ieq $target.Name }
    )
    if ($source.Count -ne 1 -or $null -eq $source[0].Configuration) {
        throw "Retained target '$($target.Name)' has no build configuration owner."
    }
    return [string]$source[0].Configuration
}
