[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('normal', 'padded')][string]$Variant,
    [Parameter(Mandatory)][string]$Transaction
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
    Get-ChildItem -LiteralPath $suiteRoot -Filter 'input.p2m2' -File -Recurse |
        ForEach-Object {
            [IO.Path]::GetRelativePath($suiteRoot, $_.DirectoryName).Replace('\', '/')
        } |
        Sort-Object -Unique
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

foreach ($suite in $suites) {
    $context = Get-VisualRegressionContext -Suite $suite
    $recordingPath = Join-Path $context.SuiteRoot 'input.p2m2'
    $suiteOutput = Join-Path (Join-Path $jobRoot 'suites') $context.SuiteRelativePath
    $captureRoot = Join-Path $suiteOutput 'capture'
    Invoke-VisualRegressionReplay `
        -Repository $repository `
        -SharedRecordingRoot $paths.pcsx2_input_recordings `
        -RecordingPath $recordingPath `
        -Game ([string]$buildVariant.build) `
        -CaptureRoot $captureRoot
    $screenshots = Join-Path $captureRoot 'screenshots'
    $screenshotCount = @(
        Get-ChildItem -LiteralPath $screenshots -Filter '*.png' -File -ErrorAction SilentlyContinue
    ).Count
    if ($screenshotCount -eq 0) {
        throw "E2E suite $suite completed without captured screenshots for $Variant."
    }
    $complete = [ordered]@{
        schema_version = 1
        suite = $suite
        variant = $Variant
        screenshots = $screenshotCount
        completed_utc = (Get-Date).ToUniversalTime().ToString('O')
    }
    $completePath = Join-Path $suiteOutput 'complete.json'
    $temporary = "$completePath.tmp-$([guid]::NewGuid().ToString('N'))"
    [void](New-Item -ItemType Directory -Path $suiteOutput -Force)
    [IO.File]::WriteAllText(
        $temporary,
        (($complete | ConvertTo-Json -Depth 4) + "`n"),
        [Text.UTF8Encoding]::new($false)
    )
    [IO.File]::Move($temporary, $completePath, $true)
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
