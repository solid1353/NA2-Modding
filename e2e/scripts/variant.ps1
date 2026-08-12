[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('normal', 'shifted')][string]$Variant,
    [Parameter(Mandatory)][string]$Transaction,
    [string]$Suite,
    [switch]$Repeat
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
. (Join-Path $PSScriptRoot 'config.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$configuration = Get-E2eConfiguration -Root $root
$buildVariant = Get-E2eBuildVariant -Name $Variant -Root $root
if (
    $Repeat.IsPresent -and
    $Variant -cne [string]$configuration.PublishedVariant.name
) {
    throw 'Only the published E2E variant can be repeated.'
}
$suiteRoot = Join-Path $root 'suites'
$suites = @(
    if ([string]::IsNullOrWhiteSpace($Suite)) {
        Get-VisualRegressionSuiteNames -SuiteRepository $suiteRoot
    }
    else {
        $requestedContext = Get-VisualRegressionContext -Suite $Suite
        if (-not (Test-Path -LiteralPath $requestedContext.SuitePath -PathType Leaf)) {
            throw "E2E suite does not exist: $($requestedContext.Suite)"
        }
        $requestedContext.Suite
    }
)
if ($suites.Count -eq 0) {
    throw 'No E2E suites are available.'
}

$jobRoot = Join-Path (Join-Path $Transaction 'jobs') $Variant
[void](New-Item -ItemType Directory -Path $jobRoot -Force)
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

$buildResult = [ordered]@{
    schema_version = 1
    variant = $Variant
    build = [string]$buildVariant.build
    iso = [string]$build.OutputIso
    build_id = [string]$build.BuildId
    build_record = [string]$build.ConfigurationLogDirectory
    preflight_cache_hit = [bool]$build.PreflightCacheHit
}
[IO.File]::WriteAllText(
    (Join-Path $jobRoot 'build.json'),
    (($buildResult | ConvertTo-Json -Depth 4) + "`n"),
    [Text.UTF8Encoding]::new($false)
)

$replayJobs = [Collections.Generic.List[object]]::new()
try {
    foreach ($suite in $suites) {
        $context = Get-VisualRegressionContext -Suite $suite
        $recordingPath = $context.SuitePath
        $replayNames = @($Variant)
        if ($Repeat.IsPresent) {
            $replayNames += "$Variant-repeat"
        }
        foreach ($replayName in $replayNames) {
            $replayRoot = Join-Path (Join-Path $Transaction 'jobs') $replayName
            $suiteOutput = Join-Path `
                (Join-Path $replayRoot 'suites') `
                $context.SuiteRelativePath
            $replayJob = Start-ThreadJob -Name "$replayName/$($context.Suite)" -ScriptBlock {
                param(
                    $SuiteScript,
                    $Repository,
                    $SharedRecordingRoot,
                    $RecordingPath,
                    $Game,
                    $CaptureRoot,
                    $SuiteOutput,
                    $Suite,
                    $ReplayName
                )
                $ErrorActionPreference = 'Stop'
                . $SuiteScript
                Invoke-VisualRegressionReplay `
                    -Repository $Repository `
                    -SharedRecordingRoot $SharedRecordingRoot `
                    -RecordingPath $RecordingPath `
                    -Game $Game `
                    -CaptureRoot $CaptureRoot
                $screenshots = Join-Path $CaptureRoot 'screenshots'
                $screenshotCount = @(
                    Get-ChildItem `
                        -LiteralPath $screenshots `
                        -Filter '*.png' `
                        -File `
                        -ErrorAction SilentlyContinue
                ).Count
                if ($screenshotCount -eq 0) {
                    throw "E2E suite $Suite completed without captured screenshots for $ReplayName."
                }
                $complete = [ordered]@{
                    schema_version = 1
                    suite = $Suite
                    variant = $ReplayName
                    screenshots = $screenshotCount
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
            ), (Join-Path $suiteOutput 'capture'), $suiteOutput, $suite, $replayName
            $replayJobs.Add($replayJob)
        }
    }

    Wait-VisualRegressionJobs `
        -Job ([object[]]$replayJobs) `
        -FailurePrefix 'E2E suite replay job'
}
finally {
    foreach ($replayJob in $replayJobs) {
        if ($replayJob.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $replayJob -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $replayJob -Force -ErrorAction SilentlyContinue
    }
}

$result = [ordered]@{
    schema_version = 1
    variant = $Variant
    status = 'passed'
    suites = $suites.Count
    replays_per_suite = $(if ($Repeat.IsPresent) { 2 } else { 1 })
    completed_utc = (Get-Date).ToUniversalTime().ToString('O')
}
[IO.File]::WriteAllText(
    (Join-Path $jobRoot 'result.json'),
    (($result | ConvertTo-Json -Depth 4) + "`n"),
    [Text.UTF8Encoding]::new($false)
)
[pscustomobject]$result
