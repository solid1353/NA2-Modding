[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateRange(1, 65535)]
    [int]$PinePort
)

$ErrorActionPreference = 'Stop'
$client = [Net.Sockets.TcpClient]::new()
try {
    $client.ReceiveTimeout = 3000
    $client.SendTimeout = 3000
    $client.Connect('127.0.0.1', $PinePort)
    $stream = $client.GetStream()
    [byte[]]$request = [BitConverter]::GetBytes([uint32]5) + [byte]0x11
    $stream.Write($request, 0, $request.Length)

    [byte[]]$reply = [byte[]]::new(5)
    $received = 0
    while ($received -lt $reply.Length) {
        $count = $stream.Read($reply, $received, $reply.Length - $received)
        if ($count -eq 0) {
            throw 'PCSX2 closed the PINE connection during the screenshot reply.'
        }
        $received += $count
    }
    if ([BitConverter]::ToUInt32($reply, 0) -ne 5 -or $reply[4] -ne 0) {
        throw 'PCSX2 rejected PINE screenshot opcode 0x11.'
    }
}
finally {
    $client.Dispose()
}

Write-Host "[injection_lab] Native screenshot queued through PINE port $PinePort."
