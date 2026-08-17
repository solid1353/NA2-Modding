[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('normal', 'shifted')][string]$Variant,
    [Parameter(Mandatory)][string]$Transaction,
    [string[]]$Suite,
    [string]$MovesetRange,
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
$buildVariant = Get-E2eBuildVariant -Name $Variant -Root $root
$recordingRoot = Join-Path ([string]$paths.pcsx2_input_recordings) 'e2e'
$suiteWasSpecified = $PSBoundParameters.ContainsKey('Suite')
$requestedSuites = @(
    Get-VisualRegressionRequestedSuiteNames `
        -Suite $Suite `
        -WasSpecified $suiteWasSpecified
)
$suites = @(
    if ($requestedSuites.Count -eq 0) {
        Get-VisualRegressionSuiteNames -RecordingRepository $recordingRoot
    }
    else {
        $selected = [Collections.Generic.HashSet[string]]::new(
            [StringComparer]::OrdinalIgnoreCase
        )
        foreach ($requestedSuite in $requestedSuites) {
            $requestedContext = Get-VisualRegressionContext -Suite $requestedSuite
            if (-not (Test-VisualRegressionSuiteExists -Context $requestedContext)) {
                throw "E2E suite does not exist: $($requestedContext.Suite)"
            }
            if (-not $selected.Add($requestedContext.Suite)) {
                throw "Duplicate E2E suite selection: $($requestedContext.Suite)"
            }
            $requestedContext.Suite
        }
    }
)
if ($suites.Count -eq 0) {
    throw 'No E2E suites are available.'
}
if (-not [string]::IsNullOrWhiteSpace($MovesetRange) -and
    ($suites.Count -ne 1 -or -not (Test-VisualRegressionGeneratedSuite -Suite $suites[0]))) {
    throw 'MovesetRange requires one generated character suite.'
}

$jobRoot = Join-Path (Join-Path $Transaction 'jobs') $Variant
$buildPath = Join-Path $jobRoot 'build.json'
$readyPath = Join-Path $jobRoot 'ready.json'
$resultPath = Join-Path $jobRoot 'result.json'
[void](New-Item -ItemType Directory -Path $jobRoot -Force)

