function Get-Na2Pcsx2Process {
    param([Parameter(Mandatory = $true)][string]$Executable)

    $resolvedExecutable = [IO.Path]::GetFullPath($Executable)
    $processName = [IO.Path]::GetFileNameWithoutExtension($resolvedExecutable)
    @(Get-Process -Name $processName -ErrorAction SilentlyContinue | Where-Object {
        try {
            [IO.Path]::Equals([IO.Path]::GetFullPath($_.Path), $resolvedExecutable)
        }
        catch {
            $false
        }
    })
}

function Stop-Na2Pcsx2 {
    param([Parameter(Mandatory = $true)][string]$Executable)

    $processes = @(Get-Na2Pcsx2Process -Executable $Executable)
    $notStopped = [Collections.Generic.List[int]]::new()
    foreach ($process in $processes) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
    foreach ($process in $processes) {
        try {
            if (-not $process.WaitForExit(5000)) {
                $notStopped.Add($process.Id)
            }
        }
        catch {
            if ($null -ne (Get-Process -Id $process.Id -ErrorAction SilentlyContinue)) {
                $notStopped.Add($process.Id)
            }
        }
    }
    if ($notStopped.Count -gt 0) {
        throw "PCSX2 did not stop within 5 seconds: PID(s) $($notStopped -join ', ')."
    }
}

function Get-Na2Pcsx2OwnershipCapabilityHash {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$Token)

    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return [Convert]::ToHexString(
            $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Token))
        )
    }
    finally {
        $sha.Dispose()
    }
}

function New-Na2Pcsx2OwnershipCapability {
    [CmdletBinding()]
    param()

    $secret = [byte[]]::new(32)
    [Security.Cryptography.RandomNumberGenerator]::Fill($secret)
    [pscustomobject]@{
        Token = [Convert]::ToBase64String($secret)
        DescriptorMac = $null
    }
}

function Get-Na2Pcsx2DescriptorMac {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][byte[]]$Content,
        [Parameter(Mandatory = $true)][string]$Token
    )

    $hmac = [Security.Cryptography.HMACSHA256]::new(
        [Text.Encoding]::UTF8.GetBytes($Token)
    )
    try {
        return [Convert]::ToHexString($hmac.ComputeHash($Content))
    }
    finally {
        $hmac.Dispose()
    }
}

function Test-Na2FixedTimeHexEquality {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Left,
        [Parameter(Mandatory = $true)][string]$Right
    )

    try {
        $leftBytes = [Convert]::FromHexString($Left)
        $rightBytes = [Convert]::FromHexString($Right)
        return [Security.Cryptography.CryptographicOperations]::FixedTimeEquals(
            $leftBytes,
            $rightBytes
        )
    }
    catch {
        return $false
    }
}

