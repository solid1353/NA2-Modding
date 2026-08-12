[CmdletBinding()]
param([switch]$Preserve)

$ErrorActionPreference = 'Stop'
$captureRepository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\captures'))
if (-not (Test-Path -LiteralPath $captureRepository -PathType Container)) {
    throw "E2E capture repository is unavailable: $captureRepository"
}

& git -C $captureRepository add --all
if ($LASTEXITCODE -ne 0) {
    throw 'Could not stage the current E2E capture changes.'
}

if ($Preserve) {
    & git -C $captureRepository diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'No E2E capture changes to commit.' -ForegroundColor Yellow
        return
    }
    if ($LASTEXITCODE -ne 1) {
        throw 'Could not inspect the current E2E capture changes.'
    }

    & git -C $captureRepository commit -m 'Update captures'
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not commit the current E2E capture changes.'
    }
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

& git -C $captureRepository commit --amend -m 'Initial commit'
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
