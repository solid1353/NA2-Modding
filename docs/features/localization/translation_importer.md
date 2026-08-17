# NA2 translation importer

This first-class `na228_builder` module imports and validates strings for
**Narutimate Accel v2.28**, based on *Naruto Shippuuden: Narutimate Accel 2*.
It never writes BIN or ELF payloads. Configuration builds pass its canonical in-memory
artifact to `string_patcher`, which applies selected semantic string patches, derives
inline versus linked placement from encoded fit and pointer availability, and
compiles one shared `binary_patcher` package. There is no standalone export
command or file-backed inter-stage handoff.

Durable structural evidence, semantic boundaries, and rejected approaches are
in [translation importer knowledge](../../knowledge/localization/translation_importer.md).

## Mapping metadata

- Canonical `mappings.tsv` rows: `2,080`
- Canonical `mappings.tsv` SHA-256: `FDE2D2C536B0021E2371B4F182E9E54FCEF0E42020AF6026263E16A8E65E2D44`

The hashes above are documentation, not a second executable manifest. Git
history and the builder's configuration-resource fingerprint own content identity.
`mappings.tsv` owns the canonical executable donor translations, overrides,
and optional pointer inventory. Normal builds import only `mappings.tsv`. Root
`catalog/implementation/string_patches.json` owns the guarded imported-title
declaration, while root `settings.title` supplies its replacement;
`string_patcher` applies that selected operation to the normal translation path.

## Source and target scope

Clean NA2 targets:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`
- `SLPS_258.37`

NUN5 donor references and donor text are retained in the table for review,
provenance, and executable translation. Normal builds do not read donor
binaries: the verified `donor` text in the table is the default translation.
A nonempty `replacement` is a user-editable override, and `prefix` is a
user-editable string prepended to the selected translation. Official donor text
and ordinary overrides remain complete. T30 uses the complete user-authored
`Ultimate` translation and the validated pointer at `NA2_BTL@0x209CB4`; encoded
fit therefore externalizes it automatically.

Treat PCSX2 operator overlays and the underlying game screen as separate
evidence. Compare NA2 and NUN5 memory-card formatting and data-creation flows by
meaning rather than assuming their screen sequences correspond one-to-one. Do
not replace identifiers, placeholders, or data of uncertain display purpose
with arbitrary text.

The translation importer owns game text and its mapping and reference data.
Font owns glyph rendering and fitting; UI layout and texture modules own
graphical assets and their placement.

## Canonical mapping table

`mappings.tsv` is the canonical mapping table used by normal builds.
`display_context` is its human-readable page/filter key; rows are sorted by
that context, then by stable `id`.

The 16 columns are:

`id`, `enabled`, `display_context`, `source`, `donor`, `prefix`,
`replacement`, `display_basis`, `source_ref`, `donor_ref`, `mode`,
`capacity`, `transform`, `arguments`, `reference_refs`, `parent_mapping_id`

### Stable IDs and enabled state

- `id` is a stable mapping identifier.
- `enabled=1` imports the row for downstream `string_patcher` composition.
- `enabled=0` retains the row without applying it.
- `mappings.tsv` is the only enabled-state source. Configuration builds never rewrite it
  or inherit flags from external state.
- Changing an enabled flag changes the canonical module input and therefore
  requires an explicit configuration-resource hash update.
- The current evidence-scoped table contains only executable rows, so all
  current rows are enabled. Unconfirmed rows are absent instead of retained as
  disabled inventory.

Canonical `mappings.tsv` contains `T#` rows confirmed visible by the paired
screenshot pass plus the explicit character-family exception, sorted by
`display_context` and numeric ID. Its cumulative first two passes have 752
unique enabled rows: 567 from the
hash-verified first-pass corpus and 185 from the second. The verified 74-table
Command Chart family adds 1,041 rows, including Naruto moves absent from the
captured 14-row subset. A subsequent missing-row audit adds another 260
policy-supported rows: 53 directly seen rows, 10 structurally inferred
siblings, and 197 character-family rows, for 2,053 total rows. Exact source,
source reference, mode, and capacity are guarded by the canonical row
declarations. T2042, T2045,
and T2050 use canonical parent IDs `T2011`, `T2043`, and `T2048`.
Paired screenshots correct three reference-table errors: T1956 uses `Off` at
`NUN5_SLES@0x513EF8`, T1957 uses `On` at `NUN5_SLES@0x513EFC`, and T2158 uses
`Warning` at `NUN5_SLES@0x513F38`.

