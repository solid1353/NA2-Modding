# UI Translation Workstream Plan

Last refreshed: 2026-07-20

This is the living handoff for the `TASKS.md` **UI Translation** task. Keep it concise enough to reread after context compaction. Refresh it only when a material fact, decision, plan, result, or blocker changes; do not turn it into a command-by-command log.

## Objective

Import appropriate official NUN5 English UI textures into NA2, correct the offsets for the selected entries, and investigate how the NUN5 PCSX2 upscale pack can help the UI-translation workflow.

## Asset inventory

### Game sources and donors

- `@source_na2/`: unpacked NA2 target files.
- `@source_nun5/`: unpacked official NUN5 English donor files.
- `@source_nun6/`: unpacked NUN6 A35 mod/reference files; reportedly translated into Brazilian Portuguese in both textures and text.
- `@analysis/disassembly/NA2/exports/SLPS_258.37/`: existing searchable NA2 boot-ELF C/TXT export.
- `@analysis/disassembly/NUN5/exports/SLES_556.05/`: existing searchable NUN5 boot-ELF C/TXT export. Check it by its exact `SLES` name; a prior `BTL|SLPS`-filtered inventory accidentally excluded it and caused a redundant temporary export attempt.
- `@analysis/disassembly/NA2/exports/ETC.BIN/` and
  `@analysis/disassembly/NUN5/exports/ETC.BIN/`: existing searchable Collection
  overlay exports; reuse them instead of generating another disassembly.
- The former `@source/__old/NUN5 DATA.CVM unpacked and stripped/` tree was
  analyzed, proven redundant, documented, and deleted as requested.

### Upscaled textures

- `@source/__upscaled/Naruto Shippuden Ultimate Ninja 5 PS2 Upscale Textures [SLES-55605]/`: complete unpacked NUN5 PCSX2 replacement-texture pack.
- The redundant packed distribution copy was deleted after the unpacked pack
  was confirmed complete and unnecessary to the production workflow.

### Tools

- `@tools/CCSFileExplorerMSF.zip`: CCS tool supplied by the NA2 modding community; currently the leading tool candidate.
- `@tools/old/`: legacy utility/archive dump containing possible CCS-related tools in unknown states.
- Relevant public comparison candidates found online:
  - `https://github.com/NCDyson/StudioCCS`
  - `https://github.com/zeroKilo/CCSFileExplorerWV`

### Mutable working data

- `work/UI translation/DATA.CVM.iso.files/`: copied extracted DATA.CVM tree used instead of source material because CCSFileExplorerMSF's mutation behavior is not yet established.
- `work/UI translation/CCSFileExplorerMSF/`: current tool/test area, including the demonstrated extracted battle-gauge textures.

## Confirmed facts

