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
$settingsPath = [IO.Path]::GetFullPath($paths.files.settings)
$settings = Get-Content -Raw -LiteralPath $settingsPath | ConvertFrom-Json
$productName = [string]$settings.title
$executableName = "${productName}_$([string]$manifest.product_version).exe"
$requirementsPath = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.requirements))
$entryPoint = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.entry_point))
$iconPath = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.icon))
$instructionsPath = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.instructions))
$configurationPath = [IO.Path]::GetFullPath((Join-Path $repository $manifest.configuration))
$releaseTemp = Resolve-Na2ProjectPathAlias -Alias $toolchain.temporary_root -Paths $paths

if ([int]$toolchain.schema_version -ne 1 -or [int]$manifest.schema_version -ne 1) {
    throw 'Unsupported release schema.'
}
if ([string]::IsNullOrWhiteSpace($productName) -or
    [IO.Path]::GetFileName($executableName) -cne $executableName) {
    throw 'Product title must produce one release executable filename.'
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
    $settingsPath,
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

$releaseRoot = if ($Development) {
    Join-Path $paths.work 'release\development'
}
else {
    $paths.release
}
New-Item -ItemType Directory -Force -Path $releaseRoot | Out-Null
New-Item -ItemType Directory -Force -Path $releaseTemp | Out-Null
$runRoot = Join-Path $releaseTemp ('build_' + [Guid]::NewGuid().ToString('N'))
$resourceRoot = Join-Path $runRoot 'resources'
$venvRoot = Join-Path $runRoot 'venv'
$workRoot = Join-Path $runRoot 'pyinstaller'
$distRoot = Join-Path $workRoot 'dist'
$specRoot = Join-Path $workRoot 'spec'
$cacheRoot = Join-Path $workRoot 'cache'
$bootstrap = Join-Path $runRoot 'release_bootstrap.py'
$packageName = [IO.Path]::ChangeExtension($executableName, '.zip')
$packagePath = Join-Path $releaseRoot $packageName
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
        & $python -B -m unittest discover -s tests -t . -p 'test_*.py'
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
from scripts.lib.paths import load_local_paths

marker = Path(sys.argv[3]).resolve()
paths = load_local_paths(repository, allow_missing=True)
configuration = load_configuration(
    Path(sys.argv[2]),
    repository,
    paths.path("builder"),
    project_paths=paths,
    root_overrides={"na2": marker, "nun5": marker},
)
excluded = {Path(sys.argv[2]).resolve()}
if configuration.selection.base_configuration_path is not None:
    excluded.add(configuration.selection.base_configuration_path.resolve())
if configuration.character_overrides is not None:
    configuration_root = paths.path("builder", "configurations")
    excluded.update(
        path.resolve()
        for path in configuration.character_overrides.resource_files
        if path.resolve().parent == configuration_root
    )
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
        [IO.Path]::GetRelativePath(
            $repository,
            (Join-Path $paths.builder 'payload_builder\config.tsv')
        ).Replace('\', '/')
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
    compile_ee_source,
    default_toolchain_bin,
)

source = Path(sys.argv[2])
compile_ee_source(
    source,
    Path(sys.argv[3]),
    language="asm" if source.suffix == ".S" else "c",
    toolchain_bin=default_toolchain_bin(repository),
)
'@
    foreach ($relative in @($resources | Sort-Object -Unique)) {
        $suffix = [IO.Path]::GetExtension([string]$relative)
        if ($suffix -cne '.c' -and $suffix -cne '.S') {
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
    $baseName = [IO.Path]::GetFileNameWithoutExtension($executableName)
    $addData = "${resourceRoot}:."
    & $python -B -m PyInstaller --noconfirm --clean --onefile --console --noupx --name $baseName --icon $iconPath --paths $repository --add-data $addData --collect-all zopfli --hidden-import na228_builder.scripts.release_runtime --distpath $distRoot --workpath (Join-Path $workRoot 'work') --specpath $specRoot $bootstrap
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }

    $built = Join-Path $distRoot $executableName
    if (-not (Test-Path -LiteralPath $built -PathType Leaf)) {
        throw "PyInstaller output is missing: $built"
    }
    $packagedConfiguration = Join-Path $distRoot ([string]$manifest.configuration_name)
    $packagedCharacterOverrides = Join-Path $distRoot 'character_overrides.tsv'
    $packagedInstructions = Join-Path $distRoot 'README.md'
    $packagedCatalog = Join-Path $distRoot 'catalog.modcat'
    $configurationProbe = @'
import json
import sys
from pathlib import Path

repository = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repository))
from na228_builder.scripts.catalog import materialized_configuration
from scripts.lib.paths import load_local_paths

