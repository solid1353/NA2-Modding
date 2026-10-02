function Get-VisualRegressionPngCount {
    param(
        [Parameter(Mandatory)][string]$Directory,
        [string]$Filter = '*.png'
    )

    return @(
        Get-ChildItem `
            -LiteralPath $Directory `
            -Filter $Filter `
            -File `
            -ErrorAction SilentlyContinue
    ).Count
}

function Write-VisualRegressionJson {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Value
    )

    [void](New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($Path)) -Force)
    $temporary = "$Path.tmp-$([guid]::NewGuid().ToString('N'))"
    try {
        [IO.File]::WriteAllText(
            $temporary,
            (($Value | ConvertTo-Json -Depth 6) + "`n"),
            [Text.UTF8Encoding]::new($false)
        )
        [IO.File]::Move($temporary, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Test-VisualRegressionPathWithin {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Root
    )

    $prefix = [IO.Path]::GetFullPath($Root).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    return [IO.Path]::GetFullPath($Path).StartsWith(
        $prefix,
        [StringComparison]::OrdinalIgnoreCase
    )
}

function ConvertTo-VisualRegressionLongPath {
    param([Parameter(Mandatory)][string]$Path)

    $fullPath = [IO.Path]::GetFullPath($Path)
    if ([IO.Path]::DirectorySeparatorChar -cne '\') {
        return $fullPath
    }
    if ($fullPath.StartsWith('\\')) {
        return '\\?\UNC\' + $fullPath.Substring(2)
    }
    return '\\?\' + $fullPath
}

function Invoke-VisualRegressionFileOperation {
    param(
        [Parameter(Mandatory)][scriptblock]$Operation,
        [Parameter(Mandatory)][string]$Description,
        [ValidateRange(1, 100)][int]$AttemptCount = 50,
        [ValidateRange(1, 1000)][int]$RetryDelayMilliseconds = 100
    )

    for ($attempt = 1; $attempt -le $AttemptCount; $attempt++) {
        try {
            & $Operation
            return
        }
        catch [IO.IOException], [UnauthorizedAccessException] {
            if ($attempt -eq $AttemptCount) {
                throw "$Description failed after $AttemptCount attempts: $($_.Exception.Message)"
            }
            Start-Sleep -Milliseconds $RetryDelayMilliseconds
        }
    }
}

function Remove-VisualRegressionEmptyParents {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Boundary
    )

    $boundaryPath = [IO.Path]::GetFullPath($Boundary).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $current = [IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Path))
    while (
        -not [string]::IsNullOrWhiteSpace($current) -and
        -not $current.Equals($boundaryPath, [StringComparison]::OrdinalIgnoreCase)
    ) {
        $parent = [IO.Path]::GetDirectoryName($current)
        if (
            -not (Test-VisualRegressionPathWithin -Path $current -Root $boundaryPath) -or
            -not (Test-Path -LiteralPath $current -PathType Container) -or
            @(Get-ChildItem -LiteralPath $current -Force).Count -ne 0
        ) {
            break
        }
        Remove-Item -LiteralPath $current -Force
        $current = $parent
    }
}
