[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('normal', 'shifted')][string]$Variant,
    [Parameter(Mandatory)][string]$Transaction,
    [string]$Suite
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
$suiteRoot = Join-Path $root 'suites'
$suites = @(
    if ([string]::IsNullOrWhiteSpace($Suite)) {
        Get-ChildItem -LiteralPath $suiteRoot -Filter 'input.p2m2' -File -Recurse |
            ForEach-Object {
                [IO.Path]::GetRelativePath($suiteRoot, $_.DirectoryName).Replace('\', '/')
            } |
            Sort-Object -Unique
    }
    else {
        $requestedContext = Get-VisualRegressionContext -Suite $Suite
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
    build_record = [string]$build.ProfileLogDirectory
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
        $recordingPath = Join-Path $context.SuiteRoot 'input.p2m2'
        $suiteOutput = Join-Path `
            (Join-Path $jobRoot 'suites') `
            $context.SuiteRelativePath
        $replayJob = Start-ThreadJob -Name $context.Suite -ScriptBlock {
            param(
                $SuiteScript,
                $Repository,
                $SharedRecordingRoot,
                $RecordingPath,
                $Game,
                $CaptureRoot,
                $SuiteOutput,
                $Suite,
                $Variant
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
                throw "E2E suite $Suite completed without captured screenshots for $Variant."
            }
            $complete = [ordered]@{
                schema_version = 1
                suite = $Suite
                variant = $Variant
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
        ), (Join-Path $suiteOutput 'capture'), $suiteOutput, $suite, $Variant
        $replayJobs.Add($replayJob)
    }

    [void](Wait-Job -Job $replayJobs)
    foreach ($replayJob in $replayJobs) {
        Receive-Job -Job $replayJob | ForEach-Object { Write-Output $_ }
        if ($replayJob.State -cne 'Completed') {
            $reason = if ($null -ne $replayJob.ChildJobs[0].JobStateInfo.Reason) {
                $replayJob.ChildJobs[0].JobStateInfo.Reason.Message
            }
            else {
                'unknown failure'
            }
            throw "E2E suite replay job $($replayJob.Name) failed: $reason"
        }
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

$result = [ordered]@{
    schema_version = 1
    variant = $Variant
    status = 'passed'
    suites = $suites.Count
    completed_utc = (Get-Date).ToUniversalTime().ToString('O')
}
[IO.File]::WriteAllText(
    (Join-Path $jobRoot 'result.json'),
    (($result | ConvertTo-Json -Depth 4) + "`n"),
    [Text.UTF8Encoding]::new($false)
)
[pscustomobject]$result
