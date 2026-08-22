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
$movesetsPath = Join-Path ([string]$paths.resources) 'movesets.tsv'
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

function Get-MovesetRowKind {
    param([Parameter(Mandatory)]$Moveset)

    if (-not [string]::IsNullOrWhiteSpace([string]$Moveset.awakening_id)) {
        return 'awakening'
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$Moveset.linked_j_id) -or
        -not [string]::IsNullOrWhiteSpace([string]$Moveset.linked_uj_id)) {
        return 'support'
    }
    if ([string]$Moveset.reversal -ceq 'Y') {
        return 'reversal'
    }
    return 'base'
}

$indexedMovesets = @(
    for ($index = 0; $index -lt $movesets.Count; $index++) {
        [pscustomobject]@{
            Row = $index + 2
            Data = $movesets[$index]
            Kind = Get-MovesetRowKind -Moveset $movesets[$index]
        }
    }
)
$blocks = [Collections.Generic.List[object]]::new()
$currentBlock = $null
foreach ($movesetRow in $indexedMovesets) {
    if ($movesetRow.Kind -ceq 'base') {
        $currentBlock = [pscustomobject]@{
            Base = $movesetRow
            Rows = [Collections.Generic.List[object]]::new()
        }
        [void]$blocks.Add($currentBlock)
    }
    elseif ($null -eq $currentBlock) {
        throw "Moveset row $($movesetRow.Row) has no preceding base row."
    }
    elseif (
        [string]$movesetRow.Data.character -cne
            [string]$currentBlock.Base.Data.character -or
        [string]$movesetRow.Data.id -cne
            [string]$currentBlock.Base.Data.id
    ) {
        throw (
            "Moveset row $($movesetRow.Row) does not match its base row " +
            "$($currentBlock.Base.Row)."
        )
    }
    [void]$currentBlock.Rows.Add($movesetRow)
}

$blocksByCharacter = @{}
foreach ($block in $blocks) {
    $key = (
        "$($block.Base.Data.character)`t" +
        [string]$block.Base.Data.id
    )
    $blocksByCharacter[$key] = $block
}

