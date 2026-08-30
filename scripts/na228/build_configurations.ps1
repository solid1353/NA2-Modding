Set-StrictMode -Version Latest

function Get-Na2BuildConfigurations {
    [CmdletBinding()]
    param([Parameter(Mandatory)][psobject]$Paths)

    $configurationRoot = Join-Path ([string]$Paths.builder) 'configurations'
    $configurationFiles = @(
        Get-ChildItem -LiteralPath $configurationRoot -Filter '*.jsonc' -File |
            Sort-Object Name
    )
    if ($configurationFiles.Count -eq 0) {
        throw 'Project configurations must not be empty.'
    }

    $property = $Paths.settings.PSObject.Properties['configurations']
    if ($null -ne $property -and $property.Value -isnot [pscustomobject]) {
        throw 'Project configurations must be an object.'
    }

    $byName = [ordered]@{}
    $byAlias = [ordered]@{}
    $bySelector = [ordered]@{}
    foreach ($configurationFile in $configurationFiles) {
        $name = [IO.Path]::GetFileNameWithoutExtension($configurationFile.Name)
        if ($name -cnotmatch '^[a-z][a-z0-9_-]*$') {
            throw "Invalid build configuration name: $name"
        }
        $byName[$name] = [pscustomobject]@{
            Name = $name
            Alias = ''
            Path = [IO.Path]::GetFullPath($configurationFile.FullName)
        }
    }

    if ($null -ne $property) {
        foreach ($definition in $property.Value.PSObject.Properties) {
            $name = [string]$definition.Name
            $alias = [string]$definition.Value
            if (-not $byName.Contains($name)) {
                throw "Build configuration does not exist: $name"
            }
            if ($definition.Value -isnot [string] -or
                $alias -cnotmatch '^[a-z][a-z0-9_-]*$') {
                throw "Invalid alias for build configuration '$name'."
            }
            if ($byAlias.Contains($alias)) {
                throw "Duplicate build configuration selector: $alias"
            }
            $byName[$name].Alias = $alias
            $byAlias[$alias] = $name
            if ($bySelector.Contains($alias)) {
                throw "Duplicate build configuration selector: $alias"
            }
            $bySelector[$alias] = $name
        }
    }

    foreach ($configuration in $byName.Values) {
        if (-not [string]::IsNullOrWhiteSpace($configuration.Alias)) {
            continue
        }
        $selector = [string]$configuration.Name
        if ($bySelector.Contains($selector)) {
            throw "Duplicate build configuration selector: $selector"
        }
        $bySelector[$selector] = [string]$configuration.Name
    }

    $reservedSelectors = @('build', 'e2e', 'help', 'release', 'test', 'w', 'worker')
    foreach ($selector in $bySelector.Keys) {
        if ($selector -in $reservedSelectors) {
            throw "Build configuration selector conflicts with a command: $selector"
        }
        if ($null -ne $Paths.games.Aliases.PSObject.Properties[$selector]) {
            throw "Build configuration selector conflicts with a source: $selector"
        }
        foreach ($otherSelector in $bySelector.Keys) {
            if ($selector -ceq $otherSelector) {
                continue
            }
            if ($selector -ceq "b$otherSelector" -or
                $selector -ceq "${otherSelector}w" -or
                $selector -ceq "b${otherSelector}w") {
                throw "Conflicting build configuration selectors: $selector, $otherSelector"
            }
        }
    }

    return [pscustomobject]@{
        ByName = $byName
        ByAlias = $byAlias
        BySelector = $bySelector
        Names = [string[]]@($byName.Keys)
    }
}

function Resolve-Na2BuildConfiguration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Selector,
        [Parameter(Mandatory)][psobject]$Configurations
    )

    $key = $Selector.Trim().ToLowerInvariant()
    $name = $Configurations.BySelector[$key]
    if ([string]::IsNullOrWhiteSpace([string]$name)) {
        throw "Unknown build configuration: $Selector"
    }
    return $Configurations.ByName[[string]$name]
}
