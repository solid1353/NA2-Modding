Set-StrictMode -Version Latest

$script:Na2RunBeginMarker = '--- NA2 RUN BEGIN ---'
$script:Na2RunEndMarker = '--- NA2 RUN END ---'

function Test-Na2WindowsAbsolutePath {
    [CmdletBinding()]
    param([AllowEmptyString()][string]$Text)

    if ([string]::IsNullOrEmpty($Text)) {
        return $false
    }

    return $Text -match '(?i)[A-Z]:[\\/]' -or
        $Text -match '(?<![\\])\\\\(?:\?\\)?[^\\/\s]+[\\/]' -or
        $Text -match '(?<![:/])//[^/\s]+/'
}

function ConvertTo-Na2PortableText {
    [CmdletBinding()]
    param(
        [AllowEmptyString()][string]$Text,
        [Parameter(Mandatory = $true)][psobject]$Paths
    )

    if ([string]::IsNullOrEmpty($Text)) {
        return ''
    }

    $sanitized = $Text.TrimStart([char]0xFEFF)
    $sanitized = [regex]::Replace(
        $sanitized,
        "`e\[[0-?]*[ -/]*[@-~]",
        ''
    )

    $configuredRoots = @(
        $Paths.PSObject.Properties |
            Where-Object {
                $_.Name -ne 'ManifestPath' -and
                -not [string]::IsNullOrWhiteSpace([string]$_.Value) -and
                [IO.Path]::IsPathRooted([string]$_.Value)
            } |
            ForEach-Object {
                [pscustomobject]@{
                    Name = $_.Name
                    Path = [IO.Path]::GetFullPath([string]$_.Value).TrimEnd([char[]]@('\', '/'))
                }
            } |
            Sort-Object -Property @{ Expression = { $_.Path.Length }; Descending = $true }
    )

    foreach ($root in $configuredRoots) {
        $variants = @(
            $root.Path
            $root.Path.Replace('\', '/')
        ) | Select-Object -Unique
        foreach ($variant in $variants) {
            $pattern = [regex]::Escape($variant) + '(?=$|[\\/"''\s:;,\)\]\}])'
            $sanitized = [regex]::Replace(
                $sanitized,
                $pattern,
                "@$($root.Name)",
                [Text.RegularExpressions.RegexOptions]::IgnoreCase
            )
        }
    }

    $portableLines = foreach ($line in ($sanitized -split "`r?`n", 0, 'RegexMatch')) {
        if (Test-Na2WindowsAbsolutePath -Text $line) {
            '[na228] Redacted output containing an external absolute path.'
        }
        else {
            ($line -replace '\\', '/')
        }
    }
    $portable = ($portableLines -join "`n").Trim()

    if (Test-Na2WindowsAbsolutePath -Text $portable) {
        throw 'Portable NA2 log text still contains a Windows absolute path.'
    }
    return $portable
}

function Remove-Na2TranscriptBoilerplate {
    [CmdletBinding()]
    param([AllowEmptyString()][string]$Text)

    if ([string]::IsNullOrEmpty($Text)) {
        return ''
    }

    $cleaned = [regex]::Replace(
        $Text,
        '(?ms)^\*{22}\r?\nPowerShell transcript start\r?\n.*?^\*{22}\r?\n',
        ''
    )
    $cleaned = [regex]::Replace(
        $cleaned,
        '(?ms)^\*{22}\r?\nPowerShell transcript end\r?\n.*?^\*{22}\r?\n?',
        ''
    )
    return $cleaned.Trim()
}

function Set-Na2Utf8FileAtomic {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [AllowEmptyString()][string]$Content
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    $directory = [IO.Path]::GetDirectoryName($fullPath)
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $temporary = Join-Path $directory (
        '.' + [IO.Path]::GetFileName($fullPath) + ".$PID.$([guid]::NewGuid().ToString('N')).tmp"
    )
    $utf8 = [Text.UTF8Encoding]::new($false)
    try {
        [IO.File]::WriteAllText($temporary, $Content, $utf8)
        [IO.File]::Move($temporary, $fullPath, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -Force -LiteralPath $temporary
        }
    }
}

function Start-Na2RunLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Mode,
        [Parameter(Mandatory = $true)][psobject]$Paths,
        [string]$LogDirectory,
        [ValidateRange(1, 1000)][int]$MaxRollingSections = 20
    )

    $logDirectory = if ([string]::IsNullOrWhiteSpace($LogDirectory)) {
        Join-Path $Paths.logs 'na228'
    }
    else {
        [IO.Path]::GetFullPath($LogDirectory)
    }
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $temporaryTranscript = Join-Path (
        [IO.Path]::GetTempPath()
    ) "na2-transcript-$PID-$([guid]::NewGuid().ToString('N')).log"

    try {
        Start-Transcript -LiteralPath $temporaryTranscript -UseMinimalHeader -Force | Out-Null
    }
    catch {
        if (Test-Path -LiteralPath $temporaryTranscript) {
            Remove-Item -Force -LiteralPath $temporaryTranscript
        }
        throw
    }

    return [pscustomobject]@{
        Mode = $Mode
        Started = Get-Date
        Paths = $Paths
        TemporaryTranscript = $temporaryTranscript
        LatestLog = Join-Path $logDirectory 'latest.log'
        RollingLog = Join-Path $logDirectory 'rolling.log'
        MaxRollingSections = $MaxRollingSections
    }
}

function Complete-Na2RunLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][psobject]$Context,
        [Parameter(Mandatory = $true)][ValidateSet('succeeded', 'failed')][string]$Outcome,
        [AllowEmptyString()][string]$FailureMessage = ''
    )

    $ended = Get-Date
    $stopError = $null
    try {
        Stop-Transcript | Out-Null
    }
    catch {
        $stopError = $_
    }

    try {
        $rawTranscript = if (Test-Path -LiteralPath $Context.TemporaryTranscript -PathType Leaf) {
            [IO.File]::ReadAllText($Context.TemporaryTranscript)
        }
        else {
            ''
        }
        $body = Remove-Na2TranscriptBoilerplate -Text $rawTranscript
        $body = ConvertTo-Na2PortableText -Text $body -Paths $Context.Paths
        $portableFailure = ConvertTo-Na2PortableText `
            -Text $FailureMessage `
            -Paths $Context.Paths

        $durationMilliseconds = [math]::Max(
            0,
            [math]::Round(($ended - $Context.Started).TotalMilliseconds)
        )
        $sectionLines = [Collections.Generic.List[string]]::new()
        $sectionLines.Add($script:Na2RunBeginMarker)
        $sectionLines.Add("mode: $($Context.Mode)")
        $sectionLines.Add("start: $($Context.Started.ToString('o'))")
        $sectionLines.Add("end: $($ended.ToString('o'))")
        $sectionLines.Add("outcome: $Outcome")
        $sectionLines.Add("duration_ms: $durationMilliseconds")
        if (-not [string]::IsNullOrWhiteSpace($portableFailure)) {
            $sectionLines.Add("error: $portableFailure")
        }
        if (-not [string]::IsNullOrWhiteSpace($body)) {
            $sectionLines.Add('')
            $sectionLines.Add($body)
        }
        $sectionLines.Add($script:Na2RunEndMarker)
        $section = ($sectionLines -join "`n") + "`n"

        if (Test-Na2WindowsAbsolutePath -Text $section) {
            throw 'Refusing to persist an NA2 run log containing a Windows absolute path.'
        }

        $existingRolling = if (Test-Path -LiteralPath $Context.RollingLog -PathType Leaf) {
            [IO.File]::ReadAllText($Context.RollingLog)
        }
        else {
            ''
        }
        $completeSections = @(
            [regex]::Matches(
                $existingRolling,
                '(?ms)^--- NA2 RUN BEGIN ---\r?\n.*?^--- NA2 RUN END ---\r?\n?'
            ) | ForEach-Object { $_.Value.TrimEnd() + "`n" }
        )
        $completeSections += $section
        if ($completeSections.Count -gt $Context.MaxRollingSections) {
            $completeSections = @(
                $completeSections |
                    Select-Object -Last $Context.MaxRollingSections
            )
        }
        $rolling = ($completeSections -join "`n").TrimEnd() + "`n"

        Set-Na2Utf8FileAtomic -Path $Context.LatestLog -Content $section
        Set-Na2Utf8FileAtomic -Path $Context.RollingLog -Content $rolling
    }
    finally {
        if (Test-Path -LiteralPath $Context.TemporaryTranscript) {
            Remove-Item -Force -LiteralPath $Context.TemporaryTranscript
        }
    }

    if ($null -ne $stopError) {
        throw $stopError
    }
}
