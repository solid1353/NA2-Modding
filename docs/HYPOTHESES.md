# Hypotheses Archive

Use this file for old patch candidates, failed experiments, unverified addresses, and leads that should not clutter active PNACH/build files.

## GF4 Font Rendering Handoff

Status: resolved for the reviewed screens on 2026-07-19. Confirmed behavior,
matched measurements, exact patch records, and negative results are preserved
in `docs/knowledge/font/README.md`; canonical accepted and historical patch
data remain under `na2_patcher/modules/raw_binary/patch_sets/`.

The accepted integration baseline uses a guarded native 14x20 NUN5-derived
secondary atlas in GF4 while keeping clean NA2 GF4C. Controls overflow uses a
local shrink-only helper, and the reviewed Controls and character-modal
placement is corrected locally. Halfwidth Latin glyphs remain visibly bolder
than NUN5 and are explicitly deferred to the next refinement iteration;
fullwidth Shift-JIS Save/Load digits are not a Latin-weight target. The old
v22/v23, palette, descriptor-height, 10x22, global-parser, and threshold-only
experiments remain negative evidence, not active candidates. Future work must
start from the accepted native package and prove any change against matched
captures before changing its established layout.

### Disassembly leads

- Reuse any applicable historical project/export evidence from Git history and
  maintain current projects under `@analysis/disassembly/NA2/` and
  `@analysis/disassembly/NUN5/`; never place analysis work under `@source/`.
- NA2 ASCII setup lead: `FUN_00186510`.
- NUN5 counterpart: `FUN_001878e0`.
- NUN5 boxed auto-fit reference: `FUN_00389df0` and `FUN_0018b1b0`.
- NA2 Controls path: `FUN_003885b0`, with the first eight calls locally fitted
  before the original `FUN_00379240` draw and the ninth call left ordinary.
- A full NUN5 text-renderer transplant remains unsafe. Any future work must use
  small, call-local, script-generated patches.

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

## External Translation Files

Status: generated module implemented; ISO/runtime validation pending. Confirmed
layout, loader, donor, and ISO findings are recorded in
`docs/knowledge/external_translation_files.md`; the canonical pointer inventory
is `na2_patcher/modules/external_translation/pointer_refs.tsv`.

- Generated boot hook: redirect the call at runtime `0x001E0F20` in
  `FUN_001e0ee0` through a resident stub, then load `MOD.BIN`, invoke its fixed
  bootstrap, and resume the original `FUN_001bda50` call. Exact instruction
  words are unit-tested; this control-flow sequence has not been run.
- Candidate resident cave: ELF file `0x00507414-0x0050747F` / runtime
  `0x00607314-0x0060737F` is zero-filled and has no aligned exact pointer found
  in SLPS, BTL, or ETC. Absence of a pointer is not proof that the range is safe.
- Candidate memory envelope: reserve `TEXTENG.BIN` at `0x008F3D00`,
  `MOD.BIN` at `0x00940000`, and move the final marker only to `0x00940100`.
  NA2 runtime stability after reducing the heap by `0x63080` bytes is unknown.
- Candidate FLIST behavior: the direct PRG loader appears able to open both
  explicit paths without FLIST registration. NUN6 lists `MOD.BIN` but not its
  text file, so an NA2 proof of concept should test omission rather than treat
  it as confirmed.
- The exact R5900 assembler/toolchain and MOD bootstrap ABI remain to be chosen
  and verified. Loading an MWO3 file must not be assumed to invoke an arbitrary
  entry unless its header constructor range or an explicit post-load call is
  deliberately implemented.
