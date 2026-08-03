[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Suite
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')

$context = Get-VisualRegressionContext -Suite $Suite
$configurationPath = Join-Path $context.SuiteRoot 'stability.json'
if (-not (Test-Path -LiteralPath $configurationPath -PathType Leaf)) {
    throw "Stability suite configuration does not exist: $configurationPath"
}
$configuration = Get-Content -Raw -LiteralPath $configurationPath | ConvertFrom-Json
if (
    [int]$configuration.schema_version -ne 1 -or
    [string]::IsNullOrWhiteSpace([string]$configuration.recording_suite) -or
    [int]$configuration.padding_bytes -le 0
) {
    throw "Invalid stability suite configuration: $configurationPath"
}
$padding = [int]$configuration.padding_bytes
if ($padding -gt 65536 -or $padding % 16 -ne 0) {
    throw 'Stability-suite padding must be a 16-byte multiple through 65536.'
}

$recordingContext = Get-VisualRegressionContext `
    -Suite ([string]$configuration.recording_suite)
$recordingPath = Join-Path $recordingContext.SuiteRoot 'input.p2m2'
if (-not (Test-Path -LiteralPath $recordingPath -PathType Leaf)) {
    throw "Stability-suite recording does not exist: $recordingPath"
}
. (Join-Path $context.Repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$buildScript = Join-Path $context.Repository 'scripts\na228\build.ps1'
$transaction = New-VisualRegressionTransaction `
    -Root $context.Root `
    -Prefix 'stability'
$probeRoot = Join-Path $transaction 'probe'
$normalRoot = Join-Path $transaction 'normal'

function Invoke-StabilityBuild {
    param([Parameter(Mandatory)][int]$PaddingBytes)

    $output = @(
        & $buildScript `
            -ScreenshotTestOnly `
            -PayloadPadding $PaddingBytes
    )
    $result = @(
        $output | Where-Object {
            $_.PSObject.Properties.Name -contains 'Status' -and
            $_.Status -ceq 'screenshot-test'
        }
    ) | Select-Object -Last 1
    if ($null -eq $result) {
        throw "Stability build returned no valid result for padding $PaddingBytes."
    }
}

function Invoke-StabilityReplay {
    param([Parameter(Mandatory)][string]$CaptureRoot)

    Invoke-VisualRegressionReplay `
        -Repository $context.Repository `
        -SharedRecordingRoot $paths.pcsx2_input_recordings `
        -RecordingPath $recordingPath `
        -Game st `
        -CaptureRoot $CaptureRoot
    $screenshots = Join-Path $CaptureRoot 'screenshots'
    if (
        -not (Test-Path -LiteralPath $screenshots -PathType Container) -or
        @(Get-ChildItem -LiteralPath $screenshots -Filter '*.png' -File).Count -eq 0
    ) {
        throw "Stability replay produced no screenshots: $CaptureRoot"
    }
    return $screenshots
}

try {
    try {
        Invoke-StabilityBuild -PaddingBytes $padding
        $probeScreenshots = Invoke-StabilityReplay -CaptureRoot $probeRoot
    }
    finally {
        Invoke-StabilityBuild -PaddingBytes 0
    }
    $normalScreenshots = Invoke-StabilityReplay -CaptureRoot $normalRoot

    $probeFiles = @(
        Get-ChildItem -LiteralPath $probeScreenshots -Filter '*.png' -File |
            Sort-Object Name
    )
    $normalFiles = @(
        Get-ChildItem -LiteralPath $normalScreenshots -Filter '*.png' -File |
            Sort-Object Name
    )
    $ignored = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $ignoredNames = @(
        Get-IgnoredCaptureNames `
            -IgnoreFile (Join-Path $recordingContext.SuiteRoot 'ignore.txt')
    )
    if ($ignoredNames.Count -gt 0) {
        $ignored.UnionWith([string[]]$ignoredNames)
        $probeFiles = @($probeFiles | Where-Object { -not $ignored.Contains($_.Name) })
        $normalFiles = @($normalFiles | Where-Object { -not $ignored.Contains($_.Name) })
    }
    $probeNames = @($probeFiles.Name)
    $normalNames = @($normalFiles.Name)
    $nameDifferences = @(Compare-Object $probeNames $normalNames)
    if ($nameDifferences.Count -gt 0) {
        throw 'Heap-stability replays produced different screenshot sets.'
    }

    $changed = [Collections.Generic.List[string]]::new()
    foreach ($probe in $probeFiles) {
        $normal = Join-Path $normalScreenshots $probe.Name
        $probeHash = (Get-FileHash -LiteralPath $probe.FullName -Algorithm SHA256).Hash
        $normalHash = (Get-FileHash -LiteralPath $normal -Algorithm SHA256).Hash
        if ($probeHash -cne $normalHash) {
            $changed.Add($probe.Name)
        }
    }
    if ($changed.Count -gt 0) {
        throw (
            'Heap-stability screenshots differ: ' +
            ($changed -join ', ')
        )
    }

    Write-Host (
        "E2E heap stability verified: $($probeFiles.Count) screenshots are " +
        "identical with and without $padding bytes of payload padding; " +
        "$($ignored.Count) base-suite captures were ignored."
    ) -ForegroundColor Green
    [pscustomobject]@{
        Suite = $Suite
        Status = 'verified'
        Screenshots = $probeFiles.Count
    }
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
