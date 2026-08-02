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
$pendingScreenshots = $pending
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
$pendingStage = Join-Path $transaction 'pending'
$reportsStage = Join-Path $transaction 'reports'
$scratch = Join-Path $transaction 'scratch'
try {
    [void](New-Item -ItemType Directory -Path $approvedStage, $pendingStage, $scratch -Force)
    $existingApproved = Join-Path $context.CaptureRoot 'approved'
    if (Test-Path -LiteralPath $existingApproved -PathType Container) {
        Get-ChildItem -LiteralPath $existingApproved -Force |
            Where-Object Name -cne 'sstates' |
            Copy-Item -Destination $approvedStage -Recurse -Force
    }
    Get-ChildItem -LiteralPath $pending -Force |
        Where-Object Name -cne 'sstates' |
        Copy-Item -Destination $pendingStage -Recurse -Force
    $approvedScreenshots = $approvedStage
    [void](New-Item -ItemType Directory -Path $approvedScreenshots -Force)
    foreach ($slot in $selected) {
        $screenshot = Get-ChildItem -LiteralPath $pendingScreenshots -Filter '*.png' -File |
            Where-Object { $_.BaseName -match '(\d+)$' -and [int]$Matches[1] -eq $slot } |
            Select-Object -First 1
        Copy-Item -LiteralPath $screenshot.FullName -Destination (Join-Path $approvedScreenshots $screenshot.Name) -Force
        Remove-Item -LiteralPath (Join-Path $pendingStage $screenshot.Name) -Force
    }

    New-VisualRegressionReports `
        -Suite $Suite `
        -PendingDirectory $pendingStage `
        -OutputRoot $reportsStage `
        -ScratchRoot $scratch `
        -ApprovedDirectory $approvedStage
    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{
            (Join-Path $context.CaptureRoot 'approved') = $approvedStage
            (Join-Path $context.CaptureRoot 'pending') = $pendingStage
            (Join-Path $context.CaptureRoot 'reports') = $reportsStage
        }) `
        -TransactionRoot $transaction
    Write-Host "Approved $($selected.Count) slot(s): $($selected -join ', ')" -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
