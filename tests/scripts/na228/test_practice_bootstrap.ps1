[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths -ManifestPath (Join-Path $repository 'paths.json')

function Assert-PracticeBootstrapTest {
    param(
        [Parameter(Mandatory)][bool]$Condition,
        [Parameter(Mandatory)][string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function Read-ActivePatches {
    param([Parameter(Mandatory)][string]$Path)

    $patches = @{}
    foreach ($line in ([IO.File]::ReadAllText($Path) -split "\r?\n")) {
        $match = [regex]::Match(
            $line,
            '^patch=1,EE,([0-9A-Fa-f]{8}),word,([0-9A-Fa-f]{8})(?:\s|$)'
        )
        if (-not $match.Success) {
            continue
        }
        $address = [Convert]::ToUInt32($match.Groups[1].Value, 16)
        $word = [Convert]::ToUInt32($match.Groups[2].Value, 16)
        Assert-PracticeBootstrapTest (
            -not $patches.ContainsKey($address)
        ) ("PNACH writes 0x{0:X8} more than once: {1}" -f $address, $Path)
        $patches[$address] = $word
    }
    return $patches
}

function Assert-CodeBlock {
    param(
        [Parameter(Mandatory)][hashtable]$Patches,
        [Parameter(Mandatory)][uint32]$Start,
        [Parameter(Mandatory)][uint32]$End,
        [Parameter(Mandatory)][uint32]$MutableState,
        [Parameter(Mandatory)][hashtable]$ExpectedAbsoluteTargets,
        [Parameter(Mandatory)][string]$Label
    )

    $expectedAddresses = @(
        for ($address = $Start; $address -le $End; $address += 4) {
            [uint32]$address
        }
    )
    $actualAddresses = @(
        $Patches.Keys |
            Where-Object { $_ -ge $Start -and $_ -le $End } |
            Sort-Object
    )
    Assert-PracticeBootstrapTest (
        ($actualAddresses -join ',') -ceq ($expectedAddresses -join ',')
    ) ("The $Label wrapper is not a contiguous 0x{0:X8}..0x{1:X8} block." -f $Start, $End)
    Assert-PracticeBootstrapTest (
        -not $Patches.ContainsKey($MutableState)
    ) ("The $Label PNACH made mutable one-shot state an every-frame patch.")

    foreach ($address in $expectedAddresses) {
        $word = [uint32]$Patches[$address]
        $opcode = ($word -shr 26) -band 0x3F
        if ($opcode -in 2, 3) {
            $target = [uint32](($word -band 0x03FFFFFF) -shl 2)
            Assert-PracticeBootstrapTest (
                $ExpectedAbsoluteTargets.ContainsKey($address) -and
                $ExpectedAbsoluteTargets[$address] -eq $target
            ) ("Unexpected absolute jump in $Label at 0x{0:X8} to 0x{1:X8}." -f $address, $target)
        }
        if ($opcode -in 1, 4, 5, 6, 7) {
            $immediate = [int]($word -band 0xFFFF)
            if ($immediate -ge 0x8000) {
                $immediate -= 0x10000
            }
            $target = [uint32]($address + 4 + ($immediate * 4))
            Assert-PracticeBootstrapTest (
                $target -ge $Start -and $target -le $MutableState
            ) ("Branch in $Label at 0x{0:X8} escapes the wrapper to 0x{1:X8}." -f $address, $target)
        }
    }
    Assert-PracticeBootstrapTest (
        $ExpectedAbsoluteTargets.Count -eq @(
            $expectedAddresses |
                Where-Object {
                    (([uint32]$Patches[$_] -shr 26) -band 0x3F) -in 2, 3
                }
        ).Count
    ) ("The $Label PNACH absolute-jump inventory changed.")
}

function Assert-PatchWords {
    param(
        [Parameter(Mandatory)][hashtable]$Patches,
        [Parameter(Mandatory)][hashtable]$Expected,
        [Parameter(Mandatory)][string]$Label
    )

    foreach ($entry in $Expected.GetEnumerator()) {
        Assert-PracticeBootstrapTest (
            $Patches.ContainsKey([uint32]$entry.Key) -and
            [uint32]$Patches[[uint32]$entry.Key] -eq [uint32]$entry.Value
        ) (
            "The $Label route-contract word at 0x{0:X8} is not 0x{1:X8}." -f
                [uint32]$entry.Key,
                [uint32]$entry.Value
        )
    }
}

$na228Profile = Join-Path $paths.repository 'launch_profiles\practice\NA228.pnach'
$nun5Profile = Join-Path $paths.repository 'launch_profiles\practice\NUN5.pnach'
$cachedIso = Get-ChildItem -LiteralPath $paths.build -File -Filter 'NA v2.28 - *.iso' |
    Select-Object -First 1
Assert-PracticeBootstrapTest ($null -ne $cachedIso) 'No cached NA2 build is available.'
$cachedSelector = [IO.Path]::GetFileNameWithoutExtension($cachedIso.Name)
$practice = & (Join-Path $repository 'launch_profiles\practice\launch.ps1') `
    -Arguments BNARUTO `
    -Games @($cachedIso.FullName, 'nun5') `
    -ProjectRoot $repository
Assert-PracticeBootstrapTest (
    $practice.MovesetCaseId -ceq 'bNaruto' -and
    $practice.PnachByGame[$cachedSelector] -ceq $na228Profile -and
    $practice.PnachByGame['nun5'] -ceq $nun5Profile
) 'Practice launch configuration did not resolve PNACH files from its launch-profile assets.'
$na228Patches = Read-ActivePatches -Path $na228Profile
$nun5Patches = Read-ActivePatches -Path $nun5Profile

foreach ($defaultPnach in @(
    [string]$paths.games.Entries.PSObject.Properties['NUN5'].Value.Config.cheats
)) {
    Assert-PracticeBootstrapTest (
        [IO.File]::ReadAllText($defaultPnach) -cnotmatch
            '(?m)^\[\+Practice bootstrap(?: configuration)?\]$'
    ) "Default PNACH retained the Practice bootstrap: $defaultPnach"
}

foreach ($address in 0x001ED600, 0x001ED604, 0x001ED608) {
    Assert-PracticeBootstrapTest (
        -not $na228Patches.ContainsKey([uint32]$address)
    ) ("NA2.28 PNACH retained inline-owned configuration word 0x{0:X8}." -f $address)
}
foreach ($address in 0x003D0FF0, 0x003D0FF4, 0x003D0FF8) {
    Assert-PracticeBootstrapTest (
        -not $nun5Patches.ContainsKey([uint32]$address)
    ) ("NUN5 PNACH retained inline-owned configuration word 0x{0:X8}." -f $address)
}

Assert-PracticeBootstrapTest (
    @(
        $na228Patches.Keys |
            Where-Object { $_ -ge 0x001ED60C -and $_ -lt 0x001ED6C0 }
    ).Count -eq 0
) 'The NA2.28 PNACH crossed into the next native function.'

$na228AbsoluteTargets = @{
    ([uint32]0x001ED4B4) = [uint32]0x001ED59C
    ([uint32]0x001ED4D4) = [uint32]0x001EDB70
    ([uint32]0x001ED57C) = [uint32]0x001FE200
    ([uint32]0x001ED58C) = [uint32]0x0020DC40
    ([uint32]0x001ED594) = [uint32]0x0020DCF8
    ([uint32]0x001ED5B8) = [uint32]0x001F4A80
    ([uint32]0x001ED5CC) = [uint32]0x001F4AF0
    ([uint32]0x001ED5E8) = [uint32]0x002005B0
}
Assert-CodeBlock `
    -Patches $na228Patches `
    -Start 0x001ED450 `
    -End 0x001ED5F8 `
    -MutableState 0x001ED5FC `
    -ExpectedAbsoluteTargets $na228AbsoluteTargets `
    -Label 'NA2.28'

$nun5AbsoluteTargets = @{
    ([uint32]0x003D0EA4) = [uint32]0x003D0F8C
    ([uint32]0x003D0EC4) = [uint32]0x001F3F40
    ([uint32]0x003D0F6C) = [uint32]0x00204ED0
    ([uint32]0x003D0F7C) = [uint32]0x00214CCC
    ([uint32]0x003D0F84) = [uint32]0x00214DE0
    ([uint32]0x003D0FA8) = [uint32]0x001FB3C0
    ([uint32]0x003D0FBC) = [uint32]0x001FB430
    ([uint32]0x003D0FD8) = [uint32]0x00207390
}
Assert-CodeBlock `
    -Patches $nun5Patches `
    -Start 0x003D0E40 `
    -End 0x003D0FE8 `
    -MutableState 0x003D0FEC `
    -ExpectedAbsoluteTargets $nun5AbsoluteTargets `
    -Label 'NUN5'

Assert-PatchWords -Patches $na228Patches -Label 'NA2.28' -Expected @{
    ([uint32]0x001ED55C) = [uint32]0x7FB20020
    ([uint32]0x001ED560) = [uint32]0x7FB10010
    ([uint32]0x001ED564) = [uint32]0x7FB00000
    ([uint32]0x001ED568) = [uint32]0x0100902D
    ([uint32]0x001ED56C) = [uint32]0x0120882D
}
Assert-PatchWords -Patches $nun5Patches -Label 'NUN5' -Expected @{
    ([uint32]0x003D0F4C) = [uint32]0x7FB20020
    ([uint32]0x003D0F50) = [uint32]0x7FB10010
    ([uint32]0x003D0F54) = [uint32]0x7FB00000
    ([uint32]0x003D0F58) = [uint32]0x0100902D
    ([uint32]0x003D0F5C) = [uint32]0x0120882D
}

$cleanElf = Join-Path $paths.source_na2 'SLPS_258.37'
$cleanBytes = [IO.File]::ReadAllBytes($cleanElf)
$cleanGuards = @{
    ([uint32]0x001E9AF8) = [uint32]0x24020004
    ([uint32]0x001E9AFC) = [uint32]0xAE020008L
    ([uint32]0x001E9B00) = [uint32]0xAE04000CL
    ([uint32]0x001E9B04) = [uint32]0x10000029
    ([uint32]0x001E9B08) = [uint32]0x00000000
    ([uint32]0x001ECA2C) = [uint32]0x0C07B514
    ([uint32]0x001ECACC) = [uint32]0x0C07B6DC
    ([uint32]0x0020DC40) = [uint32]0x0240202D
    ([uint32]0x0020DC44) = [uint32]0x0220282D
    ([uint32]0x0020DC48) = [uint32]0x2406FFFF
    ([uint32]0x0020DC4C) = [uint32]0x24070001
    ([uint32]0x0020DC50) = [uint32]0x0C0C170C
    ([uint32]0x0020DCF8) = [uint32]0xDFBF0030L
    ([uint32]0x0020DCFC) = [uint32]0x7BB20020
    ([uint32]0x0020DD00) = [uint32]0x7BB10010
    ([uint32]0x0020DD04) = [uint32]0x7BB00000
    ([uint32]0x0020DD08) = [uint32]0x27BD0040
    ([uint32]0x0020DD0C) = [uint32]0x03E00008
    ([uint32]0x0020DD10) = [uint32]0x00000000
}
foreach ($guard in $cleanGuards.GetEnumerator()) {
    $fileOffset = [int]([uint32]$guard.Key - 0x000FFF00)
    $actual = [BitConverter]::ToUInt32($cleanBytes, $fileOffset)
    Assert-PracticeBootstrapTest (
        $actual -eq [uint32]$guard.Value
    ) (
        "Clean ELF guard mismatch at 0x{0:X8}: expected 0x{1:X8}, got 0x{2:X8}." -f
            [uint32]$guard.Key,
            [uint32]$guard.Value,
            $actual
    )
}

$nun5Elf = Join-Path (
    [string]$paths.games.Entries.PSObject.Properties['NUN5'].Value.ExtractedPath
) 'SLES_556.05'
$nun5Bytes = [IO.File]::ReadAllBytes($nun5Elf)
$nun5TailGuards = @{
    ([uint32]0x00214CCC) = [uint32]0x0240202D
    ([uint32]0x00214CD0) = [uint32]0x0220282D
    ([uint32]0x00214CD4) = [uint32]0x2406FFFF
    ([uint32]0x00214CD8) = [uint32]0x24070001
    ([uint32]0x00214CDC) = [uint32]0x0C0C4160
    ([uint32]0x00214DE0) = [uint32]0xDFBF0030L
    ([uint32]0x00214DE4) = [uint32]0x7BB20020
    ([uint32]0x00214DE8) = [uint32]0x7BB10010
    ([uint32]0x00214DEC) = [uint32]0x7BB00000
    ([uint32]0x00214DF0) = [uint32]0x27BD0040
    ([uint32]0x00214DF4) = [uint32]0x03E00008
    ([uint32]0x00214DF8) = [uint32]0x00000000
}
foreach ($guard in $nun5TailGuards.GetEnumerator()) {
    $fileOffset = [int]([uint32]$guard.Key - 0x000FFE80)
    $actual = [BitConverter]::ToUInt32($nun5Bytes, $fileOffset)
    Assert-PracticeBootstrapTest (
        $actual -eq [uint32]$guard.Value
    ) (
        "Clean NUN5 ELF guard mismatch at 0x{0:X8}: expected 0x{1:X8}, got 0x{2:X8}." -f
            [uint32]$guard.Key,
            [uint32]$guard.Value,
            $actual
    )
}

Write-Host 'Practice bootstrap tests passed.' -ForegroundColor Green
