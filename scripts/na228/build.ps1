[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Configuration,
    [switch]$Force,
    [string]$LogDirectory,
    [string]$Postfix,
    [string]$OverridesJson
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\builder_module.ps1')
. (Join-Path $PSScriptRoot 'build_registry.ps1')
$paths = Get-Na2Paths
$registryPath = Join-Path $paths.logs 'na228\preflight\registry.json'
$buildRoot = [IO.Path]::GetFullPath([string]$paths.build)
$incomingRoot = Join-Path $buildRoot '.incoming'

if ($Configuration -cnotmatch '^[a-z][a-z0-9_-]*$') {
    throw "Invalid build configuration: $Configuration"
}
$configurationPath = Join-Path $paths.builder "configurations\$Configuration.jsonc"
if (-not (Test-Path -LiteralPath $configurationPath -PathType Leaf)) {
    throw "Build configuration does not exist: $Configuration"
}
$configurationRelative = [IO.Path]::GetRelativePath(
    $paths.repository,
    $configurationPath
)
$recordBase = if ([string]::IsNullOrWhiteSpace($LogDirectory)) {
    Join-Path $paths.logs 'na228\builds'
}
else {
    Join-Path ([IO.Path]::GetFullPath($LogDirectory)) 'builds'
}
$buildId = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + "_pid$PID"
$configurationLog = Join-Path $recordBase $buildId
$configurationLogRelative = [IO.Path]::GetRelativePath(
    $paths.repository,
    $configurationLog
)

try {
[void](New-Item -ItemType Directory -Path $incomingRoot -Force)
Remove-Na2StaleIncomingImages -IncomingRoot $incomingRoot
$registryArguments = @{
    Registry = $registryPath
    BuildRoot = $buildRoot
    Repository = $paths.repository
    Na2Iso = $paths.files.na2_iso
    Configuration = $configurationRelative
}
if ($PSBoundParameters.ContainsKey('Postfix')) {
    $registryArguments.Postfix = $Postfix
}
if ($PSBoundParameters.ContainsKey('OverridesJson')) {
    $registryArguments.OverridesJson = $OverridesJson
}
$verification = Invoke-Na2BuildRegistry -Command lookup @registryArguments
$cacheHit = -not $Force -and $verification.status -eq 'hit'
$configurationLogComplete = $false

if ($cacheHit) {
    Write-Host (
        "[na228] Reusing $Configuration build; SHA-256 " +
        "$($verification.output_sha256)."
    ) -ForegroundColor Cyan
}
else {
    Write-Host "[na228] Building $Configuration." -ForegroundColor Cyan
    $incomingIso = Join-Path $incomingRoot "$buildId.iso"
    $incomingLock = Enter-Na2IncomingImage -Image $incomingIso
    try {
        $builderArguments = @(
            '--source', $paths.files.na2_iso,
            '--build-id', $buildId,
            '--configuration', $configurationRelative,
            '--configuration-log-directory', $configurationLogRelative
        )
        if ($PSBoundParameters.ContainsKey('OverridesJson')) {
            $builderArguments += @('--overrides-json', $OverridesJson)
        }
        $execution = Invoke-Na2BuilderModule -Repository $paths.repository `
            -Module build_configuration -ArgumentList $builderArguments
        Assert-Na2BuilderModuleSucceeded -Execution $execution `
            -FailureMessage "NA2 $Configuration build failed (exit $($execution.ExitCode))."
        $execution.Output | ForEach-Object { Write-Host $_ }
        if (-not (Test-Path -LiteralPath $incomingIso -PathType Leaf)) {
            throw "Verified ISO candidate does not exist: $incomingIso"
        }
        $recordArguments = @{
            ExpectedFingerprint = [string]$verification.fingerprint
            Image = $incomingIso
            Force = $Force
        }
        $configurationLogComplete = Test-Path `
            -LiteralPath (Join-Path $configurationLog 'run_summary.tsv') -PathType Leaf
        if ($configurationLogComplete) {
            $recordArguments.Provenance = $configurationLog
        }
        $recorded = Invoke-Na2BuildRegistry -Command record `
            @registryArguments @recordArguments
        if ($recorded.status -ne 'recorded') {
            throw "Verified build was not registered: $($recorded.reason)"
        }
        $verification = $recorded
    }
    finally {
        if ($null -ne $incomingLock) {
            Exit-Na2IncomingImage -Image $incomingIso -Lock $incomingLock
        }
    }
}

$outputIso = [string]$verification.image
if ([string]::IsNullOrWhiteSpace($outputIso) -or
    -not (Test-Path -LiteralPath $outputIso -PathType Leaf)) {
    throw 'Verification registry returned no reusable physical ISO.'
}
return [pscustomobject]@{
    Status = if ($cacheHit) { 'reused' } else { 'built' }
    OutputIso = [IO.Path]::GetFullPath($outputIso)
    OutputSizeBytes = [long]$verification.output_size_bytes
    OutputSha256 = [string]$verification.output_sha256
    Fingerprint = [string]$verification.fingerprint
    BuildId = $buildId
    ConfigurationLogDirectory = if ($cacheHit -or $configurationLogComplete) {
        [string]$verification.provenance
    }
    else {
        ''
    }
    PreflightCacheHit = $cacheHit
    ConfigurationId = $Configuration
}
}
finally {
    try {
        if ((Test-Path -LiteralPath $incomingRoot -PathType Container) -and
            @(Get-ChildItem -LiteralPath $incomingRoot -Force).Count -eq 0) {
            Remove-Item -LiteralPath $incomingRoot -Force
        }
    }
    catch {
        Write-Warning "Could not remove empty incoming build directory: $incomingRoot"
    }
}
