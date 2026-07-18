# UI Translation Working Context

Last refreshed: 2026-07-18

This is the living handoff for the `TASKS.md` **UI Translation** task. Keep it concise enough to reread after context compaction. Refresh it only when a material fact, decision, plan, result, or blocker changes; do not turn it into a command-by-command log.

## Objective

Import appropriate official NUN5 English UI textures into NA2, correct the offsets for the selected entries, and investigate how the NUN5 PCSX2 upscale pack can help the UI-translation workflow.

## User direction and boundaries

- The user will follow the agent's technical lead for this task.
- Talk through consequential decisions; keep the approach reproducible and evidence-driven.
- Convert user-supplied absolute paths to repository/configured-root-relative notation in project materials.
- `@source/` is read-only reference material. The two explicitly authorized
  auxiliary cleanups were completed after their recorded conditions were met.
- `work/ui_translation/` is a mutable task workspace. Its contents may be inspected, reorganized, modified, regenerated, or deleted as needed.
- `@utils/old/` is an untrusted tool/archive dump. Inspect before selecting or executing anything from it.
- Useful inspected utilities may be promoted into the maintained `@utils/` area with provenance and usage notes.
- A separate **Scripts** task was running concurrently. Its changes were
  preserved and committed independently while this task was active. At the
  start of this task they were:
  - `scripts/project/set_analysis_readonly.ps1`
  - `scripts/research/ghidra/export_project.ps1`
  - `scripts/research/ghidra/import_targets.ps1`
  - `scripts/research/ghidra/targets.tsv`
  - `scripts/research/ghidra/build_manifest.ps1` (appeared while this handoff was being created)

## Asset inventory

### Game sources and donors

- `@source/NA2.iso.files/`: unpacked NA2 target files.
- `@source/NUN5.iso.files/`: unpacked official NUN5 English donor files.
- `@source/NUN6 A35.iso.files/`: unpacked NUN6 A35 mod/reference files; reportedly translated into Brazilian Portuguese in both textures and text.
- The former `@source/__old/NUN5 DATA.CVM unpacked and stripped/` tree was
  analyzed, proven redundant, documented, and deleted as requested.

### Upscaled textures

- `@source/__upscaled/Naruto Shippuden Ultimate Ninja 5 PS2 Upscale Textures [SLES-55605]/`: complete unpacked NUN5 PCSX2 replacement-texture pack.
- The redundant packed distribution copy was deleted after the unpacked pack
  was confirmed complete and unnecessary to the production workflow.

### Tools

- `@utils/CCSFileExplorerMSF.zip`: CCS tool supplied by the NA2 modding community; currently the leading tool candidate.
- `@utils/old/`: legacy utility/archive dump containing possible CCS-related tools in unknown states.
- Relevant public comparison candidates found online:
  - `https://github.com/NCDyson/StudioCCS`
  - `https://github.com/zeroKilo/CCSFileExplorerWV`

### Mutable working data

- `work/ui_translation/DATA.CVM.iso.files/`: copied extracted DATA.CVM tree used instead of source material because CCSFileExplorerMSF's mutation behavior is not yet established.
- `work/ui_translation/CCSFileExplorerMSF/`: current tool/test area, including the demonstrated extracted battle-gauge textures.

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
- `@utils/old/` contains older CCSFileExplorerWV and StudioCCS source trees. They document the CC2 section/TOC structure, indexed `TEX` (`0xCCCC0300`) and `CLT` (`0xCCCC0400`) blocks, raw import, palette quantization, and whole-file rebuilding; they are useful format evidence but not trusted production writers.
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
- `MODE2KDV` has a verified fixed-capacity alternative: retain the NA2 container, palette, portrait, and lower 192 rows; remap the donor texture's top 64 visual rows to the nearest NA2 palette entries. The preview preserves the English banner and portrait cleanly, and the resulting stream fits with 111 bytes of headroom.

## Production artifacts and validation

- `na2_patcher/modules/ui_textures/` contains 33 fixed-size blobs, 72 reviewed
  mappings, pinned source/donor/blob/payload hashes, the deterministic verifier,
  and authoring support. The canonical replacement bytes total 5,201,893 bytes.
- `na2_patcher/modules/raw_binary/patch_sets/ui_translation/` contains
  `UI-BTL-001`, the one four-byte OUGI loop edit. It remains
  `approved_for_test` until the affected battle screens are visually verified.
