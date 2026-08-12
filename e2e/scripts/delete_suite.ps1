[CmdletBinding(DefaultParameterSetName = 'Suite')]
param(
    [Parameter(Mandatory, ParameterSetName = 'Suite')][string]$Suite,
    [Parameter(Mandatory, ParameterSetName = 'All')][switch]$All
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')

if ($All) {
    $root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    $suiteRepository = Join-Path $root 'suites'
    $captureRepository = Join-Path $root 'captures'
    $suites = @(
        Get-VisualRegressionSuiteNames -SuiteRepository $suiteRepository
    )
    if (Test-Path -LiteralPath $suiteRepository) {
        Remove-Item -LiteralPath $suiteRepository -Recurse -Force
    }
    if (Test-Path -LiteralPath $captureRepository -PathType Container) {
        foreach ($item in Get-ChildItem -LiteralPath $captureRepository -Force) {
            if ($item.Name -ceq '.git') { continue }
            Remove-Item -LiteralPath $item.FullName -Recurse -Force
        }
    }
    Write-Host "Deleted all E2E suites: $($suites.Count)" -ForegroundColor Green
    return
}

$context = Get-VisualRegressionContext -Suite $Suite

if (-not (Test-Path -LiteralPath $context.SuitePath -PathType Leaf)) {
    throw "E2E suite does not exist: $($context.Suite)"
}

$descendantBranches = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
if (Test-Path -LiteralPath $context.DescendantSuiteRoot -PathType Container) {
    Get-ChildItem `
        -LiteralPath $context.DescendantSuiteRoot `
        -Filter '*.p2m2' `
        -File `
        -Recurse |
        ForEach-Object {
            $relative = [IO.Path]::GetRelativePath(
                $context.DescendantSuiteRoot,
                $_.FullName
            )
            $branch = $relative.Split([IO.Path]::DirectorySeparatorChar)[0]
            if ($branch.EndsWith('.p2m2', [StringComparison]::OrdinalIgnoreCase)) {
                $branch = [IO.Path]::GetFileNameWithoutExtension($branch)
            }
            [void]$descendantBranches.Add($branch)
        }
}

Remove-Item -LiteralPath $context.SuitePath -Force
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
    -Path $context.SuitePath `
    -Boundary $context.SuiteRepository
Remove-VisualRegressionEmptyParents `
    -Path $context.CaptureRoot `
    -Boundary $context.CaptureRepository
Write-Host "Deleted E2E suite: $($context.Suite)" -ForegroundColor Green