Six Difficulty-family rows are matched by meaning: T27 `Simple`, T1983 `Easy`,
T28 `Normal`, T1984 `Hard`, T29 `Insane`, and T50 `Difficulty`. The full T50
label links through the exact pointer at `NA2_BTL@0x20A264`. T24 reuses the
official Jump-mode help text. Paired screens correct T637 to `Hidden Leaf
Village`, T638 to `Hidden Leaf Gate`, T744 to `Faint Unease`, and T767 to
`Silent Confidence`. The paired Practice ss5 comparison corrects T1920's
displayed title to `Charge Chakra`; the retained `Charge` donor is incomplete
for this NA2 slot, so the complete visible title is stored as its override.
T30 is the sole donorless row and uses user-authored
`Ultimate`, externalized through `NA2_BTL@0x209CB4`. Donor-backed rows otherwise
leave `replacement` blank and execute independently validated official donor
text. NUN5 stores visible quotation spans as paired `@...@` delimiters. The
importer normalizes that donor convention centrally to ASCII quotation marks
before transforms or placement and rejects row-level overrides for the family.
T1958 retains the established Cross-confirm override.
The paired Ninja Song passes add 25 displayed numeric/status/bonus fields, and
the paired ss7 Movie pass adds the locked-title placeholder. This
is an evidence-scoped English table, not a claim that uncaptured screens are
covered.

The canonical table closes every admitted multi-slot `<br>` message family.
T2011/T2041/T2042 cover all four save-progress message parts, while
T2014/T2015 cover both overwrite-confirmation parts. Import fails closed on
missing, duplicate, out-of-range, or inconsistent structured parts so a linked
first line cannot continue into an unrelated resident-payload string.

### Modes

- `slot`: compile one replacement as a NUL-terminated string, inline when it
  fits or externally when it overflows and has validated pointer references.
- `sequence`: pack the `<NUL>`-delimited replacement fragments into one
  verified NA2 multi-string block. Sequences must fit inline.

Unresolved research does not belong in accepted executable `mappings.tsv`.

There is no `shorten` or `pool` mapping mode. External placement is a
`string_patcher` build decision, not canonical mapping state.

### References, text, overrides, and transforms

`source_ref` and `donor_ref` are adjacent provenance fields using
`SOURCE@OFFSET`, for example `NA2_BTL@0x1E2130` and
`NUN5_TEXTENG@0x29430`. `source` and `donor` are adjacent text fields: `source`
records the exact guarded clean NA2 text, while `donor` records the verified
official translation and is executable by default. `display_context` names the
screen and field where the row appears. `display_basis` contains one or more
`|`-separated entries beginning with `seen:`, `e2e:`, `inferred:`, or
`character:` and records why that row is admitted to the executable table.
`e2e:<suite-name>` identifies each exact maintained E2E suite that exercised
the row, for example `e2e:collection/voice`. Coverage summaries count every
entry independently, so a shared row contributes to each proven suite.

`replacement` is a user-editable override field and is normally blank. The
importer selects nonempty `replacement` or otherwise `donor`, applies the
declared transform, then prepends the user-editable `prefix`. For sequence rows,
the prefix is applied to the first resulting fragment. Most rows require no
transform. Paired `@...@` spans in official NUN5 donor text are decoded as
quotation marks by the importer before those operations; the raw `donor` and
`donor_ref` remain unchanged as provenance.

`reference_refs` stores optional comma-separated pointer sites in the same
`SOURCE@OFFSET` form. `parent_mapping_id` lets a continuation row reuse its
containing mapping's pointer inventory. Canonical mappings do not carry log
reasons; generated patch records derive a concrete reason from the mapping ID
and whether the row used the official donor, an override, or a prefix.

