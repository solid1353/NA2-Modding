[CmdletBinding()]
param(
    [psobject]$ProjectPaths,
    [scriptblock]$IdentityResolver
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\na2\ini.ps1')
. (Join-Path $PSScriptRoot 'pnach_state.ps1')
. (Join-Path $PSScriptRoot '..\na2\iso_identity.ps1')

if ($null -eq $ProjectPaths) {
    $ProjectPaths = Get-Na2ProjectPaths
}
if ($null -eq $IdentityResolver) {
    $IdentityResolver = {
        param([string]$Path)
        Get-Na2IsoPcsx2Identity -Path $Path
    }
}

function Test-Na2ActualizeBytesEqual {
    param([byte[]]$Left, [byte[]]$Right)

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

function Set-Na2ActualizeTextAtomic {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Text
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    $directory = [IO.Path]::GetDirectoryName($fullPath)
    $temporary = Join-Path $directory (
        '.{0}.{1}.tmp' -f (
            [IO.Path]::GetFileName($fullPath),
            [guid]::NewGuid().ToString('N')
        )
    )
    try {
        [IO.File]::WriteAllText(
            $temporary,
            $Text,
            [Text.UTF8Encoding]::new($false)
        )
        [IO.File]::Move($temporary, $fullPath, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Get-Na2ActualizeLinkDestination {
    param([Parameter(Mandatory)][IO.FileSystemInfo]$Item)

    if ($Item.LinkType -ne 'SymbolicLink') {
        return $null
    }
    $target = [string]$Item.LinkTarget
    if ([string]::IsNullOrWhiteSpace($target)) {
        return $null
    }
    if (-not [IO.Path]::IsPathRooted($target)) {
        $target = Join-Path $Item.DirectoryName $target
    }
    return [IO.Path]::GetFullPath($target)
}

function Test-Na2ActualizePathWithin {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Directory
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullDirectory = [IO.Path]::GetFullPath($Directory).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    return $fullPath.StartsWith(
        $fullDirectory + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase
    )
}

function Set-Na2ActualizeSymlink {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Target,
        [Parameter(Mandatory)][scriptblock]$IsManaged
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullTarget = [IO.Path]::GetFullPath($Target)
    $item = Get-Item -LiteralPath $fullPath -Force -ErrorAction SilentlyContinue
    $status = 'verified'
    if ($null -ne $item) {
        $destination = Get-Na2ActualizeLinkDestination -Item $item
        if ($null -eq $destination -or -not (& $IsManaged $item $destination)) {
            throw "Refusing to replace an unmanaged file at alias path: $fullPath"
        }
        if (-not [IO.Path]::Equals($destination, $fullTarget)) {
            Remove-Item -LiteralPath $fullPath -Force
            $item = $null
            $status = 'updated'
        }
    }
    if ($null -eq $item) {
        $relativeTarget = [IO.Path]::GetRelativePath(
            [IO.Path]::GetDirectoryName($fullPath),
            $fullTarget
        )
        New-Item `
            -ItemType SymbolicLink `
            -Path $fullPath `
            -Target $relativeTarget |
            Out-Null
        if ($status -ne 'updated') {
            $status = 'created'
        }
    }

    $verified = Get-Item -LiteralPath $fullPath -Force
    $verifiedTarget = Get-Na2ActualizeLinkDestination -Item $verified
    if ($null -eq $verifiedTarget -or
        -not [IO.Path]::Equals($verifiedTarget, $fullTarget)) {
        throw "Alias verification failed: $fullPath"
    }
    return $status
}

$files = $ProjectPaths.files
$canonicalCheats = [IO.Path]::GetFullPath($files.canonical_cheats)
$canonicalGameSettings = [IO.Path]::GetFullPath($files.canonical_gamesettings)
$cheatsDirectory = Join-Path $ProjectPaths.pcsx2_user 'cheats'
$gameSettingsDirectory = [IO.Path]::GetFullPath(
    $ProjectPaths.pcsx2_user_gamesettings
)
$memoryCardsDirectory = [IO.Path]::GetFullPath(
    $ProjectPaths.pcsx2_user_memcards
)

foreach ($requiredFile in $canonicalCheats, $canonicalGameSettings) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required NA2 actualization input not found: $requiredFile"
    }
}
foreach ($requiredDirectory in (
    $cheatsDirectory,
    $gameSettingsDirectory,
    $memoryCardsDirectory
)) {
    if (-not (Test-Path -LiteralPath $requiredDirectory -PathType Container)) {
        throw "Required PCSX2 directory not found: $requiredDirectory"
    }
}

$gameSettingsTemplate = [IO.File]::ReadAllText($canonicalGameSettings)
$baseCardName = Get-Na2IniValue `
    -Text $gameSettingsTemplate `
    -Section 'MemoryCards' `
    -Key 'Slot1_Filename'
if ([string]::IsNullOrWhiteSpace($baseCardName) -or
    $baseCardName -cne [IO.Path]::GetFileName($baseCardName)) {
    throw 'gamesettings.ini must contain a plain Slot1_Filename.'
}
$baseCard = Join-Path $memoryCardsDirectory $baseCardName
if (-not (Test-Path -LiteralPath $baseCard -PathType Leaf)) {
    throw "Base memory card referenced by gamesettings.ini was not found: $baseCard"
}

$definitions = @(
    [pscustomobject]@{ Role = 'Current'; Iso = $files.current_iso }
    [pscustomobject]@{ Role = 'Previous'; Iso = $files.previous_iso }
    [pscustomobject]@{ Role = 'Candidate'; Iso = $files.candidate_iso }
)

$baseCardStem = [IO.Path]::GetFileNameWithoutExtension($baseCardName)
$baseCardExtension = [IO.Path]::GetExtension($baseCardName)
$roles = @(
    foreach ($definition in $definitions) {
        $isoPath = [IO.Path]::GetFullPath([string]$definition.Iso)
        if (-not (Test-Path -LiteralPath $isoPath -PathType Leaf)) {
            continue
        }

        $identity = & $IdentityResolver $isoPath
        if ($null -eq $identity -or
            [string]::IsNullOrWhiteSpace([string]$identity.Serial) -or
            [string]::IsNullOrWhiteSpace([string]$identity.CRC)) {
            throw "Identity resolver returned an invalid result for $isoPath"
        }
        $serial = ([string]$identity.Serial).ToUpperInvariant()
        $crc = ([string]$identity.CRC).ToUpperInvariant()
        $roleCardName = '{0} - {1}{2}' -f (
            $baseCardStem,
            [string]$definition.Role,
            $baseCardExtension
        )
        $settingsText = Set-Na2IniValue `
            -Text $gameSettingsTemplate `
            -Section 'MemoryCards' `
            -Key 'Slot1_Filename' `
            -Value $roleCardName

        [pscustomobject]@{
            Role = [string]$definition.Role
            Iso = $isoPath
            Serial = $serial
            CRC = $crc
            PnachName = "${serial}_${crc}.pnach"
            GameSettingsName = "${serial}_${crc}.ini"
            GameSettingsText = $settingsText
            MemoryCardName = $roleCardName
            MemoryCard = Join-Path $memoryCardsDirectory $roleCardName
        }
    }
)
if ($roles.Count -eq 0) {
    throw 'No built NA2.28 image is available for actualization.'
}

$duplicateSettings = @(
    $roles |
        Group-Object GameSettingsName |
        Where-Object Count -gt 1
)
if ($duplicateSettings.Count -gt 0) {
    throw (
        'Built NA2.28 images share a GameSettings identity: ' +
        (($duplicateSettings.Name | Sort-Object) -join ', ')
    )
}

$createdMemoryCards = [Collections.Generic.List[string]]::new()
$preservedMemoryCards = [Collections.Generic.List[string]]::new()
foreach ($role in $roles) {
    if (Test-Path -LiteralPath $role.MemoryCard -PathType Leaf) {
        $preservedMemoryCards.Add($role.MemoryCardName)
        continue
    }
    if (Test-Path -LiteralPath $role.MemoryCard) {
        throw "Memory-card destination is not a file: $($role.MemoryCard)"
    }
    Copy-Item -LiteralPath $baseCard -Destination $role.MemoryCard
    if (-not (Test-Na2ActualizeBytesEqual `
        -Left ([IO.File]::ReadAllBytes($baseCard)) `
        -Right ([IO.File]::ReadAllBytes($role.MemoryCard)))) {
        throw "New memory-card copy failed verification: $($role.MemoryCard)"
    }
    $createdMemoryCards.Add($role.MemoryCardName)
}

$legacyGameSettingsDirectory = Join-Path $gameSettingsDirectory '.na2'
$managedLegacySettingsLink = {
    param($item, $destination)
    if ($item.LinkType -ne 'SymbolicLink') {
        return $false
    }
    return (
        [IO.Path]::Equals($destination, $canonicalGameSettings) -or
        (Test-Na2ActualizePathWithin `
            -Path $destination `
            -Directory $legacyGameSettingsDirectory)
    )
}
$removedLegacySettingsSymlinks = @(
    Get-ChildItem -LiteralPath $gameSettingsDirectory -Filter '*.ini' -File -Force |
        Where-Object {
            $destination = Get-Na2ActualizeLinkDestination -Item $_
            $null -ne $destination -and
                (& $managedLegacySettingsLink $_ $destination)
        } |
        ForEach-Object {
            $name = $_.Name
            Remove-Item -LiteralPath $_.FullName -Force
            $name
        }
)

$desiredSettingsNames = @($roles.GameSettingsName)
$managedGameSettingsPattern = (
    '^(?:SLOP-NA228|SLUS-NA228|SLPS-22228)_[0-9A-F]{8}\.ini$'
)
$removedGameSettings = [Collections.Generic.List[string]]::new()
Get-ChildItem -LiteralPath $gameSettingsDirectory -Filter '*.ini' -File -Force |
    Where-Object {
        $_.Name -match $managedGameSettingsPattern -and
        $_.Name -notin $desiredSettingsNames
    } |
    ForEach-Object {
        $removedGameSettings.Add($_.Name)
        Remove-Item -LiteralPath $_.FullName -Force
    }

$createdGameSettings = [Collections.Generic.List[string]]::new()
$updatedGameSettings = [Collections.Generic.List[string]]::new()
$preservedGameSettings = [Collections.Generic.List[string]]::new()
foreach ($role in $roles) {
    $path = Join-Path $gameSettingsDirectory $role.GameSettingsName
    $expectedBytes = [Text.UTF8Encoding]::new($false).GetBytes(
        $role.GameSettingsText
    )
    $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    if ($null -ne $item) {
        if ($item.PSIsContainer -or
            -not [string]::IsNullOrWhiteSpace([string]$item.LinkType)) {
            throw "GameSettings destination is not a real file: $path"
        }
        $currentBytes = [IO.File]::ReadAllBytes($path)
        $isExpected = Test-Na2ActualizeBytesEqual `
            -Left $currentBytes `
            -Right $expectedBytes
        if ($isExpected) {
            $preservedGameSettings.Add($role.GameSettingsName)
        }
        else {
            if ($role.GameSettingsName -notmatch $managedGameSettingsPattern) {
                throw "Refusing to overwrite unmanaged GameSettings: $path"
            }
            Set-Na2ActualizeTextAtomic `
                -Path $path `
                -Text $role.GameSettingsText
            $updatedGameSettings.Add($role.GameSettingsName)
        }
    }
    else {
        Set-Na2ActualizeTextAtomic `
            -Path $path `
            -Text $role.GameSettingsText
        $createdGameSettings.Add($role.GameSettingsName)
    }
}

if (Test-Path -LiteralPath $legacyGameSettingsDirectory -PathType Container) {
    foreach ($legacyName in 'Current.ini', 'Previous.ini', 'Candidate.ini') {
        $legacyPath = Join-Path $legacyGameSettingsDirectory $legacyName
        if (Test-Path -LiteralPath $legacyPath -PathType Leaf) {
            Remove-Item -LiteralPath $legacyPath -Force
        }
    }
    if (@(Get-ChildItem -LiteralPath $legacyGameSettingsDirectory -Force).Count -eq 0) {
        Remove-Item -LiteralPath $legacyGameSettingsDirectory -Force
    }
}

$managedPnachLink = {
    param($item, $destination)
    if ($item.LinkType -ne 'SymbolicLink') {
        return $false
    }
    return (
        [IO.Path]::Equals($destination, $canonicalCheats) -or
        (
            [IO.Path]::Equals(
                [IO.Path]::GetDirectoryName($destination),
                [IO.Path]::GetFullPath($ProjectPaths.pcsx2_files)
            ) -and
            [IO.Path]::GetExtension($destination) -ieq '.pnach'
        )
    )
}
$desiredPnachNames = @($roles.PnachName | Select-Object -Unique)
$removedPnachSymlinks = @(
    Get-ChildItem -LiteralPath $cheatsDirectory -Filter '*.pnach' -File -Force |
        Where-Object {
            $destination = Get-Na2ActualizeLinkDestination -Item $_
            $null -ne $destination -and
                (& $managedPnachLink $_ $destination) -and
                $_.Name -notin $desiredPnachNames
        } |
        ForEach-Object {
            $name = $_.Name
            Remove-Item -LiteralPath $_.FullName -Force
            $name
        }
)

$pnachState = Get-Na2PnachState -Path $canonicalCheats
$cheatAliases = [Collections.Generic.List[string]]::new()
if (-not $pnachState.IsEmpty) {
    foreach ($pnachName in $desiredPnachNames) {
        $aliasPath = Join-Path $cheatsDirectory $pnachName
        $null = Set-Na2ActualizeSymlink `
            -Path $aliasPath `
            -Target $canonicalCheats `
            -IsManaged $managedPnachLink
        $cheatAliases.Add($aliasPath)
    }
}
else {
    $removedPnachSymlinks += @(
        Get-ChildItem -LiteralPath $cheatsDirectory -Filter '*.pnach' -File -Force |
            Where-Object {
                $destination = Get-Na2ActualizeLinkDestination -Item $_
                $null -ne $destination -and
                    (& $managedPnachLink $_ $destination)
            } |
            ForEach-Object {
                $name = $_.Name
                Remove-Item -LiteralPath $_.FullName -Force
                $name
            }
    )
}

[pscustomobject]@{
    Roles = $roles
    CanonicalPnach = $canonicalCheats
    CheatAliases = @($cheatAliases)
    RemovedCheatSymlinks = @($removedPnachSymlinks | Select-Object -Unique)
    EnabledCheats = $pnachState.EnabledCheats
    CreatedGameSettings = @($createdGameSettings)
    UpdatedGameSettings = @($updatedGameSettings)
    PreservedGameSettings = @($preservedGameSettings)
    RemovedGameSettings = @(
        @($removedLegacySettingsSymlinks) +
        @($removedGameSettings) |
            Select-Object -Unique
    )
    CreatedMemoryCards = @($createdMemoryCards)
    PreservedMemoryCards = @($preservedMemoryCards)
}
