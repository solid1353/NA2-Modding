[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Suite,
    [switch]$f
)

$ErrorActionPreference = 'Stop'
if (-not $f) {
    throw 'Usage: na228 test reference <suite> -f'
}

. (Join-Path $PSScriptRoot 'suite.ps1')
$context = Get-VisualRegressionContext -Suite $Suite
if (-not (Test-Path -LiteralPath $context.SuiteRoot -PathType Container)) {
    throw "Visual-regression suite does not exist: $Suite"
}
$recordingPath = Join-Path $context.SuiteRoot 'input.p2m2'
if (-not (Test-Path -LiteralPath $recordingPath -PathType Leaf)) {
    throw "Suite recording does not exist: $recordingPath"
}

. (Join-Path $context.Repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$recordingFilename = "$Suite.p2m2"
$sharedRecording = Join-Path $paths.pcsx2_input_recordings $recordingFilename
if (-not (Test-Path -LiteralPath $sharedRecording -PathType Leaf)) {
    throw "Shared replay recording does not exist: $sharedRecording"
}
if ((Get-FileHash -LiteralPath $recordingPath -Algorithm SHA256).Hash -cne
    (Get-FileHash -LiteralPath $sharedRecording -Algorithm SHA256).Hash) {
    throw 'The shared replay recording differs from the suite-tracked recording.'
}

$transaction = New-VisualRegressionTransaction `
    -Root $context.Root `
    -Prefix 'reference'
$captureRoot = Join-Path $transaction 'capture'
$referenceStage = Join-Path $transaction 'references'
$referenceScreenshots = Join-Path $referenceStage 'screenshots'
$reportsStage = Join-Path $transaction 'reports'
$scratch = Join-Path $transaction 'scratch'

try {
    [void](New-Item -ItemType Directory -Path $referenceScreenshots, $scratch -Force)
    & (Join-Path $context.Repository 'na228.ps1') `
        nun5 -t $recordingFilename -o $captureRoot
    $capturedScreenshots = Join-Path $captureRoot 'screenshots'
    if (@(Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File).Count -eq 0) {
        throw 'NUN5 reference replay completed without captured screenshots.'
    }
    Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File |
        Copy-Item -Destination $referenceScreenshots

    New-VisualRegressionReports `
        -Suite $Suite `
        -ReferenceRoot $referenceStage `
        -PendingRoot (Join-Path $context.CaptureRoot 'pending') `
        -OutputRoot $reportsStage `
        -ScratchRoot $scratch
    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{
            (Join-Path $context.CaptureRoot 'references\screenshots') = $referenceScreenshots
            (Join-Path $context.CaptureRoot 'reports') = $reportsStage
        }) `
        -TransactionRoot $transaction
    Write-Host 'Reference screenshots and reports were replaced atomically.' -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
