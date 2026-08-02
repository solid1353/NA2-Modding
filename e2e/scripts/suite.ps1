$ErrorActionPreference = 'Stop'

function Get-VisualRegressionContext {
    param([Parameter(Mandatory)][string]$Suite)

    if ([string]::IsNullOrWhiteSpace($Suite) -or
        [IO.Path]::GetFileName($Suite) -cne $Suite) {
        throw 'Suite must be one directory name.'
    }
    $root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    $repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
    $caseRoot = Join-Path $root "suites\$Suite"
    $captureRoot = Join-Path $root "captures\$Suite"
    [pscustomobject]@{
        Root = $root
        Suite = $Suite
        SuiteRoot = $caseRoot
        CaptureRoot = $captureRoot
        Repository = $repository
        Manifest = Join-Path $caseRoot 'screens.tsv'
        Comparator = Join-Path $repository 'scripts\research\localization\compare_font_capture_sets.ps1'
        PythonRunner = Join-Path $repository 'scripts\lib\run_python.ps1'
        ThreeWay = Join-Path $PSScriptRoot 'three_way_grids.py'
    }
}

function New-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Prefix
    )

    $transactions = Join-Path $Root '.transactions'
    [void](New-Item -ItemType Directory -Path $transactions -Force)
    $transaction = Join-Path $transactions (
        $Prefix + '-' + [guid]::NewGuid().ToString('N')
    )
    [void](New-Item -ItemType Directory -Path $transaction)
    return $transaction
}

function Remove-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string]$Root
    )

    if (Test-Path -LiteralPath $Transaction) {
        Remove-Item -LiteralPath $Transaction -Recurse -Force
    }
    $transactions = Join-Path $Root '.transactions'
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

    $stagedName = 'e2e-' + [guid]::NewGuid().ToString('N') + '.p2m2'
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

function Remove-ApprovedIdenticalPendingScreenshots {
    param(
        [Parameter(Mandatory)][string]$PendingDirectory,
        [Parameter(Mandatory)][string]$Summary
    )

    if (-not (Test-Path -LiteralPath $Summary -PathType Leaf)) {
        return 0
    }
    $identicalSlots = [int[]]@(
        Import-Csv -LiteralPath $Summary -Delimiter "`t" |
            Where-Object { [long]$_.changed_pixels -eq 0 } |
            ForEach-Object { [int]$_.slot }
    )
    $removed = 0
    foreach ($slot in $identicalSlots) {
        $matches = @(
            Get-ChildItem -LiteralPath $PendingDirectory -Filter '*.png' -File |
                Where-Object {
                    $_.BaseName -match '(\d+)$' -and [int]$Matches[1] -eq $slot
                }
        )
        foreach ($match in $matches) {
            Remove-Item -LiteralPath $match.FullName -Force
            $removed++
        }
    }
    return $removed
}

function Write-SubsetManifest {
    param(
        [Parameter(Mandatory)][int[]]$Slots,
        [Parameter(Mandatory)][string]$SourceManifest,
        [Parameter(Mandatory)][string]$Destination
    )

    $metadata = @{}
    if (Test-Path -LiteralPath $SourceManifest -PathType Leaf) {
        foreach ($row in @(Import-Csv -LiteralPath $SourceManifest -Delimiter "`t")) {
            $metadata[[int]$row.slot] = $row
        }
    }
    $rows = foreach ($slot in $Slots) {
        $source = $metadata[$slot]
        [pscustomobject]@{
            slot = $slot
            family = if ($null -ne $source -and $source.family) { $source.family } else { 'unclassified' }
            screen = if ($null -ne $source -and $source.screen) { $source.screen } else { "Slot {0:D4}" -f $slot }
            notes = if ($null -ne $source) { $source.notes } else { '' }
        }
    }
    $rows | Export-Csv -LiteralPath $Destination -Delimiter "`t" -NoTypeInformation -Encoding utf8
}

