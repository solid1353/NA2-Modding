[CmdletBinding()]
param(
    [AllowEmptyCollection()]
    [string[]]$Arguments = @(),

    [Parameter(Mandatory)]
    [ValidateCount(1, 2)]
    [string[]]$Games,

    [string]$ProjectRoot = (Join-Path $PSScriptRoot '..\..')
)

$ErrorActionPreference = 'Stop'
. (Join-Path $ProjectRoot 'scripts\lib\paths.ps1')
$paths = Get-Na2Paths

if ($Arguments.Count -ne 1) {
    throw 'The Practice launch profile requires a case ID.'
}
$movesetCaseId = [string]$Arguments[0]
if ($movesetCaseId -cnotmatch '^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$') {
    throw 'Launch profile case ID must be a hyphen-separated alphanumeric identifier.'
}

. (Join-Path $PSScriptRoot 'moveset_cases.ps1')
$selected = @(
    Read-PracticeMovesetCases -Path ([string]$paths.files.practice_movesets) |
        Where-Object { [string]::Equals(
            $_.CaseId,
            $movesetCaseId,
            [StringComparison]::OrdinalIgnoreCase
        ) }
)
if ($selected.Count -eq 0) {
    throw "Unknown moveset case ID: $movesetCaseId"
}
Get-PracticeConfiguration -Case $selected[0] -Games $Games -Paths $paths
