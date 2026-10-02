[CmdletBinding()]
param(
    [Parameter(Mandatory)][string[]]$SelectionToken
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')

$state = Get-VisualRegressionRepositoryState
$captureRepository = $state.CaptureRepository
$selection = Resolve-VisualRegressionSuiteSelection `
    -Token $SelectionToken `
    -RecordingRepository $state.RecordingRepository

if ($selection.All) {
    if (Test-Path -LiteralPath $captureRepository -PathType Container) {
        Clear-VisualRegressionCaptureRepository -CaptureRepository $captureRepository
    }
    Write-Host 'Deleted all E2E capture history.' -ForegroundColor Green
    return
}

$plans = @(
    foreach ($request in $selection.Requests) {
        $context = Get-VisualRegressionContext -Suite $request.Suite
        if ($context.Generated -and
            -not (Test-VisualRegressionGeneratedSuiteRoot -Suite $context.Suite)) {
            throw 'Generated E2E sub-suites cannot be deleted independently.'
        }
        [pscustomobject]@{
            Context = $context
            Request = $request
        }
    }
)

function Remove-E2eGeneratedRange {
    param(
        [Parameter(Mandatory)][object]$Context,
        [Parameter(Mandatory)][string]$Range
    )

    $patterns = @(
        Get-VisualRegressionGeneratedRangePrefixes `
            -Family $Context.GeneratedFamily `
            -Range $Range |
            ForEach-Object { "$_*.png" }
    )
    $directories = @(
        $Context.Capture.ScreenshotGrids
        $Context.Capture.PairGrids
        $Context.Capture.BlendGrids
        $Context.Capture.DiffGrids
        $Context.Capture.AllGrids
    )
    foreach ($directory in $directories) {
        if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
            continue
        }
        foreach ($pattern in $patterns) {
            Get-ChildItem -LiteralPath $directory -Filter $pattern -File |
                Remove-Item -Force
        }
        if (@(Get-ChildItem -LiteralPath $directory -Force).Count -eq 0) {
            Remove-Item -LiteralPath $directory -Force
        }
    }
    if ((Test-Path -LiteralPath $Context.CaptureRoot -PathType Container) -and
        @(Get-ChildItem -LiteralPath $Context.CaptureRoot -Force).Count -eq 0) {
        Remove-Item -LiteralPath $Context.CaptureRoot -Force
    }
    Remove-VisualRegressionEmptyParents `
        -Path $Context.CaptureRoot `
        -Boundary $Context.CaptureRepository
}

function Remove-E2eOrdinarySuiteCapture {
    param([Parameter(Mandatory)][object]$Context)

    $descendantBranches = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    if (Test-Path -LiteralPath $Context.DescendantSuiteRoot -PathType Container) {
        Get-ChildItem `
            -LiteralPath $Context.DescendantSuiteRoot `
            -Filter '*.p2m2' `
            -File `
            -Recurse |
            ForEach-Object {
                $relative = [IO.Path]::GetRelativePath(
                    $Context.DescendantSuiteRoot,
                    $_.FullName
                )
                $branch = $relative.Split([IO.Path]::DirectorySeparatorChar)[0]
                if ($branch.EndsWith('.p2m2', [StringComparison]::OrdinalIgnoreCase)) {
                    $branch = [IO.Path]::GetFileNameWithoutExtension($branch)
                }
                [void]$descendantBranches.Add($branch)
            }
    }
    if (Test-Path -LiteralPath $Context.CaptureRoot -PathType Container) {
        foreach ($item in Get-ChildItem -LiteralPath $Context.CaptureRoot -Force) {
            if ($item.PSIsContainer -and $descendantBranches.Contains($item.Name)) {
                continue
            }
            Remove-Item -LiteralPath $item.FullName -Recurse -Force
        }
        if (@(Get-ChildItem -LiteralPath $Context.CaptureRoot -Force).Count -eq 0) {
            Remove-Item -LiteralPath $Context.CaptureRoot -Force
        }
    }
    Remove-VisualRegressionEmptyParents `
        -Path $Context.CaptureRoot `
        -Boundary $Context.CaptureRepository
}

foreach ($plan in $plans) {
    $context = $plan.Context
    $request = $plan.Request
    if ($context.Generated) {
        if ([string]::IsNullOrWhiteSpace([string]$request.MovesetRange)) {
            if (Test-Path -LiteralPath $context.CaptureRoot -PathType Container) {
                Remove-Item -LiteralPath $context.CaptureRoot -Recurse -Force
            }
            Remove-VisualRegressionEmptyParents `
                -Path $context.CaptureRoot `
                -Boundary $context.CaptureRepository
        }
        else {
            Remove-E2eGeneratedRange `
                -Context $context `
                -Range ([string]$request.MovesetRange)
        }
    }
    else {
        Remove-E2eOrdinarySuiteCapture -Context $context
    }
}

Write-Host (
    "Deleted E2E capture history: $(Get-VisualRegressionSelectionLabel -Request $selection.Requests)"
) -ForegroundColor Green
