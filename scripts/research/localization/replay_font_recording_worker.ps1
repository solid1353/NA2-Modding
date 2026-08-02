[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkerRoot,

    [Parameter(Mandatory = $true)]
    [string]$IsoPath,

    [Parameter(Mandatory = $true)]
    [string]$InputRecording,

    [Parameter(Mandatory = $true)]
    [string]$CaptureDirectory,

    [Parameter(Mandatory = $true)]
    [string]$BuildRecordDirectory,

    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 9999)]
    [int]$ExpectedCaptureCount,

    [Parameter(Mandatory = $true)]
    [ValidateRange(28011, 65535)]
    [int]$PinePort,

    [string]$Game = 'latest'
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\lib\paths.ps1')
$paths = Get-Na2Paths
. (Join-Path $paths.pcsx2_scripts 'iso_identity.ps1')

function Get-ContainedPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Root,

        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullRoot = [IO.Path]::GetFullPath($Root)
    $prefix = $fullRoot.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $fullPath.StartsWith(
        $prefix,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        throw "$Label must remain under $fullRoot."
    }
    return $fullPath
}

function Copy-ProvenanceInput {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,

        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "Required replay input does not exist: $Source"
    }
    [void](New-Item -ItemType Directory -Path (
        Split-Path -Parent $Destination
    ) -Force)
    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Source).Hash
        $destinationHash = (
            Get-FileHash -Algorithm SHA256 -LiteralPath $Destination
        ).Hash
        if ($sourceHash -cne $destinationHash) {
            throw "Preserved replay input differs: $Destination"
        }
        return
    }
    Copy-Item -LiteralPath $Source -Destination $Destination
}

function Set-IniValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$IniPath,

        [Parameter(Mandatory = $true)]
        [string]$Section,

        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    $lines = [Collections.Generic.List[string]]::new()
    foreach ($line in Get-Content -LiteralPath $IniPath) {
        $lines.Add($line)
    }
    $sectionIndex = -1
    $nextSection = $lines.Count
    for ($index = 0; $index -lt $lines.Count; $index += 1) {
        if ($lines[$index] -ceq "[$Section]") {
            $sectionIndex = $index
            continue
        }
        if ($sectionIndex -ge 0 -and $lines[$index] -match '^\[.+\]$') {
            $nextSection = $index
            break
        }
    }
    if ($sectionIndex -lt 0) {
        throw "PCSX2 INI has no [$Section] section: $IniPath"
    }
    for ($index = $sectionIndex + 1; $index -lt $nextSection; $index += 1) {
        if ($lines[$index] -match "^$([regex]::Escape($Name))\s*=") {
            $lines[$index] = "$Name = $Value"
            [IO.File]::WriteAllLines(
                $IniPath,
                $lines,
                [Text.UTF8Encoding]::new($false)
            )
            return
        }
    }
    $lines.Insert($nextSection, "$Name = $Value")
    [IO.File]::WriteAllLines(
        $IniPath,
        $lines,
        [Text.UTF8Encoding]::new($false)
    )
}

function Copy-ProvenanceTree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,

        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
        throw "Required provenance directory does not exist: $Source"
    }
    [void](New-Item -ItemType Directory -Path $Destination -Force)
    $sourceFiles = @(
        Get-ChildItem -LiteralPath $Source -Recurse -File |
            Sort-Object FullName
    )
    if ($sourceFiles.Count -eq 0) {
        throw "Required provenance directory is empty: $Source"
    }
    foreach ($sourceFile in $sourceFiles) {
        $relative = [IO.Path]::GetRelativePath($Source, $sourceFile.FullName)
        Copy-ProvenanceInput `
            -Source $sourceFile.FullName `
            -Destination (Join-Path $Destination $relative)
    }
    $destinationFiles = @(
        Get-ChildItem -LiteralPath $Destination -Recurse -File
    )
    if ($destinationFiles.Count -ne $sourceFiles.Count) {
        throw "Preserved provenance directory has unexpected files: $Destination"
    }
}

