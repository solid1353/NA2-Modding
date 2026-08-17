[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('CurrentPrepare', 'ReferencePrepare', 'ScreenshotGrid', 'Pair', 'Blend', 'Diff')]
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
$referenceStage = Join-Path $suiteStage $script:E2eCaptureTiers.Reference
$currentStage = Join-Path $suiteStage $script:E2eCaptureTiers.Current
$reportStage = Join-Path $suiteStage 'report'
$suitePublish = Join-Path (Join-Path $Transaction 'publish') $context.SuiteRelativePath
$screenshotStage = Join-Path $suitePublish $script:E2eScreenshotDirectory
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
        New-VisualRegressionTierStage `
            -ScreenshotDirectory $context.Capture.Screenshots `
            -StageDirectory $referenceStage `
            -Kind Reference
        [void](New-Item -ItemType Directory -Path $currentStage -Force)
        Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File |
            Copy-Item -Destination $currentStage
    }
    else {
        if ([string]::IsNullOrWhiteSpace($CapturedRoot)) {
            throw 'ReferencePrepare requires CapturedRoot.'
        }
        $capturedRoot = [IO.Path]::GetFullPath($CapturedRoot)
        $capturedScreenshots = Join-Path $capturedRoot 'screenshots'
        New-VisualRegressionTierStage `
            -ScreenshotDirectory $context.Capture.Screenshots `
            -StageDirectory $currentStage `
            -Kind Current
        [void](New-Item -ItemType Directory -Path $referenceStage -Force)
        Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File |
            Copy-Item -Destination $referenceStage
    }

    New-VisualRegressionScreenshotStage `
        -ReferenceDirectory $referenceStage `
        -CurrentDirectory $currentStage `
        -OutputDirectory $screenshotStage
    $metadata = [ordered]@{
        schema_version = 1
        suite = $context.Suite
        has_reference = @(Get-NumericPngSlots -Directory $referenceStage).Count -gt 0
        has_current = @(Get-NumericPngSlots -Directory $currentStage).Count -gt 0
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
if ($Action -ceq 'ScreenshotGrid') {
    New-VisualRegressionScreenshotGridStage `
        -Suite $Suite `
        -ScreenshotDirectory $screenshotStage `
        -OutputDirectory (Join-Path $suitePublish $script:E2eScreenshotGridDirectory)
    return
}
if (-not $metadata.has_reference -or -not $metadata.has_current) {
    return
}

$definition = Get-VisualRegressionScreenshotDefinition -Kind $Action
$baseDirectory = $script:E2eIndividualDirectoryPrefix + $definition.Label + 's'
$gridDirectory = 'grid-' + $definition.Label + 's'
New-VisualRegressionReport `
    -Suite $Suite `
    -ReferenceDirectory $referenceStage `
    -CurrentDirectory $currentStage `
    -OutputRoot $reportStage `
    -Kind $Action
New-VisualRegressionComparisonStage `
    -ReportDirectory $reportStage `
    -OutputDirectory (Join-Path $suitePublish $baseDirectory) `
    -Kind $Action
New-VisualRegressionGridStage `
    -ReportDirectory $reportStage `
    -GridDirectory $gridDirectory `
    -OutputDirectory (Join-Path $suitePublish $gridDirectory)
