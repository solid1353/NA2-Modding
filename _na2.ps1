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
    [string]$Profile,
    [string]$ProfileLogDirectory,
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
$latestLogPath = Join-Path $logDirectory 'latest.log'
$rollingLogPath = Join-Path $logDirectory 'rolling.log'
$maxRollingLogSections = 500
$runStarted = Get-Date
$transcriptStarted = $false

function Format-Na2LogTimestamp {
    param([datetime]$Value)
    $Value.ToString("dddd, d MMMM yyyy 'at' HH:mm:ss.fff zzz", [Globalization.CultureInfo]::InvariantCulture)
}

function Limit-Na2RollingLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [ValidateRange(1, [int]::MaxValue)]
        [int]$MaxSections
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return
    }

    $fullPath = [IO.Path]::GetFullPath($Path)
    $content = [IO.File]::ReadAllText($fullPath)
    $sectionStarts = [regex]::Matches(
        $content,
        '(?m)^={80}\r?\nNA2 run started:'
    )
    if ($sectionStarts.Count -le $MaxSections) {
        return
    }

    $firstRetained = $sectionStarts[$sectionStarts.Count - $MaxSections].Index
    $trimmed = $content.Substring($firstRetained)
    $temporary = "$fullPath.$PID.tmp"
    $backup = "$fullPath.$PID.bak"
    $utf8 = [Text.UTF8Encoding]::new($false)
    try {
        [IO.File]::WriteAllText($temporary, $trimmed, $utf8)
        [IO.File]::Replace($temporary, $fullPath, $backup)
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -Force -LiteralPath $temporary
        }
        if (Test-Path -LiteralPath $backup) {
            Remove-Item -Force -LiteralPath $backup
        }
    }
}

try {
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    Start-Transcript -LiteralPath $latestLogPath -UseMinimalHeader -Force | Out-Null
    $transcriptStarted = $true
    Write-Host "[na2] Latest log: $latestLogPath" -ForegroundColor DarkGray
    Write-Host "[na2] Rolling log: $rollingLogPath" -ForegroundColor DarkGray
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
    if ([string]::IsNullOrWhiteSpace($table)) {
        throw "Builder run summary does not reference a translation TSV: $($summary.FullName)"
    }

    $table = Join-Path $summary.DirectoryName $table
    if (-not (Test-Path -LiteralPath $table -PathType Leaf)) {
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
    -not $Profile -and -not $ProfileLogDirectory -and
    -not $Pcsx2Exe -and -not $Packages -and -not $BuildOnly -and
    -not $RunOnly -and -not $Help -and -not $Na2Iso -and
    -not $OutputDirectory -and -not $TranslationTsv -and -not $BtlApplyTsv -and -not $EtcApplyTsv -and
    -not $NoStrictHash -and -not $IsoPath -and -not $CanonicalPnach -and
    -not $Serial -and -not $RemainingArguments.Count

if ($Help) {
    Write-Na2Stage 'Show command help'
    @(
        'NA2 shortcuts:'
        '  na2       Build the pinned modular profile, actualize PNACH, then run'
        '  na2 ub    Retired; import new mappings into the integrated module instead'
        '  na2 tr    Export a standalone translation TSV for review/compatibility'
        '  na2 act   Actualize the PNACH symlink for the build ISO CRC'
        ''
    ) | Write-Output
}

if ($command -eq 'ub') {
    throw 'na2 ub is retired. Import new mappings into translation_package_builder, validate them, then create a new immutable profile snapshot.'
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

if ($command) {
    throw "Unknown NA2 command: $Mode"
}

$applyArgs = @{
    InputIso  = Join-Path $na2Root 'source\NA2.iso'
    OutputIso = Join-Path $na2Root 'build\Current.iso'
    Pcsx2Exe  = Join-Path $na2Root 'pcsx2\pcsx2-qt.exe'
}
@{
    InputIso         = $InputIso
    OutputIso        = $OutputIso
    PackageDirectory = $PackageDirectory
    Profile          = $Profile
    ProfileLogDirectory = $ProfileLogDirectory
    TranslationTsv   = $TranslationTsv
    Pcsx2Exe         = $Pcsx2Exe
}.GetEnumerator() | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.Value) } |
    ForEach-Object { $applyArgs[$_.Key] = $_.Value }

if ($Packages)  { $applyArgs.Packages = $Packages }
if ($BuildOnly) { $applyArgs.BuildOnly = $true }
if ($RunOnly)   { $applyArgs.RunOnly = $true }
if ($Help)      { $applyArgs.Help = $true }

if ($fullWorkflow) {
    $applyArgs.Profile = 'na2_patcher\profiles\current'
    $applyArgs.ProfileLogDirectory = 'logs\na2_patcher\current_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff')
    $applyArgs.BuildOnly = $true
}
elseif (-not $RunOnly -and -not $applyArgs.ContainsKey('Profile')) {
    if (-not $Packages) {
        $applyArgs.Profile = 'na2_patcher\profiles\current'
        $applyArgs.ProfileLogDirectory = 'logs\na2_patcher\current_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff')
    }
    else {
        if (-not $applyArgs.ContainsKey('PackageDirectory')) {
            $applyArgs.PackageDirectory = Join-Path $na2Root 'packages'
        }
        $translationSelected = @($applyArgs.Packages | Where-Object { $_ -ieq 'Translation' }).Count -gt 0
        if ($translationSelected -and -not $applyArgs.ContainsKey('TranslationTsv')) {
            $latestBuilderTsv = Get-LatestBuilderTranslationTsv
            if ($latestBuilderTsv) {
                $applyArgs.TranslationTsv = $latestBuilderTsv
            }
        }
    }
}

$apply = Join-Path $scriptsRoot 'apply_latest_na2.ps1'
if ($fullWorkflow) {
    Write-Na2Stage '1/2 Build and actualize pinned modular profile'
}
elseif ($RunOnly) {
    Write-Na2Stage 'Run existing output ISO'
}
elseif ($applyArgs.ContainsKey('Profile')) {
    Write-Na2Stage ("Build profile: " + $applyArgs.Profile)
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
    $runArgs = @{
        OutputIso = $applyArgs.OutputIso
        Pcsx2Exe  = $applyArgs.Pcsx2Exe
        RunOnly   = $true
    }
    Write-Na2Stage '2/2 Launch rebuilt ISO in PCSX2'
    & $apply @runArgs
}
}
finally {
    if ($transcriptStarted) {
        Stop-Transcript | Out-Null
        try {
            $runEnded = Get-Date
            $separator = '=' * 80
            $header = @(
                $separator
                "NA2 run started: $(Format-Na2LogTimestamp $runStarted)"
                "NA2 run ended:   $(Format-Na2LogTimestamp $runEnded)"
                $separator
            ) -join [Environment]::NewLine
            $transcript = Get-Content -LiteralPath $latestLogPath -Raw
            $section = $header + [Environment]::NewLine + $transcript.TrimEnd() +
                [Environment]::NewLine + [Environment]::NewLine
            $utf8 = [Text.UTF8Encoding]::new($false)
            [IO.File]::WriteAllText($latestLogPath, $section, $utf8)
            [IO.File]::AppendAllText($rollingLogPath, $section, $utf8)
            Limit-Na2RollingLog -Path $rollingLogPath -MaxSections $maxRollingLogSections
        }
        catch {
            Write-Warning "Could not finalize NA2 logs: $_"
        }
    }
}
