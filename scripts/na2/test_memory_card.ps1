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

. (Join-Path $PSScriptRoot 'ini.ps1')

function Enter-Na2TestMemoryCard {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$GlobalIniPath,
        [Parameter(Mandatory = $true)][string]$GameSettingsDirectory,
        [Parameter(Mandatory = $true)][string]$SourceMemoryCardsDirectory,
        [Parameter(Mandatory = $true)][string]$TaskMemoryCardsDirectory,
        [Parameter(Mandatory = $true)][string]$Serial,
        [Parameter(Mandatory = $true)][string]$CRC,
        [Parameter(Mandatory = $true)][string]$AgentName,
        [Parameter(Mandatory = $true)][string]$TaskIdentity
    )

    foreach ($directory in $GameSettingsDirectory, $SourceMemoryCardsDirectory) {
        if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
            throw "Required PCSX2 directory does not exist: $directory"
        }
    }
    New-Item -ItemType Directory -Force -Path $TaskMemoryCardsDirectory | Out-Null
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

    $baseCardPath = Join-Path $SourceMemoryCardsDirectory $baseCardName
    if (-not (Test-Path -LiteralPath $baseCardPath -PathType Leaf)) {
        throw "Configured Slot 1 memory card does not exist: $baseCardPath"
    }

    $agentComponent = ConvertTo-Na2TestCardComponent -Value $AgentName
    $taskComponent = ConvertTo-Na2TestCardComponent -Value $TaskIdentity
    $baseStem = [IO.Path]::GetFileNameWithoutExtension($baseCardName)
    $extension = [IO.Path]::GetExtension($baseCardName)
    $taskCardName = "${baseStem}_${agentComponent}_${taskComponent}${extension}"
    $taskCardPath = Join-Path $TaskMemoryCardsDirectory $taskCardName
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
        InjectedSlot1Enable = 'true'
        InjectedSlot1Filename = $taskCardName
    }
}

function Exit-Na2TestMemoryCard {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object]$Context,
        [switch]$OnlyIfInjected
    )

    if ($OnlyIfInjected) {
        if (-not (Test-Path -LiteralPath $Context.GameSettingsPath -PathType Leaf)) {
            return $false
        }
        $current = [IO.File]::ReadAllText($Context.GameSettingsPath)
        $currentEnable = Get-Na2IniValue `
            -Text $current `
            -Section 'MemoryCards' `
            -Key 'Slot1_Enable'
        $currentFilename = Get-Na2IniValue `
            -Text $current `
            -Section 'MemoryCards' `
            -Key 'Slot1_Filename'
        if ($currentEnable -cne $Context.InjectedSlot1Enable -or
            $currentFilename -cne $Context.InjectedSlot1Filename) {
            return $false
        }
    }

    if ($Context.GameSettingsExisted) {
        [IO.File]::WriteAllBytes($Context.GameSettingsPath, $Context.OriginalGameSettingsBytes)
    }
    elseif (Test-Path -LiteralPath $Context.GameSettingsPath) {
        Remove-Item -LiteralPath $Context.GameSettingsPath -Force
    }
    return $true
}
