[CmdletBinding(DefaultParameterSetName = 'Configured')]
param(
    [Parameter(ParameterSetName = 'Configured')]
    [ValidateSet('stable', 'dev')]
    [string]$Target = 'dev',

    [Parameter(Mandatory, ParameterSetName = 'Worker')]
    [string]$WorkerRoot,

    [Parameter(ParameterSetName = 'Configured')]
    [Parameter(Mandatory, ParameterSetName = 'Worker')]
    [string]$IsoPath,

    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Arguments,

    [switch]$Wait,

    [switch]$PassThru
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
. (Join-Path $PSScriptRoot '..\na228\worker_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

function Initialize-WorkerWindowApi {
    if ('Na228WorkerWindowApi' -as [type]) {
        return
    }

    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class Na228WorkerWindowApi
{
    public delegate bool EnumWindowsCallback(IntPtr window, IntPtr parameter);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(
        EnumWindowsCallback callback,
        IntPtr parameter
    );

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(
        IntPtr window,
        out uint processId
    );

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr window);

    [DllImport("user32.dll")]
    public static extern bool ShowWindowAsync(IntPtr window, int command);
}
'@
}

function Get-VisibleProcessWindows {
    param(
        [Parameter(Mandatory)]
        [int]$OwnerProcessId
    )

    $windows = [Collections.Generic.List[IntPtr]]::new()
    $callback = [Na228WorkerWindowApi+EnumWindowsCallback]{
        param([IntPtr]$window, [IntPtr]$parameter)

        [uint32]$windowProcessId = 0
        [void][Na228WorkerWindowApi]::GetWindowThreadProcessId(
            $window,
            [ref]$windowProcessId
        )
        if (
            $windowProcessId -eq [uint32]$OwnerProcessId -and
            [Na228WorkerWindowApi]::IsWindowVisible($window)
        ) {
            $windows.Add($window)
        }
        return $true
    }
    [void][Na228WorkerWindowApi]::EnumWindows($callback, [IntPtr]::Zero)
    return @($windows)
}

function Hide-WorkerProcessWindows {
    param(
        [Parameter(Mandatory)]
        [Diagnostics.Process]$Process
    )

    Initialize-WorkerWindowApi
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    do {
        $Process.Refresh()
        if ($Process.HasExited) {
            throw "Worker PCSX2 exited during launch (exit $($Process.ExitCode))."
        }

        foreach ($window in @(Get-VisibleProcessWindows -OwnerProcessId $Process.Id)) {
            [void][Na228WorkerWindowApi]::ShowWindowAsync($window, 0)
        }
        Start-Sleep -Milliseconds 50
    } while ([DateTime]::UtcNow -lt $deadline)

    $visibleWindows = @(
        Get-VisibleProcessWindows -OwnerProcessId $Process.Id
    )
    if ($visibleWindows.Count -gt 0) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        throw (
            'Worker PCSX2 did not remain hidden; terminated process ' +
            "$($Process.Id)."
        )
    }
}

if ($PSCmdlet.ParameterSetName -eq 'Worker') {
    $worker = Get-Na2WorkerContext `
        -WorkerRoot $WorkerRoot `
        -ProjectPaths $projectPaths `
        -RequireRelative
    if ($IsoPath) {
        if ([IO.Path]::IsPathRooted($IsoPath)) {
            throw 'Worker ISO paths must be repository-relative.'
        }
        $resolvedIso = [IO.Path]::GetFullPath(
            (Join-Path $projectPaths.repository $IsoPath)
        )
        $allowedIsoRoot = [IO.Path]::GetFullPath(
            (Join-Path $worker.Inputs 'isos')
        )
        $prefix = $allowedIsoRoot.TrimEnd(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        ) + [IO.Path]::DirectorySeparatorChar
        if (-not $resolvedIso.StartsWith(
            $prefix,
            [StringComparison]::OrdinalIgnoreCase
        )) {
            throw (
                'Worker ISO must be an independent copy under ' +
                "work/$($worker.WorkerName)/inputs/isos/."
            )
        }
    }
    $workerExecutables = @(
        Get-ChildItem -LiteralPath $worker.Pcsx2 -File -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -ceq 'pcsx2-qt.exe' -or
                $_.Name -like 'pcsx2-qtx64-*.exe'
            } |
            Sort-Object @{
                Expression = { if ($_.Name -ceq 'pcsx2-qt.exe') { 0 } else { 1 } }
            }, Name
    )
    if ($workerExecutables.Count -eq 0) {
        throw (
            'The workstream PCSX2 copy contains no supported executable: ' +
            $worker.Pcsx2
        )
    }
    $executable = $workerExecutables[0].FullName
    $workingDirectory = $worker.Pcsx2
    $hidden = $true
}
else {
    if ($IsoPath) {
        $resolvedIso = if ([IO.Path]::IsPathRooted($IsoPath)) {
            [IO.Path]::GetFullPath($IsoPath)
        }
        else {
            [IO.Path]::GetFullPath(
                (Join-Path $projectPaths.repository $IsoPath)
            )
        }
    }
    if ($Target -eq 'stable') {
        $executable = [IO.Path]::GetFullPath(
            $projectPaths.files.pcsx2_stable_exe
        )
        $workingDirectory = [IO.Path]::GetFullPath(
            $projectPaths.pcsx2_stable
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

if ($IsoPath -and -not (
    Test-Path -LiteralPath $resolvedIso -PathType Leaf
)) {
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

$launchArguments = @()
if ($hidden) {
    $launchArguments += '-nogui'
}
if (
    $PSCmdlet.ParameterSetName -eq 'Configured' -and
    $Target -eq 'dev'
) {
    $launchArguments += '-unlimited'
}
if ($IsoPath) {
    $launchArguments += @('-batch', "`"$resolvedIso`"")
}
if ($Arguments) {
    $launchArguments += @(
        $Arguments | Where-Object { -not [string]::IsNullOrEmpty($_) }
    )
}
$startArguments = @{
    FilePath = $executable
    WorkingDirectory = $workingDirectory
}
if ($launchArguments.Count -gt 0) {
    $startArguments.ArgumentList = $launchArguments
}
if ($hidden) {
    $startArguments.WindowStyle = 'Hidden'
    $startArguments.PassThru = $true
    $process = Start-Process @startArguments
    try {
        Hide-WorkerProcessWindows -Process $process
    }
    catch {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
        throw
    }
    if ($Wait) {
        $process.WaitForExit()
    }
    if ($PassThru) {
        $process
    }
    return
}
if ($Wait) {
    $startArguments.Wait = $true
}
if ($PassThru) {
    $startArguments.PassThru = $true
}
Start-Process @startArguments
