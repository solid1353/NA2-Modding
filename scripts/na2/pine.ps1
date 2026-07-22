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
    return $buffer
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
    if ($reply.Length -eq 1) { return [byte[]]::new(0) }
    return [byte[]]$reply[1..($reply.Length - 1)]
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
        $statusReply = Invoke-Na2PineRequest -Stream $stream -Payload ([byte[]]@(0x0F))
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
            Version = Get-Na2PineString -Stream $stream -Opcode 0x08
            Title = Get-Na2PineString -Stream $stream -Opcode 0x0B
            Serial = Get-Na2PineString -Stream $stream -Opcode 0x0C
            CRC = (Get-Na2PineString -Stream $stream -Opcode 0x0D).ToUpperInvariant()
            GameVersion = Get-Na2PineString -Stream $stream -Opcode 0x0E
        }
    }
    finally {
        $client.Dispose()
    }
}

function Wait-Na2PineIdentity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][ValidateRange(1, 65535)][int]$Port,
        [Parameter(Mandatory = $true)][string]$Serial,
        [Parameter(Mandatory = $true)][string]$CRC,
        [Parameter(Mandatory = $true)][int]$ProcessId,
        [ValidateRange(1, 300)][int]$TimeoutSeconds = 60
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $lastError = 'PINE did not become ready.'
    do {
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
