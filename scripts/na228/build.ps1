[CmdletBinding()]
param(
    [switch]$ManualTestOnly,
    [switch]$ScreenshotTestOnly,
    [switch]$ComposeOnly,
    [string]$WorkerOutputIso
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\build_log.ps1')
. (Join-Path $PSScriptRoot 'worker_paths.ps1')
$paths = Get-Na2Paths

if (
    @(
        $ManualTestOnly.IsPresent
        $ScreenshotTestOnly.IsPresent
        $ComposeOnly.IsPresent
        -not [string]::IsNullOrWhiteSpace($WorkerOutputIso)
    ).Where({ $_ }).Count -gt 1
) {
    throw '-ManualTestOnly, -ScreenshotTestOnly, -ComposeOnly, and -WorkerOutputIso are mutually exclusive.'
}
$workerBuild = if (-not [string]::IsNullOrWhiteSpace($WorkerOutputIso)) {
    Get-Na2WorkerBuildContext `
        -OutputPath $WorkerOutputIso `
        -Paths $paths
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
        [Parameter(Mandatory = $true)][string]$LatestIso,
        [Parameter(Mandatory = $true)][string]$Profile,
        [Parameter(Mandatory = $true)][string]$Receipt,
        [AllowNull()][string]$ExpectedFingerprint,
        [Parameter(Mandatory = $true)][string]$Repository
    )

    $arguments = @(
        '-B'
        '-m', 'na228_builder.build_preflight'
        $Command
        '--na2-iso', $Na2Iso
        '--nun5-iso', $Nun5Iso
        '--latest', $LatestIso
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
        [Parameter(Mandatory = $true)][string]$LatestIso,
        [Parameter(Mandatory = $true)][string]$PreviousIso
    )

    $latest = [IO.Path]::GetFullPath($LatestIso)
    $previous = [IO.Path]::GetFullPath($PreviousIso)
    $staged = "$latest.building"
    if (-not (Test-Path -LiteralPath $staged -PathType Leaf)) {
        throw "Verified staged ISO does not exist: $staged"
    }

    if ((Test-Path -LiteralPath $latest -PathType Leaf) -and
        (Test-FileContentEqual -LeftPath $staged -RightPath $latest)) {
        Write-Host "[na228] ISO result: unchanged; staged image matches $([IO.Path]::GetFileName($latest)), promotion and rotation skipped." -ForegroundColor Cyan
        return [pscustomobject]@{
            Status = 'unchanged'
            LatestIso = $latest
            PreviousIso = $previous
            Rotated = $false
            ChangedRoles = [string[]]@()
        }
    }

    $rotatedLatest = $false
    try {
        if (Test-Path -LiteralPath $latest -PathType Leaf) {
            [IO.File]::Move($latest, $previous, $true)
            $rotatedLatest = $true
        }
        [IO.File]::Move($staged, $latest, $true)
    }
    catch {
        if ($rotatedLatest -and
            -not (Test-Path -LiteralPath $latest) -and
            (Test-Path -LiteralPath $previous -PathType Leaf)) {
            [IO.File]::Move($previous, $latest, $true)
        }
        throw
    }

    $rotationResult = if ($rotatedLatest) {
        "previous image retained as $([IO.Path]::GetFileName($previous))"
    }
    else {
        'no previous image was available to retain'
    }
    Write-Host "[na228] ISO result: updated; staged image promoted to $([IO.Path]::GetFileName($latest)), $rotationResult." -ForegroundColor Cyan
    $changedRoles = [Collections.Generic.List[string]]::new()
    $changedRoles.Add('latest')
    if ($rotatedLatest) {
        $changedRoles.Add('previous')
    }
    [pscustomobject]@{
        Status = 'updated'
        LatestIso = $latest
        PreviousIso = $previous
        Rotated = $rotatedLatest
        ChangedRoles = [string[]]@($changedRoles)
    }
}

$inputIso = $paths.files.na2_iso
$nun5Iso = $paths.files.nun5_iso
$resolvedLatestIso = [IO.Path]::GetFullPath($paths.files.latest_iso)
$resolvedPreviousIso = [IO.Path]::GetFullPath($paths.files.previous_iso)
$resolvedManualTestIso = [IO.Path]::GetFullPath($paths.files.manual_test_iso)
$resolvedScreenshotTestIso = [IO.Path]::GetFullPath($paths.files.screenshot_test_iso)
$profile = [IO.Path]::GetRelativePath(
    $paths.repository,
    (Join-Path $paths.builder 'profiles\default.tsv')
)
$logDirectory = Join-Path $paths.logs 'na228'
$buildLogRoot = Join-Path $logDirectory 'builds'
$receiptPath = Join-Path $logDirectory 'preflight\latest.json'
$stagedIso = "$resolvedLatestIso.building"

