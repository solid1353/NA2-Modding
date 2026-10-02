function Invoke-VisualRegressionGeneratedCapture {
    param(
        [Parameter(Mandatory)][object]$Context,
        [Parameter(Mandatory)][string]$Game,
        [Parameter(Mandatory)][string]$Tier,
        [Parameter(Mandatory)][string]$OutputRoot,
        [Parameter(Mandatory)][int]$ThrottleLimit,
        [string]$ConcurrencyPoolRoot,
        [string]$MovesetRange
    )

    $arguments = @{
        Game = $Game
        Tier = $Tier
        OutputRoot = $OutputRoot
        ThrottleLimit = $ThrottleLimit
        ConcurrencyPoolRoot = $ConcurrencyPoolRoot
        ProjectRoot = $Context.Repository
        MemoryCard = $Context.MemoryCard
        LaunchProfile = $Context.LaunchProfile
        MovesetFamily = $Context.GeneratedFamily
    }
    if (-not [string]::IsNullOrWhiteSpace($MovesetRange)) {
        $arguments.MovesetRange = $MovesetRange
    }
    & $Context.GeneratedScript @arguments
}

function Add-VisualRegressionSuiteLaunchSettings {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][hashtable]$Target,
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string]$Game,
        [string]$MemoryCard,
        [AllowNull()][psobject]$LaunchProfile,
        [AllowNull()][psobject]$Paths
    )

    if (-not [string]::IsNullOrWhiteSpace($MemoryCard)) {
        $Target.MemoryCard = $MemoryCard
    }
    if ($null -ne $LaunchProfile) {
        if ($null -eq $Paths) {
            . (Join-Path $Repository 'scripts\lib\paths.ps1')
            $Paths = Get-Na2Paths
        }
        . (Join-Path $Repository 'scripts\na228\launch_profile.ps1')
        $profile = Resolve-Na2LaunchProfile `
            -Name ([string]$LaunchProfile.Name) `
            -Paths $Paths
        $profileResults = @(
            Invoke-Na2LaunchProfile `
                -Profile $profile `
                -Arguments ([string[]]@($LaunchProfile.Arguments)) `
                -Games @($Game) `
                -ProjectRoot $Repository
        )
        if ($profileResults.Count -ne 1) {
            throw (
                "E2E suite launch profile $($profile.Name) must return exactly " +
                "one configuration; got $($profileResults.Count)."
            )
        }
        $Target.ReadOnlySettings = $true
        Merge-Na2LaunchProfileParameters `
            -Target $Target `
            -Profile $profile `
            -Result $profileResults[0]
    }
}

function Enter-VisualRegressionConcurrencyPool {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][ValidateRange(1, 64)][int]$Capacity
    )

    $resolvedRoot = [IO.Path]::GetFullPath($Root)
    [void](New-Item -ItemType Directory -Path $resolvedRoot -Force)
    while ($true) {
        for ($slot = 1; $slot -le $Capacity; $slot++) {
            $slotPath = Join-Path $resolvedRoot ('slot-{0:D2}.lock' -f $slot)
            try {
                return [IO.File]::Open(
                    $slotPath,
                    [IO.FileMode]::OpenOrCreate,
                    [IO.FileAccess]::ReadWrite,
                    [IO.FileShare]::None
                )
            }
            catch [IO.IOException] {
                # Another replay owns this slot. Try the next one.
            }
        }
        Start-Sleep -Milliseconds 50
    }
}

function Invoke-VisualRegressionPooledReplay {
    param(
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string]$SharedRecordingRoot,
        [Parameter(Mandatory)][string]$RecordingPath,
        [Parameter(Mandatory)][string]$Game,
        [Parameter(Mandatory)][string]$CaptureRoot,
        [Parameter(Mandatory)][string]$ConcurrencyPoolRoot,
        [Parameter(Mandatory)][ValidateRange(1, 64)][int]$ConcurrencyLimit,
        [string]$MemoryCard,
        [AllowNull()][psobject]$LaunchProfile
    )

    $permit = Enter-VisualRegressionConcurrencyPool `
        -Root $ConcurrencyPoolRoot `
        -Capacity $ConcurrencyLimit
    try {
        $resolvedRecordingRoot = [IO.Path]::GetFullPath($SharedRecordingRoot)
        if (-not (Test-VisualRegressionPathWithin `
            -Path $RecordingPath `
            -Root $resolvedRecordingRoot)) {
            throw "E2E recording must be inside $resolvedRecordingRoot."
        }
        $recordingName = [IO.Path]::GetRelativePath(
            $resolvedRecordingRoot,
            [IO.Path]::GetFullPath($RecordingPath)
        )

        Write-Host "[e2e] Replaying $Game"
        . (Join-Path $Repository 'scripts\lib\paths.ps1')
        $paths = Get-Na2Paths
        $launchArguments = @{
            Games = $Game
            Play = $recordingName
            Snapshots = $true
            InputRecordingCaptureMode = 'screenshots'
            CaptureDirectory = $CaptureRoot
            InputRecordingsRoot = $SharedRecordingRoot
            ProjectRoot = $Repository
        }
        Add-VisualRegressionSuiteLaunchSettings `
            -Target $launchArguments `
            -Repository $Repository `
            -Game $Game `
            -MemoryCard $MemoryCard `
            -LaunchProfile $LaunchProfile `
            -Paths $paths
        & $paths.files.pcsx2_game_launch_command @launchArguments
    }
    finally {
        $permit.Dispose()
    }
}
