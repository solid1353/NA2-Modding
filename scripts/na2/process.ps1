function Get-Na2Pcsx2Process {
    param([Parameter(Mandatory = $true)][string]$Executable)

    $resolvedExecutable = [IO.Path]::GetFullPath($Executable)
    $processName = [IO.Path]::GetFileNameWithoutExtension($resolvedExecutable)
    @(Get-Process -Name $processName -ErrorAction SilentlyContinue | Where-Object {
        try {
            [IO.Path]::Equals([IO.Path]::GetFullPath($_.Path), $resolvedExecutable)
        }
        catch {
            $false
        }
    })
}

function Stop-Na2Pcsx2 {
    param([Parameter(Mandatory = $true)][string]$Executable)

    $processes = @(Get-Na2Pcsx2Process -Executable $Executable)
    foreach ($process in $processes) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
    foreach ($process in $processes) {
        try {
            $process.WaitForExit(5000) | Out-Null
        }
        catch {
            # A process that already exited needs no further cleanup.
        }
    }
}
