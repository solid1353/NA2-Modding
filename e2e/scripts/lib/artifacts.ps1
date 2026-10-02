function Get-VisualRegressionScreenshotDefinition {
    param([Parameter(Mandatory)][string]$Kind)

    if (-not $script:E2eScreenshotKinds.Contains($Kind)) {
        throw "Unknown screenshot kind: $Kind"
    }
    return $script:E2eScreenshotKinds[$Kind]
}

function Get-VisualRegressionGridSuffixes {
    param(
        [Parameter(Mandatory)]
        [ValidateSet('Reference', 'Current')]
        [string]$CapturedTier
    )

    $capturedDefinition = Get-VisualRegressionScreenshotDefinition -Kind $CapturedTier
    $preservedTier = if ($CapturedTier -ieq 'Reference') { 'Current' } else { 'Reference' }
    $preservedDefinition = Get-VisualRegressionScreenshotDefinition -Kind $preservedTier
    [pscustomobject]@{
        Captured = "_$($capturedDefinition.Order)_$($capturedDefinition.Label).png"
        Preserved = "_$($preservedDefinition.Order)_$($preservedDefinition.Label).png"
    }
}

function Copy-VisualRegressionGridStage {
    param(
        [Parameter(Mandatory)][string]$ExistingDirectory,
        [Parameter(Mandatory)][IO.FileInfo[]]$CapturedFile,
        [Parameter(Mandatory)][string]$OutputDirectory,
        [Parameter(Mandatory)][object]$Suffix,
        [switch]$PreserveCapturedTier
    )

    if (Test-Path -LiteralPath $OutputDirectory) {
        Remove-Item -LiteralPath $OutputDirectory -Recurse -Force
    }
    [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
    if (Test-Path -LiteralPath $ExistingDirectory -PathType Container) {
        Get-ChildItem -LiteralPath $ExistingDirectory -Filter '*.png' -File |
            Where-Object {
                $_.Name.EndsWith($Suffix.Preserved, [StringComparison]::Ordinal) -or
                    ($PreserveCapturedTier.IsPresent -and
                        $_.Name.EndsWith($Suffix.Captured, [StringComparison]::Ordinal))
            } |
            Copy-Item -Destination $OutputDirectory
    }
    $CapturedFile | Copy-Item -Destination $OutputDirectory -Force
}

function New-VisualRegressionGeneratedGridStage {
    param(
        [Parameter(Mandatory)][string]$ExistingDirectory,
        [Parameter(Mandatory)][string]$CapturedDirectory,
        [Parameter(Mandatory)][string]$OutputDirectory,
        [Parameter(Mandatory)]
        [ValidateSet('Reference', 'Current')]
        [string]$CapturedTier,
        [switch]$PreserveCapturedTier
    )

    $suffix = Get-VisualRegressionGridSuffixes -CapturedTier $CapturedTier
    if (-not (Test-Path -LiteralPath $CapturedDirectory -PathType Container)) {
        throw "Generated E2E grid capture does not exist: $CapturedDirectory"
    }
    $capturedFiles = @(
        Get-ChildItem -LiteralPath $CapturedDirectory -Filter '*.png' -File |
            Where-Object { $_.Name.EndsWith($suffix.Captured, [StringComparison]::Ordinal) }
    )
    if ($capturedFiles.Count -eq 0) {
        throw "Generated E2E capture contains no $CapturedTier grids: $CapturedDirectory"
    }
    $unexpectedFiles = @(
        Get-ChildItem -LiteralPath $CapturedDirectory -Filter '*.png' -File |
            Where-Object { -not $_.Name.EndsWith($suffix.Captured, [StringComparison]::Ordinal) }
    )
    if ($unexpectedFiles.Count -gt 0) {
        throw (
            "Generated E2E $CapturedTier capture contains an unexpected grid: " +
            $unexpectedFiles[0].Name
        )
    }

    Copy-VisualRegressionGridStage `
        -ExistingDirectory $ExistingDirectory `
        -CapturedFile $capturedFiles `
        -OutputDirectory $OutputDirectory `
        -Suffix $suffix `
        -PreserveCapturedTier:$PreserveCapturedTier.IsPresent

    [pscustomobject]@{
        CapturedTier = $CapturedTier.ToLowerInvariant()
        Captured = $capturedFiles.Count
        Preserved = @(
            Get-ChildItem -LiteralPath $OutputDirectory -Filter '*.png' -File |
                Where-Object { $_.Name.EndsWith($suffix.Preserved, [StringComparison]::Ordinal) }
        ).Count
    }
}

function New-VisualRegressionGeneratedArtifactStage {
    param(
        [Parameter(Mandatory)][string]$ExistingDirectory,
        [Parameter(Mandatory)][string]$CapturedDirectory,
        [Parameter(Mandatory)][string]$OutputRoot,
        [Parameter(Mandatory)][string]$Comparator,
        [Parameter(Mandatory)]
        [ValidateSet('Reference', 'Current')]
        [string]$CapturedTier,
        [switch]$PreserveCapturedTier
    )

    $screenshotGridDirectory = Join-Path `
        $OutputRoot `
        $script:E2eScreenshotGridDirectory
    New-VisualRegressionGeneratedGridStage `
        -ExistingDirectory $ExistingDirectory `
        -CapturedDirectory $CapturedDirectory `
        -OutputDirectory $screenshotGridDirectory `
        -CapturedTier $CapturedTier `
        -PreserveCapturedTier:$PreserveCapturedTier.IsPresent

    & $Comparator `
        -PairedGridDirectory $screenshotGridDirectory `
        -OutputDirectory $OutputRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Generated grid comparison failed with exit code $LASTEXITCODE."
    }
}

