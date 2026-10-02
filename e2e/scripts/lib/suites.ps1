function Get-VisualRegressionRepositoryState {
    if ($null -eq $script:E2eRepositoryState) {
        $root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
        $repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
        . (Join-Path $repository 'scripts\lib\paths.ps1')
        $paths = Get-Na2Paths
        $script:E2eRepositoryState = [pscustomobject]@{
            Root = $root
            Repository = $repository
            Paths = $paths
            Configuration = Get-E2eConfiguration -Root $root
            CaptureRepository = [string]$paths.e2e_captures
            RecordingRepository = Join-Path ([string]$paths.pcsx2_input_recordings) 'e2e'
            Comparator = Join-Path `
                ([string]$paths.scripts) `
                'research\localization\compare_font_capture_sets.ps1'
        }
    }
    return $script:E2eRepositoryState
}

function Get-VisualRegressionCharacterCount {
    $paths = (Get-VisualRegressionRepositoryState).Paths
    return @(
        Import-Csv `
            -LiteralPath (Join-Path ([string]$paths.resources) 'character_data.tsv') `
            -Delimiter "`t"
    ).Count
}

function Get-VisualRegressionSelectionLabel {
    param([Parameter(Mandatory)][object[]]$Request)

    return @(
        $Request | ForEach-Object {
            if ($_.Arguments.Count -eq 0) {
                $_.Suite
            }
            else {
                "$($_.Suite) $($_.Arguments -join ' ')"
            }
        }
    ) -join ', '
}

