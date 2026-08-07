# Battle UI draw-path mappings

This record preserves the paired NA2/NUN5 battle-overlay findings used by the
texture-only UI correction pass. It covers executable layout and atlas-selection
behavior; command-name text, font metrics, and gameplay input semantics are
outside this boundary.

The common binary identities and address convention remain here. Focused
findings are split by draw-path family so agents can load only the relevant
evidence.

## Documents

- [Selectors and prompts](battle/selectors_and_prompts.md): awakening labels,
  VS Jutsu selection, confirmation prompts, and scroll indicators.
- [Item status](battle/item_status.md): paired, numeric, single, fixed, and
  substitution-doll item-status paths.
- [Settings and results](battle/settings_and_results.md): Mash prompts,
  Settings footers, and Battle Results/rank rendering.

## Intentional exclusion

The Ultimate Jutsu interface prompts are intentionally not fixed. The complete
Ultimate Jutsu interface is planned for exclusion as part of the QoL work, so
localizing those prompts separately would be superseded by that change.

## Binary identities and address convention

| Game | Binary | Size | SHA-256 | Archived live base |
| --- | --- | ---: | --- | ---: |
| NA2 v2.28 | `@source/NA2.iso.files/PRG/BTL.BIN` | 2,237,184 | `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` | `0x006B3F00` |
| NUN5 SLES-55605 | `@source/NUN5.iso.files/PRG/BTL.BIN` | 2,253,184 | `7E8518DA7BD4957AF18CB0ABABE67F0E9B37C42C6551375201B15997F0A3DFE3` | `0x006C6D00` |
| NA2 v2.28 | `@source/NA2.iso.files/SLPS_258.37` | 5,273,256 | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` | `0x00100000` |
| NUN5 SLES-55605 | `@source/NUN5.iso.files/SLES_556.05` | 5,340,912 | `20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D` | `0x00100000` |

The focused exports are under
`@analysis/disassembly/NA2/exports/BTL.BIN/` and
`@analysis/disassembly/NUN5/exports/BTL.BIN/`. Those projects omit the
40-byte BTL file header when mapping code, so a Ghidra address is the archived
live address minus `0x40`. File offsets below always refer to the complete
source file. For the boot ELFs, the relevant `PT_LOAD` mappings place NA2 file
offset `0x100` and NUN5 file offset `0x180` at runtime `0x00100000`.