- CCSFileExplorerMSF opens the relevant CCS files and displays embedded textures.
- Its UI exposes named texture entries and separate `TEX_*` image-data and `CLT_*` palette blocks.
- It successfully extracted a `BATTLEGAUGE` texture set from the working copy.
- Preview and extraction are therefore demonstrated. Safe import/save/rebuild behavior is not demonstrated.
- Community reports about older CCS File Explorer builds describe palette corruption during Naruto texture reimport, so GUI saving must not be trusted without controlled validation.
- CCSFileExplorerMSF probably has no CLI. The production workflow should not depend on GUI automation if a deterministic parser/patcher can be built.
- Official NUN5 game assets are the authoritative English donor for disc texture transplantation.
- NUN6 A35 is a potentially valuable translated comparison donor. Its Portuguese texture/text changes can help identify localization-bearing CCS entries, demonstrate viable structural edits, and distinguish graphical text from ordinary string data. It is not the authority for final English wording.
- The NUN5 PCSX2 upscale pack is initially an identification/reference asset and optional emulator overlay. High-resolution replacements are not assumed safe for insertion into PS2 CCS containers.
- The upscale pack contains 8,217 PCSX2 replacement files, all hash-named DDS files under `textures/SLES-55605/replacements/`; it is not a directly named CCS asset tree.
- The community executable identifies itself as CCSFileExplorer 3.0.0.0, targets .NET Framework 4.8, previews gzip-wrapped CCS files, and has demonstrated batch texture extraction. Its archive contains binaries and PDBs but no source.
- `@tools/old/` contains older CCSFileExplorerWV and StudioCCS source trees. They document the CC2 section/TOC structure, indexed `TEX` (`0xCCCC0300`) and `CLT` (`0xCCCC0400`) blocks, raw import, palette quantization, and whole-file rebuilding; they are useful format evidence but not trusted production writers.
- The tested `BATTLEGAUGE.CCS` files are gzip streams named `battlegauge.tmp`. The mutable working copy is byte-identical to clean NA2, and the legacy stripped copy is byte-identical to clean official NUN5.
- The legacy stripped tree is not a uniquely patched translation source. Its 3,464 CCS files match the official NUN5 extraction; `charsel1.tmp` and `mapsel1.tmp` are exact decompressions of the official donor CCS files, and `GZLIST.TXT` is the original gzip/member-size inventory. It is useful workflow evidence but is reproducible and likely redundant after this task is documented.
- `BATTLEGAUGE.CCS` contains 32 named textures in both NA2 and NUN5. All 32 names match, and every corresponding texture/palette pair has identical dimensions and byte capacity. Object order and section offsets differ, so donor file offsets must not be copied; target sections can instead be resolved structurally by internal file/object name and patched in place without changing the decompressed NA2 payload size.
- The scoped UI inventory covers all root-level CCS files plus `LOADING/`, `MODENAME/`, and `HOME/`: 104 NA2, 323 NUN5 (including regional variants), and 51 NUN6 texture-bearing containers, with no parse failures. The official English donor is the unsuffixed NUN5 path rather than its `_F`, `_G`, `_I`, or `_S` regional variants.
- NA2 and unsuffixed NUN5 have 104 exact relative-path containers in common. Of these, 102 are fully compatible by internal texture name, dimensions, image-data capacity, and palette capacity. Across the common set, 881 of 885 shared textures are capacity-compatible; 195 compatible textures have differing image and/or palette hashes and are candidates for intentional review, not automatic wholesale replacement.
- `LOGO.CCS` is structurally exceptional: NA2 has four textures, NUN5 has five, and only three names are shared. The unmatched entries must not be transplanted blindly.
- `OUGI.CCS` is the other structural exception. Twenty names are shared, but four NUN5 entries are `128x64` where the corresponding NA2 entries are `64x64`; NA2 also has four additional `64x64` entries. NUN6 uses `256x128` versions of the same four shared names. The leading hypothesis is that NUN5 combines each pair of NA2 half-width textures into one wider localized texture; this requires visual and layout confirmation before designing the select-entry correction.
- The OUGI hypothesis is confirmed. NA2 has eight square label textures/models (`a1/a2` through `d1/d2`) and its BTL construction loop instantiates two parts. NUN5 and NUN6 have four wide labels, identical one-part model geometry, and identical one-iteration BTL construction logic. In NA2, the loop bound is the `slti` instruction at BTL file offset `0xB5E80`; changing its immediate from `2` to `1` is the minimal size-preserving equivalent when the complete NUN5 `OUGI.CCS` is imported.
- NUN6 is a useful translated control for layout. Its BATTLEGAUGE, CONTINUE, OPTION, OUGI, SPBATTLE, and VS placement geometry agrees with NUN5 where NA2 differs, even when NUN6 textures are Portuguese or higher resolution. This proves that the relevant NUN5 model/UV changes are localization data rather than incidental art differences.
- A decoded-RGBA audit found that every visual difference in the selected containers is already an intentional translation asset. OUGI additionally changes four English gauge/result textures (`ougi_gauge2`, `ougi_gauge3`, `ougi_spgau1`, and `ougi_spgau2`) that the initial mapping omitted. There are no unrelated changed images in the other selected containers.
- Most selected NA2/NUN5 containers have identical internal file/object name sets. The structural exceptions are BATTLEGAUGE, CHARSEL1, CONTINUE, OUGI, SPBATTLE, and one TITLE animation name; their external resource names and internal animation ownership must be checked rather than assumed. OUGI is the only confirmed case so far that requires a companion executable/BIN edit.
- Deterministically recompressed complete NUN5 payloads fit the fixed NA2 member capacity for every selected container except `MODENAME/MODE2KDV.CCS`. This includes HOME, whose original donor gzip is larger but whose recompressed stream has 19,940 bytes of headroom. `MODE2KDV` remains 207 bytes too large even with Zopfli.
- Preserved slots 3 and 4 proved that whole-container HOME import is not valid
  despite fitting the member: NUN5's collection models/layout duplicate the
  translated headers in NA2. HOME is now a mapped structural exception that
  retains the complete NA2 CCS structure and imports only the five reviewed
  NUN5 TEX/CLT pairs. Each target TEX keeps its first four-byte, container-local
  palette-object reference.
- `MODE2KDV` has a verified fixed-capacity alternative: retain the NA2 container, palette, portrait, and lower 192 rows; remap the donor texture's top 64 visual rows to the nearest NA2 palette entries. The preview preserves the English banner and portrait cleanly, and the resulting stream fits with 111 bytes of headroom.
- Ten manually paired F1 savestates were imported for NUN5 and Current: Mode
  Select, Options, Collection Characters, Collection Movie, four character-name
  selections, and two stage-name selections. All 20 `.p2s` files and embedded
  screenshots passed integrity checks. Pulsating labels are treated as capture
  phase noise; semantic mismatch, missing text, clipping, order, and placement
  remain defects.
- The wrong bottom button prompts are a shared-asset defect, not separate
  per-screen offsets. `CMN/GAUGE.CCS` contains `TEX_xpanel`: NA2 literally shows
  Circle/decision and Cross/back, while NUN5 supplies Cross/OK and Triangle/Back.
  The complete official NUN5 container fits the unchanged 72,505-byte NA2 member
  with 9,035 bytes of zero padding and is now the pinned `gauge` replacement.
