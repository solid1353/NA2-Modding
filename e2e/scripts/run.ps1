[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Suite,
    [switch]$b
)

$ErrorActionPreference = 'Stop'
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
$sharedRecording = Join-Path $paths.pcsx2_input_recordings "$Suite.p2m2"
if (-not (Test-Path -LiteralPath $sharedRecording -PathType Leaf)) {
    throw "Shared replay recording does not exist: $sharedRecording"
}
if ((Get-FileHash -LiteralPath $recordingPath -Algorithm SHA256).Hash -cne
    (Get-FileHash -LiteralPath $sharedRecording -Algorithm SHA256).Hash) {
    throw 'The shared replay recording differs from the suite-tracked recording.'
}
$transaction = New-VisualRegressionTransaction `
    -Root $context.Root `
    -Prefix 'run'
$captureRoot = Join-Path $transaction 'capture'
$pendingStage = Join-Path $transaction 'pending'
$reportsStage = Join-Path $transaction 'reports'
$scratch = Join-Path $transaction 'scratch'

try {
    [void](New-Item -ItemType Directory -Path $pendingStage, $scratch -Force)

    if ($b) {
        $build = & (Join-Path $context.Repository 'scripts\na228\build.ps1') -ScreenshotTestOnly
        if (-not $build -or $build.Status -ne 'screenshot-test') {
            throw 'Screenshot Test build did not return a valid result.'
        }
    }
    elseif (-not (Test-Path -LiteralPath $paths.files.screenshot_test_iso -PathType Leaf)) {
        throw 'Screenshot Test.iso does not exist; rerun with -b.'
    }

    & (Join-Path $context.Repository 'na228.ps1') `
        st -t $Suite -o $captureRoot
    if (-not (Test-Path -LiteralPath $captureRoot -PathType Container)) {
        throw "Replay completed without a capture directory: $captureRoot"
    }
    $capturedScreenshots = Join-Path $captureRoot 'screenshots'
    if (@(Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File).Count -eq 0) {
        throw 'Replay completed without captured screenshots.'
    }
    Copy-Item -LiteralPath $capturedScreenshots -Destination $pendingStage -Recurse
    $capturedStates = Join-Path $captureRoot 'sstates'
    if (Test-Path -LiteralPath $capturedStates -PathType Container) {
        Copy-Item -LiteralPath $capturedStates -Destination $pendingStage -Recurse
    }

    New-VisualRegressionReports `
        -Suite $Suite `
        -PendingRoot $pendingStage `
        -OutputRoot $reportsStage `
        -ScratchRoot $scratch
    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{
            (Join-Path $context.CaptureRoot 'pending') = $pendingStage
            (Join-Path $context.CaptureRoot 'reports') = $reportsStage
        }) `
        -TransactionRoot $transaction
    $pendingSlots = @(Get-NumericPngSlots -Directory (Join-Path $context.CaptureRoot 'pending\screenshots'))
    $approvedDirectory = Join-Path $context.CaptureRoot 'approved\screenshots'
    $approvedSlots = @(Get-NumericPngSlots -Directory $approvedDirectory)
    $clean = $pendingSlots.Count -eq $approvedSlots.Count
    if ($clean) {
        foreach ($slot in $pendingSlots) {
            $pendingFile = Get-ChildItem `
                -LiteralPath (Join-Path $context.CaptureRoot 'pending\screenshots') `
                -Filter '*.png' -File |
                Where-Object { $_.BaseName -match '(\d+)$' -and [int]$Matches[1] -eq $slot } |
                Select-Object -First 1
            $approvedFile = Get-ChildItem -LiteralPath $approvedDirectory -Filter '*.png' -File |
                Where-Object { $_.BaseName -match '(\d+)$' -and [int]$Matches[1] -eq $slot } |
                Select-Object -First 1
            if ($null -eq $approvedFile -or
                (Get-FileHash -LiteralPath $pendingFile.FullName -Algorithm SHA256).Hash -cne
                (Get-FileHash -LiteralPath $approvedFile.FullName -Algorithm SHA256).Hash) {
                $clean = $false
                break
            }
        }
    }
    $status = if ($clean) { 'clean' } else { 'review-required' }
    Write-Host (
        "Visual-regression batch completed ($status). " +
        'Pending captures and reports were replaced atomically.'
    ) -ForegroundColor $(if ($clean) { 'Green' } else { 'Yellow' })
    [pscustomobject]@{
        Suite = $Suite
        Status = $status
        PendingScreenshots = $pendingSlots.Count
        ApprovedScreenshots = $approvedSlots.Count
    }
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
