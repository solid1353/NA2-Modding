param(
    [ValidateSet('all', 'NA2', 'NUN5', 'NUN6', 'shared')]
    [string]$Target = 'all',
    [switch]$VerifyOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

function Resolve-SourceAlias([string]$Alias) {
    if (-not $Alias.StartsWith('@source/', [StringComparison]::Ordinal)) {
        throw "Unsupported source alias: $Alias"
    }
    return Join-Path $projectPaths.source $Alias.Substring(8)
}

function Find-JavaHome {
    $java = Get-Command java.exe -ErrorAction SilentlyContinue
    if ($java) { return Split-Path (Split-Path $java.Source -Parent) -Parent }
    $jetBrainsRoot = Join-Path $env:ProgramFiles 'JetBrains'
    $javaItem = Get-ChildItem -LiteralPath $jetBrainsRoot -Directory -Filter 'JetBrains Rider *' -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        ForEach-Object { Get-Item -LiteralPath (Join-Path $_.FullName 'jbr\bin\java.exe') -ErrorAction SilentlyContinue } |
        Select-Object -First 1
    if (-not $javaItem) { throw 'A Ghidra-compatible JDK was not found.' }
    return Split-Path (Split-Path $javaItem.FullName -Parent) -Parent
}

$targets = Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'targets.tsv') -Delimiter "`t"
if ($Target -ne 'all') { $targets = @($targets | Where-Object target -eq $Target) }

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
$settingsRoot = Join-Path $runtimeRoot 'AppData\Roaming\ghidra\ghidra_12.1.2_PUBLIC'
$extensionsRoot = Join-Path $settingsRoot 'Extensions'
$extensionDir = Join-Path $extensionsRoot 'ghidra-emotionengine-reloaded'
$extensionZip = Join-Path $projectPaths.utils 'ghidra\ghidra_12.1.2_PUBLIC_20260607_ghidra-emotionengine-reloaded.zip'
$headless = Join-Path $projectPaths.utils 'ghidra\support\analyzeHeadless.bat'
New-Item -ItemType Directory -Force -Path $runtimeRoot, $extensionsRoot | Out-Null
if (-not (Test-Path -LiteralPath $extensionDir -PathType Container)) {
    Expand-Archive -LiteralPath $extensionZip -DestinationPath $extensionsRoot
}

$env:USERPROFILE = $runtimeRoot
$env:APPDATA = Join-Path $runtimeRoot 'AppData\Roaming'
$env:LOCALAPPDATA = Join-Path $runtimeRoot 'AppData\Local'
$env:JAVA_HOME = Find-JavaHome
$env:PATH = (Join-Path $env:JAVA_HOME 'bin') + ';' + $env:PATH
New-Item -ItemType Directory -Force -Path $env:APPDATA, $env:LOCALAPPDATA | Out-Null

foreach ($item in $targets) {
    $analysisDirectory = if ($item.target -eq 'shared') { 'shared_NA2_NUN5_NUN6' } else { $item.target }
    $analysisRoot = Join-Path $projectPaths.analysis "disassembly\$analysisDirectory"
    $projectRoot = Join-Path $analysisRoot 'ghidra'
    $summaryPath = Join-Path $analysisRoot "summaries\$($item.program).tsv"
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
                '-loader-blockName', 'image', '-scriptPath', $PSScriptRoot,
                '-preScript', 'PrepareMwo3.java', $loadBase, ('0x{0:X8}' -f $textLength), $entry
            )
        }
        default { throw "Unsupported target format: $($item.format)" }
    }
    $arguments += @(
        '-scriptPath', $PSScriptRoot,
        '-postScript', 'WriteAnalysisSummary.java', $summaryPath, $item.source,
        $item.expected_sha256, $item.format, $loadBase,
        '-analysisTimeoutPerFile', '900'
    )
    & $headless @arguments
    if ($LASTEXITCODE -ne 0) { throw "Ghidra import failed: $($item.target)/$($item.program)" }
}
