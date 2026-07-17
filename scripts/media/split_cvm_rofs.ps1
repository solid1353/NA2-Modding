param(
    [Parameter(Mandatory = $true)]
    [string]$CvmPath,

    [Parameter(Mandatory = $true)]
    [string]$OutIsoPath,

    [string]$OutHeaderPath = "",

    [Parameter(Mandatory = $true)]
    [string]$Password,

    [string]$RofsCryptSource = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

$sectorSize = 0x800

function Read-U32BE([byte[]]$Data, [int]$Offset) {
    return (([uint32]$Data[$Offset] -shl 24) -bor ([uint32]$Data[$Offset + 1] -shl 16) -bor ([uint32]$Data[$Offset + 2] -shl 8) -bor [uint32]$Data[$Offset + 3])
}

function Read-U64BE([byte[]]$Data, [int]$Offset) {
    [uint64]$v = 0
    for ($i = 0; $i -lt 8; $i++) {
        $v = ($v -shl 8) -bor [uint64]$Data[$Offset + $i]
    }
    return $v
}

function Read-U32LE([byte[]]$Data, [int]$Offset) {
    return ([uint32]$Data[$Offset] -bor ([uint32]$Data[$Offset + 1] -shl 8) -bor ([uint32]$Data[$Offset + 2] -shl 16) -bor ([uint32]$Data[$Offset + 3] -shl 24))
}

function Get-RofsPrimes([string]$SourcePath) {
    $text = Get-Content -LiteralPath $SourcePath -Raw
    $m = [regex]::Match($text, 'int\s+primes\s*\[\]\s*=\s*\{(?<body>.*?)\};', [Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $m.Success) { throw "Could not find primes[] in $SourcePath" }
    $nums = [regex]::Matches($m.Groups['body'].Value, '\d+') | ForEach-Object { [int]$_.Value }
    if ($nums.Count -lt 1024) { throw "Expected at least 1024 primes, found $($nums.Count)." }
    return [int[]]$nums
}

function Put-WordBE([uint16]$Val, [byte[]]$Buf, [int]$Offset) {
    $Buf[$Offset] = [byte](($Val -shr 8) -band 0xff)
    $Buf[$Offset + 1] = [byte]($Val -band 0xff)
}

function Put-DwordBE([uint32]$Val, [byte[]]$Buf, [int]$Offset) {
    $Buf[$Offset] = [byte](($Val -shr 24) -band 0xff)
    $Buf[$Offset + 1] = [byte](($Val -shr 16) -band 0xff)
    $Buf[$Offset + 2] = [byte](($Val -shr 8) -band 0xff)
    $Buf[$Offset + 3] = [byte]($Val -band 0xff)
}

function Calc-OneVal([byte[]]$Buf, [int]$Len, [uint16]$StartVal, [int[]]$Primes) {
    [uint16]$val = $StartVal
    for ($i = 0; $i -lt $Len; $i++) {
        $idxByte = ([int]$Buf[$i] + 128) % 256
        [int]$p = $Primes[$idxByte] * [int]$val
        $val = [uint16]$Primes[$p -band 0x3ff]
    }
    return $val
}

function Calc-HashVals([byte[]]$Buf, [int]$Len, [int[]]$Primes) {
    return @(
        (Calc-OneVal $Buf $Len 18973 $Primes),
        (Calc-OneVal $Buf $Len 21503 $Primes),
        (Calc-OneVal $Buf $Len 24001 $Primes)
    )
}

function Extra-Hash([byte[]]$Buf, [int[]]$Primes) {
    for ($i = 0; $i -lt 4; $i++) {
        $pair = [byte[]]::new(2)
        $pair[0] = $Buf[$i * 2]
        $pair[1] = $Buf[$i * 2 + 1]
        $vals = Calc-HashVals $pair 2 $Primes
        Put-WordBE ([uint16]$vals[0]) $Buf ($i * 2)
    }
}

function Get-KeyFromString([string]$Password, [int[]]$Primes) {
    [uint64]$sum = 0
    $chars = [Text.Encoding]::ASCII.GetBytes($Password)
    for ($k = 0; $k -lt $chars.Length; $k++) {
        $c = [uint64]$chars[$k]
        $sum = ($c * ($c + $sum)) -band 0xffffffffL
        for ($i = $k + 1; $i -lt $chars.Length; $i++) {
            $sum = ($sum + [uint64]$chars[$i]) -band 0xffffffffL
        }
    }

    [uint32]$seed = [uint32](([uint64]0x100001 * $sum) -band 0xffffffffL)
    $tmp = [byte[]]::new(4)
    Put-DwordBE $seed $tmp 0

    $key = [byte[]]::new(8)
    for ($j = 0; $j -lt 4; $j++) {
        $key[$j * 2] = $tmp[$j]
        $key[$j * 2 + 1] = $tmp[3 - $j]
    }
    Extra-Hash $key $Primes
    return $key
}

function Calc-Hash([uint32]$Seed, [int[]]$Primes) {
    $buf = [byte[]]::new(4)
    [uint32]$x = [uint32](([uint64]0x100001 * [uint64]$Seed) -band 0xffffffffL)
    Put-DwordBE $x $buf 0
    $vals = Calc-HashVals $buf 4 $Primes
    $hash = [byte[]]::new(4)
    Put-WordBE ([uint16]$vals[1]) $hash 0
    Put-WordBE ([uint16]$vals[2]) $hash 2
    return @{ Index = ([int]$vals[0] % 9); Hash = $hash }
}

$scrambles = @(
    '^03 .0 37 .4 .1 26 .2 15',
    '^12 .7 .5 23 00 .6 .4 31',
    '^.1 27 .6 12 35 .3 00 .4',
    '+23 .6 .0 .2 04 11 .7 35',
    '+.7 30 02 16 .4 .3 .5 21',
    '+.2 23 .6 07 .0 11 .4 35',
    '+03 .7^12 .6 .1 25 .0+34',
    ' .7^34 .3+21 .0 .2 15^06',
    ' .3^10 .6+04^32 .7 .1+25'
)

function Get-LocalKey([byte[]]$Key, [byte[]]$Hash, [int]$Index) {
    $scramble = $scrambles[$Index]
    $dst = [byte[]]::new(8)
    $p = 0
    $type = '^'
    for ($i = 0; $i -lt 8; $i++) {
        while ($p -lt $scramble.Length -and $scramble[$p] -eq ' ') { $p++ }
        if ($scramble[$p] -eq '^' -or $scramble[$p] -eq '+') {
            $type = $scramble[$p]
            $p++
        }
        $o1 = $scramble[$p]; $p++
        $o2 = $scramble[$p]; $p++
        [byte]$b = $Key[[int][string]$o2]
        if ($o1 -ne '.') {
            $h = $Hash[[int][string]$o1]
            if ($type -eq '^') {
                $b = [byte]($b -bxor $h)
            }
            else {
                $b = [byte](([int]$b + [int]$h) -band 0xff)
            }
        }
        $dst[$i] = $b
    }
    return $dst
}

function Decrypt-SectorInPlace([byte[]]$Buf, [int]$LogicalSector, [byte[]]$Key, [int[]]$Primes) {
    [int64]$seed = [int]$Key[5]
    for ($off = 0; $off -lt $Buf.Length; $off += 8) {
        $calc = Calc-Hash ([uint32](([int64]$LogicalSector * $seed) -band 0xffffffffL)) $Primes
        $localKey = Get-LocalKey $Key $calc.Hash $calc.Index
        $seed = $calc.Index + $off
        for ($i = 0; $i -lt 8; $i++) {
            $Buf[$off + $i] = [byte]($Buf[$off + $i] -bxor $localKey[$i])
            $seed = ([int64]$seed * [int64]$localKey[$i]) -band 0xffffffffL
        }
    }
}

function Read-CvmSector([IO.FileStream]$Stream, [int]$IsoSector, [int]$IsoStartSector, [int]$IsoZoneSector, [bool]$Decrypt, [byte[]]$Key, [int[]]$Primes) {
    $buf = [byte[]]::new($sectorSize)
    $physical = $IsoSector + $IsoStartSector
    $Stream.Position = [int64]$physical * $sectorSize
    $read = $Stream.Read($buf, 0, $buf.Length)
    if ($read -ne $buf.Length) { throw "Unexpected EOF reading physical sector $physical." }
    if ($Decrypt) {
        $logical = $IsoSector + $IsoZoneSector - $IsoStartSector
        Decrypt-SectorInPlace $buf $logical $Key $Primes
    }
    return $buf
}

function Get-DirRecord([byte[]]$Data, [int]$Offset) {
    $length = [int]$Data[$Offset]
    if ($length -eq 0) { return $null }
    $nameLength = [int]$Data[$Offset + 32]
    $nameBytes = [byte[]]::new($nameLength)
    [Array]::Copy($Data, $Offset + 33, $nameBytes, 0, $nameLength)
    if ($nameLength -eq 1 -and $nameBytes[0] -eq 0) { $name = '.' }
    elseif ($nameLength -eq 1 -and $nameBytes[0] -eq 1) { $name = '..' }
    else { $name = ([Text.Encoding]::ASCII.GetString($nameBytes) -replace ';[0-9]+$', '') }
    return [pscustomobject]@{
        Length = $length
        Extent = Read-U32LE $Data ($Offset + 2)
        Size = Read-U32LE $Data ($Offset + 10)
        ExtAttrLength = [int]$Data[$Offset + 1]
        Flags = [int]$Data[$Offset + 25]
        Name = $name
        IsDirectory = ((([int]$Data[$Offset + 25]) -band 0x02) -ne 0)
    }
}

function Parse-Directory([IO.FileStream]$Stream, [int]$Extent, [int]$Size, [int]$IsoStartSector, [int]$IsoZoneSector, [byte[]]$Key, [int[]]$Primes, [ref]$EndDirSector) {
    $dirSector = $Extent
    $remaining = $Size
    while ($remaining -gt 0) {
        $sec = Read-CvmSector $Stream $dirSector $IsoStartSector $IsoZoneSector $true $Key $Primes
        $chunk = [Math]::Min($sectorSize, $remaining)
        $remaining -= $chunk
        $offset = 0
        while ($offset -lt $chunk) {
            $len = [int]$sec[$offset]
            if ($len -eq 0) { break }
            if ($len -lt 0x22) { throw "Bad ISO directory record length $len in sector $dirSector." }
            $rec = Get-DirRecord $sec $offset
            if ($rec.IsDirectory -and $rec.Name -ne '.' -and $rec.Name -ne '..') {
                Parse-Directory $Stream ([int]($rec.Extent + $rec.ExtAttrLength)) ([int]$rec.Size) $IsoStartSector $IsoZoneSector $Key $Primes $EndDirSector
            }
            $offset += $len
        }
        $dirSector++
    }
    if ($EndDirSector.Value -lt $dirSector) { $EndDirSector.Value = $dirSector }
}

if ([string]::IsNullOrWhiteSpace($RofsCryptSource)) {
    $RofsCryptSource = Join-Path $projectPaths.utils 'old\CVM Parser\rofs_crypt.cpp'
}

$CvmPath = (Resolve-Path -LiteralPath $CvmPath).Path
if (Test-Path -LiteralPath $OutIsoPath) { throw "Output ISO already exists: $OutIsoPath" }
if (-not [string]::IsNullOrWhiteSpace($OutHeaderPath) -and (Test-Path -LiteralPath $OutHeaderPath)) { throw "Output header already exists: $OutHeaderPath" }

$primes = Get-RofsPrimes $RofsCryptSource
$key = Get-KeyFromString $Password $primes

$stream = [IO.File]::OpenRead($CvmPath)
$out = $null
$hdrOut = $null
try {
    $chunk = [byte[]]::new(12)
    [void]$stream.Read($chunk, 0, 12)
    if ([Text.Encoding]::ASCII.GetString($chunk, 0, 4) -ne 'CVMH') { throw 'CVMH chunk not found at start.' }
    $cvmhLen = [int64](Read-U64BE $chunk 4)
    $cvmh = [byte[]]::new([int]$cvmhLen)
    [void]$stream.Read($cvmh, 0, $cvmh.Length)

    $flags = Read-U32BE $cvmh 0x24
    $isoStartSector = [int](Read-U32BE $cvmh 0x7c)
    if (($flags -band 0x10) -eq 0) { Write-Warning 'CVM does not have encrypted TOC flag set.' }

    $zoneHeader = [byte[]]::new(12)
    [void]$stream.Read($zoneHeader, 0, 12)
    if ([Text.Encoding]::ASCII.GetString($zoneHeader, 0, 4) -ne 'ZONE') { throw 'ZONE chunk not found after CVMH.' }
    $zonePayloadStart = $stream.Position
    $zoneFixed = [byte[]]::new($sectorSize)
    [void]$stream.Read($zoneFixed, 0, $zoneFixed.Length)
    $isoZoneSector = [int](Read-U32BE $zoneFixed 0x20)
    $isoLength = [int64](Read-U64BE $zoneFixed 0x24)
    $sectorCount = [int]($isoLength / $sectorSize)

    $pvd = Read-CvmSector $stream 16 $isoStartSector $isoZoneSector $true $key $primes
    if ($pvd[0] -ne 1 -or [Text.Encoding]::ASCII.GetString($pvd, 1, 5) -ne 'CD001') {
        throw "Bad PVD after decryption; password is probably wrong."
    }

    $root = Get-DirRecord $pvd 156
    $endDirSector = 0
    Parse-Directory $stream ([int]($root.Extent + $root.ExtAttrLength)) ([int]$root.Size) $isoStartSector $isoZoneSector $key $primes ([ref]$endDirSector)

    $outDir = Split-Path -Parent $OutIsoPath
    if (-not [string]::IsNullOrWhiteSpace($outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
    $out = [IO.File]::Create($OutIsoPath)
    for ($i = 0; $i -lt $sectorCount; $i++) {
        $decrypt = ($i -ge 16 -and $i -lt $endDirSector)
        $sec = Read-CvmSector $stream $i $isoStartSector $isoZoneSector $decrypt $key $primes
        $out.Write($sec, 0, $sec.Length)
    }

    if (-not [string]::IsNullOrWhiteSpace($OutHeaderPath)) {
        $hdrDir = Split-Path -Parent $OutHeaderPath
        if (-not [string]::IsNullOrWhiteSpace($hdrDir)) { New-Item -ItemType Directory -Force -Path $hdrDir | Out-Null }
        $hdrOut = [IO.File]::Create($OutHeaderPath)
        $stream.Position = 0
        $headerBytes = [byte[]]::new($isoStartSector * $sectorSize)
        [void]$stream.Read($headerBytes, 0, $headerBytes.Length)
        $hdrOut.Write($headerBytes, 0, $headerBytes.Length)
    }

    [pscustomobject]@{
        Cvm = $CvmPath
        OutIso = $OutIsoPath
        OutHeader = $OutHeaderPath
        Password = $Password
        KeyHex = (($key | ForEach-Object { '{0:X2}' -f $_ }) -join '')
        IsoStartSector = $isoStartSector
        IsoZoneSector = $isoZoneSector
        IsoLength = $isoLength
        SectorCount = $sectorCount
        EndTocSector = $endDirSector
    }
}
finally {
    if ($null -ne $hdrOut) { $hdrOut.Dispose() }
    if ($null -ne $out) { $out.Dispose() }
    $stream.Dispose()
}
