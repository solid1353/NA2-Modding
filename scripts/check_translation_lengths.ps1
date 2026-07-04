param(
    [Parameter(Mandatory = $true)]
    [string]$TablePath,

    [string]$OldColumn = "old",

    [string]$NewColumn = "new",

    [string]$OutPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $TablePath)) {
    throw "Table not found: $TablePath"
}

Add-Type -AssemblyName System.Text.Encoding.CodePages
[Text.Encoding]::RegisterProvider([Text.CodePagesEncodingProvider]::Instance)
$cp932 = [Text.Encoding]::GetEncoding(932)

$ext = [IO.Path]::GetExtension($TablePath).ToLowerInvariant()
$delimiter = if ($ext -eq ".csv") { "," } else { "`t" }

$rows = @(Import-Csv -LiteralPath $TablePath -Delimiter $delimiter)

if ($rows.Count -eq 0) {
    throw "No rows found: $TablePath"
}

$columns = @($rows[0].PSObject.Properties.Name)

if (-not ($columns -contains $OldColumn)) {
    throw "Missing old column '$OldColumn'. Available: $($columns -join ', ')"
}

if (-not ($columns -contains $NewColumn)) {
    throw "Missing new column '$NewColumn'. Available: $($columns -join ', ')"
}

if ([string]::IsNullOrWhiteSpace($OutPath)) {
    $root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    $logDir = Join-Path $root "logs"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutPath = Join-Path $logDir ("translation_length_check_" + $stamp + ".tsv")
}

$result = New-Object System.Collections.Generic.List[object]

for ($i = 0; $i -lt $rows.Count; $i++) {
    $old = [string]$rows[$i].$OldColumn
    $new = [string]$rows[$i].$NewColumn

    $oldBytes = $cp932.GetByteCount($old)
    $newBytes = $cp932.GetByteCount($new)

    $result.Add([pscustomobject]@{
        Row = $i + 1
        OldBytes = $oldBytes
        NewBytes = $newBytes
        Delta = $newBytes - $oldBytes
        Fits = ($newBytes -le $oldBytes)
        Old = $old
        New = $new
    })
}

$result | Export-Csv -LiteralPath $OutPath -Delimiter "`t" -NoTypeInformation -Encoding UTF8

$bad = @($result | Where-Object { -not $_.Fits })

Write-Host "Checked rows: $($result.Count)"
Write-Host "Too long: $($bad.Count)"
Write-Host "Report:"
Write-Host $OutPath

if ($bad.Count -gt 0) {
    Write-Host ""
    Write-Host "First too-long rows:"
    $bad | Select-Object -First 20 Row, OldBytes, NewBytes, Delta, Old, New | Format-Table -AutoSize
}
