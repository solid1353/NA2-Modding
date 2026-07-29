[CmdletBinding()]
param(
    [switch]$BuildOnly,
    [string]$CurrentIso,
    [string]$CheatsDirectory,
    [int]$PinePort,
    [string]$ProductionSource,
    [string]$ProductionEntry
)

$ErrorActionPreference = 'Stop'

$labRoot = $PSScriptRoot
$repository = Split-Path -Parent $labRoot
$projectPathsScript = Join-Path $repository 'scripts\lib\project_paths.ps1'
. $projectPathsScript
$projectPaths = Get-Na2ProjectPaths
$statePath = Join-Path $labRoot 'build\test-install.json'
$payloadConfigPath = Join-Path $repository 'na228_builder\payload_builder\config.tsv'
$identityScript = Join-Path $repository 'scripts\na228\iso_identity.ps1'
$hookRuntimeAddress = 0x001D0578
$hookRuntimeAddresses = [uint32[]]@(
    0x001D0578,
    0x001D057C,
    0x001D0580,
    0x001D0584,
    0x001D0588
)
$expectedHook = [byte[]](
    0x00, 0x00, 0xBF, 0xDF,
    0x10, 0x00, 0xBD, 0x27,
    0x08, 0x00, 0xE0, 0x03,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00
)
$productionMode = [bool]$ProductionSource -or [bool]$ProductionEntry
if ([bool]$ProductionSource -ne [bool]$ProductionEntry) {
    throw 'ProductionSource and ProductionEntry must be supplied together.'
}
$expectedLayout = if ($productionMode) {
    'production_dispatcher_v1'
}
else {
    'dispatcher_v1'
}

