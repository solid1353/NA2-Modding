# Mode availability

## Remove Adventure mode

The menu setup loop skips entries whose table value is negative, so storing the
signed sentinel `-1` omits an item rather than displaying and blocking it after
selection. The comparative implementation is documented in
[NUN6 Mode Select](../nun6/gameplay/mode_select.md).

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

## Result-table edit constraints

These follow from the retail
[Mode Select result table](../../knowledge/game/mode_flow.md#mode-select-result-table)
and [manager callback dispatch](../../knowledge/game/mode_flow.md#high-level-mode-callback-dispatcher):

- The compact array has capacity for all seven physical slots. Changing a
  negative table entry to a nonnegative value automatically admits that slot;
  no separate active-count constant needs changing.
- The filter validates only the sign. A nonnegative value that is not handled
  by the manager callback switch passes Mode Select confirmation and becomes
  manager `+0x0C`, after which manager phase 4 has no default recovery and
  stalls.
- Changing a table result remaps the callback but does not change the physical
  carousel order or remembered-slot behavior. `0x006045E0` continues to store
  the physical slot rather than the remapped mode ID.
- An all-negative table is not a supported empty-menu encoding: construction
  has no empty-list guard and reads an unwritten compact entry. A deliberately
  empty menu therefore needs code changes, not only seven negative table
  values.
