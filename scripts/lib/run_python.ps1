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

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$configPath = Join-Path $repository 'packages.json'
$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json

$setProperty = $config.sets.PSObject.Properties[$PackageSet]
if ($null -eq $setProperty) {
    $available = @($config.sets.PSObject.Properties.Name) -join ', '
    throw "Unknown Python package set '$PackageSet'. Available: $available"
}
$requirements = @($setProperty.Value)
foreach ($requirement in $requirements) {
    if ($requirement -isnot [string] -or
        $requirement -cnotmatch '^[A-Za-z_][A-Za-z0-9_.]*(==[A-Za-z0-9][A-Za-z0-9._+-]*)?$') {
        throw "Invalid Python requirement in package set '$PackageSet': $requirement"
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
import importlib.metadata
import importlib.util
import sys

missing = []
for requirement in sys.argv[1:]:
    module, separator, expected_version = requirement.partition("==")
    if importlib.util.find_spec(module) is None:
        missing.append(requirement)
        continue
    if separator:
        try:
            actual_version = importlib.metadata.version(module)
        except importlib.metadata.PackageNotFoundError:
            missing.append(requirement)
            continue
        if actual_version != expected_version:
            missing.append(requirement)
raise SystemExit(1 if missing else 0)
'@
foreach ($candidate in $candidates) {
    if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
    $candidatePath = [IO.Path]::GetFullPath($candidate)
    if (-not $seen.Add($candidatePath) -or
        -not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) {
        continue
    }

    & $candidatePath -B -c $probe @requirements *> $null
    if ($LASTEXITCODE -eq 0) {
        $runtime = $candidatePath
        break
    }
}

if ($null -eq $runtime) {
    $requirementText = if ($requirements.Count -eq 0) {
        'standard library'
    }
    else {
        $requirements -join ', '
    }
    throw (
        "No unified Python runtime satisfies package set '$PackageSet' " +
        "($requirementText). Set NA228_PYTHON to a compatible python.exe."
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
