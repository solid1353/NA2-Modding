Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot 'ini.ps1')

function Test-Na2PathWithinRoot {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    $resolvedPath = [IO.Path]::GetFullPath($Path)
    $resolvedRoot = [IO.Path]::GetFullPath($Root)
    $prefix = $resolvedRoot.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    return (
        [IO.Path]::Equals($resolvedPath, $resolvedRoot) -or
        $resolvedPath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)
    )
}

function Get-Na2WorkerPcsx2Context {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][psobject]$Worker,
        [Parameter(Mandatory = $true)][psobject]$ProjectPaths
    )

    $root = [IO.Path]::GetFullPath($Worker.Pcsx2)
    if (-not (Test-Na2PathWithinRoot -Path $root -Root $Worker.Root) -or
        [IO.Path]::GetFileName($root) -cne 'pcsx2') {
        throw 'The worker PCSX2 clone must be work/<task title>/pcsx2.'
    }

    [pscustomobject]@{
        TemplateRoot = [IO.Path]::GetFullPath($ProjectPaths.pcsx2_clean)
        Root = $root
        Executable = Join-Path $root 'pcsx2-qt.exe'
        PortableMarker = Join-Path $root 'portable.txt'
        Ini = Join-Path $root 'inis\PCSX2.ini'
        Bios = Join-Path $root 'bios'
        GameSettings = Join-Path $root 'gamesettings'
        MemoryCards = Join-Path $root 'memcards'
        Cheats = Join-Path $root 'cheats'
        BlockMarker = Join-Path $Worker.Root 'pcsx2.runtime-blocked.json'
    }
}

function Assert-Na2WorkerPcsx2NotBlocked {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][psobject]$Context)

    if (Test-Path -LiteralPath $Context.BlockMarker) {
        throw (
            'This workstream PCSX2 clone is quarantined after an unsafe runtime ' +
            'shutdown. Do not launch or delete it until the user confirms the ' +
            'recorded process is gone: ' + $Context.BlockMarker
        )
    }
}

function Set-Na2WorkerPcsx2Blocked {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][psobject]$Context,
        [Parameter(Mandatory = $true)][string]$Reason,
        [Parameter(Mandatory = $true)][string]$RuntimePath
    )

    $content = [ordered]@{
        schema_version = 1
        state = 'blocked'
        reason = $Reason
        runtime = $RuntimePath
    } | ConvertTo-Json
    $content += "`n"
    $temporary = "$($Context.BlockMarker).$PID.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        [IO.File]::WriteAllText(
            $temporary,
            $content,
            [Text.UTF8Encoding]::new($false)
        )
        [IO.File]::Move($temporary, $Context.BlockMarker, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Assert-Na2Pcsx2PortableTree {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [string]$AllowedRoot,
        [switch]$CleanTemplate
    )

    $resolvedRoot = [IO.Path]::GetFullPath($Root)
    $resolvedAllowedRoot = if ([string]::IsNullOrWhiteSpace($AllowedRoot)) {
        $resolvedRoot
    }
    else {
        [IO.Path]::GetFullPath($AllowedRoot)
    }
    $rootItem = Get-Item -LiteralPath $resolvedRoot -Force -ErrorAction Stop
    if (($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "PCSX2 portable root must not be a symlink or junction: $resolvedRoot"
    }
    $reparsePoint = Get-ChildItem -LiteralPath $resolvedRoot -Force -Recurse |
        Where-Object {
            ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
        } |
        Select-Object -First 1
    if ($null -ne $reparsePoint) {
        throw "PCSX2 portable tree contains a symlink or junction: $($reparsePoint.FullName)"
    }
    $executable = Join-Path $resolvedRoot 'pcsx2-qt.exe'
    $portableMarker = Join-Path $resolvedRoot 'portable.txt'
    $iniPath = Join-Path $resolvedRoot 'inis\PCSX2.ini'
    foreach ($requiredFile in $executable, $portableMarker, $iniPath) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
            throw "PCSX2 portable tree is missing a required file: $requiredFile"
        }
    }

    $iniText = [IO.File]::ReadAllText($iniPath)
    foreach ($folderKey in @(
        'Bios',
        'Snapshots',
        'SaveStates',
        'MemoryCards',
        'Logs',
        'Cheats',
        'Cache',
        'Textures',
        'InputProfiles',
        'Videos'
    )) {
        $folderValue = Get-Na2IniValue -Text $iniText -Section 'Folders' -Key $folderKey
        if ([string]::IsNullOrWhiteSpace($folderValue)) { continue }
        $folderPath = if ([IO.Path]::IsPathRooted($folderValue)) {
            [IO.Path]::GetFullPath($folderValue)
        }
        else {
            [IO.Path]::GetFullPath((Join-Path $resolvedRoot $folderValue))
        }
        if (-not (Test-Na2PathWithinRoot `
            -Path $folderPath `
            -Root $resolvedAllowedRoot)) {
            throw "PCSX2 folder '$folderKey' escapes its workstream root."
        }
    }

    $biosName = Get-Na2IniValue -Text $iniText -Section 'Filenames' -Key 'BIOS'
    if ([string]::IsNullOrWhiteSpace($biosName)) {
        throw 'PCSX2 portable configuration does not select a BIOS.'
    }
    if ([IO.Path]::GetFileName($biosName) -cne $biosName -or
        -not (Test-Path -LiteralPath (Join-Path $resolvedRoot "bios\$biosName") -PathType Leaf)) {
        throw "PCSX2 portable configuration selects a missing or nested BIOS: $biosName"
    }

    $cardName = Get-Na2IniValue -Text $iniText -Section 'MemoryCards' -Key 'Slot1_Filename'
    if ([string]::IsNullOrWhiteSpace($cardName) -or
        [IO.Path]::GetFileName($cardName) -cne $cardName -or
        -not (Test-Path -LiteralPath (Join-Path $resolvedRoot "memcards\$cardName") -PathType Leaf)) {
        throw "PCSX2 portable configuration selects a missing or nested Slot 1 card: $cardName"
    }
    if ($CleanTemplate) {
        $cards = @(Get-ChildItem -LiteralPath (Join-Path $resolvedRoot 'memcards') -File -Filter '*.ps2')
        if ($cards.Count -ne 1 -or $cards[0].Name -cne $cardName) {
            throw 'The clean PCSX2 template must contain exactly its configured Slot 1 card.'
        }
    }
}