paths = load_local_paths(repository, allow_missing=True)

print(json.dumps(materialized_configuration(
    paths.path("builder", "catalog"),
    Path(sys.argv[2]),
), indent=2))
'@
    $configurationText = @(& $python -B -c $configurationProbe $repository $configurationPath)
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not construct the merged release configuration.'
    }
    [IO.File]::WriteAllText(
        $packagedConfiguration,
        ($configurationText -join "`n") + "`n",
        [Text.UTF8Encoding]::new($false)
    )
    $characterOverrideProbe = @'
import sys
from pathlib import Path

repository = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repository))
from na228_builder.scripts.character_overrides import (
    load_character_overrides,
    render_character_overrides,
)
from scripts.lib.paths import load_local_paths

paths = load_local_paths(repository, allow_missing=True)

configuration = load_character_overrides(
    Path(sys.argv[2]),
    paths.path("builder"),
    paths.path("resources", "character_data.tsv"),
)
print(render_character_overrides(configuration), end="")
'@
    $characterOverrideText = @(& $python -B -c $characterOverrideProbe $repository $configurationPath)
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not construct the merged release character overrides.'
    }
    [IO.File]::WriteAllText(
        $packagedCharacterOverrides,
        ($characterOverrideText -join "`n") + "`n",
        [Text.UTF8Encoding]::new($false)
    )
    Copy-Item -LiteralPath $instructionsPath -Destination $packagedInstructions

    $catalogProbe = @'
import sys
from pathlib import Path

repository = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repository))
from na228_builder.scripts.catalog import public_catalog
from scripts.lib.paths import load_local_paths

paths = load_local_paths(repository, allow_missing=True)

print(public_catalog(paths.path("builder", "catalog")), end="")
'@
    $catalogText = @(& $python -B -c $catalogProbe $repository)
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not construct the consolidated release catalog.'
    }
    [IO.File]::WriteAllText(
        $packagedCatalog,
        ($catalogText -join "`n") + "`n",
        [Text.UTF8Encoding]::new($false)
    )

    $env:NA2_RELEASE_SELF_TEST = '1'
    $selfTest = @(& $built 2>&1)
    $selfTestExit = $LASTEXITCODE
    Remove-Item Env:NA2_RELEASE_SELF_TEST -ErrorAction SilentlyContinue
    if ($selfTestExit -ne 0 -or -not (($selfTest -join "`n").Contains('Release package self-test: OK'))) {
        throw "Packaged executable self-test failed.`n$($selfTest -join "`n")"
    }

    if ((Get-Item -LiteralPath $built).Length -lt 1MB) {
        throw 'Packaged executable is unexpectedly small.'
    }

    $packageStaging = Join-Path $runRoot $packageName
    Compress-Archive `
        -LiteralPath @(
            $built,
            $packagedConfiguration,
            $packagedCharacterOverrides,
            $packagedCatalog,
            $packagedInstructions
        ) `
        -DestinationPath $packageStaging `
        -CompressionLevel Optimal
    [IO.File]::Move($packageStaging, $packagePath, $true)
    $hash = (Get-FileHash -LiteralPath $packagePath -Algorithm SHA256).Hash
    Write-Host '[release] Release package built successfully.' -ForegroundColor Green
    Write-Host "[release] Output: $packagePath"
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
