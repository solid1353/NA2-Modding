# NA2 Translation Package Builder v26

This builder generates one post-composition translation TSV for Naruto: Narutimate Accel 2. It never packages replacement BIN or ELF files. The surrounding NA2 pipeline composes selected packages first and then applies the generated TSV over the composed files.

Project-level scripts are not included. This archive contains only `translation_package_builder`.

## Source and target scope

Clean NA2 targets:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`
- `SLPS_258.37`

Official UN5 sources:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`
- `PRG/TEXTENG.BIN`
- `SLES_556.05`

All emitted English text is read from exact UN5 offsets at build time. `mappings.tsv` and the Python builder contain no hardcoded translated prose. The paired executable disassemblies were used to identify structures and call sites, but are not needed at runtime and are not included.

## Mapping file and `enabled` flag

`mappings.tsv` is in the builder root. Its first column is the numeric flag `enabled`:

- `1`: apply the row.
- `0`: skip the row completely and record it under `disabled_mappings` in `build_summary.json`.

Use `0` to disable a suspicious row or an entire rollback group without deleting mapping data. TSV has no portable checkbox metadata, so it cannot natively display checkboxes; `0`/`1` is the reliable representation in text editors, scripts, and spreadsheet applications.

The columns, in order, are:

`enabled`, `mode`, `target`, `target_offset`, `capacity`, `source`, `source_offset`, `pool_offset`, `pool_capacity`, `runtime_base`, `pointer_offsets`, `transform`, `arg1_source`, `arg1_offset`, `arg2_source`, `arg2_offset`, `expected_hex`, `replacement_hex`, `reason`

Row modes:

- `slot`: copy one NUL-terminated official UN5 string into a verified fixed-capacity NA2 slot.
- `pool`: write official UN5 text into a verified relocation pool and rewrite the listed target-file pointers.
- `bytes`: apply a size-preserving structural byte patch after verifying `expected_hex` exactly.
- `unresolved`: retain a known NA2 target for which no safe official-source mapping has been proven.

Supported source transforms are structural operations over strings read from UN5:

- blank: use the official string unchanged.
- `format_arg1`: substitute official `arg1` for `%1`.
- `format_args`: substitute official `arg1` and `arg2` for `%1` and `%2`.
- `format_prefix_arg2`: substitute `%1`, then keep the official template prefix before `%2`.
- `format_suffix_arg2`: keep the official template suffix after `%2`.
- `empty`: emit only a NUL terminator for a deliberately empty assembly fragment.

These transforms are used for source-derived dialog assembly. They do not contain English prose.

## Output

Each run creates:

