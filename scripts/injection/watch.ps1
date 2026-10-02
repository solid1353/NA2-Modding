[CmdletBinding()]
param(
    [string]$SourcePath,
    [string]$OverlayPlan,
    [ValidateRange(1, 65535)]
    [int]$PinePort
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3

$repository = [IO.Path]::GetFullPath(
    (Join-Path $PSScriptRoot '..\..')
)
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$patchesPath = Join-Path ([string]$paths.builder) 'patches'
$configurationPath = Join-Path ([string]$paths.builder) (
    'configurations\base.jsonc'
)
$buildScript = Join-Path $PSScriptRoot 'build.py'
$applyScript = Join-Path $PSScriptRoot 'apply.py'
$markerPath = Join-Path $PSScriptRoot 'hot_reload_message.c'
$pineScript = [string]$paths.files.pcsx2_pine_command
$debounceMilliseconds = 400
$pollMilliseconds = 150

# Resolve the interpreter once; the watcher polls PINE several times a second.
$python = & (Join-Path ([string]$paths.scripts) 'lib\run_python.ps1') `
    -PackageSet builder -Command 'import sys; print(sys.executable)'
if ($LASTEXITCODE -ne 0) {
    throw 'Could not resolve the builder Python runtime.'
}

function Resolve-RepositoryPath([string]$Path) {
    if ([IO.Path]::IsPathRooted($Path)) {
        return [IO.Path]::GetFullPath($Path)
    }
    return [IO.Path]::GetFullPath((Join-Path $repository $Path))
}

function Get-ConfiguredDevelopmentPinePort {
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
        $state = & $python -B $pineScript --port $Port status 2>$null
        if (
            $LASTEXITCODE -eq 0 -and
            ([string]$state).Trim() -in @('running', 'paused')
        ) {
            $hook = & $python -B $pineScript `
                --port $Port `
                read 0x001D0578 20 `
                2>$null
            $hookExitCode = $LASTEXITCODE
            $resident = & $python -B $pineScript `
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

$watchPaths = @($patchesPath, $configurationPath)
if ($OverlayPlan) {
    $resolvedOverlayPlan = Resolve-RepositoryPath $OverlayPlan
    if (-not (Test-Path -LiteralPath $resolvedOverlayPlan -PathType Leaf)) {
        throw "Overlay plan was not found: $resolvedOverlayPlan"
    }
    $plan = Get-Content -Raw -LiteralPath $resolvedOverlayPlan |
        ConvertFrom-Json
    $sourceId = [string]$plan.source_id
    $entry = [string]$plan.entry_symbols[0].symbol
    $outputName = $sourceId
    $selection = "$sourceId -> $entry"
    $selectionArguments = @(
        '--source-id', $sourceId,
        '--entry', $entry,
        '--overlay-plan', $resolvedOverlayPlan
    )
    # Every catalog EE source lives below the watched patches folder.
    $watchPaths += @($markerPath, $resolvedOverlayPlan)
}
else {
    $resolvedSourcePath = Resolve-RepositoryPath $SourcePath
    if (-not (Test-Path -LiteralPath $resolvedSourcePath)) {
        throw "Source path was not found: $resolvedSourcePath"
    }
    $sourceRoots = @($patchesPath, $PSScriptRoot)
    if (-not @(
        $sourceRoots | Where-Object {
            Test-Na2PathWithin -Path $resolvedSourcePath -Root $_
        }
    ).Count) {
        throw "Source path must be inside $($sourceRoots -join ' or ')"
    }
    if (
        (Test-Path -LiteralPath $resolvedSourcePath -PathType Leaf) -and
        [IO.Path]::GetExtension($resolvedSourcePath) -cne '.c' -and
        [IO.Path]::GetExtension($resolvedSourcePath) -cne '.S'
    ) {
        throw "Source path must be an EE .c/.S file or folder: $resolvedSourcePath"
    }
    $outputName = [IO.Path]::GetFileNameWithoutExtension($resolvedSourcePath)
    $selection = $resolvedSourcePath
    $selectionArguments = @('--source-path', $resolvedSourcePath)
    $watchPaths += $resolvedSourcePath
    if (-not (Test-Na2PathWithin -Path $markerPath -Root $resolvedSourcePath)) {
        $watchPaths += $markerPath
    }
}
$resolvedOutput = Join-Path ([string]$paths.build) "injection\$outputName"
# Copy of the last manifest this session applied; its writes may already be live.
$appliedManifest = Join-Path $resolvedOutput 'applied.json'
if (Test-Path -LiteralPath $appliedManifest) {
    Remove-Item -LiteralPath $appliedManifest -Force
}

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
    $suffix = if ($ExitOnFailure) { '' } else { ' Watching for the next save.' }
    $timestamp = Get-Date -Format 'HH:mm:ss'
    Write-Host "[injection] $timestamp building $selection" `
        -ForegroundColor Cyan
    & $python -B $buildScript @selectionArguments `
        --output $resolvedOutput `
        --hot-reload-label "HOT RELOAD $timestamp"
    $buildExitCode = $LASTEXITCODE
    if ($buildExitCode -ne 0) {
        Write-Host "[injection] Build failed (exit $buildExitCode).$suffix" `
            -ForegroundColor Red
        if ($ExitOnFailure) {
            exit $buildExitCode
        }
        return
    }
    $applyArguments = @('--input', $resolvedOutput, '--port', $PinePort)
    if (Test-Path -LiteralPath $appliedManifest -PathType Leaf) {
        $applyArguments += @('--previous', $appliedManifest)
    }
    & $python -B $applyScript @applyArguments
    $applyExitCode = $LASTEXITCODE
    if ($applyExitCode -ne 0) {
        Write-Host "[injection] Apply failed (exit $applyExitCode).$suffix" `
            -ForegroundColor Red
        if ($ExitOnFailure) {
            exit $applyExitCode
        }
        return
    }
    Copy-Item -LiteralPath (Join-Path $resolvedOutput 'manifest.json') `
        -Destination $appliedManifest -Force
    Write-Host '[injection] Build/apply complete; watching.' `
        -ForegroundColor Green
}

Write-Host '[injection] User watcher started.'
if ($OverlayPlan) {
    Write-Host "[injection] Source: $sourceId"
    Write-Host "[injection] Entry: $entry"
    Write-Host "[injection] Overlay plan: $resolvedOverlayPlan"
}
else {
    Write-Host "[injection] Source: $resolvedSourcePath"
}
Write-Host "[injection] Output: $resolvedOutput"
Write-Host '[injection] Press Ctrl+C to stop.'

try {
    $observedSignature = Get-WatchSignature
    Invoke-InjectionBuild -ExitOnFailure
    $pendingSignature = $null
    $lastChange = [DateTime]::MinValue

    while ($true) {
        Start-Sleep -Milliseconds $pollMilliseconds
        $vmState = & $python -B $pineScript --port $PinePort status 2>$null
        if (
            $LASTEXITCODE -ne 0 -or
            ([string]$vmState).Trim() -ceq 'shutdown'
        ) {
            Write-Host (
                "[injection] PCSX2 on PINE port $PinePort exited; stopping watcher."
            ) -ForegroundColor Yellow
            exit 0
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
            $debounceMilliseconds
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
}
finally {
    if (Test-Path -LiteralPath $appliedManifest) {
        Remove-Item -LiteralPath $appliedManifest -Force
    }
}
