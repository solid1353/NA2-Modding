Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'paths.ps1')
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
    param([Parameter(Mandatory = $true)][psobject]$Paths)

    [pscustomobject]@{
        Latest = ConvertTo-Na2ProjectPath `
            -Path $Paths.files.latest_iso `
            -Paths $Paths
        Previous = ConvertTo-Na2ProjectPath `
            -Path $Paths.files.previous_iso `
            -Paths $Paths
        E2eTest = ConvertTo-Na2ProjectPath `
            -Path $Paths.files.e2e_test_iso `
            -Paths $Paths
    }
}

function Read-Na2BuildMap {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$LogDirectory,
        [Parameter(Mandatory = $true)][psobject]$Paths
    )

    $mapPath = Join-Path $LogDirectory 'builds.tsv'
    if (-not (Test-Path -LiteralPath $mapPath -PathType Leaf)) {
        return [pscustomobject]@{
            LatestBuildId = $null
            PreviousBuildId = $null
            E2eTestBuildId = $null
        }
    }

    $lines = @([IO.File]::ReadAllLines($mapPath))
    if ($lines.Count -lt 3 -or $lines[0] -cne "iso`tbuild_record") {
        throw 'builds.tsv must contain its exact header and at least Latest/Previous rows.'
    }
    $rows = @($lines | Select-Object -Skip 1 | ConvertFrom-Csv -Delimiter "`t" -Header iso, build_record)
    $isoKeys = Get-Na2ConfiguredIsoMapKeys -Paths $Paths
    $rowsByIso = @{}
    foreach ($row in $rows) {
        $iso = [string]$row.iso
        if ([string]::IsNullOrWhiteSpace($iso) -or $rowsByIso.ContainsKey($iso)) {
            throw "builds.tsv contains an empty or duplicate ISO row: $iso"
        }
        $rowsByIso[$iso] = $row
    }

    $latestRow = $rowsByIso[$isoKeys.Latest]
    $previousRow = $rowsByIso[$isoKeys.Previous]
    if ($null -eq $latestRow) {
        throw "builds.tsv has no row for $($isoKeys.Latest)."
    }
    if ($null -eq $previousRow) {
        throw "builds.tsv has no row for $($isoKeys.Previous)."
    }

    $latestBuildId = ConvertFrom-Na2BuildRecordPath `
        -BuildRecord ([string]$latestRow.build_record) `
        -LogDirectory $LogDirectory
    $previousBuildId = ConvertFrom-Na2BuildRecordPath `
        -BuildRecord ([string]$previousRow.build_record) `
        -LogDirectory $LogDirectory
    if (
        -not [string]::IsNullOrWhiteSpace($latestBuildId) -and
        $latestBuildId -eq $previousBuildId
    ) {
        throw 'Latest and Previous ISOs cannot reference the same build record.'
    }
    $e2eRow = $rowsByIso[$isoKeys.E2eTest]
    $e2eBuildId = ConvertFrom-Na2BuildRecordPath `
        -BuildRecord $(if ($null -ne $e2eRow) { [string]$e2eRow.build_record } else { '' }) `
        -LogDirectory $LogDirectory
    return [pscustomobject]@{
        LatestBuildId = $latestBuildId
        PreviousBuildId = $previousBuildId
        E2eTestBuildId = $e2eBuildId
    }
}

