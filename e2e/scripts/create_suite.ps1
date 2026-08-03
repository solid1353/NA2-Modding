[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Suite,
    [string]$Game
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$context = Get-VisualRegressionContext -Suite $Suite

. (Join-Path $context.Repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$recordingPath = [IO.Path]::GetFullPath((Join-Path `
    $paths.pcsx2_input_recordings `
    ($context.SuiteRelativePath + '.p2m2')
))
if (-not (Test-Path -LiteralPath $recordingPath -PathType Leaf)) {
    throw "Input recording does not exist: $recordingPath"
}

$transaction = New-VisualRegressionTransaction -Root $context.Root -Prefix 'create'
$suiteStage = Join-Path $transaction 'suite-definition'
$captureStage = Join-Path $transaction 'capture-history'
$suiteBackup = Join-Path $transaction 'previous-suite-definition'
$referenceCapture = Join-Path $transaction 'reference-capture'
$referenceJob = $null
$suiteInstalled = $false
$hadSuite = Test-Path -LiteralPath $context.SuiteRoot -PathType Container
$suiteBackedUp = $false
$completed = $false
try {
    [void](New-Item -ItemType Directory -Path $suiteStage, $captureStage -Force)
    Copy-Item -LiteralPath $recordingPath -Destination (Join-Path $suiteStage 'input.p2m2')
    [IO.File]::WriteAllText(
        (Join-Path $suiteStage 'ignore.txt'),
        '',
        [Text.UTF8Encoding]::new($false)
    )
    [void](New-Item -ItemType Directory -Path @(
        [IO.Path]::GetDirectoryName($context.SuiteRoot)
        [IO.Path]::GetDirectoryName($context.CaptureRoot)
    ) -Force)
    if ($hadSuite) {
        [IO.Directory]::Move($context.SuiteRoot, $suiteBackup)
        $suiteBackedUp = $true
    }
    [IO.Directory]::Move($suiteStage, $context.SuiteRoot)
    $suiteInstalled = $true

    if (-not [string]::IsNullOrWhiteSpace($Game)) {
        $referenceJob = Start-ThreadJob -Name 'reference' -ScriptBlock {
            param($Script, $Suite, $Game, $CaptureOutputRoot)
            $ErrorActionPreference = 'Stop'
            & $Script `
                -Suite $Suite `
                -Game $Game `
                -CaptureOutputRoot $CaptureOutputRoot
        } -ArgumentList (
            Join-Path $PSScriptRoot 'reference.ps1'
        ), $context.Suite, $Game, $referenceCapture
        Write-Host 'Reference replay and E2E test pipeline started concurrently.' -ForegroundColor Cyan
    }

    & (Join-Path $PSScriptRoot 'run.ps1') `
        -Suite $context.Suite `
        -CaptureRoot $captureStage

    if ($null -ne $referenceJob) {
        [void](Wait-Job -Job $referenceJob)
        Receive-Job -Job $referenceJob | ForEach-Object { Write-Output $_ }
        if ($referenceJob.State -cne 'Completed') {
            $reason = if ($null -ne $referenceJob.ChildJobs[0].JobStateInfo.Reason) {
                $referenceJob.ChildJobs[0].JobStateInfo.Reason.Message
            }
            else {
                'unknown failure'
            }
            throw "Reference replay failed: $reason"
        }
        & (Join-Path $PSScriptRoot 'reference.ps1') `
            -Suite $context.Suite `
            -CapturedRoot $referenceCapture `
            -CaptureRoot $captureStage
    }

    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{ ($context.CaptureRoot) = $captureStage }) `
        -TransactionRoot $transaction
    $completed = $true
    Write-Host "Created or replaced E2E suite: $($context.Suite)" -ForegroundColor Green
}
finally {
    if ($null -ne $referenceJob) {
        if ($referenceJob.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $referenceJob -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $referenceJob -Force -ErrorAction SilentlyContinue
    }
    if (-not $completed) {
        if ($suiteInstalled -and (Test-Path -LiteralPath $context.SuiteRoot -PathType Container)) {
            Remove-Item -LiteralPath $context.SuiteRoot -Recurse -Force
        }
        if ($suiteBackedUp -and (Test-Path -LiteralPath $suiteBackup -PathType Container)) {
            [void](New-Item -ItemType Directory -Path (
                [IO.Path]::GetDirectoryName($context.SuiteRoot)
            ) -Force)
            [IO.Directory]::Move($suiteBackup, $context.SuiteRoot)
        }
        Remove-VisualRegressionEmptyParents `
            -Path $context.SuiteRoot `
            -Boundary (Join-Path $context.Root 'suites')
    }
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}
