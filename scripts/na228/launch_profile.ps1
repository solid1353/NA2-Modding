Set-StrictMode -Version Latest

function Resolve-Na2LaunchProfile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][psobject]$Paths
    )

    if ($Name -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]*$') {
        throw "Invalid launch profile name: $Name"
    }
    $property = $Paths.settings.launch_settings.PSObject.Properties[$Name]
    if ($null -eq $property -or $property.Value -isnot [pscustomobject]) {
        throw "Unknown launch profile: $Name"
    }

    $canonicalName = [string]$property.Name
    $profilesRoot = [IO.Path]::GetFullPath((Join-Path `
        ([string]$Paths.repository) `
        'launch_profiles'
    ))
    $profileRoot = [IO.Path]::GetFullPath((Join-Path `
        $profilesRoot `
        $canonicalName
    ))
    $profilesPrefix = $profilesRoot.TrimEnd('\', '/') + `
        [IO.Path]::DirectorySeparatorChar
    if (-not $profileRoot.StartsWith(
        $profilesPrefix,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Launch profile '$canonicalName' escapes the profile root."
    }
    $scriptPath = Join-Path $profileRoot 'launch.ps1'

    [pscustomobject]@{
        Name = $canonicalName
        Settings = $property.Value
        Root = $profileRoot
        Script = if (Test-Path -LiteralPath $scriptPath -PathType Leaf) {
            $scriptPath
        }
        else {
            $null
        }
    }
}

function Invoke-Na2LaunchProfile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][psobject]$Profile,
        [AllowEmptyCollection()][string[]]$Arguments = @(),
        [Parameter(Mandatory)][string[]]$Games,
        [Parameter(Mandatory)][string]$ProjectRoot
    )

    if ([string]::IsNullOrWhiteSpace([string]$Profile.Script)) {
        if ($Arguments.Count -gt 0) {
            throw "Launch profile '$($Profile.Name)' accepts no arguments."
        }
        return
    }

    $results = @(
        & ([string]$Profile.Script) `
            -Arguments $Arguments `
            -Games $Games `
            -ProjectRoot $ProjectRoot
    )
    if ($results.Count -eq 0) {
        throw "Launch profile '$($Profile.Name)' returned no result."
    }
    foreach ($result in $results) {
        $launchParameters = $result.PSObject.Properties['LaunchParameters']
        if ($null -eq $launchParameters -or
            $launchParameters.Value -isnot [Collections.IDictionary]) {
            throw (
                "Launch profile '$($Profile.Name)' must return a " +
                'LaunchParameters dictionary.'
            )
        }
        $result
    }
}

function Merge-Na2LaunchProfileParameters {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][hashtable]$Target,
        [Parameter(Mandatory)][psobject]$Profile,
        [Parameter(Mandatory)][psobject]$Result
    )

    foreach ($entry in $Result.LaunchParameters.GetEnumerator()) {
        $name = [string]$entry.Key
        if ($Target.ContainsKey($name)) {
            throw (
                "Launch profile '$($Profile.Name)' conflicts with " +
                "launch parameter '$name'."
            )
        }
        $Target[$name] = $entry.Value
    }
}
