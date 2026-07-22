Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot 'ini.ps1')
. (Join-Path $PSScriptRoot 'test_memory_card.ps1')

function Enter-Na2Pcsx2ConfigurationLock {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$IniPath,
        [ValidateRange(1, 300)][int]$TimeoutSeconds = 60
    )

    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $hash = [Convert]::ToHexString(
            $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes([IO.Path]::GetFullPath($IniPath).ToUpperInvariant()))
        ).Substring(0, 24)
    }
    finally {
        $sha.Dispose()
    }
    $mutex = [Threading.Mutex]::new($false, "Local\NA2Modding.PCSX2Config.$hash")
    try {
        try {
            $acquired = $mutex.WaitOne([TimeSpan]::FromSeconds($TimeoutSeconds))
        }
        catch [Threading.AbandonedMutexException] {
            $acquired = $true
        }
        if (-not $acquired) { throw 'Timed out waiting for the shared PCSX2 configuration lock.' }
        return $mutex
    }
    catch {
        $mutex.Dispose()
        throw
    }
}

function Exit-Na2Pcsx2ConfigurationLock {
    param([Parameter(Mandatory = $true)][Threading.Mutex]$Mutex)

    try { $Mutex.ReleaseMutex() } finally { $Mutex.Dispose() }
}

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
        SaveStates = Join-Path (Join-Path $Worker.Artifacts 'sstates') $runId
        Snapshots = Join-Path (Join-Path $Worker.Artifacts 'screenshots') $runId
        Videos = Join-Path (Join-Path $Worker.Artifacts 'recordings') $runId
        MemoryCards = Join-Path $Worker.Artifacts 'memcards'
        Cache = Join-Path (Join-Path $Worker.Temp 'pcsx2') "$runId\cache"
        BlockDumps = Join-Path (Join-Path $Worker.Temp 'pcsx2') "$runId\block-dumps"
        GsDumps = Join-Path (Join-Path $Worker.Temp 'pcsx2') "$runId\gs-dumps"
        TempRoot = Join-Path (Join-Path $Worker.Temp 'pcsx2') $runId
    }
    New-Item -ItemType Directory -Force -Path @(
        $layout.LogDirectory
        $layout.SaveStates
        $layout.Snapshots
        $layout.Videos
        $layout.MemoryCards
        $layout.Cache
        $layout.BlockDumps
        $layout.GsDumps
    ) | Out-Null
    return $layout
}

