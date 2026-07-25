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
    $resolved['files'] = [pscustomobject]$resolvedFiles

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
            Where-Object { $_.Name -notin @('ManifestPath', 'files') } |
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
    if ($null -eq $rootProperty -or $rootName -in @('ManifestPath', 'files')) {
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
