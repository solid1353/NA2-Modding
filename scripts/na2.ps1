[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Mode,

    [Alias('i')]
    [string]$InputIso,
    [Alias('o')]
    [string]$OutputIso,
    [Alias('d')]
    [string]$PackageDirectory,
    [Alias('e')]
    [string]$Pcsx2Exe,
    [Alias('p')]
    [string[]]$Packages,
    [Alias('b')]
    [switch]$BuildOnly,
    [Alias('r')]
    [switch]$RunOnly,
    [Alias('h')]
    [switch]$Help,

    [string]$Na2Iso,
    [string]$OutputDirectory,
    [string]$BtlApplyTsv,
    [string]$EtcApplyTsv,
    [switch]$NoStrictHash,

    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]]$RemainingArguments
)

$na2Root = 'C:\Games\Modding\UN Modding\NA2 Modding'
$command = if ($Mode) { $Mode.ToLowerInvariant() } else { '' }
if ($command -eq 'tr') {
    $builderArgs = @{}
    @{
        Na2Iso          = $Na2Iso
        OutputDirectory = $OutputDirectory
        BtlApplyTsv     = $BtlApplyTsv
        EtcApplyTsv     = $EtcApplyTsv
    }.GetEnumerator() | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.Value) } |
        ForEach-Object { $builderArgs[$_.Key] = $_.Value }
    if ($NoStrictHash) { $builderArgs.NoStrictHash = $true }

    $builder = Join-Path $na2Root 'translation_package_builder\build_na2_translation_package.ps1'
    if ($RemainingArguments.Count) {
        & $builder @builderArgs @RemainingArguments
    } else {
        & $builder @builderArgs
    }
    return
}

if ($command -and $command -notmatch '^(f|t|ft|tf)$') {
    throw "Unknown NA2 command: $Mode"
}

$applyArgs = @{
    InputIso         = Join-Path $na2Root 'source\NA2.iso'
    OutputIso        = Join-Path $na2Root 'build\Current.iso'
    PackageDirectory = Join-Path $HOME 'Downloads'
    Pcsx2Exe         = Join-Path $na2Root 'pcsx2\pcsx2-qt.exe'
}
@{
    InputIso         = $InputIso
    OutputIso        = $OutputIso
    PackageDirectory = $PackageDirectory
    Pcsx2Exe         = $Pcsx2Exe
}.GetEnumerator() | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.Value) } |
    ForEach-Object { $applyArgs[$_.Key] = $_.Value }

if ($Packages)  { $applyArgs.Packages = $Packages }
if ($BuildOnly) { $applyArgs.BuildOnly = $true }
if ($RunOnly)   { $applyArgs.RunOnly = $true }
if ($Help)      { $applyArgs.Help = $true }

if ($command) {
    $packageNames = @{ f = 'Font'; t = 'Translation' }
    $applyArgs.Packages = $command.ToCharArray() | ForEach-Object {
        $packageNames[[string]$_]
    }
}

$apply = Join-Path $na2Root 'scripts\apply_latest_na2.ps1'
if ($RemainingArguments.Count) {
    & $apply @applyArgs @RemainingArguments
} else {
    & $apply @applyArgs
}
