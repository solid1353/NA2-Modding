# UI Translation context

Consolidated on 2026-08-01 from the former workstream plan and the completed
Remaining UI epic. This document contains durable execution context and accepted
results. Exact reverse-engineering evidence remains in the linked knowledge
documents.

## Objective

Import appropriate official NUN5 English UI artwork into NA2, preserve NA2's
fixed media layout, and port the placement, selection, ordering, visibility,
and animation data needed for the imported artwork to render like NUN5.

Text content and font rendering, fitting, measurement, and spacing remain
outside this workstream.

## Current state

- The declared Remaining UI epic is complete.
- No UI comparison grid or savestate case is awaiting approval.
- All cases listed under [Accepted runtime results](#accepted-runtime-results)
  were explicitly accepted by the user.
- The current `TASKS.md` Bugs list contains `UI Translation: long character
  names.` This is context only and is not selected or authorized work.
- Optional future research remains possible for `LOGO.CCS`, mapping the NUN5
  upscale pack back to disc assets, and broader NUN6 comparison.

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

## Donor-first implementation

- Official unsuffixed NUN5 assets are the authoritative English donor.
- Normal compatible CCS members use complete deterministic NUN5 payloads,
  recompressed into the unchanged NA2 member capacity. Padding follows the
  valid gzip stream; DATA.CVM member sizes, ISO records, and source files stay
  unchanged.
- No replacement CCS blobs are stored. The normal profile derives replacements
  directly from canonical NA2 and NUN5 inputs.
- `MODE2KDV`, ENDDEMO, Haku, and Shikamaru are mapped exceptions where complete
  donor replacement is unsuitable or cannot fit. Their adaptations still use
  canonical donor pixels or palettes and preserve required NA2 structure.
- `HOME.CCS` is a complete NUN5 donor. Earlier mapped texture-only import kept
  incompatible NA2 models and UVs and caused duplicated or clipped Collection
  artwork.
- `CMN/GAUGE.CCS` is imported as a complete unit so global button legends,
  models, and UVs remain coupled.
- `OUGI.CCS` uses NUN5's four wide labels. The companion BTL patch changes the
  NA2 construction loop at file offset `0xB5E80` from two parts to one because
  no exact donor instruction exists at an equivalent NA2 location.
- `MODE2KDV` retains the NA2 container, portrait, palette, and lower rows while
  mapping the NUN5 banner into the fixed target capacity.
- The texture patcher validates source identities, reparses decompressed output,
  checks intentional visual coverage, and verifies fixed capacities.
- Binary-patcher companions use exact NUN5 ranges where compatible and narrow
  NA2-ABI adaptations only where the donor code cannot be copied directly.

## Important layout ports

- Character Select names use a 96-record boot-ELF rectangle table. The complete
  NUN5 table is copied rather than applying per-character guesses.
- Stage Select uses all 24 official NUN5 stage rectangles and the NUN5
  horizontal `min(1, 214 / width)` fit. Vertical scale remains `1.0`; preview
  and thumbnail consumers preserve the matched stage index.
- Options uses the complete guarded NUN5 menu/difficulty rectangle block from
  the boot ELF; screen positions and scale otherwise match.
- Collection submenu layout uses exact NUN5 ETC position and rectangle blocks
  for page prompts, Characters/Movie/Music titles, Play/Stop, and the
  character-viewer controls. Font wrapping and string content are separate.
- Jutsu Selection suppresses the two closed-state horizontal-arrow draws and
  routes the vertical arrows through a draw-scoped NUN5 rotation helper. The
  rejected global sprite-mode transplant and native-texture graft remain
  documented negative results.
- Command Menu and Command Chart share one NUN5 `TEX_xselect` rectangle fix;
  their pulse-dependent placement remains intact.
- Footer fixes are renderer-specific. Options, Collection root, Collection
  actions, Character Select, Stage Select, and Control Settings do not all use
  one universal anchor table.
- Collection Movie uses the exact official NUN5 strings. The rejected authored
  `<br>` insertion was removed; text fitting is not UI-texture work.
- Battle Results rank stamps use the complete five-record NUN5 atlas table.
  Screen-space Y compensation was rejected; detailed binding evidence is in
  the battle knowledge document.
- Battle item substitution doll uses the same-index NUN5 item record. The
  earlier cross-index `0x2E` edit was inert; the live consumer selects logical
  record `0x0A`.

## Runtime comparison

- Compare official NUN5 on the left with Current NA2.28 on the right. Vanilla
  NA2 is an optional diagnostic fallback, not a routine third capture.
- Normal pulsing differences are capture-phase noise. Semantic mismatch,
  clipping, wrong artwork, ordering, visibility, animation, and placement are
  UI defects.
- Report grids use exact integrated-build captures. Runtime-injected candidates
  remain explicitly labeled candidates until reproduced through the normal
  integrated pipeline.
- Savestate pairs and worker media live only under `work/UI translation/` while
  active. Accepted-case grids, states, worker ISOs, probes, logs, and PCSX2
  copies are removed after reusable findings are promoted.

## Accepted runtime results

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

The former epic's explicit acceptance dates were:

- 2026-07-26: Cross/Triangle labels, Character Items, Victory winner names,
  Ninja Song footer, and Battle Results screen 2.
- 2026-07-27: Collection Music Stop group and footer anchor; Cross/Play already
  matched.
- 2026-07-31: Battle item substitution doll.

## Cleanup already completed

- Deleted the redundant upscale archive and stripped NUN5 tree after verifying
  their retained counterparts.
- Removed the formerly tracked derived CCS blobs after exact source-derivation
  parity was established; Git history remains the recovery path.
- Removed accepted epic grids and their task-owned runtime evidence after user
  verification and promotion of reusable findings.

## Detailed knowledge

- [Battle UI](../../knowledge/localization/ui/battle.md)
- [Collection UI](../../knowledge/localization/ui/collection.md)
- [Options UI](../../knowledge/localization/ui/options.md)
- [Stage Select UI](../../knowledge/localization/ui/stage_select.md)
- [Victory UI](../../knowledge/localization/ui/victory.md)

