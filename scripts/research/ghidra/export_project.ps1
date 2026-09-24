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
$analysisRoot = Join-Path $paths.disassembly $analysisDirectory
$projectRoot = Join-Path $analysisRoot 'ghidra'
if ([string]::IsNullOrWhiteSpace($env:NA228_TASK_WORK_ROOT)) {
    throw 'NA228_TASK_WORK_ROOT must name the current chat work directory.'
}
. (Join-Path $PSScriptRoot '..\..\na228\task_paths.ps1')
$taskContext = Get-Na2TaskContext `
    -TaskRoot $env:NA228_TASK_WORK_ROOT `
    -Paths $paths
$tempRoot = Join-Path $taskContext.Root 'temp'
$runtimeRoot = Join-Path $tempRoot (
    "ghidra_export_$Target-" + [Guid]::NewGuid().ToString('N')
)
$runtimeEnvironment = @{}
foreach ($name in @(
    'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'JAVA_HOME', 'PATH',
    'GHIDRA_HEADLESS_MAXMEM'
)) {
    $runtimeEnvironment[$name] = [Environment]::GetEnvironmentVariable(
        $name, 'Process'
    )
}

try {
    $ghidra = Initialize-GhidraRuntime `
        -RuntimeRoot $runtimeRoot `
        -ToolsRoot $paths.utils
    $headless = $ghidra.Headless
    $sharedScriptPath = $ghidra.ScriptPath

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
}
finally {
    foreach ($name in $runtimeEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable(
            $name, $runtimeEnvironment[$name], 'Process'
        )
    }
    if (Test-Path -LiteralPath $runtimeRoot -PathType Container) {
        Remove-Item -LiteralPath $runtimeRoot -Recurse -Force
    }
    if ((Test-Path -LiteralPath $tempRoot -PathType Container) -and
        @(Get-ChildItem -LiteralPath $tempRoot -Force).Count -eq 0) {
        Remove-Item -LiteralPath $tempRoot -Force
    }
}