function Set-Na2BuildMap {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$LogDirectory,
        [AllowNull()][string]$LatestBuildId,
        [AllowNull()][string]$PreviousBuildId,
        [AllowNull()][string]$E2eTestBuildId,
        [Parameter(Mandatory = $true)][psobject]$Paths
    )

    if ($LatestBuildId -eq $PreviousBuildId) {
        $PreviousBuildId = $null
    }
    foreach ($buildId in @(
        $LatestBuildId,
        $PreviousBuildId,
        $E2eTestBuildId
    )) {
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

    $recordPath = {
        param([AllowNull()][string]$BuildId)
        if ([string]::IsNullOrWhiteSpace($BuildId)) { return '' }
        return "@logs/na228/builds/$BuildId"
    }
    $isoKeys = Get-Na2ConfiguredIsoMapKeys -Paths $Paths
    $content = @(
        "iso`tbuild_record"
        "$($isoKeys.Latest)`t$(& $recordPath $LatestBuildId)"
        "$($isoKeys.Previous)`t$(& $recordPath $PreviousBuildId)"
        "$($isoKeys.E2eTest)`t$(& $recordPath $E2eTestBuildId)"
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
        [Parameter(Mandatory = $true)][string]$Configuration,
        [Parameter(Mandatory = $true)][psobject]$Paths
    )

    $rotation = if ($Rotated) { 'yes' } else { 'no' }
    $latestPortable = ConvertTo-Na2PortableText -Text $LatestIso -Paths $Paths
    $previousPortable = if ([string]::IsNullOrWhiteSpace($PreviousIso)) {
        ''
    }
    else {
        ConvertTo-Na2PortableText -Text $PreviousIso -Paths $Paths
    }
    $configurationPortable = ConvertTo-Na2PortableText -Text $Configuration -Paths $Paths
    $recordPortable = ConvertTo-Na2PortableText -Text $RecordDirectory -Paths $Paths
    $content = @(
        "timestamp_utc`tresult`trotation`tconfiguration`tlatest_iso`tprevious_iso`tbuild_record"
        (
            (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') + "`t" +
            "$Result`t$rotation`t$configurationPortable`t$latestPortable`t$previousPortable`t$recordPortable"
        )
    ) -join "`n"
    $content += "`n"
    if (Test-Na2WindowsAbsolutePath -Text $content) {
        throw 'Refusing to write build_result.tsv with an absolute path.'
    }
    Set-Na2Utf8FileAtomic -Path (Join-Path $RecordDirectory 'build_result.tsv') -Content $content
}

function Write-Na2E2eBuildResult {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$RecordDirectory,
        [Parameter(Mandatory = $true)][string]$OutputIso,
        [Parameter(Mandatory = $true)][string]$Configuration,
        [Parameter(Mandatory = $true)][psobject]$Paths
    )

    $outputPortable = ConvertTo-Na2PortableText -Text $OutputIso -Paths $Paths
    $configurationPortable = ConvertTo-Na2PortableText -Text $Configuration -Paths $Paths
    $recordPortable = ConvertTo-Na2PortableText -Text $RecordDirectory -Paths $Paths
    $content = @(
        "timestamp_utc`tresult`tconfiguration`toutput_iso`tbuild_record"
        (
            (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') + "`t" +
            "built`t$configurationPortable`t$outputPortable`t$recordPortable"
        )
    ) -join "`n"
    $content += "`n"
    if (Test-Na2WindowsAbsolutePath -Text $content) {
        throw 'Refusing to write E2E build_result.tsv with an absolute path.'
    }
    Set-Na2Utf8FileAtomic -Path (Join-Path $RecordDirectory 'build_result.tsv') -Content $content
}

function Enter-Na2BuildMapLock {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$LogDirectory,
        [ValidateRange(1, 300)][int]$TimeoutSeconds = 120
    )

    [void](New-Item -ItemType Directory -Path $LogDirectory -Force)
    $lockPath = Join-Path $LogDirectory '.builds.lock'
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        try {
            return [IO.File]::Open(
                $lockPath,
                [IO.FileMode]::OpenOrCreate,
                [IO.FileAccess]::ReadWrite,
                [IO.FileShare]::None
            )
        }
        catch [IO.IOException] {
            if ([DateTime]::UtcNow -ge $deadline) {
                throw "Timed out waiting for the NA2 build-map lock: $lockPath"
            }
            Start-Sleep -Milliseconds 100
        }
    } while ($true)
}

