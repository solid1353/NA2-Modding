# Translation importer history

Historical mapping-version notes, runtime follow-ups, and validation
checklists are kept here so the current importer contract remains concise.

## Version 44 changes

### Final-acceptance Collection selector

The matched final-acceptance slot-1 savestates show the Collection ->
Characters screen with the official NUN5 `Opponent` selector label and the
same field still Japanese in Current. Version 44 adds `M0550` for the exact
clean source `<r対戦相手|たいせんあいて>` at `NA2_ETC@0x2EE50`, using the
exact official `Opponent` donor at `NUN5_TEXTENG@0x778` and the concrete
`Collection > Characters > selector label` display context.

The paired Current screen also shows `Flying Thunder God Jutsu` overflowing
the right panel while NUN5 wraps the same official text. `M0720` remains
unchanged: the translation itself is correct, and per-caller wrapping or
auto-fit belongs to the separate layout path rather than canonical string
content.

Version 44 contains 2,051 enabled mappings: 2,047 slots and four sequences.
`M0550` fits inline, so external placement remains 31 mappings and 33 pointer
edits, the generated `PRG/228.BIN` remains 1,776 bytes, and the compiled
translation package contains 2,288 binary edits. `M0537` remains the sole user
override; there are no shortened, unresolved, or prefixed rows.

## Version 42 changes

### Final-acceptance Mode Select confirmation

The matched final-acceptance slot-2 savestates prove that the Mode Select
return confirmation uses the previously omitted `M0549` source at
`NA2_SLPS@0x4B1E00`. Version 42 restores that one row with the exact official
`NUN5_TEXTENG@0x1C90` donor, `Return to Title Screen?`, and the concrete
`Game Mode Select > return confirmation` display context.

This is deliberately separate from `M0804`, the Save/Load prompt whose
official donor uses lowercase `title screen`, and `M0557`, the shorter
Character Select source. The slot-2 Current capture translated the shared
`Yes` / `No` choices but retained this prompt in Japanese, which confirmed that
the missing source row—not the generic modal choices—was the defect.

Version 42 contained 2,050 enabled mappings: 2,046 slots and four sequences.
Every row had display metadata and no shortened, unresolved, prefixed, or
user-override rows. `M0549` fits inline, so the existing 31 external mappings,
33 pointer edits, and 1,776-byte `PRG/228.BIN` remained unchanged. The
compiled translation package contained 2,287 binary edits.

## Version 41 changes

### Evidence-scoped from-scratch rebuild

Version 41 rebuilds the executable table from zero using the diagnostic
mapping-ID screenshots, the paired savestate library, exact clean NA2 bytes,
and the archived v40 table as reference rather than presumed coverage. Every
one of the 2,049 executable rows now declares a concrete `display_context` and
one stable evidence basis:

- `seen:` for strings visible in the diagnostic screenshots or paired
  savestates;
- `inferred:` for hidden members of a proven selector, running-help, or shared
  screen table;
- `character:` for structurally proven character names, Ultimate Jutsu names,
  Command Chart moves, figure-animation titles, and voice titles.

The rebuild retains 2,048 v40 rows, adds `M2247` for the confirmed Battle HUD
`MAX` label, and removes 124 previously active rows that had no confirmed
display location. Removed content includes the unvisited Ultimate Battle and
inventory blocks, unvisited alternate mode branches, unused generic
choice slots, and the unmatched voice title `M0523`; those clean Japanese bytes
remain untouched.

Three incorrect character-family matches are corrected:

- plain Kankuro `M0246` now uses exact NUN5 `Kankuro` from
  `NUN5_SLES@0x513D88`, not `Kankuro (Classic)`;
- `M0521` now uses `Provocation` from `NUN5_TEXTENG@0x2B18`;
- `M0522` now uses `Contrasting Pair` from `NUN5_TEXTENG@0x2B30`.

All 2,049 source declarations exactly match the clean NA2 targets. All 2,049
donor declarations were independently checked against their NUL-terminated
NUN5 bytes after the specified fullwidth-ASCII normalization, with zero
mismatches. The table has 2,045 slots, four sequences, 32 pointer-inventory
rows, three parent-message rows, no prefixes, and no user overrides.