if (-not $CurrentIso) {
    $CurrentIso = $projectPaths.files.current_iso
}
if (-not $CheatsDirectory) {
    $CheatsDirectory = $projectPaths.pcsx2_cheats
}
$currentIso = [IO.Path]::GetFullPath($CurrentIso)
$cheatsDirectory = [IO.Path]::GetFullPath($CheatsDirectory)

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Write-PnachInPlace([string]$Source, [string]$Target) {
    $existing = Get-Item -LiteralPath $Target -Force -ErrorAction SilentlyContinue
    if ($existing -and
        ($existing.PSIsContainer -or [string]$existing.LinkType)) {
        throw "PNACH refresh target must be a regular file: $Target"
    }

    $bytes = [IO.File]::ReadAllBytes($Source)
    $mode = if ($existing) {
        [IO.FileMode]::Open
    }
    else {
        [IO.FileMode]::CreateNew
    }
    $sharing = [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete
    $stream = [IO.File]::Open(
        $Target,
        $mode,
        [IO.FileAccess]::Write,
        $sharing
    )
    try {
        $stream.SetLength(0)
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally {
        $stream.Dispose()
    }
}

function Get-InjectionLabPinePort(
    [string]$CheatsDirectory,
    [int]$ExplicitPort
) {
    if ($ExplicitPort) {
        if ($ExplicitPort -lt 1 -or $ExplicitPort -gt 65535) {
            throw "PINE port is outside 1..65535: $ExplicitPort"
        }
        return $ExplicitPort
    }

    $pcsx2Root = Split-Path -Parent $CheatsDirectory
    $iniPath = Join-Path $pcsx2Root 'inis\PCSX2.ini'
    if (-not (Test-Path -LiteralPath $iniPath)) {
        throw "PCSX2.ini was not found beside the cheats directory: $iniPath"
    }
    $ini = Get-Content -Raw -LiteralPath $iniPath
    if ($ini -notmatch '(?m)^\s*EnablePINE\s*=\s*true\s*$') {
        throw "PINE is not enabled in PCSX2.ini: $iniPath"
    }
    if ($ini -notmatch '(?m)^\s*PINESlot\s*=\s*(\d+)\s*$') {
        throw "PCSX2.ini has no valid PINESlot: $iniPath"
    }
    $configuredPort = [int]$Matches[1]
    if ($configuredPort -lt 1 -or $configuredPort -gt 65535) {
        throw "Configured PINE port is outside 1..65535: $configuredPort"
    }
    return $configuredPort
}

function Read-PineBytes([IO.Stream]$Stream, [int]$Length) {
    $result = [byte[]]::new($Length)
    $offset = 0
    while ($offset -lt $Length) {
        $read = $Stream.Read($result, $offset, $Length - $offset)
        if ($read -eq 0) {
            throw 'PCSX2 closed the PINE connection during the reply.'
        }
        $offset += $read
    }
    return $result
}

function Invoke-PineReloadPatches([int]$Port) {
    $client = [Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.ConnectAsync('127.0.0.1', $Port)
        if (-not $connection.Wait([TimeSpan]::FromSeconds(3))) {
            throw "Timed out connecting to PINE port $Port."
        }
        $stream = $client.GetStream()
        $stream.ReadTimeout = 3000
        $stream.WriteTimeout = 3000

        [byte[]]$packet = [BitConverter]::GetBytes([uint32]5) +
            [byte[]]@(0x10)
        $stream.Write($packet, 0, $packet.Length)
        $stream.Flush()

        $sizeBytes = Read-PineBytes -Stream $stream -Length 4
        $replySize = [BitConverter]::ToUInt32($sizeBytes, 0)
        if ($replySize -ne 5) {
            throw "PINE reload returned an invalid reply size: $replySize"
        }
        $reply = Read-PineBytes -Stream $stream -Length 1
        if ($reply[0] -ne 0) {
            throw (
                'PCSX2 rejected PINE reload opcode 0x10. ' +
                'Run the custom reload-enabled PCSX2 build.'
            )
        }
    }
    catch {
        throw "Could not reload PCSX2 patches through PINE: $($_.Exception.Message)"
    }
    finally {
        $client.Dispose()
    }
}

function Get-UInt16LE([byte[]]$Data, [int]$Offset) {
    return [BitConverter]::ToUInt16($Data, $Offset)
}

function Get-UInt32LE([byte[]]$Data, [int]$Offset) {
    return [BitConverter]::ToUInt32($Data, $Offset)
}

function Get-ElfFileOffset(
    [byte[]]$Elf,
    [uint32]$RuntimeAddress,
    [int]$Length
) {
    if ($Elf.Length -lt 0x34 -or
        $Elf[0] -ne 0x7F -or
        $Elf[1] -ne 0x45 -or
        $Elf[2] -ne 0x4C -or
        $Elf[3] -ne 0x46) {
        throw 'Current boot executable is not an ELF file.'
    }

    $programOffset = [int](Get-UInt32LE $Elf 0x1C)
    $entrySize = [int](Get-UInt16LE $Elf 0x2A)
    $entryCount = [int](Get-UInt16LE $Elf 0x2C)
    if ($entrySize -lt 0x20) {
        throw "Invalid ELF program-header size: $entrySize"
    }

    for ($index = 0; $index -lt $entryCount; $index++) {
        $offset = $programOffset + $index * $entrySize
        if ($offset -lt 0 -or $offset + 0x20 -gt $Elf.Length) {
            throw 'ELF program-header table extends outside the file.'
        }
        if ((Get-UInt32LE $Elf $offset) -ne 1) {
            continue
        }
        $fileOffset = [uint32](Get-UInt32LE $Elf ($offset + 4))
        $virtualAddress = [uint32](Get-UInt32LE $Elf ($offset + 8))
        $fileSize = [uint32](Get-UInt32LE $Elf ($offset + 16))
        if ($RuntimeAddress -ge $virtualAddress -and
            [uint64]$RuntimeAddress + $Length -le
                [uint64]$virtualAddress + $fileSize) {
            return [int]($fileOffset + ($RuntimeAddress - $virtualAddress))
        }
    }
    throw ('Runtime address 0x{0:X8} is not file-backed in the Current ELF.' -f
        $RuntimeAddress)
}

function Assert-Bytes(
    [byte[]]$Data,
    [int]$Offset,
    [byte[]]$Expected,
    [string]$Context
) {
    if ($Offset -lt 0 -or $Offset + $Expected.Length -gt $Data.Length) {
        throw "$Context is outside the supplied data."
    }
    for ($index = 0; $index -lt $Expected.Length; $index++) {
        if ($Data[$Offset + $index] -ne $Expected[$index]) {
            $actual = [Convert]::ToHexString(
                $Data[$Offset..($Offset + $Expected.Length - 1)]
            )
            throw (
                "$Context guard mismatch: $actual != " +
                [Convert]::ToHexString($Expected)
            )
        }
    }
}

function Get-BuildId {
    $inputs = @(
        Get-Item -LiteralPath (Join-Path $labRoot 'linker.asm')
        Get-ChildItem -LiteralPath (Join-Path $labRoot 'src') -File |
            Where-Object { $_.Extension -in '.c', '.h' } |
            Sort-Object Name
    )
    $lines = foreach ($inputFile in $inputs) {
        if (-not $inputFile.FullName.StartsWith(
            $labRoot + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase
        )) {
            throw "Injection input is outside the lab: $($inputFile.FullName)"
        }
        $relative = $inputFile.FullName.Substring($labRoot.Length + 1)
        "$relative`t$(Get-Sha256 $inputFile.FullName)"
    }
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $hash = $sha.ComputeHash(
            [Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))
        )
    }
    finally {
        $sha.Dispose()
    }
    $id = [BitConverter]::ToUInt32($hash, 0)
    if ($id -eq 0) {
        $id = 1
    }
    return $id
}

