[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Suite,
    [Parameter(Mandatory)][string]$Recording,
    [string]$Game
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
if ([IO.Path]::GetFileName($Recording) -cne $Recording) {
    throw 'Recording must be a shared input-recording filename or stem.'
}
$context = Get-VisualRegressionContext -Suite $Suite

. (Join-Path $context.Repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$recordingFilename = if ($Recording.EndsWith('.p2m2', [StringComparison]::OrdinalIgnoreCase)) {
    $Recording
}
else {
    "$Recording.p2m2"
}
$recordingPath = [IO.Path]::GetFullPath((
    Join-Path $paths.pcsx2_input_recordings $recordingFilename
))
if (-not (Test-Path -LiteralPath $recordingPath -PathType Leaf)) {
    throw "Input recording does not exist: $recordingPath"
}

$transaction = New-VisualRegressionTransaction -Root $context.Root -Prefix 'new'
$suiteStage = Join-Path $transaction 'suite-definition'
$captureStage = Join-Path $transaction 'capture-history'
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
    Publish-VisualRegressionTransaction `
        -Replacements ([ordered]@{
            ($context.SuiteRoot) = $suiteStage
            ($context.CaptureRoot) = $captureStage
        }) `
        -TransactionRoot $transaction
    Write-Host "Created or replaced E2E suite: $($context.Suite)" -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $context.Root
}

if (-not [string]::IsNullOrWhiteSpace($Game)) {
    & (Join-Path $PSScriptRoot 'reference.ps1') -Suite $context.Suite -Game $Game
}
& (Join-Path $PSScriptRoot 'run.ps1') -Suite $context.Suite
