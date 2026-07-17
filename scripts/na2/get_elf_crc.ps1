param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$ElfPath,

    [switch]$Detailed
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'pcsx2_elf_crc.ps1')

$resolved = Resolve-Path -LiteralPath $ElfPath
$path = $resolved.ProviderPath

$bytes = [System.IO.File]::ReadAllBytes($path)
$wordCount = [int]([math]::Floor($bytes.Length / 4))
$crcText = Get-Pcsx2ElfCrc -Bytes $bytes

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