After project-title policy, 31 mappings are linked externally through 33
guarded pointer edits. The payload contains 29 logical rows at 28 distinct
strings, uses 1,470 encoded bytes, and produces a `0x6F0`-byte `PRG/228.BIN`
with SHA-256
`84DD5C72F4B7D7A472EE2E3C69FBB92621A806E04116D281ED734AE61F5D02EF`.
The compiled translation package contains 2,286 binary edits.

## Version 40 changes

### User-editable translation schema

Version 40 makes the mapping table describe translation ownership directly.
The clean NA2 location is one `source_ref`; optional pointer sites are one
`reference_refs` list. Source and donor references are adjacent, as are source
and donor text. Historical per-row `reason` labels were removed because they
did not define executable mapping policy; generated patch logs now synthesize
specific reasons from stable mapping IDs.

The official donor is executable by default. `replacement` is blank unless the
user intentionally overrides that donor, and `prefix` is a separate
user-editable field prepended to the transformed result. The current 2,177-row
table keeps the same 2,172 enabled and five disabled mappings while using 2,176
blank replacements, one explicit override, 27 declared transforms, and no
current prefixes.

Focused importer and string-patcher validation reproduced the preceding
composition exactly: generated `PRG/228.BIN` remains `0x700` bytes with SHA-256
`36CFF1341AC14A5AC6DCE5D6640F4F082676CF576851E0BEAF393207C3EE16FB`,
and the compiled package remains 2,434 edits.

## Version 39 changes

### Canonical-table and placement refactor

Version 39 consolidates mapping semantics, provenance, and pointer references
into one `mappings.tsv`. It removes the separate `references.tsv`, the four
disabled structural-byte rows, the `shorten` mode, and every `[S]` fallback.
The table now contains 2,177 mappings: 2,172 enabled and five disabled. Enabled
rows comprise 2,168 `slot` and four `sequence` mappings.

Every row stores its observed NA2 `source`, exact NUN5 `donor_ref` and `donor`,
and complete executable `replacement`. Source and donor fields are
informational. Historical donor transforms were materialized into replacement
text; only three parent-message `split_br` views remain.

After profile title policy is applied, `string_patcher` encodes each final
replacement. A slot that fits is compiled inline. An overflowing slot is linked
externally only when that same row declares validated pointer references;
otherwise the build fails. Sequences must fit inline. This makes placement a
deterministic build result rather than stored mapping state.

The current clean build derives 32 external mapping rows, 34 pointer edits, and
30 logical external messages at 29 distinct symbols. The one formerly
externalized mapping whose full replacement fits (`M0743`) is now inline.
Generated `PRG/228.BIN` is `0x700` bytes with SHA-256
`36CFF1341AC14A5AC6DCE5D6640F4F082676CF576851E0BEAF393207C3EE16FB`.
The compiled package remains 2,434 edits.

A committed-HEAD versus refactored byte-parity reconstruction confirmed that
no translated output changed. Target-file differences are limited to the new
inline `M0743` slot, removal of its old redirect, and shifted external pointer
addresses after that string left the compact pool. All other inline replacement
bytes match the preceding pipeline.

## Version 38 changes

### Restore shared modal-label capitalization

Version 38 restores `M0566` and `M0799` to the exact official NUN5 donor text,
`No` and `Yes`. Runtime testing showed that the attempted uppercase forms did
not control the supplied startup prompt, and these slots are generic modal
labels rather than startup-specific presentation. Applying a global uppercase
transform here would therefore alter unrelated dialogs. The unused `uppercase`
transform is removed from the importer.

The v37 project-title policy remains unchanged: the six guarded title-bearing
mapping results still materialize `Narutimate Accel v2.28`.

The packaged v38 table contains 2,181 mappings: 2,172 enabled and 9 disabled.
Enabled rows comprise 2,135 `slot`, 4 `sequence`, and 33 `shorten` mappings.

## Version 37 changes

### Project title presentation

