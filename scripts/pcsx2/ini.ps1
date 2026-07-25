# Shared PCSX2 INI helpers.
Set-StrictMode -Version Latest

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
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Value
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

function Remove-Na2IniValue {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text,
        [Parameter(Mandatory = $true)][string]$Section,
        [Parameter(Mandatory = $true)][string]$Key
    )

    $sectionPattern = '(?ms)^\s*\[' + [regex]::Escape($Section) + '\]\s*\r?\n(?<body>.*?)(?=^\s*\[|\z)'
    $sectionMatch = [regex]::Match($Text, $sectionPattern)
    if (-not $sectionMatch.Success) { return $Text }
    $bodyGroup = $sectionMatch.Groups['body']
    $body = $bodyGroup.Value
    $keyPattern = '(?m)^[ \t]*' + [regex]::Escape($Key) + '[ \t]*=[^\r\n]*(?:\r?\n|$)'
    $matches = [regex]::Matches($body, $keyPattern)
    if ($matches.Count -gt 1) {
        throw "INI section [$Section] contains duplicate $Key settings."
    }
    if ($matches.Count -eq 0) { return $Text }
    $match = $matches[0]
    $newBody = $body.Remove($match.Index, $match.Length)
    return $Text.Substring(0, $bodyGroup.Index) + $newBody + $Text.Substring($bodyGroup.Index + $bodyGroup.Length)
}

function Set-Na2IniSettings {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text,
        [Parameter(Mandatory = $true)][object[]]$Settings
    )

    $result = $Text
    foreach ($setting in $Settings) {
        $result = Set-Na2IniValue `
            -Text $result `
            -Section ([string]$setting.Section) `
            -Key ([string]$setting.Key) `
            -Value ([string]$setting.Value)
    }
    return $result
}
