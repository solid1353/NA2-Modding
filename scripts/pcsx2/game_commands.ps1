. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')

function Invoke-Na2Pcsx2Game {
    param(
        [Parameter(Mandatory)]
        [ValidateSet('na2s', 'nun3', 'nun5', 'nun6')]
        [string]$Game,

        [Parameter(ValueFromRemainingArguments)]
        [string[]]$Arguments
    )

    $projectPaths = Get-Na2ProjectPaths
    $isoFile = switch ($Game) {
        'na2s' { 'na2_iso' }
        'nun3' { 'nun3_iso' }
        'nun5' { 'nun5_iso' }
        'nun6' { 'nun6_iso' }
    }

    & $projectPaths.files.pcsx2_user_launch_command `
        -batch `
        $projectPaths.files.$isoFile `
        @Arguments
}

function na2s { Invoke-Na2Pcsx2Game -Game na2s -Arguments $args }
function nun3 { Invoke-Na2Pcsx2Game -Game nun3 -Arguments $args }
function nun5 { Invoke-Na2Pcsx2Game -Game nun5 -Arguments $args }
function nun6 { Invoke-Na2Pcsx2Game -Game nun6 -Arguments $args }
