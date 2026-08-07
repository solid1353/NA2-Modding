# Legacy 2022 localization artifact audit

The exact removed `old/` artifacts remain recoverable from Git commit
`a3e5c23`. A shallow 2026-07-17 audit established the following durable
conclusions; none of these files is a canonical build or translation input.

- `ADV.BIN` and `ETC.BIN` were byte-identical to the clean NA2 source copies.
- `BTL.BIN` changes were confined to the battle-menu text block around file
  offset `0x208A30`. Current translation mappings supersede its fullwidth text
  and `Placeholder` values.
- `Battle options 208A30.bin` was a mixed draft with placeholders and swapped
  navigation labels, not a canonical extraction or patch input.
- `SLPS_258.37` was an experimental scratch ELF containing legacy instruction
  edits, coherent NUN5-derived text, and literal test strings such as
  `asdfasdfasdf`. Do not use it as a build input or translation source.

Translation mapping v36 also removed 57 contextless battle offsets and one
obsolete legacy dialog fragment from the executable mapping table. Git history
retains them, but none had a verified official source or generated a patch.
