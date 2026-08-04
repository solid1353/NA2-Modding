[CmdletBinding()]
param(
    [string]$Suite,
    [string]$CaptureRoot,
    [switch]$Shifted
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
. (Join-Path $PSScriptRoot 'config.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
$configuration = Get-E2eConfiguration -Root $root
$suiteRoot = Join-Path $root 'suites'
if (-not [string]::IsNullOrWhiteSpace($CaptureRoot) -and
    [string]::IsNullOrWhiteSpace($Suite)) {
    throw 'CaptureRoot requires one selected suite.'
}
function Get-E2eRunContext {
    param([Parameter(Mandatory)][string]$Name)

    if ([string]::IsNullOrWhiteSpace($CaptureRoot)) {
        return Get-VisualRegressionContext -Suite $Name
    }
    return Get-VisualRegressionContext -Suite $Name -CaptureRoot $CaptureRoot
}
$availableSuites = @(
    Get-ChildItem -LiteralPath $suiteRoot -Filter 'input.p2m2' -File -Recurse |
        ForEach-Object {
            [IO.Path]::GetRelativePath($suiteRoot, $_.DirectoryName).Replace('\', '/')
        } |
        Sort-Object -Unique
)
$suites = @(
    if ([string]::IsNullOrWhiteSpace($Suite)) {
        $availableSuites
    }
    else {
        $requestedContext = Get-E2eRunContext -Name $Suite
        $recording = Join-Path $requestedContext.SuiteRoot 'input.p2m2'
        if (-not (Test-Path -LiteralPath $recording -PathType Leaf)) {
            throw "E2E suite does not exist: $($requestedContext.Suite)"
        }
        $requestedContext.Suite
    }
)
if ($suites.Count -eq 0) {
    throw 'No E2E suites are available.'
}
$publishedVariant = [string]$configuration.PublishedVariant.name
$runVariants = @(
    if ($Shifted.IsPresent) {
        $configuration.Variants
    }
    else {
        $configuration.PublishedVariant
    }
)
$comparisonVariants = @(
    $runVariants |
        Where-Object { [string]$_.name -cne $publishedVariant }
)
foreach ($comparisonVariant in $comparisonVariants) {
    if ([string]$comparisonVariant.compare_against -cne $publishedVariant) {
        throw "Comparison variant $($comparisonVariant.name) must compare against $publishedVariant."
    }
}

$transaction = New-VisualRegressionTransaction -Root $root -Prefix 'run'
$jobs = [Collections.Generic.List[object]]::new()
$compared = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$comparisonFailures = [Collections.Generic.List[string]]::new()
$compareReadyVariants = {
    param([bool]$RequireComplete)

    foreach ($comparisonVariant in $comparisonVariants) {
        $candidateName = [string]$comparisonVariant.name
        foreach ($suite in $suites) {
            $comparisonKey = "$candidateName|$suite"
            if ($compared.Contains($comparisonKey)) { continue }
            $context = Get-E2eRunContext -Name $suite
            $normalSuite = Join-Path `
                (Join-Path (Join-Path (Join-Path $transaction 'jobs') $publishedVariant) 'suites') `
                $context.SuiteRelativePath
            $candidateSuite = Join-Path `
                (Join-Path (Join-Path (Join-Path $transaction 'jobs') $candidateName) 'suites') `
                $context.SuiteRelativePath
            $normalComplete = Test-Path -LiteralPath `
                (Join-Path $normalSuite 'complete.json') `
                -PathType Leaf
            $candidateComplete = Test-Path -LiteralPath `
                (Join-Path $candidateSuite 'complete.json') `
                -PathType Leaf
            if (-not $normalComplete -or -not $candidateComplete) {
                if ($RequireComplete) {
                    throw "Missing completed replay for $publishedVariant/$candidateName suite $suite."
                }
                continue
            }
            $comparisonRoot = Join-Path `
                (Join-Path (Join-Path $transaction 'comparisons') $candidateName) `
                $context.SuiteRelativePath
            $comparison = Compare-VisualRegressionVariants `
                -Suite $suite `
                -BaselineDirectory (Join-Path $normalSuite 'capture\screenshots') `
                -CandidateDirectory (Join-Path $candidateSuite 'capture\screenshots') `
                -CandidateName $candidateName `
                -OutputRoot $comparisonRoot `
                -IgnoreFile (Join-Path $context.SuiteRoot 'ignore.txt')
            [void]$compared.Add($comparisonKey)
            if ($comparison.status -cne 'passed') {
                $failure = "$candidateName/$suite"
                $comparisonFailures.Add($failure)
                Write-Warning (
                    "$publishedVariant/$candidateName comparison failed for $suite with " +
                    "$(@($comparison.mismatches).Count) differing capture(s)."
                )
            }
        }
    }
}
$pipelineCompleted = $false
try {
    Write-Host (
        "E2E pipeline started for $($suites -join ', '): permanent tests and " +
        "build/replay variants $(@($runVariants.name) -join ', ') run concurrently."
    ) -ForegroundColor Cyan
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
    foreach ($variant in $runVariants) {
        $variantName = [string]$variant.name
        $variantJob = Start-Job -Name $variantName -ScriptBlock {
            param($Script, $Variant, $Transaction, $Suite)
            $ErrorActionPreference = 'Stop'
            & $Script -Variant $Variant -Transaction $Transaction -Suite $Suite
        } -ArgumentList (
            Join-Path $PSScriptRoot 'variant.ps1'
        ), $variantName, $transaction, $Suite
        $jobs.Add($variantJob)
    }
    Write-Host (
        "E2E ISO build jobs running: " +
        "$(@($runVariants.name) -join ', ')."
    ) -ForegroundColor Cyan

    $nextProgress = [DateTime]::UtcNow
    while (@($jobs | Where-Object State -in @('NotStarted', 'Running')).Count -gt 0) {
        if ([DateTime]::UtcNow -ge $nextProgress) {
            $jobState = @(
                $jobs | ForEach-Object { "$($_.Name)=$($_.State)" }
            ) -join ', '
            Write-Host "E2E pipeline running: $jobState"
            $nextProgress = [DateTime]::UtcNow.AddSeconds(10)
        }
        & $compareReadyVariants $false
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

    & $compareReadyVariants $true
    if ($comparisonFailures.Count -gt 0) {
        foreach ($comparisonVariant in $comparisonVariants) {
            Preserve-VisualRegressionMismatchEvidence `
                -Transaction $transaction `
                -ComparisonVariant ([string]$comparisonVariant.name)
        }
        throw (
            'Build-variant comparison failed for E2E case(s): ' +
            ($comparisonFailures -join ', ')
        )
    }

    $replacements = [ordered]@{}
    foreach ($suite in $suites) {
        $context = Get-E2eRunContext -Name $suite
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

        $statesStage = $null
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
        if ($null -ne $statesStage) {
            $replacements[$context.Capture.States] = $statesStage
        }
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction
    Write-Host (
        "E2E pipeline passed: $($suites.Count) suite(s), " +
        "build variant(s) $(@($runVariants.name) -join ', '), " +
        "$publishedVariant captures published."
    ) -ForegroundColor Green
    [pscustomobject]@{
        Status = 'passed'
        Suites = $suites.Count
        Variants = $runVariants.Count
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