function New-VisualRegressionScreenshotInputStage {
    param(
        [Parameter(Mandatory)][string]$ReferenceDirectory,
        [Parameter(Mandatory)][string]$CurrentDirectory,
        [Parameter(Mandatory)][string]$OutputDirectory
    )

    [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
    foreach ($source in @(
        [pscustomobject]@{ Kind = 'Reference'; Directory = $ReferenceDirectory },
        [pscustomobject]@{ Kind = 'Current'; Directory = $CurrentDirectory }
    )) {
        if (-not (Test-Path -LiteralPath $source.Directory -PathType Container)) {
            continue
        }
        $definition = Get-VisualRegressionScreenshotDefinition -Kind $source.Kind
        foreach ($file in Get-ChildItem -LiteralPath $source.Directory -Filter '*.png' -File) {
            if ($file.BaseName -notmatch '^\d+$') {
                throw "Non-numeric screenshot name: $($file.FullName)"
            }
            $name = '{0:D3}_{1}_{2}.png' -f `
                ([int]$file.BaseName),
                $definition.Order,
                $definition.Label
            Copy-Item `
                -LiteralPath $file.FullName `
                -Destination (Join-Path $OutputDirectory $name)
        }
    }
}

function New-VisualRegressionPagedScreenshotGridStage {
    param(
        [Parameter(Mandatory)][string]$ExistingDirectory,
        [Parameter(Mandatory)][string]$CapturedScreenshotDirectory,
        [Parameter(Mandatory)][string]$OutputDirectory,
        [Parameter(Mandatory)]
        [ValidateSet('Reference', 'Current')]
        [string]$CapturedTier
    )

    $suffix = Get-VisualRegressionGridSuffixes -CapturedTier $CapturedTier
    $workRoot = Join-Path `
        ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($OutputDirectory))) `
        ('.screenshot-grid-' + [guid]::NewGuid().ToString('N'))
    $inputRoot = Join-Path $workRoot 'input'
    $capturedGridRoot = Join-Path $workRoot 'captured'
    try {
        $emptyRoot = Join-Path $workRoot 'empty'
        [void](New-Item -ItemType Directory -Path $emptyRoot -Force)
        New-VisualRegressionScreenshotInputStage `
            -ReferenceDirectory $(if ($CapturedTier -ieq 'Reference') {
                $CapturedScreenshotDirectory
            } else { $emptyRoot }) `
            -CurrentDirectory $(if ($CapturedTier -ieq 'Current') {
                $CapturedScreenshotDirectory
            } else { $emptyRoot }) `
            -OutputDirectory $inputRoot
        $comparator = (Get-VisualRegressionRepositoryState).Comparator
        & $comparator `
            -ScreenshotDirectory $inputRoot `
            -OutputDirectory $capturedGridRoot
        if ($LASTEXITCODE -ne 0) {
            throw "Screenshot grid generation failed with exit code $LASTEXITCODE."
        }

        $capturedFiles = @(
            Get-ChildItem -LiteralPath $capturedGridRoot -Filter '*.png' -File |
                Where-Object {
                    $_.Name.EndsWith($suffix.Captured, [StringComparison]::Ordinal)
                }
        )
        if ($capturedFiles.Count -eq 0) {
            throw "Captured $CapturedTier screenshots produced no grids."
        }
        Copy-VisualRegressionGridStage `
            -ExistingDirectory $ExistingDirectory `
            -CapturedFile $capturedFiles `
            -OutputDirectory $OutputDirectory `
            -Suffix $suffix
    }
    finally {
        if (Test-Path -LiteralPath $workRoot) {
            Remove-Item -LiteralPath $workRoot -Recurse -Force
        }
    }
}

