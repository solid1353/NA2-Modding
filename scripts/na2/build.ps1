[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\build_log.ps1')
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
    param(
        [Parameter(Mandatory = $true)][string]$CurrentIso,
        [Parameter(Mandatory = $true)][string]$PreviousIso
    )

    $current = [IO.Path]::GetFullPath($CurrentIso)
    $previous = [IO.Path]::GetFullPath($PreviousIso)
    $candidate = "$current.building"
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Verified staged ISO does not exist: $candidate"
    }

    if ((Test-Path -LiteralPath $current -PathType Leaf) -and
        (Test-FileContentEqual -LeftPath $candidate -RightPath $current)) {
        Write-Host "[na2] ISO result: unchanged; candidate matches $([IO.Path]::GetFileName($current)), promotion and rotation skipped." -ForegroundColor Cyan
        return [pscustomobject]@{
            Status = 'unchanged'
            CurrentIso = $current
            PreviousIso = $previous
            Rotated = $false
        }
    }

    $rotatedCurrent = $false
    try {
        if (Test-Path -LiteralPath $current -PathType Leaf) {
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
        "previous image retained as $([IO.Path]::GetFileName($previous))"
    }
    else {
        'no previous image was available to retain'
    }
    Write-Host "[na2] ISO result: updated; candidate promoted to $([IO.Path]::GetFileName($current)), $rotationResult." -ForegroundColor Cyan
    [pscustomobject]@{
        Status = 'updated'
        CurrentIso = $current
        PreviousIso = $previous
        Rotated = $rotatedCurrent
    }
}

$inputIso = Join-Path $projectPaths.source 'NA2.iso'
$resolvedOutputIso = [IO.Path]::GetFullPath($projectPaths.files.current_iso)
$resolvedPreviousIso = [IO.Path]::GetFullPath($projectPaths.files.previous_iso)
$profile = [IO.Path]::GetRelativePath(
    $projectPaths.repository,
    (Join-Path $projectPaths.patcher 'profiles\current')
)
$logDirectory = Join-Path $projectPaths.logs 'na2'
$buildLogRoot = Join-Path $logDirectory 'builds'
New-Item -ItemType Directory -Path $buildLogRoot -Force | Out-Null
$buildId = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + "_pid$PID"
$profileLog = Join-Path $buildLogRoot $buildId
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
$promotionCompleted = $false
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
    if (-not (Test-Path -LiteralPath $profileLog -PathType Container)) {
        throw 'Profile build completed without creating its structured build record.'
    }

    Stop-Na2Pcsx2 -Executable $pcsx2Exe
    $promotion = Promote-VerifiedIso `
        -CurrentIso $resolvedOutputIso `
        -PreviousIso $resolvedPreviousIso
    $promotionCompleted = $true
    $buildRecord = Complete-Na2BuildRecord `
        -LogDirectory $logDirectory `
        -BuildId $buildId `
        -Result $promotion.Status `
        -Rotated $promotion.Rotated `
        -CurrentIso $promotion.CurrentIso `
        -PreviousIso $promotion.PreviousIso `
        -Profile $profile `
        -ProjectPaths $projectPaths
    $recordAction = if ($buildRecord.Reused) { 'reused' } else { 'retained' }
    Write-Host "[na2] Build record: $recordAction $($buildRecord.BuildRecord)." -ForegroundColor Cyan
    $promotion | Add-Member -NotePropertyName BuildId -NotePropertyValue $buildRecord.BuildId
    $promotion | Add-Member -NotePropertyName ProfileLogDirectory -NotePropertyValue $buildRecord.BuildRecord
    $promotion
}
finally {
    if (Test-Path -LiteralPath $candidateIso) {
        Remove-Item -Force -LiteralPath $candidateIso
    }
    if (-not $promotionCompleted -and (Test-Path -LiteralPath $profileLog -PathType Container)) {
        Remove-Item -LiteralPath $profileLog -Recurse -Force
    }
}