$workerRootFull = Get-ContainedPath `
    -Path $WorkerRoot `
    -Root $paths.work `
    -Label 'Worker root'
$workerPcsx2 = Join-Path $workerRootFull 'pcsx2'
$workerIni = Join-Path $workerPcsx2 'inis\PCSX2.ini'
if (-not (Test-Path -LiteralPath $workerIni -PathType Leaf)) {
    throw (
        'Worker PCSX2 is missing. Recreate it with the Workshop ' +
        'copy_worker.ps1 command first.'
    )
}

$isoFull = Get-ContainedPath `
    -Path $IsoPath `
    -Root (Join-Path $workerRootFull 'inputs\isos') `
    -Label 'Worker ISO'
if (-not (Test-Path -LiteralPath $isoFull -PathType Leaf)) {
    throw "Worker ISO does not exist: $isoFull"
}
$isoItem = Get-Item -LiteralPath $isoFull
if (
    -not [string]::IsNullOrWhiteSpace([string]$isoItem.LinkType) -or
    (($isoItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
) {
    throw "Worker ISO must be a full independent file copy: $isoFull"
}
$isoHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $isoFull).Hash
$isoIdentity = Get-Pcsx2IsoIdentity -Path $isoFull

$buildRecordSource = Get-ContainedPath `
    -Path $BuildRecordDirectory `
    -Root $workerRootFull `
    -Label 'Build record'
if (-not (Test-Path -LiteralPath $buildRecordSource -PathType Container)) {
    throw "Build record does not exist: $buildRecordSource"
}
$payloadSummarySource = Join-Path `
    $buildRecordSource `
    'payload_builder\payload_summary.json'
if (-not (Test-Path -LiteralPath $payloadSummarySource -PathType Leaf)) {
    throw "Build record has no payload summary: $buildRecordSource"
}
$payloadSummary = Get-Content -Raw -LiteralPath $payloadSummarySource |
    ConvertFrom-Json
$payloadHash = [string]$payloadSummary.sha256
if ($payloadHash -cnotmatch '^[0-9A-F]{64}$') {
    throw "Build record has an invalid resident payload hash: $buildRecordSource"
}

$captureFull = Get-ContainedPath `
    -Path $CaptureDirectory `
    -Root $workerRootFull `
    -Label 'Capture directory'
if ((Test-Path -LiteralPath $captureFull) -and @(
    Get-ChildItem -LiteralPath $captureFull -Force -ErrorAction SilentlyContinue
).Count -gt 0) {
    throw "Capture directory is not empty: $captureFull"
}
[void](New-Item -ItemType Directory -Path $captureFull -Force)

$gameAlias = @(
    $paths.games.Aliases.PSObject.Properties |
        Where-Object { $_.Name -ieq $Game }
)[0]
if ($null -eq $gameAlias) {
    throw "Unknown game selector: $Game"
}
$gameName = [string]$gameAlias.Value
$gameProperty = @(
    $paths.games.Entries.PSObject.Properties |
        Where-Object { $_.Name -ieq $gameName }
)[0]
if ($null -eq $gameProperty) {
    throw "Resolved game entry does not exist: $gameName"
}
$gameEntry = $gameProperty.Value

$recordingSource = [IO.Path]::GetFullPath($InputRecording)
$recordingDirectory = Join-Path $workerRootFull 'inputs\recordings'
$recordingName = [IO.Path]::GetFileName($recordingSource)
$recordingCopy = Join-Path $recordingDirectory $recordingName
Copy-ProvenanceInput -Source $recordingSource -Destination $recordingCopy

$runtimeInputRoot = Join-Path `
    $workerRootFull `
    "inputs\runtime\$gameName\$payloadHash"
$runtimeRecordCopy = Join-Path `
    $workerRootFull `
    "inputs\runtime-records\$payloadHash"
if (
    -not $buildRecordSource.Equals(
        $runtimeRecordCopy,
        [StringComparison]::OrdinalIgnoreCase
    )
) {
    Copy-ProvenanceTree `
        -Source $buildRecordSource `
        -Destination $runtimeRecordCopy
}
$residentIdentityPath = Join-Path $runtimeInputRoot 'resident_identity.json'
$verificationHost = (Get-Process -Id $PID).Path
& $verificationHost `
    -NoLogo `
    -NoProfile `
    -File (Join-Path $PSScriptRoot 'verify_font_replay_bundle.ps1') `
    -IsoPath $isoFull `
    -BuildRecordDirectory $runtimeRecordCopy `
    -BootElf ([string]$isoIdentity.BootElf) `
    -Serial ([string]$isoIdentity.Serial) `
    -Crc ([string]$isoIdentity.CRC) `
    -OutputPath $residentIdentityPath `
    -RequiredSymbols (
        'localization.font.v2.global_selected_style;' +
        'localization.font.v2.ninja_objective_row_adapter'
    )
if ($LASTEXITCODE -ne 0) {
    throw "Worker ISO/build-record verification failed (exit $LASTEXITCODE)."
}
if (-not (Test-Path -LiteralPath $residentIdentityPath -PathType Leaf)) {
    throw "Worker ISO verification produced no identity record."
}
$memoryCardName = [IO.Path]::GetFileName([string]$gameEntry.MemoryCardPath)
$memoryCardInput = Join-Path $runtimeInputRoot $memoryCardName
Copy-ProvenanceInput `
    -Source ([string]$gameEntry.MemoryCardPath) `
    -Destination $memoryCardInput
Copy-Item `
    -LiteralPath $memoryCardInput `
    -Destination (Join-Path $workerPcsx2 "memcards\$memoryCardName") `
    -Force

$gameSettingsSource = [string]$gameEntry.Config.gamesettings_template
$gameSettingsName = [IO.Path]::GetFileName($gameSettingsSource)
$gameSettingsInput = Join-Path $runtimeInputRoot $gameSettingsName
Copy-ProvenanceInput `
    -Source $gameSettingsSource `
    -Destination $gameSettingsInput
$gameSettingsText = Get-Content -Raw -LiteralPath $gameSettingsInput
$profileMatch = [regex]::Match(
    $gameSettingsText,
    '(?m)^InputProfileName\s*=\s*(?<name>[^\r\n]+)'
)
if (-not $profileMatch.Success) {
    throw "Game settings provide no input profile: $gameSettingsInput"
}
$inputProfileName = $profileMatch.Groups['name'].Value.Trim()
$inputProfileSource = Join-Path `
    $paths.pcsx2_input_profiles `
    "$inputProfileName.ini"
$inputProfileInput = Join-Path `
    $runtimeInputRoot `
    "$inputProfileName.ini"
Copy-ProvenanceInput `
    -Source $inputProfileSource `
    -Destination $inputProfileInput
Copy-Item `
    -LiteralPath $inputProfileInput `
    -Destination (Join-Path $workerPcsx2 "inputprofiles\$inputProfileName.ini") `
    -Force

$workerGameSettings = Join-Path `
    $workerPcsx2 `
    "gamesettings\$([string]$isoIdentity.GameSettingsName)"
$workerGameSettingsText = @(
    '[EmuCore]'
    "InputProfileName = $inputProfileName"
    ''
    '[MemoryCards]'
    "Slot1_Filename = $memoryCardName"
    ''
) -join "`r`n"
[IO.File]::WriteAllText(
    $workerGameSettings,
    $workerGameSettingsText,
    [Text.UTF8Encoding]::new($false)
)
Set-IniValue `
    -IniPath $workerIni `
    -Section 'Folders' `
    -Name 'InputRecordings' `
    -Value '..\inputs\recordings'
Set-IniValue `
    -IniPath $workerIni `
    -Section 'EmuCore' `
    -Name 'PINESlot' `
    -Value ([string]$PinePort)
Set-IniValue `
    -IniPath $workerIni `
    -Section 'MemoryCards' `
    -Name 'Slot1_Enable' `
    -Value 'true'
Set-IniValue `
    -IniPath $workerIni `
    -Section 'MemoryCards' `
    -Name 'Slot1_Filename' `
    -Value $memoryCardName

$provenance = @(
    $recordingCopy,
    $memoryCardInput,
    $gameSettingsInput,
    $inputProfileInput,
    $isoFull,
    $residentIdentityPath,
    (Join-Path $runtimeRecordCopy 'build_result.tsv'),
    (Join-Path $runtimeRecordCopy 'payload_builder\payload_summary.json'),
    (Join-Path $runtimeRecordCopy 'payload_builder\symbol_map.tsv')
) | ForEach-Object {
    $item = Get-Item -LiteralPath $_
    $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $item.FullName
    [pscustomobject]@{
        artifact = [IO.Path]::GetRelativePath(
            $workerRootFull,
            $item.FullName
        ).Replace('\', '/')
        sha256 = $hash.Hash
        size = $item.Length
        last_write_utc = $item.LastWriteTimeUtc.ToString('o')
        disc_serial = [string]$isoIdentity.Serial
        disc_crc = [string]$isoIdentity.CRC
        iso_sha256 = $isoHash
        resident_payload_sha256 = $payloadHash
        build_record = [IO.Path]::GetRelativePath(
            $workerRootFull,
            $runtimeRecordCopy
        ).Replace('\', '/')
    }
}
$recordingStem = [IO.Path]::GetFileNameWithoutExtension($recordingName)
$provenancePath = Join-Path `
    $runtimeInputRoot `
    "replay_provenance_$recordingStem.tsv"
$provenance | Export-Csv `
    -LiteralPath $provenancePath `
    -Delimiter "`t" `
    -NoTypeInformation

$arguments = @(
    '-unlimited',
    '-input-recording',
    "`"$recordingName`"",
    '-input-recording-capture-directory',
    "`"$captureFull`""
)
$processOutput = @(& ([string]$paths.files.pcsx2_launch_command) `
    -WorkerRoot $workerRootFull `
    -IsoPath $isoFull `
    -Arguments $arguments `
    -Wait `
    -PassThru)
$process = @(
    $processOutput | Where-Object { $_ -is [Diagnostics.Process] }
) | Select-Object -Last 1
if ($null -eq $process) {
    throw 'Worker launcher returned no process completion record.'
}
$process.Refresh()
if (-not $process.HasExited) {
    throw "Worker PCSX2 did not exit after the recording replay."
}
if ($process.ExitCode -ne 0) {
    throw "Worker PCSX2 replay failed (exit $($process.ExitCode))."
}

$states = @(
    Get-ChildItem -LiteralPath $captureFull -Recurse -File -Filter '*.p2s'
)
$screenshots = @(
    Get-ChildItem -LiteralPath $captureFull -Recurse -File -Filter '*.png'
)
if (
    $states.Count -ne $ExpectedCaptureCount -or
    $screenshots.Count -ne $ExpectedCaptureCount
) {
    throw (
        "Recording produced $($states.Count) states and " +
        "$($screenshots.Count) screenshots; expected exactly " +
        "$ExpectedCaptureCount paired captures: $captureFull"
    )
}
for ($captureIndex = 1; $captureIndex -le $ExpectedCaptureCount; $captureIndex += 1) {
    $captureName = $captureIndex.ToString('0000')
    $statePath = Join-Path $captureFull "$captureName.p2s"
    $screenshotPath = Join-Path `
        $captureFull `
        "screenshots\$captureName.png"
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
        throw "Recording is missing savestate ${captureName}: $statePath"
    }
    if (-not (Test-Path -LiteralPath $screenshotPath -PathType Leaf)) {
        throw "Recording is missing screenshot ${captureName}: $screenshotPath"
    }
}
[pscustomobject]@{
    CaptureDirectory = $captureFull
    Savestates = $states.Count
    Screenshots = $screenshots.Count
    Serial = [string]$isoIdentity.Serial
    CRC = [string]$isoIdentity.CRC
    IsoSha256 = $isoHash
    ResidentPayloadSha256 = $payloadHash
    BuildRecord = $runtimeRecordCopy
    Provenance = $provenancePath
}
