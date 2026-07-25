[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

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
    $scriptRoot = Join-Path $repository 'scripts\na2'
    $libRoot = Join-Path $repository 'scripts\lib'
    New-Item -ItemType Directory -Force -Path $scriptRoot, $libRoot | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'build.ps1') -Destination $scriptRoot
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'process.ps1') -Destination $scriptRoot
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'worker_paths.ps1') -Destination $scriptRoot
    foreach ($name in 'project_paths.ps1', 'run_log.ps1', 'build_log.ps1') {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot "..\lib\$name") -Destination $libRoot
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
    "patcher": "na2_patcher",
    "pcsx2_user": "pcsx2_user",
    "scripts": "scripts",
    "work": "work"
  },
  "files": {
    "pcsx2_user_exe": "@pcsx2_user/pcsx2-qt.exe",
    "na2_iso": "@source/NA2.iso",
    "nun5_iso": "@source/NUN5.iso",
    "current_iso": "@build/NA2.28 - Current.iso",
    "previous_iso": "@build/NA2.28 - Previous.iso",
    "candidate_iso": "@build/NA2.28 - Candidate.iso"
  }
}
'@
    [IO.File]::WriteAllText((Join-Path $repository 'project-paths.json'), $manifest)
    foreach ($directory in 'source\NA2.iso.files', 'source\NUN5.iso.files', 'build', 'logs', 'na2_patcher', 'pcsx2_user', 'work') {
        New-Item -ItemType Directory -Force -Path (Join-Path $repository $directory) | Out-Null
    }
    New-Item -ItemType Directory -Force `
        -Path (Join-Path $repository 'na2_patcher\profiles\current') | Out-Null
    [IO.File]::WriteAllText((Join-Path $repository 'source\NA2.iso'), 'clean na2')
    [IO.File]::WriteAllText((Join-Path $repository 'source\NUN5.iso'), 'clean nun5')
    $currentIso = Join-Path $repository 'build\NA2.28 - Current.iso'
    [IO.File]::WriteAllText($currentIso, 'verified current')

    $logDirectory = Join-Path $repository 'logs\na2'
    New-Item -ItemType Directory -Force `
        -Path (Join-Path $logDirectory 'builds\existing') | Out-Null
    $buildMap = @(
        "iso`tbuild_record"
        "@build/NA2.28 - Current.iso`t@logs/na2/builds/existing"
        "@build/NA2.28 - Previous.iso`t"
    ) -join "`n"
    [IO.File]::WriteAllText((Join-Path $logDirectory 'builds.tsv'), $buildMap + "`n")

    $global:Na2PreflightTestMode = 'hit'
    $global:Na2PreflightTestCalls = @()
    $global:Na2PreflightTestRepository = $repository
    function python {
        $arguments = @($args)
        $global:Na2PreflightTestCalls += ,$arguments
        if ($arguments -contains 'na2_patcher.build_preflight') {
            $commandIndex = [Array]::IndexOf($arguments, 'na2_patcher.build_preflight') + 1
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
        if ($arguments -contains 'na2_patcher.build_profile') {
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
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Cache hit invoked module derivation or receipt recording.'
    Assert-Na2PreflightTest -Condition (-not (Test-Path -LiteralPath "$currentIso.building")) `
        -Message 'Cache hit created a .building ISO.'

    $global:Na2PreflightTestMode = 'miss'
    $global:Na2PreflightTestCalls = @()
    $miss = & (Join-Path $scriptRoot 'build.ps1')
    Assert-Na2PreflightTest -Condition ($miss.Status -eq 'unchanged') `
        -Message 'Synthetic full-build fallback did not preserve unchanged result.'
    Assert-Na2PreflightTest -Condition (-not $miss.PreflightCacheHit) `
        -Message 'Full-build fallback was incorrectly marked as a cache hit.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 3) `
        -Message 'Full-build fallback did not check, build, and record exactly once.'
    Assert-Na2PreflightTest -Condition (-not (Test-Path -LiteralPath "$currentIso.building")) `
        -Message 'Full-build fallback left a .building ISO.'

    $global:Na2PreflightTestCalls = @()
    $candidate = & (Join-Path $scriptRoot 'build.ps1') -CandidateOnly
    $candidateIso = Join-Path $repository 'build\NA2.28 - Candidate.iso'
    Assert-Na2PreflightTest -Condition ($candidate.Status -eq 'candidate') `
        -Message 'Candidate-only build did not return candidate status.'
    Assert-Na2PreflightTest -Condition (-not $candidate.Pcsx2Closed) `
        -Message 'Candidate-only build reported that it closed PCSX2.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Candidate-only build invoked preflight or receipt recording.'
    Assert-Na2PreflightTest `
        -Condition ($global:Na2PreflightTestCalls[0] -contains 'na2_patcher.build_profile') `
        -Message 'Candidate-only build did not run the full profile builder.'
    Assert-Na2PreflightTest -Condition (Test-Path -LiteralPath $candidateIso -PathType Leaf) `
        -Message 'Candidate-only build did not retain its verified ISO.'
    Assert-Na2PreflightTest `
        -Condition ([IO.File]::ReadAllText($currentIso) -ceq 'verified current') `
        -Message 'Candidate-only build changed the Current ISO.'
    Assert-Na2PreflightTest -Condition (-not (Test-Path -LiteralPath "$candidateIso.building")) `
        -Message 'Candidate-only build left its .building ISO.'
    Assert-Na2PreflightTest `
        -Condition (Test-Path -LiteralPath (Join-Path $repository $candidate.ProfileLogDirectory.Replace('@logs/', 'logs/')) -PathType Container) `
        -Message 'Candidate-only build did not retain its structured record.'

    $global:Na2PreflightTestCalls = @()
    $unchangedCandidate = & (Join-Path $scriptRoot 'build.ps1') -CandidateOnly
    Assert-Na2PreflightTest -Condition ($unchangedCandidate.CandidateState -eq 'unchanged') `
        -Message 'Repeated candidate-only build did not detect unchanged output.'
    Assert-Na2PreflightTest -Condition ($global:Na2PreflightTestCalls.Count -eq 1) `
        -Message 'Repeated candidate-only build invoked anything except profile composition.'
    Assert-Na2PreflightTest `
        -Condition (@(Get-ChildItem -LiteralPath (Join-Path $logDirectory 'candidates') -Directory).Count -eq 1) `
        -Message 'Candidate-only build retained obsolete candidate records.'

    $currentBeforeWorkers = [IO.File]::ReadAllText($currentIso)
    $candidateBeforeWorkers = [IO.File]::ReadAllText($candidateIso)
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
        -Condition ([IO.File]::ReadAllText($currentIso) -ceq $currentBeforeWorkers) `
        -Message 'Worker build changed Current.'
    Assert-Na2PreflightTest `
        -Condition ([IO.File]::ReadAllText($candidateIso) -ceq $candidateBeforeWorkers) `
        -Message 'Worker build changed Candidate.'

    foreach ($invalidOutput in @(
        'build\agent.iso',
        'work\General\agent.iso',
        'work\General\build\agent.bin',
        'work\General\nested\build\agent.iso'
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
