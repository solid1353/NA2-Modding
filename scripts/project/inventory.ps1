param(
    [int]$MaxHashSizeMB = 2048
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$Root = $projectPaths.repository

if (-not (Test-Path -LiteralPath $Root)) {
    throw "Root not found: $Root"
}

$logDir = Join-Path $projectPaths.logs "inventory"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$report = Join-Path $logDir ("inventory_" + $stamp + ".md")

$keyExts = @(
    ".cvm", ".afs", ".elf", ".bin", ".ccs", ".tm2", ".pss",
    ".iso", ".pnach", ".ini", ".zip", ".exe", ".ps1", ".tsv", ".csv", ".md"
)

$keyNames = @(
    "SLPS_258.37", "BTL.BIN", "ETC.bin", "ADV.bin", "DATA.CVM",
    "logo.ccs", "LOGO_C.PSS", "NOTICE.PSS", "OPENING.PSS"
)

function Get-RelativePath {
    param([string]$Path)

    $rootFull = [IO.Path]::GetFullPath($Root)
    $pathFull = [IO.Path]::GetFullPath($Path)

    if (-not $rootFull.EndsWith([IO.Path]::DirectorySeparatorChar)) {
        $rootFull = $rootFull + [IO.Path]::DirectorySeparatorChar
    }

    if ($pathFull.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) {
        return $pathFull.Substring($rootFull.Length)
    }

    return $Path
}

function Get-Sha256OrSkip {
    param([System.IO.FileInfo]$File)

    $maxBytes = [int64]$MaxHashSizeMB * 1024 * 1024

    if ($File.Length -gt $maxBytes) {
        return ("SKIPPED_OVER_{0}MB" -f $MaxHashSizeMB)
    }

    try {
        return (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash
    }
    catch {
        return ("HASH_ERROR: {0}" -f $_.Exception.Message)
    }
}

$allFiles = @(
    Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue
)

$keyFiles = @(
    $allFiles |
        Where-Object {
            ($keyNames -contains $_.Name) -or
            ($keyExts -contains $_.Extension.ToLowerInvariant()) -or
            ($_.Name -match "^DA.*\.PSS$")
        } |
        Sort-Object FullName
)

$toolHits = New-Object System.Collections.Generic.List[object]

foreach ($name in @("cvm_tool.exe", "7z.exe", "7za.exe", "isoinfo.exe", "vgmstream-cli.exe", "pcsx2-qt.exe")) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue

    if ($cmd) {
        $toolHits.Add([pscustomobject]@{
            Tool = $name
            Source = "PATH"
            Path = $cmd.Source
        })
    }

    $localHits = @(
        Get-ChildItem -LiteralPath $Root -Recurse -File -Filter $name -ErrorAction SilentlyContinue
    )

    foreach ($hit in $localHits) {
        $toolHits.Add([pscustomobject]@{
            Tool = $name
            Source = "workspace"
            Path = $hit.FullName
        })
    }
}

$lines = New-Object System.Collections.Generic.List[string]

$lines.Add("# Inventory")
$lines.Add("")
$lines.Add(("Root: {0}" -f $Root))
$lines.Add(("Timestamp: {0}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss")))
$lines.Add(("Files scanned: {0}" -f $allFiles.Count))
$lines.Add(("Key files: {0}" -f $keyFiles.Count))
$lines.Add(("Max hash size: {0}MB" -f $MaxHashSizeMB))
$lines.Add("")

$lines.Add("## Detected tools")
$lines.Add("")

$uniqueTools = @($toolHits | Sort-Object Tool, Source, Path -Unique)

if ($uniqueTools.Count -eq 0) {
    $lines.Add("No known tools found.")
}
else {
    $lines.Add("| Tool | Source | Path |")
    $lines.Add("|---|---|---|")

    foreach ($tool in $uniqueTools) {
        $lines.Add(("| {0} | {1} | {2} |" -f $tool.Tool, $tool.Source, $tool.Path))
    }
}

$lines.Add("")
$lines.Add("## Key files")
$lines.Add("")
$lines.Add("| Relative path | Size | SHA256 |")
$lines.Add("|---|---:|---|")

foreach ($file in $keyFiles) {
    $relative = Get-RelativePath -Path $file.FullName
    $hash = Get-Sha256OrSkip -File $file
    $lines.Add(("| {0} | {1} | {2} |" -f $relative, $file.Length, $hash))
}

$lines.Add("")
$lines.Add("No binaries were modified.")

$lines | Set-Content -LiteralPath $report -Encoding UTF8

Write-Host "Inventory report:"
Write-Host $report
