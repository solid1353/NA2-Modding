[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Game,

    [Parameter(Mandatory)]
    [ValidateSet('reference', 'current')]
    [string]$Tier,

    [Parameter(Mandatory)]
    [string]$OutputRoot,

    [string]$MovesetRange,

    [ValidateSet('movesets', 'base', 'specials', 'idle')]
    [string]$MovesetFamily = 'movesets',

    [ValidateRange(1, 64)]
    [int]$ThrottleLimit = 16,

    [string]$ConcurrencyPoolRoot,

    [string]$MemoryCard,

    [AllowNull()]
    [psobject]$LaunchProfile,

    [string]$ProjectRoot = (Join-Path $PSScriptRoot '..\..')
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = [IO.Path]::GetFullPath($ProjectRoot)

. (Join-Path $ProjectRoot 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths -ManifestPath (Join-Path $ProjectRoot 'paths.json')
$taskScript = Join-Path $ProjectRoot 'e2e\scripts\suite.ps1'
. $taskScript

$characterDataPath = Join-Path ([string]$paths.resources) 'character_data.tsv'
$characterData = @(Import-Csv -LiteralPath $characterDataPath -Delimiter "`t")
$characterDataById = @{}
foreach ($character in $characterData) {
    $characterId = [string]$character.id
    if ($characterDataById.ContainsKey($characterId)) {
        throw "Duplicate character_data.tsv ID: $characterId"
    }
    $characterDataById[$characterId] = $character
}
$movesetsPath = [string]$paths.files.practice_movesets
$movesets = @(Import-Csv -LiteralPath $movesetsPath -Delimiter "`t")
$lastAvailableRow = $characterData.Count + 1
$firstRow = 2
$lastRow = $lastAvailableRow
if (-not [string]::IsNullOrWhiteSpace($MovesetRange)) {
    $resolvedRange = Resolve-VisualRegressionMovesetRange `
        -Range $MovesetRange `
        -LastAvailableRow $lastAvailableRow
    $firstRow = $resolvedRange.FirstRow
    $lastRow = $resolvedRange.LastRow
    $MovesetRange = $resolvedRange.Value
}

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    throw 'OutputRoot cannot be empty.'
}
$runRoot = if ([IO.Path]::IsPathRooted($OutputRoot)) {
    [IO.Path]::GetFullPath($OutputRoot)
}
else {
    [IO.Path]::GetFullPath((Join-Path $ProjectRoot $OutputRoot))
}
$gridOutputRoot = Join-Path $runRoot 'screenshots'
$workingBase = Join-Path $runRoot '.work'
[void](New-Item -ItemType Directory -Path $gridOutputRoot, $workingBase -Force)
$ConcurrencyPoolRoot = if ([string]::IsNullOrWhiteSpace($ConcurrencyPoolRoot)) {
    Join-Path $workingBase 'concurrency'
}
else {
    [IO.Path]::GetFullPath($ConcurrencyPoolRoot)
}

$gridScript = Join-Path `
    ([string]$paths.scripts) `
    'research\localization\compare_font_capture_sets.ps1'
$launcher = [string]$paths.files.pcsx2_game_launch_command

$gameTarget = if ($Tier -ieq 'reference') {
    [pscustomobject]@{
        Selector = $Game
        Suffix = 'a_reference'
        GridVariant = 'a_reference'
        Label = "$Game reference"
    }
}
else {
    [pscustomobject]@{
        Selector = $Game
        Suffix = 'b_current'
        GridVariant = 'b_current'
        Label = "$Game current"
    }
}
$gameTargets = @($gameTarget)

function Resolve-VisualRegressionMovesetKind {
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

$expectedMovesetColumns = @(
    'case_id',
    'character_id',
    'awakening_id',
    'support_id',
    'capture_policy'
)
if ($movesets.Count -eq 0) {
    throw "Moveset metadata is empty: $movesetsPath"
}
$actualMovesetColumns = @($movesets[0].PSObject.Properties.Name)
if (($actualMovesetColumns -join "`t") -cne
    ($expectedMovesetColumns -join "`t")) {
    throw (
        'Moveset metadata columns must be: ' +
        ($expectedMovesetColumns -join ', ')
    )
}

$knownCaseIds = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
$indexedMovesets = @(
    foreach ($moveset in $movesets) {
        $caseId = [string]$moveset.case_id
        if ($caseId -cnotmatch '^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$') {
            throw "Moveset case ID '$caseId' is not a hyphen-separated alphanumeric identifier."
        }
        if (-not $knownCaseIds.Add($caseId)) {
            throw "Duplicate moveset case ID: $caseId"
        }
        $characterId = [string]$moveset.character_id
        if (-not $characterDataById.ContainsKey($characterId)) {
            throw (
                "Moveset case '$caseId' has unknown character ID " +
                "'$characterId'."
            )
        }
        $kind = Resolve-VisualRegressionMovesetKind -CaseId $caseId
        $capturePolicy = [string]$moveset.capture_policy
        if ($capturePolicy -cnotin @(
            '',
            'base',
            'specials',
            'base, specials',
            'base, parent-specials'
        )) {
            throw (
                "Moveset case '$caseId' has invalid capture_policy " +
                "'$capturePolicy'."
            )
        }
        if ($capturePolicy -ceq 'base, parent-specials' -and
            $kind -cne '2nd form') {
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
        [pscustomobject]@{
            CaseId = $caseId
            CharacterId = $characterId
            CharacterName = [string]$characterDataById[$characterId].character
            Data = $moveset
            Kind = $kind
            CapturesBase = $capturePolicy -cin @(
                'base',
                'base, specials',
                'base, parent-specials'
            )
            CapturesSpecials = $capturePolicy -cin @('specials', 'base, specials')
            CapturesParentSpecials = $capturePolicy -ceq 'base, parent-specials'
        }
    }
)
$indexedMovesetsByCaseId = @{}
foreach ($movesetCase in $indexedMovesets) {
    $indexedMovesetsByCaseId[$movesetCase.CaseId] = $movesetCase
}
$blocks = [Collections.Generic.List[object]]::new()
$currentBlock = $null
foreach ($movesetCase in $indexedMovesets) {
    if ($movesetCase.Kind -cin @('base', '2nd form')) {
        $currentBlock = [pscustomobject]@{
            Base = $movesetCase
            Rows = [Collections.Generic.List[object]]::new()
        }
        [void]$blocks.Add($currentBlock)
    }
    elseif ($null -eq $currentBlock) {
        throw (
            "Moveset case '$($movesetCase.CaseId)' has no preceding base or " +
            "'2nd form' case."
        )
    }
    elseif (
        $movesetCase.CharacterId -cne $currentBlock.Base.CharacterId
    ) {
        throw (
            "Moveset case '$($movesetCase.CaseId)' does not match its block " +
            "case '$($currentBlock.Base.CaseId)'."
        )
    }
    [void]$currentBlock.Rows.Add($movesetCase)
}

$blocksByCharacterId = @{}
foreach ($block in $blocks) {
    $characterId = $block.Base.CharacterId
    if ($blocksByCharacterId.ContainsKey($characterId)) {
        throw "Duplicate moveset block for character ID '$characterId'."
    }
    $blocksByCharacterId[$characterId] = $block
}

$outputPlans = [Collections.Generic.List[object]]::new()
for ($characterIndex = $firstRow - 2; $characterIndex -le $lastRow - 2; $characterIndex++) {
    $character = $characterData[$characterIndex]
    $characterId = [string]$character.id
    if (-not $blocksByCharacterId.ContainsKey($characterId)) {
        throw (
            "Character_data.tsv row $($characterIndex + 2) has no matching " +
            'movesets.tsv block.'
        )
    }
    $block = $blocksByCharacterId[$characterId]
    $outputNumber = $characterIndex + 2
    if ($MovesetFamily -ceq 'idle') {
        continue
    }

    $slug = ([string]$character.character).ToLowerInvariant()
    $slug = [regex]::Replace($slug, '[^a-z0-9]+', '_')
    $slug = $slug.Trim('_')
    if ([string]::IsNullOrWhiteSpace($slug)) {
        $slug = 'character'
    }
    if ($block.Base.CapturesBase) {
        [void]$outputPlans.Add([pscustomobject]@{
            Name = ('{0:D3}_{1}_base' -f $outputNumber, $slug)
            Family = 'base'
            Captures = @(
                [pscustomobject]@{
                    CaseId = $block.Base.CaseId
                    Recording = 'movesets\base.p2m2'
                }
            )
        })
    }
    foreach ($awakeningCase in @(
        $block.Rows | Where-Object Kind -CEQ 'awakening'
    )) {
        if (-not $awakeningCase.CapturesBase) {
            continue
        }
        $awakeningId = [string]$awakeningCase.Data.awakening_id
        [void]$outputPlans.Add([pscustomobject]@{
            Name = ('{0:D3}_{1}_mode_{2}' -f $outputNumber, $slug, $awakeningId)
            Family = 'base'
            Captures = @(
                [pscustomobject]@{
                    CaseId = $awakeningCase.CaseId
                    Recording = 'movesets\base.p2m2'
                }
            )
        })
    }

    $ownsSpecialsGrid = @(
        $block.Rows | Where-Object Kind -CEQ 'half_hp'
    ).Count -gt 0
    if ($ownsSpecialsGrid) {
        $secondFormBlock = $null
        if ($characterIndex + 1 -lt $characterData.Count) {
            $secondForm = $characterData[$characterIndex + 1]
            $secondFormId = [string]$secondForm.id
            if ($blocksByCharacterId.ContainsKey($secondFormId)) {
                $candidate = $blocksByCharacterId[$secondFormId]
                if ($candidate.Base.Kind -ceq '2nd form') {
                    $secondFormBlock = $candidate
                }
            }
        }

        $specialCaptures = [Collections.Generic.List[object]]::new()
        foreach ($movesetCase in $block.Rows) {
            if ($movesetCase.CapturesSpecials) {
                [void]$specialCaptures.Add([pscustomobject]@{
                    CaseId = $movesetCase.CaseId
                    Recording = 'movesets\specials.p2m2'
                })
            }
        }
        if ($null -ne $secondFormBlock -and
            $secondFormBlock.Base.CapturesParentSpecials) {
            [void]$specialCaptures.Add([pscustomobject]@{
                CaseId = $secondFormBlock.Base.CaseId
                Recording = 'movesets\specials.p2m2'
            })
        }
        if ($specialCaptures.Count -gt 0) {
            [void]$outputPlans.Add([pscustomobject]@{
                Name = ('{0:D3}_{1}_specials' -f $outputNumber, $slug)
                Family = 'specials'
                Captures = @($specialCaptures)
            })
        }
    }
}

if ($MovesetFamily -ceq 'idle') {
    foreach ($idlePage in @(
        Get-VisualRegressionIdlePagePlans `
            -FirstRow $firstRow `
            -LastRow $lastRow `
            -CharacterCount $characterData.Count
    )) {
        $pageCaptures = [Collections.Generic.List[object]]::new()
        for (
            $characterIndex = $idlePage.FirstCharacterIndex;
            $characterIndex -le $idlePage.LastCharacterIndex;
            $characterIndex++
        ) {
            $character = $characterData[$characterIndex]
            $characterId = [string]$character.id
            if (-not $blocksByCharacterId.ContainsKey($characterId)) {
                throw (
                    "Character_data.tsv row $($characterIndex + 2) has no matching " +
                    'movesets.tsv block.'
                )
            }
            [void]$pageCaptures.Add([pscustomobject]@{
                CaseId = $blocksByCharacterId[$characterId].Base.CaseId
                Recording = 'characters\idle.p2m2'
            })
        }
        [void]$outputPlans.Add([pscustomobject]@{
            Name = ('page_{0:D2}' -f $idlePage.Page)
            Family = 'idle'
            Captures = @($pageCaptures)
        })
    }
}

$selectedOutputPlans = @(
    $outputPlans | Where-Object {
        ($MovesetFamily -ceq 'movesets' -and $_.Family -cin @('base', 'specials')) -or
            $_.Family -ceq $MovesetFamily
    }
)
$practiceCaseIds = [string[]]@(
    $selectedOutputPlans |
        ForEach-Object Captures |
        ForEach-Object { [string]$_.CaseId } |
        Sort-Object -Unique
)
$practiceGames = [string[]]@($gameTargets | ForEach-Object Selector)
$practiceByCaseId = @{}
foreach ($practice in @(
    Get-VisualRegressionPracticeConfiguration `
        -Repository $ProjectRoot `
        -MovesetCaseId $practiceCaseIds `
        -Game $practiceGames
)) {
    $practiceByCaseId[[string]$practice.MovesetCaseId] = $practice
}

$tasks = [Collections.Generic.List[object]]::new()
$gridPlans = [Collections.Generic.List[object]]::new()
foreach ($outputPlan in $selectedOutputPlans) {
    foreach ($gameTarget in $gameTargets) {
        $outputName = '{0}_{1}' -f $outputPlan.Name, $gameTarget.Suffix
        $workingRoot = Join-Path $workingBase $outputName
        $finalGrid = Join-Path $gridOutputRoot ($outputName + '.png')
        if (Test-Path -LiteralPath $finalGrid -PathType Leaf) {
            continue
        }
        $captureContexts = [Collections.Generic.List[object]]::new()
        $captureTaskKeys = [Collections.Generic.List[string]]::new()
        $captureIndex = 0
        foreach ($capture in $outputPlan.Captures) {
            $captureIndex++
            $captureRoot = Join-Path `
                $workingRoot `
                ('captures\{0:D3}-{1}\{2}' -f
                    $captureIndex,
                    $capture.CaseId,
                    $gameTarget.Selector)
            if (-not $practiceByCaseId.ContainsKey($capture.CaseId)) {
                throw (
                    "Practice data was not resolved for moveset case " +
                    "'$($capture.CaseId)'."
                )
            }
            $practice = $practiceByCaseId[$capture.CaseId]
            if (-not $practice.PnachByGame.ContainsKey($gameTarget.Selector) -or
                -not $practice.PnachLinesByGame.ContainsKey($gameTarget.Selector)) {
                throw (
                    "Practice data for moveset case '$($capture.CaseId)' does not " +
                    "contain game $($gameTarget.Selector)."
                )
            }
            $pnachByGame = @{}
            $pnachByGame[$gameTarget.Selector] =
                $practice.PnachByGame[$gameTarget.Selector]
            $pnachLinesByGame = @{}
            $pnachLinesByGame[$gameTarget.Selector] =
                $practice.PnachLinesByGame[$gameTarget.Selector]
            $taskContext = [pscustomobject]@{
                CaseId = $capture.CaseId
                Character = [string](
                    $indexedMovesetsByCaseId[$capture.CaseId].CharacterName
                )
                Recording = $capture.Recording
                Game = $gameTarget.Selector
                GameLabel = $gameTarget.Label
                InputRecordingsRoot = Join-Path ([string]$paths.pcsx2_input_recordings) 'e2e'
                CaptureRoot = $captureRoot
                CaseRoot = Split-Path -Parent $captureRoot
                CompletePath = Join-Path (Split-Path -Parent $captureRoot) 'complete.json'
                PnachByGame = $pnachByGame
                PnachLinesByGame = $pnachLinesByGame
                MemoryCard = $MemoryCard
                LaunchProfile = $LaunchProfile
                ConcurrencyPoolRoot = $ConcurrencyPoolRoot
                ConcurrencyLimit = $ThrottleLimit
            }
            [void]$captureContexts.Add($taskContext)

            $taskName = 'capture-{0}-{1}-{2:D3}' -f
                $outputPlan.Name,
                $gameTarget.GridVariant,
                $captureIndex
            $capturedScreenshots = Join-Path $taskContext.CaptureRoot 'screenshots'
            $captureComplete = (
                (Test-Path -LiteralPath $taskContext.CompletePath -PathType Leaf) -and
                @(
                    Get-ChildItem `
                        -LiteralPath $capturedScreenshots `
                        -Filter '*.png' `
                        -File `
                        -ErrorAction SilentlyContinue
                ).Count -gt 0
            )
            if ($captureComplete) {
                continue
            }
            [void]$captureTaskKeys.Add($taskName)
            $startTask = {
                Start-ThreadJob `
                    -Name $taskName `
                    -ThrottleLimit $ThrottleLimit `
                    -ArgumentList @(
                        $taskContext,
                        $launcher,
                        $ProjectRoot,
                        $taskScript
                    ) `
                    -ScriptBlock {
                        param($Context, $Launcher, $Repository, $SuiteScript)
                        $ErrorActionPreference = 'Stop'
                        . $SuiteScript
                        Write-Host (
                            "Capturing $($Context.GameLabel) moveset case " +
                            "'$($Context.CaseId)' with $($Context.Recording) -> " +
                            $Context.CaptureRoot
                        ) -ForegroundColor Cyan
                        if (Test-Path -LiteralPath $Context.CaseRoot) {
                            Remove-Item `
                                -LiteralPath $Context.CaseRoot `
                                -Recurse `
                                -Force
                        }
                        [void](New-Item `
                            -ItemType Directory `
                            -Path $Context.CaptureRoot `
                            -Force)
                        $permit = Enter-VisualRegressionConcurrencyPool `
                            -Root $Context.ConcurrencyPoolRoot `
                            -Capacity $Context.ConcurrencyLimit
                        try {
                            $launchArguments = @{
                                Games = @($Context.Game)
                                Play = $Context.Recording
                                Snapshots = $true
                                InputRecordingCaptureMode = 'screenshots'
                                CaptureDirectory = $Context.CaptureRoot
                                ReadOnlySettings = $true
                                PnachByGame = $Context.PnachByGame
                                PnachLinesByGame = $Context.PnachLinesByGame
                                ProjectRoot = $Repository
                                InputRecordingsRoot = $Context.InputRecordingsRoot
                            }
                            Add-VisualRegressionSuiteLaunchSettings `
                                -Target $launchArguments `
                                -Repository $Repository `
                                -Game $Context.Game `
                                -MemoryCard $Context.MemoryCard `
                                -LaunchProfile $Context.LaunchProfile
                            & $Launcher @launchArguments
                        }
                        finally {
                            $permit.Dispose()
                        }

                        $screenshots = Join-Path $Context.CaptureRoot 'screenshots'
                        $screenshotCount = @(
                            Get-ChildItem `
                                -LiteralPath $screenshots `
                                -Filter '*.png' `
                                -File
                        ).Count
                        if ($screenshotCount -eq 0) {
                            throw (
                                "$($Context.GameLabel) snapshot replay produced " +
                                "no screenshots for moveset case " +
                                "'$($Context.CaseId)'."
                            )
                        }
                        $complete = [ordered]@{
                            case_id = $Context.CaseId
                            recording = $Context.Recording
                            game = $Context.Game
                            screenshots = $screenshotCount
                            completed_utc = (Get-Date).ToUniversalTime().ToString('O')
                        } | ConvertTo-Json
                        $temporary = "$($Context.CompletePath).tmp-$([guid]::NewGuid().ToString('N'))"
                        [IO.File]::WriteAllText(
                            $temporary,
                            $complete + "`n",
                            [Text.UTF8Encoding]::new($false)
                        )
                        [IO.File]::Move($temporary, $Context.CompletePath, $true)
                        [pscustomobject]@{
                            CaseId = $Context.CaseId
                            Character = $Context.Character
                            Recording = $Context.Recording
                            Game = $Context.Game
                            Screenshots = $screenshotCount
                        }
                    }
            }.GetNewClosure()
            [void]$tasks.Add([pscustomobject]@{
                Key = $taskName
                Priority = 10
                DependsOn = @()
                Ready = $null
                Start = $startTask
            })
        }

        $gridRoot = Join-Path $workingRoot 'grid'
        $gridInput = Join-Path $workingRoot 'grid-input'
        $gridContext = [pscustomobject]@{
            Name = $outputName
            Captures = @($captureContexts)
            CanonicalVariant = $gameTarget.GridVariant
            AlwaysGrid = $outputPlan.Family -ceq 'idle'
            GridRoot = $gridRoot
            GridInput = $gridInput
            FinalGrid = $finalGrid
            WorkingRoot = $workingRoot
        }
        [void]$gridPlans.Add([pscustomobject]@{
            Context = $gridContext
            DependsOn = @($captureTaskKeys)
        })
    }
}

$gridJobScript = {
    param($Context, $GridScript)
    $ErrorActionPreference = 'Stop'
                foreach ($generatedPath in @(
                    $Context.GridInput,
                    $Context.GridRoot
                )) {
                    if (Test-Path -LiteralPath $generatedPath) {
                        Remove-Item `
                            -LiteralPath $generatedPath `
                            -Recurse `
                            -Force
                    }
                }
                [void](New-Item `
                    -ItemType Directory `
                    -Path $Context.GridInput `
                    -Force)
                try {
                    $slot = 0
                    $singleScreenshot = $null
                    foreach ($capture in $Context.Captures) {
                        $screenshots = Join-Path $capture.CaptureRoot 'screenshots'
                        $captureScreenshots = @(
                            Get-ChildItem `
                                -LiteralPath $screenshots `
                                -Filter '*.png' `
                                -File |
                                Sort-Object Name
                        )
                        if ($captureScreenshots.Count -eq 0) {
                            throw (
                                "No screenshots remain for moveset case " +
                                "'$($capture.CaseId)'."
                            )
                        }
                        foreach ($screenshot in $captureScreenshots) {
                            $slot++
                            $singleScreenshot = $screenshot.FullName
                            $canonicalName = '{0:D4}_{1}.png' -f
                                $slot,
                                $Context.CanonicalVariant
                            [void](New-Item `
                                -ItemType HardLink `
                                -Path (Join-Path $Context.GridInput $canonicalName) `
                                -Target $screenshot.FullName)
                        }
                    }
                    if ($slot -gt 6) {
                        throw (
                            "Moveset grid $($Context.Name) contains $slot " +
                            'screenshots; the fixed 3x2 grid supports at most 6.'
                        )
                    }
                    if ($slot -eq 1 -and -not $Context.AlwaysGrid) {
                        Copy-Item `
                            -LiteralPath $singleScreenshot `
                            -Destination $Context.FinalGrid `
                            -Force
                    }
                    else {
                        & $GridScript `
                            -ScreenshotDirectory $Context.GridInput `
                            -OutputDirectory $Context.GridRoot
                        if ($LASTEXITCODE -ne 0) {
                            throw "Grid generation failed for $($Context.Name)."
                        }
                        $gridPages = @(
                            Get-ChildItem `
                                -LiteralPath $Context.GridRoot `
                                -Filter 'page_*.png' `
                                -File
                        )
                        if ($gridPages.Count -ne 1) {
                            throw (
                                "Grid generation produced $($gridPages.Count) pages " +
                                "for $($Context.Name); expected exactly one."
                            )
                        }
                        Move-Item `
                            -LiteralPath $gridPages[0].FullName `
                            -Destination $Context.FinalGrid `
                            -Force
                    }
                }
                finally {
                    if (Test-Path `
                        -LiteralPath $Context.GridInput `
                        -PathType Container
                    ) {
                        Remove-Item `
                            -LiteralPath $Context.GridInput `
                            -Recurse `
                            -Force
                    }
                }

                for ($attempt = 1; $attempt -le 50; $attempt++) {
                    try {
                        if (Test-Path `
                            -LiteralPath $Context.WorkingRoot `
                            -PathType Container
                        ) {
                            Remove-Item `
                                -LiteralPath $Context.WorkingRoot `
                                -Recurse `
                                -Force
                        }
                        break
                    }
                    catch [IO.IOException], [UnauthorizedAccessException] {
                        if ($attempt -eq 50) {
                            throw (
                                'Failed to remove generated capture directory ' +
                                "$($Context.WorkingRoot): " +
                                $_.Exception.Message
                            )
                        }
                        Start-Sleep -Milliseconds 100
                    }
                }
                [pscustomobject]@{
                    Output = $Context.FinalGrid
                    Screenshots = $slot
                }
}
foreach ($gridPlan in $gridPlans) {
    $gridContext = $gridPlan.Context
    $taskName = 'grid-' + $gridContext.Name
    $startTask = {
        Start-ThreadJob `
            -Name $taskName `
            -ThrottleLimit $ThrottleLimit `
            -ArgumentList @($gridContext, $gridScript) `
            -ScriptBlock $gridJobScript
    }.GetNewClosure()
    [void]$tasks.Add([pscustomobject]@{
        Key = $taskName
        Priority = 20
        DependsOn = @($gridPlan.DependsOn)
        Ready = $null
        Start = $startTask
    })
}

Invoke-VisualRegressionTaskGraph `
    -Task @($tasks) `
    -ThrottleLimit $ThrottleLimit `
    -FailurePrefix 'Moveset capture'

if (Test-Path -LiteralPath $workingBase -PathType Container) {
    Remove-Item -LiteralPath $workingBase -Recurse -Force
}
$gridCount = @(
    Get-ChildItem -LiteralPath $gridOutputRoot -Filter '*.png' -File
).Count
if ($gridCount -eq 0) {
    throw "Moveset capture produced no $Tier grids for $Game."
}
Write-Host "Moveset $Tier grids captured for ${Game}: $gridOutputRoot" -ForegroundColor Green
[pscustomobject]@{
    Game = $Game
    Tier = $Tier
    Grids = $gridCount
    OutputRoot = $gridOutputRoot
}
