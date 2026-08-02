[CmdletBinding(DefaultParameterSetName = 'None')]
param(
    [Parameter(Mandatory)]
    [string]$Suite,

    [Parameter(ParameterSetName = 'Slots')]
    [string]$Slots,

    [Parameter(ParameterSetName = 'All')]
    [switch]$All
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
if ($PSCmdlet.ParameterSetName -eq 'None') {
    Write-Host 'Usage: .\approve.ps1 -Suite <name> -Slots 2,4,18-21 | .\approve.ps1 -Suite <name> -All'
    return
}
$context = Get-VisualRegressionContext -Suite $Suite
$pending = Join-Path $context.CaptureRoot 'pending'
$pendingScreenshots = Join-Path $pending 'screenshots'
$available = @(Get-NumericPngSlots -Directory $pendingScreenshots)
if ($available.Count -eq 0) {
    throw 'No pending screenshots are available for approval.'
}

if ($All) {
    $selected = $available
}
else {
    $selectedSet = [Collections.Generic.HashSet[int]]::new()
    foreach ($token in $Slots.Split(',')) {
        $token = $token.Trim()
        if (-not $token) { continue }
        if ($token -match '^(\d+)-(\d+)$') {
            $start = [int]$Matches[1]
            $end = [int]$Matches[2]
            if ($end -lt $start) { throw "Descending slot range is invalid: $token" }
            foreach ($slot in $start..$end) { [void]$selectedSet.Add($slot) }
        }
        elseif ($token -match '^\d+$') {
            [void]$selectedSet.Add([int]$token)
        }
        else {
            throw "Invalid slot selector: $token"
        }
    }
    $selected = [int[]]@($selectedSet | Sort-Object)
    if ($selected.Count -eq 0) { throw 'Slot selection is empty.' }
    $missing = [int[]]@($selected | Where-Object { $_ -notin $available })
    if ($missing.Count -gt 0) {
        throw "Selected slots are absent from pending screenshots: $($missing -join ', ')"
    }
}

$transaction = New-VisualRegressionTransaction `
    -Root $context.Root `
    -Prefix 'approve'
$approvedStage = Join-Path $transaction 'approved'
$reportsStage = Join-Path $transaction 'reports'
$scratch = Join-Path $transaction 'scratch'
try {
    [void](New-Item -ItemType Directory -Path $approvedStage, $scratch -Force)
    $existingApproved = Join-Path $context.CaptureRoot 'approved'
    if (Test-Path -LiteralPath $existingApproved -PathType Container) {
        Get-ChildItem -LiteralPath $existingApproved -Force |
            Copy-Item -Destination $approvedStage -Recurse -Force
    }
    $approvedScreenshots = Join-Path $approvedStage 'screenshots'
    $approvedStates = Join-Path $approvedStage 'sstates'
    [void](New-Item -ItemType Directory -Path $approvedScreenshots, $approvedStates -Force)
    $pendingStates = Join-Path $pending 'sstates'
    foreach ($slot in $selected) {
        $screenshot = Get-ChildItem -LiteralPath $pendingScreenshots -Filter '*.png' -File |
            Where-Object { $_.BaseName -match '(\d+)$' -and [int]$Matches[1] -eq $slot } |
            Select-Object -First 1
        Copy-Item -LiteralPath $screenshot.FullName -Destination (Join-Path $approvedScreenshots $screenshot.Name) -Force

        $approvedSlotStates = @(Get-ChildItem -LiteralPath $approvedStates -Filter '*.p2s' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.BaseName -match '(\d+)$' -and [int]$Matches[1] -eq $slot })
        foreach ($state in $approvedSlotStates) { Remove-Item -LiteralPath $state.FullName -Force }
        if (Test-Path -LiteralPath $pendingStates -PathType Container) {
            $pendingState = Get-ChildItem -LiteralPath $pendingStates -Filter '*.p2s' -File |
                Where-Object { $_.BaseName -match '(\d+)$' -and [int]$Matches[1] -eq $slot } |
                Select-Object -First 1
            if ($null -ne $pendingState) {
                Copy-Item -LiteralPath $pendingState.FullName -Destination (Join-Path $approvedStates $pendingState.Name) -Force
            }
        }
    }

    New-VisualRegressionReports `
        -Suite $Suite `
        -PendingRoot $pending `
        -OutputRoot $reportsStage `
        -ScratchRoot $scratch `
        -ApprovedRoot $approvedStage
    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{
            (Join-Path $context.CaptureRoot 'approved') = $approvedStage
            (Join-Path $context.CaptureRoot 'reports') = $reportsStage
        }) `
        -TransactionRoot $transaction
    Write-Host "Approved $($selected.Count) slot(s): $($selected -join ', ')" -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
