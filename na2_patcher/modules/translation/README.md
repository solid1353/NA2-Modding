# NA2 translation module (mapping version 33)

This first-class `na2_patcher` module builds an in-memory translation plan for **Narutimate Accel v2.28**, based on *Naruto Shippuuden: Narutimate Accel 2*. It never packages patched BIN or ELF payloads. Profile builds invoke `engine.py` directly and log the plan without using a TSV as an inter-stage handoff. There is no standalone export command.

## Mapping metadata

- Version: `33`
- Packaged `mappings.tsv` SHA-256: `c4f317c0a86c2be3fb07512652ce5e50d9b73ae485ebaa502c4ed1fabc9c28a5`

The README is the canonical home for both values. The module does not use one-line `VERSION.txt` or `MAPPINGS_DEFAULT.sha256` sidecars; it reads and validates this metadata directly from `README.md`.

## Source and target scope

Clean NA2 targets:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`
- `SLPS_258.37`

Official NUN5 sources:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`
- `PRG/TEXTENG.BIN`
- `SLES_556.05`

`slot` and `sequence` mappings read their English bytes from exact NUN5 offsets at build time. The only manual English permitted is in `shorten` rows, where the replacement begins with `[S]` because the official NUN5 text cannot fit the original NA2 slot. No translation is relocated into spare space and no text pointer is rewritten.

## Canonical `mappings.tsv`

`mappings.tsv` is the single canonical mapping table. TSV has no worksheet tabs, so `section` is the page/filter key for grouping mappings by screen or mode.

The 12 columns are:

`id`, `enabled`, `section`, `mode`, `target`, `target_offset`, `capacity`, `source_ref`, `transform`, `arguments`, `value`, `reason`

### Stable IDs and enabled state

- `id` is a stable mapping identifier.
- `enabled=1` applies the row.
- `enabled=0` retains the row without applying it.
- `mappings.tsv` is the only enabled-state source. Profile builds never rewrite it
  or inherit flags from external state.
- Changing an enabled flag changes the canonical module input and therefore
  requires an explicit profile hash update.

### Modes

- `slot`: copy one exact official NUN5 text value into one original NA2 slot.
- `sequence`: pack selected exact `<br>` parts from one official NUN5 string into one verified NA2 multi-string block using NUL separators.
- `shorten`: use the `[S]` replacement in `value`, retaining the exact NUN5 source reference for traceability.
- `bytes`: fixed-size structural patch represented as `EXPECTED=>REPLACEMENT` in `value`.
- `unresolved`: retain an investigated but unsafe or unproven mapping without applying it.

There is no `pool` mode. Text stays in its original target slot.

### Source references and transforms

`source_ref` uses `SOURCE@OFFSET`, for example `NUN5_TEXTENG@0x29430`.

Supported source-derived transforms:

- `format_arg1`, `format_args`
- `format_prefix_arg2`, `format_suffix_arg2`
- `between_placeholders`, `after_placeholder2`
- `split_br`, `split_br_sequence`, `join_br_parts`
- `flatten_br_slice`
- `append_space`
- `empty`

Arguments use compact key/value syntax, for example:

- `arg1=NUN5_TEXTENG@0x708`
- `part=1`
- `parts=2,3;join=<br>`
- `start=13;end=83`

`split_br_sequence` selects official NUN5 `<br>` parts listed by `parts=...` and writes them as consecutive NUL-terminated NA2 fragments.

`flatten_br_slice` replaces each official NUN5 `<br>` with one space and selects a verified character range. It is used to distribute one official loading sentence across NA2's three original fixed slots without embedding manual prose.

## Output

Each profile build records the translation module under:

`logs/na2_patcher/current_<run id>/<module id>/`

containing:

- `translation_plan.tsv`
- `translation_summary.json`

The generated translation TSV contains exactly six columns:

`path`, `offset`, `expected_hex`, `replacement_hex`, `source_text`, `replacement_text`

