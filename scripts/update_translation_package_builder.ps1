$ErrorActionPreference = 'Stop'

$na2Root = 'C:\Games\Modding\UN Modding\NA2 Modding'
$downloads = Join-Path $HOME 'Downloads'
$zip = Get-ChildItem -LiteralPath $downloads -File -Filter 'NA2_translation_package_builder*.zip' |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $zip) {
    throw 'No NA2_translation_package_builder*.zip found in Downloads'
}

$target = Join-Path $na2Root 'translation_package_builder'
$trash = Join-Path $na2Root 'trash'

if (Test-Path -LiteralPath $target) {
    New-Item -ItemType Directory -Path $trash -Force | Out-Null
    $removed = Join-Path $trash ('translation_package_builder_removed_' + (Get-Date -Format 'yyyyMMdd_HHmmssfff'))
    Move-Item -LiteralPath $target -Destination $removed
}

Expand-Archive -LiteralPath $zip.FullName -DestinationPath $na2Root -Force
