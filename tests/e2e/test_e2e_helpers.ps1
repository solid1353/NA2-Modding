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

    $omittedSuites = @(
        Get-VisualRegressionRequestedSuiteNames `
            -Suite $null `
            -WasSpecified $false
    )
    $selectedSuites = @(
        Get-VisualRegressionRequestedSuiteNames `
            -Suite @('collection/characters', 'collection/figures') `
            -WasSpecified $true
    )
    $blankSuiteRejected = $false
    try {
        Get-VisualRegressionRequestedSuiteNames `
            -Suite @('collection/characters', '') `
            -WasSpecified $true
    }
    catch {
        $blankSuiteRejected = $_.Exception.Message -ceq (
            'Suite cannot contain an empty name.'
        )
    }
    Assert-E2eHelperTest `
        -Condition (
            $omittedSuites.Count -eq 0 -and
            ($selectedSuites -join ',') -ceq (
                'collection/characters,collection/figures'
            ) -and
            $blankSuiteRejected
        ) `
        -Message 'E2E suite selection did not distinguish omission from an explicitly blank name.'

    foreach ($runnerName in @('run.ps1', 'variant.ps1')) {
        $tokens = $null
        $parseErrors = $null
        $runnerPath = Join-Path $repository "e2e\scripts\$runnerName"
        $runnerAst = [Management.Automation.Language.Parser]::ParseFile(
            $runnerPath,
            [ref]$tokens,
            [ref]$parseErrors
        )
        $suiteIteratorCollisions = @(
            $runnerAst.FindAll(
                {
                    param($node)
                    $node -is [Management.Automation.Language.ForEachStatementAst] -and
                    $node.Variable.VariablePath.UserPath -ieq 'Suite'
                },
                $true
            )
        )
        Assert-E2eHelperTest `
            -Condition (
                $parseErrors.Count -eq 0 -and
                $suiteIteratorCollisions.Count -eq 0
            ) `
            -Message "$runnerName reuses the typed Suite parameter as a foreach iterator."
    }

    foreach ($jobKind in @('thread', 'process')) {
        $jobCommand = if ($jobKind -ceq 'thread') { 'Start-ThreadJob' } else { 'Start-Job' }
        $failedJob = & $jobCommand -Name "$jobKind-synthetic-failure" -ScriptBlock {
            Start-Sleep -Milliseconds 100
            throw 'synthetic replay failure'
        }
        $blockedJob = & $jobCommand -Name "$jobKind-synthetic-blocked-sibling" -ScriptBlock {
            Start-Sleep -Seconds 30
        }
        $failureStopwatch = [Diagnostics.Stopwatch]::StartNew()
        $failureMessage = $null
        try {
            Wait-VisualRegressionJobs `
                -Job @($failedJob, $blockedJob) `
                -FailurePrefix 'Synthetic E2E job' 2>$null
        }
        catch {
            $failureMessage = $_.Exception.Message
        }
        finally {
            $failureStopwatch.Stop()
            foreach ($job in @($failedJob, $blockedJob)) {
                if ($job.State -in @('NotStarted', 'Running')) {
                    Stop-Job -Job $job -ErrorAction SilentlyContinue
                }
                Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
            }
        }
        Assert-E2eHelperTest `
            -Condition (
                $failureMessage -match 'synthetic-failure.*synthetic replay failure' -and
                $failureStopwatch.Elapsed.TotalSeconds -lt 5
            ) `
            -Message "$jobKind E2E job supervision did not report a failed child immediately."
        Assert-E2eHelperTest `
            -Condition ($blockedJob.State -eq 'Stopped') `
            -Message "$jobKind E2E job supervision did not stop a running sibling after failure."
    }

    $graphRoot = Join-Path $testRoot 'task-graph'
    [void](New-Item -ItemType Directory -Path $graphRoot -Force)
    $firstMarker = Join-Path $graphRoot 'first.txt'
    $dependentMarker = Join-Path $graphRoot 'dependent.txt'
    $firstTask = [pscustomobject]@{
        Key = 'synthetic/first'
        DependsOn = @()
        Ready = $null
        Start = {
            Start-ThreadJob -Name 'synthetic/first' -ScriptBlock {
                param($Marker)
                [IO.File]::WriteAllText($Marker, 'first')
            } -ArgumentList $firstMarker
        }.GetNewClosure()
    }
    $dependentTask = [pscustomobject]@{
        Key = 'synthetic/dependent'
        DependsOn = @('synthetic/first')
        Ready = $null
        Start = {
            Start-ThreadJob -Name 'synthetic/dependent' -ScriptBlock {
                param($RequiredMarker, $Marker)
                if (-not (Test-Path -LiteralPath $RequiredMarker -PathType Leaf)) {
                    throw 'dependency marker was absent'
                }
                [IO.File]::WriteAllText($Marker, 'dependent')
            } -ArgumentList $firstMarker, $dependentMarker
        }.GetNewClosure()
    }
    Invoke-VisualRegressionTaskGraph `
        -Task @($dependentTask, $firstTask) `
        -ThrottleLimit 2
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath $dependentMarker -PathType Leaf) `
        -Message 'The bounded E2E task graph did not honor a declared dependency.'

    $graphFailure = [pscustomobject]@{
        Key = 'synthetic/failure'
        DependsOn = @()
        Ready = $null
        Start = {
            Start-ThreadJob -Name 'synthetic/failure' -ScriptBlock {
                Start-Sleep -Milliseconds 100
                throw 'synthetic graph failure'
            }
        }
    }
    $graphBlocked = [pscustomobject]@{
        Key = 'synthetic/blocked'
        DependsOn = @()
        Ready = $null
        Start = {
            Start-ThreadJob -Name 'synthetic/blocked' -ScriptBlock {
                Start-Sleep -Seconds 30
            }
        }
    }
    $graphFailureStopwatch = [Diagnostics.Stopwatch]::StartNew()
    $graphFailureMessage = $null
    try {
        Invoke-VisualRegressionTaskGraph `
            -Task @($graphFailure, $graphBlocked) `
            -ThrottleLimit 2 `
            -FailurePrefix 'Synthetic graph task' 2>$null
    }
    catch {
        $graphFailureMessage = $_.Exception.Message
    }
    finally {
        $graphFailureStopwatch.Stop()
    }
    Assert-E2eHelperTest `
        -Condition (
            $graphFailureMessage -match 'synthetic/failure.*synthetic graph failure' -and
            $graphFailureStopwatch.Elapsed.TotalSeconds -lt 5
        ) `
        -Message 'The bounded E2E task graph did not fail fast with the exact failed task.'

    $activeVariantRoot = Join-Path $testRoot 'active-variant-config'
    [void](New-Item -ItemType Directory -Path $activeVariantRoot -Force)
    [IO.File]::WriteAllText(
        (Join-Path $activeVariantRoot 'config.json'),
        @'
{
  "schema_version": 1,
  "build_variants": [
    {
      "name": "baseline",
      "build": "baseline_build",
      "payload_shift_bytes": 0,
      "publish": true
    },
    {
      "name": "qualified",
      "build": "qualified_build",
      "payload_shift_bytes": 16,
      "ignored": false,
      "compare_against": "baseline"
    }
  ]
}
'@
    )
    $configuration = Get-E2eConfiguration -Root $activeVariantRoot
    Assert-E2eHelperTest `
        -Condition ((@($configuration.Variants.name) -join ',') -ceq 'baseline,qualified') `
        -Message 'E2E configuration did not expose both active synthetic variants.'
    Assert-E2eHelperTest `
        -Condition ([string]$configuration.PublishedVariant.name -ceq 'baseline') `
        -Message 'E2E configuration did not select the published synthetic variant.'
    Assert-E2eHelperTest `
        -Condition ($configuration.AllVariants[1].ignored -eq $false) `
        -Message 'The qualified synthetic variant is not explicitly active.'

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

    $layoutRoot = Join-Path $testRoot ('capture-layout-' + ('x' * 128))
    $layoutReference = Join-Path $layoutRoot 'reference'
    $layoutCurrent = Join-Path $layoutRoot 'current'
    $layoutReport = Join-Path $layoutRoot 'report'
    $layoutPublish = Join-Path $layoutRoot 'publish'
    foreach ($directory in @(
        $layoutReference,
        $layoutCurrent,
        (Join-Path $layoutReport 'base-pairs'),
        (Join-Path $layoutReport 'base-blends'),
        (Join-Path $layoutReport 'base-diffs'),
        (Join-Path $layoutReport 'grid-screenshots'),
        (Join-Path $layoutReport 'grid-pairs'),
        (Join-Path $layoutReport 'grid-blends'),
        (Join-Path $layoutReport 'grid-diffs')
    )) {
        [void](New-Item -ItemType Directory -Path $directory -Force)
    }
    [IO.File]::WriteAllText((Join-Path $layoutReference '0001.png'), 'reference')
    [IO.File]::WriteAllText((Join-Path $layoutCurrent '0001.png'), 'current')
    [IO.File]::WriteAllText((Join-Path $layoutReport 'base-pairs\0001.png'), 'pair')
    [IO.File]::WriteAllText((Join-Path $layoutReport 'base-blends\0001.png'), 'blend')
    [IO.File]::WriteAllText((Join-Path $layoutReport 'base-diffs\0001.png'), 'diff')
    [IO.File]::WriteAllText(
        (Join-Path $layoutReport 'grid-screenshots\page_01_a_reference.png'),
        'reference grid'
    )
    [IO.File]::WriteAllText(
        (Join-Path $layoutReport 'grid-screenshots\page_01_b_current.png'),
        'current grid'
    )
    [IO.File]::WriteAllText((Join-Path $layoutReport 'grid-pairs\page_01.png'), 'pair grid')
    [IO.File]::WriteAllText(
        (Join-Path $layoutReport 'grid-blends\page_01.png'),
        'blend grid'
    )
    [IO.File]::WriteAllText(
        (Join-Path $layoutReport 'grid-diffs\page_01.png'),
        'diff grid'
    )
    New-VisualRegressionScreenshotStage `
        -ReferenceDirectory $layoutReference `
        -CurrentDirectory $layoutCurrent `
        -OutputDirectory (Join-Path $layoutPublish 'base-screenshots')
    foreach ($comparison in @(
        [pscustomobject]@{ Kind = 'Pair'; Directory = 'base-pairs' },
        [pscustomobject]@{ Kind = 'Blend'; Directory = 'base-blends' },
        [pscustomobject]@{ Kind = 'Diff'; Directory = 'base-diffs' }
    )) {
        New-VisualRegressionComparisonStage `
            -ReportDirectory $layoutReport `
            -OutputDirectory (Join-Path $layoutPublish $comparison.Directory) `
            -Kind $comparison.Kind
    }
    New-VisualRegressionAggregateLinkStage `
        -Source @(
            [pscustomobject]@{
                Directory = (Join-Path $layoutPublish 'base-screenshots')
                Suffix = ''
            },
            [pscustomobject]@{ Directory = (Join-Path $layoutPublish 'base-blends'); Suffix = '' },
            [pscustomobject]@{ Directory = (Join-Path $layoutPublish 'base-diffs'); Suffix = '' }
        ) `
        -OutputDirectory (Join-Path $layoutPublish 'base-all')
    New-VisualRegressionGridStage `
        -ReportDirectory $layoutReport `
        -GridDirectory 'grid-screenshots' `
        -OutputDirectory (Join-Path $layoutPublish 'grid-screenshots')
    New-VisualRegressionGridStage `
        -ReportDirectory $layoutReport `
        -GridDirectory 'grid-pairs' `
        -OutputDirectory (Join-Path $layoutPublish 'grid-pairs')
    New-VisualRegressionGridStage `
        -ReportDirectory $layoutReport `
        -GridDirectory 'grid-blends' `
        -OutputDirectory (Join-Path $layoutPublish 'grid-blends')
    New-VisualRegressionGridStage `
        -ReportDirectory $layoutReport `
        -GridDirectory 'grid-diffs' `
        -OutputDirectory (Join-Path $layoutPublish 'grid-diffs')
    New-VisualRegressionAggregateLinkStage `
        -Source @(
            [pscustomobject]@{
                Directory = (Join-Path $layoutPublish 'grid-screenshots')
                Suffix = ''
            },
            [pscustomobject]@{
                Directory = (Join-Path $layoutPublish 'grid-blends')
                Suffix = 'c_blend'
            },
            [pscustomobject]@{
                Directory = (Join-Path $layoutPublish 'grid-diffs')
                Suffix = 'd_diff'
            }
        ) `
        -OutputDirectory (Join-Path $layoutPublish 'grid-all')
    $layoutFiles = @(
        Get-ChildItem -LiteralPath $layoutPublish -Recurse -File |
            ForEach-Object {
                [IO.Path]::GetRelativePath($layoutPublish, $_.FullName).Replace('\', '/')
            } |
            Sort-Object
    )
    Assert-E2eHelperTest `
        -Condition (
            ($layoutFiles -join ',') -ceq (
                'base-all/001_a_reference.png,' +
                'base-all/001_b_current.png,' +
                'base-all/001_c_blend.png,' +
                'base-all/001_d_diff.png,' +
                'base-blends/001_c_blend.png,' +
                'base-diffs/001_d_diff.png,' +
                'base-pairs/001_e_pair.png,' +
                'base-screenshots/001_a_reference.png,' +
                'base-screenshots/001_b_current.png,' +
                'grid-all/page_01_a_reference.png,' +
                'grid-all/page_01_b_current.png,' +
                'grid-all/page_01_c_blend.png,' +
                'grid-all/page_01_d_diff.png,' +
                'grid-blends/page_01.png,' +
                'grid-diffs/page_01.png,' +
                'grid-pairs/page_01.png,' +
                'grid-screenshots/page_01_a_reference.png,' +
                'grid-screenshots/page_01_b_current.png'
            )
        ) `
        -Message (
            'Capture artifacts were not separated into the flat published layout. Actual: ' +
            ($layoutFiles -join ',')
        )
    [IO.File]::WriteAllText(
        (Join-Path $layoutPublish 'base-blends\001_c_blend.png'),
        'updated blend'
    )
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText(
                (Join-Path $layoutPublish 'base-all\001_c_blend.png')
            ) -ceq 'updated blend'
        ) `
        -Message 'The all view did not reuse its canonical blend through a hardlink.'

    $aggregateContext = [pscustomobject]@{
        SuiteRelativePath = 'capture-layout'
        Capture = [pscustomobject]@{
            Screenshots = Join-Path $layoutPublish 'base-screenshots'
            Pairs = Join-Path $layoutPublish 'base-pairs'
            Blends = Join-Path $layoutPublish 'base-blends'
            Diffs = Join-Path $layoutPublish 'base-diffs'
            All = Join-Path $layoutPublish 'base-all'
            ScreenshotGrids = Join-Path $layoutPublish 'grid-screenshots'
            PairGrids = Join-Path $layoutPublish 'grid-pairs'
            BlendGrids = Join-Path $layoutPublish 'grid-blends'
            DiffGrids = Join-Path $layoutPublish 'grid-diffs'
            AllGrids = Join-Path $layoutPublish 'grid-all'
        }
    }
    Publish-VisualRegressionAggregateViews `
        -Context @($aggregateContext) `
        -TransactionRoot (Join-Path $layoutRoot 'aggregate-transaction')
    Assert-E2eHelperTest `
        -Condition (
            -not (Test-Path -LiteralPath (
                Join-Path $layoutPublish 'base-all\001_e_pair.png'
            )) -and
            -not (Test-Path -LiteralPath (
                Join-Path $layoutPublish 'grid-all\page_01_e_pair.png'
            ))
        ) `
        -Message 'Aggregate publication included a pair view.'
    [IO.File]::WriteAllText(
        (Join-Path $layoutPublish 'grid-diffs\page_01.png'),
        'updated diff grid'
    )
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText(
                (Join-Path $layoutPublish 'grid-all\page_01_d_diff.png')
            ) -ceq 'updated diff grid'
        ) `
        -Message 'Aggregate publication did not retain hardlinks to canonical grid pages.'

    $callbackRoot = Join-Path $layoutRoot 'callback-rollback'
    $callbackSource = Join-Path $callbackRoot 'source'
    $callbackDestination = Join-Path $callbackRoot 'destination'
    [void](New-Item -ItemType Directory -Path $callbackSource, $callbackDestination -Force)
    [IO.File]::WriteAllText((Join-Path $callbackSource 'new.txt'), 'new')
    [IO.File]::WriteAllText((Join-Path $callbackDestination 'old.txt'), 'old')
    $callbackFailed = $false
    try {
        Publish-VisualRegressionTransaction `
            -Replacements ([ordered]@{ $callbackDestination = $callbackSource }) `
            -TransactionRoot (Join-Path $callbackRoot 'transaction') `
            -AfterPublish { throw 'callback failure' }
    }
    catch {
        $callbackFailed = $_.Exception.Message -ceq 'callback failure'
    }
    Assert-E2eHelperTest `
        -Condition (
            $callbackFailed -and
            (Test-Path -LiteralPath (Join-Path $callbackDestination 'old.txt')) -and
            -not (Test-Path -LiteralPath (Join-Path $callbackDestination 'new.txt'))
        ) `
        -Message 'A failed post-publication callback did not roll back canonical publication.'

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
    $failed = Compare-VisualRegressionVariants `
        -Suite 'test/helpers' `
        -BaselineDirectory $normal `
        -CandidateDirectory $shifted `
        -CandidateName 'shifted' `
        -OutputRoot $comparison
    Assert-E2eHelperTest `
        -Condition (
            $failed.status -ceq 'failed' -and
            $failed.PSObject.Properties.Name -notcontains 'ignored'
        ) `
        -Message 'A normal/shifted difference was not mandatory or still exposed ignore state.'
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
        -OutputRoot $repeatComparison)
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

    $lockedDestination = Join-Path $testRoot 'published\locked\sstates'
    $lockedSource = Join-Path $testRoot 'sources\locked\sstates'
    $lockedPath = Join-Path $lockedDestination '0025.p2s'
    $lockReady = Join-Path $testRoot 'locked-file-ready'
    [void](New-Item -ItemType Directory -Path $lockedDestination, $lockedSource -Force)
    [IO.File]::WriteAllText($lockedPath, 'old locked state')
    [IO.File]::WriteAllText((Join-Path $lockedSource '0025.p2s'), 'new state')
    $lockJob = Start-ThreadJob -Name 'synthetic-transient-file-reader' -ScriptBlock {
        param($Path, $Ready)
        $stream = [IO.File]::Open(
            $Path,
            [IO.FileMode]::Open,
            [IO.FileAccess]::Read,
            [IO.FileShare]::None
        )
        try {
            [IO.File]::WriteAllText($Ready, '')
            Start-Sleep -Milliseconds 500
        }
        finally {
            $stream.Dispose()
        }
    } -ArgumentList $lockedPath, $lockReady
    try {
        $lockDeadline = [DateTime]::UtcNow.AddSeconds(5)
        while (-not (Test-Path -LiteralPath $lockReady -PathType Leaf)) {
            if ([DateTime]::UtcNow -ge $lockDeadline) {
                throw 'Synthetic file reader did not acquire its lock.'
            }
            Start-Sleep -Milliseconds 20
        }
        Publish-VisualRegressionTransaction `
            -Replacements ([ordered]@{ $lockedDestination = $lockedSource }) `
            -TransactionRoot $transaction
    }
    finally {
        Wait-Job -Job $lockJob -Timeout 5 | Out-Null
        if ($lockJob.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $lockJob -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $lockJob -Force -ErrorAction SilentlyContinue
    }
    Assert-E2eHelperTest `
        -Condition ([IO.File]::ReadAllText($lockedPath) -ceq 'new state') `
        -Message 'Atomic E2E publication did not tolerate a transient file reader.'

    $fakeCommitRoot = Join-Path $testRoot 'g'
    $fakeCommitScripts = Join-Path $fakeCommitRoot 'e2e\scripts'
    $fakeSuiteRepository = Join-Path $fakeCommitRoot 'e2e\suites'
    $fakeCaptureRepository = Join-Path $fakeCommitRoot 'e2e\captures'
    [void](New-Item -ItemType Directory -Path `
        $fakeCommitScripts, `
        $fakeSuiteRepository, `
        $fakeCaptureRepository `
        -Force)
    Copy-Item -LiteralPath (Join-Path $repository 'e2e\scripts\commit_captures.ps1') `
        -Destination (Join-Path $fakeCommitScripts 'commit_captures.ps1')
    $previousGitIdentity = @{
        AuthorName = $env:GIT_AUTHOR_NAME
        AuthorEmail = $env:GIT_AUTHOR_EMAIL
        CommitterName = $env:GIT_COMMITTER_NAME
        CommitterEmail = $env:GIT_COMMITTER_EMAIL
    }
    try {
        $env:GIT_AUTHOR_NAME = 'E2E Helper Test'
        $env:GIT_AUTHOR_EMAIL = 'e2e-helper-test@agent.invalid'
        $env:GIT_COMMITTER_NAME = 'E2E Helper Test'
        $env:GIT_COMMITTER_EMAIL = 'e2e-helper-test@agent.invalid'

        & git -C $fakeCommitRoot init --initial-branch=main | Out-Null
        [IO.File]::WriteAllText((Join-Path $fakeCommitRoot 'unrelated.txt'), 'original')
        & git -C $fakeCommitRoot add --all
        & git -C $fakeCommitRoot commit -m 'Initial main commit' | Out-Null

        & git -C $fakeCaptureRepository init --initial-branch=main | Out-Null
        [IO.File]::WriteAllText((Join-Path $fakeCaptureRepository 'capture.txt'), 'capture')
        & git -C $fakeCaptureRepository add --all
        & git -C $fakeCaptureRepository commit -m 'Initial commit' | Out-Null

        [IO.File]::WriteAllText(
            (Join-Path $fakeSuiteRepository 'test.p2m2'),
            'suite recording'
        )
        [IO.File]::WriteAllText((Join-Path $fakeCommitRoot 'unrelated.txt'), 'staged unrelated')
        & git -C $fakeCommitRoot add -- 'unrelated.txt'
        Remove-Item -LiteralPath (Join-Path $fakeCaptureRepository 'capture.txt') -Force
        & (Join-Path $fakeCommitScripts 'commit_captures.ps1')

        [IO.File]::WriteAllText(
            (Join-Path $fakeSuiteRepository 'test.p2m2'),
            'updated suite recording'
        )
        & (Join-Path $fakeCommitScripts 'commit_captures.ps1') -Preserve

        Remove-Item -LiteralPath $fakeSuiteRepository -Recurse -Force
        & (Join-Path $fakeCommitScripts 'commit_captures.ps1') -Preserve
    }
    finally {
        $env:GIT_AUTHOR_NAME = $previousGitIdentity.AuthorName
        $env:GIT_AUTHOR_EMAIL = $previousGitIdentity.AuthorEmail
        $env:GIT_COMMITTER_NAME = $previousGitIdentity.CommitterName
        $env:GIT_COMMITTER_EMAIL = $previousGitIdentity.CommitterEmail
    }
    Assert-E2eHelperTest `
        -Condition (
            [int](& git -C $fakeCaptureRepository rev-list --count HEAD) -eq 1 -and
            @(& git -C $fakeCaptureRepository ls-tree -r --name-only HEAD).Count -eq 0 -and
            @(& git -C $fakeCaptureRepository status --porcelain).Count -eq 0 -and
            [string](& git -C $fakeCaptureRepository log -1 --format='%s') -ceq 'Initial commit' -and
            [int](& git -C $fakeCommitRoot rev-list --count HEAD) -eq 4 -and
            [string](& git -C $fakeCommitRoot log -1 --format='%s') -ceq 'Update E2E suites' -and
            (@(
                & git -C $fakeCommitRoot show --format= --name-only HEAD |
                    Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
            ) -join ',') -ceq 'e2e/suites/test.p2m2' -and
            (@(& git -C $fakeCommitRoot diff --cached --name-only) -join ',') -ceq 'unrelated.txt' -and
            @(& git -C $fakeCommitRoot ls-tree -r --name-only HEAD -- 'e2e/suites').Count -eq 0
        ) `
        -Message 'E2E update did not commit only suites across capture modes while preserving unrelated staging.'

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
        (Join-Path $fakeScripts 'publish_references.ps1'),
        @'
param(
    [string[]]$Suite,
    [string]$CapturedRepository,
    [string]$CaptureRepository
)
foreach ($suiteName in $Suite) {
    $captureRoot = Join-Path $CaptureRepository $suiteName.Replace('/', [IO.Path]::DirectorySeparatorChar)
    [void](New-Item -ItemType Directory -Path $captureRoot -Force)
    [IO.File]::WriteAllText((Join-Path $captureRoot 'reference.txt'), 'reference')
    Add-Content -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') -Value "reference-publish suite=$suiteName"
}
'@
    )
    [IO.File]::WriteAllText(
        (Join-Path $fakeScripts 'run.ps1'),
        @'
param(
    [string[]]$Suite,
    [string]$CaptureRoot,
    [string]$CaptureRepository,
    [switch]$Shifted,
    [switch]$RepeatNormal,
    [object[]]$SupervisedJob
)
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'fail-run')) {
    throw 'synthetic run failure'
}
$suites = [string[]]@($Suite)
$hasReferenceSuite = $suites -ccontains 'test/with_reference'
if ($hasReferenceSuite) {
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
    "run suite=$($suites -join ',') shifted=$($Shifted.IsPresent) " +
    "repeatNormal=$($RepeatNormal.IsPresent)"
)
if ($hasReferenceSuite) {
    [IO.File]::WriteAllText((Join-Path $sync 'run-started'), '')
}
foreach ($suiteName in $suites) {
    $suiteCaptureRoot = if (-not [string]::IsNullOrWhiteSpace($CaptureRoot)) {
        $CaptureRoot
    }
    else {
        Join-Path $CaptureRepository $suiteName.Replace('/', [IO.Path]::DirectorySeparatorChar)
    }
    [void](New-Item -ItemType Directory -Path $suiteCaptureRoot -Force)
    [IO.File]::WriteAllText((Join-Path $suiteCaptureRoot 'current.txt'), 'current')
}
'@
    )
    $noReferenceRecording = Join-Path $fakeRecordings 'test\no_reference.p2m2'
    $withReferenceRecording = Join-Path $fakeRecordings 'test\with_reference.p2m2'
    [void](New-Item -ItemType Directory -Path (
        [IO.Path]::GetDirectoryName($noReferenceRecording)
    ) -Force)
    [IO.File]::WriteAllText($noReferenceRecording, 'first')
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/no_reference' `
        -NoReference
    $firstSuitePath = Join-Path $fakeRepository 'e2e\suites\test\no_reference.p2m2'
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText($firstSuitePath) -ceq 'first' -and
            @(Get-ChildItem `
                -LiteralPath (Join-Path $fakeRepository 'e2e\suites') `
                -Filter 'ignore.txt' `
                -File `
                -Recurse).Count -eq 0
        ) `
        -Message 'Suite creation did not produce one flat .p2m2 definition without ignores.'
    $firstCaptureRoot = Join-Path $fakeRepository 'e2e\captures\test\no_reference'
    [void](New-Item -ItemType Directory -Path (
        Join-Path $firstCaptureRoot 'base-screenshots'
    ) -Force)
    [IO.File]::WriteAllText(
        (Join-Path $firstCaptureRoot 'base-screenshots\001_b_current.png'),
        'stale capture data'
    )
    [IO.File]::WriteAllText($noReferenceRecording, 'second')
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/no_reference' `
        -NoReference
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText($firstSuitePath) -ceq 'second' -and
            (Test-Path -LiteralPath $firstCaptureRoot -PathType Container) -and
            [IO.File]::ReadAllText((Join-Path $firstCaptureRoot 'current.txt')) -ceq 'current' -and
            -not (Test-Path -LiteralPath (
                Join-Path $firstCaptureRoot 'base-screenshots\001_b_current.png'
            ))
        ) `
        -Message 'Existing suite definition or capture history was not completely replaced.'
    [IO.File]::WriteAllText($withReferenceRecording, 'second')
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/with_reference'
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
    $suiteNames = @(
        Get-VisualRegressionSuiteNames `
            -SuiteRepository (Join-Path $fakeRepository 'e2e\suites')
    )
    Assert-E2eHelperTest `
        -Condition (($suiteNames -join ',') -ceq 'test/no_reference,test/with_reference') `
        -Message 'Flat .p2m2 suite discovery did not return canonical extensionless names.'

    $sourceCaptureRoot = Join-Path $fakeRepository 'e2e\captures\test\with_reference'
    [IO.File]::WriteAllText((Join-Path $sourceCaptureRoot 'accepted.txt'), 'accepted history')
    [IO.File]::WriteAllText((Join-Path $fakeScripts 'fail-run'), '')
    [IO.File]::WriteAllText($withReferenceRecording, 'first')
    $replacementFailed = $false
    try {
        & (Join-Path $fakeScripts 'create_suite.ps1') `
            -Suite 'test/with_reference' `
            -NoReference
    }
    catch {
        $replacementFailed = $true
    }
    Remove-Item -LiteralPath (Join-Path $fakeScripts 'fail-run') -Force
    Assert-E2eHelperTest `
        -Condition (
            $replacementFailed -and
            [IO.File]::ReadAllText((Join-Path $fakeRepository 'e2e\suites\test\with_reference.p2m2')) -ceq 'second' -and
            [IO.File]::ReadAllText((Join-Path $sourceCaptureRoot 'accepted.txt')) -ceq 'accepted history'
        ) `
        -Message 'Failed suite replacement did not restore its previous definition and capture history.'
    [IO.File]::WriteAllText((Join-Path $sourceCaptureRoot 'capture.txt'), 'capture history')
    $sourceChildSuitePath = Join-Path `
        $fakeRepository `
        'e2e\suites\test\with_reference\child.p2m2'
    $sourceChildCaptureRoot = Join-Path $sourceCaptureRoot 'child'
    [void](New-Item -ItemType Directory -Path `
        ([IO.Path]::GetDirectoryName($sourceChildSuitePath)), `
        $sourceChildCaptureRoot `
        -Force)
    [IO.File]::WriteAllText($sourceChildSuitePath, 'child recording')
    [IO.File]::WriteAllText(
        (Join-Path $sourceChildCaptureRoot 'capture.txt'),
        'child history'
    )
    & (Join-Path $fakeScripts 'rename_suite.ps1') `
        -Suite 'test/with_reference' `
        -NewSuite 'renamed/with_reference'
    $renamedSuitePath = Join-Path $fakeRepository 'e2e\suites\renamed\with_reference.p2m2'
    $renamedCaptureRoot = Join-Path $fakeRepository 'e2e\captures\renamed\with_reference'
    $childSuitePath = Join-Path $fakeRepository 'e2e\suites\renamed\with_reference\child.p2m2'
    $childCaptureRoot = Join-Path $renamedCaptureRoot 'child'
    Assert-E2eHelperTest `
        -Condition (
            -not (Test-Path -LiteralPath (Join-Path $fakeRepository 'e2e\suites\test\with_reference.p2m2')) -and
            -not (Test-Path -LiteralPath $sourceChildSuitePath) -and
            -not (Test-Path -LiteralPath $sourceCaptureRoot) -and
            (Test-Path -LiteralPath $renamedSuitePath -PathType Leaf) -and
            (Test-Path -LiteralPath $childSuitePath -PathType Leaf) -and
            [IO.File]::ReadAllText((Join-Path $renamedCaptureRoot 'capture.txt')) -ceq 'capture history' -and
            [IO.File]::ReadAllText((Join-Path $childCaptureRoot 'capture.txt')) -ceq 'child history'
        ) `
        -Message 'Suite rename did not move the definition, descendants, and capture history.'
    & (Join-Path $fakeScripts 'delete_suite.ps1') -Suite 'renamed/with_reference'
    Assert-E2eHelperTest `
        -Condition (
            -not (Test-Path -LiteralPath $renamedSuitePath) -and
            -not (Test-Path -LiteralPath (Join-Path $renamedCaptureRoot 'capture.txt')) -and
            (Test-Path -LiteralPath $childSuitePath -PathType Leaf) -and
            [IO.File]::ReadAllText((Join-Path $childCaptureRoot 'capture.txt')) -ceq 'child history'
        ) `
        -Message 'Suite deletion removed a descendant suite or retained parent artifacts.'
    & (Join-Path $fakeScripts 'delete_suite.ps1') -Suite 'renamed/with_reference/child'
    Assert-E2eHelperTest `
        -Condition (
            -not (Test-Path -LiteralPath $renamedSuitePath) -and
            -not (Test-Path -LiteralPath $renamedCaptureRoot) -and
            -not (Test-Path -LiteralPath (Join-Path $fakeRepository 'e2e\suites\renamed')) -and
            -not (Test-Path -LiteralPath (Join-Path $fakeRepository 'e2e\captures\renamed'))
        ) `
        -Message 'Leaf suite deletion did not remove both roots and their empty parents.'

    $fakeCaptureGit = Join-Path $fakeRepository 'e2e\captures\.git'
    $fakeCaptureAttributes = Join-Path $fakeRepository 'e2e\captures\.gitattributes'
    $fakeCaptureIgnore = Join-Path $fakeRepository 'e2e\captures\.gitignore'
    $orphanCapture = Join-Path $fakeRepository 'e2e\captures\orphan'
    $generatedRecording = Join-Path $fakeRecordings '__generated\transient.p2m2'
    [void](New-Item -ItemType Directory -Path $fakeCaptureGit, $orphanCapture -Force)
    [void](New-Item -ItemType Directory -Path (
        [IO.Path]::GetDirectoryName($generatedRecording)
    ) -Force)
    [IO.File]::WriteAllText((Join-Path $fakeCaptureGit 'preserved.txt'), 'git metadata')
    [IO.File]::WriteAllText(
        $fakeCaptureAttributes,
        ".gitattributes text eol=lf`n.gitignore text eol=lf`n"
    )
    [IO.File]::WriteAllText(
        $fakeCaptureIgnore,
        "**/base-all/`n**/grid-all/`n"
    )
    [IO.File]::WriteAllText((Join-Path $orphanCapture 'stale.txt'), 'orphan history')
    $orphanSuite = Join-Path $fakeRepository 'e2e\suites\orphan.p2m2'
    [IO.File]::WriteAllText($orphanSuite, 'orphan suite')
    [IO.File]::WriteAllText($generatedRecording, 'transient recording')
    & (Join-Path $fakeScripts 'create_suite.ps1') -All -NoReference
    $bulkSuiteNames = @(
        Get-VisualRegressionSuiteNames `
            -SuiteRepository (Join-Path $fakeRepository 'e2e\suites')
    )
    Assert-E2eHelperTest `
        -Condition (
            ($bulkSuiteNames -join ',') -ceq 'test/no_reference,test/with_reference' -and
            (Get-Content -LiteralPath (Join-Path $fakeScripts 'calls.txt') | Select-Object -Last 1) `
                -ceq 'run suite=test/no_reference,test/with_reference shifted=False repeatNormal=True' -and
            (Test-Path -LiteralPath (
                Join-Path $fakeRepository 'e2e\captures\test\no_reference\current.txt'
            ) -PathType Leaf) -and
            (Test-Path -LiteralPath (
                Join-Path $fakeRepository 'e2e\captures\test\with_reference\current.txt'
            ) -PathType Leaf) -and
            -not (Test-Path -LiteralPath $orphanSuite) -and
            -not (Test-Path -LiteralPath $orphanCapture) -and
            [IO.File]::ReadAllText((Join-Path $fakeCaptureGit 'preserved.txt')) -ceq 'git metadata' -and
            [IO.File]::ReadAllText($fakeCaptureAttributes) -ceq (
                ".gitattributes text eol=lf`n.gitignore text eol=lf`n"
            ) -and
            [IO.File]::ReadAllText($fakeCaptureIgnore) -ceq (
                "**/base-all/`n**/grid-all/`n"
            )
        ) `
        -Message 'Bulk suite creation did not completely rewrite public suites and histories while preserving capture Git metadata.'
    $acceptedBulkCapture = Join-Path `
        $fakeRepository `
        'e2e\captures\test\no_reference\accepted.txt'
    [IO.File]::WriteAllText($acceptedBulkCapture, 'accepted bulk history')
    [IO.File]::WriteAllText($noReferenceRecording, 'third')
    [IO.File]::WriteAllText((Join-Path $fakeScripts 'fail-run'), '')
    $bulkReplacementFailed = $false
    try {
        & (Join-Path $fakeScripts 'create_suite.ps1') -All -NoReference
    }
    catch {
        $bulkReplacementFailed = $true
    }
    Remove-Item -LiteralPath (Join-Path $fakeScripts 'fail-run') -Force
    Assert-E2eHelperTest `
        -Condition (
            $bulkReplacementFailed -and
            [IO.File]::ReadAllText($firstSuitePath) -ceq 'second' -and
            [IO.File]::ReadAllText($acceptedBulkCapture) -ceq 'accepted bulk history' -and
            [IO.File]::ReadAllText((Join-Path $fakeCaptureGit 'preserved.txt')) -ceq 'git metadata' -and
            [IO.File]::ReadAllText($fakeCaptureAttributes) -ceq (
                ".gitattributes text eol=lf`n.gitignore text eol=lf`n"
            ) -and
            [IO.File]::ReadAllText($fakeCaptureIgnore) -ceq (
                "**/base-all/`n**/grid-all/`n"
            )
        ) `
        -Message 'Failed bulk suite creation did not restore the complete prior definition and capture trees.'
    $looseCapture = Join-Path $fakeRepository 'e2e\captures\loose.txt'
    $suiteMetadata = Join-Path $fakeRepository 'e2e\suites\metadata.txt'
    [IO.File]::WriteAllText($looseCapture, 'loose capture history')
    [IO.File]::WriteAllText($suiteMetadata, 'suite metadata')
    & (Join-Path $fakeScripts 'delete_suite.ps1') -All
    & (Join-Path $fakeScripts 'delete_suite.ps1') -All
    Assert-E2eHelperTest `
        -Condition (
            -not (Test-Path -LiteralPath (Join-Path $fakeRepository 'e2e\suites')) -and
            @(
                Get-ChildItem `
                    -LiteralPath (Join-Path $fakeRepository 'e2e\captures') `
                    -Force |
                    Where-Object Name -NotIn @('.git', '.gitattributes', '.gitignore')
            ).Count -eq 0 -and
            [IO.File]::ReadAllText((Join-Path $fakeCaptureGit 'preserved.txt')) -ceq 'git metadata' -and
            [IO.File]::ReadAllText($fakeCaptureAttributes) -ceq (
                ".gitattributes text eol=lf`n.gitignore text eol=lf`n"
            ) -and
            [IO.File]::ReadAllText($fakeCaptureIgnore) -ceq (
                "**/base-all/`n**/grid-all/`n"
            )
        ) `
        -Message 'Bulk suite deletion did not remove all histories idempotently or preserve capture Git metadata.'

    Remove-VisualRegressionTransaction -Transaction $transaction -Root $testRoot
    Write-Host 'E2E helper tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