All ISO target paths inside the TSV remain ISO-root-relative. The profile-level module inventory also records only repository-relative paths.

`translation_summary.json` contains general and aggregate information:

- mapping version and selected targets;
- patch and mapping totals;
- active mapping coverage grouped by mode and section;
- source and translated-file hashes.

Disabled and unresolved rows remain solely in `mappings.tsv`.

## Safety behavior

Known clean-source SHA-1 values are always checked. Unknown source media is rejected before a plan is produced.

The module rejects malformed flags, duplicate IDs, invalid offsets, invalid source references, malformed transforms, overlapping active mappings, unexpected structural bytes, text exceeding its declared slot or sequence block, malformed target sequences, and invalid named-color conversion. Enabled bad mappings fail the build instead of becoming silent runtime skips.

### Exact slot boundaries

A text mapping's `capacity` must end inside zero padding belonging to that string. The module rejects a declared slot if any nonzero byte appears after the original NUL terminator within that capacity. This prevents a text write from zero-filling adjacent pointer tables or other structural data.

This check directly guards against both v28 regressions fixed in v29:

- `M0776` crossed from the `Credits` string into the Collection movie-pointer table at `SLPS + 0x2FFD1C`.
- `M0792` crossed from the difficulty-reset result string into the Options navigation table at `SLPS + 0x4B2BF0`.

Official Western text is decoded as Windows-1252. NA2 target strings are decoded as CP932 for inspection and markup adaptation. File sizes never change.

## Markup handling

The original NA2 target is authoritative for renderer-specific color forms:

- NUN5 `<WHITE>` becomes NA2 `<colorFFFFFF>` only where that target uses it.
- NUN5 `<BLACK>` remains `<BLACK>` or becomes `<color000000>` according to the verified target form.
- `<RED>` is retained only where the target supports it.
- Other shared color, icon, line-break, and control tags are preserved.

## Version 33 changes

### Temari Collection voice-title resolution

The previously unresolved Temari voice title `姉の喜び` is now mapped to the exact official NUN5 title `Silent Confidence`. The user supplied the matching NUN5 Collection screenshot, and the binary source was verified at `PRG/TEXTENG.BIN + 0x24B0`.

`M0725` now applies an enabled `slot` mapping to `PRG/ETC.BIN + 0x2C750`. The 18-byte English string fits the original 32-byte zero-padded NA2 slot, so no shortening, relocation, pointer rewrite, or file-size change is required.

### Packaged table totals

The packaged v33 table contains 2,241 mappings: 2,231 enabled and 10 disabled. Enabled rows comprise 2,136 `slot`, 4 `sequence`, 33 `shorten`, and 58 `unresolved` mappings. All four structural `bytes` rows remain disabled.

All script and generated-artifact path references remain relative. v33 adds no absolute path literals, patched payload files, relocation pools, pointer rewrites, or target-size changes.

### v33 build validation

A clean-source full build was validated with all three targets selected:

- 2,437 six-column TSV patch rows;
- 2,173 applied text mappings;
- 33 shortened mappings;
- zero active structural patches;
- unchanged target file sizes;
- relative `translation_tsv` in `build_summary.json`;
- exact `M0725` patch at `PRG/ETC.BIN + 0x2C750`, replacing `<r姉|あね>の<r喜|よろこ>び` with `Silent Confidence`.

## Version 32 changes

### Collection character-model animation pass

v32 traces the remaining Japanese mannequin/model animation labels through the per-character `if...anmN` identifiers shared by NA2 and NUN5. It adds or activates 35 verified mappings:

- 32 exact official names copied from `PRG/TEXTENG.BIN` or the NUN5 executable short-string table;
- `M0717` is activated as exact `Hey!` after its identifier match was confirmed;
- `[S]Long Time!` is used for `Long Time No See!`, which cannot fit Ino's 16-byte NA2 slot;
- `[S]Now` is used for `Now then...`, which cannot fit Kankuro's 8-byte executable slot.

