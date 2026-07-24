[CmdletBinding()]
param(
    [ValidateSet('Current', 'Previous', 'Candidate')]
    [string]$ActiveRole = 'Current',
    [psobject]$ProjectPaths,
    [scriptblock]$IdentityResolver
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'ini.ps1')
. (Join-Path $PSScriptRoot 'pnach_state.ps1')
. (Join-Path $PSScriptRoot 'iso_identity.ps1')

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
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
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
    $status = 'verified symlink'
    if ($null -ne $item) {
        $destination = Get-Na2ActualizeLinkDestination -Item $item
        if ($null -eq $destination -or -not (& $IsManaged $item $destination)) {
            throw "Refusing to replace an unmanaged file at alias path: $fullPath"
        }
        if (-not [IO.Path]::Equals($destination, $fullTarget)) {
            Remove-Item -LiteralPath $fullPath -Force
            $item = $null
            $status = 'updated symlink'
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
        if ($status -ne 'updated symlink') {
            $status = 'created symlink'
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
$baseCard = [IO.Path]::GetFullPath($files.na228_base_memcard)
$cheatsDirectory = Join-Path $ProjectPaths.pcsx2 'cheats'
$gameSettingsDirectory = [IO.Path]::GetFullPath($ProjectPaths.pcsx2_gamesettings)
$managedGameSettingsDirectory = [IO.Path]::GetDirectoryName(
    [IO.Path]::GetFullPath($files.current_gamesettings)
)

foreach ($requiredFile in $canonicalCheats, $canonicalGameSettings, $baseCard) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required PCSX2 actualization input not found: $requiredFile"
    }
}
foreach ($requiredDirectory in $cheatsDirectory, $gameSettingsDirectory) {
    if (-not (Test-Path -LiteralPath $requiredDirectory -PathType Container)) {
        throw "Required PCSX2 directory not found: $requiredDirectory"
    }
}
New-Item `
    -ItemType Directory `
    -Path $managedGameSettingsDirectory `
    -Force |
    Out-Null

$definitions = @(
    [pscustomobject]@{
        Role = 'Current'
        Iso = $files.current_iso
        Card = $files.na228_current_memcard
        Settings = $files.current_gamesettings
    }
    [pscustomobject]@{
        Role = 'Previous'
        Iso = $files.previous_iso
        Card = $files.na228_previous_memcard
        Settings = $files.previous_gamesettings
    }
    [pscustomobject]@{
        Role = 'Candidate'
        Iso = $files.candidate_iso
        Card = $files.na228_candidate_memcard
        Settings = $files.candidate_gamesettings
    }
)

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
        $cardPath = [IO.Path]::GetFullPath([string]$definition.Card)
        $cardCreated = $false
        if (-not (Test-Path -LiteralPath $cardPath -PathType Leaf)) {
            Copy-Item -LiteralPath $baseCard -Destination $cardPath
            $cardCreated = $true
            if (-not (Test-Na2ActualizeBytesEqual `
                -Left ([IO.File]::ReadAllBytes($baseCard)) `
                -Right ([IO.File]::ReadAllBytes($cardPath)))) {
                throw "New memory-card copy failed verification: $cardPath"
            }
        }

        $settingsText = [IO.File]::ReadAllText($canonicalGameSettings)
        $settingsText = Set-Na2IniValue `
            -Text $settingsText `
            -Section 'MemoryCards' `
            -Key 'Slot1_Filename' `
            -Value ([IO.Path]::GetFileName($cardPath))
        $settingsPath = [IO.Path]::GetFullPath([string]$definition.Settings)
        $settingsChanged = (
            -not (Test-Path -LiteralPath $settingsPath -PathType Leaf) -or
            [IO.File]::ReadAllText($settingsPath) -cne $settingsText
        )
        if ($settingsChanged) {
            Set-Na2ActualizeTextAtomic -Path $settingsPath -Text $settingsText
        }

        [pscustomobject]@{
            Role = [string]$definition.Role
            Iso = $isoPath
            Serial = $serial
            CRC = $crc
            PnachName = "${serial}_${crc}.pnach"
            GameSettingsName = "${serial}_${crc}.ini"
            Card = $cardPath
            CardCreated = $cardCreated
            Settings = $settingsPath
            SettingsChanged = $settingsChanged
        }
    }
)

$active = @($roles | Where-Object Role -CEQ $ActiveRole)
if ($active.Count -ne 1) {
    throw "$ActiveRole ISO is not available for PCSX2 actualization."
}
$active = $active[0]

$existingRoleNames = @($roles.Role)
foreach ($definition in $definitions) {
    if ($definition.Role -notin $existingRoleNames -and
        (Test-Path -LiteralPath $definition.Settings -PathType Leaf)) {
        Remove-Item -LiteralPath $definition.Settings -Force
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
    Get-ChildItem -LiteralPath $cheatsDirectory -Filter '*.pnach' -Force |
        Where-Object {
            $destination = Get-Na2ActualizeLinkDestination -Item $_
            $null -ne $destination -and
            (& $managedPnachLink $_ $destination) -and
            ($_.Name -notin $desiredPnachNames -or
                -not [IO.Path]::Equals($destination, $canonicalCheats))
        } |
        ForEach-Object {
            $name = $_.Name
            Remove-Item -LiteralPath $_.FullName -Force
            $name
        }
)

$pnachState = Get-Na2PnachState -Path $canonicalCheats
$pnachStatus = 'skipped empty canonical PNACH'
$activePnach = $null
if (-not $pnachState.IsEmpty) {
    foreach ($pnachName in $desiredPnachNames) {
        $aliasPath = Join-Path $cheatsDirectory $pnachName
        $status = Set-Na2ActualizeSymlink `
            -Path $aliasPath `
            -Target $canonicalCheats `
            -IsManaged $managedPnachLink
        if ($pnachName -ceq $active.PnachName) {
            $pnachStatus = $status
            $activePnach = $aliasPath
        }
    }
}
else {
    $removedPnachSymlinks += @(
        Get-ChildItem -LiteralPath $cheatsDirectory -Filter '*.pnach' -Force |
            Where-Object {
                $destination = Get-Na2ActualizeLinkDestination -Item $_
                $null -ne $destination -and (& $managedPnachLink $_ $destination)
            } |
            ForEach-Object {
                $name = $_.Name
                Remove-Item -LiteralPath $_.FullName -Force
                $name
            }
    )
}

