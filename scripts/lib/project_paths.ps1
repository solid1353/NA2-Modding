Set-StrictMode -Version Latest

function Get-Na2ProjectPaths {
    [CmdletBinding()]
    param(
        [string]$ManifestPath = (Join-Path $PSScriptRoot '..\..\project-paths.json'),
        [switch]$AllowMissing
    )

    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw "Project path manifest not found: $ManifestPath"
    }

    $manifestItem = Get-Item -LiteralPath $ManifestPath
    $repositoryRoot = $manifestItem.Directory.FullName
    $manifest = Get-Content -Raw -LiteralPath $manifestItem.FullName | ConvertFrom-Json
    if ([int]$manifest.schema_version -ne 1) {
        throw "Unsupported project path manifest schema: $($manifest.schema_version)"
    }

    $resolved = [ordered]@{
        ManifestPath = $manifestItem.FullName
    }
    $names = @($manifest.roots.PSObject.Properties.Name)
    if ($names.Count -eq 0) {
        throw 'Project path manifest has no roots.'
    }
    $deferredRoots = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::Ordinal
    )
    if ($null -ne $manifest.PSObject.Properties['existence_deferred_roots']) {
        foreach ($name in @($manifest.existence_deferred_roots)) {
            if ($name -isnot [string] -or
                [string]::IsNullOrWhiteSpace($name) -or
                $name -notin $names) {
                throw "Invalid existence-deferred project root: $name"
            }
            [void]$deferredRoots.Add($name)
        }
    }

    $pending = [Collections.Generic.List[string]]::new()
    foreach ($name in $names) { $pending.Add($name) }
    while ($pending.Count -gt 0) {
        $madeProgress = $false
        foreach ($name in @($pending)) {
            $value = [string]$manifest.roots.$name
            if ([string]::IsNullOrWhiteSpace($value) -or [IO.Path]::IsPathRooted($value)) {
                throw "Project root '$name' must be a non-empty repository-relative path or @root path: $value"
            }

            $basePath = $repositoryRoot
            $relativePath = $value
            if ($value.StartsWith('@')) {
                $aliasMatch = [regex]::Match($value, '^@(?<root>[^/\\]+)(?:[/\\](?<child>.*))?$')
                if (-not $aliasMatch.Success) {
                    throw "Project root '$name' has an invalid root alias: $value"
                }
                $parentName = $aliasMatch.Groups['root'].Value
                if ($parentName -notin $names) {
                    throw "Project root '$name' references unknown project root '$parentName': $value"
                }
                if (-not $resolved.Contains($parentName)) { continue }
                if ($deferredRoots.Contains($parentName)) {
                    [void]$deferredRoots.Add($name)
                }
                $basePath = [string]$resolved[$parentName]
                $relativePath = $aliasMatch.Groups['child'].Value
            }

            $path = if ([string]::IsNullOrEmpty($relativePath)) {
                [IO.Path]::GetFullPath($basePath)
            }
            else {
                [IO.Path]::GetFullPath((Join-Path $basePath $relativePath))
            }
            $basePrefix = $basePath.TrimEnd(
                [IO.Path]::DirectorySeparatorChar,
                [IO.Path]::AltDirectorySeparatorChar
            ) + [IO.Path]::DirectorySeparatorChar
            if ($value.StartsWith('@') -and
                -not [IO.Path]::Equals($path, $basePath) -and
                -not $path.StartsWith($basePrefix, [StringComparison]::OrdinalIgnoreCase)) {
                throw "Project root '$name' must remain within '$parentName': $value"
            }
            if (-not $AllowMissing -and
                -not $deferredRoots.Contains($name) -and
                -not (Test-Path -LiteralPath $path)) {
                throw "Configured project root '$name' does not exist: $path"
            }
            $resolved[$name] = $path
            [void]$pending.Remove($name)
            $madeProgress = $true
        }
        if (-not $madeProgress) {
            throw "Project root aliases contain a dependency cycle: $($pending -join ', ')"
        }
    }

    $configuredFiles = $manifest.files
    if ($null -eq $configuredFiles) {
        throw 'Project path manifest has no files.'
    }
    $fileNames = @($configuredFiles.PSObject.Properties.Name)
    if ($fileNames.Count -eq 0) {
        throw 'Project path manifest has no files.'
    }
    $resolvedFiles = [ordered]@{}
    foreach ($name in $fileNames) {
        $value = [string]$configuredFiles.$name
        if ([string]::IsNullOrWhiteSpace($value) -or [IO.Path]::IsPathRooted($value)) {
            throw "Project file '$name' must be a non-empty repository-relative path or @root path: $value"
        }

        $basePath = $repositoryRoot
        $relativePath = $value
        if ($value.StartsWith('@')) {
            $aliasMatch = [regex]::Match($value, '^@(?<root>[^/\\]+)[/\\](?<child>.+)$')
            if (-not $aliasMatch.Success) {
                throw "Project file '$name' has an invalid root alias: $value"
            }

            $rootName = $aliasMatch.Groups['root'].Value
            if (-not $resolved.Contains($rootName)) {
                throw "Project file '$name' references unknown project root '$rootName': $value"
            }

            $basePath = [string]$resolved[$rootName]
            $relativePath = $aliasMatch.Groups['child'].Value
            if ([IO.Path]::IsPathRooted($relativePath)) {
                throw "Project file '$name' has an invalid root-relative path: $value"
            }
        }

        $path = [IO.Path]::GetFullPath((Join-Path $basePath $relativePath))
        $basePrefix = $basePath.TrimEnd(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        ) + [IO.Path]::DirectorySeparatorChar
        if ($value.StartsWith('@') -and
            -not $path.StartsWith($basePrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Project file '$name' must remain within its configured root: $value"
        }

        $repositoryPrefix = $repositoryRoot.TrimEnd(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        ) + [IO.Path]::DirectorySeparatorChar
        if (-not $value.StartsWith('@') -and
            -not $path.StartsWith($repositoryPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Project file '$name' must remain within the repository: $value"
        }
        $resolvedFiles[$name] = $path
    }

    $resolvedGames = [ordered]@{}
    $resolvedGameAliases = [ordered]@{}
    if ($resolvedFiles.Contains('game_catalog')) {
        $catalogPath = [string]$resolvedFiles['game_catalog']
        if (-not (Test-Path -LiteralPath $catalogPath -PathType Leaf)) {
            throw "Game catalog not found: $catalogPath"
        }
        $catalog = Get-Content -Raw -LiteralPath $catalogPath | ConvertFrom-Json
        if ([int]$catalog.schema_version -ne 1) {
            throw "Unsupported game catalog schema: $($catalog.schema_version)"
        }
        $gameResolver = Join-Path $PSScriptRoot 'resolve_game.py'
        if (-not (Test-Path -LiteralPath $gameResolver -PathType Leaf)) {
            throw "Game resolver not found: $gameResolver"
        }

        $resolveGameConfigValue = {
            param([string]$Label, [object]$Value)
            if ($Value -isnot [string] -or -not $Value.StartsWith('@')) {
                if ($null -eq $Value -or
                    $Value -is [pscustomobject] -or
                    ($Value -is [Collections.IEnumerable] -and
                        $Value -isnot [string])) {
                    throw "$Label must be a scalar or @root path."
                }
                return $Value
            }
            $configMatch = [regex]::Match(
                $Value,
                '^@(?<root>[^/\\]+)[/\\](?<child>.+)$'
            )
            if (-not $configMatch.Success) {
                throw "$Label has an invalid path: $Value"
            }
            $configRootName = $configMatch.Groups['root'].Value
            if (-not $resolved.Contains($configRootName)) {
                throw "$Label references unknown project root '$configRootName'."
            }
            $configRoot = [string]$resolved[$configRootName]
            $configFile = [IO.Path]::GetFullPath((
                Join-Path $configRoot $configMatch.Groups['child'].Value
            ))
            $configRootPrefix = $configRoot.TrimEnd(
                [IO.Path]::DirectorySeparatorChar,
                [IO.Path]::AltDirectorySeparatorChar
            ) + [IO.Path]::DirectorySeparatorChar
            if (-not $configFile.StartsWith(
                $configRootPrefix,
                [StringComparison]::OrdinalIgnoreCase
            )) {
                throw "$Label must remain within '$configRootName'."
            }
            return $configFile
        }

        $resolvedGlobalConfig = [ordered]@{}
        $globalConfigProperty = $catalog.PSObject.Properties['config']
        if ($null -ne $globalConfigProperty) {
            foreach ($configProperty in $globalConfigProperty.Value.PSObject.Properties) {
                $configName = $configProperty.Name
                if ($configName -cnotmatch '^[a-z][a-z0-9_]*$') {
                    throw "Invalid global game configuration name: $configName"
                }
                $configValue = & $resolveGameConfigValue `
                    "Global game configuration '$configName'" `
                    $configProperty.Value
                $resolvedGlobalConfig[$configName] = $configValue
                if ([string]$configProperty.Value -like '@*') {
                    if ($resolvedFiles.Contains($configName)) {
                        throw "Project file '$configName' duplicates games.json."
                    }
                    $resolvedFiles[$configName] = $configValue
                }
            }
        }

        $allSelectors = [Collections.Generic.HashSet[string]]::new(
            [StringComparer]::OrdinalIgnoreCase
        )
        foreach ($category in @('builds', 'sources')) {
            $categoryProperty = $catalog.PSObject.Properties[$category]
            if ($null -eq $categoryProperty) {
                throw "Game catalog has no '$category' section."
            }

            $resolvedCategoryConfig = [ordered]@{}
            foreach ($configName in $resolvedGlobalConfig.Keys) {
                $resolvedCategoryConfig[$configName] = $resolvedGlobalConfig[$configName]
            }
            if ($category -eq 'builds') {
                $entriesProperty = (
                    $categoryProperty.Value.PSObject.Properties['entries']
                )
                if ($null -eq $entriesProperty) {
                    throw "Game catalog 'builds' section has no entries."
                }
                $definitions = $entriesProperty.Value
                foreach ($configProperty in (
                    $categoryProperty.Value.PSObject.Properties |
                        Where-Object Name -ne 'entries'
                )) {
                    $configName = $configProperty.Name
                    if ($configName -cnotmatch '^[a-z][a-z0-9_]*$') {
                        throw "Invalid '$category' configuration name: $configName"
                    }
                    $configValue = & $resolveGameConfigValue `
                        "Game category '$category' configuration '$configName'" `
                        $configProperty.Value
                    $resolvedCategoryConfig[$configName] = $configValue
                    if ([string]$configProperty.Value -like '@*' -and
                        -not $resolvedFiles.Contains($configName)) {
                        $resolvedFiles[$configName] = $configValue
                    }
                }
            }
            else {
                $definitions = $categoryProperty.Value
            }
            $gameNames = @($definitions.PSObject.Properties.Name)
            if ($gameNames.Count -eq 0) {
                throw "Game catalog '$category' section is empty."
            }

            foreach ($gameName in $gameNames) {
                if ($gameName -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_]*$') {
                    throw "Invalid canonical game selector: $gameName"
                }
                if (-not $allSelectors.Add($gameName)) {
                    throw "Duplicate game selector or alias: $gameName"
                }

                $definition = $definitions.PSObject.Properties[$gameName].Value
                $postfix = ''
                $memoryCardPath = $null
                $extractedPath = $null
                $resolvedGameConfig = [ordered]@{}
                foreach ($configName in $resolvedCategoryConfig.Keys) {
                    $resolvedGameConfig[$configName] = (
                        $resolvedCategoryConfig[$configName]
                    )
                }
                foreach ($configProperty in (
                    $definition.PSObject.Properties |
                        Where-Object Name -notin @(
                            'aliases',
                            'postfix'
                        )
                )) {
                    $configName = $configProperty.Name
                    if ($configName -cnotmatch '^[a-z][a-z0-9_]*$') {
                        throw "Invalid game '$gameName' configuration name: $configName"
                    }
                    $resolvedGameConfig[$configName] = & $resolveGameConfigValue `
                        "Game '$gameName' configuration '$configName'" `
                        $configProperty.Value
                }
                $resolverOutput = & python -B $gameResolver $gameName
                if ($LASTEXITCODE -ne 0) {
                    throw "Game resolver failed for '$gameName'."
                }
                $derived = ($resolverOutput -join "`n") | ConvertFrom-Json
                $isoPath = [IO.Path]::GetFullPath([string]$derived.iso)
                $memoryCardPath = [IO.Path]::GetFullPath(
                    [string]$derived.memory_card
                )
                $resolvedGameConfig['input_profile'] = [IO.Path]::GetFullPath(
                    [string]$derived.input_profile
                )
                $derivedOverrideProperty = (
                    $derived.PSObject.Properties['input_profile_overrides']
                )
                if ($null -ne $derivedOverrideProperty) {
                    $resolvedGameConfig['input_profile_overrides'] = (
                        [IO.Path]::GetFullPath(
                            [string]$derivedOverrideProperty.Value
                        )
                    )
                }
                if (-not $resolvedFiles.Contains('input_profile')) {
                    $resolvedFiles['input_profile'] = $resolvedGameConfig.input_profile
                }
                $postfix = if ($category -eq 'builds') {
                    [string]$definition.postfix
                }
                else { '' }
                if ($category -eq 'builds') {
                    $resolvedGameConfig['cheat_template'] = [IO.Path]::GetFullPath(
                        [string]$derived.cheats
                    )
                    $resolvedGameConfig['gamesettings_template'] = [IO.Path]::GetFullPath(
                        [string]$derived.game_settings
                    )
                    if (-not $resolvedFiles.Contains('cheat_template')) {
                        $resolvedFiles['cheat_template'] = $resolvedGameConfig.cheat_template
                    }
                    if (-not $resolvedFiles.Contains('gamesettings_template')) {
                        $resolvedFiles['gamesettings_template'] = $resolvedGameConfig.gamesettings_template
                    }
                }
                else {
                    $extractedPath = [IO.Path]::GetFullPath(
                        [string]$derived.extracted
                    )
                    $resolvedGameConfig['cheats'] = [IO.Path]::GetFullPath(
                        [string]$derived.cheats
                    )
                    $resolvedGameConfig['game_settings'] = [IO.Path]::GetFullPath(
                        [string]$derived.game_settings
                    )
                    $resolvedGameConfig['memory_card'] = $memoryCardPath
                    if (-not $AllowMissing -and
                        -not (Test-Path -LiteralPath $extractedPath)) {
                        throw "Configured source extraction for '$gameName' does not exist: $extractedPath"
                    }
                    $derivedRootName = "source_$($gameName.ToLowerInvariant())"
                    if ($resolved.Contains($derivedRootName)) {
                        throw "Project root '$derivedRootName' duplicates games.json."
                    }
                    $resolved[$derivedRootName] = $extractedPath
                }

                $aliasesProperty = $definition.PSObject.Properties['aliases']
                $aliases = if ($null -eq $aliasesProperty) {
                    @()
                }
                else {
                    @($aliasesProperty.Value)
                }
                foreach ($alias in $aliases) {
                    if ($alias -isnot [string] -or
                        $alias -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_]*$') {
                        throw "Invalid alias for game '$gameName': $alias"
                    }
                    if (-not $allSelectors.Add($alias)) {
                        throw "Duplicate game selector or alias: $alias"
                    }
                    $resolvedGameAliases[$alias] = $gameName
                    if ($category -eq 'sources') {
                        $aliasName = $alias.ToLowerInvariant()
                        if (-not $resolved.Contains("source_$aliasName")) {
                            $resolved["source_$aliasName"] = $extractedPath
                        }
                        if (-not $resolvedFiles.Contains("${aliasName}_iso")) {
                            $resolvedFiles["${aliasName}_iso"] = $isoPath
                        }
                    }
                }

                $gameKey = $gameName.ToLowerInvariant()
                $fileName = "${gameKey}_iso"
                if ($resolvedFiles.Contains($fileName)) {
                    throw "Project file '$fileName' duplicates games.json."
                }
                $resolvedFiles[$fileName] = $isoPath
                if ($null -ne $memoryCardPath) {
                    $memoryCardFileName = "${gameKey}_memory_card"
                    if ($resolvedFiles.Contains($memoryCardFileName)) {
                        throw "Project file '$memoryCardFileName' duplicates games.json."
                    }
                    $resolvedFiles[$memoryCardFileName] = $memoryCardPath
                }
                $resolvedGameAliases[$gameName] = $gameName
                $resolvedGames[$gameName] = [pscustomobject]@{
                    Name = $gameName
                    Category = $category
                    Aliases = $aliases
                    Postfix = $postfix
                    IsoPath = $isoPath
                    MemoryCardPath = $memoryCardPath
                    ExtractedPath = $extractedPath
                    Config = [pscustomobject]$resolvedGameConfig
                    FileName = $fileName
                }
            }
        }
    }
    $resolved['files'] = [pscustomobject]$resolvedFiles
    $resolved['games'] = [pscustomobject]@{
        Entries = [pscustomobject]$resolvedGames
        Aliases = [pscustomobject]$resolvedGameAliases
        Names = @($resolvedGames.Keys)
    }

    if (-not $resolved.Contains('repository') -or
        -not [IO.Path]::Equals($resolved.repository, $repositoryRoot)) {
        throw "The 'repository' root must resolve to the directory containing project-paths.json."
    }

    return [pscustomobject]$resolved
}

