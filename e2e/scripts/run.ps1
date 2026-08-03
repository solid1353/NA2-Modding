[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
. (Join-Path $PSScriptRoot 'config.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
$configuration = Get-E2eConfiguration -Root $root
$suiteRoot = Join-Path $root 'suites'
$suites = @(
    Get-ChildItem -LiteralPath $suiteRoot -Filter 'input.p2m2' -File -Recurse |
        ForEach-Object {
            [IO.Path]::GetRelativePath($suiteRoot, $_.DirectoryName).Replace('\', '/')
        } |
        Sort-Object -Unique
)
if ($suites.Count -eq 0) {
    throw 'No E2E suites are available.'
}
if ($configuration.Variants.Count -ne 2) {
    throw 'The complete E2E pipeline currently requires exactly two build variants.'
}
$publishedVariant = [string]$configuration.PublishedVariant.name
$comparisonVariants = @(
    $configuration.Variants |
        Where-Object { [string]$_.name -cne $publishedVariant }
)
if ($comparisonVariants.Count -ne 1) {
    throw 'The complete E2E pipeline requires one comparison build variant.'
}
$comparisonVariant = $comparisonVariants[0]
if ([string]$comparisonVariant.compare_against -cne $publishedVariant) {
    throw 'The comparison E2E variant must compare against the published variant.'
}

$transaction = New-VisualRegressionTransaction -Root $root -Prefix 'run'
$jobs = [Collections.Generic.List[object]]::new()
$compared = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$comparisonFailures = [Collections.Generic.List[string]]::new()
$pipelineCompleted = $false
try {
    $testsJob = Start-Job -Name 'tests' -ScriptBlock {
        param($Repository, $Transaction)
        $ErrorActionPreference = 'Stop'
        $jobRoot = Join-Path (Join-Path $Transaction 'jobs') 'tests'
        [void](New-Item -ItemType Directory -Path $jobRoot -Force)
        & (Join-Path $Repository 'tests\run.ps1') *>&1 |
            Tee-Object -FilePath (Join-Path $jobRoot 'output.log')
        [IO.File]::WriteAllText(
            (Join-Path $jobRoot 'result.json'),
            "{`"schema_version`":1,`"status`":`"passed`"}`n",
            [Text.UTF8Encoding]::new($false)
        )
    } -ArgumentList $repository, $transaction
    $jobs.Add($testsJob)
    foreach ($variant in $configuration.Variants) {
        $variantName = [string]$variant.name
        $variantJob = Start-Job -Name $variantName -ScriptBlock {
            param($Script, $Variant, $Transaction)
            $ErrorActionPreference = 'Stop'
            & $Script -Variant $Variant -Transaction $Transaction
        } -ArgumentList (Join-Path $PSScriptRoot 'variant.ps1'), $variantName, $transaction
        $jobs.Add($variantJob)
    }

    while (@($jobs | Where-Object State -in @('NotStarted', 'Running')).Count -gt 0) {
        foreach ($suite in $suites) {
            if ($compared.Contains($suite)) { continue }
            $context = Get-VisualRegressionContext -Suite $suite
            $normalSuite = Join-Path `
                (Join-Path (Join-Path (Join-Path $transaction 'jobs') $publishedVariant) 'suites') `
                $context.SuiteRelativePath
            $candidateSuite = Join-Path `
                (Join-Path (Join-Path (Join-Path $transaction 'jobs') ([string]$comparisonVariant.name)) 'suites') `
                $context.SuiteRelativePath
            if (
                -not (Test-Path -LiteralPath (Join-Path $normalSuite 'complete.json') -PathType Leaf) -or
                -not (Test-Path -LiteralPath (Join-Path $candidateSuite 'complete.json') -PathType Leaf)
            ) {
                continue
            }
            $comparisonRoot = Join-Path `
                (Join-Path $transaction 'comparisons') `
                $context.SuiteRelativePath
            $comparison = Compare-VisualRegressionVariants `
                -Suite $suite `
                -BaselineDirectory (Join-Path $normalSuite 'capture\screenshots') `
                -CandidateDirectory (Join-Path $candidateSuite 'capture\screenshots') `
                -OutputRoot $comparisonRoot `
                -IgnoreFile (Join-Path $context.SuiteRoot 'ignore.txt')
            [void]$compared.Add($suite)
            if ($comparison.status -cne 'passed') {
                $comparisonFailures.Add($suite)
                Write-Warning (
                    "Normal/padded comparison failed for $suite with " +
                    "$(@($comparison.mismatches).Count) differing capture(s)."
                )
            }
        }
        if (@($jobs | Where-Object State -in @('NotStarted', 'Running')).Count -gt 0) {
            Start-Sleep -Milliseconds 200
        }
    }

    foreach ($job in $jobs) {
        $jobOutput = @(Receive-Job -Job $job -Keep)
        $jobOutput | ForEach-Object { Write-Output $_ }
        if ($job.State -cne 'Completed') {
            $reason = if ($null -ne $job.ChildJobs[0].JobStateInfo.Reason) {
                $job.ChildJobs[0].JobStateInfo.Reason.Message
            }
            else {
                'unknown failure'
            }
            throw "E2E pipeline job $($job.Name) failed: $reason"
        }
    }

    foreach ($suite in $suites) {
        if ($compared.Contains($suite)) { continue }
        $context = Get-VisualRegressionContext -Suite $suite
        $normalSuite = Join-Path `
            (Join-Path (Join-Path (Join-Path $transaction 'jobs') $publishedVariant) 'suites') `
            $context.SuiteRelativePath
        $candidateSuite = Join-Path `
            (Join-Path (Join-Path (Join-Path $transaction 'jobs') ([string]$comparisonVariant.name)) 'suites') `
            $context.SuiteRelativePath
        $comparison = Compare-VisualRegressionVariants `
            -Suite $suite `
            -BaselineDirectory (Join-Path $normalSuite 'capture\screenshots') `
            -CandidateDirectory (Join-Path $candidateSuite 'capture\screenshots') `
            -OutputRoot (Join-Path (Join-Path $transaction 'comparisons') $context.SuiteRelativePath) `
            -IgnoreFile (Join-Path $context.SuiteRoot 'ignore.txt')
        [void]$compared.Add($suite)
        if ($comparison.status -cne 'passed') {
            $comparisonFailures.Add($suite)
            Write-Warning (
                "Normal/padded comparison failed for $suite with " +
                "$(@($comparison.mismatches).Count) differing capture(s)."
            )
        }
    }
    if ($comparisonFailures.Count -gt 0) {
        throw (
            'Heap-stability comparison failed for E2E suite(s): ' +
            ($comparisonFailures -join ', ')
        )
    }

    $replacements = [ordered]@{}
    foreach ($suite in $suites) {
        $context = Get-VisualRegressionContext -Suite $suite
        $suiteJob = Join-Path `
            (Join-Path (Join-Path (Join-Path $transaction 'jobs') $publishedVariant) 'suites') `
            $context.SuiteRelativePath
        $capturedScreenshots = Join-Path $suiteJob 'capture\screenshots'
        $suiteStage = Join-Path (Join-Path $transaction 'stages') $context.SuiteRelativePath
        $referenceStage = Join-Path $suiteStage $script:E2eCaptureTiers.Reference
        $existingCurrentStage = Join-Path $suiteStage 'existing-current'
        $currentStage = Join-Path $suiteStage $script:E2eCaptureTiers.Current
        New-VisualRegressionTierStage `
            -ScreenshotDirectory $context.Capture.Screenshots `
            -StageDirectory $referenceStage `
            -Kind Reference
        New-VisualRegressionTierStage `
            -ScreenshotDirectory $context.Capture.Screenshots `
            -StageDirectory $existingCurrentStage `
            -Kind Current
        [void](New-Item -ItemType Directory -Path $currentStage -Force)
        Get-ChildItem -LiteralPath $capturedScreenshots -Filter '*.png' -File |
            Copy-Item -Destination $currentStage
        [void](Restore-IgnoredCurrentScreenshots `
            -CurrentDirectory $currentStage `
            -ExistingDirectory $existingCurrentStage `
            -IgnoreFile (Join-Path $context.SuiteRoot 'ignore.txt'))

        $capturedStates = Join-Path $suiteJob 'capture\sstates'
        if (Test-Path -LiteralPath $capturedStates -PathType Container) {
            $statesStage = Join-Path (Join-Path $transaction 'publish') (
                Join-Path $context.SuiteRelativePath 'sstates'
            )
            New-VisualRegressionStateStage `
                -ExistingRoot $context.Capture.States `
                -StageRoot $statesStage `
                -Tier $script:E2eCaptureTiers.Current `
                -CapturedDirectory $capturedStates `
                -CaptureRepository $context.CaptureRepository `
                -ExistingScreenshotDirectory $context.Capture.Screenshots `
                -ExistingScreenshotKind Current `
                -CapturedScreenshotDirectory $capturedScreenshots `
                -PythonRunner $context.PythonRunner `
                -IgnoreFile (Join-Path $context.SuiteRoot 'ignore.txt')
            $replacements[$context.Capture.States] = $statesStage
        }
        $reportStage = Join-Path $suiteStage 'report'
        $hasReference = @(Get-NumericPngSlots -Directory $referenceStage).Count -gt 0
        if ($hasReference) {
            New-VisualRegressionReport `
                -Suite $suite `
                -ReferenceDirectory $referenceStage `
                -CurrentDirectory $currentStage `
                -OutputRoot $reportStage
        }
        $suitePublish = Join-Path (Join-Path $transaction 'publish') $context.SuiteRelativePath
        $screenshotStage = Join-Path $suitePublish $script:E2eScreenshotDirectory
        New-VisualRegressionScreenshotStage `
            -ReferenceDirectory $referenceStage `
            -CurrentDirectory $currentStage `
            -ReportDirectory $(if ($hasReference) { $reportStage } else { $null }) `
            -OutputDirectory $screenshotStage
        $replacements[$context.Capture.Screenshots] = $screenshotStage
        if ($hasReference) {
            $gridStage = Join-Path $suitePublish $script:E2eGridDirectory
            [void](New-Item -ItemType Directory -Path $gridStage -Force)
            $generatedGrids = Join-Path $reportStage 'grids'
            if (Test-Path -LiteralPath $generatedGrids -PathType Container) {
                Get-ChildItem -LiteralPath $generatedGrids -File |
                    Copy-Item -Destination $gridStage
            }
            $replacements[$context.Capture.Grids] = $gridStage
        }
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction
    Write-Host (
        "E2E pipeline passed: $($suites.Count) suite(s), normal and padded builds, " +
        'normal captures published.'
    ) -ForegroundColor Green
    [pscustomobject]@{
        Status = 'passed'
        Suites = $suites.Count
        Variants = $configuration.Variants.Count
    }
    $pipelineCompleted = $true
}
finally {
    foreach ($job in $jobs) {
        if ($job.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
    if ($pipelineCompleted) {
        Remove-VisualRegressionTransaction -Transaction $transaction -Root $root
    }
    else {
        Write-Warning "Failed E2E transaction retained for inspection: $transaction"
    }
}