if (-not (Test-Path -LiteralPath $currentIso)) {
    throw "Current ISO was not found: $currentIso"
}
if (-not (Test-Path -LiteralPath $payloadConfigPath)) {
    throw "Payload-builder config was not found: $payloadConfigPath"
}

. $identityScript
$identity = Get-Na2IsoPcsx2Identity -Path $currentIso
if ([string]$identity.Serial -cne 'SLOP-NA228') {
    throw "Injection lab requires Current serial SLOP-NA228, got $($identity.Serial)."
}

$configRows = Import-Csv -LiteralPath $payloadConfigPath -Delimiter "`t"
$config = @{}
foreach ($row in $configRows) {
    $config[[string]$row.key] = [string]$row.value
}
$loadBase = [Convert]::ToUInt32($config.load_base.Substring(2), 16)
$maximumEnd = [Convert]::ToUInt32($config.maximum_end.Substring(2), 16)
$oldBoundary = [Convert]::ToUInt32($config.old_memory_boundary.Substring(2), 16)
$injectionBase = [Convert]::ToUInt32(
    $config.development_injection_base.Substring(2), 16
)
$injectionEnd = [Convert]::ToUInt32(
    $config.development_injection_end.Substring(2), 16
)
if (-not (
    $oldBoundary -le $injectionBase -and
    $injectionBase -lt $injectionEnd -and
    $injectionEnd -le $loadBase
)) {
    throw 'Payload-builder development injection reservation is invalid.'
}
$dispatcherRuntimeAddress = [uint32]$injectionBase
$activeTargetRuntimeAddress = [uint32]($injectionBase + 0x10)
$codeAreaBase = [uint32]($injectionBase + 0x100)
$codeAreaLength = [uint32]($injectionEnd - $codeAreaBase)
if ($codeAreaLength -lt 0x200 -or $codeAreaLength % 0x20 -ne 0) {
    throw 'Injection reservation cannot be divided into two aligned code banks.'
}
$codeBankSize = [uint32]($codeAreaLength / 2)
$codeBankA = $codeAreaBase
$codeBankB = [uint32]($codeBankA + $codeBankSize)
$previousCodeBase = $null
if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    $selectionState = Get-Content -Raw -LiteralPath $statePath |
        ConvertFrom-Json
    if ('code_base' -in $selectionState.PSObject.Properties.Name) {
        $encodedCodeBase = [string]$selectionState.code_base
        if ($encodedCodeBase -notmatch '^0x[0-9A-Fa-f]{8}$') {
            throw 'Injection-lab state contains an invalid code_base.'
        }
        $previousCodeBase = [Convert]::ToUInt32(
            $encodedCodeBase.Substring(2),
            16
        )
        if ($previousCodeBase -notin $codeBankA, $codeBankB) {
            throw 'Injection-lab state contains an unknown code bank.'
        }
    }
}
$codeBase = if ($previousCodeBase -eq $codeBankA) {
    $codeBankB
}
else {
    $codeBankA
}
$codeEnd = [uint32]($codeBase + $codeBankSize)
$requiresDispatcherRestart = $null -eq $previousCodeBase

