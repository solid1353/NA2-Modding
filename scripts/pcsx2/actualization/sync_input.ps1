# Generate selected PCSX2 input profiles from canonical source inputs.
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Profile,

    [string]$TemplatePath,
    [string[]]$OverridePath,
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

$usingConfiguredPaths = [string]::IsNullOrWhiteSpace($TemplatePath)
if ($usingConfiguredPaths) {
    . (Join-Path $PSScriptRoot '..\..\lib\project_paths.ps1')
    . (Join-Path $PSScriptRoot '..\ini.ps1')
    $projectPaths = Get-Na2ProjectPaths
    $generatedDefaultPath = [IO.Path]::GetFullPath(
        $projectPaths.files.input_profile
    )
    $profileRoot = [IO.Path]::GetDirectoryName($generatedDefaultPath)
    $baseName = [IO.Path]::GetFileNameWithoutExtension(
        $generatedDefaultPath
    )
    $sourcesRoot = Join-Path $profileRoot 'sources'
    $templateFullPath = Join-Path $sourcesRoot "$baseName.ini"
    $selectedName = if ([string]::IsNullOrWhiteSpace($Profile)) {
        $baseName
    }
    else {
        $Profile
    }
    if ($selectedName -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]*$') {
        throw "Invalid input profile name: $selectedName"
    }

    $profileOverridesRoot = Join-Path $sourcesRoot 'profiles'
    $selectedOverrides = @()
    if ($selectedName -cne $baseName) {
        $selectedOverride = Join-Path $profileOverridesRoot "$selectedName.ini"
        if (-not (Test-Path -LiteralPath $selectedOverride -PathType Leaf)) {
            throw "Input-profile override not found: $selectedOverride"
        }
        $selectedOverrides = @($selectedOverride)
    }

    $plans = [ordered]@{}
    $settingsProfiles = [ordered]@{}
    $entries = @($projectPaths.games.Entries.PSObject.Properties.Value)
    foreach ($entry in $entries) {
        $gameOverrideProperty = (
            $entry.Config.PSObject.Properties['input_profile_overrides']
        )
        $hasGameOverride = $null -ne $gameOverrideProperty
        $gameOverride = if ($hasGameOverride) {
            [string]$gameOverrideProperty.Value
        }
        else {
            $null
        }
        $profileName = if ($hasGameOverride) {
            "${selectedName}_$($entry.Name)"
        }
        else {
            $selectedName
        }
        $overrides = @($selectedOverrides)
        if ($hasGameOverride) { $overrides += $gameOverride }
        if (-not $plans.Contains($profileName)) {
            $plans[$profileName] = [pscustomobject]@{
                Name = $profileName
                Overrides = $overrides
                Output = Join-Path $profileRoot "$profileName.ini"
            }
        }

        $settingsPath = if ($entry.Category -eq 'sources') {
            [string]$entry.Config.game_settings
        }
        else {
            [string]$entry.Config.gamesettings_template
        }
        $settingsProfiles[$settingsPath] = $profileName
    }

    $removedProfiles = [Collections.Generic.List[string]]::new()
    Get-ChildItem -LiteralPath $profileRoot -Filter '*.ini' -File |
        ForEach-Object {
            $removedProfiles.Add($_.FullName)
            Remove-Item -LiteralPath $_.FullName -Force
        }

    $generated = @(
        foreach ($plan in $plans.Values) {
            & $PSCommandPath `
                -TemplatePath $templateFullPath `
                -OverridePath $plan.Overrides `
                -OutputPath $plan.Output `
                -PassThru
        }
    )
    $updatedSettings = [Collections.Generic.List[string]]::new()
    foreach ($settingsPath in $settingsProfiles.Keys) {
        if (-not (Test-Path -LiteralPath $settingsPath -PathType Leaf)) {
            throw "Configured GameSettings file not found: $settingsPath"
        }
        $text = [IO.File]::ReadAllText($settingsPath)
        $updated = Set-Na2IniValue `
            -Text $text `
            -Section 'EmuCore' `
            -Key 'InputProfileName' `
            -Value ([string]$settingsProfiles[$settingsPath])
        if ($updated -cne $text) {
            [IO.File]::WriteAllText(
                $settingsPath,
                $updated,
                [Text.UTF8Encoding]::new($false)
            )
            $updatedSettings.Add($settingsPath)
        }
    }

    $configuredResult = [pscustomobject]@{
        Profile = $selectedName
        GeneratedProfiles = $generated
        RemovedProfiles = @($removedProfiles)
        UpdatedGameSettings = @($updatedSettings)
        Changed = (
            $removedProfiles.Count -gt 0 -or
            @($generated | Where-Object Changed).Count -gt 0 -or
            $updatedSettings.Count -gt 0
        )
    }
    if ($PassThru) {
        $configuredResult
    }
    else {
        Write-Host (
            "Input profile '$selectedName': generated $($generated.Count), " +
            "removed $($removedProfiles.Count), " +
            "updated GameSettings $($updatedSettings.Count)."
        )
    }
    return
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    throw 'TemplatePath and OutputPath must be supplied together.'
}

