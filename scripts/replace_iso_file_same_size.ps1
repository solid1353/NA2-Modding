param(
    [Parameter(Mandatory = $true)] [string]$IsoPath,
    [Parameter(Mandatory = $true)] [string]$IsoFilePath,
    [Parameter(Mandatory = $true)] [string]$ReplacementPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot 'project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$sectorSize = 2048

function Read-UInt32LE([byte[]]$Data, [int]$Offset) {
    [BitConverter]::ToUInt32($Data, $Offset)
}

function Read-DirectoryRecord([byte[]]$Data, [int]$Offset) {
    $length = [int]$Data[$Offset]
    if ($length -eq 0) { return $null }
    $nameLength = [int]$Data[$Offset + 32]
    $nameBytes = [byte[]]::new($nameLength)
    [Array]::Copy($Data, $Offset + 33, $nameBytes, 0, $nameLength)
    if ($nameLength -eq 1 -and $nameBytes[0] -eq 0) { $name = "." }
    elseif ($nameLength -eq 1 -and $nameBytes[0] -eq 1) { $name = ".." }
    else { $name = ([Text.Encoding]::ASCII.GetString($nameBytes) -replace ';[0-9]+$', '') }
    [pscustomobject]@{
        Length = $length
        Extent = [uint32](Read-UInt32LE $Data ($Offset + 2))
        Size = [uint32](Read-UInt32LE $Data ($Offset + 10))
        Name = $name
        IsDirectory = ((([int]$Data[$Offset + 25]) -band 0x02) -ne 0)
    }
}

function Read-IsoExtent([IO.FileStream]$Iso, [uint32]$Extent, [uint32]$Size) {
    $data = [byte[]]::new([int]$Size)
    $Iso.Position = [int64]$Extent * $sectorSize
    $total = 0
    while ($total -lt $data.Length) {
        $read = $Iso.Read($data, $total, $data.Length - $total)
        if ($read -le 0) { throw "Unexpected EOF while reading extent $Extent" }
        $total += $read
    }
    $data
}

function Get-IsoChildren([IO.FileStream]$Iso, [object]$DirRecord) {
    $dirData = Read-IsoExtent $Iso $DirRecord.Extent $DirRecord.Size
    $children = @()
    $offset = 0
    while ($offset -lt $dirData.Length) {
        $length = [int]$dirData[$offset]
        if ($length -eq 0) { $offset++; continue }
        $record = Read-DirectoryRecord $dirData $offset
        $offset += $length
        if ($null -ne $record -and $record.Name -ne "." -and $record.Name -ne "..") { $children += $record }
    }
    $children
}

function Find-IsoPath([IO.FileStream]$Iso, [object]$RootRecord, [string]$Path) {
    $current = $RootRecord
    foreach ($part in ($Path -split '[\\/]' | Where-Object { $_ })) {
        if (-not $current.IsDirectory) { return $null }
        $current = @(Get-IsoChildren $Iso $current | Where-Object { $_.Name -ieq $part } | Select-Object -First 1)[0]
        if ($null -eq $current) { return $null }
    }
    $current
}

$isoResolved = (Resolve-Path -LiteralPath $IsoPath).Path
$replacementResolved = (Resolve-Path -LiteralPath $ReplacementPath).Path
$replacementBytes = [IO.File]::ReadAllBytes($replacementResolved)

$iso = [IO.File]::Open($isoResolved, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
try {
    $pvd = [byte[]]::new($sectorSize)
    $iso.Position = 16 * $sectorSize
    [void]$iso.Read($pvd, 0, $pvd.Length)
    if ($pvd[0] -ne 1 -or [Text.Encoding]::ASCII.GetString($pvd, 1, 5) -ne "CD001") { throw "Primary Volume Descriptor not found." }
    $rootRecord = Read-DirectoryRecord $pvd 156
    $record = Find-IsoPath $iso $rootRecord $IsoFilePath
    if ($null -eq $record -or $record.IsDirectory) { throw "ISO file not found: $IsoFilePath" }
    if ($replacementBytes.Length -ne [int]$record.Size) {
        throw "Replacement size $($replacementBytes.Length) does not match ISO file size $($record.Size)."
    }
    $byteOffset = [int64]$record.Extent * $sectorSize
    $iso.Position = $byteOffset
    $iso.Write($replacementBytes, 0, $replacementBytes.Length)
    $iso.Flush()
    [pscustomobject]@{
        Iso = $isoResolved
        IsoFilePath = $IsoFilePath
        Replacement = $replacementResolved
        Size = $record.Size
        Extent = $record.Extent
        IsoByteOffset = "0x{0:X}" -f $byteOffset
    }
}
finally {
    $iso.Dispose()
}