if ($ComposeOnly) {
    $composeArguments = @(
        '-B'
        '-m', 'na228_builder.build_profile'
        '--source', $inputIso
        '--profile', $profile
        '--compose-only'
    )
    Write-Host (
        '[na228] Compose-only: derive and conflict-check the full pinned profile; ' +
        'preflight reuse and ISO staging are disabled.'
    ) -ForegroundColor Cyan
    Push-Location $paths.repository
    try {
        $composeOutput = & python @composeArguments
        $composeExitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    $composeOutput | ForEach-Object { Write-Host $_ }
    if ($composeExitCode -ne 0) {
        throw "NA2 profile composition failed (exit $composeExitCode)."
    }
    Write-Host '[na228] Profile composition valid; no ISO produced.' -ForegroundColor Cyan
    return [pscustomobject]@{
        Status = 'validated'
        LatestIso = $resolvedLatestIso
        PreviousIso = $resolvedPreviousIso
        Rotated = $false
        PreflightCacheHit = $false
        ChangedRoles = [string[]]@()
    }
}

if ($ManualTestOnly -or $ScreenshotTestOnly -or $null -ne $workerBuild) {
    $isolatedBuildId = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + "_pid$PID"
    $isolatedKind = if ($null -ne $workerBuild) {
        'worker'
    }
    elseif ($ScreenshotTestOnly) {
        'screenshot-test'
    }
    else {
        'manual-test'
    }
    $isolatedOutputIso = if ($null -ne $workerBuild) {
        $workerBuild.OutputIso
    }
    elseif ($ScreenshotTestOnly) {
        $resolvedScreenshotTestIso
    }
    else {
        $resolvedManualTestIso
    }
    $isolatedLogRoot = if ($null -ne $workerBuild) {
        Join-Path $workerBuild.Logs 'builds'
    }
    elseif ($ScreenshotTestOnly) {
        Join-Path $logDirectory 'screenshot_tests'
    }
    else {
        Join-Path $logDirectory 'manual_tests'
    }
    $isolatedProfileLog = Join-Path $isolatedLogRoot $isolatedBuildId
    $isolatedProfileLogDirectory = [IO.Path]::GetRelativePath(
        $paths.repository,
        $isolatedProfileLog
    )
    $isolatedBuildingIso = "$isolatedOutputIso.building"
    $isolatedArguments = @(
        '-B'
        '-m', 'na228_builder.build_profile'
        '--source', $inputIso
        '--output', $isolatedOutputIso
        '--profile', $profile
        '--profile-log-directory', $isolatedProfileLogDirectory
    )

    $isolatedLabel = switch ($isolatedKind) {
        'worker' { 'Worker-output mode' }
        'screenshot-test' { 'Screenshot Test mode' }
        default { 'Manual Test mode' }
    }
    Write-Host (
        "[na228] ${isolatedLabel}: full verified build; preflight, " +
        'Latest/Previous promotion, rotation, and receipt updates are disabled.'
    ) -ForegroundColor Cyan
    $isolatedCompleted = $false
    try {
        Push-Location $paths.repository
        try {
            $isolatedOutput = & python @isolatedArguments
            $isolatedExitCode = $LASTEXITCODE
        }
        finally {
            Pop-Location
        }
        $isolatedOutput | ForEach-Object { Write-Host $_ }
        if ($isolatedExitCode -ne 0) {
            throw "NA2 $isolatedKind build failed (exit $isolatedExitCode)."
        }
        if (-not (Test-Path -LiteralPath $isolatedProfileLog -PathType Container)) {
            throw "$isolatedLabel completed without creating its structured build record."
        }
        if (-not (Test-Path -LiteralPath $isolatedBuildingIso -PathType Leaf)) {
            throw "Verified $isolatedKind ISO does not exist: $isolatedBuildingIso"
        }

        $isolatedChanged = -not (
            (Test-Path -LiteralPath $isolatedOutputIso -PathType Leaf) -and
            (Test-FileContentEqual `
                -LeftPath $isolatedBuildingIso `
                -RightPath $isolatedOutputIso)
        )
        $isolatedState = if ($isolatedChanged) { 'updated' } else { 'unchanged' }

        $profilePortable = ConvertTo-Na2PortableText `
            -Text $profile `
            -Paths $paths
        $outputPortable = ConvertTo-Na2PortableText `
            -Text $isolatedOutputIso `
            -Paths $paths
        $recordPortable = ConvertTo-Na2PortableText `
            -Text $isolatedProfileLog `
            -Paths $paths
        $resultContent = @(
            "timestamp_utc`tresult`toutput_state`trotation`tpcsx2_closed`tprofile`toutput_iso`tbuild_record"
            (
                (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') + "`t" +
                "$isolatedKind`t$isolatedState`tno`tno`t$profilePortable`t$outputPortable`t$recordPortable"
            )
        ) -join "`n"
        $resultContent += "`n"
        if (Test-Na2WindowsAbsolutePath -Text $resultContent) {
            throw "Refusing to write the $isolatedKind result with an absolute path."
        }
        $resultFilename = switch ($isolatedKind) {
            'worker' { 'build_result.tsv' }
            'screenshot-test' { 'screenshot_test_result.tsv' }
            default { 'manual_test_result.tsv' }
        }
        Set-Na2Utf8FileAtomic `
            -Path (Join-Path $isolatedProfileLog $resultFilename) `
            -Content $resultContent

        if ($isolatedChanged) {
            [IO.File]::Move($isolatedBuildingIso, $isolatedOutputIso, $true)
        }
        else {
            Remove-Item -LiteralPath $isolatedBuildingIso -Force
        }

        if ($isolatedKind -in @('manual-test', 'screenshot-test')) {
            Get-ChildItem -LiteralPath $isolatedLogRoot -Directory |
                Where-Object FullName -CNE $isolatedProfileLog |
                Remove-Item -Recurse -Force
        }
        else {
            Get-ChildItem -LiteralPath $isolatedLogRoot -Directory |
                Where-Object {
                    $_.FullName -CNE $isolatedProfileLog -and
                    (Test-Path -LiteralPath (Join-Path $_.FullName 'build_result.tsv') -PathType Leaf)
                } |
                Sort-Object LastWriteTimeUtc -Descending |
                Select-Object -Skip 19 |
                Remove-Item -Recurse -Force
        }
        $isolatedCompleted = $true
        $isolatedRecord = ConvertTo-Na2ProjectPath `
            -Path $isolatedProfileLog `
            -Paths $paths
        Write-Host (
            "[na228] ISO result: $isolatedKind ($isolatedState); Latest/Previous unchanged; " +
            'rotation: no; PCSX2 left running.'
        ) -ForegroundColor Cyan
        Write-Host (
            "[na228] $isolatedLabel record: retained " +
            $isolatedProfileLog
        ) -ForegroundColor Cyan
        return [pscustomobject]@{
            Status = $isolatedKind
            ManualTestState = if ($isolatedKind -eq 'manual-test') { $isolatedState } else { $null }
            ScreenshotTestState = if ($isolatedKind -eq 'screenshot-test') { $isolatedState } else { $null }
            OutputState = $isolatedState
            OutputIso = $isolatedOutputIso
            ManualTestIso = if ($isolatedKind -eq 'manual-test') { $isolatedOutputIso } else { $null }
            ScreenshotTestIso = if ($isolatedKind -eq 'screenshot-test') { $isolatedOutputIso } else { $null }
            LatestIso = $resolvedLatestIso
            PreviousIso = $resolvedPreviousIso
            Rotated = $false
            BuildId = $isolatedBuildId
            ProfileLogDirectory = $isolatedRecord
            PreflightCacheHit = $false
            ChangedRoles = [string[]]@(
                if ($isolatedKind -eq 'manual-test' -and $isolatedChanged) {
                    'manual_test'
                }
                elseif ($isolatedKind -eq 'screenshot-test' -and $isolatedChanged) {
                    'screenshot_test'
                }
            )
        }
    }
    finally {
        if (Test-Path -LiteralPath $isolatedBuildingIso) {
            Remove-Item -LiteralPath $isolatedBuildingIso -Force
        }
        if (-not $isolatedCompleted -and
            (Test-Path -LiteralPath $isolatedProfileLog -PathType Container)) {
            Remove-Item -LiteralPath $isolatedProfileLog -Recurse -Force
        }
        if ($null -ne $workerBuild) {
            Remove-Na2EmptyWorkerAncestors `
                -Path $isolatedLogRoot `
                -WorkRoot $paths.work
            Remove-Na2EmptyWorkerAncestors `
                -Path ([IO.Path]::GetDirectoryName($isolatedBuildingIso)) `
                -WorkRoot $paths.work
        }
    }
}

New-Item -ItemType Directory -Path $buildLogRoot -Force | Out-Null

try {
    $preflight = Invoke-Na2BuildPreflight `
        -Command check `
        -Na2Iso $inputIso `
        -Nun5Iso $nun5Iso `
        -LatestIso $resolvedLatestIso `
        -Profile $profile `
        -Receipt $receiptPath `
        -Repository $paths.repository
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
            -Paths $paths
        if ([string]::IsNullOrWhiteSpace($buildMap.LatestBuildId)) {
            throw 'The Latest ISO has no retained build record.'
        }
        $buildRecord = "@logs/na228/builds/$($buildMap.LatestBuildId)"
        Write-Host (
            "[na228] Preflight: cache hit; fingerprint $($preflight.fingerprint); " +
            "Latest SHA-256 $($preflight.output_sha256)."
        ) -ForegroundColor Cyan
        Write-Host '[na228] ISO result: unchanged; preflight cache hit; rotation: no.' -ForegroundColor Cyan
        $buildRecordPath = Join-Path $buildLogRoot $buildMap.LatestBuildId
        Write-Host "[na228] Build record: reused $buildRecordPath" -ForegroundColor Cyan
        return [pscustomobject]@{
            Status = 'unchanged'
            LatestIso = $resolvedLatestIso
            PreviousIso = $resolvedPreviousIso
            Rotated = $false
            BuildId = $buildMap.LatestBuildId
            ProfileLogDirectory = $buildRecord
            PreflightCacheHit = $true
            ChangedRoles = [string[]]@()
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
    "[na228] Preflight: cache miss ($($preflight.reason)$preflightDetail); " +
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
$profileLogDirectory = [IO.Path]::GetRelativePath($paths.repository, $profileLog)
$arguments = @(
    '-B'
    '-m', 'na228_builder.build_profile'
    '--source', $inputIso
    '--output', $resolvedLatestIso
    '--profile', $profile
    '--profile-log-directory', $profileLogDirectory
)

$promotionCompleted = $false
try {
    Push-Location $paths.repository
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

    $promotion = Promote-VerifiedIso `
        -LatestIso $resolvedLatestIso `
        -PreviousIso $resolvedPreviousIso
    $promotionCompleted = $true
    $buildRecord = Complete-Na2BuildRecord `
        -LogDirectory $logDirectory `
        -BuildId $buildId `
        -Result $promotion.Status `
        -Rotated $promotion.Rotated `
        -LatestIso $promotion.LatestIso `
        -PreviousIso $promotion.PreviousIso `
        -Profile $profile `
        -Paths $paths
    $buildRecordPath = Join-Path $buildLogRoot $buildRecord.BuildId
    Write-Host "[na228] Build record: retained $buildRecordPath" -ForegroundColor Cyan
    $promotion | Add-Member -NotePropertyName BuildId -NotePropertyValue $buildRecord.BuildId
    $promotion | Add-Member -NotePropertyName ProfileLogDirectory -NotePropertyValue $buildRecord.BuildRecord
    $promotion | Add-Member -NotePropertyName PreflightCacheHit -NotePropertyValue $false
    if (-not [string]::IsNullOrWhiteSpace($preflightFingerprint)) {
        try {
            $receiptResult = Invoke-Na2BuildPreflight `
                -Command record `
                -Na2Iso $inputIso `
                -Nun5Iso $nun5Iso `
                -LatestIso $resolvedLatestIso `
                -Profile $profile `
                -Receipt $receiptPath `
                -ExpectedFingerprint $preflightFingerprint `
                -Repository $paths.repository
            if ($receiptResult.status -eq 'written') {
                Write-Host (
                    "[na228] Preflight receipt: updated for fingerprint " +
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
    if (Test-Path -LiteralPath $stagedIso) {
        Remove-Item -Force -LiteralPath $stagedIso
    }
    if (-not $promotionCompleted -and (Test-Path -LiteralPath $profileLog -PathType Container)) {
        Remove-Item -LiteralPath $profileLog -Recurse -Force
    }
}