$outputPlans = [Collections.Generic.List[object]]::new()
for ($characterIndex = $firstRow - 2; $characterIndex -le $lastRow - 2; $characterIndex++) {
    $character = $characterData[$characterIndex]
    $key = "$($character.character)`t$($character.id)"
    if (-not $blocksByCharacter.ContainsKey($key)) {
        throw (
            "Character_data.tsv row $($characterIndex + 2) has no matching " +
            'movesets.tsv block.'
        )
    }
    $block = $blocksByCharacter[$key]
    $outputNumber = $characterIndex + 2
    if ($MovesetFamily -ceq 'idle') {
        continue
    }

    foreach ($awakeningRow in @(
        $block.Rows | Where-Object Kind -CEQ 'awakening'
    )) {
        $uniqueness = ([string]$awakeningRow.Data.uniqueness).Trim()
        if ($uniqueness -cnotin @('', '-', '+', 's', 'd-', 'd+', 'ds')) {
            throw (
                "Moveset row $($awakeningRow.Row) has invalid uniqueness " +
                "'$uniqueness'."
            )
        }
    }
    foreach ($duplicateKind in @('d-', 'd+', 'ds')) {
        $duplicateRows = @(
            $block.Rows | Where-Object {
                $_.Kind -ceq 'awakening' -and
                ([string]$_.Data.uniqueness).Trim() -ceq $duplicateKind
            }
        )
        if ($duplicateRows.Count -notin @(0, 2)) {
            throw (
                "Moveset base row $($block.Base.Row) has " +
                "$($duplicateRows.Count) '$duplicateKind' awakenings; " +
                'duplicate uniqueness requires exactly two.'
            )
        }
    }

    $slug = ([string]$block.Base.Data.character).ToLowerInvariant()
    $slug = [regex]::Replace($slug, '[^a-z0-9]+', '_')
    $slug = $slug.Trim('_')
    if ([string]::IsNullOrWhiteSpace($slug)) {
        $slug = 'character'
    }
    [void]$outputPlans.Add([pscustomobject]@{
        Name = ('{0:D3}_{1}_base' -f $outputNumber, $slug)
        Family = 'base'
        Captures = @(
            [pscustomobject]@{
                Row = $block.Base.Row
                Recording = 'movesets\base.p2m2'
            }
        )
    })
    $emittedDuplicateBase = $false
    foreach ($awakeningRow in @(
        $block.Rows | Where-Object Kind -CEQ 'awakening'
    )) {
        $uniqueness = ([string]$awakeningRow.Data.uniqueness).Trim()
        $isUniqueMode = $false
        if ($uniqueness -ceq '+') {
            $isUniqueMode = $true
        }
        elseif ($uniqueness -ceq 'd+' -and -not $emittedDuplicateBase) {
            $emittedDuplicateBase = $true
            $isUniqueMode = $true
        }
        if (-not $isUniqueMode) {
            continue
        }
        $awakeningId = [string]$awakeningRow.Data.awakening_id
        [void]$outputPlans.Add([pscustomobject]@{
            Name = ('{0:D3}_{1}_mode_{2}' -f $outputNumber, $slug, $awakeningId)
            Family = 'base'
            Captures = @(
                [pscustomobject]@{
                    Row = $awakeningRow.Row
                    Recording = 'movesets\base.p2m2'
                }
            )
        })
    }

    $hasReversal = @(
        $block.Rows | Where-Object Kind -CEQ 'reversal'
    ).Count -gt 0
    if ($hasReversal) {
        $secondFormBlock = $null
        if ($characterIndex + 1 -lt $characterData.Count) {
            $secondForm = $characterData[$characterIndex + 1]
            $secondFormKey = "$($secondForm.character)`t$($secondForm.id)"
            if ($blocksByCharacter.ContainsKey($secondFormKey)) {
                $candidate = $blocksByCharacter[$secondFormKey]
                $candidateHasReversal = @(
                    $candidate.Rows | Where-Object Kind -CEQ 'reversal'
                ).Count -gt 0
                if (-not $candidateHasReversal) {
                    $secondFormBlock = $candidate
                }
            }
        }

        $specialCaptures = [Collections.Generic.List[object]]::new()
        [void]$specialCaptures.Add([pscustomobject]@{
            Row = $block.Base.Row
            Recording = 'movesets\specials.p2m2'
        })
        $emittedDuplicatePlusSpecials = $false
        $emittedDuplicateSpecials = $false
        foreach ($movesetRow in $block.Rows) {
            $include = switch ($movesetRow.Kind) {
                'awakening' {
                    $uniqueness = ([string]$movesetRow.Data.uniqueness).Trim()
                    if ($uniqueness -cin @('+', 's')) {
                        $true
                    }
                    elseif ($uniqueness -ceq 'd+' -and
                        -not $emittedDuplicatePlusSpecials) {
                        $emittedDuplicatePlusSpecials = $true
                        $true
                    }
                    elseif ($uniqueness -ceq 'ds' -and
                        -not $emittedDuplicateSpecials) {
                        $emittedDuplicateSpecials = $true
                        $true
                    }
                    else {
                        $false
                    }
                    break
                }
                'support' { $true; break }
                'reversal' { $true; break }
                default { $false }
            }
            if ($include) {
                [void]$specialCaptures.Add([pscustomobject]@{
                    Row = $movesetRow.Row
                    Recording = 'movesets\specials.p2m2'
                })
            }
        }
        if ($null -ne $secondFormBlock) {
            [void]$specialCaptures.Add([pscustomobject]@{
                Row = $secondFormBlock.Base.Row
                Recording = 'movesets\specials.p2m2'
            })
        }
        [void]$outputPlans.Add([pscustomobject]@{
            Name = ('{0:D3}_{1}_specials' -f $outputNumber, $slug)
            Family = 'specials'
            Captures = @($specialCaptures)
        })
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
            $key = "$($character.character)`t$($character.id)"
            if (-not $blocksByCharacter.ContainsKey($key)) {
                throw (
                    "Character_data.tsv row $($characterIndex + 2) has no matching " +
                    'movesets.tsv block.'
                )
            }
            [void]$pageCaptures.Add([pscustomobject]@{
                Row = $blocksByCharacter[$key].Base.Row
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
$practiceRows = @(
    $selectedOutputPlans |
        ForEach-Object Captures |
        ForEach-Object { [int]$_.Row } |
        Sort-Object -Unique
)
$practiceGames = [string[]]@($gameTargets | ForEach-Object Selector)
$practiceByRow = @{}
foreach ($practice in @(
    Get-VisualRegressionPracticeConfiguration `
        -Repository $ProjectRoot `
        -MovesetRow $practiceRows `
        -Game $practiceGames
)) {
    $practiceByRow[[int]$practice.MovesetRow] = $practice
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
                ('captures\{0:D3}-{1:D3}\{2}' -f
                    $captureIndex,
                    $capture.Row,
                    $gameTarget.Selector)
            if (-not $practiceByRow.ContainsKey($capture.Row)) {
                throw "Practice data was not resolved for moveset row $($capture.Row)."
            }
            $practice = $practiceByRow[$capture.Row]
            if (-not $practice.PnachByGame.ContainsKey($gameTarget.Selector) -or
                -not $practice.PnachLinesByGame.ContainsKey($gameTarget.Selector)) {
                throw (
                    "Practice data for moveset row $($capture.Row) does not " +
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
                Row = $capture.Row
                Character = [string]$movesets[$capture.Row - 2].character
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
                            "Capturing $($Context.GameLabel) moveset row " +
                            "$($Context.Row) with $($Context.Recording) -> " +
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
                                'no screenshots for moveset row ' +
                                "$($Context.Row)."
                            )
                        }
                        $complete = [ordered]@{
                            row = $Context.Row
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
                            Row = $Context.Row
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
                                "No screenshots remain for moveset row " +
                                "$($capture.Row)."
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