- The character-select renderer reads 96 eight-byte UV records from the boot ELF,
  not from `CHARSEL1.CCS`. NA2 `FUN_0037d410` uses ELF file offset `0x4D4F70`;
  NUN5 `FUN_0038c3a0` uses `0x4DC120`. All 96 records differ. `ui_layout_character_name_rectangles`
  copies the complete range with source and destination range-hash guards.
- The stage-name problem combines wrong rectangles with missing width fitting.
  NA2 and NUN5 have the same 24 stage IDs and indices in the same order, but NA2
  stores Japanese rectangles inline at BTL file offset `0x20FC10`; NUN5 reads its
  English rectangles from ELF file offset `0x4DDB90` and horizontally fits any
  source wider than 214 pixels. `ui_layout_stage_select` copies all 24 official rectangles
  and stores the exact single-precision `min(1, 214/width)` result in NA2's
  redundant index word. The selected-preview consumer uses the already matched
  loop index; the thumbnail consumer recovers that index from its `row * 16`
  byte offset instead of reading the repurposed word. The draw path loads the
  stored horizontal scale while retaining vertical scale `1.0`. No code cave or
  absolute jump is used.
- The Options root renderer uses five menu-label and six difficulty-label
  rectangles from the boot ELF even when the complete NUN5 `OPTION.CCS` is
  present. NA2 and NUN5 use byte-identical screen positions, scales, and arrow
  rectangle; their label rectangles differ. `ui_layout_options_labels` copies the complete
  guarded 96-byte NUN5 block, including its eight-byte zero separator, from ELF
  file offset `0x4DDD10` to NA2 file offset `0x4D53E0`.
- The Collection Movie strings were already exact official NUN5 text. The
  authored `insert_br_after_words` transforms added in mapping version 34 were
  not part of texture translation and were rejected during runtime review.
  Mapping version 35 restores `M0771` through `M0774` to their exact prior NUN5
  source copies with no inserted `<br>`; text/font fit remains out of scope.
- Preserved slot 1 showed that the imported Mode Select START art was clipped by
  NA2's static `(1,397,206,22)` rectangle and X=`130` anchor. NUN5 localized
  accessor `FUN_003d4bc0` supplies `(1,393,254,26)` and renderer
  `FUN_003972e0` uses X=`150`. `ui_layout_mode_select` copies the exact rectangle and uses
  an authored same-register immediate port for X because the two compiled
  renderers use different destination registers. A later slot-1 pair showed
  the same screen's OK/Back anchors still right of NUN5. NUN5 applies regional
  offsets `-12/-8` after nominal X=`400/470`; NA2 has no equivalent additions.
  The same patch now uses authored effective anchors X=`388/462`. A guarded
  task-owned render places both prompts within +1 pixel X/Y of NUN5, consistent
  with their normal pulse phase. The user accepted the final Mode Select footer
  on 2026-07-26.
- Paired slot 1 proves the stage-picture pixels themselves already match while
  NA2's retained CCS structure associates and positions them incorrectly.
  `MAPSEL1.CCS` therefore uses the complete NUN5 donor so pictures, ordering,
  models, UVs, and labels remain coupled. The stage-name fitter now leaves
  vertical scale at `1.0` and applies the 214-pixel cap only horizontally. The
  fresh Slot 3 pair then exposed the missed thumbnail-index read and NA2's
  X=`300` Random prompt; the corrected patch derives indices `0..23` from the
  matched row and copies NUN5's exact X=`260` instructions for both prompt
  sprites.
- Paired slot 2 proves NUN5 retains the Jutsu1/Jutsu2 graphics beneath the open
  selector. The later suppression wrapper and hook caused the regression and
  are removed; the original 14 runtime-proven rectangle/placement edits remain.
- Paired slots 4 through 7 prove that texture-only HOME import retained
  incompatible NA2 models and UVs. `HOME.CCS` returns to the complete NUN5
  donor, restoring Collection chrome, Characters/Previous Page, the accepted
  character-details layout, and Movie/Play graphics together.
- Paired slot 8 resolves the missing graphical Vibration label through an exact
  eight-byte NUN5 boot-ELF rectangle copy. OFF/On text and font data are not
  changed.
- Slot 5 Controls and slot 7 Customize are complete. The accepted Customize
  screenshot is the corrected NA2 result produced by this task, not a NUN5
  donor reference. Its X=`255` placement remains the live-proven NA2 correction.
- Generic Slot 1 isolates the Victory defects to the shared `WINNER` artwork in
  `3EYE/ENDDEMO.CCS` and one `TEX_name` visual in each of 74 name-bearing
  `3EYE/3???3PCT.CCS` character resources. The former package-derived
  inventory covered only 61 and omitted 13 valid variants, including Sasuke's
  runtime-proven `3SSV3PCT.CCS`. Seventy-two complete character donors fit.
  Haku and Shikamaru use bounded NUN5-palette capacity adaptations; their exact
  evidence and negative results are in
  `docs/knowledge/localization/ui/victory.md`.

## Production artifacts and validation

