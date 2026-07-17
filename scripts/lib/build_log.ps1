Set-StrictMode -Version Latest
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
    if ($value -notmatch '^@logs/na2/builds/([A-Za-z0-9][A-Za-z0-9._-]*)$') {
        throw "Invalid build record path in builds.tsv: $value"
    }
    $buildId = $Matches[1]
    $recordDirectory = Join-Path (Join-Path $LogDirectory 'builds') $buildId
    if (-not (Test-Path -LiteralPath $recordDirectory -PathType Container)) {
        throw "builds.tsv references a missing record: $value"
    }
    return $buildId
}

function Read-Na2BuildMap {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$LogDirectory)

    $mapPath = Join-Path $LogDirectory 'builds.tsv'
    if (-not (Test-Path -LiteralPath $mapPath -PathType Leaf)) {
        return [pscustomobject]@{
            CurrentBuildId = $null
            PreviousBuildId = $null
        }
    }

    $lines = @([IO.File]::ReadAllLines($mapPath))
    if ($lines.Count -ne 3 -or $lines[0] -cne "iso`tbuild_record") {
        throw 'builds.tsv must contain its exact header and exactly two ISO rows.'
    }
    $rows = @($lines | Select-Object -Skip 1 | ConvertFrom-Csv -Delimiter "`t" -Header iso, build_record)
    $expectedIsoRows = @('@build/Current.iso', '@build/Previous.iso')
    $actualIsoText = @($rows.iso | Sort-Object) -join "`n"
    $expectedIsoText = @($expectedIsoRows | Sort-Object) -join "`n"
    if ($actualIsoText -cne $expectedIsoText) {
        throw 'builds.tsv must contain one row each for @build/Current.iso and @build/Previous.iso.'
    }

    $currentRecord = [string]($rows | Where-Object iso -CEQ '@build/Current.iso').build_record
    $previousRecord = [string]($rows | Where-Object iso -CEQ '@build/Previous.iso').build_record
    $currentBuildId = ConvertFrom-Na2BuildRecordPath `
        -BuildRecord $currentRecord `
        -LogDirectory $LogDirectory
    if ([string]::IsNullOrWhiteSpace($currentBuildId)) {
        throw 'The @build/Current.iso row in builds.tsv must reference a retained build record.'
    }
    $previousBuildId = ConvertFrom-Na2BuildRecordPath `
        -BuildRecord $previousRecord `
        -LogDirectory $LogDirectory
    if ($currentBuildId -eq $previousBuildId) {
        throw 'Current.iso and Previous.iso cannot reference the same build record.'
    }

    return [pscustomobject]@{
        CurrentBuildId = $currentBuildId
        PreviousBuildId = $previousBuildId
    }
}

