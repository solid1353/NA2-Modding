[CmdletBinding()]
param(
    [switch]$ManualTestOnly,
    [ValidateSet('normal', 'shifted')][string]$E2eVariant,
    [string]$WorkerOutputIso
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\build_log.ps1')
. (Join-Path $PSScriptRoot 'worker_paths.ps1')
$paths = Get-Na2Paths
$e2eBuild = $null
if (-not [string]::IsNullOrWhiteSpace($E2eVariant)) {
    . (Join-Path $paths.repository 'e2e\scripts\config.ps1')
    $e2eBuild = Get-E2eBuildVariant -Name $E2eVariant
}

if (
    @(
        $ManualTestOnly.IsPresent
        $null -ne $e2eBuild
        -not [string]::IsNullOrWhiteSpace($WorkerOutputIso)
    ).Where({ $_ }).Count -gt 1
) {
    throw '-ManualTestOnly, -E2eVariant, and -WorkerOutputIso are mutually exclusive.'
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

function Get-Na2BuildCrcDiscriminator {
    param(
        [Parameter(Mandatory = $true)][string]$BuildSelector,
        [Parameter(Mandatory = $true)][psobject]$Paths
    )

    $productPath = Join-Path $Paths.repository 'product.json'
    if (-not (Test-Path -LiteralPath $productPath -PathType Leaf)) {
        throw "NA2 product catalog does not exist: $productPath"
    }
    $product = Get-Content -Raw -LiteralPath $productPath | ConvertFrom-Json
    $entryProperty = $product.builds.PSObject.Properties[$BuildSelector]
    if ($null -eq $entryProperty) {
        throw "Unknown NA2 build selector: $BuildSelector"
    }
    $valueProperty = (
        $entryProperty.Value.PSObject.Properties['boot_elf_crc_discriminator']
    )
    if ($null -eq $valueProperty) {
        return [uint32]0
    }
    $value = [string]$valueProperty.Value
    if ($value -cnotmatch '^0x(?<hex>[0-9A-Fa-f]{1,8})$') {
        throw (
            "Build $BuildSelector boot_elf_crc_discriminator must be a " +
            '32-bit hexadecimal value.'
        )
    }
    return [Convert]::ToUInt32($Matches['hex'], 16)
}

function Sync-Na2BuildGameSettings {
    param(
        [Parameter(Mandatory = $true)][string[]]$BuildSelector,
        [Parameter(Mandatory = $true)][psobject]$Paths
    )

    $result = @(
        & $Paths.files.pcsx2_sync_build_game_settings_command `
            -BuildSelector $BuildSelector `
            -ProjectRoot $Paths.repository `
            -PassThru
    )
    if (
        $result.Count -ne 1 -or
        $null -eq $result[0].PSObject.Properties['Builds']
    ) {
        throw 'Build GameSettings synchronization returned no valid result.'
    }
    $updated = @($result[0].UpdatedGameSettings).Count
    Write-Host (
        "[na228] GameSettings: synchronized $(@($result[0].Builds).Count) build(s); " +
        "updated files $updated."
    ) -ForegroundColor Cyan
    return $result[0]
}

function Invoke-Na2BuildPreflight {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('check', 'record')][string]$Command,
        [Parameter(Mandatory = $true)][string]$Na2Iso,
        [Parameter(Mandatory = $true)][string]$Nun5Iso,
        [Parameter(Mandatory = $true)][string]$OutputIso,
        [Parameter(Mandatory = $true)][string]$Profile,
        [Parameter(Mandatory = $true)][string]$Receipt,
        [Parameter(Mandatory = $true)][int]$PayloadShift,
        [Parameter(Mandatory = $true)][uint32]$BootElfCrcDiscriminator,
        [AllowNull()][string]$ExpectedFingerprint,
        [Parameter(Mandatory = $true)][string]$Repository
    )

    $arguments = @(
        '-B'
        '-m', 'na228_builder.build_preflight'
        $Command
        '--na2-iso', $Na2Iso
        '--nun5-iso', $Nun5Iso
        '--output', $OutputIso
        '--profile', $Profile
        '--receipt', $Receipt
        '--payload-shift', [string]$PayloadShift
        '--boot-elf-crc-discriminator', ('0x{0:X8}' -f $BootElfCrcDiscriminator)
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

function Find-Na2IsolatedBuildRecord {
    param(
        [Parameter(Mandatory = $true)][string]$LogRoot,
        [Parameter(Mandatory = $true)][string]$ResultFilename,
        [Parameter(Mandatory = $true)][string]$OutputIso,
        [AllowNull()][string]$Variant,
        [Parameter(Mandatory = $true)][psobject]$Paths
    )

    if (-not (Test-Path -LiteralPath $LogRoot -PathType Container)) {
        return $null
    }
    $expectedOutput = ConvertTo-Na2PortableText -Text $OutputIso -Paths $Paths
    foreach ($record in Get-ChildItem -LiteralPath $LogRoot -Directory |
        Sort-Object LastWriteTimeUtc -Descending) {
        $resultPath = Join-Path $record.FullName $ResultFilename
        if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
            continue
        }
        try {
            $rows = @(Import-Csv -LiteralPath $resultPath -Delimiter "`t")
        }
        catch {
            continue
        }
        if ($rows.Count -ne 1) {
            continue
        }
        $row = $rows[0]
        $outputProperty = $row.PSObject.Properties['output_iso']
        if ($null -eq $outputProperty) {
            continue
        }
        $variantProperty = $row.PSObject.Properties['variant']
        if (
            -not [string]::IsNullOrWhiteSpace($Variant) -and
            (
                $null -eq $variantProperty -or
                [string]$variantProperty.Value -cne $Variant
            )
        ) {
            continue
        }
        if ([string]$outputProperty.Value -ceq $expectedOutput) {
            return $record
        }
    }
    return $null
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
$profile = [IO.Path]::GetRelativePath(
    $paths.repository,
    (Join-Path $paths.builder 'profiles\default.tsv')
)
$logDirectory = Join-Path $paths.logs 'na228'
$buildLogRoot = Join-Path $logDirectory 'builds'
$latestReceiptPath = Join-Path $logDirectory 'preflight\latest.json'
$stagedIso = "$resolvedLatestIso.building"
$buildSelector = if ($null -ne $workerBuild) {
    $null
}
elseif ($null -ne $e2eBuild) {
    [string]$e2eBuild.build
}
elseif ($ManualTestOnly) {
    'manual_test'
}
else {
    'latest'
}
$bootElfCrcDiscriminator = if ($null -eq $buildSelector) {
    [uint32]0
}
else {
    Get-Na2BuildCrcDiscriminator -BuildSelector $buildSelector -Paths $paths
}

if ($ManualTestOnly -or $null -ne $e2eBuild -or $null -ne $workerBuild) {
    $isolatedBuildId = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + "_pid$PID"
    $isolatedKind = if ($null -ne $workerBuild) {
        'worker'
    }
    elseif ($null -ne $e2eBuild) {
        'e2e-test'
    }
    else {
        'manual-test'
    }
    $isolatedOutputIso = if ($null -ne $workerBuild) {
        $workerBuild.OutputIso
    }
    elseif ($null -ne $e2eBuild) {
        $outputProperty = "$([string]$e2eBuild.build)_iso"
        $configuredOutput = $paths.files.PSObject.Properties[$outputProperty]
        if ($null -eq $configuredOutput) {
            throw "E2E build output is not configured: $outputProperty"
        }
        [IO.Path]::GetFullPath([string]$configuredOutput.Value)
    }
    else {
        $resolvedManualTestIso
    }
    $isolatedLogRoot = if ($null -ne $workerBuild) {
        Join-Path $workerBuild.Logs 'builds'
    }
    elseif ($null -ne $e2eBuild) {
        $buildLogRoot
    }
    else {
        Join-Path $logDirectory 'manual_tests'
    }
    $resultFilename = switch ($isolatedKind) {
        'worker' { 'build_result.tsv' }
        'e2e-test' { 'build_result.tsv' }
        default { 'manual_test_result.tsv' }
    }
    $isolatedReceiptPath = if ($null -ne $workerBuild) {
        Join-Path $workerBuild.Logs (
            'preflight\' + [IO.Path]::GetFileName($isolatedOutputIso) + '.json'
        )
    }
    elseif ($null -ne $e2eBuild) {
        Join-Path $logDirectory "preflight\e2e_test_$E2eVariant.json"
    }
    else {
        Join-Path $logDirectory 'preflight\manual_test.json'
    }
    $isolatedProfileLog = Join-Path $isolatedLogRoot $isolatedBuildId
    $isolatedProfileLogDirectory = [IO.Path]::GetRelativePath(
        $paths.repository,
        $isolatedProfileLog
    )
    $isolatedBuildingIso = "$isolatedOutputIso.building"
    $payloadShift = if ($null -ne $e2eBuild) {
        [int]$e2eBuild.payload_shift_bytes
    }
    else {
        0
    }
    $isolatedArguments = @(
        '-B'
        '-m', 'na228_builder.build_profile'
        '--source', $inputIso
        '--output', $isolatedOutputIso
        '--profile', $profile
        '--profile-log-directory', $isolatedProfileLogDirectory
        '--payload-shift', [string]$payloadShift
        '--boot-elf-crc-discriminator', ('0x{0:X8}' -f $bootElfCrcDiscriminator)
    )

    $isolatedLabel = switch ($isolatedKind) {
        'worker' { 'Worker-output mode' }
        'e2e-test' { "E2E Test $E2eVariant mode" }
        default { 'Manual Test mode' }
    }
    try {
        $isolatedPreflight = Invoke-Na2BuildPreflight `
            -Command check `
            -Na2Iso $inputIso `
            -Nun5Iso $nun5Iso `
            -OutputIso $isolatedOutputIso `
            -Profile $profile `
            -Receipt $isolatedReceiptPath `
            -PayloadShift $payloadShift `
            -BootElfCrcDiscriminator $bootElfCrcDiscriminator `
            -Repository $paths.repository
    }
    catch {
        $isolatedPreflight = [pscustomobject]@{
            status = 'miss'
            reason = 'preflight-command-error'
            detail = $_.Exception.Message
        }
    }
    if ($isolatedPreflight.status -eq 'hit') {
        $retainedRecord = Find-Na2IsolatedBuildRecord `
            -LogRoot $isolatedLogRoot `
            -ResultFilename $resultFilename `
            -OutputIso $isolatedOutputIso `
            -Variant $(if ($isolatedKind -eq 'e2e-test') { $E2eVariant } else { $null }) `
            -Paths $paths
        if ($null -ne $retainedRecord) {
            if ($isolatedKind -ne 'worker') {
                $null = Sync-Na2BuildGameSettings `
                    -BuildSelector $buildSelector `
                    -Paths $paths
            }
            $retainedRecordPath = ConvertTo-Na2ProjectPath `
                -Path $retainedRecord.FullName `
                -Paths $paths
            Write-Host (
                "[na228] Preflight: cache hit; fingerprint $($isolatedPreflight.fingerprint); " +
                "$isolatedLabel SHA-256 $($isolatedPreflight.output_sha256)."
            ) -ForegroundColor Cyan
            Write-Host (
                "[na228] ISO result: $isolatedKind (unchanged); preflight cache hit; " +
                'Latest/Previous unchanged; rotation: no; PCSX2 left running.'
            ) -ForegroundColor Cyan
            Write-Host (
                "[na228] $isolatedLabel record: reused $($retainedRecord.FullName)"
            ) -ForegroundColor Cyan
            return [pscustomobject]@{
                Status = $isolatedKind
                ManualTestState = if ($isolatedKind -eq 'manual-test') { 'unchanged' } else { $null }
                E2eTestState = if ($isolatedKind -eq 'e2e-test') { 'unchanged' } else { $null }
                OutputState = 'unchanged'
                OutputIso = $isolatedOutputIso
                ManualTestIso = if ($isolatedKind -eq 'manual-test') { $isolatedOutputIso } else { $null }
                E2eTestIso = if ($isolatedKind -eq 'e2e-test') { $isolatedOutputIso } else { $null }
                E2eVariant = if ($isolatedKind -eq 'e2e-test') { $E2eVariant } else { $null }
                LatestIso = $resolvedLatestIso
                PreviousIso = $resolvedPreviousIso
                Rotated = $false
                BuildId = $retainedRecord.Name
                ProfileLogDirectory = $retainedRecordPath
                PreflightCacheHit = $true
                ChangedRoles = [string[]]@()
            }
        }
        $isolatedPreflight = [pscustomobject]@{
            status = 'miss'
            reason = 'build-record-invalid'
            detail = "$isolatedLabel has no retained build record for its output."
            fingerprint = $isolatedPreflight.fingerprint
        }
    }
    $isolatedPreflightDetail = if (
        $isolatedPreflight.PSObject.Properties.Name -contains 'detail'
    ) {
        ": $($isolatedPreflight.detail)"
    }
    else {
        ''
    }
    Write-Host (
        "[na228] Preflight: cache miss ($($isolatedPreflight.reason)$isolatedPreflightDetail); " +
        'running the full verified build.'
    ) -ForegroundColor Yellow
    $isolatedPreflightFingerprint = if (
        $isolatedPreflight.PSObject.Properties.Name -contains 'fingerprint'
    ) {
        [string]$isolatedPreflight.fingerprint
    }
    else {
        $null
    }
    Write-Host (
        "[na228] ${isolatedLabel}: full verified build; " +
        'Latest/Previous promotion and rotation are disabled.'
    ) -ForegroundColor Cyan
    $activeBuildMarker = if ($isolatedKind -eq 'e2e-test') {
        Join-Path $buildLogRoot ".active-$isolatedBuildId"
    }
    else {
        $null
    }
    $isolatedCompleted = $false
    try {
        if ($null -ne $activeBuildMarker) {
            [void](New-Item -ItemType Directory -Path $buildLogRoot -Force)
            Set-Na2Utf8FileAtomic `
                -Path $activeBuildMarker `
                -Content ("pid`tstarted_utc`n$PID`t$((Get-Date).ToUniversalTime().ToString('O'))`n")
        }
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

        if ($isolatedKind -ne 'e2e-test') {
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
            Set-Na2Utf8FileAtomic `
                -Path (Join-Path $isolatedProfileLog $resultFilename) `
                -Content $resultContent
        }

        if ($isolatedChanged) {
            [IO.File]::Move($isolatedBuildingIso, $isolatedOutputIso, $true)
        }
        else {
            Remove-Item -LiteralPath $isolatedBuildingIso -Force
        }

        if ($isolatedKind -ne 'worker') {
            $null = Sync-Na2BuildGameSettings `
                -BuildSelector $buildSelector `
                -Paths $paths
        }

        if ($isolatedKind -eq 'e2e-test') {
            $e2eRecord = Complete-Na2E2eBuildRecord `
                -LogDirectory $logDirectory `
                -BuildId $isolatedBuildId `
                -Variant $E2eVariant `
                -OutputIso $isolatedOutputIso `
                -Profile $profile `
                -PayloadShift $payloadShift `
                -BootElfCrcDiscriminator $bootElfCrcDiscriminator `
                -Paths $paths
        }
        elseif ($isolatedKind -eq 'manual-test') {
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
        if (-not [string]::IsNullOrWhiteSpace($isolatedPreflightFingerprint)) {
            try {
                $isolatedReceiptResult = Invoke-Na2BuildPreflight `
                    -Command record `
                    -Na2Iso $inputIso `
                    -Nun5Iso $nun5Iso `
                    -OutputIso $isolatedOutputIso `
                    -Profile $profile `
                    -Receipt $isolatedReceiptPath `
                    -PayloadShift $payloadShift `
                    -BootElfCrcDiscriminator $bootElfCrcDiscriminator `
                    -ExpectedFingerprint $isolatedPreflightFingerprint `
                    -Repository $paths.repository
                if ($isolatedReceiptResult.status -eq 'written') {
                    Write-Host (
                        '[na228] Preflight receipt: updated for fingerprint ' +
                        "$($isolatedReceiptResult.fingerprint)."
                    ) -ForegroundColor Cyan
                }
                else {
                    Write-Warning (
                        "Preflight receipt was not updated ($($isolatedReceiptResult.reason)); " +
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
            Write-Warning (
                'Preflight fingerprint was unavailable; the next build will safely run in full.'
            )
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
            E2eTestState = if ($isolatedKind -eq 'e2e-test') { $isolatedState } else { $null }
            OutputState = $isolatedState
            OutputIso = $isolatedOutputIso
            ManualTestIso = if ($isolatedKind -eq 'manual-test') { $isolatedOutputIso } else { $null }
            E2eTestIso = if ($isolatedKind -eq 'e2e-test') { $isolatedOutputIso } else { $null }
            E2eVariant = if ($isolatedKind -eq 'e2e-test') { $E2eVariant } else { $null }
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
                elseif ($isolatedKind -eq 'e2e-test' -and $isolatedChanged) {
                    "e2e_test_$E2eVariant"
                }
            )
        }
    }
    finally {
        if (Test-Path -LiteralPath $isolatedBuildingIso) {
            Remove-Item -LiteralPath $isolatedBuildingIso -Force
        }
        if ($null -ne $activeBuildMarker -and (Test-Path -LiteralPath $activeBuildMarker -PathType Leaf)) {
            Remove-Item -LiteralPath $activeBuildMarker -Force
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
        -OutputIso $resolvedLatestIso `
        -Profile $profile `
        -Receipt $latestReceiptPath `
        -PayloadShift 0 `
        -BootElfCrcDiscriminator $bootElfCrcDiscriminator `
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
        $null = Sync-Na2BuildGameSettings `
            -BuildSelector 'latest' `
            -Paths $paths
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
    '--boot-elf-crc-discriminator', ('0x{0:X8}' -f $bootElfCrcDiscriminator)
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
    $settingsSelectors = [Collections.Generic.List[string]]::new()
    $settingsSelectors.Add('latest')
    if (
        $promotion.Rotated -and
        (Test-Path -LiteralPath $resolvedPreviousIso -PathType Leaf)
    ) {
        $settingsSelectors.Add('previous')
    }
    $null = Sync-Na2BuildGameSettings `
        -BuildSelector @($settingsSelectors) `
        -Paths $paths
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
                -OutputIso $resolvedLatestIso `
                -Profile $profile `
                -Receipt $latestReceiptPath `
                -PayloadShift 0 `
                -BootElfCrcDiscriminator $bootElfCrcDiscriminator `
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