`translation_package_builder\work\runs\<UTC+3 run id>\`

containing:

- `NA2_APPLY__TRANSLATION__<run id>.tsv`
- `build_summary.json`

The generated translation TSV still contains exactly six columns:

`path`, `offset`, `expected_hex`, `replacement_hex`, `source_text`, `replacement_text`

Readable text patches populate the text columns. Pointer writes, pool clearing, and structural code patches leave them empty.

## Safety behavior

Known clean-source SHA-1 values are checked by default. `-NoStrictHash` disables that check only for deliberate experiments.

The builder rejects malformed flags, invalid offsets, malformed source strings, overlapping fixed slots, unexpected code bytes, invalid pointers, undersized pools, and unverified named-color conversions. Fixed-slot text that does not fit is skipped and logged rather than overrunning adjacent data.

Official Western text is read as Windows-1252 so the original UN5 byte stream, including characters such as the DUALSHOCK registered mark, can be preserved. NA2 target text is still decoded as CP932 for target-side markup inspection.

`build_summary.json` records hashes, patch counts, disabled rows, runtime skips, unresolved mappings, and structural byte-patch counts.

## Markup handling

NA2 and UN5 share inline markup, but named color aliases differ in some renderers. The target slot remains the authority:

- UN5 `<WHITE>` becomes NA2 `<colorFFFFFF>` when that target uses it.
- UN5 `<BLACK>` remains `<BLACK>` when the target uses it, or becomes `<color000000>` when that is the verified target form.
- `<RED>` is retained only when the target also uses `<RED>`.
- Generic color, icon, line-break, and other shared tags are preserved.

No tags are stripped merely because they are inconvenient. If no verified NA2 equivalent exists, the mapping is rejected.

## Version 26 changes

v26 continues from the accepted v25 baseline.

### Practice, Free Battle, and Command Chart

- Added the official Opponent Settings Status help text.
- Mapped `Random` from its exact UN5 executable offset.
- Redirected the four ON/OFF targets to exact uppercase ASCII UN5 offsets.
- Added official `Guard`, `Flee`, `Taunt`, `(Hold)`, and `or` mappings.
- Corrected `Recovery` to the official `Rebound` source.
- Relocated the full official Flee directional instruction and rewrote its pointer.
- Rebuilt Practice/Free Battle confirmation assembly from official UN5 templates and official mode labels.
- Added four verified MIPS instruction-word changes so the two direct Free Battle quit paths use the source-derived full sentence instead of concatenating incompatible fragments.
- Added the real spaced-Yes target used by Shop/Collection; the existing Practice/Free Battle Yes mapping remains active.

### Options and save/load

- Added the five runtime Options description strings, preserving their verified color markup.
- Added verified runtime save/load strings: save prompt, load-selection prompt, load confirmation, load-completed message, save-location prompt, and Play Time.
- `Unused`, Next, OK, and Back were not mapped because no verified corresponding runtime target/source pair was proven for those screenshots. Their visible forms may be graphical or generated.

### Shop

- Corrected the final Shop help slot from 160 to 112 bytes. The old size erased the nine-entry help pointer table at `ETC.BIN + 0x2F4D0`; v26 stops exactly at that table.
- Added verified Shop-list copies for Sai, Tenten, Temari, Sasori, Jiraiya, Shizune, Yamato, and Haku.
- Added the spaced Yes target used by the Shop/Collection confirmation UI.
- Money, Ryo, and Points were investigated. Runtime strings with similar wording exist elsewhere, but no verified Shop-HUD target slots were found. No unrelated mappings were added; those labels remain outside v26.

### Collection

- Added the seven captured Movie-list titles.
- Added the eleven captured Character-list titles.
- Relocated The Boar-Deer-Butterfly Trio into a verified ETC zero pool because its original slot is too small.
- Built Quit Collection? from the official generic UN5 Quit template plus the official Collection label.

## Rollback ledger

Every v26 mapping change has a `reason` beginning with `V26_`. Filter the final column to find a group. Set `enabled` to `0` for all rows in a group to suppress that group on the next build.

Main groups:

- `V26_OPPONENT_STATUS_HELP`
- `V26_RANDOM`
- `V26_ASCII_ON_OFF`
- `V26_COMMAND_LABELS`
- `V26_FLEE_HELP_RELOCATION`
- `V26_REBOUND`
- `V26_DIALOG_*`
- `V26_OPTIONS_HELP`
- `V26_SAVE_LOAD`
- `V26_SHOP_HELP_BOUNDARY`
- `V26_SHOP_NAMES*`
- `V26_COLLECTION_MOVIES`
- `V26_COLLECTION_CHARACTERS*`
- `V26_COLLECTION_EXIT`

The three old v25 dialog-fragment rows are retained with `enabled=0` and reason `V26_DISABLED_LEGACY_DIALOG_FRAGMENT`. To restore the exact v25 dialog method, disable every `V26_DIALOG_*` row and re-enable those three legacy rows. The accepted v25 archive remains the complete builder-level fallback if the new parser or transform support itself must be rolled back.

`V26_SHOP_HELP_BOUNDARY` can be disabled safely; doing so leaves the clean Japanese target and its pointer table intact. Do not restore the old 160-byte capacity unless deliberately reproducing the v25 pointer-table corruption.

## Deliberately logged for later

These are rendering tasks, not reasons to alter official text:

- identify and port UN5 automatic fit-to-width behavior;
- Chakra Charge Gauge instruction beginning with `1+...`;
- long Substitution Jutsu, Flee, Extra Hit, Shadowblur, Options, Collection, and confirmation text;
- investigate fullwidth SJIS numeric characters and map them to verified UN5 ASCII numeric sources only where structurally correct.

Until that renderer work is done, preserve exact UN5 strings. Do not shorten them or insert manual line breaks.

## v26 test checklist

Test these screens before accepting v26:

1. Opponent Settings: Status help is English; Linked Attack shows Random; ON/OFF are compact uppercase ASCII.
2. Practice/Free Battle confirmations: return to Character Select and Game Mode Select for both modes; direct Quit Battle in Free Battle; Yes and No choices; no mixed Japanese/English assembly.
3. Command Chart: Guard, Flee, Taunt, `(Hold)`, `or`, Rebound, and the full Flee instruction. Verify Charge Chakra remains correct.
4. Options: all five bottom descriptions are English, colors render correctly, and no literal `<WHITE>` or other tag appears.
5. Save/load: save prompt, load selection, load confirmation, load completed, save-location prompt, and Play Time. `Unused` and graphical controls are expected to remain unchanged in v26.
6. Shop: visit every Shop section and verify the blue help strip is present; check all eight newly mapped names; open the quit dialog and verify Yes/No. Money/Ryo/Points are expected to remain unchanged.
7. Collection: Movie titles, Character titles on both captured pages, and Quit Collection? with Yes/No.
8. Stability: enter and leave each affected screen repeatedly, verify no white screen or crash, and verify unrelated v25 translations and font behavior did not regress.

## Direct use

```powershell
& '.\translation_package_builder\build_na2_translation_package.ps1'
```

Default target selection is `BTL,ETC,SLPS`. `ELF`, `SLES`, and `EXE` alias `SLPS`; `ALL` selects all targets.
