[CmdletBinding()]
param(
    [string]$BasePath,
    [string]$OutputPath,
    [switch]$PassThru
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-ByteArrayEqual {
    param(
        [Parameter(Mandatory)]
        [byte[]]$Left,

        [Parameter(Mandatory)]
        [byte[]]$Right
    )

    if ($Left.Length -ne $Right.Length) {
        return $false
    }

    for ($index = 0; $index -lt $Left.Length; $index++) {
        if ($Left[$index] -ne $Right[$index]) {
            return $false
        }
    }

    return $true
}

if ([string]::IsNullOrWhiteSpace($BasePath) -xor
    [string]::IsNullOrWhiteSpace($OutputPath)) {
    throw 'BasePath and OutputPath must be supplied together.'
}

$usingConfiguredPaths = [string]::IsNullOrWhiteSpace($BasePath)
if ($usingConfiguredPaths) {
    . (Join-Path $PSScriptRoot '..\..\lib\project_paths.ps1')
    $projectPaths = Get-Na2ProjectPaths
    $BasePath = $projectPaths.files.comparison_input_profile
    $OutputPath = $projectPaths.files.comparison_na2_input_profile
}

$baseFullPath = [IO.Path]::GetFullPath($BasePath)
$outputFullPath = [IO.Path]::GetFullPath($OutputPath)
if ([IO.Path]::Equals($baseFullPath, $outputFullPath)) {
    throw 'The base and generated input profiles must be different files.'
}
if (-not (Test-Path -LiteralPath $baseFullPath -PathType Leaf)) {
    throw "Base input profile not found: $baseFullPath"
}

$outputDirectory = [IO.Path]::GetDirectoryName($outputFullPath)
if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
    throw "Generated input-profile directory not found: $outputDirectory"
}

$baseBytes = [IO.File]::ReadAllBytes($baseFullPath)
$text = [Text.Encoding]::Latin1.GetString($baseBytes)
$sectionPattern = (
    '(?ms)^\[Pad1\][^\r\n]*(?:\r\n|\n|\r)' +
    '(?<body>.*?)' +
    '(?=^\[[^\r\n]+\][^\r\n]*(?:\r\n|\n|\r)|\z)'
)
$sectionRegex = [regex]::new($sectionPattern)
$sections = @($sectionRegex.Matches($text))
if ($sections.Count -ne 1) {
    throw "Expected exactly one [Pad1] section; found $($sections.Count)."
}

$section = $sections[0]
$bodyGroup = $section.Groups['body']
$body = $bodyGroup.Value
$bindings = [ordered]@{
    Triangle = 'SDL-0/FaceEast'
    Circle   = 'SDL-0/FaceSouth'
    Cross    = 'SDL-0/FaceNorth'
    Square   = 'SDL-0/FaceWest'
}

foreach ($binding in $bindings.GetEnumerator()) {
    $escapedName = [regex]::Escape([string]$binding.Key)
    $bindingPattern = (
        "(?m)^(?<prefix>[ `t]*$escapedName[ `t]*=[ `t]*)" +
        '(?<value>SDL-[^\r\n]*?)(?<trailing>[ \t]*)(?=\r?$)'
    )
    $bindingRegex = [regex]::new(
        $bindingPattern,
        [Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    $matches = @($bindingRegex.Matches($body))
    if ($matches.Count -ne 1) {
        throw (
            "Expected exactly one SDL '$($binding.Key)' binding in [Pad1]; " +
            "found $($matches.Count)."
        )
    }

    $replacementValue = [string]$binding.Value
    $body = $bindingRegex.Replace(
        $body,
        [Text.RegularExpressions.MatchEvaluator] {
            param($match)
            return (
                $match.Groups['prefix'].Value +
                $replacementValue +
                $match.Groups['trailing'].Value
            )
        }
    )
}

$generatedText = (
    $text.Substring(0, $bodyGroup.Index) +
    $body +
    $text.Substring($bodyGroup.Index + $bodyGroup.Length)
)
$generatedBytes = [Text.Encoding]::Latin1.GetBytes($generatedText)

$changed = $true
if (Test-Path -LiteralPath $outputFullPath -PathType Leaf) {
    $changed = -not (Test-ByteArrayEqual `
        -Left ([IO.File]::ReadAllBytes($outputFullPath)) `
        -Right $generatedBytes)
}

if ($changed) {
    if (Test-Path -LiteralPath $outputFullPath -PathType Leaf) {
        $stream = [IO.File]::Open(
            $outputFullPath,
            [IO.FileMode]::Create,
            [IO.FileAccess]::Write,
            [IO.FileShare]::Read
        )
        try {
            $stream.Write($generatedBytes, 0, $generatedBytes.Length)
            $stream.Flush($true)
        }
        finally {
            $stream.Dispose()
        }
    }
    else {
        [IO.File]::WriteAllBytes($outputFullPath, $generatedBytes)
    }
}

$result = [pscustomobject]@{
    Changed = $changed
    Base    = $baseFullPath
    Output  = $outputFullPath
}

if ($PassThru) {
    $result
}
else {
    $state = if ($changed) { 'updated' } else { 'already current' }
    Write-Host "Comparison input profiles: $state."
}
