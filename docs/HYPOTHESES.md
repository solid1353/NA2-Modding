# Hypotheses Archive

Use this file for old patch candidates, failed experiments, unverified addresses, and leads that should not clutter active PNACH/build files.

## GF4 Font Rendering Handoff

Status: paused after v23. Confirmed observations, the exact patch record, and the final comparison screenshot are preserved in `docs/knowledge/font/README.md`; canonical accepted and historical patch data remain under `na2_patcher/modules/raw_binary/patch_sets/`. Review those records and the preserved disassembly before proposing another experiment.

The unresolved work remains at least three separate problems: glyph appearance, positioning/advance behavior, and missing NUN5-style auto-fit/squish for text that exceeds a box.

### Disassembly leads

- Reuse the preserved projects/exports under `@source/NA2_disassembly` and `@source/NUN5_disassembly`; do not disassemble either ELF from scratch.
- NA2 ASCII setup lead: `FUN_00186510`.
- NUN5 counterpart: `FUN_001878e0`.
- NUN5 boxed auto-fit leads: `FUN_00389df0` and `FUN_0018b1b0`.
- NA2 menu lead: `FUN_003885b0`, which calls `FUN_00379240` and appears to center/draw without the corresponding 128-pixel auto-fit path.
- A full NUN5 text-renderer transplant is unsafe. Continue with small, proven renderer-logic comparisons and script-generated patches only.

## Legacy 2022 Scratch Notes

Status: unverified historical leads. The exact `old/` artifacts are preserved in
Git commit `a3e5c23`; they were removed from the working tree after a shallow
2026-07-17 audit. Treat the gameplay names and address interpretations below as
hypotheses unless current module data or a new test proves them.

### Artifact disposition

- `ADV.BIN` and `ETC.BIN` were byte-identical to the clean NA2 source copies.
- The changes in `BTL.BIN` were confined to the battle-menu text block around
  file offset `0x208A30`. Current translation mappings supersede its fullwidth
  text and `Placeholder` values.
- `Battle options 208A30.bin` was a mixed draft with placeholders and swapped
  navigation labels, not a canonical extraction or patch input.
- `SLPS_258.37` was an experimental scratch ELF containing legacy instruction
  edits, coherent NUN5-derived text, and literal test strings such as
  `asdfasdfasdf`. Do not use it as a build input or translation source.

### Gameplay leads

- Substitution-cost candidate at EE `0x202298BC` / ELF file `0x1299BC`:
  historical notes record `0x4040` as 3/15 and `0x40A0` as 5/15. The current
  patch set already preserves the 3/15 form as disabled `ELF-S001`; the 5/15
  form has not been revalidated.
- Historical one-branch candidates exist at EE `0x20241F40` (labelled
  "extra hit") and `0x202457C8` (labelled "RPS"). Their instruction changes
  are preserved in Git history, but the gameplay labels and runtime effects
  should not be assumed. Current battle-logic patches supersede the latter.
- Jutsu-name-display idea near EE `0x001F64A4`: an old note proposes forcing
  part or all of `v0` to zero in a branch delay slot. The intended bit/byte and
  the screen behavior are unspecified; do not patch it without fresh analysis.
- Ultimate-Jutsu chakra notes point to file `0x1492B0` for level-scaled
  subtraction and `FUN_002254a0` for shared chakra addition. These are leads,
  not retained conclusions; recheck the preserved disassembly before use.

### Localization and asset leads

- Possible unmapped item/equipment strings occupy ELF file range
  `0x4B01E0-0x4B04D0`. The old ELF overwrote them with test text, so recover
  only from clean NA2 and official NUN5 sources.
- Dialogue targets `0x2FFD40`, `0x2FFD58`, `0x2FFD80`, `0x2FFDB0`, and
  `0x2FFDC0` matched official NUN5 dialogue during the audit but are not current
  mapping rows.
- Controller/help targets near `0x4B1E30`, `0x4B24E0`, `0x4B2580`, and
  `0x4B25D0` have apparent NUN5 counterparts. Their visibility and reachability
  are untested.
- A character CCS filename table appears to begin at file `0x301D48`.
- `0x494EFC` and `0x49AF8C` were labelled as possible Sai-lion and
  Sasuke-Chidori data. Those identities remain unproven.

The remaining contextless constants, vague table addresses, obsolete absolute
CVM commands, and the claimed alphabet at `0x2FB840` were not retained as
actionable leads.