$templateFullPath = [IO.Path]::GetFullPath($TemplatePath)
$overrideFullPaths = @($OverridePath | ForEach-Object {
    [IO.Path]::GetFullPath($_)
})
$outputFullPath = [IO.Path]::GetFullPath($OutputPath)
if ([IO.Path]::Equals($templateFullPath, $outputFullPath)) {
    throw 'The template and generated input profiles must be different files.'
}
if (-not (Test-Path -LiteralPath $templateFullPath -PathType Leaf)) {
    throw "Input-profile template not found: $templateFullPath"
}
foreach ($overrideFullPath in $overrideFullPaths) {
    if (-not (Test-Path -LiteralPath $overrideFullPath -PathType Leaf)) {
        throw "Input-profile override not found: $overrideFullPath"
    }
}

$outputDirectory = [IO.Path]::GetDirectoryName($outputFullPath)
if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
    throw "Generated input-profile directory not found: $outputDirectory"
}

$templateBytes = [IO.File]::ReadAllBytes($templateFullPath)
$generatedText = [Text.Encoding]::Latin1.GetString($templateBytes)
$sectionPattern = (
    '(?ms)^\[(?<name>[^\]\r\n]+)\][^\r\n]*(?:\r\n|\n|\r)' +
    '(?<body>.*?)' +
    '(?=^\[[^\r\n]+\][^\r\n]*(?:\r\n|\n|\r)|\z)'
)
$newline = if ($generatedText.Contains("`r`n")) { "`r`n" } else { "`n" }
foreach ($overrideFullPath in $overrideFullPaths) {
    $overrideText = [Text.Encoding]::Latin1.GetString(
        [IO.File]::ReadAllBytes($overrideFullPath)
    )
    $overrideSections = @([regex]::Matches($overrideText, $sectionPattern))
    if ($overrideSections.Count -eq 0) {
        throw "Input-profile override contains no sections: $overrideFullPath"
    }

    foreach ($overrideSection in $overrideSections) {
        $sectionName = $overrideSection.Groups['name'].Value
        $escapedSection = [regex]::Escape($sectionName)
        $baseSections = @([regex]::Matches(
            $generatedText,
            (
                "(?ms)^\[$escapedSection\][^\r\n]*(?:\r\n|\n|\r)" +
                '(?<body>.*?)' +
                '(?=^\[[^\r\n]+\][^\r\n]*(?:\r\n|\n|\r)|\z)'
            )
        ))
        if ($baseSections.Count -ne 1) {
            throw (
                "Expected exactly one [$sectionName] section; found " +
                "$($baseSections.Count)."
            )
        }

        $bodyGroup = $baseSections[0].Groups['body']
        $body = $bodyGroup.Value
        $overrideLines = @(
            $overrideSection.Groups['body'].Value -split '\r\n|\n|\r' |
                Where-Object { $_ -match '^\s*[^;#\s][^=]*=' }
        )
        if ($overrideLines.Count -eq 0) {
            throw (
                "Override section [$sectionName] has no assignments: " +
                $overrideFullPath
            )
        }

        foreach ($overrideLine in $overrideLines) {
            $parts = $overrideLine -split '=', 2
            $name = $parts[0].Trim()
            $value = $parts[1].Trim()
            $escapedName = [regex]::Escape($name)
            $body = [regex]::Replace(
                $body,
                (
                    "(?m)^[ `t]*$escapedName[ `t]*=[^\r\n]*" +
                    '(?:\r?\n|$)'
                ),
                '',
                [Text.RegularExpressions.RegexOptions]::IgnoreCase
            )
            if ($body.Length -gt 0 -and -not $body.EndsWith("`n")) {
                $body += $newline
            }
            $body += "$name = $value$newline"
        }

        $generatedText = (
            $generatedText.Substring(0, $bodyGroup.Index) +
            $body +
            $generatedText.Substring($bodyGroup.Index + $bodyGroup.Length)
        )
    }
}
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
    Changed   = $changed
    Template  = $templateFullPath
    Overrides = $overrideFullPaths
    Output    = $outputFullPath
}

if ($PassThru) {
    $result
}
else {
    $state = if ($changed) { 'updated' } else { 'already current' }
    Write-Host "$([IO.Path]::GetFileName($outputFullPath)): $state."
}