- `na228_builder/features/localization/texture_patcher/` contains 109
  source-derived fixed-size recipes, 223 reviewed mappings, recorded
  source/donor/replacement/payload identities, and the deterministic verifier.
  Every replacement retains its target member size, and no replacement CCS
  blobs are stored in the repository.
- `na228_builder/features/localization/binary_patcher/` contains the canonical UI
  companion patches across BTL, ETC, and the boot ELF. The current UI subset
  has 27 patches and 297 guarded edits: 101 exact NUN5 copies, 24 values
  derived from NUN5's stage-width formula, 78 complete Victory descriptors
  derived from NUN5's frame templates and English widths, and 94 remaining
  NA2-ABI adaptations. Stage Select, Jutsu, command-scroll, Items, Mash, and
  Mode Select and both Settings footers are runtime-proven; Vibration,
  Collection, Victory, and the Battle Results screen-2 rank label still await
  their respective normal runtime acceptance.
  The Battle Results labels, title, summary footer, and moving clouds are
  proven; the details footer is user-accepted. The prior rank renderer/atlas
  trials remain disabled, and the replacement is now one exact five-record
  NUN5 rank-atlas table copied over NA2's incompatible 64x56 records. It awaits
  the next normal pipeline run.
- Translation mapping version 35 restores the four Collection Movie rows to
  exact official NUN5 source strings with no authored line breaks. A
  clean-source full in-memory plan produced 2,437 fixed-size patch rows with
  all three targets selected.
- The Localization feature's aggregate current-profile pin covers both canonical
  module inputs and their feature-relative paths.
- The complete Localization binary-patcher package validates as 7 targets, 9
  groups, 102 patches, and 461 edits; its UI subset is the 27 patches and 297
  edits counted above. The UI texture plan derives all 109 members with 105 whole
  donors and four mapped exceptions: MODE2KDV, ENDDEMO, Haku, and Shikamaru.
  The historical runtime harness remains available. Current binary-patcher
  validation and the focused UI texture provenance tests pass. No full-suite
  run or ISO build was performed for the latest BTL rank-table change.
- The 2026-07-19 non-launching normal profile build derived all 34 replacements
  through 76 texture mappings, applied all 88 companion edits, and reported
  `ISO result: updated` with rotation. Build record
  `@logs/na228/builds/20260719_030924_177_pid43832/` promoted a
  1,928,429,568-byte Current ISO with SHA-256
  `1AAE44B09BA9DA02F5AEBAF45F1605CEFB5B39B5C34E88D47745F8F613370369`;
  the previous accepted image rotated to Previous with SHA-256
  `C90B6B51AF8D4FB7DAC327DF144D1017653BDF8CC398CD1C837AAB53BC538A4C`.
  That historical Current boot ELF has independently verified PCSX2 CRC
  `273C80F3`. The runtime target has since been refreshed to the live Current
  identity, CRC `6D94D558`, with matching neutral per-game settings.
- Build record `@logs/na228/builds/20260718_061234_625_pid41880/` fully verified
  and promoted a changed 1,928,429,568-byte image. It is now
  `NA2.28 - Previous.iso`. An independent on-disc check found all 33 member ranges exact and the
  BTL bytes at `0xB5E80` equal to `01 00 42 2A`. This build predates the global
  `GAUGE.CCS`, character-table, and stage-layout fixes and is the captured
  defect baseline.
- Build record `@logs/na228/builds/20260718_094002_615_pid32972/` verified and
  promoted the complete current batch as the new 1,928,429,568-byte
  `NA2.28 - Current.iso`, rotating the defect baseline to Previous. The ISO
  SHA-256 is
  `2568D4DBD59BAD54442CB33041E0EB5784CB11F4CA36EE7A1AC49A85B3D50876`.
  Independent on-disc checks passed the exact `CMN/GAUGE.CCS` replacement, OUGI byte,
  final BTL hash, complete character and Options tables, all four Movie line
  breaks, renamed boot file, and preserved BTL/ELF sizes.
- The pre-final Current boot ELF had PCSX2 CRC `2FD18170`. The runtime target guard and
  its CRC-specific PCSX2 settings filename were updated; the settings copy is
  byte-identical to the previous neutral Current override and preserves the
  dedicated NA2 memory card. Both NUN5 and Current pass the neutral-rendering
  preflight. The canonical PNACH is empty, so actualization removed no aliases
  and enabled no cheats.
- A hidden, muted 20-second PCSX2 smoke test loaded `NA2.28 - Current.iso`, executed
  `SLPS_222.28`, reported CRC `71ADE583`, and stayed running without a boot-time
  error. The canonical PNACH was empty, so no cheats or managed aliases were
  active. This is boot validation, not screen-by-screen UI approval.
- The prior accepted build's boot ELF had independently verified PCSX2 CRC
  `273480D7`. Its runtime guard selected `SLPS-22228_273480D7.ini`, copied
  byte-for-byte from the earlier neutral Current override so rendering and the
  dedicated memory-card setup remained unchanged.
