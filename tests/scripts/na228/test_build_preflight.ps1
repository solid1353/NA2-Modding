[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$sourceRepository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$testRoot = Join-Path $env:TEMP ('na228-build-preflight-' + [Guid]::NewGuid().ToString('N'))
$repository = Join-Path $testRoot 'repository'
$activeLock = $null

function Assert-BuildPreflight {
    param([Parameter(Mandatory)][bool]$Condition, [Parameter(Mandatory)][string]$Message)
    if (-not $Condition) { throw $Message }
}

try {
    foreach ($directory in @(
        'build', 'logs', 'scripts\lib', 'scripts\na228',
        'na228_builder\configurations', 'source'
    )) {
        [void](New-Item -ItemType Directory -Path (Join-Path $repository $directory) -Force)
    }
    foreach ($name in 'build.ps1', 'build_registry.ps1') {
        Copy-Item -LiteralPath (Join-Path $sourceRepository "scripts\na228\$name") `
            -Destination (Join-Path $repository "scripts\na228\$name")
    }
    [IO.File]::WriteAllText((Join-Path $repository 'na228_builder\configurations\base.json'), '{}')
    [IO.File]::WriteAllText((Join-Path $repository 'source\na2.iso'), 'source')
    [IO.File]::WriteAllText((Join-Path $repository 'source\nun5.iso'), 'donor')
    [IO.File]::WriteAllText((Join-Path $repository 'scripts\lib\run_log.ps1'), '')
    [IO.File]::WriteAllText((Join-Path $repository 'scripts\lib\paths.ps1'), @'
function Get-Na2Paths {
    $repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
    [pscustomobject]@{
        repository = $repository
        scripts = Join-Path $repository 'scripts'
        builder = Join-Path $repository 'na228_builder'
        build = Join-Path $repository 'build'
        logs = Join-Path $repository 'logs'
        files = [pscustomobject]@{
            na2_iso = Join-Path $repository 'source\na2.iso'
            nun5_iso = Join-Path $repository 'source\nun5.iso'
        }
    }
}
'@)
    [IO.File]::WriteAllText((Join-Path $repository 'scripts\lib\run_python.ps1'), @'
param(
    [string]$PackageSet,
    [string]$Module,
    [string[]]$ArgumentList,
    [switch]$NoBytecode
)
$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
function Get-ArgumentValue([string]$Name) {
    $index = [Array]::IndexOf($ArgumentList, $Name)
    if ($index -lt 0) { return '' }
    return $ArgumentList[$index + 1]
}
if ($Module -ceq 'na228_builder.scripts.build_configuration') {
    $output = Get-ArgumentValue '--output'
    $provenance = Join-Path $repository (Get-ArgumentValue '--configuration-log-directory')
    [void](New-Item -ItemType Directory -Path $provenance -Force)
    [IO.File]::WriteAllText($output, 'built-image')
    [IO.File]::WriteAllText((Join-Path $repository 'builder-called.txt'), 'yes')
    Write-Output 'builder complete'
    exit 0
}
if ($Module -cne 'na228_builder.scripts.build_preflight') { exit 3 }
$command = $ArgumentList[0]
$cached = Join-Path $repository 'build\cached.iso'
if ($command -ceq 'lookup') {
    if (Test-Path -LiteralPath (Join-Path $repository 'cache-hit.txt')) {
        [ordered]@{
            status = 'hit'; image = $cached; output_size_bytes = 12
            output_sha256 = 'ABC'; fingerprint = 'FINGERPRINT'; provenance = 'logs/builds/existing'
        } | ConvertTo-Json -Compress
    }
    else {
        [ordered]@{ status = 'miss'; fingerprint = 'FINGERPRINT' } | ConvertTo-Json -Compress
    }
    exit 0
}
if ($command -ceq 'record') {
    $image = Get-ArgumentValue '--image'
    Move-Item -LiteralPath $image -Destination $cached -Force
    [ordered]@{
        status = 'recorded'; image = $cached; output_size_bytes = 11
        output_sha256 = 'DEF'; fingerprint = 'FINGERPRINT'; provenance = (Get-ArgumentValue '--provenance')
    } | ConvertTo-Json -Compress
    exit 0
}
exit 4
'@)

    $buildScript = Join-Path $repository 'scripts\na228\build.ps1'
    $built = & $buildScript -Configuration base
    Assert-BuildPreflight ($built.Status -ceq 'built') 'Cache miss did not report a built ISO.'
    Assert-BuildPreflight ($built.OutputIso -ceq (Join-Path $repository 'build\cached.iso')) `
        'Cache miss did not return the registered ISO.'
    Assert-BuildPreflight (Test-Path -LiteralPath (Join-Path $repository 'builder-called.txt')) `
        'Cache miss did not invoke the builder.'
    Assert-BuildPreflight (
        @(Get-ChildItem -LiteralPath (Join-Path $repository 'build\.incoming') -Force).Count -eq 0
    ) 'Completed build left an incoming ISO or lock.'

    Remove-Item -LiteralPath (Join-Path $repository 'builder-called.txt') -Force
    [IO.File]::WriteAllText((Join-Path $repository 'cache-hit.txt'), 'yes')
    $reused = & $buildScript -Configuration base
    Assert-BuildPreflight ($reused.Status -ceq 'reused' -and $reused.PreflightCacheHit) `
        'Cache hit did not report a reused ISO.'
    Assert-BuildPreflight (-not (Test-Path -LiteralPath (Join-Path $repository 'builder-called.txt'))) `
        'Cache hit invoked the builder.'

    $missingRejected = $false
    try { $null = & $buildScript -Configuration missing }
    catch { $missingRejected = $_.Exception.Message -match 'does not exist' }
    Assert-BuildPreflight $missingRejected 'Missing configuration was not rejected.'

    . (Join-Path $repository 'scripts\na228\build_registry.ps1')
    $incomingRoot = Join-Path $repository 'build\.incoming'
    $staleImage = Join-Path $incomingRoot 'stale.iso'
    [IO.File]::WriteAllText($staleImage, 'stale')
    $activeLock = Enter-Na2IncomingImage -Image $staleImage
    Remove-Na2StaleIncomingImages -IncomingRoot $incomingRoot
    Assert-BuildPreflight (Test-Path -LiteralPath $staleImage) `
        'Cleanup removed an actively locked incoming ISO.'
    $activeLock.Dispose()
    $activeLock = $null
    Remove-Na2StaleIncomingImages -IncomingRoot $incomingRoot
    Assert-BuildPreflight (-not (Test-Path -LiteralPath $staleImage)) `
        'Cleanup retained an unlocked stale incoming ISO.'

    Write-Host 'NA228 build-preflight tests passed.' -ForegroundColor Green
}
finally {
    if ($null -ne $activeLock) { $activeLock.Dispose() }
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