function Write-Na2Pcsx2OwnershipDescriptor {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][Collections.IDictionary]$Descriptor,
        [Parameter(Mandatory = $true)][psobject]$OwnershipCapability
    )

    if ([string]::IsNullOrWhiteSpace([string]$OwnershipCapability.Token)) {
        throw 'PCSX2 ownership capability is missing.'
    }
    $Descriptor['ownership_capability_sha256'] =
        Get-Na2Pcsx2OwnershipCapabilityHash -Token $OwnershipCapability.Token
    $content = ($Descriptor | ConvertTo-Json -Depth 6) + "`n"
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($content)
    $directory = [IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Path))
    if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
        throw "PCSX2 descriptor directory does not exist: $directory"
    }
    $temporary = Join-Path $directory (
        ".$([IO.Path]::GetFileName($Path)).$PID.$([guid]::NewGuid().ToString('N')).tmp"
    )
    try {
        [IO.File]::WriteAllBytes($temporary, $bytes)
        [IO.File]::Move($temporary, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
    $OwnershipCapability.DescriptorMac =
        Get-Na2Pcsx2DescriptorMac -Content $bytes -Token $OwnershipCapability.Token
}

function Get-Na2Pcsx2OwnershipState {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$DescriptorPath,
        [psobject]$OwnershipCapability,
        [switch]$KeepDescriptorOpen
    )

    $invalid = {
        param([string]$Reason)
        [pscustomobject]@{
            Valid = $false
            Reason = $Reason
            Descriptor = $null
            DescriptorHandle = $null
        }
    }

    if ($null -eq $OwnershipCapability -or
        [string]::IsNullOrWhiteSpace([string]$OwnershipCapability.Token) -or
        [string]::IsNullOrWhiteSpace([string]$OwnershipCapability.DescriptorMac)) {
        return & $invalid 'the in-memory ownership capability is missing'
    }
    if (-not (Test-Path -LiteralPath $DescriptorPath -PathType Leaf)) {
        return & $invalid 'the live instance descriptor is missing'
    }

    $descriptorHandle = $null
    $retainDescriptorHandle = $false
    try {
        $descriptorHandle = [IO.File]::Open(
            $DescriptorPath,
            [IO.FileMode]::Open,
            [IO.FileAccess]::Read,
            [IO.FileShare]::Read
        )
        $bytes = [byte[]]::new([int]$descriptorHandle.Length)
        $offset = 0
        while ($offset -lt $bytes.Length) {
            $read = $descriptorHandle.Read($bytes, $offset, $bytes.Length - $offset)
            if ($read -le 0) { throw 'Unexpected end of the instance descriptor.' }
            $offset += $read
        }
        $actualMac = Get-Na2Pcsx2DescriptorMac `
            -Content $bytes `
            -Token $OwnershipCapability.Token
        if (-not (Test-Na2FixedTimeHexEquality `
            -Left $actualMac `
            -Right ([string]$OwnershipCapability.DescriptorMac))) {
            return & $invalid 'the instance descriptor no longer matches the ownership capability'
        }
        $descriptor = [Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
        $capabilityHash = Get-Na2Pcsx2OwnershipCapabilityHash `
            -Token $OwnershipCapability.Token
        if (-not (Test-Na2FixedTimeHexEquality `
            -Left $capabilityHash `
            -Right ([string]$descriptor.ownership_capability_sha256))) {
            return & $invalid 'the instance descriptor contains a different ownership capability'
        }
        if ($KeepDescriptorOpen) {
            $retainDescriptorHandle = $true
        }
        return [pscustomobject]@{
            Valid = $true
            Reason = $null
            Descriptor = $descriptor
            DescriptorHandle = if ($retainDescriptorHandle) { $descriptorHandle } else { $null }
        }
    }
    catch {
        return & $invalid "the instance descriptor is invalid: $($_.Exception.Message)"
    }
    finally {
        if ($null -ne $descriptorHandle -and -not $retainDescriptorHandle) {
            $descriptorHandle.Dispose()
        }
    }
}

function Stop-Na2Pcsx2Process {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$DescriptorPath,
        [Parameter(Mandatory = $true)][psobject]$OwnershipCapability,
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string]$ExecutableIdentity
    )

    $ownership = Get-Na2Pcsx2OwnershipState `
        -DescriptorPath $DescriptorPath `
        -OwnershipCapability $OwnershipCapability `
        -KeepDescriptorOpen
    if (-not $ownership.Valid) {
        return [pscustomobject]@{
            Status = 'LostOwnership'
            Reason = $ownership.Reason
        }
    }

    $process = $null
    try {
        $descriptor = $ownership.Descriptor
        if ([string]$descriptor.executable -cne $ExecutableIdentity) {
            return [pscustomobject]@{
                Status = 'LostOwnership'
                Reason = "the descriptor's executable identity is inconsistent"
            }
        }
        $processId = [int]$descriptor.process_id
        $expectedStartTime = if ($descriptor.process_start_utc -is [datetime]) {
            [datetime]$descriptor.process_start_utc
        }
        else {
            [datetime]::Parse(
                [string]$descriptor.process_start_utc,
                [Globalization.CultureInfo]::InvariantCulture,
                [Globalization.DateTimeStyles]::RoundtripKind
            )
        }
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($null -eq $process) {
            return [pscustomobject]@{
                Status = 'AlreadyExited'
                Reason = $null
            }
        }
        if (-not [IO.Path]::Equals(
            [IO.Path]::GetFullPath($process.Path),
            [IO.Path]::GetFullPath($Executable)
        )) {
            return [pscustomobject]@{
                Status = 'LostOwnership'
                Reason = "process $processId is not the descriptor's executable"
            }
        }
        $startTimeDeltaSeconds = [math]::Abs((
            $process.StartTime.ToUniversalTime() -
            $expectedStartTime.ToUniversalTime()
        ).TotalSeconds)
        if ($startTimeDeltaSeconds -gt 1) {
            return [pscustomobject]@{
                Status = 'LostOwnership'
                Reason = (
                    "process $processId no longer has the descriptor's start time " +
                    "(delta ${startTimeDeltaSeconds}s)"
                )
            }
        }
        Stop-Process -Id $processId -Force
        if (-not $process.WaitForExit(5000)) {
            return [pscustomobject]@{
                Status = 'StopTimedOut'
                Reason = "owned process $processId did not exit within 5 seconds"
            }
        }
        return [pscustomobject]@{
            Status = 'Stopped'
            Reason = $null
        }
    }
    finally {
        if ($null -ne $process) { $process.Dispose() }
        $ownership.DescriptorHandle.Dispose()
    }
}
