[CmdletBinding()]
param(
    [string]$SourcePath,
    [string]$SourceId,
    [string]$Entry,
    [string]$OverlayPlan,
    [string]$Output,
    [string]$LatestIso,
    [ValidateRange(1, 65535)]
    [int]$PinePort,
    [ValidateRange(100, 10000)]
    [int]$DebounceMilliseconds = 400,
    [ValidateRange(50, 5000)]
    [int]$PollMilliseconds = 150,
    [switch]$BuildOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3

$repository = [IO.Path]::GetFullPath(
    (Join-Path $PSScriptRoot '..\..')
)
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$injectionsPath = Join-Path $repository 'na228_builder\injections.json'
$configurationPath = Join-Path $repository (
    'na228_builder\configurations\development.json'
)
$buildScript = Join-Path $PSScriptRoot 'build.py'
$applyScript = Join-Path $PSScriptRoot 'apply.py'
$pineScript = [string]$paths.files.pcsx2_pine_command
$hotReloadSourceId = 'hot_reload_message'
$hotReloadEntry = 'project.hot_reload_message'

function Resolve-RepositoryPath([string]$Path) {
    if ([IO.Path]::IsPathRooted($Path)) {
        return [IO.Path]::GetFullPath($Path)
    }
    return [IO.Path]::GetFullPath((Join-Path $repository $Path))
}

function Get-InjectionPayloadEntry {
    param([Parameter(Mandatory = $true)][Collections.IDictionary]$Injections)

    foreach ($injectionId in $Injections.Keys) {
        $injection = $Injections[$injectionId]
        if ($injection.Contains('payload')) {
            foreach ($payloadId in $injection['payload'].Keys) {
                [pscustomobject]@{
                    Id = [string]$payloadId
                    Value = $injection['payload'][$payloadId]
                }
            }
        }
    }
}

function Get-ConfiguredDevelopmentPinePort {
    . (Join-Path $repository 'scripts\lib\paths.ps1')
    $paths = Get-Na2Paths
    $iniPath = Join-Path $paths.pcsx2_dev 'inis\PCSX2.ini'
    if (-not (Test-Path -LiteralPath $iniPath -PathType Leaf)) {
        throw "Development PCSX2 configuration was not found: $iniPath"
    }
    $match = Select-String `
        -LiteralPath $iniPath `
        -Pattern '^\s*PINESlot\s*=\s*(\d+)\s*$' |
        Select-Object -First 1
    if ($null -eq $match) {
        throw "Development PCSX2 PINESlot is not configured in $iniPath"
    }
    $port = [int]$match.Matches[0].Groups[1].Value
    if ($port -lt 1 -or $port -gt 65535) {
        throw "Development PCSX2 PINESlot is invalid: $port"
    }
    return $port
}

function Wait-InjectionTarget {
    param(
        [int]$Port,
        [int]$TimeoutSeconds = 60
    )

    $emptyHook = '00' * 20
    $residentMagic = '4D576F33'
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        $state = & python -B $pineScript --port $Port status 2>$null
        if (
            $LASTEXITCODE -eq 0 -and
            ([string]$state).Trim() -in @('running', 'paused')
        ) {
            $hook = & python -B $pineScript `
                --port $Port `
                read 0x001D0578 20 `
                2>$null
            $hookExitCode = $LASTEXITCODE
            $resident = & python -B $pineScript `
                --port $Port `
                read 0x008F3D00 4 `
                2>$null
            $residentExitCode = $LASTEXITCODE
            if (
                $hookExitCode -eq 0 -and
                $residentExitCode -eq 0 -and
                ([string]$hook).Trim() -ne $emptyHook -and
                ([string]$resident).Trim() -ceq $residentMagic
            ) {
                return
            }
        }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)

    throw "Development PCSX2 did not load the resident payload and root injection target on PINE port $Port within $TimeoutSeconds seconds."
}

