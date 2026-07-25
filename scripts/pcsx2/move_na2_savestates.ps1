[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$SubPath
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

$sourceRoot = Join-Path $projectPaths.pcsx2_user 'sstates'
$destinationRoot = $projectPaths.user_savestates

if ([string]::IsNullOrWhiteSpace($SubPath)) {
    throw 'SubPath cannot be empty.'
}

if ([IO.Path]::IsPathRooted($SubPath)) {
    throw "SubPath must be relative, not an absolute path: $SubPath"
}

if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    throw "Savestate source directory does not exist: $sourceRoot"
}

$trimChars = [char[]]@(
    [IO.Path]::DirectorySeparatorChar,
    [IO.Path]::AltDirectorySeparatorChar
)

$destinationRootFull = [IO.Path]::GetFullPath($destinationRoot).TrimEnd($trimChars)
$destinationFull = [IO.Path]::GetFullPath(
    (Join-Path -Path $destinationRootFull -ChildPath $SubPath)
).TrimEnd($trimChars)

$rootPrefix = $destinationRootFull + [IO.Path]::DirectorySeparatorChar
$destinationPrefix = $destinationFull + [IO.Path]::DirectorySeparatorChar

if (-not $destinationPrefix.StartsWith(
    $rootPrefix,
    [StringComparison]::OrdinalIgnoreCase
)) {
    throw "SubPath escapes the savestate destination root: $SubPath"
}

if ($destinationFull.Equals(
    $destinationRootFull,
    [StringComparison]::OrdinalIgnoreCase
)) {
    throw 'Supply an actual subdirectory rather than the destination root itself.'
}

if (Test-Path -LiteralPath $destinationFull -PathType Leaf) {
    throw "Destination exists as a file: $destinationFull"
}

if (-not (Test-Path -LiteralPath $destinationFull -PathType Container)) {
    if ($PSCmdlet.ShouldProcess($destinationFull, 'Create destination directory')) {
        New-Item `
            -ItemType Directory `
            -Path $destinationFull `
            -Force `
            -ErrorAction Stop |
            Out-Null
    }
}

$stateFiles = @(
    Get-ChildItem `
        -LiteralPath $sourceRoot `
        -File `
        -ErrorAction Stop |
    Where-Object {
        $_.Extension -ieq '.p2s'
    } |
    Sort-Object -Property Name
)

if ($stateFiles.Count -eq 0) {
    Write-Warning "No .p2s savestates found in: $sourceRoot"
    return
}

$parsedStates = @(
    foreach ($file in $stateFiles) {
        $match = [regex]::Match(
            $file.Name,
            '^(?<stem>.+)\.(?<slot>\d+)\.p2s$',
            [Text.RegularExpressions.RegexOptions]::IgnoreCase
        )

        if (-not $match.Success) {
            Write-Warning "Leaving unrecognized savestate filename untouched: $($file.Name)"
            continue
        }

        $slotText = $match.Groups['slot'].Value

        try {
            [long]$slot = $slotText
        }
        catch {
            Write-Warning "Leaving savestate with invalid slot untouched: $($file.Name)"
            continue
        }

        [pscustomobject]@{
            File             = $file
            Stem             = $match.Groups['stem'].Value
            Slot             = $slot
            OriginalSlotText = $slotText
            Width            = [Math]::Max(2, $slotText.Length)
        }
    }
)

if ($parsedStates.Count -eq 0) {
    Write-Warning 'No recognized PCSX2 savestate filenames were found.'
    return
}

$reservedTargets = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)

$slotGroups = @(
    $parsedStates |
    Group-Object -Property Slot |
    Sort-Object {
        [long]$_.Name
    }
)

foreach ($slotGroup in $slotGroups) {
    [long]$candidateSlot = [long]$slotGroup.Name

    do {
        $plans = @(
            foreach ($state in $slotGroup.Group) {
                $slotFormat = 'D{0}' -f $state.Width
                $candidateSlotText = $candidateSlot.ToString(
                    $slotFormat,
                    [Globalization.CultureInfo]::InvariantCulture
                )
                $targetName = '{0}.{1}.p2s' -f (
                    $state.Stem,
                    $candidateSlotText
                )
                $targetPath = Join-Path `
                    -Path $destinationFull `
                    -ChildPath $targetName

                [pscustomobject]@{
                    State             = $state
                    CandidateSlot     = $candidateSlot
                    CandidateSlotText = $candidateSlotText
                    TargetName        = $targetName
                    TargetPath        = $targetPath
                }
            }
        )

        $hasConflict = $false

        foreach ($plan in $plans) {
            if (
                (Test-Path -LiteralPath $plan.TargetPath) -or
                $reservedTargets.Contains($plan.TargetPath)
            ) {
                $hasConflict = $true
                break
            }
        }

        if ($hasConflict) {
            if ($candidateSlot -gt ([long]::MaxValue - 10)) {
                throw "Could not allocate another slot for source slot $($slotGroup.Name)."
            }

            $candidateSlot += 10
        }
    }
    while ($hasConflict)

    foreach ($plan in $plans) {
        [void]$reservedTargets.Add($plan.TargetPath)
    }

    foreach ($plan in $plans) {
        $sourcePath = $plan.State.File.FullName

        if ($PSCmdlet.ShouldProcess(
            $plan.TargetPath,
            "Move '$sourcePath'"
        )) {
            Move-Item `
                -LiteralPath $sourcePath `
                -Destination $plan.TargetPath `
                -ErrorAction Stop

            [pscustomobject]@{
                Source             = $plan.State.File.Name
                Destination        = $plan.TargetName
                OriginalSlot       = $plan.State.OriginalSlotText
                NewSlot            = $plan.CandidateSlotText
                RenamedForConflict = (
                    $plan.CandidateSlot -ne $plan.State.Slot
                )
            }
        }
    }
}
