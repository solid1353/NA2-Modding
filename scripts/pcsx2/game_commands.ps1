. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')

function Invoke-Na2Pcsx2Game {
    param(
        [Parameter(Mandatory)]
        [ValidateSet('na2', 'nun3', 'nun5', 'nun6')]
        [string]$Game,

        [Parameter(ValueFromRemainingArguments)]
        [string[]]$Arguments
    )

    $projectPaths = Get-Na2ProjectPaths
    $isoFile = switch ($Game) {
        'na2' { 'na2_iso' }
        'nun3' { 'nun3_iso' }
        'nun5' { 'nun5_iso' }
        'nun6' { 'nun6_iso' }
    }

    & $projectPaths.files.pcsx2_launch_command `
        -IsoPath $projectPaths.files.$isoFile `
        -Arguments $Arguments `
        -Wait
}

function na2 { Invoke-Na2Pcsx2Game -Game na2 -Arguments $args }
function nun3 { Invoke-Na2Pcsx2Game -Game nun3 -Arguments $args }
function nun5 { Invoke-Na2Pcsx2Game -Game nun5 -Arguments $args }
function nun6 { Invoke-Na2Pcsx2Game -Game nun6 -Arguments $args }
