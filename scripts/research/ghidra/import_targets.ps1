param(
    [ValidateSet('all', 'NA2', 'NUN3', 'NUN5', 'NUN6', 'shared')]
    [string]$Target = 'all',
    [string]$Program,
    [switch]$ReanalyzeExisting,
    [switch]$VerifyOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
. $projectPaths.files.ghidra_runtime

function Resolve-SourceAlias([string]$Alias) {
    return Resolve-Na2ProjectPathAlias -Alias $Alias -ProjectPaths $projectPaths
}

$targets = Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'targets.tsv') -Delimiter "`t"
if ($Target -ne 'all') { $targets = @($targets | Where-Object target -eq $Target) }
if ($Program) { $targets = @($targets | Where-Object program -eq $Program) }
if ($targets.Count -eq 0) { throw 'No matching Ghidra targets.' }
if ($ReanalyzeExisting -and -not $Program) { throw '-ReanalyzeExisting requires -Program.' }
if ($ReanalyzeExisting -and $VerifyOnly) { throw '-ReanalyzeExisting cannot be combined with -VerifyOnly.' }

foreach ($item in $targets) {
    $inputPath = Resolve-SourceAlias $item.source
    if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) {
        throw "Source input missing: $($item.source)"
    }
    $actualHash = (Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash
    if ($actualHash -ne $item.expected_sha256) {
        throw "Source hash mismatch: $($item.source)"
    }
}
if ($VerifyOnly) {
    Write-Host "Verified target inputs:" $targets.Count
    exit 0
}

$runtimeRoot = Join-Path $projectPaths.work 'temp\ghidra_import'
$ghidra = Initialize-GhidraRuntime `
    -RuntimeRoot $runtimeRoot `
    -ToolsRoot $projectPaths.utils
$headless = $ghidra.Headless
$sharedScriptPath = $ghidra.ScriptPath

foreach ($item in $targets) {
    $analysisDirectory = if ($item.target -eq 'shared') { 'shared' } else { $item.target }
    $analysisRoot = Join-Path $projectPaths.analysis "disassembly\$analysisDirectory"
    $projectRoot = Join-Path $analysisRoot 'ghidra'
    $artifactRoot = if ($item.target -eq 'shared') { Join-Path $analysisRoot $item.shared_scope } else { $analysisRoot }
    $summaryPath = Join-Path $artifactRoot "summaries\$($item.program).tsv"
    if ($ReanalyzeExisting) {
        if (-not (Test-Path -LiteralPath $projectRoot -PathType Container)) {
            throw "Ghidra project is missing: $($item.target)"
        }
        $inputPath = Resolve-SourceAlias $item.source
        $loadBase = '-'
        if ($item.format -eq 'mwo3') {
            $stream = [IO.File]::OpenRead($inputPath)
            try {
                $header = New-Object byte[] 12
                [void]$stream.Read($header, 0, $header.Length)
            }
            finally { $stream.Dispose() }
            if ([Text.Encoding]::ASCII.GetString($header, 0, 4) -ne 'MWo3') { throw "Invalid MWo3 input: $($item.source)" }
            $loadBase = '0x{0:X8}' -f [BitConverter]::ToUInt32($header, 8)
        }
        $arguments = @(
            $projectRoot, $item.target, '-process', $item.program,
            '-scriptPath', $sharedScriptPath,
            '-postScript', 'WriteAnalysisSummary.java', $summaryPath, $item.source,
            $item.expected_sha256, $item.format, $loadBase
        )
        & $headless @arguments
        if ($LASTEXITCODE -ne 0) { throw "Ghidra reanalysis failed: $($item.target)/$($item.program)" }
        continue
    }
    if (Test-Path -LiteralPath $summaryPath) {
        Write-Host "Skip existing:" "$($item.target)/$($item.program)"
        continue
    }
    New-Item -ItemType Directory -Force -Path $projectRoot, (Split-Path $summaryPath -Parent) | Out-Null
    $inputPath = Resolve-SourceAlias $item.source
    $arguments = @($projectRoot, $item.target, '-import', $inputPath)
    $loadBase = '-'
    switch ($item.format) {
        'ee_elf' { $arguments += @('-processor', 'r5900:LE:32:default', '-cspec', 'default', '-loader', 'ElfLoader') }
        'iop_elf' { $arguments += @('-processor', 'MIPS:LE:32:default', '-cspec', 'default', '-loader', 'ElfLoader') }
        'mwo3' {
            $stream = [IO.File]::OpenRead($inputPath)
            try {
                $header = New-Object byte[] 20
                [void]$stream.Read($header, 0, $header.Length)
            }
            finally { $stream.Dispose() }
            if ([Text.Encoding]::ASCII.GetString($header, 0, 4) -ne 'MWo3') { throw "Invalid MWo3 input: $($item.source)" }
            $base = [BitConverter]::ToUInt32($header, 8)
            $textLength = [BitConverter]::ToUInt32($header, 12)
            $loadBase = '0x{0:X8}' -f $base
            $entry = '-'
            if ($item.entry_file_offset) {
                $entryOffset = [Convert]::ToInt64($item.entry_file_offset.Substring(2), 16)
                $entry = '0x{0:X8}' -f ($base + $entryOffset - 0x40)
            }
            $arguments += @(
                '-processor', 'r5900:LE:32:default', '-cspec', 'default',
                '-loader', 'BinaryLoader', '-loader-baseAddr', $loadBase,
                '-loader-fileOffset', '0x40', '-loader-length', [string]((Get-Item $inputPath).Length - 0x40),
                '-loader-blockName', 'image', '-scriptPath', $sharedScriptPath,
                '-preScript', 'PrepareMwo3.java', $loadBase, ('0x{0:X8}' -f $textLength), $entry
            )
        }
        default { throw "Unsupported target format: $($item.format)" }
    }
    $arguments += @(
        '-scriptPath', $sharedScriptPath,
        '-postScript', 'WriteAnalysisSummary.java', $summaryPath, $item.source,
        $item.expected_sha256, $item.format, $loadBase
    )
    & $headless @arguments
    if ($LASTEXITCODE -ne 0) { throw "Ghidra import failed: $($item.target)/$($item.program)" }
}
