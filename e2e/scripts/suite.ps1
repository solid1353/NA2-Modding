$ErrorActionPreference = 'Stop'
$script:E2eCaptureTiers = [ordered]@{
    Reference = 'reference'
    Current = 'current'
}
$script:E2eReportDirectory = 'report'

function Get-VisualRegressionContext {
    param([Parameter(Mandatory)][string]$Suite)

    if ([string]::IsNullOrWhiteSpace($Suite) -or [IO.Path]::IsPathRooted($Suite)) {
        throw 'Suite must be a relative path.'
    }
    $normalizedSuite = $Suite.Replace('\', '/')
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
    $root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    $repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
    $caseRoot = Join-Path (Join-Path $root 'suites') $suiteRelativePath
    $captureRoot = Join-Path (Join-Path $root 'captures') $suiteRelativePath
    $statesRoot = Join-Path $captureRoot 'sstates'
    [pscustomobject]@{
        Root = $root
        CaptureRepository = Join-Path $root 'captures'
        Suite = $suiteName
        SuiteRelativePath = $suiteRelativePath
        SuiteRoot = $caseRoot
        CaptureRoot = $captureRoot
        Capture = [pscustomobject]@{
            Reference = Join-Path $captureRoot $script:E2eCaptureTiers.Reference
            Current = Join-Path $captureRoot $script:E2eCaptureTiers.Current
            Report = Join-Path $captureRoot $script:E2eReportDirectory
            States = $statesRoot
            ReferenceStates = Join-Path $statesRoot $script:E2eCaptureTiers.Reference
            CurrentStates = Join-Path $statesRoot $script:E2eCaptureTiers.Current
        }
        Repository = $repository
        Comparator = Join-Path $repository 'scripts\research\localization\compare_font_capture_sets.ps1'
        PythonRunner = Join-Path $repository 'scripts\lib\run_python.ps1'
    }
}

function New-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Prefix
    )

    $transactions = [IO.Path]::GetFullPath((Join-Path $Root '.transactions'))
    [void](New-Item -ItemType Directory -Path $transactions -Force)
    foreach ($candidate in Get-ChildItem -LiteralPath $transactions -Directory -Force) {
        $ownerPath = Join-Path $candidate.FullName 'owner.json'
        if (-not (Test-Path -LiteralPath $ownerPath -PathType Leaf)) {
            continue
        }
        try {
            $owner = Get-Content -Raw -LiteralPath $ownerPath | ConvertFrom-Json
            $ownerProcess = [Diagnostics.Process]::GetProcessById([int]$owner.pid)
            $ownerStart = [DateTime]::Parse(
                [string]$owner.process_start_utc,
                [Globalization.CultureInfo]::InvariantCulture,
                [Globalization.DateTimeStyles]::RoundtripKind
            ).ToUniversalTime()
            $isLive = (
                [int]$owner.pid -ne $PID -and
                $ownerProcess.StartTime.ToUniversalTime() -eq $ownerStart
            )
        }
        catch [ArgumentException] {
            $isLive = $false
        }
        catch [InvalidOperationException] {
            $isLive = $false
        }
        catch {
            $isLive = $true
        }
        if ($isLive) {
            continue
        }
        Remove-Item -LiteralPath $candidate.FullName -Recurse -Force
    }
    $transaction = Join-Path $transactions (
        $Prefix + '-' + [guid]::NewGuid().ToString('N')
    )
    [void](New-Item -ItemType Directory -Path $transaction)
    $process = Get-Process -Id $PID
    $owner = [ordered]@{
        schema_version = 1
        pid = $PID
        process_start_utc = $process.StartTime.ToUniversalTime().ToString('O')
        created_utc = (Get-Date).ToUniversalTime().ToString('O')
    } | ConvertTo-Json
    $ownerPath = Join-Path $transaction 'owner.json'
    $ownerTemporary = "$ownerPath.tmp-$([guid]::NewGuid().ToString('N'))"
    [IO.File]::WriteAllText($ownerTemporary, $owner + "`n", [Text.UTF8Encoding]::new($false))
    [IO.File]::Move($ownerTemporary, $ownerPath, $true)
    return $transaction
}

function Remove-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string]$Root
    )

    $transactions = [IO.Path]::GetFullPath((Join-Path $Root '.transactions'))
    $resolvedTransaction = [IO.Path]::GetFullPath($Transaction)
    $transactionPrefix = $transactions.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $resolvedTransaction.StartsWith($transactionPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a transaction outside $transactions"
    }
    if (Test-Path -LiteralPath $resolvedTransaction) {
        Remove-Item -LiteralPath $resolvedTransaction -Recurse -Force
    }
    if ((Test-Path -LiteralPath $transactions -PathType Container) -and
        @(Get-ChildItem -LiteralPath $transactions -Force).Count -eq 0) {
        Remove-Item -LiteralPath $transactions -Force
    }
}

