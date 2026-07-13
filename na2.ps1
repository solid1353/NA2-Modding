[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Mode,

    [Alias('i')]
    [string]$InputIso,
    [Alias('o')]
    [string]$OutputIso,
    [Alias('d')]
    [string]$PackageDirectory,
    [string]$TranslationTsv,
    [Alias('e')]
    [string]$Pcsx2Exe,
    [Alias('p')]
    [string[]]$Packages,
    [Alias('b')]
    [switch]$BuildOnly,
    [Alias('r')]
    [switch]$RunOnly,
    [Alias('h')]
    [switch]$Help,

    [string]$Na2Iso,
    [string]$OutputDirectory,
    [string]$BtlApplyTsv,
    [string]$EtcApplyTsv,
    [switch]$NoStrictHash,

    [string]$IsoPath,
    [string]$CanonicalPnach,
    [string]$Serial,

    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]]$RemainingArguments
)

$na2Root = $PSScriptRoot
$logDirectory = Join-Path $na2Root 'logs\na2'
$logTimestamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$logPath = Join-Path $logDirectory "na2_${logTimestamp}_pid$PID.log"
$latestLogPath = Join-Path $logDirectory 'latest.log'
$transcriptStarted = $false

try {
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    Start-Transcript -LiteralPath $logPath -UseMinimalHeader | Out-Null
    $transcriptStarted = $true
    Write-Host "[na2] Log: $logPath" -ForegroundColor DarkGray
}
catch {
    Write-Warning "Could not start NA2 log: $_"
}

try {
$scriptsRoot = Join-Path $na2Root 'scripts'
$builderRoot = Join-Path $na2Root 'translation_package_builder'
$command = if ($Mode) { $Mode.ToLowerInvariant() } else { '' }

function Write-Na2Stage {
    param([string]$Message)
    Write-Host "[na2] $Message" -ForegroundColor Cyan
}

function Get-LatestBuilderTranslationTsv {
    $runsRoot = Join-Path $builderRoot 'work\runs'
    if (-not (Test-Path -LiteralPath $runsRoot -PathType Container)) {
        return $null
    }

    $summary = Get-ChildItem -LiteralPath $runsRoot -Recurse -File -Filter 'build_summary.json' |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $summary) {
        return $null
    }

    $run = Get-Content -LiteralPath $summary.FullName -Raw | ConvertFrom-Json
    $table = [string]$run.translation_tsv
    if ([string]::IsNullOrWhiteSpace($table) -or -not (Test-Path -LiteralPath $table -PathType Leaf)) {
        throw "Builder run summary does not reference an existing translation TSV: $($summary.FullName)"
    }
    return (Resolve-Path -LiteralPath $table).Path
}

function Invoke-TranslationBuilder {
    if ($BtlApplyTsv -or $EtcApplyTsv) {
        throw 'BtlApplyTsv and EtcApplyTsv are obsolete. The translation builder now produces one unified TSV.'
    }
    if ($OutputDirectory) {
        throw 'OutputDirectory is obsolete. Translation builder runs are stored under translation_package_builder\work\runs.'
    }

    $builderArgs = @{}
    @{
        Na2Iso = $Na2Iso
    }.GetEnumerator() | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.Value) } |
        ForEach-Object { $builderArgs[$_.Key] = $_.Value }
    if ($NoStrictHash) { $builderArgs.NoStrictHash = $true }

    $builder = Join-Path $builderRoot 'build_na2_translation_package.ps1'
    if ($RemainingArguments.Count) {
        & $builder @builderArgs @RemainingArguments
    } else {
        & $builder @builderArgs
    }
}

$fullWorkflow = -not $command -and
    -not $InputIso -and -not $OutputIso -and -not $PackageDirectory -and
    -not $Pcsx2Exe -and -not $Packages -and -not $BuildOnly -and
    -not $RunOnly -and -not $Help -and -not $Na2Iso -and
    -not $OutputDirectory -and -not $TranslationTsv -and -not $BtlApplyTsv -and -not $EtcApplyTsv -and
    -not $NoStrictHash -and -not $IsoPath -and -not $CanonicalPnach -and
    -not $Serial -and -not $RemainingArguments.Count

if ($fullWorkflow) {
    Write-Na2Stage '1/5 Update translation builder'
    & (Join-Path $scriptsRoot 'update_translation_package_builder.ps1')
    Write-Na2Stage '2/5 Generate translation TSV'
    Invoke-TranslationBuilder
}

if ($Help) {
    Write-Na2Stage 'Show command help'
    @(
        'NA2 shortcuts:'
        '  na2       Update builder, translate, build, actualize PNACH, then run'
        '  na2 ub    Update translation builder'
        '  na2 tr    Generate translation TSV'
        '  na2 act   Actualize the PNACH symlink for the build ISO CRC'
        '  na2 f     Apply Font package'
        '  na2 t     Apply Translation TSV'
        '  na2 ft    Apply Font package, then Translation TSV'
        ''
    ) | Write-Output
}

