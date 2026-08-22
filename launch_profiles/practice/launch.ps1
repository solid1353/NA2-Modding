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
    throw 'The Practice launch profile requires a case ID.'
}
$movesetCaseId = [string]$Arguments[0]
if ($movesetCaseId -cnotmatch '^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$') {
    throw 'Launch profile case ID must be a hyphen-separated alphanumeric identifier.'
}

function ConvertFrom-PracticeHexId {
    param(
        [Parameter(Mandatory)][string]$Value,
        [Parameter(Mandatory)][string]$Label,
        [Parameter(Mandatory)][uint32]$Maximum
    )

    $match = [regex]::Match($Value, '^0[xX]([0-9A-Fa-f]{1,8})$')
    if (-not $match.Success) {
        throw "$Label must be a hexadecimal 0x-prefixed ID."
    }
    $result = [Convert]::ToUInt32($match.Groups[1].Value, 16)
    if ($result -gt $Maximum) {
        throw "$Label must be between 0x00 and 0x$($Maximum.ToString('X2'))."
    }
    return $result
}

function Resolve-PracticeMovesetKind {
    param([Parameter(Mandatory)][string]$CaseId)

    switch -Regex -CaseSensitive ($CaseId) {
        '-2nd$' { return '2nd form' }
        '-rev$' { return 'half_hp' }
        '-awk-[1-9][0-9]*$' { return 'awakening' }
        '-luj-[1-9][0-9]*$' { return 'linked_uj' }
        '-lj-[1-9][0-9]*$' { return 'linked_jutsu' }
        default { return 'base' }
    }
}

$movesetsPath = [string]$paths.files.practice_movesets
if (-not (Test-Path -LiteralPath $movesetsPath -PathType Leaf)) {
    throw "Moveset metadata does not exist: $movesetsPath"
}
$movesets = @(Import-Csv -LiteralPath $movesetsPath -Delimiter "`t")
if ($movesets.Count -eq 0) {
    throw "Moveset metadata is empty: $movesetsPath"
}
$expectedColumns = @(
    'case_id',
    'character_id',
    'awakening_id',
    'support_id',
    'capture_policy'
)
$actualColumns = @($movesets[0].PSObject.Properties.Name)
if (($actualColumns -join "`t") -cne ($expectedColumns -join "`t")) {
    throw (
        'Moveset metadata columns must be: ' +
        ($expectedColumns -join ', ')
    )
}

$movesetsByCaseId =
    [Collections.Generic.Dictionary[string, object]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
foreach ($moveset in $movesets) {
    $caseId = [string]$moveset.case_id
    if ($caseId -cnotmatch '^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$') {
        throw "Moveset case ID '$caseId' is not a hyphen-separated alphanumeric identifier."
    }
    if ($movesetsByCaseId.ContainsKey($caseId)) {
        throw "Duplicate moveset case ID: $caseId"
    }
    $characterText = [string]$moveset.character_id
    if ($characterText -cnotmatch '^[0-9]+$') {
        throw "Moveset case '$caseId' has an invalid decimal character ID."
    }
    $characterId = [uint32]$characterText
    if ($characterId -lt 1 -or $characterId -gt 93) {
        throw "Moveset case '$caseId' character ID must be between 1 and 93."
    }

    $kind = Resolve-PracticeMovesetKind -CaseId $caseId
    $supportText = [string]$moveset.support_id
    $supportId = if ($supportText -ceq '') {
        [uint32]0x25
    }
    else {
        ConvertFrom-PracticeHexId `
            -Value $supportText `
            -Label "Moveset case '$caseId' support ID" `
            -Maximum 0x25
    }
    $awakeningText = [string]$moveset.awakening_id
    $awakeningId = if ($awakeningText -ceq '') {
        [uint32]::MaxValue
    }
    else {
        ConvertFrom-PracticeHexId `
            -Value $awakeningText `
            -Label "Moveset case '$caseId' awakening ID" `
            -Maximum 0x89
    }
    $capturePolicy = [string]$moveset.capture_policy
    if ($capturePolicy -cnotin @(
        '',
        'base',
        'specials',
        'base, specials',
        'base, parent-specials'
    )) {
        throw "Moveset case '$caseId' has invalid capture_policy '$capturePolicy'."
    }
    if ($capturePolicy -ceq 'base, parent-specials' -and $kind -cne '2nd form') {
        throw (
            "Moveset case '$caseId' may use capture_policy " +
            "'base, parent-specials' only with kind '2nd form'."
        )
    }
    if ($kind -ceq '2nd form' -and
        $capturePolicy -cne 'base, parent-specials') {
        throw (
            "Moveset case '$caseId' with kind '2nd form' must use " +
            "capture_policy 'base, parent-specials'."
        )
    }

    switch -CaseSensitive ($kind) {
        { $_ -cin @('base', '2nd form') } {
            if ($supportText -cne '' -or $awakeningText -cne '') {
                throw "Moveset case '$caseId' has fields incompatible with kind '$kind'."
            }
        }
        'awakening' {
            if ($supportText -cne '' -or $awakeningText -ceq '') {
                throw "Moveset case '$caseId' has fields incompatible with kind 'awakening'."
            }
        }
        'half_hp' {
            if ($supportText -cne '' -or $awakeningText -cne '') {
                throw "Moveset case '$caseId' has fields incompatible with kind 'half_hp'."
            }
        }
        { $_ -cin @('linked_uj', 'linked_jutsu') } {
            if ($supportText -ceq '' -or $supportId -eq 0x25 -or
                $awakeningText -cne '') {
                throw "Moveset case '$caseId' has fields incompatible with kind '$kind'."
            }
        }
    }

    $movesetsByCaseId.Add($caseId, [pscustomobject]@{
        CaseId = $caseId
        Kind = $kind
        CharacterId = $characterId
        SupportId = [uint32]$supportId
        AwakeningId = [uint32]$awakeningId
    })
}
if (-not $movesetsByCaseId.ContainsKey($movesetCaseId)) {
    throw "Unknown moveset case ID: $movesetCaseId"
}
$selected = $movesetsByCaseId[$movesetCaseId]
$movesetCaseId = [string]$selected.CaseId
$character = [uint32]$selected.CharacterId
$support = [uint32]$selected.SupportId
$awakening = [uint32]$selected.AwakeningId
$usesHalfHp = [string]$selected.Kind -ceq 'half_hp'
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
        if ($usesHalfHp) {
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
    MovesetCaseId = $movesetCaseId
    CharacterId = $character
    SupportId = $support
    AwakeningId = $awakening
    HalfHp = $usesHalfHp
    PnachByGame = $pnachByGame
    PnachLinesByGame = $pnachLinesByGame
    LaunchParameters = @{
        PnachByGame = $pnachByGame
        PnachLinesByGame = $pnachLinesByGame
    }
}
