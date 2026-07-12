$script:Na2Root = 'C:\Games\Modding\UN Modding\NA2 Modding'

function na2 {
    & (Join-Path $script:Na2Root 'scripts\apply_latest_na2.ps1') `
        -InputIso (Join-Path $script:Na2Root 'source\NA2.iso') `
        -OutputIso (Join-Path $script:Na2Root 'build\Current.iso') `
        -Pcsx2Exe (Join-Path $script:Na2Root 'pcsx2\pcsx2-qt.exe') `
        -PackageDirectory (Join-Path $HOME 'Downloads') `
        -Packages Font, Translation `
        @args
}

function na2t {
    & (Join-Path $script:Na2Root 'translation_package_builder\build_na2_translation_package.ps1') @args
}

Export-ModuleMember -Function na2, na2t