Version 37 applies one exact, hash-pinned semantic policy after official-source
transforms and before inline or linked placement: the donor token
`Naruto Shippuden: Ultimate Ninja 5` becomes `Narutimate Accel v2.28`. The
guarded coverage is six final mapping results and seven donor-token occurrences:
`M0823`, `M0826`, `M0827`, `M0828`, `M0829`, and `M0832`. The full `M0823`
parent message is policy-resolved separately for the `M0825` continuation, so
both its inline prefix and linked complete message carry the project title.

Raw NUN5 templates remain available as provenance. `mappings.tsv` continues to
store source references and transforms rather than duplicated source/result
sentences; generated logs record the resolved text. Configuration pins the
exact donor token, output token, and expected coverage so source drift or
accidental expansion fails the build.

The supplied side-by-side runtime capture also confirms that the prompt overflow
is separate: NUN5 word-wraps inside donor `<br>` parts, while NA2 renders each
packed sequence fragment as one clipped line. Title shortening reduces that
overflow but does not replace the Font workstream's renderer/autofit fix.

The packaged v37 table still contains 2,181 mappings: 2,172 enabled and 9
disabled. Enabled rows comprise 2,135 `slot`, 4 `sequence`, and 33 `shorten`
mappings.

### v37 build validation

A clean-source full in-memory plan was validated with all three targets:

- the v37 mappings hash, profile title-policy counts, and reference guards matched;
- 2,434 generated import rows and 2,172 applied text mappings;
- all six title-bearing results use `Narutimate Accel v2.28`;
- `M0566`/`M0799` resolved to `NO`/`YES` in v37 (reverted in v38);
- 31 logical external messages occupy 1,512 encoded bytes at 30 distinct symbols;
- generated `PRG/228.BIN` is `0x720` bytes with SHA-256
  `AD94B66F2916C0014A87D110F5807DC0F0F5D7E91615AE3F04EC970CFBA00E9F`.

## Version 36 changes

### Executable-table cleanup and semantic guard

Version 36 removes all 59 non-executable `unresolved` rows. Fifty-seven carried
only `NO_VERIFIED_OFFICIAL_SOURCE_OFFSET`, one retained an obsolete disabled
dialog fragment, and one recorded the dynamic save-date renderer lead later resolved by the
[Font numeric-rendering work](../../knowledge/localization/font/numeric_rendering.md).

`M1336` is also removed. It would have overwritten the clean identifier-like
value `pjrvspl0` at `SLPS_258.37 + 0x3C0660` with the literal NUN5 executable
placeholder `unknown`. No evidence proves that slot is display text, so the
clean NA2 bytes remain authoritative.

The importer no longer accepts an `unresolved` mode. It also fails closed when
placeholder donor text such as `unknown`, `placeholder`, or `dummy` would
replace identifier-like target data. Resolved source and replacement text stay
in generated logs; `mappings.tsv` continues to store source references and
transforms rather than duplicated strings.

The packaged v36 table contains 2,181 mappings: 2,172 enabled and 9 disabled.
Enabled rows comprise 2,135 `slot`, 4 `sequence`, and 33 `shorten` mappings.
The disabled rows are 5 retained `slot` mappings and 4 structural `bytes` rows.

### v36 build validation

A clean-source full in-memory plan was validated with all three targets:

- mapping version 36 and its packaged hash matched;
- 2,436 generated import rows;
- 2,172 applied and changed text mappings;
- 33 shortened mappings and zero active structural patches;
- no `unresolved` rows or active identifier-to-placeholder replacements;
- unchanged `228.BIN` payload bytes and layout.

## Version 35 changes

### Collection Movie exact-source rollback

`M0771` through `M0774` again copy their exact official NUN5 source strings
without an authored `<br>` transform. Version 34 incorrectly treated a
text/font fit issue as part of the Texture-patcher task and inserted line breaks that
were not present in the selected NUN5 bytes. Version 35 restores the prior
source-derived mappings exactly; any remaining overflow belongs to separate
text/font work and is outside the Texture-patcher scope.

### v35 build validation

A clean-source full in-memory plan was validated with all three targets:

- mapping version 35 and the packaged mapping hash matched the README;
- 2,437 six-column TSV patch rows;
- 2,173 applied and changed text mappings;
- 33 shortened mappings;
- zero active structural patches;
- all four Collection Movie rows retained their exact NUN5 source strings and
  contained no authored `<br>` transform.

## Version 34 changes (superseded by v35)

### Collection Movie line wrapping

Four exact official NUN5 movie titles already fit their original NA2 executable
slots but NA2 rendered each title as one clipped line. NUN5's `ETC.BIN`
contains an additional Movie-specific construction path using
`ccHomeIspMovie`; the NA2 homolog does not invoke that path. Porting the whole
overlay routine would also import unrelated object-layout and renderer-call
changes.

`M0771` through `M0774` used `insert_br_after_words` to preserve every word
from their existing exact NUN5 source references while reproducing the line
breaks visible in the official NUN5 screen:

- `Sealing Jutsu: Nine<br>Phantom Dragons`
- `People of Endless<br>Darkness`
- `Ninja Art: Beast<br>Scroll Replicas`
- `Fourth Awakened<br>Mode`

The transform accepts only a valid single-space word boundary. All four results
fit their existing fixed slots; no shortening, relocation, pointer rewrite,
overlay edit, or target-size change was used. Runtime review rejected this
authored text change, so v35 removes it.

### v34 build validation

A clean-source full in-memory plan was validated with all three targets
selected:

- mapping version 34 and the packaged mapping hash matched the README;
- 2,439 six-column TSV patch rows;
- 2,173 applied and changed text mappings;
- 33 shortened mappings;
- zero active structural patches;
- all four Collection Movie replacements contained the declared `<br>` at the
  official word boundary and remained inside their original slots.

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
- a relative ten-column import inventory in the profile module log;
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

### Reverted in v38

- **Generic modal choice capitalization:** the v37 uppercase transforms on
  `M0566` and `M0799` did not affect the supplied startup prompt and were
  semantically wrong because the slots are shared modal labels. Version 38
  restores exact official NUN5 `No`/`Yes`; do not repeat the global transform.

### Rejected in v34 and rolled back in v35

- **Collection Movie authored line breaks:** removed from `M0771` through
  `M0774`; any remaining fit issue is separate text/font work.

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

- **Options main-screen graphical labels:** owned by the separate Texture-patcher and
  layout task; they remain outside this text module.
- **Collection Movie screen chrome:** graphical title/category and button assets
  are owned by the separate Texture-patcher task and remain outside this text module.
- **Command Chart chrome:** any remaining Japanese heading or back prompt that is graphical rather than string-backed remains outside current scope pending resource extraction.

PCSX2 application chrome, toolbar text, pause indicators, graphical controller prompts, and emulator toasts are not game translation issues and are not logged here.

## v35 test checklist

1. Build from a clean mapping-version-35 module and confirm the summary reports version 35.
2. Confirm `build_summary.json`, console output, scripts, and documentation contain only relative path references.
3. Preserve external enabled state and verify `M0745=1`; `M0725` must remain enabled and apply as a `slot` mapping.
4. Recheck all 54 supplied Collection screenshots and confirm every v32-covered model-animation, voice-title, and jutsu entry is English.
5. Confirm Temari's final voice-title entry displays exact NUN5 `Silent Confidence`.
6. Verify the four new shortened entries visibly retain `[S]` and fit their fixed slots: `Long Time!`, `Now`, `Naru/Sasuke`, and `Task`.
7. Verify `Kachofuketsu` appears in both the battle-select and Command Chart contexts using the shared target string.
8. Verify `Temple of Nirvana Technique` appears in the battle-select entry.
9. Recheck v29-v31 Options, Theater, save/load, memory-card, Naruto, and roster-wide Command Chart fixes for regressions.
10. Confirm the four long Collection Movie mappings copy their exact NUN5
    source strings and contain no authored `<br>`; text/font fit is outside
    this Texture-patcher task.
11. Generated TSV validation: exactly ten columns, fixed-size imports only,
    relative summary reference, no active overlap, unchanged target file sizes,
    and successful compilation/application through `string_patcher` and the
    current Font package.