- Build record `@logs/na228/builds/20260718_233134_587_pid36704/` verified and
  promoted the prior accepted profile as a 1,928,429,568-byte Current ISO. That
  image is now Previous; its SHA-256 is
  `C90B6B51AF8D4FB7DAC327DF144D1017653BDF8CC398CD1C837AAB53BC538A4C`.
  The on-disc `PRG/ETC.BIN` remains 200,448 bytes.

## Completed cleanup

- Deleted the redundant upscale RAR after confirming the unpacked 8,217-file
  pack is complete and the archive form is not consumed. Its recorded size was
  1,042,489,809 bytes and SHA-256 was
  `677271AF46DFA4E61D9BFF9D86F0D7AC61B56CA5FDBD8F7D376465EA36740CE6`.
- Deleted the redundant legacy stripped tree after proving its 3,464 CCS members
  match official NUN5, its `.tmp` examples are exact decompressions, and its
  inventory role is reproduced by maintained extraction/module tooling. The
  deleted tree contained 3,474 files totaling 742,699,364 bytes.
- The unpacked upscale pack, official NUN5 source/extraction, and tracked
  evidence remain. The 34 formerly tracked production blobs were removed after
  exact source-derivation parity; they remain recoverable through Git history.
  The deleted auxiliary source copies are not locally recoverable except by
  re-extraction or reacquiring the distribution.

## Implemented technical design

The deterministic NUN5-to-NA2 CCS container transplant module uses
CCSFileExplorerMSF as an inspector and independent validator, not as the
production writer.

1. Keep a declarative repository-relative inventory of the intentionally translated textures, including structural relationships such as the paired NA2 OUGI labels.
2. For normal containers, verify both source hashes, decompress the complete official NUN5 CCS payload, recompress it deterministically into the unchanged NA2 member capacity, and pad only after the valid gzip stream. The normal profile performs this derivation directly; zlib is tried first and 28 tighter members use pinned Zopfli 0.4.3. This carries the donor's matching models, UVs, and animations together with its translated pixels without storing replacement blobs.
3. Treat `MODE2KDV`, ENDDEMO, Haku, and Shikamaru as the four mapped
   fixed-capacity/target-preservation exceptions. Every approximation uses only
   canonical donor pixels/palettes and records why a complete donor is
   unsuitable.
4. Keep the outer DATA.CVM member size, ISO record size, and all source files unchanged. Refuse any output that cannot fit the original fixed capacity.
5. Represent the OUGI one-part loop as a separate binary-patcher BTL semantic port.
   NUN5 proves the one-part behavior, but the exact NA2 replacement instruction
   is absent from canonical NUN5 ELF/BTL/ETC/ADV and therefore cannot honestly
   be represented as a donor copy.
6. Import the common `CMN/GAUGE.CCS` container as one fixed-size donor unit so
   its global regional button legends, matching models, and UVs remain coupled.
7. Pair `CHARSEL1.CCS` with the complete homologous NUN5 boot-ELF character-name
   rectangle table rather than applying per-character guesses.
8. Pair `MAPSEL1.CCS` with all 24 NUN5 stage rectangles and the equivalent
   214-pixel fit scale stored inside NA2's existing record topology.
9. Pair `OPTION.CCS` with the complete NUN5 Options and difficulty rectangle
   tables from the boot ELF.
10. Leave text content and font rendering to their separate workstreams; this
    task changes no text bytes or translation mappings.
11. Validate every output by decompressing/reparsing it, checking the intentional decoded visual set, comparing full-container payloads to the donor, verifying the KDV preserved region, and recording hashes/capacity.
12. The proven UI module and companion binary-patcher patches are integrated into the
   hash-pinned current profile without overwriting concurrent work.

## Runtime comparison workflow

- The normal runtime comparison is intentionally two-way: official NUN5 is the
  English target and Current is the result being corrected. Vanilla NA2 is an
  optional diagnostic fallback only; no routine third capture is required.
- `scripts/research/ui_translation/` provides a PINE-backed, read-only-first
  capture harness. It verifies live serial/CRC identity, ISO hash, rendering
  conditions, and paused state before archiving a `.p2s`, its embedded
  `Screenshot.png`, and a repository-relative manifest under
  `@work/UI translation/runtime_cases/`.
- The focused harness suite has 17 passing tests. Its manual F1 importer preserves
  the user-created states, extracts embedded screenshots, hashes inputs, and
  records repository-relative manifests without requiring a live PINE capture.
- Ten matching NUN5/Current pairs are archived under
  `@work/UI translation/runtime_cases/`; the two contact sheets are under
  `@work/UI translation/runtime_review/`.
- The configured savestate folder was cleared before the fresh pilot. The 14
  prior slot, resume, and backup states were moved to the Windows Recycle Bin.
- Texture replacements are disabled. Current and NUN5 both pass the
  neutral-rendering preflight. NUN5's per-game settings now permanently use
  `4:3`, and its former `Widescreen 16:9` patch override has been removed while
  preserving the dedicated NUN5 memory-card selection.