function Write-E2eVariantJson {
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

function Get-E2eVariantSuiteOutput {
    param([Parameter(Mandatory)]$Context)

    return Join-Path (Join-Path $jobRoot 'suites') $Context.SuiteRelativePath
}

function Test-E2eVariantSuiteComplete {
    param([Parameter(Mandatory)]$Context)

    $suiteOutput = Get-E2eVariantSuiteOutput -Context $Context
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
        [string]$complete.variant -cne $Variant -or
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

function Set-E2eVariantReady {
    param([string]$IsoSha256)

    $completedUtc = (Get-Date).ToUniversalTime().ToString('O')
    Write-E2eVariantJson -Path $readyPath -Value ([ordered]@{
        schema_version = 1
        variant = $Variant
        iso_sha256 = $IsoSha256
        completed_utc = $completedUtc
    })
}

function Complete-E2eVariant {
    $completedUtc = (Get-Date).ToUniversalTime().ToString('O')
    $result = [ordered]@{
        schema_version = 1
        variant = $Variant
        status = 'passed'
        suites = $suites.Count
        replays_per_suite = 1
        completed_utc = $completedUtc
    }
    Write-E2eVariantJson -Path $resultPath -Value $result
    return [pscustomobject]$result
}

$suiteContexts = @(
    $suites | ForEach-Object { Get-VisualRegressionContext -Suite $_ }
)
$existingBuild = if (Test-Path -LiteralPath $buildPath -PathType Leaf) {
    try { Get-Content -Raw -LiteralPath $buildPath | ConvertFrom-Json }
    catch { $null }
}
else { $null }
$existingBuildMatchesVariant = $null -ne $existingBuild -and
    [string]$existingBuild.variant -ceq $Variant
$allSuitesComplete = @(
    $suiteContexts | Where-Object { -not (Test-E2eVariantSuiteComplete -Context $_) }
).Count -eq 0
$previousIsoSha256 = if ($existingBuildMatchesVariant) {
    [string]$existingBuild.iso_sha256
}
else { '' }
if ([string]::IsNullOrWhiteSpace($previousIsoSha256) -and $existingBuildMatchesVariant) {
    $buildMapPath = Join-Path ([string]$paths.logs) 'na228\builds.tsv'
    $mappedBuild = if (Test-Path -LiteralPath $buildMapPath -PathType Leaf) {
        @(
            Import-Csv -LiteralPath $buildMapPath -Delimiter "`t" |
                Where-Object {
                    [string]$_.build_record -ceq [string]$existingBuild.build_record
                }
        ) | Select-Object -First 1
    }
    else { $null }
    $preflightPath = Join-Path `
        ([string]$paths.logs) `
        "na228\preflight\e2e_test_$Variant.json"
    if ($null -ne $mappedBuild -and
        (Test-Path -LiteralPath $preflightPath -PathType Leaf)) {
        try {
            $preflight = Get-Content -Raw -LiteralPath $preflightPath | ConvertFrom-Json
            $previousIsoSha256 = [string]$preflight.output.sha256
        }
        catch {
            $previousIsoSha256 = ''
        }
    }
}

$buildOutput = @(
    & (Join-Path $repository 'scripts\na228\build.ps1') -E2eVariant $Variant
)
$build = @(
    $buildOutput | Where-Object {
        $_.PSObject.Properties.Name -contains 'Status' -and
        $_.Status -ceq 'e2e-test'
    }
) | Select-Object -Last 1
if ($null -eq $build -or $build.E2eVariant -cne $Variant) {
    throw "E2E Test $Variant build returned no valid result."
}
$isoSha256 = [string]$build.OutputSha256
if ([string]::IsNullOrWhiteSpace($isoSha256)) {
    throw "E2E Test $Variant build returned no ISO hash."
}

$suiteOutputRoot = Join-Path $jobRoot 'suites'
$hasExistingSuiteOutput = Test-Path -LiteralPath $suiteOutputRoot -PathType Container
$buildIsCompatible = $existingBuildMatchesVariant -and
    -not [string]::IsNullOrWhiteSpace($previousIsoSha256) -and
    $previousIsoSha256 -ceq $isoSha256
if ($hasExistingSuiteOutput -and -not $buildIsCompatible) {
    Move-VisualRegressionTransactionItemsToAttempt `
        -Transaction $Transaction `
        -RelativePath @(
            "jobs\$Variant\suites",
            "jobs\$Variant\build.json",
            "jobs\$Variant\result.json",
            "jobs\$Variant\ready.json"
        ) `
        -Label "$Variant-build" |
        Out-Null
    $existingBuild = $null
}
elseif ($null -ne $existingBuild -and -not $buildIsCompatible) {
    Move-VisualRegressionTransactionItemsToAttempt `
        -Transaction $Transaction `
        -RelativePath @(
            "jobs\$Variant\build.json",
            "jobs\$Variant\result.json",
            "jobs\$Variant\ready.json"
        ) `
        -Label "$Variant-build" |
        Out-Null
    $existingBuild = $null
}

$buildResult = [ordered]@{
    schema_version = 2
    variant = $Variant
    build = [string]$buildVariant.build
    iso = [string]$build.OutputIso
    iso_sha256 = $isoSha256
    build_id = [string]$build.BuildId
    build_record = [string]$build.ConfigurationLogDirectory
    preflight_cache_hit = [bool]$build.PreflightCacheHit
}
Write-E2eVariantJson -Path $buildPath -Value $buildResult
Set-E2eVariantReady -IsoSha256 $isoSha256
if ($allSuitesComplete -and $buildIsCompatible) {
    Write-Host "Continuing with completed $Variant E2E suite captures." -ForegroundColor Cyan
    Complete-E2eVariant
    return
}

$replayJobs = [Collections.Generic.List[object]]::new()
try {
    foreach ($context in $suiteContexts) {
        if (Test-E2eVariantSuiteComplete -Context $context) {
            Write-Host "Reusing completed $Variant/$($context.Suite) capture." -ForegroundColor Cyan
            continue
        }
        $suiteOutput = Get-E2eVariantSuiteOutput -Context $context
        if (-not $context.Generated -and (Test-Path -LiteralPath $suiteOutput)) {
            Move-VisualRegressionTransactionItemsToAttempt `
                -Transaction $Transaction `
                -RelativePath @(
                    [IO.Path]::GetRelativePath($Transaction, $suiteOutput)
                ) `
                -Label "$Variant-incomplete" |
                Out-Null
        }
        $recordingPath = $context.SuitePath
        $replayName = $Variant
        $suiteName = $context.Suite
        $replayJob = Start-ThreadJob -Name "$replayName/$suiteName" -ScriptBlock {
                param(
                    $SuiteScript,
                    $Repository,
                    $SharedRecordingRoot,
                    $RecordingPath,
                    $Game,
                    $CaptureRoot,
                    $SuiteOutput,
                    $Suite,
                    $ReplayName,
                    $Generated,
                    $GeneratedScript,
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
                    throw "E2E suite $Suite completed without captured $artifactLabel for $ReplayName."
                }
                $complete = [ordered]@{
                    schema_version = 1
                    suite = $Suite
                    variant = $ReplayName
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
            [string]$buildVariant.build
        ), (Join-Path $suiteOutput 'capture'), $suiteOutput, $suiteName, $replayName, (
            [bool]$context.Generated
        ), $context.GeneratedScript, $ConcurrencyLimit, (
            $ConcurrencyPoolRoot
        ), $MovesetRange, $context.GeneratedFamily
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
    $suiteContexts | Where-Object { -not (Test-E2eVariantSuiteComplete -Context $_) }
)
if ($incompleteSuites.Count -gt 0) {
    throw (
        "E2E Test $Variant did not complete suites: " +
        (@($incompleteSuites.Suite) -join ', ')
    )
}
Complete-E2eVariant
