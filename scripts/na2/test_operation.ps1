Set-StrictMode -Version Latest

function Resolve-Na2TaskOwnedFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][psobject]$Worker,
        [Parameter(Mandatory = $true)][string]$Repository,
        [string]$RequiredExtension
    )

    if ([IO.Path]::IsPathRooted($Path)) {
        throw 'Task operation paths must be repository-relative.'
    }
    $resolved = [IO.Path]::GetFullPath((Join-Path $Repository $Path))
    $workerPrefix = $Worker.Root.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $resolved.StartsWith($workerPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Task operation path must stay below work/$($Worker.WorkerName)/."
    }
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "Task operation file does not exist: $Path"
    }
    if (-not [string]::IsNullOrWhiteSpace($RequiredExtension) -and
        [IO.Path]::GetExtension($resolved) -ine $RequiredExtension) {
        throw "Task operation input must use the $RequiredExtension extension."
    }
    return $resolved
}

function Get-Na2TestOperationPlan {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$Path)

    try {
        $plan = [IO.File]::ReadAllText($Path) | ConvertFrom-Json
    }
    catch {
        throw "Task operation plan is not valid JSON: $($_.Exception.Message)"
    }
    if ($plan -is [array] -or $null -eq $plan) {
        throw 'Task operation plan root must be a JSON object.'
    }
    $schemaProperty = $plan.PSObject.Properties['schema_version']
    if ($null -eq $schemaProperty -or [int]$schemaProperty.Value -ne 1) {
        $schemaValue = if ($null -eq $schemaProperty) {
            '<missing>'
        }
        else {
            [string]$schemaProperty.Value
        }
        throw "Unsupported task operation plan schema: $schemaValue"
    }
    $actionsProperty = $plan.PSObject.Properties['actions']
    $actions = if ($null -eq $actionsProperty) {
        @()
    }
    else {
        @($actionsProperty.Value)
    }
    if ($actions.Count -lt 1 -or $actions.Count -gt 100) {
        throw 'Task operation plans must contain between 1 and 100 actions.'
    }
    $supportedActions = @(
        'identity',
        'load_state',
        'read_memory',
        'patch_memory',
        'save_state',
        'capture_state',
        'wait'
    )
    foreach ($action in $actions) {
        $actionProperty = $action.PSObject.Properties['action']
        if ($null -eq $actionProperty -or
            [string]::IsNullOrWhiteSpace([string]$actionProperty.Value)) {
            throw 'Every task operation action must have an action name.'
        }
        $actionName = ([string]$actionProperty.Value).Trim().ToLowerInvariant()
        if ($actionName -notin $supportedActions) {
            throw "Unsupported task operation action: $actionName"
        }
    }
    $resultProperty = $plan.PSObject.Properties['result_path']
    return [pscustomobject]@{
        Actions = $actions
        ResultPath = if ($null -eq $resultProperty) {
            ''
        }
        else {
            [string]$resultProperty.Value
        }
    }
}

function ConvertFrom-Na2OperationHexBytes {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$FieldName
    )

    $normalized = $Value.Trim()
    if ($normalized.StartsWith('0x', [StringComparison]::OrdinalIgnoreCase)) {
        $normalized = $normalized.Substring(2)
    }
    if ([string]::IsNullOrWhiteSpace($normalized) -or
        $normalized.Length % 2 -ne 0 -or
        $normalized -notmatch '^[0-9A-Fa-f]+$') {
        throw "$FieldName must be a non-empty even-length hexadecimal byte string."
    }
    return ,([Convert]::FromHexString($normalized))
}

function ConvertTo-Na2OperationAddress {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]$Value,
        [Parameter(Mandatory = $true)][string]$FieldName
    )

    if ($Value -is [string]) {
        $text = ([string]$Value).Trim()
        $style = [Globalization.NumberStyles]::Integer
        if ($text.StartsWith('0x', [StringComparison]::OrdinalIgnoreCase)) {
            $text = $text.Substring(2)
            $style = [Globalization.NumberStyles]::AllowHexSpecifier
        }
        [uint32]$parsed = 0
        if (-not [uint32]::TryParse(
            $text,
            $style,
            [Globalization.CultureInfo]::InvariantCulture,
            [ref]$parsed
        )) {
            throw "$FieldName is not a valid 32-bit address."
        }
        return $parsed
    }
    try {
        return [uint32]$Value
    }
    catch {
        throw "$FieldName is not a valid 32-bit address."
    }
}

function Get-Na2OperationInteger {
    [CmdletBinding()]
    param(
        $Value,
        [Parameter(Mandatory = $true)][string]$FieldName,
        [Parameter(Mandatory = $true)][int]$Minimum,
        [Parameter(Mandatory = $true)][int]$Maximum,
        [Parameter(Mandatory = $true)][int]$Default
    )

    if ($null -eq $Value) { return $Default }
    try {
        $parsed = [int]$Value
    }
    catch {
        throw "$FieldName must be an integer."
    }
    if ($parsed -lt $Minimum -or $parsed -gt $Maximum) {
        throw "$FieldName must be between $Minimum and $Maximum."
    }
    return $parsed
}

