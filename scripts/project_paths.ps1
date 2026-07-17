Set-StrictMode -Version Latest

function Get-Na2ProjectPaths {
    [CmdletBinding()]
    param(
        [string]$ManifestPath = (Join-Path (Split-Path -Parent $PSScriptRoot) 'project-paths.json'),
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

    if (-not $resolved.Contains('repository') -or
        -not [IO.Path]::Equals($resolved.repository, $repositoryRoot)) {
        throw "The 'repository' root must resolve to the directory containing project-paths.json."
    }

    return [pscustomobject]$resolved
}