- `na2_patcher/profiles/current/modules.tsv` enables both modules by canonical
  executable-input hash.
- All 29 repository tests passed after integration. The focused UI suite proves
  donor equality for all 32 whole-container imports, exact KDV changed-region
  bounds, OUGI topology, fixed member sizes, and complete profile logging.
- Build record `@logs/na2/builds/20260718_061234_625_pid41880/` fully verified
  and promoted a changed 1,928,429,568-byte `NA2.28 - Current.iso`, rotating the previous
  image. An independent on-disc check found all 33 member ranges exact and the
  BTL bytes at `0xB5E80` equal to `01 00 42 2A`.
- A hidden, muted 20-second PCSX2 smoke test loaded `NA2.28 - Current.iso`, executed
  `SLPS_222.28`, reported CRC `71ADE583`, and stayed running without a boot-time
  error. The canonical PNACH was empty, so no cheats or managed aliases were
  active. This is boot validation, not screen-by-screen UI approval.

## Completed cleanup

- Deleted the redundant upscale RAR after confirming the unpacked 8,217-file
  pack is complete and the archive form is not consumed. Its recorded size was
  1,042,489,809 bytes and SHA-256 was
  `677271AF46DFA4E61D9BFF9D86F0D7AC61B56CA5FDBD8F7D376465EA36740CE6`.
- Deleted the redundant legacy stripped tree after proving its 3,464 CCS members
  match official NUN5, its `.tmp` examples are exact decompressions, and its
  inventory role is reproduced by maintained extraction/module tooling. The
  deleted tree contained 3,474 files totaling 742,699,364 bytes.
- The unpacked upscale pack, official NUN5 source/extraction, production blobs,
  and tracked evidence remain. The deleted auxiliary copies are not locally
  recoverable except by re-extraction or reacquiring the distribution.

## Implemented technical design

The deterministic NUN5-to-NA2 CCS container transplant module uses
CCSFileExplorerMSF as an inspector and independent validator, not as the
production writer.

1. Keep a declarative repository-relative inventory of the intentionally translated textures, including structural relationships such as the paired NA2 OUGI labels.
2. For normal containers, verify both source hashes, decompress the complete official NUN5 CCS payload, recompress it deterministically into the unchanged NA2 member capacity, and pad only after the valid gzip stream. This carries the donor's matching models, UVs, and animations together with its translated pixels.
3. Treat `MODE2KDV` as the single declared indexed-row exception: preserve the NA2 payload and palette and import only the donor's top 64 visual rows through a deterministic palette remap.
4. Keep the outer DATA.CVM member size, ISO record size, and all source files unchanged. Refuse any output that cannot fit the original fixed capacity.
5. Represent the OUGI one-part loop as a separate approved-for-test raw-binary BTL patch with exact expected bytes and provenance from matching NUN5/NUN6 behavior.
6. Validate every output by decompressing/reparsing it, checking the intentional decoded visual set, comparing full-container payloads to the donor, verifying the KDV preserved region, and recording hashes/capacity.
7. The proven UI module and companion raw-binary patch are integrated into the
   hash-pinned current profile without overwriting concurrent work.

## Open questions

- Whether BATTLEGAUGE, CHARSEL1, CONTINUE, SPBATTLE, and TITLE require any companion code/name adjustment after their complete donor containers are tested. Current static evidence says their externally loaded names remain available; OUGI is the one confirmed code edit.
- How `LOGO.CCS` should be treated, given its intentionally unmatched regional/language textures.
- How PCSX2 texture hashes/names in the upscale pack map back to CCS entries.
- Which NUN6 A35 files differ from NUN5 specifically because of Brazilian Portuguese localization, and whether those differences reveal a proven texture-import method.

## Current status and next checkpoint

Static implementation, deterministic verification, profile integration, full ISO
verification, and a clean boot smoke test are complete. Original game sources
were not modified; only the two explicitly authorized redundant auxiliary
references were deleted. The first user-visible pass found many issues, so this
state is an initial reproducible visual baseline rather than an accepted UI
result. The next checkpoint is to inventory the failures by exact screen and
symptom, prioritizing OUGI, BATTLEGAUGE, CHARSEL1, CONTINUE, SPBATTLE, TITLE,
and MODE2KDV. Cutoff, placement, missing-resource, animation, and unrelated-art
problems must be separated before changing another offset or container strategy.
