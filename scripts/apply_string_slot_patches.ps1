param(
    [Parameter(Mandatory = $true)] [string]$InputPath,
    [Parameter(Mandatory = $true)] [string]$OutputPath,
    [Parameter(Mandatory = $true)] [string]$PatchTable,
    [Parameter(Mandatory = $true)] [string]$LogPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$encoding = [Text.Encoding]::GetEncoding(932)

function Parse-Offset([string]$Value) {
    if ($Value -match '^0x') { return [Convert]::ToInt32($Value, 16) }
    return [int]$Value
}

if (-not (Test-Path -LiteralPath $InputPath)) { throw "Input not found: $InputPath" }
if (-not (Test-Path -LiteralPath $PatchTable)) { throw "Patch table not found: $PatchTable" }

$bytes = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $InputPath).Path)
$patches = Import-Csv -LiteralPath $PatchTable -Delimiter "`t"
$logRows = [System.Collections.Generic.List[object]]::new()

foreach ($patch in $patches) {
    $offset = Parse-Offset $patch.Offset
    $capacity = [int]$patch.CapacityBytes
    $newBytes = $encoding.GetBytes([string]$patch.NewText)
    if ($newBytes.Length -gt $capacity) {
        throw "Patch too long at $($patch.Offset): $($newBytes.Length) > $capacity bytes for '$($patch.NewText)'"
    }
    if ($offset -lt 0 -or ($offset + $capacity) -gt $bytes.Length) {
        throw "Patch outside file at $($patch.Offset) capacity $capacity"
    }

    $oldBytes = [byte[]]::new($capacity)
    [Array]::Copy($bytes, $offset, $oldBytes, 0, $capacity)
    $oldText = $encoding.GetString(($oldBytes | Where-Object { $_ -ne 0 }))

    for ($i = 0; $i -lt $capacity; $i++) { $bytes[$offset + $i] = 0 }
    [Array]::Copy($newBytes, 0, $bytes, $offset, $newBytes.Length)

    $logRows.Add([pscustomobject]@{
        Offset = $patch.Offset
        CapacityBytes = $capacity
        OldText = $oldText
        NewText = $patch.NewText
        NewByteCount = $newBytes.Length
        Reason = $patch.Reason
    })
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LogPath) | Out-Null
[IO.File]::WriteAllBytes($OutputPath, $bytes)
$logRows | Export-Csv -LiteralPath $LogPath -Delimiter "`t" -NoTypeInformation -Encoding UTF8
[pscustomobject]@{ OutputPath = $OutputPath; LogPath = $LogPath; PatchCount = $logRows.Count }
