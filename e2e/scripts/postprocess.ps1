[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('CurrentPrepare', 'ReferencePrepare', 'All')]
    [string]$Action,
    [Parameter(Mandatory)][string]$Suite,
    [Parameter(Mandatory)][string]$Transaction,
    [Parameter(Mandatory)][string]$CaptureRoot,
    [string]$CapturedRoot
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$context = Get-VisualRegressionContext -Suite $Suite -CaptureRoot $CaptureRoot
$suiteStage = Join-Path (Join-Path $Transaction 'stages') $context.SuiteRelativePath
$suitePublish = Join-Path (Join-Path $Transaction 'publish') $context.SuiteRelativePath
$screenshotStage = Join-Path $suitePublish $script:E2eScreenshotGridDirectory
$metadataPath = Join-Path $suiteStage 'postprocess.json'

if ($Action -ne 'All') {
    if ([string]::IsNullOrWhiteSpace($CapturedRoot)) {
        throw "$Action requires CapturedRoot."
    }
    $capturedScreenshots = [IO.Path]::GetFullPath($CapturedRoot)
    if ($context.Generated) {
        $capturedScreenshots = Join-Path $capturedScreenshots 'screenshots'
    }

    New-VisualRegressionPagedScreenshotGridStage `
        -ExistingDirectory $context.Capture.ScreenshotGrids `
        -CapturedScreenshotDirectory $capturedScreenshots `
        -OutputDirectory $screenshotStage `
        -CapturedTier $Action.Substring(0, $Action.Length - 'Prepare'.Length)
    $metadata = [ordered]@{
        suite = $context.Suite
        has_reference = (Get-VisualRegressionPngCount `
            -Directory $screenshotStage `
            -Filter 'page_*_a_reference.png') -gt 0
        has_current = (Get-VisualRegressionPngCount `
            -Directory $screenshotStage `
            -Filter 'page_*_b_current.png') -gt 0
    }
    Write-VisualRegressionJson -Path $metadataPath -Value $metadata
    [pscustomobject]$metadata
    return
}

if (-not (Test-Path -LiteralPath $metadataPath -PathType Leaf)) {
    throw "Missing E2E post-processing metadata for $Suite."
}
$metadata = Get-Content -Raw -LiteralPath $metadataPath | ConvertFrom-Json
if (-not $metadata.has_reference -or -not $metadata.has_current) {
    return
}

& $context.Comparator `
    -PairedGridDirectory $screenshotStage `
    -OutputDirectory $suitePublish
if ($LASTEXITCODE -ne 0) {
    throw "$Action grid generation failed with exit code $LASTEXITCODE."
}
