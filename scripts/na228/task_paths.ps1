Set-StrictMode -Version Latest

function Get-Na2TaskContext {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$TaskRoot,
        [Parameter(Mandatory = $true)][psobject]$Paths
    )

    $resolved = if ([IO.Path]::IsPathRooted($TaskRoot)) {
        [IO.Path]::GetFullPath($TaskRoot)
    }
    else {
        [IO.Path]::GetFullPath((Join-Path $Paths.repository $TaskRoot))
    }
    $workRoot = [IO.Path]::GetFullPath($Paths.work)
    $parent = [IO.Path]::GetDirectoryName($resolved)
    $taskName = [IO.Path]::GetFileName($resolved.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ))

    if (-not [IO.Path]::Equals($parent, $workRoot) -or
        [string]::IsNullOrWhiteSpace($taskName)) {
        throw 'NA228_TASK_WORK_ROOT must name an immediate child of work/.'
    }

    [pscustomobject]@{
        TaskName = $taskName
        Root = $resolved
        Logs = Join-Path $resolved 'logs'
    }
}