function Initialize-Na2WorkerPcsx2 {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][psobject]$Worker,
        [Parameter(Mandatory = $true)][psobject]$ProjectPaths
    )

    $context = Get-Na2WorkerPcsx2Context -Worker $Worker -ProjectPaths $ProjectPaths
    if (Test-Path -LiteralPath $context.Root) {
        if (-not (Test-Path -LiteralPath $context.Root -PathType Container)) {
            throw "Worker PCSX2 clone path is not a directory: $($context.Root)"
        }
        Assert-Na2Pcsx2PortableTree `
            -Root $context.Root `
            -AllowedRoot $Worker.Root
        return $context
    }

    Assert-Na2Pcsx2PortableTree -Root $context.TemplateRoot -CleanTemplate
    New-Item -ItemType Directory -Force -Path $Worker.Root | Out-Null
    $staging = "$($context.Root).building"
    if (Test-Path -LiteralPath $staging) {
        Remove-Item -LiteralPath $staging -Recurse -Force
    }
    try {
        Copy-Item -LiteralPath $context.TemplateRoot -Destination $staging -Recurse -Force
        foreach ($item in @(Get-Item -LiteralPath $staging -Force) +
            @(Get-ChildItem -LiteralPath $staging -Force -Recurse)) {
            if (($item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0) {
                $item.Attributes = $item.Attributes -band (-bnot [IO.FileAttributes]::ReadOnly)
            }
        }
        Assert-Na2Pcsx2PortableTree -Root $staging
        [IO.Directory]::Move($staging, $context.Root)
    }
    finally {
        if (Test-Path -LiteralPath $staging) {
            Remove-Item -LiteralPath $staging -Recurse -Force
        }
    }
    return $context
}

function Enter-Na2WorkerPcsx2Lock {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$CloneRoot,
        [ValidateRange(1, 300)][int]$TimeoutSeconds = 60
    )

    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $hash = [Convert]::ToHexString(
            $sha.ComputeHash(
                [Text.Encoding]::UTF8.GetBytes(
                    [IO.Path]::GetFullPath($CloneRoot).ToUpperInvariant()
                )
            )
        ).Substring(0, 24)
    }
    finally {
        $sha.Dispose()
    }
    $mutex = [Threading.Mutex]::new($false, "Local\NA2Modding.WorkerPCSX2.$hash")
    try {
        try {
            $acquired = $mutex.WaitOne([TimeSpan]::FromSeconds($TimeoutSeconds))
        }
        catch [Threading.AbandonedMutexException] {
            $acquired = $true
        }
        if (-not $acquired) {
            throw 'Timed out waiting for this workstream PCSX2 clone.'
        }
        return $mutex
    }
    catch {
        $mutex.Dispose()
        throw
    }
}

function Exit-Na2WorkerPcsx2Lock {
    param([Parameter(Mandatory = $true)][Threading.Mutex]$Mutex)

    try { $Mutex.ReleaseMutex() } finally { $Mutex.Dispose() }
}