function ConvertTo-Na2ProjectPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [object]$ProjectPaths
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    $roots = @(
        $ProjectPaths.PSObject.Properties |
            Where-Object { $_.Name -notin @('ManifestPath', 'files', 'games') } |
            ForEach-Object {
                [pscustomobject]@{
                    Name = $_.Name
                    Path = [IO.Path]::GetFullPath([string]$_.Value)
                }
            } |
            Sort-Object { $_.Path.Length } -Descending
    )

    foreach ($root in $roots) {
        if ([IO.Path]::Equals($fullPath, $root.Path)) {
            return "@$($root.Name)"
        }

        $prefix = $root.Path.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
        if ($fullPath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
            $relative = $fullPath.Substring($prefix.Length).Replace([IO.Path]::DirectorySeparatorChar, '/')
            return "@$($root.Name)/$relative"
        }
    }

    throw "Path is outside configured project roots: $Path"
}

function Resolve-Na2ProjectPathAlias {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Alias,

        [Parameter(Mandatory = $true)]
        [object]$ProjectPaths
    )

    $aliasMatch = [regex]::Match(
        $Alias,
        '^@(?<root>[^/\\]+)(?:[/\\](?<child>.*))?$'
    )
    if (-not $aliasMatch.Success) {
        throw "Invalid project root alias: $Alias"
    }

    $rootName = $aliasMatch.Groups['root'].Value
    $rootProperty = $ProjectPaths.PSObject.Properties[$rootName]
    if ($null -eq $rootProperty -or
        $rootName -in @('ManifestPath', 'files', 'games')) {
        throw "Unknown project root '$rootName': $Alias"
    }

    $rootPath = [IO.Path]::GetFullPath([string]$rootProperty.Value)
    $child = $aliasMatch.Groups['child'].Value
    if ([string]::IsNullOrEmpty($child)) {
        return $rootPath
    }
    if ([IO.Path]::IsPathRooted($child)) {
        throw "Invalid project root alias: $Alias"
    }

    $resolved = [IO.Path]::GetFullPath((Join-Path $rootPath $child))
    $rootPrefix = $rootPath.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $resolved.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Project root alias escapes '$rootName': $Alias"
    }
    return $resolved
}
