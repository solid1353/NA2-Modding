Set-StrictMode -Version Latest

function Read-Na2PineExact {
    param(
        [Parameter(Mandatory = $true)][IO.Stream]$Stream,
        [Parameter(Mandatory = $true)][int]$Size
    )

    $buffer = [byte[]]::new($Size)
    $offset = 0
    while ($offset -lt $Size) {
        $read = $Stream.Read($buffer, $offset, $Size - $offset)
        if ($read -le 0) { throw 'PINE connection closed during a reply.' }
        $offset += $read
    }
    return ,$buffer
}

function Invoke-Na2PineRequest {
    param(
        [Parameter(Mandatory = $true)][IO.Stream]$Stream,
        [Parameter(Mandatory = $true)][byte[]]$Payload
    )

    $header = [BitConverter]::GetBytes([uint32]($Payload.Length + 4))
    $Stream.Write($header, 0, $header.Length)
    $Stream.Write($Payload, 0, $Payload.Length)
    $Stream.Flush()

    $replySize = [BitConverter]::ToUInt32((Read-Na2PineExact -Stream $Stream -Size 4), 0)
    if ($replySize -lt 5 -or $replySize -gt 450000) {
        throw "Invalid PINE reply size: $replySize"
    }
    $reply = Read-Na2PineExact -Stream $Stream -Size ([int]$replySize - 4)
    if ($reply[0] -ne 0) { throw 'PCSX2 rejected the PINE request.' }
    if ($reply.Length -eq 1) { return ,([byte[]]::new(0)) }
    return ,([byte[]]$reply[1..($reply.Length - 1)])
}

function Get-Na2PineString {
    param(
        [Parameter(Mandatory = $true)][IO.Stream]$Stream,
        [Parameter(Mandatory = $true)][byte]$Opcode
    )

    $reply = Invoke-Na2PineRequest -Stream $Stream -Payload ([byte[]]@($Opcode))
    if ($reply.Length -lt 5) { throw 'PINE string reply is too short.' }
    $size = [BitConverter]::ToUInt32($reply, 0)
    if ($size -lt 1 -or $reply.Length -ne $size + 4 -or $reply[$reply.Length - 1] -ne 0) {
        throw 'Malformed PINE string reply.'
    }
    return [Text.Encoding]::UTF8.GetString($reply, 4, [int]$size - 1)
}

function Get-Na2PineIdentity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][ValidateRange(1, 65535)][int]$Port,
        [ValidateRange(100, 10000)][int]$TimeoutMilliseconds = 1000
    )

    $client = [Net.Sockets.TcpClient]::new()
    try {
        $connect = $client.ConnectAsync([Net.IPAddress]::Loopback, $Port)
        if (-not $connect.Wait($TimeoutMilliseconds)) {
            throw "Timed out connecting to PINE port $Port."
        }
        $stream = $client.GetStream()
        $stream.ReadTimeout = $TimeoutMilliseconds
        $stream.WriteTimeout = $TimeoutMilliseconds
        Get-Na2PineIdentityFromStream -Stream $stream
    }
    finally {
        $client.Dispose()
    }
}

function Get-Na2PineIdentityFromStream {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][IO.Stream]$Stream)

    $statusReply = Invoke-Na2PineRequest -Stream $Stream -Payload ([byte[]]@(0x0F))
    if ($statusReply.Length -ne 4) { throw 'Malformed PINE status reply.' }
    $statusValue = [BitConverter]::ToUInt32($statusReply, 0)
    $status = switch ($statusValue) {
        0 { 'running' }
        1 { 'paused' }
        2 { 'shutdown' }
        default { throw "Unknown PINE status value: $statusValue" }
    }
    [pscustomobject]@{
        Status = $status
        Version = Get-Na2PineString -Stream $Stream -Opcode 0x08
        Title = Get-Na2PineString -Stream $Stream -Opcode 0x0B
        Serial = Get-Na2PineString -Stream $Stream -Opcode 0x0C
        CRC = (Get-Na2PineString -Stream $Stream -Opcode 0x0D).ToUpperInvariant()
        GameVersion = Get-Na2PineString -Stream $Stream -Opcode 0x0E
    }
}

