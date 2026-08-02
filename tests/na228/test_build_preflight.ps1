[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$sourceRepository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))

function Assert-Na2PreflightTest {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

$testRoot = Join-Path (
    [IO.Path]::GetTempPath()
) "na2-build-preflight-tests-$PID-$([guid]::NewGuid().ToString('N'))"

try {
    $repository = Join-Path $testRoot 'repository'
    $scriptRoot = Join-Path $repository 'scripts\na228'
    $libRoot = Join-Path $repository 'scripts\lib'
    New-Item -ItemType Directory -Force `
        -Path $scriptRoot, $libRoot |
        Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'scripts\na228\build.ps1') -Destination $scriptRoot
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'scripts\na228\worker_paths.ps1') -Destination $scriptRoot
    foreach ($name in 'paths.ps1', 'run_log.ps1', 'build_log.ps1') {
        Copy-Item -LiteralPath (Join-Path $sourceRepository "scripts\lib\$name") -Destination $libRoot
    }

    $manifest = @'
{
  "schema_version": 1,
  "roots": {
    "repository": ".",
    "source": "source",
    "source_na2": "@source/NA2.iso.files",
    "source_nun5": "@source/NUN5.iso.files",
    "build": "build",
    "logs": "logs",
    "builder": "na228_builder",
    "pcsx2_stable": "pcsx2_stable",
    "scripts": "scripts",
    "work": "work"
  },
  "files": {
    "pcsx2_stable_exe": "@pcsx2_stable/pcsx2-qt.exe",
    "na2_iso": "@source/NA2.iso",
    "nun5_iso": "@source/NUN5.iso",
    "latest_iso": "@build/NA2.28 - Latest.iso",
    "previous_iso": "@build/NA2.28 - Previous.iso",
    "manual_test_iso": "@build/NA2.28 - Manual Test.iso",
    "screenshot_test_iso": "@build/NA2.28 - Screenshot Test.iso"
  }
}
'@
    [IO.File]::WriteAllText((Join-Path $repository 'paths.json'), $manifest)
    foreach ($directory in 'source\NA2.iso.files', 'source\NUN5.iso.files', 'build', 'logs', 'na228_builder', 'pcsx2_stable', 'work') {
        New-Item -ItemType Directory -Force -Path (Join-Path $repository $directory) | Out-Null
    }
    New-Item -ItemType Directory -Force `
        -Path (Join-Path $repository 'na228_builder\profiles') | Out-Null
    [IO.File]::WriteAllText(
        (Join-Path $repository 'na228_builder\profiles\default.tsv'),
        "feature_id`tenabled`texpected_sha256`tbypass_check`n"
    )
    [IO.File]::WriteAllText((Join-Path $repository 'source\NA2.iso'), 'clean na2')
    [IO.File]::WriteAllText((Join-Path $repository 'source\NUN5.iso'), 'clean nun5')
    $latestIso = Join-Path $repository 'build\NA2.28 - Latest.iso'
    [IO.File]::WriteAllText($latestIso, 'verified latest')

    $logDirectory = Join-Path $repository 'logs\na228'
    New-Item -ItemType Directory -Force `
        -Path (Join-Path $logDirectory 'builds\existing') | Out-Null
    $buildMap = @(
        "iso`tbuild_record"
        "@build/NA2.28 - Latest.iso`t@logs/na228/builds/existing"
        "@build/NA2.28 - Previous.iso`t"
    ) -join "`n"
    [IO.File]::WriteAllText((Join-Path $logDirectory 'builds.tsv'), $buildMap + "`n")

    $global:Na2PreflightTestMode = 'hit'
    $global:Na2PreflightTestCalls = @()
    $global:Na2PreflightTestRepository = $repository
    function python {
        $arguments = @($args)
        $global:Na2PreflightTestCalls += ,$arguments
        if ($arguments -contains 'na228_builder.build_preflight') {
            $commandIndex = [Array]::IndexOf($arguments, 'na228_builder.build_preflight') + 1
            $command = $arguments[$commandIndex]
            if ($command -eq 'check' -and $global:Na2PreflightTestMode -eq 'hit') {
                $global:LASTEXITCODE = 0
                return '{"fingerprint":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","output_sha256":"BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB","reason":"receipt-and-output-match","status":"hit"}'
            }
            if ($command -eq 'check') {
                $global:LASTEXITCODE = 0
                return '{"fingerprint":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","reason":"receipt-missing","status":"miss"}'
            }
            if ($command -eq 'record') {
                $global:LASTEXITCODE = 0
                return '{"fingerprint":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","output_sha256":"BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB","reason":"successful-build","status":"written"}'
            }
        }
        if ($arguments -contains 'na228_builder.build_profile') {
            $sourceIndex = [Array]::IndexOf($arguments, '--source') + 1
            $outputIndex = [Array]::IndexOf($arguments, '--output') + 1
            $profileLogIndex = [Array]::IndexOf($arguments, '--profile-log-directory') + 1
            $fixtureSource = if (Test-Path -LiteralPath $arguments[$outputIndex] -PathType Leaf) {
                $arguments[$outputIndex]
            }
            else {
                $arguments[$sourceIndex]
            }
            New-Item -ItemType Directory -Force `
                -Path ([IO.Path]::GetDirectoryName($arguments[$outputIndex])) | Out-Null
            [IO.File]::Copy($fixtureSource, "$($arguments[$outputIndex]).building", $true)
            New-Item -ItemType Directory -Force `
                -Path (Join-Path $global:Na2PreflightTestRepository $arguments[$profileLogIndex]) | Out-Null
            $global:LASTEXITCODE = 0
            return 'synthetic verified build'
        }
        throw "Unexpected python invocation: $($arguments -join ' ')"
    }

    $hit = & (Join-Path $scriptRoot 'build.ps1')
    Assert-Na2PreflightTest -Condition ($hit.Status -eq 'unchanged') `
        -Message 'Cache hit did not return unchanged.'
    Assert-Na2PreflightTest -Condition $hit.PreflightCacheHit `
        -Message 'Cache hit was not marked on the build result.'
    Assert-Na2PreflightTest -Condition (@($hit.ChangedRoles).Count -eq 0) `
        -Message 'Cache hit incorrectly reported changed build roles.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Cache hit invoked module derivation or receipt recording.'
    Assert-Na2PreflightTest -Condition (-not (Test-Path -LiteralPath "$latestIso.building")) `
        -Message 'Cache hit created a .building ISO.'

    $global:Na2PreflightTestMode = 'miss'
    $global:Na2PreflightTestCalls = @()
    $miss = & (Join-Path $scriptRoot 'build.ps1')
    Assert-Na2PreflightTest -Condition ($miss.Status -eq 'unchanged') `
        -Message 'Synthetic full-build fallback did not preserve unchanged result.'
    Assert-Na2PreflightTest -Condition (-not $miss.PreflightCacheHit) `
        -Message 'Full-build fallback was incorrectly marked as a cache hit.'
    Assert-Na2PreflightTest -Condition (@($miss.ChangedRoles).Count -eq 0) `
        -Message 'Unchanged full build incorrectly reported changed roles.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 3) `
        -Message 'Full-build fallback did not check, build, and record exactly once.'
    Assert-Na2PreflightTest -Condition (-not (Test-Path -LiteralPath "$latestIso.building")) `
        -Message 'Full-build fallback left a .building ISO.'

    $global:Na2PreflightTestCalls = @()
    $test = & (Join-Path $scriptRoot 'build.ps1') -ManualTestOnly
    $testIso = Join-Path $repository 'build\NA2.28 - Manual Test.iso'
    Assert-Na2PreflightTest -Condition ($test.Status -eq 'manual-test') `
        -Message 'Manual Test-only build did not return manual-test status.'
    Assert-Na2PreflightTest `
        -Condition ((@($test.ChangedRoles) -join ',') -ceq 'manual_test') `
        -Message 'Changed Manual Test build did not report only its own role.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Manual Test-only build invoked preflight or receipt recording.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls[0] -contains 'na228_builder.build_profile') `
        -Message 'Manual Test-only build did not run the full profile builder.'
    Assert-Na2PreflightTest -Condition (Test-Path -LiteralPath $testIso -PathType Leaf) `
        -Message 'Manual Test-only build did not retain its verified ISO.'
    Assert-Na2PreflightTest `
        -Condition ([IO.File]::ReadAllText($latestIso) -ceq 'verified latest') `
        -Message 'Manual Test-only build changed the Latest ISO.'
    Assert-Na2PreflightTest -Condition (-not (Test-Path -LiteralPath "$testIso.building")) `
        -Message 'Manual Test-only build left its .building ISO.'
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath (Join-Path $repository $test.ProfileLogDirectory.Replace('@logs/', 'logs/')) -PathType Container) `
        -Message 'Manual Test-only build did not retain its structured record.'

    $global:Na2PreflightTestCalls = @()
    $unchangedTest = & (Join-Path $scriptRoot 'build.ps1') -ManualTestOnly
    Assert-Na2PreflightTest -Condition ($unchangedTest.ManualTestState -eq 'unchanged') `
        -Message 'Repeated Manual Test-only build did not detect unchanged output.'
    Assert-Na2PreflightTest `
        -Condition (@($unchangedTest.ChangedRoles).Count -eq 0) `
        -Message 'Unchanged Manual Test build incorrectly reported a changed role.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Repeated Manual Test-only build invoked anything except profile composition.'
    Assert-Na2PreflightTest `
        -Condition (@(Get-ChildItem -LiteralPath (Join-Path $logDirectory 'manual_tests') -Directory).Count -eq 1) `
        -Message 'Manual Test-only build retained obsolete test records.'

    $global:Na2PreflightTestCalls = @()
    $screenshotTest = & (Join-Path $scriptRoot 'build.ps1') -ScreenshotTestOnly
    $screenshotTestIso = Join-Path $repository 'build\NA2.28 - Screenshot Test.iso'
    Assert-Na2PreflightTest -Condition ($screenshotTest.Status -eq 'screenshot-test') `
        -Message 'Screenshot-test build did not return screenshot-test status.'
    Assert-Na2PreflightTest `
        -Condition ((@($screenshotTest.ChangedRoles) -join ',') -ceq 'screenshot_test') `
        -Message 'Changed Screenshot Test build did not report only its own role.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Screenshot-test build invoked preflight or receipt recording.'
    Assert-Na2PreflightTest -Condition (Test-Path -LiteralPath $screenshotTestIso -PathType Leaf) `
        -Message 'Screenshot-test build did not retain its verified ISO.'
    Assert-Na2PreflightTest `
        -Condition ([IO.File]::ReadAllText($latestIso) -ceq 'verified latest') `
        -Message 'Screenshot-test build changed the Latest ISO.'
    Assert-Na2PreflightTest -Condition (-not (Test-Path -LiteralPath "$screenshotTestIso.building")) `
        -Message 'Screenshot-test build left its .building ISO.'
    $screenshotTestRecord = Join-Path $repository (
        $screenshotTest.ProfileLogDirectory.Replace('@logs/', 'logs/')
    )
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath (Join-Path $screenshotTestRecord 'screenshot_test_result.tsv') -PathType Leaf) `
        -Message 'Screenshot-test build did not retain its dedicated structured record.'

    $latestBeforeWorkers = [IO.File]::ReadAllText($latestIso)
    $testBeforeWorkers = [IO.File]::ReadAllText($testIso)
    $global:Na2PreflightTestCalls = @()
    $generalOutput = 'work\General\build\general-test.iso'
    $general = & (Join-Path $scriptRoot 'build.ps1') -WorkerOutputIso $generalOutput
    Assert-Na2PreflightTest -Condition ($general.Status -eq 'worker') `
        -Message 'Worker build did not return worker status.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Worker build invoked preflight or another shared pipeline.'
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath (Join-Path $repository $generalOutput) -PathType Leaf) `
        -Message 'Worker build did not retain its requested ISO.'
    Assert-Na2PreflightTest `
        -Condition (-not (Test-Path -LiteralPath ((Join-Path $repository $generalOutput) + '.building'))) `
        -Message 'Worker build left its .building ISO.'
    $generalRecord = Join-Path $repository ($general.ProfileLogDirectory.Replace('@work/', 'work/'))
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath (Join-Path $generalRecord 'build_result.tsv') -PathType Leaf) `
        -Message 'Worker build record was not retained under the worker logs.'

    $global:Na2PreflightTestCalls = @()
    $uiOutput = 'work\UI Translation\build\ui-test.iso'
    $ui = & (Join-Path $scriptRoot 'build.ps1') -WorkerOutputIso $uiOutput
    Assert-Na2PreflightTest -Condition ($ui.Status -eq 'worker') `
        -Message 'Second worker build did not return worker status.'
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath (Join-Path $repository $generalOutput) -PathType Leaf) `
        -Message 'Second worker build overwrote the first worker output.'
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath $generalRecord -PathType Container) `
        -Message 'Second worker build pruned the first worker record.'
    Assert-Na2PreflightTest `
        -Condition ([IO.File]::ReadAllText($latestIso) -ceq $latestBeforeWorkers) `
        -Message 'Worker build changed Latest.'
    Assert-Na2PreflightTest `
        -Condition ([IO.File]::ReadAllText($testIso) -ceq $testBeforeWorkers) `
        -Message 'Worker build changed Manual Test.'

    foreach ($invalidOutput in @(
        'build\agent.iso',
        'work\General\agent.iso',
        'work\General\build\agent.bin',
        'work\General\nested\build\agent.iso',
        'build\NA2.28 - Manual Test.iso',
        'build\NA2.28 - Screenshot Test.iso'
    )) {
        $failed = $false
        try {
            & (Join-Path $scriptRoot 'build.ps1') -WorkerOutputIso $invalidOutput | Out-Null
        }
        catch {
            $failed = $true
        }
        Assert-Na2PreflightTest -Condition $failed `
            -Message "Invalid worker output was accepted: $invalidOutput"
    }

    Write-Host 'NA2 build preflight PowerShell tests passed.' -ForegroundColor Green
}
finally {
    Remove-Variable -Name Na2PreflightTestMode -Scope Global -ErrorAction SilentlyContinue
    Remove-Variable -Name Na2PreflightTestCalls -Scope Global -ErrorAction SilentlyContinue
    Remove-Variable -Name Na2PreflightTestRepository -Scope Global -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
