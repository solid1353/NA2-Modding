[CmdletBinding()]
param(
    [psobject]$ProjectPaths,
    [switch]$PassThru
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')

if ($null -eq $ProjectPaths) {
    $ProjectPaths = Get-Na2ProjectPaths
}

if ($null -eq ('Na2Actualization.FileIdentity' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace Na2Actualization
{
    public static class FileIdentity
    {
        [StructLayout(LayoutKind.Sequential)]
        private struct ByHandleFileInformation
        {
            public uint FileAttributes;
            public System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
            public System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
            public System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
            public uint VolumeSerialNumber;
            public uint FileSizeHigh;
            public uint FileSizeLow;
            public uint NumberOfLinks;
            public uint FileIndexHigh;
            public uint FileIndexLow;
        }

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool GetFileInformationByHandle(
            SafeFileHandle handle,
            out ByHandleFileInformation information
        );

        public static string Read(string path)
        {
            using (FileStream stream = new FileStream(
                path,
                FileMode.Open,
                FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete))
            {
                ByHandleFileInformation information;
                if (!GetFileInformationByHandle(
                    stream.SafeFileHandle,
                    out information))
                {
                    throw new System.ComponentModel.Win32Exception(
                        Marshal.GetLastWin32Error()
                    );
                }
                return String.Format(
                    "{0:X8}:{1:X8}{2:X8}",
                    information.VolumeSerialNumber,
                    information.FileIndexHigh,
                    information.FileIndexLow
                );
            }
        }
    }
}
'@
}

function Test-Na2SameFile {
    param(
        [Parameter(Mandatory)][string]$Left,
        [Parameter(Mandatory)][string]$Right
    )

    return (
        [Na2Actualization.FileIdentity]::Read($Left) -ceq
        [Na2Actualization.FileIdentity]::Read($Right)
    )
}

$pairs = @(
    [pscustomobject]@{
        Name = 'game_settings'
        Source = $ProjectPaths.pcsx2_game_settings
        Destination = $ProjectPaths.pcsx2_user_gamesettings
    }
    [pscustomobject]@{
        Name = 'input_profiles'
        Source = $ProjectPaths.pcsx2_input_profiles
        Destination = $ProjectPaths.pcsx2_user_inputprofiles
    }
    [pscustomobject]@{
        Name = 'input_recordings'
        Source = $ProjectPaths.pcsx2_input_recordings
        Destination = $ProjectPaths.pcsx2_user_inputrecordings
    }
)

$created = [Collections.Generic.List[string]]::new()
$verified = [Collections.Generic.List[string]]::new()
foreach ($pair in $pairs) {
    $sourceRoot = [IO.Path]::GetFullPath([string]$pair.Source)
    $destinationRoot = [IO.Path]::GetFullPath([string]$pair.Destination)
    foreach ($root in $sourceRoot, $destinationRoot) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) {
            throw "Required hardlink directory not found: $root"
        }
    }

    foreach ($sourceItem in (
        Get-ChildItem -LiteralPath $sourceRoot -File -Recurse -Force |
            Sort-Object FullName
    )) {
        if ($sourceItem.LinkType -in @('SymbolicLink', 'Junction')) {
            throw "Project hardlink source must be a real file: $($sourceItem.FullName)"
        }
        $relativePath = [IO.Path]::GetRelativePath(
            $sourceRoot,
            $sourceItem.FullName
        )
        $destinationPath = [IO.Path]::GetFullPath(
            (Join-Path $destinationRoot $relativePath)
        )
        $destinationPrefix = $destinationRoot.TrimEnd(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        ) + [IO.Path]::DirectorySeparatorChar
        if (-not $destinationPath.StartsWith(
            $destinationPrefix,
            [StringComparison]::OrdinalIgnoreCase
        )) {
            throw "Hardlink destination escaped its configured root: $relativePath"
        }

        $destinationDirectory = [IO.Path]::GetDirectoryName($destinationPath)
        if (-not (Test-Path -LiteralPath $destinationDirectory -PathType Container)) {
            New-Item `
                -ItemType Directory `
                -Path $destinationDirectory `
                -Force |
                Out-Null
        }

        if (Test-Path -LiteralPath $destinationPath -PathType Leaf) {
            if (-not (Test-Na2SameFile `
                -Left $sourceItem.FullName `
                -Right $destinationPath)) {
                throw "Refusing differing occupied PCSX2 counterpart: $destinationPath"
            }
            $verified.Add("$($pair.Name)/$($relativePath.Replace('\', '/'))")
            continue
        }
        if (Test-Path -LiteralPath $destinationPath) {
            throw "PCSX2 counterpart is not a file: $destinationPath"
        }

        New-Item `
            -ItemType HardLink `
            -Path $destinationPath `
            -Target $sourceItem.FullName |
            Out-Null
        if (-not (Test-Na2SameFile `
            -Left $sourceItem.FullName `
            -Right $destinationPath)) {
            throw "Hardlink verification failed: $destinationPath"
        }
        $created.Add("$($pair.Name)/$($relativePath.Replace('\', '/'))")
    }
}

$result = [pscustomobject]@{
    Created = @($created)
    Verified = @($verified)
}
if ($PassThru) {
    $result
}
else {
    Write-Host (
        'PCSX2 hardlinks: created={0}; verified={1}.' -f
        $created.Count,
        $verified.Count
    )
}