This completes every untranslated Japanese model-animation label found in the supplied 54-screen v31 review set, including Naruto, Kakashi, Neji, Tenten, Shikamaru, Choji, Ino, Asuma, Kiba, Shino, Hinata, Kurenai, Kankuro, Temari, Chiyo, Itachi, Kisame, Deidara, Jiraiya, Tsunade, Shizune, Yamato, Orochimaru, Kabuto, and Sasuke entries.

### Collection voice/audio title pass

v32 adds or activates 20 verified voice-title mappings by matching their position in the official NUN5 title sequence and, where applicable, the NUN5 executable's short-string copies. This includes the supplied Sai, Kakashi, Shikamaru, Choji, Shino, Kiba, Itachi, Orochimaru, Chiyo, Kabuto, Sasuke, and Sasori screenshots.

Two constrained slots use traceable shortening:

- `[S]Naru/Sasuke` for official `Naruto and Sasuke` in a 16-byte ETC slot;
- `[S]Task` for official `Assignment` in an 8-byte executable slot.

Temari's `姉の喜び` remained unresolved as `M0725` in v32 because no exact official NUN5 English source had yet been verified. It is resolved in v33 after the matching NUN5 screen and binary source were supplied.

### Remaining Collection jutsu and shared battle-name gaps

v32 fills all 16 verified gaps in the Collection ultimate/special-jutsu sequence exposed by the screenshot set, including:

- `Facing the Sunset`;
- `My Rule: One` and `My Rule: Two`;
- `IQ 200` in both verified target copies;
- `Super Human Boulder 2`;
- `Sand Spear Funeral`;
- `Ten Puppets of Chikamatsu`;
- `Puppet: Iron Sand Cluster 2`;
- `Chakra Dissection Blade: Destroy`;
- `Partial Expansion Jutsu 2`;
- `Galium Spurium Dance 2`;
- `Summoning: Rashomon, Abyss 2`;
- `Tongue-Lash Combo 2`;
- `Raining Spider 2`;
- `Earth Style: Terra Shield 2`.

The battle-select/Command Chart shared strings `鹿蝶封結` and `涅槃精舎の術` are also mapped to exact NUN5 `Kachofuketsu` and `Temple of Nirvana Technique`.

No string is relocated and no pointer is rewritten. Every new exact mapping fits its original zero-padded slot; only the four explicitly marked `[S]` rows use manual shortening.

### Packaged table totals

The packaged v32 table contains 2,241 mappings: 2,231 enabled and 10 disabled. Enabled rows comprise 2,135 `slot`, 4 `sequence`, 33 `shorten`, and 59 `unresolved` mappings. All four structural `bytes` rows remain disabled.

All script and generated-artifact path references remain relative. v32 adds no absolute path literals, patched payload files, relocation pools, or target-size changes.

### v32 build validation

A clean-source full build was validated with all three targets selected:

- 2,436 six-column TSV patch rows;
- 2,172 applied text mappings;
- 33 shortened mappings;
- zero active structural patches;
- unchanged target file sizes;
- a relative six-column translation plan in the profile module log;
- `M0745=1` and all new v32 IDs retaining their packaged enabled defaults.

## Version 31 changes

### Character Command Chart expansion

v31 ports the character-specific Command Chart move names by matching the actual table structures instead of searching for isolated Japanese strings.

NA2 contains 74 verified command-record arrays in `SLPS_258.37`. Each record is `0x54` bytes and stores its displayed-name pointer at record offset `+0x08`. NUN5 contains the corresponding per-character pointer arrays in `PRG/TEXTENG.BIN`. The mapping data was expanded only where the NA2 record index and the corresponding NUN5 pointer-table index both reference nonblank text. The Naruto mappings introduced in v28-v30 served as the anchor and were reproduced exactly by this method before it was extended to the other characters.

