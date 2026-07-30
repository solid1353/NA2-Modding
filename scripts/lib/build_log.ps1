Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'project_paths.ps1')
. (Join-Path $PSScriptRoot 'run_log.ps1')

function ConvertFrom-Na2BuildRecordPath {
    [CmdletBinding()]
    param(
        [AllowEmptyString()][string]$BuildRecord,
        [Parameter(Mandatory = $true)][string]$LogDirectory
    )

    if ([string]::IsNullOrWhiteSpace($BuildRecord)) {
        return $null
    }
    $value = $BuildRecord.Trim().Replace('\', '/')
    if ($value -notmatch '^@logs/na228/builds/([A-Za-z0-9][A-Za-z0-9._-]*)$') {
        throw "Invalid build record path in builds.tsv: $value"
    }
    $buildId = $Matches[1]
    $recordDirectory = Join-Path (Join-Path $LogDirectory 'builds') $buildId
    if (-not (Test-Path -LiteralPath $recordDirectory -PathType Container)) {
        throw "builds.tsv references a missing record: $value"
    }
    return $buildId
}

function Get-Na2ConfiguredIsoMapKeys {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][psobject]$ProjectPaths)

    [pscustomobject]@{
        Latest = ConvertTo-Na2ProjectPath `
            -Path $ProjectPaths.files.latest_iso `
            -ProjectPaths $ProjectPaths
        Previous = ConvertTo-Na2ProjectPath `
            -Path $ProjectPaths.files.previous_iso `
            -ProjectPaths $ProjectPaths
    }
}

function Read-Na2BuildMap {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$LogDirectory,
        [Parameter(Mandatory = $true)][psobject]$ProjectPaths
    )

    $mapPath = Join-Path $LogDirectory 'builds.tsv'
    if (-not (Test-Path -LiteralPath $mapPath -PathType Leaf)) {
        return [pscustomobject]@{
            LatestBuildId = $null
            PreviousBuildId = $null
        }
    }

    $lines = @([IO.File]::ReadAllLines($mapPath))
    if ($lines.Count -ne 3 -or $lines[0] -cne "iso`tbuild_record") {
        throw 'builds.tsv must contain its exact header and exactly two ISO rows.'
    }
    $rows = @($lines | Select-Object -Skip 1 | ConvertFrom-Csv -Delimiter "`t" -Header iso, build_record)
    $isoKeys = Get-Na2ConfiguredIsoMapKeys -ProjectPaths $ProjectPaths
    $migrated = $rows[0].iso -cne $isoKeys.Latest -or
        $rows[1].iso -cne $isoKeys.Previous
    if ($migrated) {
        $previousSuffix = $isoKeys.Previous.Substring($isoKeys.Previous.LastIndexOf(' - '))
        $legacyLatest = ([string]$rows[0].iso).EndsWith(
            ' - Current.iso',
            [StringComparison]::Ordinal
        )
        if (
            -not $legacyLatest -or
            -not ([string]$rows[1].iso).EndsWith($previousSuffix, [StringComparison]::Ordinal)
        ) {
            throw "builds.tsv must contain one row each for $($isoKeys.Latest) and $($isoKeys.Previous)."
        }
    }

    $latestRecord = [string]$rows[0].build_record
    $previousRecord = [string]$rows[1].build_record
    $latestBuildId = ConvertFrom-Na2BuildRecordPath `
        -BuildRecord $latestRecord `
        -LogDirectory $LogDirectory
    if ([string]::IsNullOrWhiteSpace($latestBuildId)) {
        throw "The $($isoKeys.Latest) row in builds.tsv must reference a retained build record."
    }
    $previousBuildId = ConvertFrom-Na2BuildRecordPath `
        -BuildRecord $previousRecord `
        -LogDirectory $LogDirectory
    if ($latestBuildId -eq $previousBuildId) {
        throw 'Latest and Previous ISOs cannot reference the same build record.'
    }
    if ($migrated) {
        Set-Na2BuildMap `
            -LogDirectory $LogDirectory `
            -LatestBuildId $latestBuildId `
            -PreviousBuildId $previousBuildId `
            -ProjectPaths $ProjectPaths
    }

    return [pscustomobject]@{
        LatestBuildId = $latestBuildId
        PreviousBuildId = $previousBuildId
    }
}

function Set-Na2BuildMap {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$LogDirectory,
        [Parameter(Mandatory = $true)][string]$LatestBuildId,
        [AllowNull()][string]$PreviousBuildId,
        [Parameter(Mandatory = $true)][psobject]$ProjectPaths
    )

    if ($LatestBuildId -eq $PreviousBuildId) {
        $PreviousBuildId = $null
    }
    foreach ($buildId in @($LatestBuildId, $PreviousBuildId)) {
        if ([string]::IsNullOrWhiteSpace($buildId)) {
            continue
        }
        if ($buildId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
            throw "Invalid build record ID: $buildId"
        }
        $recordDirectory = Join-Path (Join-Path $LogDirectory 'builds') $buildId
        if (-not (Test-Path -LiteralPath $recordDirectory -PathType Container)) {
            throw "Cannot map an ISO to a missing build record: @logs/na228/builds/$buildId"
        }
    }

    $previousRecord = if ([string]::IsNullOrWhiteSpace($PreviousBuildId)) {
        ''
    }
    else {
        "@logs/na228/builds/$PreviousBuildId"
    }
    $isoKeys = Get-Na2ConfiguredIsoMapKeys -ProjectPaths $ProjectPaths
    $content = @(
        "iso`tbuild_record"
        "$($isoKeys.Latest)`t@logs/na228/builds/$LatestBuildId"
        "$($isoKeys.Previous)`t$previousRecord"
    ) -join "`n"
    Set-Na2Utf8FileAtomic `
        -Path (Join-Path $LogDirectory 'builds.tsv') `
        -Content ($content + "`n")
}

