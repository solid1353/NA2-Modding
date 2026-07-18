param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('NA2', 'NUN3', 'NUN5', 'NUN6', 'shared')]
    [string]$Target,
    [string]$Program
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

$analysisDirectory = if ($Target -eq 'shared') { 'shared' } else { $Target }
$analysisRoot = Join-Path $projectPaths.analysis "disassembly\$analysisDirectory"
$projectRoot = Join-Path $analysisRoot 'ghidra'
$runtimeRoot = Join-Path $projectPaths.work "temp\ghidra_export\$Target"
$settingsRoot = Join-Path $runtimeRoot 'AppData\Roaming\ghidra\ghidra_12.1.2_PUBLIC'
$extensionsRoot = Join-Path $settingsRoot 'Extensions'
$extensionDir = Join-Path $extensionsRoot 'ghidra-emotionengine-reloaded'
$extensionZip = Join-Path $projectPaths.utils 'ghidra\ghidra_12.1.2_PUBLIC_20260607_ghidra-emotionengine-reloaded.zip'
$headless = Join-Path $projectPaths.utils 'ghidra\support\analyzeHeadless.bat'

New-Item -ItemType Directory -Force -Path $runtimeRoot, $extensionsRoot | Out-Null
if (-not (Test-Path -LiteralPath $extensionDir -PathType Container)) {
    Expand-Archive -LiteralPath $extensionZip -DestinationPath $extensionsRoot
}

$java = Get-Command java.exe -ErrorAction SilentlyContinue
if ($java) {
    $javaHome = Split-Path (Split-Path $java.Source -Parent) -Parent
}
else {
    $jetBrainsRoot = Join-Path $env:ProgramFiles 'JetBrains'
    $javaItem = Get-ChildItem -LiteralPath $jetBrainsRoot -Directory -Filter 'JetBrains Rider *' -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        ForEach-Object { Get-Item -LiteralPath (Join-Path $_.FullName 'jbr\bin\java.exe') -ErrorAction SilentlyContinue } |
        Select-Object -First 1
    if (-not $javaItem) { throw 'A Ghidra-compatible JDK was not found.' }
    $javaHome = Split-Path (Split-Path $javaItem.FullName -Parent) -Parent
}

$env:USERPROFILE = $runtimeRoot
$env:APPDATA = Join-Path $runtimeRoot 'AppData\Roaming'
$env:LOCALAPPDATA = Join-Path $runtimeRoot 'AppData\Local'
$env:JAVA_HOME = $javaHome
$env:PATH = (Join-Path $javaHome 'bin') + ';' + $env:PATH
$env:GHIDRA_HEADLESS_MAXMEM = '2G'
New-Item -ItemType Directory -Force -Path $env:APPDATA, $env:LOCALAPPDATA | Out-Null

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
                '-scriptPath', $PSScriptRoot,
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
            '-scriptPath', $PSScriptRoot,
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
