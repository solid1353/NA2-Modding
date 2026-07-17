function Get-Na2PnachState {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if ($item.PSIsContainer) {
        throw "PNACH path is not a file: $($item.FullName)"
    }

    $enabledCheats = [Collections.Generic.List[string]]::new()
    $seenCheats = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $metadataKeys = [Collections.Generic.HashSet[string]]::new(
        [string[]]@('author', 'comment', 'description', 'gametitle'),
        [StringComparer]::OrdinalIgnoreCase
    )
    $currentName = $null
    $lineNumber = 0

    foreach ($line in [IO.File]::ReadLines($item.FullName)) {
        $lineNumber++

        if ($line -match '^\s*//\s*#') {
            $currentName = $null
            continue
        }
        if ($line -match '^\s*//\s*\[(?<name>[^\]]+)\]\s*$') {
            $currentName = $Matches.name.Trim()
            continue
        }

        $trimmed = $line.TrimStart()
        if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith('//')) {
            continue
        }
        if ($trimmed -notmatch '^(?<key>[A-Za-z][A-Za-z0-9_.-]*)\s*=') {
            continue
        }

        $key = $Matches.key
        if ($metadataKeys.Contains($key)) {
            continue
        }

        $name = if ([string]::IsNullOrWhiteSpace($currentName)) {
            "unnamed line $lineNumber"
        }
        else {
            $currentName
        }
        if ($seenCheats.Add($name)) {
            $enabledCheats.Add($name)
        }
    }

    [pscustomobject]@{
        Path = $item.FullName
        Length = $item.Length
        IsEmpty = ($item.Length -eq 0)
        EnabledCheats = @($enabledCheats)
    }
}
