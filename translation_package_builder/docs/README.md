# NA2 Translation Package Builder v5

Builds a self-contained translation package from clean NA2 files and official
UN5 `PRG/TEXTENG.BIN` strings.

The builder:

- preserves the previously working safe BTL/ETC translation baseline;
- replaces verified matching entries with the official UN5 English wording;
- reads no translation TSV files;
- never edits an ISO;
- writes `NA2_APPLY__TRANSLATION__*.zip` to Downloads;
- includes only `PRG/BTL.BIN` and `PRG/ETC.BIN`.

Run from the project:

```powershell
& '.\translation_package_builder\build_na2_translation_package.ps1'
```

Then test with the project's existing translation-package command:

```powershell
na2 tr
```
