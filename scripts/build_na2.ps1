[CmdletBinding()]
param(
    [string]$InputIso,
    [string]$OutputIso,
    [string]$Profile,
    [string]$ProfileLogDirectory,
    [string]$Pcsx2Exe,
    [switch]$AllowSizeChanges
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

function Stop-PortablePcsx2 {
    param([Parameter(Mandatory = $true)][string]$Executable)

    $processName = [IO.Path]::GetFileNameWithoutExtension($Executable)
    Stop-Process -Name $processName -Force -ErrorAction SilentlyContinue
}

function Test-FileContentEqual {
    param(
        [Parameter(Mandatory = $true)][string]$LeftPath,
        [Parameter(Mandatory = $true)][string]$RightPath
    )

    $left = Get-Item -LiteralPath $LeftPath
    $right = Get-Item -LiteralPath $RightPath
    if ($left.Length -ne $right.Length) {
        return $false
    }

    $leftHash = (Get-FileHash -LiteralPath $left.FullName -Algorithm SHA256).Hash
    $rightHash = (Get-FileHash -LiteralPath $right.FullName -Algorithm SHA256).Hash
    $leftHash -ceq $rightHash
}

function Promote-VerifiedIso {
    param([Parameter(Mandatory = $true)][string]$CurrentIso)

    $current = [IO.Path]::GetFullPath($CurrentIso)
    $candidate = "$current.building"
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Verified staged ISO does not exist: $candidate"
    }

    $directory = [IO.Path]::GetDirectoryName($current)
    $isStandardCurrent = [IO.Path]::GetFileName($current) -ieq 'Current.iso'
    $previous = if ($isStandardCurrent) { Join-Path $directory 'Previous.iso' } else { $null }

    if ((Test-Path -LiteralPath $current -PathType Leaf) -and
        (Test-FileContentEqual -LeftPath $candidate -RightPath $current)) {
        Write-Host '[na2] ISO result: unchanged; candidate matches Current.iso, promotion and rotation skipped.' -ForegroundColor Cyan
        return [pscustomobject]@{
            Status = 'unchanged'
            CurrentIso = $current
            PreviousIso = $previous
            Rotated = $false
        }
    }

    $rotatedCurrent = $false
    try {
        if ($previous -and (Test-Path -LiteralPath $current -PathType Leaf)) {
            [IO.File]::Move($current, $previous, $true)
            $rotatedCurrent = $true
        }
        [IO.File]::Move($candidate, $current, $true)
    }
    catch {
        if ($rotatedCurrent -and
            -not (Test-Path -LiteralPath $current) -and
            (Test-Path -LiteralPath $previous -PathType Leaf)) {
            [IO.File]::Move($previous, $current, $true)
        }
        throw
    }

    $rotationResult = if ($rotatedCurrent) {
        'previous image retained as Previous.iso'
    }
    else {
        'no previous image was available to retain'
    }
    Write-Host "[na2] ISO result: updated; candidate promoted to Current.iso, $rotationResult." -ForegroundColor Cyan
    [pscustomobject]@{
        Status = 'updated'
        CurrentIso = $current
        PreviousIso = $previous
        Rotated = $rotatedCurrent
    }
}

if ([string]::IsNullOrWhiteSpace($InputIso)) {
    $InputIso = Join-Path $projectPaths.source 'NA2.iso'
}
if ([string]::IsNullOrWhiteSpace($OutputIso)) {
    $OutputIso = Join-Path $projectPaths.build 'Current.iso'
}
if ([string]::IsNullOrWhiteSpace($Profile)) {
    $Profile = [IO.Path]::GetRelativePath(
        $projectPaths.repository,
        (Join-Path $projectPaths.patcher 'profiles\current')
    )
}
if ([string]::IsNullOrWhiteSpace($ProfileLogDirectory)) {
    $profileLog = Join-Path $projectPaths.logs (
        'na2_patcher\current_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff')
    )
    $ProfileLogDirectory = [IO.Path]::GetRelativePath($projectPaths.repository, $profileLog)
}
if ([string]::IsNullOrWhiteSpace($Pcsx2Exe)) {
    $Pcsx2Exe = Join-Path $projectPaths.pcsx2 'pcsx2-qt.exe'
}

$resolvedOutputIso = if ([IO.Path]::IsPathRooted($OutputIso)) {
    [IO.Path]::GetFullPath($OutputIso)
}
else {
    [IO.Path]::GetFullPath((Join-Path $projectPaths.repository $OutputIso))
}
$candidateIso = "$resolvedOutputIso.building"
$arguments = @(
    (Join-Path $PSScriptRoot 'build_na2_profile.py')
    '--workspace', $projectPaths.repository
    '--source', $InputIso
    '--output', $resolvedOutputIso
    '--profile', $Profile
    '--profile-log-directory', $ProfileLogDirectory
)
if ($AllowSizeChanges) {
    $arguments += '--allow-size-changes'
}

Stop-PortablePcsx2 -Executable $Pcsx2Exe
try {
    $buildOutput = & python -B @arguments
    $buildExitCode = $LASTEXITCODE
    $buildOutput | ForEach-Object { Write-Host $_ }
    if ($buildExitCode -ne 0) {
        throw "NA2 profile build failed (exit $buildExitCode)."
    }

    Stop-PortablePcsx2 -Executable $Pcsx2Exe
    $promotion = Promote-VerifiedIso -CurrentIso $resolvedOutputIso
    $promotion | Add-Member -NotePropertyName ProfileLogDirectory -NotePropertyValue $ProfileLogDirectory
    $promotion
}
finally {
    if (Test-Path -LiteralPath $candidateIso) {
        Remove-Item -Force -LiteralPath $candidateIso
    }
}
