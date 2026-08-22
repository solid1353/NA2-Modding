Set-StrictMode -Version Latest

function Get-Na2StartupFastForwardFrames {
    [CmdletBinding()]
    param(
        [string]$Configuration,
        [Parameter(Mandatory)][psobject]$Paths,
        [string]$LaunchProfile
    )

    $launchSettings = $Paths.settings.launch_settings
    $startupFrames = $launchSettings.startup_fast_forward_frames
    if (-not [string]::IsNullOrWhiteSpace($LaunchProfile)) {
        $profile = $launchSettings.PSObject.Properties[$LaunchProfile]
        if ($null -eq $profile -or $profile.Value -isnot [pscustomobject]) {
            throw "Unknown launch profile: $LaunchProfile"
        }
        $profileFrames = $profile.Value.PSObject.Properties[
            'startup_fast_forward_frames'
        ]
        if ($null -ne $profileFrames) {
            $startupFrames = $profileFrames.Value
        }
    }
    if ([string]::IsNullOrWhiteSpace($Configuration)) {
        return [UInt64]$startupFrames
    }
    if ($Configuration -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]*$') {
        throw "Invalid launch configuration ID: $Configuration"
    }
    $configurationPath = Join-Path $Paths.builder (
        "configurations\$Configuration.json"
    )
    if (-not (Test-Path -LiteralPath $configurationPath -PathType Leaf)) {
        throw "Launch configuration does not exist: $Configuration"
    }
    $pythonRunner = Join-Path ([string]$Paths.scripts) 'lib\run_python.ps1'
    $arguments = @(
        '--catalog', (Join-Path $Paths.builder 'catalog'),
        '--configuration', $configurationPath,
        '--baseline-frames', [string]$startupFrames
    )
    Push-Location -LiteralPath $Paths.repository
    try {
        $output = @(
            & $pythonRunner -PackageSet builder `
                -Module 'na228_builder.scripts.launch_settings' `
                -ArgumentList $arguments -NoBytecode 2>&1
        )
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    $lines = [string[]]@($output | ForEach-Object { [string]$_ })
    if ($exitCode -ne 0) {
        $configurationFailure = @(
            $lines | Where-Object { $_ -match '^ConfigurationError: (.+)$' }
        ) | Select-Object -Last 1
        if ($configurationFailure -match '^ConfigurationError: (.+)$') {
            $exception = [InvalidOperationException]::new($Matches[1])
            $exception.Data['Na2ConfigurationError'] = $true
            $exception.Data['Na2TechnicalDetails'] = $lines -join "`n"
            throw $exception
        }
        $lines | ForEach-Object { Write-Host $_ }
        throw "Could not resolve startup fast-forward frames for $Configuration."
    }
    $text = ($lines -join '').Trim()
    [UInt64]$frames = 0
    if (-not [UInt64]::TryParse($text, [ref]$frames)) {
        throw "Invalid startup fast-forward frame result for $Configuration`: $text"
    }
    return $frames
}