function Test-VisualRegressionGeneratedSuite {
    param([Parameter(Mandatory)][string]$Suite)

    $normalized = $Suite.Replace('\', '/').TrimEnd('/')
    return (
        $normalized -imatch '^movesets(?:/(?:base|specials))?$' -or
        $normalized -ieq $script:E2eGeneratedIdleSuiteName
    )
}

function Get-VisualRegressionGeneratedSuiteFamily {
    param([Parameter(Mandatory)][string]$Suite)

    $normalized = $Suite.Replace('\', '/').TrimEnd('/')
    if (-not (Test-VisualRegressionGeneratedSuite -Suite $normalized)) {
        return $null
    }
    if ($normalized -ieq $script:E2eGeneratedIdleSuiteName) {
        return 'idle'
    }
    if ($normalized -ieq $script:E2eGeneratedMovesetSuiteName) {
        return 'movesets'
    }
    return @($normalized.Split('/'))[-1].ToLowerInvariant()
}

function Test-VisualRegressionGeneratedSuiteRoot {
    param([Parameter(Mandatory)][string]$Suite)

    $normalized = $Suite.Replace('\', '/').TrimEnd('/')
    return $script:E2eGeneratedSuiteNames -icontains $normalized
}

function Resolve-VisualRegressionMovesetRange {
    param(
        [Parameter(Mandatory)][string]$Range,
        [Parameter(Mandatory)][ValidateRange(2, [int]::MaxValue)]
        [int]$LastAvailableRow
    )

    $rangeMatch = [regex]::Match($Range, '^(\d+)(?:-(\d+))?$')
    if (-not $rangeMatch.Success) {
        throw (
            'Moveset range must be one character_data.tsv row or an inclusive ' +
            'row range, for example 8 or 8-18.'
        )
    }
    $firstRow = 0
    $lastRow = 0
    if (-not [int]::TryParse($rangeMatch.Groups[1].Value, [ref]$firstRow)) {
        throw "Moveset range is outside the supported integer range: $Range"
    }
    if ($rangeMatch.Groups[2].Success) {
        if (-not [int]::TryParse($rangeMatch.Groups[2].Value, [ref]$lastRow)) {
            throw "Moveset range is outside the supported integer range: $Range"
        }
    }
    else {
        $lastRow = $firstRow
    }
    if ($firstRow -gt $lastRow) {
        throw "Moveset range starts after it ends: $Range"
    }
    if ($firstRow -lt 2 -or $lastRow -gt $LastAvailableRow) {
        throw (
            "Moveset range $Range must stay within character_data.tsv rows " +
            "2-$LastAvailableRow."
        )
    }

    [pscustomobject]@{
        FirstRow = $firstRow
        LastRow = $lastRow
        Value = $(if ($firstRow -eq $lastRow) {
            [string]$firstRow
        }
        else {
            "$firstRow-$lastRow"
        })
    }
}

function Get-VisualRegressionIdlePagePlans {
    param(
        [Parameter(Mandatory)][ValidateRange(2, [int]::MaxValue)]
        [int]$FirstRow,
        [Parameter(Mandatory)][ValidateRange(2, [int]::MaxValue)]
        [int]$LastRow,
        [Parameter(Mandatory)][ValidateRange(1, [int]::MaxValue)]
        [int]$CharacterCount
    )

    if ($FirstRow -gt $LastRow -or $LastRow -gt $CharacterCount + 1) {
        throw 'Idle page rows must be an ascending range within character_data.tsv.'
    }
    [int]$firstPage = [Math]::Floor(($FirstRow - 2) / 6) + 1
    [int]$lastPage = [Math]::Floor(($LastRow - 2) / 6) + 1
    for ($page = $firstPage; $page -le $lastPage; $page++) {
        [pscustomobject]@{
            Page = [int]$page
            FirstCharacterIndex = [int](($page - 1) * 6)
            LastCharacterIndex = [int][Math]::Min(
                ($page * 6) - 1,
                $CharacterCount - 1
            )
        }
    }
}

function Test-VisualRegressionGeneratedSuiteNamespace {
    param([Parameter(Mandatory)][string]$Suite)

    $normalized = $Suite.Replace('\', '/').TrimEnd('/')
    return (
        $normalized -ieq $script:E2eGeneratedIdleSuiteName -or
        $normalized.StartsWith(
            $script:E2eGeneratedIdleSuiteName + '/',
            [StringComparison]::OrdinalIgnoreCase
        ) -or
        $normalized -ieq $script:E2eGeneratedMovesetSuiteName -or
        $normalized.StartsWith(
            $script:E2eGeneratedMovesetSuiteName + '/',
            [StringComparison]::OrdinalIgnoreCase
        )
    )
}

function Get-VisualRegressionGeneratedStorageSuite {
    param([Parameter(Mandatory)][string]$Family)

    if ($Family -ceq 'idle') {
        return $script:E2eGeneratedIdleSuiteName
    }
    return $script:E2eGeneratedMovesetSuiteName
}

function Get-VisualRegressionGeneratedRangePrefixes {
    param(
        [Parameter(Mandatory)][string]$Family,
        [Parameter(Mandatory)][string]$Range
    )

    $rangeMatch = [regex]::Match($Range, '^(\d+)(?:-(\d+))?$')
    $firstRow = [int]$rangeMatch.Groups[1].Value
    $lastRow = if ($rangeMatch.Groups[2].Success) {
        [int]$rangeMatch.Groups[2].Value
    }
    else { $firstRow }
    if ($Family -ceq 'idle') {
        return [string[]]@(
            Get-VisualRegressionIdlePagePlans `
                -FirstRow $firstRow `
                -LastRow $lastRow `
                -CharacterCount (Get-VisualRegressionCharacterCount) |
                ForEach-Object { 'page_{0:D2}_' -f $_.Page }
        )
    }
    return [string[]]@(
        for ($row = $firstRow; $row -le $lastRow; $row++) {
            '{0:D3}_' -f $row
        }
    )
}

function Get-VisualRegressionGeneratedInputPaths {
    param(
        [Parameter(Mandatory)][string]$RecordingRepository,
        [Parameter(Mandatory)][string]$Suite
    )

    $family = Get-VisualRegressionGeneratedSuiteFamily -Suite $Suite
    [string[]]@(
        if ($family -cin @('movesets', 'base')) {
            Join-Path $RecordingRepository 'movesets\base.p2m2'
        }
        if ($family -cin @('movesets', 'specials')) {
            Join-Path $RecordingRepository 'movesets\specials.p2m2'
        }
        if ($family -ceq 'idle') {
            Join-Path $RecordingRepository 'characters\idle.p2m2'
        }
    )
}

function Test-VisualRegressionSuiteExists {
    param([Parameter(Mandatory)][object]$Context)

    if ($Context.Generated) {
        if (-not (Test-Path -LiteralPath $Context.GeneratedScript -PathType Leaf)) {
            return $false
        }
        return @(
            Get-VisualRegressionGeneratedInputPaths `
                -RecordingRepository $Context.RecordingRepository `
                -Suite $Context.Suite |
                Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) }
        ).Count -eq 0
    }
    if ($Context.GeneratedNamespace) {
        return $false
    }
    Test-Path -LiteralPath $Context.SuitePath -PathType Leaf
}

function Get-VisualRegressionContext {
    param(
        [Parameter(Mandatory)][string]$Suite,
        [string]$CaptureRoot
    )

    if ([string]::IsNullOrWhiteSpace($Suite) -or [IO.Path]::IsPathRooted($Suite)) {
        throw 'Suite must be a relative path.'
    }
    $normalizedSuite = $Suite.Replace('\', '/')
    if ($normalizedSuite.EndsWith('.p2m2', [StringComparison]::OrdinalIgnoreCase)) {
        $normalizedSuite = $normalizedSuite.Substring(0, $normalizedSuite.Length - 5)
    }
    $segments = @($normalizedSuite.Split('/'))
    if ($segments.Count -eq 0 -or @(
        $segments | Where-Object {
            [string]::IsNullOrWhiteSpace($_) -or
            $_ -in @('.', '..') -or
            $_.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0
        }
    ).Count -gt 0) {
        throw "Suite contains an invalid path component: $Suite"
    }
    $suiteName = $segments -join '/'
    $suiteRelativePath = $segments -join [IO.Path]::DirectorySeparatorChar
    $state = Get-VisualRegressionRepositoryState
    $root = $state.Root
    $generated = Test-VisualRegressionGeneratedSuite -Suite $suiteName
    $generatedFamily = if ($generated) {
        Get-VisualRegressionGeneratedSuiteFamily -Suite $suiteName
    }
    else { $null }
    $suiteSettings = Resolve-E2eSuiteSettings `
        -Configuration $state.Configuration `
        -Suite $suiteName
    $recordingRepository = $state.RecordingRepository
    $storageRelativePath = if ($generated) {
        (Get-VisualRegressionGeneratedStorageSuite -Family $generatedFamily).Replace(
            '/',
            [IO.Path]::DirectorySeparatorChar
        )
    }
    else {
        $suiteRelativePath
    }
    $suitePath = Join-Path $recordingRepository ($suiteRelativePath + '.p2m2')
    $captureRoot = if ([string]::IsNullOrWhiteSpace($CaptureRoot)) {
        Join-Path $state.CaptureRepository $storageRelativePath
    }
    else {
        [IO.Path]::GetFullPath($CaptureRoot)
    }
    [pscustomobject]@{
        Root = $root
        CaptureRepository = $state.CaptureRepository
        RecordingRepository = $recordingRepository
        Suite = $suiteName
        SuiteRelativePath = $storageRelativePath
        SuitePath = $suitePath
        Generated = $generated
        GeneratedNamespace = Test-VisualRegressionGeneratedSuiteNamespace -Suite $suiteName
        GeneratedFamily = $generatedFamily
        GeneratedScript = Join-Path $root 'scripts\movesets.ps1'
        MemoryCard = $suiteSettings.MemoryCard
        LaunchProfile = $suiteSettings.LaunchProfile
        DescendantSuiteRoot = Join-Path $recordingRepository $suiteRelativePath
        CaptureRoot = $captureRoot
        Capture = [pscustomobject]@{
            AllGrids = Join-Path $captureRoot $script:E2eAllGridDirectory
            ScreenshotGrids = Join-Path $captureRoot $script:E2eScreenshotGridDirectory
            PairGrids = Join-Path $captureRoot $script:E2ePairGridDirectory
            BlendGrids = Join-Path $captureRoot $script:E2eBlendGridDirectory
            DiffGrids = Join-Path $captureRoot $script:E2eDiffGridDirectory
        }
        Repository = $state.Repository
        Comparator = $state.Comparator
    }
}

function Get-VisualRegressionSuiteNames {
    param([Parameter(Mandatory)][string]$RecordingRepository)

    [string[]]@(
        if (Test-Path -LiteralPath $RecordingRepository -PathType Container) {
            Get-ChildItem -LiteralPath $RecordingRepository -Filter '*.p2m2' -File -Recurse |
                ForEach-Object {
                    $relative = [IO.Path]::GetRelativePath($RecordingRepository, $_.FullName)
                    $suite = $relative.Substring(0, $relative.Length - 5).Replace('\', '/')
                    if (-not (Test-VisualRegressionGeneratedSuiteNamespace -Suite $suite)) {
                        $suite
                    }
                }
        }
        $generatedScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'movesets.ps1'
        if (Test-Path -LiteralPath $generatedScript -PathType Leaf) {
            foreach ($generatedSuite in $script:E2eGeneratedSuiteNames) {
                $missingInputs = @(
                    Get-VisualRegressionGeneratedInputPaths `
                        -RecordingRepository $RecordingRepository `
                        -Suite $generatedSuite |
                        Where-Object {
                            -not (Test-Path -LiteralPath $_ -PathType Leaf)
                        }
                )
                if ($missingInputs.Count -eq 0) {
                    $generatedSuite
                }
            }
        }
    ) | Sort-Object -Unique
}

function Get-VisualRegressionSelectableSuiteNames {
    param([Parameter(Mandatory)][string]$RecordingRepository)

    $available = @(
        Get-VisualRegressionSuiteNames -RecordingRepository $RecordingRepository
    )
    [string[]]@(
        $available
        if ($available -icontains $script:E2eGeneratedMovesetSuiteName) {
            "$($script:E2eGeneratedMovesetSuiteName)/base"
            "$($script:E2eGeneratedMovesetSuiteName)/specials"
        }
    ) | Sort-Object -Unique
}

function Resolve-VisualRegressionSuiteArguments {
    param(
        [Parameter(Mandatory)][object]$Context,
        [AllowEmptyCollection()][string[]]$Argument = @()
    )

    $arguments = [string[]]@($Argument)
    if (-not $Context.Generated) {
        if ($arguments.Count -gt 0) {
            throw "E2E suite $($Context.Suite) accepts no arguments."
        }
        return [pscustomobject]@{
            Arguments = $arguments
            MovesetRange = $null
        }
    }
    if ($arguments.Count -gt 1) {
        throw "E2E suite $($Context.Suite) accepts at most one character row range."
    }
    if ($arguments.Count -eq 0) {
        return [pscustomobject]@{
            Arguments = $arguments
            MovesetRange = $null
        }
    }

    $resolvedRange = Resolve-VisualRegressionMovesetRange `
        -Range $arguments[0] `
        -LastAvailableRow ((Get-VisualRegressionCharacterCount) + 1)
    [pscustomobject]@{
        Arguments = [string[]]@($resolvedRange.Value)
        MovesetRange = $resolvedRange.Value
    }
}

function Resolve-VisualRegressionSuiteSelection {
    param(
        [Parameter(Mandatory)][string[]]$Token,
        [Parameter(Mandatory)][string]$RecordingRepository
    )

    $tokens = [string[]]@($Token)
    if ($tokens.Count -eq 0) {
        throw 'Select all or at least one E2E suite.'
    }
    if (@($tokens | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count -gt 0) {
        throw 'E2E suite selection cannot contain an empty token.'
    }
    $allTokens = @($tokens | Where-Object { $_ -ieq 'all' })
    if ($allTokens.Count -gt 0) {
        if ($tokens.Count -ne 1) {
            throw 'E2E all cannot be combined with suites or suite arguments.'
        }
        $allRequests = @(
            Get-VisualRegressionSuiteNames -RecordingRepository $RecordingRepository |
                ForEach-Object {
                    $context = Get-VisualRegressionContext -Suite $_
                    [pscustomobject]@{
                        Suite = $context.Suite
                        Arguments = [string[]]@()
                        MovesetRange = $null
                        Generated = [bool]$context.Generated
                        GeneratedFamily = $context.GeneratedFamily
                    }
                }
        )
        if ($allRequests.Count -eq 0) {
            throw 'No E2E suites are available.'
        }
        return [pscustomobject]@{
            All = $true
            Requests = [object[]]$allRequests
        }
    }

    $suiteLookup = [Collections.Generic.Dictionary[string, string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($suiteName in @(
        Get-VisualRegressionSelectableSuiteNames -RecordingRepository $RecordingRepository
    )) {
        $suiteLookup[$suiteName] = $suiteName
    }
    $requests = [Collections.Generic.List[object]]::new()
    $selected = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $captureOwners = [Collections.Generic.Dictionary[string, string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $currentSuite = $null
    $currentArguments = [Collections.Generic.List[string]]::new()
    $completeRequest = {
        if ($null -ne $currentSuite) {
            $context = Get-VisualRegressionContext -Suite $currentSuite
            $resolved = Resolve-VisualRegressionSuiteArguments `
                -Context $context `
                -Argument ([string[]]$currentArguments)
            if (-not $selected.Add($context.Suite)) {
                throw "Duplicate E2E suite selection: $($context.Suite)"
            }
            $captureKey = [IO.Path]::GetFullPath($context.CaptureRoot)
            if ($captureOwners.ContainsKey($captureKey)) {
                throw (
                    "E2E suites $($captureOwners[$captureKey]) and $($context.Suite) " +
                    'share capture history and cannot be selected together.'
                )
            }
            $captureOwners[$captureKey] = $context.Suite
            $requests.Add([pscustomobject]@{
                Suite = $context.Suite
                Arguments = [string[]]@($resolved.Arguments)
                MovesetRange = $resolved.MovesetRange
                Generated = [bool]$context.Generated
                GeneratedFamily = $context.GeneratedFamily
            })
        }
    }

    foreach ($tokenValue in $tokens) {
        $normalized = $tokenValue.Replace('\', '/')
        if ($normalized.EndsWith('.p2m2', [StringComparison]::OrdinalIgnoreCase)) {
            $normalized = $normalized.Substring(0, $normalized.Length - 5)
        }
        if ($suiteLookup.ContainsKey($normalized)) {
            . $completeRequest
            $currentSuite = $suiteLookup[$normalized]
            $currentArguments = [Collections.Generic.List[string]]::new()
            continue
        }
        if ($null -eq $currentSuite) {
            throw "E2E suite does not exist: $tokenValue"
        }
        $currentArguments.Add($tokenValue)
    }
    . $completeRequest
    if ($requests.Count -eq 0) {
        throw 'Select all or at least one E2E suite.'
    }
    [pscustomobject]@{
        All = $false
        Requests = [object[]]$requests
    }
}