- Recommended capture priority is CHARSEL1 first, then BATTLEGAUGE, OUGI,
  TITLE, MODESEL1/MAPSEL1, CONTINUE, SPBATTLE, and the hybrid MODE2KDV banner.
  HOME/Collection, options/practice, clash prompts, and result screens
  are secondary coverage rather than prerequisites for the pilot.

### Paired savestate 1-8 correction matrix

- Slot 1, Stage Select: use whole NUN5 `MAPSEL1.CCS` for exact stage
  association/order/layout and keep stage-name vertical scale at `1.0` while
  applying the 214-pixel fit only horizontally.
- Slot 2, battle confirmation with selector open: remove the rejected
  Jutsu-label suppression wrapper/hook and retain the 14 runtime-proven texture
  rectangle, glyph, arrow, and prompt edits.
- Slot 4, Collection main: whole NUN5 `HOME.CCS` restores the complete
  graphical chrome.
- Slot 5, Collection Characters: whole HOME restores the English Characters
  and page-control artwork, but NA2's ETC draw tables still clipped the
  144-pixel `Previous Page` donor to 118 pixels and extended the Characters
  rectangle into the Movie row. `ui_layout_collection_submenu` copies the paired NUN5 page
  centers/rectangles plus the NUN5 category-title rectangles; runtime
  acceptance is pending.
- Slot 6, character details: whole HOME restores the earlier accepted button
  labels and layout that the mapped import regressed.
- Slot 7, Collection Movie: whole HOME supplies Movie and Play graphics;
  `ui_layout_collection_submenu` now supplies their exact NUN5 source rectangles, while mapping
  v35 removes the four unauthorized authored `<br>` transforms.
- Slot 8, Controls: `ui_layout_controls_vibration` copies the exact NUN5 Vibration-label
  rectangle used by the imported common UI atlas.
- Visible text overflow/font spacing and OFF/On values are out of scope.
  Normal pulsation differences are not defects.

## Open questions

No static implementation question blocks the remaining-screen pass. Runtime
visual acceptance remains with the user by explicit instruction. Slot 3 Stage
Select passed comparison with NUN5 on 2026-07-22 and `ui_layout_stage_select` is now
`runtime_proven`; the guarded Mode Select slot-1 comparison likewise promotes
`ui_layout_mode_select` to `runtime_proven`. Vibration and Collection submenu patches
stay `approved_for_test` until their respective screens pass. `LOGO.CCS`,
upscale-pack hash mapping, and broader NUN6 comparison remain optional future
research.

## Current status and next checkpoint

### Active mismatch priority

1. Victory. The complete source-derived texture and rectangle implementation
   is integrated; normal-entry runtime acceptance remains.
2. The remaining grouped screens.
3. Combat prompts.

Items and Mash Prompt are complete. The Mash Prompt pair is a separate
task-owned evidence category under
`@work/UI translation/inputs/sstates/library/Mash Prompt/`, immediately below
Items in this queue. It is now part of the general remaining-issues pass rather
than a separate `TASKS.md` subtask.

All eight preserved cases now have declarative implementations. The normal
workflow derives all 109 fixed-size CCS replacements directly from
canonical NA2/NUN5 inputs with no stored replacement blobs. The source trees
and original savestates remain untouched. The unique historical
`NA2.28 - Previous.iso`, paired NA2.28/NUN5 states 1-8, and the minimal
Zstandard extraction helper now live under
`@work/UI translation/runtime_baselines/savestates_1_8/`. The former ownerless
lab was removed after deleting its regenerable EE-memory dumps, embedded
screenshot copies, and superseded exploratory scripts. Static validation
passes all 61 repository tests, exact-source raw composition, translation v35, and
34-container derivation.

The non-launching profile build retained
`@logs/na228/builds/20260719_071938_407_pid46920/`, promoted the
1,928,429,568-byte Current ISO with SHA-256
`8BC43A5C583F488A9D71CD17338E6164006CF68EF8C439A209F59640D77B7E37`,
and rotated the prior Current to Previous with SHA-256
`869170F6209EAF3B8E28CECC8AE24EF9D8C5C89431065AE78F3CEF11BDF8EDFD`.
An immediate second build hit the receipt-backed preflight, reported
`ISO result: unchanged`, performed no rotation, and created no `.building`
image. PCSX2 was never launched; screen-by-screen acceptance is deliberately
left to the user.

After user runtime review, either promote the stage-fit and Vibration patches
to `runtime_proven` or retain a narrowly described defect for another
iteration.
`Investigate upscaling.` remains the separate UI Translation workstream item.

### Screen correction pass: Collection Characters, Movie, and Music

The 2026-07-22 paired slot-1 capture isolates two defects: NA2.28 displays
`Previous Pa` while NUN5 displays the full `Previous Page`, and the NA2
Characters title includes fragments from the next atlas row. `Next Page` and
the character grid are otherwise accepted for this pass. The same page-prompt
clipping exists in the preserved Previous-ISO capture, so it predates the
latest donor conversion.

The user then supplied paired slot-2 Movie and slot-3 Music states. Movie
samples the Music row beneath its title, Music has no visible title, and both
screens clip `Play` to `Pl...`. Their list wording, wrapping, and font spacing
remain explicitly outside this texture-only pass.

