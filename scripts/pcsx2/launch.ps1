[CmdletBinding()]
param(
    [Parameter(Mandatory, ParameterSetName = 'Configured')]
    [ValidateSet('stable', 'dev')]
    [string]$Target,

    [Parameter(Mandatory, ParameterSetName = 'Worker')]
    [string]$WorkerRoot,

    [Parameter(Mandatory)]
    [string]$IsoPath,

    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Arguments,

    [switch]$Wait
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\na2\worker_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

if ($PSCmdlet.ParameterSetName -eq 'Worker') {
    $worker = Get-Na2WorkerContext `
        -WorkerRoot $WorkerRoot `
        -ProjectPaths $projectPaths `
        -RequireRelative
    if ([IO.Path]::IsPathRooted($IsoPath)) {
        throw 'Worker ISO paths must be repository-relative.'
    }
    $resolvedIso = [IO.Path]::GetFullPath(
        (Join-Path $projectPaths.repository $IsoPath)
    )
    $executable = Join-Path $worker.Pcsx2 'pcsx2-qt.exe'
    $workingDirectory = $worker.Pcsx2
    $hidden = $true
}
else {
    $resolvedIso = if ([IO.Path]::IsPathRooted($IsoPath)) {
        [IO.Path]::GetFullPath($IsoPath)
    }
    else {
        [IO.Path]::GetFullPath(
            (Join-Path $projectPaths.repository $IsoPath)
        )
    }
    if ($Target -eq 'stable') {
        $executable = [IO.Path]::GetFullPath(
            $projectPaths.files.pcsx2_user_exe
        )
        $workingDirectory = [IO.Path]::GetFullPath(
            $projectPaths.pcsx2_user
        )
    }
    else {
        $executable = [IO.Path]::GetFullPath(
            $projectPaths.files.pcsx2_dev_exe
        )
        $workingDirectory = [IO.Path]::GetFullPath(
            $projectPaths.pcsx2_dev
        )
    }
    $hidden = $false
}

if (-not (Test-Path -LiteralPath $resolvedIso -PathType Leaf)) {
    throw "ISO does not exist: $resolvedIso"
}
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    if ($PSCmdlet.ParameterSetName -eq 'Worker') {
        throw (
            'The workstream PCSX2 copy does not exist. Copy pcsx2_clean to ' +
            "work/$($worker.WorkerName)/pcsx2 before launching."
        )
    }
    throw "PCSX2 executable does not exist: $executable"
}

$launchArguments = @('-batch', "`"$resolvedIso`"")
if ($Arguments) {
    $launchArguments += @(
        $Arguments | Where-Object { -not [string]::IsNullOrEmpty($_) }
    )
}
$startArguments = @{
    FilePath = $executable
    WorkingDirectory = $workingDirectory
    ArgumentList = $launchArguments
}
if ($hidden) {
    $startArguments.WindowStyle = 'Hidden'
}
if ($Wait) {
    $startArguments.Wait = $true
}
Start-Process @startArguments
