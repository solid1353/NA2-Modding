function ConvertTo-Na2TestCardComponent {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [ValidateRange(16, 96)][int]$MaxLength = 48
    )

    $invalid = [Collections.Generic.HashSet[char]]::new([IO.Path]::GetInvalidFileNameChars())
    $characters = foreach ($character in $Value.ToCharArray()) {
        if ($invalid.Contains($character)) { '_' } else { $character }
    }
    $clean = ((-join $characters) -replace '\s+', ' ').Trim().TrimEnd('.')
    if ([string]::IsNullOrWhiteSpace($clean)) {
        throw 'A test-card identity component became empty after filename sanitization.'
    }
    if ($clean.Length -le $MaxLength) {
        return $clean
    }

    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $hash = [Convert]::ToHexString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($clean))).Substring(0, 8)
    }
    finally {
        $sha.Dispose()
    }
    return $clean.Substring(0, $MaxLength - 9).TrimEnd() + '_' + $hash
}

function Get-Na2IniValue {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text,
        [Parameter(Mandatory = $true)][string]$Section,
        [Parameter(Mandatory = $true)][string]$Key
    )

    $sectionPattern = '(?ms)^\s*\[' + [regex]::Escape($Section) + '\]\s*\r?\n(?<body>.*?)(?=^\s*\[|\z)'
    $sectionMatch = [regex]::Match($Text, $sectionPattern)
    if (-not $sectionMatch.Success) { return $null }

    $keyPattern = '(?m)^[ \t]*' + [regex]::Escape($Key) + '[ \t]*=[ \t]*(?<value>[^\r\n]*)'
    $matches = [regex]::Matches($sectionMatch.Groups['body'].Value, $keyPattern)
    if ($matches.Count -gt 1) {
        throw "INI section [$Section] contains duplicate $Key settings."
    }
    if ($matches.Count -eq 0) { return $null }
    return $matches[0].Groups['value'].Value.Trim()
}

function Set-Na2IniValue {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text,
        [Parameter(Mandatory = $true)][string]$Section,
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Value
    )

    $newline = if ($Text.Contains("`r`n")) { "`r`n" } else { "`n" }
    $sectionPattern = '(?ms)^\s*\[' + [regex]::Escape($Section) + '\]\s*\r?\n(?<body>.*?)(?=^\s*\[|\z)'
    $sectionMatch = [regex]::Match($Text, $sectionPattern)
    if (-not $sectionMatch.Success) {
        $prefix = $Text
        if ($prefix.Length -gt 0 -and -not $prefix.EndsWith("`n")) { $prefix += $newline }
        if ($prefix.Length -gt 0 -and -not $prefix.EndsWith($newline + $newline)) { $prefix += $newline }
        return $prefix + "[$Section]$newline$Key = $Value$newline"
    }

    $bodyGroup = $sectionMatch.Groups['body']
    $body = $bodyGroup.Value
    $keyPattern = '(?m)^(?<prefix>[ \t]*' + [regex]::Escape($Key) + '[ \t]*=[ \t]*)[^\r\n]*(?<cr>\r?)$'
    $keyMatches = [regex]::Matches($body, $keyPattern)
    if ($keyMatches.Count -gt 1) {
        throw "INI section [$Section] contains duplicate $Key settings."
    }
    if ($keyMatches.Count -eq 1) {
        $keyMatch = $keyMatches[0]
        $replacement = $keyMatch.Groups['prefix'].Value + $Value + $keyMatch.Groups['cr'].Value
        $newBody = $body.Substring(0, $keyMatch.Index) + $replacement + $body.Substring($keyMatch.Index + $keyMatch.Length)
    }
    else {
        $newBody = $body
        if ($newBody.Length -gt 0 -and -not $newBody.EndsWith("`n")) { $newBody += $newline }
        $newBody += "$Key = $Value$newline"
    }
    return $Text.Substring(0, $bodyGroup.Index) + $newBody + $Text.Substring($bodyGroup.Index + $bodyGroup.Length)
}

