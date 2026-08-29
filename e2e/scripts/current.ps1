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
. (Join-Path $PSScriptRoot 'config.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$configuration = Get-E2eConfiguration -Root $root
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

function Write-E2eJobJson {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Value
    )

    [void](New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($Path)) -Force)
    $temporary = "$Path.tmp-$([guid]::NewGuid().ToString('N'))"
    try {
        [IO.File]::WriteAllText(
            $temporary,
            (($Value | ConvertTo-Json -Depth 6) + "`n"),
            [Text.UTF8Encoding]::new($false)
        )
        [IO.File]::Move($temporary, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

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
    $artifactDirectory = Join-Path `
        (Join-Path $suiteOutput 'capture') `
        'screenshots'
    $actualCount = @(
        Get-ChildItem `
            -LiteralPath $artifactDirectory `
            -Filter '*.png' `
            -File `
            -ErrorAction SilentlyContinue
    ).Count
    return $actualCount -eq $expectedCount
}

function Set-E2eReady {
    param([string]$IsoSha256)

    $completedUtc = (Get-Date).ToUniversalTime().ToString('O')
    Write-E2eJobJson -Path $readyPath -Value ([ordered]@{
        iso_sha256 = $IsoSha256
        completed_utc = $completedUtc
    })
}

function Complete-E2eRun {
    $completedUtc = (Get-Date).ToUniversalTime().ToString('O')
    $result = [ordered]@{
        status = 'passed'
        suites = $suites.Count
        replays_per_suite = 1
        completed_utc = $completedUtc
    }
    Write-E2eJobJson -Path $resultPath -Value $result
    return [pscustomobject]$result
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
    [string]$existingBuild.build -ceq [string]$configuration.Build
$allSuitesComplete = @(
    $suiteContexts | Where-Object { -not (Test-E2eSuiteComplete -Context $_) }
).Count -eq 0
$previousIsoSha256 = if ($existingBuildMatches) {
    [string]$existingBuild.iso_sha256
}
else { '' }

$buildOutput = @(
    & (Join-Path ([string]$paths.scripts) 'na228\build.ps1') -E2e
)
$build = @(
    $buildOutput | Where-Object {
        $_.PSObject.Properties.Name -contains 'Status' -and
        $_.Status -ceq 'e2e-test'
    }
) | Select-Object -Last 1
if ($null -eq $build) {
    throw 'E2E Test build returned no valid result.'
}
$isoSha256 = [string]$build.OutputSha256
if ([string]::IsNullOrWhiteSpace($isoSha256)) {
    throw 'E2E Test build returned no ISO hash.'
}

$suiteOutputRoot = Join-Path $jobRoot 'suites'
$hasExistingSuiteOutput = Test-Path -LiteralPath $suiteOutputRoot -PathType Container
$buildIsCompatible = $existingBuildMatches -and
    -not [string]::IsNullOrWhiteSpace($previousIsoSha256) -and
    $previousIsoSha256 -ceq $isoSha256
if ($hasExistingSuiteOutput -and -not $buildIsCompatible) {
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
    $existingBuild = $null
}
elseif ($null -ne $existingBuild -and -not $buildIsCompatible) {
    Move-VisualRegressionTransactionItemsToAttempt `
        -Transaction $Transaction `
        -RelativePath @(
            "jobs\$jobName\build.json",
            "jobs\$jobName\result.json",
            "jobs\$jobName\ready.json"
        ) `
        -Label 'current-build' |
        Out-Null
    $existingBuild = $null
}

$buildResult = [ordered]@{
    build = [string]$configuration.Build
    iso = [string]$build.OutputIso
    iso_sha256 = $isoSha256
    build_id = [string]$build.BuildId
    build_record = [string]$build.ConfigurationLogDirectory
    preflight_cache_hit = [bool]$build.PreflightCacheHit
}
Write-E2eJobJson -Path $buildPath -Value $buildResult
Set-E2eReady -IsoSha256 $isoSha256
if ($allSuitesComplete -and $buildIsCompatible) {
    Write-Host 'Continuing with completed E2E suite captures.' -ForegroundColor Cyan
    Complete-E2eRun | Out-Null
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
        $recordingPath = $context.SuitePath
        $suiteName = $context.Suite
        $replayJob = Start-ThreadJob -Name "current/$suiteName" -ScriptBlock {
                param(
                    $SuiteScript,
                    $Repository,
                    $SharedRecordingRoot,
                    $RecordingPath,
                    $Game,
                    $CaptureRoot,
                    $SuiteOutput,
                    $Suite,
                    $Generated,
                    $GeneratedScript,
                    $MemoryCard,
                    $LaunchProfile,
                    $ConcurrencyLimit,
                    $ConcurrencyPoolRoot,
                    $MovesetRange,
                    $MovesetFamily
                )
                $ErrorActionPreference = 'Stop'
                . $SuiteScript
                if ($Generated) {
                    $generatedArguments = @{
                        Game = $Game
                        Tier = 'current'
                        OutputRoot = $CaptureRoot
                        ThrottleLimit = $ConcurrencyLimit
                        ConcurrencyPoolRoot = $ConcurrencyPoolRoot
                        ProjectRoot = $Repository
                        MemoryCard = $MemoryCard
                        LaunchProfile = $LaunchProfile
                    }
                    if (-not [string]::IsNullOrWhiteSpace($MovesetRange)) {
                        $generatedArguments.MovesetRange = $MovesetRange
                    }
                    $generatedArguments.MovesetFamily = $MovesetFamily
                    & $GeneratedScript @generatedArguments
                    $artifactDirectory = Join-Path $CaptureRoot 'screenshots'
                    $artifactLabel = 'grids'
                }
                else {
                    Invoke-VisualRegressionPooledReplay `
                        -Repository $Repository `
                        -SharedRecordingRoot $SharedRecordingRoot `
                        -RecordingPath $RecordingPath `
                        -Game $Game `
                        -CaptureRoot $CaptureRoot `
                        -MemoryCard $MemoryCard `
                        -LaunchProfile $LaunchProfile `
                        -ConcurrencyPoolRoot $ConcurrencyPoolRoot `
                        -ConcurrencyLimit $ConcurrencyLimit
                    $artifactDirectory = Join-Path $CaptureRoot 'screenshots'
                    $artifactLabel = 'screenshots'
                }
                $artifactCount = @(
                    Get-ChildItem `
                        -LiteralPath $artifactDirectory `
                        -Filter '*.png' `
                        -File `
                        -ErrorAction SilentlyContinue
                ).Count
                if ($artifactCount -eq 0) {
                    throw "E2E suite $Suite completed without captured $artifactLabel."
                }
                $complete = [ordered]@{
                    suite = $Suite
                    screenshots = $artifactCount
                    artifact_type = $artifactLabel
                    completed_utc = (Get-Date).ToUniversalTime().ToString('O')
                }
                $completePath = Join-Path $SuiteOutput 'complete.json'
                $temporary = "$completePath.tmp-$([guid]::NewGuid().ToString('N'))"
                [void](New-Item -ItemType Directory -Path $SuiteOutput -Force)
                [IO.File]::WriteAllText(
                    $temporary,
                    (($complete | ConvertTo-Json -Depth 4) + "`n"),
                    [Text.UTF8Encoding]::new($false)
                )
                [IO.File]::Move($temporary, $completePath, $true)
                [pscustomobject]$complete
        } -ArgumentList (
            Join-Path $PSScriptRoot 'suite.ps1'
        ), $repository, $paths.pcsx2_input_recordings, $recordingPath, (
            [string]$configuration.Build
        ), (Join-Path $suiteOutput 'capture'), $suiteOutput, $suiteName, (
            [bool]$context.Generated
        ), $context.GeneratedScript, $context.MemoryCard, $context.LaunchProfile, (
            $ConcurrencyLimit
        ), (
            $ConcurrencyPoolRoot
        ), $context.MovesetRange, $context.GeneratedFamily
        $replayJobs.Add($replayJob)
    }

    if ($replayJobs.Count -gt 0) {
        Wait-VisualRegressionJobs `
            -Job ([object[]]$replayJobs) `
            -FailurePrefix 'E2E suite replay job'
    }
}
finally {
    foreach ($replayJob in $replayJobs) {
        if ($replayJob.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $replayJob -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $replayJob -Force -ErrorAction SilentlyContinue
    }
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
Complete-E2eRun | Out-Null