Two or more `slot` rows may share a clean source slot only when exactly one is
the ordinary inline mapping and every alternate row owns pointer references.
Those pointer-specific aliases are always linked, even when their text would
fit inline, so one shared Japanese string can retain distinct official donor
selections at structurally distinct records. Aliases must declare identical
source text and capacity, and none may redirect the source slot itself.
An empty shared slot may instead contain only pointer-specific aliases; every
alias is linked and the empty inline storage remains untouched.

## Output

Each configuration build records the translation importer under:

`logs/na228/builds/<build-id>/<module-id>/`

containing:

- `translation_imports.tsv`
- `translation_import_summary.json`

The generated import TSV contains exactly ten columns:

`import_id`, `group_id`, `path`, `offset`, `expected_hex`, `replacement_hex`,
`source_text`, `replacement_text`, `source_mapping_id`, `reason`

All ISO target paths inside the TSV remain ISO-root-relative. The configuration-level module inventory also records only repository-relative paths.

`translation_import_summary.json` contains general and aggregate information:

- mapping version and selected targets;
- patch and mapping totals;
- active mapping coverage grouped by mode and display context;
- source and translated-file hashes.

The current table contains no disabled rows.

## Safety behavior

Known clean-source SHA-1 values are always checked. Unknown source media is rejected before a plan is produced.

The module rejects malformed flags, duplicate IDs, missing or invalid display
metadata, invalid offsets, invalid source or donor references, source text that
does not exactly match the clean target, malformed pointer-reference lists,
malformed transforms, overlapping active mappings, unexpected structural
bytes, text exceeding its declared slot or sequence block, malformed target
sequences, invalid named-color conversion, and placeholder donor text that
would overwrite identifier-like NA2 data. Enabled bad mappings fail the build
instead of becoming silent runtime skips. Fullwidth ASCII-compatible donor,
prefix, override, and transform output is normalized to ASCII before encoding;
CP932 source guards are not normalized.

### Exact slot boundaries

A text mapping's `capacity` must end inside zero padding belonging to that string. The module rejects a declared slot if any nonzero byte appears after the original NUL terminator within that capacity. This prevents a text write from zero-filling adjacent pointer tables or other structural data.

This check directly guards against both v28 regressions fixed in v29:

- `M0776` crossed from the `Credits` string into the Collection movie-pointer table at `SLPS + 0x2FFD1C`.
- `M0792` crossed from the difficulty-reset result string into the Options navigation table at `SLPS + 0x4B2BF0`.

Official Western text is decoded as Windows-1252. NA2 target strings are decoded as CP932 for inspection and markup adaptation. File sizes never change.

## Markup handling

The original NA2 target is authoritative for renderer-specific color forms:

- NUN5 `<WHITE>` becomes NA2 `<colorFFFFFF>` only where that target uses it.
- NUN5 `<BLACK>` adopts a target's existing `<color000000>` form; otherwise it
  remains the native `<BLACK>` token supported by clean NA2 binaries.
- `<RED>` is retained only where the target supports it.
- Other shared color, icon, line-break, and control tags are preserved.


## Integration expectations

- The reusable engine lives in `na228_builder/modules/translation_importer/`; this feature-owned directory contains the live mappings and their documentation.
- Do not replace the integrated module by extracting a legacy builder archive over the project.
- Do not copy generated configuration-log plans back into the module.
- Do not add patched `BTL.BIN`, `ETC.BIN`, or `SLPS_258.37` payloads to the importer or checkpoint commits; binary deliverables belong only in the frozen release archive.
- `string_patcher` owns conversion of imported rows into enabled BTL,
  ETC, and SLPS patches; `binary_patcher` owns guards, conflicts, writes, and logs.
- The configuration orchestrator owns composition and ISO application. The importer
  must run immediately before its consuming `string_patcher` instance.

The module has no standalone CLI. Mapping `enabled` flags determine imported
targets, and enabling the Localization feature invokes the complete importer.
