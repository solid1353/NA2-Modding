[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('CurrentPrepare', 'ReferencePrepare', 'Pair', 'Blend', 'Diff')]
    [string]$Action,
    [Parameter(Mandatory)][string]$Suite,
    [Parameter(Mandatory)][string]$Transaction,
    [Parameter(Mandatory)][string]$CaptureRoot,
    [string]$PublishedVariant,
    [string]$CapturedRoot
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$context = Get-VisualRegressionContext -Suite $Suite -CaptureRoot $CaptureRoot
$suiteStage = Join-Path (Join-Path $Transaction 'stages') $context.SuiteRelativePath
$suitePublish = Join-Path (Join-Path $Transaction 'publish') $context.SuiteRelativePath
$screenshotStage = Join-Path $suitePublish $script:E2eScreenshotGridDirectory
$metadataPath = Join-Path $suiteStage 'postprocess.json'

if ($Action -in @('CurrentPrepare', 'ReferencePrepare')) {
    if ($Action -ceq 'CurrentPrepare') {
        if ([string]::IsNullOrWhiteSpace($PublishedVariant)) {
            throw 'CurrentPrepare requires PublishedVariant.'
        }
        $suiteJob = Join-Path `
            (Join-Path (Join-Path (Join-Path $Transaction 'jobs') $PublishedVariant) 'suites') `
            $context.SuiteRelativePath
        $capturedRoot = Join-Path $suiteJob 'capture'
        $capturedScreenshots = Join-Path $capturedRoot 'screenshots'
        $capturedTier = 'Current'
    }
    else {
        if ([string]::IsNullOrWhiteSpace($CapturedRoot)) {
            throw 'ReferencePrepare requires CapturedRoot.'
        }
        $capturedRoot = [IO.Path]::GetFullPath($CapturedRoot)
        $capturedScreenshots = Join-Path $capturedRoot 'screenshots'
        $capturedTier = 'Reference'
    }

    New-VisualRegressionPagedScreenshotGridStage `
        -Suite $Suite `
        -ExistingDirectory $context.Capture.ScreenshotGrids `
        -CapturedScreenshotDirectory $capturedScreenshots `
        -OutputDirectory $screenshotStage `
        -CapturedTier $capturedTier
    $metadata = [ordered]@{
        schema_version = 1
        suite = $context.Suite
        has_reference = @(
            Get-ChildItem `
                -LiteralPath $screenshotStage `
                -Filter 'page_*_a_reference.png' `
                -File `
                -ErrorAction SilentlyContinue
        ).Count -gt 0
        has_current = @(
            Get-ChildItem `
                -LiteralPath $screenshotStage `
                -Filter 'page_*_b_current.png' `
                -File `
                -ErrorAction SilentlyContinue
        ).Count -gt 0
    }
    [void](New-Item -ItemType Directory -Path $suiteStage -Force)
    [IO.File]::WriteAllText(
        $metadataPath,
        (($metadata | ConvertTo-Json -Depth 3) + "`n"),
        [Text.UTF8Encoding]::new($false)
    )
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
    -OutputDirectory $suitePublish `
    -Kind $Action
if ($LASTEXITCODE -ne 0) {
    throw "$Action grid generation failed with exit code $LASTEXITCODE."
}
