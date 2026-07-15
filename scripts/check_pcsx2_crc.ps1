param(
    [string]$LogPath = (Join-Path (Split-Path -Parent $PSScriptRoot) 'pcsx2\logs\emulog.txt'),
    [string]$PnachPath = "",
    [string]$Serial = "SLPS-25837"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-LatestGameCrcFromLog {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Log not found: $Path"
    }

    $matches = @(
        Select-String `
            -LiteralPath $Path `
            -Pattern 'ELF Loading:.*Game CRC\s*=\s*([0-9A-Fa-f]{8})' `
            -AllMatches
    )

    $last = $matches |
        ForEach-Object { $_.Matches } |
        Select-Object -Last 1

    if ($null -eq $last) {
        return $null
    }

    return $last.Groups[1].Value.ToUpperInvariant()
}

function Get-CrcFromPnachName {
    param(
        [string]$Path,
        [string]$Serial
    )

    $name = [IO.Path]::GetFileName($Path)
    $pattern = "^{0}_([0-9A-Fa-f]{{8}})\.pnach$" -f [regex]::Escape($Serial)

    if ($name -match $pattern) {
        return $Matches[1].ToUpperInvariant()
    }

    return $null
}

$logCrc = Get-LatestGameCrcFromLog -Path $LogPath

Write-Host "PCSX2 log:"
Write-Host $LogPath

if ($logCrc) {
    Write-Host "Latest Game CRC from boot log: $logCrc"
}
else {
    Write-Warning "No boot Game CRC found in log."
}

if (-not [string]::IsNullOrWhiteSpace($PnachPath)) {
    if (-not (Test-Path -LiteralPath $PnachPath)) {
        throw "PNACH not found: $PnachPath"
    }

    $pnachCrc = Get-CrcFromPnachName -Path $PnachPath -Serial $Serial

    Write-Host ""
    Write-Host "PNACH:"
    Write-Host $PnachPath

    if ($pnachCrc) {
        Write-Host "CRC from PNACH filename: $pnachCrc"
    }
    else {
        Write-Warning "Could not parse CRC from PNACH filename."
    }

    if ($logCrc -and $pnachCrc) {
        if ($logCrc -eq $pnachCrc) {
            Write-Host "OK: PNACH filename matches latest logged Game CRC."
        }
        else {
            Write-Warning "MISMATCH: PNACH filename CRC does not match latest logged Game CRC."
        }
    }
}
