$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'config.ps1')
$script:E2eCaptureTiers = [ordered]@{
    Reference = 'reference'
    Current = 'current'
}
$script:E2eGeneratedMovesetSuiteName = 'movesets'
$script:E2eGeneratedIdleSuiteName = 'characters/idle'
$script:E2eGeneratedSuiteNames = @(
    $script:E2eGeneratedMovesetSuiteName,
    $script:E2eGeneratedIdleSuiteName
)
$script:E2eScreenshotKinds = [ordered]@{
    Reference = [pscustomobject]@{ Order = 'a'; Label = 'reference' }
    Current = [pscustomobject]@{ Order = 'b'; Label = 'current' }
    Blend = [pscustomobject]@{ Order = 'c'; Label = 'blend' }
    Diff = [pscustomobject]@{ Order = 'd'; Label = 'diff' }
    Pair = [pscustomobject]@{ Order = 'e'; Label = 'pair' }
}
$script:E2eAllGridDirectory = 'all'
$script:E2eCaptureRepositoryMetadataNames = @('.git', '.gitattributes', '.gitignore')
$script:E2eScreenshotGridDirectory = 'screenshots'
$script:E2ePairGridDirectory = 'pairs'
$script:E2eBlendGridDirectory = 'blends'
$script:E2eDiffGridDirectory = 'diffs'
$script:E2eStableCaptureDirectories = @(
    $script:E2eScreenshotGridDirectory,
    $script:E2ePairGridDirectory,
    $script:E2eBlendGridDirectory,
    $script:E2eDiffGridDirectory
)
$script:E2eRepositoryState = $null

. (Join-Path $PSScriptRoot 'lib\files.ps1')
. (Join-Path $PSScriptRoot 'lib\suites.ps1')
. (Join-Path $PSScriptRoot 'lib\tasks.ps1')
. (Join-Path $PSScriptRoot 'lib\captures.ps1')
. (Join-Path $PSScriptRoot 'lib\artifacts.ps1')
. (Join-Path $PSScriptRoot 'lib\transactions.ps1')
. (Join-Path $PSScriptRoot 'lib\replay.ps1')
