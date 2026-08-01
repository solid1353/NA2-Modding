[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0, ValueFromRemainingArguments)]
    [string[]]$Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Resolve-FileSystemItem {
    param(
        [Parameter(Mandatory)]
        [string]$LiteralPath
    )

    $resolved = Resolve-Path -LiteralPath $LiteralPath
    if ($resolved.Provider.Name -ne 'FileSystem') {
        throw "Path is not a filesystem item: $LiteralPath"
    }
    return Get-Item -LiteralPath $resolved.ProviderPath
}

function Write-SavestateScreenshot {
    param(
        [Parameter(Mandatory)]
        [IO.FileInfo]$Savestate,

        [Parameter(Mandatory)]
        [string]$OutputDirectory
    )

    $archive = $null
    $inputStream = $null
    $outputStream = $null
    $outputPath = Join-Path $OutputDirectory ($Savestate.BaseName + '.png')

    try {
        $archive = [IO.Compression.ZipFile]::OpenRead($Savestate.FullName)
        $entry = $archive.GetEntry('Screenshot.png')
        if ($null -eq $entry) {
            throw "$($Savestate.Name) has no embedded Screenshot.png"
        }

        $inputStream = $entry.Open()
        $outputStream = [IO.File]::Open(
            $outputPath,
            [IO.FileMode]::Create,
            [IO.FileAccess]::Write,
            [IO.FileShare]::None
        )
        $inputStream.CopyTo($outputStream)
    }
    finally {
        if ($null -ne $outputStream) {
            $outputStream.Dispose()
        }
        if ($null -ne $inputStream) {
            $inputStream.Dispose()
        }
        if ($null -ne $archive) {
            $archive.Dispose()
        }
    }

    Write-Host "$($Savestate.Name) -> screenshots/$($Savestate.BaseName).png"
}

$items = @($Path | ForEach-Object { Resolve-FileSystemItem -LiteralPath $_ })
$folderMode = $items.Count -eq 1 -and $items[0] -is [IO.DirectoryInfo]

if ($folderMode) {
    $sourceDirectory = $items[0]
    $savestates = @(
        Get-ChildItem -LiteralPath $sourceDirectory.FullName -File |
            Where-Object { $_.Extension -ieq '.p2s' } |
            Sort-Object Name
    )
}
else {
    if ($items | Where-Object { $_ -isnot [IO.FileInfo] }) {
        throw 'Pass either one folder or one or more .p2s files from the same folder.'
    }
    if ($items | Where-Object { $_.Extension -ine '.p2s' }) {
        throw 'Every explicit file must have the .p2s extension.'
    }

    $sourceDirectory = $items[0].Directory
    foreach ($item in $items) {
        if (-not [string]::Equals(
            $item.Directory.FullName,
            $sourceDirectory.FullName,
            [StringComparison]::OrdinalIgnoreCase
        )) {
            throw 'All explicit savestates must belong to the same folder.'
        }
    }
    $savestates = $items
}

$outputDirectory = Join-Path $sourceDirectory.FullName 'screenshots'
if ($folderMode -and (Test-Path -LiteralPath $outputDirectory)) {
    Remove-Item -LiteralPath $outputDirectory -Recurse -Force
}
[void](New-Item -ItemType Directory -Path $outputDirectory -Force)

foreach ($savestate in $savestates) {
    Write-SavestateScreenshot -Savestate $savestate -OutputDirectory $outputDirectory
}

Write-Host "Extracted $($savestates.Count) screenshot(s) into $outputDirectory"
