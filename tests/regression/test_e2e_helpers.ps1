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
        -Condition ((@($configuration.Variants.name) -join ',') -ceq 'normal,padded') `
        -Message 'E2E configuration did not expose normal and padded variants.'
    Assert-E2eHelperTest `
        -Condition ([string]$configuration.PublishedVariant.name -ceq 'normal') `
        -Message 'E2E configuration did not select normal as the published variant.'
    Assert-E2eHelperTest `
        -Condition ($configuration.AllVariants[1].ignored -eq $false) `
        -Message 'The padded variant is not explicitly active.'

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
      "payload_padding_bytes": 0,
      "publish": true
    },
    {
      "name": "padded",
      "build": "e2e_test_padded",
      "payload_padding_bytes": 32,
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
            (@($ignoredVariantConfiguration.AllVariants.name) -join ',') -ceq 'normal,padded'
        ) `
        -Message 'An ignored build variant was not excluded from the active variants.'

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
      "payload_padding_bytes": 0,
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
    $stale = Join-Path $transactions 'run-stale'
    [void](New-Item -ItemType Directory -Path $legacy, $stale -Force)
    [IO.File]::WriteAllText(
        (Join-Path $stale 'owner.json'),
        '{"schema_version":1,"pid":2147483647,"process_start_utc":"2000-01-01T00:00:00.0000000Z"}'
    )
    $transaction = New-VisualRegressionTransaction -Root $testRoot -Prefix 'run'
    Assert-E2eHelperTest `
        -Condition (-not (Test-Path -LiteralPath $stale)) `
        -Message 'A metadata-owned abandoned E2E transaction was not removed.'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath $legacy -PathType Container) `
        -Message 'A legacy transaction without ownership metadata was removed.'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath (Join-Path $transaction 'owner.json') -PathType Leaf) `
        -Message 'A new E2E transaction did not record its owner.'

    $normal = Join-Path $testRoot 'normal'
    $padded = Join-Path $testRoot 'padded'
    $comparison = Join-Path $testRoot 'comparison'
    [void](New-Item -ItemType Directory -Path $normal, $padded -Force)
    [IO.File]::WriteAllBytes((Join-Path $normal '0001.png'), [byte[]](1, 2, 3))
    [IO.File]::WriteAllBytes((Join-Path $padded '0001.png'), [byte[]](1, 2, 3))
    [IO.File]::WriteAllBytes((Join-Path $normal '0002.png'), [byte[]](4))
    [IO.File]::WriteAllBytes((Join-Path $padded '0002.png'), [byte[]](5))
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
        -CandidateDirectory $padded `
        -OutputRoot $comparison `
        -IgnoreFile $ignore
    Assert-E2eHelperTest -Condition ($passed.status -ceq 'passed') `
        -Message 'Ignored variant differences incorrectly failed stability comparison.'

    Remove-Item -LiteralPath $comparison -Recurse -Force
    [IO.File]::WriteAllText($ignore, '')
    $failed = Compare-VisualRegressionVariants `
        -Suite 'test/helpers' `
        -BaselineDirectory $normal `
        -CandidateDirectory $padded `
        -OutputRoot $comparison `
        -IgnoreFile $ignore
    Assert-E2eHelperTest -Condition ($failed.status -ceq 'failed') `
        -Message 'A real normal/padded screenshot difference was not detected.'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath (Join-Path $comparison 'differences\normal\0002.png')) `
        -Message 'Normal evidence for a failed variant comparison was not retained.'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath (Join-Path $comparison 'differences\padded\0002.png')) `
        -Message 'Padded evidence for a failed variant comparison was not retained.'

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
param([string]$Suite, [string]$Game)
Add-Content -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') -Value "reference suite=$Suite game=$Game"
'@
    )
    [IO.File]::WriteAllText(
        (Join-Path $fakeScripts 'run.ps1'),
        @'
param([string]$Suite)
Add-Content -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') -Value "run suite=$Suite"
'@
    )
    [IO.File]::WriteAllText((Join-Path $fakeRecordings 'first.p2m2'), 'first')
    [IO.File]::WriteAllText((Join-Path $fakeRecordings 'second.p2m2'), 'second')
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/no_reference' `
        -Recording 'first'
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
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/no_reference' `
        -Recording 'second'
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $firstSuiteRoot 'input.p2m2')) -ceq 'second' -and
            (Get-Item -LiteralPath $firstIgnore).Length -eq 0 -and
            -not (Test-Path -LiteralPath (Join-Path $firstSuiteRoot 'stale.txt')) -and
            (Test-Path -LiteralPath $firstCaptureRoot -PathType Container) -and
            @(Get-ChildItem -LiteralPath $firstCaptureRoot -Recurse -Force).Count -eq 0
        ) `
        -Message 'Existing suite definition or capture history was not completely replaced.'
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/with_reference' `
        -Recording 'second.p2m2' `
        -Game 'nun5'
    $newSuiteCalls = @(Get-Content -LiteralPath (Join-Path $fakeScripts 'calls.txt'))
    Assert-E2eHelperTest `
        -Condition (
            $newSuiteCalls.Count -eq 4 -and
            $newSuiteCalls[0] -ceq 'run suite=test/no_reference' -and
            $newSuiteCalls[1] -ceq 'run suite=test/no_reference' -and
            $newSuiteCalls[2] -ceq 'reference suite=test/with_reference game=nun5' -and
            $newSuiteCalls[3] -ceq 'run suite=test/with_reference'
        ) `
        -Message 'Suite creation or replacement did not order optional reference capture before the mandatory run.'

    $sourceCaptureRoot = Join-Path $fakeRepository 'e2e\captures\test\with_reference'
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
