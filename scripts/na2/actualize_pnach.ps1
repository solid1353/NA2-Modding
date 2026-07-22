param(
    [string]$IsoPath = "",
    [string[]]$PreserveIsoPath = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'pnach_state.ps1')
. (Join-Path $PSScriptRoot 'iso_identity.ps1')
$projectPaths = Get-Na2ProjectPaths
$CanonicalPnach = Join-Path $projectPaths.pcsx2_files 'SLPS-25837_C0659AD1.pnach'
$ManagedSerials = @('SLPS-25837', 'SLPS-22228')

function Get-SymbolicLinkDestinationPath {
    param([IO.FileSystemInfo]$Item)

    if ($Item.LinkType -ne "SymbolicLink") {
        throw "PNACH alias is not a symbolic link: $($Item.FullName)"
    }
    $linkTarget = [string]$Item.LinkTarget
    if ([string]::IsNullOrWhiteSpace($linkTarget)) {
        throw "Could not read PNACH symlink target: $($Item.FullName)"
    }
    $candidate = if ([IO.Path]::IsPathRooted($linkTarget)) {
        $linkTarget
    }
    else {
        Join-Path $Item.DirectoryName $linkTarget
    }
    return (Resolve-Path -LiteralPath $candidate).Path
}

function Test-CanonicalPnachSymlink {
    param(
        [IO.FileSystemInfo]$Item,
        [string]$CanonicalPnach
    )

    if ($Item.LinkType -ne "SymbolicLink") {
        return $false
    }
    try {
        return (Get-SymbolicLinkDestinationPath -Item $Item) -eq $CanonicalPnach
    }
    catch {
        return $false
    }
}

function Get-ManagedPnachSymlinks {
    param(
        [Parameter(Mandatory = $true)][string]$CheatsDirectory,
        [Parameter(Mandatory = $true)][string]$CanonicalPnach,
        [Parameter(Mandatory = $true)][string[]]$Serials
    )

    $serialPattern = '^(?:' + (($Serials | ForEach-Object { [regex]::Escape($_) }) -join '|') + ')_[0-9A-Fa-f]{8}\.pnach$'
    Get-ChildItem -LiteralPath $CheatsDirectory -Filter '*.pnach' -Force |
        Where-Object {
            $_.Name -match $serialPattern -and
            (Test-CanonicalPnachSymlink -Item $_ -CanonicalPnach $CanonicalPnach)
        }
}

$CanonicalPnach = (Resolve-Path -LiteralPath $CanonicalPnach).Path
$pnachState = Get-Na2PnachState -Path $CanonicalPnach
$cheatsDir = Join-Path $projectPaths.pcsx2 'cheats'
if (-not (Test-Path -LiteralPath $cheatsDir -PathType Container)) {
    throw "Configured PCSX2 cheats directory does not exist: $cheatsDir"
}
$cheatsDir = (Resolve-Path -LiteralPath $cheatsDir).Path
$canonicalLinkTarget = [IO.Path]::GetRelativePath($cheatsDir, $CanonicalPnach)

if ($pnachState.IsEmpty) {
    $removedPnachSymlinks = @(
        Get-ManagedPnachSymlinks `
            -CheatsDirectory $cheatsDir `
            -CanonicalPnach $CanonicalPnach `
            -Serials $ManagedSerials |
            ForEach-Object {
                $name = $_.Name
                Remove-Item -LiteralPath $_.FullName -Force
                $name
            }
    )

    return [pscustomobject]@{
        Iso = $null
        BootElf = $null
        PCSX2ElfCRC = $null
        CanonicalPnach = $CanonicalPnach
        CheatsPnach = $null
        PnachStatus = "skipped empty canonical PNACH"
        RemovedPnachSymlinks = $removedPnachSymlinks
        EnabledCheats = @()
    }
}

if ([string]::IsNullOrWhiteSpace($IsoPath)) {
    $IsoPath = $projectPaths.files.current_iso
    if (-not (Test-Path -LiteralPath $IsoPath -PathType Leaf)) {
        throw "Default build ISO does not exist: $IsoPath. Pass -IsoPath explicitly."
    }
}
$identity = Get-Na2IsoPcsx2Identity -Path $IsoPath
if ($identity.Serial -notin $ManagedSerials) {
    throw "Boot serial is not managed by this project: $($identity.Serial)"
}
$preservedIdentities = @(
    $PreserveIsoPath |
        Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
        ForEach-Object {
            $preservedIdentity = Get-Na2IsoPcsx2Identity -Path $_
            if ($preservedIdentity.Serial -notin $ManagedSerials) {
                throw "Boot serial is not managed by this project: $($preservedIdentity.Serial)"
            }
            $preservedIdentity
        }
)
$desiredPnachNames = @($identity.PnachName) + @($preservedIdentities.PnachName) |
    Select-Object -Unique
$targetPnach = Join-Path $cheatsDir $identity.PnachName
$desiredPnachPaths = @($desiredPnachNames | ForEach-Object { Join-Path $cheatsDir $_ })

$removedPnachSymlinks = @(
    Get-ManagedPnachSymlinks `
        -CheatsDirectory $cheatsDir `
        -CanonicalPnach $CanonicalPnach `
        -Serials $ManagedSerials |
        Where-Object {
            $_.FullName -notin $desiredPnachPaths
        } |
        ForEach-Object {
            $name = $_.Name
            Remove-Item -LiteralPath $_.FullName -Force
            $name
        }
)

foreach ($desiredPnachPath in $desiredPnachPaths) {
    $targetItem = Get-Item -LiteralPath $desiredPnachPath -Force -ErrorAction SilentlyContinue
    if ($null -ne $targetItem) {
        if ($targetItem.LinkType -ne "SymbolicLink") {
            throw "Refusing to replace real PNACH file at CRC alias path: $desiredPnachPath"
        }
        $existingDestination = Get-SymbolicLinkDestinationPath -Item $targetItem
        if ($existingDestination -ne $CanonicalPnach) {
            throw "Refusing to replace unmanaged PNACH symlink at CRC alias path: $desiredPnachPath -> $existingDestination"
        }
        if ($desiredPnachPath -eq $targetPnach) {
            $pnachStatus = "verified symlink"
        }
    }
    else {
        New-Item -ItemType SymbolicLink -Path $desiredPnachPath -Target $canonicalLinkTarget | Out-Null
        if ($desiredPnachPath -eq $targetPnach) {
            $pnachStatus = "created symlink"
        }
    }

    $verifiedItem = Get-Item -LiteralPath $desiredPnachPath -Force
    $verifiedDestination = Get-SymbolicLinkDestinationPath -Item $verifiedItem
    if ($verifiedDestination -ne $CanonicalPnach) {
        throw "PNACH alias verification failed: $desiredPnachPath -> $verifiedDestination"
    }
}

[pscustomobject]@{
    Iso = $identity.Iso
    BootElf = $identity.BootElf
    PCSX2ElfCRC = $identity.CRC
    CanonicalPnach = $CanonicalPnach
    CheatsPnach = $targetPnach
    PnachStatus = $pnachStatus
    PreservedPnachAliases = @($preservedIdentities | ForEach-Object { Join-Path $cheatsDir $_.PnachName })
    RemovedPnachSymlinks = $removedPnachSymlinks
    EnabledCheats = $pnachState.EnabledCheats
}
