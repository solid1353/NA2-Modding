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
$paths = Get-Na2Paths
$taskScript = Join-Path $ProjectRoot 'e2e\scripts\suite.ps1'
. $taskScript
. (Join-Path ([string]$paths.scripts) 'na228\launch_profile.ps1')
$practiceProfile = Resolve-Na2LaunchProfile -Name 'practice' -Paths $paths
. (Join-Path $practiceProfile.Root 'moveset_cases.ps1')

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

$gameSelector = if ($Game.EndsWith('.iso', [StringComparison]::OrdinalIgnoreCase)) {
    [IO.Path]::GetFileNameWithoutExtension($Game)
}
else { $Game }
$gridVariant = if ($Tier -ieq 'reference') { 'a_reference' } else { 'b_current' }
$gameLabel = "$gameSelector $($gridVariant.Substring(2))"

$indexedMovesets = @(
    foreach ($movesetCase in Read-PracticeMovesetCases -Path ([string]$paths.files.practice_movesets)) {
        $characterId = [string]$movesetCase.Data.character_id
        if (-not $characterDataById.ContainsKey($characterId)) {
            throw (
                "Moveset case '$($movesetCase.CaseId)' has unknown character ID " +
                "'$characterId'."
            )
        }
        [pscustomobject]@{
            CaseId = $movesetCase.CaseId
            CharacterId = $characterId
            CharacterName = [string]$characterDataById[$characterId].character
            Data = $movesetCase.Data
            Kind = $movesetCase.Kind
            CapturesBase = $movesetCase.CapturesBase
            CapturesSpecials = $movesetCase.CapturesSpecials
            CapturesParentSpecials = $movesetCase.CapturesParentSpecials
            Case = $movesetCase
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
$practiceByCaseId = @{}
foreach ($caseId in $practiceCaseIds) {
    $practice = Get-PracticeConfiguration `
        -Case $indexedMovesetsByCaseId[$caseId].Case `
        -Games @($Game) `
        -Paths $paths
    $practiceByCaseId[[string]$practice.MovesetCaseId] = $practice
}

$tasks = [Collections.Generic.List[object]]::new()
$gridPlans = [Collections.Generic.List[object]]::new()
foreach ($outputPlan in $selectedOutputPlans) {
    $outputName = '{0}_{1}' -f $outputPlan.Name, $gridVariant
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
                $gameSelector)
        if (-not $practiceByCaseId.ContainsKey($capture.CaseId)) {
            throw (
                "Practice data was not resolved for moveset case " +
                "'$($capture.CaseId)'."
            )
        }
        $practice = $practiceByCaseId[$capture.CaseId]
        if (-not $practice.PnachByGame.ContainsKey($gameSelector) -or
            -not $practice.PnachLinesByGame.ContainsKey($gameSelector)) {
            throw (
                "Practice data for moveset case '$($capture.CaseId)' does not " +
                "contain game $gameSelector."
            )
        }
        $pnachByGame = @{}
        $pnachByGame[$gameSelector] = $practice.PnachByGame[$gameSelector]
        $pnachLinesByGame = @{}
        $pnachLinesByGame[$gameSelector] = $practice.PnachLinesByGame[$gameSelector]
        $taskContext = [pscustomobject]@{
            CaseId = $capture.CaseId
            Character = [string](
                $indexedMovesetsByCaseId[$capture.CaseId].CharacterName
            )
            Recording = $capture.Recording
            Game = $Game
            GameLabel = $gameLabel
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
            $gridVariant,
            $captureIndex
        if ((Test-Path -LiteralPath $taskContext.CompletePath -PathType Leaf) -and
            (Get-VisualRegressionPngCount -Directory $taskContext.CaptureRoot) -gt 0) {
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

                    $screenshotCount = Get-VisualRegressionPngCount `
                        -Directory $Context.CaptureRoot
                    if ($screenshotCount -eq 0) {
                        throw (
                            "$($Context.GameLabel) snapshot replay produced " +
                            "no screenshots for moveset case " +
                            "'$($Context.CaseId)'."
                        )
                    }
                    Write-VisualRegressionJson -Path $Context.CompletePath -Value ([ordered]@{
                        case_id = $Context.CaseId
                        recording = $Context.Recording
                        game = $Context.Game
                        screenshots = $screenshotCount
                        completed_utc = (Get-Date).ToUniversalTime().ToString('O')
                    })
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

    [void]$gridPlans.Add([pscustomobject]@{
        Context = [pscustomobject]@{
            Name = $outputName
            Captures = @($captureContexts)
            CanonicalVariant = $gridVariant
            AlwaysGrid = $outputPlan.Family -ceq 'idle'
            GridRoot = Join-Path $workingRoot 'grid'
            GridInput = Join-Path $workingRoot 'grid-input'
            FinalGrid = $finalGrid
            WorkingRoot = $workingRoot
        }
        DependsOn = @($captureTaskKeys)
    })
}

$gridJobScript = {
    param($Context, $GridScript, $SuiteScript)
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
            $captureScreenshots = @(
                Get-ChildItem `
                    -LiteralPath $capture.CaptureRoot `
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

    . $SuiteScript
    Invoke-VisualRegressionFileOperation `
        -Description "Removing generated capture directory '$($Context.WorkingRoot)'" `
        -Operation {
            if (Test-Path -LiteralPath $Context.WorkingRoot -PathType Container) {
                Remove-Item `
                    -LiteralPath $Context.WorkingRoot `
                    -Recurse `
                    -Force `
                    -ErrorAction Stop
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
            -ArgumentList @($gridContext, $gridScript, $taskScript) `
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
$gridCount = Get-VisualRegressionPngCount -Directory $gridOutputRoot
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
