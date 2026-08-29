[CmdletBinding()]
param(
    [switch]$ManualOnly,
    [switch]$E2e,
    [string]$CacheConfiguration,
    [string]$CacheLogDirectory,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
. (Join-Path $PSScriptRoot '..\lib\build_log.ps1')
. (Join-Path $PSScriptRoot 'build_registry.ps1')
. (Join-Path $PSScriptRoot 'build_targets.ps1')
$paths = Get-Na2Paths
$pythonRunner = Join-Path ([string]$paths.scripts) 'lib\run_python.ps1'
$registryPath = Join-Path $paths.logs 'na228\preflight\registry.json'
$isoCacheRoot = Join-Path $paths.cache 'isos'
$incomingRoot = Join-Path $isoCacheRoot '.incoming'
$cacheBuild = $PSBoundParameters.ContainsKey('CacheConfiguration')

if (@(
    $ManualOnly.IsPresent
    $E2e.IsPresent
    $cacheBuild
).Where({ $_ }).Count -gt 1) {
    throw '-ManualOnly, -E2e, and -CacheConfiguration are mutually exclusive.'
}
if ($Force -and ($E2e -or $cacheBuild)) {
    throw '-Force is valid only for ordinary Latest or Manual builds.'
}
if ($cacheBuild -and $CacheConfiguration -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]*$') {
    throw "Invalid cache configuration ID: $CacheConfiguration"
}
if (-not $cacheBuild -and -not [string]::IsNullOrWhiteSpace($CacheLogDirectory)) {
    throw '-CacheLogDirectory is valid only with -CacheConfiguration.'
}