Static tracing identifies exact homologous records rather than authored
placement guesses. `ui_layout_collection_submenu` copies NUN5 centers X=`87`/`233` over NA2
X=`100`/`220`, then copies the two 144x24 page rectangles over NA2's 118x24
rectangles. It also replaces the three NA2 category-title records with NUN5's
exact Characters `(0,0,192,28)`, Movie `(0,28,96,28)`, and Music
`(0,56,96,28)` records. The common Play helper receives NUN5's exact
`(144,24,72,24)` record in place of NA2's 24-pixel-left `(120,24,72,24)`
selection. The neighboring Stop and other unreviewed HOME controls remain
untouched. The normal workflow derives every byte from canonical NUN5
`ETC.BIN`/ELF; no stored asset or replacement byte was added. Detailed
function, address, memory, and negative-result evidence is preserved in
`docs/knowledge/localization/ui/collection.md`. PCSX2 has not been launched and no ISO has
been rebuilt for this correction.

The isolated six-edit checkpoint preserved ETC's 200,448-byte size and produced
SHA-256
`E83768B6B39264A97146BE384E3D0A245EE5CBBB288848D1A965934C66C28FFA`.
Exactly 16 destination bytes differ, all within the six declared ranges; the
adjacent Stop record remains byte-identical. At that checkpoint,
binary-package validation reported 86 patches and 250 edits, the 33 focused
profile/UI tests passed, and the full repository suite passed 127/127. Its
Localization feature pin was
`7242AC919B21DD834ECFEB391B3EA35709969EA090779F6687A601858928445E`.
Runtime acceptance still requires a user-authorized ISO rebuild followed by
the user's visual review.

### Screen correction pass: Collection character-viewer lower controls

The later paired slot-1 capture isolates only the four lower-left controls.
NA2 places Rotate, Move, Zoom In, and Zoom Out on one horizontal row at
Y=`360`; NUN5 places Zoom In/Zoom Out at Y=`339` and Move/Rotate at Y=`364`.
The NUN5 rectangle table also widens both Zoom records and selects Zoom Out at
its English-atlas U coordinate. Back, the character model, and all name/jutsu
text are accepted or out of scope and remain untouched.

`ui_layout_collection_submenu` now adds two exact guarded NUN5 ETC copies: the complete 64-byte
position block from `0x283D0` to NA2 `0x2EB40`, and the complete 32-byte
rectangle block from `0x29A90` to NA2 `0x30AB0`. No literal replacement or
stored asset is added. The isolated eight-edit apply preserves the 200,448-byte
ETC size, produces SHA-256
`E6054FCD42A3834197AE638D3EF77E10BE86633A997C6CF9F18887FA788A298A`,
and differs from canonical NA2 in exactly 30 bytes, all inside declared ranges.
Package validation reports 7 targets, 9 groups, 86 patches, and 252 edits; the
33 focused UI/profile tests and full 127-test suite pass. The current
Localization feature pin is
`CF173194E0BB28DB3CC516B176DB9F90F1103749890F5EE4AF6BD6CCC9CBDB56`.
PCSX2 has not been launched and no ISO has been rebuilt.

### Remaining paired screen-reference batch

The user supplied eight paired NA2.28/NUN5 savestate references for the next
screen-by-screen correction pass:

1. Character Select: `Select Color` and `Random` should move left.
2. Stage Select: total layout mismatch.
3. Jutsu Selection: horizontal arrows must be hidden and vertical arrows must
   be shown.
4. Command Menu: green garbage appears where vertical arrows should be.
5. Command Chart: the same vertical-arrow/green-garbage defect appears.
6. Options: `Cancel` placement is wrong.
7. Music Options: `Select` should move right.

The maintained capture importer archived both games' state, embedded 640x480
screenshot, and repository-relative manifest for each pair under:

- `@work/UI translation/runtime_cases/remaining_02_character_select_color_random/`
- `@work/UI translation/runtime_cases/remaining_03_stage_select_total_mismatch/`
- `@work/UI translation/runtime_cases/remaining_04_jutsu_selection_arrows/`
- `@work/UI translation/runtime_cases/remaining_05_command_menu_vertical_arrows/`
- `@work/UI translation/runtime_cases/remaining_06_command_chart_vertical_arrows/`
- `@work/UI translation/runtime_cases/remaining_07_options_cancel_placement/`
- `@work/UI translation/runtime_cases/remaining_08_music_options_select_placement/`

All 16 archived state hashes and all 16 screenshot hashes match the supplied
slot files, and the original PCSX2 states remain untouched. Savestate age is
irrelevant for these visual screen references and must not be used to date a
regression. Cases may be handled individually or grouped only after static
analysis demonstrates a shared renderer or table root cause. Slot 3 Stage
Select is runtime-proven. The integrated visual pass accepted Slots 5 and 6,
promoting their shared `ui_layout_command_scroll_arrows` correction to runtime-proven, while Slot 4
rejected the first `ui_layout_jutsu_selector_arrows` result and remains under active correction. The
other slots remain untouched by this iteration.

