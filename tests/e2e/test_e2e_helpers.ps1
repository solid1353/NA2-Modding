[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
. (Join-Path $repository 'e2e\scripts\config.ps1')
. (Join-Path $repository 'e2e\scripts\suite.ps1')

function Assert-E2eHelperTest {
    param(
        [Parameter(Mandatory)][bool]$Condition,
        [Parameter(Mandatory)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

$testRoot = Join-Path (
    [IO.Path]::GetTempPath()
) "na2-e2e-helper-tests-$PID-$([guid]::NewGuid().ToString('N'))"
try {
    [void](New-Item -ItemType Directory -Path $testRoot -Force)

    $omittedSuites = @(
        Get-VisualRegressionRequestedSuiteNames `
            -Suite $null `
            -WasSpecified $false
    )
    $selectedSuites = @(
        Get-VisualRegressionRequestedSuiteNames `
            -Suite @('collection/characters', 'collection/figures') `
            -WasSpecified $true
    )
    $blankSuiteRejected = $false
    try {
        Get-VisualRegressionRequestedSuiteNames `
            -Suite @('collection/characters', '') `
            -WasSpecified $true
    }
    catch {
        $blankSuiteRejected = $_.Exception.Message -ceq (
            'Suite cannot contain an empty name.'
        )
    }
    Assert-E2eHelperTest `
        -Condition (
            $omittedSuites.Count -eq 0 -and
            ($selectedSuites -join ',') -ceq (
                'collection/characters,collection/figures'
            ) -and
            $blankSuiteRejected
        ) `
        -Message 'E2E suite selection did not distinguish omission from an explicitly blank name.'

    $singleMovesetRow = Resolve-VisualRegressionMovesetRange `
        -Range '8' `
        -LastAvailableRow 20
    $movesetRows = Resolve-VisualRegressionMovesetRange `
        -Range '8-18' `
        -LastAvailableRow 20
    $reversedMovesetRangeRejected = $false
    $outsideMovesetRangeRejected = $false
    try {
        Resolve-VisualRegressionMovesetRange -Range '18-8' -LastAvailableRow 20
    }
    catch {
        $reversedMovesetRangeRejected = $true
    }
    try {
        Resolve-VisualRegressionMovesetRange -Range '1' -LastAvailableRow 20
    }
    catch {
        $outsideMovesetRangeRejected = $true
    }
    Assert-E2eHelperTest `
        -Condition (
            $singleMovesetRow.FirstRow -eq 8 -and
            $singleMovesetRow.LastRow -eq 8 -and
            $singleMovesetRow.Value -ceq '8' -and
            $movesetRows.FirstRow -eq 8 -and
            $movesetRows.LastRow -eq 18 -and
            $movesetRows.Value -ceq '8-18' -and
            $reversedMovesetRangeRejected -and
            $outsideMovesetRangeRejected
        ) `
        -Message 'Movesets range parsing or character-data row bounds regressed.'

    $poolRoot = Join-Path $testRoot 'shared-concurrency-pool'
    $poolPermit = Enter-VisualRegressionConcurrencyPool -Root $poolRoot -Capacity 1
    $poolReady = Join-Path $poolRoot 'waiter-ready'
    $poolAcquired = Join-Path $poolRoot 'waiter-acquired'
    $poolJob = Start-Job -ArgumentList @(
        (Join-Path $repository 'e2e\scripts\suite.ps1'),
        $poolRoot,
        $poolReady,
        $poolAcquired
    ) -ScriptBlock {
        param($SuiteScript, $PoolRoot, $ReadyPath, $AcquiredPath)
        $ErrorActionPreference = 'Stop'
        . $SuiteScript
        [IO.File]::WriteAllText($ReadyPath, '')
        $permit = Enter-VisualRegressionConcurrencyPool -Root $PoolRoot -Capacity 1
        try {
            [IO.File]::WriteAllText($AcquiredPath, '')
        }
        finally {
            $permit.Dispose()
        }
    }
    try {
        $deadline = [DateTime]::UtcNow.AddSeconds(5)
        while (-not (Test-Path -LiteralPath $poolReady -PathType Leaf)) {
            if ([DateTime]::UtcNow -ge $deadline) {
                throw 'Shared concurrency-pool waiter did not start.'
            }
            Start-Sleep -Milliseconds 20
        }
        Start-Sleep -Milliseconds 100
        Assert-E2eHelperTest `
            -Condition (-not (Test-Path -LiteralPath $poolAcquired -PathType Leaf)) `
            -Message 'Shared concurrency pool exceeded its capacity.'
        $poolPermit.Dispose()
        $poolPermit = $null
        Wait-Job -Job $poolJob -Timeout 5 | Out-Null
        Receive-Job -Job $poolJob -ErrorAction Stop | Out-Null
        Assert-E2eHelperTest `
            -Condition (
                $poolJob.State -ceq 'Completed' -and
                (Test-Path -LiteralPath $poolAcquired -PathType Leaf)
            ) `
            -Message 'Released shared concurrency capacity was not reused by another process.'
    }
    finally {
        if ($null -ne $poolPermit) {
            $poolPermit.Dispose()
        }
        if ($poolJob.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $poolJob -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $poolJob -Force -ErrorAction SilentlyContinue
    }

    $replayRepository = Join-Path $testRoot 'screenshot-replay'
    $replayLibrary = Join-Path $replayRepository 'scripts\lib'
    $replayRecordings = Join-Path $replayRepository 'recordings'
    $replayCapture = Join-Path $replayRepository 'capture'
    $replayLauncher = Join-Path $replayRepository 'launcher.ps1'
    [void](New-Item -ItemType Directory -Path $replayLibrary, $replayRecordings -Force)
    [IO.File]::WriteAllText((Join-Path $replayRepository 'paths.json'), '{}')
    [IO.File]::WriteAllText(
        (Join-Path $replayLibrary 'paths.ps1'),
        @"
function Get-Na2Paths {
    [pscustomobject]@{
        files = [pscustomobject]@{
            pcsx2_game_launch_command = '$($replayLauncher.Replace("'", "''"))'
        }
    }
}
"@
    )
    [IO.File]::WriteAllText(
        $replayLauncher,
        @'
param(
    [string[]]$Games,
    [string]$Play,
    [switch]$Snapshots,
    [string]$InputRecordingCaptureMode,
    [string]$CaptureDirectory,
    [string]$InputRecordingsRoot,
    [string]$ProjectRoot
)
[void](New-Item -ItemType Directory -Path (Join-Path $CaptureDirectory 'screenshots') -Force)
[IO.File]::WriteAllText((Join-Path $CaptureDirectory 'screenshots\0001.png'), 'screenshot')
[IO.File]::WriteAllText(
    (Join-Path $ProjectRoot 'launcher.json'),
    ([ordered]@{
        snapshots = $Snapshots.IsPresent
        capture_mode = $InputRecordingCaptureMode
        play = $Play
    } | ConvertTo-Json)
)
'@
    )
    $replayRecording = Join-Path $replayRecordings 'recording.p2m2'
    $replayPool = Join-Path $replayRepository 'command-pool'
    [IO.File]::WriteAllText($replayRecording, 'recording')
    Invoke-VisualRegressionPooledReplay `
        -Repository $replayRepository `
        -SharedRecordingRoot $replayRecordings `
        -RecordingPath $replayRecording `
        -Game 'e2e_test' `
        -CaptureRoot $replayCapture `
        -ConcurrencyPoolRoot $replayPool `
        -ConcurrencyLimit 16
    $replayInvocation = Get-Content `
        -Raw `
        -LiteralPath (Join-Path $replayRepository 'launcher.json') |
        ConvertFrom-Json
    Assert-E2eHelperTest `
        -Condition (
            $replayInvocation.snapshots -and
            $replayInvocation.capture_mode -ceq 'screenshots' -and
            (Test-Path -LiteralPath (Join-Path $replayCapture 'screenshots\0001.png')) -and
            (Test-Path -LiteralPath (Join-Path $replayPool 'slot-01.lock')) -and
            -not (Test-Path -LiteralPath (Join-Path $replayCapture 'sstates'))
        ) `
        -Message 'E2E replay did not use the command pool or screenshot-only PCSX2 capture.'

    $generatedDiscoveryRoot = Join-Path $testRoot 'generated-discovery\e2e'
    $generatedSuiteRoot = Join-Path $generatedDiscoveryRoot 'recordings'
    $generatedScriptRoot = Join-Path $generatedDiscoveryRoot 'scripts'
    [void](New-Item -ItemType Directory -Path `
        (Join-Path $generatedSuiteRoot 'collection'), `
        (Join-Path $generatedSuiteRoot 'movesets'), `
        $generatedScriptRoot `
        -Force)
    [IO.File]::WriteAllText(
        (Join-Path $generatedSuiteRoot 'collection\test.p2m2'),
        'recording'
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedSuiteRoot 'movesets\base.p2m2'),
        'generated input, not a suite'
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedScriptRoot 'movesets.ps1'),
        '# generated suite'
    )
    $generatedSuiteNames = @(
        Get-VisualRegressionSuiteNames -RecordingRepository $generatedSuiteRoot
    )
    Assert-E2eHelperTest `
        -Condition (($generatedSuiteNames -join ',') -ceq 'collection/test,movesets') `
        -Message 'Generated suite discovery did not add movesets or exclude its input recordings.'
    $generatedIdleContext = Get-VisualRegressionContext -Suite 'movesets/idle'
    Assert-E2eHelperTest `
        -Condition (
            $generatedIdleContext.Generated -and
            $generatedIdleContext.GeneratedFamily -ceq 'idle' -and
            $generatedIdleContext.SuiteRelativePath -ceq 'movesets' -and
            [IO.Path]::GetFileName($generatedIdleContext.CaptureRoot) -ceq 'movesets'
        ) `
        -Message 'Generated moveset sub-suite selection did not retain the shared capture root.'

    $generatedStageRoot = Join-Path $testRoot 'generated-grid-stage'
    $existingGrids = Join-Path $generatedStageRoot 'existing'
    $capturedCurrentGrids = Join-Path $generatedStageRoot 'captured-current'
    $capturedReferenceGrids = Join-Path $generatedStageRoot 'captured-reference'
    $stagedGrids = Join-Path $generatedStageRoot 'staged'
    [void](New-Item -ItemType Directory -Path `
        $existingGrids, `
        $capturedCurrentGrids, `
        $capturedReferenceGrids `
        -Force)
    [IO.File]::WriteAllText(
        (Join-Path $existingGrids '002-naruto-base-a-reference.png'),
        'accepted reference'
    )
    [IO.File]::WriteAllText(
        (Join-Path $existingGrids '002-naruto-base-b-current.png'),
        'stale current'
    )
    [IO.File]::WriteAllText((Join-Path $existingGrids 'stale.png'), 'stale')
    [IO.File]::WriteAllText(
        (Join-Path $capturedCurrentGrids '002-naruto-base-b-current.png'),
        'new current'
    )
    [void](New-VisualRegressionGeneratedGridStage `
        -ExistingDirectory $existingGrids `
        -CapturedDirectory $capturedCurrentGrids `
        -OutputDirectory $stagedGrids `
        -CapturedTier Current)
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $stagedGrids '002-naruto-base-a-reference.png')) -ceq 'accepted reference' -and
            [IO.File]::ReadAllText((Join-Path $stagedGrids '002-naruto-base-b-current.png')) -ceq 'new current' -and
            -not (Test-Path -LiteralPath (Join-Path $stagedGrids 'stale.png'))
        ) `
        -Message 'Generated current-grid staging did not preserve only reference history.'
    [IO.File]::WriteAllText(
        (Join-Path $capturedReferenceGrids '002-naruto-base-a-reference.png'),
        'new reference'
    )
    [void](New-VisualRegressionGeneratedGridStage `
        -ExistingDirectory $stagedGrids `
        -CapturedDirectory $capturedReferenceGrids `
        -OutputDirectory $existingGrids `
        -CapturedTier Reference)
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $existingGrids '002-naruto-base-a-reference.png')) -ceq 'new reference' -and
            [IO.File]::ReadAllText((Join-Path $existingGrids '002-naruto-base-b-current.png')) -ceq 'new current' -and
            -not (Test-Path -LiteralPath (Join-Path $existingGrids 'stale.png'))
        ) `
        -Message 'Generated reference-grid staging did not preserve only current history.'

    $generatedRunRepository = Join-Path $testRoot 'generated-run-repository'
    $generatedRunRoot = Join-Path $generatedRunRepository 'e2e'
    $generatedRunScripts = Join-Path $generatedRunRoot 'scripts'
    $generatedRunCapture = Join-Path $generatedRunRoot 'captures\movesets\screenshots'
    $generatedRunResources = Join-Path $generatedRunRepository 'resources'
    $generatedRunRecordings = Join-Path $generatedRunRepository 'pcsx2_files\input_recordings'
    $generatedRunLibrary = Join-Path $generatedRunRepository 'scripts\lib'
    $generatedRunComparatorRoot = Join-Path `
        $generatedRunRepository `
        'scripts\research\localization'
    [void](New-Item -ItemType Directory -Path `
        $generatedRunScripts, `
        $generatedRunCapture, `
        $generatedRunResources, `
        (Join-Path $generatedRunRecordings 'e2e\movesets'), `
        $generatedRunLibrary, `
        $generatedRunComparatorRoot `
        -Force)
    foreach ($file in @('suite.ps1', 'run.ps1', 'config.ps1')) {
        Copy-Item `
            -LiteralPath (Join-Path $repository "e2e\scripts\$file") `
            -Destination (Join-Path $generatedRunScripts $file)
    }
    Copy-Item `
        -LiteralPath (Join-Path $repository 'e2e\config.json') `
        -Destination (Join-Path $generatedRunRoot 'config.json')
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunScripts 'movesets.ps1'),
        '# generated suite'
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunResources 'character_data.tsv'),
        "character`tcharacter_id`nNaruto`t1`n"
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunResources 'movesets.tsv'),
        "character`tid`nNaruto`t1`n"
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunRecordings 'e2e\movesets\base.p2m2'),
        'recording'
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunLibrary 'paths.ps1'),
        @"
