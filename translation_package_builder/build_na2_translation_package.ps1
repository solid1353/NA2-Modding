param(
    [string]$Na2Iso,
    [string]$Na2Folder,
    [string]$Un5Iso,
    [string]$Un5Folder,
    [string]$OutputDirectory = (Join-Path $HOME 'Downloads'),
    [string]$Apply = 'BTL,ETC',
    [switch]$NoStrictHash
)

$ErrorActionPreference = 'Stop'

$builderRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $builderRoot
$builder = Join-Path $builderRoot 'scripts\build_translation_package.py'
$dataRoot = Join-Path $builderRoot 'data'

if ([string]::IsNullOrWhiteSpace($Na2Folder)) {
    $candidate = Join-Path $projectRoot 'source\NA2'
    if (Test-Path -LiteralPath $candidate -PathType Container) {
        $Na2Folder = $candidate
    }
}

if ([string]::IsNullOrWhiteSpace($Na2Iso)) {
    $candidate = Join-Path $projectRoot 'source\NA2.iso'
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $Na2Iso = $candidate
    }
}

if ([string]::IsNullOrWhiteSpace($Un5Folder)) {
    $candidate = Join-Path $projectRoot 'source\UN5'
    if (Test-Path -LiteralPath $candidate -PathType Container) {
        $Un5Folder = $candidate
    }
}

if ([string]::IsNullOrWhiteSpace($Un5Iso)) {
    $candidate = Join-Path $projectRoot 'source\UN5.iso'
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $Un5Iso = $candidate
    }
}

if ([string]::IsNullOrWhiteSpace($Na2Folder) -and [string]::IsNullOrWhiteSpace($Na2Iso)) {
    throw 'NA2 source not found. Expected source\NA2 or source\NA2.iso.'
}

if ([string]::IsNullOrWhiteSpace($Un5Folder) -and [string]::IsNullOrWhiteSpace($Un5Iso)) {
    throw 'UN5 source not found. Expected source\UN5 or source\UN5.iso.'
}

$arguments = @(
    '--output-directory', $OutputDirectory,
    '--work-root', (Join-Path $builderRoot 'work'),
    '--data-root', $dataRoot,
    '--apply', $Apply
)

if (-not [string]::IsNullOrWhiteSpace($Na2Folder)) {
    $arguments += @('--na2-folder', $Na2Folder)
}
elseif (-not [string]::IsNullOrWhiteSpace($Na2Iso)) {
    $arguments += @('--na2-iso', $Na2Iso)
}

if (-not [string]::IsNullOrWhiteSpace($Un5Folder)) {
    $arguments += @('--un5-folder', $Un5Folder)
}
elseif (-not [string]::IsNullOrWhiteSpace($Un5Iso)) {
    $arguments += @('--un5-iso', $Un5Iso)
}

if ($NoStrictHash) {
    $arguments += '--no-strict-hash'
}

& python $builder @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Translation package builder failed with exit code $LASTEXITCODE"
}
