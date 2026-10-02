Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot '..\lib\builder_module.ps1')

function Get-Na2LaunchSettings {
    [CmdletBinding()]
    param(
        [string]$Configuration,
        [Parameter(Mandatory)][psobject]$Paths,
        [string]$LaunchProfile
    )

    $launchSettings = $Paths.settings.launch_settings
    $startupFrames = $launchSettings.default.startup_fast_forward_frames
    $speedAfterStartup = [string]$launchSettings.default.speed_after_startup
    if (-not [string]::IsNullOrWhiteSpace($LaunchProfile)) {
        $profileSettings = $launchSettings.PSObject.Properties[$LaunchProfile].Value
        $profileFrames = $profileSettings.PSObject.Properties['startup_fast_forward_frames']
        if ($null -ne $profileFrames) {
            $startupFrames = $profileFrames.Value
        }
        $profileSpeed = $profileSettings.PSObject.Properties['speed_after_startup']
        if ($null -ne $profileSpeed) {
            $speedAfterStartup = [string]$profileSpeed.Value
        }
    }
    if (-not [string]::IsNullOrWhiteSpace($Configuration)) {
        $execution = Invoke-Na2BuilderModule -Repository $Paths.repository `
            -Module launch_settings -ArgumentList @(
                '--catalog', (Join-Path $Paths.builder 'catalog.modcat'),
                '--configuration', (Join-Path $Paths.builder (
                    "configurations\$Configuration.jsonc"
                )),
                '--baseline-frames', [string]$startupFrames
            )
        Assert-Na2BuilderModuleSucceeded -Execution $execution `
            -FailureMessage "Could not resolve startup fast-forward frames for $Configuration."
        $text = ($execution.Output -join '').Trim()
        [UInt64]$resolvedFrames = 0
        if (-not [UInt64]::TryParse($text, [ref]$resolvedFrames)) {
            throw "Invalid startup fast-forward frame result for $Configuration`: $text"
        }
        $startupFrames = $resolvedFrames
    }
    [pscustomobject]@{
        StartupFastForwardFrames = [UInt64]$startupFrames
        SpeedAfterStartup = $speedAfterStartup
    }
}
