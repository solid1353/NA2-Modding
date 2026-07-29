[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()]
    [string]$SourcePath = (Join-Path $PSScriptRoot 'src'),

    [string]$ProductionEntry,
    [string]$OverlayPlan,

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
    'na228_builder\features\localization\runtime_injector'
)
$sourceTable = Join-Path $packageRoot 'c_sources.tsv'
$resolvedOverlayPlan = $null
if ($OverlayPlan) {
    $resolvedOverlayPlan = if ([IO.Path]::IsPathRooted($OverlayPlan)) {
        [IO.Path]::GetFullPath($OverlayPlan)
    }
    else {
        [IO.Path]::GetFullPath((Join-Path $repository $OverlayPlan))
    }
    $workRoot = [IO.Path]::GetFullPath(
        (Join-Path $repository 'work')
    ).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $workPrefix = $workRoot + [IO.Path]::DirectorySeparatorChar
    if (-not $resolvedOverlayPlan.StartsWith(
        $workPrefix,
        [StringComparison]::OrdinalIgnoreCase
    ) -or -not (Test-Path -LiteralPath $resolvedOverlayPlan -PathType Leaf)) {
        throw 'OverlayPlan must be a task-owned file under work/<task>/.'
    }
}
$resolvedSourcePath = if ([IO.Path]::IsPathRooted($SourcePath)) {
    [IO.Path]::GetFullPath($SourcePath)
}
else {
    [IO.Path]::GetFullPath((Join-Path $repository $SourcePath))
}
$sourceItem = Get-Item -LiteralPath $resolvedSourcePath -Force `
    -ErrorAction SilentlyContinue
if (-not $sourceItem -or (
    -not $sourceItem.PSIsContainer -and
    -not (Test-Path -LiteralPath $resolvedSourcePath -PathType Leaf)
)) {
    throw "SourcePath must be an existing file or directory: $resolvedSourcePath"
}
$genericSourceFile = [IO.Path]::GetFullPath(
    (Join-Path $labRoot 'src\test.c')
)
$genericSourceDirectory = [IO.Path]::GetFullPath(
    (Join-Path $labRoot 'src')
)
$genericMode = (
    $resolvedSourcePath.Equals(
        $genericSourceFile,
        [StringComparison]::OrdinalIgnoreCase
    ) -or
    (
        $sourceItem.PSIsContainer -and
        $resolvedSourcePath.Equals(
            $genericSourceDirectory,
            [StringComparison]::OrdinalIgnoreCase
        )
    )
)
$ProductionSource = ''
if ($genericMode) {
    if ($ProductionEntry -or $resolvedOverlayPlan) {
        throw (
            'ProductionEntry and OverlayPlan cannot be used with the ' +
            'generic lab source.'
        )
    }
}
else {
    if (-not (Test-Path -LiteralPath $sourceTable -PathType Leaf)) {
        throw "Canonical C source table was not found: $sourceTable"
    }
    $ProductionSource = ''
    if ($resolvedOverlayPlan) {
        $plan = Get-Content -Raw -LiteralPath $resolvedOverlayPlan |
            ConvertFrom-Json
        $planSource = [string]$plan.source_id
        if ([int]$plan.schema_version -eq 2) {
            $planEntries = @(
                $plan.entry_symbols | ForEach-Object { [string]$_.symbol }
            )
        }
        else {
            $planEntries = @([string]$plan.entry_symbol)
        }
        $planEntry = [string]$planEntries[0]
        if (-not $planSource -or -not $planEntry) {
            throw 'OverlayPlan must declare source_id and at least one entry.'
        }
        if ($ProductionEntry -and $ProductionEntry -cne $planEntry) {
            throw 'ProductionEntry does not match OverlayPlan entry_symbol.'
        }
        $ProductionSource = $planSource
        $ProductionEntry = $planEntry
    }
    else {
        if (-not $ProductionEntry) {
            throw 'ProductionEntry is required for a canonical production source.'
        }
        $entryTable = Join-Path $labRoot 'production_entries.tsv'
        $entryRows = @(Import-Csv -LiteralPath $entryTable -Delimiter "`t" |
            Where-Object {
                $_.entry_symbol -ceq $ProductionEntry
            })
        if ($entryRows.Count -ne 1) {
            throw (
                "ProductionEntry '$ProductionEntry' must match exactly one " +
                'production_entries.tsv row.'
            )
        }
        $ProductionSource = [string]$entryRows[0].source_id
    }
    $sourceRows = @(Import-Csv -LiteralPath $sourceTable -Delimiter "`t")
    $selectedSources = @($sourceRows | Where-Object {
        $_.source_id -ceq $ProductionSource -and
        [string]$_.language -ceq 'c'
    })
    if ($selectedSources.Count -ne 1) {
        throw (
            "Production entry source '$ProductionSource' must match exactly " +
            'one canonical C source.'
        )
    }
    $canonicalSourcePath = [IO.Path]::GetFullPath(
        (Join-Path $packageRoot ([string]$selectedSources[0].path))
    )
    $sourceContainsCanonical = if ($sourceItem.PSIsContainer) {
        $directoryPrefix = $resolvedSourcePath.TrimEnd(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        ) + [IO.Path]::DirectorySeparatorChar
        $canonicalSourcePath.StartsWith(
            $directoryPrefix,
            [StringComparison]::OrdinalIgnoreCase
        )
    }
    else {
        $resolvedSourcePath.Equals(
            $canonicalSourcePath,
            [StringComparison]::OrdinalIgnoreCase
        )
    }
    if (-not $sourceContainsCanonical) {
        throw (
            "SourcePath does not contain the canonical source selected by " +
            "$ProductionEntry`: $canonicalSourcePath"
        )
    }
}
$productionMode = -not $genericMode
$declarationPaths = if ($productionMode) {
    $paths = @(
        $resolvedSourcePath,
        $sourceTable,
        (Join-Path $packageRoot 'c_imports.tsv'),
        (Join-Path $packageRoot 'c_fragments.tsv'),
        (Join-Path $packageRoot 'fragments.tsv'),
        (Join-Path $packageRoot 'relocations.tsv'),
        (Join-Path $labRoot 'production_entries.tsv')
    )
    if ($resolvedOverlayPlan) {
        $paths += $resolvedOverlayPlan
    }
    $paths
}
else {
    @(
        $resolvedSourcePath,
        (Join-Path $labRoot 'src\Main.h'),
        (Join-Path $labRoot 'linker.asm'),
        (Join-Path $labRoot 'gen_pnach.py')
    )
}