function Invoke-Na2BuilderModule {
    param(
        [Parameter(Mandatory)][string]$Module,
        [Parameter(Mandatory)][string[]]$ArgumentList
    )
    $output = @(
        & $pythonRunner -PackageSet builder -Module $Module `
            -ArgumentList $ArgumentList -NoBytecode 2>&1
    )
    [pscustomobject]@{
        Output = [string[]]@($output | ForEach-Object { [string]$_ })
        ExitCode = $LASTEXITCODE
    }
}

function Throw-Na2BuilderFailure {
    param(
        [Parameter(Mandatory)][psobject]$Execution,
        [Parameter(Mandatory)][string]$FallbackMessage
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

function Write-Na2IsolatedResult {
    param(
        [Parameter(Mandatory)][string]$RecordDirectory,
        [Parameter(Mandatory)][string]$Kind,
        [Parameter(Mandatory)][string]$State,
        [Parameter(Mandatory)][string]$Configuration,
        [Parameter(Mandatory)][string]$OutputIso,
        [Parameter(Mandatory)][long]$Size,
        [Parameter(Mandatory)][string]$Sha256
    )
    $configurationPortable = ConvertTo-Na2PortableText -Text $Configuration -Paths $paths
    $outputPortable = ConvertTo-Na2PortableText -Text $OutputIso -Paths $paths
    $recordPortable = ConvertTo-Na2PortableText -Text $RecordDirectory -Paths $paths
    $content = @(
        'timestamp_utc`tresult`toutput_state`tconfiguration`toutput_iso`toutput_size_bytes`toutput_sha256`tbuild_record'.Replace('`t', "`t")
        (
            (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') + "`t" +
            "$Kind`t$State`t$configurationPortable`t$outputPortable`t" +
            "$Size`t$Sha256`t$recordPortable"
        )
    ) -join "`n"
    Set-Na2Utf8FileAtomic -Path (Join-Path $RecordDirectory 'build_result.tsv') `
        -Content ($content + "`n")
}

$inputIso = $paths.files.na2_iso
$nun5Iso = $paths.files.nun5_iso
$buildTargets = Get-Na2BuildTargetRegistry -Paths $paths
$latestTarget = Find-Na2BuildTarget -Targets $buildTargets -Name 'latest'
$manualTarget = Find-Na2BuildTarget -Targets $buildTargets -Name 'manual'
if ($null -eq $latestTarget) {
    throw "Unknown build target: latest"
}
if ($null -eq $manualTarget) {
    throw "Unknown build target: manual"
}
if ([string]::IsNullOrWhiteSpace([string]$latestTarget.RotateTo)) {
    throw "Build target 'latest' requires rotate_to."
}
$previousTarget = Find-Na2BuildTarget `
    -Targets $buildTargets `
    -Name $latestTarget.RotateTo
$latestIso = [IO.Path]::GetFullPath([string]$latestTarget.Entry.IsoPath)
$previousIso = [IO.Path]::GetFullPath([string]$previousTarget.Entry.IsoPath)
$manualIso = [IO.Path]::GetFullPath([string]$manualTarget.Entry.IsoPath)
$buildTarget = if ($cacheBuild) {
    $null
}
elseif ($E2e) {
    Find-Na2BuildTarget `
        -Targets $buildTargets `
        -Name 'e2e_test'
}
elseif ($ManualOnly) {
    $manualTarget
}
else {
    $latestTarget
}
if (-not $cacheBuild -and $null -eq $buildTarget) {
    throw 'Unknown E2E build target: e2e_test'
}
if (-not $cacheBuild -and
    [string]::IsNullOrWhiteSpace([string]$buildTarget.Configuration)) {
    throw "Build target '$($buildTarget.Name)' is retained and cannot be built."
}
$configurationId = if ($cacheBuild) {
    $CacheConfiguration
}
else {
    [string]$buildTarget.Configuration
}
$configuration = Join-Path $paths.builder "configurations\$configurationId.json"
if (-not (Test-Path -LiteralPath $configuration -PathType Leaf)) {
    throw "Configuration does not exist: $configurationId"
}
$configurationRelative = [IO.Path]::GetRelativePath($paths.repository, $configuration)
$sharedLogDirectory = Join-Path $paths.logs 'na228'

if ($cacheBuild) {
    $kind = 'cache'
    $outputIso = $null
    $cacheRecordBase = if ([string]::IsNullOrWhiteSpace($CacheLogDirectory)) {
        Join-Path $sharedLogDirectory 'cache-builds'
    }
    else {
        [IO.Path]::GetFullPath($CacheLogDirectory)
    }
    $recordRoot = Join-Path $cacheRecordBase 'builds'
    $recordAliasRoot = (ConvertTo-Na2PortableText -Text $recordRoot -Paths $paths).Replace('\', '/')
}
elseif ($E2e) {
    $kind = 'e2e-test'
    $role = [string]$buildTarget.Name
    $outputIso = [IO.Path]::GetFullPath([string]$buildTarget.Entry.IsoPath)
    $recordRoot = Join-Path $sharedLogDirectory 'builds'
    $recordAliasRoot = '@logs/na228/builds'
}
elseif ($ManualOnly) {
    $kind = 'manual'
    $role = 'manual'
    $outputIso = $manualIso
    $recordRoot = Join-Path $sharedLogDirectory 'manual'
    $recordAliasRoot = '@logs/na228/manual'
}
else {
    $kind = 'latest'
    $role = 'latest'
    $outputIso = $latestIso
    $recordRoot = Join-Path $sharedLogDirectory 'builds'
    $recordAliasRoot = '@logs/na228/builds'
}

$buildId = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + "_pid$PID"
$configurationLog = Join-Path $recordRoot $buildId
$configurationLogRelative = [IO.Path]::GetRelativePath(
    $paths.repository,
    $configurationLog
)

$lookupArguments = @{
    Command = 'lookup'
    Registry = $registryPath
    CacheRoot = $isoCacheRoot
    Repository = $paths.repository
    PythonRunner = $pythonRunner
    Na2Iso = $inputIso
    Nun5Iso = $nun5Iso
    Configuration = $configurationRelative
}
try {
    $verification = Invoke-Na2BuildRegistry @lookupArguments
}
catch {
    if (-not $Force) { throw }
    Write-Warning "Build registry lookup failed: $($_.Exception.Message)"
    $verification = [pscustomobject]@{
        status = 'miss'
        reason = 'registry-command-error'
        detail = $_.Exception.Message
        fingerprint = $null
    }
}
$cacheHit = $verification.status -eq 'hit'
$registered = $cacheHit
if ($cacheHit -and [string]::IsNullOrWhiteSpace([string]$verification.provenance)) {
    $cacheHit = $false
    $registered = $false
    $verification = [pscustomobject]@{
        status = 'miss'
        reason = 'provenance-missing'
        fingerprint = $verification.fingerprint
    }
}

if ($cacheHit) {
    Write-Host (
        "[na228] Verification registry: hit; fingerprint $($verification.fingerprint); " +
        "SHA-256 $($verification.output_sha256)."
    ) -ForegroundColor Cyan
    try {
        Copy-Na2RegistryProvenance -Source $verification.provenance -Destination $configurationLog
    }
    catch {
        if (-not $Force) { throw }
        Write-Warning "Verified-build provenance could not be copied: $($_.Exception.Message)"
        [void](New-Item -ItemType Directory -Path $configurationLog -Force)
    }
}
else {
    $detail = if ($verification.PSObject.Properties['detail']) {
        ": $($verification.detail)"
    }
    else { '' }
    Write-Host (
        "[na228] Verification registry: miss ($($verification.reason)$detail); " +
        'running the full verified build.'
    ) -ForegroundColor Yellow
    [void](New-Item -ItemType Directory -Path $incomingRoot -Force)
    Remove-Na2StaleIncomingImages -IncomingRoot $incomingRoot
    $incomingIso = Join-Path $incomingRoot "$buildId.iso"
    $incomingLock = Enter-Na2IncomingImage -Image $incomingIso
    try {
        $builderArguments = @(
            '--source', $inputIso
            '--output', $incomingIso
            '--configuration', $configurationRelative
            '--configuration-log-directory', $configurationLogRelative
        )
        if ($Force) { $builderArguments += '--best-effort-metadata' }
        Push-Location $paths.repository
        try {
            $execution = Invoke-Na2BuilderModule `
                -Module 'na228_builder.scripts.build_configuration' `
                -ArgumentList $builderArguments
        }
        finally { Pop-Location }
        if ($execution.ExitCode -ne 0) {
            Throw-Na2BuilderFailure -Execution $execution `
                -FallbackMessage "NA2 $kind build failed (exit $($execution.ExitCode))."
        }
        $execution.Output | ForEach-Object { Write-Host $_ }
        if (-not (Test-Path -LiteralPath $configurationLog -PathType Container)) {
            if (-not $Force) {
                throw 'Verified build completed without its structured provenance.'
            }
            Write-Warning 'Verified build completed without its structured provenance.'
            [void](New-Item -ItemType Directory -Path $configurationLog -Force)
        }
        $recordArguments = @{
            Command = 'record'
            Registry = $registryPath
            CacheRoot = $isoCacheRoot
            Repository = $paths.repository
            PythonRunner = $pythonRunner
            Na2Iso = $inputIso
            Nun5Iso = $nun5Iso
            Configuration = $configurationRelative
            ExpectedFingerprint = $verification.fingerprint
            Provenance = $configurationLog
        }
        if (-not (Test-Path -LiteralPath $incomingIso -PathType Leaf)) {
            throw "Verified ISO candidate does not exist: $incomingIso"
        }
        $recordArguments.Image = $incomingIso
        $recordFailure = $null
        $recordRejected = $false
        if (-not [string]::IsNullOrWhiteSpace([string]$verification.fingerprint)) {
            try {
                $recordedVerification = Invoke-Na2BuildRegistry @recordArguments
                if ($recordedVerification.status -ne 'recorded') {
                    $recordRejected = $true
                    throw "Verified build was not registered: $($recordedVerification.reason)"
                }
                $verification = $recordedVerification
                $registered = $true
            }
            catch {
                if ($recordRejected) { throw }
                $recordFailure = $_
            }
        }
        else {
            $recordFailure = [System.Management.Automation.ErrorRecord]::new(
                [InvalidOperationException]::new('No registry fingerprint was available.'),
                'Na2RegistryFingerprintUnavailable',
                [System.Management.Automation.ErrorCategory]::InvalidData,
                $null
            )
        }
        if ($null -ne $recordFailure) {
            if (-not $Force) {
                throw $recordFailure
            }
            Write-Warning "Verified-build registry update failed: $($recordFailure.Exception.Message)"
            $cached = Move-Na2VerifiedImageToCache -Candidate $incomingIso -CacheRoot $isoCacheRoot
            $verification = [pscustomobject]@{
                status = 'verified-unregistered'
                fingerprint = $null
                output_size_bytes = $cached.Size
                output_sha256 = $cached.Sha256
                image = $cached.Image
            }
        }
    }
    finally {
        if ($null -ne $incomingLock) {
            Exit-Na2IncomingImage -Image $incomingIso -Lock $incomingLock
        }
    }
}

$size = [long]$verification.output_size_bytes
$sha256 = [string]$verification.output_sha256
$fingerprint = [string]$verification.fingerprint

$candidate = [string]$verification.image
if ([string]::IsNullOrWhiteSpace($candidate) -or
    -not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
    throw 'Verification registry returned no reusable physical ISO.'
}
$promotion = if ($cacheBuild) {
    $outputIso = $candidate
    [pscustomobject]@{
        Status = if ($cacheHit) { 'reused' } else { 'built' }
        Rotated = $false
    }
}
else {
    $publishArguments = @{
        Candidate = $candidate
        Destination = $outputIso
        Size = $size
        Sha256 = $sha256
        CacheRoot = $isoCacheRoot
    }
    if ($kind -eq 'latest') {
        $publishArguments.Previous = $previousIso
        $publishArguments.Rotate = $true
    }
    Publish-Na2VerifiedImage @publishArguments
}
if ($promotion.Status -eq 'pending') {
    $retryMessage = if ($registered) {
        'Rotation will be retried without rebuilding on the next matching build.'
    }
    else {
        'The cache image remains available, but registry recovery may require another verification.'
    }
    Write-Warning (
        "Verified $kind ISO is retained in shared cache because promotion is blocked: " +
        "$($promotion.Failure) $retryMessage"
    )
}
else {
    if ($registered -and -not $cacheBuild) {
        try {
            $completedLocations = @($outputIso)
            if ($kind -eq 'latest' -and $promotion.Rotated) {
                $completedLocations += $previousIso
            }
            [void](Invoke-Na2BuildRegistry -Command complete -Registry $registryPath `
                -CacheRoot $isoCacheRoot -Repository $paths.repository `
                -PythonRunner $pythonRunner -Fingerprint $fingerprint `
                -Location $completedLocations)
        }
        catch {
            if (-not $Force) { throw }
            Write-Warning "Promoted role could not be recorded: $($_.Exception.Message)"
        }
    }
}

$state = $promotion.Status
$changedRoles = if ($state -eq 'updated') {
    if ($kind -eq 'latest') {
        [string[]]@('latest') + $(if ($promotion.Rotated) { 'previous' } else { @() })
    }
    elseif ($kind -eq 'e2e-test') { [string[]]@($role) }
    else { [string[]]@($kind) }
}
else { [string[]]@() }

$buildRecord = $null
if ($state -ne 'pending') {
    try {
        if ($kind -eq 'latest') {
            $buildRecord = Complete-Na2BuildRecord -LogDirectory $sharedLogDirectory `
                -BuildId $buildId -Result $state -Rotated $promotion.Rotated `
                -LatestIso $latestIso -PreviousIso $previousIso `
                -Configuration $configuration -Paths $paths
        }
        elseif ($kind -eq 'e2e-test') {
            $buildRecord = Complete-Na2E2eBuildRecord -LogDirectory $sharedLogDirectory `
                -BuildId $buildId -OutputIso $outputIso `
                -Configuration $configuration -Paths $paths
        }
        else {
            Write-Na2IsolatedResult -RecordDirectory $configurationLog -Kind $kind `
                -State $state -Configuration $configuration -OutputIso $outputIso `
                -Size $size -Sha256 $sha256
            if ($kind -eq 'manual') {
                Get-ChildItem -LiteralPath $recordRoot -Directory | Where-Object {
                    $_.FullName -cne $configurationLog
                } | Remove-Item -Recurse -Force
            }
            else {
                Get-ChildItem -LiteralPath $recordRoot -Directory | Sort-Object LastWriteTimeUtc -Descending |
                    Select-Object -Skip 20 | Remove-Item -Recurse -Force
            }
            $buildRecord = [pscustomobject]@{
                BuildId = $buildId
                BuildRecord = "$recordAliasRoot/$buildId"
            }
        }
    }
    catch {
        if (-not $Force) { throw }
        Write-Warning "Build record update failed: $($_.Exception.Message)"
    }
}
else {
    Write-Na2IsolatedResult -RecordDirectory $configurationLog -Kind $kind `
        -State pending -Configuration $configuration -OutputIso $candidate `
        -Size $size -Sha256 $sha256
    Remove-Item -LiteralPath $configurationLog -Recurse -Force
    if ($registered) {
        $buildRecord = [pscustomobject]@{
            BuildId = $buildId
            BuildRecord = "@logs/na228/preflight/records/$fingerprint"
        }
    }
}

if ($kind -eq 'latest') {
    if ($state -eq 'updated') {
        Write-Host "[na228] ISO result: updated; verified cached image promoted to $([IO.Path]::GetFileName($latestIso)); rotation: $(if ($promotion.Rotated) { 'yes' } else { 'no' })." -ForegroundColor Cyan
    }
    elseif ($state -eq 'unchanged') {
        Write-Host '[na228] ISO result: unchanged; verified registry identity already matches Latest; rotation: no.' -ForegroundColor Cyan
    }
    else {
        Write-Host '[na228] ISO result: pending promotion; verified cached image retained; rotation: deferred.' -ForegroundColor Yellow
    }
    return [pscustomobject]@{
        Status = $state
        LatestIso = $latestIso
        PreviousIso = $previousIso
        LaunchIso = if ($state -eq 'pending') { $candidate } else { $null }
        Rotated = [bool]$promotion.Rotated
        BuildId = if ($null -ne $buildRecord) { $buildRecord.BuildId } else { $buildId }
        ConfigurationLogDirectory = if ($null -ne $buildRecord) { $buildRecord.BuildRecord } else { "$recordAliasRoot/$buildId" }
        PreflightCacheHit = $cacheHit
        ChangedRoles = $changedRoles
        ConfigurationId = $configurationId
    }
}

Write-Host (
    "[na228] ISO result: $kind ($state); rotation: no; PCSX2 left running."
) -ForegroundColor Cyan
return [pscustomobject]@{
    Status = $kind
    OutputState = $state
    OutputIso = if ($state -eq 'pending') { $candidate } else { $outputIso }
    OutputSizeBytes = $size
    OutputSha256 = $sha256
    ManualState = if ($kind -eq 'manual') { $state } else { $null }
    BuildId = if ($null -ne $buildRecord) { $buildRecord.BuildId } else { $buildId }
    ConfigurationLogDirectory = if ($null -ne $buildRecord) { $buildRecord.BuildRecord } else { "$recordAliasRoot/$buildId" }
    PreflightCacheHit = $cacheHit
    ChangedRoles = $changedRoles
    ConfigurationId = $configurationId
}