function Invoke-Na2PineOwnedSession {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][ValidateRange(1, 65535)][int]$Port,
        [Parameter(Mandatory = $true)][string]$Serial,
        [Parameter(Mandatory = $true)][string]$CRC,
        [Parameter(Mandatory = $true)]
        [ValidateSet(
            'Identity',
            'LoadState',
            'SaveState',
            'CaptureState',
            'ReadMemory',
            'PatchMemory'
        )]
        [string]$Operation,
        [ValidateRange(0, 99)][int]$Slot = 0,
        [uint32]$Address = 0,
        [byte[]]$Expected,
        [byte[]]$Replacement,
        [ValidateRange(100, 10000)][int]$TimeoutMilliseconds = 3000
    )

    $client = [Net.Sockets.TcpClient]::new()
    $actionStarted = $false
    try {
        $connect = $client.ConnectAsync([Net.IPAddress]::Loopback, $Port)
        if (-not $connect.Wait($TimeoutMilliseconds)) {
            throw "Timed out connecting to the owned PINE port $Port."
        }
        $stream = $client.GetStream()
        $stream.ReadTimeout = $TimeoutMilliseconds
        $stream.WriteTimeout = $TimeoutMilliseconds
        $identity = Get-Na2PineIdentityFromStream -Stream $stream
        if ($identity.Status -eq 'shutdown' -or
            $identity.Serial -cne $Serial -or
            $identity.CRC -cne $CRC.ToUpperInvariant()) {
            throw (
                "Owned PINE identity mismatch on port ${Port}: " +
                "$($identity.Serial)/$($identity.CRC), expected " +
                "$Serial/$($CRC.ToUpperInvariant())."
            )
        }
        $actionStarted = $true
        return Invoke-Na2PineControlledAction `
            -Stream $stream `
            -Identity $identity `
            -Operation $Operation `
            -Slot $Slot `
            -Address $Address `
            -Expected $Expected `
            -Replacement $Replacement
    }
    catch {
        if (-not $actionStarted) {
            $lost = [InvalidOperationException]::new(
                "Owned PINE validation failed: $($_.Exception.Message)",
                $_.Exception
            )
            $lost.Data['Na2OwnershipLost'] = $true
            throw $lost
        }
        throw
    }
    finally {
        $client.Dispose()
    }
}

function Invoke-Na2PineControlledAction {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][IO.Stream]$Stream,
        [Parameter(Mandatory = $true)][psobject]$Identity,
        [Parameter(Mandatory = $true)]
        [ValidateSet(
            'Identity',
            'LoadState',
            'SaveState',
            'CaptureState',
            'ReadMemory',
            'PatchMemory'
        )]
        [string]$Operation,
        [ValidateRange(0, 99)][int]$Slot = 0,
        [uint32]$Address = 0,
        [byte[]]$Expected,
        [byte[]]$Replacement
    )

    switch ($Operation) {
        'Identity' {
            return $Identity
        }
        'LoadState' {
            Invoke-Na2PineStateCommand `
                -Stream $Stream `
                -Command Load `
                -Slot $Slot
            return
        }
        { $_ -in @('SaveState', 'CaptureState') } {
            Invoke-Na2PineStateCommand `
                -Stream $Stream `
                -Command Save `
                -Slot $Slot
            return
        }
        'ReadMemory' {
            if ($null -eq $Expected -or $Expected.Length -eq 0) {
                throw 'ReadMemory requires a non-empty -Expected byte array.'
            }
            $live = Read-Na2PineMemoryRange `
                -Stream $Stream `
                -Address $Address `
                -Length $Expected.Length
            if (-not (Test-Na2ByteArrayEquality -Left $live -Right $Expected)) {
                throw (
                    "Guarded PINE read rejected at 0x$($Address.ToString('X8')): " +
                    "live $([Convert]::ToHexString($live)) != expected " +
                    "$([Convert]::ToHexString($Expected))."
                )
            }
            return $live
        }
        'PatchMemory' {
            if ($null -eq $Expected -or $null -eq $Replacement) {
                throw 'PatchMemory requires -Expected and -Replacement byte arrays.'
            }
            return Invoke-Na2PineGuardedMemoryPatch `
                -Stream $Stream `
                -Address $Address `
                -Expected $Expected `
                -Replacement $Replacement
        }
    }
}

