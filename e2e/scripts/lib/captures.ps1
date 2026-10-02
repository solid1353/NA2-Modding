function Clear-VisualRegressionCaptureRepository {
    param([Parameter(Mandatory)][string]$CaptureRepository)

    foreach ($item in @(Get-ChildItem -LiteralPath $CaptureRepository -Force)) {
        if ($script:E2eCaptureRepositoryMetadataNames -ccontains $item.Name) {
            continue
        }
        Remove-Item -LiteralPath $item.FullName -Recurse -Force
    }
}

function Assert-VisualRegressionCaptureGitBaseline {
    param([Parameter(Mandatory)][string]$CaptureRepository)

    $captureRoot = [IO.Path]::GetFullPath($CaptureRepository)
    if (-not (Test-Path -LiteralPath $captureRoot -PathType Container)) {
        throw "E2E capture repository does not exist: $captureRoot"
    }
    $topLevelOutput = @(
        & git -C $captureRoot rev-parse --show-toplevel 2>&1
    )
    if ($LASTEXITCODE -ne 0 -or $topLevelOutput.Count -ne 1) {
        throw "E2E capture Git baseline is unavailable: $($topLevelOutput -join ' ')"
    }
    $topLevel = [IO.Path]::GetFullPath([string]$topLevelOutput[0])
    if (-not [string]::Equals(
        $topLevel,
        $captureRoot,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        throw "E2E captures are not their own Git repository: $captureRoot"
    }
    $headOutput = @(& git -C $captureRoot rev-parse --verify HEAD 2>&1)
    if ($LASTEXITCODE -ne 0 -or $headOutput.Count -ne 1) {
        throw "E2E capture Git HEAD is unavailable: $($headOutput -join ' ')"
    }
}

function Get-VisualRegressionCaptureGitChanges {
    param([Parameter(Mandatory)][string]$CaptureRepository)

    $captureRoot = [IO.Path]::GetFullPath($CaptureRepository)
    $changes = [Collections.Generic.List[object]]::new()
    $trackedOutput = @(
        & git -C $captureRoot -c core.quotepath=false `
            diff --name-status --no-renames HEAD -- . 2>&1
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to read E2E capture changes: $($trackedOutput -join ' ')"
    }
    foreach ($line in $trackedOutput) {
        $separator = ([string]$line).IndexOf("`t")
        if ($separator -lt 1) {
            throw "Git returned an invalid E2E capture change: $line"
        }
        $status = ([string]$line).Substring(0, $separator)
        $path = ([string]$line).Substring($separator + 1).Replace('\', '/')
        $kind = if ($status.StartsWith('A', [StringComparison]::Ordinal)) {
            'Added'
        }
        elseif ($status.StartsWith('D', [StringComparison]::Ordinal)) {
            'Deleted'
        }
        else { 'Modified' }
        $changes.Add([pscustomobject]@{
            Path = $path
            Kind = $kind
        })
    }
    $untrackedOutput = @(
        & git -C $captureRoot -c core.quotepath=false `
            ls-files --others --exclude-standard -- . 2>&1
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to read untracked E2E captures: $($untrackedOutput -join ' ')"
    }
    foreach ($path in $untrackedOutput) {
        $changes.Add([pscustomobject]@{
            Path = ([string]$path).Replace('\', '/')
            Kind = 'Added'
        })
    }
    return [object[]]$changes
}

function Get-VisualRegressionRequestCaptureFilter {
    param([Parameter(Mandatory)][object]$Request)

    $suite = [string]$Request.Suite
    $generated = [bool]$Request.Generated
    $family = [string]$Request.GeneratedFamily
    $storagePath = if ($generated) {
        Get-VisualRegressionGeneratedStorageSuite -Family $family
    }
    else { $suite }
    $rangePrefixes = $null
    if ($generated -and
        -not [string]::IsNullOrWhiteSpace([string]$Request.MovesetRange)) {
        $rangePrefixes = [string[]]@(
            Get-VisualRegressionGeneratedRangePrefixes `
                -Family $family `
                -Range ([string]$Request.MovesetRange)
        )
    }
    $movesetSubfamily = if ($suite -ceq "$($script:E2eGeneratedMovesetSuiteName)/base") {
        'base'
    }
    elseif ($suite -ceq "$($script:E2eGeneratedMovesetSuiteName)/specials") {
        'specials'
    }
    else { $null }
    [pscustomobject]@{
        Suite = $suite
        PathPrefix = $storagePath.Trim('/') + '/'
        Generated = $generated
        ArtifactDirectories = [string[]]$script:E2eStableCaptureDirectories
        RangePrefixes = $rangePrefixes
        MovesetSubfamily = $movesetSubfamily
    }
}

function Test-VisualRegressionCaptureChangeSelected {
    param(
        [Parameter(Mandatory)][object]$Change,
        [Parameter(Mandatory)][object]$Filter
    )

    $path = [string]$Change.Path
    if (-not $path.StartsWith(
        [string]$Filter.PathPrefix,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        return $false
    }
    $relativePath = $path.Substring(([string]$Filter.PathPrefix).Length)
    $artifactDirectory = @($relativePath.Split('/'))[0]
    if ($Filter.ArtifactDirectories -inotcontains $artifactDirectory) {
        return $false
    }
    if (-not $Filter.Generated) {
        return $true
    }
    $name = [IO.Path]::GetFileName($path)
    if ($null -ne $Filter.RangePrefixes -and @(
        $Filter.RangePrefixes | Where-Object {
            $name.StartsWith($_, [StringComparison]::OrdinalIgnoreCase)
        }
    ).Count -eq 0) {
        return $false
    }
    if ($Filter.MovesetSubfamily -ceq 'base') {
        return $name -match '_(?:base|mode_[^_]+)(?:_|\.png$)'
    }
    if ($Filter.MovesetSubfamily -ceq 'specials') {
        return $name -match '_specials(?:_|\.png$)'
    }
    return $true
}

function Get-VisualRegressionCaptureRegression {
    param(
        [Parameter(Mandatory)][object[]]$Request,
        [Parameter(Mandatory)][string]$CaptureRepository
    )

    $changes = @(Get-VisualRegressionCaptureGitChanges `
        -CaptureRepository $CaptureRepository)
    $suiteChanges = [Collections.Generic.List[object]]::new()
    $added = 0
    $modified = 0
    $deleted = 0
    foreach ($suiteRequest in $Request) {
        $filter = Get-VisualRegressionRequestCaptureFilter -Request $suiteRequest
        $selected = @(
            $changes | Where-Object {
                Test-VisualRegressionCaptureChangeSelected `
                    -Change $_ `
                    -Filter $filter
            }
        )
        if ($selected.Count -eq 0) {
            continue
        }
        $suiteChange = [pscustomobject]@{
            Suite = [string]$suiteRequest.Suite
            Added = @($selected | Where-Object Kind -CEQ 'Added').Count
            Modified = @($selected | Where-Object Kind -CEQ 'Modified').Count
            Deleted = @($selected | Where-Object Kind -CEQ 'Deleted').Count
        }
        $suiteChanges.Add($suiteChange)
        $added += $suiteChange.Added
        $modified += $suiteChange.Modified
        $deleted += $suiteChange.Deleted
    }
    [pscustomobject]@{
        Regression = $(if ($suiteChanges.Count -gt 0) { 'changed' } else { 'unchanged' })
        Suites = $Request.Count
        ChangedSuites = $suiteChanges.Count
        Added = $added
        Modified = $modified
        Deleted = $deleted
        SuiteChanges = [object[]]$suiteChanges
    }
}
