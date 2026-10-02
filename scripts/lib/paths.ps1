Set-StrictMode -Version Latest

function Test-Na2PathWithin {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullRoot = [IO.Path]::GetFullPath($Root).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    return $fullPath.Equals($fullRoot, [StringComparison]::OrdinalIgnoreCase) -or
        $fullPath.StartsWith(
            $fullRoot + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase
        )
}

function Resolve-Na2PathManifest {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$ManifestPath,
        [switch]$AllowMissing,
        [switch]$Local
    )

    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw "Project path manifest not found: $ManifestPath"
    }
    $manifest = (Get-Item -LiteralPath $ManifestPath).FullName

    # One resolution serves every caller within the same command line.
    $cacheKey = "$($MyInvocation.HistoryId)|$manifest|$AllowMissing|$Local"
    $cache = Get-Variable -Name Na2PathCache -Scope Global -ValueOnly `
        -ErrorAction SilentlyContinue
    if ($cache -isnot [hashtable]) {
        $cache = @{}
        Set-Variable -Name Na2PathCache -Scope Global -Value $cache
    }
    if ($cache.ContainsKey($cacheKey)) {
        return $cache[$cacheKey]
    }

    $arguments = @($manifest)
    if ($AllowMissing) { $arguments += '--allow-missing' }
    if ($Local) { $arguments += '--local' }
    $output = @(
        & (Join-Path $PSScriptRoot 'run_python.ps1') -PackageSet builder `
            -Script (Join-Path $PSScriptRoot 'paths.py') `
            -ArgumentList $arguments -NoBytecode 2>&1
    )
    $exitCode = $LASTEXITCODE
    $lines = [string[]]@($output | ForEach-Object { [string]$_ })
    if ($exitCode -ne 0) {
        throw "Project paths could not be resolved: $($lines -join "`n")"
    }
    $loaded = ($lines -join "`n") | ConvertFrom-Json

    $resolved = [ordered]@{ ManifestPath = [string]$loaded.manifest }
    foreach ($root in $loaded.roots.PSObject.Properties) {
        $resolved[$root.Name] = [string]$root.Value
    }
    if ($null -ne $loaded.settings) {
        $resolved['settings'] = $loaded.settings
    }
    $resolved['files'] = $loaded.files
    $entries = [ordered]@{}
    $aliases = [ordered]@{}
    foreach ($game in $loaded.games.PSObject.Properties) {
        foreach ($alias in @($game.Value.aliases)) {
            $aliases[[string]$alias] = $game.Name
        }
        $aliases[$game.Name] = $game.Name
        $entries[$game.Name] = [pscustomobject]@{
            Name = $game.Name
            Config = $game.Value.config
        }
    }
    $resolved['games'] = [pscustomobject]@{
        Entries = [pscustomobject]$entries
        Aliases = [pscustomobject]$aliases
        Names = @($entries.Keys)
    }

    $paths = [pscustomobject]$resolved
    $cache[$cacheKey] = $paths
    return $paths
}

function Get-Na2LocalPaths {
    [CmdletBinding()]
    param(
        [string]$ManifestPath = (Join-Path $PSScriptRoot '..\..\paths.json'),
        [switch]$AllowMissing
    )

    Resolve-Na2PathManifest `
        -ManifestPath $ManifestPath `
        -AllowMissing:$AllowMissing `
        -Local
}

function Get-Na2Paths {
    [CmdletBinding()]
    param(
        [string]$ManifestPath = (Join-Path $PSScriptRoot '..\..\paths.json'),
        [switch]$AllowMissing
    )

    Resolve-Na2PathManifest `
        -ManifestPath $ManifestPath `
        -AllowMissing:$AllowMissing
}