function Remove-Na2UnreferencedBuildRecords {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$LogDirectory,
        [AllowNull()][string]$LatestBuildId,
        [AllowNull()][string]$PreviousBuildId,
        [AllowNull()][string]$E2eTestBuildId
    )

    $buildRoot = Join-Path $LogDirectory 'builds'
    if (-not (Test-Path -LiteralPath $buildRoot -PathType Container)) {
        return
    }
    $retained = @(
        $LatestBuildId,
        $PreviousBuildId,
        $E2eTestBuildId
    ) |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Select-Object -Unique
    foreach ($record in Get-ChildItem -LiteralPath $buildRoot -Directory -Force) {
        if ($record.Name -in $retained) {
            continue
        }
        if (Test-Path -LiteralPath (Join-Path $buildRoot ".active-$($record.Name)") -PathType Leaf) {
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
        [Parameter(Mandatory = $true)][string]$Configuration,
        [Parameter(Mandatory = $true)][psobject]$Paths
    )

    $buildRoot = Join-Path $LogDirectory 'builds'
    $recordDirectory = Join-Path $buildRoot $BuildId
    if (-not (Test-Path -LiteralPath $recordDirectory -PathType Container)) {
        throw "Configuration build record does not exist: builds/$BuildId"
    }
    Write-Na2BuildResult `
        -RecordDirectory $recordDirectory `
        -Result $Result `
        -Rotated $Rotated `
        -LatestIso $LatestIso `
        -PreviousIso $PreviousIso `
        -Configuration $Configuration `
        -Paths $Paths
    $lock = Enter-Na2BuildMapLock -LogDirectory $LogDirectory
    try {
        $buildMap = Read-Na2BuildMap `
            -LogDirectory $LogDirectory `
            -Paths $Paths
        $previousExists = -not [string]::IsNullOrWhiteSpace($PreviousIso) -and
            (Test-Path -LiteralPath $PreviousIso -PathType Leaf)
        $effectivePreviousBuildId = if ($Result -eq 'updated' -and $Rotated) {
            $buildMap.LatestBuildId
        }
        elseif ($previousExists) {
            $buildMap.PreviousBuildId
        }
        else {
            $null
        }

        Set-Na2BuildMap `
            -LogDirectory $LogDirectory `
            -LatestBuildId $BuildId `
            -PreviousBuildId $effectivePreviousBuildId `
            -E2eTestBuildId $buildMap.E2eTestBuildId `
            -Paths $Paths
        Remove-Na2UnreferencedBuildRecords `
            -LogDirectory $LogDirectory `
            -LatestBuildId $BuildId `
            -PreviousBuildId $effectivePreviousBuildId `
            -E2eTestBuildId $buildMap.E2eTestBuildId
    }
    finally {
        $lock.Dispose()
    }

    return [pscustomobject]@{
        BuildId = $BuildId
        BuildRecord = "@logs/na228/builds/$BuildId"
    }
}

function Complete-Na2E2eBuildRecord {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$LogDirectory,
        [Parameter(Mandatory = $true)][string]$BuildId,
        [Parameter(Mandatory = $true)][string]$OutputIso,
        [Parameter(Mandatory = $true)][string]$Configuration,
        [Parameter(Mandatory = $true)][psobject]$Paths
    )

    $recordDirectory = Join-Path (Join-Path $LogDirectory 'builds') $BuildId
    if (-not (Test-Path -LiteralPath $recordDirectory -PathType Container)) {
        throw "E2E build record does not exist: builds/$BuildId"
    }
    Write-Na2E2eBuildResult `
        -RecordDirectory $recordDirectory `
        -OutputIso $OutputIso `
        -Configuration $Configuration `
        -Paths $Paths

    $lock = Enter-Na2BuildMapLock -LogDirectory $LogDirectory
    try {
        $buildMap = Read-Na2BuildMap `
            -LogDirectory $LogDirectory `
            -Paths $Paths
        Set-Na2BuildMap `
            -LogDirectory $LogDirectory `
            -LatestBuildId $buildMap.LatestBuildId `
            -PreviousBuildId $buildMap.PreviousBuildId `
            -E2eTestBuildId $BuildId `
            -Paths $Paths
        Remove-Na2UnreferencedBuildRecords `
            -LogDirectory $LogDirectory `
            -LatestBuildId $buildMap.LatestBuildId `
            -PreviousBuildId $buildMap.PreviousBuildId `
            -E2eTestBuildId $BuildId
    }
    finally {
        $lock.Dispose()
    }

    return [pscustomobject]@{
        BuildId = $BuildId
        BuildRecord = "@logs/na228/builds/$BuildId"
    }
}
