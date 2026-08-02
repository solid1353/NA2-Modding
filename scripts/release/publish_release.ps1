[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Version
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '..\lib\paths.ps1')
$paths = Get-Na2LocalPaths -AllowMissing
$repository = [IO.Path]::GetFullPath($paths.repository)
$toolchainPath = Join-Path $PSScriptRoot 'toolchain.json'
$toolchain = Get-Content -Raw -LiteralPath $toolchainPath | ConvertFrom-Json
$manifestRelative = [string]$toolchain.release_manifest
$manifestPath = [IO.Path]::GetFullPath((Join-Path $repository $manifestRelative))
$builderPath = Join-Path $PSScriptRoot 'build_release.ps1'

function Invoke-ReleaseGit {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$GitArguments,

        [switch]$Capture
    )

    $output = @(& git -C $repository @GitArguments 2>&1)
    if ($LASTEXITCODE -ne 0) {
        $details = ($output | ForEach-Object { [string]$_ }) -join "`n"
        throw "git $($GitArguments -join ' ') failed.`n$details"
    }
    if ($Capture) {
        return $output
    }
    foreach ($line in $output) {
        Write-Host ([string]$line)
    }
}

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Release manifest is missing: $manifestRelative"
}
if (-not (Test-Path -LiteralPath $builderPath -PathType Leaf)) {
    throw 'Release builder is missing.'
}

$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$targetVersion = if ([string]::IsNullOrWhiteSpace($Version)) {
    [string]$manifest.product_version
}
else {
    $Version.Trim()
}
if ($targetVersion -notmatch '^\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?$') {
    throw "Release version must be SemVer-like text such as 0.1.0 or 0.1.0-dev: $targetVersion"
}

$executableMatch = [regex]::Match(
    [string]$manifest.executable_name,
    '^(?<stem>.+)_v[^/\\]+\.exe$',
    [Text.RegularExpressions.RegexOptions]::IgnoreCase
)
if (-not $executableMatch.Success) {
    throw 'Release executable_name must follow <product>_v<version>.exe.'
}
$targetExecutable = "$($executableMatch.Groups['stem'].Value)_v$targetVersion.exe"
$tag = "v$targetVersion"

$status = @(Invoke-ReleaseGit -GitArguments @(
    'status', '--porcelain=v1', '--untracked-files=all'
) -Capture)
if ($status.Count -ne 0) {
    throw 'Refusing to publish from a dirty Git tree. Commit or stash every change first.'
}

$remoteTag = @(& git -C $repository ls-remote --exit-code --tags origin "refs/tags/$tag" 2>&1)
$remoteTagExit = $LASTEXITCODE
if ($remoteTagExit -eq 0) {
    Write-Host "[release] $tag already exists on origin; nothing was published." -ForegroundColor Yellow
    return
}
if ($remoteTagExit -ne 2) {
    $details = ($remoteTag | ForEach-Object { [string]$_ }) -join "`n"
    throw "Could not check origin for $tag.`n$details"
}

$manifestChanged =
    [string]$manifest.product_version -cne $targetVersion -or
    [string]$manifest.executable_name -cne $targetExecutable
if ($manifestChanged) {
    $manifest.product_version = $targetVersion
    $manifest.executable_name = $targetExecutable
    $temporaryManifest = "$manifestPath.publish.tmp"
    if (Test-Path -LiteralPath $temporaryManifest) {
        throw "Reserved manifest staging file already exists: $temporaryManifest"
    }
    try {
        $json = ($manifest | ConvertTo-Json -Depth 10).Replace("`r`n", "`n")
        [IO.File]::WriteAllText(
            $temporaryManifest,
            $json + "`n",
            [Text.UTF8Encoding]::new($false)
        )
        [IO.File]::Move($temporaryManifest, $manifestPath, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporaryManifest) {
            Remove-Item -LiteralPath $temporaryManifest -Force
        }
    }

    Invoke-ReleaseGit -GitArguments @('add', '--', $manifestRelative)
    Invoke-ReleaseGit -GitArguments @(
        'commit', '-m', "Prepare $($manifest.product_name) $tag"
    )
    Write-Host "[release] Prepared $tag in the release manifest." -ForegroundColor Cyan
}
else {
    Write-Host "[release] Using the manifest's existing $tag identity." -ForegroundColor Cyan
}

$status = @(Invoke-ReleaseGit -GitArguments @(
    'status', '--porcelain=v1', '--untracked-files=all'
) -Capture)
if ($status.Count -ne 0) {
    throw 'The release-preparation commit did not leave a clean Git tree.'
}

Write-Host '[release] Building and validating the production package...' -ForegroundColor Cyan
& $builderPath
if ($LASTEXITCODE -ne 0) {
    throw 'Production release validation failed; the release commit was not pushed.'
}

$branch = (Invoke-ReleaseGit -GitArguments @(
    'symbolic-ref', '--quiet', '--short', 'HEAD'
) -Capture | Select-Object -First 1).ToString().Trim()
if ([string]::IsNullOrWhiteSpace($branch)) {
    throw 'Release publication requires a named Git branch, not detached HEAD.'
}

Invoke-ReleaseGit -GitArguments @('push', 'origin', "HEAD:refs/heads/$branch")

$localTagType = @(& git -C $repository cat-file -t $tag 2>$null)
$localTagExit = $LASTEXITCODE
if ($localTagExit -eq 0) {
    if (($localTagType | Select-Object -First 1).Trim() -cne 'tag') {
        throw "Local $tag exists but is not an annotated tag."
    }
    $tagCommit = (Invoke-ReleaseGit -GitArguments @(
        'rev-parse', "$tag^{commit}"
    ) -Capture | Select-Object -First 1).ToString().Trim()
    $headCommit = (Invoke-ReleaseGit -GitArguments @(
        'rev-parse', 'HEAD'
    ) -Capture | Select-Object -First 1).ToString().Trim()
    if ($tagCommit -cne $headCommit) {
        throw "Local $tag does not point at the release commit."
    }
    Write-Host "[release] Resuming with existing local annotated tag $tag." -ForegroundColor Cyan
}
else {
    Invoke-ReleaseGit -GitArguments @(
        'tag', '-a', $tag, '-m', "$($manifest.product_name) $targetVersion"
    )
}

Invoke-ReleaseGit -GitArguments @('push', 'origin', "refs/tags/$tag")
Write-Host "[release] Published $tag. GitHub Actions will create the GitHub Release." -ForegroundColor Green