$managedSettingsLink = {
    param($item, $destination)
    if ($item.LinkType -ne 'SymbolicLink') {
        return $false
    }
    return (
        [IO.Path]::Equals($destination, $canonicalGameSettings) -or
        (Test-Na2ActualizePathWithin `
            -Path $destination `
            -Directory $managedGameSettingsDirectory)
    )
}
$settingsWinners = @{}
foreach ($role in $roles) {
    if (-not $settingsWinners.ContainsKey($role.GameSettingsName)) {
        $settingsWinners[$role.GameSettingsName] = $role
    }
}
$settingsWinners[$active.GameSettingsName] = $active
$desiredSettingsNames = @($settingsWinners.Keys)
$removedGameSettingsSymlinks = @(
    Get-ChildItem -LiteralPath $gameSettingsDirectory -Filter '*.ini' -Force |
        Where-Object {
            $destination = Get-Na2ActualizeLinkDestination -Item $_
            $null -ne $destination -and
            (& $managedSettingsLink $_ $destination) -and
            ($_.Name -notin $desiredSettingsNames -or
                -not [IO.Path]::Equals(
                    $destination,
                    $settingsWinners[$_.Name].Settings
                ))
        } |
        ForEach-Object {
            $name = $_.Name
            Remove-Item -LiteralPath $_.FullName -Force
            $name
        }
)

$activeSettingsStatus = ''
foreach ($settingsName in $desiredSettingsNames) {
    $winner = $settingsWinners[$settingsName]
    $aliasPath = Join-Path $gameSettingsDirectory $settingsName
    $status = Set-Na2ActualizeSymlink `
        -Path $aliasPath `
        -Target $winner.Settings `
        -IsManaged $managedSettingsLink
    if ($settingsName -ceq $active.GameSettingsName) {
        $activeSettingsStatus = $status
    }
}

[pscustomobject]@{
    ActiveRole = $active.Role
    Iso = $active.Iso
    PCSX2Serial = $active.Serial
    PCSX2ElfCRC = $active.CRC
    CanonicalPnach = $canonicalCheats
    CheatsPnach = $activePnach
    PnachStatus = $pnachStatus
    RemovedPnachSymlinks = @($removedPnachSymlinks | Select-Object -Unique)
    EnabledCheats = $pnachState.EnabledCheats
    GameSettings = Join-Path $gameSettingsDirectory $active.GameSettingsName
    GameSettingsStatus = $activeSettingsStatus
    RemovedGameSettingsSymlinks = @(
        $removedGameSettingsSymlinks | Select-Object -Unique
    )
    MemoryCard = $active.Card
    MemoryCardStatus = if ($active.CardCreated) { 'created' } else { 'preserved' }
    CreatedMemoryCards = @(
        $roles | Where-Object CardCreated | ForEach-Object {
            [IO.Path]::GetFileName($_.Card)
        }
    )
    Roles = $roles
}
