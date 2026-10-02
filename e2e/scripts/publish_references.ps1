[CmdletBinding()]
param(
    [Parameter(Mandatory)][string[]]$Suite,
    [Parameter(Mandatory)][string]$CapturedRepository,
    [Parameter(Mandatory)][string]$CaptureRepository,
    [string[]]$PreserveGeneratedSuite = @()
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$root = (Get-VisualRegressionRepositoryState).Root
$capturedRepository = [IO.Path]::GetFullPath($CapturedRepository)
$captureRepository = [IO.Path]::GetFullPath($CaptureRepository)
$transaction = New-VisualRegressionTransaction -Root $root -Prefix 'reference-publish'
$tasks = [Collections.Generic.List[object]]::new()
$contexts = [Collections.Generic.List[object]]::new()

try {
    foreach ($suiteName in $Suite) {
        $defaultContext = Get-VisualRegressionContext -Suite $suiteName
        $context = Get-VisualRegressionContext `
            -Suite $suiteName `
            -CaptureRoot (Join-Path $captureRepository $defaultContext.SuiteRelativePath)
        $contexts.Add($context)
        foreach ($task in @(
            New-VisualRegressionArtifactTasks `
                -Context $context `
                -Transaction $transaction `
                -CapturedRoot (Join-Path $capturedRepository $defaultContext.SuiteRelativePath) `
                -CapturedTier Reference `
                -KeyPrefix 'reference-' `
                -PreserveCapturedTier ($PreserveGeneratedSuite -icontains $context.Suite)
        )) {
            $tasks.Add($task)
        }
    }

    Invoke-VisualRegressionTaskGraph `
        -Task ([object[]]$tasks) `
        -FailurePrefix 'Reference publication task'
    Publish-VisualRegressionArtifacts -Context ([object[]]$contexts) -Transaction $transaction
    Write-Host "Published NUN5 reference artifacts for $($contexts.Count) suite(s)." -ForegroundColor Green
}
finally {
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $root
}
