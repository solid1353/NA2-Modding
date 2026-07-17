[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('act')]
    [string]$Mode,

    [Alias('c')]
    [switch]$Current,
    [Alias('p')]
    [switch]$Previous,
    [Alias('h')]
    [switch]$Help
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'scripts\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$logDirectory = Join-Path $projectPaths.logs 'na2'
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
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][ValidateRange(1, [int]::MaxValue)][int]$MaxSections
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return
    }

    $fullPath = [IO.Path]::GetFullPath($Path)
    $content = [IO.File]::ReadAllText($fullPath)
    $sectionStarts = [regex]::Matches($content, '(?m)^={80}\r?\nNA2 run started:')
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

function Write-Na2Stage {
    param([string]$Message)
    Write-Host "[na2] $Message" -ForegroundColor Cyan
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
    $command = if ($Mode) { $Mode.ToLowerInvariant() } else { '' }
    $runSelected = $Current -or $Previous

    if ($Current -and $Previous) {
        throw '-Current / -c and -Previous / -p cannot be used together.'
    }
    if ($command -and $runSelected) {
        throw '-Current / -c and -Previous / -p cannot be combined with a command mode.'
    }
    if ($Help) {
        Write-Na2Stage 'Show command help'
        @(
            'NA2 commands:'
            '  na2       Build the pinned current profile, conditionally rotate, then run Current.iso'
            '  na2 -c    Run build/Current.iso without rebuilding'
            '  na2 -p    Run build/Previous.iso without rebuilding'
            '  na2 act   Actualize the PNACH symlink for build/Current.iso without launching'
            ''
        ) | Write-Output
        return
    }

    if ($command -eq 'act') {
        Write-Na2Stage 'Actualize PNACH symlink for Current.iso CRC'
        & (Join-Path $projectPaths.scripts 'na2\actualize_pnach.ps1')
        return
    }

    if ($runSelected) {
        $isoName = if ($Previous) { 'Previous.iso' } else { 'Current.iso' }
        Write-Na2Stage "Run $isoName without rebuilding"
        & (Join-Path $projectPaths.scripts 'na2\launch.ps1') -IsoPath (Join-Path $projectPaths.build $isoName)
        return
    }

    Write-Na2Stage '1/2 Build pinned current profile'
    $buildResult = & (Join-Path $projectPaths.scripts 'na2\build.ps1')
    if (-not $buildResult -or $buildResult.Status -notin @('unchanged', 'updated')) {
        throw 'Profile build did not return a valid promotion result.'
    }

    Write-Na2Stage '2/2 Actualize PNACH and launch Current.iso'
    & (Join-Path $projectPaths.scripts 'na2\launch.ps1') -IsoPath (Join-Path $projectPaths.build 'Current.iso')
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
