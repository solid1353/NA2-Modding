param(
    [string]$IsoPath = "",
    [string]$CanonicalPnach = "",
    [string]$Serial = "SLPS-25837"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

function Get-Pcsx2ElfCrcFromBytes {
    param([byte[]]$Bytes)

    [uint32]$crc = 0
    $wordCount = [int]([math]::Floor($Bytes.Length / 4))
    for ($i = 0; $i -lt $wordCount; $i++) {
        $offset = $i * 4
        [uint32]$word =
            [uint32]$Bytes[$offset] -bor
            ([uint32]$Bytes[$offset + 1] -shl 8) -bor
            ([uint32]$Bytes[$offset + 2] -shl 16) -bor
            ([uint32]$Bytes[$offset + 3] -shl 24)
        $crc = $crc -bxor $word
    }
    return ('{0:X8}' -f $crc)
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if ([string]::IsNullOrWhiteSpace($IsoPath)) {
    $isos = @(Get-ChildItem -File -LiteralPath (Join-Path $root "build") -Filter "*.iso")
    if ($isos.Count -ne 1) {
        throw "Expected exactly one ISO in build/. Found $($isos.Count). Pass -IsoPath explicitly."
    }
    $IsoPath = $isos[0].FullName
}

$IsoPath = (Resolve-Path -LiteralPath $IsoPath).Path
if ([string]::IsNullOrWhiteSpace($CanonicalPnach)) {
    $CanonicalPnach = Join-Path $root "cheats\SLPS-25837_C0659AD1.pnach"
    & python -B (Join-Path $root "na2_patcher\modules\pnach\render.py") `
        --workspace $root `
        --output "cheats/SLPS-25837_C0659AD1.pnach"
    if ($LASTEXITCODE -ne 0) {
        throw "PNACH section rendering failed (exit $LASTEXITCODE)."
    }
}
$CanonicalPnach = (Resolve-Path -LiteralPath $CanonicalPnach).Path
$cheatsDir = Split-Path -Parent $CanonicalPnach

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

    $elfRecord = Find-IsoPath -IsoStream $iso -RootRecord $rootRecord -Path $bootPath
    if ($null -eq $elfRecord) { throw "Boot ELF not found in ISO: $bootPath" }

    $elfBytes = Read-IsoExtent -IsoStream $iso -Extent $elfRecord.Extent -Size $elfRecord.Size
    $crc = Get-Pcsx2ElfCrcFromBytes -Bytes $elfBytes
}
finally {
    $iso.Dispose()
}

$pnachName = "${Serial}_${crc}.pnach"
$targetPnach = Join-Path $cheatsDir $pnachName

$removedPnachSymlinks = @(
    Get-ChildItem -LiteralPath $cheatsDir -Filter "${Serial}_*.pnach" -Force |
        Where-Object {
            $_.FullName -ne $targetPnach -and
            $_.FullName -ne $CanonicalPnach -and
            $_.LinkType -eq "SymbolicLink"
        } |
        ForEach-Object {
            $name = $_.Name
            Remove-Item -LiteralPath $_.FullName -Force
            $name
        }
)

$targetItem = Get-Item -LiteralPath $targetPnach -Force -ErrorAction SilentlyContinue
if ($targetPnach -eq $CanonicalPnach) {
    $pnachStatus = "canonical PNACH already matches CRC"
}
elseif ($null -ne $targetItem) {
    if ($targetItem.LinkType -ne "SymbolicLink") {
        throw "Refusing to replace real PNACH file at CRC alias path: $targetPnach"
    }
    $existingDestination = $null
    try {
        $existingDestination = Get-SymbolicLinkDestinationPath -Item $targetItem
    }
    catch {
        # A dangling or unreadable symlink is safe to replace; a real file is not.
    }
    if ($existingDestination -ne $CanonicalPnach) {
        Remove-Item -LiteralPath $targetPnach -Force
        New-Item -ItemType SymbolicLink -Path $targetPnach -Target (Split-Path -Leaf $CanonicalPnach) | Out-Null
        $pnachStatus = "replaced incorrect symlink"
    }
    else {
        $pnachStatus = "verified symlink"
    }
}
else {
    New-Item -ItemType SymbolicLink -Path $targetPnach -Target (Split-Path -Leaf $CanonicalPnach) | Out-Null
    $pnachStatus = "created symlink"
}

if ($targetPnach -ne $CanonicalPnach) {
    $verifiedItem = Get-Item -LiteralPath $targetPnach -Force
    $verifiedDestination = Get-SymbolicLinkDestinationPath -Item $verifiedItem
    if ($verifiedDestination -ne $CanonicalPnach) {
        throw "PNACH alias verification failed: $targetPnach -> $verifiedDestination"
    }
}

[pscustomobject]@{
    Iso = $IsoPath
    BootElf = $bootPath
    PCSX2ElfCRC = $crc
    CanonicalPnach = $CanonicalPnach
    CheatsPnach = $targetPnach
    PnachStatus = $pnachStatus
    RemovedPnachSymlinks = $removedPnachSymlinks
}
