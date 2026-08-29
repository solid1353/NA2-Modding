[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
. (Join-Path $repository 'scripts\lib\run_log.ps1')
$testRoot = Join-Path $env:TEMP ('na228-run-log-' + [Guid]::NewGuid().ToString('N'))

function Assert-RunLog {
    param([Parameter(Mandatory)][bool]$Condition, [Parameter(Mandatory)][string]$Message)
    if (-not $Condition) { throw $Message }
}

try {
    $paths = [pscustomobject]@{
        repository = $repository
        logs = Join-Path $testRoot 'logs'
    }
    $context = Start-Na2RunLog -Mode 'configuration-build' -Paths $paths `
        -LogDirectory $paths.logs -MaxRollingSections 2
    Write-Host "repository: $repository"
    Complete-Na2RunLog -Context $context -Outcome succeeded

    $latest = [IO.File]::ReadAllText((Join-Path $paths.logs 'latest.log'))
    $rolling = [IO.File]::ReadAllText((Join-Path $paths.logs 'rolling.log'))
    Assert-RunLog ($latest -match '(?m)^mode: configuration-build$') 'Latest log omitted the mode.'
    Assert-RunLog ($latest -match '(?m)^outcome: succeeded$') 'Latest log omitted the outcome.'
    Assert-RunLog ($latest -match '@repository') 'Latest log did not normalize a configured path.'
    Assert-RunLog (-not (Test-Na2WindowsAbsolutePath -Text $latest)) `
        'Latest log retained an absolute Windows path.'
    Assert-RunLog (
        ([regex]::Matches($rolling, '(?m)^--- NA2 RUN BEGIN ---$')).Count -eq 1
    ) 'Rolling log did not contain exactly one complete section.'

    Write-Host 'NA228 run-log tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
