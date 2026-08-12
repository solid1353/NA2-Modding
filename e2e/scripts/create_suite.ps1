[CmdletBinding(DefaultParameterSetName = 'Suite')]
param(
    [Parameter(Mandatory, ParameterSetName = 'Suite')][string]$Suite,
    [Parameter(Mandatory, ParameterSetName = 'All')][switch]$All,
    [string]$Game
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$recordingRoot = [IO.Path]::GetFullPath($paths.pcsx2_input_recordings)

if (-not (Test-Path -LiteralPath $recordingRoot -PathType Container)) {
    throw "Shared recording root does not exist: $recordingRoot"
}

$recordings = @(
    if ($All) {
        Get-ChildItem -LiteralPath $recordingRoot -Filter '*.p2m2' -File -Recurse |
            Where-Object {
                $relative = [IO.Path]::GetRelativePath($recordingRoot, $_.FullName)
                $relativeDirectory = [IO.Path]::GetDirectoryName($relative)
                [string]::IsNullOrEmpty($relativeDirectory) -or
                    @(
                        $relativeDirectory.Split([IO.Path]::DirectorySeparatorChar) |
                            Where-Object {
                                $_.StartsWith('__', [StringComparison]::Ordinal)
                            }
                    ).Count -eq 0
            } |
            Sort-Object FullName |
            ForEach-Object {
                $relative = [IO.Path]::GetRelativePath($recordingRoot, $_.FullName)
                [pscustomobject]@{
                    Path = $_.FullName
                    Suite = $relative.Substring(0, $relative.Length - 5).Replace('\', '/')
                }
            }
    }
    else {
        $context = Get-VisualRegressionContext -Suite $Suite
        $recordingPath = [IO.Path]::GetFullPath((Join-Path `
            $recordingRoot `
            ($context.SuiteRelativePath + '.p2m2')
        ))
        if (-not (Test-Path -LiteralPath $recordingPath -PathType Leaf)) {
            throw "Input recording does not exist: $recordingPath"
        }
        [pscustomobject]@{
            Path = $recordingPath
            Suite = $context.Suite
        }
    }
)
if ($recordings.Count -eq 0) {
    throw "No shared E2E recordings exist under: $recordingRoot"
}

$transaction = New-VisualRegressionTransaction -Root $root -Prefix 'create'
$definitionStageRoot = Join-Path $transaction 'suite-definitions'
$definitionBackupRoot = Join-Path $transaction 'previous-suite-definitions'
$captureStageRoot = Join-Path $transaction 'capture-history'
$referenceCaptureRoot = Join-Path $transaction 'reference-captures'
$referenceJobs = [Collections.Generic.List[object]]::new()
$referencePublishJobs = [Collections.Generic.List[object]]::new()
$installed = [Collections.Generic.List[object]]::new()
$completed = $false
try {
    foreach ($recording in $recordings) {
        $context = Get-VisualRegressionContext -Suite $recording.Suite
        $suiteStage = Join-Path $definitionStageRoot ($context.SuiteRelativePath + '.p2m2')
        $suiteBackup = Join-Path $definitionBackupRoot ($context.SuiteRelativePath + '.p2m2')
        $entry = [pscustomobject]@{
            Context = $context
            Backup = $suiteBackup
            Installed = $false
            BackedUp = $false
        }
        $installed.Add($entry)

        [void](New-Item -ItemType Directory -Path @(
            [IO.Path]::GetDirectoryName($suiteStage)
            [IO.Path]::GetDirectoryName($context.SuitePath)
            [IO.Path]::GetDirectoryName($context.CaptureRoot)
        ) -Force)
        Copy-Item -LiteralPath $recording.Path -Destination $suiteStage
        if (Test-Path -LiteralPath $context.SuitePath -PathType Leaf) {
            [void](New-Item -ItemType Directory -Path (
                [IO.Path]::GetDirectoryName($suiteBackup)
            ) -Force)
            [IO.File]::Move($context.SuitePath, $suiteBackup)
            $entry.BackedUp = $true
        }
        [IO.File]::Move($suiteStage, $context.SuitePath)
        $entry.Installed = $true
    }

    if (-not [string]::IsNullOrWhiteSpace($Game)) {
        foreach ($entry in $installed) {
            $context = $entry.Context
            $referenceCapture = Join-Path $referenceCaptureRoot $context.SuiteRelativePath
            $referenceJob = Start-ThreadJob -Name "reference/$($context.Suite)" -ScriptBlock {
                param($Script, $Suite, $Game, $CaptureOutputRoot)
                $ErrorActionPreference = 'Stop'
                & $Script `
                    -Suite $Suite `
                    -Game $Game `
                    -CaptureOutputRoot $CaptureOutputRoot
            } -ArgumentList (
                Join-Path $PSScriptRoot 'reference.ps1'
            ), $context.Suite, $Game, $referenceCapture
            $referenceJobs.Add($referenceJob)
        }
        Write-Host (
            "Reference replays and the E2E test pipeline started concurrently for " +
            "$($recordings.Count) suite(s)."
        ) -ForegroundColor Cyan
    }

    & (Join-Path $PSScriptRoot 'run.ps1') `
        -Suite ([string[]]@($recordings.Suite)) `
        -CaptureRepository $captureStageRoot `
        -RepeatNormal

    if ($referenceJobs.Count -gt 0) {
        Wait-VisualRegressionJobs `
            -Job ([object[]]$referenceJobs) `
            -FailurePrefix 'Reference replay job'
        foreach ($entry in $installed) {
            $context = $entry.Context
            $referencePublishJob = Start-ThreadJob `
                -Name "reference-publish/$($context.Suite)" `
                -ScriptBlock {
                    param($Script, $Suite, $CapturedRoot, $CaptureRoot)
                    $ErrorActionPreference = 'Stop'
                    & $Script `
                        -Suite $Suite `
                        -CapturedRoot $CapturedRoot `
                        -CaptureRoot $CaptureRoot
                } `
                -ArgumentList (
                    Join-Path $PSScriptRoot 'reference.ps1'
                ), $context.Suite, (
                    Join-Path $referenceCaptureRoot $context.SuiteRelativePath
                ), (
                    Join-Path $captureStageRoot $context.SuiteRelativePath
                )
            $referencePublishJobs.Add($referencePublishJob)
        }
        Wait-VisualRegressionJobs `
            -Job ([object[]]$referencePublishJobs) `
            -FailurePrefix 'Reference publication job'
    }

    $replacements = [ordered]@{}
    foreach ($entry in $installed) {
        $context = $entry.Context
        $replacements[$context.CaptureRoot] = Join-Path `
            $captureStageRoot `
            $context.SuiteRelativePath
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $transaction
    $completed = $true
    if ($All) {
        Write-Host "Created or replaced all E2E suites: $($recordings.Count)" -ForegroundColor Green
    }
    else {
        Write-Host "Created or replaced E2E suite: $($recordings[0].Suite)" -ForegroundColor Green
    }
}
finally {
    foreach ($job in @($referenceJobs) + @($referencePublishJobs)) {
        if ($job.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
    if (-not $completed) {
        for ($index = $installed.Count - 1; $index -ge 0; $index--) {
            $entry = $installed[$index]
            $context = $entry.Context
            if ($entry.Installed -and (Test-Path -LiteralPath $context.SuitePath -PathType Leaf)) {
                Remove-Item -LiteralPath $context.SuitePath -Force
            }
            if ($entry.BackedUp -and (Test-Path -LiteralPath $entry.Backup -PathType Leaf)) {
                [void](New-Item -ItemType Directory -Path (
                    [IO.Path]::GetDirectoryName($context.SuitePath)
                ) -Force)
                [IO.File]::Move($entry.Backup, $context.SuitePath)
            }
            Remove-VisualRegressionEmptyParents `
                -Path $context.SuitePath `
                -Boundary $context.SuiteRepository
        }
    }
    Remove-VisualRegressionTransaction -Transaction $transaction -Root $root
}
