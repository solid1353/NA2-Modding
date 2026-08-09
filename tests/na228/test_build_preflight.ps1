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
    $e2eScripts = Join-Path $repository 'e2e\scripts'
    $pcsx2Scripts = Join-Path $repository 'scripts\pcsx2'
    New-Item -ItemType Directory -Force `
        -Path $scriptRoot, $libRoot, $e2eScripts, $pcsx2Scripts |
        Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'scripts\na228\build.ps1') -Destination $scriptRoot
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'scripts\na228\worker_paths.ps1') -Destination $scriptRoot
    foreach ($name in 'paths.ps1', 'run_log.ps1', 'build_log.ps1') {
        Copy-Item -LiteralPath (Join-Path $sourceRepository "scripts\lib\$name") -Destination $libRoot
    }
    $fakePythonRunner = @'
[CmdletBinding()]
param(
    [string]$PackageSet,
    [string]$Module,
    [string[]]$ArgumentList,
    [switch]$NoBytecode
)

& python '-B' '-m' $Module @ArgumentList
exit $LASTEXITCODE
'@
    [IO.File]::WriteAllText(
        (Join-Path $libRoot 'run_python.ps1'),
        $fakePythonRunner
    )
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'e2e\scripts\config.ps1') -Destination $e2eScripts
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'e2e\config.json') -Destination (Join-Path $repository 'e2e')
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'product.json') -Destination $repository

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
    "e2e_test_iso": "@build/NA2.28 - E2E Test.iso",
    "e2e_test_shifted_iso": "@build/NA2.28 - E2E Test Shifted.iso"
  }
}
'@
    [IO.File]::WriteAllText((Join-Path $repository 'paths.json'), $manifest)
    foreach ($directory in 'source\NA2.iso.files', 'source\NUN5.iso.files', 'build', 'logs', 'na228_builder', 'pcsx2_stable', 'work') {
        New-Item -ItemType Directory -Force -Path (Join-Path $repository $directory) | Out-Null
    }
    New-Item -ItemType Directory -Force `
        -Path (Join-Path $repository 'na228_builder\configurations') | Out-Null
    foreach ($name in 'development', 'test', 'release') {
        [IO.File]::WriteAllText(
            (Join-Path $repository "na228_builder\configurations\$name.json"),
            "{}`n"
        )
    }
    [IO.File]::WriteAllText((Join-Path $repository 'source\NA2.iso'), 'clean na2')
    [IO.File]::WriteAllText((Join-Path $repository 'source\NUN5.iso'), 'clean nun5')
    . (Join-Path $libRoot 'paths.ps1')
    . (Join-Path $libRoot 'build_log.ps1')
    $testPaths = Get-Na2Paths
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
        if ($arguments -contains 'na228_builder.scripts.build_preflight') {
            $commandIndex = [Array]::IndexOf($arguments, 'na228_builder.scripts.build_preflight') + 1
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
        if ($arguments -contains 'na228_builder.scripts.build_configuration') {
            $sourceIndex = [Array]::IndexOf($arguments, '--source') + 1
            $outputIndex = [Array]::IndexOf($arguments, '--output') + 1
            $configurationLogIndex = [Array]::IndexOf($arguments, '--configuration-log-directory') + 1
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
                -Path (Join-Path $global:Na2PreflightTestRepository $arguments[$configurationLogIndex]) | Out-Null
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
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls[0] -contains 'na228_builder\configurations\development.json') `
        -Message 'Normal development build did not use development.json.'
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

    $global:Na2PreflightTestMode = 'miss'
    $global:Na2PreflightTestCalls = @()
    $test = & (Join-Path $scriptRoot 'build.ps1') -ManualTestOnly
    $testIso = Join-Path $repository 'build\NA2.28 - Manual Test.iso'
    Assert-Na2PreflightTest -Condition ($test.Status -eq 'manual-test') `
        -Message 'Manual Test-only build did not return manual-test status.'
    Assert-Na2PreflightTest `
        -Condition ((@($test.ChangedRoles) -join ',') -ceq 'manual_test') `
        -Message 'Changed Manual Test build did not report only its own role.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 3) `
        -Message 'Manual Test-only miss did not check, build, and record exactly once.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls[1] -contains 'na228_builder.scripts.build_configuration') `
        -Message 'Manual Test-only build did not run the full configuration builder.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls[1] -contains 'na228_builder\configurations\test.json') `
        -Message 'Manual Test-only build did not use test.json.'
    Assert-Na2PreflightTest -Condition (Test-Path -LiteralPath $testIso -PathType Leaf) `
        -Message 'Manual Test-only build did not retain its verified ISO.'
    Assert-Na2PreflightTest `
        -Condition ([IO.File]::ReadAllText($latestIso) -ceq 'verified latest') `
        -Message 'Manual Test-only build changed the Latest ISO.'
    Assert-Na2PreflightTest -Condition (-not (Test-Path -LiteralPath "$testIso.building")) `
        -Message 'Manual Test-only build left its .building ISO.'
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath (Join-Path $repository $test.ConfigurationLogDirectory.Replace('@logs/', 'logs/')) -PathType Container) `
        -Message 'Manual Test-only build did not retain its structured record.'

    $global:Na2PreflightTestMode = 'hit'
    $global:Na2PreflightTestCalls = @()
    $unchangedTest = & (Join-Path $scriptRoot 'build.ps1') -ManualTestOnly
    Assert-Na2PreflightTest -Condition ($unchangedTest.ManualTestState -eq 'unchanged') `
        -Message 'Repeated Manual Test-only build did not detect unchanged output.'
    Assert-Na2PreflightTest `
        -Condition (@($unchangedTest.ChangedRoles).Count -eq 0) `
        -Message 'Unchanged Manual Test build incorrectly reported a changed role.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Repeated Manual Test-only cache hit invoked composition or receipt recording.'
    Assert-Na2PreflightTest -Condition $unchangedTest.PreflightCacheHit `
        -Message 'Repeated Manual Test-only build was not marked as a preflight hit.'
    Assert-Na2PreflightTest `
        -Condition (@(Get-ChildItem -LiteralPath (Join-Path $logDirectory 'manual_tests') -Directory).Count -eq 1) `
        -Message 'Manual Test-only build retained obsolete test records.'

    $global:Na2PreflightTestMode = 'miss'
    $global:Na2PreflightTestCalls = @()
    $e2eNormal = & (Join-Path $scriptRoot 'build.ps1') -E2eVariant normal
    $e2eNormalIso = Join-Path $repository 'build\NA2.28 - E2E Test.iso'
    Assert-Na2PreflightTest -Condition ($e2eNormal.Status -eq 'e2e-test') `
        -Message 'Normal E2E Test build did not return e2e-test status.'
    Assert-Na2PreflightTest `
        -Condition ((@($e2eNormal.ChangedRoles) -join ',') -ceq 'e2e_test_normal') `
        -Message 'Changed normal E2E Test build did not report only its own role.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 3) `
        -Message 'Normal E2E Test miss did not check, build, and record exactly once.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls[1] -contains 'na228_builder\configurations\test.json') `
        -Message 'E2E Test build did not use test.json.'
    Assert-Na2PreflightTest -Condition (Test-Path -LiteralPath $e2eNormalIso -PathType Leaf) `
        -Message 'Normal E2E Test build did not retain its verified ISO.'
    Assert-Na2PreflightTest `
        -Condition ([IO.File]::ReadAllText($latestIso) -ceq 'verified latest') `
        -Message 'Normal E2E Test build changed the Latest ISO.'
    Assert-Na2PreflightTest -Condition (-not (Test-Path -LiteralPath "$e2eNormalIso.building")) `
        -Message 'Normal E2E Test build left its .building ISO.'
    $e2eNormalRecord = Join-Path $repository (
        $e2eNormal.ConfigurationLogDirectory.Replace('@logs/', 'logs/')
    )
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath (Join-Path $e2eNormalRecord 'build_result.tsv') -PathType Leaf) `
        -Message 'Normal E2E Test build did not retain its shared structured record.'

    $newerStandardRecord = Join-Path $logDirectory 'builds\newer-standard'
    [void](New-Item -ItemType Directory -Path $newerStandardRecord -Force)
    [IO.File]::WriteAllText(
        (Join-Path $newerStandardRecord 'build_result.tsv'),
        "timestamp_utc`tresult`tlatest_iso`n2026-08-03T00:00:00Z`tupdated`t@build/NA2.28 - Latest.iso`n"
    )

    $global:Na2PreflightTestMode = 'hit'
    $global:Na2PreflightTestCalls = @()
    $e2eNormalHit = & (Join-Path $scriptRoot 'build.ps1') -E2eVariant normal
    Assert-Na2PreflightTest -Condition $e2eNormalHit.PreflightCacheHit `
        -Message 'Repeated normal E2E Test build was not marked as a preflight hit.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Normal E2E Test cache hit invoked composition or receipt recording.'

    $global:Na2PreflightTestMode = 'miss'
    $global:Na2PreflightTestCalls = @()
    $e2eShifted = & (Join-Path $scriptRoot 'build.ps1') -E2eVariant shifted
    $e2eShiftedIso = Join-Path $repository 'build\NA2.28 - E2E Test Shifted.iso'
    Assert-Na2PreflightTest -Condition ($e2eShifted.Status -eq 'e2e-test') `
        -Message 'Shifted E2E Test build did not return e2e-test status.'
    Assert-Na2PreflightTest `
        -Condition ((@($e2eShifted.ChangedRoles) -join ',') -ceq 'e2e_test_shifted') `
        -Message 'Changed shifted E2E Test build did not report only its own role.'
    Assert-Na2PreflightTest -Condition (Test-Path -LiteralPath $e2eShiftedIso -PathType Leaf) `
        -Message 'Shifted E2E Test build did not retain its verified ISO.'
    $shiftedBuildCalls = @(
        $global:Na2PreflightTestCalls |
            Where-Object { $_ -contains 'na228_builder.scripts.build_configuration' }
    )
    Assert-Na2PreflightTest -Condition ($shiftedBuildCalls.Count -eq 1) `
        -Message 'Shifted E2E Test did not run exactly one full configuration build.'
    $shiftedBuildCall = $shiftedBuildCalls[0]
    $shiftIndex = [Array]::IndexOf($shiftedBuildCall, '--payload-shift') + 1
    Assert-Na2PreflightTest `
        -Condition ($shiftedBuildCall[$shiftIndex] -ceq '32') `
        -Message 'Shifted E2E Test build did not use the configured 32-byte shift.'
    $e2eMap = Read-Na2BuildMap -LogDirectory $logDirectory -Paths $testPaths
    Assert-Na2PreflightTest `
        -Condition (-not [string]::IsNullOrWhiteSpace($e2eMap.E2eTestNormalBuildId)) `
        -Message 'Normal E2E Test build was not retained in builds.tsv.'
    Assert-Na2PreflightTest `
        -Condition (-not [string]::IsNullOrWhiteSpace($e2eMap.E2eTestShiftedBuildId)) `
        -Message 'Shifted E2E Test build was not retained in builds.tsv.'

    $latestBeforeWorkers = [IO.File]::ReadAllText($latestIso)
    $testBeforeWorkers = [IO.File]::ReadAllText($testIso)
    $global:Na2PreflightTestMode = 'miss'
    $global:Na2PreflightTestCalls = @()
    $generalOutput = 'work\General\build\general-test.iso'
    $general = & (Join-Path $scriptRoot 'build.ps1') -WorkerOutputIso $generalOutput
    Assert-Na2PreflightTest -Condition ($general.Status -eq 'worker') `
        -Message 'Worker build did not return worker status.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 3) `
        -Message 'Worker miss did not check, build, and record exactly once.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls[1] -contains 'na228_builder\configurations\test.json') `
        -Message 'Worker build did not use test.json.'
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath (Join-Path $repository $generalOutput) -PathType Leaf) `
        -Message 'Worker build did not retain its requested ISO.'
    Assert-Na2PreflightTest `
        -Condition (-not (Test-Path -LiteralPath ((Join-Path $repository $generalOutput) + '.building'))) `
        -Message 'Worker build left its .building ISO.'
    $generalRecord = Join-Path $repository ($general.ConfigurationLogDirectory.Replace('@work/', 'work/'))
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath (Join-Path $generalRecord 'build_result.tsv') -PathType Leaf) `
        -Message 'Worker build record was not retained under the worker logs.'

    $global:Na2PreflightTestMode = 'hit'
    $global:Na2PreflightTestCalls = @()
    $generalHit = & (Join-Path $scriptRoot 'build.ps1') -WorkerOutputIso $generalOutput
    Assert-Na2PreflightTest -Condition $generalHit.PreflightCacheHit `
        -Message 'Repeated worker build was not marked as a preflight hit.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Worker cache hit invoked composition or receipt recording.'

    $global:Na2PreflightTestMode = 'miss'
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
        'build\NA2.28 - E2E Test.iso',
        'build\NA2.28 - E2E Test Shifted.iso'
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