This adds 1,041 new Command Chart mappings:

- 1,035 exact official NUN5 names that fit their original NA2 slots;
- 6 traceable `[S]` shortenings for the only command names that do not fit;
- no relocation pools, pointer rewrites, or writes beyond original zero-padded string slots.

Together with the 15 already-mapped Naruto entries, v31 covers 1,056 unique command-name targets across the 74 shared character tables. One table contains two NA2/NUN5 presence differences; those unmatched entries remain untouched rather than being guessed.

The six new shortened command names are:

- `[S]Fairy Tale is Real!!`
- `[S]Bamboo Shoot Thrust`
- `[S]Clover Boar`
- `[S]Anesth. Wt.`
- `[S]Clarity Rush`
- `[S]Inst. Blade`

### Ultimate and character-specific jutsu expansion

Ultimate/special-jutsu records use a separate verified `0x14`-byte structure. The first word is the localized name pointer, while the remaining four metadata words are identical between NA2 and NUN5. Matching those four words identifies the official NUN5 name without relying on string order or manual translation.

v31 covers:

- 153 unique executable-side names in `SLPS_258.37`, including all discovered Naruto Ultimate Jutsu entries rather than only `Unchanging Relationship`;
- 146 verified duplicate names in `PRG/ETC.BIN`;
- 152 newly added SLPS mappings and 133 newly added ETC mappings;
- one shortened official name in each target: `[S]8 Trigrams Mountain Break` for `8 Trigrams Mountain Break Attack`.

Three older suffix-only ETC mappings are corrected to their complete official names:

- `64 Palms` becomes `8 Trigrams 64 Palms`;
- `Sand Burial` becomes `Giant Sand Burial`;
- `Wolf Fang` becomes `Wolf Fang Over Fang`.

Previously unresolved `M0718`, `M0719`, and `M0720` are now pointer-verified and active for `Lightning Blade, Single Sharpness`, `Ninja Art: Copy Jutsu`, and `Flying Thunder God Jutsu`.

Three record-selected NUN5 names contain decorative color tags while separate plain official copies also exist in `TEXTENG.BIN`. v31 references those plain official copies because the corresponding NA2 slots contain no verified color-tag form. No English wording is invented.

### Packaged table totals

The packaged v31 table contains 2,180 mappings: 2,170 enabled and 10 disabled. Enabled rows comprise 2,066 `slot`, 4 `sequence`, 29 `shorten`, and 71 `unresolved` mappings. All four structural `bytes` rows remain disabled.

All generated paths remain relative. v31 adds no absolute script paths, no patched payload files, and no relocation behavior.

## Version 30 changes

### Packed multi-string message blocks

Several NA2 dialogs are stored as consecutive NUL-terminated fragments inside one fixed-size region. Earlier mapping versions treated each fragment as an independent fixed slot and zero-filled the remainder of every original fragment. When an English fragment was shorter than the Japanese one, the inserted zero padding created an early empty string and stopped the renderer before later fragments.

v30 adds `sequence` mode for these verified blocks. A sequence mapping:

- reads exact parts from one official NUN5 string;
- writes the selected parts consecutively with one NUL terminator after each part;
- writes one additional NUL after the complete sequence;
- zero-fills only the unused tail of the whole verified block;
- never changes file size or writes outside the declared block.

Generated TSV annotations render the internal separators as `<NUL>` for readability. The literal characters `<NUL>` are not written into the game.

### Memory-card dialog repairs

v30 replaces the broken fragment-by-fragment mappings with four packed sequence mappings:

- `M0857`, `SLPS + 0x3039E0`, exact NUN5 no-card notice from `NUN5_TEXTENG + 0x29060`:
  `No memory card (PS2) is inserted in <br>MEMORY CARD slot 1.<br>Please insert a memory card (PS2) in<br>MEMORY CARD slot 1.`