function Get-FileSignature([string]$Path) {
    if (Test-Path -LiteralPath $Path -PathType Container) {
        $root = [IO.Path]::GetFullPath($Path).TrimEnd(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        )
        $parts = [Collections.Generic.List[string]]::new()
        foreach ($file in @(
            Get-ChildItem -LiteralPath $root -Recurse -File -Force |
                Sort-Object FullName
        )) {
            $relativePath = $file.FullName.Substring($root.Length + 1)
            $parts.Add(
                "$relativePath`t$(Get-FileSignature $file.FullName)"
            )
        }
        return "DIRECTORY`n$([string]::Join("`n", $parts))"
    }
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

function Get-WatchState {
    $paths = [Collections.Generic.List[string]]::new()
    foreach ($path in $declarationPaths) {
        $paths.Add([IO.Path]::GetFullPath($path))
    }

    $uniquePaths = @($paths |
        Sort-Object -Unique)
    $parts = [Collections.Generic.List[string]]::new()
    foreach ($path in $uniquePaths) {
        $parts.Add("$path`t$(Get-FileSignature $path)")
    }
    return [pscustomobject]@{
        Paths = $uniquePaths
        Signature = [string]::Join("`n", $parts)
    }
}

function Invoke-WatchedBuild {
    $arguments = [Collections.Generic.List[string]]::new()
    foreach ($argument in @(
        '-NoProfile',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        $testScript
    )) {
        $arguments.Add($argument)
    }
    if ($productionMode) {
        foreach ($argument in @(
            '-ProductionSource',
            $ProductionSource,
            '-ProductionEntry',
            $ProductionEntry
        )) {
            $arguments.Add($argument)
        }
        if ($resolvedOverlayPlan) {
            $arguments.Add('-OverlayPlan')
            $arguments.Add($resolvedOverlayPlan)
        }
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
    $selection = if ($productionMode) {
        "$ProductionSource -> $ProductionEntry"
    }
    else {
        'generic lab source'
    }
    Write-Host "[injection_lab] $timestamp building $selection" `
        -ForegroundColor Cyan

    $pwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
    $powerShell = if ($pwsh) {
        $pwsh.Source
    }
    else {
        (Get-Process -Id $PID).Path
    }
    & $powerShell @arguments 2>&1 | ForEach-Object {
        Write-Host $_
    }
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Write-Host (
            "[injection_lab] Build/reload failed (exit $exitCode); " +
            'watching for the next save.'
        ) -ForegroundColor Red
        return $false
    }
    Write-Host '[injection_lab] Build/reload completed; watching.' `
        -ForegroundColor Green
    return $true
}

$state = Get-WatchState
if ($productionMode) {
    Write-Host '[injection_lab] Production watcher started.'
    Write-Host "[injection_lab] Source ID: $ProductionSource"
    Write-Host "[injection_lab] Entry: $ProductionEntry"
    if ($resolvedOverlayPlan) {
        Write-Host "[injection_lab] Overlay plan: $resolvedOverlayPlan"
    }
}
else {
    Write-Host '[injection_lab] Generic source watcher started.'
}
Write-Host "[injection_lab] Source path: $resolvedSourcePath"
Write-Host '[injection_lab] Inputs:'
foreach ($path in $state.Paths) {
    Write-Host "  $path"
}
Write-Host '[injection_lab] Press Ctrl+C to stop.'

$initialBuildSignature = $state.Signature
[void](Invoke-WatchedBuild)
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
    [void](Invoke-WatchedBuild)

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
