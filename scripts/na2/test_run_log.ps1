[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\build_log.ps1')

function Assert-Na2Test {
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
) "na2-run-log-tests-$PID-$([guid]::NewGuid().ToString('N'))"

try {
    $repository = Join-Path $testRoot 'repo'
    $logs = Join-Path $repository 'logs'
    $build = Join-Path $repository 'build'
    $paths = [pscustomobject]@{
        repository = $repository
        source = Join-Path $testRoot 'source'
        build = $build
        logs = $logs
        patcher = Join-Path $repository 'na2_patcher'
        pcsx2_user = Join-Path $testRoot 'pcsx2_user'
        scripts = Join-Path $repository 'scripts'
        files = [pscustomobject]@{
            current_iso = Join-Path $build 'NA2.28 - Current.iso'
            previous_iso = Join-Path $build 'NA2.28 - Previous.iso'
        }
    }
    New-Item -ItemType Directory -Force -Path $logs, $build | Out-Null
    $externalPath = 'C{0}{1}Private{1}outside.txt' -f `
        [IO.Path]::VolumeSeparatorChar, [IO.Path]::DirectorySeparatorChar

    $portable = ConvertTo-Na2PortableText `
        -Text "ISO: $build\NA2.28 - Current.iso`nExternal: $externalPath" `
        -ProjectPaths $paths
    Assert-Na2Test `
        -Condition ($portable -match 'ISO: @build/NA2\.28 - Current\.iso') `
        -Message 'Configured build path was not converted to @build.'
    Assert-Na2Test `
        -Condition ($portable -match 'Redacted output containing an external absolute path') `
        -Message 'External absolute path was not redacted.'
    Assert-Na2Test `
        -Condition (-not (Test-Na2WindowsAbsolutePath -Text $portable)) `
        -Message 'Portable text retained a Windows absolute path.'

    foreach ($index in 1..22) {
        $context = Start-Na2RunLog `
            -Mode "test-$index" `
            -ProjectPaths $paths `
            -MaxRollingSections 20
        Write-Host "run-marker-$index $build\NA2.28 - Current.iso"
        Complete-Na2RunLog -Context $context -Outcome succeeded
    }

    $latest = [IO.File]::ReadAllText((Join-Path $logs 'na2\latest.log'))
    $rolling = [IO.File]::ReadAllText((Join-Path $logs 'na2\rolling.log'))
    $sections = [regex]::Matches(
        $rolling,
        '(?ms)^--- NA2 RUN BEGIN ---\n.*?^--- NA2 RUN END ---\n?'
    )
    Assert-Na2Test -Condition ($sections.Count -eq 20) -Message 'rolling.log was not capped at 20 runs.'
    Assert-Na2Test -Condition ($latest -match '(?m)^mode: test-22$') -Message 'latest.log is not the newest run.'
    Assert-Na2Test -Condition ($rolling -notmatch '(?m)^run-marker-1 ') -Message 'rolling.log retained an expired run.'
    Assert-Na2Test -Condition ($rolling -match '(?m)^run-marker-3 ') -Message 'rolling.log lost the oldest retained run.'
    Assert-Na2Test -Condition ($rolling -match '(?m)^run-marker-22 ') -Message 'rolling.log lost the newest run.'
    Assert-Na2Test -Condition ($rolling -notmatch 'PowerShell transcript') -Message 'Transcript boilerplate was retained.'
    Assert-Na2Test -Condition (-not (Test-Na2WindowsAbsolutePath -Text $rolling)) -Message 'rolling.log contains an absolute path.'
    foreach ($field in 'mode:', 'start:', 'end:', 'outcome:', 'duration_ms:') {
        Assert-Na2Test -Condition ($latest.Contains($field)) -Message "latest.log is missing $field"
    }

    $failurePaths = $paths.PSObject.Copy()
    $failurePaths.logs = Join-Path $repository 'failure-logs'
    $failureContext = Start-Na2RunLog -Mode failure-test -ProjectPaths $failurePaths
    Write-Host "failure marker $build\NA2.28 - Current.iso"
    $failureExternalPath = 'C{0}{1}Private{1}failure.txt' -f `
        [IO.Path]::VolumeSeparatorChar, [IO.Path]::DirectorySeparatorChar
    Complete-Na2RunLog `
        -Context $failureContext `
        -Outcome failed `
        -FailureMessage "Configured: $build\NA2.28 - Current.iso`nExternal: $failureExternalPath"
    $failureLog = [IO.File]::ReadAllText((Join-Path $failurePaths.logs 'na2\latest.log'))
    Assert-Na2Test -Condition ($failureLog -match '(?m)^outcome: failed$') -Message 'Failed outcome was not recorded.'
    Assert-Na2Test -Condition ($failureLog -match '@build/NA2\.28 - Current\.iso') -Message 'Failure path was not made portable.'
    Assert-Na2Test -Condition (-not (Test-Na2WindowsAbsolutePath -Text $failureLog)) -Message 'Failure log contains an absolute path.'

    $fakeRepository = Join-Path $testRoot 'help-project'
    New-Item -ItemType Directory -Force -Path (Join-Path $fakeRepository 'scripts\lib') | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\..\_na2.ps1') -Destination $fakeRepository
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\lib\project_paths.ps1') `
        -Destination (Join-Path $fakeRepository 'scripts\lib')
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\lib\run_log.ps1') `
        -Destination (Join-Path $fakeRepository 'scripts\lib')
    $fakeNa2Scripts = Join-Path $fakeRepository 'scripts\na2'
    New-Item -ItemType Directory -Force -Path $fakeNa2Scripts | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'worker_paths.ps1') `
        -Destination $fakeNa2Scripts
    $manifest = @'
{
  "schema_version": 1,
  "roots": {
    "repository": ".",
    "source": "source",
    "utils": "utils",
    "build": "build",
    "logs": "logs",
    "patcher": "na2_patcher",
    "pcsx2_user": "pcsx2_user",
    "pcsx2_files": "pcsx2_files",
    "scripts": "scripts",
    "work": "work"
  },
  "files": {
    "current_iso": "@build/NA2.28 - Current.iso",
    "previous_iso": "@build/NA2.28 - Previous.iso",
    "candidate_iso": "@build/NA2.28 - Candidate.iso"
  }
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeRepository 'project-paths.json') -Content $manifest
    foreach ($directory in @(
        'source', 'utils', 'build', 'logs', 'na2_patcher', 'pcsx2_user',
        'pcsx2_files', 'scripts', 'work'
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $fakeRepository $directory) | Out-Null
    }
    & (Join-Path $fakeRepository '_na2.ps1') -Help | Out-Null
    Assert-Na2Test `
        -Condition (-not (Test-Path -LiteralPath (Join-Path $fakeRepository 'logs\na2'))) `
        -Message 'Help invocation created run logs.'

    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeNa2Scripts 'actualize.ps1') -Content @'
param([string]$ActiveRole)
Write-Host "[fake] actualize $ActiveRole"
[pscustomobject]@{
    ActiveRole = $ActiveRole
    PCSX2Serial = 'SLOP-NA228'
    PCSX2ElfCRC = '12345678'
    CheatsPnach = 'pcsx2_user/cheats/SLOP-NA228_12345678.pnach'
    PnachStatus = 'verified symlink'
    RemovedPnachSymlinks = @()
    GameSettings = 'pcsx2_user/gamesettings/SLOP-NA228_12345678.ini'
    GameSettingsStatus = 'verified symlink'
    RemovedGameSettingsSymlinks = @()
    MemoryCard = 'pcsx2_user/memcards/Mcd001_NA228_Current.ps2'
    MemoryCardStatus = 'preserved'
    EnabledCheats = @()
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeNa2Scripts 'launch.ps1') -Content @'
param([string]$IsoPath, [switch]$KeepExistingInstance)
Write-Host "[fake] launch $IsoPath keep-existing=$KeepExistingInstance"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeNa2Scripts 'build.ps1') -Content @'
param([switch]$CandidateOnly, [string]$WorkerOutputIso)
if ($WorkerOutputIso) {
    Write-Host '[na2] ISO result: worker; rotation: no; PCSX2 left running.'
    [pscustomobject]@{ Status = 'worker' }
}
elseif ($CandidateOnly) {
    Write-Host '[na2] ISO result: candidate; rotation: no; PCSX2 left running.'
    [pscustomobject]@{ Status = 'candidate' }
}
else {
    Write-Host '[na2] ISO result: unchanged; rotation: no.'
    [pscustomobject]@{ Status = 'unchanged' }
}
'@
    & (Join-Path $fakeRepository '_na2.ps1') act
    & (Join-Path $fakeRepository '_na2.ps1') -Current
    & (Join-Path $fakeRepository '_na2.ps1') -Previous
    & (Join-Path $fakeRepository '_na2.ps1') -t
    & (Join-Path $fakeRepository '_na2.ps1') -t 'work\General\build\agent.iso'
    & (Join-Path $fakeRepository '_na2.ps1') -b
    & (Join-Path $fakeRepository '_na2.ps1')
    $fakeLatest = [IO.File]::ReadAllText((Join-Path $fakeRepository 'logs\na2\latest.log'))
    $fakeRolling = [IO.File]::ReadAllText((Join-Path $fakeRepository 'logs\na2\rolling.log'))
    Assert-Na2Test -Condition ($fakeLatest -match '(?m)^mode: build$') -Message 'Root build mode was not logged.'
    foreach ($mode in 'actualize', 'current', 'previous', 'candidate-build', 'build') {
        Assert-Na2Test `
            -Condition ($fakeRolling -match "(?m)^mode: $mode$") `
            -Message "Root $mode dispatch was not logged."
    }
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, '(?m)^--- NA2 RUN BEGIN ---$').Count -eq 6) `
        -Message 'Root dispatch test produced the wrong rolling-log section count.'
    Assert-Na2Test `
        -Condition (-not (Test-Na2WindowsAbsolutePath -Text $fakeRolling)) `
        -Message 'Root dispatch persisted an absolute path.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, 'keep-existing=True').Count -eq 2) `
        -Message 'Current/Previous dispatch did not preserve an existing PCSX2 instance.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, 'keep-existing=False').Count -eq 1) `
        -Message 'Build-and-launch dispatch unexpectedly preserved an existing PCSX2 instance.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, 'ISO result: candidate').Count -eq 1) `
        -Message 'Test build did not dispatch exactly once to Candidate.'
    $workerLatest = [IO.File]::ReadAllText((Join-Path $fakeRepository 'work\General\logs\latest.log'))
    Assert-Na2Test `
        -Condition ($workerLatest -match '(?m)^mode: worker-build$') `
        -Message 'Explicit worker build was not logged under the worker root.'
    Assert-Na2Test `
        -Condition ($workerLatest -match 'ISO result: worker') `
        -Message 'Explicit worker build did not dispatch to worker-output mode.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, 'ISO result: unchanged').Count -eq 2) `
        -Message 'Build-only and build-and-launch did not both use the standard build pipeline.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, '\[fake\] actualize Current').Count -eq 4) `
        -Message 'Current actualization did not cover act, launch, and both standard build paths.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, '\[fake\] actualize Previous').Count -eq 1) `
        -Message 'Previous launch did not actualize Previous PCSX2 state.'
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, '\[fake\] actualize Candidate').Count -eq 1) `
        -Message 'Candidate build did not actualize Candidate PCSX2 state.'
    $structuredLog = Join-Path $logs 'na2'
    $buildRecords = Join-Path $structuredLog 'builds'
    foreach ($buildId in 'old-previous', 'old-current', 'new-current', 'orphan') {
        New-Item -ItemType Directory -Force -Path (Join-Path $buildRecords $buildId) | Out-Null
    }
    Set-Content -NoNewline -LiteralPath $paths.files.current_iso -Value 'current'
    Set-Content -NoNewline -LiteralPath $paths.files.previous_iso -Value 'previous'
    Set-Na2BuildMap `
        -LogDirectory $structuredLog `
        -CurrentBuildId 'old-current' `
        -PreviousBuildId 'old-previous' `
        -ProjectPaths $paths
    $record = Complete-Na2BuildRecord `
        -LogDirectory $structuredLog `
        -BuildId 'new-current' `
        -Result updated `
        -Rotated $true `
        -CurrentIso $paths.files.current_iso `
        -PreviousIso $paths.files.previous_iso `
        -Profile (Join-Path $paths.patcher 'profiles\current') `
        -ProjectPaths $paths
    Assert-Na2Test -Condition ($record.BuildId -eq 'new-current') -Message 'Updated build was not retained.'
    $updatedBuildMap = Read-Na2BuildMap `
        -LogDirectory $structuredLog `
        -ProjectPaths $paths
    Assert-Na2Test `
        -Condition ($updatedBuildMap.CurrentBuildId -eq 'new-current') `
        -Message 'Current build mapping was not advanced.'
    Assert-Na2Test `
        -Condition ($updatedBuildMap.PreviousBuildId -eq 'old-current') `
        -Message 'Previous build mapping was not rotated.'
    $buildMapText = [IO.File]::ReadAllText((Join-Path $structuredLog 'builds.tsv'))
    Assert-Na2Test `
        -Condition ($buildMapText -ceq (
            "iso`tbuild_record`n" +
            "@build/NA2.28 - Current.iso`t@logs/na2/builds/new-current`n" +
            "@build/NA2.28 - Previous.iso`t@logs/na2/builds/old-current`n"
        )) `
        -Message 'builds.tsv does not contain the exact atomic two-ISO mapping.'
    $remainingRecords = @(Get-ChildItem -LiteralPath $buildRecords -Directory).Name
    Assert-Na2Test -Condition ($remainingRecords.Count -eq 2) -Message 'Unreferenced build records were not pruned.'
    $buildResult = [IO.File]::ReadAllText((Join-Path $buildRecords 'new-current\build_result.tsv'))
    Assert-Na2Test -Condition ($buildResult -match "updated`tyes") -Message 'build_result.tsv lacks result/rotation.'
    Assert-Na2Test -Condition ($buildResult -match '@build/NA2\.28 - Current\.iso') -Message 'build_result.tsv lacks a portable ISO path.'
    Assert-Na2Test -Condition (-not (Test-Na2WindowsAbsolutePath -Text $buildResult)) -Message 'build_result.tsv contains an absolute path.'

    New-Item -ItemType Directory -Path (Join-Path $buildRecords 'duplicate') | Out-Null
    $unchanged = Complete-Na2BuildRecord `
        -LogDirectory $structuredLog `
        -BuildId duplicate `
        -Result unchanged `
        -Rotated $false `
        -CurrentIso $paths.files.current_iso `
        -PreviousIso $paths.files.previous_iso `
        -Profile 'na2_patcher/profiles/current' `
        -ProjectPaths $paths
    Assert-Na2Test `
        -Condition ($unchanged.BuildId -eq 'duplicate') `
        -Message 'Unchanged full build did not become the current provenance record.'
    Assert-Na2Test `
        -Condition (Test-Path -LiteralPath (Join-Path $buildRecords 'duplicate')) `
        -Message 'Unchanged full build record was not retained.'
    Assert-Na2Test `
        -Condition (-not (Test-Path -LiteralPath (Join-Path $buildRecords 'new-current'))) `
        -Message 'Superseded current build record was not pruned.'

    $freshStructuredLog = Join-Path $logs 'fresh-na2'
    $firstBuildId = 'first-unchanged'
    New-Item -ItemType Directory -Force `
        -Path (Join-Path $freshStructuredLog "builds\$firstBuildId") | Out-Null
    $firstUnchanged = Complete-Na2BuildRecord `
        -LogDirectory $freshStructuredLog `
        -BuildId $firstBuildId `
        -Result unchanged `
        -Rotated $false `
        -CurrentIso $paths.files.current_iso `
        -PreviousIso $null `
        -Profile 'na2_patcher/profiles/current' `
        -ProjectPaths $paths
    Assert-Na2Test `
        -Condition ($firstUnchanged.BuildId -eq $firstBuildId) `
        -Message 'First unchanged build was incorrectly discarded.'
    $firstBuildMap = Read-Na2BuildMap `
        -LogDirectory $freshStructuredLog `
        -ProjectPaths $paths
    Assert-Na2Test `
        -Condition ($firstBuildMap.CurrentBuildId -eq $firstBuildId) `
        -Message 'First unchanged build did not establish the current mapping.'
    Assert-Na2Test `
        -Condition ([string]::IsNullOrWhiteSpace($firstBuildMap.PreviousBuildId)) `
        -Message 'Unavailable previous ISO record was not left empty.'
    $firstBuildMapText = [IO.File]::ReadAllText((Join-Path $freshStructuredLog 'builds.tsv'))
    Assert-Na2Test `
        -Condition ($firstBuildMapText -match "(?m)^@build/NA2\.28 - Previous\.iso`t$") `
        -Message 'builds.tsv omitted the empty previous ISO row.'
    $firstBuildResult = [IO.File]::ReadAllText(
        (Join-Path $freshStructuredLog "builds\$firstBuildId\build_result.tsv")
    )
    Assert-Na2Test `
        -Condition ($firstBuildResult -match "unchanged`tno") `
        -Message 'First unchanged build result was not recorded.'

    $status = Format-Na2ActualizeStatus `
        -Result ([pscustomobject]@{
            ActiveRole = 'Current'
            PCSX2Serial = 'SLOP-NA228'
            PCSX2ElfCRC = 'C0659AD1'
            CheatsPnach = Join-Path $paths.pcsx2_user 'cheats\SLOP-NA228_C0659AD1.pnach'
            PnachStatus = 'verified symlink'
            RemovedPnachSymlinks = @('old-link')
            GameSettings = Join-Path $paths.pcsx2_user 'gamesettings\SLOP-NA228_C0659AD1.ini'
            GameSettingsStatus = 'verified symlink'
            RemovedGameSettingsSymlinks = @('old-settings')
            MemoryCard = Join-Path $paths.pcsx2_user 'memcards\Mcd001_NA228_Current.ps2'
            MemoryCardStatus = 'preserved'
        }) `
        -ProjectPaths $paths
    Assert-Na2Test -Condition ($status -match '@pcsx2_user/cheats/') -Message 'Actualize status path is not portable.'
    Assert-Na2Test -Condition ($status -match 'CRC=C0659AD1') -Message 'Actualize status omitted the CRC.'
    Assert-Na2Test -Condition ($status -match 'GameSettings') -Message 'Actualize status omitted GameSettings.'
    Assert-Na2Test -Condition ($status -match 'memory card') -Message 'Actualize status omitted the memory card.'

    Write-Host 'NA2 run-log tests passed.' -ForegroundColor Green
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {
    }
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
