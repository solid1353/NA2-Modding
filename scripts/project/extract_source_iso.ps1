param(
    [Parameter(Mandatory = $true)]
    [string]$IsoPath,

    [Parameter(Mandatory = $true)]
    [string]$TaskTitle,

    [string]$CvmPassword = "",

    [switch]$KeepFailedWork
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths

$extractIsoScript = Join-Path $projectPaths.media_scripts 'extract_iso.ps1'
$extractAfsScript = Join-Path $projectPaths.media_scripts 'extract_afs.ps1'
$splitCvmScript = Join-Path $projectPaths.media_scripts 'split_cvm_rofs.ps1'
$verifyExtractionScript = Join-Path $PSScriptRoot 'verify_source_extraction.py'
$setReadOnlyScript = Join-Path $PSScriptRoot 'set_source_readonly.ps1'

function Test-PathInside {
    param(
        [string]$Path,
        [string]$Root
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullRoot = [IO.Path]::GetFullPath($Root)
    $prefix = $fullRoot.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    return $fullPath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)
}

function Set-DerivedTime {
    param(
        [string]$Path,
        [DateTime]$RecordedAt
    )

    if ((Get-Item -LiteralPath $Path).PSIsContainer) {
        [IO.Directory]::SetCreationTime($Path, $RecordedAt)
        [IO.Directory]::SetLastWriteTime($Path, $RecordedAt)
    }
    else {
        [IO.File]::SetCreationTime($Path, $RecordedAt)
        [IO.File]::SetLastWriteTime($Path, $RecordedAt)
    }
}

function Get-FinalAlias {
    param(
        [string]$StagePath,
        [string]$StageRoot,
        [string]$FinalRoot
    )

    $relative = [IO.Path]::GetRelativePath($StageRoot, $StagePath).Replace([IO.Path]::DirectorySeparatorChar, '/')
    $finalPath = if ($relative -eq '.') { $FinalRoot } else { Join-Path $FinalRoot $relative }
    return ConvertTo-Na2ProjectPath -Path $finalPath -ProjectPaths $projectPaths
}

if (-not (Test-Path -LiteralPath $IsoPath -PathType Leaf)) {
    throw "ISO not found: $IsoPath"
}

if ([string]::IsNullOrWhiteSpace($TaskTitle) -or
    $TaskTitle -ne $TaskTitle.Trim() -or
    $TaskTitle -in @('.', '..') -or
    $TaskTitle.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0) {
    throw "TaskTitle must be one exact task-title directory name, without path separators: $TaskTitle"
}

$IsoPath = (Resolve-Path -LiteralPath $IsoPath).Path
$isoItem = Get-Item -LiteralPath $IsoPath
if (-not [IO.Path]::Equals($isoItem.Directory.FullName, $projectPaths.source)) {
    throw "Source ISO must be a direct child of @source; refusing nested or __old input: $IsoPath"
}
if ([string]::IsNullOrWhiteSpace($CvmPassword)) {
    $CvmPassword = switch ($isoItem.Name) {
        'NUN6_A35.iso' { 'Iruka' }
        default { 'cc2fuku' }
    }
}

$finalRoot = Join-Path $isoItem.DirectoryName ($isoItem.Name + '.files')
if (Test-Path -LiteralPath $finalRoot) {
    throw "Final extraction already exists; refusing to merge or overwrite: $finalRoot"
}

$runId = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$runId = $runId + "_pid" + $PID + "_" + $isoItem.BaseName
$taskWorkRoot = Join-Path $projectPaths.work $TaskTitle
$stageParent = Join-Path $taskWorkRoot 'temp\source_extraction'
$stageRun = Join-Path $stageParent $runId
$stageRoot = Join-Path $stageRun ($isoItem.Name + '.files')
$logDir = Join-Path $projectPaths.workstream_logs ("Project\extraction\" + $runId)
$summaryPath = Join-Path $logDir 'summary.tsv'
$inventoryPath = Join-Path $logDir 'inventory.tsv'

if (-not (Test-PathInside -Path $stageRun -Root $stageParent)) {
    throw "Unsafe staging path: $stageRun"
}

$summary = [System.Collections.Generic.List[object]]::new()
$movedToFinal = $false
$completed = $false
$failed = $false

try {
    New-Item -ItemType Directory -Force -Path $stageRun | Out-Null
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null

    & $extractIsoScript -IsoPath $IsoPath -OutDir $stageRoot -NoLog *> $null
    $summary.Add([pscustomobject]@{
        Kind = 'iso'
        Archive = ConvertTo-Na2ProjectPath -Path $IsoPath -ProjectPaths $projectPaths
        ExtractedDir = ConvertTo-Na2ProjectPath -Path $finalRoot -ProjectPaths $projectPaths
        TimestampSource = 'iso9660_recording_time'
    })

    while ($true) {
        $processedOne = $false

        $pendingCvm = @(
            Get-ChildItem -LiteralPath $stageRoot -Recurse -Force -File |
                Where-Object {
                    $_.Extension -ieq '.cvm' -and
                    -not (Test-Path -LiteralPath ($_.FullName + '.files'))
                } |
                Sort-Object FullName
        )
        if ($pendingCvm.Count -gt 0) {
            $cvm = $pendingCvm[0]
            $cvmOut = $cvm.FullName + '.files'
            $innerIso = Join-Path $cvmOut ($cvm.Name + '.iso')
            $innerHeader = Join-Path $cvmOut ($cvm.Name + '.hdr')
            New-Item -ItemType Directory -Path $cvmOut | Out-Null
            & $splitCvmScript -CvmPath $cvm.FullName -OutIsoPath $innerIso -OutHeaderPath $innerHeader -Password $CvmPassword *> $null
            Set-DerivedTime -Path $innerIso -RecordedAt $cvm.LastWriteTime
            Set-DerivedTime -Path $innerHeader -RecordedAt $cvm.LastWriteTime
            Set-DerivedTime -Path $cvmOut -RecordedAt $cvm.LastWriteTime
            $summary.Add([pscustomobject]@{
                Kind = 'cvm'
                Archive = Get-FinalAlias -StagePath $cvm.FullName -StageRoot $stageRoot -FinalRoot $finalRoot
                ExtractedDir = Get-FinalAlias -StagePath $cvmOut -StageRoot $stageRoot -FinalRoot $finalRoot
                TimestampSource = 'container_fallback_for_derived_files'
            })
            $processedOne = $true
        }
        if ($processedOne) { continue }

        $pendingIso = @(
            Get-ChildItem -LiteralPath $stageRoot -Recurse -Force -File |
                Where-Object {
                    $_.Extension -ieq '.iso' -and
                    -not (Test-Path -LiteralPath ($_.FullName + '.files'))
                } |
                Sort-Object FullName
        )
        if ($pendingIso.Count -gt 0) {
            $innerIso = $pendingIso[0]
            $innerOut = $innerIso.FullName + '.files'
            & $extractIsoScript -IsoPath $innerIso.FullName -OutDir $innerOut -NoLog *> $null
            $summary.Add([pscustomobject]@{
                Kind = 'iso'
                Archive = Get-FinalAlias -StagePath $innerIso.FullName -StageRoot $stageRoot -FinalRoot $finalRoot
                ExtractedDir = Get-FinalAlias -StagePath $innerOut -StageRoot $stageRoot -FinalRoot $finalRoot
                TimestampSource = 'iso9660_recording_time'
            })
            $processedOne = $true
        }
        if ($processedOne) { continue }

        $pendingAfs = @(
            Get-ChildItem -LiteralPath $stageRoot -Recurse -Force -File |
                Where-Object {
                    $_.Extension -ieq '.afs' -and
                    -not (Test-Path -LiteralPath ($_.FullName + '.files'))
                } |
                Sort-Object FullName
        )
        if ($pendingAfs.Count -gt 0) {
            $afs = $pendingAfs[0]
            $afsOut = $afs.FullName + '.files'
            & $extractAfsScript -AfsPath $afs.FullName -OutDir $afsOut -NoLog *> $null
            $summary.Add([pscustomobject]@{
                Kind = 'afs'
                Archive = Get-FinalAlias -StagePath $afs.FullName -StageRoot $stageRoot -FinalRoot $finalRoot
                ExtractedDir = Get-FinalAlias -StagePath $afsOut -StageRoot $stageRoot -FinalRoot $finalRoot
                TimestampSource = 'afs_metadata_or_container_fallback'
            })
            if (($summary.Count % 25) -eq 0) {
                Write-Host "Expanded containers:" $summary.Count
            }
            $processedOne = $true
        }

        if (-not $processedOne) { break }
    }

    $unsupported = @(
        Get-ChildItem -LiteralPath $stageRoot -Recurse -Force -File |
            Where-Object {
                $_.Extension -in @('.iso', '.cvm', '.afs') -and
                -not (Test-Path -LiteralPath ($_.FullName + '.files'))
            }
    )
    if ($unsupported.Count -gt 0) {
        throw "Supported archives remain unexpanded: $($unsupported.FullName -join ', ')"
    }

    & python $verifyExtractionScript --iso $IsoPath --out-dir $stageRoot --normalize-timestamps
    if ($LASTEXITCODE -ne 0) {
        throw "Recursive extraction verification failed with exit code $LASTEXITCODE."
    }

    if (Test-Path -LiteralPath $finalRoot) {
        throw "Final extraction appeared during staging: $finalRoot"
    }
    Move-Item -LiteralPath $stageRoot -Destination $finalRoot
    $movedToFinal = $true

    & $setReadOnlyScript -SourceDir $finalRoot | Out-Null
    $isoItem.Attributes = $isoItem.Attributes -bor [IO.FileAttributes]::ReadOnly

    $summary | Export-Csv -LiteralPath $summaryPath -Delimiter "`t" -NoTypeInformation -Encoding UTF8
    $inventory = Get-ChildItem -LiteralPath $finalRoot -Recurse -Force | ForEach-Object {
        [pscustomobject]@{
            Path = ConvertTo-Na2ProjectPath -Path $_.FullName -ProjectPaths $projectPaths
            Type = if ($_.PSIsContainer) { 'dir' } else { 'file' }
            Size = if ($_.PSIsContainer) { '' } else { $_.Length }
            CreationTime = $_.CreationTime.ToString('yyyy-MM-ddTHH:mm:ss')
            LastWriteTime = $_.LastWriteTime.ToString('yyyy-MM-ddTHH:mm:ss')
        }
    }
    $inventory | Export-Csv -LiteralPath $inventoryPath -Delimiter "`t" -NoTypeInformation -Encoding UTF8

    Write-Host "Recursive source extraction complete:"
    Write-Host (ConvertTo-Na2ProjectPath -Path $IsoPath -ProjectPaths $projectPaths)
    Write-Host "Output:"
    Write-Host (ConvertTo-Na2ProjectPath -Path $finalRoot -ProjectPaths $projectPaths)
    Write-Host "Containers:"
    Write-Host $summary.Count
    Write-Host "Log:"
    Write-Host (ConvertTo-Na2ProjectPath -Path $logDir -ProjectPaths $projectPaths)
    $completed = $true
}
catch {
    $failed = $true
    throw
}
finally {
    if (Test-Path -LiteralPath $stageRun) {
        $canRemove = Test-PathInside -Path $stageRun -Root $stageParent
        if (-not $canRemove) {
            throw "Refusing to clean unsafe staging path: $stageRun"
        }
        if (-not $failed -or -not $KeepFailedWork) {
            Remove-Item -LiteralPath $stageRun -Recurse -Force
        }
    }
    if ($failed -and $movedToFinal -and -not $completed -and -not $KeepFailedWork -and (Test-Path -LiteralPath $finalRoot)) {
        Remove-Item -LiteralPath $finalRoot -Recurse -Force
    }
    if ($failed -and -not $KeepFailedWork -and (Test-Path -LiteralPath $logDir)) {
        Remove-Item -LiteralPath $logDir -Recurse -Force
    }
}
