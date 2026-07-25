Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot 'ini.ps1')

function Get-Na2AvailablePinePort {
    [CmdletBinding()]
    param([ValidateRange(1024, 65000)][int]$StartPort = 28011)

    foreach ($port in $StartPort..([math]::Min(65535, $StartPort + 255))) {
        $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $port)
        try {
            $listener.Server.ExclusiveAddressUse = $true
            $listener.Start()
            return $port
        }
        catch {
        }
        finally {
            try { $listener.Stop() } catch { }
        }
    }
    throw "No free PINE port was found from $StartPort through $([math]::Min(65535, $StartPort + 255))."
}

function New-Na2TestRuntimeLayout {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][psobject]$Worker)

    $runId = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + "_pid${PID}_" + [guid]::NewGuid().ToString('N').Substring(0, 8)
    $layout = [pscustomobject]@{
        RunId = $runId
        LogDirectory = Join-Path $Worker.Logs $runId
        Videos = Join-Path (Join-Path $Worker.Artifacts 'recordings') $runId
        Cache = Join-Path (Join-Path $Worker.Temp 'pcsx2') "$runId\cache"
        BlockDumps = Join-Path (Join-Path $Worker.Temp 'pcsx2') "$runId\block-dumps"
        GsDumps = Join-Path (Join-Path $Worker.Temp 'pcsx2') "$runId\gs-dumps"
        TempRoot = Join-Path (Join-Path $Worker.Temp 'pcsx2') $runId
    }
    New-Item -ItemType Directory -Force -Path @(
        $layout.LogDirectory
        $layout.Videos
        $layout.Cache
        $layout.BlockDumps
        $layout.GsDumps
    ) | Out-Null
    return $layout
}

function Set-Na2TestRuntimeConfiguration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][psobject]$Pcsx2,
        [Parameter(Mandatory = $true)][psobject]$Layout,
        [Parameter(Mandatory = $true)][psobject]$IsoIdentity,
        [bool]$StartPaused = $false
    )

    $iniPath = $Pcsx2.Ini
    $iniText = [IO.File]::ReadAllText($iniPath)
    $iniText = Remove-Na2IniValue `
        -Text $iniText `
        -Section 'Folders' `
        -Key 'SaveStates'
    $configuredPort = Get-Na2IniValue `
        -Text $iniText `
        -Section 'EmuCore' `
        -Key 'PINESlot'
    $portStart = 28011
    if (-not [string]::IsNullOrWhiteSpace($configuredPort)) {
        $parsedPort = 0
        if ([int]::TryParse($configuredPort, [ref]$parsedPort) -and
            $parsedPort -ge 1024 -and $parsedPort -le 65000) {
            $portStart = $parsedPort
        }
    }
    $pinePort = Get-Na2AvailablePinePort -StartPort $portStart

    $gameSettingsPath = Join-Path (
        $Pcsx2.GameSettings
    ) "$($IsoIdentity.Serial)_$($IsoIdentity.CRC).ini"
    $gameSettingsText = if (
        Test-Path -LiteralPath $gameSettingsPath -PathType Leaf
    ) {
        [IO.File]::ReadAllText($gameSettingsPath)
    }
    else {
        ''
    }
    $memoryCardName = Get-Na2IniValue `
        -Text $gameSettingsText `
        -Section 'MemoryCards' `
        -Key 'Slot1_Filename'
    if ([string]::IsNullOrWhiteSpace($memoryCardName)) {
        $memoryCardName = Get-Na2IniValue `
            -Text $iniText `
            -Section 'MemoryCards' `
            -Key 'Slot1_Filename'
    }
    if ([string]::IsNullOrWhiteSpace($memoryCardName) -or
        [IO.Path]::GetFileName($memoryCardName) -cne $memoryCardName) {
        throw 'The cloned PCSX2 does not select a valid Slot 1 memory card.'
    }
    $memoryCardPath = Join-Path $Pcsx2.MemoryCards $memoryCardName
    if (-not (Test-Path -LiteralPath $memoryCardPath -PathType Leaf)) {
        throw "The cloned PCSX2 Slot 1 memory card is missing: $memoryCardPath"
    }
    New-Item -ItemType Directory -Force -Path @(
        $Pcsx2.SaveStates
        $Pcsx2.Snapshots
    ) | Out-Null

    $settings = @(
        [pscustomobject]@{ Section = 'Folders'; Key = 'Snapshots'; Value = 'snaps' }
        [pscustomobject]@{ Section = 'Folders'; Key = 'Savestates'; Value = 'sstates' }
        [pscustomobject]@{ Section = 'Folders'; Key = 'Logs'; Value = $Layout.LogDirectory }
        [pscustomobject]@{ Section = 'Folders'; Key = 'Cache'; Value = $Layout.Cache }
        [pscustomobject]@{ Section = 'Folders'; Key = 'Videos'; Value = $Layout.Videos }
        [pscustomobject]@{ Section = 'EmuCore'; Key = 'EnablePINE'; Value = 'true' }
        [pscustomobject]@{ Section = 'EmuCore'; Key = 'PINESlot'; Value = [string]$pinePort }
        [pscustomobject]@{ Section = 'EmuCore'; Key = 'BlockDumpSaveDirectory'; Value = $Layout.BlockDumps }
        [pscustomobject]@{ Section = 'EmuCore/GS'; Key = 'ScreenshotFormat'; Value = '0' }
        [pscustomobject]@{ Section = 'EmuCore/GS'; Key = 'OrganizeScreenshotsByGame'; Value = 'false' }
        [pscustomobject]@{ Section = 'EmuCore/GS'; Key = 'HWDumpDirectory'; Value = $Layout.GsDumps }
        [pscustomobject]@{ Section = 'EmuCore/GS'; Key = 'SWDumpDirectory'; Value = $Layout.GsDumps }
        [pscustomobject]@{ Section = 'SPU2/Output'; Key = 'OutputMuted'; Value = 'true' }
        [pscustomobject]@{ Section = 'UI'; Key = 'StartPaused'; Value = $StartPaused.ToString().ToLowerInvariant() }
        [pscustomobject]@{ Section = 'Hotkeys'; Key = 'Screenshot'; Value = 'Keyboard/F8' }
    )
    $configured = Set-Na2IniSettings -Text $iniText -Settings $settings
    [IO.File]::WriteAllText(
        $iniPath,
        $configured,
        [Text.UTF8Encoding]::new($false)
    )

    return [pscustomobject]@{
        IniPath = $iniPath
        MemoryCardName = $memoryCardName
        MemoryCardPath = $memoryCardPath
        SaveStates = $Pcsx2.SaveStates
        Snapshots = $Pcsx2.Snapshots
        PinePort = $pinePort
        Layout = $Layout
    }
}

function Remove-Na2TestRuntimeLayout {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][psobject]$Layout,
        [Parameter(Mandatory = $true)][psobject]$Worker,
        [Parameter(Mandatory = $true)][string]$WorkRoot
    )

    if (Test-Path -LiteralPath $Layout.TempRoot -PathType Container) {
        Remove-Item -LiteralPath $Layout.TempRoot -Recurse -Force
    }
    foreach ($path in @(
        $Layout.LogDirectory
        $Layout.Videos
        ([IO.Path]::GetDirectoryName($Layout.TempRoot))
    )) {
        Remove-Na2EmptyWorkerAncestors -Path $path -WorkRoot $WorkRoot
    }
}
