[CmdletBinding()]
param(
    [switch]$BuildOnly,
    [switch]$Remove,
    [string]$CurrentIso,
    [string]$CheatsDirectory
)

$ErrorActionPreference = 'Stop'

$labRoot = $PSScriptRoot
$repository = Split-Path -Parent $labRoot
$statePath = Join-Path $labRoot 'build\test-install.json'
$backupPath = Join-Path $labRoot 'build\current-pnach.before-test'
$payloadConfigPath = Join-Path $repository 'na2_patcher\payload_builder\config.tsv'
$identityScript = Join-Path $repository 'scripts\na2\iso_identity.ps1'
$hookRuntimeAddress = 0x001D0570
$expectedHook = [byte[]](0x04, 0x77, 0x05, 0x0C)

if (-not $CurrentIso) {
    $CurrentIso = Join-Path $repository 'build\NA2.28 - Current.iso'
}
if (-not $CheatsDirectory) {
    $CheatsDirectory = Join-Path $repository 'pcsx2\cheats'
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

function New-FileSymbolicLink([string]$Path, [string]$Target) {
    $useNative = -not [IO.Path]::IsPathRooted($Target)
    if (-not $useNative) {
        try {
            [void](New-Item -ItemType SymbolicLink -Path $Path -Target $Target)
            return
        }
        catch [UnauthorizedAccessException] {
            $useNative = $true
        }
    }
    if ($useNative) {
        if (-not ('InjectionLabNativeMethods' -as [type])) {
            Add-Type @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class InjectionLabNativeMethods {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CreateSymbolicLink(
        string symbolicLink,
        string target,
        int flags
    );

    public static void CreateFileSymbolicLink(string symbolicLink, string target) {
        const int SYMBOLIC_LINK_FLAG_ALLOW_UNPRIVILEGED_CREATE = 0x2;
        if (!CreateSymbolicLink(
            symbolicLink,
            target,
            SYMBOLIC_LINK_FLAG_ALLOW_UNPRIVILEGED_CREATE
        )) {
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }
    }
}
'@
        }
        [InjectionLabNativeMethods]::CreateFileSymbolicLink($Path, $Target)
    }
}

function Restore-TestPnach {
    if (-not (Test-Path -LiteralPath $statePath)) {
        Write-Host '[injection_lab] No installed test PNACH is recorded.'
        return
    }

    $state = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
    $recordedTarget = [string]$state.target
    if (Test-Path -LiteralPath $recordedTarget) {
        $actualHash = Get-Sha256 $recordedTarget
        if ($actualHash -cne [string]$state.installed_sha256) {
            throw "Refusing to remove a PNACH changed after installation: $recordedTarget"
        }
        Remove-Item -LiteralPath $recordedTarget -Force
    }

    switch ([string]$state.previous_kind) {
        'symbolic_link' {
            New-FileSymbolicLink -Path $recordedTarget `
                -Target ([string]$state.previous_target)
            Write-Host "[injection_lab] Restored the managed PNACH link: $recordedTarget"
        }
        'file' {
            if (-not (Test-Path -LiteralPath $backupPath)) {
                throw "Cannot restore the pre-test PNACH because its backup is missing: $backupPath"
            }
            Copy-Item -LiteralPath $backupPath -Destination $recordedTarget
            Remove-Item -LiteralPath $backupPath -Force
            Write-Host "[injection_lab] Restored the pre-test PNACH: $recordedTarget"
        }
        'none' {
            Write-Host "[injection_lab] Removed the test PNACH: $recordedTarget"
        }
        default {
            throw "Unknown recorded PNACH kind: $($state.previous_kind)"
        }
    }

    Remove-Item -LiteralPath $statePath -Force
    Write-Host '[injection_lab] Restart Current to restore the original in-memory hook.'
}

if ($Remove) {
    Restore-TestPnach
    exit 0
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

$buildId = Get-BuildId
$output = Join-Path $labRoot ("build\{0}.pnach" -f $identity.CRC)
$oldEnvironment = @{
    NA2_INJECTION_CRC = $env:NA2_INJECTION_CRC
    NA2_INJECTION_BASE = $env:NA2_INJECTION_BASE
    NA2_INJECTION_END = $env:NA2_INJECTION_END
    NA2_INJECTION_BUILD_ID = $env:NA2_INJECTION_BUILD_ID
}
$env:NA2_INJECTION_CRC = [string]$identity.CRC
$env:NA2_INJECTION_BASE = ('0x{0:X8}' -f $injectionBase)
$env:NA2_INJECTION_END = ('0x{0:X8}' -f $injectionEnd)
$env:NA2_INJECTION_BUILD_ID = ('0x{0:X8}' -f $buildId)
Push-Location $labRoot
try {
    & python gen_pnach.py
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

$hookWriteCount = 0
foreach ($line in Get-Content -LiteralPath $output) {
    if ($line -notmatch '^patch=1,EE,(?<address>[0-9A-F]{8}),extended,[0-9A-F]{8}$') {
        continue
    }
    $encodedAddress = [Convert]::ToUInt32($Matches.address, 16)
    $runtimeAddress = $encodedAddress -band 0x0FFFFFFF
    if ($runtimeAddress -eq $hookRuntimeAddress) {
        $hookWriteCount++
        continue
    }
    if ($runtimeAddress -lt $injectionBase -or $runtimeAddress -ge $injectionEnd) {
        throw ('Generated PNACH writes outside the reserved range: 0x{0:X8}' -f
            $runtimeAddress)
    }
}
if ($hookWriteCount -ne 1) {
    throw "Generated PNACH must contain exactly one guarded hook write."
}

$outputHash = Get-Sha256 $output
if ($BuildOnly) {
    Write-Host '[injection_lab] Build-only validation passed.'
    Write-Host "[injection_lab] Current: $($identity.Serial)_$($identity.CRC)"
    Write-Host (
        '[injection_lab] Reservation: 0x{0:X8}-0x{1:X8} ({2} bytes)' -f
        $injectionBase, $injectionEnd, ($injectionEnd - $injectionBase)
    )
    Write-Host ('[injection_lab] Build ID: 0x{0:X8}' -f $buildId)
    Write-Host "[injection_lab] PNACH: $output"
    Write-Host "[injection_lab] SHA-256: $outputHash"
    exit 0
}

if (-not (Test-Path -LiteralPath $cheatsDirectory)) {
    throw "PCSX2 cheats directory was not found: $cheatsDirectory"
}
$target = Join-Path $cheatsDirectory ([string]$identity.PnachName)

if (Test-Path -LiteralPath $statePath) {
    $state = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
    if ([string]$state.target -cne $target) {
        throw (
            'Current identity changed while a test PNACH is installed. ' +
            'Run .\injection_lab\test.ps1 -Remove first.'
        )
    }
    if (-not (Test-Path -LiteralPath $target)) {
        throw "Recorded test PNACH is missing: $target"
    }
    $actualHash = Get-Sha256 $target
    if ($actualHash -cne [string]$state.installed_sha256) {
        throw "Refusing to overwrite a PNACH changed after installation: $target"
    }
}
else {
    $existing = Get-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue
    $previousKind = 'none'
    $previousTarget = ''
    if ($existing) {
        if ([string]$existing.LinkType -ceq 'SymbolicLink') {
            $previousKind = 'symbolic_link'
            $previousTarget = [string]$existing.Target
            Remove-Item -LiteralPath $target -Force
        }
        elseif (-not $existing.PSIsContainer) {
            $previousKind = 'file'
            Copy-Item -LiteralPath $target -Destination $backupPath
        }
        else {
            throw "Refusing to replace a directory at the PNACH path: $target"
        }
    }
    $state = [pscustomobject]@{
        target = $target
        previous_kind = $previousKind
        previous_target = $previousTarget
        installed_sha256 = ''
        current_crc = [string]$identity.CRC
        build_id = ('0x{0:X8}' -f $buildId)
    }
}

Write-PnachInPlace -Source $output -Target $target
$state.installed_sha256 = Get-Sha256 $target
$state.current_crc = [string]$identity.CRC
$state.build_id = ('0x{0:X8}' -f $buildId)
$state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8

Write-Host '[injection_lab] Current development PNACH installed.'
Write-Host "[injection_lab] Target: $target"
Write-Host ('[injection_lab] Build ID: 0x{0:X8}' -f $buildId)
Write-Host '[injection_lab] PCSX2 should detect the in-place PNACH rewrite automatically.'
Write-Host '[injection_lab] If it does not, select System -> Reload Cheats/Patches.'
Write-Host '[injection_lab] Watch the PCSX2 console for:'
Write-Host 'NA2.28 injection lab: C hot reload active'
