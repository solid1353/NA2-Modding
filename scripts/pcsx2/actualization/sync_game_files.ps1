# Synchronize NA2.28 CRC-named cheats and GameSettings with retained builds.
[CmdletBinding()]
param(
    [psobject]$ProjectPaths,
    [scriptblock]$IdentityResolver,

    [Alias('Roles')]
    [ValidateSet('latest', 'previous', 'test')]
    [string[]]$SelectedRoles
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\ini.ps1')
. (Join-Path $PSScriptRoot 'pnach_state.ps1')
. (Join-Path $PSScriptRoot '..\..\na228\iso_identity.ps1')

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

function Resolve-Na2ActualizePhysicalPath {
    param([Parameter(Mandatory)][string]$Path)

    $fullPath = [IO.Path]::GetFullPath($Path)
    $root = [IO.Path]::GetPathRoot($fullPath)
    $current = $root
    $relative = $fullPath.Substring($root.Length)
    foreach ($component in $relative.Split(
        [char[]]@(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        ),
        [StringSplitOptions]::RemoveEmptyEntries
    )) {
        $next = Join-Path $current $component
        $item = Get-Item -LiteralPath $next -Force -ErrorAction SilentlyContinue
        if ($null -eq $item) {
            $current = $next
            continue
        }

        if ($item.LinkType -in @('SymbolicLink', 'Junction')) {
            $resolved = $item.ResolveLinkTarget($true)
            if ($null -ne $resolved) {
                $current = $resolved.FullName
                continue
            }
        }
        $current = $item.FullName
    }

    return [IO.Path]::GetFullPath($current)
}

function Get-Na2ActualizeLinkDestination {
    param([Parameter(Mandatory)][IO.FileSystemInfo]$Item)

    if ($Item.LinkType -ne 'SymbolicLink') {
        return $null
    }

    $resolved = $Item.ResolveLinkTarget($true)
    if ($null -ne $resolved) {
        return Resolve-Na2ActualizePhysicalPath -Path $resolved.FullName
    }

    $target = [string]$Item.LinkTarget
    if ([string]::IsNullOrWhiteSpace($target)) {
        return $null
    }
    if (-not [IO.Path]::IsPathRooted($target)) {
        $physicalParent = Resolve-Na2ActualizePhysicalPath `
            -Path $Item.DirectoryName
        $target = Join-Path $physicalParent $target
    }
    return Resolve-Na2ActualizePhysicalPath -Path $target
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
        [Parameter(Mandatory)][scriptblock]$IsManaged,
        [switch]$ReplaceRegularFile
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullTarget = Resolve-Na2ActualizePhysicalPath -Path $Target
    $logicalParent = [IO.Path]::GetDirectoryName($fullPath)
    $physicalParent = Resolve-Na2ActualizePhysicalPath -Path $logicalParent
    $physicalPath = Join-Path $physicalParent (
        [IO.Path]::GetFileName($fullPath)
    )
    $item = Get-Item -LiteralPath $fullPath -Force -ErrorAction SilentlyContinue
    if ($null -eq $item) {
        $item = Get-ChildItem -LiteralPath $logicalParent -Force |
            Where-Object Name -CEQ ([IO.Path]::GetFileName($fullPath)) |
            Select-Object -First 1
    }
    $status = 'verified'
    if ($null -ne $item) {
        $destination = Get-Na2ActualizeLinkDestination -Item $item
        $replaceableRegularFile = (
            $ReplaceRegularFile -and
            $null -eq $destination -and
            -not $item.PSIsContainer -and
            [string]::IsNullOrWhiteSpace([string]$item.LinkType)
        )
        if (-not $replaceableRegularFile -and (
            $null -eq $destination -or
            -not (& $IsManaged $item $destination)
        )) {
            throw "Refusing to replace an unmanaged file at alias path: $fullPath"
        }
        if ($replaceableRegularFile -or
            -not [IO.Path]::Equals($destination, $fullTarget)) {
            Remove-Item -LiteralPath $physicalPath -Force
            $item = $null
            $status = 'updated'
        }
    }
    if ($null -eq $item) {
        $relativeTarget = [IO.Path]::GetRelativePath(
            $physicalParent,
            $fullTarget
        )
        New-Item `
            -ItemType SymbolicLink `
            -Path $physicalPath `
            -Target $relativeTarget |
            Out-Null
        if ($status -ne 'updated') {
            $status = 'created'
        }
    }

    $verified = Get-Item -LiteralPath $physicalPath -Force
    $verifiedTarget = Get-Na2ActualizeLinkDestination -Item $verified
    if ($null -eq $verifiedTarget -or
        -not [IO.Path]::Equals($verifiedTarget, $fullTarget)) {
        throw "Alias verification failed: $fullPath"
    }
    return $status
}

$buildEntries = @(
    $ProjectPaths.games.Entries.PSObject.Properties |
        ForEach-Object { $_.Value } |
        Where-Object Category -eq 'builds'
)
if ($buildEntries.Count -eq 0) {
    throw 'Game catalog has no NA2.28 build entries.'
}
$buildConfig = $buildEntries[0].Config
$cheatTemplate = Resolve-Na2ActualizePhysicalPath `
    -Path $buildConfig.cheat_template
$gameSettingsTemplatePath = Resolve-Na2ActualizePhysicalPath `
    -Path $buildConfig.gamesettings_template
$cheatsDirectory = Resolve-Na2ActualizePhysicalPath `
    -Path $ProjectPaths.pcsx2_cheats
$gameSettingsDirectory = Resolve-Na2ActualizePhysicalPath -Path (
    $ProjectPaths.pcsx2_game_settings
)
$memoryCardsDirectory = Resolve-Na2ActualizePhysicalPath -Path (
    $ProjectPaths.pcsx2_memory_cards
)

foreach ($requiredFile in $cheatTemplate, $gameSettingsTemplatePath) {
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

$gameSettingsTemplate = [IO.File]::ReadAllText($gameSettingsTemplatePath)

$definitions = @(
    foreach ($entry in $buildEntries) {
        [pscustomobject]@{
            Role = $entry.Postfix
            Iso = $entry.IsoPath
            MemoryCard = $entry.MemoryCardPath
        }
    }
)

$requestedRoleNames = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
foreach ($selectedRole in @($SelectedRoles)) {
    if (-not [string]::IsNullOrWhiteSpace($selectedRole)) {
        [void]$requestedRoleNames.Add($selectedRole)
    }
}
if ($requestedRoleNames.Count -gt 0) {
    $knownRoleNames = @($definitions.Role)
    $unknownRoleNames = @(
        $requestedRoleNames |
            Where-Object { $_ -notin $knownRoleNames }
    )
    if ($unknownRoleNames.Count -gt 0) {
        throw "Unknown NA2.28 build role: $($unknownRoleNames -join ', ')."
    }
}

$allResolvedRoles = @(
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
        $memoryCardPath = [IO.Path]::GetFullPath(
            [string]$definition.MemoryCard
        )
        $memoryCardName = [IO.Path]::GetFileName($memoryCardPath)

        [pscustomobject]@{
            Role = [string]$definition.Role
            Iso = $isoPath
            Serial = $serial
            CRC = $crc
            PnachName = "${serial}_${crc}.pnach"
            GameSettingsName = "${serial}_${crc}.ini"
            MemoryCardPath = $memoryCardPath
            MemoryCardName = $memoryCardName
        }
    }
)
if ($allResolvedRoles.Count -eq 0) {
    throw 'No built NA2.28 image is available for actualization.'
}

$roles = @(
    if ($requestedRoleNames.Count -eq 0) {
        $allResolvedRoles
    }
    else {
        $allResolvedRoles |
            Where-Object { $requestedRoleNames.Contains($_.Role) }
    }
)
if ($roles.Count -eq 0) {
    throw (
        'No selected NA2.28 build image is available for actualization: ' +
        "$(@($SelectedRoles) -join ', ')."
    )
}

$allSettingsRoles = @(
    $allResolvedRoles |
        Group-Object GameSettingsName |
        ForEach-Object { $_.Group | Select-Object -First 1 }
)
$settingsRoles = @(
    if ($requestedRoleNames.Count -eq 0) {
        $allSettingsRoles
    }
    else {
        $allSettingsRoles |
            Where-Object { $requestedRoleNames.Contains($_.Role) }
    }
)
foreach ($role in $settingsRoles) {
    if (-not (Test-Path -LiteralPath $role.MemoryCardPath -PathType Leaf)) {
        throw "$($role.Role) memory card was not found: $($role.MemoryCardPath)"
    }
    $settingsText = Set-Na2IniValue `
        -Text $gameSettingsTemplate `
        -Section 'MemoryCards' `
        -Key 'Slot1_Filename' `
        -Value $role.MemoryCardName
    $role | Add-Member `
        -NotePropertyName GameSettingsText `
        -NotePropertyValue $settingsText
}

$legacyGameSettingsDirectory = Join-Path $gameSettingsDirectory '.na2'
$managedLegacySettingsLink = {
    param($item, $destination)
    if ($item.LinkType -ne 'SymbolicLink') {
        return $false
    }
    return (
        [IO.Path]::Equals($destination, $gameSettingsTemplatePath) -or
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

$desiredSettingsNames = @($allSettingsRoles.GameSettingsName)
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
foreach ($role in $settingsRoles) {
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
    foreach ($legacyName in @($definitions.Role | ForEach-Object { "$_.ini" })) {
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
        [IO.Path]::Equals($destination, $cheatTemplate) -or
        (
            [IO.Path]::Equals(
                [IO.Path]::GetDirectoryName($destination),
                $cheatsDirectory
            ) -and
            [IO.Path]::GetExtension($destination) -ieq '.pnach'
        )
    )
}
$allDesiredPnachNames = @(
    $allResolvedRoles.PnachName |
        Select-Object -Unique
)
$desiredPnachNames = @($roles.PnachName | Select-Object -Unique)
$managedPnachNamePattern = (
    '^(?:SLOP-NA228|SLUS-NA228|SLPS-22228)_[0-9A-F]{8}\.pnach$'
)
$removedPnachSymlinks = @(
    Get-ChildItem -LiteralPath $cheatsDirectory -Filter '*.pnach' -File -Force |
        Where-Object {
            $destination = Get-Na2ActualizeLinkDestination -Item $_
            $_.Name -notin $allDesiredPnachNames -and
                (
                    $_.Name -match $managedPnachNamePattern -or
                    (
                        $null -ne $destination -and
                        (& $managedPnachLink $_ $destination)
                    )
                )
        } |
        ForEach-Object {
            $name = $_.Name
            Remove-Item -LiteralPath $_.FullName -Force
            $name
        }
)

$pnachState = Get-Na2PnachState -Path $cheatTemplate
$cheatAliases = [Collections.Generic.List[string]]::new()
foreach ($pnachName in $desiredPnachNames) {
    $aliasPath = Join-Path $cheatsDirectory $pnachName
    if (-not $pnachState.IsEmpty) {
        $null = Set-Na2ActualizeSymlink `
            -Path $aliasPath `
            -Target $cheatTemplate `
            -IsManaged $managedPnachLink `
            -ReplaceRegularFile
        $cheatAliases.Add($aliasPath)
    }
}
if ($pnachState.IsEmpty) {
    $removedPnachSymlinks += @(
        Get-ChildItem -LiteralPath $cheatsDirectory -Filter '*.pnach' -File -Force |
            Where-Object {
                $destination = Get-Na2ActualizeLinkDestination -Item $_
                (
                        $_.Name -in $desiredPnachNames -or
                        (
                            $null -ne $destination -and
                            (& $managedPnachLink $_ $destination)
                        )
                    )
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
    CheatTemplate = $cheatTemplate
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
}
