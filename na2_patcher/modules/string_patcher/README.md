# String patcher

This module owns fixed-size replacements for embedded NA2 strings that do not
belong to the official NUN5-backed translation mapping module. Its sole
executable input is `strings.tsv`, which declares text-oriented fields such as
encoding, storage mode, expected text, replacement text, byte capacity, and
target location. The module validates and encodes those declarations, then
compiles an in-memory binary-patcher package. Profile composition delegates all
selection, byte guards, conflict handling, replacement, and logging behavior to
`na2_patcher.modules.binary_patcher.engine`. No binary-patcher tables or
duplicate patch engine are stored here.

## `ELF-S001` — Game title

The clean NA2 boot ELF stores its memory-card title at file offset `0x2FBAE0` in
a 64-byte CP932 slot beside the `BISLPS-25837NARUTO5`, `icon00.icn`, and
`icon.sys` metadata.

`ELF-S001` replaces the original title with the full-width CP932 string
`ＮＡ　ｖ２．２８`. Its 16 encoded bytes are followed by a NUL terminator and 47
zero-padding bytes through the end of the original slot. The edit preserves the
ELF size and is guarded by the exact 64 original bytes.

The full-width form follows the official NUN5 memory-card title convention. A
half-width ASCII test was copied into a newly created save correctly but rendered
as a blank title in the USA PS2 BIOS. A longer full-width
`Ｎａｒｕｔｉｍａｔｅ　Ａｃｃｅｌ　ｖ２．２８` test rendered successfully but wrapped at an
unattractive position, so the final title uses the shorter form above.

Status is `approved_for_test` until the resulting title is verified in the PS2
memory-card browser.
