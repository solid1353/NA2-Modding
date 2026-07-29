[CmdletBinding()]
param(
    [switch]$Development
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$paths = Get-Na2ProjectPaths -AllowMissing
$repository = [IO.Path]::GetFullPath($paths.repository)
$toolchainPath = Join-Path $PSScriptRoot 'toolchain.json'
$toolchain = Get-Content -Raw -LiteralPath $toolchainPath | ConvertFrom-Json
$manifestPath = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.release_manifest))
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$requirementsPath = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.requirements))
$entryPoint = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.entry_point))
$iconPath = [IO.Path]::GetFullPath((Join-Path $repository $toolchain.icon))
$releaseTemp = Resolve-Na2ProjectPathAlias -Alias $toolchain.temporary_root -ProjectPaths $paths

if ([int]$toolchain.schema_version -ne 1 -or [int]$manifest.schema_version -ne 1) {
    throw 'Unsupported release schema.'
}
if ([string]::IsNullOrWhiteSpace([string]$manifest.executable_name) -or
    [IO.Path]::GetFileName([string]$manifest.executable_name) -cne [string]$manifest.executable_name -or
    -not ([string]$manifest.executable_name).EndsWith('.exe', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Release executable_name must be one .exe filename.'
}
foreach ($required in @($requirementsPath, $entryPoint, $iconPath, $manifestPath)) {
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
$candidate = Join-Path $candidateRoot ([string]$manifest.executable_name)
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
        & $python -B -m unittest discover -s na228_builder/tests -p 'test_*.py'
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
from na228_builder.profile import load_profile, profile_resource_files

marker = Path(sys.argv[3]).resolve()
profile = load_profile(
    Path(sys.argv[2]),
    repository,
    root_overrides={"na2": marker, "nun5": marker},
)
print(json.dumps([
    path.relative_to(repository).as_posix()
    for path in profile_resource_files(profile)
]))
'@
    $profilePath = [IO.Path]::GetFullPath((Join-Path $repository $manifest.profile))
    $resourceText = & $python -B -c $resourceProbe $repository $profilePath $manifestPath
    if ($LASTEXITCODE -ne 0) { throw 'Could not inventory packaged profile resources.' }
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

    $bootstrapText = @'
import os

if os.environ.get("NA2_RELEASE_SELF_TEST") == "1":
    from na228_builder.release_runtime import validate_packaged_release
    count = validate_packaged_release()
    print(f"Release package self-test: OK ({count} module invocations)")
    raise SystemExit(0)

from na228_builder.app import main

raise SystemExit(main())
'@
    [IO.File]::WriteAllText($bootstrap, $bootstrapText, [Text.UTF8Encoding]::new($false))

    $env:PYINSTALLER_CONFIG_DIR = $cacheRoot
    $baseName = [IO.Path]::GetFileNameWithoutExtension([string]$manifest.executable_name)
    $addData = "${resourceRoot}:."
    & $python -B -m PyInstaller --noconfirm --clean --onefile --console --noupx --name $baseName --icon $iconPath --paths $repository --add-data $addData --collect-all zopfli --hidden-import na228_builder.release_runtime --distpath $distRoot --workpath (Join-Path $workRoot 'work') --specpath $specRoot $bootstrap
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }

    $built = Join-Path $distRoot ([string]$manifest.executable_name)
    if (-not (Test-Path -LiteralPath $built -PathType Leaf)) {
        throw "PyInstaller output is missing: $built"
    }
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

    [IO.File]::Move($built, $candidate, $true)
    $hash = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash
    Write-Host '[release] Release candidate built successfully.' -ForegroundColor Green
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
