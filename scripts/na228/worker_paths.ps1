Set-StrictMode -Version Latest

function Get-Na2WorkerContext {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$WorkerRoot,
        [Parameter(Mandatory = $true)][psobject]$Paths,
        [switch]$RequireRelative
    )

    if ($RequireRelative -and [IO.Path]::IsPathRooted($WorkerRoot)) {
        throw 'Worker roots must be supplied as repository-relative work/<worker> paths.'
    }

    $resolved = if ([IO.Path]::IsPathRooted($WorkerRoot)) {
        [IO.Path]::GetFullPath($WorkerRoot)
    }
    else {
        [IO.Path]::GetFullPath((Join-Path $Paths.repository $WorkerRoot))
    }
    $workRoot = [IO.Path]::GetFullPath($Paths.work)
    $parent = [IO.Path]::GetDirectoryName($resolved)
    $workerName = [IO.Path]::GetFileName($resolved.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ))

    if (-not [IO.Path]::Equals($parent, $workRoot) -or
        [string]::IsNullOrWhiteSpace($workerName)) {
        throw 'Worker roots must be immediate, named children of work/.'
    }

    [pscustomobject]@{
        WorkerName = $workerName
        Root = $resolved
        Build = Join-Path $resolved 'build'
        Logs = Join-Path $resolved 'logs'
        Inputs = Join-Path $resolved 'inputs'
        Artifacts = Join-Path $resolved 'artifacts'
        Temp = Join-Path $resolved 'temp'
        Pcsx2 = Join-Path $resolved 'pcsx2'
    }
}

function Get-Na2WorkerBuildContext {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$OutputPath,
        [Parameter(Mandatory = $true)][psobject]$Paths,
        [switch]$RequireRelative
    )

    if ($RequireRelative -and [IO.Path]::IsPathRooted($OutputPath)) {
        throw 'Worker ISO outputs must be supplied as repository-relative paths.'
    }

    $resolvedOutput = if ([IO.Path]::IsPathRooted($OutputPath)) {
        [IO.Path]::GetFullPath($OutputPath)
    }
    else {
        [IO.Path]::GetFullPath((Join-Path $Paths.repository $OutputPath))
    }
    if ([IO.Path]::GetExtension($resolvedOutput) -ine '.iso') {
        throw 'Worker ISO output filenames must end in .iso.'
    }

    $buildDirectory = [IO.Path]::GetDirectoryName($resolvedOutput)
    if ([IO.Path]::GetFileName($buildDirectory) -ine 'build') {
        throw 'Worker ISO outputs must be direct children of work/<worker>/build/.'
    }
    $workerRoot = [IO.Path]::GetDirectoryName($buildDirectory)
    $worker = Get-Na2WorkerContext `
        -WorkerRoot $workerRoot `
        -Paths $Paths

    $sharedOutputs = @(
        foreach ($property in @(
            'latest_iso',
            'previous_iso',
            'manual_iso',
            'e2e_test_iso',
            'e2e_test_shifted_iso'
        )) {
            $configured = $Paths.files.PSObject.Properties[$property]
            if ($null -ne $configured) { $configured.Value }
        }
    ) | ForEach-Object { [IO.Path]::GetFullPath([string]$_) }
    if ($sharedOutputs | Where-Object { [IO.Path]::Equals($_, $resolvedOutput) }) {
        throw 'Worker ISO output must not target Latest, Previous, Manual, or E2E Test outputs.'
    }

    $worker | Add-Member -NotePropertyName OutputIso -NotePropertyValue $resolvedOutput
    $worker | Add-Member -NotePropertyName BuildingIso -NotePropertyValue "$resolvedOutput.building"
    return $worker
}

function Remove-Na2EmptyWorkerAncestors {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$WorkRoot
    )

    $stop = [IO.Path]::GetFullPath($WorkRoot)
    $current = [IO.Path]::GetFullPath($Path)
    while (-not [IO.Path]::Equals($current, $stop)) {
        $parent = [IO.Path]::GetDirectoryName($current)
        if ([string]::IsNullOrWhiteSpace($parent)) { break }
        $stopPrefix = $stop.TrimEnd(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        ) + [IO.Path]::DirectorySeparatorChar
        if (-not $current.StartsWith($stopPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            break
        }
        if (Test-Path -LiteralPath $current -PathType Container) {
            $children = @(Get-ChildItem -Force -LiteralPath $current)
            if ($children.Count -gt 0) { break }
            Remove-Item -LiteralPath $current -Force
        }
        $current = $parent
    }
}
