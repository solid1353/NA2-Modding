[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'pine.ps1')

if (-not ('Na2ScriptedDuplexStream' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.IO;

public sealed class Na2ScriptedDuplexStream : Stream {
    private readonly Queue<byte> input = new Queue<byte>();
    private readonly MemoryStream output = new MemoryStream();

    public void Enqueue(byte[] data) {
        foreach (byte value in data)
            input.Enqueue(value);
    }

    public byte[] Written {
        get { return output.ToArray(); }
    }

    public override bool CanRead { get { return true; } }
    public override bool CanSeek { get { return false; } }
    public override bool CanWrite { get { return true; } }
    public override long Length { get { throw new NotSupportedException(); } }
    public override long Position {
        get { throw new NotSupportedException(); }
        set { throw new NotSupportedException(); }
    }

    public override void Flush() { }

    public override int Read(byte[] buffer, int offset, int count) {
        int read = 0;
        while (read < count && input.Count > 0) {
            buffer[offset + read] = input.Dequeue();
            read++;
        }
        return read;
    }

    public override void Write(byte[] buffer, int offset, int count) {
        output.Write(buffer, offset, count);
    }

    public override long Seek(long offset, SeekOrigin origin) {
        throw new NotSupportedException();
    }

    public override void SetLength(long value) {
        throw new NotSupportedException();
    }
}
'@
}

function Assert-Na2PineTest {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

function Add-Na2PineTestReply {
    param(
        [Parameter(Mandatory = $true)][Na2ScriptedDuplexStream]$Stream,
        [byte[]]$Data = [byte[]]::new(0)
    )

    $size = [uint32](5 + $Data.Length)
    $Stream.Enqueue([BitConverter]::GetBytes($size))
    $Stream.Enqueue([byte[]]@(0))
    if ($Data.Length -gt 0) {
        $Stream.Enqueue($Data)
    }
}

$expected = [byte[]]@(0x10, 0x20, 0x30, 0x40)
$replacement = [byte[]]@(0xAA, 0xBB, 0xCC, 0xDD)
$stream = [Na2ScriptedDuplexStream]::new()
Add-Na2PineTestReply -Stream $stream -Data $expected
Add-Na2PineTestReply -Stream $stream
Add-Na2PineTestReply -Stream $stream -Data $replacement
$patched = Invoke-Na2PineGuardedMemoryPatch `
    -Stream $stream `
    -Address 0x00123450 `
    -Expected $expected `
    -Replacement $replacement
Assert-Na2PineTest `
    -Condition (
        $patched.ReadbackVerified -and
        $patched.Expected -ceq '10203040' -and
        $patched.Replacement -ceq 'AABBCCDD'
    ) `
    -Message 'The exact-byte guarded PINE patch did not verify its readback.'

$mismatchStream = [Na2ScriptedDuplexStream]::new()
Add-Na2PineTestReply `
    -Stream $mismatchStream `
    -Data ([byte[]]@(0x10, 0x20, 0x31, 0x40))
$guardRejected = $false
try {
    Invoke-Na2PineGuardedMemoryPatch `
        -Stream $mismatchStream `
        -Address 0x00123450 `
        -Expected $expected `
        -Replacement $replacement | Out-Null
}
catch {
    $guardRejected = $_.Exception.Message -match 'Guarded PINE patch rejected'
}
Assert-Na2PineTest `
    -Condition $guardRejected `
    -Message 'A mismatched exact-byte PINE guard was not rejected.'

$stateStream = [Na2ScriptedDuplexStream]::new()
Add-Na2PineTestReply -Stream $stateStream
Invoke-Na2PineStateCommand -Stream $stateStream -Command Load -Slot 7
Assert-Na2PineTest `
    -Condition (
        [Convert]::ToHexString($stateStream.Written) -ceq '060000000A07'
    ) `
    -Message 'The maintained PINE load-state command packet is incorrect.'

Write-Host 'NA2 PINE guarded-memory tests passed.' -ForegroundColor Green