function New-VisualRegressionAggregateLinkStage {
    param(
        [Parameter(Mandatory)][object[]]$Source,
        [Parameter(Mandatory)][string]$OutputDirectory
    )

    [void](New-Item -ItemType Directory -Path $OutputDirectory -Force)
    foreach ($item in $Source) {
        $sourceDirectory = [string]$item.Directory
        if (-not (Test-Path -LiteralPath $sourceDirectory -PathType Container)) {
            continue
        }
        foreach ($file in Get-ChildItem -LiteralPath $sourceDirectory -Filter '*.png' -File) {
            $suffix = [string]$item.Suffix
            $name = if ([string]::IsNullOrWhiteSpace($suffix)) {
                $file.Name
            }
            else {
                $file.BaseName + '_' + $suffix + $file.Extension
            }
            $target = Join-Path $OutputDirectory $name
            if (Test-Path -LiteralPath $target) {
                throw "Duplicate aggregate view name: $name"
            }
            try {
                [void](New-Item `
                    -ItemType HardLink `
                    -Path (ConvertTo-VisualRegressionLongPath -Path $target) `
                    -Target (ConvertTo-VisualRegressionLongPath -Path $file.FullName))
            }
            catch {
                throw "Cannot hardlink aggregate view '$target' to '$($file.FullName)': $($_.Exception.Message)"
            }
        }
    }
}

function New-VisualRegressionAggregateViewStage {
    param(
        [Parameter(Mandatory)][object]$Context,
        [Parameter(Mandatory)][string]$OutputRoot
    )

    if (Test-Path -LiteralPath $OutputRoot) {
        Remove-Item -LiteralPath $OutputRoot -Recurse -Force
    }
    New-VisualRegressionAggregateLinkStage `
        -Source @(
            [pscustomobject]@{
                Directory = $Context.Capture.ScreenshotGrids
                Suffix = ''
            },
            [pscustomobject]@{
                Directory = $Context.Capture.BlendGrids
                Suffix = 'c_blend'
            },
            [pscustomobject]@{
                Directory = $Context.Capture.DiffGrids
                Suffix = 'd_diff'
            }
        ) `
        -OutputDirectory (Join-Path $OutputRoot $script:E2eAllGridDirectory)
}

function Publish-VisualRegressionAggregateViews {
    param(
        [Parameter(Mandatory)][object[]]$Context,
        [Parameter(Mandatory)][string]$TransactionRoot
    )

    $aggregateTransaction = Join-Path $TransactionRoot 'aggregate-views'
    [void](New-Item -ItemType Directory -Path $aggregateTransaction -Force)
    $suiteScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'suite.ps1'
    $tasks = @(
        foreach ($currentContext in $Context) {
            $taskContext = $currentContext
            $stageRoot = Join-Path `
                (Join-Path $aggregateTransaction 'stages') `
                $taskContext.SuiteRelativePath
            $taskName = "aggregate/$($taskContext.SuiteRelativePath.Replace('\', '/'))"
            [pscustomobject]@{
                Key = $taskName
                Priority = 10
                DependsOn = @()
                Ready = $null
                Start = {
                    Start-ThreadJob `
                        -Name $taskName `
                        -ScriptBlock {
                            param($Script, $CurrentContext, $OutputRoot)
                            $ErrorActionPreference = 'Stop'
                            . $Script
                            New-VisualRegressionAggregateViewStage `
                                -Context $CurrentContext `
                                -OutputRoot $OutputRoot
                        } `
                        -ArgumentList $suiteScript, $taskContext, $stageRoot
                }.GetNewClosure()
            }
        }
    )
    Invoke-VisualRegressionTaskGraph `
        -Task $tasks `
        -FailurePrefix 'E2E aggregate preparation task'

    $replacements = [ordered]@{}
    foreach ($currentContext in $Context) {
        $stageRoot = Join-Path `
            (Join-Path $aggregateTransaction 'stages') `
            $currentContext.SuiteRelativePath
        $replacements[$currentContext.Capture.AllGrids] = Join-Path `
            $stageRoot `
            $script:E2eAllGridDirectory
    }
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $aggregateTransaction
}

