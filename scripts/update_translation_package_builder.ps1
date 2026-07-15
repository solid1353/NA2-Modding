$ErrorActionPreference = 'Stop'

$na2Root = Split-Path -Parent $PSScriptRoot
$packages = Join-Path $na2Root 'packages'
$candidates = Get-ChildItem -LiteralPath $packages -File -Filter 'NA2_translation_package_builder*.zip' |
    ForEach-Object {
        $timestamp = ''
        if ($_.Name -match '(?<!\d)(20\d{6})[_-](\d{6})(?!\d)') {
            $timestamp = $Matches[1] + $Matches[2]
        }

        $version = -1
        if ($_.Name -match '(?i)(?:^|[_-])v(\d+)(?:[_-]|\.|\s|$)') {
            $version = [int]$Matches[1]
        }

        [pscustomobject]@{
            File = $_
            HasTimestamp = [int](-not [string]::IsNullOrEmpty($timestamp))
            Timestamp = $timestamp
            Version = $version
            Name = $_.Name.ToUpperInvariant()
        }
    }

$selected = $candidates |
    Sort-Object HasTimestamp, Timestamp, Version, Name -Descending |
    Select-Object -First 1
$zip = $selected.File

if (-not $zip) {
    throw "No NA2_translation_package_builder*.zip found in $packages. Add the newest builder package there and try again."
}

$trash = Join-Path $na2Root 'trash'
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmssfff'
$builder = Join-Path $na2Root 'translation_package_builder'

if (Test-Path -LiteralPath $builder) {
    New-Item -ItemType Directory -Path $trash -Force | Out-Null
    Move-Item -LiteralPath $builder -Destination (Join-Path $trash "translation_package_builder_removed_$timestamp")
}

Expand-Archive -LiteralPath $zip.FullName -DestinationPath $na2Root -Force
