. (Join-Path $PSScriptRoot 'pcsx2_elf_crc.ps1')

$script:Na2IsoSectorSize = 2048

function Get-Na2DiscSerialFromBootPath {
    param([Parameter(Mandatory = $true)][string]$BootPath)

    $name = [IO.Path]::GetFileName($BootPath)
    if ($name -notmatch '^(?<prefix>[A-Za-z0-9]{4})_(?<first>[A-Za-z0-9]{3})\.(?<last>[A-Za-z0-9]{2})$') {
        throw "Could not derive a PS2 serial from boot executable: $BootPath"
    }
    return ("{0}-{1}{2}" -f $Matches.prefix, $Matches.first, $Matches.last).ToUpperInvariant()
}

function Read-Na2UInt32LE {
    param([byte[]]$Data, [int]$Offset)
    return [BitConverter]::ToUInt32($Data, $Offset)
}

function Read-Na2IsoDirectoryRecord {
    param([byte[]]$Data, [int]$Offset)

    $length = [int]$Data[$Offset]
    if ($length -eq 0) { return $null }

    $nameLength = [int]$Data[$Offset + 32]
    $nameBytes = [byte[]]::new($nameLength)
    [Array]::Copy($Data, $Offset + 33, $nameBytes, 0, $nameLength)

    if ($nameLength -eq 1 -and $nameBytes[0] -eq 0) {
        $name = '.'
    }
    elseif ($nameLength -eq 1 -and $nameBytes[0] -eq 1) {
        $name = '..'
    }
    else {
        $name = [Text.Encoding]::ASCII.GetString($nameBytes)
        $name = ($name -replace ';[0-9]+$', '')
    }

    [pscustomobject]@{
        Length = $length
        Extent = [uint32](Read-Na2UInt32LE -Data $Data -Offset ($Offset + 2))
        Size = [uint32](Read-Na2UInt32LE -Data $Data -Offset ($Offset + 10))
        Flags = [int]$Data[$Offset + 25]
        Name = $name
        IsDirectory = ((([int]$Data[$Offset + 25]) -band 0x02) -ne 0)
    }
}

function Read-Na2IsoExtent {
    param([IO.FileStream]$IsoStream, [uint32]$Extent, [uint32]$Size)

    $data = [byte[]]::new([int]$Size)
    $IsoStream.Position = [int64]$Extent * $script:Na2IsoSectorSize
    $readTotal = 0
    while ($readTotal -lt $data.Length) {
        $read = $IsoStream.Read($data, $readTotal, $data.Length - $readTotal)
        if ($read -le 0) { throw "Unexpected EOF while reading ISO extent $Extent." }
        $readTotal += $read
    }
    return $data
}

function Get-Na2IsoChildren {
    param([IO.FileStream]$IsoStream, [object]$DirRecord)

    $dirData = Read-Na2IsoExtent -IsoStream $IsoStream -Extent $DirRecord.Extent -Size $DirRecord.Size
    $children = @()
    $offset = 0
    while ($offset -lt $dirData.Length) {
        $length = [int]$dirData[$offset]
        if ($length -eq 0) { $offset++; continue }

        $record = Read-Na2IsoDirectoryRecord -Data $dirData -Offset $offset
        $offset += $length
        if ($null -ne $record -and $record.Name -ne '.' -and $record.Name -ne '..') {
            $children += $record
        }
    }
    return $children
}

function Find-Na2IsoPath {
    param([IO.FileStream]$IsoStream, [object]$RootRecord, [string]$Path)

    $parts = @($Path -split '[\/]' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $current = $RootRecord
    foreach ($part in $parts) {
        if (-not $current.IsDirectory) { return $null }
        $next = Get-Na2IsoChildren -IsoStream $IsoStream -DirRecord $current |
            Where-Object { $_.Name -ieq $part } |
            Select-Object -First 1
        if ($null -eq $next) { return $null }
        $current = $next
    }
    return $current
}

function Get-Na2IsoPcsx2Identity {
    param([Parameter(Mandatory = $true)][string]$Path)

    $resolvedPath = (Resolve-Path -LiteralPath $Path).Path
    $iso = [IO.File]::OpenRead($resolvedPath)
    try {
        $pvd = [byte[]]::new($script:Na2IsoSectorSize)
        $iso.Position = 16 * $script:Na2IsoSectorSize
        [void]$iso.Read($pvd, 0, $pvd.Length)

        $magic = [Text.Encoding]::ASCII.GetString($pvd, 1, 5)
        if ($pvd[0] -ne 1 -or $magic -ne 'CD001') {
            throw 'Primary Volume Descriptor not found at sector 16.'
        }

        $rootRecord = Read-Na2IsoDirectoryRecord -Data $pvd -Offset 156
        $systemRecord = Find-Na2IsoPath -IsoStream $iso -RootRecord $rootRecord -Path 'SYSTEM.CNF'
        if ($null -eq $systemRecord) { throw 'SYSTEM.CNF not found in ISO.' }

        $systemBytes = Read-Na2IsoExtent -IsoStream $iso -Extent $systemRecord.Extent -Size $systemRecord.Size
        $systemText = [Text.Encoding]::ASCII.GetString($systemBytes)
        $bootLine = ($systemText -split "`r?`n" | Where-Object { $_ -match '^\s*BOOT2?\s*=' } | Select-Object -First 1)
        if ([string]::IsNullOrWhiteSpace($bootLine)) { throw 'Boot line not found in SYSTEM.CNF.' }

        $bootPath = (($bootLine -replace '^\s*BOOT2?\s*=\s*', '') -replace '^\s*cdrom0?:\\?', '' -replace ';[0-9]+\s*$', '').Trim()
        $bootPath = $bootPath -replace '\\', '/'
        $serial = Get-Na2DiscSerialFromBootPath -BootPath $bootPath

        $elfRecord = Find-Na2IsoPath -IsoStream $iso -RootRecord $rootRecord -Path $bootPath
        if ($null -eq $elfRecord) { throw "Boot ELF not found in ISO: $bootPath" }

        $elfBytes = Read-Na2IsoExtent -IsoStream $iso -Extent $elfRecord.Extent -Size $elfRecord.Size
        $crc = Get-Pcsx2ElfCrc -Bytes $elfBytes
    }
    finally {
        $iso.Dispose()
    }

    [pscustomobject]@{
        Iso = $resolvedPath
        BootElf = $bootPath
        Serial = $serial
        CRC = $crc
        PnachName = "${serial}_${crc}.pnach"
        GameSettingsName = "${serial}_${crc}.ini"
    }
}
