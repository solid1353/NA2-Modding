# Implements PCSX2's boot-ELF CRC calculation.
function Get-Pcsx2ElfCrc {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [byte[]]$Bytes
    )

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