function New-VisualRegressionReports {
    param(
        [Parameter(Mandatory)][string]$Suite,
        [Parameter(Mandatory)][string]$PendingDirectory,
        [Parameter(Mandatory)][string]$OutputRoot,
        [Parameter(Mandatory)][string]$ScratchRoot,
        [string]$ReferenceDirectory,
        [string]$ApprovedDirectory
    )

    $context = Get-VisualRegressionContext -Suite $Suite
    [void](New-Item -ItemType Directory -Path $ScratchRoot -Force)
    if ([string]::IsNullOrWhiteSpace($ApprovedDirectory)) {
        $ApprovedDirectory = Join-Path $context.CaptureRoot 'approved'
    }
    if ([string]::IsNullOrWhiteSpace($ReferenceDirectory)) {
        $ReferenceDirectory = Join-Path $context.CaptureRoot 'references'
    }
    $sets = @{
        Reference = $ReferenceDirectory
        Approved = $ApprovedDirectory
        Pending = $PendingDirectory
    }
    [void](New-Item -ItemType Directory -Path $OutputRoot -Force)
    $comparisons = @(
        [pscustomobject]@{ Left = 'Approved'; Right = 'Pending'; Name = 'approved-vs-pending' }
        [pscustomobject]@{ Left = 'Reference'; Right = 'Approved'; Name = 'reference-vs-approved' }
        [pscustomobject]@{ Left = 'Reference'; Right = 'Pending'; Name = 'reference-vs-pending' }
    )
    foreach ($comparison in $comparisons) {
        $left = $comparison.Left
        $right = $comparison.Right
        $name = $comparison.Name
        $slots = @(Get-CommonSlots -Directories @($sets[$left], $sets[$right]))
        if ($slots.Count -eq 0) {
            continue
        }
        $destination = Join-Path $OutputRoot $name
        [void](New-Item -ItemType Directory -Path $destination -Force)
        $manifest = Join-Path $ScratchRoot "$name.tsv"
        Write-SubsetManifest -Slots $slots -SourceManifest $context.Manifest -Destination $manifest
        & $context.Comparator `
            -ReferenceDirectory $sets[$left] `
            -CurrentDirectory $sets[$right] `
            -OutputDirectory $destination `
            -Manifest $manifest `
            -ReferenceLabel $left `
            -CurrentLabel $right
        if ($LASTEXITCODE -ne 0) {
            throw "$left/$right comparison failed with exit code $LASTEXITCODE."
        }
    }

    $threeWaySlots = @(Get-CommonSlots -Directories @(
        $sets.Reference, $sets.Approved, $sets.Pending
    ))
    if ($threeWaySlots.Count -eq 0) {
        return
    }
    $threeWayOutput = Join-Path $OutputRoot 'three-way-grids'
    [void](New-Item -ItemType Directory -Path $threeWayOutput -Force)
    $threeWayManifest = Join-Path $ScratchRoot 'three-way.tsv'
    Write-SubsetManifest `
        -Slots $threeWaySlots `
        -SourceManifest $context.Manifest `
        -Destination $threeWayManifest
    & $context.PythonRunner `
        -PackageSet imaging `
        -Script $context.ThreeWay `
        -ArgumentList @(
            '--reference', $sets.Reference,
            '--approved', $sets.Approved,
            '--pending', $sets.Pending,
            '--manifest', $threeWayManifest,
            '--output', $threeWayOutput
        ) `
        -NoBytecode
    if ($LASTEXITCODE -ne 0) {
        throw "Three-way grid generation failed with exit code $LASTEXITCODE."
    }
}

function Publish-VisualRegressionTransaction {
    param(
        [Parameter(Mandatory)][Collections.IDictionary]$Replacements,
        [Parameter(Mandatory)][string]$TransactionRoot
    )

    $published = [Collections.Generic.List[object]]::new()
    try {
        foreach ($destination in $Replacements.Keys) {
            $source = $Replacements[$destination]
            $backup = Join-Path $TransactionRoot ('.backup-' + [IO.Path]::GetFileName($destination))
            if (Test-Path -LiteralPath $destination) {
                [IO.Directory]::Move($destination, $backup)
            }
            try {
                [IO.Directory]::Move($source, $destination)
                $published.Add([pscustomobject]@{ Destination = $destination; Backup = $backup })
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
