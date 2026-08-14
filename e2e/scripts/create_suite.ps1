[CmdletBinding(DefaultParameterSetName = 'Suite')]
param(
    [Parameter(Mandatory, ParameterSetName = 'Suite')][string]$Suite,
    [Parameter(Mandatory, ParameterSetName = 'All')][switch]$All,
    [switch]$NoReference
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'suite.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$repository = [IO.Path]::GetFullPath((Join-Path $root '..'))
. (Join-Path $repository 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths
$recordingRoot = [IO.Path]::GetFullPath($paths.pcsx2_input_recordings)
$referenceGame = 'nun5'

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
$installed = [Collections.Generic.List[object]]::new()
$allDefinitionsBackedUp = $false
$allDefinitionsInstalled = $false
$allCapturesPublished = $false
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

        [void](New-Item -ItemType Directory -Path (
            [IO.Path]::GetDirectoryName($suiteStage)
        ) -Force)
        Copy-Item -LiteralPath $recording.Path -Destination $suiteStage
        if (-not $All) {
            [void](New-Item -ItemType Directory -Path @(
                [IO.Path]::GetDirectoryName($context.SuitePath)
                [IO.Path]::GetDirectoryName($context.CaptureRoot)
            ) -Force)
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
    }

    if ($All) {
        $suiteRepository = $installed[0].Context.SuiteRepository
        if (Test-Path -LiteralPath $suiteRepository) {
            [IO.Directory]::Move($suiteRepository, $definitionBackupRoot)
            $allDefinitionsBackedUp = $true
        }
        [IO.Directory]::Move($definitionStageRoot, $suiteRepository)
        $allDefinitionsInstalled = $true
    }

    if (-not $NoReference.IsPresent) {
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
            ), $context.Suite, $referenceGame, $referenceCapture
            $referenceJobs.Add($referenceJob)
        }
        Write-Host (
            "Reference replays and the E2E test pipeline started concurrently for " +
            "$($recordings.Count) suite(s)."
        ) -ForegroundColor Cyan
    }

    $runArguments = @{
        Suite = [string[]]@($recordings.Suite)
        CaptureRepository = $captureStageRoot
        RepeatNormal = $true
    }
    if ($referenceJobs.Count -gt 0) {
        $runArguments.SupervisedJob = [object[]]$referenceJobs
    }
    & (Join-Path $PSScriptRoot 'run.ps1') @runArguments

    if ($referenceJobs.Count -gt 0) {
        Wait-VisualRegressionJobs `
            -Job ([object[]]$referenceJobs) `
            -FailurePrefix 'Reference replay job'
        & (Join-Path $PSScriptRoot 'publish_references.ps1') `
            -Suite ([string[]]@($installed.Context.Suite)) `
            -CapturedRepository $referenceCaptureRoot `
            -CaptureRepository $captureStageRoot
    }

    if ($All) {
        $captureRepository = $installed[0].Context.CaptureRepository
        $captureBackupRoot = Join-Path $transaction 'previous-capture-history'
        [void](New-Item -ItemType Directory -Path `
            $captureRepository, `
            $captureBackupRoot `
            -Force)
        $oldCaptureMoveCompleted = $false
        try {
            foreach ($item in @(Get-ChildItem -LiteralPath $captureRepository -Force)) {
                if ($script:E2eCaptureRepositoryMetadataNames -ccontains $item.Name) {
                    continue
                }
                Move-Item `
                    -LiteralPath $item.FullName `
                    -Destination (Join-Path $captureBackupRoot $item.Name)
            }
            $oldCaptureMoveCompleted = $true
            foreach ($item in @(Get-ChildItem -LiteralPath $captureStageRoot -Force)) {
                Move-Item `
                    -LiteralPath $item.FullName `
                    -Destination (Join-Path $captureRepository $item.Name)
            }
            $allCapturesPublished = $true
        }
        catch {
            if ($oldCaptureMoveCompleted) {
                foreach ($item in @(Get-ChildItem -LiteralPath $captureRepository -Force)) {
                    if ($script:E2eCaptureRepositoryMetadataNames -ccontains $item.Name) {
                        continue
                    }
                    Remove-Item -LiteralPath $item.FullName -Recurse -Force
                }
            }
            foreach ($item in @(Get-ChildItem -LiteralPath $captureBackupRoot -Force)) {
                Move-Item `
                    -LiteralPath $item.FullName `
                    -Destination (Join-Path $captureRepository $item.Name)
            }
            throw
        }
    }
    else {
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
    }
    $completed = $true
    if ($All) {
        Write-Host "Created or replaced all E2E suites: $($recordings.Count)" -ForegroundColor Green
    }
    else {
        Write-Host "Created or replaced E2E suite: $($recordings[0].Suite)" -ForegroundColor Green
    }
}
finally {
    foreach ($job in $referenceJobs) {
        if ($job.State -in @('NotStarted', 'Running')) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
        }
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
    if (-not $completed -and $All) {
        if ($allCapturesPublished) {
            $captureRepository = $installed[0].Context.CaptureRepository
            foreach ($item in @(Get-ChildItem -LiteralPath $captureRepository -Force)) {
                if ($script:E2eCaptureRepositoryMetadataNames -ccontains $item.Name) {
                    continue
                }
                Remove-Item -LiteralPath $item.FullName -Recurse -Force
            }
            $captureBackupRoot = Join-Path $transaction 'previous-capture-history'
            foreach ($item in @(Get-ChildItem -LiteralPath $captureBackupRoot -Force)) {
                Move-Item `
                    -LiteralPath $item.FullName `
                    -Destination (Join-Path $captureRepository $item.Name)
            }
        }
        $suiteRepository = $installed[0].Context.SuiteRepository
        if ($allDefinitionsInstalled) {
            if (Test-Path -LiteralPath $suiteRepository) {
                Remove-Item -LiteralPath $suiteRepository -Recurse -Force
            }
        }
        if ($allDefinitionsBackedUp -and (Test-Path -LiteralPath $definitionBackupRoot)) {
            [IO.Directory]::Move($definitionBackupRoot, $suiteRepository)
        }
    }
    elseif (-not $completed) {
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
