[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidatePattern('^(?:all|\d+(?:-\d+)?)$')]
    [string]$Range,

    [ValidateRange(1, 64)]
    [int]$ThrottleLimit = 16,

    [string]$OutputRoot,

    [string]$ProjectRoot = (Join-Path $PSScriptRoot '..\..\..')
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = [IO.Path]::GetFullPath($ProjectRoot)

. (Join-Path $ProjectRoot 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths -ManifestPath (Join-Path $ProjectRoot 'paths.json')

$characterDataPath = Join-Path ([string]$paths.resources) 'character_data.tsv'
$characterData = @(Import-Csv -LiteralPath $characterDataPath -Delimiter "`t")
$movesetsPath = Join-Path ([string]$paths.resources) 'movesets.tsv'
$movesets = @(Import-Csv -LiteralPath $movesetsPath -Delimiter "`t")
$lastAvailableRow = $characterData.Count + 1
$firstRow, $lastRow = if ($Range -ieq 'all') {
    2, $lastAvailableRow
}
elseif ($Range -match '^\d+$') {
    [int]$Range, [int]$Range
}
else {
    $rangeMatch = [regex]::Match($Range, '^(\d+)-(\d+)$')
    [int]$rangeMatch.Groups[1].Value,
    [int]$rangeMatch.Groups[2].Value
}
if ($firstRow -lt 2 -or $lastRow -lt $firstRow) {
    throw (
        "Range must be 'all', one physical TSV row, or an inclusive " +
        'physical TSV row range starting at row 2.'
    )
}
if ($lastRow -gt $lastAvailableRow) {
    throw (
        "Range ends at row $lastRow, but character_data.tsv ends at row " +
        "$lastAvailableRow."
    )
}

$workRoot = [IO.Path]::GetFullPath((Join-Path $ProjectRoot 'work'))
$runRoot = if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    [IO.Path]::GetFullPath((Join-Path $workRoot 'captures\movesets'))
}
elseif ([IO.Path]::IsPathRooted($OutputRoot)) {
    [IO.Path]::GetFullPath($OutputRoot)
}
else {
    [IO.Path]::GetFullPath((Join-Path $ProjectRoot $OutputRoot))
}
$relativeOutput = [IO.Path]::GetRelativePath($workRoot, $runRoot)
if ($relativeOutput -eq '.' -or
    [IO.Path]::IsPathRooted($relativeOutput) -or
    $relativeOutput -eq '..' -or
    $relativeOutput.StartsWith(
        '..' + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::Ordinal
    )) {
    throw "Moveset output must be below the project work directory: $runRoot"
}
[void](New-Item -ItemType Directory -Path $runRoot -Force)

$practiceScript = Join-Path $ProjectRoot 'scripts\na228\practice.ps1'
$gridScript = Join-Path `
    $ProjectRoot `
    'scripts\research\localization\compare_font_capture_sets.ps1'
$launcher = [string]$paths.files.pcsx2_game_launch_command
$taskScript = Join-Path $ProjectRoot 'e2e\scripts\suite.ps1'
. $taskScript

$e2eRoot = Join-Path $ProjectRoot 'e2e'
$publishedE2eVariant = & {
    param($ConfigScript, $Root)

    . $ConfigScript
    (Get-E2eConfiguration -Root $Root).PublishedVariant
} (Join-Path $e2eRoot 'scripts\config.ps1') $e2eRoot
$currentE2eVariant = [string]$publishedE2eVariant.name
$currentGame = [string]$publishedE2eVariant.build
$gameTargets = @(
    [pscustomobject]@{
        Selector = 'nun5'
        Suffix = 'a-reference'
        GridVariant = 'a_reference'
        Label = 'NUN5 reference'
    }
    [pscustomobject]@{
        Selector = $currentGame
        Suffix = 'b-current'
        GridVariant = 'b_current'
        Label = 'NA2.28 current'
    }
)

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
    $slug = [regex]::Replace($slug, '[^a-z0-9]+', '-')
    $slug = $slug.Trim('-')
    if ([string]::IsNullOrWhiteSpace($slug)) {
        $slug = 'character'
    }
    [void]$outputPlans.Add([pscustomobject]@{
        Name = ('{0:D3}-{1}-base' -f $outputNumber, $slug)
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
            Name = ('{0:D3}-{1}-mode-{2}' -f $outputNumber, $slug, $awakeningId)
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
        [void]$outputPlans.Add([pscustomobject]@{
            Name = ('{0:D3}-{1}-specials' -f $outputNumber, $slug)
            Captures = @($specialCaptures)
        })
    }
}

