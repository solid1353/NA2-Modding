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
        pcsx2 = Join-Path $testRoot 'pcsx2'
        scripts = Join-Path $repository 'scripts'
    }
    New-Item -ItemType Directory -Force -Path $logs, $build | Out-Null
    $externalPath = 'C{0}{1}Private{1}outside.txt' -f `
        [IO.Path]::VolumeSeparatorChar, [IO.Path]::DirectorySeparatorChar

    $portable = ConvertTo-Na2PortableText `
        -Text "ISO: $build\Current.iso`nExternal: $externalPath" `
        -ProjectPaths $paths
    Assert-Na2Test `
        -Condition ($portable -match 'ISO: @build/Current\.iso') `
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
        Write-Host "run-marker-$index $build\Current.iso"
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
    Write-Host "failure marker $build\Current.iso"
    $failureExternalPath = 'C{0}{1}Private{1}failure.txt' -f `
        [IO.Path]::VolumeSeparatorChar, [IO.Path]::DirectorySeparatorChar
    Complete-Na2RunLog `
        -Context $failureContext `
        -Outcome failed `
        -FailureMessage "Configured: $build\Current.iso`nExternal: $failureExternalPath"
    $failureLog = [IO.File]::ReadAllText((Join-Path $failurePaths.logs 'na2\latest.log'))
    Assert-Na2Test -Condition ($failureLog -match '(?m)^outcome: failed$') -Message 'Failed outcome was not recorded.'
    Assert-Na2Test -Condition ($failureLog -match '@build/Current\.iso') -Message 'Failure path was not made portable.'
    Assert-Na2Test -Condition (-not (Test-Na2WindowsAbsolutePath -Text $failureLog)) -Message 'Failure log contains an absolute path.'

    $fakeRepository = Join-Path $testRoot 'help-project'
    New-Item -ItemType Directory -Force -Path (Join-Path $fakeRepository 'scripts\lib') | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\..\_na2.ps1') -Destination $fakeRepository
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\lib\project_paths.ps1') `
        -Destination (Join-Path $fakeRepository 'scripts\lib')
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\lib\run_log.ps1') `
        -Destination (Join-Path $fakeRepository 'scripts\lib')
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
    "pcsx2": "pcsx2",
    "pcsx2_files": "pcsx2_files",
    "releases": "releases",
    "scripts": "scripts",
    "work": "work"
  }
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeRepository 'project-paths.json') -Content $manifest
    foreach ($directory in @(
        'source', 'utils', 'build', 'logs', 'na2_patcher', 'pcsx2',
        'pcsx2_files', 'releases', 'scripts', 'work'
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $fakeRepository $directory) | Out-Null
    }
    & (Join-Path $fakeRepository '_na2.ps1') -Help | Out-Null
    Assert-Na2Test `
        -Condition (-not (Test-Path -LiteralPath (Join-Path $fakeRepository 'logs\na2'))) `
        -Message 'Help invocation created run logs.'

    $fakeNa2Scripts = Join-Path $fakeRepository 'scripts\na2'
    New-Item -ItemType Directory -Force -Path $fakeNa2Scripts | Out-Null
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeNa2Scripts 'actualize_pnach.ps1') -Content @'
[pscustomobject]@{
    PCSX2ElfCRC = $null
    CheatsPnach = $null
    PnachStatus = 'skipped empty canonical PNACH'
    RemovedPnachSymlinks = @()
    EnabledCheats = @()
}
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeNa2Scripts 'launch.ps1') -Content @'
param([string]$IsoPath)
Write-Host "[fake] launch $IsoPath"
'@
    Set-Na2Utf8FileAtomic -Path (Join-Path $fakeNa2Scripts 'build.ps1') -Content @'