function Get-Na2Paths {
    [pscustomobject]@{
        resources = '$($generatedRunResources.Replace("'", "''"))'
        pcsx2_input_recordings = '$($generatedRunRecordings.Replace("'", "''"))'
    }
}
"@
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunComparatorRoot 'compare_font_capture_sets.ps1'),
        @'
param(
    [string]$PairedGridDirectory,
    [string]$OutputDirectory,
    [string]$Kind
)
foreach ($reference in Get-ChildItem -LiteralPath $PairedGridDirectory -Filter '*-a-reference.png' -File) {
    $caseName = $reference.Name.Substring(
        0,
        $reference.Name.Length - '-a-reference.png'.Length
    )
    $current = Join-Path $PairedGridDirectory ($caseName + '-b-current.png')
    if (-not (Test-Path -LiteralPath $current -PathType Leaf)) {
        continue
    }
    $directories = if ([string]::IsNullOrWhiteSpace($Kind)) {
        @('pairs', 'blends', 'diffs')
    }
    else {
        @($Kind.ToLowerInvariant() + 's')
    }
    foreach ($directory in $directories) {
        $targetRoot = Join-Path $OutputDirectory $directory
        [void](New-Item -ItemType Directory -Path $targetRoot -Force)
        Copy-Item `
            -LiteralPath $reference.FullName `
            -Destination (Join-Path $targetRoot ($caseName + '.png')) `
            -Force
    }
}
exit 0
'@
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunScripts 'variant.ps1'),
        @'
param(
    [string]$Variant,
    [string]$Transaction,
    [string[]]$Suite,
    [string]$MovesetRange,
    [string]$ConcurrencyPoolRoot,
    [int]$ConcurrencyLimit
)
[IO.File]::WriteAllText(
    (Join-Path $PSScriptRoot "command-pool-$Variant.txt"),
    $ConcurrencyPoolRoot
)
[IO.File]::WriteAllText(
    (Join-Path $PSScriptRoot "command-limit-$Variant.txt"),
    [string]$ConcurrencyLimit
)
if (-not [string]::IsNullOrWhiteSpace($MovesetRange)) {
    [IO.File]::WriteAllText(
        (Join-Path $PSScriptRoot 'moveset-range.txt'),
        $MovesetRange
    )
}
foreach ($suiteName in $Suite) {
    $suiteRoot = Join-Path `
        (Join-Path (Join-Path (Join-Path $Transaction 'jobs') $Variant) 'suites') `
        $suiteName.Replace('/', [IO.Path]::DirectorySeparatorChar)
    $grids = Join-Path $suiteRoot 'capture\screenshots'
    [void](New-Item -ItemType Directory -Path $grids -Force)
    $gridName = '002-naruto-base-b-current.png'
    $gridContent = if ([string]::IsNullOrWhiteSpace($MovesetRange)) {
        'identical current grid'
    }
    else {
        "range $MovesetRange current grid"
    }
    [IO.File]::WriteAllText((Join-Path $grids $gridName), $gridContent)
    [IO.File]::WriteAllText(
        (Join-Path $suiteRoot 'complete.json'),
        '{"screenshots":1}'
    )
}
$jobRoot = Join-Path (Join-Path $Transaction 'jobs') $Variant
[IO.File]::WriteAllText((Join-Path $jobRoot 'ready.json'), '{}')
'@
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunCapture '002-naruto-base-a-reference.png'),
        'accepted reference grid'
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunCapture '002-naruto-base-b-current.png'),
        'stale current grid'
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunRoot 'captures\movesets\stale.txt'),
        'stale generated artifact'
    )
    & (Join-Path $generatedRunScripts 'run.ps1') `
        -Suite 'movesets' `
        -Shifted | Out-Null
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $generatedRunCapture '002-naruto-base-a-reference.png')) -ceq 'accepted reference grid' -and
            [IO.File]::ReadAllText((Join-Path $generatedRunCapture '002-naruto-base-b-current.png')) -ceq 'identical current grid' -and
            [IO.File]::ReadAllText((Join-Path $generatedRunScripts 'command-pool-normal.txt')) -ceq
                [IO.File]::ReadAllText((Join-Path $generatedRunScripts 'command-pool-shifted.txt')) -and
            -not [string]::IsNullOrWhiteSpace([IO.File]::ReadAllText((Join-Path $generatedRunScripts 'command-pool-normal.txt'))) -and
            [IO.File]::ReadAllText((Join-Path $generatedRunScripts 'command-limit-normal.txt')) -ceq '16' -and
            [IO.File]::ReadAllText((Join-Path $generatedRunScripts 'command-limit-shifted.txt')) -ceq '16' -and
            (Test-Path -LiteralPath (Join-Path `
                $generatedRunRoot `
                'captures\movesets\pairs\002-naruto-base.png')) -and
            (Test-Path -LiteralPath (Join-Path `
                $generatedRunRoot `
                'captures\movesets\blends\002-naruto-base.png')) -and
            (Test-Path -LiteralPath (Join-Path `
                $generatedRunRoot `
                'captures\movesets\diffs\002-naruto-base.png')) -and
            (Test-Path -LiteralPath (Join-Path `
                $generatedRunRoot `
                'captures\movesets\all\002-naruto-base-a-reference.png')) -and
            (Test-Path -LiteralPath (Join-Path `
                $generatedRunRoot `
                'captures\movesets\all\002-naruto-base_c_blend.png')) -and
            (Test-Path -LiteralPath (Join-Path `
                $generatedRunRoot `
                'captures\movesets\all\002-naruto-base_d_diff.png')) -and
            -not (Test-Path -LiteralPath (Join-Path `
                $generatedRunRoot `
                'captures\movesets\all\002-naruto-base_e_pair.png')) -and
            -not (Test-Path -LiteralPath (
                Join-Path $generatedRunRoot 'captures\movesets\stale.txt'
            ))
        ) `
        -Message 'Generated run did not compare normal/shifted grids and publish current history.'
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunCapture '003-sakura-base-a-reference.png'),
        'preserved reference grid'
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunCapture '003-sakura-base-b-current.png'),
        'preserved outside-range current grid'
    )
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunCapture 'stale.png'),
        'invalid generated artifact'
    )
    & (Join-Path $generatedRunScripts 'run.ps1') `
        -Suite 'movesets' `
        -MovesetRange '2' | Out-Null
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $generatedRunCapture '002-naruto-base-a-reference.png')) -ceq 'accepted reference grid' -and
            [IO.File]::ReadAllText((Join-Path $generatedRunCapture '002-naruto-base-b-current.png')) -ceq 'range 2 current grid' -and
            [IO.File]::ReadAllText((Join-Path $generatedRunCapture '003-sakura-base-a-reference.png')) -ceq 'preserved reference grid' -and
            [IO.File]::ReadAllText((Join-Path $generatedRunCapture '003-sakura-base-b-current.png')) -ceq 'preserved outside-range current grid' -and
            [IO.File]::ReadAllText((Join-Path $generatedRunScripts 'moveset-range.txt')) -ceq '2' -and
            -not (Test-Path -LiteralPath (Join-Path $generatedRunCapture 'stale.png'))
        ) `
        -Message 'Ranged generated run did not replace selected grids and preserve all other history.'
    Copy-Item `
        -LiteralPath (Join-Path $repository 'e2e\scripts\publish_references.ps1') `
        -Destination (Join-Path $generatedRunScripts 'publish_references.ps1')
    $generatedReferenceRepository = Join-Path $generatedRunRepository 'captured-reference'
    $generatedReferenceCapture = Join-Path `
        $generatedReferenceRepository `
        'movesets\screenshots'
    [void](New-Item -ItemType Directory -Path $generatedReferenceCapture -Force)
    [IO.File]::WriteAllText(
        (Join-Path $generatedReferenceCapture '002-naruto-base-a-reference.png'),
        'refreshed reference grid'
    )
    & (Join-Path $generatedRunScripts 'publish_references.ps1') `
        -Suite 'movesets' `
        -CapturedRepository $generatedReferenceRepository `
        -CaptureRepository (Join-Path $generatedRunRoot 'captures') `
        -PreserveGeneratedTier | Out-Null
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $generatedRunCapture '002-naruto-base-a-reference.png')) -ceq 'refreshed reference grid' -and
            [IO.File]::ReadAllText((Join-Path $generatedRunCapture '002-naruto-base-b-current.png')) -ceq 'range 2 current grid' -and
            [IO.File]::ReadAllText((Join-Path $generatedRunCapture '003-sakura-base-a-reference.png')) -ceq 'preserved reference grid' -and
            [IO.File]::ReadAllText((Join-Path $generatedRunCapture '003-sakura-base-b-current.png')) -ceq 'preserved outside-range current grid'
        ) `
        -Message 'Generated reference publication did not refresh reference and preserve current grids.'
    Copy-Item `
        -LiteralPath (Join-Path $repository 'e2e\scripts\reference.ps1') `
        -Destination (Join-Path $generatedRunScripts 'reference.ps1')
    [IO.File]::WriteAllText(
        (Join-Path $generatedRunScripts 'movesets.ps1'),
        @'
param(
    [string]$Game,
    [string]$Tier,
    [string]$OutputRoot,
    [string]$MovesetRange,
    [int]$ThrottleLimit,
    [string]$ConcurrencyPoolRoot,
    [string]$ProjectRoot
)
$grids = Join-Path $OutputRoot 'screenshots'
[void](New-Item -ItemType Directory -Path $grids -Force)
[IO.File]::WriteAllText(
    (Join-Path $grids '002-naruto-base-a-reference.png'),
    "$Game/$Tier/$ThrottleLimit/$MovesetRange"
)
'@
    )
    $coordinatedReferenceCapture = Join-Path $generatedRunRepository 'coordinated-reference'
    & (Join-Path $generatedRunScripts 'reference.ps1') `
        -Suite 'movesets' `
        -Game 'nun5' `
        -CaptureOutputRoot $coordinatedReferenceCapture `
        -MovesetRange '2' `
        -ConcurrencyLimit 5 | Out-Null
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path `
                $coordinatedReferenceCapture `
                'screenshots\002-naruto-base-a-reference.png')) -ceq 'nun5/reference/5/2'
        ) `
        -Message 'Generated reference capture did not delegate to the moveset suite runner.'

    foreach ($runnerName in @('run.ps1', 'variant.ps1', 'movesets.ps1')) {
        $tokens = $null
        $parseErrors = $null
        $runnerPath = Join-Path $repository "e2e\scripts\$runnerName"
        $runnerAst = [Management.Automation.Language.Parser]::ParseFile(
            $runnerPath,
            [ref]$tokens,
            [ref]$parseErrors
        )
        $suiteIteratorCollisions = @(
            $runnerAst.FindAll(
                {
                    param($node)
                    $node -is [Management.Automation.Language.ForEachStatementAst] -and
                    $node.Variable.VariablePath.UserPath -ieq 'Suite'
                },
                $true
            )
        )
        Assert-E2eHelperTest `
            -Condition (
                $parseErrors.Count -eq 0 -and
                $suiteIteratorCollisions.Count -eq 0
            ) `
            -Message "$runnerName reuses the typed Suite parameter as a foreach iterator."
    }

    foreach ($jobKind in @('thread', 'process')) {
        $jobCommand = if ($jobKind -ceq 'thread') { 'Start-ThreadJob' } else { 'Start-Job' }
        $failedJob = & $jobCommand -Name "$jobKind-synthetic-failure" -ScriptBlock {
            Start-Sleep -Milliseconds 100
            throw 'synthetic replay failure'
        }
        $blockedJob = & $jobCommand -Name "$jobKind-synthetic-blocked-sibling" -ScriptBlock {
            Start-Sleep -Seconds 30
        }
        $failureStopwatch = [Diagnostics.Stopwatch]::StartNew()
        $failureMessage = $null
        try {
            Wait-VisualRegressionJobs `
                -Job @($failedJob, $blockedJob) `
                -FailurePrefix 'Synthetic E2E job' 2>$null
        }
        catch {
            $failureMessage = $_.Exception.Message
        }
        finally {
            $failureStopwatch.Stop()
            foreach ($job in @($failedJob, $blockedJob)) {
                if ($job.State -in @('NotStarted', 'Running')) {
                    Stop-Job -Job $job -ErrorAction SilentlyContinue
                }
                Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
            }
        }
        Assert-E2eHelperTest `
            -Condition (
                $failureMessage -match 'synthetic-failure.*synthetic replay failure' -and
                $failureStopwatch.Elapsed.TotalSeconds -lt 5
            ) `
            -Message "$jobKind E2E job supervision did not report a failed child immediately."
        Assert-E2eHelperTest `
            -Condition ($blockedJob.State -eq 'Stopped') `
            -Message "$jobKind E2E job supervision did not stop a running sibling after failure."
    }

    $graphRoot = Join-Path $testRoot 'task-graph'
    [void](New-Item -ItemType Directory -Path $graphRoot -Force)
    $firstMarker = Join-Path $graphRoot 'first.txt'
    $dependentMarker = Join-Path $graphRoot 'dependent.txt'
    $firstTask = [pscustomobject]@{
        Key = 'synthetic/first'
        DependsOn = @()
        Ready = $null
        Start = {
            Start-ThreadJob -Name 'synthetic/first' -ScriptBlock {
                param($Marker)
                [IO.File]::WriteAllText($Marker, 'first')
            } -ArgumentList $firstMarker
        }.GetNewClosure()
    }
    $dependentTask = [pscustomobject]@{
        Key = 'synthetic/dependent'
        DependsOn = @('synthetic/first')
        Ready = $null
        Start = {
            Start-ThreadJob -Name 'synthetic/dependent' -ScriptBlock {
                param($RequiredMarker, $Marker)
                if (-not (Test-Path -LiteralPath $RequiredMarker -PathType Leaf)) {
                    throw 'dependency marker was absent'
                }
                [IO.File]::WriteAllText($Marker, 'dependent')
            } -ArgumentList $firstMarker, $dependentMarker
        }.GetNewClosure()
    }
    Invoke-VisualRegressionTaskGraph `
        -Task @($dependentTask, $firstTask) `
        -ThrottleLimit 2
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath $dependentMarker -PathType Leaf) `
        -Message 'The bounded E2E task graph did not honor a declared dependency.'

    $graphFailure = [pscustomobject]@{
        Key = 'synthetic/failure'
        DependsOn = @()
        Ready = $null
        Start = {
            Start-ThreadJob -Name 'synthetic/failure' -ScriptBlock {
                Start-Sleep -Milliseconds 100
                throw 'synthetic graph failure'
            }
        }
    }
    $graphBlocked = [pscustomobject]@{
        Key = 'synthetic/blocked'
        DependsOn = @()
        Ready = $null
        Start = {
            Start-ThreadJob -Name 'synthetic/blocked' -ScriptBlock {
                Start-Sleep -Seconds 30
            }
        }
    }
    $graphFailureStopwatch = [Diagnostics.Stopwatch]::StartNew()
    $graphFailureMessage = $null
    try {
        Invoke-VisualRegressionTaskGraph `
            -Task @($graphFailure, $graphBlocked) `
            -ThrottleLimit 2 `
            -FailurePrefix 'Synthetic graph task' 2>$null
    }
    catch {
        $graphFailureMessage = $_.Exception.Message
    }
    finally {
        $graphFailureStopwatch.Stop()
    }
    Assert-E2eHelperTest `
        -Condition (
            $graphFailureMessage -match 'synthetic/failure.*synthetic graph failure' -and
            $graphFailureStopwatch.Elapsed.TotalSeconds -lt 5
        ) `
        -Message 'The bounded E2E task graph did not fail fast with the exact failed task.'

    $activeVariantRoot = Join-Path $testRoot 'active-variant-config'
    [void](New-Item -ItemType Directory -Path $activeVariantRoot -Force)
    [IO.File]::WriteAllText(
        (Join-Path $activeVariantRoot 'config.json'),
        @'
{
  "schema_version": 1,
  "build_variants": [
    {
      "name": "baseline",
      "build": "baseline_build",
      "payload_shift_bytes": 0,
      "publish": true
    },
    {
      "name": "qualified",
      "build": "qualified_build",
      "payload_shift_bytes": 16,
      "compare_against": "baseline"
    }
  ]
}
'@
    )
    $configuration = Get-E2eConfiguration -Root $activeVariantRoot
    Assert-E2eHelperTest `
        -Condition ((@($configuration.Variants.name) -join ',') -ceq 'baseline,qualified') `
        -Message 'E2E configuration did not expose both active synthetic variants.'
    Assert-E2eHelperTest `
        -Condition ([string]$configuration.PublishedVariant.name -ceq 'baseline') `
        -Message 'E2E configuration did not select the published synthetic variant.'
    $qualifiedBuildVariant = Get-E2eBuildVariant `
        -Name 'qualified' `
        -Root $activeVariantRoot
    Assert-E2eHelperTest `
        -Condition ([string]$qualifiedBuildVariant.name -ceq 'qualified') `
        -Message 'A configured build variant was unavailable to explicit build resolution.'

    $layoutRoot = Join-Path $testRoot ('capture-layout-' + ('x' * 128))
    $layoutPublish = Join-Path $layoutRoot 'publish'
    foreach ($directory in @(
        (Join-Path $layoutPublish 'screenshots'),
        (Join-Path $layoutPublish 'pairs'),
        (Join-Path $layoutPublish 'blends'),
        (Join-Path $layoutPublish 'diffs')
    )) {
        [void](New-Item -ItemType Directory -Path $directory -Force)
    }
    [IO.File]::WriteAllText(
        (Join-Path $layoutPublish 'screenshots\page_01_a_reference.png'),
        'reference grid'
    )
    [IO.File]::WriteAllText(
        (Join-Path $layoutPublish 'screenshots\page_01_b_current.png'),
        'current grid'
    )
    [IO.File]::WriteAllText((Join-Path $layoutPublish 'pairs\page_01.png'), 'pair grid')
    [IO.File]::WriteAllText(
        (Join-Path $layoutPublish 'blends\page_01.png'),
        'blend grid'
    )
    [IO.File]::WriteAllText(
        (Join-Path $layoutPublish 'diffs\page_01.png'),
        'diff grid'
    )
    New-VisualRegressionAggregateLinkStage `
        -Source @(
            [pscustomobject]@{
                Directory = (Join-Path $layoutPublish 'screenshots')
                Suffix = ''
            },
            [pscustomobject]@{
                Directory = (Join-Path $layoutPublish 'blends')
                Suffix = 'c_blend'
            },
            [pscustomobject]@{
                Directory = (Join-Path $layoutPublish 'diffs')
                Suffix = 'd_diff'
            }
        ) `
        -OutputDirectory (Join-Path $layoutPublish 'all')
    $layoutFiles = @(
        Get-ChildItem -LiteralPath $layoutPublish -Recurse -File |
            ForEach-Object {
                [IO.Path]::GetRelativePath($layoutPublish, $_.FullName).Replace('\', '/')
            } |
            Sort-Object
    )
    Assert-E2eHelperTest `
        -Condition (
            ($layoutFiles -join ',') -ceq (
                'all/page_01_a_reference.png,' +
                'all/page_01_b_current.png,' +
                'all/page_01_c_blend.png,' +
                'all/page_01_d_diff.png,' +
                'blends/page_01.png,' +
                'diffs/page_01.png,' +
                'pairs/page_01.png,' +
                'screenshots/page_01_a_reference.png,' +
                'screenshots/page_01_b_current.png'
            )
        ) `
        -Message (
            'Capture artifacts were not separated into the flat published layout. Actual: ' +
            ($layoutFiles -join ',')
        )
    [IO.File]::WriteAllText(
        (Join-Path $layoutPublish 'blends\page_01.png'),
        'updated blend'
    )
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText(
                (Join-Path $layoutPublish 'all\page_01_c_blend.png')
            ) -ceq 'updated blend'
        ) `
        -Message 'The all view did not reuse its canonical blend through a hardlink.'

    $aggregateContext = [pscustomobject]@{
        SuiteRelativePath = 'capture-layout'
        Generated = $false
        Capture = [pscustomobject]@{
            ScreenshotGrids = Join-Path $layoutPublish 'screenshots'
            PairGrids = Join-Path $layoutPublish 'pairs'
            BlendGrids = Join-Path $layoutPublish 'blends'
            DiffGrids = Join-Path $layoutPublish 'diffs'
            AllGrids = Join-Path $layoutPublish 'all'
        }
    }
    Publish-VisualRegressionAggregateViews `
        -Context @($aggregateContext) `
        -TransactionRoot (Join-Path $layoutRoot 'aggregate-transaction')
    Assert-E2eHelperTest `
        -Condition (
            -not (Test-Path -LiteralPath (
                Join-Path $layoutPublish 'all\page_01_e_pair.png'
            ))
        ) `
        -Message 'Aggregate publication included a pair view.'
    [IO.File]::WriteAllText(
        (Join-Path $layoutPublish 'diffs\page_01.png'),
        'updated diff grid'
    )
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText(
                (Join-Path $layoutPublish 'all\page_01_d_diff.png')
            ) -ceq 'updated diff grid'
        ) `
        -Message 'Aggregate publication did not retain hardlinks to canonical grid pages.'

    $callbackRoot = Join-Path $layoutRoot 'callback-rollback'
    $callbackSource = Join-Path $callbackRoot 'source'
    $callbackDestination = Join-Path $callbackRoot 'destination'
    [void](New-Item -ItemType Directory -Path $callbackSource, $callbackDestination -Force)
    [IO.File]::WriteAllText((Join-Path $callbackSource 'new.txt'), 'new')
    [IO.File]::WriteAllText((Join-Path $callbackDestination 'old.txt'), 'old')
    $callbackFailed = $false
    try {
        Publish-VisualRegressionTransaction `
            -Replacements ([ordered]@{ $callbackDestination = $callbackSource }) `
            -TransactionRoot (Join-Path $callbackRoot 'transaction') `
            -AfterPublish { throw 'callback failure' }
    }
    catch {
        $callbackFailed = $_.Exception.Message -ceq 'callback failure'
    }
    Assert-E2eHelperTest `
        -Condition (
            $callbackFailed -and
            (Test-Path -LiteralPath (Join-Path $callbackDestination 'old.txt')) -and
            -not (Test-Path -LiteralPath (Join-Path $callbackDestination 'new.txt')) -and
            (Test-Path -LiteralPath (Join-Path $callbackSource 'new.txt') -PathType Leaf)
        ) `
        -Message 'A failed post-publication callback did not preserve staged output and roll back canonical publication.'

    $missingParentSource = Join-Path $testRoot 'missing-parent-source\movesets'
    $missingParentDestination = Join-Path `
        $testRoot `
        'missing-parent-destination\capture-history\movesets'
    [void](New-Item -ItemType Directory -Path $missingParentSource -Force)
    [IO.File]::WriteAllText(
        (Join-Path $missingParentSource 'grid.png'),
        'completed generated capture'
    )
    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{
            $missingParentDestination = $missingParentSource
        }) `
        -TransactionRoot (Join-Path $testRoot 'missing-parent-transaction')
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText(
                (Join-Path $missingParentDestination 'grid.png')
            ) -ceq 'completed generated capture' -and
            (Test-Path -LiteralPath (
                Join-Path $missingParentSource 'grid.png'
            ) -PathType Leaf)
        ) `
        -Message 'Generated E2E publication failed when the capture-history parent did not exist.'

    $transactions = Join-Path $testRoot '.transactions'
    $legacy = Join-Path $transactions 'legacy-without-owner'
    $recent = Join-Path $transactions 'recent-without-owner'
    $stale = Join-Path $transactions 'run-stale'
    [void](New-Item -ItemType Directory -Path $legacy, $recent, $stale -Force)
    (Get-Item -LiteralPath $legacy).LastWriteTimeUtc = [DateTime]::UtcNow.AddMinutes(-2)
    [IO.File]::WriteAllText(
        (Join-Path $stale 'owner.json'),
        '{"schema_version":1,"pid":2147483647,"process_start_utc":"2000-01-01T00:00:00.0000000Z"}'
    )
    $transaction = New-VisualRegressionTransaction -Root $testRoot -Prefix 'run'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath $stale -PathType Container) `
        -Message 'A metadata-owned abandoned E2E transaction was discarded.'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath $legacy -PathType Container) `
        -Message 'An old ownerless E2E transaction was discarded.'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath $recent -PathType Container) `
        -Message 'A newly created ownerless transaction was not protected from the creation race.'
    $transactionOwner = Get-Content -Raw -LiteralPath (Join-Path $transaction 'owner.json') |
        ConvertFrom-Json
    Assert-E2eHelperTest `
        -Condition (
            [int]$transactionOwner.schema_version -eq 2 -and
            [long]$transactionOwner.process_start_file_time_utc -eq
                (Get-Process -Id $PID).StartTime.ToFileTimeUtc()
        ) `
        -Message 'A new E2E transaction did not record a stable process identity.'
    (Get-Item -LiteralPath $recent).LastWriteTimeUtc = [DateTime]::UtcNow.AddMinutes(-2)
    $nestedTransaction = New-VisualRegressionTransaction -Root $testRoot -Prefix 'nested'
    Assert-E2eHelperTest `
        -Condition (
            (Test-Path -LiteralPath $transaction -PathType Container) -and
            (Test-Path -LiteralPath $recent -PathType Container)
        ) `
        -Message 'Creating a transaction discarded unrelated retained state.'
    Set-VisualRegressionTransactionRetained `
        -Transaction $nestedTransaction `
        -Root $testRoot
    $sweepTransaction = New-VisualRegressionTransaction -Root $testRoot -Prefix 'sweep'
    Assert-E2eHelperTest `
        -Condition (
            (Test-Path -LiteralPath $nestedTransaction -PathType Container) -and
            (Test-Path -LiteralPath $transaction -PathType Container)
        ) `
        -Message 'Creating another transaction discarded a failed resumable transaction.'
    Remove-VisualRegressionTransaction -Transaction $sweepTransaction -Root $testRoot

    $resumeKey = '{"suite":"resume-test"}'
    $resumableTransaction = New-VisualRegressionTransaction `
        -Root $testRoot `
        -Prefix 'resume' `
        -ResumeKey $resumeKey
    [void](New-Item `
        -ItemType Directory `
        -Path (Join-Path $resumableTransaction 'publish') `
        -Force)
    [IO.File]::WriteAllText(
        (Join-Path $resumableTransaction 'publish\result.txt'),
        'completed output'
    )
    Set-VisualRegressionTransactionRetained `
        -Transaction $resumableTransaction `
        -Root $testRoot
    $resumedTransaction = New-VisualRegressionTransaction `
        -Root $testRoot `
        -Prefix 'resume' `
        -ResumeKey $resumeKey
    $resumedRequest = Get-Content `
        -Raw `
        -LiteralPath (Join-Path $resumedTransaction 'request.json') |
        ConvertFrom-Json
    Assert-E2eHelperTest `
        -Condition (
            $resumedTransaction -ceq $resumableTransaction -and
            [int]$resumedRequest.resume_count -eq 1 -and
            -not (Test-Path -LiteralPath (Join-Path $resumedTransaction 'retained.json')) -and
            [IO.File]::ReadAllText(
                (Join-Path $resumedTransaction 'publish\result.txt')
            ) -ceq 'completed output'
        ) `
        -Message 'The same request did not reclaim its retained transaction and completed output.'
    $differentTransaction = New-VisualRegressionTransaction `
        -Root $testRoot `
        -Prefix 'resume' `
        -ResumeKey '{"suite":"different"}'
    Assert-E2eHelperTest `
        -Condition (
            $differentTransaction -cne $resumedTransaction -and
            (Test-Path -LiteralPath $resumedTransaction -PathType Container)
        ) `
        -Message 'A different request reused or discarded an incompatible transaction.'

    $legacyRun = Join-Path $transactions 'run-legacy-resume'
    $legacySuite = Join-Path $legacyRun 'jobs\normal\suites\legacy\suite'
    [void](New-Item -ItemType Directory -Path $legacySuite -Force)
    [IO.File]::WriteAllText((Join-Path $legacySuite 'complete.json'), '{}')
    Set-VisualRegressionTransactionRetained -Transaction $legacyRun -Root $testRoot
    $adoptedLegacyRun = New-VisualRegressionTransaction `
        -Root $testRoot `
        -Prefix 'run' `
        -ResumeKey '{"legacy":true}' `
        -LegacySuite @('legacy/suite')
    Assert-E2eHelperTest `
        -Condition (
            $adoptedLegacyRun -ceq $legacyRun -and
            (Test-VisualRegressionTransactionResumed -Transaction $adoptedLegacyRun)
        ) `
        -Message 'A compatible pre-resume E2E run was not adopted.'

    $attempt = Move-VisualRegressionTransactionItemsToAttempt `
        -Transaction $resumedTransaction `
        -RelativePath @('publish') `
        -Label 'test'
    Assert-E2eHelperTest `
        -Condition (
            -not (Test-Path -LiteralPath (Join-Path $resumedTransaction 'publish')) -and
            [IO.File]::ReadAllText((Join-Path $attempt 'publish\result.txt')) -ceq 'completed output'
        ) `
        -Message 'Superseded derived output was not preserved as a resumable attempt.'

    $normal = Join-Path $testRoot 'normal'
    $shifted = Join-Path $testRoot 'shifted'
    $comparison = Join-Path $testRoot 'comparison'
    [void](New-Item -ItemType Directory -Path $normal, $shifted -Force)
    [IO.File]::WriteAllBytes((Join-Path $normal '0001.png'), [byte[]](1, 2, 3))
    [IO.File]::WriteAllBytes((Join-Path $shifted '0001.png'), [byte[]](1, 2, 3))
    [IO.File]::WriteAllBytes((Join-Path $normal '0002.png'), [byte[]](4))
    [IO.File]::WriteAllBytes((Join-Path $shifted '0002.png'), [byte[]](5))
    $failed = Compare-VisualRegressionVariants `
        -Suite 'test/helpers' `
        -BaselineDirectory $normal `
        -CandidateDirectory $shifted `
        -CandidateName 'shifted' `
        -OutputRoot $comparison
    Assert-E2eHelperTest `
        -Condition ($failed.status -ceq 'failed') `
        -Message 'A normal/shifted difference was not mandatory.'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath (Join-Path $comparison 'differences\normal\0002.png')) `
        -Message 'Normal evidence for a failed variant comparison was not retained.'
    Assert-E2eHelperTest `
        -Condition (Test-Path -LiteralPath (Join-Path $comparison 'differences\shifted\0002.png')) `
        -Message 'Shifted evidence for a failed variant comparison was not retained.'

    $qualification = Join-Path $testRoot 'qualification'
    $qualificationComparison = Join-Path `
        $qualification `
        'comparisons\shifted\test\helpers'
    [void](New-Item -ItemType Directory -Path $qualificationComparison -Force)
    Copy-Item -Path (Join-Path $comparison '*') `
        -Destination $qualificationComparison `
        -Recurse
    [IO.File]::WriteAllText((Join-Path $qualification 'owner.json'), 'discarded')
    $qualificationEvidence = Preserve-VisualRegressionMismatchEvidence `
        -Transaction $qualification `
        -ComparisonVariant @('shifted')
    $qualificationFiles = @(
        Get-ChildItem -LiteralPath $qualificationEvidence -Recurse -File |
            ForEach-Object {
                [IO.Path]::GetRelativePath($qualificationEvidence, $_.FullName).Replace('\', '/')
            } |
            Sort-Object
    )
    Assert-E2eHelperTest `
        -Condition (
            ($qualificationFiles -join ',') -ceq (
                'shifted/test/helpers/report/result.json,' +
                'shifted/test/helpers/screenshots/normal/0002.png,' +
                'shifted/test/helpers/screenshots/shifted/0002.png'
            ) -and
            (Test-Path -LiteralPath (Join-Path $qualification 'owner.json') -PathType Leaf)
        ) `
        -Message 'Failed qualification did not preserve focused screenshot mismatch evidence.'

    $firstDestination = Join-Path $testRoot 'published\one\current'
    $secondDestination = Join-Path $testRoot 'published\two\current'
    $firstSource = Join-Path $testRoot 'sources\one\current'
    $secondSource = Join-Path $testRoot 'sources\two\current'
    [void](New-Item -ItemType Directory -Path `
        $firstDestination, $secondDestination, $firstSource, $secondSource -Force)
    [IO.File]::WriteAllText((Join-Path $firstDestination 'old.txt'), 'old-one')
    [IO.File]::WriteAllText((Join-Path $secondDestination 'old.txt'), 'old-two')
    [IO.File]::WriteAllText((Join-Path $firstSource 'new.txt'), 'new-one')
    [IO.File]::WriteAllText((Join-Path $secondSource 'new.txt'), 'new-two')
    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{
            $firstDestination = $firstSource
            $secondDestination = $secondSource
        }) `
        -TransactionRoot $transaction
    Assert-E2eHelperTest `
        -Condition ([IO.File]::ReadAllText((Join-Path $firstDestination 'new.txt')) -ceq 'new-one') `
        -Message 'First same-name capture directory was not published.'
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $secondDestination 'new.txt')) -ceq 'new-two' -and
            (Test-Path -LiteralPath (Join-Path $firstSource 'new.txt') -PathType Leaf) -and
            (Test-Path -LiteralPath (Join-Path $secondSource 'new.txt') -PathType Leaf)
        ) `
        -Message 'Second same-name capture directory was not published.'

    $screenshotDestination = Join-Path $testRoot 'published\screenshots\screenshots'
    $screenshotSource = Join-Path $testRoot 'sources\screenshots\screenshots'
    [void](New-Item -ItemType Directory -Path $screenshotDestination, $screenshotSource -Force)
    [IO.File]::WriteAllText((Join-Path $screenshotDestination '0001.png'), 'old')
    [IO.File]::WriteAllText((Join-Path $screenshotDestination 'stale.png'), 'stale')
    [IO.File]::WriteAllText((Join-Path $screenshotSource '0001.png'), 'new')
    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{ $screenshotDestination = $screenshotSource }) `
        -TransactionRoot $transaction
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $screenshotDestination '0001.png')) -ceq 'new' -and
            -not (Test-Path -LiteralPath (Join-Path $screenshotDestination 'stale.png')) -and
            (Test-Path -LiteralPath (Join-Path $screenshotSource '0001.png') -PathType Leaf)
        ) `
        -Message 'Screenshots were not synchronized without moving their staged directory.'

    $lockedDestination = Join-Path $testRoot 'published\locked\screenshots'
    $lockedSource = Join-Path $testRoot 'sources\locked\screenshots'
    $lockedPath = Join-Path $lockedDestination '0025.png'
    $lockReady = Join-Path $testRoot 'locked-file-ready'
    [void](New-Item -ItemType Directory -Path $lockedDestination, $lockedSource -Force)
    [IO.File]::WriteAllText($lockedPath, 'old locked screenshot')
    [IO.File]::WriteAllText((Join-Path $lockedSource '0025.png'), 'new screenshot')
    $lockJob = Start-ThreadJob -Name 'synthetic-transient-file-reader' -ScriptBlock {
        param($Path, $Ready)
        $stream = [IO.File]::Open(
            $Path,
            [IO.FileMode]::Open,
            [IO.FileAccess]::Read,
            [IO.FileShare]::None
        )
        try {
            [IO.File]::WriteAllText($Ready, '')
            Start-Sleep -Milliseconds 500
        }
        finally {
            $stream.Dispose()
        }
    } -ArgumentList $lockedPath, $lockReady
    try {
        $lockDeadline = [DateTime]::UtcNow.AddSeconds(5)
        while (-not (Test-Path -LiteralPath $lockReady -PathType Leaf)) {
            if ([DateTime]::UtcNow -ge $lockDeadline) {
                throw 'Synthetic file reader did not acquire its lock.'
            }
            Start-Sleep -Milliseconds 20
        }
        Publish-VisualRegressionTransaction `
            -Replacements ([ordered]@{ $lockedDestination = $lockedSource }) `
            -TransactionRoot $transaction
    }
    finally {
        Wait-Job -Job $lockJob -Timeout 5 | Out-Null
        if ($lockJob.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $lockJob -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $lockJob -Force -ErrorAction SilentlyContinue
    }
    Assert-E2eHelperTest `
        -Condition ([IO.File]::ReadAllText($lockedPath) -ceq 'new screenshot') `
        -Message 'Atomic E2E publication did not tolerate a transient file reader.'

    $fakeCommitRoot = Join-Path $testRoot 'g'
    $fakeCommitScripts = Join-Path $fakeCommitRoot 'e2e\scripts'
    $fakeCaptureRepository = Join-Path $fakeCommitRoot 'e2e\captures'
    [void](New-Item -ItemType Directory -Path `
        $fakeCommitScripts, `
        $fakeCaptureRepository `
        -Force)
    Copy-Item -LiteralPath (Join-Path $repository 'e2e\scripts\commit_captures.ps1') `
        -Destination (Join-Path $fakeCommitScripts 'commit_captures.ps1')
    $previousGitIdentity = @{
        AuthorName = $env:GIT_AUTHOR_NAME
        AuthorEmail = $env:GIT_AUTHOR_EMAIL
        CommitterName = $env:GIT_COMMITTER_NAME
        CommitterEmail = $env:GIT_COMMITTER_EMAIL
    }
    try {
        $env:GIT_AUTHOR_NAME = 'E2E Helper Test'
        $env:GIT_AUTHOR_EMAIL = 'e2e-helper-test@agent.invalid'
        $env:GIT_COMMITTER_NAME = 'E2E Helper Test'
        $env:GIT_COMMITTER_EMAIL = 'e2e-helper-test@agent.invalid'

        & git -C $fakeCommitRoot init --initial-branch=main | Out-Null
        [IO.File]::WriteAllText((Join-Path $fakeCommitRoot 'unrelated.txt'), 'original')
        & git -C $fakeCommitRoot add --all
        & git -C $fakeCommitRoot commit -m 'Initial main commit' | Out-Null

        & git -C $fakeCaptureRepository init --initial-branch=main | Out-Null
        [IO.File]::WriteAllText((Join-Path $fakeCaptureRepository 'capture.txt'), 'capture')
        & git -C $fakeCaptureRepository add --all
        & git -C $fakeCaptureRepository commit -m 'Initial commit' | Out-Null

        [IO.File]::WriteAllText((Join-Path $fakeCommitRoot 'unrelated.txt'), 'staged unrelated')
        & git -C $fakeCommitRoot add -- 'unrelated.txt'
        Remove-Item -LiteralPath (Join-Path $fakeCaptureRepository 'capture.txt') -Force
        & (Join-Path $fakeCommitScripts 'commit_captures.ps1')

        & (Join-Path $fakeCommitScripts 'commit_captures.ps1') -Preserve

        & (Join-Path $fakeCommitScripts 'commit_captures.ps1') -Preserve
    }
    finally {
        $env:GIT_AUTHOR_NAME = $previousGitIdentity.AuthorName
        $env:GIT_AUTHOR_EMAIL = $previousGitIdentity.AuthorEmail
        $env:GIT_COMMITTER_NAME = $previousGitIdentity.CommitterName
        $env:GIT_COMMITTER_EMAIL = $previousGitIdentity.CommitterEmail
    }
    Assert-E2eHelperTest `
        -Condition (
            [int](& git -C $fakeCaptureRepository rev-list --count HEAD) -eq 1 -and
            @(& git -C $fakeCaptureRepository ls-tree -r --name-only HEAD).Count -eq 0 -and
            @(& git -C $fakeCaptureRepository status --porcelain).Count -eq 0 -and
            [string](& git -C $fakeCaptureRepository log -1 --format='%s') -ceq 'Initial commit' -and
            [int](& git -C $fakeCommitRoot rev-list --count HEAD) -eq 1 -and
            [string](& git -C $fakeCommitRoot log -1 --format='%s') -ceq 'Initial main commit' -and
            (@(& git -C $fakeCommitRoot diff --cached --name-only) -join ',') -ceq 'unrelated.txt'
        ) `
        -Message 'E2E capture commit changed the main repository or disturbed unrelated staging.'

    $fakeRepository = Join-Path $testRoot 'suite-lifecycle-repository'
    $fakeScripts = Join-Path $fakeRepository 'e2e\scripts'
    $fakeInputRecordingsRoot = Join-Path $fakeRepository 'pcsx2_files\input_recordings'
    $fakeRecordings = Join-Path $fakeInputRecordingsRoot 'e2e'
    $fakeResources = Join-Path $fakeRepository 'resources'
    [void](New-Item -ItemType Directory -Path `
        $fakeScripts, `
        (Join-Path $fakeRepository 'e2e\captures'), `
        (Join-Path $fakeRepository 'scripts\lib'), `
        $fakeRecordings, `
        $fakeResources `
        -Force)
    Copy-Item -LiteralPath (Join-Path $repository 'e2e\scripts\suite.ps1') `
        -Destination (Join-Path $fakeScripts 'suite.ps1')
    Copy-Item -LiteralPath (Join-Path $repository 'e2e\scripts\create_suite.ps1') `
        -Destination (Join-Path $fakeScripts 'create_suite.ps1')
    Copy-Item -LiteralPath (Join-Path $repository 'e2e\scripts\rename_suite.ps1') `
        -Destination (Join-Path $fakeScripts 'rename_suite.ps1')
    Copy-Item -LiteralPath (Join-Path $repository 'e2e\scripts\remove_suite.ps1') `
        -Destination (Join-Path $fakeScripts 'remove_suite.ps1')
    [IO.File]::WriteAllText(
        (Join-Path $fakeRepository 'scripts\lib\paths.ps1'),
        @"
function Get-Na2Paths {
    [pscustomobject]@{
        pcsx2_input_recordings = '$($fakeInputRecordingsRoot.Replace("'", "''"))'
        resources = '$($fakeResources.Replace("'", "''"))'
    }
}
"@
    )
    [IO.File]::WriteAllText(
        (Join-Path $fakeScripts 'reference.ps1'),
        @'
param(
    [string]$Suite,
    [string]$Game,
    [string]$CaptureOutputRoot,
    [string]$CapturedRoot,
    [string]$CaptureRoot,
    [string]$MovesetRange,
    [string]$ConcurrencyPoolRoot,
    [int]$ConcurrencyLimit
)
$sync = Join-Path $PSScriptRoot 'sync'
[void](New-Item -ItemType Directory -Path $sync -Force)
if (-not [string]::IsNullOrWhiteSpace($CaptureOutputRoot)) {
    [IO.File]::WriteAllText(
        (Join-Path $PSScriptRoot 'reference-pool.txt'),
        $ConcurrencyPoolRoot
    )
    [IO.File]::WriteAllText(
        (Join-Path $PSScriptRoot 'reference-limit.txt'),
        [string]$ConcurrencyLimit
    )
    [IO.File]::WriteAllText((Join-Path $sync 'reference-started'), '')
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    while (-not (Test-Path -LiteralPath (Join-Path $sync 'run-started'))) {
        if ([DateTime]::UtcNow -ge $deadline) {
            throw 'The test run did not overlap the reference capture.'
        }
        Start-Sleep -Milliseconds 20
    }
    [void](New-Item -ItemType Directory -Path (Join-Path $CaptureOutputRoot 'screenshots') -Force)
    [IO.File]::WriteAllText((Join-Path $CaptureOutputRoot 'screenshots\0001.png'), 'reference')
    Add-Content -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') -Value "reference-capture suite=$Suite game=$Game"
    return
}
[void](New-Item -ItemType Directory -Path $CaptureRoot -Force)
[IO.File]::WriteAllText((Join-Path $CaptureRoot 'reference.txt'), 'reference')
Add-Content -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') -Value "reference-publish suite=$Suite"
'@
    )
    [IO.File]::WriteAllText(
        (Join-Path $fakeScripts 'publish_references.ps1'),
        @'
param(
    [string[]]$Suite,
    [string]$CapturedRepository,
    [string]$CaptureRepository,
    [switch]$PreserveGeneratedTier
)
foreach ($suiteName in $Suite) {
    $captureRoot = Join-Path $CaptureRepository $suiteName.Replace('/', [IO.Path]::DirectorySeparatorChar)
    [void](New-Item -ItemType Directory -Path $captureRoot -Force)
    [IO.File]::WriteAllText((Join-Path $captureRoot 'reference.txt'), 'reference')
    Add-Content -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') -Value "reference-publish suite=$suiteName"
}
'@
    )
    [IO.File]::WriteAllText(
        (Join-Path $fakeScripts 'run.ps1'),
        @'
param(
    [string[]]$Suite,
    [string]$CaptureRoot,
    [string]$CaptureRepository,
    [switch]$Shifted,
    [object[]]$SupervisedJob,
    [string]$MovesetRange,
    [string]$ConcurrencyPoolRoot,
    [int]$ConcurrencyLimit
)
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'fail-run')) {
    throw 'synthetic run failure'
}
$suites = [string[]]@($Suite)
[IO.File]::WriteAllText(
    (Join-Path $PSScriptRoot 'run-pool.txt'),
    $ConcurrencyPoolRoot
)
[IO.File]::WriteAllText(
    (Join-Path $PSScriptRoot 'run-throttle.txt'),
    [string]$ConcurrencyLimit
)
$hasReferenceSuite = $suites -ccontains 'test/with_reference'
if ($hasReferenceSuite) {
    $sync = Join-Path $PSScriptRoot 'sync'
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    while (-not (Test-Path -LiteralPath (Join-Path $sync 'reference-started'))) {
        if ([DateTime]::UtcNow -ge $deadline) {
            throw 'Reference capture did not start alongside the test run.'
        }
        Start-Sleep -Milliseconds 20
    }
}
Add-Content -LiteralPath (Join-Path $PSScriptRoot 'calls.txt') -Value (
    "run suite=$($suites -join ',') shifted=$($Shifted.IsPresent)" +
        $(if ([string]::IsNullOrWhiteSpace($MovesetRange)) { '' } else { " range=$MovesetRange" })
)
if ($hasReferenceSuite) {
    [IO.File]::WriteAllText((Join-Path $sync 'run-started'), '')
}
foreach ($suiteName in $suites) {
    $suiteCaptureRoot = if (-not [string]::IsNullOrWhiteSpace($CaptureRoot)) {
        $CaptureRoot
    }
    else {
        Join-Path $CaptureRepository $suiteName.Replace('/', [IO.Path]::DirectorySeparatorChar)
    }
    [void](New-Item -ItemType Directory -Path $suiteCaptureRoot -Force)
    [IO.File]::WriteAllText((Join-Path $suiteCaptureRoot 'current.txt'), 'current')
}
'@
    )
    $noReferenceRecording = Join-Path $fakeRecordings 'test\no_reference.p2m2'
    $withReferenceRecording = Join-Path $fakeRecordings 'test\with_reference.p2m2'
    [void](New-Item -ItemType Directory -Path (
        [IO.Path]::GetDirectoryName($noReferenceRecording)
    ) -Force)
    [IO.File]::WriteAllText($noReferenceRecording, 'first')
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/no_reference' `
        -NoReference
    $firstSuitePath = $noReferenceRecording
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText($firstSuitePath) -ceq 'first' -and
            @(Get-ChildItem -LiteralPath $fakeRecordings -Filter '*.p2m2' -File -Recurse).Count -eq 1
        ) `
        -Message 'Suite creation did not use the canonical recording in place.'
    $firstCaptureRoot = Join-Path $fakeRepository 'e2e\captures\test\no_reference'
    [void](New-Item -ItemType Directory -Path (
        Join-Path $firstCaptureRoot 'screenshots'
    ) -Force)
    [IO.File]::WriteAllText(
        (Join-Path $firstCaptureRoot 'screenshots\001_b_current.png'),
        'stale capture data'
    )
    [IO.File]::WriteAllText($noReferenceRecording, 'second')
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/no_reference' `
        -NoReference
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText($firstSuitePath) -ceq 'second' -and
            (Test-Path -LiteralPath $firstCaptureRoot -PathType Container) -and
            [IO.File]::ReadAllText((Join-Path $firstCaptureRoot 'current.txt')) -ceq 'current' -and
            -not (Test-Path -LiteralPath (
                Join-Path $firstCaptureRoot 'screenshots\001_b_current.png'
            ))
        ) `
        -Message 'Existing suite capture history was not completely replaced.'
    [IO.File]::WriteAllText($withReferenceRecording, 'second')
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'test/with_reference'
    $newSuiteCalls = @(Get-Content -LiteralPath (Join-Path $fakeScripts 'calls.txt'))
    Assert-E2eHelperTest `
        -Condition (
            $newSuiteCalls.Count -eq 5 -and
            $newSuiteCalls[0] -ceq 'run suite=test/no_reference shifted=False' -and
            $newSuiteCalls[1] -ceq 'run suite=test/no_reference shifted=False' -and
            $newSuiteCalls[2] -ceq 'run suite=test/with_reference shifted=False' -and
            $newSuiteCalls[3] -ceq 'reference-capture suite=test/with_reference game=nun5' -and
            $newSuiteCalls[4] -ceq 'reference-publish suite=test/with_reference'
        ) `
        -Message 'Suite creation did not overlap reference capture with the mandatory run before publication.'
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $fakeScripts 'reference-pool.txt')) -ceq
                [IO.File]::ReadAllText((Join-Path $fakeScripts 'run-pool.txt')) -and
            -not [string]::IsNullOrWhiteSpace(
                [IO.File]::ReadAllText((Join-Path $fakeScripts 'run-pool.txt'))
            ) -and
            [IO.File]::ReadAllText((Join-Path $fakeScripts 'reference-limit.txt')) -ceq '16' -and
            [IO.File]::ReadAllText((Join-Path $fakeScripts 'run-throttle.txt')) -ceq '16'
        ) `
        -Message 'Suite creation did not share one 16-slot replay pool across reference and current work.'
    $suiteNames = @(
        Get-VisualRegressionSuiteNames `
            -RecordingRepository $fakeRecordings
    )
    Assert-E2eHelperTest `
        -Condition (($suiteNames -join ',') -ceq 'movesets,test/no_reference,test/with_reference') `
        -Message 'Flat .p2m2 suite discovery did not return canonical extensionless names.'

    $sourceCaptureRoot = Join-Path $fakeRepository 'e2e\captures\test\with_reference'
    [IO.File]::WriteAllText((Join-Path $sourceCaptureRoot 'accepted.txt'), 'accepted history')
    [IO.File]::WriteAllText((Join-Path $fakeScripts 'fail-run'), '')
    [IO.File]::WriteAllText($withReferenceRecording, 'first')
    $replacementFailed = $false
    try {
        & (Join-Path $fakeScripts 'create_suite.ps1') `
            -Suite 'test/with_reference' `
            -NoReference
    }
    catch {
        $replacementFailed = $true
    }
    Remove-Item -LiteralPath (Join-Path $fakeScripts 'fail-run') -Force
    Assert-E2eHelperTest `
        -Condition (
            $replacementFailed -and
            [IO.File]::ReadAllText($withReferenceRecording) -ceq 'first' -and
            [IO.File]::ReadAllText((Join-Path $sourceCaptureRoot 'accepted.txt')) -ceq 'accepted history'
        ) `
        -Message 'Failed suite replacement changed the canonical recording or accepted capture history.'
    [IO.File]::WriteAllText((Join-Path $sourceCaptureRoot 'capture.txt'), 'capture history')
    $sourceChildSuitePath = Join-Path $fakeRecordings 'test\with_reference\child.p2m2'
    $sourceChildCaptureRoot = Join-Path $sourceCaptureRoot 'child'
    [void](New-Item -ItemType Directory -Path `
        ([IO.Path]::GetDirectoryName($sourceChildSuitePath)), `
        $sourceChildCaptureRoot `
        -Force)
    [IO.File]::WriteAllText($sourceChildSuitePath, 'child recording')
    [IO.File]::WriteAllText(
        (Join-Path $sourceChildCaptureRoot 'capture.txt'),
        'child history'
    )
    & (Join-Path $fakeScripts 'rename_suite.ps1') `
        -Suite 'test/with_reference' `
        -NewSuite 'renamed/with_reference'
    $renamedSuitePath = Join-Path $fakeRecordings 'renamed\with_reference.p2m2'
    $renamedCaptureRoot = Join-Path $fakeRepository 'e2e\captures\renamed\with_reference'
    $childSuitePath = Join-Path $fakeRecordings 'renamed\with_reference\child.p2m2'
    $childCaptureRoot = Join-Path $renamedCaptureRoot 'child'
    Assert-E2eHelperTest `
        -Condition (
            -not (Test-Path -LiteralPath $withReferenceRecording) -and
            -not (Test-Path -LiteralPath $sourceChildSuitePath) -and
            -not (Test-Path -LiteralPath $sourceCaptureRoot) -and
            (Test-Path -LiteralPath $renamedSuitePath -PathType Leaf) -and
            (Test-Path -LiteralPath $childSuitePath -PathType Leaf) -and
            [IO.File]::ReadAllText((Join-Path $renamedCaptureRoot 'capture.txt')) -ceq 'capture history' -and
            [IO.File]::ReadAllText((Join-Path $childCaptureRoot 'capture.txt')) -ceq 'child history'
        ) `
        -Message 'Suite rename did not move the definition, descendants, and capture history.'
    & (Join-Path $fakeScripts 'remove_suite.ps1') -Suite 'renamed/with_reference'
    Assert-E2eHelperTest `
        -Condition (
            (Test-Path -LiteralPath $renamedSuitePath -PathType Leaf) -and
            -not (Test-Path -LiteralPath (Join-Path $renamedCaptureRoot 'capture.txt')) -and
            (Test-Path -LiteralPath $childSuitePath -PathType Leaf) -and
            [IO.File]::ReadAllText((Join-Path $childCaptureRoot 'capture.txt')) -ceq 'child history'
        ) `
        -Message 'Capture removal changed canonical recordings, removed descendant history, or retained parent artifacts.'
    & (Join-Path $fakeScripts 'remove_suite.ps1') -Suite 'renamed/with_reference/child'
    Assert-E2eHelperTest `
        -Condition (
            (Test-Path -LiteralPath $renamedSuitePath -PathType Leaf) -and
            (Test-Path -LiteralPath $childSuitePath -PathType Leaf) -and
            -not (Test-Path -LiteralPath $renamedCaptureRoot) -and
            -not (Test-Path -LiteralPath (Join-Path $fakeRepository 'e2e\captures\renamed'))
        ) `
        -Message 'Leaf capture removal changed canonical recordings or retained empty capture parents.'

    $fakeGeneratedScript = Join-Path $fakeScripts 'movesets.ps1'
    $fakeMovesetInput = Join-Path $fakeRecordings 'movesets\base.p2m2'
    [void](New-Item -ItemType Directory -Path (Split-Path -Parent $fakeMovesetInput) -Force)
    [IO.File]::WriteAllText(
        (Join-Path $fakeResources 'character_data.tsv'),
        "character`tid`nNaruto`t1`n"
    )
    [IO.File]::WriteAllText(
        (Join-Path $fakeResources 'movesets.tsv'),
        "character`tid`nNaruto`t1`n"
    )
    [IO.File]::WriteAllText($fakeMovesetInput, 'generated suite input')
    [IO.File]::WriteAllText($fakeGeneratedScript, '# generated suite')
    & (Join-Path $fakeScripts 'create_suite.ps1') -Suite 'movesets' -NoReference
    $fakeGeneratedCapture = Join-Path $fakeRepository 'e2e\captures\movesets'
    [IO.File]::WriteAllText(
        (Join-Path $fakeGeneratedCapture 'preserved.txt'),
        'preserved ranged history'
    )
    & (Join-Path $fakeScripts 'create_suite.ps1') `
        -Suite 'movesets' `
        -MovesetRange '2' `
        -NoReference
    Assert-E2eHelperTest `
        -Condition (
            [IO.File]::ReadAllText((Join-Path $fakeGeneratedCapture 'preserved.txt')) -ceq 'preserved ranged history' -and
            -not [string]::IsNullOrWhiteSpace(
                [IO.File]::ReadAllText((Join-Path $fakeScripts 'run-pool.txt'))
            ) -and
            [IO.File]::ReadAllText((Join-Path $fakeScripts 'run-throttle.txt')) -ceq '16' -and
            @(Get-Content -LiteralPath (Join-Path $fakeScripts 'calls.txt'))[-1] -ceq 'run suite=movesets shifted=False range=2'
        ) `
        -Message 'Ranged generated creation did not preserve existing history or pass its range to the run.'
    $generatedRenameRejected = $false
    try {
        & (Join-Path $fakeScripts 'rename_suite.ps1') `
            -Suite 'movesets' `
            -NewSuite 'renamed-movesets'
    }
    catch {
        $generatedRenameRejected = $_.Exception.Message -ceq (
            "The generated E2E suite 'movesets' cannot be renamed."
        )
    }
    & (Join-Path $fakeScripts 'remove_suite.ps1') -Suite 'movesets'
    $postRemoveGeneratedNames = @(
        Get-VisualRegressionSuiteNames `
            -RecordingRepository $fakeRecordings
    )
    Assert-E2eHelperTest `
        -Condition (
            (Test-Path -LiteralPath $fakeMovesetInput -PathType Leaf) -and
            -not (Test-Path -LiteralPath $fakeGeneratedCapture) -and
            $generatedRenameRejected -and
            $postRemoveGeneratedNames -ccontains 'movesets'
        ) `
        -Message 'Generated suite create, rename, or capture-history removal semantics regressed.'
    $fakeCaptureGit = Join-Path $fakeRepository 'e2e\captures\.git'
    $fakeCaptureAttributes = Join-Path $fakeRepository 'e2e\captures\.gitattributes'
    $fakeCaptureIgnore = Join-Path $fakeRepository 'e2e\captures\.gitignore'
    $orphanCapture = Join-Path $fakeRepository 'e2e\captures\orphan'
    $generatedRecording = Join-Path $fakeRecordings '__generated\transient.p2m2'
    $movesetInputRecording = Join-Path $fakeRecordings 'movesets\base.p2m2'
    [void](New-Item -ItemType Directory -Path $fakeCaptureGit, $orphanCapture -Force)
    [void](New-Item -ItemType Directory -Path `
        ([IO.Path]::GetDirectoryName($generatedRecording)), `
        ([IO.Path]::GetDirectoryName($movesetInputRecording)) `
        -Force)
    [IO.File]::WriteAllText((Join-Path $fakeCaptureGit 'preserved.txt'), 'git metadata')
    [IO.File]::WriteAllText(
        $fakeCaptureAttributes,
        ".gitattributes text eol=lf`n.gitignore text eol=lf`n"
    )
    [IO.File]::WriteAllText(
        $fakeCaptureIgnore,
        "**/all/`n"
    )
    [IO.File]::WriteAllText((Join-Path $orphanCapture 'stale.txt'), 'orphan history')
    $orphanSuite = Join-Path $fakeRecordings 'orphan.p2m2'
    [IO.File]::WriteAllText($orphanSuite, 'orphan suite')
    [IO.File]::WriteAllText($generatedRecording, 'transient recording')
    [IO.File]::WriteAllText($movesetInputRecording, 'generated suite input')
    & (Join-Path $fakeScripts 'create_suite.ps1') -All -NoReference
    $bulkSuiteNames = @(
        Get-VisualRegressionSuiteNames `
            -RecordingRepository $fakeRecordings
    )
    Assert-E2eHelperTest `
        -Condition (
            ($bulkSuiteNames -join ',') -ceq '__generated/transient,movesets,orphan,renamed/with_reference,renamed/with_reference/child,test/no_reference' -and
            (Get-Content -LiteralPath (Join-Path $fakeScripts 'calls.txt') | Select-Object -Last 1) `
                -ceq 'run suite=__generated/transient,orphan,renamed/with_reference,renamed/with_reference/child,test/no_reference,movesets shifted=False' -and
            (Test-Path -LiteralPath (
                Join-Path $fakeRepository 'e2e\captures\test\no_reference\current.txt'
            ) -PathType Leaf) -and
            (Test-Path -LiteralPath (
                Join-Path $fakeRepository 'e2e\captures\movesets\current.txt'
            ) -PathType Leaf) -and
            (Test-Path -LiteralPath $orphanSuite -PathType Leaf) -and
            (Test-Path -LiteralPath (Join-Path $orphanCapture 'current.txt') -PathType Leaf) -and
            -not (Test-Path -LiteralPath (Join-Path $orphanCapture 'stale.txt')) -and
            [IO.File]::ReadAllText((Join-Path $fakeCaptureGit 'preserved.txt')) -ceq 'git metadata' -and
            [IO.File]::ReadAllText($fakeCaptureAttributes) -ceq (
                ".gitattributes text eol=lf`n.gitignore text eol=lf`n"
            ) -and
            [IO.File]::ReadAllText($fakeCaptureIgnore) -ceq (
                "**/all/`n"
            )
        ) `
        -Message 'Bulk suite creation did not discover canonical recordings or rewrite histories while preserving capture Git metadata.'
    $acceptedBulkCapture = Join-Path `
        $fakeRepository `
        'e2e\captures\test\no_reference\accepted.txt'
    [IO.File]::WriteAllText($acceptedBulkCapture, 'accepted bulk history')
    [IO.File]::WriteAllText($noReferenceRecording, 'third')
    [IO.File]::WriteAllText((Join-Path $fakeScripts 'fail-run'), '')
    $bulkReplacementFailed = $false
    try {
        & (Join-Path $fakeScripts 'create_suite.ps1') -All -NoReference
    }
    catch {
        $bulkReplacementFailed = $true
    }
    Remove-Item -LiteralPath (Join-Path $fakeScripts 'fail-run') -Force
    Assert-E2eHelperTest `
        -Condition (
            $bulkReplacementFailed -and
            [IO.File]::ReadAllText($firstSuitePath) -ceq 'third' -and
            [IO.File]::ReadAllText($acceptedBulkCapture) -ceq 'accepted bulk history' -and
            [IO.File]::ReadAllText((Join-Path $fakeCaptureGit 'preserved.txt')) -ceq 'git metadata' -and
            [IO.File]::ReadAllText($fakeCaptureAttributes) -ceq (
                ".gitattributes text eol=lf`n.gitignore text eol=lf`n"
            ) -and
            [IO.File]::ReadAllText($fakeCaptureIgnore) -ceq (
                "**/all/`n"
            )
        ) `
        -Message 'Failed bulk suite creation changed canonical recordings or accepted capture history.'
    $looseCapture = Join-Path $fakeRepository 'e2e\captures\loose.txt'
    [IO.File]::WriteAllText($looseCapture, 'loose capture history')
    & (Join-Path $fakeScripts 'remove_suite.ps1') -All
    & (Join-Path $fakeScripts 'remove_suite.ps1') -All
    Assert-E2eHelperTest `
        -Condition (
            (Test-Path -LiteralPath $movesetInputRecording -PathType Leaf) -and
            (Test-Path -LiteralPath $orphanSuite -PathType Leaf) -and
            (Test-Path -LiteralPath $generatedRecording -PathType Leaf) -and
            (Test-Path -LiteralPath $firstSuitePath -PathType Leaf) -and
            @(
                Get-ChildItem `
                    -LiteralPath (Join-Path $fakeRepository 'e2e\captures') `
                    -Force |
                    Where-Object Name -NotIn @('.git', '.gitattributes', '.gitignore')
            ).Count -eq 0 -and
            [IO.File]::ReadAllText((Join-Path $fakeCaptureGit 'preserved.txt')) -ceq 'git metadata' -and
            [IO.File]::ReadAllText($fakeCaptureAttributes) -ceq (
                ".gitattributes text eol=lf`n.gitignore text eol=lf`n"
            ) -and
            [IO.File]::ReadAllText($fakeCaptureIgnore) -ceq (
                "**/all/`n"
            )
        ) `
        -Message 'Bulk capture removal changed canonical recordings, retained history, or changed capture Git metadata.'

    Remove-VisualRegressionTransaction -Transaction $transaction -Root $testRoot
    Write-Host 'E2E helper tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