$practiceRows = @(
    $outputPlans |
        ForEach-Object Captures |
        ForEach-Object { [int]$_.Row } |
        Sort-Object -Unique
)
$buildResult = @(
    & (Join-Path $ProjectRoot 'scripts\na228\build.ps1') `
        -E2eVariant $currentE2eVariant
) | Where-Object {
    [string]$_.Status -ceq 'e2e-test' -and
    [string]$_.E2eVariant -ceq $currentE2eVariant
} | Select-Object -Last 1
if ($null -eq $buildResult) {
    throw "E2E Test $currentE2eVariant build returned no valid result."
}

$practiceGames = [string[]]@($gameTargets | ForEach-Object Selector)
$practiceByRow = @{}
foreach ($practice in @(
    & $practiceScript `
        -MovesetRow $practiceRows `
        -Games $practiceGames `
        -ProjectRoot $ProjectRoot
)) {
    $practiceByRow[[int]$practice.MovesetRow] = $practice
}

$tasks = [Collections.Generic.List[object]]::new()
$gridPlans = [Collections.Generic.List[object]]::new()
foreach ($outputPlan in $outputPlans) {
    foreach ($gameTarget in $gameTargets) {
        $outputName = "$($outputPlan.Name)-$($gameTarget.Suffix)"
        $workingRoot = Join-Path $runRoot $outputName
        $finalGrid = Join-Path $runRoot ($outputName + '.png')
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
                InputRecordingsRoot = [string]$paths.pcsx2_input_recordings
                CaptureRoot = $captureRoot
                CaseRoot = Split-Path -Parent $captureRoot
                PnachByGame = $pnachByGame
                PnachLinesByGame = $pnachLinesByGame
            }
            [void]$captureContexts.Add($taskContext)

            $taskName = 'capture-{0}-{1}-{2:D3}' -f
                $outputPlan.Name,
                $gameTarget.GridVariant,
                $captureIndex
            [void]$captureTaskKeys.Add($taskName)
            $startTask = {
                Start-ThreadJob `
                    -Name $taskName `
                    -ThrottleLimit $ThrottleLimit `
                    -ArgumentList @(
                        $taskContext,
                        $launcher,
                        $ProjectRoot
                    ) `
                    -ScriptBlock {
                        param($Context, $Launcher, $Repository)
                        $ErrorActionPreference = 'Stop'
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
                        & $Launcher `
                            -Games @($Context.Game) `
                            -Play $Context.Recording `
                            -Snapshots `
                            -InputRecordingCaptureMode screenshots `
                            -CaptureDirectory $Context.CaptureRoot `
                            -ReadOnlySettings `
                            -PnachByGame $Context.PnachByGame `
                            -PnachLinesByGame $Context.PnachLinesByGame `
                            -ProjectRoot $Repository `
                            -InputRecordingsRoot $Context.InputRecordingsRoot

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
                            $canonicalName = '{0:D4}_{1}.png' -f
                                $slot,
                                $Context.CanonicalVariant
                            [void](New-Item `
                                -ItemType HardLink `
                                -Path (Join-Path $Context.GridInput $canonicalName) `
                                -Target $screenshot.FullName)
                        }
                    }
                    if ($slot -gt 32) {
                        throw (
                            "Moveset grid $($Context.Name) contains $slot " +
                            'screenshots; one grid supports at most 32.'
                        )
                    }
                    $gridColumns = if ($slot -le 4) {
                        $slot
                    }
                    else {
                        [Math]::Min(8, [int][Math]::Ceiling($slot / 2.0))
                    }
                    & $GridScript `
                        -ScreenshotDirectory $Context.GridInput `
                        -OutputDirectory $Context.GridRoot `
                        -GridColumns $gridColumns `
                        -GridItemsPerPage $slot
                    if ($LASTEXITCODE -ne 0) {
                        throw "Grid generation failed for $($Context.Name)."
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

Write-Host "NUN5/NA2.28 moveset grids: $runRoot" -ForegroundColor Green
