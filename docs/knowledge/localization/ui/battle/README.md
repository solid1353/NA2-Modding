# Battle UI draw-path mappings

This record preserves the paired NA2/NUN5 battle-overlay findings used by the
texture-only UI correction pass. It covers executable layout and atlas-selection
behavior; command-name text, font metrics, and gameplay input semantics are
outside this boundary.

The common binary identities and address convention remain here. Focused
findings are split by draw-path family so agents can load only the relevant
evidence.

## Documents

- [Selectors and prompts](selectors_and_prompts.md): awakening labels,
  VS Jutsu selection, confirmation prompts, and scroll indicators.
- [Item status](item_status.md): paired, numeric, single, fixed, and
  substitution-doll item-status paths.
- [Settings and results](settings_and_results.md): Mash prompts,
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
`@disassembly/NA2/exports/BTL.BIN/` and
`@disassembly/NUN5/exports/BTL.BIN/`. Those projects omit the
40-byte BTL file header when mapping code, so a Ghidra address is the archived
live address minus `0x40`. File offsets below always refer to the complete
source file. For the boot ELFs, the relevant `PT_LOAD` mappings place NA2 file
offset `0x100` and NUN5 file offset `0x180` at runtime `0x00100000`.

Direct MIPS call targets and absolute data operands remain runtime addresses.
Resolve those operands to a complete BTL file offset by subtracting the
archived live base directly; do not apply the Ghidra project's header shift a
second time. For example, NA2 runtime operand `0x008C42D8` maps to file offset
`0x2103D8`, not `0x210418`.

## Battle HUD character-name anchor

The `characters/idle` E2E baseline contains 74 populated character cells. In
every cell, NA2 v2.28 placed the Player 1 name exactly 20 output pixels to the
right of NUN5 and the Player 2 name exactly 20 output pixels to the left. At the
640-pixel capture width, that symmetric error corresponds to 16 units in the
game's 512-unit logical coordinate system, identifying a shared mirrored anchor
rather than character-specific data or font metrics.

NA2 renders these names through the function at BTL file offset `0x67F20`,
runtime `0x0071BE20`, which the header-omitting Ghidra project labels
`FUN_0071bde0`. The NUN5 homolog is at file offset `0x6B0C0`, runtime
`0x00731DC0`, and Ghidra label `FUN_00731d80`. The renderer applies its X
anchor as:

```text
left:  x = base_x + local_x
right: x = base_x - local_x - rendered_width
```

The native X load is the isolated `lui/lwc1` pair at complete BTL file range
`0x67F54..0x67F5B`, clean bytes `8C00023CD84240C4`. It reads runtime address
`0x008C42D8`, BTL file offset `0x2103D8`, whose value is `90.0`. NUN5 reads
runtime `0x008DC8F8`, file offset `0x215BF8`, whose value is `74.0`. When the
substitution gauge is selected, the current uncommitted candidate replaces that
pair with a guarded `jal; nop` to
`substitution_gauge_battle_hud_character_name_x_shim`. The shim preserves the
renderer's live `v1` destination pointer, calls the C coordinate getter, and
returns its readable decimal `BATTLE_HUD_CHARACTER_NAME_X` value in `f0` to the
unchanged native scale multiplication.
This moves the left name 16 logical units left and the mirrored right name 16
units right while leaving character data and font metrics unchanged. The
offset and direction are screenshot-proven across the full existing suite;
runtime confirmation of the injected storage path remains pending.

The independent 160-unit name-width cap remains part of the same renderer and
continues to belong to the Localization runtime injection. Its resident
`PRG/228.BIN` entries are `localization_ui_battle_hud_fit_width` and
`localization_ui_battle_hud_fit_width_adapter`. A guarded call hook at BTL file
offset `0x67F44` replaces the native width multiplication and preserves the
accepted `a0=160` delay-slot side effect. The adapter preserves the caller-live
`a1`, `v1`, `f1`, and `ra`, calls C to compute
`min(source_width, 160.0f) * scale`, returns the result in native `f5`, and
executes the displaced height load in its return delay slot. The former BTL
header-cave helper is no longer used. The width hook ends at `0x67F4B`; the X
anchor hook begins at `0x67F54`, so the two guarded ranges do not overlap.

The immediately following native Y pair at `0x67F60..0x67F67`, clean bytes
`8C00023CDC4240C4`, is owned by the same substitution-gauge feature. When
selected, that injection returns the readable decimal
`BATTLE_HUD_CHARACTER_NAME_Y` (`55.0`) compiled from the same C file through the
same pointer-preserving shim pattern. The gauge therefore owns both character-name coordinates; when
it is disabled, neither coordinate hook is selected and the native anchors
remain in use. Localization owns only name width fitting and atlas content.

The supplied `ss1` from build CRC `0CAE98A3` established why direct calls to the
C getters were invalid at these two inline hooks: the native renderer loads its
name destination into `v1` before both coordinate loads and stores X/Y through
that pointer afterward, while the C display-state lookup uses `v1` as a
temporary. Preserving `v1` in the two ABI shims restores both names.

The behavior and screenshot evidence above apply to the integrated NA228
result. This resident-storage refactor is uncommitted and has only static
validation: the compiled C body, ABI adapter, guard, and production
payload/hook resolution passed their focused contracts and catalog tests. No
runtime or E2E run has validated the refactored storage path; that validation
remains user-only.