With the user's authorization, global PCSX2 texture replacement loading was
disabled before archiving (`LoadTextureReplacements = false`); asynchronous
replacement support remains configured but inactive. PCSX2 was not launched.

### Screen correction pass: Jutsu selector and command scroll arrows

Paired Slot 4 proves that the open Jutsu selector is not a rectangle-only
problem. NA2 `FUN_006bd4d0` retains two closed-state horizontal-arrow draws,
uses a Japanese-atlas rectangle that samples lettering after the NUN5 VS
import, and never rotates the donor's right-pointing green arrow. NUN5 homolog
`FUN_006d0850` omits the horizontal draws, uses rectangle
`(145,385,22,38)`, and applies `+pi/2`/`-pi/2` around the upper/lower draws.
The accepted `ui_layout_jutsu_selector_arrows` replaces only the dead horizontal-arrow draw region
with a draw-scoped helper, copies both NUN5 rotation constants and the complete
NUN5 arrow record, and redirects the two existing vertical-arrow calls through
that helper. The helper enables sprite mode 1 only around the rotated draw and
flush, restores mode 0 afterward, and conditionally flips the lower arrow.
This avoids both the rejected unscoped sprite-mode transplant and the rejected
native-texture graft while retaining the complete official NUN5 `VS.CCS`.
Detailed negative and accepted-path evidence is preserved in
`docs/knowledge/localization/ui/battle.md`.

Paired Slots 5 and 6 reuse the same `TEX_xselect` sprite object and the same
draw record. NA2 `FUN_00878820` and NUN5 `FUN_00894f60` already share the
two-draw/one-rotation behavior; only their source rectangles differ.
`ui_layout_command_scroll_arrows` therefore copies one exact NUN5 record `(1,225,20,22)` over
NA2's imported-atlas garbage selection `(194,195,20,20)`. Pulse-dependent
placement is preserved. The user verified both integrated screens and accepted
Command Menu and Command Chart as good.

Canonical binary-package validation reports 7 targets, 9 groups, 102 patches,
and 461 edits. The accepted isolated runtime result additionally copies the
complete NUN5 OK/Back records, suppresses NA2's redundant separate glyph draws,
and calibrates their NA2 anchors so both prompts match the NUN5 reference.
The user's final paired visual inspection accepted Slot 4 as perfect on
2026-07-22; Slots 5 and 6 remain runtime-proven. The accepted Slot 4 savestate
pair and active mismatch-list entry were then removed under workstream policy.

No maintained mismatch remains in the declared remaining-UI epic. The user
accepted Collection Music ss10 on 2026-07-27 after its patch copied NUN5's
exact `(144,48,76,24)` Stop record, applied the homologous state-4 compositor
delta `-2`, and changed the Stop-label local X offset from `-35` to `-40`;
Cross/Play remained unchanged and matched. Battle Results
screen 2, Ninja Song details ss8, Victory ss7 all-character donor coverage,
Character Items transition behavior, and the Cross/Triangle-label batch are
user-accepted.
Within the accepted Cross/Triangle batch,
the Options-root Slot 1 caller now uses the proven effective NUN5 OK/Back
anchors X=`388`/`462`. Collection-root Slot 2 uses its separate ETC position
table with effective NUN5 anchors X=`368`/`452`; a guarded task-owned render
matches the reference. Collection Music Slot 3 uses the different shared HOME
action helper: one guarded wrapper applies NUN5's state-specific Cross
`-12`, Play `-24`, and Triangle `-8` geometry, and the Play label receives the
same localized centering shift. Its task-owned render matches the reference.
Character Select Slot 4 extends its existing `ui_layout_character_select_footer` footer patch with
effective NUN5 OK/Back anchors X=`388`/`462`; its task-owned render also
matches the reference. Stage Select Slot 5 extends `ui_layout_stage_select` with the same
effective anchors at its separate overlay call sites; its guarded task-owned
render matches the reference. Current Slots 1-5 are complete. New paired
slot-1 Music Settings extends the existing `ui_layout_options_footers` renderer patch with
effective NUN5 OK/Back anchors X=`388`/`462`; its guarded task-owned render
matches the reference. Newer paired slot-2 Collection Characters is a true
reuse of the already-canonical `ui_layout_common_prompts` HOME helper: the existing five
guarded rows align its OK/Back groups with no new binary edit. Newer paired
slot-3 Control Settings extends the same `ui_layout_options_footers` ownership at its separate
renderer call sites with the same effective NUN5 anchors; its guarded
task-owned render matches the reference. The
earlier original Slot 2 failure of the `0x2E7E0` table/HOME helper remains
evidence only that Collection root uses a separate renderer. The rejected
rank-label Y-compensation trial and exact pixel/object evidence are preserved
in `docs/knowledge/localization/ui/battle.md`; resume from texture/CLUT binding
or cached GS-packet evidence rather than retrying screen-space constants. The
standalone binary-patcher package validates with the otherwise canonical
patch. Focused UI texture provenance tests pass; the latest footer change has
not received a full-suite run or ISO build.
