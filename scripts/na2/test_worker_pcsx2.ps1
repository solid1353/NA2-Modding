[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'worker_paths.ps1')
. (Join-Path $PSScriptRoot 'worker_pcsx2.ps1')

function Assert-Na2WorkerPcsx2Test {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

function New-Na2WorkerPcsx2Fixture {
    param([Parameter(Mandatory = $true)][string]$Root)

    foreach ($directory in @(
        'bios',
        'inis',
        'gamesettings',
        'memcards',
        'cheats',
        'snaps',
        'sstates',
        'logs',
        'cache',
        'textures',
        'inputprofiles',
        'videos'
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $Root $directory) |
            Out-Null
    }
    [IO.File]::WriteAllBytes((Join-Path $Root 'pcsx2-qt.exe'), [byte[]](1, 2, 3))
    [IO.File]::WriteAllText((Join-Path $Root 'portable.txt'), '')
    [IO.File]::WriteAllBytes((Join-Path $Root 'bios\SCPH-70012.bin'), [byte[]](4, 5, 6))
    [IO.File]::WriteAllBytes((Join-Path $Root 'memcards\Mcd001.ps2'), [byte[]](7, 8, 9))
    [IO.File]::WriteAllText(
        (Join-Path $Root 'inis\PCSX2.ini'),
        @'
[Folders]
Bios = bios
Snapshots = snaps
SaveStates = sstates
MemoryCards = memcards
Logs = logs
Cheats = cheats
Cache = cache
Textures = textures
InputProfiles = inputprofiles
Videos = videos

[Filenames]
BIOS = SCPH-70012.bin

[MemoryCards]
Slot1_Enable = true
Slot1_Filename = Mcd001.ps2
'@
    )
}

$testRoot = Join-Path ([IO.Path]::GetTempPath()) (
    "na2-worker-pcsx2-tests-$PID-$([guid]::NewGuid().ToString('N'))"
)
try {
    $repository = Join-Path $testRoot 'repository'
    $workRoot = Join-Path $repository 'work'
    $template = Join-Path $testRoot 'pcsx2_clean'
    New-Item -ItemType Directory -Force -Path $repository, $workRoot, $template |
        Out-Null
    New-Na2WorkerPcsx2Fixture -Root $template

    $paths = [pscustomobject]@{
        repository = $repository
        work = $workRoot
        pcsx2_clean = $template
    }
    $worker = Get-Na2WorkerContext `
        -WorkerRoot 'work\Scripting' `
        -ProjectPaths $paths `
        -RequireRelative
    $templateIni = Join-Path $template 'inis\PCSX2.ini'
    $beforeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $templateIni).Hash
    $context = Initialize-Na2WorkerPcsx2 -Worker $worker -ProjectPaths $paths

    Assert-Na2WorkerPcsx2Test `
        -Condition (Test-Path -LiteralPath $context.Executable -PathType Leaf) `
        -Message 'Provisioning did not create the worker PCSX2 executable.'
    Assert-Na2WorkerPcsx2Test `
        -Condition (Test-Na2PathWithinRoot -Path $context.Root -Root $worker.Root) `
        -Message 'Provisioning escaped the worker root.'
    Assert-Na2WorkerPcsx2Test `
        -Condition ((Get-FileHash -Algorithm SHA256 -LiteralPath $templateIni).Hash -ceq $beforeHash) `
        -Message 'Provisioning modified the clean template.'
    Assert-Na2WorkerPcsx2Test `
        -Condition (-not (Test-Path -LiteralPath "$($context.Root).building")) `
        -Message 'Provisioning retained its staging directory.'

    [IO.File]::WriteAllText((Join-Path $context.Root 'clone-only.txt'), 'preserve')
    $reused = Initialize-Na2WorkerPcsx2 -Worker $worker -ProjectPaths $paths
    Assert-Na2WorkerPcsx2Test `
        -Condition (Test-Path -LiteralPath (Join-Path $reused.Root 'clone-only.txt')) `
        -Message 'Existing worker clone was overwritten instead of reused.'

    Set-Na2WorkerPcsx2Blocked `
        -Context $context `
        -Reason 'synthetic lost ownership' `
        -RuntimePath '@work/Scripting/logs/test'
    $blocked = $false
    try {
        Assert-Na2WorkerPcsx2NotBlocked -Context $context
    }
    catch {
        $blocked = $_.Exception.Message -match 'quarantined'
    }
    Assert-Na2WorkerPcsx2Test `
        -Condition $blocked `
        -Message 'A quarantined worker clone was accepted for launch.'
    Remove-Item -LiteralPath $context.BlockMarker -Force

    $invalidRoot = Join-Path $testRoot 'invalid'
    Copy-Item -LiteralPath $template -Destination $invalidRoot -Recurse
    $invalidIni = Join-Path $invalidRoot 'inis\PCSX2.ini'
    $invalidText = [IO.File]::ReadAllText($invalidIni).Replace(
        'Logs = logs',
        'Logs = C:\outside'
    )
    [IO.File]::WriteAllText($invalidIni, $invalidText)
    $rejected = $false
    try {
        Assert-Na2Pcsx2PortableTree -Root $invalidRoot
    }
    catch {
        $rejected = $_.Exception.Message -match "folder 'Logs' must be relative"
    }
    Assert-Na2WorkerPcsx2Test `
        -Condition $rejected `
        -Message 'Portable-tree validation accepted an absolute mutable folder.'

    Write-Host 'NA2 workstream PCSX2 provisioning tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
