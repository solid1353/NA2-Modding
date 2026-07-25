[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'process.ps1')

function Assert-Na2OwnershipTest {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

function Test-Na2TestProcessRunning {
    param([Parameter(Mandatory = $true)][int]$Id)

    return $null -ne (Get-Process -Id $Id -ErrorAction SilentlyContinue)
}

$testRoot = Join-Path ([IO.Path]::GetTempPath()) (
    "na2-pcsx2-ownership-tests-$PID-$([guid]::NewGuid().ToString('N'))"
)
$child = $null
try {
    New-Item -ItemType Directory -Force -Path $testRoot | Out-Null
    $executable = [IO.Path]::GetFullPath((Get-Process -Id $PID).Path)
    $executableIdentity = '@test/pwsh.exe'
    $child = Start-Process `
        -FilePath $executable `
        -ArgumentList @(
            '-NoProfile',
            '-NonInteractive',
            '-Command',
            'Start-Sleep -Seconds 60'
        ) `
        -PassThru
    $child.Refresh()
    $descriptorPath = Join-Path $testRoot 'pcsx2-instance.json'
    $capability = New-Na2Pcsx2OwnershipCapability
    $descriptor = [ordered]@{
        schema_version = 2
        state = 'ready'
        worker = 'Scripting'
        iso = '@test/test.iso'
        serial = 'TEST-00000'
        crc = '12345678'
        executable = $executableIdentity
        process_id = $child.Id
        process_start_utc = $child.StartTime.ToUniversalTime().ToString('o')
        window_handle = '0x1'
        pine_port = 28011
        memory_card = '@test/Mcd001.ps2'
        log_directory = '@test/logs'
    }

    Write-Na2Pcsx2OwnershipDescriptor `
        -Path $descriptorPath `
        -Descriptor $descriptor `
        -OwnershipCapability $capability
    $valid = Get-Na2Pcsx2OwnershipState `
        -DescriptorPath $descriptorPath `
        -OwnershipCapability $capability
    Assert-Na2OwnershipTest `
        -Condition $valid.Valid `
        -Message 'A freshly written descriptor did not validate.'

    $held = Get-Na2Pcsx2OwnershipState `
        -DescriptorPath $descriptorPath `
        -OwnershipCapability $capability `
        -KeepDescriptorOpen
    $deleteBlocked = $false
    try {
        Remove-Item -LiteralPath $descriptorPath -Force
    }
    catch {
        $deleteBlocked = $true
    }
    finally {
        $held.DescriptorHandle.Dispose()
    }
    Assert-Na2OwnershipTest `
        -Condition ($held.Valid -and $deleteBlocked -and (Test-Path -LiteralPath $descriptorPath)) `
        -Message 'A held ownership descriptor could be removed during an authorized operation.'

    Remove-Item -LiteralPath $descriptorPath -Force
    $missing = Stop-Na2Pcsx2Process `
        -DescriptorPath $descriptorPath `
        -OwnershipCapability $capability `
        -Executable $executable `
        -ExecutableIdentity $executableIdentity
    Assert-Na2OwnershipTest `
        -Condition ($missing.Status -ceq 'LostOwnership') `
        -Message 'A missing descriptor did not fail closed.'
    Assert-Na2OwnershipTest `
        -Condition (Test-Na2TestProcessRunning -Id $child.Id) `
        -Message 'Missing-descriptor cleanup terminated the test process.'

    Write-Na2Pcsx2OwnershipDescriptor `
        -Path $descriptorPath `
        -Descriptor $descriptor `
        -OwnershipCapability $capability
    $wrongCapability = New-Na2Pcsx2OwnershipCapability
    $mismatched = Stop-Na2Pcsx2Process `
        -DescriptorPath $descriptorPath `
        -OwnershipCapability $wrongCapability `
        -Executable $executable `
        -ExecutableIdentity $executableIdentity
    Assert-Na2OwnershipTest `
        -Condition ($mismatched.Status -ceq 'LostOwnership') `
        -Message 'A mismatched capability did not fail closed.'
    Assert-Na2OwnershipTest `
        -Condition (Test-Na2TestProcessRunning -Id $child.Id) `
        -Message 'Mismatched-capability cleanup terminated the test process.'

    [IO.File]::AppendAllText($descriptorPath, ' ')
    $tampered = Stop-Na2Pcsx2Process `
        -DescriptorPath $descriptorPath `
        -OwnershipCapability $capability `
        -Executable $executable `
        -ExecutableIdentity $executableIdentity
    Assert-Na2OwnershipTest `
        -Condition ($tampered.Status -ceq 'LostOwnership') `
        -Message 'A changed descriptor did not fail closed.'
    Assert-Na2OwnershipTest `
        -Condition (Test-Na2TestProcessRunning -Id $child.Id) `
        -Message 'Changed-descriptor cleanup terminated the test process.'

    Write-Na2Pcsx2OwnershipDescriptor `
        -Path $descriptorPath `
        -Descriptor $descriptor `
        -OwnershipCapability $capability
    $stopped = Stop-Na2Pcsx2Process `
        -DescriptorPath $descriptorPath `
        -OwnershipCapability $capability `
        -Executable $executable `
        -ExecutableIdentity $executableIdentity
    Assert-Na2OwnershipTest `
        -Condition ($stopped.Status -ceq 'Stopped') `
        -Message (
            "Valid descriptor/capability cleanup did not stop its owned process: " +
            "$($stopped.Status) $($stopped.Reason)"
        )
    Assert-Na2OwnershipTest `
        -Condition (-not (Test-Na2TestProcessRunning -Id $child.Id)) `
        -Message 'The valid owned test process remained running.'

    Write-Host 'NA2 PCSX2 ownership-capability tests passed.' -ForegroundColor Green
}
finally {
    if ($null -ne $child) {
        $remaining = Get-Process -Id $child.Id -ErrorAction SilentlyContinue
        if ($null -ne $remaining) {
            Stop-Process -Id $remaining.Id -Force
            $remaining.Dispose()
        }
        $child.Dispose()
    }
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
