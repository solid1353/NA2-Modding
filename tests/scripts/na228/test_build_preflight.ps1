param()

$ErrorActionPreference = 'Stop'
$sourceRepository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))

function Assert-Na2PreflightTest {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

$testRoot = Join-Path ([IO.Path]::GetTempPath()) (
    "na2-build-registry-tests-$PID-$([guid]::NewGuid().ToString('N'))"
)
$activeIncomingLock = $null

try {
    $repository = Join-Path $testRoot 'repository'
    $scriptRoot = Join-Path $repository 'scripts\na228'
    $libRoot = Join-Path $repository 'scripts\lib'
    $e2eScriptRoot = Join-Path $repository 'e2e\scripts'
    New-Item -ItemType Directory -Force `
        -Path $scriptRoot, $libRoot, $e2eScriptRoot | Out-Null
    foreach ($name in 'build.ps1', 'build_registry.ps1') {
        Copy-Item -LiteralPath (Join-Path $sourceRepository "scripts\na228\$name") `
            -Destination $scriptRoot
    }
    [IO.File]::WriteAllText((Join-Path $scriptRoot 'build_targets.ps1'), @'
function Find-Na2BuildTarget {
    param([Collections.IDictionary]$Targets, [string]$Name)
    foreach ($key in $Targets.Keys) {
        if ([string]$key -ieq $Name) { return $Targets[$key] }
    }
    return $null
}
function Get-Na2BuildTargetRegistry {
    param([psobject]$Paths)
    [ordered]@{
        latest = [pscustomobject]@{
            Name = 'latest'
            Entry = [pscustomobject]@{ IsoPath = $Paths.files.latest_iso }
            Configuration = 'dev'
            RotateTo = 'previous'
        }
        previous = [pscustomobject]@{
            Name = 'previous'
            Entry = [pscustomobject]@{ IsoPath = $Paths.files.previous_iso }
            Configuration = $null
            RotateTo = $null
        }
        manual = [pscustomobject]@{
            Name = 'manual'
            Entry = [pscustomobject]@{ IsoPath = $Paths.files.manual_iso }
            Configuration = 'release'
            RotateTo = $null
        }
        e2e_test = [pscustomobject]@{
            Name = 'e2e_test'
            Entry = [pscustomobject]@{ IsoPath = $Paths.files.e2e_test_iso }
            Configuration = 'test'
            RotateTo = $null
        }
    }
}
'@)
    . (Join-Path $scriptRoot 'build_registry.ps1')
    foreach ($name in 'paths.ps1', 'run_log.ps1', 'build_log.ps1') {
        Copy-Item -LiteralPath (Join-Path $sourceRepository "scripts\lib\$name") `
            -Destination $libRoot
    }
    Copy-Item -LiteralPath (Join-Path $sourceRepository 'e2e\scripts\config.ps1') `
        -Destination $e2eScriptRoot
    [IO.File]::WriteAllText((Join-Path $libRoot 'run_python.ps1'), @'
[CmdletBinding()]
param([string]$PackageSet, [string]$Module, [string[]]$ArgumentList, [switch]$NoBytecode)
& python '-B' '-m' $Module @ArgumentList
exit $LASTEXITCODE
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'e2e\config.json'), @'
{
  "schema_version": 1,
  "build_variants": [
    {
      "name": "normal",
      "build": "e2e_test",
      "payload_shift_bytes": 0,
      "publish": true
    }
  ]
}
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'paths.json'), @'
{
  "schema_version": 1,
  "roots": {
    "repository": ".",
    "source": "source",
    "build": "build",
    "logs": "logs",
    "builder": "na228_builder",
    "scripts": "scripts",
    "work": "work",
    "cache": "@build/cache"
  },
  "files": {
    "na2_iso": "@source/NA2.iso",
    "nun5_iso": "@source/NUN5.iso",
    "latest_iso": "@build/Synthetic Product - Latest.iso",
    "previous_iso": "@build/Synthetic Product - Previous.iso",
    "manual_iso": "@build/Synthetic Product - Manual.iso",
    "e2e_test_iso": "@build/Synthetic Product - E2E Test.iso",
    "e2e_test_shifted_iso": "@build/Synthetic Product - E2E Test Shifted.iso"
  }
}
'@)
    . (Join-Path $libRoot 'paths.ps1')
    $testPaths = Get-Na2LocalPaths `
        -ManifestPath (Join-Path $repository 'paths.json') `
        -AllowMissing
    $isoCacheRoot = Join-Path $testPaths.cache 'isos'
    foreach ($directory in @(
        'source', 'build', 'logs\na228\builds\existing',
        'na228_builder\configurations', 'scripts', 'work\Project'
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $repository $directory) | Out-Null
    }
    New-Item -ItemType Directory -Force -Path $isoCacheRoot | Out-Null
    foreach ($name in 'dev', 'test', 'release') {
        [IO.File]::WriteAllText(
            (Join-Path $repository "na228_builder\configurations\$name.json"),
            "{}`n"
        )
    }
    [IO.File]::WriteAllText((Join-Path $repository 'source\NA2.iso'), 'clean na2')
    [IO.File]::WriteAllText((Join-Path $repository 'source\NUN5.iso'), 'clean nun5')
    $latestIso = Join-Path $repository 'build\Synthetic Product - Latest.iso'
    $previousIso = Join-Path $repository 'build\Synthetic Product - Previous.iso'
    [IO.File]::WriteAllText($latestIso, 'old latest')
    [IO.File]::WriteAllText((Join-Path $repository 'logs\na228\builds\existing\data.tsv'), 'old')
    [IO.File]::WriteAllText((Join-Path $repository 'logs\na228\builds.tsv'), @"
iso`tbuild_record
@build/Synthetic Product - Latest.iso`t@logs/na228/builds/existing
@build/Synthetic Product - Previous.iso`t
@build/Synthetic Product - E2E Test.iso`t
@build/Synthetic Product - E2E Test Shifted.iso`t
"@)

    $global:Na2RegistryEntries = @{}
    $global:Na2RegistryCalls = @()
    $global:Na2BuilderCalls = @()
    $global:Na2RegistryRepository = $repository
    $global:Na2RegistryIsoCacheRoot = $isoCacheRoot
    $global:Na2RegistryUnavailable = $false
    function python {
        $arguments = @($args)
        if ($arguments -contains 'na228_builder.scripts.build_preflight') {
            if ($global:Na2RegistryUnavailable) {
                $global:LASTEXITCODE = 9
                return 'synthetic registry outage'
            }
            $moduleIndex = [Array]::IndexOf($arguments, 'na228_builder.scripts.build_preflight')
            $command = $arguments[$moduleIndex + 1]
            $global:Na2RegistryCalls += ,$arguments
            $configIndex = [Array]::IndexOf($arguments, '--configuration')
            $configuration = if ($configIndex -ge 0) { $arguments[$configIndex + 1] } else { '' }
            $key = "$configuration|0"
            $fingerprint = if ($configuration -match 'dev') { 'A' * 64 } else { 'B' * 64 }
            if ($command -eq 'lookup') {
                if (-not $global:Na2RegistryEntries.ContainsKey($key)) {
                    $global:LASTEXITCODE = 0
                    return (@{ status='miss'; reason='fingerprint-missing'; fingerprint=$fingerprint } | ConvertTo-Json -Compress)
                }
                $entry = $global:Na2RegistryEntries[$key]
                $result = @{
                    status = 'hit'; reason = 'verified-build-match'; fingerprint = $fingerprint
                    output_size_bytes = $entry.Size; output_sha256 = $entry.Hash
                    provenance = $entry.Provenance
                }
                $result.image = $entry.Image
                $global:LASTEXITCODE = 0
                return ($result | ConvertTo-Json -Compress)
            }
            if ($command -eq 'record') {
                $provenanceIndex = [Array]::IndexOf($arguments, '--provenance') + 1
                $central = Join-Path $global:Na2RegistryRepository "logs\na228\preflight\records\$fingerprint"
                New-Item -ItemType Directory -Force -Path $central | Out-Null
                Get-ChildItem -LiteralPath $arguments[$provenanceIndex] -Force | Copy-Item -Destination $central -Recurse
                $imageIndex = [Array]::IndexOf($arguments, '--image')
                $incoming = $arguments[$imageIndex + 1]
                $item = Get-Item -LiteralPath $incoming
                $hash = (Get-FileHash -LiteralPath $incoming -Algorithm SHA256).Hash
                $cached = Join-Path $global:Na2RegistryIsoCacheRoot "$hash.iso"
                [IO.File]::Move($incoming, $cached, $true)
                $size = $item.Length
                $entry = [pscustomobject]@{
                    Size=$size; Hash=$hash; Image=$cached; Provenance=$central
                }
                $global:Na2RegistryEntries[$key] = $entry
                $result = @{
                    status='recorded'; reason='verified-build-recorded'; fingerprint=$fingerprint
                    output_size_bytes=$size; output_sha256=$hash; provenance=$central
                }
                if ($null -ne $cached) { $result.image = $cached }
                $global:LASTEXITCODE = 0
                return ($result | ConvertTo-Json -Compress)
            }
            if ($command -eq 'complete') {
                $global:LASTEXITCODE = 0
                return (@{ status='completed'; fingerprint=$fingerprint } | ConvertTo-Json -Compress)
            }
            $global:LASTEXITCODE = 0
            return (@{ status=$command; fingerprint=$fingerprint } | ConvertTo-Json -Compress)
        }
        if ($arguments -contains 'na228_builder.scripts.build_configuration') {
            $global:Na2BuilderCalls += ,$arguments
            $output = $arguments[[Array]::IndexOf($arguments, '--output') + 1]
            $record = $arguments[[Array]::IndexOf($arguments, '--configuration-log-directory') + 1]
            $recordPath = Join-Path $global:Na2RegistryRepository $record
            New-Item -ItemType Directory -Force -Path $recordPath | Out-Null
            [IO.File]::WriteAllText((Join-Path $recordPath 'configuration.tsv'), 'verified')
            New-Item -ItemType Directory -Force -Path ([IO.Path]::GetDirectoryName($output)) | Out-Null
            [IO.File]::WriteAllText($output, 'verified development')
            $global:LASTEXITCODE = 0
            return "Verified ISO candidate: $([IO.Path]::GetFileName($output))"
        }
        throw "Unexpected python invocation: $($arguments -join ' ')"
    }

    $incomingRoot = Join-Path $isoCacheRoot '.incoming'
    New-Item -ItemType Directory -Path $incomingRoot -Force | Out-Null
    $staleIncoming = Join-Path $incomingRoot 'stale.iso'
    $activeIncoming = Join-Path $incomingRoot 'active.iso'
    [IO.File]::WriteAllText($staleIncoming, 'stale')
    [IO.File]::WriteAllText($activeIncoming, 'active')
    $activeIncomingLockPath = $activeIncoming + '.lock'
    $activeIncomingLock = [IO.File]::Open(
        $activeIncomingLockPath,
        [IO.FileMode]::CreateNew,
        [IO.FileAccess]::ReadWrite,
        [IO.FileShare]::None
    )

    $first = & (Join-Path $scriptRoot 'build.ps1')
    Assert-Na2PreflightTest ($first.Status -eq 'updated') 'First Latest build was not promoted.'
    Assert-Na2PreflightTest ($first.ConfigurationId -ceq 'dev') 'Latest did not use its owned configuration.'
    Assert-Na2PreflightTest (-not $first.PreflightCacheHit) 'First build was incorrectly a registry hit.'
    Assert-Na2PreflightTest ([IO.File]::ReadAllText($latestIso) -ceq 'verified development') 'Latest did not receive the verified image.'
    Assert-Na2PreflightTest ([IO.File]::ReadAllText($previousIso) -ceq 'old latest') 'Latest rotation did not preserve Previous.'
    Assert-Na2PreflightTest ((Get-Item -LiteralPath $latestIso).LinkType -eq 'HardLink') 'Latest was not published as a hardlink.'
    Assert-Na2PreflightTest ((Get-Item -LiteralPath $previousIso).LinkType -eq 'HardLink') 'Previous was not published as a hardlink.'
    Assert-Na2PreflightTest ($global:Na2BuilderCalls.Count -eq 1) 'First build did not assemble exactly once.'
    Assert-Na2PreflightTest (-not (Test-Path -LiteralPath $staleIncoming)) 'A stale incoming ISO was not reclaimed.'
    Assert-Na2PreflightTest (Test-Path -LiteralPath $activeIncoming -PathType Leaf) 'A locked active incoming ISO was removed.'
    $firstLookup = @(
        $global:Na2RegistryCalls | Where-Object {
            $_[[Array]::IndexOf($_, 'na228_builder.scripts.build_preflight') + 1] -eq 'lookup'
        }
    )[0]
    Assert-Na2PreflightTest (-not ($firstLookup -contains '--fingerprint')) 'Registry lookup received a completion-only fingerprint argument.'
    Assert-Na2PreflightTest (-not ($firstLookup -contains '--location')) 'Registry lookup received a completion-only location argument.'
    $firstComplete = @(
        $global:Na2RegistryCalls | Where-Object {
            $_[[Array]::IndexOf($_, 'na228_builder.scripts.build_preflight') + 1] -eq 'complete'
        }
    )[-1]
    $completedLocations = for ($index = 0; $index -lt $firstComplete.Count; $index++) {
        if ($firstComplete[$index] -eq '--location') { $firstComplete[$index + 1] }
    }
    Assert-Na2PreflightTest ($completedLocations.Count -eq 2) 'Latest rotation did not report both physical locations.'
    Assert-Na2PreflightTest ($completedLocations -contains $latestIso) 'Latest location was not synchronized.'
    Assert-Na2PreflightTest ($completedLocations -contains $previousIso) 'Previous location was not synchronized.'
    $activeIncomingLock.Dispose()
    Remove-Item -LiteralPath $activeIncoming,$activeIncomingLockPath -Force

    $second = & (Join-Path $scriptRoot 'build.ps1')
    Assert-Na2PreflightTest ($second.Status -eq 'unchanged') 'Repeated Latest build was not unchanged.'
    Assert-Na2PreflightTest $second.PreflightCacheHit 'Repeated Latest build did not reuse the registry.'
    Assert-Na2PreflightTest ($global:Na2BuilderCalls.Count -eq 1) 'Registry hit rebuilt the image.'

    $developmentEntry = $global:Na2RegistryEntries['na228_builder\configurations\dev.json|0']
    $cacheImage = Join-Path $isoCacheRoot "$($developmentEntry.Hash).iso"
    Assert-Na2PreflightTest (Test-Path -LiteralPath $cacheImage -PathType Leaf) 'Latest promotion did not retain its canonical cache image.'
    $developmentEntry.Image = $cacheImage
    Remove-Item -LiteralPath $latestIso -Force
    New-Item -ItemType Directory -Path $latestIso | Out-Null
    $pending = & (Join-Path $scriptRoot 'build.ps1')
    Assert-Na2PreflightTest ($pending.Status -eq 'pending') 'Blocked promotion did not retain a pending result.'
    Assert-Na2PreflightTest ($pending.LaunchIso -ceq $cacheImage) 'Blocked promotion did not expose the cached launch image.'
    Assert-Na2PreflightTest (Test-Path -LiteralPath $cacheImage -PathType Leaf) 'Blocked promotion lost the verified cached ISO.'
    Assert-Na2PreflightTest ($global:Na2BuilderCalls.Count -eq 1) 'Blocked registry hit rebuilt the image.'
    Remove-Item -LiteralPath $latestIso -Force
    $retried = & (Join-Path $scriptRoot 'build.ps1')
    Assert-Na2PreflightTest ($retried.Status -eq 'updated') 'Next matching build did not retry pending promotion.'
    Assert-Na2PreflightTest ($global:Na2BuilderCalls.Count -eq 1) 'Pending promotion retry rebuilt the image.'

    $cacheLogDirectory = Join-Path $repository 'work\Project\logs'
    $cacheBuild = & (Join-Path $scriptRoot 'build.ps1') `
        -CacheConfiguration dev `
        -CacheLogDirectory $cacheLogDirectory
    Assert-Na2PreflightTest $cacheBuild.PreflightCacheHit 'Cache build did not reuse the Latest verification.'
    Assert-Na2PreflightTest ($cacheBuild.OutputIso -ceq $cacheImage) 'Cache build did not return the canonical cached ISO.'
    Assert-Na2PreflightTest (@(Get-ChildItem -LiteralPath (Join-Path $repository 'work\Project') -Recurse -Filter '*.iso' -File).Count -eq 0) 'Cache build materialized a task-owned ISO.'
    Assert-Na2PreflightTest ($global:Na2BuilderCalls.Count -eq 1) 'Cache reuse rebuilt the image.'

    $e2e = & (Join-Path $scriptRoot 'build.ps1') -E2eVariant normal
    $e2eIso = Join-Path $repository 'build\Synthetic Product - E2E Test.iso'
    Assert-Na2PreflightTest ($e2e.Status -eq 'e2e-test') 'E2E build did not return e2e-test status.'
    Assert-Na2PreflightTest ($e2e.E2eVariant -ceq 'normal') 'E2E build did not retain its variant.'
    Assert-Na2PreflightTest ($e2e.ConfigurationId -ceq 'test') 'E2E did not use its build target configuration.'
    Assert-Na2PreflightTest ($e2e.OutputIso -ceq $e2eIso) 'E2E build did not resolve the configured build selector to its ISO.'
    Assert-Na2PreflightTest (Test-Path -LiteralPath $e2eIso -PathType Leaf) 'E2E build did not publish its configured ISO.'

    Assert-Na2PreflightTest (@(Get-ChildItem -LiteralPath $repository -Recurse -Filter '*.building' -File).Count -eq 0) 'Build workflow created a .building ISO.'

    $otherIsoRoot = Join-Path $repository 'work\other\isos'
    New-Item -ItemType Directory -Path $otherIsoRoot -Force | Out-Null
    $otherIso = Join-Path $otherIsoRoot 'retained.iso'
    $otherDestination = Join-Path $repository 'work\Project\build\copied.iso'
    [IO.File]::WriteAllText($otherIso, 'retained source')
    $otherHash = (Get-FileHash -LiteralPath $otherIso -Algorithm SHA256).Hash
    $otherPromotion = Publish-Na2VerifiedImage `
        -Candidate $otherIso `
        -Destination $otherDestination `
        -Size (Get-Item -LiteralPath $otherIso).Length `
        -Sha256 $otherHash `
        -CacheRoot $isoCacheRoot
    Assert-Na2PreflightTest ($otherPromotion.Status -eq 'updated') 'A retained registry location was not copied.'
    Assert-Na2PreflightTest (Test-Path -LiteralPath $otherIso -PathType Leaf) 'A non-cache directory named isos was mistaken for the shared cache.'
    Assert-Na2PreflightTest ((Get-Item -LiteralPath $otherDestination).LinkType -eq 'HardLink') 'A retained registry location was not materialized as a hardlink.'

    $global:Na2RegistryUnavailable = $true
    $manual = & (Join-Path $scriptRoot 'build.ps1') -ManualOnly -Force
    $manualIso = Join-Path $repository 'build\Synthetic Product - Manual.iso'
    Assert-Na2PreflightTest ($manual.Status -eq 'manual') 'Force mode did not complete through a registry outage.'
    Assert-Na2PreflightTest ($manual.ConfigurationId -ceq 'release') 'Manual did not use its owned configuration.'
    Assert-Na2PreflightTest (Test-Path -LiteralPath $manualIso -PathType Leaf) 'Force mode did not promote its verified Manual ISO.'
    Assert-Na2PreflightTest (@(Get-ChildItem -LiteralPath (Join-Path $isoCacheRoot '.incoming') -File -ErrorAction SilentlyContinue).Count -eq 0) 'Force registry fallback left an incoming ISO.'
    $global:Na2RegistryUnavailable = $false

    Write-Host 'NA2 shared build registry PowerShell tests passed.' -ForegroundColor Green
}
finally {
    if ($null -ne $activeIncomingLock) {
        $activeIncomingLock.Dispose()
    }
    Remove-Variable Na2RegistryEntries -Scope Global -ErrorAction SilentlyContinue
    Remove-Variable Na2RegistryCalls -Scope Global -ErrorAction SilentlyContinue
    Remove-Variable Na2BuilderCalls -Scope Global -ErrorAction SilentlyContinue
    Remove-Variable Na2RegistryRepository -Scope Global -ErrorAction SilentlyContinue
    Remove-Variable Na2RegistryIsoCacheRoot -Scope Global -ErrorAction SilentlyContinue
    Remove-Variable Na2RegistryUnavailable -Scope Global -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
