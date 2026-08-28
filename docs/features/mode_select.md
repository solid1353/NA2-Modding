# Mode Select

## Remove Adventure mode

NUN6 removes Adventure from the Mode Select carousel by storing the signed
sentinel `-1` in entry 0 of the boot ELF's seven-entry mode table. The menu setup
loop skips entries whose table value is negative, so the item is omitted rather
than displayed and blocked after selection.

The corresponding tables are:

- NA2: virtual address `0x005D51D0`, ELF offset `0x4D52D0`, values
  `(4, 2, 3, -1, 5, 6, 7)`.
- NUN5: virtual address `0x005DC300`, ELF offset `0x4DC480`, values
  `(4, 2, 3, -1, 5, 6, 7)`.
- NUN6: the NUN5 address and offset, values
  `(-1, 2, 3, -1, -1, -1, 7)`.

The Remove Adventure patch changes only NA2 entry 0 from `04 00 00 00` to
`FF FF FF FF`.
NUN6's changes to entries 4 and 5 are unrelated and are intentionally not
ported. NUN5 is not a suitable byte donor because its entry 0 matches NA2; the
raw replacement is used because the desired behavior deliberately follows the
NUN6 variant. The source ELF remains untouched and the output size is preserved.

Runtime testing of the integrated Current ISO confirmed that Adventure is absent
and the remaining Mode Select entries work normally. The setting is therefore
enabled in the release configuration; its runtime proof is retained in documentation.
