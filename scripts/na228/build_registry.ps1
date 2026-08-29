Set-StrictMode -Version Latest

if (-not ('Na228.NativeFileLinks' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

namespace Na228
{
    public static class NativeFileLinks
    {
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool CreateHardLink(
            string newFileName,
            string existingFileName,
            IntPtr securityAttributes
        );
    }
}
'@
}

function ConvertTo-Na2ExtendedPath {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)

    $fullPath = [IO.Path]::GetFullPath($Path)
    if ($fullPath.StartsWith('\\?\')) { return $fullPath }
    if ($fullPath.StartsWith('\\')) {
        return '\\?\UNC\' + $fullPath.Substring(2)
    }
    return '\\?\' + $fullPath
}

function Invoke-Na2BuildRegistry {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][ValidateSet('lookup', 'record', 'complete')]
        [string]$Command,
        [Parameter(Mandatory)][string]$Registry,
        [Parameter(Mandatory)][string]$CacheRoot,
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string]$PythonRunner,
        [string]$Na2Iso,
        [string]$Nun5Iso,
        [string]$Configuration,
        [string]$ExpectedFingerprint,
        [string]$Image,
        [string]$Provenance,
        [string]$Fingerprint,
        [string[]]$Location
    )

    $arguments = @(
        $Command
        '--registry', $Registry
        '--cache-root', $CacheRoot
    )
    if ($Command -in @('lookup', 'record')) {
        $arguments += @(
            '--na2-iso', $Na2Iso
            '--nun5-iso', $Nun5Iso
            '--configuration', $Configuration
        )
    }
    if ($Command -eq 'record') {
        $arguments += @(
            '--expected-fingerprint', $ExpectedFingerprint
            '--image', $Image
        )
        if (-not [string]::IsNullOrWhiteSpace($Provenance)) {
            $arguments += @('--provenance', $Provenance)
        }
    }
    elseif ($Command -eq 'complete') {
        $arguments += @('--fingerprint', $Fingerprint)
        foreach ($completedLocation in $Location) {
            $arguments += @('--location', $completedLocation)
        }
    }

    Push-Location $Repository
    try {
        $output = @(
            & $PythonRunner `
                -PackageSet builder `
                -Module 'na228_builder.scripts.build_preflight' `
                -ArgumentList $arguments `
                -NoBytecode 2>&1
        )
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    if ($exitCode -ne 0) {
        throw "NA2 build registry failed to execute (exit $exitCode): $($output -join "`n")"
    }
    if ($output.Count -ne 1) {
        throw 'NA2 build registry did not return exactly one JSON result.'
    }
    try {
        return $output[0] | ConvertFrom-Json
    }
    catch {
        throw "NA2 build registry returned invalid JSON: $($output[0])"
    }
}

function Copy-Na2RegistryProvenance {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
        throw "Verified build provenance is unavailable: $Source"
    }
    if (Test-Path -LiteralPath $Destination) {
        throw "Build record destination already exists: $Destination"
    }
    [void](New-Item -ItemType Directory -Path $Destination)
    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $Destination -Recurse
    }
}

function Test-Na2ImageIdentity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][long]$Size,
        [Parameter(Mandatory)][string]$Sha256
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    $item = Get-Item -LiteralPath $Path
    if ($item.Length -ne $Size) { return $false }
    (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash -ceq $Sha256
}

function Set-Na2HardLink {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )

    $sourcePath = [IO.Path]::GetFullPath($Source)
    $destinationPath = [IO.Path]::GetFullPath($Destination)
    $destinationParent = [IO.Path]::GetDirectoryName($destinationPath)
    [void](New-Item -ItemType Directory -Path $destinationParent -Force)
    $temporary = Join-Path $destinationParent (".hl-{0}" -f [Guid]::NewGuid().ToString('N'))
    try {
        $created = [Na228.NativeFileLinks]::CreateHardLink(
            (ConvertTo-Na2ExtendedPath $temporary),
            (ConvertTo-Na2ExtendedPath $sourcePath),
            [IntPtr]::Zero
        )
        if (-not $created) {
            throw [ComponentModel.Win32Exception]::new(
                [Runtime.InteropServices.Marshal]::GetLastWin32Error()
            )
        }
        [IO.File]::Move($temporary, $destinationPath, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            [IO.File]::Delete($temporary)
        }
    }
}

function Get-Na2CachedImage {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Candidate,
        [Parameter(Mandatory)][long]$Size,
        [Parameter(Mandatory)][string]$Sha256,
        [Parameter(Mandatory)][string]$CacheRoot
    )

    $candidatePath = [IO.Path]::GetFullPath($Candidate)
    if (-not (Test-Na2ImageIdentity -Path $candidatePath -Size $Size -Sha256 $Sha256)) {
        throw "Verified ISO candidate identity mismatch: $candidatePath"
    }
    [void](New-Item -ItemType Directory -Path $CacheRoot -Force)
    $cacheImage = [IO.Path]::GetFullPath((Join-Path $CacheRoot "$Sha256.iso"))
    if ($candidatePath -ine $cacheImage) {
        if (Test-Path -LiteralPath $cacheImage) {
            if (-not (Test-Na2ImageIdentity -Path $cacheImage -Size $Size -Sha256 $Sha256)) {
                throw "Cached ISO identity mismatch: $cacheImage"
            }
        }
        else {
            Set-Na2HardLink -Source $candidatePath -Destination $cacheImage
            if (-not (Test-Na2ImageIdentity -Path $cacheImage -Size $Size -Sha256 $Sha256)) {
                throw "Cached ISO identity mismatch after hardlink creation: $cacheImage"
            }
        }
    }
    return $cacheImage
}

function Move-Na2VerifiedImageToCache {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Candidate,
        [Parameter(Mandatory)][string]$CacheRoot
    )

    $candidatePath = [IO.Path]::GetFullPath($Candidate)
    if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) {
        throw "Verified ISO candidate does not exist: $candidatePath"
    }
    $item = Get-Item -LiteralPath $candidatePath
    $sha256 = (Get-FileHash -LiteralPath $candidatePath -Algorithm SHA256).Hash
    [void](New-Item -ItemType Directory -Path $CacheRoot -Force)
    $cacheImage = Join-Path $CacheRoot "$sha256.iso"
    if (Test-Path -LiteralPath $cacheImage) {
        if (-not (Test-Na2ImageIdentity -Path $cacheImage -Size $item.Length -Sha256 $sha256)) {
            throw "Cached ISO identity mismatch: $cacheImage"
        }
        [IO.File]::Delete($candidatePath)
    }
    else {
        [IO.File]::Move($candidatePath, $cacheImage)
    }
    return [pscustomobject]@{
        Image = [IO.Path]::GetFullPath($cacheImage)
        Size = [long]$item.Length
        Sha256 = $sha256
    }
}

function Remove-Na2StaleIncomingImages {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$IncomingRoot)

    if (-not (Test-Path -LiteralPath $IncomingRoot -PathType Container)) { return }
    foreach ($image in Get-ChildItem -LiteralPath $IncomingRoot -File -Filter '*.iso') {
        $lockPath = $image.FullName + '.lock'
        $lock = $null
        try {
            $lock = [IO.File]::Open(
                $lockPath,
                [IO.FileMode]::OpenOrCreate,
                [IO.FileAccess]::ReadWrite,
                [IO.FileShare]::None
            )
        }
        catch [IO.IOException] {
            continue
        }
        try {
            try {
                [IO.File]::Delete($image.FullName)
            }
            catch [IO.IOException] {
                continue
            }
        }
        finally {
            $lock.Dispose()
            try { [IO.File]::Delete($lockPath) } catch [IO.IOException] {}
        }
    }
    foreach ($lockFile in Get-ChildItem -LiteralPath $IncomingRoot -File -Filter '*.iso.lock') {
        $imagePath = $lockFile.FullName.Substring(0, $lockFile.FullName.Length - 5)
        if (Test-Path -LiteralPath $imagePath) { continue }
        $lock = $null
        try {
            $lock = [IO.File]::Open(
                $lockFile.FullName,
                [IO.FileMode]::Open,
                [IO.FileAccess]::ReadWrite,
                [IO.FileShare]::None
            )
        }
        catch [IO.IOException] {
            continue
        }
        $lock.Dispose()
        try { [IO.File]::Delete($lockFile.FullName) } catch [IO.IOException] {}
    }
}

function Enter-Na2IncomingImage {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Image)

    $lockPath = [IO.Path]::GetFullPath($Image) + '.lock'
    [IO.File]::Open(
        $lockPath,
        [IO.FileMode]::CreateNew,
        [IO.FileAccess]::ReadWrite,
        [IO.FileShare]::None
    )
}

function Exit-Na2IncomingImage {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Image,
        [Parameter(Mandatory)][IO.FileStream]$Lock
    )

    $lockPath = [IO.Path]::GetFullPath($Image) + '.lock'
    $Lock.Dispose()
    if (Test-Path -LiteralPath $Image -PathType Leaf) {
        [IO.File]::Delete($Image)
    }
    if (Test-Path -LiteralPath $lockPath -PathType Leaf) {
        [IO.File]::Delete($lockPath)
    }
}

function Publish-Na2VerifiedImage {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Candidate,
        [Parameter(Mandatory)][string]$Destination,
        [Parameter(Mandatory)][long]$Size,
        [Parameter(Mandatory)][string]$Sha256,
        [Parameter(Mandatory)][string]$CacheRoot,
        [string]$Previous,
        [switch]$Rotate
    )

    $candidatePath = [IO.Path]::GetFullPath($Candidate)
    $destinationPath = [IO.Path]::GetFullPath($Destination)
    [void](New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destinationPath)) -Force)
    $cacheImage = Get-Na2CachedImage -Candidate $candidatePath -Size $Size `
        -Sha256 $Sha256 -CacheRoot $CacheRoot
    if (Test-Na2ImageIdentity -Path $destinationPath -Size $Size -Sha256 $Sha256) {
        return [pscustomobject]@{
            Status = 'unchanged'
            OutputIso = $destinationPath
            PreviousIso = $Previous
            Rotated = $false
            ChangedRoles = [string[]]@()
        }
    }

    $rotated = $false
    $previousChanged = $false
    $previousBackup = $null
    $previousPath = if ([string]::IsNullOrWhiteSpace($Previous)) {
        $null
    }
    else {
        [IO.Path]::GetFullPath($Previous)
    }
    try {
        if ($Rotate -and (Test-Path -LiteralPath $destinationPath -PathType Leaf)) {
            $outgoing = Get-Item -LiteralPath $destinationPath
            $outgoingHash = (Get-FileHash -LiteralPath $destinationPath -Algorithm SHA256).Hash
            $outgoingCache = Get-Na2CachedImage -Candidate $destinationPath `
                -Size $outgoing.Length -Sha256 $outgoingHash -CacheRoot $CacheRoot
            if (Test-Path -LiteralPath $previousPath -PathType Leaf) {
                $previousBackup = Join-Path (
                    [IO.Path]::GetDirectoryName($previousPath)
                ) (".rb-{0}" -f [Guid]::NewGuid().ToString('N'))
                $backupCreated = [Na228.NativeFileLinks]::CreateHardLink(
                    (ConvertTo-Na2ExtendedPath $previousBackup),
                    (ConvertTo-Na2ExtendedPath $previousPath),
                    [IntPtr]::Zero
                )
                if (-not $backupCreated) {
                    throw [ComponentModel.Win32Exception]::new(
                        [Runtime.InteropServices.Marshal]::GetLastWin32Error()
                    )
                }
            }
            Set-Na2HardLink -Source $outgoingCache -Destination $previousPath
            $previousChanged = $true
        }
        Set-Na2HardLink -Source $cacheImage -Destination $destinationPath
        $rotated = $previousChanged
    }
    catch {
        if ($previousChanged) {
            if ($null -ne $previousBackup -and
                (Test-Path -LiteralPath $previousBackup -PathType Leaf)) {
                Set-Na2HardLink -Source $previousBackup -Destination $previousPath
            }
            elseif (Test-Path -LiteralPath $previousPath -PathType Leaf) {
                [IO.File]::Delete($previousPath)
            }
        }
        return [pscustomobject]@{
            Status = 'pending'
            OutputIso = $cacheImage
            PreviousIso = $previousPath
            Rotated = $false
            Failure = $_.Exception.Message
            ChangedRoles = [string[]]@()
        }
    }
    finally {
        if ($null -ne $previousBackup -and
            (Test-Path -LiteralPath $previousBackup -PathType Leaf)) {
            [IO.File]::Delete($previousBackup)
        }
    }

    $changedRoles = [Collections.Generic.List[string]]::new()
    $changedRoles.Add('output')
    if ($rotated) { $changedRoles.Add('previous') }
    return [pscustomobject]@{
        Status = 'updated'
        OutputIso = $destinationPath
        PreviousIso = $previousPath
        Rotated = $rotated
        ChangedRoles = [string[]]@($changedRoles)
    }
}