function Enter-Na2TestMemoryCard {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$GlobalIniPath,
        [Parameter(Mandatory = $true)][string]$GameSettingsDirectory,
        [Parameter(Mandatory = $true)][string]$MemoryCardsDirectory,
        [Parameter(Mandatory = $true)][string]$Serial,
        [Parameter(Mandatory = $true)][string]$CRC,
        [Parameter(Mandatory = $true)][string]$AgentName,
        [Parameter(Mandatory = $true)][string]$TaskIdentity
    )

    foreach ($directory in $GameSettingsDirectory, $MemoryCardsDirectory) {
        if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
            throw "Required PCSX2 directory does not exist: $directory"
        }
    }
    if (-not (Test-Path -LiteralPath $GlobalIniPath -PathType Leaf)) {
        throw "PCSX2 configuration does not exist: $GlobalIniPath"
    }

    $gameSettingsPath = Join-Path $GameSettingsDirectory "${Serial}_${CRC}.ini"
    $gameSettingsExisted = Test-Path -LiteralPath $gameSettingsPath -PathType Leaf
    $originalGameSettingsBytes = if ($gameSettingsExisted) {
        [IO.File]::ReadAllBytes($gameSettingsPath)
    }
    else {
        $null
    }
    $gameSettingsText = if ($gameSettingsExisted) {
        [IO.File]::ReadAllText($gameSettingsPath)
    }
    else {
        ''
    }
    $globalIniText = [IO.File]::ReadAllText($GlobalIniPath)

    $baseCardName = Get-Na2IniValue -Text $gameSettingsText -Section 'MemoryCards' -Key 'Slot1_Filename'
    if ([string]::IsNullOrWhiteSpace($baseCardName)) {
        $baseCardName = Get-Na2IniValue -Text $globalIniText -Section 'MemoryCards' -Key 'Slot1_Filename'
    }
    if ([string]::IsNullOrWhiteSpace($baseCardName)) {
        throw "No effective Slot1_Filename is configured for ${Serial}_${CRC}."
    }
    if ([IO.Path]::GetFileName($baseCardName) -cne $baseCardName) {
        throw "The configured Slot 1 memory card must be a file directly under the PCSX2 memcards directory: $baseCardName"
    }

    $baseCardPath = Join-Path $MemoryCardsDirectory $baseCardName
    if (-not (Test-Path -LiteralPath $baseCardPath -PathType Leaf)) {
        throw "Configured Slot 1 memory card does not exist: $baseCardPath"
    }

    $agentComponent = ConvertTo-Na2TestCardComponent -Value $AgentName
    $taskComponent = ConvertTo-Na2TestCardComponent -Value $TaskIdentity
    $baseStem = [IO.Path]::GetFileNameWithoutExtension($baseCardName)
    $extension = [IO.Path]::GetExtension($baseCardName)
    $taskCardName = "${baseStem}_${agentComponent}_${taskComponent}${extension}"
    $taskCardPath = Join-Path $MemoryCardsDirectory $taskCardName
    $taskCardCreated = $false

    try {
        if (-not (Test-Path -LiteralPath $taskCardPath -PathType Leaf)) {
            [IO.File]::Copy($baseCardPath, $taskCardPath, $false)
            $taskCardCreated = $true
        }

        $updatedGameSettings = Set-Na2IniValue -Text $gameSettingsText -Section 'MemoryCards' -Key 'Slot1_Enable' -Value 'true'
        $updatedGameSettings = Set-Na2IniValue -Text $updatedGameSettings -Section 'MemoryCards' -Key 'Slot1_Filename' -Value $taskCardName
        [IO.File]::WriteAllText($gameSettingsPath, $updatedGameSettings, [Text.UTF8Encoding]::new($false))
    }
    catch {
        if ($taskCardCreated -and (Test-Path -LiteralPath $taskCardPath -PathType Leaf)) {
            Remove-Item -LiteralPath $taskCardPath -Force
        }
        throw
    }

    [pscustomobject]@{
        BaseCardName = $baseCardName
        TaskCardName = $taskCardName
        TaskCardPath = $taskCardPath
        TaskCardCreated = $taskCardCreated
        GameSettingsPath = $gameSettingsPath
        GameSettingsExisted = $gameSettingsExisted
        OriginalGameSettingsBytes = $originalGameSettingsBytes
    }
}

function Exit-Na2TestMemoryCard {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object]$Context)

    if ($Context.GameSettingsExisted) {
        [IO.File]::WriteAllBytes($Context.GameSettingsPath, $Context.OriginalGameSettingsBytes)
    }
    elseif (Test-Path -LiteralPath $Context.GameSettingsPath) {
        Remove-Item -LiteralPath $Context.GameSettingsPath -Force
    }
}
