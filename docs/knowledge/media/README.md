# NA2 Media Layout Inventories

These exact inventories were promoted from the 2026-07-03/04 extraction logs so the game-media structure can be searched without repeating ISO, encrypted-CVM, or nested-AFS extraction.

| Durable file | Contents | Entries |
| --- | --- | ---: |
| `na2_iso9660.tsv` | Outer `@source/NA2.iso` ISO9660 layout: path, object type, extent, byte offset, and size | 36: 32 files, 4 directories |
| `data_cvm_iso9660.tsv` | Decrypted ISO payload layout from `@source/NA2.iso.files/DATA/DATA.CVM` | 2,332: 2,312 files, 20 directories |
| `afs_members.tsv` | Consolidated nested AFS-member layout under `@source/NA2.iso.files` | 9,480 members across 170 AFS containers |

The TSV files are exact copies of the original inventories. Backslash paths inside them are historical extraction-relative paths:

- paths in `na2_iso9660.tsv` are relative to the root of `@source/NA2.iso`;
- paths in `data_cvm_iso9660.tsv` are relative to the decrypted ISO payload of `DATA.CVM`;
- paths in `afs_members.tsv` begin with `NA2.iso.files` and are relative to `@source/`.

`DATA.CVM` was split with the project password, yielding a 737,226,752-byte ISO payload with 359,974 sectors and end-of-TOC sector 87. These values came from the associated split summary; the full layout is `data_cvm_iso9660.tsv`.

The 2026-07-04 extraction pass completed all four top-level and 166 nested AFS archives, leaving no discovered AFS without a sibling `.files` extraction. Its final source-tree inventory contained 12,195 items and found no item missing the Windows read-only attribute at that time. These are dated completion facts, not a substitute for rechecking attributes after future source changes.

The inventories describe untouched source extractions. They are reference data, not permission to modify `@source/`. Regenerate them only if the source media or extraction interpretation changes, and compare the new result before replacing a durable inventory.
