# Mode Select

## Remove Adventure mode

The menu setup loop skips entries whose table value is negative, so storing the
signed sentinel `-1` omits an item rather than displaying and blocking it after
selection. The comparative implementation is documented in
[NUN6 Mode Select](nun6/gameplay/mode_select.md).

The corresponding tables are:

- NA2: virtual address `0x005D51D0`, ELF offset `0x4D52D0`, values
  `(4, 2, 3, -1, 5, 6, 7)`.
- NUN5: virtual address `0x005DC300`, ELF offset `0x4DC480`, values
  `(4, 2, 3, -1, 5, 6, 7)`.

The Remove Adventure patch changes only NA2 entry 0 from `04 00 00 00` to
`FF FF FF FF`.
NUN5 is not a suitable byte donor because its entry 0 matches NA2. The source
ELF remains untouched and the output size is preserved.

Runtime testing of the integrated Current ISO confirmed that Adventure is absent
and the remaining Mode Select entries work normally. The setting is therefore
enabled in the release configuration; its runtime proof is retained in documentation.
