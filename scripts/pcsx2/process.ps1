# User-PCSX2 process helpers used by standard NA2 workflows.
function Get-Na2Pcsx2Process {
    param([Parameter(Mandatory = $true)][string]$Executable)

    $resolvedExecutable = [IO.Path]::GetFullPath($Executable)
    $processName = [IO.Path]::GetFileNameWithoutExtension($resolvedExecutable)
    @(Get-Process -Name $processName -ErrorAction SilentlyContinue | Where-Object {
        try {
            [IO.Path]::Equals(
                [IO.Path]::GetFullPath($_.Path),
                $resolvedExecutable
            )
        }
        catch {
            $false
        }
    })
}

function Stop-Na2Pcsx2 {
    param([Parameter(Mandatory = $true)][string]$Executable)

    $processes = @(Get-Na2Pcsx2Process -Executable $Executable)
    $notStopped = [Collections.Generic.List[int]]::new()
    foreach ($process in $processes) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
    foreach ($process in $processes) {
        try {
            if (-not $process.WaitForExit(5000)) {
                $notStopped.Add($process.Id)
            }
        }
        catch {
            if ($null -ne (
                Get-Process -Id $process.Id -ErrorAction SilentlyContinue
            )) {
                $notStopped.Add($process.Id)
            }
        }
    }
    if ($notStopped.Count -gt 0) {
        throw (
            'PCSX2 did not stop within 5 seconds: PID(s) ' +
            "$($notStopped -join ', ')."
        )
    }
}
