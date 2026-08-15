[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateRange(2, [int]::MaxValue)]
    [int]$MovesetRow,

    [Parameter(Mandatory)]
    [ValidateCount(1, 2)]
    [string[]]$Games,

    [string]$ProjectRoot = (Join-Path $PSScriptRoot '..\..')
)

$ErrorActionPreference = 'Stop'
. (Join-Path $ProjectRoot 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths -ManifestPath (Join-Path $ProjectRoot 'paths.json')

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
    'character_id',
    'linked_j_id',
    'linked_uj_id',
    'awakening_id'
)
$actualColumns = @($movesets[0].PSObject.Properties.Name)
if (($actualColumns -join "`t") -cne ($expectedColumns -join "`t")) {
    throw (
        'Moveset metadata columns must be: ' +
        ($expectedColumns -join ', ')
    )
}

$movesetIndex = $MovesetRow - 2
if ($movesetIndex -ge $movesets.Count) {
    throw "Unknown moveset row: $MovesetRow"
}
$selected = $movesets[$movesetIndex]

$characterText = [string]$selected.character_id
if ($characterText -cnotmatch '^[0-9]+$') {
    throw "Moveset row $MovesetRow has an invalid decimal character ID."
}
$character = [uint32]$characterText
if ($character -lt 1 -or $character -gt 93) {
    throw "Moveset row $MovesetRow character ID must be between 1 and 93."
}
$linkedJutsu = if (
    [string]::IsNullOrWhiteSpace([string]$selected.linked_j_id)
) {
    $null
}
else {
    ConvertFrom-PracticeHexId `
        -Value ([string]$selected.linked_j_id) `
        -Label "Moveset row $MovesetRow linked Jutsu ID" `
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
        -Label "Moveset row $MovesetRow linked UJ ID" `
        -Maximum 0x25
}
if ($null -ne $linkedJutsu -and $null -ne $linkedUj) {
    throw "Moveset row $MovesetRow may select only one linked support ID."
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
        -Label "Moveset row $MovesetRow awakening ID" `
        -Maximum 0x89
}
$values = @($character, $support, $awakening)

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
    if ([string]$entry.Category -ceq 'builds') {
        $pnachName = 'NA228p.pnach'
        $addresses = @('001ED600', '001ED604', '001ED608')
    }
    elseif ([string]$entry.Name -ceq 'NUN5') {
        $pnachName = 'NUN5p.pnach'
        $addresses = @('003D0FF0', '003D0FF4', '003D0FF8')
    }
    else {
        throw (
            "Practice supports NUN5 and NA2.28 build games; " +
            "got '$([string]$entry.Name)'."
        )
    }

    $pnachByGame[$selector] = [IO.Path]::GetFullPath(
        (Join-Path $paths.pcsx2_files "cheats\practice\$pnachName")
    )
    $pnachLinesByGame[$selector] = [string[]]@(
        for ($index = 0; $index -lt $addresses.Count; $index++) {
            (
                'patch=1,EE,{0},word,{1}' -f
                    $addresses[$index],
                    ([uint32]$values[$index]).ToString('X8')
            )
        }
    )
}

[pscustomobject]@{
    MovesetRow = $MovesetRow
    CharacterId = $character
    SupportId = $support
    AwakeningId = $awakening
    PnachByGame = $pnachByGame
    PnachLinesByGame = $pnachLinesByGame
}
