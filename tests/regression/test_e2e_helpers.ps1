[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
. (Join-Path $repository 'e2e\scripts\config.ps1')
. (Join-Path $repository 'e2e\scripts\suite.ps1')

function Assert-E2eHelperTest {
    param(
        [Parameter(Mandatory)][bool]$Condition,
        [Parameter(Mandatory)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

$testRoot = Join-Path (
    [IO.Path]::GetTempPath()
) "na2-e2e-helper-tests-$PID-$([guid]::NewGuid().ToString('N'))"
try {
    [void](New-Item -ItemType Directory -Path $testRoot -Force)
    $configuration = Get-E2eConfiguration -Root (Join-Path $repository 'e2e')
    Assert-E2eHelperTest `
        -Condition ((@($configuration.Variants.name) -join ',') -ceq 'normal,shifted') `
        -Message 'E2E configuration did not expose normal and shifted variants.'
    Assert-E2eHelperTest `
        -Condition ([string]$configuration.PublishedVariant.name -ceq 'normal') `
        -Message 'E2E configuration did not select normal as the published variant.'
    Assert-E2eHelperTest `
        -Condition ($configuration.AllVariants[1].ignored -eq $false) `
        -Message 'The shifted variant is not explicitly active.'

    $ignoredVariantRoot = Join-Path $testRoot 'ignored-variant-config'
    [void](New-Item -ItemType Directory -Path $ignoredVariantRoot -Force)
    [IO.File]::WriteAllText(
        (Join-Path $ignoredVariantRoot 'config.json'),
        @'
{
  "schema_version": 1,
  "build_variants": [
    {
      "name": "normal",
      "build": "e2e_test",
      "payload_shift_bytes": 0,
      "publish": true
    },
    {
      "name": "shifted",
      "build": "e2e_test_shifted",
      "payload_shift_bytes": 32,
      "ignored": true,
      "compare_against": "normal"
    }
  ]
}
'@
    )
    $ignoredVariantConfiguration = Get-E2eConfiguration -Root $ignoredVariantRoot
    Assert-E2eHelperTest `
        -Condition (
            (@($ignoredVariantConfiguration.Variants.name) -join ',') -ceq 'normal' -and
            (@($ignoredVariantConfiguration.AllVariants.name) -join ',') -ceq 'normal,shifted'
        ) `
        -Message 'An ignored build variant was not excluded from the active variants.'
    $ignoredBuildVariant = Get-E2eBuildVariant `
        -Name 'shifted' `
        -Root $ignoredVariantRoot
    Assert-E2eHelperTest `
        -Condition (
            [string]$ignoredBuildVariant.name -ceq 'shifted' -and
            $ignoredBuildVariant.ignored -eq $true
        ) `
        -Message 'An ignored build variant was unavailable to explicit build resolution.'

    $invalidVariantRoot = Join-Path $testRoot 'invalid-variant-config'
    [void](New-Item -ItemType Directory -Path $invalidVariantRoot -Force)
    [IO.File]::WriteAllText(
        (Join-Path $invalidVariantRoot 'config.json'),
        @'
{
  "schema_version": 1,
  "build_variants": [
    {
      "name": "normal",
      "build": "e2e_test",
      "payload_shift_bytes": 0,
      "publish": true,
      "ignored": "false"
    }
  ]
}
'@
    )
    $invalidIgnoredRejected = $false
    try {
        [void](Get-E2eConfiguration -Root $invalidVariantRoot)
    }
    catch {
        $invalidIgnoredRejected = $_.Exception.Message -match 'ignored must be a boolean'
    }
    Assert-E2eHelperTest `
        -Condition $invalidIgnoredRejected `
        -Message 'A non-boolean build-variant ignored field was accepted.'

    $transactions = Join-Path $testRoot '.transactions'
    $legacy = Join-Path $transactions 'legacy-without-owner'
    $recent = Join-Path $transactions 'recent-without-owner'
    $stale = Join-Path $transactions 'run-stale'
    [void](New-Item -ItemType Directory -Path $legacy, $recent, $stale -Force)
    (Get-Item -LiteralPath $legacy).LastWriteTimeUtc = [DateTime]::UtcNow.AddMinutes(-2)
    [IO.File]::WriteAllText(
        (Join-Path $stale 'owner.json'),
        '{"schema_version":1,"pid":2147483647,"process_start_utc":"2000-01-01T00:00:00.0000000Z"}'
    )
    $transaction = New-VisualRegressionTransaction -Root $testRoot -Prefix 'run'
    Assert-E2eHelperTest `
        -Condition (-not (Test-Path -LiteralPath $stale)) `
        -Message 'A metadata-owned abandoned E2E transaction was not removed.'
    Assert-E2eHelperTest `
        -Condition (-not (Test-Path -LiteralPath $legacy)) `
        -Message 'An old ownerless E2E transaction was not removed.'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath $recent -PathType Container) `
        -Message 'A newly created ownerless transaction was not protected from the creation race.'
    $transactionOwner = Get-Content -Raw -LiteralPath (Join-Path $transaction 'owner.json') |
        ConvertFrom-Json
    Assert-E2eHelperTest `
        -Condition (
            [int]$transactionOwner.schema_version -eq 2 -and
            [long]$transactionOwner.process_start_file_time_utc -eq
                (Get-Process -Id $PID).StartTime.ToFileTimeUtc()
        ) `
        -Message 'A new E2E transaction did not record a stable process identity.'
    (Get-Item -LiteralPath $recent).LastWriteTimeUtc = [DateTime]::UtcNow.AddMinutes(-2)
    $nestedTransaction = New-VisualRegressionTransaction -Root $testRoot -Prefix 'nested'
    Assert-E2eHelperTest `
        -Condition (
            (Test-Path -LiteralPath $transaction -PathType Container) -and
            -not (Test-Path -LiteralPath $recent)
        ) `
        -Message 'Nested same-shell ownership or aged ownerless cleanup was incorrect.'
    Set-VisualRegressionTransactionRetained `
        -Transaction $nestedTransaction `
        -Root $testRoot
    $sweepTransaction = New-VisualRegressionTransaction -Root $testRoot -Prefix 'sweep'
    Assert-E2eHelperTest `
        -Condition (
            -not (Test-Path -LiteralPath $nestedTransaction) -and
            (Test-Path -LiteralPath $transaction -PathType Container)
        ) `
        -Message 'A completed failed transaction remained pinned to its live interactive shell.'
    Remove-VisualRegressionTransaction -Transaction $sweepTransaction -Root $testRoot

    $normal = Join-Path $testRoot 'normal'
    $shifted = Join-Path $testRoot 'shifted'
    $comparison = Join-Path $testRoot 'comparison'
    [void](New-Item -ItemType Directory -Path $normal, $shifted -Force)
    [IO.File]::WriteAllBytes((Join-Path $normal '0001.png'), [byte[]](1, 2, 3))
    [IO.File]::WriteAllBytes((Join-Path $shifted '0001.png'), [byte[]](1, 2, 3))
    [IO.File]::WriteAllBytes((Join-Path $normal '0002.png'), [byte[]](4))
    [IO.File]::WriteAllBytes((Join-Path $shifted '0002.png'), [byte[]](5))
    $ignore = Join-Path $testRoot 'ignore.txt'
    [IO.File]::WriteAllText($ignore, "# ignored captures`n2`n004`n5-7`n")
    $ignoredNames = @(Get-IgnoredCaptureNames -IgnoreFile $ignore)
    Assert-E2eHelperTest `
        -Condition (($ignoredNames -join ',') -ceq '0002.png,0004.png,0005.png,0006.png,0007.png') `
        -Message 'Ignore slots, zero padding, comments, or ranges were parsed incorrectly.'
    [IO.File]::WriteAllText($ignore, "0002.png`n")
    $legacyIgnoreRejected = $false
    try {
        [void](Get-IgnoredCaptureNames -IgnoreFile $ignore)
    }
    catch {
        $legacyIgnoreRejected = $_.Exception.Message -match 'Invalid ignore entry'
    }
    Assert-E2eHelperTest `
        -Condition $legacyIgnoreRejected `
        -Message 'The retired ignore filename format was accepted.'
    [IO.File]::WriteAllText($ignore, "# ignored captures`n2`n004`n5-7`n")
    $passed = Compare-VisualRegressionVariants `
        -Suite 'test/helpers' `
        -BaselineDirectory $normal `
        -CandidateDirectory $shifted `
        -CandidateName 'shifted' `
        -OutputRoot $comparison `
        -IgnoreFile $ignore
    Assert-E2eHelperTest -Condition ($passed.status -ceq 'passed') `
        -Message 'Ignored variant differences incorrectly failed stability comparison.'

    Remove-Item -LiteralPath $comparison -Recurse -Force
    [IO.File]::WriteAllText($ignore, '')
    $failed = Compare-VisualRegressionVariants `
        -Suite 'test/helpers' `
        -BaselineDirectory $normal `
        -CandidateDirectory $shifted `
        -CandidateName 'shifted' `
        -OutputRoot $comparison `
        -IgnoreFile $ignore
    Assert-E2eHelperTest -Condition ($failed.status -ceq 'failed') `
        -Message 'A real normal/shifted screenshot difference was not detected.'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath (Join-Path $comparison 'differences\normal\0002.png')) `
        -Message 'Normal evidence for a failed variant comparison was not retained.'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath (Join-Path $comparison 'differences\shifted\0002.png')) `
        -Message 'Shifted evidence for a failed variant comparison was not retained.'

    $qualification = Join-Path $testRoot 'qualification'
    $qualificationComparison = Join-Path `
        $qualification `
        'comparisons\shifted\test\helpers'
    $repeatComparison = Join-Path `
        $qualification `
        'comparisons\normal-repeat\test\helpers'
    [void](New-Item -ItemType Directory -Path $qualificationComparison -Force)
    Copy-Item -Path (Join-Path $comparison '*') `
        -Destination $qualificationComparison `
        -Recurse
    [void](Compare-VisualRegressionVariants `
        -Suite 'test/helpers' `
        -BaselineDirectory $normal `
        -CandidateDirectory $shifted `
        -CandidateName 'normal-repeat' `
        -OutputRoot $repeatComparison `
        -IgnoreFile $ignore)
    foreach ($variant in @('normal', 'normal-repeat', 'shifted')) {
        $states = Join-Path `
            $qualification `
            "jobs\$variant\suites\test\helpers\capture\sstates"
        [void](New-Item -ItemType Directory -Path $states -Force)
        [IO.File]::WriteAllText((Join-Path $states '0001.p2s'), 'matching')
        [IO.File]::WriteAllText((Join-Path $states '0002.p2s'), $variant)
    }
    [IO.File]::WriteAllText((Join-Path $qualification 'owner.json'), 'discarded')
    Preserve-VisualRegressionMismatchEvidence `
        -Transaction $qualification `
        -ComparisonVariant @('normal-repeat', 'shifted')
    $qualificationFiles = @(
        Get-ChildItem -LiteralPath $qualification -Recurse -File |
            ForEach-Object {
                [IO.Path]::GetRelativePath($qualification, $_.FullName).Replace('\', '/')
            } |
            Sort-Object
    )
    Assert-E2eHelperTest `
        -Condition (
            ($qualificationFiles -join ',') -ceq (
                'normal-repeat/test/helpers/report/result.json,' +
                'normal-repeat/test/helpers/screenshots/normal-repeat/0002.png,' +
                'normal-repeat/test/helpers/screenshots/normal/0002.png,' +
                'normal-repeat/test/helpers/sstates/normal-repeat/0002.p2s,' +
                'normal-repeat/test/helpers/sstates/normal/0002.p2s,' +
                'shifted/test/helpers/report/result.json,' +
                'shifted/test/helpers/screenshots/normal/0002.png,' +
                'shifted/test/helpers/screenshots/shifted/0002.png,' +
                'shifted/test/helpers/sstates/normal/0002.p2s,' +
                'shifted/test/helpers/sstates/shifted/0002.p2s'
            )
        ) `
        -Message 'Failed qualification retained more or less than its mismatch evidence.'

    $firstDestination = Join-Path $testRoot 'published\one\current'
    $secondDestination = Join-Path $testRoot 'published\two\current'
    $firstSource = Join-Path $testRoot 'sources\one\current'
    $secondSource = Join-Path $testRoot 'sources\two\current'
    [void](New-Item -ItemType Directory -Path `
        $firstDestination, $secondDestination, $firstSource, $secondSource -Force)
    [IO.File]::WriteAllText((Join-Path $firstDestination 'old.txt'), 'old-one')
    [IO.File]::WriteAllText((Join-Path $secondDestination 'old.txt'), 'old-two')
    [IO.File]::WriteAllText((Join-Path $firstSource 'new.txt'), 'new-one')
    [IO.File]::WriteAllText((Join-Path $secondSource 'new.txt'), 'new-two')
    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{
            $firstDestination = $firstSource
            $secondDestination = $secondSource
        }) `
        -TransactionRoot $transaction
    Assert-E2eHelperTest `
        -Condition ([IO.File]::ReadAllText((Join-Path $firstDestination 'new.txt')) -ceq 'new-one') `
        -Message 'First same-name capture directory was not published.'
    Assert-E2eHelperTest `
        -Condition ([IO.File]::ReadAllText((Join-Path $secondDestination 'new.txt')) -ceq 'new-two') `
        -Message 'Second same-name capture directory was not published.'

    $stateDestination = Join-Path $testRoot 'published\states\sstates'
    $stateSource = Join-Path $testRoot 'sources\states\sstates'
    [void](New-Item -ItemType Directory -Path $stateDestination, $stateSource -Force)
    [IO.File]::WriteAllText((Join-Path $stateDestination '0001.p2s'), 'old')
    [IO.File]::WriteAllText((Join-Path $stateDestination 'stale.p2s'), 'stale')
    [IO.File]::WriteAllText((Join-Path $stateSource '0001.p2s'), 'new')
    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{ $stateDestination = $stateSource }) `
        -TransactionRoot $transaction
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $stateDestination '0001.p2s')) -ceq 'new' -and
            -not (Test-Path -LiteralPath (Join-Path $stateDestination 'stale.p2s')) -and
            (Test-Path -LiteralPath (Join-Path $stateSource '0001.p2s') -PathType Leaf)
        ) `
        -Message 'Savestates were not synchronized without moving their staged directory.'

    $fakeRepository = Join-Path $testRoot 'suite-lifecycle-repository'
    $fakeScripts = Join-Path $fakeRepository 'e2e\scripts'
    $fakeRecordings = Join-Path $testRoot 'shared-recordings'
    [void](New-Item -ItemType Directory -Path `
        $fakeScripts, `
        (Join-Path $fakeRepository 'e2e\captures'), `
        (Join-Path $fakeRepository 'scripts\lib'), `
        $fakeRecordings `
        -Force)
    Copy-Item -LiteralPath (Join-Path $repository 'e2e\scripts\suite.ps1') `
        -Destination (Join-Path $fakeScripts 'suite.ps1')
    Copy-Item -LiteralPath (Join-Path $repository 'e2e\scripts\create_suite.ps1') `
        -Destination (Join-Path $fakeScripts 'create_suite.ps1')
    Copy-Item -LiteralPath (Join-Path $repository 'e2e\scripts\rename_suite.ps1') `
        -Destination (Join-Path $fakeScripts 'rename_suite.ps1')
    Copy-Item -LiteralPath (Join-Path $repository 'e2e\scripts\delete_suite.ps1') `
        -Destination (Join-Path $fakeScripts 'delete_suite.ps1')
    [IO.File]::WriteAllText(
        (Join-Path $fakeRepository 'scripts\lib\paths.ps1'),
        @"
function Get-Na2Paths {
    [pscustomobject]@{ pcsx2_input_recordings = '$($fakeRecordings.Replace("'", "''"))' }
}
"@
    )
    [IO.File]::WriteAllText(
        (Join-Path $fakeScripts 'reference.ps1'),
        @'
param(
    [string]$Suite,
    [string]$Game,
    [string]$CaptureOutputRoot,
    [string]$CapturedRoot,
    [string]$CaptureRoot
)
$sync = Join-Path $PSScriptRoot 'sync'
[void](New-Item -ItemType Directory -Path $sync -Force)
if (-not [string]::IsNullOrWhiteSpace($CaptureOutputRoot)) {
    [IO.File]::WriteAllText((Join-Path $sync 'reference-started'), '')
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    while (-not (Test-Path -LiteralPath (Join-Path $sync 'run-started'))) {
        if ([DateTime]::UtcNow -ge $deadline) {
            throw 'The test run did not overlap the reference capture.'
        }
        Start-Sleep -Milliseconds 20
    }
    [void](New-Item -ItemType Directory -Path (Join-Path $CaptureOutputRoot 'screenshots') -Force)
    [IO.File]::WriteAllText((Join-Path $CaptureOutputRoot 'screenshots\0001.png'), 'reference')
    Add-Content -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') -Value "reference-capture suite=$Suite game=$Game"
    return
}
[void](New-Item -ItemType Directory -Path $CaptureRoot -Force)
[IO.File]::WriteAllText((Join-Path $CaptureRoot 'reference.txt'), 'reference')
Add-Content -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') -Value "reference-publish suite=$Suite"
'@
    )
    [IO.File]::WriteAllText(
        (Join-Path $fakeScripts 'run.ps1'),
        @'
param(
    [string]$Suite,
    [string]$CaptureRoot,
    [switch]$Shifted,
    [switch]$RepeatNormal
)
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'fail-run')) {
    throw 'synthetic run failure'
}
if ($Suite -ceq 'test/with_reference') {
    $sync = Join-Path $PSScriptRoot 'sync'
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    while (-not (Test-Path -LiteralPath (Join-Path $sync 'reference-started'))) {
        if ([DateTime]::UtcNow -ge $deadline) {
            throw 'Reference capture did not start alongside the test run.'
        }
        Start-Sleep -Milliseconds 20
    }
}
Add-Content -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') -Value (
    "run suite=$Suite shifted=$($Shifted.IsPresent) " +
    "repeatNormal=$($RepeatNormal.IsPresent)"
)
if ($Suite -ceq 'test/with_reference') {
    [IO.File]::WriteAllText((Join-Path $sync 'run-started'), '')
}
[void](New-Item -ItemType Directory -Path $CaptureRoot -Force)
[IO.File]::WriteAllText((Join-Path $CaptureRoot 'current.txt'), 'current')
'@
    )
    $noReferenceRecording = Join-Path $fakeRecordings 'test\no_reference.p2m2'
    $withReferenceRecording = Join-Path $fakeRecordings 'test\with_reference.p2m2'
    [void](New-Item -ItemType Directory -Path (
        [IO.Path]::GetDirectoryName($noReferenceRecording)
    ) -Force)
    [IO.File]::WriteAllText($noReferenceRecording, 'first')
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/no_reference'
    $firstIgnore = Join-Path $fakeRepository 'e2e\suites\test\no_reference\ignore.txt'
    Assert-E2eHelperTest `
        -Condition (
            (Test-Path -LiteralPath $firstIgnore -PathType Leaf) -and
            (Get-Item -LiteralPath $firstIgnore).Length -eq 0
        ) `
        -Message 'Suite creation did not generate an empty ignore.txt.'
    $firstSuiteRoot = Split-Path $firstIgnore
    $firstCaptureRoot = Join-Path $fakeRepository 'e2e\captures\test\no_reference'
    [IO.File]::WriteAllText($firstIgnore, "1`n")
    [IO.File]::WriteAllText((Join-Path $firstSuiteRoot 'stale.txt'), 'stale suite data')
    [void](New-Item -ItemType Directory -Path (
        Join-Path $firstCaptureRoot 'screenshots'
    ) -Force)
    [IO.File]::WriteAllText(
        (Join-Path $firstCaptureRoot 'screenshots\001_b_current.png'),
        'stale capture data'
    )
    [IO.File]::WriteAllText($noReferenceRecording, 'second')
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/no_reference'
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $firstSuiteRoot 'input.p2m2')) -ceq 'second' -and
            (Get-Item -LiteralPath $firstIgnore).Length -eq 0 -and
            -not (Test-Path -LiteralPath (Join-Path $firstSuiteRoot 'stale.txt')) -and
            (Test-Path -LiteralPath $firstCaptureRoot -PathType Container) -and
            [IO.File]::ReadAllText((Join-Path $firstCaptureRoot 'current.txt')) -ceq 'current' -and
            -not (Test-Path -LiteralPath (
                Join-Path $firstCaptureRoot 'screenshots\001_b_current.png'
            ))
        ) `
        -Message 'Existing suite definition or capture history was not completely replaced.'
    [IO.File]::WriteAllText($withReferenceRecording, 'second')
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/with_reference' `
        -Game 'nun5'
    $newSuiteCalls = @(Get-Content -LiteralPath (Join-Path $fakeScripts 'calls.txt'))
    Assert-E2eHelperTest `
        -Condition (
            $newSuiteCalls.Count -eq 5 -and
            $newSuiteCalls[0] -ceq 'run suite=test/no_reference shifted=False repeatNormal=True' -and
            $newSuiteCalls[1] -ceq 'run suite=test/no_reference shifted=False repeatNormal=True' -and
            $newSuiteCalls[2] -ceq 'run suite=test/with_reference shifted=False repeatNormal=True' -and
            $newSuiteCalls[3] -ceq 'reference-capture suite=test/with_reference game=nun5' -and
            $newSuiteCalls[4] -ceq 'reference-publish suite=test/with_reference'
        ) `
        -Message 'Suite creation did not overlap reference capture with the mandatory run before publication.'

    $sourceCaptureRoot = Join-Path $fakeRepository 'e2e\captures\test\with_reference'
    [IO.File]::WriteAllText((Join-Path $sourceCaptureRoot 'accepted.txt'), 'accepted history')
    [IO.File]::WriteAllText((Join-Path $fakeScripts 'fail-run'), '')
    [IO.File]::WriteAllText($withReferenceRecording, 'first')
    $replacementFailed = $false
    try {
        & (Join-Path $fakeScripts 'create_suite.ps1') `
            -Suite 'test/with_reference'
    }
    catch {
        $replacementFailed = $true
    }
    Remove-Item -LiteralPath (Join-Path $fakeScripts 'fail-run') -Force
    Assert-E2eHelperTest `
        -Condition (
            $replacementFailed -and
            [IO.File]::ReadAllText((Join-Path $fakeRepository 'e2e\suites\test\with_reference\input.p2m2')) -ceq 'second' -and
            [IO.File]::ReadAllText((Join-Path $sourceCaptureRoot 'accepted.txt')) -ceq 'accepted history'
        ) `
        -Message 'Failed suite replacement did not restore its previous definition and capture history.'
    [IO.File]::WriteAllText((Join-Path $sourceCaptureRoot 'capture.txt'), 'capture history')
    & (Join-Path $fakeScripts 'rename_suite.ps1') `
        -Suite 'test/with_reference' `
        -NewSuite 'renamed/with_reference'
    $renamedSuiteRoot = Join-Path $fakeRepository 'e2e\suites\renamed\with_reference'
    $renamedCaptureRoot = Join-Path $fakeRepository 'e2e\captures\renamed\with_reference'
    Assert-E2eHelperTest `
        -Condition (
            -not (Test-Path -LiteralPath (Join-Path $fakeRepository 'e2e\suites\test\with_reference')) -and
            -not (Test-Path -LiteralPath $sourceCaptureRoot) -and
            (Test-Path -LiteralPath (Join-Path $renamedSuiteRoot 'input.p2m2') -PathType Leaf) -and
            [IO.File]::ReadAllText((Join-Path $renamedCaptureRoot 'capture.txt')) -ceq 'capture history'
        ) `
        -Message 'Suite rename did not move both the definition and capture history.'
    & (Join-Path $fakeScripts 'delete_suite.ps1') -Suite 'renamed/with_reference'
    Assert-E2eHelperTest `
        -Condition (
            -not (Test-Path -LiteralPath $renamedSuiteRoot) -and
            -not (Test-Path -LiteralPath $renamedCaptureRoot) -and
            -not (Test-Path -LiteralPath (Join-Path $fakeRepository 'e2e\suites\renamed')) -and
            -not (Test-Path -LiteralPath (Join-Path $fakeRepository 'e2e\captures\renamed'))
        ) `
        -Message 'Suite deletion did not remove both roots and their empty parents.'

    Remove-VisualRegressionTransaction -Transaction $transaction -Root $testRoot
    Write-Host 'E2E helper tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