function New-VisualRegressionArtifactTasks {
    param(
        [Parameter(Mandatory)][object]$Context,
        [Parameter(Mandatory)][string]$Transaction,
        [Parameter(Mandatory)][string]$CapturedRoot,
        [Parameter(Mandatory)]
        [ValidateSet('Reference', 'Current')]
        [string]$CapturedTier,
        [AllowEmptyString()][string]$KeyPrefix = '',
        [bool]$PreserveCapturedTier,
        [scriptblock]$Ready
    )

    $suiteScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'suite.ps1'
    $postprocessScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'postprocess.ps1'
    $suite = [string]$Context.Suite
    $prepareKey = "${KeyPrefix}prepare/$suite"
    if ($Context.Generated) {
        $existingDirectory = $Context.Capture.ScreenshotGrids
        $capturedDirectory = Join-Path $CapturedRoot $script:E2eScreenshotGridDirectory
        $outputRoot = Join-Path (Join-Path $Transaction 'publish') $Context.SuiteRelativePath
        $comparator = $Context.Comparator
        [pscustomobject]@{
            Key = $prepareKey
            Priority = 80
            DependsOn = @()
            Ready = $Ready
            Start = {
                Start-ThreadJob -Name $prepareKey -ScriptBlock {
                    param(
                        $Script,
                        $ExistingDirectory,
                        $CapturedDirectory,
                        $OutputRoot,
                        $Comparator,
                        $CapturedTier,
                        $PreserveCapturedTier
                    )
                    $ErrorActionPreference = 'Stop'
                    . $Script
                    New-VisualRegressionGeneratedArtifactStage `
                        -ExistingDirectory $ExistingDirectory `
                        -CapturedDirectory $CapturedDirectory `
                        -OutputRoot $OutputRoot `
                        -Comparator $Comparator `
                        -CapturedTier $CapturedTier `
                        -PreserveCapturedTier:$PreserveCapturedTier
                } -ArgumentList (
                    $suiteScript,
                    $existingDirectory,
                    $capturedDirectory,
                    $outputRoot,
                    $comparator,
                    $CapturedTier,
                    $PreserveCapturedTier
                )
            }.GetNewClosure()
        }
        return
    }

    $captureRoot = $Context.CaptureRoot
    $prepareAction = "${CapturedTier}Prepare"
    [pscustomobject]@{
        Key = $prepareKey
        Priority = 80
        DependsOn = @()
        Ready = $Ready
        Start = {
            Start-ThreadJob -Name $prepareKey -ScriptBlock {
                param($Script, $Action, $Suite, $Transaction, $CaptureRoot, $CapturedRoot)
                $ErrorActionPreference = 'Stop'
                & $Script `
                    -Action $Action `
                    -Suite $Suite `
                    -Transaction $Transaction `
                    -CaptureRoot $CaptureRoot `
                    -CapturedRoot $CapturedRoot
            } -ArgumentList (
                $postprocessScript,
                $prepareAction,
                $suite,
                $Transaction,
                $captureRoot,
                $CapturedRoot
            )
        }.GetNewClosure()
    }
    $artifactKey = "${KeyPrefix}artifact/$suite/all"
    [pscustomobject]@{
        Key = $artifactKey
        Priority = 10
        DependsOn = @($prepareKey)
        Ready = $null
        Start = {
            Start-ThreadJob -Name $artifactKey -ScriptBlock {
                param($Script, $Suite, $Transaction, $CaptureRoot)
                $ErrorActionPreference = 'Stop'
                & $Script `
                    -Action All `
                    -Suite $Suite `
                    -Transaction $Transaction `
                    -CaptureRoot $CaptureRoot
            } -ArgumentList (
                $postprocessScript,
                $suite,
                $Transaction,
                $captureRoot
            )
        }.GetNewClosure()
    }
}

function Publish-VisualRegressionArtifacts {
    param(
        [Parameter(Mandatory)][object[]]$Context,
        [Parameter(Mandatory)][string]$Transaction
    )

    $replacements = [ordered]@{}
    foreach ($currentContext in $Context) {
        $suitePublish = Join-Path `
            (Join-Path $Transaction 'publish') `
            $currentContext.SuiteRelativePath
        if ($currentContext.Generated) {
            $replacements[$currentContext.CaptureRoot] = $suitePublish
            continue
        }
        $suiteStage = Join-Path `
            (Join-Path $Transaction 'stages') `
            $currentContext.SuiteRelativePath
        $metadata = Get-Content `
            -Raw `
            -LiteralPath (Join-Path $suiteStage 'postprocess.json') |
            ConvertFrom-Json
        $replacements[$currentContext.Capture.ScreenshotGrids] = Join-Path `
            $suitePublish `
            $script:E2eScreenshotGridDirectory
        if ($metadata.has_reference -and $metadata.has_current) {
            $replacements[$currentContext.Capture.PairGrids] = Join-Path `
                $suitePublish `
                $script:E2ePairGridDirectory
            $replacements[$currentContext.Capture.BlendGrids] = Join-Path `
                $suitePublish `
                $script:E2eBlendGridDirectory
            $replacements[$currentContext.Capture.DiffGrids] = Join-Path `
                $suitePublish `
                $script:E2eDiffGridDirectory
        }
    }
    $artifactContexts = $Context
    $artifactTransaction = $Transaction
    Publish-VisualRegressionTransaction `
        -Replacements $replacements `
        -TransactionRoot $Transaction `
        -AfterPublish {
            Publish-VisualRegressionAggregateViews `
                -Context $artifactContexts `
                -TransactionRoot $artifactTransaction
        }
}
