[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Transaction,
    [Parameter(Mandatory)][string]$SuiteRequestJson,
    [Parameter(Mandatory)][string]$ConcurrencyPoolRoot,
    [ValidateRange(1, 64)]
    [int]$ConcurrencyLimit = 16
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$state = Get-VisualRegressionRepositoryState
$paths = $state.Paths
$configuration = $state.Configuration
$jobName = 'current'
$suiteRequests = @($SuiteRequestJson | ConvertFrom-Json)
$suites = [string[]]@($suiteRequests.Suite)
if ($suites.Count -eq 0) {
    throw 'No E2E suites are available.'
}

$jobRoot = Join-Path (Join-Path $Transaction 'jobs') $jobName
$buildPath = Join-Path $jobRoot 'build.json'
$readyPath = Join-Path $jobRoot 'ready.json'
$resultPath = Join-Path $jobRoot 'result.json'
[void](New-Item -ItemType Directory -Path $jobRoot -Force)

function Get-E2eSuiteOutput {
    param([Parameter(Mandatory)]$Context)

    return Join-Path (Join-Path $jobRoot 'suites') $Context.SuiteRelativePath
}

function Test-E2eSuiteComplete {
    param([Parameter(Mandatory)]$Context)

    $suiteOutput = Get-E2eSuiteOutput -Context $Context
    $completePath = Join-Path $suiteOutput 'complete.json'
    if (-not (Test-Path -LiteralPath $completePath -PathType Leaf)) {
        return $false
    }
    try {
        $complete = Get-Content -Raw -LiteralPath $completePath | ConvertFrom-Json
        $expectedCount = [int]$complete.screenshots
    }
    catch {
        return $false
    }
    if ($expectedCount -le 0) {
        return $false
    }
    $expectedArtifactType = if ($Context.Generated) { 'grids' } else { 'screenshots' }
    if ([string]$complete.suite -cne [string]$Context.Suite -or
        [string]$complete.artifact_type -cne $expectedArtifactType) {
        return $false
    }
    $artifactDirectory = Join-Path $suiteOutput 'capture'
    if ($Context.Generated) {
        $artifactDirectory = Join-Path $artifactDirectory 'screenshots'
    }
    return (Get-VisualRegressionPngCount -Directory $artifactDirectory) -eq $expectedCount
}

function Complete-E2eRun {
    Write-VisualRegressionJson -Path $resultPath -Value ([ordered]@{
        status = 'passed'
        suites = $suites.Count
        replays_per_suite = 1
        completed_utc = (Get-Date).ToUniversalTime().ToString('O')
    })
}

$suiteContexts = @(
    foreach ($request in $suiteRequests) {
        $context = Get-VisualRegressionContext -Suite ([string]$request.Suite)
        Add-Member `
            -InputObject $context `
            -NotePropertyName MovesetRange `
            -NotePropertyValue ([string]$request.MovesetRange)
        $context
    }
)
$existingBuild = if (Test-Path -LiteralPath $buildPath -PathType Leaf) {
    try { Get-Content -Raw -LiteralPath $buildPath | ConvertFrom-Json }
    catch { $null }
}
else { $null }
$existingBuildMatches = $null -ne $existingBuild -and
    [string]$existingBuild.configuration -ceq [string]$configuration.Configuration
$allSuitesComplete = @(
    $suiteContexts | Where-Object { -not (Test-E2eSuiteComplete -Context $_) }
).Count -eq 0
$previousIsoSha256 = if ($existingBuildMatches) {
    [string]$existingBuild.iso_sha256
}
else { '' }

$buildOutput = @(& (Join-Path ([string]$paths.scripts) 'na228\build.ps1') `
    -Configuration ([string]$configuration.Configuration))
$build = @(
    $buildOutput | Where-Object {
        $_.PSObject.Properties.Name -contains 'Status' -and
        $_.Status -in @('built', 'reused')
    }
) | Select-Object -Last 1
if ($null -eq $build) {
    throw 'E2E build returned no valid result.'
}
$isoSha256 = [string]$build.OutputSha256
if ([string]::IsNullOrWhiteSpace($isoSha256)) {
    throw 'E2E build returned no ISO hash.'
}

$buildIsCompatible = $existingBuildMatches -and
    -not [string]::IsNullOrWhiteSpace($previousIsoSha256) -and
    $previousIsoSha256 -ceq $isoSha256
if (-not $buildIsCompatible -and (
    (Test-Path -LiteralPath (Join-Path $jobRoot 'suites') -PathType Container) -or
    $null -ne $existingBuild
)) {
    Move-VisualRegressionTransactionItemsToAttempt `
        -Transaction $Transaction `
        -RelativePath @(
            "jobs\$jobName\suites",
            "jobs\$jobName\build.json",
            "jobs\$jobName\result.json",
            "jobs\$jobName\ready.json"
        ) `
        -Label 'current-build' |
        Out-Null
}

Write-VisualRegressionJson -Path $buildPath -Value ([ordered]@{
    configuration = [string]$configuration.Configuration
    iso = [string]$build.OutputIso
    iso_sha256 = $isoSha256
    build_id = [string]$build.BuildId
    build_record = [string]$build.ConfigurationLogDirectory
    preflight_cache_hit = [bool]$build.PreflightCacheHit
})
Write-VisualRegressionJson -Path $readyPath -Value ([ordered]@{
    iso_sha256 = $isoSha256
    completed_utc = (Get-Date).ToUniversalTime().ToString('O')
})
if ($allSuitesComplete -and $buildIsCompatible) {
    Write-Host 'Continuing with completed E2E suite captures.' -ForegroundColor Cyan
    Complete-E2eRun
    return
}

$replayJobs = [Collections.Generic.List[object]]::new()
try {
    foreach ($context in $suiteContexts) {
        if (Test-E2eSuiteComplete -Context $context) {
            Write-Host "Reusing completed E2E/$($context.Suite) capture." -ForegroundColor Cyan
            continue
        }
        $suiteOutput = Get-E2eSuiteOutput -Context $context
        if (-not $context.Generated -and (Test-Path -LiteralPath $suiteOutput)) {
            Move-VisualRegressionTransactionItemsToAttempt `
                -Transaction $Transaction `
                -RelativePath @(
                    [IO.Path]::GetRelativePath($Transaction, $suiteOutput)
                ) `
                -Label 'current-incomplete' |
                Out-Null
        }
        $replayJob = Start-ThreadJob -Name "current/$($context.Suite)" -ScriptBlock {
                param(
                    $SuiteScript,
                    $Context,
                    $SharedRecordingRoot,
                    $Game,
                    $SuiteOutput,
                    $ConcurrencyLimit,
                    $ConcurrencyPoolRoot
                )
                $ErrorActionPreference = 'Stop'
                . $SuiteScript
                $captureRoot = Join-Path $SuiteOutput 'capture'
                if ($Context.Generated) {
                    Invoke-VisualRegressionGeneratedCapture `
                        -Context $Context `
                        -Game $Game `
                        -Tier 'current' `
                        -OutputRoot $captureRoot `
                        -ThrottleLimit $ConcurrencyLimit `
                        -ConcurrencyPoolRoot $ConcurrencyPoolRoot `
                        -MovesetRange $Context.MovesetRange
                    $artifactDirectory = Join-Path $captureRoot 'screenshots'
                    $artifactLabel = 'grids'
                }
                else {
                    Invoke-VisualRegressionPooledReplay `
                        -Repository $Context.Repository `
                        -SharedRecordingRoot $SharedRecordingRoot `
                        -RecordingPath $Context.SuitePath `
                        -Game $Game `
                        -CaptureRoot $captureRoot `
                        -MemoryCard $Context.MemoryCard `
                        -LaunchProfile $Context.LaunchProfile `
                        -ConcurrencyPoolRoot $ConcurrencyPoolRoot `
                        -ConcurrencyLimit $ConcurrencyLimit
                    $artifactDirectory = $captureRoot
                    $artifactLabel = 'screenshots'
                }
                $artifactCount = Get-VisualRegressionPngCount -Directory $artifactDirectory
                if ($artifactCount -eq 0) {
                    throw "E2E suite $($Context.Suite) completed without captured $artifactLabel."
                }
                $complete = [ordered]@{
                    suite = $Context.Suite
                    screenshots = $artifactCount
                    artifact_type = $artifactLabel
                    completed_utc = (Get-Date).ToUniversalTime().ToString('O')
                }
                Write-VisualRegressionJson `
                    -Path (Join-Path $SuiteOutput 'complete.json') `
                    -Value $complete
                [pscustomobject]$complete
        } -ArgumentList (
            Join-Path $PSScriptRoot 'suite.ps1'
        ), $context, $paths.pcsx2_input_recordings, (
            [string]$build.OutputIso
        ), $suiteOutput, $ConcurrencyLimit, $ConcurrencyPoolRoot
        $replayJobs.Add($replayJob)
    }

    if ($replayJobs.Count -gt 0) {
        Wait-VisualRegressionJobs `
            -Job ([object[]]$replayJobs) `
            -FailurePrefix 'E2E suite replay job'
    }
}
finally {
    Remove-VisualRegressionJobs -Job $replayJobs
}

$incompleteSuites = @(
    $suiteContexts | Where-Object { -not (Test-E2eSuiteComplete -Context $_) }
)
if ($incompleteSuites.Count -gt 0) {
    throw (
        'E2E Test did not complete suites: ' +
        (@($incompleteSuites.Suite) -join ', ')
    )
}
Complete-E2eRun