$iso = [IO.File]::OpenRead($currentIso)
try {
    $pvd = [byte[]]::new(2048)
    $iso.Position = 16 * 2048
    [void]$iso.Read($pvd, 0, $pvd.Length)
    if ($pvd[0] -ne 1 -or
        [Text.Encoding]::ASCII.GetString($pvd, 1, 5) -cne 'CD001') {
        throw 'Current ISO primary volume descriptor was not found.'
    }
    $root = Read-Na2IsoDirectoryRecord -Data $pvd -Offset 156
    $bootRecord = Find-Na2IsoPath -IsoStream $iso -RootRecord $root `
        -Path ([string]$identity.BootElf)
    $payloadRecord = Find-Na2IsoPath -IsoStream $iso -RootRecord $root `
        -Path 'PRG/228.BIN'
    if ($null -eq $bootRecord -or $null -eq $payloadRecord) {
        throw 'Current ISO does not contain its boot ELF and PRG/228.BIN.'
    }
    $bootBytes = Read-Na2IsoExtent -IsoStream $iso `
        -Extent $bootRecord.Extent -Size $bootRecord.Size
    $payloadBytes = Read-Na2IsoExtent -IsoStream $iso `
        -Extent $payloadRecord.Extent -Size $payloadRecord.Size
}
finally {
    $iso.Dispose()
}

if ($payloadBytes.Length -lt 0x20 -or
    [Text.Encoding]::ASCII.GetString($payloadBytes, 0, 4) -cne 'MWo3') {
    throw 'Current PRG/228.BIN does not have the expected MWO3 header.'
}
$payloadBase = [uint32](Get-UInt32LE $payloadBytes 8)
$payloadMemoryEnd = [uint32](Get-UInt32LE $payloadBytes 0x18)
if ($payloadBase -ne $loadBase -or
    $payloadMemoryEnd -ne [uint32](Get-UInt32LE $payloadBytes 0x1C) -or
    $payloadMemoryEnd -ne $loadBase + $payloadBytes.Length -or
    $payloadMemoryEnd -gt $maximumEnd) {
    throw 'Current PRG/228.BIN does not match the payload-builder memory contract.'
}

$hookFileOffset = Get-ElfFileOffset -Elf $bootBytes `
    -RuntimeAddress $hookRuntimeAddress -Length $expectedHook.Length
Assert-Bytes -Data $bootBytes -Offset $hookFileOffset -Expected $expectedHook `
    -Context ('Current hook at runtime 0x{0:X8}' -f $hookRuntimeAddress)

foreach ($boundaryOffset in 0x2F79F4, 0x50763C) {
    if ((Get-UInt32LE $bootBytes $boundaryOffset) -ne $payloadMemoryEnd) {
        throw (
            'Current ELF memory-boundary integration does not match 228.BIN ' +
            ('at file offset 0x{0:X}.' -f $boundaryOffset)
        )
    }
}

$inputDirectory = Join-Path $labRoot 'data\FILES'
[void](New-Item -ItemType Directory -Path $inputDirectory -Force)
[IO.File]::WriteAllBytes(
    (Join-Path $inputDirectory 'SLOP_NA2.28'),
    $bootBytes
)
[IO.File]::WriteAllBytes(
    (Join-Path $inputDirectory '228.BIN'),
    $payloadBytes
)