function Invoke-Na2PineStateCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][IO.Stream]$Stream,
        [Parameter(Mandatory = $true)][ValidateSet('Save', 'Load')][string]$Command,
        [Parameter(Mandatory = $true)][ValidateRange(0, 99)][int]$Slot
    )

    $opcode = if ($Command -ceq 'Save') { 0x09 } else { 0x0A }
    $reply = Invoke-Na2PineRequest `
        -Stream $Stream `
        -Payload ([byte[]]@($opcode, $Slot))
    if ($reply.Length -ne 0) {
        throw "Unexpected data in the PINE $Command-state reply."
    }
}

function Read-Na2PineMemoryValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][IO.Stream]$Stream,
        [Parameter(Mandatory = $true)][uint32]$Address,
        [Parameter(Mandatory = $true)][ValidateSet(8, 16, 32, 64)][int]$Width
    )

    $opcode = switch ($Width) {
        8 { 0x00 }
        16 { 0x01 }
        32 { 0x02 }
        64 { 0x03 }
    }
    $payload = [Collections.Generic.List[byte]]::new()
    $payload.Add([byte]$opcode)
    $payload.AddRange([BitConverter]::GetBytes($Address))
    $reply = Invoke-Na2PineRequest -Stream $Stream -Payload $payload.ToArray()
    $expectedSize = [int]($Width / 8)
    if ($reply.Length -ne $expectedSize) {
        throw "PINE Read$Width returned $($reply.Length) bytes, expected $expectedSize."
    }
    switch ($Width) {
        8 { return [uint64]$reply[0] }
        16 { return [uint64][BitConverter]::ToUInt16($reply, 0) }
        32 { return [uint64][BitConverter]::ToUInt32($reply, 0) }
        64 { return [BitConverter]::ToUInt64($reply, 0) }
    }
}

function Get-Na2PineMemoryChunks {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][uint32]$Address,
        [Parameter(Mandatory = $true)][ValidateRange(1, 1048576)][int]$Length
    )

    $end = [uint64]$Address + [uint64]$Length
    if ($end -gt 0x100000000) {
        throw 'PINE memory range exceeds the 32-bit address space.'
    }
    $cursor = 0
    while ($cursor -lt $Length) {
        $remaining = $Length - $cursor
        $width = if ($remaining -ge 8) {
            64
        }
        elseif ($remaining -ge 4) {
            32
        }
        elseif ($remaining -ge 2) {
            16
        }
        else {
            8
        }
        $size = [int]($width / 8)
        [pscustomobject]@{
            Address = [uint32]([uint64]$Address + [uint64]$cursor)
            Width = $width
            Offset = $cursor
            Size = $size
        }
        $cursor += $size
    }
}

