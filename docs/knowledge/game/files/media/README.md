# NA2 Media Layout Inventories

These exact inventories preserve the game-media structure without requiring repeated ISO, encrypted-CVM, or nested-AFS extraction.

For a human-readable explanation of what the files and major nested families
do, use [`../disc_files.md`](../disc_files.md). This directory remains the
canonical exact structural inventory rather than duplicating semantic notes.

## Research coverage

- **Assigned scope:** Exact ISO9660, decrypted DATA.CVM, and nested AFS layout
  inventories for the untouched NA2 source extraction.
- **Exploration depth:** The inventories cover the complete outer ISO layout,
  decrypted DATA.CVM payload, and all four top-level plus 166 nested AFS
  archives discovered by the extraction.
- **Confirmed coverage:** The recorded paths, object types, extents, offsets,
  sizes, entry totals, DATA.CVM sector totals, and absence of an unextracted
  discovered AFS are established by the listed inventories and split summary.
- **Unresolved or untested:** The inventories do not determine the semantic
  purpose of individual files or archive members.
- **Deliberate exclusions and overlap:** Human-readable file and family roles
  belong to [NA2 Game File Reference](../disc_files.md); this directory owns
  only the exact structural data.
- **Evidence limitations:** The paths retain historical extraction-relative
  prefixes, and the DATA.CVM size and sector summary is reported from the
  associated split result rather than duplicated as another inventory.

| Durable file | Contents | Entries |
| --- | --- | ---: |
| `na2_iso9660.tsv` | Outer `na2_iso` project-file ISO9660 layout: path, object type, extent, byte offset, and size | 36: 32 files, 4 directories |
| `data_cvm_iso9660.tsv` | Decrypted ISO payload layout from `@source_na2/DATA/DATA.CVM` | 2,332: 2,312 files, 20 directories |
| `afs_members.tsv` | Consolidated nested AFS-member layout under `@source_na2` | 9,480 members across 170 AFS containers |

The TSV files are exact copies of the original inventories. Backslash paths inside them are historical extraction-relative paths:

- paths in `na2_iso9660.tsv` are relative to the root of project file `na2_iso`;
- paths in `data_cvm_iso9660.tsv` are relative to the decrypted ISO payload of `DATA.CVM`;
- paths in `afs_members.tsv` begin with `NA2.iso.files` and are relative to `@source/`.

`DATA.CVM` was split with the project password, yielding a 737,226,752-byte ISO payload with 359,974 sectors and end-of-TOC sector 87. These values came from the associated split summary; the full layout is `data_cvm_iso9660.tsv`.

The extraction covered all four top-level and 166 nested AFS archives, leaving no discovered AFS without a sibling `.files` extraction. Its source-tree inventory contained 12,195 items and found no item missing the Windows read-only attribute. This does not replace checking attributes after source changes.

The inventories describe untouched source extractions. They are reference data, not permission to modify `@source/`. Regenerate them only if the source media or extraction interpretation changes, and compare the new result before replacing a durable inventory.
