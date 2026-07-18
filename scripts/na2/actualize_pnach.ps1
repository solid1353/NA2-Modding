param(
    [string]$IsoPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'pnach_state.ps1')
. (Join-Path $PSScriptRoot 'pcsx2_elf_crc.ps1')
$projectPaths = Get-Na2ProjectPaths
$CanonicalPnach = Join-Path $projectPaths.pcsx2_files 'SLPS-25837_C0659AD1.pnach'
$ManagedSerials = @('SLPS-25837', 'SLPS-22228')

$sectorSize = 2048

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

function Get-DiscSerialFromBootPath {
    param([Parameter(Mandatory = $true)][string]$BootPath)

    $name = [IO.Path]::GetFileName($BootPath)
    if ($name -notmatch '^(?<prefix>[A-Za-z]{4})_(?<first>[0-9]{3})\.(?<last>[0-9]{2})$') {
        throw "Could not derive a PS2 serial from boot executable: $BootPath"
    }
    return ("{0}-{1}{2}" -f $Matches.prefix, $Matches.first, $Matches.last).ToUpperInvariant()
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

function Read-UInt32LE {
    param([byte[]]$Data, [int]$Offset)
    return [BitConverter]::ToUInt32($Data, $Offset)
}

function Read-DirectoryRecord {
    param([byte[]]$Data, [int]$Offset)

    $length = [int]$Data[$Offset]
    if ($length -eq 0) { return $null }

    $nameLength = [int]$Data[$Offset + 32]
    $nameBytes = [byte[]]::new($nameLength)
    [Array]::Copy($Data, $Offset + 33, $nameBytes, 0, $nameLength)

    if ($nameLength -eq 1 -and $nameBytes[0] -eq 0) {
        $name = "."
    }
    elseif ($nameLength -eq 1 -and $nameBytes[0] -eq 1) {
        $name = ".."
    }
    else {
        $name = [Text.Encoding]::ASCII.GetString($nameBytes)
        $name = ($name -replace ';[0-9]+$', '')
    }

    [pscustomobject]@{
        Length = $length
        Extent = [uint32](Read-UInt32LE -Data $Data -Offset ($Offset + 2))
        Size = [uint32](Read-UInt32LE -Data $Data -Offset ($Offset + 10))
        Flags = [int]$Data[$Offset + 25]
        Name = $name
        IsDirectory = ((([int]$Data[$Offset + 25]) -band 0x02) -ne 0)
    }
}

function Read-IsoExtent {
    param([IO.FileStream]$IsoStream, [uint32]$Extent, [uint32]$Size)

    $data = [byte[]]::new([int]$Size)
    $IsoStream.Position = [int64]$Extent * $sectorSize
    $readTotal = 0
    while ($readTotal -lt $data.Length) {
        $read = $IsoStream.Read($data, $readTotal, $data.Length - $readTotal)
        if ($read -le 0) { throw "Unexpected EOF while reading ISO extent $Extent." }
        $readTotal += $read
    }
    return $data
}

function Get-IsoChildren {
    param([IO.FileStream]$IsoStream, [object]$DirRecord)

    $dirData = Read-IsoExtent -IsoStream $IsoStream -Extent $DirRecord.Extent -Size $DirRecord.Size
    $children = @()
    $offset = 0
    while ($offset -lt $dirData.Length) {
        $length = [int]$dirData[$offset]
        if ($length -eq 0) { $offset++; continue }

        $record = Read-DirectoryRecord -Data $dirData -Offset $offset
        $offset += $length
        if ($null -ne $record -and $record.Name -ne "." -and $record.Name -ne "..") {
            $children += $record
        }
    }
    return $children
}

function Find-IsoPath {
    param([IO.FileStream]$IsoStream, [object]$RootRecord, [string]$Path)

    $parts = @($Path -split '[\/]' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $current = $RootRecord
    foreach ($part in $parts) {
        if (-not $current.IsDirectory) { return $null }
        $next = Get-IsoChildren -IsoStream $IsoStream -DirRecord $current |
            Where-Object { $_.Name -ieq $part } |
            Select-Object -First 1
        if ($null -eq $next) { return $null }
        $current = $next
    }
    return $current
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
    $IsoPath = Join-Path $projectPaths.build 'Current.iso'
    if (-not (Test-Path -LiteralPath $IsoPath -PathType Leaf)) {
        throw "Default build ISO does not exist: $IsoPath. Pass -IsoPath explicitly."
    }
}
$IsoPath = (Resolve-Path -LiteralPath $IsoPath).Path

$iso = [IO.File]::OpenRead($IsoPath)
try {
    $pvd = [byte[]]::new($sectorSize)
    $iso.Position = 16 * $sectorSize
    [void]$iso.Read($pvd, 0, $pvd.Length)

    $magic = [Text.Encoding]::ASCII.GetString($pvd, 1, 5)
    if ($pvd[0] -ne 1 -or $magic -ne "CD001") {
        throw "Primary Volume Descriptor not found at sector 16."
    }

    $rootRecord = Read-DirectoryRecord -Data $pvd -Offset 156
    $systemRecord = Find-IsoPath -IsoStream $iso -RootRecord $rootRecord -Path "SYSTEM.CNF"
    if ($null -eq $systemRecord) { throw "SYSTEM.CNF not found in ISO." }

    $systemText = [Text.Encoding]::ASCII.GetString((Read-IsoExtent -IsoStream $iso -Extent $systemRecord.Extent -Size $systemRecord.Size))
    $bootLine = ($systemText -split "`r?`n" | Where-Object { $_ -match '^\s*BOOT2?\s*=' } | Select-Object -First 1)
    if ([string]::IsNullOrWhiteSpace($bootLine)) { throw "Boot line not found in SYSTEM.CNF." }

    $bootPath = (($bootLine -replace '^\s*BOOT2?\s*=\s*', '') -replace '^\s*cdrom0?:\\?', '' -replace ';[0-9]+\s*$', '').Trim()
    $bootPath = $bootPath -replace '\\', '/'
    $Serial = Get-DiscSerialFromBootPath -BootPath $bootPath
    if ($Serial -notin $ManagedSerials) {
        throw "Boot serial is not managed by this project: $Serial"
    }

    $elfRecord = Find-IsoPath -IsoStream $iso -RootRecord $rootRecord -Path $bootPath
    if ($null -eq $elfRecord) { throw "Boot ELF not found in ISO: $bootPath" }

    $elfBytes = Read-IsoExtent -IsoStream $iso -Extent $elfRecord.Extent -Size $elfRecord.Size
    $crc = Get-Pcsx2ElfCrc -Bytes $elfBytes
}
finally {
    $iso.Dispose()
}

$pnachName = "${Serial}_${crc}.pnach"
$targetPnach = Join-Path $cheatsDir $pnachName

$removedPnachSymlinks = @(
    Get-ManagedPnachSymlinks `
        -CheatsDirectory $cheatsDir `
        -CanonicalPnach $CanonicalPnach `
        -Serials $ManagedSerials |
        Where-Object {
            $_.FullName -ne $targetPnach
        } |
        ForEach-Object {
            $name = $_.Name
            Remove-Item -LiteralPath $_.FullName -Force
            $name
        }
)

$targetItem = Get-Item -LiteralPath $targetPnach -Force -ErrorAction SilentlyContinue
if ($null -ne $targetItem) {
    if ($targetItem.LinkType -ne "SymbolicLink") {
        throw "Refusing to replace real PNACH file at CRC alias path: $targetPnach"
    }
    $existingDestination = Get-SymbolicLinkDestinationPath -Item $targetItem
    if ($existingDestination -ne $CanonicalPnach) {
        throw "Refusing to replace unmanaged PNACH symlink at CRC alias path: $targetPnach -> $existingDestination"
    }
    $pnachStatus = "verified symlink"
}
else {
    New-Item -ItemType SymbolicLink -Path $targetPnach -Target $canonicalLinkTarget | Out-Null
    $pnachStatus = "created symlink"
}

$verifiedItem = Get-Item -LiteralPath $targetPnach -Force
$verifiedDestination = Get-SymbolicLinkDestinationPath -Item $verifiedItem
if ($verifiedDestination -ne $CanonicalPnach) {
    throw "PNACH alias verification failed: $targetPnach -> $verifiedDestination"
}

[pscustomobject]@{
    Iso = $IsoPath
    BootElf = $bootPath
    PCSX2ElfCRC = $crc
    CanonicalPnach = $CanonicalPnach
    CheatsPnach = $targetPnach
    PnachStatus = $pnachStatus
    RemovedPnachSymlinks = $removedPnachSymlinks
    EnabledCheats = $pnachState.EnabledCheats
}
