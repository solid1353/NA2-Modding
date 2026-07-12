# NA2 Translation Package Builder

This tool replaces the old ISO-patcher workflow for translation builds.
It does not create or modify an ISO.

It reads the clean source ISO:

`C:\Games\Modding\UN Modding\NA2 Modding\source\NA2.iso`

It applies:

- `translations\apply\btl_apply.tsv`
- `translations\apply\etc_apply.tsv`

It writes a self-contained package to:

`C:\Users\solid\Downloads\NA2_APPLY__TRANSLATION__*.zip`

The package contains exactly:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`

Run:

```powershell
.\build_na2_translation_package.ps1
```

Then test it with:

```powershell
na2 -Translation
```

Optional overrides:

```powershell
.\build_na2_translation_package.ps1 `
  -Na2Iso 'D:\path\NA2.iso' `
  -OutputDirectory 'D:\output'
```

`-NoStrictHash` permits a source whose BTL/ETC hashes differ from the known clean NA2 files. Normally leave strict checking enabled.
