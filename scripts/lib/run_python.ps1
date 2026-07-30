[CmdletBinding(DefaultParameterSetName = 'Script')]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z][a-z0-9_]*$')]
    [string]$PackageSet,

    [Parameter(Mandatory = $true, ParameterSetName = 'Script')]
    [string]$Script,

    [Parameter(Mandatory = $true, ParameterSetName = 'Module')]
    [string]$Module,

    [Parameter(Mandatory = $true, ParameterSetName = 'Command')]
    [string]$Command,

    [string[]]$ArgumentList = @(),

    [switch]$NoBytecode
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$configPath = Join-Path $PSScriptRoot 'python_packages.json'
$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
if ([int]$config.schema_version -ne 1) {
    throw "Unsupported Python package-set schema: $($config.schema_version)"
}

$setProperty = $config.sets.PSObject.Properties[$PackageSet]
if ($null -eq $setProperty) {
    $available = @($config.sets.PSObject.Properties.Name) -join ', '
    throw "Unknown Python package set '$PackageSet'. Available: $available"
}
$requiredModules = @($setProperty.Value)
foreach ($requiredModule in $requiredModules) {
    if ($requiredModule -isnot [string] -or
        $requiredModule -cnotmatch '^[A-Za-z_][A-Za-z0-9_.]*$') {
        throw "Invalid Python module in package set '$PackageSet': $requiredModule"
    }
}

$candidates = [Collections.Generic.List[string]]::new()
if (-not [string]::IsNullOrWhiteSpace($env:NA228_PYTHON)) {
    $candidates.Add($env:NA228_PYTHON)
}
if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    $candidates.Add((Join-Path $env:USERPROFILE (
        '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    )))
}
foreach ($commandInfo in @(
    Get-Command python -CommandType Application -All -ErrorAction SilentlyContinue
)) {
    $candidates.Add($commandInfo.Source)
}

$seen = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
$runtime = $null
$probe = @'
import importlib.util
import sys

missing = [name for name in sys.argv[1:] if importlib.util.find_spec(name) is None]
raise SystemExit(1 if missing else 0)
'@
foreach ($candidate in $candidates) {
    if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
    $candidatePath = [IO.Path]::GetFullPath($candidate)
    if (-not $seen.Add($candidatePath) -or
        -not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) {
        continue
    }

    & $candidatePath -B -c $probe @requiredModules *> $null
    if ($LASTEXITCODE -eq 0) {
        $runtime = $candidatePath
        break
    }
}

if ($null -eq $runtime) {
    $modules = if ($requiredModules.Count -eq 0) {
        'standard library'
    }
    else {
        $requiredModules -join ', '
    }
    throw (
        "No unified Python runtime satisfies package set '$PackageSet' " +
        "($modules). Set NA228_PYTHON to a compatible python.exe."
    )
}

$pythonArguments = [Collections.Generic.List[string]]::new()
if ($NoBytecode) {
    $pythonArguments.Add('-B')
}
switch ($PSCmdlet.ParameterSetName) {
    'Script' {
        $pythonArguments.Add($Script)
    }
    'Module' {
        $pythonArguments.Add('-m')
        $pythonArguments.Add($Module)
    }
    'Command' {
        $pythonArguments.Add('-c')
        $pythonArguments.Add($Command)
    }
}
foreach ($argument in $ArgumentList) {
    $pythonArguments.Add($argument)
}

& $runtime @pythonArguments
exit $LASTEXITCODE