function Invoke-VisualRegressionReplay {
    param(
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string]$SharedRecordingRoot,
        [Parameter(Mandatory)][string]$RecordingPath,
        [Parameter(Mandatory)][string]$Game,
        [Parameter(Mandatory)][string]$CaptureRoot
    )

    $generatedRecordingRoot = Join-Path $SharedRecordingRoot 'generated'
    [void](New-Item -ItemType Directory -Path $generatedRecordingRoot -Force)
    $stagedName = Join-Path `
        'generated' `
        ('e2e-' + [guid]::NewGuid().ToString('N') + '.p2m2')
    $stagedPath = Join-Path $SharedRecordingRoot $stagedName
    try {
        Copy-Item -LiteralPath $RecordingPath -Destination $stagedPath
        & (Join-Path $Repository 'na228.ps1') `
            $Game -t $stagedName -o $CaptureRoot
    }
    finally {
        if (Test-Path -LiteralPath $stagedPath -PathType Leaf) {
            Remove-Item -LiteralPath $stagedPath -Force
        }
    }
}

function New-VisualRegressionStateStage {
    param(
        [Parameter(Mandatory)][string]$ExistingRoot,
        [Parameter(Mandatory)][string]$StageRoot,
        [Parameter(Mandatory)][string]$Tier,
        [Parameter(Mandatory)][string]$CapturedDirectory,
        [Parameter(Mandatory)][string]$CaptureRepository,
        [Parameter(Mandatory)][string]$ExistingScreenshotDirectory,
        [Parameter(Mandatory)][string]$CapturedScreenshotDirectory,
        [Parameter(Mandatory)][string]$PythonRunner,
        [string]$IgnoreFile
    )

    if ($Tier -cnotin $script:E2eCaptureTiers.Values) {
        throw "Unknown capture tier: $Tier"
    }
    [void](New-Item -ItemType Directory -Path $StageRoot -Force)
    foreach ($preservedTier in $script:E2eCaptureTiers.Values) {
        if ($preservedTier -ceq $Tier) { continue }
        $source = Join-Path $ExistingRoot $preservedTier
        if (Test-Path -LiteralPath $source -PathType Container) {
            Copy-Item -LiteralPath $source -Destination $StageRoot -Recurse -Force
        }
    }
    $destination = Join-Path $StageRoot $Tier
    [void](New-Item -ItemType Directory -Path $destination -Force)
    $existingStates = Join-Path $ExistingRoot $Tier
    $committedStates = Join-Path $StageRoot '.committed-states'
    [void](New-Item -ItemType Directory -Path $committedStates -Force)
    $identicalScreenshots = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    if (Test-Path -LiteralPath $ExistingScreenshotDirectory -PathType Container) {
        $comparison = @(
            & $PythonRunner `
                -PackageSet imaging `
                -Script (Join-Path $PSScriptRoot 'find_identical_pngs.py') `
                -ArgumentList @(
                    '--repository', $CaptureRepository,
                    '--existing-prefix', [IO.Path]::GetRelativePath(
                        $CaptureRepository,
                        $ExistingScreenshotDirectory
                    ).Replace('\', '/'),
                    '--captured', $CapturedScreenshotDirectory,
                    '--state-prefix', [IO.Path]::GetRelativePath(
                        $CaptureRepository,
                        $existingStates
                    ).Replace('\', '/'),
                    '--state-output', $committedStates
                ) `
                -NoBytecode
        )
        if ($LASTEXITCODE -ne 0) {
            throw "PNG comparison failed with exit code $LASTEXITCODE."
        }
        foreach ($name in $comparison) {
            if (-not [string]::IsNullOrWhiteSpace($name)) {
                [void]$identicalScreenshots.Add($name)
            }
        }
    }

    $ignoredScreenshots = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $ignoredNames = @(Get-IgnoredCaptureNames -IgnoreFile $IgnoreFile)
    if ($ignoredNames.Count -gt 0) {
        $ignoredScreenshots.UnionWith([string[]]$ignoredNames)
    }
    foreach ($capturedState in Get-ChildItem -LiteralPath $CapturedDirectory -Filter '*.p2s' -File) {
        $screenshotName = $capturedState.BaseName + '.png'
        if ($ignoredScreenshots.Contains($screenshotName)) {
            continue
        }
        $existingState = Join-Path $committedStates $capturedState.Name
        $sourceState = if (
            $identicalScreenshots.Contains($screenshotName) -and
            (Test-Path -LiteralPath $existingState -PathType Leaf)
        ) {
            $existingState
        }
        else {
            $capturedState.FullName
        }
        Copy-Item -LiteralPath $sourceState -Destination $destination
    }
    foreach ($screenshotName in $ignoredScreenshots) {
        $stateName = [IO.Path]::ChangeExtension($screenshotName, '.p2s')
        $existingState = Join-Path $existingStates $stateName
        if (Test-Path -LiteralPath $existingState -PathType Leaf) {
            Copy-Item -LiteralPath $existingState -Destination $destination
        }
    }
    Remove-Item -LiteralPath $committedStates -Recurse -Force
}

function Get-NumericPngSlots {
    param([Parameter(Mandatory)][string]$Directory)

    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) {
        return [int[]]@()
    }
    [int[]]@(
        Get-ChildItem -LiteralPath $Directory -Filter '*.png' -File |
            ForEach-Object {
                if ($_.BaseName -notmatch '(\d+)$') {
                    throw "PNG name has no numeric suffix: $($_.FullName)"
                }
                [int]$Matches[1]
            } |
            Sort-Object -Unique
    )
}

function Get-IgnoredCaptureNames {
    param([string]$IgnoreFile)

    if (-not (Test-Path -LiteralPath $IgnoreFile -PathType Leaf)) {
        return [string[]]@()
    }

    [string[]]@(
        foreach ($line in Get-Content -LiteralPath $IgnoreFile) {
            $entry = $line.Trim()
            if ($entry.Length -gt 0 -and -not $entry.StartsWith('#')) {
                $entry
            }
        }
    )
}

function Restore-IgnoredCurrentScreenshots {
    param(
        [Parameter(Mandatory)][string]$CurrentDirectory,
        [Parameter(Mandatory)][string]$ExistingDirectory,
        [Parameter(Mandatory)][string]$IgnoreFile
    )

    $restored = 0
    foreach ($name in Get-IgnoredCaptureNames -IgnoreFile $IgnoreFile) {
        $current = Join-Path $CurrentDirectory $name
        $existing = Join-Path $ExistingDirectory $name
        if (Test-Path -LiteralPath $existing -PathType Leaf) {
            Copy-Item -LiteralPath $existing -Destination $current -Force
            $restored++
        }
        elseif (Test-Path -LiteralPath $current -PathType Leaf) {
            Remove-Item -LiteralPath $current -Force
        }
    }
    return $restored
}

function Get-CommonSlots {
    param([Parameter(Mandatory)][string[]]$Directories)

    $common = $null
    foreach ($directory in $Directories) {
        $slots = [Collections.Generic.HashSet[int]]::new()
        $numericSlots = @(Get-NumericPngSlots -Directory $directory)
        if ($numericSlots.Count -gt 0) {
            $slots.UnionWith([int[]]$numericSlots)
        }
        if ($null -eq $common) {
            $common = $slots
        }
        else {
            $common.IntersectWith($slots)
        }
    }
    if ($null -eq $common) {
        return [int[]]@()
    }
    [int[]]@($common | Sort-Object)
}

function New-VisualRegressionReport {
    param(
        [Parameter(Mandatory)][string]$Suite,
        [Parameter(Mandatory)][string]$CurrentDirectory,
        [Parameter(Mandatory)][string]$OutputRoot,
        [string]$ReferenceDirectory
    )

    $context = Get-VisualRegressionContext -Suite $Suite
    if ([string]::IsNullOrWhiteSpace($ReferenceDirectory)) {
        $ReferenceDirectory = $context.Capture.Reference
    }
    $slots = @(Get-CommonSlots -Directories @($ReferenceDirectory, $CurrentDirectory))
    if ($slots.Count -eq 0) {
        return
    }
    [void](New-Item -ItemType Directory -Path $OutputRoot -Force)
    & $context.Comparator `
        -ReferenceDirectory $ReferenceDirectory `
        -CurrentDirectory $CurrentDirectory `
        -OutputDirectory $OutputRoot `
        -ReferenceLabel 'Reference' `
        -CurrentLabel 'Current'
    if ($LASTEXITCODE -ne 0) {
        throw "Reference/current comparison failed with exit code $LASTEXITCODE."
    }
}

function Compare-VisualRegressionVariants {
    param(
        [Parameter(Mandatory)][string]$Suite,
        [Parameter(Mandatory)][string]$BaselineDirectory,
        [Parameter(Mandatory)][string]$CandidateDirectory,
        [Parameter(Mandatory)][string]$OutputRoot,
        [string]$IgnoreFile
    )

    $ignored = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $ignoredNames = @(Get-IgnoredCaptureNames -IgnoreFile $IgnoreFile)
    if ($ignoredNames.Count -gt 0) {
        $ignored.UnionWith([string[]]$ignoredNames)
    }
    $baseline = @{}
    $candidate = @{}
    foreach ($file in Get-ChildItem -LiteralPath $BaselineDirectory -Filter '*.png' -File) {
        if (-not $ignored.Contains($file.Name)) { $baseline[$file.Name] = $file.FullName }
    }
    foreach ($file in Get-ChildItem -LiteralPath $CandidateDirectory -Filter '*.png' -File) {
        if (-not $ignored.Contains($file.Name)) { $candidate[$file.Name] = $file.FullName }
    }
    $names = @($baseline.Keys + $candidate.Keys | Sort-Object -Unique)
    $mismatches = [Collections.Generic.List[object]]::new()
    $differenceRoot = Join-Path $OutputRoot 'differences'
    foreach ($name in $names) {
        $kind = if (-not $baseline.ContainsKey($name)) {
            'missing-in-normal'
        }
        elseif (-not $candidate.ContainsKey($name)) {
            'missing-in-padded'
        }
        elseif (
            (Get-FileHash -LiteralPath $baseline[$name] -Algorithm SHA256).Hash -cne
            (Get-FileHash -LiteralPath $candidate[$name] -Algorithm SHA256).Hash
        ) {
            'content'
        }
        else {
            $null
        }
        if ($null -eq $kind) { continue }
        $mismatches.Add([ordered]@{ name = $name; kind = $kind })
        foreach ($side in @(
            [pscustomobject]@{ Name = 'normal'; Files = $baseline },
            [pscustomobject]@{ Name = 'padded'; Files = $candidate }
        )) {
            if (-not $side.Files.ContainsKey($name)) { continue }
            $sideRoot = Join-Path $differenceRoot $side.Name
            [void](New-Item -ItemType Directory -Path $sideRoot -Force)
            Copy-Item -LiteralPath $side.Files[$name] -Destination (Join-Path $sideRoot $name)
        }
    }
    [void](New-Item -ItemType Directory -Path $OutputRoot -Force)
    $result = [ordered]@{
        schema_version = 1
        suite = $Suite
        status = if ($mismatches.Count -eq 0) { 'passed' } else { 'failed' }
        compared = $names.Count
        ignored = $ignored.Count
        mismatches = @($mismatches)
    }
    $resultPath = Join-Path $OutputRoot 'result.json'
    [IO.File]::WriteAllText(
        $resultPath,
        (($result | ConvertTo-Json -Depth 5) + "`n"),
        [Text.UTF8Encoding]::new($false)
    )
    return [pscustomobject]$result
}

function Publish-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][Collections.IDictionary]$Replacements,
        [Parameter(Mandatory)][string]$TransactionRoot
    )

    function Clear-PublishedFiles {
        param([Parameter(Mandatory)][string]$Root)

        if (Test-Path -LiteralPath $Root -PathType Container) {
            Get-ChildItem -LiteralPath $Root -Recurse -File -Force |
                Remove-Item -Force
        }
    }

    function Copy-PublishedFiles {
        param(
            [Parameter(Mandatory)][string]$Source,
            [Parameter(Mandatory)][string]$Destination
        )

        [void](New-Item -ItemType Directory -Path $Destination -Force)
        foreach ($file in Get-ChildItem -LiteralPath $Source -Recurse -File -Force) {
            $relative = [IO.Path]::GetRelativePath($Source, $file.FullName)
            $target = Join-Path $Destination $relative
            [void](New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force)
            $temporary = "$target.publishing-$([guid]::NewGuid().ToString('N'))"
            try {
                [IO.File]::Copy($file.FullName, $temporary, $true)
                [IO.File]::Move($temporary, $target, $true)
            }
            finally {
                if (Test-Path -LiteralPath $temporary -PathType Leaf) {
                    Remove-Item -LiteralPath $temporary -Force
                }
            }
        }
    }

    function Sync-PublishedFiles {
        param(
            [Parameter(Mandatory)][string]$Source,
            [Parameter(Mandatory)][string]$Destination
        )

        [void](New-Item -ItemType Directory -Path $Destination -Force)
        $sourceFiles = @(Get-ChildItem -LiteralPath $Source -Recurse -File -Force)
        $relativePaths = [Collections.Generic.HashSet[string]]::new(
            [StringComparer]::OrdinalIgnoreCase
        )
        foreach ($file in $sourceFiles) {
            $relative = [IO.Path]::GetRelativePath($Source, $file.FullName)
            [void]$relativePaths.Add($relative)
            $target = Join-Path $Destination $relative
            [void](New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force)
            $temporary = "$target.publishing-$([guid]::NewGuid().ToString('N'))"
            try {
                [IO.File]::Copy($file.FullName, $temporary, $true)
                [IO.File]::Move($temporary, $target, $true)
            }
            finally {
                if (Test-Path -LiteralPath $temporary -PathType Leaf) {
                    Remove-Item -LiteralPath $temporary -Force
                }
            }
        }
        foreach ($file in @(Get-ChildItem -LiteralPath $Destination -Recurse -File -Force)) {
            $relative = [IO.Path]::GetRelativePath($Destination, $file.FullName)
            if (-not $relativePaths.Contains($relative)) {
                Remove-Item -LiteralPath $file.FullName -Force
            }
        }
    }

    function Remove-EmptyPublishedDirectories {
        param([Parameter(Mandatory)][string]$Root)

        if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return }
        foreach ($directory in @(
            Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force |
                Sort-Object { $_.FullName.Length } -Descending
        )) {
            if (@(Get-ChildItem -LiteralPath $directory.FullName -Force).Count -ne 0) {
                continue
            }
            try {
                [IO.Directory]::Delete($directory.FullName)
            }
            catch [IO.IOException] {}
            catch [UnauthorizedAccessException] {}
        }
    }

    $published = [Collections.Generic.List[object]]::new()
    $backupRoot = Join-Path $TransactionRoot '.backups'
    [void](New-Item -ItemType Directory -Path $backupRoot -Force)
    $backupIndex = 0
    try {
        foreach ($destination in $Replacements.Keys) {
            $source = $Replacements[$destination]
            $backup = Join-Path $backupRoot ('{0:D4}' -f $backupIndex)
            $backupIndex++
            $stableDirectoryNames = @($script:E2eCaptureTiers.Values) + $script:E2eReportDirectory
            if ($stableDirectoryNames -ccontains [IO.Path]::GetFileName($destination)) {
                if (Test-Path -LiteralPath $destination -PathType Container) {
                    Copy-PublishedFiles -Source $destination -Destination $backup
                }
                try {
                    Sync-PublishedFiles -Source $source -Destination $destination
                    Remove-EmptyPublishedDirectories -Root $destination
                    $published.Add([pscustomobject]@{
                        Destination = $destination
                        Backup = $backup
                        Stable = $true
                    })
                }
                catch {
                    Clear-PublishedFiles -Root $destination
                    if (Test-Path -LiteralPath $backup -PathType Container) {
                        Copy-PublishedFiles -Source $backup -Destination $destination
                    }
                    throw
                }
                continue
            }
            if (Test-Path -LiteralPath $destination) {
                [IO.Directory]::Move($destination, $backup)
            }
            try {
                [IO.Directory]::Move($source, $destination)
                $published.Add([pscustomobject]@{
                    Destination = $destination
                    Backup = $backup
                    Stable = $false
                })
            }
            catch {
                if (Test-Path -LiteralPath $backup) {
                    [IO.Directory]::Move($backup, $destination)
                }
                throw
            }
        }
    }
    catch {
        for ($index = $published.Count - 1; $index -ge 0; $index--) {
            $item = $published[$index]
            if ($item.Stable) {
                Clear-PublishedFiles -Root $item.Destination
                if (Test-Path -LiteralPath $item.Backup -PathType Container) {
                    Copy-PublishedFiles -Source $item.Backup -Destination $item.Destination
                }
                Remove-EmptyPublishedDirectories -Root $item.Destination
                continue
            }
            if (Test-Path -LiteralPath $item.Destination) {
                Remove-Item -LiteralPath $item.Destination -Recurse -Force
            }
            if (Test-Path -LiteralPath $item.Backup) {
                [IO.Directory]::Move($item.Backup, $item.Destination)
            }
        }
        throw
    }
    foreach ($item in $published) {
        if (Test-Path -LiteralPath $item.Backup) {
            Remove-Item -LiteralPath $item.Backup -Recurse -Force
        }
    }
}
