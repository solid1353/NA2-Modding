[CmdletBinding()]
param(
    [AllowEmptyCollection()]
    [string[]]$Arguments = @(),

    [Parameter(Mandatory)]
    [ValidateCount(1, 2)]
    [string[]]$Games,

    [string]$ProjectRoot = (Join-Path $PSScriptRoot '..\..')
)

$ErrorActionPreference = 'Stop'
. (Join-Path $ProjectRoot 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths -ManifestPath (Join-Path $ProjectRoot 'paths.json')

if ($Arguments.Count -ne 1) {
    throw 'The Practice launch profile requires a row.'
}
$movesetRow = 0
if (-not [int]::TryParse([string]$Arguments[0], [ref]$movesetRow) -or
    $movesetRow -lt 2) {
    throw 'Launch profile row must be a decimal integer starting at 2.'
}

function ConvertFrom-PracticeHexId {
    param(
        [Parameter(Mandatory)][string]$Value,
        [Parameter(Mandatory)][string]$Label,
        [Parameter(Mandatory)][uint32]$Maximum
    )

    $match = [regex]::Match($Value, '^0[xX]([0-9A-Fa-f]{1,8})$')
    if (-not $match.Success) {
        throw "$Label must be an empty cell or a hexadecimal 0x-prefixed ID."
    }
    $result = [Convert]::ToUInt32($match.Groups[1].Value, 16)
    if ($result -gt $Maximum) {
        throw "$Label must be between 0x00 and 0x$($Maximum.ToString('X2'))."
    }
    return $result
}

$movesetsPath = Join-Path ([string]$paths.resources) 'movesets.tsv'
if (-not (Test-Path -LiteralPath $movesetsPath -PathType Leaf)) {
    throw "Moveset metadata does not exist: $movesetsPath"
}
$movesets = @(Import-Csv -LiteralPath $movesetsPath -Delimiter "`t")
if ($movesets.Count -eq 0) {
    throw "Moveset metadata is empty: $movesetsPath"
}
$expectedColumns = @(
    'character',
    'id',
    'linked_j_id',
    'linked_uj_id',
    'awakening_id',
    'reversal',
    'uniqueness'
)
$actualColumns = @($movesets[0].PSObject.Properties.Name)
if (($actualColumns -join "`t") -cne ($expectedColumns -join "`t")) {
    throw (
        'Moveset metadata columns must be: ' +
        ($expectedColumns -join ', ')
    )
}

$currentMovesetRow = $movesetRow
$movesetIndex = $currentMovesetRow - 2
if ($movesetIndex -ge $movesets.Count) {
    throw "Unknown moveset row: $currentMovesetRow"
}
$selected = $movesets[$movesetIndex]
$reversalText = [string]$selected.reversal
if (-not [string]::IsNullOrWhiteSpace($reversalText) -and
    $reversalText -cne 'Y') {
    throw "Moveset row $currentMovesetRow reversal must be an empty cell or Y."
}
$isReversal = $reversalText -ceq 'Y'

$characterText = [string]$selected.id
if ($characterText -cnotmatch '^[0-9]+$') {
    throw "Moveset row $currentMovesetRow has an invalid decimal character ID."
}
$character = [uint32]$characterText
if ($character -lt 1 -or $character -gt 93) {
    throw "Moveset row $currentMovesetRow character ID must be between 1 and 93."
}
$linkedJutsu = if (
    [string]::IsNullOrWhiteSpace([string]$selected.linked_j_id)
) {
    $null
}
else {
    ConvertFrom-PracticeHexId `
        -Value ([string]$selected.linked_j_id) `
        -Label "Moveset row $currentMovesetRow linked Jutsu ID" `
        -Maximum 0x25
}
$linkedUj = if (
    [string]::IsNullOrWhiteSpace([string]$selected.linked_uj_id)
) {
    $null
}
else {
    ConvertFrom-PracticeHexId `
        -Value ([string]$selected.linked_uj_id) `
        -Label "Moveset row $currentMovesetRow linked UJ ID" `
        -Maximum 0x25
}
if ($null -ne $linkedJutsu -and $null -ne $linkedUj) {
    throw "Moveset row $currentMovesetRow may select only one linked support ID."
}
$support = if ($null -ne $linkedJutsu) {
    [uint32]$linkedJutsu
}
elseif ($null -ne $linkedUj) {
    [uint32]$linkedUj
}
else {
    [uint32]0x25
}
$awakening = if ([string]::IsNullOrWhiteSpace([string]$selected.awakening_id)) {
    [uint32]::MaxValue
}
else {
    ConvertFrom-PracticeHexId `
        -Value ([string]$selected.awakening_id) `
        -Label "Moveset row $currentMovesetRow awakening ID" `
        -Maximum 0x89
}
$values = @($character, $support, $awakening)
$usesGaaraMovesetAwakening = (
    $character -eq 0x3B -and $awakening -eq 0x3B
)
$usesChiyoMovesetAwakening = (
    $character -eq 0x4D -and $awakening -eq 0x4E
)
$usesFullNativeAwakeningEntry = (
    $character -eq 0x40 -and $awakening -eq 0x41
)

$pnachByGame = @{}
$pnachLinesByGame = @{}
foreach ($requestedGame in $Games) {
    $selector = $requestedGame.ToLowerInvariant()
    $alias = @(
        $paths.games.Aliases.PSObject.Properties |
            Where-Object { $_.Name -ieq $selector }
    ) | Select-Object -First 1
    if ($null -eq $alias) {
        throw "Unknown game selector: $requestedGame"
    }
    $entry = $paths.games.Entries.PSObject.Properties[
        [string]$alias.Value
    ].Value
    $catalogPnach = if ([string]$entry.Category -ceq 'builds') {
        [string]$entry.Config.cheat_template
    }
    else {
        [string]$entry.Config.cheats
    }
    $pnachName = [IO.Path]::GetFileName($catalogPnach)
    if ([string]$entry.Category -ceq 'builds') {
        $addresses = @('001ED600', '001ED604', '001ED608')
        $halfHpAddress = '001E7AE8'
        $gaaraMovesetAwakeningLines = @(
            'patch=1,EE,001ED54C,word,FFA80008'
            'patch=1,EE,001ED550,word,0100202D'
            'patch=1,EE,001ED554,word,24050001'
            'patch=1,EE,001ED558,word,0C0A7078'
            'patch=1,EE,001ED55C,word,00000000'
            'patch=1,EE,001ED560,word,DFA80008'
            'patch=1,EE,001ED564,word,DFBF0000'
            'patch=1,EE,001ED568,word,27BD0010'
            'patch=1,EE,001ED56C,word,27BDFFC0'
            'patch=1,EE,001ED570,word,FFBF0030'
            'patch=1,EE,001ED574,word,7FB20020'
            'patch=1,EE,001ED578,word,7FB10010'
            'patch=1,EE,001ED57C,word,7FB00000'
            'patch=1,EE,001ED580,word,0100902D'
            'patch=1,EE,001ED584,word,2411003B'
            'patch=1,EE,001ED588,word,08083710'
            'patch=1,EE,001ED58C,word,00000000'
        )
        $chiyoMovesetAwakeningLines = @(
            'patch=1,EE,001ED54C,word,FFA80008'
            'patch=1,EE,001ED550,word,0100202D'
            'patch=1,EE,001ED554,word,24050001'
            'patch=1,EE,001ED558,word,0C0B606C'
            'patch=1,EE,001ED55C,word,00000000'
            'patch=1,EE,001ED560,word,DFA80008'
            'patch=1,EE,001ED564,word,DFBF0000'
            'patch=1,EE,001ED568,word,27BD0010'
            'patch=1,EE,001ED56C,word,08083644'
            'patch=1,EE,001ED570,word,0100202D'
        )
        $fullNativeAwakeningLines = @(
            'patch=1,EE,001ED54C,word,0100202D'
            'patch=1,EE,001ED550,word,DFBF0000'
            'patch=1,EE,001ED554,word,08083644'
            'patch=1,EE,001ED558,word,27BD0010'
        )
    }
    elseif ([string]$entry.Name -ceq 'NUN5') {
        $addresses = @('003D0FF0', '003D0FF4', '003D0FF8')
        $halfHpAddress = '001ED8D8'
        $gaaraMovesetAwakeningLines = @(
            'patch=1,EE,003D0F3C,word,FFA80008'
            'patch=1,EE,003D0F40,word,0100202D'
            'patch=1,EE,003D0F44,word,24050001'
            'patch=1,EE,003D0F48,word,0C0A9644'
            'patch=1,EE,003D0F4C,word,00000000'
            'patch=1,EE,003D0F50,word,DFA80008'
            'patch=1,EE,003D0F54,word,DFBF0000'
            'patch=1,EE,003D0F58,word,27BD0010'
            'patch=1,EE,003D0F5C,word,27BDFFC0'
            'patch=1,EE,003D0F60,word,FFBF0030'
            'patch=1,EE,003D0F64,word,7FB20020'
            'patch=1,EE,003D0F68,word,7FB10010'
            'patch=1,EE,003D0F6C,word,7FB00000'
            'patch=1,EE,003D0F70,word,0100902D'
            'patch=1,EE,003D0F74,word,2411003B'
            'patch=1,EE,003D0F78,word,08085333'
            'patch=1,EE,003D0F7C,word,00000000'
        )
        $chiyoMovesetAwakeningLines = @(
            'patch=1,EE,003D0F3C,word,FFA80008'
            'patch=1,EE,003D0F40,word,0100202D'
            'patch=1,EE,003D0F44,word,24050001'
            'patch=1,EE,003D0F48,word,0C0B88BC'
            'patch=1,EE,003D0F4C,word,00000000'
            'patch=1,EE,003D0F50,word,DFA80008'
            'patch=1,EE,003D0F54,word,DFBF0000'
            'patch=1,EE,003D0F58,word,27BD0010'
            'patch=1,EE,003D0F5C,word,08085278'
            'patch=1,EE,003D0F60,word,0100202D'
        )
        $fullNativeAwakeningLines = @(
            'patch=1,EE,003D0F3C,word,0100202D'
            'patch=1,EE,003D0F40,word,DFBF0000'
            'patch=1,EE,003D0F44,word,08085278'
            'patch=1,EE,003D0F48,word,27BD0010'
        )
    }
    else {
        throw (
            "Practice supports NUN5 and NA2.28 build games; " +
            "got '$([string]$entry.Name)'."
        )
    }

    $pnachPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $pnachName))
    if (-not (Test-Path -LiteralPath $pnachPath -PathType Leaf)) {
        throw "Practice launch profile PNACH does not exist: $pnachPath"
    }
    $pnachByGame[$selector] = $pnachPath
    $pnachLinesByGame[$selector] = [string[]]@(
        for ($index = 0; $index -lt $addresses.Count; $index++) {
            (
                'patch=1,EE,{0},word,{1}' -f
                    $addresses[$index],
                    ([uint32]$values[$index]).ToString('X8')
            )
        }
        if ($isReversal) {
            'patch=1,EE,{0},word,A0850001' -f $halfHpAddress
        }
        if ($usesGaaraMovesetAwakening) {
            $gaaraMovesetAwakeningLines
        }
        elseif ($usesChiyoMovesetAwakening) {
            $chiyoMovesetAwakeningLines
        }
        elseif ($usesFullNativeAwakeningEntry) {
            $fullNativeAwakeningLines
        }
    )
}

[pscustomobject]@{
    MovesetRow = $currentMovesetRow
    CharacterId = $character
    SupportId = $support
    AwakeningId = $awakening
    Reversal = $isReversal
    PnachByGame = $pnachByGame
    PnachLinesByGame = $pnachLinesByGame
    LaunchParameters = @{
        PnachByGame = $pnachByGame
        PnachLinesByGame = $pnachLinesByGame
    }
}