$buildId = Get-BuildId
$output = Join-Path $labRoot ("build\{0}.pnach" -f $identity.CRC)
$oldEnvironment = @{
    NA2_INJECTION_CRC = $env:NA2_INJECTION_CRC
    NA2_INJECTION_BASE = $env:NA2_INJECTION_BASE
    NA2_INJECTION_END = $env:NA2_INJECTION_END
    NA2_INJECTION_CODE_BASE = $env:NA2_INJECTION_CODE_BASE
    NA2_INJECTION_CODE_END = $env:NA2_INJECTION_CODE_END
    NA2_INJECTION_BUILD_ID = $env:NA2_INJECTION_BUILD_ID
    NA2_INJECTION_MSYS = $env:NA2_INJECTION_MSYS
}
$env:NA2_INJECTION_CRC = [string]$identity.CRC
$env:NA2_INJECTION_BASE = ('0x{0:X8}' -f $injectionBase)
$env:NA2_INJECTION_END = ('0x{0:X8}' -f $injectionEnd)
$env:NA2_INJECTION_CODE_BASE = ('0x{0:X8}' -f $codeBase)
$env:NA2_INJECTION_CODE_END = ('0x{0:X8}' -f $codeEnd)
$env:NA2_INJECTION_BUILD_ID = ('0x{0:X8}' -f $buildId)
$env:NA2_INJECTION_MSYS = [string]$projectPaths.ps2_msys
Push-Location $labRoot
try {
    if ($productionMode) {
        & python production_adapter.py `
            --source-id $ProductionSource `
            --entry $ProductionEntry
    }
    else {
        & python gen_pnach.py
    }
    if ($LASTEXITCODE -ne 0) {
        throw "PNACH generation failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
    foreach ($name in $oldEnvironment.Keys) {
        if ($null -eq $oldEnvironment[$name]) {
            Remove-Item -Path "Env:$name" -ErrorAction SilentlyContinue
        }
        else {
            Set-Item -Path "Env:$name" -Value $oldEnvironment[$name]
        }
    }
}

if (-not (Test-Path -LiteralPath $output)) {
    throw "Generator did not produce the expected PNACH: $output"
}

if ($productionMode) {
    $manifestPath = Join-Path $labRoot 'build\production-adapter.json'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "Production adapter did not produce its manifest: $manifestPath"
    }
    $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
    if ([string]$manifest.mode -cne 'production_c' -or
        [string]$manifest.source_id -cne $ProductionSource -or
        [string]$manifest.entry_symbol -cne $ProductionEntry) {
        throw 'Production adapter manifest does not match the requested source/entry.'
    }
    $manifestPayloadHash = [string]$manifest.payload_sha256
    $actualPayloadHash = Get-Sha256 (Join-Path $inputDirectory '228.BIN')
    if ($manifestPayloadHash -cne $actualPayloadHash) {
        throw 'Production adapter manifest does not match exact Current 228.BIN.'
    }
    $residentEntryAddress = [Convert]::ToUInt32(
        ([string]$manifest.entry_resident_address).Substring(2),
        16
    )
    $bankEntryAddress = [Convert]::ToUInt32(
        ([string]$manifest.entry_bank_address).Substring(2),
        16
    )
    $usedEnd = [Convert]::ToUInt32(
        ([string]$manifest.used_end).Substring(2),
        16
    )
    if ($usedEnd -le $codeBase -or $usedEnd -gt $codeEnd) {
        throw 'Production adapter manifest reports an invalid used bank range.'
    }
    $expectedResidentEntry = [Convert]::FromHexString(
        [string]$manifest.entry_resident_expected_hex
    )
    if ($expectedResidentEntry.Length -ne 8) {
        throw 'Production adapter manifest must guard exactly eight entry bytes.'
    }
    $residentOffset = [uint32]($residentEntryAddress - $payloadBase)
    Assert-Bytes -Data $payloadBytes -Offset $residentOffset `
        -Expected $expectedResidentEntry `
        -Context ('Current 228.BIN entry at runtime 0x{0:X8}' -f
            $residentEntryAddress)

    $writes = @{}
    foreach ($line in Get-Content -LiteralPath $output) {
        if ($line -notmatch (
            '^patch=1,EE,(?<address>[0-9A-F]{8}),extended,' +
            '(?<value>[0-9A-F]{8})$'
        )) {
            continue
        }
        $encodedAddress = [Convert]::ToUInt32($Matches.address, 16)
        $runtimeAddress = $encodedAddress -band 0x0FFFFFFF
        if ($writes.ContainsKey($runtimeAddress)) {
            throw (
                'Generated production PNACH writes address 0x{0:X8} more ' +
                'than once.' -f $runtimeAddress
            )
        }
        $writes[$runtimeAddress] = [Convert]::ToUInt32($Matches.value, 16)
        $insideDispatcher = (
            $runtimeAddress -ge $injectionBase -and
            $runtimeAddress -lt $codeAreaBase
        )
        $insideUsedBank = (
            $runtimeAddress -ge $codeBase -and
            $runtimeAddress -lt $usedEnd
        )
        $insideEntry = (
            $runtimeAddress -eq $residentEntryAddress -or
            $runtimeAddress -eq [uint32]($residentEntryAddress + 4)
        )
        if (-not ($insideDispatcher -or $insideUsedBank -or $insideEntry)) {
            throw (
                'Generated production PNACH writes outside its guarded ' +
                ('ranges: 0x{0:X8}' -f $runtimeAddress)
            )
        }
    }

    for ($address = $codeBase; $address -lt $usedEnd; $address += 4) {
        if (-not $writes.ContainsKey([uint32]$address)) {
            throw ('Production PNACH is missing bank word 0x{0:X8}.' -f $address)
        }
    }
    $expectedDispatcher = @(
        [pscustomobject]@{
            Address = $dispatcherRuntimeAddress
            Value = [Convert]::ToUInt32('3C19008F', 16)
        }
        [pscustomobject]@{
            Address = [uint32]($dispatcherRuntimeAddress + 4)
            Value = [Convert]::ToUInt32('8F390010', 16)
        }
        [pscustomobject]@{
            Address = [uint32]($dispatcherRuntimeAddress + 8)
            Value = [Convert]::ToUInt32('03200008', 16)
        }
        [pscustomobject]@{
            Address = [uint32]($dispatcherRuntimeAddress + 12)
            Value = [uint32]0
        }
        [pscustomobject]@{
            Address = $activeTargetRuntimeAddress
            Value = $bankEntryAddress
        }
    )
    foreach ($entry in $expectedDispatcher) {
        if (-not $writes.ContainsKey($entry.Address) -or
            [uint32]$writes[$entry.Address] -ne [uint32]$entry.Value) {
            throw (
                (
                    'Generated production dispatcher mismatch at 0x{0:X8}: ' +
                    'expected 0x{1:X8}.'
                ) -f $entry.Address, $entry.Value
            )
        }
    }
    $redirect = [uint32]$writes[$residentEntryAddress]
    if (($redirect -band 0xFC000000) -ne 0x08000000) {
        throw ('Production resident redirect is not J: 0x{0:X8}.' -f $redirect)
    }
    $redirectTarget = [uint32](($redirect -band 0x03FFFFFF) -shl 2)
    if ($redirectTarget -ne $dispatcherRuntimeAddress -or
        [uint32]$writes[[uint32]($residentEntryAddress + 4)] -ne 0) {
        throw 'Production resident redirect does not tail-jump through the dispatcher.'
    }
}
else {
$hookWrites = @{}
$dispatcherWrites = @{}
foreach ($line in Get-Content -LiteralPath $output) {
    if ($line -notmatch (
        '^patch=1,EE,(?<address>[0-9A-F]{8}),extended,' +
        '(?<value>[0-9A-F]{8})$'
    )) {
        continue
    }
    $encodedAddress = [Convert]::ToUInt32($Matches.address, 16)
    $runtimeAddress = $encodedAddress -band 0x0FFFFFFF
    if ($runtimeAddress -in $hookRuntimeAddresses) {
        if ($hookWrites.ContainsKey($runtimeAddress)) {
            throw (
                'Generated PNACH writes hook address 0x{0:X8} more than once.' -f
                $runtimeAddress
            )
        }
        $hookWrites[$runtimeAddress] = [Convert]::ToUInt32($Matches.value, 16)
        continue
    }
    if ($runtimeAddress -lt $injectionBase -or $runtimeAddress -ge $injectionEnd) {
        throw ('Generated PNACH writes outside the reserved range: 0x{0:X8}' -f
            $runtimeAddress)
    }
    if ($runtimeAddress -lt $codeAreaBase) {
        if ($dispatcherWrites.ContainsKey($runtimeAddress)) {
            throw (
                'Generated PNACH writes dispatcher address 0x{0:X8} more than once.' -f
                $runtimeAddress
            )
        }
        $dispatcherWrites[$runtimeAddress] = [Convert]::ToUInt32(
            $Matches.value,
            16
        )
    }
}
if ($hookWrites.Count -ne $hookRuntimeAddresses.Count) {
    throw (
        'Generated PNACH must contain exactly five guarded epilogue-hook ' +
        "writes; found $($hookWrites.Count)."
    )
}
foreach ($address in $hookRuntimeAddresses) {
    if (-not $hookWrites.ContainsKey($address)) {
        throw ('Generated PNACH is missing hook address 0x{0:X8}.' -f $address)
    }
}
$jal = [uint32]$hookWrites[[uint32]0x001D0578]
if (($jal -band 0xFC000000) -ne 0x0C000000) {
    throw ('Generated hook is not a JAL instruction: 0x{0:X8}.' -f $jal)
}
$hookTarget = [uint32](($jal -band 0x03FFFFFF) -shl 2)
if ($hookTarget -ne $dispatcherRuntimeAddress) {
    throw (
        'Generated hook target is not the fixed dispatcher: 0x{0:X8}.' -f
        $hookTarget
    )
}
$expectedHookTail = @(
    [pscustomobject]@{
        Address = [uint32]0x001D057C
        Value = [uint32]0x00000000
    }
    [pscustomobject]@{
        Address = [uint32]0x001D0580
        Value = [Convert]::ToUInt32('DFBF0000', 16)
    }
    [pscustomobject]@{
        Address = [uint32]0x001D0584
        Value = [uint32]0x03E00008
    }
    [pscustomobject]@{
        Address = [uint32]0x001D0588
        Value = [uint32]0x27BD0010
    }
)
foreach ($entry in $expectedHookTail) {
    if ([uint32]$hookWrites[$entry.Address] -ne [uint32]$entry.Value) {
        throw (
            (
                'Generated displaced epilogue mismatch at 0x{0:X8}: ' +
                '0x{1:X8} != 0x{2:X8}.'
            ) -f $entry.Address, $hookWrites[$entry.Address], $entry.Value
        )
    }
}
$expectedDispatcher = @(
    [pscustomobject]@{
        Address = $dispatcherRuntimeAddress
        Value = [Convert]::ToUInt32('3C19008F', 16)
    }
    [pscustomobject]@{
        Address = [uint32]($dispatcherRuntimeAddress + 4)
        Value = [Convert]::ToUInt32('8F390010', 16)
    }
    [pscustomobject]@{
        Address = [uint32]($dispatcherRuntimeAddress + 8)
        Value = [Convert]::ToUInt32('03200008', 16)
    }
    [pscustomobject]@{
        Address = [uint32]($dispatcherRuntimeAddress + 12)
        Value = [uint32]0
    }
    [pscustomobject]@{
        Address = $activeTargetRuntimeAddress
        Value = $codeBase
    }
)
foreach ($entry in $expectedDispatcher) {
    if (-not $dispatcherWrites.ContainsKey($entry.Address) -or
        [uint32]$dispatcherWrites[$entry.Address] -ne [uint32]$entry.Value) {
        throw (
            (
                'Generated dispatcher mismatch at 0x{0:X8}: ' +
                'expected 0x{1:X8}.'
            ) -f $entry.Address, $entry.Value
        )
    }
}
}