function Get-Na2OperationProperty {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Write-Na2TestOperationResult {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )

    $content = ($Value | ConvertTo-Json -Depth 8) + "`n"
    New-Item `
        -ItemType Directory `
        -Force `
        -Path ([IO.Path]::GetDirectoryName($Path)) | Out-Null
    $temporary = "$Path.$PID.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        [IO.File]::WriteAllText(
            $temporary,
            $content,
            [Text.UTF8Encoding]::new($false)
        )
        [IO.File]::Move($temporary, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Resolve-Na2TaskOwnedOutputPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][psobject]$Worker,
        [Parameter(Mandatory = $true)][string]$Repository,
        [string]$RequiredExtension
    )

    if ([IO.Path]::IsPathRooted($Path)) {
        throw 'Task operation output paths must be repository-relative.'
    }
    $resolved = [IO.Path]::GetFullPath((Join-Path $Repository $Path))
    $workerPrefix = $Worker.Root.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $resolved.StartsWith($workerPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Task operation output must stay below work/$($Worker.WorkerName)/."
    }
    if (-not [string]::IsNullOrWhiteSpace($RequiredExtension) -and
        [IO.Path]::GetExtension($resolved) -ine $RequiredExtension) {
        throw "Task operation output must use the $RequiredExtension extension."
    }
    return $resolved
}

function Get-Na2Pcsx2StateSlotPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$StateDirectory,
        [Parameter(Mandatory = $true)][string]$Serial,
        [Parameter(Mandatory = $true)][string]$CRC,
        [Parameter(Mandatory = $true)][ValidateRange(0, 99)][int]$Slot
    )

    Join-Path $StateDirectory (
        '{0} ({1}).{2:D2}.p2s' -f $Serial, $CRC.ToUpperInvariant(), $Slot
    )
}

function Copy-Na2Pcsx2StateToSlot {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$DestinationPath
    )

    $resolvedSource = [IO.Path]::GetFullPath($SourcePath)
    $resolvedDestination = [IO.Path]::GetFullPath($DestinationPath)
    if ([IO.Path]::Equals($resolvedSource, $resolvedDestination)) {
        return $resolvedDestination
    }
    $temporary = "$resolvedDestination.$PID.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        [IO.File]::Copy($resolvedSource, $temporary, $true)
        if ((Get-Item -LiteralPath $temporary).Length -le 0) {
            throw 'The task-owned savestate is empty.'
        }
        [IO.File]::Move($temporary, $resolvedDestination, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
    return $resolvedDestination
}

function Get-Na2Pcsx2StateSignature {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $item = Get-Item -LiteralPath $Path
    return "$($item.Length):$($item.LastWriteTimeUtc.Ticks)"
}

function Test-Na2Pcsx2StateScreenshot {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$Path)

    try {
        $archive = [IO.Compression.ZipFile]::OpenRead($Path)
        try {
            return $null -ne ($archive.Entries | Where-Object {
                $_.FullName -ceq 'Screenshot.png' -and $_.Length -gt 0
            } | Select-Object -First 1)
        }
        finally {
            $archive.Dispose()
        }
    }
    catch {
        return $false
    }
}

function Wait-Na2Pcsx2StateCapture {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [string]$PreviousSignature,
        [ValidateRange(1, 300)][int]$TimeoutSeconds = 30
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $lastSignature = $null
    $stableSamples = 0
    do {
        $signature = Get-Na2Pcsx2StateSignature -Path $Path
        if ($null -ne $signature -and $signature -cne $PreviousSignature) {
            if ($signature -ceq $lastSignature) {
                $stableSamples += 1
            }
            else {
                $lastSignature = $signature
                $stableSamples = 1
            }
            if ($stableSamples -ge 3 -and
                (Test-Na2Pcsx2StateScreenshot -Path $Path)) {
                return [IO.Path]::GetFullPath($Path)
            }
        }
        Start-Sleep -Milliseconds 200
    } while ([DateTime]::UtcNow -lt $deadline)

    throw "PCSX2 did not produce a stable savestate with Screenshot.png within $TimeoutSeconds seconds."
}

function Export-Na2Pcsx2StateScreenshot {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$StatePath,
        [Parameter(Mandatory = $true)][string]$OutputPath
    )

    New-Item `
        -ItemType Directory `
        -Force `
        -Path ([IO.Path]::GetDirectoryName($OutputPath)) | Out-Null
    $temporary = "$OutputPath.$PID.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        $archive = [IO.Compression.ZipFile]::OpenRead($StatePath)
        try {
            $entry = $archive.Entries | Where-Object {
                $_.FullName -ceq 'Screenshot.png' -and $_.Length -gt 0
            } | Select-Object -First 1
            if ($null -eq $entry) {
                throw 'The captured savestate has no non-empty Screenshot.png.'
            }
            $input = $entry.Open()
            try {
                $output = [IO.File]::Open(
                    $temporary,
                    [IO.FileMode]::Create,
                    [IO.FileAccess]::Write,
                    [IO.FileShare]::None
                )
                try {
                    $input.CopyTo($output)
                }
                finally {
                    $output.Dispose()
                }
            }
            finally {
                $input.Dispose()
            }
        }
        finally {
            $archive.Dispose()
        }
        $header = [IO.File]::ReadAllBytes($temporary)
        if ($header.Length -lt 8 -or
            $header[0] -ne 0x89 -or
            $header[1] -ne 0x50 -or
            $header[2] -ne 0x4E -or
            $header[3] -ne 0x47 -or
            $header[4] -ne 0x0D -or
            $header[5] -ne 0x0A -or
            $header[6] -ne 0x1A -or
            $header[7] -ne 0x0A) {
            throw 'The embedded savestate screenshot is not a PNG.'
        }
        [IO.File]::Move($temporary, $OutputPath, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
    return [IO.Path]::GetFullPath($OutputPath)
}