function Enter-Na2TestRuntimeConfiguration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][psobject]$ProjectPaths,
        [Parameter(Mandatory = $true)][psobject]$Layout,
        [Parameter(Mandatory = $true)][psobject]$IsoIdentity,
        [Parameter(Mandatory = $true)][string]$AgentName,
        [Parameter(Mandatory = $true)][string]$TaskIdentity
    )

    $iniPath = $ProjectPaths.files.pcsx2_ini
    $memory = $null
    $snapshot = $null
    try {
        $memory = Enter-Na2TestMemoryCard `
            -GlobalIniPath $iniPath `
            -GameSettingsDirectory $ProjectPaths.pcsx2_gamesettings `
            -SourceMemoryCardsDirectory $ProjectPaths.pcsx2_memcards `
            -TaskMemoryCardsDirectory $Layout.MemoryCards `
            -Serial $IsoIdentity.Serial `
            -CRC $IsoIdentity.CRC `
            -AgentName $AgentName `
            -TaskIdentity $TaskIdentity

        $iniText = [IO.File]::ReadAllText($iniPath)
        $configuredPort = Get-Na2IniValue -Text $iniText -Section 'EmuCore' -Key 'PINESlot'
        $portStart = 28011
        if (-not [string]::IsNullOrWhiteSpace($configuredPort)) {
            $parsedPort = 0
            if ([int]::TryParse($configuredPort, [ref]$parsedPort) -and
                $parsedPort -ge 1024 -and $parsedPort -le 65000) {
                $portStart = $parsedPort
            }
        }
        $pinePort = Get-Na2AvailablePinePort -StartPort $portStart
        $settings = @(
            [pscustomobject]@{ Section = 'Folders'; Key = 'Snapshots'; Value = $Layout.Snapshots }
            [pscustomobject]@{ Section = 'Folders'; Key = 'SaveStates'; Value = $Layout.SaveStates }
            [pscustomobject]@{ Section = 'Folders'; Key = 'MemoryCards'; Value = $Layout.MemoryCards }
            [pscustomobject]@{ Section = 'Folders'; Key = 'Logs'; Value = $Layout.LogDirectory }
            [pscustomobject]@{ Section = 'Folders'; Key = 'Cache'; Value = $Layout.Cache }
            [pscustomobject]@{ Section = 'Folders'; Key = 'Videos'; Value = $Layout.Videos }
            [pscustomobject]@{ Section = 'EmuCore'; Key = 'EnablePINE'; Value = 'true' }
            [pscustomobject]@{ Section = 'EmuCore'; Key = 'PINESlot'; Value = [string]$pinePort }
            [pscustomobject]@{ Section = 'EmuCore'; Key = 'BlockDumpSaveDirectory'; Value = $Layout.BlockDumps }
            [pscustomobject]@{ Section = 'EmuCore/GS'; Key = 'HWDumpDirectory'; Value = $Layout.GsDumps }
            [pscustomobject]@{ Section = 'EmuCore/GS'; Key = 'SWDumpDirectory'; Value = $Layout.GsDumps }
            [pscustomobject]@{ Section = 'SPU2/Output'; Key = 'OutputMuted'; Value = 'true' }
        )
        $snapshot = Get-Na2IniSettingSnapshot -Text $iniText -Settings $settings
        $injected = Set-Na2IniSettings -Text $iniText -Settings $settings
        [IO.File]::WriteAllText($iniPath, $injected, [Text.UTF8Encoding]::new($false))

        return [pscustomobject]@{
            IniPath = $iniPath
            IniSnapshot = $snapshot
            MemoryCard = $memory
            PinePort = $pinePort
            Layout = $Layout
        }
    }
    catch {
        if ($null -ne $snapshot -and (Test-Path -LiteralPath $iniPath -PathType Leaf)) {
            $current = [IO.File]::ReadAllText($iniPath)
            $restored = Restore-Na2IniSettings -Text $current -Snapshot $snapshot -OnlyIfInjected
            [IO.File]::WriteAllText($iniPath, $restored, [Text.UTF8Encoding]::new($false))
        }
        if ($null -ne $memory) {
            Exit-Na2TestMemoryCard -Context $memory -OnlyIfInjected | Out-Null
        }
        throw
    }
}

function Restore-Na2TestRuntimeConfiguration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][psobject]$Context,
        [switch]$OnlyIfInjected
    )

    if (Test-Path -LiteralPath $Context.IniPath -PathType Leaf) {
        $current = [IO.File]::ReadAllText($Context.IniPath)
        $restored = Restore-Na2IniSettings `
            -Text $current `
            -Snapshot $Context.IniSnapshot `
            -OnlyIfInjected:$OnlyIfInjected
        if ($restored -cne $current) {
            [IO.File]::WriteAllText($Context.IniPath, $restored, [Text.UTF8Encoding]::new($false))
        }
    }
    Exit-Na2TestMemoryCard `
        -Context $Context.MemoryCard `
        -OnlyIfInjected:$OnlyIfInjected | Out-Null
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
        $Layout.SaveStates
        $Layout.Snapshots
        $Layout.Videos
        $Layout.MemoryCards
        ([IO.Path]::GetDirectoryName($Layout.TempRoot))
    )) {
        Remove-Na2EmptyWorkerAncestors -Path $path -WorkRoot $WorkRoot
    }
}
