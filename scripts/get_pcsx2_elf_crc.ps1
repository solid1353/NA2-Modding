param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$ElfPath,

    [switch]$Detailed
)

$ErrorActionPreference = 'Stop'

$resolved = Resolve-Path -LiteralPath $ElfPath
$path = $resolved.ProviderPath

$bytes = [System.IO.File]::ReadAllBytes($path)
[uint32]$crc = 0

$wordCount = [int]([math]::Floor($bytes.Length / 4))
for ($i = 0; $i -lt $wordCount; $i++) {
    $offset = $i * 4
    [uint32]$word =
        [uint32]$bytes[$offset] -bor
        ([uint32]$bytes[$offset + 1] -shl 8) -bor
        ([uint32]$bytes[$offset + 2] -shl 16) -bor
        ([uint32]$bytes[$offset + 3] -shl 24)

    $crc = $crc -bxor $word
}

$crcText = '{0:X8}' -f $crc

if ($Detailed) {
    [pscustomobject]@{
        Path = $path
        Size = $bytes.Length
        WordCount = $wordCount
        IgnoredTrailingBytes = ($bytes.Length % 4)
        PCSX2ElfCRC = $crcText
    }
}
else {
    $crcText
}