function Set-Na2BuildMap {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$LogDirectory,
        [Parameter(Mandatory = $true)][string]$CurrentBuildId,
        [AllowNull()][string]$PreviousBuildId
    )

    if ($CurrentBuildId -eq $PreviousBuildId) {
        $PreviousBuildId = $null
    }
    foreach ($buildId in @($CurrentBuildId, $PreviousBuildId)) {
        if ([string]::IsNullOrWhiteSpace($buildId)) {
            continue
        }
        if ($buildId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
            throw "Invalid build record ID: $buildId"
        }
        $recordDirectory = Join-Path (Join-Path $LogDirectory 'builds') $buildId
        if (-not (Test-Path -LiteralPath $recordDirectory -PathType Container)) {
            throw "Cannot map an ISO to a missing build record: @logs/na2/builds/$buildId"
        }
    }

    $previousRecord = if ([string]::IsNullOrWhiteSpace($PreviousBuildId)) {
        ''
    }
    else {
        "@logs/na2/builds/$PreviousBuildId"
    }
    $content = @(
        "iso`tbuild_record"
        "@build/Current.iso`t@logs/na2/builds/$CurrentBuildId"
        "@build/Previous.iso`t$previousRecord"
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
        [Parameter(Mandatory = $true)][string]$CurrentIso,
        [AllowNull()][string]$PreviousIso,
        [Parameter(Mandatory = $true)][string]$Profile,
        [Parameter(Mandatory = $true)][psobject]$ProjectPaths
    )

    $rotation = if ($Rotated) { 'yes' } else { 'no' }
    $currentPortable = ConvertTo-Na2PortableText -Text $CurrentIso -ProjectPaths $ProjectPaths
    $previousPortable = if ([string]::IsNullOrWhiteSpace($PreviousIso)) {
        ''
    }
    else {
        ConvertTo-Na2PortableText -Text $PreviousIso -ProjectPaths $ProjectPaths
    }
    $profilePortable = ConvertTo-Na2PortableText -Text $Profile -ProjectPaths $ProjectPaths
    $recordPortable = ConvertTo-Na2PortableText -Text $RecordDirectory -ProjectPaths $ProjectPaths
    $content = @(
        "timestamp_utc`tresult`trotation`tprofile`tcurrent_iso`tprevious_iso`tbuild_record"
        (
            (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') + "`t" +
            "$Result`t$rotation`t$profilePortable`t$currentPortable`t$previousPortable`t$recordPortable"
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
        [AllowNull()][string]$CurrentBuildId,
        [AllowNull()][string]$PreviousBuildId
    )

    $buildRoot = Join-Path $LogDirectory 'builds'
    if (-not (Test-Path -LiteralPath $buildRoot -PathType Container)) {
        return
    }
    $retained = @($CurrentBuildId, $PreviousBuildId) |
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
        [Parameter(Mandatory = $true)][string]$CurrentIso,
        [AllowNull()][string]$PreviousIso,
        [Parameter(Mandatory = $true)][string]$Profile,
        [Parameter(Mandatory = $true)][psobject]$ProjectPaths
    )

    $buildRoot = Join-Path $LogDirectory 'builds'
    $recordDirectory = Join-Path $buildRoot $BuildId
    if (-not (Test-Path -LiteralPath $recordDirectory -PathType Container)) {
        throw "Profile build record does not exist: builds/$BuildId"
    }
    $buildMap = Read-Na2BuildMap -LogDirectory $LogDirectory
    $currentBuildId = $buildMap.CurrentBuildId
    $previousBuildId = $buildMap.PreviousBuildId

    $reused = $false
    if ($Result -eq 'unchanged' -and -not [string]::IsNullOrWhiteSpace($currentBuildId)) {
        Remove-Item -LiteralPath $recordDirectory -Recurse -Force
        $effectiveCurrentBuildId = $currentBuildId
        $reused = $true
    }
    else {
        Write-Na2BuildResult `
            -RecordDirectory $recordDirectory `
            -Result $Result `
            -Rotated $Rotated `
            -CurrentIso $CurrentIso `
            -PreviousIso $PreviousIso `
            -Profile $Profile `
            -ProjectPaths $ProjectPaths
        $effectiveCurrentBuildId = $BuildId
    }

    $previousExists = -not [string]::IsNullOrWhiteSpace($PreviousIso) -and
        (Test-Path -LiteralPath $PreviousIso -PathType Leaf)
    $effectivePreviousBuildId = if ($Result -eq 'updated' -and $Rotated) {
        $currentBuildId
    }
    elseif ($previousExists) {
        $previousBuildId
    }
    else {
        $null
    }

    Set-Na2BuildMap `
        -LogDirectory $LogDirectory `
        -CurrentBuildId $effectiveCurrentBuildId `
        -PreviousBuildId $effectivePreviousBuildId
    Remove-Na2UnreferencedBuildRecords `
        -LogDirectory $LogDirectory `
        -CurrentBuildId $effectiveCurrentBuildId `
        -PreviousBuildId $effectivePreviousBuildId

    return [pscustomobject]@{
        BuildId = $effectiveCurrentBuildId
        BuildRecord = "@logs/na2/builds/$effectiveCurrentBuildId"
        Reused = $reused
    }
}
