# Source extraction runbook

This runbook owns the canonical extraction layout and procedures for original
source media. Source protection remains canonical in
[`repository.md`](../policies/repository.md#file-and-folder-management).

## Layout

Keep original archives under `@source/`. Extract each archive beside itself into
`<archive filename>.files`, repeating the convention for nested archives:

```text
<game>.iso
<game>.iso.files/
  DATA/DATA.CVM
  DATA/DATA.CVM.files/
    DATA.CVM.iso
    DATA.CVM.iso.files/
  DATA/SOUND.AFS
  DATA/SOUND.AFS.files/
```

Shared generated inventories use configured work/log roots and source-relative
paths, never the source tree.

## Canonical ISO extraction

Resolve the
[current exact chat title](../policies/work_directories.md)
and use:

```powershell
scripts/project/extract_source_iso.ps1 `
  -IsoPath <path> `
  -TaskTitle <exact chat title>
```

The command stages under `temp/source_extraction/` in the
[acting task's work root](../policies/work_directories.md),
recursively expands CVM, inner ISO, AFS, and nested AFS containers, verifies file
sets/bytes, normalizes timestamps, and promotes one complete
`<ISO filename>.files` tree. It refuses to merge into an existing extraction.

Recheck an existing tree with:

```powershell
& .\scripts\lib\run_python.ps1 `
  -PackageSet builder `
  -Script scripts/project/verify_source_extraction.py `
  -NoBytecode `
  -ArgumentList @(
    '--iso', '<original-iso>',
    '--out-dir', '<extraction-tree>'
  )
```

Add `--require-read-only` to `-ArgumentList` when verifying the protected active
source ISO and extraction tree.

Restore Windows read-only attributes for one explicit active ISO extraction
with:

```powershell
scripts/project/set_source_readonly.ps1 -SourceDir <tree>
```

The command refuses the whole source root and `@source/__old/`.

## DATA.CVM

Confirmed ROFS/CVM passwords:

- NA2, NUN3, NUN5: `cc2fuku`

Reference-mod source details are documented with their owning feature; see the
[NUN6 source identity](../features/nun6/source.md#source-identity).

Use `@media_scripts/split_cvm_rofs.ps1` to split encrypted CVM safely. Do not use
the historical `@tools/old/CVM Parser/cvm_tool.exe` workflow.