Write-Host '[na2] ISO result: unchanged; rotation: no.'
[pscustomobject]@{ Status = 'unchanged' }
'@
    & (Join-Path $fakeRepository '_na2.ps1') act
    & (Join-Path $fakeRepository '_na2.ps1') -Current
    & (Join-Path $fakeRepository '_na2.ps1') -Previous
    & (Join-Path $fakeRepository '_na2.ps1')
    $fakeLatest = [IO.File]::ReadAllText((Join-Path $fakeRepository 'logs\na2\latest.log'))
    $fakeRolling = [IO.File]::ReadAllText((Join-Path $fakeRepository 'logs\na2\rolling.log'))
    Assert-Na2Test -Condition ($fakeLatest -match '(?m)^mode: build$') -Message 'Root build mode was not logged.'
    foreach ($mode in 'actualize', 'current', 'previous', 'build') {
        Assert-Na2Test `
            -Condition ($fakeRolling -match "(?m)^mode: $mode$") `
            -Message "Root $mode dispatch was not logged."
    }
    Assert-Na2Test `
        -Condition ([regex]::Matches($fakeRolling, '(?m)^--- NA2 RUN BEGIN ---$').Count -eq 4) `
        -Message 'Root dispatch test produced the wrong rolling-log section count.'
    Assert-Na2Test `
        -Condition (-not (Test-Na2WindowsAbsolutePath -Text $fakeRolling)) `
        -Message 'Root dispatch persisted an absolute path.'

    $structuredLog = Join-Path $logs 'na2'
    $buildRecords = Join-Path $structuredLog 'builds'
    foreach ($buildId in 'old-previous', 'old-current', 'new-current', 'orphan') {
        New-Item -ItemType Directory -Force -Path (Join-Path $buildRecords $buildId) | Out-Null
    }
    Set-Content -NoNewline -LiteralPath (Join-Path $build 'Current.iso') -Value 'current'
    Set-Content -NoNewline -LiteralPath (Join-Path $build 'Previous.iso') -Value 'previous'
    Set-Na2BuildMap `
        -LogDirectory $structuredLog `
        -CurrentBuildId 'old-current' `
        -PreviousBuildId 'old-previous'
    $record = Complete-Na2BuildRecord `
        -LogDirectory $structuredLog `
        -BuildId 'new-current' `
        -Result updated `
        -Rotated $true `
        -CurrentIso (Join-Path $build 'Current.iso') `
        -PreviousIso (Join-Path $build 'Previous.iso') `
        -Profile (Join-Path $paths.patcher 'profiles\current') `
        -ProjectPaths $paths
    Assert-Na2Test -Condition ($record.BuildId -eq 'new-current') -Message 'Updated build was not retained.'
    $updatedBuildMap = Read-Na2BuildMap -LogDirectory $structuredLog
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
            "@build/Current.iso`t@logs/na2/builds/new-current`n" +
            "@build/Previous.iso`t@logs/na2/builds/old-current`n"
        )) `
        -Message 'builds.tsv does not contain the exact atomic two-ISO mapping.'
    $remainingRecords = @(Get-ChildItem -LiteralPath $buildRecords -Directory).Name
    Assert-Na2Test -Condition ($remainingRecords.Count -eq 2) -Message 'Unreferenced build records were not pruned.'
    $buildResult = [IO.File]::ReadAllText((Join-Path $buildRecords 'new-current\build_result.tsv'))
    Assert-Na2Test -Condition ($buildResult -match "updated`tyes") -Message 'build_result.tsv lacks result/rotation.'
    Assert-Na2Test -Condition ($buildResult -match '@build/Current\.iso') -Message 'build_result.tsv lacks a portable ISO path.'
    Assert-Na2Test -Condition (-not (Test-Na2WindowsAbsolutePath -Text $buildResult)) -Message 'build_result.tsv contains an absolute path.'

    New-Item -ItemType Directory -Path (Join-Path $buildRecords 'duplicate') | Out-Null
    $unchanged = Complete-Na2BuildRecord `
        -LogDirectory $structuredLog `
        -BuildId duplicate `
        -Result unchanged `
        -Rotated $false `
        -CurrentIso (Join-Path $build 'Current.iso') `
        -PreviousIso (Join-Path $build 'Previous.iso') `
        -Profile 'na2_patcher/profiles/current' `
        -ProjectPaths $paths
    Assert-Na2Test -Condition $unchanged.Reused -Message 'Unchanged build did not reuse the current record.'
    Assert-Na2Test `
        -Condition (-not (Test-Path -LiteralPath (Join-Path $buildRecords 'duplicate'))) `
        -Message 'Duplicate unchanged build record was retained.'

    $freshStructuredLog = Join-Path $logs 'fresh-na2'
    $firstBuildId = 'first-unchanged'
    New-Item -ItemType Directory -Force `
        -Path (Join-Path $freshStructuredLog "builds\$firstBuildId") | Out-Null
    $firstUnchanged = Complete-Na2BuildRecord `
        -LogDirectory $freshStructuredLog `
        -BuildId $firstBuildId `
        -Result unchanged `
        -Rotated $false `
        -CurrentIso (Join-Path $build 'Current.iso') `
        -PreviousIso $null `
        -Profile 'na2_patcher/profiles/current' `
        -ProjectPaths $paths
    Assert-Na2Test -Condition (-not $firstUnchanged.Reused) -Message 'First unchanged build was incorrectly discarded.'
    $firstBuildMap = Read-Na2BuildMap -LogDirectory $freshStructuredLog
    Assert-Na2Test `
        -Condition ($firstBuildMap.CurrentBuildId -eq $firstBuildId) `
        -Message 'First unchanged build did not establish the current mapping.'
    Assert-Na2Test `
        -Condition ([string]::IsNullOrWhiteSpace($firstBuildMap.PreviousBuildId)) `
        -Message 'Unavailable Previous.iso record was not left empty.'
    $firstBuildMapText = [IO.File]::ReadAllText((Join-Path $freshStructuredLog 'builds.tsv'))
    Assert-Na2Test `
        -Condition ($firstBuildMapText -match "(?m)^@build/Previous\.iso`t$") `
        -Message 'builds.tsv omitted the empty Previous.iso row.'
    $firstBuildResult = [IO.File]::ReadAllText(
        (Join-Path $freshStructuredLog "builds\$firstBuildId\build_result.tsv")
    )
    Assert-Na2Test `
        -Condition ($firstBuildResult -match "unchanged`tno") `
        -Message 'First unchanged build result was not recorded.'

    $status = Format-Na2ActualizeStatus `
        -Result ([pscustomobject]@{
            PCSX2ElfCRC = 'C0659AD1'
            CheatsPnach = Join-Path $paths.pcsx2 'cheats\SLPS-25837_C0659AD1.pnach'
            PnachStatus = 'verified symlink'
            RemovedPnachSymlinks = @('old-link')
        }) `
        -ProjectPaths $paths
    Assert-Na2Test -Condition ($status -match '@pcsx2/cheats/') -Message 'Actualize status path is not portable.'
    Assert-Na2Test -Condition ($status -match 'CRC=C0659AD1') -Message 'Actualize status omitted the CRC.'

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
