# UI Translation context

Consolidated on 2026-08-01 from the former workstream plan and completed
Remaining UI work. This document is a concise status and architecture overview;
it does not select work or grant execution authority. Exact offsets, functions,
donor ranges, negative results, and per-screen evidence live in the linked
knowledge documents.

## Objective

Import appropriate official NUN5 English UI artwork into NA2, preserve NA2's
fixed media layout, and port the placement, selection, ordering, visibility,
and animation data needed for the imported artwork to render like NUN5.

Text content and font rendering, fitting, measurement, and spacing remain
outside this workstream.

## Current state

- The declared Remaining UI work is complete.
- No UI comparison case is awaiting approval.
- All cases listed under [Accepted outcomes](#accepted-outcomes)
  were explicitly accepted by the user.

## Canonical assets and tools

### Sources and donors

- `@source_na2/`: unpacked NA2 target files.
- `@source_nun5/`: unpacked official NUN5 English donor files.
- `@source_nun6/`: unpacked NUN6 A35 reference files. Its Brazilian Portuguese
  texture and text changes are useful for identifying localization-bearing
  assets and confirming layout changes, but it is not the English authority.
- `@analysis/disassembly/NA2/exports/SLPS_258.37/` and
  `@analysis/disassembly/NUN5/exports/SLES_556.05/`: existing searchable boot
  ELF exports.
- `@analysis/disassembly/NA2/exports/ETC.BIN/` and
  `@analysis/disassembly/NUN5/exports/ETC.BIN/`: existing Collection-overlay
  exports. Reuse them instead of creating redundant disassemblies.

### Texture references

- The unpacked NUN5 PCSX2 upscale pack under `@source/__upscaled/` contains
  8,217 hash-named DDS replacements. It is useful for visual identification
  and emulator comparison, not as a direct CCS asset tree.
- The redundant packed RAR was deleted after the unpacked pack was verified
  complete.
- The former stripped NUN5 DATA.CVM tree was proven byte-equivalent to the
  official donor extraction and deleted after its useful workflow evidence was
  documented.

### CCS tooling

- `@tools/CCSFileExplorerMSF` is the primary CCS explorer. It opens gzip-wrapped
  CCS files, displays named textures and separate TEX/CLT blocks, and can
  extract textures.
- Preview and extraction are demonstrated; safe reimport and rebuilding through
  the GUI are not. Production changes use deterministic project patchers.
- Older StudioCCS and CCSFileExplorerWV sources remain format references, not
  trusted production writers.

## Architecture and implementation overview

- Official NUN5 assets are the authoritative English donor.
- Compatible CCS members derive complete NUN5 payloads while preserving NA2's
  fixed member capacities. Whole-container imports keep artwork, models,
  palettes, and UVs coupled when partial import is unsafe.
- Mapped exceptions retain only the NA2 structure required by capacity or ABI
  constraints and still derive suitable pixels, palettes, or data from NUN5.
- Narrow authored patches exist only where NUN5 code cannot be copied directly
  into the NA2 ABI or where NA2 intentionally requires different behavior.
- Shared executable tables replace repeated per-screen or per-character guesses
  when several renderers consume the same atlas.
- Renderer-specific footer and prompt anchors remain separate when the games
  use different call paths; there is no assumed universal footer table.
- Animation and visibility ports preserve existing NA2 state machines unless
  NUN5 evidence proves a localized behavior difference.
- No replacement CCS blobs are stored. The profile derives replacements from
  canonical inputs, validates source identities, reparses output, checks visual
  coverage, and verifies fixed capacities.

Exact implementation mechanics and evidence are organized by screen family in
the linked knowledge documents.

## Runtime comparison

- Compare official NUN5 on the left with Current NA2.28 on the right. Vanilla
  NA2 is an optional diagnostic fallback, not a routine third capture.
- Normal pulsing differences are capture-phase noise. Semantic mismatch,
  clipping, wrong artwork, ordering, visibility, animation, and placement are
  UI defects.
- Runtime comparisons use exact integrated-build captures. Runtime-injected
  candidates remain explicitly labeled candidates until reproduced through the
  normal integrated pipeline.
- Savestate pairs and worker media live only under `work/UI translation/` while
  active. Accepted-case captures, states, worker ISOs, probes, logs, and PCSX2
  copies are removed after reusable findings are promoted.

## Accepted outcomes

- Stage Select layout, stage association, thumbnails, labels, Random prompt,
  and footer.
- Mode Select START artwork and OK/Back footer.
- Options and Settings footers, including Music Settings and Control Settings.
- Collection root, Characters, Movie, Music, character-viewer controls, page
  prompts, Play/Stop, and common prompts.
- Character Select names, Select Color/Random placement, and footer.
- Jutsu Selection arrows and confirmation-screen texture behavior.
- Command Menu and Command Chart vertical arrows.
- Controls Vibration artwork.
- Cross/Triangle prompt batch across the preserved original and newer screen
  pairs.
- Character Items five-phase transition behavior.
- Mash Prompt.
- Victory winner names across the complete character set.
- Ninja Song details footer.
- Battle Results screen 2 labels, title, moving clouds, footer, and all five
  rank stamps.
- Battle item substitution doll in slot 4.

The explicit acceptance dates were:

- 2026-07-26: Cross/Triangle labels, Character Items, Victory winner names,
  Ninja Song footer, and Battle Results screen 2.
- 2026-07-27: Collection Music Stop group and footer anchor; Cross/Play already
  matched.
- 2026-07-31: Battle item substitution doll.

## Deferred work

Optional future research remains for `LOGO.CCS`, mapping the NUN5 upscale pack
back to disc assets, and broader NUN6 comparison.

## Retired artifacts

- Deleted the redundant upscale archive and stripped NUN5 tree after verifying
  their retained counterparts.
- Removed the formerly tracked derived CCS blobs after exact source-derivation
  parity was established; Git history remains the recovery path.
- Removed superseded manual comparison artifacts and their task-owned runtime
  evidence after user verification and promotion of reusable findings;
  maintained screenshot comparison now belongs to E2E tests.

## Detailed knowledge

- [Battle UI](../../knowledge/localization/ui/battle/README.md)
- [Character Select UI](../../knowledge/localization/ui/character_select.md)
- [Collection UI](../../knowledge/localization/ui/collection.md)
- [Options UI](../../knowledge/localization/ui/options.md)
- [Stage Select UI](../../knowledge/localization/ui/stage_select.md)
- [Victory UI](../../knowledge/localization/ui/victory.md)
