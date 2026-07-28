[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$ProductionSource,

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$ProductionEntry,

    [ValidateRange(100, 10000)]
    [int]$DebounceMilliseconds = 400,

    [ValidateRange(50, 5000)]
    [int]$PollMilliseconds = 150,

    [switch]$BuildOnly,
    [string]$CurrentIso,
    [string]$CheatsDirectory,
    [int]$PinePort
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3

$labRoot = $PSScriptRoot
$repository = Split-Path -Parent $labRoot
$testScript = Join-Path $labRoot 'test.ps1'
$packageRoot = Join-Path $repository (
    'na2_patcher\features\localization\runtime_injector'
)
$sourceTable = Join-Path $packageRoot 'c_sources.tsv'
$declarationPaths = @(
    $sourceTable,
    (Join-Path $packageRoot 'c_imports.tsv'),
    (Join-Path $packageRoot 'c_fragments.tsv'),
    (Join-Path $labRoot 'production_entries.tsv')
)

function Get-FileSignature([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return 'MISSING'
    }
    $sharing = [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete
    $stream = [IO.File]::Open(
        $Path,
        [IO.FileMode]::Open,
        [IO.FileAccess]::Read,
        $sharing
    )
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        return [BitConverter]::ToString(
            $sha256.ComputeHash($stream)
        ).Replace('-', '')
    }
    finally {
        $sha256.Dispose()
        $stream.Dispose()
    }
}

function Resolve-SelectedSourcePath {
    if (-not (Test-Path -LiteralPath $sourceTable -PathType Leaf)) {
        throw "Canonical C source table was not found: $sourceTable"
    }

    $rows = @(Import-Csv -LiteralPath $sourceTable -Delimiter "`t")
    $selected = @($rows | Where-Object {
        $_.source_id -ceq $ProductionSource
    })
    if ($selected.Count -ne 1) {
        throw (
            "Production source '$ProductionSource' must match exactly one " +
            'c_sources.tsv row.'
        )
    }
    if ([string]$selected[0].language -cne 'c') {
        throw "Production source '$ProductionSource' is not declared as C."
    }

    $relativePath = [string]$selected[0].path
    if (-not $relativePath) {
        throw "Production source '$ProductionSource' has no declared path."
    }
    $candidate = [IO.Path]::GetFullPath((Join-Path $packageRoot $relativePath))
    $rootPrefix = [IO.Path]::GetFullPath($packageRoot).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith(
        $rootPrefix,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Production source path escapes its package: $relativePath"
    }
    return $candidate
}

function Get-WatchState {
    $paths = [Collections.Generic.List[string]]::new()
    foreach ($path in $declarationPaths) {
        $paths.Add([IO.Path]::GetFullPath($path))
    }

    $resolutionError = ''
    try {
        $paths.Add((Resolve-SelectedSourcePath))
    }
    catch {
        $resolutionError = $_.Exception.Message
    }

    $uniquePaths = @($paths |
        Sort-Object -Unique)
    $parts = [Collections.Generic.List[string]]::new()
    foreach ($path in $uniquePaths) {
        $parts.Add("$path`t$(Get-FileSignature $path)")
    }
    if ($resolutionError) {
        $parts.Add("SOURCE_RESOLUTION_ERROR`t$resolutionError")
    }

    return [pscustomobject]@{
        Paths = $uniquePaths
        Signature = [string]::Join("`n", $parts)
    }
}

function Invoke-ProductionBuild {
    $arguments = [Collections.Generic.List[string]]::new()
    foreach ($argument in @(
        '-NoProfile',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        $testScript,
        '-ProductionSource',
        $ProductionSource,
        '-ProductionEntry',
        $ProductionEntry
    )) {
        $arguments.Add($argument)
    }
    if ($BuildOnly) {
        $arguments.Add('-BuildOnly')
    }
    if ($CurrentIso) {
        $arguments.Add('-CurrentIso')
        $arguments.Add($CurrentIso)
    }
    if ($CheatsDirectory) {
        $arguments.Add('-CheatsDirectory')
        $arguments.Add($CheatsDirectory)
    }
    if ($PinePort) {
        $arguments.Add('-PinePort')
        $arguments.Add([string]$PinePort)
    }

    $timestamp = Get-Date -Format 'HH:mm:ss'
    Write-Host (
        "[injection_lab] $timestamp building $ProductionSource -> " +
        $ProductionEntry
    ) -ForegroundColor Cyan

    $pwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
    $powerShell = if ($pwsh) {
        $pwsh.Source
    }
    else {
        (Get-Process -Id $PID).Path
    }
    & $powerShell @arguments
    if ($LASTEXITCODE -ne 0) {
        Write-Host (
            "[injection_lab] Build/reload failed (exit $LASTEXITCODE); " +
            'watching for the next save.'
        ) -ForegroundColor Red
        return $false
    }
    Write-Host '[injection_lab] Build/reload completed; watching.' `
        -ForegroundColor Green
    return $true
}

$state = Get-WatchState
Write-Host '[injection_lab] Production watcher started.'
Write-Host "[injection_lab] Source: $ProductionSource"
Write-Host "[injection_lab] Entry: $ProductionEntry"
Write-Host '[injection_lab] Inputs:'
foreach ($path in $state.Paths) {
    Write-Host "  $path"
}
Write-Host '[injection_lab] Press Ctrl+C to stop.'

$initialBuildSignature = $state.Signature
[void](Invoke-ProductionBuild)
$state = Get-WatchState
$observedSignature = $state.Signature
$pendingSignature = $null
$lastChange = [DateTime]::MinValue
if ($observedSignature -cne $initialBuildSignature) {
    $pendingSignature = $observedSignature
    $lastChange = [DateTime]::UtcNow
    Write-Host (
        '[injection_lab] Input changed during the initial build; one ' +
        'follow-up build is queued.'
    )
}

while ($true) {
    Start-Sleep -Milliseconds $PollMilliseconds
    $nextState = Get-WatchState
    if ($nextState.Signature -cne $observedSignature) {
        $observedSignature = $nextState.Signature
        $pendingSignature = $observedSignature
        $lastChange = [DateTime]::UtcNow
        Write-Host '[injection_lab] Canonical input changed; debouncing...'
        continue
    }

    if ($null -eq $pendingSignature) {
        continue
    }
    $quietFor = [DateTime]::UtcNow - $lastChange
    if ($quietFor.TotalMilliseconds -lt $DebounceMilliseconds) {
        continue
    }

    $buildSignature = $pendingSignature
    $pendingSignature = $null
    [void](Invoke-ProductionBuild)

    $afterBuild = Get-WatchState
    $observedSignature = $afterBuild.Signature
    if ($observedSignature -cne $buildSignature) {
        $pendingSignature = $observedSignature
        $lastChange = [DateTime]::UtcNow
        Write-Host (
            '[injection_lab] Input changed during the build; one follow-up ' +
            'build is queued.'
        )
    }
}