function Write-Na2BuildResult {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$RecordDirectory,
        [Parameter(Mandatory = $true)][ValidateSet('unchanged', 'updated')][string]$Result,
        [Parameter(Mandatory = $true)][bool]$Rotated,
        [Parameter(Mandatory = $true)][string]$LatestIso,
        [AllowNull()][string]$PreviousIso,
        [Parameter(Mandatory = $true)][string]$Profile,
        [Parameter(Mandatory = $true)][psobject]$ProjectPaths
    )

    $rotation = if ($Rotated) { 'yes' } else { 'no' }
    $latestPortable = ConvertTo-Na2PortableText -Text $LatestIso -ProjectPaths $ProjectPaths
    $previousPortable = if ([string]::IsNullOrWhiteSpace($PreviousIso)) {
        ''
    }
    else {
        ConvertTo-Na2PortableText -Text $PreviousIso -ProjectPaths $ProjectPaths
    }
    $profilePortable = ConvertTo-Na2PortableText -Text $Profile -ProjectPaths $ProjectPaths
    $recordPortable = ConvertTo-Na2PortableText -Text $RecordDirectory -ProjectPaths $ProjectPaths
    $content = @(
        "timestamp_utc`tresult`trotation`tprofile`tlatest_iso`tprevious_iso`tbuild_record"
        (
            (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') + "`t" +
            "$Result`t$rotation`t$profilePortable`t$latestPortable`t$previousPortable`t$recordPortable"
        )
    ) -join "`n"
    $content += "`n"
    if (Test-Na2WindowsAbsolutePath -Text $content) {
        throw 'Refusing to write build_result.tsv with an absolute path.'
    }
    Set-Na2Utf8FileAtomic -Path (Join-Path $RecordDirectory 'build_result.tsv') -Content $content
}

function Remove-Na2UnreferencedBuildRecords {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$LogDirectory,
        [AllowNull()][string]$LatestBuildId,
        [AllowNull()][string]$PreviousBuildId
    )

    $buildRoot = Join-Path $LogDirectory 'builds'
    if (-not (Test-Path -LiteralPath $buildRoot -PathType Container)) {
        return
    }
    $retained = @($LatestBuildId, $PreviousBuildId) |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Select-Object -Unique
    foreach ($record in Get-ChildItem -LiteralPath $buildRoot -Directory -Force) {
        if ($record.Name -in $retained) {
            continue
        }
        if (($record.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Refusing to remove unexpected linked build record: $($record.Name)"
        }
        Remove-Item -LiteralPath $record.FullName -Recurse -Force
    }
}

function Complete-Na2BuildRecord {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$LogDirectory,
        [Parameter(Mandatory = $true)][string]$BuildId,
        [Parameter(Mandatory = $true)][ValidateSet('unchanged', 'updated')][string]$Result,
        [Parameter(Mandatory = $true)][bool]$Rotated,
        [Parameter(Mandatory = $true)][string]$LatestIso,
        [AllowNull()][string]$PreviousIso,
        [Parameter(Mandatory = $true)][string]$Profile,
        [Parameter(Mandatory = $true)][psobject]$ProjectPaths
    )

    $buildRoot = Join-Path $LogDirectory 'builds'
    $recordDirectory = Join-Path $buildRoot $BuildId
    if (-not (Test-Path -LiteralPath $recordDirectory -PathType Container)) {
        throw "Profile build record does not exist: builds/$BuildId"
    }
    $buildMap = Read-Na2BuildMap `
        -LogDirectory $LogDirectory `
        -ProjectPaths $ProjectPaths
    $latestBuildId = $buildMap.LatestBuildId
    $previousBuildId = $buildMap.PreviousBuildId

    Write-Na2BuildResult `
        -RecordDirectory $recordDirectory `
        -Result $Result `
        -Rotated $Rotated `
        -LatestIso $LatestIso `
        -PreviousIso $PreviousIso `
        -Profile $Profile `
        -ProjectPaths $ProjectPaths
    $effectiveLatestBuildId = $BuildId

    $previousExists = -not [string]::IsNullOrWhiteSpace($PreviousIso) -and
        (Test-Path -LiteralPath $PreviousIso -PathType Leaf)
    $effectivePreviousBuildId = if ($Result -eq 'updated' -and $Rotated) {
        $latestBuildId
    }
    elseif ($previousExists) {
        $previousBuildId
    }
    else {
        $null
    }

    Set-Na2BuildMap `
        -LogDirectory $LogDirectory `
        -LatestBuildId $effectiveLatestBuildId `
        -PreviousBuildId $effectivePreviousBuildId `
        -ProjectPaths $ProjectPaths
    Remove-Na2UnreferencedBuildRecords `
        -LogDirectory $LogDirectory `
        -LatestBuildId $effectiveLatestBuildId `
        -PreviousBuildId $effectivePreviousBuildId

    return [pscustomobject]@{
        BuildId = $effectiveLatestBuildId
        BuildRecord = "@logs/na228/builds/$effectiveLatestBuildId"
    }
}