- `M0813`, `SLPS + 0x303C40`, the lower unformatted-card notice from parts 0 and 1 of `NUN5_TEXTENG + 0x291D0`:
  `The memory card (PS2) in <br>MEMORY CARD slot 1 is unformatted.`
- `M0816`, `SLPS + 0x303CE0`, the separate upper prompt from part 2 of `NUN5_TEXTENG + 0x291D0`:
  `Format memory card (PS2)?`
- `M0829`, `SLPS + 0x3046A0`, the exact startup no-card Yes/No prompt from `NUN5_TEXTENG + 0x29A10`:
  `No memory card (PS2) is inserted.<br>Please insert a memory card (PS2) in MEMORY CARD slot 1.<br>At least 102 KB of free space is necessary to save Naruto Shippuden: Ultimate Ninja 5 data. Start the game anyway?`

Retired fragment rows `M0814`, `M0815`, `M0817`, `M0830`, and `M0831` are removed. Obsolete external enabled-state files are no longer read; the canonical table is authoritative.

### Naruto Ultimate Jutsu name

The visible `変わらない関係` entry is translated with the exact NUN5 name `Unchanging Relationship` from `NUN5_TEXTENG + 0x3F60`.

Both verified NA2 copies are covered:

- `M0858`: `ETC + 0x284C0`
- `M0859`: `SLPS + 0x4AE030`

### Carried-forward repairs

v30 retains all v29 fixes: Options help-line pointer preservation, the first Theater entry restoration, `Charging Kick`, `Clone Jumping Explosion Hit`, relative generated paths, the `M0745` migration repair, original-slot text only, traceable `[S]` shortening, and no relocation pools or pointer redirects.

The packaged v30 table contains 854 mappings: 844 enabled and 10 disabled. Active mappings comprise 745 `slot` rows, 4 `sequence` rows, and 21 `shorten` rows. Seventy-four enabled `unresolved` entries remain documented but unapplied; all four structural `bytes` rows remain disabled.

## Rolling runtime issue log

This log persists unresolved visual/runtime findings across mapping versions. Entries implemented in the current module remain in the verification section until confirmed in-game.

### Implemented in v33, runtime verification required

- **Temari voice title:** verify `姉の喜び` now displays exact NUN5 `Silent Confidence` in the Collection character voice list.

### Implemented in v32, runtime verification required

- **Collection character models:** verify the newly covered mannequin/model animation labels across the supplied roster screenshots, including the short `[S]Long Time!` and `[S]Now` entries.
- **Collection voice/audio lists:** verify the newly covered title entries, especially `[S]Naru/Sasuke` and `[S]Task`; Temari's previously unresolved final entry is covered by v33.
- **Collection jutsu lists:** verify all newly filled numbered/alternate moves, including My Rule 1/2, the second Human Boulder, Iron Sand Cluster, Rashomon, Tongue-Lash, Raining Spider, and Terra Shield entries.
- **Battle select and Command Chart:** verify `Kachofuketsu` and `Temple of Nirvana Technique` replace the two remaining Japanese names in the supplied screenshots.

### Implemented in v31, runtime verification required

- **All character Command Charts:** verify character-specific move names across the roster, not only Naruto, and report any still-visible Japanese name with its character and screen position.
- **Ultimate Jutsu lists:** verify that each character's multiple Ultimate Jutsu names are translated, including Naruto entries beyond `Unchanging Relationship`.
- **Previously partial ETC names:** verify full `8 Trigrams 64 Palms`, `Giant Sand Burial`, and `Wolf Fang Over Fang` text where those copies are used.
- **New `[S]` entries:** verify the eight newly shortened target copies display completely and remain understandable.

### Implemented in v30, runtime verification required