$outputHash = Get-Sha256 $output
if ($BuildOnly) {
    Write-Host '[injection_lab] Build-only validation passed.'
    Write-Host "[injection_lab] Current: $($identity.Serial)_$($identity.CRC)"
    if ($productionMode) {
        Write-Host (
            '[injection_lab] Production C: {0} -> {1}' -f
            $ProductionSource, $ProductionEntry
        )
    }
    Write-Host (
        '[injection_lab] Reservation: 0x{0:X8}-0x{1:X8} ({2} bytes)' -f
        $injectionBase, $injectionEnd, ($injectionEnd - $injectionBase)
    )
    Write-Host (
        '[injection_lab] Code bank: 0x{0:X8}-0x{1:X8}' -f
        $codeBase, $codeEnd
    )
    Write-Host ('[injection_lab] Build ID: 0x{0:X8}' -f $buildId)
    Write-Host "[injection_lab] PNACH: $output"
    Write-Host "[injection_lab] SHA-256: $outputHash"
    exit 0
}

if (-not (Test-Path -LiteralPath $cheatsDirectory)) {
    throw "PCSX2 cheats directory was not found: $cheatsDirectory"
}
$effectivePinePort = Get-InjectionLabPinePort `
    -CheatsDirectory $cheatsDirectory `
    -ExplicitPort $PinePort