if ($command -eq 'ub') {
    Write-Na2Stage 'Update translation builder'
    & (Join-Path $scriptsRoot 'update_translation_package_builder.ps1')
    return
}

if ($command -eq 'tr') {
    Write-Na2Stage 'Generate translation TSV'
    Invoke-TranslationBuilder
    return
}

if ($command -eq 'act') {
    Write-Na2Stage 'Actualize PNACH symlink for build ISO CRC'
    $actualizeArgs = @{}
    @{
        IsoPath        = $IsoPath
        CanonicalPnach = $CanonicalPnach
        Serial         = $Serial
    }.GetEnumerator() | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.Value) } |
        ForEach-Object { $actualizeArgs[$_.Key] = $_.Value }

    $actualize = Join-Path $scriptsRoot 'actualize_cheats_for_build_iso.ps1'
    if ($RemainingArguments.Count) {
        & $actualize @actualizeArgs @RemainingArguments
    } else {
        & $actualize @actualizeArgs
    }
    return
}

if ($command -and $command -notmatch '^(f|t|ft|tf)$') {
    throw "Unknown NA2 command: $Mode"
}

$applyArgs = @{
    InputIso         = Join-Path $na2Root 'source\NA2.iso'
    OutputIso        = Join-Path $na2Root 'build\Current.iso'
    PackageDirectory = Join-Path $HOME 'Downloads'
    Pcsx2Exe         = Join-Path $na2Root 'pcsx2\pcsx2-qt.exe'
}
@{
    InputIso         = $InputIso
    OutputIso        = $OutputIso
    PackageDirectory = $PackageDirectory
    TranslationTsv   = $TranslationTsv
    Pcsx2Exe         = $Pcsx2Exe
}.GetEnumerator() | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.Value) } |
    ForEach-Object { $applyArgs[$_.Key] = $_.Value }

if ($Packages)  { $applyArgs.Packages = $Packages }
if ($BuildOnly) { $applyArgs.BuildOnly = $true }
if ($RunOnly)   { $applyArgs.RunOnly = $true }
if ($Help)      { $applyArgs.Help = $true }

if ($command) {
    $packageNames = @{ f = 'Font'; t = 'Translation' }
    $applyArgs.Packages = $command.ToCharArray() | ForEach-Object {
        $packageNames[[string]$_]
    }
}
elseif (-not $Packages -and -not $RunOnly) {
    $applyArgs.Packages = @('Font', 'Translation')
}

$translationSelected = @($applyArgs.Packages | Where-Object { $_ -ieq 'Translation' }).Count -gt 0
if ($translationSelected -and -not $applyArgs.TranslationTsv) {
    $latestBuilderTsv = Get-LatestBuilderTranslationTsv
    if ($latestBuilderTsv) {
        $applyArgs.TranslationTsv = $latestBuilderTsv
    }
}

if ($fullWorkflow) {
    $applyArgs.BuildOnly = $true
}

$apply = Join-Path $scriptsRoot 'apply_latest_na2.ps1'
if ($fullWorkflow) {
    Write-Na2Stage '3/5 Build ISO with Font package and Translation TSV'
}
elseif ($RunOnly) {
    Write-Na2Stage 'Run existing output ISO'
}
elseif ($BuildOnly) {
    Write-Na2Stage ("Build ISO with: " + ($applyArgs.Packages -join ', '))
}
elseif (-not $Help) {
    Write-Na2Stage ("Build and run ISO with: " + ($applyArgs.Packages -join ', '))
}

if ($RemainingArguments.Count) {
    & $apply @applyArgs @RemainingArguments
} else {
    & $apply @applyArgs
}

if ($fullWorkflow) {
    Write-Na2Stage '4/5 Actualize PNACH symlink for rebuilt ISO CRC'
    & (Join-Path $scriptsRoot 'actualize_cheats_for_build_iso.ps1') -IsoPath $applyArgs.OutputIso

    $runArgs = @{
        OutputIso = $applyArgs.OutputIso
        Pcsx2Exe  = $applyArgs.Pcsx2Exe
        RunOnly   = $true
    }
    Write-Na2Stage '5/5 Launch rebuilt ISO in PCSX2'
    & $apply @runArgs
}
}
finally {
    if ($transcriptStarted) {
        Stop-Transcript | Out-Null
        try {
            Copy-Item -LiteralPath $logPath -Destination $latestLogPath -Force
        }
        catch {
            Write-Warning "Could not refresh NA2 latest log: $_"
        }
    }
}
