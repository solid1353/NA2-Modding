param(
    [Parameter(Mandatory = $true)]
    [string]$Name,

    [Parameter(Mandatory = $true)]
    [string]$IsoPath,

    [Parameter(Mandatory = $true)]
    [string]$PnachPath,

    [string]$ExpectedCrc = "",

    [string]$ReleaseDir = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path "releases")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-SafeName {
    param([string]$Value)
    $safe = $Value -replace '[<>:"/\\|?*]+', '_'
    $safe = $safe.Trim()
    if ([string]::IsNullOrWhiteSpace($safe)) {
        throw "Milestone name became empty after sanitizing."
    }
    return $safe
}

function Get-CrcFromPnachName {
    param([string]$Path)

    $name = [IO.Path]::GetFileName($Path)
    if ($name -match '^SLPS-25837_([0-9A-Fa-f]{8})\.pnach$') {
        return $Matches[1].ToUpperInvariant()
    }

    return $null
}

if (-not (Test-Path -LiteralPath $IsoPath)) {
    throw "ISO not found: $IsoPath"
}

if (-not (Test-Path -LiteralPath $PnachPath)) {
    throw "PNACH not found: $PnachPath"
}

if (-not (Test-Path -LiteralPath $ReleaseDir)) {
    throw "Release dir not found: $ReleaseDir"
}

$safeName = Get-SafeName -Value $Name
$targetDir = Join-Path $ReleaseDir $safeName

if (Test-Path -LiteralPath $targetDir) {
    throw "Release target already exists. Stop and inspect manually: $targetDir"
}

$pnachCrc = Get-CrcFromPnachName -Path $PnachPath
if (-not $pnachCrc) {
    throw "PNACH filename does not contain expected SLPS-25837 CRC suffix: $PnachPath"
}

if (-not [string]::IsNullOrWhiteSpace($ExpectedCrc)) {
    $expected = $ExpectedCrc.ToUpperInvariant()
    if ($expected -ne $pnachCrc) {
        throw "Expected CRC $expected does not match PNACH filename CRC $pnachCrc."
    }
}
else {
    Write-Warning "No ExpectedCrc provided. Release will record PNACH filename CRC only; ISO/ELF PCSX2 CRC must be verified separately."
}

New-Item -ItemType Directory -Path $targetDir | Out-Null

$isoOut = Join-Path $targetDir ([IO.Path]::GetFileName($IsoPath))
$pnachOut = Join-Path $targetDir ([IO.Path]::GetFileName($PnachPath))
$manifestOut = Join-Path $targetDir "manifest.tsv"

foreach ($path in @($isoOut, $pnachOut, $manifestOut)) {
    if (Test-Path -LiteralPath $path) {
        throw "Unexpected existing release output. Stop and inspect manually: $path"
    }
}

Copy-Item -LiteralPath $IsoPath -Destination $isoOut
Copy-Item -LiteralPath $PnachPath -Destination $pnachOut

$isoHash = Get-FileHash -LiteralPath $isoOut -Algorithm SHA256
$pnachHash = Get-FileHash -LiteralPath $pnachOut -Algorithm SHA256

$rows = @(
    [pscustomobject]@{
        Item = "ISO"
        Path = [IO.Path]::GetFileName($isoOut)
        Size = (Get-Item -LiteralPath $isoOut).Length
        SHA256 = $isoHash.Hash
        Pcsx2Crc = if ([string]::IsNullOrWhiteSpace($ExpectedCrc)) { "UNVERIFIED" } else { $ExpectedCrc.ToUpperInvariant() }
    },
    [pscustomobject]@{
        Item = "PNACH"
        Path = [IO.Path]::GetFileName($pnachOut)
        Size = (Get-Item -LiteralPath $pnachOut).Length
        SHA256 = $pnachHash.Hash
        Pcsx2Crc = $pnachCrc
    }
)

$rows | Export-Csv -LiteralPath $manifestOut -Delimiter "`t" -NoTypeInformation -Encoding UTF8

Write-Host "Created milestone release:"
Write-Host $targetDir
Write-Host "PNACH CRC suffix: $pnachCrc"

if ([string]::IsNullOrWhiteSpace($ExpectedCrc)) {
    Write-Warning "ISO/ELF PCSX2 CRC was not verified by this script."
}