$target = Join-Path $cheatsDirectory ([string]$identity.PnachName)

if (Test-Path -LiteralPath $statePath) {
    $state = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
}
else {
    $existing = Get-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue
    if ($existing) {
        if ([string]$existing.LinkType -ceq 'SymbolicLink') {
            Remove-Item -LiteralPath $target -Force
        }
        elseif ($existing.PSIsContainer) {
            throw "Refusing to replace a directory at the PNACH path: $target"
        }
    }
    $state = [pscustomobject]@{
        target = $target
        current_crc = [string]$identity.CRC
        build_id = ('0x{0:X8}' -f $buildId)
        code_base = ('0x{0:X8}' -f $codeBase)
        layout = $expectedLayout
        production_source = $(if ($productionMode) { $ProductionSource } else { '' })
        production_entry = $(if ($productionMode) { $ProductionEntry } else { '' })
    }
}
Write-PnachInPlace -Source $output -Target $target
$state.target = $target
$state.current_crc = [string]$identity.CRC
$state.build_id = ('0x{0:X8}' -f $buildId)
$state | Add-Member `
    -NotePropertyName code_base `
    -NotePropertyValue ('0x{0:X8}' -f $codeBase) `
    -Force
$state | Add-Member `
    -NotePropertyName layout `
    -NotePropertyValue $expectedLayout `
    -Force
$state | Add-Member `
    -NotePropertyName production_source `
    -NotePropertyValue $(if ($productionMode) { $ProductionSource } else { '' }) `
    -Force
$state | Add-Member `
    -NotePropertyName production_entry `
    -NotePropertyValue $(if ($productionMode) { $ProductionEntry } else { '' }) `
    -Force
$state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
Invoke-PineReloadPatches -Port $effectivePinePort

Write-Host '[injection_lab] Current development PNACH installed.'
Write-Host "[injection_lab] Target: $target"
Write-Host ('[injection_lab] Code bank: 0x{0:X8}' -f $codeBase)
Write-Host ('[injection_lab] Build ID: 0x{0:X8}' -f $buildId)
if ($requiresDispatcherRestart) {
    Write-Host '[injection_lab] Start or restart Current once to activate the dispatcher.'
}
Write-Host "[injection_lab] PCSX2 patches reloaded through PINE port $effectivePinePort."
Write-Host '[injection_lab] Check pcsx2/logs/emulog.txt for:'
Write-Host 'NA2.28 injection lab: C hot reload active'