- **Standard no-card notice:** the lower dialog should show the complete exact NUN5 no-card and insertion message instead of mostly Japanese text.
- **Unformatted-card dialog:** the lower notice should show `The memory card (PS2) in MEMORY CARD slot 1 is unformatted.` and the upper prompt should show `Format memory card (PS2)?`.
- **Startup no-card Yes/No prompt:** the complete exact NUN5 prompt should appear instead of stopping after `No memory card (PS2) is inserted in`.
- **Naruto Command Chart:** `変わらない関係` should show `Unchanging Relationship`.

### Carried from v29, runtime verification still required

- **Options, Difficulty Settings:** bottom blue help line should show `Set the Com strength for when in the Free Battle and Practice.`
- **Options, Control Settings:** bottom blue help line should show `Assign button controls.`
- **Collection Movie list:** first entry should show `Reunion Time I` in the correct list position.
- **Naruto Command Chart:** `特攻蹴撃` should show `Charging Kick`.
- **Naruto Command Chart:** `分身跳爆打` should show `Clone Jumping Explosion Hit`.

### Open

- **Startup no-card choice capitalization:** later replace the visible `Yes` and `No` labels with uppercase `YES` and `NO`; intentionally not included yet.
- **Options main-screen graphical labels:** the `Options` logo, difficulty/value, controls, screen, audio, restore, confirm, and back labels remain Japanese in supplied screenshots. They appear to use graphical/CCS resources outside the current text targets and remain untouched pending extracted NA2 and NUN5 assets.
- **Collection Movie screen chrome:** the `Collection` title, `Movie` category heading, and play/back prompts remain Japanese and appear to use graphical/CCS resources outside the current text targets.
- **Collection movie-title fit:** exact NUN5 titles are present, but several extend beyond the visible right edge. They remain unshortened until a requested shortening or verified NUN5 width/scale behavior is applied.
- **Command Chart chrome:** any remaining Japanese heading or back prompt that is graphical rather than string-backed remains outside current scope pending resource extraction.
- **Dynamic save date/time numerals:** retained as unresolved mapping `M0833`; the digits are generated by executable code and still require a verified renderer/code mapping.

PCSX2 application chrome, toolbar text, pause indicators, graphical controller prompts, and emulator toasts are not game translation issues and are not logged here.

## v33 test checklist

1. Export from a clean mapping-version-33 module and confirm the summary reports version 33.
2. Confirm `build_summary.json`, console output, scripts, and documentation contain only relative path references.
3. Preserve external enabled state and verify `M0745=1`; `M0725` must remain enabled and apply as a `slot` mapping.
4. Recheck all 54 supplied Collection screenshots and confirm every v32-covered model-animation, voice-title, and jutsu entry is English.
5. Confirm Temari's final voice-title entry displays exact NUN5 `Silent Confidence`.
6. Verify the four new shortened entries visibly retain `[S]` and fit their fixed slots: `Long Time!`, `Now`, `Naru/Sasuke`, and `Task`.
7. Verify `Kachofuketsu` appears in both the battle-select and Command Chart contexts using the shared target string.
8. Verify `Temple of Nirvana Technique` appears in the battle-select entry.
9. Recheck v29-v31 Options, Theater, save/load, memory-card, Naruto, and roster-wide Command Chart fixes for regressions.
10. Generated TSV validation: exactly six columns, fixed-size patches only, relative summary reference, no active overlap, unchanged target file sizes, and successful composition with the current Font package.

## Integration expectations

- The repository-owned engine, live mappings, and documentation all live in `na2_patcher/modules/translation/`.
- Do not replace the integrated module by extracting a legacy builder archive over the project.
- Do not copy generated profile-log plans back into the module.
- Do not add patched `BTL.BIN`, `ETC.BIN`, or `SLPS_258.37` payloads to the translation module or checkpoint commits; binary deliverables belong only in the frozen release archive.
- The profile orchestrator owns composition and ISO application.
- Translation is an ordered first-class module and is currently applied after the font overlay and raw menu patch so conflicts are checked against their composed bytes.

The module has no standalone CLI. Target selection belongs to the hash-pinned profile.
