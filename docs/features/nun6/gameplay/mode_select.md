# NUN6 Mode Select reference

NUN6 removes entries from the Mode Select carousel by storing the signed
sentinel `-1` in its seven-entry mode table. The menu setup loop skips negative
entries.

Its table uses the NUN5 virtual address `0x005DC300` and ELF offset
`0x4DC480`, with values `(-1, 2, 3, -1, -1, -1, 7)`. Entry 0 supplies the
comparative behavior used by NA228's
[Remove Adventure feature](../../mode_select.md#remove-adventure-mode).
NUN6's changes to entries 4 and 5 are unrelated and are not ported.
