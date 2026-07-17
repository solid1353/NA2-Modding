param(
    [string]$SourceDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot 'project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
if ([string]::IsNullOrWhiteSpace($SourceDir)) {
    $SourceDir = $projectPaths.source
}

if (-not (Test-Path -LiteralPath $SourceDir)) {
    throw "Original dir not found: $SourceDir"
}

$SourceDir = (Resolve-Path -LiteralPath $SourceDir).Path

$items = @(
    Get-ChildItem -Force -Recurse -LiteralPath $SourceDir
)

foreach ($item in $items) {
    $item.Attributes = $item.Attributes -bor [IO.FileAttributes]::ReadOnly
}

$rootItem = Get-Item -Force -LiteralPath $SourceDir
$rootItem.Attributes = $rootItem.Attributes -bor [IO.FileAttributes]::ReadOnly

$files = @($items | Where-Object { -not $_.PSIsContainer })
$dirs = @($items | Where-Object { $_.PSIsContainer })
$notReadOnly = @(
    Get-ChildItem -Force -Recurse -LiteralPath $SourceDir |
        Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 }
)

Write-Host "Read-only applied:"
Write-Host $SourceDir
Write-Host "Directories:" $dirs.Count
Write-Host "Files:" $files.Count
Write-Host "Not read-only:" $notReadOnly.Count

if ($notReadOnly.Count -gt 0) {
    $notReadOnly | Select-Object FullName, Attributes | Format-Table -AutoSize
    throw "Some source files/folders are not read-only."
}
