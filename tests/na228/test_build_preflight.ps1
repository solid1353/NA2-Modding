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
    [IO.File]::WriteAllText(
        (Join-Path $repository 'e2e\config.json'),
        @'
{
  "schema_version": 1,
  "build_variants": [
    {
      "name": "normal",
      "build": "e2e_test",
      "payload_shift_bytes": 0,
      "publish": true
    },
    {
      "name": "shifted",
      "build": "e2e_test_shifted",
      "payload_shift_bytes": 48,
      "ignored": false,
      "compare_against": "normal"
    }
  ]
}
'@
    )
    [IO.File]::WriteAllText(
        (Join-Path $repository 'product.json'),
        @'
{
  "schema_version": 1,
  "title": "Synthetic Product",
  "serial": "TEST-00000",
  "output_boot_path": "TEST_000.00",
  "builds": {
    "latest": { "aliases": ["l"] },
    "previous": { "aliases": ["p"] },
    "manual": { "aliases": ["m"] },
    "e2e_test": {},
    "e2e_test_shifted": {}
  }
}
'@
    )

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
    "latest_iso": "@build/Synthetic Product - Latest.iso",
    "previous_iso": "@build/Synthetic Product - Previous.iso",
    "manual_iso": "@build/Synthetic Product - Manual.iso",
    "e2e_test_iso": "@build/Synthetic Product - E2E Test.iso",
    "e2e_test_shifted_iso": "@build/Synthetic Product - E2E Test Shifted.iso"
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
    $latestIso = Join-Path $repository 'build\Synthetic Product - Latest.iso'
    [IO.File]::WriteAllText($latestIso, 'verified latest')

    $logDirectory = Join-Path $repository 'logs\na228'
    New-Item -ItemType Directory -Force `
        -Path (Join-Path $logDirectory 'builds\existing') | Out-Null
    $buildMap = @(
        "iso`tbuild_record"
        "@build/Legacy Product - Latest.iso`t@logs/na228/builds/existing"
        "@build/Legacy Product - Previous.iso`t"
    ) -join "`n"
    [IO.File]::WriteAllText((Join-Path $logDirectory 'builds.tsv'), $buildMap + "`n")

    $global:Na2PreflightTestMode = 'hit'
    $global:Na2PreflightTestCalls = @()
    $global:Na2PreflightTestRepository = $repository
    $global:Na2PreflightTestSkipConfigurationLog = $false
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
            if ($arguments -contains '--compose-only') {
                $global:LASTEXITCODE = 0
                return 'Validated composition: synthetic; no ISO staged.'
            }
            $sourceIndex = [Array]::IndexOf($arguments, '--source') + 1
            $outputIndex = [Array]::IndexOf($arguments, '--output') + 1
            $configurationLogIndex = [Array]::IndexOf($arguments, '--configuration-log-directory') + 1
            $fixtureSource = if (Test-Path -LiteralPath $arguments[$outputIndex] -PathType Leaf) {
                $arguments[$outputIndex]
            }
            else {
                $arguments[$sourceIndex]
            }
            if (-not $global:Na2PreflightTestSkipConfigurationLog) {
                New-Item -ItemType Directory -Force `
                    -Path (Join-Path $global:Na2PreflightTestRepository $arguments[$configurationLogIndex]) | Out-Null
            }
            $global:LASTEXITCODE = 0
            if ($arguments -contains '--digest-only') {
                $fixtureItem = Get-Item -LiteralPath $fixtureSource
                $fixtureHash = (Get-FileHash -LiteralPath $fixtureSource -Algorithm SHA256).Hash
                return "Verified virtual ISO: $($fixtureItem.Length) bytes; SHA-256 $fixtureHash"
            }
            New-Item -ItemType Directory -Force `
                -Path ([IO.Path]::GetDirectoryName($arguments[$outputIndex])) | Out-Null
            [IO.File]::Copy($fixtureSource, "$($arguments[$outputIndex]).building", $true)
            return 'synthetic verified build'
        }
        throw "Unexpected python invocation: $($arguments -join ' ')"
    }

    $global:Na2PreflightTestCalls = @()
    $dryRunOutput = (& (Join-Path $scriptRoot 'build.ps1') -DryRun *>&1) -join "`n"
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Development dry run did not invoke the builder exactly once.'
    $dryRunCall = $global:Na2PreflightTestCalls[0]
    Assert-Na2PreflightTest `
        -Condition (
            $dryRunCall -contains 'na228_builder.scripts.build_configuration' -and
            $dryRunCall -contains 'na228_builder\configurations\development.json' -and
            $dryRunCall -contains '--compose-only' -and
            $dryRunCall -notcontains '--output' -and
            $dryRunCall -notcontains '--configuration-log-directory'
        ) `
        -Message 'Development dry run did not use the compose-only development route.'
    Assert-Na2PreflightTest `
        -Condition ($dryRunOutput -match 'Validated composition: synthetic; no ISO staged') `
        -Message 'Development dry run did not report composition success.'
    Assert-Na2PreflightTest `
        -Condition (-not (Test-Path -LiteralPath "$latestIso.building")) `
        -Message 'Development dry run staged an ISO.'

    $global:Na2PreflightTestCalls = @()
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
    $migratedBuildMap = [IO.File]::ReadAllText((Join-Path $logDirectory 'builds.tsv'))
    Assert-Na2PreflightTest `
        -Condition (
            $migratedBuildMap.Contains("@build/Synthetic Product - Latest.iso`t@logs/na228/builds/existing") -and
            $migratedBuildMap.Contains("@build/Synthetic Product - Previous.iso`t") -and
            -not $migratedBuildMap.Contains('@build/Legacy Product')
        ) `
        -Message 'Product-title change did not migrate builds.tsv to the configured ISO names.'

    $global:Na2PreflightTestMode = 'hit'
    $global:Na2PreflightTestCalls = @()
    $forcedHit = & (Join-Path $scriptRoot 'build.ps1') -Force
    Assert-Na2PreflightTest `
        -Condition ($forcedHit.Status -eq 'unchanged' -and $forcedHit.PreflightCacheHit) `
        -Message 'Force mode did not reuse a valid cached ISO.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Force mode invoked the builder after a preflight cache hit.'
    Assert-Na2PreflightTest `
        -Condition (-not (Test-Path -LiteralPath "$latestIso.building")) `
        -Message 'Force mode staged an ISO after a preflight cache hit.'

    $global:Na2PreflightTestMode = 'miss'
    $global:Na2PreflightTestCalls = @()
    $global:Na2PreflightTestSkipConfigurationLog = $true
    $forcedItems = @(& (Join-Path $scriptRoot 'build.ps1') -Force *>&1)
    $global:Na2PreflightTestSkipConfigurationLog = $false
    $forced = @(
        $forcedItems |
            Where-Object { $null -ne $_.PSObject.Properties['Status'] }
    )[-1]
    $forcedText = ($forcedItems | ForEach-Object { [string]$_ }) -join "`n"
    Assert-Na2PreflightTest `
        -Condition ($forced.Status -eq 'unchanged' -and -not $forced.PreflightCacheHit) `
        -Message 'Force mode did not retain a usable result after a real cache miss.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls.Count -eq 3) `
        -Message 'Force mode did not check, build, and record exactly once.'
    $forcedBuildCall = @(
        $global:Na2PreflightTestCalls |
            Where-Object { $_ -contains 'na228_builder.scripts.build_configuration' }
    )[-1]
    Assert-Na2PreflightTest `
        -Condition ($forcedBuildCall -contains '--best-effort-metadata') `
        -Message 'Force mode did not enable best-effort builder metadata.'
    Assert-Na2PreflightTest `
        -Condition (
            $forcedText -match 'continuing without a structured configuration build record' -and
            $forcedText -match 'could not retain the build record'
        ) `
        -Message 'Force mode did not downgrade missing build metadata to warnings.'
    Assert-Na2PreflightTest `
        -Condition (-not (Test-Path -LiteralPath "$latestIso.building")) `
        -Message 'Force mode left an unnecessary staged ISO after successful promotion.'

    $latestBackup = "$latestIso.force-test"
    Move-Item -LiteralPath $latestIso -Destination $latestBackup
    New-Item -ItemType Directory -Path $latestIso | Out-Null
    try {
        $global:Na2PreflightTestMode = 'miss'
        $global:Na2PreflightTestCalls = @()
        $forcedStagedItems = @(& (Join-Path $scriptRoot 'build.ps1') -Force *>&1)
        $forcedStaged = @(
            $forcedStagedItems |
                Where-Object { $null -ne $_.PSObject.Properties['Status'] }
        )[-1]
        Assert-Na2PreflightTest `
            -Condition (
                $forcedStaged.Status -eq 'forced-staged' -and
                $forcedStaged.LaunchIso -ceq "$latestIso.building" -and
                (Test-Path -LiteralPath $forcedStaged.LaunchIso -PathType Leaf)
            ) `
            -Message 'Force mode did not preserve a verified staged ISO after promotion failed.'
        Assert-Na2PreflightTest `
            -Condition ($global:Na2PreflightTestCalls.Count -eq 2) `
            -Message 'Staged force fallback unexpectedly wrote a preflight receipt.'
    }
    finally {
        if (Test-Path -LiteralPath "$latestIso.building" -PathType Leaf) {
            Remove-Item -LiteralPath "$latestIso.building" -Force
        }
        if (Test-Path -LiteralPath $latestIso -PathType Container) {
            Remove-Item -LiteralPath $latestIso -Force
        }
        Move-Item -LiteralPath $latestBackup -Destination $latestIso
    }

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
    $test = & (Join-Path $scriptRoot 'build.ps1') -ManualOnly
    $testIso = Join-Path $repository 'build\Synthetic Product - Manual.iso'
    Assert-Na2PreflightTest -Condition ($test.Status -eq 'manual') `
        -Message 'Manual-only build did not return manual status.'
    Assert-Na2PreflightTest `
        -Condition ((@($test.ChangedRoles) -join ',') -ceq 'manual') `
        -Message 'Changed Manual build did not report only its own role.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 3) `
        -Message 'Manual-only miss did not check, build, and record exactly once.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls[1] -contains 'na228_builder.scripts.build_configuration') `
        -Message 'Manual-only build did not run the full configuration builder.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls[1] -contains 'na228_builder\configurations\test.json') `
        -Message 'Manual-only build did not use test.json.'
    Assert-Na2PreflightTest -Condition (Test-Path -LiteralPath $testIso -PathType Leaf) `
        -Message 'Manual-only build did not retain its verified ISO.'
    Assert-Na2PreflightTest `
        -Condition ([IO.File]::ReadAllText($latestIso) -ceq 'verified latest') `
        -Message 'Manual-only build changed the Latest ISO.'
    Assert-Na2PreflightTest -Condition (-not (Test-Path -LiteralPath "$testIso.building")) `
        -Message 'Manual-only build left its .building ISO.'
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath (Join-Path $repository $test.ConfigurationLogDirectory.Replace('@logs/', 'logs/')) -PathType Container) `
        -Message 'Manual-only build did not retain its structured record.'

    $global:Na2PreflightTestMode = 'miss'
    $global:Na2PreflightTestCalls = @()
    $global:Na2PreflightTestSkipConfigurationLog = $true
    $forcedManualItems = @(
        & (Join-Path $scriptRoot 'build.ps1') -ManualOnly -Force *>&1
    )
    $global:Na2PreflightTestSkipConfigurationLog = $false
    $forcedManual = @(
        $forcedManualItems |
            Where-Object { $null -ne $_.PSObject.Properties['Status'] }
    )[-1]
    $forcedManualText = ($forcedManualItems | ForEach-Object { [string]$_ }) -join "`n"
    Assert-Na2PreflightTest `
        -Condition (
            $forcedManual.Status -eq 'manual' -and
            -not $forcedManual.PreflightCacheHit -and
            $null -eq $forcedManual.ConfigurationLogDirectory
        ) `
        -Message 'Forced Manual build did not retain its verified output without metadata.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls.Count -eq 3) `
        -Message 'Forced Manual build did not check, build, and record exactly once.'
    $forcedManualBuildCall = @(
        $global:Na2PreflightTestCalls |
            Where-Object { $_ -contains 'na228_builder.scripts.build_configuration' }
    )[-1]
    Assert-Na2PreflightTest `
        -Condition ($forcedManualBuildCall -contains '--best-effort-metadata') `
        -Message 'Forced Manual build did not enable best-effort builder metadata.'
    Assert-Na2PreflightTest `
        -Condition (
            $forcedManualText -match 'continuing without a structured build record' -and
            $forcedManualText -match 'force mode retained the verified ISO'
        ) `
        -Message 'Forced Manual build did not downgrade missing metadata to warnings.'
    Assert-Na2PreflightTest -Condition (Test-Path -LiteralPath $testIso -PathType Leaf) `
        -Message 'Forced Manual build lost its verified ISO.'

    $global:Na2PreflightTestMode = 'hit'
    $global:Na2PreflightTestCalls = @()
    $unchangedTest = & (Join-Path $scriptRoot 'build.ps1') -ManualOnly
    Assert-Na2PreflightTest -Condition ($unchangedTest.ManualState -eq 'unchanged') `
        -Message 'Repeated Manual-only build did not detect unchanged output.'
    Assert-Na2PreflightTest `
        -Condition (@($unchangedTest.ChangedRoles).Count -eq 0) `
        -Message 'Unchanged Manual build incorrectly reported a changed role.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Repeated Manual-only cache hit invoked composition or receipt recording.'
    Assert-Na2PreflightTest -Condition $unchangedTest.PreflightCacheHit `
        -Message 'Repeated Manual-only build was not marked as a preflight hit.'
    Assert-Na2PreflightTest `
        -Condition (@(Get-ChildItem -LiteralPath (Join-Path $logDirectory 'manual') -Directory).Count -eq 1) `
        -Message 'Manual-only build retained obsolete records.'

    $global:Na2PreflightTestMode = 'miss'
    $global:Na2PreflightTestCalls = @()
    $e2eNormal = & (Join-Path $scriptRoot 'build.ps1') -E2eVariant normal
    $e2eNormalIso = Join-Path $repository 'build\Synthetic Product - E2E Test.iso'
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
        "timestamp_utc`tresult`tlatest_iso`n2026-08-03T00:00:00Z`tupdated`t@build/Synthetic Product - Latest.iso`n"
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
    $e2eShiftedIso = Join-Path $repository 'build\Synthetic Product - E2E Test Shifted.iso'
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
        -Condition ($shiftedBuildCall[$shiftIndex] -ceq '48') `
        -Message 'Shifted E2E Test build did not use the configured synthetic shift.'
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

    $global:Na2PreflightTestMode = 'hit'
    $global:Na2PreflightTestCalls = @()
    $ephemeralOutput = 'work\Equivalence\build\candidate.iso'
    $ephemeralItems = @(
        & (Join-Path $scriptRoot 'build.ps1') `
            -WorkerOutputIso $ephemeralOutput `
            -WorkerEphemeral *>&1
    )
    $ephemeral = @(
        $ephemeralItems |
            Where-Object { $null -ne $_.PSObject.Properties['Status'] }
    )[-1]
    $ephemeralText = ($ephemeralItems | ForEach-Object { [string]$_ }) -join "`n"
    $ephemeralOutputPath = Join-Path $repository $ephemeralOutput
    $expectedEphemeralItem = Get-Item -LiteralPath (Join-Path $repository 'source\NA2.iso')
    $expectedEphemeralHash = (
        Get-FileHash -LiteralPath $expectedEphemeralItem.FullName -Algorithm SHA256
    ).Hash
    Assert-Na2PreflightTest `
        -Condition (
            $ephemeral.Status -eq 'worker' -and
            $ephemeral.OutputState -eq 'ephemeral' -and
            -not $ephemeral.OutputRetained -and
            $ephemeral.OutputSizeBytes -eq $expectedEphemeralItem.Length -and
            $ephemeral.OutputSha256 -ceq $expectedEphemeralHash
        ) `
        -Message 'Ephemeral worker build did not return its retained size/hash evidence.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls.Count -eq 2) `
        -Message 'Ephemeral worker build did not check preflight and build exactly once while skipping receipt recording.'
    Assert-Na2PreflightTest `
        -Condition (
            -not (Test-Path -LiteralPath $ephemeralOutputPath) -and
            -not (Test-Path -LiteralPath "$ephemeralOutputPath.building") -and
            -not (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($ephemeralOutputPath)) -PathType Container)
        ) `
        -Message 'Ephemeral worker build created an output ISO, staging file, or build directory.'
    Assert-Na2PreflightTest `
        -Condition (
            $ephemeralText -match 'cache miss \(ephemeral-build-required' -and
            $ephemeralText -match "Ephemeral worker ISO: $($expectedEphemeralItem.Length) bytes" -and
            $ephemeralText -match "SHA-256 $expectedEphemeralHash; not written to disk"
        ) `
        -Message 'Ephemeral worker build did not force a full build or print its virtual size/hash result.'
    $ephemeralRecord = Join-Path $repository (
        $ephemeral.ConfigurationLogDirectory.Replace('@work/', 'work/')
    )
    $ephemeralRow = Import-Csv `
        -LiteralPath (Join-Path $ephemeralRecord 'build_result.tsv') `
        -Delimiter "`t"
    Assert-Na2PreflightTest `
        -Condition (
            $ephemeralRow.output_state -ceq 'ephemeral' -and
            $ephemeralRow.output_size_bytes -ceq [string]$expectedEphemeralItem.Length -and
            $ephemeralRow.output_sha256 -ceq $expectedEphemeralHash -and
            $ephemeralRow.output_retained -ceq 'no'
        ) `
        -Message 'Ephemeral worker build record did not preserve size/hash/non-retention evidence.'

    New-Item -ItemType Directory -Force `
        -Path ([IO.Path]::GetDirectoryName($ephemeralOutputPath)) | Out-Null
    [IO.File]::WriteAllText($ephemeralOutputPath, 'preserve existing output')
    $global:Na2PreflightTestCalls = @()
    $existingEphemeralRejected = $false
    try {
        & (Join-Path $scriptRoot 'build.ps1') `
            -WorkerOutputIso $ephemeralOutput `
            -WorkerEphemeral | Out-Null
    }
    catch {
        $existingEphemeralRejected = (
            $_.Exception.Message -match 'refusing to replace it'
        )
    }
    Assert-Na2PreflightTest `
        -Condition (
            $existingEphemeralRejected -and
            [IO.File]::ReadAllText($ephemeralOutputPath) -ceq 'preserve existing output' -and
            $global:Na2PreflightTestCalls.Count -eq 0
        ) `
        -Message 'Ephemeral worker mode did not reject and preserve a pre-existing destination before build work.'
    Remove-Item -LiteralPath $ephemeralOutputPath -Force

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
        -Message 'Worker build changed Manual.'

    foreach ($invalidOutput in @(
        'build\agent.iso',
        'work\General\agent.iso',
        'work\General\build\agent.bin',
        'work\General\nested\build\agent.iso',
        'build\Synthetic Product - Manual.iso',
        'build\Synthetic Product - E2E Test.iso',
        'build\Synthetic Product - E2E Test Shifted.iso'
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
    Remove-Variable -Name Na2PreflightTestSkipConfigurationLog -Scope Global -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
