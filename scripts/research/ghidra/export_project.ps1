param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('NA2', 'NUN3', 'NUN5', 'NUN6', 'shared')]
    [string]$Target,
    [string]$Program
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\lib\paths.ps1')
$paths = Get-Na2Paths
. $paths.files.ghidra_runtime

$analysisDirectory = if ($Target -eq 'shared') { 'shared' } else { $Target }
$analysisRoot = Join-Path $paths.analysis "disassembly\$analysisDirectory"
$projectRoot = Join-Path $analysisRoot 'ghidra'
$runtimeRoot = Join-Path $paths.work "temp\ghidra_export\$Target"
$ghidra = Initialize-GhidraRuntime `
    -RuntimeRoot $runtimeRoot `
    -ToolsRoot $paths.utils
$headless = $ghidra.Headless
$sharedScriptPath = $ghidra.ScriptPath

try {
    if ($Target -eq 'shared') {
        $targets = @(Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'targets.tsv') -Delimiter "`t" |
            Where-Object target -eq 'shared')
        if ($Program) { $targets = @($targets | Where-Object program -eq $Program) }
        if ($targets.Count -eq 0) { throw 'No matching shared Ghidra targets.' }
        foreach ($item in $targets) {
            $exportRoot = Join-Path $analysisRoot "$($item.shared_scope)\exports"
            New-Item -ItemType Directory -Force -Path $exportRoot | Out-Null
            $arguments = @(
                $projectRoot, $Target,
                '-process', $item.program, '-readOnly', '-noanalysis',
                '-scriptPath', $sharedScriptPath,
                '-postScript', 'ExportAnalysis.java', $exportRoot
            )
            & $headless @arguments
            if ($LASTEXITCODE -ne 0) { throw "Ghidra export failed: shared/$($item.program)" }
        }
    }
    else {
        $exportRoot = Join-Path $analysisRoot 'exports'
        New-Item -ItemType Directory -Force -Path $exportRoot | Out-Null
        $arguments = @($projectRoot, $Target, '-process')
        if ($Program) { $arguments += $Program }
        $arguments += @(
            '-readOnly', '-noanalysis',
            '-scriptPath', $sharedScriptPath,
            '-postScript', 'ExportAnalysis.java', $exportRoot
        )
        & $headless @arguments
        if ($LASTEXITCODE -ne 0) { throw "Ghidra export failed with exit code $LASTEXITCODE" }
    }
    & (Join-Path $PSScriptRoot 'build_manifest.ps1') -Target $Target
    Set-Content -LiteralPath (Join-Path $runtimeRoot 'worker.complete') -Value 'complete' -Encoding utf8
}
catch {
    Set-Content -LiteralPath (Join-Path $runtimeRoot 'worker.failed') -Value $_.Exception.Message -Encoding utf8
    throw
}
