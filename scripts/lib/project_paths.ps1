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

    foreach ($name in $names) {
        $value = [string]$manifest.roots.$name
        if ([string]::IsNullOrWhiteSpace($value) -or [IO.Path]::IsPathRooted($value)) {
            throw "Project root '$name' must be a non-empty repository-relative path: $value"
        }
        $path = [IO.Path]::GetFullPath((Join-Path $repositoryRoot $value))
        if (-not $AllowMissing -and -not (Test-Path -LiteralPath $path)) {
            throw "Configured project root '$name' does not exist: $path"
        }
        $resolved[$name] = $path
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
