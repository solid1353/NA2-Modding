param([string[]]$AnalysisDirs)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
$paths = Get-Na2Paths

if (-not $AnalysisDirs -or $AnalysisDirs.Count -eq 0) {
    $AnalysisDirs = @('NA2', 'NUN3', 'NUN5', 'NUN6', 'shared') | ForEach-Object {
        Join-Path $paths.analysis "disassembly\$_"
    }
}
$disassemblyRoot = [IO.Path]::GetFullPath((Join-Path $paths.analysis 'disassembly'))
$disassemblyPrefix = $disassemblyRoot.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar

foreach ($analysisDir in $AnalysisDirs) {
    $fullPath = [IO.Path]::GetFullPath($analysisDir)
    if (-not $fullPath.StartsWith($disassemblyPrefix, [StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::Equals($fullPath, $disassemblyRoot)) {
        throw "Analysis directory must be one target below @analysis/disassembly: $analysisDir"
    }
    if (-not (Test-Path -LiteralPath $fullPath -PathType Container)) {
        throw "Analysis directory not found: $fullPath"
    }
    $items = @(Get-ChildItem -LiteralPath $fullPath -Force -Recurse)
    foreach ($item in $items) { $item.Attributes = $item.Attributes -bor [IO.FileAttributes]::ReadOnly }
    $root = Get-Item -LiteralPath $fullPath -Force
    $root.Attributes = $root.Attributes -bor [IO.FileAttributes]::ReadOnly
    $notReadOnly = @(@($root) + @(Get-ChildItem -LiteralPath $fullPath -Force -Recurse) |
        Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
    if ($notReadOnly.Count -ne 0) { throw "Some analysis items remain writable below $fullPath" }
    $fileCount = @($items | Where-Object { -not $_.PSIsContainer }).Count
    $directoryCount = @($items | Where-Object { $_.PSIsContainer }).Count + 1
    Write-Host "Read-only analysis tree: $(ConvertTo-Na2ProjectPath -Path $fullPath -Paths $paths)"
    Write-Host "Directories: $directoryCount; files: $fileCount; not read-only: 0"
}

$disassemblyItem = Get-Item -LiteralPath $disassemblyRoot -Force
$disassemblyItem.Attributes = $disassemblyItem.Attributes -bor [IO.FileAttributes]::ReadOnly
$notReadOnly = @(@($disassemblyItem) + @(Get-ChildItem -LiteralPath $disassemblyRoot -Force -Recurse) |
    Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
if ($notReadOnly.Count -ne 0) { throw "Some items remain writable below $disassemblyRoot" }
Write-Host 'Verified complete read-only tree: @analysis/disassembly'
