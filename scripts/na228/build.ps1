[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Configuration,
    [string]$LogDirectory
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\run_log.ps1')
. (Join-Path $PSScriptRoot 'build_registry.ps1')
$paths = Get-Na2Paths
$pythonRunner = Join-Path ([string]$paths.scripts) 'lib\run_python.ps1'
$registryPath = Join-Path $paths.logs 'na228\preflight\registry.json'
$buildRoot = [IO.Path]::GetFullPath([string]$paths.build)
$incomingRoot = Join-Path $buildRoot '.incoming'

if ($Configuration -cnotmatch '^[a-z][a-z0-9_-]*$') {
    throw "Invalid build configuration: $Configuration"
}
$configurationPath = Join-Path $paths.builder "configurations\$Configuration.json"
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

function Invoke-Na2BuilderModule {
    param(
        [Parameter(Mandatory)][string]$Module,
        [Parameter(Mandatory)][string[]]$ArgumentList
    )

    $output = @(
        & $pythonRunner -PackageSet builder -Module $Module `
            -ArgumentList $ArgumentList -NoBytecode 2>&1
    )
    return [pscustomobject]@{
        Output = [string[]]@($output | ForEach-Object { [string]$_ })
        ExitCode = $LASTEXITCODE
    }
}

function Throw-Na2BuilderFailure {
    param(
        [Parameter(Mandatory)][psobject]$Execution,
        [Parameter(Mandatory)][string]$FallbackMessage
    )

    $configurationFailure = Get-Na2ConfigurationFailure -Output $Execution.Output
    if ($null -ne $configurationFailure) {
        $exception = [InvalidOperationException]::new($configurationFailure.Message)
        $exception.Data['Na2ConfigurationError'] = $true
        $exception.Data['Na2TechnicalDetails'] = $configurationFailure.TechnicalDetails
        throw $exception
    }
    $Execution.Output | ForEach-Object { Write-Host $_ }
    throw $FallbackMessage
}

[void](New-Item -ItemType Directory -Path $incomingRoot -Force)
Remove-Na2StaleIncomingImages -IncomingRoot $incomingRoot
$registryArguments = @{
    Registry = $registryPath
    BuildRoot = $buildRoot
    Repository = $paths.repository
    PythonRunner = $pythonRunner
    Na2Iso = $paths.files.na2_iso
    Nun5Iso = $paths.files.nun5_iso
    Configuration = $configurationRelative
}
$verification = Invoke-Na2BuildRegistry -Command lookup @registryArguments
$cacheHit = $verification.status -eq 'hit'

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
            '--output', $incomingIso,
            '--configuration', $configurationRelative,
            '--configuration-log-directory', $configurationLogRelative
        )
        Push-Location $paths.repository
        try {
            $execution = Invoke-Na2BuilderModule `
                -Module 'na228_builder.scripts.build_configuration' `
                -ArgumentList $builderArguments
        }
        finally {
            Pop-Location
        }
        if ($execution.ExitCode -ne 0) {
            Throw-Na2BuilderFailure -Execution $execution `
                -FallbackMessage "NA2 $Configuration build failed (exit $($execution.ExitCode))."
        }
        $execution.Output | ForEach-Object { Write-Host $_ }
        if (-not (Test-Path -LiteralPath $configurationLog -PathType Container)) {
            throw 'Verified build completed without structured provenance.'
        }
        if (-not (Test-Path -LiteralPath $incomingIso -PathType Leaf)) {
            throw "Verified ISO candidate does not exist: $incomingIso"
        }
        $recorded = Invoke-Na2BuildRegistry -Command record @registryArguments `
            -ExpectedFingerprint ([string]$verification.fingerprint) `
            -Image $incomingIso -Provenance $configurationLog
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
    ConfigurationLogDirectory = if ($cacheHit) {
        [string]$verification.provenance
    }
    else {
        [IO.Path]::GetFullPath($configurationLog)
    }
    PreflightCacheHit = $cacheHit
    ConfigurationId = $Configuration
}
