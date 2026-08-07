# Source extraction runbook

This runbook owns the canonical extraction layout and procedures for original
source media. Source protection remains canonical in
[`../policies/modding.md`](../policies/modding.md).

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

Do not edit anything in `@source/` in place. Copy a required file/archive to the
owning task/build tree before patching it. Shared generated inventories use
configured work/log roots and source-relative paths, never the source tree.

## Canonical ISO extraction

Use:

```powershell
scripts/project/extract_source_iso.ps1 `
  -IsoPath <path> `
  -TaskTitle <exact task title>
```

The command stages under
`work/<task>/temp/source_extraction/`, recursively expands CVM, inner ISO, AFS,
and nested AFS containers, verifies file sets/bytes, normalizes timestamps, and
promotes one complete `<ISO filename>.files` tree. It refuses to merge into an
existing extraction.

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
- NUN6 A35: `Iruka`

Use `@media_scripts/split_cvm_rofs.ps1` to split encrypted CVM safely. Do not use
the historical `@tools/old/CVM Parser/cvm_tool.exe` workflow.