$resolvedOverlayPlan = $null
if ($OverlayPlan) {
    $resolvedOverlayPlan = Resolve-RepositoryPath $OverlayPlan
    if (-not (Test-Path -LiteralPath $resolvedOverlayPlan -PathType Leaf)) {
        throw "Overlay plan was not found: $resolvedOverlayPlan"
    }
    $plan = Get-Content -Raw -LiteralPath $resolvedOverlayPlan |
        ConvertFrom-Json
    if (-not $SourceId) {
        $SourceId = [string]$plan.source_id
    }
    if (-not $Entry) {
        if ([int]$plan.schema_version -eq 2) {
            $Entry = [string]$plan.entry_symbols[0].symbol
        }
        else {
            $Entry = [string]$plan.entry_symbol
        }
    }
}

$directScope = -not $resolvedOverlayPlan -and -not $SourceId -and -not $Entry
if ($directScope) {
    if (-not $SourcePath) {
        $SourcePath = 'src'
    }
    $resolvedSourcePath = Resolve-RepositoryPath $SourcePath
    $sourceItem = Get-Item -LiteralPath $resolvedSourcePath -Force `
        -ErrorAction SilentlyContinue
    if (-not $sourceItem) {
        throw "Source path was not found: $resolvedSourcePath"
    }
    $sourceRoot = [IO.Path]::GetFullPath((Join-Path $repository 'src'))
    $sourcePrefix = $sourceRoot.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (
        -not $resolvedSourcePath.Equals(
            $sourceRoot,
            [StringComparison]::OrdinalIgnoreCase
        ) -and
        -not $resolvedSourcePath.StartsWith(
            $sourcePrefix,
            [StringComparison]::OrdinalIgnoreCase
        )
    ) {
        throw "Source path must be inside $sourceRoot"
    }
    if (
        -not $sourceItem.PSIsContainer -and
        [IO.Path]::GetExtension($resolvedSourcePath) -ine '.c'
    ) {
        throw "Source path must be a C file or folder: $resolvedSourcePath"
    }
}
else {
    if (-not $Entry) {
        throw 'Entry is required when OverlayPlan does not declare one.'
    }
    if ($SourceId -ceq $hotReloadSourceId) {
        if ($Entry -cne $hotReloadEntry) {
            throw "Source '$hotReloadSourceId' requires entry '$hotReloadEntry'."
        }
        $canonicalSource = Join-Path $repository 'src\hot_reload_message.c'
    }
    else {
        $injections = Get-Content -Raw -LiteralPath $injectionsPath |
            ConvertFrom-Json -AsHashtable
        $payloadEntries = @(
            Get-InjectionPayloadEntry -Injections $injections
        )
        $sourceRows = @(
            $payloadEntries |
                Where-Object { $_.Value['kind'] -ceq 'c' }
        )
        if (-not $resolvedOverlayPlan) {
            $entryRows = [Collections.Generic.List[object]]::new()
            foreach ($sourceRow in $sourceRows) {
                $fragments = $sourceRow.Value['fragments']
                if ($fragments.Contains($Entry)) {
                    $entryRows.Add([pscustomobject]@{
                        source_id = $sourceRow.Id
                        entry_symbol = $Entry
                    })
                }
            }
            foreach ($payloadEntry in $payloadEntries) {
                if (
                    $payloadEntry.Id -ceq $Entry -and
                    $payloadEntry.Value.Contains('abi') -and
                    $payloadEntry.Value.Contains('source')
                ) {
                    $entryRows.Add([pscustomobject]@{
                        source_id = [string]$payloadEntry.Value['source']
                        entry_symbol = $Entry
                    })
                }
            }
            if ($entryRows.Count -ne 1) {
                throw "Entry '$Entry' must match exactly one catalog ABI declaration."
            }
            if (-not $SourceId) {
                $SourceId = [string]$entryRows[0].source_id
            }
            if ($SourceId -cne [string]$entryRows[0].source_id) {
                throw "Entry '$Entry' does not belong to source '$SourceId'."
            }
        }

        $selectedSources = @(
            $sourceRows | Where-Object { $_.Id -ceq $SourceId }
        )
        if ($selectedSources.Count -ne 1) {
            throw "Source '$SourceId' must match exactly one canonical C source."
        }
        $sourceDeclaration = [string]$selectedSources[0].Value['path']
        $canonicalSource = [IO.Path]::GetFullPath(
            (Join-Path $repository $sourceDeclaration)
        )
    }
    if (-not $SourcePath) {
        $SourcePath = $canonicalSource
    }
    $resolvedSourcePath = Resolve-RepositoryPath $SourcePath
    $sourceItem = Get-Item -LiteralPath $resolvedSourcePath -Force `
        -ErrorAction SilentlyContinue
    if (-not $sourceItem) {
        throw "Source path was not found: $resolvedSourcePath"
    }
    if ($sourceItem.PSIsContainer) {
        $prefix = $resolvedSourcePath.TrimEnd(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        ) + [IO.Path]::DirectorySeparatorChar
        if (-not $canonicalSource.StartsWith(
            $prefix,
            [StringComparison]::OrdinalIgnoreCase
        )) {
            throw "Source path does not contain $canonicalSource"
        }
    }
    elseif (-not $resolvedSourcePath.Equals(
        $canonicalSource,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Source path is not the selected canonical source: $canonicalSource"
    }
}

$outputName = if ($directScope) {
    if ($resolvedSourcePath.Equals(
        [IO.Path]::GetFullPath((Join-Path $repository 'src')),
        [StringComparison]::OrdinalIgnoreCase
    )) {
        'all'
    }
    else {
        [IO.Path]::GetFileNameWithoutExtension($resolvedSourcePath)
    }
}
else {
    $SourceId
}
$resolvedOutput = if ($Output) {
    Resolve-RepositoryPath $Output
}
else {
    Join-Path $repository "build\injection\$outputName"
}
if (-not $BuildOnly) {
    if ($PinePort -eq 0) {
        $PinePort = Get-ConfiguredDevelopmentPinePort
    }
    Write-Host (
        "[injection] Wait up to 60 seconds for the injection target on PINE port $PinePort"
    ) -ForegroundColor Cyan
    Wait-InjectionTarget -Port $PinePort
    Write-Host (
        "[injection] Watch and hot-reload through PINE port $PinePort"
    ) -ForegroundColor Cyan
}

$watchPaths = @(
    $resolvedSourcePath,
    $catalogPath,
    $configurationPath
)
$markerPath = Join-Path $repository 'src\hot_reload_message.c'
if (
    -not $resolvedSourcePath.Equals(
        $markerPath,
        [StringComparison]::OrdinalIgnoreCase
    ) -and
    (
        -not $sourceItem.PSIsContainer -or
        -not $markerPath.StartsWith(
            $resolvedSourcePath.TrimEnd(
                [IO.Path]::DirectorySeparatorChar,
                [IO.Path]::AltDirectorySeparatorChar
            ) + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase
        )
    )
) {
    $watchPaths += $markerPath
}
if ($resolvedOverlayPlan) {
    $watchPaths += $resolvedOverlayPlan
}

function Get-FileSignature([string]$Path) {
    if (Test-Path -LiteralPath $Path -PathType Container) {
        $root = [IO.Path]::GetFullPath($Path).TrimEnd(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        )
        $parts = foreach ($file in @(
            Get-ChildItem -LiteralPath $root -Recurse -File -Force |
                Sort-Object FullName
        )) {
            $relative = $file.FullName.Substring($root.Length + 1)
            "$relative`t$(Get-FileSignature $file.FullName)"
        }
        return "DIRECTORY`n$([string]::Join("`n", $parts))"
    }
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return 'MISSING'
    }
    try {
        return (
            Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop
        ).Hash
    }
    catch [System.IO.IOException] {
        return 'BUSY'
    }
    catch [System.UnauthorizedAccessException] {
        return 'BUSY'
    }
}

function Get-WatchSignature {
    $parts = foreach ($path in @($watchPaths | Sort-Object -Unique)) {
        "$path`t$(Get-FileSignature $path)"
    }
    return [string]::Join("`n", $parts)
}

function Invoke-InjectionBuild([switch]$ExitOnFailure) {
    $buildArguments = @(
        '-B',
        $buildScript,
        '--output',
        $resolvedOutput
    )
    if ($directScope) {
        $buildArguments += @('--source-path', $resolvedSourcePath)
    }
    else {
        $buildArguments += @(
            '--source-id',
            $SourceId,
            '--entry',
            $Entry
        )
    }
    if ($resolvedOverlayPlan) {
        $buildArguments += @('--overlay-plan', $resolvedOverlayPlan)
    }
    $buildArguments += @(
        '--hot-reload-label',
        ('HOT RELOAD ' + (Get-Date -Format 'HH:mm:ss'))
    )
    if ($LatestIso) {
        $buildArguments += @('--iso', (Resolve-RepositoryPath $LatestIso))
    }

    $timestamp = Get-Date -Format 'HH:mm:ss'
    $selection = if ($directScope) {
        $resolvedSourcePath
    }
    else {
        "$SourceId -> $Entry"
    }
    Write-Host "[injection] $timestamp building $selection" `
        -ForegroundColor Cyan
    & python @buildArguments
    $buildExitCode = $LASTEXITCODE
    if ($buildExitCode -ne 0) {
        $suffix = if ($ExitOnFailure) {
            ''
        }
        else {
            ' Watching for the next save.'
        }
        Write-Host "[injection] Build failed (exit $buildExitCode).$suffix" `
            -ForegroundColor Red
        if ($ExitOnFailure) {
            exit $buildExitCode
        }
        return
    }
    if (-not $BuildOnly) {
        & python -B $applyScript `
            --input $resolvedOutput `
            --port $PinePort `
            --force-writes
        $applyExitCode = $LASTEXITCODE
        if ($applyExitCode -ne 0) {
            $suffix = if ($ExitOnFailure) {
                ''
            }
            else {
                ' Watching for the next save.'
            }
            Write-Host "[injection] Apply failed (exit $applyExitCode).$suffix" `
                -ForegroundColor Red
            if ($ExitOnFailure) {
                exit $applyExitCode
            }
            return
        }
    }
    Write-Host '[injection] Build/apply complete; watching.' `
        -ForegroundColor Green
}

Write-Host '[injection] User watcher started.'
Write-Host "[injection] Source: $resolvedSourcePath"
if (-not $directScope) {
    Write-Host "[injection] Entry: $Entry"
}
if ($resolvedOverlayPlan) {
    Write-Host "[injection] Overlay plan: $resolvedOverlayPlan"
}
Write-Host "[injection] Output: $resolvedOutput"
Write-Host '[injection] Press Ctrl+C to stop.'

$observedSignature = Get-WatchSignature
Invoke-InjectionBuild -ExitOnFailure
$pendingSignature = $null
$lastChange = [DateTime]::MinValue

while ($true) {
    Start-Sleep -Milliseconds $PollMilliseconds
    if (-not $BuildOnly) {
        $vmState = & python -B $pineScript --port $PinePort status 2>$null
        if (
            $LASTEXITCODE -ne 0 -or
            ([string]$vmState).Trim() -ceq 'shutdown'
        ) {
            Write-Host (
                "[injection] PCSX2 on PINE port $PinePort exited; stopping watcher."
            ) -ForegroundColor Yellow
            exit 0
        }
    }
    $nextSignature = Get-WatchSignature
    if ($nextSignature -cne $observedSignature) {
        $observedSignature = $nextSignature
        $pendingSignature = $nextSignature
        $lastChange = [DateTime]::UtcNow
        continue
    }
    if ($null -eq $pendingSignature) {
        continue
    }
    if (([DateTime]::UtcNow - $lastChange).TotalMilliseconds -lt (
        $DebounceMilliseconds
    )) {
        continue
    }

    $buildSignature = $pendingSignature
    $pendingSignature = $null
    Invoke-InjectionBuild
    $afterBuildSignature = Get-WatchSignature
    $observedSignature = $afterBuildSignature
    if ($afterBuildSignature -cne $buildSignature) {
        $pendingSignature = $afterBuildSignature
        $lastChange = [DateTime]::UtcNow
    }
}
