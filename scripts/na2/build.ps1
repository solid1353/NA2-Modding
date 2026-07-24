[CmdletBinding()]
param(
    [switch]$CandidateOnly,
    [string]$WorkerOutputIso,
    [ValidateSet('translation', 'mapping_ids')]
    [string]$TranslationDisplay = 'translation'
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\build_log.ps1')
. (Join-Path $PSScriptRoot 'process.ps1')
. (Join-Path $PSScriptRoot 'worker_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

if ($CandidateOnly -and -not [string]::IsNullOrWhiteSpace($WorkerOutputIso)) {
    throw '-CandidateOnly and -WorkerOutputIso are mutually exclusive.'
}
if ($TranslationDisplay -ne 'translation' -and
    [string]::IsNullOrWhiteSpace($WorkerOutputIso)) {
    throw 'Diagnostic translation display is allowed only for worker-output builds.'
}
$workerBuild = if (-not [string]::IsNullOrWhiteSpace($WorkerOutputIso)) {
    Get-Na2WorkerBuildContext `
        -OutputPath $WorkerOutputIso `
        -ProjectPaths $projectPaths
}
else {
    $null
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

function Invoke-Na2BuildPreflight {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('check', 'record')][string]$Command,
        [Parameter(Mandatory = $true)][string]$Na2Iso,
        [Parameter(Mandatory = $true)][string]$Nun5Iso,
        [Parameter(Mandatory = $true)][string]$CurrentIso,
        [Parameter(Mandatory = $true)][string]$Profile,
        [Parameter(Mandatory = $true)][string]$Receipt,
        [AllowNull()][string]$ExpectedFingerprint,
        [Parameter(Mandatory = $true)][string]$Repository
    )

    $arguments = @(
        '-B'
        '-m', 'na2_patcher.build_preflight'
        $Command
        '--na2-iso', $Na2Iso
        '--nun5-iso', $Nun5Iso
        '--current', $CurrentIso
        '--profile', $Profile
        '--receipt', $Receipt
    )
    if ($Command -eq 'record') {
        if ([string]::IsNullOrWhiteSpace($ExpectedFingerprint)) {
            throw 'Cannot record a build receipt without the pre-build fingerprint.'
        }
        $arguments += @('--expected-fingerprint', $ExpectedFingerprint)
    }

    Push-Location $Repository
    try {
        $output = @(& python @arguments)
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    if ($exitCode -ne 0) {
        throw "NA2 build preflight failed to execute (exit $exitCode)."
    }
    if ($output.Count -ne 1) {
        throw 'NA2 build preflight did not return exactly one JSON result.'
    }
    try {
        return $output[0] | ConvertFrom-Json
    }
    catch {
        throw 'NA2 build preflight returned invalid JSON.'
    }
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

$inputIso = $projectPaths.files.na2_iso
$nun5Iso = $projectPaths.files.nun5_iso
$resolvedOutputIso = [IO.Path]::GetFullPath($projectPaths.files.current_iso)
$resolvedPreviousIso = [IO.Path]::GetFullPath($projectPaths.files.previous_iso)
$resolvedCandidateIso = [IO.Path]::GetFullPath($projectPaths.files.candidate_iso)
$profile = [IO.Path]::GetRelativePath(
    $projectPaths.repository,
    (Join-Path $projectPaths.patcher 'profiles\current')
)
$logDirectory = Join-Path $projectPaths.logs 'na2'
$buildLogRoot = Join-Path $logDirectory 'builds'
$receiptPath = Join-Path $logDirectory 'preflight\current.json'
$candidateIso = "$resolvedOutputIso.building"

if ($CandidateOnly -or $null -ne $workerBuild) {
    $candidateBuildId = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + "_pid$PID"
    $isolatedKind = if ($null -ne $workerBuild) { 'worker' } else { 'candidate' }
    $isolatedOutputIso = if ($null -ne $workerBuild) {
        $workerBuild.OutputIso
    }
    else {
        $resolvedCandidateIso
    }
    $candidateLogRoot = if ($null -ne $workerBuild) {
        Join-Path $workerBuild.Logs 'builds'
    }
    else {
        Join-Path $logDirectory 'candidates'
    }
    $candidateProfileLog = Join-Path $candidateLogRoot $candidateBuildId
    $candidateProfileLogDirectory = [IO.Path]::GetRelativePath(
        $projectPaths.repository,
        $candidateProfileLog
    )
    $candidateBuildingIso = "$isolatedOutputIso.building"
    $candidateArguments = @(
        '-B'
        '-m', 'na2_patcher.build_profile'
        '--source', $inputIso
        '--output', $isolatedOutputIso
        '--profile', $profile
        '--profile-log-directory', $candidateProfileLogDirectory
        '--translation-display', $TranslationDisplay
    )

    $isolatedLabel = if ($isolatedKind -eq 'worker') {
        'Worker-output mode'
    }
    else {
        'Candidate mode'
    }
    Write-Host (
        "[na2] ${isolatedLabel}: full verified build; preflight, PCSX2 shutdown, " +
        'Current/Previous promotion, rotation, and receipt updates are disabled.'
    ) -ForegroundColor Cyan
    if ($TranslationDisplay -ne 'translation') {
        Write-Host (
            "[na2] Diagnostic translation display: $TranslationDisplay; " +
            'canonical mappings and the active profile remain unchanged.'
        ) -ForegroundColor Cyan
    }
    $candidateCompleted = $false
    try {
        Push-Location $projectPaths.repository
        try {
            $candidateOutput = & python @candidateArguments
            $candidateExitCode = $LASTEXITCODE
        }
        finally {
            Pop-Location
        }
        $candidateOutput | ForEach-Object { Write-Host $_ }
        if ($candidateExitCode -ne 0) {
            throw "NA2 $isolatedKind build failed (exit $candidateExitCode)."
        }
        if (-not (Test-Path -LiteralPath $candidateProfileLog -PathType Container)) {
            throw "$isolatedLabel completed without creating its structured build record."
        }
        if (-not (Test-Path -LiteralPath $candidateBuildingIso -PathType Leaf)) {
            throw "Verified $isolatedKind ISO does not exist: $candidateBuildingIso"
        }

        $candidateChanged = -not (
            (Test-Path -LiteralPath $isolatedOutputIso -PathType Leaf) -and
            (Test-FileContentEqual `
                -LeftPath $candidateBuildingIso `
                -RightPath $isolatedOutputIso)
        )
        $candidateState = if ($candidateChanged) { 'updated' } else { 'unchanged' }

        $profilePortable = ConvertTo-Na2PortableText `
            -Text $profile `
            -ProjectPaths $projectPaths
        $candidatePortable = ConvertTo-Na2PortableText `
            -Text $isolatedOutputIso `
            -ProjectPaths $projectPaths
        $recordPortable = ConvertTo-Na2PortableText `
            -Text $candidateProfileLog `
            -ProjectPaths $projectPaths
        $resultContent = @(
            "timestamp_utc`tresult`toutput_state`trotation`tpcsx2_closed`tprofile`toutput_iso`tbuild_record"
            (
                (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') + "`t" +
                "$isolatedKind`t$candidateState`tno`tno`t$profilePortable`t$candidatePortable`t$recordPortable"
            )
        ) -join "`n"
        $resultContent += "`n"
        if (Test-Na2WindowsAbsolutePath -Text $resultContent) {
            throw "Refusing to write the $isolatedKind result with an absolute path."
        }
        $resultFilename = if ($isolatedKind -eq 'worker') {
            'build_result.tsv'
        }
        else {
            'candidate_result.tsv'
        }
        Set-Na2Utf8FileAtomic `
            -Path (Join-Path $candidateProfileLog $resultFilename) `
            -Content $resultContent

        if ($candidateChanged) {
            [IO.File]::Move($candidateBuildingIso, $isolatedOutputIso, $true)
        }
        else {
            Remove-Item -LiteralPath $candidateBuildingIso -Force
        }

        if ($isolatedKind -eq 'candidate') {
            Get-ChildItem -LiteralPath $candidateLogRoot -Directory |
                Where-Object FullName -CNE $candidateProfileLog |
                Remove-Item -Recurse -Force
        }
        else {
            Get-ChildItem -LiteralPath $candidateLogRoot -Directory |
                Where-Object {
                    $_.FullName -CNE $candidateProfileLog -and
                    (Test-Path -LiteralPath (Join-Path $_.FullName 'build_result.tsv') -PathType Leaf)
                } |
                Sort-Object LastWriteTimeUtc -Descending |
                Select-Object -Skip 19 |
                Remove-Item -Recurse -Force
        }
        $candidateCompleted = $true
        $candidateRecord = ConvertTo-Na2ProjectPath `
            -Path $candidateProfileLog `
            -ProjectPaths $projectPaths
        Write-Host (
            "[na2] ISO result: $isolatedKind ($candidateState); Current/Previous unchanged; " +
            'rotation: no; PCSX2 left running.'
        ) -ForegroundColor Cyan
        Write-Host "[na2] $isolatedLabel record: retained $candidateRecord." -ForegroundColor Cyan
        return [pscustomobject]@{
            Status = $isolatedKind
            CandidateState = $candidateState
            OutputState = $candidateState
            OutputIso = $isolatedOutputIso
            CandidateIso = if ($isolatedKind -eq 'candidate') { $isolatedOutputIso } else { $null }
            CurrentIso = $resolvedOutputIso
            PreviousIso = $resolvedPreviousIso
            Rotated = $false
            BuildId = $candidateBuildId
            ProfileLogDirectory = $candidateRecord
            PreflightCacheHit = $false
            Pcsx2Closed = $false
        }
    }
    finally {
        if (Test-Path -LiteralPath $candidateBuildingIso) {
            Remove-Item -LiteralPath $candidateBuildingIso -Force
        }
        if (-not $candidateCompleted -and
            (Test-Path -LiteralPath $candidateProfileLog -PathType Container)) {
            Remove-Item -LiteralPath $candidateProfileLog -Recurse -Force
        }
        if ($null -ne $workerBuild) {
            Remove-Na2EmptyWorkerAncestors `
                -Path $candidateLogRoot `
                -WorkRoot $projectPaths.work
            Remove-Na2EmptyWorkerAncestors `
                -Path ([IO.Path]::GetDirectoryName($candidateBuildingIso)) `
                -WorkRoot $projectPaths.work
        }
    }
}

New-Item -ItemType Directory -Path $buildLogRoot -Force | Out-Null

try {
    $preflight = Invoke-Na2BuildPreflight `
        -Command check `
        -Na2Iso $inputIso `
        -Nun5Iso $nun5Iso `
        -CurrentIso $resolvedOutputIso `
        -Profile $profile `
        -Receipt $receiptPath `
        -Repository $projectPaths.repository
}
catch {
    $preflight = [pscustomobject]@{
        status = 'miss'
        reason = 'preflight-command-error'
        detail = $_.Exception.Message
    }
}

if ($preflight.status -eq 'hit') {
    try {
        $buildMap = Read-Na2BuildMap `
            -LogDirectory $logDirectory `
            -ProjectPaths $projectPaths
        if ([string]::IsNullOrWhiteSpace($buildMap.CurrentBuildId)) {
            throw 'The Current ISO has no retained build record.'
        }
        $buildRecord = "@logs/na2/builds/$($buildMap.CurrentBuildId)"
        Write-Host (
            "[na2] Preflight: cache hit; fingerprint $($preflight.fingerprint); " +
            "Current SHA-256 $($preflight.output_sha256)."
        ) -ForegroundColor Cyan
        Write-Host '[na2] ISO result: unchanged; preflight cache hit; rotation: no.' -ForegroundColor Cyan
        Write-Host "[na2] Build record: reused $buildRecord." -ForegroundColor Cyan
        return [pscustomobject]@{
            Status = 'unchanged'
            CurrentIso = $resolvedOutputIso
            PreviousIso = $resolvedPreviousIso
            Rotated = $false
            BuildId = $buildMap.CurrentBuildId
            ProfileLogDirectory = $buildRecord
            PreflightCacheHit = $true
        }
    }
    catch {
        $preflight = [pscustomobject]@{
            status = 'miss'
            reason = 'build-record-invalid'
            detail = $_.Exception.Message
            fingerprint = $preflight.fingerprint
        }
    }
}

$preflightDetail = if ($preflight.PSObject.Properties.Name -contains 'detail') {
    ": $($preflight.detail)"
}
else {
    ''
}
Write-Host (
    "[na2] Preflight: cache miss ($($preflight.reason)$preflightDetail); " +
    'running the full verified build.'
) -ForegroundColor Yellow
$preflightFingerprint = if ($preflight.PSObject.Properties.Name -contains 'fingerprint') {
    [string]$preflight.fingerprint
}
else {
    $null
}

$buildId = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + "_pid$PID"
$profileLog = Join-Path $buildLogRoot $buildId
$profileLogDirectory = [IO.Path]::GetRelativePath($projectPaths.repository, $profileLog)
$pcsx2Exe = $projectPaths.files.pcsx2_exe
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
    Write-Host "[na2] Build record: retained $($buildRecord.BuildRecord)." -ForegroundColor Cyan
    $promotion | Add-Member -NotePropertyName BuildId -NotePropertyValue $buildRecord.BuildId
    $promotion | Add-Member -NotePropertyName ProfileLogDirectory -NotePropertyValue $buildRecord.BuildRecord
    $promotion | Add-Member -NotePropertyName PreflightCacheHit -NotePropertyValue $false
    if (-not [string]::IsNullOrWhiteSpace($preflightFingerprint)) {
        try {
            $receiptResult = Invoke-Na2BuildPreflight `
                -Command record `
                -Na2Iso $inputIso `
                -Nun5Iso $nun5Iso `
                -CurrentIso $resolvedOutputIso `
                -Profile $profile `
                -Receipt $receiptPath `
                -ExpectedFingerprint $preflightFingerprint `
                -Repository $projectPaths.repository
            if ($receiptResult.status -eq 'written') {
                Write-Host (
                    "[na2] Preflight receipt: updated for fingerprint " +
                    "$($receiptResult.fingerprint)."
                ) -ForegroundColor Cyan
            }
            else {
                Write-Warning (
                    "Preflight receipt was not updated ($($receiptResult.reason)); " +
                    'the next build will safely run in full.'
                )
            }
        }
        catch {
            Write-Warning (
                "Preflight receipt was not updated: $($_.Exception.Message) " +
                'The next build will safely run in full.'
            )
        }
    }
    else {
        Write-Warning 'Preflight fingerprint was unavailable; the next build will safely run in full.'
    }
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
