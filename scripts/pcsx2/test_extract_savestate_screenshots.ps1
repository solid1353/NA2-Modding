[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$scriptPath = Join-Path $PSScriptRoot 'extract_savestate_screenshots.ps1'
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ("na228-savestate-screenshots-" + [guid]::NewGuid())
$stateDirectory = Join-Path $testRoot 'states'
$otherDirectory = Join-Path $testRoot 'other'
$pngBytes = [byte[]](0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A)

function New-TestSavestate {
    param(
        [Parameter(Mandatory)]
        [string]$LiteralPath
    )

    $archive = [IO.Compression.ZipFile]::Open(
        $LiteralPath,
        [IO.Compression.ZipArchiveMode]::Create
    )
    try {
        $entry = $archive.CreateEntry('Screenshot.png')
        $stream = $entry.Open()
        try {
            $stream.Write($pngBytes, 0, $pngBytes.Length)
        }
        finally {
            $stream.Dispose()
        }
    }
    finally {
        $archive.Dispose()
    }
}

function Assert-True {
    param(
        [Parameter(Mandatory)]
        [bool]$Condition,

        [Parameter(Mandatory)]
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

try {
    [void](New-Item -ItemType Directory -Path $stateDirectory, $otherDirectory)
    $firstState = Join-Path $stateDirectory 'ss1.p2s'
    $secondState = Join-Path $stateDirectory 'ss2.p2s'
    $otherState = Join-Path $otherDirectory 'ss3.p2s'
    New-TestSavestate -LiteralPath $firstState
    New-TestSavestate -LiteralPath $secondState
    New-TestSavestate -LiteralPath $otherState

    $screenshots = Join-Path $stateDirectory 'screenshots'
    [void](New-Item -ItemType Directory -Path $screenshots)
    Set-Content -LiteralPath (Join-Path $screenshots 'stale.png') -Value 'stale'

    & $scriptPath $stateDirectory
    Assert-True -Condition (-not (Test-Path (Join-Path $screenshots 'stale.png'))) `
        -Message 'Folder mode did not clean stale screenshots.'
    Assert-True -Condition (Test-Path (Join-Path $screenshots 'ss1.png')) `
        -Message 'Folder mode did not extract ss1.png.'
    Assert-True -Condition (Test-Path (Join-Path $screenshots 'ss2.png')) `
        -Message 'Folder mode did not extract ss2.png.'

    Set-Content -LiteralPath (Join-Path $screenshots 'preserved.png') -Value 'preserve'
    & $scriptPath $firstState
    Assert-True -Condition (Test-Path (Join-Path $screenshots 'preserved.png')) `
        -Message 'Explicit-file mode removed an unrelated screenshot.'

    $mixedFoldersRejected = $false
    try {
        & $scriptPath $firstState $otherState
    }
    catch {
        $mixedFoldersRejected = $true
    }
    Assert-True -Condition $mixedFoldersRejected `
        -Message 'Explicit files from different folders were accepted.'

    Write-Host 'Savestate screenshot extraction tests passed.'
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
