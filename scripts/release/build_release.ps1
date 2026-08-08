[CmdletBinding()]
param(
    [switch]$Development
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
$paths = Get-Na2LocalPaths -AllowMissing
$repository = [IO.Path]::GetFullPath($paths.repository)
$toolchainPath = Join-Path $PSScriptRoot 'toolchain.json'
$toolchain = Get-Content -Raw -LiteralPath $toolchainPath | ConvertFrom-Json
$manifestPath = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.release_manifest))
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$requirementsPath = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.requirements))
$entryPoint = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.entry_point))
$iconPath = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.icon))
$instructionsPath = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.instructions))
$configurationPath = [IO.Path]::GetFullPath((Join-Path $repository $manifest.configuration))
$releaseTemp = Resolve-Na2ProjectPathAlias -Alias $toolchain.temporary_root -Paths $paths

if ([int]$toolchain.schema_version -ne 1 -or [int]$manifest.schema_version -ne 1) {
    throw 'Unsupported release schema.'
}
if ([string]::IsNullOrWhiteSpace([string]$manifest.executable_name) -or
    [IO.Path]::GetFileName([string]$manifest.executable_name) -cne [string]$manifest.executable_name -or
    -not ([string]$manifest.executable_name).EndsWith('.exe', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Release executable_name must be one .exe filename.'
}
if ([string]::IsNullOrWhiteSpace([string]$manifest.configuration_name) -or
    [IO.Path]::GetFileName([string]$manifest.configuration_name) -cne [string]$manifest.configuration_name -or
    -not ([string]$manifest.configuration_name).EndsWith('.json', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Release configuration_name must be one .json filename.'
}
foreach ($required in @(
    $requirementsPath,
    $entryPoint,
    $iconPath,
    $manifestPath,
    $instructionsPath,
    $configurationPath
)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required release input is missing: $required"
    }
}

$gitStatus = @(& git -C $repository status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0) {
    throw 'Could not inspect Git status.'
}
if ($gitStatus.Count -and -not $Development) {
    throw 'Refusing to package a release from a dirty tree. Use -Development only for local validation.'
}

$hostPython = (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Path
$runtimeText = & $hostPython -B -c "import json,platform,struct,sys; print(json.dumps({'platform':sys.platform,'architecture':str(struct.calcsize('P')*8)+'bit','python_version':platform.python_version()}))"
if ($LASTEXITCODE -ne 0) {
    throw 'Could not inspect the Python runtime.'
}
$runtime = $runtimeText | ConvertFrom-Json
foreach ($field in @('platform', 'architecture', 'python_version')) {
    if ([string]$runtime.$field -cne [string]$toolchain.$field) {
        throw "Release toolchain requires $field=$($toolchain.$field); found $($runtime.$field)."
    }
}

$candidateRoot = $paths.release_candidates
if ($Development) {
    $candidateRoot = Join-Path $candidateRoot 'development'
}
New-Item -ItemType Directory -Force -Path $candidateRoot | Out-Null
New-Item -ItemType Directory -Force -Path $releaseTemp | Out-Null
$runRoot = Join-Path $releaseTemp ('build_' + [Guid]::NewGuid().ToString('N'))
$resourceRoot = Join-Path $runRoot 'resources'
$venvRoot = Join-Path $runRoot 'venv'
$workRoot = Join-Path $runRoot 'pyinstaller'
$distRoot = Join-Path $workRoot 'dist'
$specRoot = Join-Path $workRoot 'spec'
$cacheRoot = Join-Path $workRoot 'cache'
$bootstrap = Join-Path $runRoot 'release_bootstrap.py'
$packageName = [IO.Path]::ChangeExtension([string]$manifest.executable_name, '.zip')
$candidate = Join-Path $candidateRoot $packageName
$oldPyInstallerConfig = $env:PYINSTALLER_CONFIG_DIR

try {
    New-Item -ItemType Directory -Path $resourceRoot -Force | Out-Null
    & $hostPython -B -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the release virtual environment.' }
    $python = Join-Path $venvRoot 'Scripts\python.exe'
    & $python -B -m pip install --disable-pip-version-check --require-hashes --only-binary=:all: --requirement $requirementsPath
    if ($LASTEXITCODE -ne 0) { throw 'Could not install pinned release dependencies.' }

    Push-Location $repository
    try {
        & $python -B -m unittest discover -s tests -p 'test_*.py'
        if ($LASTEXITCODE -ne 0) { throw 'Patcher tests failed.' }
    }
    finally {
        Pop-Location
    }

    $resourceProbe = @'
import json
import sys
from pathlib import Path

repository = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repository))
from na228_builder.scripts.configuration import configuration_resource_files, load_configuration

marker = Path(sys.argv[3]).resolve()
configuration = load_configuration(
    Path(sys.argv[2]),
    repository,
    repository / "na228_builder",
    root_overrides={"na2": marker, "nun5": marker},
)
excluded = {Path(sys.argv[2]).resolve()}
if configuration.selection.base_configuration_path is not None:
    excluded.add(configuration.selection.base_configuration_path.resolve())
print(json.dumps([
    path.relative_to(repository).as_posix()
    for path in configuration_resource_files(configuration, include_disabled=True)
    if path.resolve() not in excluded
]))
'@
    $resourceText = & $python -B -c $resourceProbe $repository $configurationPath $manifestPath
    if ($LASTEXITCODE -ne 0) { throw 'Could not inventory packaged configuration resources.' }
    $resources = @($resourceText | ConvertFrom-Json)
    $resources += @(
        [IO.Path]::GetRelativePath($repository, $paths.ManifestPath).Replace('\', '/'),
        [IO.Path]::GetRelativePath($repository, $manifestPath).Replace('\', '/'),
        'na228_builder/payload_builder/config.tsv'
    )
    foreach ($relative in @($resources | Sort-Object -Unique)) {
        $source = [IO.Path]::GetFullPath((Join-Path $repository $relative))
        $destination = Join-Path $resourceRoot $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination
    }

    $compileRuntimeSource = @'
import sys
from pathlib import Path

repository = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repository))
from na228_builder.payload_builder.ee_c_fragments import (
    compile_ee_c,
    default_toolchain_bin,
)

compile_ee_c(
    Path(sys.argv[2]),
    Path(sys.argv[3]),
    toolchain_bin=default_toolchain_bin(repository),
)
'@
    foreach ($relative in @($resources | Sort-Object -Unique)) {
        if (-not ([string]$relative).EndsWith('.c', [StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        $source = [IO.Path]::GetFullPath((Join-Path $repository $relative))
        $packagedObject = (Join-Path $resourceRoot $relative) + '.o'
        & $python -B -c $compileRuntimeSource $repository $source $packagedObject
        if ($LASTEXITCODE -ne 0) {
            throw "Could not precompile packaged runtime source: $relative"
        }
    }

    $bootstrapText = @'
import os

if os.environ.get("NA2_RELEASE_SELF_TEST") == "1":
    from na228_builder.scripts.release_runtime import validate_packaged_release
    count = validate_packaged_release()
    print(f"Release package self-test: OK ({count} module invocations)")
    raise SystemExit(0)

from na228_builder.scripts.app import main

raise SystemExit(main())
'@
    [IO.File]::WriteAllText($bootstrap, $bootstrapText, [Text.UTF8Encoding]::new($false))

    $env:PYINSTALLER_CONFIG_DIR = $cacheRoot
    $baseName = [IO.Path]::GetFileNameWithoutExtension([string]$manifest.executable_name)
    $addData = "${resourceRoot}:."
    & $python -B -m PyInstaller --noconfirm --clean --onefile --console --noupx --name $baseName --icon $iconPath --paths $repository --add-data $addData --collect-all zopfli --hidden-import na228_builder.scripts.release_runtime --distpath $distRoot --workpath (Join-Path $workRoot 'work') --specpath $specRoot $bootstrap
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }

    $built = Join-Path $distRoot ([string]$manifest.executable_name)
    if (-not (Test-Path -LiteralPath $built -PathType Leaf)) {
        throw "PyInstaller output is missing: $built"
    }
    $packagedConfiguration = Join-Path $distRoot ([string]$manifest.configuration_name)
    $packagedInstructions = Join-Path $distRoot 'README.txt'
    $materializedProbe = @'
import json
import sys
from pathlib import Path

repository = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repository))
from na228_builder.scripts.catalog import materialized_configuration

print(json.dumps(materialized_configuration(
    repository / "na228_builder" / "catalog.json",
    Path(sys.argv[2]),
), indent=2))
'@
    $materializedText = @(& $python -B -c $materializedProbe $repository $configurationPath)
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not construct the merged release configuration.'
    }
    [IO.File]::WriteAllText(
        $packagedConfiguration,
        ($materializedText -join "`n") + "`n",
        [Text.UTF8Encoding]::new($false)
    )
    Copy-Item -LiteralPath $instructionsPath -Destination $packagedInstructions

    $env:NA2_RELEASE_SELF_TEST = '1'
    $selfTest = @(& $built 2>&1)
    $selfTestExit = $LASTEXITCODE
    Remove-Item Env:NA2_RELEASE_SELF_TEST -ErrorAction SilentlyContinue
    if ($selfTestExit -ne 0 -or -not (($selfTest -join "`n").Contains('Release package self-test: OK'))) {
        throw "Packaged executable self-test failed.`n$($selfTest -join "`n")"
    }

    $allEnabledProbe = @'
import json
import sys
from pathlib import Path

repository = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repository))
from na228_builder.scripts.catalog import all_enabled_configuration

print(json.dumps(all_enabled_configuration(Path(sys.argv[2])), indent=2))
'@
    $catalogPath = Join-Path $repository 'na228_builder\catalog.json'
    $allEnabledText = @(& $python -B -c $allEnabledProbe $repository $catalogPath)
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not create the transient all-enabled configuration.'
    }
    [IO.File]::WriteAllText(
        $packagedConfiguration,
        ($allEnabledText -join "`n") + "`n",
        [Text.UTF8Encoding]::new($false)
    )
    $env:NA2_RELEASE_SELF_TEST = '1'
    $allEnabledSelfTest = @(& $built 2>&1)
    $allEnabledSelfTestExit = $LASTEXITCODE
    Remove-Item Env:NA2_RELEASE_SELF_TEST -ErrorAction SilentlyContinue
    if ($allEnabledSelfTestExit -ne 0 -or
        -not (($allEnabledSelfTest -join "`n").Contains('Release package self-test: OK'))) {
        throw "All-enabled packaged executable self-test failed.`n$($allEnabledSelfTest -join "`n")"
    }
    [IO.File]::WriteAllText(
        $packagedConfiguration,
        ($materializedText -join "`n") + "`n",
        [Text.UTF8Encoding]::new($false)
    )
    if ((Get-Item -LiteralPath $built).Length -lt 1MB) {
        throw 'Packaged executable is unexpectedly small.'
    }

    $packageStaging = Join-Path $runRoot $packageName
    Compress-Archive `
        -LiteralPath @($built, $packagedConfiguration, $packagedInstructions) `
        -DestinationPath $packageStaging `
        -CompressionLevel Optimal
    [IO.File]::Move($packageStaging, $candidate, $true)
    $hash = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash
    Write-Host '[release] Release package built successfully.' -ForegroundColor Green
    Write-Host "[release] Output: $candidate"
    Write-Host "[release] SHA-256: $hash"
}
finally {
    $env:PYINSTALLER_CONFIG_DIR = $oldPyInstallerConfig
    Remove-Item Env:NA2_RELEASE_SELF_TEST -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $runRoot) {
        $resolvedRun = [IO.Path]::GetFullPath($runRoot)
        $resolvedParent = [IO.Path]::GetFullPath($releaseTemp).TrimEnd('\') + '\'
        if (-not $resolvedRun.StartsWith($resolvedParent, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean release staging outside its configured root: $resolvedRun"
        }
        Remove-Item -LiteralPath $resolvedRun -Recurse -Force
    }
}
