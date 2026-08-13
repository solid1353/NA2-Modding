[CmdletBinding()]
param([switch]$Preserve)

$ErrorActionPreference = 'Stop'
$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$suiteRepository = Join-Path $repository 'e2e\suites'
$captureRepository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\captures'))
if (-not (Test-Path -LiteralPath $captureRepository -PathType Container)) {
    throw "E2E capture repository is unavailable: $captureRepository"
}

function Commit-E2eSuites {
    $suiteStatus = @(& git -C $repository status --porcelain --untracked-files=all -- 'e2e/suites')
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not inspect the current E2E suite changes.'
    }
    if ($suiteStatus.Count -eq 0) {
        Write-Host 'No E2E suite changes to commit.' -ForegroundColor Yellow
        return
    }

    & git -C $repository add --all -- 'e2e/suites'
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not stage the current E2E suite changes.'
    }
    & git -C $repository commit -m 'Update E2E suites' -- 'e2e/suites'
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not commit the current E2E suite changes.'
    }
}

& git -C $captureRepository add --all
if ($LASTEXITCODE -ne 0) {
    throw 'Could not stage the current E2E capture changes.'
}

if ($Preserve) {
    & git -C $captureRepository diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'No E2E capture changes to commit.' -ForegroundColor Yellow
    }
    elseif ($LASTEXITCODE -ne 1) {
        throw 'Could not inspect the current E2E capture changes.'
    }
    else {
        & git -C $captureRepository commit -m 'Update captures'
        if ($LASTEXITCODE -ne 0) {
            throw 'Could not commit the current E2E capture changes.'
        }
    }
    Commit-E2eSuites
    return
}

$commitCount = & git -C $captureRepository rev-list --count HEAD
if ($LASTEXITCODE -ne 0 -or $commitCount -notmatch '^\d+$' -or [int]$commitCount -lt 1) {
    throw 'Could not resolve the E2E capture repository commit count.'
}

if ([int]$commitCount -gt 1) {
    $rootCommit = & git -C $captureRepository rev-list --max-parents=0 HEAD
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not resolve the E2E capture repository root commit.'
    }

    & git -C $captureRepository reset --soft $rootCommit
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not reset the E2E capture repository to its root commit.'
    }
}

& git -C $captureRepository commit --amend --allow-empty -m 'Initial commit'
if ($LASTEXITCODE -ne 0) {
    throw 'Could not consolidate the E2E capture repository history.'
}

& git -C $captureRepository reflog expire --expire=now --all
if ($LASTEXITCODE -ne 0) {
    throw 'Could not expire the E2E capture repository reflogs.'
}

& git -C $captureRepository gc --prune=now
if ($LASTEXITCODE -ne 0) {
    throw 'Could not compact the E2E capture repository.'
}

Commit-E2eSuites
