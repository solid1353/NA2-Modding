[CmdletBinding()]
param([Parameter(Mandatory)][string]$Recording)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
if ([IO.Path]::GetFileName($Recording) -cne $Recording) {
    throw 'Recording must be a shared input-recording filename or stem.'
}
$recordingName = [IO.Path]::GetFileNameWithoutExtension($Recording)
$context = Get-VisualRegressionContext -Suite $recordingName
if ((Test-Path -LiteralPath $context.SuiteRoot) -or
    (Test-Path -LiteralPath $context.CaptureRoot)) {
    throw "Visual-regression suite already exists: $recordingName"
}

. (Join-Path $context.Repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$recordingFilename = if ($Recording.EndsWith('.p2m2', [StringComparison]::OrdinalIgnoreCase)) {
    [IO.Path]::GetFileName($Recording)
}
else {
    "$Recording.p2m2"
}
$recordingPath = [IO.Path]::GetFullPath((
    Join-Path $paths.pcsx2_input_recordings $recordingFilename
))
if (-not (Test-Path -LiteralPath $recordingPath -PathType Leaf)) {
    throw "Input recording does not exist: $recordingPath"
}

$transaction = New-VisualRegressionTransaction `
    -Root $context.Root `
    -Prefix 'new'
$capture = Join-Path $transaction 'runtime-capture'
$suiteStage = Join-Path $transaction $recordingName
$captureStage = Join-Path $transaction 'capture-data'
try {
    & (Join-Path $context.Repository 'na228.ps1') `
        nun5 -t $recordingFilename -o $capture
    $capturedScreenshots = Join-Path $capture 'screenshots'
    if (@(Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File).Count -eq 0) {
        throw 'NUN5 reference replay completed without captured screenshots.'
    }

    $referenceScreenshots = Join-Path $captureStage 'references'
    $approvedScreenshots = Join-Path $captureStage 'approved'
    $suiteStates = Join-Path $captureStage 'sstates'
    [void](New-Item -ItemType Directory -Path `
        $suiteStage, `
        $referenceScreenshots, $approvedScreenshots -Force)
    Copy-Item -LiteralPath $recordingPath -Destination (Join-Path $suiteStage 'input.p2m2')
    Get-ChildItem -LiteralPath $capturedScreenshots -File |
        Copy-Item -Destination $referenceScreenshots
    $capturedStates = Join-Path $capture 'sstates'
    if (Test-Path -LiteralPath $capturedStates -PathType Container) {
        [void](New-Item -ItemType Directory -Path $suiteStates -Force)
        Get-ChildItem -LiteralPath $capturedStates -File |
            Copy-Item -Destination $suiteStates
    }

    $manifestRows = foreach ($slot in (Get-NumericPngSlots -Directory $referenceScreenshots)) {
        [pscustomobject]@{
            slot = $slot
            family = 'unclassified'
            screen = "Slot {0:D4}" -f $slot
            notes = ''
        }
    }
    $manifestRows | Export-Csv `
        -LiteralPath (Join-Path $suiteStage 'screens.tsv') `
        -Delimiter "`t" -NoTypeInformation -Encoding utf8

    [void](New-Item `
        -ItemType Directory `
        -Path `
            ([IO.Path]::GetDirectoryName($context.SuiteRoot)), `
            ([IO.Path]::GetDirectoryName($context.CaptureRoot)) `
        -Force)
    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{
            $context.SuiteRoot = $suiteStage
            $context.CaptureRoot = $captureStage
        }) `
        -TransactionRoot $transaction
    Write-Host "Created visual-regression suite: $recordingName" -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
    $suitesRoot = Join-Path $context.Root 'suites'
    if ((Test-Path -LiteralPath $suitesRoot -PathType Container) -and
        @(Get-ChildItem -LiteralPath $suitesRoot -Force).Count -eq 0) {
        Remove-Item -LiteralPath $suitesRoot -Force
    }
    $capturesRoot = Join-Path $context.Root 'captures'
    if ((Test-Path -LiteralPath $capturesRoot -PathType Container) -and
        @(Get-ChildItem -LiteralPath $capturesRoot -Force).Count -eq 0) {
        Remove-Item -LiteralPath $capturesRoot -Force
    }
}
