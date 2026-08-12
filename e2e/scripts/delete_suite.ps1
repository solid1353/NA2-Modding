[CmdletBinding()]
param([Parameter(Mandatory)][string]$Suite)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$context = Get-VisualRegressionContext -Suite $Suite
$definition = Join-Path $context.SuiteRoot 'input.p2m2'

if (-not (Test-Path -LiteralPath $definition -PathType Leaf)) {
    throw "E2E suite does not exist: $($context.Suite)"
}

$descendantBranches = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
Get-ChildItem `
    -LiteralPath $context.SuiteRoot `
    -Filter 'input.p2m2' `
    -File `
    -Recurse |
    Where-Object { $_.FullName -cne $definition } |
    ForEach-Object {
        $relative = [IO.Path]::GetRelativePath(
            $context.SuiteRoot,
            $_.DirectoryName
        )
        [void]$descendantBranches.Add(
            $relative.Split([IO.Path]::DirectorySeparatorChar)[0]
        )
    }

foreach ($item in Get-ChildItem -LiteralPath $context.SuiteRoot -Force) {
    if ($item.PSIsContainer -and $descendantBranches.Contains($item.Name)) {
        continue
    }
    Remove-Item -LiteralPath $item.FullName -Recurse -Force
}
if (@(Get-ChildItem -LiteralPath $context.SuiteRoot -Force).Count -eq 0) {
    Remove-Item -LiteralPath $context.SuiteRoot -Force
}
if (Test-Path -LiteralPath $context.CaptureRoot -PathType Container) {
    foreach ($item in Get-ChildItem -LiteralPath $context.CaptureRoot -Force) {
        if ($item.PSIsContainer -and $descendantBranches.Contains($item.Name)) {
            continue
        }
        Remove-Item -LiteralPath $item.FullName -Recurse -Force
    }
    if (@(Get-ChildItem -LiteralPath $context.CaptureRoot -Force).Count -eq 0) {
        Remove-Item -LiteralPath $context.CaptureRoot -Force
    }
}
Remove-VisualRegressionEmptyParents `
    -Path $context.SuiteRoot `
    -Boundary (Join-Path $context.Root 'suites')
Remove-VisualRegressionEmptyParents `
    -Path $context.CaptureRoot `
    -Boundary $context.CaptureRepository
Write-Host "Deleted E2E suite: $($context.Suite)" -ForegroundColor Green
