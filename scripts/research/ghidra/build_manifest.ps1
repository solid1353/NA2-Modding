param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('NA2', 'NUN3', 'NUN5', 'NUN6', 'shared')]
    [string]$Target
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\lib\paths.ps1')
$paths = Get-Na2Paths

function Resolve-SourceAlias([string]$Alias) {
    return Resolve-Na2ProjectPathAlias -Alias $Alias -Paths $paths
}

$analysisDirectory = if ($Target -eq 'shared') { 'shared' } else { $Target }
$analysisRoot = Join-Path $paths.analysis "disassembly\$analysisDirectory"
$targets = @(Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'targets.tsv') -Delimiter "`t" |
    Where-Object target -eq $Target)
if ($targets.Count -eq 0) { throw "No manifest targets found for $Target" }

$versionLine = Get-Content -LiteralPath (Join-Path $paths.utils 'ghidra\Ghidra\application.properties') |
    Where-Object { $_ -like 'application.version=*' } |
    Select-Object -First 1
if (-not $versionLine) { throw 'Ghidra application version was not found.' }
$ghidraVersion = $versionLine.Substring('application.version='.Length)

$groups = if ($Target -eq 'shared') {
    @($targets | Group-Object shared_scope)
}
else {
    @([pscustomobject]@{ Name = ''; Group = $targets })
}

foreach ($group in $groups) {
    $artifactRoot = if ($Target -eq 'shared') { Join-Path $analysisRoot $group.Name } else { $analysisRoot }
    $rows = foreach ($item in $group.Group) {
        $summaryPath = Join-Path $artifactRoot "summaries\$($item.program).tsv"
        $exportRoot = Join-Path $artifactRoot "exports\$($item.program)"
        $cPath = Join-Path $exportRoot "$($item.program).c"
        $asciiPath = Join-Path $exportRoot "$($item.program).txt"
        $markerPath = Join-Path $exportRoot 'export.complete'
        foreach ($required in @($summaryPath, $cPath, $asciiPath, $markerPath)) {
            if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Missing analysis artifact: $required" }
        }

        $summary = Import-Csv -LiteralPath $summaryPath -Delimiter "`t"
        if ($summary.source -ne $item.source -or $summary.sha256 -ne $item.expected_sha256) {
            throw "Summary identity mismatch: $Target/$($item.program)"
        }
        $sourcePath = Resolve-SourceAlias $item.source
        $sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
        if ($sourceHash -ne $item.expected_sha256) { throw "Source hash mismatch: $($item.source)" }

        $cFile = Get-Item -LiteralPath $cPath
        $asciiFile = Get-Item -LiteralPath $asciiPath
        if ($cFile.Length -eq 0 -or $asciiFile.Length -eq 0) { throw "Empty export: $Target/$($item.program)" }
        $marker = ConvertFrom-StringData (Get-Content -Raw -LiteralPath $markerPath)
        if ([int64]$marker.c_bytes -ne $cFile.Length -or
            [int64]$marker.ascii_bytes -ne $asciiFile.Length -or
            $marker.ascii_undefined_data -ne 'false') {
            throw "Export marker mismatch: $Target/$($item.program)"
        }

        [pscustomobject][ordered]@{
            program = $item.program
            source = $item.source
            source_sha256 = $item.expected_sha256
            source_bytes = (Get-Item -LiteralPath $sourcePath).Length
            format = $item.format
            language = $summary.language
            load_base = $summary.load_base
            memory_blocks = $summary.memory_blocks
            functions = $summary.functions
            instructions = $summary.instructions
            c_export_bytes = $cFile.Length
            ascii_export_bytes = $asciiFile.Length
            ascii_undefined_data = 'false'
            ghidra_version = $ghidraVersion
        }
    }

    $manifestPath = Join-Path $artifactRoot 'manifest.tsv'
    $rows | Export-Csv -LiteralPath $manifestPath -Delimiter "`t" -NoTypeInformation -Encoding utf8
    Write-Host "Verified analysis manifest: $(ConvertTo-Na2ProjectPath -Path $manifestPath -Paths $paths)"
    Write-Host "Programs: $($rows.Count)"
}
