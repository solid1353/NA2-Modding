[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'test_operation.ps1')

function Assert-Na2OperationTest {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

$testRoot = Join-Path ([IO.Path]::GetTempPath()) (
    "na2-test-operation-$PID-$([guid]::NewGuid().ToString('N'))"
)
try {
    $repository = Join-Path $testRoot 'repository'
    $workerRoot = Join-Path $repository 'work\Font'
    $inputDirectory = Join-Path $workerRoot 'inputs\sstates'
    $stateDirectory = Join-Path $workerRoot 'artifacts\sstates\run'
    New-Item -ItemType Directory -Force -Path @(
        $inputDirectory,
        $stateDirectory
    ) | Out-Null
    $worker = [pscustomobject]@{
        WorkerName = 'Font'
        Root = $workerRoot
    }

    $operationPath = Join-Path $workerRoot 'operation.json'
    [IO.File]::WriteAllText(
        $operationPath,
        @'
{
  "schema_version": 1,
  "result_path": "work/Font/artifacts/runtime/result.json",
  "actions": [
    {
      "action": "read_memory",
      "address": "0x00123450",
      "expected_hex": "00112233"
    }
  ]
}
'@
    )
    $resolvedOperation = Resolve-Na2TaskOwnedFile `
        -Path 'work\Font\operation.json' `
        -Worker $worker `
        -Repository $repository `
        -RequiredExtension '.json'
    Assert-Na2OperationTest `
        -Condition ([IO.Path]::Equals($resolvedOperation, $operationPath)) `
        -Message 'The task-owned operation plan did not resolve.'
    $operation = Get-Na2TestOperationPlan -Path $resolvedOperation
    Assert-Na2OperationTest `
        -Condition (
            $operation.Actions.Count -eq 1 -and
            $operation.Actions[0].action -ceq 'read_memory' -and
            $operation.ResultPath -ceq 'work/Font/artifacts/runtime/result.json'
        ) `
        -Message 'The maintained JSON operation plan contract did not parse.'
    $address = ConvertTo-Na2OperationAddress `
        -Value $operation.Actions[0].address `
        -FieldName 'address'
    $bytes = ConvertFrom-Na2OperationHexBytes `
        -Value $operation.Actions[0].expected_hex `
        -FieldName 'expected_hex'
    Assert-Na2OperationTest `
        -Condition (
            $address -eq 0x00123450 -and
            [Convert]::ToHexString($bytes) -ceq '00112233'
        ) `
        -Message 'Operation-plan address or exact-byte parsing is incorrect.'
    $resultPath = Resolve-Na2TaskOwnedOutputPath `
        -Path $operation.ResultPath `
        -Worker $worker `
        -Repository $repository `
        -RequiredExtension '.json'
    Write-Na2TestOperationResult `
        -Path $resultPath `
        -Value ([ordered]@{ schema_version = 1; actions = @() })
    Assert-Na2OperationTest `
        -Condition (
            (Test-Path -LiteralPath $resultPath -PathType Leaf) -and
            ([IO.File]::ReadAllText($resultPath) | ConvertFrom-Json).schema_version -eq 1
        ) `
        -Message 'The portable task-owned operation result was not written atomically.'

    $outsidePath = Join-Path $repository 'outside.json'
    [IO.File]::WriteAllText($outsidePath, "{}")
    $outsideRejected = $false
    try {
        Resolve-Na2TaskOwnedFile `
            -Path 'outside.json' `
            -Worker $worker `
            -Repository $repository `
            -RequiredExtension '.json' | Out-Null
    }
    catch {
        $outsideRejected = $true
    }
    Assert-Na2OperationTest `
        -Condition $outsideRejected `
        -Message 'An operation plan outside the worker root was accepted.'

    $unsupportedPath = Join-Path $workerRoot 'unsupported.json'
    [IO.File]::WriteAllText(
        $unsupportedPath,
        '{"schema_version":1,"actions":[{"action":"run_script"}]}'
    )
    $unsupportedRejected = $false
    try {
        Get-Na2TestOperationPlan -Path $unsupportedPath | Out-Null
    }
    catch {
        $unsupportedRejected = $_.Exception.Message -match (
            'Unsupported task operation action'
        )
    }
    Assert-Na2OperationTest `
        -Condition $unsupportedRejected `
        -Message 'An unsupported operation-plan action was accepted.'

    $sourceState = Join-Path $inputDirectory 'source.p2s'
    $archive = [IO.Compression.ZipFile]::Open(
        $sourceState,
        [IO.Compression.ZipArchiveMode]::Create
    )
    try {
        $entry = $archive.CreateEntry('Screenshot.png')
        $stream = $entry.Open()
        try {
            $pngMarker = [byte[]]@(0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A)
            $stream.Write($pngMarker, 0, $pngMarker.Length)
        }
        finally {
            $stream.Dispose()
        }
    }
    finally {
        $archive.Dispose()
    }

    $slotPath = Get-Na2Pcsx2StateSlotPath `
        -StateDirectory $stateDirectory `
        -Serial 'SLPS-25837' `
        -CRC 'C0659AD1' `
        -Slot 7
    Assert-Na2OperationTest `
        -Condition ([IO.Path]::GetFileName($slotPath) -ceq 'SLPS-25837 (C0659AD1).07.p2s') `
        -Message 'The PCSX2 savestate slot filename is incorrect.'
    Copy-Na2Pcsx2StateToSlot `
        -SourcePath $sourceState `
        -DestinationPath $slotPath | Out-Null
    Assert-Na2OperationTest `
        -Condition (Test-Na2Pcsx2StateScreenshot -Path $slotPath) `
        -Message 'The copied task-owned savestate lost its embedded screenshot.'
    $captured = Wait-Na2Pcsx2StateCapture `
        -Path $slotPath `
        -TimeoutSeconds 3
    Assert-Na2OperationTest `
        -Condition ([IO.Path]::Equals($captured, $slotPath)) `
        -Message 'A stable captured savestate was not returned.'
    $screenshotPath = Resolve-Na2TaskOwnedOutputPath `
        -Path 'work\Font\artifacts\screenshots\capture.png' `
        -Worker $worker `
        -Repository $repository `
        -RequiredExtension '.png'
    $exported = Export-Na2Pcsx2StateScreenshot `
        -StatePath $captured `
        -OutputPath $screenshotPath
    Assert-Na2OperationTest `
        -Condition (
            [IO.Path]::Equals($exported, $screenshotPath) -and
            (Get-Item -LiteralPath $screenshotPath).Length -eq 8
        ) `
        -Message 'The embedded screenshot was not exported to the task-owned output.'

    Write-Host 'NA2 in-process test-operation helper tests passed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
