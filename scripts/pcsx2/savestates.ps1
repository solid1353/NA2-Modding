param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet('move', 'extract')]
    [string]$Command,

    [Parameter(Position = 1, ValueFromRemainingArguments)]
    [string[]]$Arguments,

    [ValidateSet('stable', 'dev')]
    [string]$Target,

    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'

switch ($Command) {
    'move' {
        if ($Arguments.Count -ne 2) {
            throw 'Usage: savestates.ps1 move <game> <subpath> [-Target dev|stable]'
        }

        $parameters = @{
            Game = $Arguments[0]
            SubPath = $Arguments[1]
        }
        if ($PSBoundParameters.ContainsKey('Target')) {
            $parameters.Target = $Target
        }
        if ($WhatIf) {
            $parameters.WhatIf = $true
        }
        & (Join-Path $PSScriptRoot 'move_savestates.ps1') @parameters
    }
    'extract' {
        if ($PSBoundParameters.ContainsKey('Target') -or $WhatIf) {
            throw '-Target and -WhatIf apply only to the move command.'
        }
        & (Join-Path $PSScriptRoot 'extract_savestate_screenshots.ps1') @Arguments
    }
}
