[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot 'process.ps1')
$projectPaths = Get-Na2ProjectPaths

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

$inputIso = Join-Path $projectPaths.source 'NA2.iso'
$resolvedOutputIso = [IO.Path]::GetFullPath((Join-Path $projectPaths.build 'Current.iso'))
$profile = [IO.Path]::GetRelativePath(
    $projectPaths.repository,
    (Join-Path $projectPaths.patcher 'profiles\current')
)
$profileLog = Join-Path $projectPaths.logs (
    'na2_patcher\current_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + "_pid$PID"
)
$profileLogDirectory = [IO.Path]::GetRelativePath($projectPaths.repository, $profileLog)
$pcsx2Exe = Join-Path $projectPaths.pcsx2 'pcsx2-qt.exe'
$candidateIso = "$resolvedOutputIso.building"
$arguments = @(
    '-B'
    '-m', 'na2_patcher.build_profile'
    '--source', $inputIso
    '--output', $resolvedOutputIso
    '--profile', $profile
    '--profile-log-directory', $profileLogDirectory
)

Stop-Na2Pcsx2 -Executable $pcsx2Exe
try {
    Push-Location $projectPaths.repository
    try {
        $buildOutput = & python @arguments
        $buildExitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    $buildOutput | ForEach-Object { Write-Host $_ }
    if ($buildExitCode -ne 0) {
        throw "NA2 profile build failed (exit $buildExitCode)."
    }

    Stop-Na2Pcsx2 -Executable $pcsx2Exe
    $promotion = Promote-VerifiedIso -CurrentIso $resolvedOutputIso
    $promotion | Add-Member -NotePropertyName ProfileLogDirectory -NotePropertyValue $profileLogDirectory
    $promotion
}
finally {
    if (Test-Path -LiteralPath $candidateIso) {
        Remove-Item -Force -LiteralPath $candidateIso
    }
}
