param(
    [string]$Na2Iso,
    [string]$Na2Folder,
    [string]$Un5Iso,
    [string]$Un5Folder,
    [string]$Apply = 'BTL,ETC,SLPS',
    [switch]$NoStrictHash
)

$ErrorActionPreference = 'Stop'

$moduleRoot = $PSScriptRoot
$projectRoot = [IO.Path]::GetFullPath((Join-Path $moduleRoot '..\..\..'))
$engine = Join-Path $moduleRoot 'engine.py'
$mappingRoot = $moduleRoot
$workRoot = Join-Path $projectRoot 'logs\na2_patcher\translation_exports'

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
    '--work-root', $workRoot,
    '--data-root', $mappingRoot,
    '--apply', $Apply
)

if (-not [string]::IsNullOrWhiteSpace($Na2Folder)) {
    $arguments += @('--na2-folder', $Na2Folder)
}
else {
    $arguments += @('--na2-iso', $Na2Iso)
}

if (-not [string]::IsNullOrWhiteSpace($Un5Folder)) {
    $arguments += @('--un5-folder', $Un5Folder)
}
else {
    $arguments += @('--un5-iso', $Un5Iso)
}

if ($NoStrictHash) {
    $arguments += '--no-strict-hash'
}

& python $engine @arguments
if ($LASTEXITCODE -ne 0) {
    throw "NA2 translation module failed with exit code $LASTEXITCODE"
}