function Read-Na2PineMemoryRange {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][IO.Stream]$Stream,
        [Parameter(Mandatory = $true)][uint32]$Address,
        [Parameter(Mandatory = $true)][ValidateRange(1, 1048576)][int]$Length
    )

    $result = [Collections.Generic.List[byte]]::new($Length)
    foreach ($chunk in Get-Na2PineMemoryChunks -Address $Address -Length $Length) {
        $value = Read-Na2PineMemoryValue `
            -Stream $Stream `
            -Address $chunk.Address `
            -Width $chunk.Width
        $bytes = [BitConverter]::GetBytes([uint64]$value)
        for ($index = 0; $index -lt $chunk.Size; $index++) {
            $result.Add($bytes[$index])
        }
    }
    return ,$result.ToArray()
}

function Write-Na2PineMemoryRange {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][IO.Stream]$Stream,
        [Parameter(Mandatory = $true)][uint32]$Address,
        [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][byte[]]$Data
    )

    foreach ($chunk in Get-Na2PineMemoryChunks -Address $Address -Length $Data.Length) {
        $opcode = switch ($chunk.Width) {
            8 { 0x04 }
            16 { 0x05 }
            32 { 0x06 }
            64 { 0x07 }
        }
        $payload = [Collections.Generic.List[byte]]::new()
        $payload.Add([byte]$opcode)
        $payload.AddRange([BitConverter]::GetBytes($chunk.Address))
        for ($index = 0; $index -lt $chunk.Size; $index++) {
            $payload.Add($Data[$chunk.Offset + $index])
        }
        $reply = Invoke-Na2PineRequest -Stream $Stream -Payload $payload.ToArray()
        if ($reply.Length -ne 0) {
            throw "Unexpected data in the PINE Write$($chunk.Width) reply."
        }
    }
}

function Test-Na2ByteArrayEquality {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][byte[]]$Left,
        [Parameter(Mandatory = $true)][byte[]]$Right
    )

    if ($Left.Length -ne $Right.Length) { return $false }
    for ($index = 0; $index -lt $Left.Length; $index++) {
        if ($Left[$index] -ne $Right[$index]) { return $false }
    }
    return $true
}

function Invoke-Na2PineGuardedMemoryPatch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][IO.Stream]$Stream,
        [Parameter(Mandatory = $true)][uint32]$Address,
        [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][byte[]]$Expected,
        [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][byte[]]$Replacement
    )

    if ($Expected.Length -ne $Replacement.Length) {
        throw 'Expected and replacement memory ranges must have identical lengths.'
    }
    $current = Read-Na2PineMemoryRange `
        -Stream $Stream `
        -Address $Address `
        -Length $Expected.Length
    if (-not (Test-Na2ByteArrayEquality -Left $current -Right $Expected)) {
        $mismatch = 0
        while ($mismatch -lt $Expected.Length -and
            $current[$mismatch] -eq $Expected[$mismatch]) {
            $mismatch += 1
        }
        throw (
            "Guarded PINE patch rejected at 0x$(([uint64]$Address + $mismatch).ToString('X8')): " +
            "live $($current[$mismatch].ToString('X2')) != expected " +
            "$($Expected[$mismatch].ToString('X2'))."
        )
    }

    try {
        Write-Na2PineMemoryRange `
            -Stream $Stream `
            -Address $Address `
            -Data $Replacement
        $verified = Read-Na2PineMemoryRange `
            -Stream $Stream `
            -Address $Address `
            -Length $Replacement.Length
        if (-not (Test-Na2ByteArrayEquality -Left $verified -Right $Replacement)) {
            throw 'Guarded PINE patch readback did not match the replacement bytes.'
        }
    }
    catch {
        try {
            Write-Na2PineMemoryRange `
                -Stream $Stream `
                -Address $Address `
                -Data $Expected
            $rolledBack = Test-Na2ByteArrayEquality `
                -Left (Read-Na2PineMemoryRange `
                    -Stream $Stream `
                    -Address $Address `
                    -Length $Expected.Length) `
                -Right $Expected
        }
        catch {
            $rolledBack = $false
        }
        $rollback = if ($rolledBack) { 'runtime bytes restored' } else { 'runtime rollback failed' }
        throw "Guarded PINE patch failed; ${rollback}: $($_.Exception.Message)"
    }

    [pscustomobject]@{
        Address = ('0x{0:X8}' -f $Address)
        Length = $Replacement.Length
        Expected = [Convert]::ToHexString($Expected)
        Replacement = [Convert]::ToHexString($Replacement)
        ReadbackVerified = $true
    }
}

function Wait-Na2PineIdentity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][ValidateRange(1, 65535)][int]$Port,
        [Parameter(Mandatory = $true)][string]$Serial,
        [Parameter(Mandatory = $true)][string]$CRC,
        [Parameter(Mandatory = $true)][int]$ProcessId,
        [scriptblock]$OwnershipValidator,
        [ValidateRange(1, 300)][int]$TimeoutSeconds = 60
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $lastError = 'PINE did not become ready.'
    do {
        if ($null -ne $OwnershipValidator) {
            $ownership = & $OwnershipValidator
            if ($null -eq $ownership -or -not $ownership.Valid) {
                $reason = if ($null -ne $ownership) {
                    [string]$ownership.Reason
                }
                else {
                    'the ownership validator returned no result'
                }
                throw "PCSX2 ownership lost while waiting for PINE: $reason."
            }
        }
        $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($null -eq $process) { throw "PCSX2 process $ProcessId exited before PINE became ready." }
        try {
            $identity = Get-Na2PineIdentity -Port $Port
            if ($identity.Status -ne 'shutdown' -and
                $identity.Serial -ceq $Serial -and
                $identity.CRC -ceq $CRC.ToUpperInvariant()) {
                return $identity
            }
            $lastError = (
                "PINE identity mismatch on port ${Port}: " +
                "$($identity.Serial)/$($identity.CRC), expected $Serial/$($CRC.ToUpperInvariant())."
            )
        }
        catch {
            $lastError = $_.Exception.Message
        }
        Start-Sleep -Milliseconds 200
    } while ([DateTime]::UtcNow -lt $deadline)

    throw "PCSX2 did not load the expected game within $TimeoutSeconds seconds: $lastError"
}
