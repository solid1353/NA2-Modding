Set-StrictMode -Version Latest

function Invoke-Na2BuildRegistry {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][ValidateSet('lookup', 'record', 'resolve')]
        [string]$Command,
        [Parameter(Mandatory)][string]$Registry,
        [Parameter(Mandatory)][string]$BuildRoot,
        [Parameter(Mandatory)][string]$Repository,
        [Parameter(Mandatory)][string]$PythonRunner,
        [string]$Na2Iso,
        [string]$Nun5Iso,
        [string]$Configuration,
        [string]$ConfigurationId,
        [string]$ExpectedFingerprint,
        [string]$Image,
        [string]$Provenance
    )

    $arguments = @($Command, '--registry', $Registry, '--cache-root', $BuildRoot)
    if ($Command -in @('lookup', 'record')) {
        $arguments += @(
            '--na2-iso', $Na2Iso,
            '--nun5-iso', $Nun5Iso,
            '--configuration', $Configuration
        )
    }
    if ($Command -eq 'record') {
        $arguments += @(
            '--expected-fingerprint', $ExpectedFingerprint,
            '--image', $Image
        )
        if (-not [string]::IsNullOrWhiteSpace($Provenance)) {
            $arguments += @('--provenance', $Provenance)
        }
    }
    elseif ($Command -eq 'resolve') {
        $arguments += @('--configuration-id', $ConfigurationId)
    }

    Push-Location $Repository
    try {
        $output = @(
            & $PythonRunner -PackageSet builder `
                -Module 'na228_builder.scripts.build_preflight' `
                -ArgumentList $arguments -NoBytecode 2>&1
        )
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    if ($exitCode -ne 0) {
        throw "NA2 build registry failed to execute (exit $exitCode): $($output -join "`n")"
    }
    if ($output.Count -ne 1) {
        throw 'NA2 build registry did not return exactly one JSON result.'
    }
    try {
        return $output[0] | ConvertFrom-Json
    }
    catch {
        throw "NA2 build registry returned invalid JSON: $($output[0])"
    }
}

function Resolve-Na2CachedBuild {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Configuration,
        [Parameter(Mandatory)][psobject]$Paths
    )

    $resolved = Invoke-Na2BuildRegistry -Command resolve `
        -Registry (Join-Path $Paths.logs 'na228\preflight\registry.json') `
        -BuildRoot $Paths.build `
        -Repository $Paths.repository `
        -PythonRunner (Join-Path ([string]$Paths.scripts) 'lib\run_python.ps1') `
        -ConfigurationId $Configuration
    if ($resolved.status -ne 'resolved') {
        throw "No cached build exists for '$Configuration'."
    }
    return $resolved
}

function Remove-Na2StaleIncomingImages {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$IncomingRoot)

    if (-not (Test-Path -LiteralPath $IncomingRoot -PathType Container)) { return }
    foreach ($image in Get-ChildItem -LiteralPath $IncomingRoot -File -Filter '*.iso') {
        $lockPath = $image.FullName + '.lock'
        $lock = $null
        try {
            $lock = [IO.File]::Open(
                $lockPath,
                [IO.FileMode]::OpenOrCreate,
                [IO.FileAccess]::ReadWrite,
                [IO.FileShare]::None
            )
        }
        catch [IO.IOException] { continue }
        try {
            try { [IO.File]::Delete($image.FullName) }
            catch [IO.IOException] { continue }
        }
        finally {
            $lock.Dispose()
            try { [IO.File]::Delete($lockPath) } catch [IO.IOException] {}
        }
    }
    foreach ($lockFile in Get-ChildItem -LiteralPath $IncomingRoot -File -Filter '*.iso.lock') {
        $imagePath = $lockFile.FullName.Substring(0, $lockFile.FullName.Length - 5)
        if (Test-Path -LiteralPath $imagePath) { continue }
        $lock = $null
        try {
            $lock = [IO.File]::Open(
                $lockFile.FullName,
                [IO.FileMode]::Open,
                [IO.FileAccess]::ReadWrite,
                [IO.FileShare]::None
            )
        }
        catch [IO.IOException] { continue }
        $lock.Dispose()
        try { [IO.File]::Delete($lockFile.FullName) } catch [IO.IOException] {}
    }
}

function Enter-Na2IncomingImage {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Image)

    [IO.File]::Open(
        ([IO.Path]::GetFullPath($Image) + '.lock'),
        [IO.FileMode]::CreateNew,
        [IO.FileAccess]::ReadWrite,
        [IO.FileShare]::None
    )
}

function Exit-Na2IncomingImage {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Image,
        [Parameter(Mandatory)][IO.FileStream]$Lock
    )

    $lockPath = [IO.Path]::GetFullPath($Image) + '.lock'
    $Lock.Dispose()
    if (Test-Path -LiteralPath $Image -PathType Leaf) {
        [IO.File]::Delete($Image)
    }
    if (Test-Path -LiteralPath $lockPath -PathType Leaf) {
        [IO.File]::Delete($lockPath)
    }
}
