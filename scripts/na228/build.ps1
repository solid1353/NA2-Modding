[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$ManualOnly,
    [ValidateSet('normal', 'shifted')][string]$E2eVariant,
    [string]$WorkerOutputIso,
    [switch]$WorkerEphemeral,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\build_log.ps1')
. (Join-Path $PSScriptRoot 'worker_paths.ps1')
$paths = Get-Na2Paths
$pythonRunner = Join-Path $paths.repository 'scripts\lib\run_python.ps1'
$e2eBuild = $null
if (-not [string]::IsNullOrWhiteSpace($E2eVariant)) {
    . (Join-Path $paths.repository 'e2e\scripts\config.ps1')
    $e2eBuild = Get-E2eBuildVariant -Name $E2eVariant
}

if (
    @(
        $DryRun.IsPresent
        $ManualOnly.IsPresent
        $null -ne $e2eBuild
        -not [string]::IsNullOrWhiteSpace($WorkerOutputIso)
    ).Where({ $_ }).Count -gt 1
) {
    throw '-DryRun, -ManualOnly, -E2eVariant, and -WorkerOutputIso are mutually exclusive.'
}
if ($Force -and (
    $DryRun -or
    $null -ne $e2eBuild -or
    -not [string]::IsNullOrWhiteSpace($WorkerOutputIso)
)) {
    throw '-Force is valid only for ordinary Latest or Manual builds.'
}
if ($WorkerEphemeral -and [string]::IsNullOrWhiteSpace($WorkerOutputIso)) {
    throw '-WorkerEphemeral requires -WorkerOutputIso.'
}
$workerBuild = if (-not [string]::IsNullOrWhiteSpace($WorkerOutputIso)) {
    Get-Na2WorkerBuildContext `
        -OutputPath $WorkerOutputIso `
        -Paths $paths
}
else {
    $null
}
if ($WorkerEphemeral -and (Test-Path -LiteralPath $workerBuild.OutputIso)) {
    throw "Ephemeral worker output already exists; refusing to replace it: $($workerBuild.OutputIso)"
}
if ($WorkerEphemeral -and (Test-Path -LiteralPath "$($workerBuild.OutputIso).building")) {
    throw "Ephemeral worker staging output already exists; refusing to replace it: $($workerBuild.OutputIso).building"
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

function Invoke-Na2BuilderModule {
    param(
        [Parameter(Mandatory = $true)][string]$Module,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList
    )

    $output = @(
        & $pythonRunner `
            -PackageSet builder `
            -Module $Module `
            -ArgumentList $ArgumentList `
            -NoBytecode 2>&1
    )
    [pscustomobject]@{
        Output = [string[]]@($output | ForEach-Object { [string]$_ })
        ExitCode = $LASTEXITCODE
    }
}

function Throw-Na2BuilderFailure {
    param(
        [Parameter(Mandatory = $true)][psobject]$Execution,
        [Parameter(Mandatory = $true)][string]$FallbackMessage
    )

    $configurationFailure = Get-Na2ConfigurationFailure -Output $Execution.Output
    if ($null -ne $configurationFailure) {
        $exception = [InvalidOperationException]::new($configurationFailure.Message)
        $exception.Data['Na2ConfigurationError'] = $true
        $exception.Data['Na2TechnicalDetails'] = $configurationFailure.TechnicalDetails
        throw $exception
    }

    $Execution.Output | ForEach-Object { Write-Host $_ }
    throw $FallbackMessage
}

function Invoke-Na2BuildPreflight {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('check', 'record')][string]$Command,
        [Parameter(Mandatory = $true)][string]$Na2Iso,
        [Parameter(Mandatory = $true)][string]$Nun5Iso,
        [Parameter(Mandatory = $true)][string]$OutputIso,
        [Parameter(Mandatory = $true)][string]$Configuration,
        [Parameter(Mandatory = $true)][string]$Receipt,
        [Parameter(Mandatory = $true)][int]$PayloadShift,
        [AllowNull()][string]$ExpectedFingerprint,
        [Parameter(Mandatory = $true)][string]$Repository
    )

    $arguments = @(
        $Command
        '--na2-iso', $Na2Iso
        '--nun5-iso', $Nun5Iso
        '--output', $OutputIso
        '--configuration', $Configuration
        '--receipt', $Receipt
        '--payload-shift', [string]$PayloadShift
    )
    if ($Command -eq 'record') {
        if ([string]::IsNullOrWhiteSpace($ExpectedFingerprint)) {
            throw 'Cannot record a build receipt without the pre-build fingerprint.'
        }
        $arguments += @('--expected-fingerprint', $ExpectedFingerprint)
    }

    Push-Location $Repository
    try {
        $execution = Invoke-Na2BuilderModule `
            -Module 'na228_builder.scripts.build_preflight' `
            -ArgumentList $arguments
        $output = @($execution.Output)
        $exitCode = $execution.ExitCode
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
$resolvedManualIso = [IO.Path]::GetFullPath($paths.files.manual_iso)
$configurationName = if (
    $ManualOnly -or $null -ne $e2eBuild -or $null -ne $workerBuild
) {
    'test.json'
}
else {
    'development.json'
}
$configuration = [IO.Path]::GetRelativePath(
    $paths.repository,
    (Join-Path $paths.builder "configurations\$configurationName")
)
if ($DryRun) {
    $dryRunArguments = @(
        '--source', $inputIso
        '--configuration', $configuration
        '--compose-only'
    )
    Push-Location $paths.repository
    try {
        $dryRunExecution = Invoke-Na2BuilderModule `
            -Module 'na228_builder.scripts.build_configuration' `
            -ArgumentList $dryRunArguments
    }
    finally {
        Pop-Location
    }
    if ($dryRunExecution.ExitCode -ne 0) {
        Throw-Na2BuilderFailure `
            -Execution $dryRunExecution `
            -FallbackMessage "NA2 development composition failed (exit $($dryRunExecution.ExitCode))."
    }
    $dryRunExecution.Output | ForEach-Object { Write-Host $_ }
    return
}
$logDirectory = Join-Path $paths.logs 'na228'
$buildLogRoot = Join-Path $logDirectory 'builds'
$latestReceiptPath = Join-Path $logDirectory 'preflight\latest.json'
$stagedIso = "$resolvedLatestIso.building"
if ($ManualOnly -or $null -ne $e2eBuild -or $null -ne $workerBuild) {
    $isolatedBuildId = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + "_pid$PID"
    $isolatedKind = if ($null -ne $workerBuild) {
        'worker'
    }
    elseif ($null -ne $e2eBuild) {
        'e2e-test'
    }
    else {
        'manual'
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
        $resolvedManualIso
    }
    $isolatedLogRoot = if ($null -ne $workerBuild) {
        Join-Path $workerBuild.Logs 'builds'
    }
    elseif ($null -ne $e2eBuild) {
        $buildLogRoot
    }
    else {
        Join-Path $logDirectory 'manual'
    }
    $resultFilename = switch ($isolatedKind) {
        'worker' { 'build_result.tsv' }
        'e2e-test' { 'build_result.tsv' }
        default { 'manual_result.tsv' }
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
        Join-Path $logDirectory 'preflight\manual.json'
    }
    $isolatedConfigurationLog = Join-Path $isolatedLogRoot $isolatedBuildId
    $isolatedConfigurationLogDirectory = [IO.Path]::GetRelativePath(
        $paths.repository,
        $isolatedConfigurationLog
    )
    $isolatedBuildingIso = "$isolatedOutputIso.building"
    $payloadShift = if ($null -ne $e2eBuild) {
        [int]$e2eBuild.payload_shift_bytes
    }
    else {
        0
    }
    $isolatedArguments = @(
        '--source', $inputIso
        '--output', $isolatedOutputIso
        '--configuration', $configuration
        '--configuration-log-directory', $isolatedConfigurationLogDirectory
        '--payload-shift', [string]$payloadShift
    )
    if ($WorkerEphemeral) {
        $isolatedArguments += '--digest-only'
    }
    if ($Force) {
        $isolatedArguments += '--best-effort-metadata'
    }

    $isolatedLabel = switch ($isolatedKind) {
        'worker' { 'Worker-output mode' }
        'e2e-test' { "E2E Test $E2eVariant mode" }
        default { 'Manual mode' }
    }
    try {
        $isolatedPreflight = Invoke-Na2BuildPreflight `
            -Command check `
            -Na2Iso $inputIso `
            -Nun5Iso $nun5Iso `
            -OutputIso $isolatedOutputIso `
            -Configuration $configuration `
            -Receipt $isolatedReceiptPath `
            -PayloadShift $payloadShift `
            -Repository $paths.repository
    }
    catch {
        $isolatedPreflight = [pscustomobject]@{
            status = 'miss'
            reason = 'preflight-command-error'
            detail = $_.Exception.Message
        }
    }
    if ($WorkerEphemeral -and $isolatedPreflight.status -eq 'hit') {
        $isolatedPreflight = [pscustomobject]@{
            status = 'miss'
            reason = 'ephemeral-build-required'
            detail = 'ephemeral mode always computes a fresh verified virtual ISO'
            fingerprint = $isolatedPreflight.fingerprint
        }
    }
    if ($isolatedPreflight.status -eq 'hit') {
        try {
            $retainedRecord = Find-Na2IsolatedBuildRecord `
                -LogRoot $isolatedLogRoot `
                -ResultFilename $resultFilename `
                -OutputIso $isolatedOutputIso `
                -Variant $(if ($isolatedKind -eq 'e2e-test') { $E2eVariant } else { $null }) `
                -Paths $paths
        }
        catch {
            if (-not $Force) {
                throw
            }
            Write-Warning "Force mode could not validate the retained build record: $($_.Exception.Message)"
            $retainedRecord = $null
        }
        if ($null -ne $retainedRecord) {
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
                ManualState = if ($isolatedKind -eq 'manual') { 'unchanged' } else { $null }
                E2eTestState = if ($isolatedKind -eq 'e2e-test') { 'unchanged' } else { $null }
                OutputState = 'unchanged'
                OutputIso = $isolatedOutputIso
                ManualIso = if ($isolatedKind -eq 'manual') { $isolatedOutputIso } else { $null }
                E2eTestIso = if ($isolatedKind -eq 'e2e-test') { $isolatedOutputIso } else { $null }
                E2eVariant = if ($isolatedKind -eq 'e2e-test') { $E2eVariant } else { $null }
                LatestIso = $resolvedLatestIso
                PreviousIso = $resolvedPreviousIso
                Rotated = $false
                BuildId = $retainedRecord.Name
                ConfigurationLogDirectory = $retainedRecordPath
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
    $ephemeralOutputOwned = $false
    $isolatedConfigurationLogAvailable = $false
    try {
        if ($null -ne $activeBuildMarker) {
            [void](New-Item -ItemType Directory -Path $buildLogRoot -Force)
            Set-Na2Utf8FileAtomic `
                -Path $activeBuildMarker `
                -Content ("pid`tstarted_utc`n$PID`t$((Get-Date).ToUniversalTime().ToString('O'))`n")
        }
        Push-Location $paths.repository
        try {
            $isolatedExecution = Invoke-Na2BuilderModule `
                -Module 'na228_builder.scripts.build_configuration' `
                -ArgumentList $isolatedArguments
            $isolatedOutput = @($isolatedExecution.Output)
            $isolatedExitCode = $isolatedExecution.ExitCode
        }
        finally {
            Pop-Location
        }
        if ($isolatedExitCode -ne 0) {
            Throw-Na2BuilderFailure `
                -Execution $isolatedExecution `
                -FallbackMessage "NA2 $isolatedKind build failed (exit $isolatedExitCode)."
        }
        $isolatedOutput | ForEach-Object { Write-Host $_ }
        $isolatedConfigurationLogAvailable = Test-Path `
            -LiteralPath $isolatedConfigurationLog `
            -PathType Container
        if (-not $isolatedConfigurationLogAvailable) {
            if (-not $Force) {
                throw "$isolatedLabel completed without creating its structured build record."
            }
            Write-Warning "$isolatedLabel is continuing without a structured build record."
        }
        if (-not $WorkerEphemeral -and
            -not (Test-Path -LiteralPath $isolatedBuildingIso -PathType Leaf)) {
            throw "Verified $isolatedKind ISO does not exist: $isolatedBuildingIso"
        }

        if ($WorkerEphemeral) {
            $digestMatches = @(
                $isolatedOutput |
                    ForEach-Object {
                        [regex]::Match(
                            $_,
                            '^Verified virtual ISO: (?<size>[0-9]+) bytes; SHA-256 (?<hash>[0-9A-F]{64})$'
                        )
                    } |
                    Where-Object Success
            )
            if ($digestMatches.Count -ne 1) {
                throw 'Ephemeral worker build did not report exactly one verified virtual ISO digest.'
            }
            $isolatedOutputSizeBytes = [long]$digestMatches[0].Groups['size'].Value
            $isolatedOutputSha256 = $digestMatches[0].Groups['hash'].Value
            if (
                (Test-Path -LiteralPath $isolatedOutputIso) -or
                (Test-Path -LiteralPath $isolatedBuildingIso)
            ) {
                $ephemeralOutputOwned = Test-Path -LiteralPath $isolatedOutputIso -PathType Leaf
                throw 'Ephemeral worker build wrote an ISO instead of using virtual assembly.'
            }
        }

        $isolatedChanged = if ($WorkerEphemeral) {
            $true
        }
        else {
            -not (
                (Test-Path -LiteralPath $isolatedOutputIso -PathType Leaf) -and
                (Test-FileContentEqual `
                    -LeftPath $isolatedBuildingIso `
                    -RightPath $isolatedOutputIso)
            )
        }
        $isolatedState = if ($WorkerEphemeral) {
            'ephemeral'
        }
        elseif ($isolatedChanged) {
            'updated'
        }
        else {
            'unchanged'
        }

        if (-not $WorkerEphemeral) {
            if ($isolatedChanged) {
                [IO.File]::Move($isolatedBuildingIso, $isolatedOutputIso, $true)
            }
            else {
                Remove-Item -LiteralPath $isolatedBuildingIso -Force
            }
        }

        if (-not $WorkerEphemeral) {
            $isolatedOutputItem = Get-Item -LiteralPath $isolatedOutputIso
            $isolatedOutputSizeBytes = [long]$isolatedOutputItem.Length
            $isolatedOutputSha256 = (
                Get-FileHash -LiteralPath $isolatedOutputItem.FullName -Algorithm SHA256
            ).Hash
        }

        if ($isolatedKind -ne 'e2e-test' -and $isolatedConfigurationLogAvailable) {
            try {
                $configurationPortable = ConvertTo-Na2PortableText `
                    -Text $configuration `
                    -Paths $paths
                $outputPortable = ConvertTo-Na2PortableText `
                    -Text $isolatedOutputIso `
                    -Paths $paths
                $recordPortable = ConvertTo-Na2PortableText `
                    -Text $isolatedConfigurationLog `
                    -Paths $paths
                $outputRetained = if ($WorkerEphemeral) { 'no' } else { 'yes' }
                $resultContent = @(
                    "timestamp_utc`tresult`toutput_state`trotation`tpcsx2_closed`tconfiguration`toutput_iso`toutput_size_bytes`toutput_sha256`toutput_retained`tbuild_record"
                    (
                        (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') + "`t" +
                        "$isolatedKind`t$isolatedState`tno`tno`t$configurationPortable`t$outputPortable`t" +
                        "$isolatedOutputSizeBytes`t$isolatedOutputSha256`t$outputRetained`t$recordPortable"
                    )
                ) -join "`n"
                $resultContent += "`n"
                if (Test-Na2WindowsAbsolutePath -Text $resultContent) {
                    throw "Refusing to write the $isolatedKind result with an absolute path."
                }
                Set-Na2Utf8FileAtomic `
                    -Path (Join-Path $isolatedConfigurationLog $resultFilename) `
                    -Content $resultContent
            }
            catch {
                if (-not $Force) {
                    throw
                }
                Write-Warning "Force mode could not retain the $isolatedKind result: $($_.Exception.Message)"
            }
        }

        if ($isolatedKind -eq 'e2e-test') {
            $e2eRecord = Complete-Na2E2eBuildRecord `
                -LogDirectory $logDirectory `
                -BuildId $isolatedBuildId `
                -Variant $E2eVariant `
                -OutputIso $isolatedOutputIso `
                -Configuration $configuration `
                -PayloadShift $payloadShift `
                -Paths $paths
        }
        elseif ($isolatedKind -eq 'manual') {
            if ($isolatedConfigurationLogAvailable) {
                try {
                    Get-ChildItem -LiteralPath $isolatedLogRoot -Directory |
                        Where-Object FullName -CNE $isolatedConfigurationLog |
                        Remove-Item -Recurse -Force
                }
                catch {
                    if (-not $Force) {
                        throw
                    }
                    Write-Warning "Force mode could not prune Manual records: $($_.Exception.Message)"
                }
            }
        }
        else {
            Get-ChildItem -LiteralPath $isolatedLogRoot -Directory |
                Where-Object {
                    $_.FullName -CNE $isolatedConfigurationLog -and
                    (Test-Path -LiteralPath (Join-Path $_.FullName 'build_result.tsv') -PathType Leaf)
                } |
                Sort-Object LastWriteTimeUtc -Descending |
                Select-Object -Skip 19 |
                Remove-Item -Recurse -Force
        }
        if ($WorkerEphemeral) {
            Write-Host '[na228] Preflight receipt: skipped for virtual ephemeral output.' -ForegroundColor Cyan
        }
        elseif (-not [string]::IsNullOrWhiteSpace($isolatedPreflightFingerprint)) {
            try {
                $isolatedReceiptResult = Invoke-Na2BuildPreflight `
                    -Command record `
                    -Na2Iso $inputIso `
                    -Nun5Iso $nun5Iso `
                    -OutputIso $isolatedOutputIso `
                    -Configuration $configuration `
                    -Receipt $isolatedReceiptPath `
                    -PayloadShift $payloadShift `
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
        $isolatedRecord = if ($isolatedConfigurationLogAvailable) {
            ConvertTo-Na2ProjectPath `
                -Path $isolatedConfigurationLog `
                -Paths $paths
        }
        else {
            $null
        }
        if ($WorkerEphemeral) {
            Write-Host (
                "[na228] Ephemeral worker ISO: $isolatedOutputSizeBytes bytes; " +
                "SHA-256 $isolatedOutputSha256; not written to disk."
            ) -ForegroundColor Cyan
            Write-Host (
                '[na228] ISO result: worker (ephemeral); virtual output only; ' +
                'Latest/Previous unchanged; rotation: no; PCSX2 left running.'
            ) -ForegroundColor Cyan
        }
        else {
            Write-Host (
                "[na228] ISO result: $isolatedKind ($isolatedState); Latest/Previous unchanged; " +
                'rotation: no; PCSX2 left running.'
            ) -ForegroundColor Cyan
        }
        if ($isolatedConfigurationLogAvailable) {
            Write-Host (
                "[na228] $isolatedLabel record: retained " +
                $isolatedConfigurationLog
            ) -ForegroundColor Cyan
        }
        else {
            Write-Warning "$isolatedLabel record: unavailable; force mode retained the verified ISO."
        }
        return [pscustomobject]@{
            Status = $isolatedKind
            ManualState = if ($isolatedKind -eq 'manual') { $isolatedState } else { $null }
            E2eTestState = if ($isolatedKind -eq 'e2e-test') { $isolatedState } else { $null }
            OutputState = $isolatedState
            OutputIso = $isolatedOutputIso
            OutputSizeBytes = $isolatedOutputSizeBytes
            OutputSha256 = $isolatedOutputSha256
            OutputRetained = -not $WorkerEphemeral
            ManualIso = if ($isolatedKind -eq 'manual') { $isolatedOutputIso } else { $null }
            E2eTestIso = if ($isolatedKind -eq 'e2e-test') { $isolatedOutputIso } else { $null }
            E2eVariant = if ($isolatedKind -eq 'e2e-test') { $E2eVariant } else { $null }
            LatestIso = $resolvedLatestIso
            PreviousIso = $resolvedPreviousIso
            Rotated = $false
            BuildId = if ($isolatedConfigurationLogAvailable) { $isolatedBuildId } else { $null }
            ConfigurationLogDirectory = $isolatedRecord
            PreflightCacheHit = $false
            ChangedRoles = [string[]]@(
                if ($isolatedKind -eq 'manual' -and $isolatedChanged) {
                    'manual'
                }
                elseif ($isolatedKind -eq 'e2e-test' -and $isolatedChanged) {
                    "e2e_test_$E2eVariant"
                }
            )
        }
    }
    finally {
        if ($ephemeralOutputOwned -and (Test-Path -LiteralPath $isolatedOutputIso -PathType Leaf)) {
            [IO.File]::Delete($isolatedOutputIso)
        }
        if (Test-Path -LiteralPath $isolatedBuildingIso) {
            Remove-Item -LiteralPath $isolatedBuildingIso -Force
        }
        if ($null -ne $activeBuildMarker -and (Test-Path -LiteralPath $activeBuildMarker -PathType Leaf)) {
            Remove-Item -LiteralPath $activeBuildMarker -Force
        }
        if (-not $isolatedCompleted -and
            (Test-Path -LiteralPath $isolatedConfigurationLog -PathType Container)) {
            Remove-Item -LiteralPath $isolatedConfigurationLog -Recurse -Force
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

try {
    New-Item -ItemType Directory -Path $buildLogRoot -Force | Out-Null
}
catch {
    if (-not $Force) {
        throw
    }
    Write-Warning "Force mode could not prepare build logs: $($_.Exception.Message)"
}

try {
    $preflight = Invoke-Na2BuildPreflight `
        -Command check `
        -Na2Iso $inputIso `
        -Nun5Iso $nun5Iso `
        -OutputIso $resolvedLatestIso `
        -Configuration $configuration `
        -Receipt $latestReceiptPath `
        -PayloadShift 0 `
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
            ConfigurationLogDirectory = $buildRecord
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
$configurationLog = Join-Path $buildLogRoot $buildId
$configurationLogDirectory = [IO.Path]::GetRelativePath(
    $paths.repository,
    $configurationLog
)
$arguments = @(
    '--source', $inputIso
    '--output', $resolvedLatestIso
    '--configuration', $configuration
    '--configuration-log-directory', $configurationLogDirectory
)
if ($Force) {
    $arguments += '--best-effort-metadata'
}

$promotionCompleted = $false
$preserveStagedIso = $false
try {
    Push-Location $paths.repository
    try {
        $buildExecution = Invoke-Na2BuilderModule `
            -Module 'na228_builder.scripts.build_configuration' `
            -ArgumentList $arguments
        $buildOutput = @($buildExecution.Output)
        $buildExitCode = $buildExecution.ExitCode
    }
    finally {
        Pop-Location
    }
    if ($buildExitCode -ne 0) {
        Throw-Na2BuilderFailure `
            -Execution $buildExecution `
            -FallbackMessage "NA2 configuration build failed (exit $buildExitCode)."
    }
    $buildOutput | ForEach-Object { Write-Host $_ }
    if (-not (Test-Path -LiteralPath $configurationLog -PathType Container)) {
        if (-not $Force) {
            throw 'Configuration build completed without creating its structured build record.'
        }
        Write-Warning 'Force mode is continuing without a structured configuration build record.'
    }

    try {
        $promotion = Promote-VerifiedIso `
            -LatestIso $resolvedLatestIso `
            -PreviousIso $resolvedPreviousIso
        $promotionCompleted = $true
    }
    catch {
        if (-not $Force -or -not (Test-Path -LiteralPath $stagedIso -PathType Leaf)) {
            throw
        }
        $preserveStagedIso = $true
        Write-Warning (
            "Force mode could not promote Latest: $($_.Exception.Message) " +
            "The verified staged ISO will be launched directly: $stagedIso"
        )
        $promotion = [pscustomobject]@{
            Status = 'forced-staged'
            LatestIso = $resolvedLatestIso
            PreviousIso = $resolvedPreviousIso
            Rotated = $false
            ChangedRoles = [string[]]@()
            LaunchIso = $stagedIso
        }
    }

    $buildRecord = $null
    if (-not $preserveStagedIso) {
        try {
            $buildRecord = Complete-Na2BuildRecord `
                -LogDirectory $logDirectory `
                -BuildId $buildId `
                -Result $promotion.Status `
                -Rotated $promotion.Rotated `
                -LatestIso $promotion.LatestIso `
                -PreviousIso $promotion.PreviousIso `
                -Configuration $configuration `
                -Paths $paths
            $buildRecordPath = Join-Path $buildLogRoot $buildRecord.BuildId
            Write-Host "[na228] Build record: retained $buildRecordPath" -ForegroundColor Cyan
        }
        catch {
            if (-not $Force) {
                throw
            }
            Write-Warning "Force mode could not retain the build record: $($_.Exception.Message)"
        }
    }
    $promotion | Add-Member -NotePropertyName BuildId -NotePropertyValue $(
        if ($null -ne $buildRecord) { $buildRecord.BuildId } else { $null }
    )
    $promotion | Add-Member -NotePropertyName ConfigurationLogDirectory -NotePropertyValue $(
        if ($null -ne $buildRecord) { $buildRecord.BuildRecord } else { $null }
    )
    $promotion | Add-Member -NotePropertyName PreflightCacheHit -NotePropertyValue $false
    if (-not $preserveStagedIso -and -not [string]::IsNullOrWhiteSpace($preflightFingerprint)) {
        try {
            $receiptResult = Invoke-Na2BuildPreflight `
                -Command record `
                -Na2Iso $inputIso `
                -Nun5Iso $nun5Iso `
                -OutputIso $resolvedLatestIso `
                -Configuration $configuration `
                -Receipt $latestReceiptPath `
                -PayloadShift 0 `
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
    if (-not $preserveStagedIso -and (Test-Path -LiteralPath $stagedIso)) {
        Remove-Item -Force -LiteralPath $stagedIso
    }
    if (-not $promotionCompleted -and (Test-Path -LiteralPath $configurationLog -PathType Container)) {
        Remove-Item -LiteralPath $configurationLog -Recurse -Force
    }
}
