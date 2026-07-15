param(
    [Parameter(Mandatory = $true)]
    [string[]]$Path,

    [string]$Reason = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$trashRoot = Join-Path $root "trash"
$logDir = Join-Path $root "logs\trash"

New-Item -ItemType Directory -Force -Path $trashRoot | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Get-RelativePath {
    param([string]$FullPath)

    $rootFull = [IO.Path]::GetFullPath($root)
    if (-not $rootFull.EndsWith([IO.Path]::DirectorySeparatorChar)) {
        $rootFull += [IO.Path]::DirectorySeparatorChar
    }

    $pathFull = [IO.Path]::GetFullPath($FullPath)
    if (-not $pathFull.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to trash path outside workspace: $FullPath"
    }

    return $pathFull.Substring($rootFull.Length)
}

function Assert-TrashAllowed {
    param([string]$RelativePath)

    $first = ($RelativePath -split '[\\/]', 2)[0]

    if ($first -eq "source") {
        throw "Refusing to trash anything under source/: $RelativePath"
    }

    if ($first -eq "releases") {
        throw "Refusing to trash anything under releases/: $RelativePath"
    }

    if ($first -eq "trash") {
        throw "Refusing to trash trash/: $RelativePath"
    }
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$batchDir = Join-Path $trashRoot $stamp
if (Test-Path -LiteralPath $batchDir) {
    throw "Trash batch already exists: $batchDir"
}

$items = New-Object System.Collections.Generic.List[object]

foreach ($pathItem in $Path) {
    if (-not (Test-Path -LiteralPath $pathItem)) {
        throw "Path not found: $pathItem"
    }

    $resolved = (Resolve-Path -LiteralPath $pathItem).Path
    $relative = Get-RelativePath -FullPath $resolved
    Assert-TrashAllowed -RelativePath $relative

    $items.Add([pscustomobject]@{
        Source = $resolved
        Relative = $relative
    })
}

New-Item -ItemType Directory -Path $batchDir | Out-Null

$rows = New-Object System.Collections.Generic.List[object]

foreach ($item in $items) {
    $target = Join-Path $batchDir $item.Relative
    $targetParent = Split-Path -Parent $target
    New-Item -ItemType Directory -Force -Path $targetParent | Out-Null

    if (Test-Path -LiteralPath $target) {
        throw "Trash target already exists: $target"
    }

    Move-Item -LiteralPath $item.Source -Destination $target

    $rows.Add([pscustomobject]@{
        Timestamp = $stamp
        Source = $item.Relative
        TrashPath = ("trash\" + $stamp + "\" + $item.Relative)
        Reason = $Reason
    })
}

$manifest = Join-Path $batchDir "trash_manifest.tsv"
$rows | Export-Csv -LiteralPath $manifest -Delimiter "`t" -NoTypeInformation -Encoding UTF8

$logPath = Join-Path $logDir ("trash_" + $stamp + ".tsv")
$rows | Export-Csv -LiteralPath $logPath -Delimiter "`t" -NoTypeInformation -Encoding UTF8

Write-Host "Moved to trash:"
Write-Host $batchDir
Write-Host "Items:" $rows.Count
Write-Host "Log:"
Write-Host $logPath

