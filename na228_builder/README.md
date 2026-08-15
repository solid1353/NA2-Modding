# NA2.28 builder

The builder creates a reproducible product from one configuration and the
integrated catalog data.

## Canonical data

- `catalog/*.modcat` owns the complete nested selectable hierarchy. Each file
  is named for one direct child of the logical `features` root. The custom
  declarative syntax uses JSON-like objects and TypeScript-like value types and
  is parsed directly by the Python builder.
  [`CATALOG.md`](CATALOG.md) is the complete authoring and
  configuration-semantics reference.
- Catalog settings contain their descriptions and one `patches` array. IDs
  beginning with `e__` resolve to guarded edits; IDs beginning with `i__`
  resolve to injection units; IDs beginning with `s__` resolve to semantic
  string patches. Implementation details never appear in the release catalog
  reference.
- `catalog/implementation/edits.json` is the direct root map of guarded binary
  edit definitions. A typed setting may feed its validated value to a declared
  binary adapter instead of storing a fixed `replacement_hex`. A bare setting
  may also select an adapter-backed fixed edit whose readable expected and
  replacement values are encoded by the adapter.
- `catalog/implementation/injections.json` is the direct root map of runtime
  injection units. Each unit contains `hooks`, `payload`, or both.
- `catalog/implementation/string_patches.json` owns semantic transformations
  performed by the string patcher before inline and external string layout.
- `configurations/base.json` contains the complete shared `features` tree.
  `dev.json`, `test.json`, and `release.json` contain
  concrete `overrides`. Each overrides object may be empty or partially mirror
  the catalog's feature tree directly. The loader applies the concrete
  configuration's `overrides` to `base.features`. Normal local builds use
  `dev.json`; Manual, worker, and E2E builds use `test.json`; only
  release packaging uses `release.json`.
- `configurations/base.character_overrides.tsv` contains the required `base`
  row and shared per-character overrides. Matching `dev`, `test`, and `release`
  TSVs layer nonempty cells over it by character ID. Empty cells inherit;
  numeric zero is an explicit value.
- `resources/character_data.tsv` is the builder-owned ID/name and native-value
  reference used to validate character rows and Practice bootstrap inputs. Its
  `support_id` cells contain the native support-roster ID corresponding to each
  playable character, written in hexadecimal; an empty cell means that the
  character has no native support entry. Its
  `awakening_ids` cells contain comma-separated native IDs such as
  `0x61,0x62`. They are the union of the character's fighter-controller effect
  associations, nonempty Ultimate-Jutsu post-effects, and hard-coded
  transformed-form initialization effects, so membership does not imply a
  particular activation route; an empty cell means none of those native sources
  supplies an effect. `linked_uj` and `linked_jutsu` contain the native
  support IDs associated with each character by the corresponding BTL tables;
  empty cells mean no relationship of that type. It is not an override file.
- `catalog/implementation/targets.tsv` is the single target registry used by
  edits and injection hooks.
- `modules/binary_patcher/operations/*.tsv` defines the allowed fields and basic types for each binary operation.
- `localization/assets/` owns edit-referenced localization binary assets.
- Enabling `features.localization` includes the retained translation-importer and texture-patcher inputs under `localization/`; they are real inputs, not empty catalog selector nodes.
- `scripts/` contains every builder Python implementation file. Reusable engines and their code-only contracts remain under `modules/`.
- Root `release_manifest.json` owns release packaging metadata and remains
  outside the catalog.
- Root `settings.json` owns the product title, explicit output boot path, named
  build variants, and project launch settings.

JSON configurations select features. The paired character-override TSVs are
the separate per-character build inputs for battle values.

## Edit per-character battle values

1. Put shared defaults and agreed character values in
   `configurations/base.character_overrides.tsv`.
2. Put temporary local values in `dev.character_overrides.tsv`, test-only
   values in `test.character_overrides.tsv`, or release-only values in
   `release.character_overrides.tsv`. Only nonempty cells replace the base
   layer.
3. Keep each numeric `id` paired with the exact `character` name from
   `resources/character_data.tsv`. `base_id` identifies a form's base
   character, and `tier` records the human-readable balance tier. Tier labels
   use at most four ASCII characters because the development Character Select
   overlay reads them from the resident table. Rows retain the order written in
   the base TSV so forms can stay directly below their base characters.
4. Write the `base` row's `substitution_cost` as a literal value such as `2.5`.
   In a character row, write an unsigned value such as `3` for a literal cost,
   `+0.5` to add to the base cost, or `-0.5` to subtract from it. The explicit
   sign is what distinguishes a delta from a literal value.
5. Leave a value cell empty to inherit the lower layer, including its
   literal-or-delta mode. If neither a character nor the `base` row supplies a
   substitution cost, the generated table leaves that value to native game
   behavior. `0` is literal zero; `+0.0` is a zero delta.
6. Save the file as UTF-8 TSV and run the normal build for that profile.

For example, these rows set the base cost to `2.5`, give Naruto a `+2.0`
delta, and give Sakura a literal cost of `3`:

```tsv
id	base_id	character	tier	substitution_cost	hp	damage_multiplier	health_recovery_multiplier	chakra_recovery_multiplier
base		Base		2.5
57		Naruto Uzumaki	S	+2.0
58		Sakura Haruno	A	3
```

The builder rejects unknown IDs, invalid base IDs, mismatched names, duplicate
rows, malformed columns, non-finite numbers, and negative literal values before
composition. Signed substitution-cost deltas may be negative.

## Catalog nodes

Catalog nodes may nest to any depth. A bare `setting` accepts `true` to apply
its patches and `false` to disable it. `setting<T>` accepts a typed scalar or
closed object value. Direct boolean typed settings are forbidden so `true` and
`false` remain unambiguous node controls; boolean data is supplied through an
object such as `setting<{ value: bool }>`.

`false` disables any setting, union, or structural parent before type
validation. Structural parents otherwise require explicit objects; `true`
does not expand a parent. Plain containers merge recursively through
configuration overrides, while settings and node unions replace atomically.
Union branches must be provably disjoint and are never selected by order.
Structural catalog objects may use `&` to declare fields shared by several
object-union branches once; intersected fields must be disjoint. Unconditional
object fields remain recursive merge points in overrides, while the
branch-specific part of an intersected union remains atomic.

The grammar supports `bool`, `int`, `decimal`, and `string`, literal types,
closed object types with optional fields, disjoint `|` unions, structural
object intersections, numeric `&` comparisons, ranges, and steps,
parentheses, `//` comments, and trailing commas. It rejects every unlisted
construct, including `null`.

Binary edit definitions always contain an explicit `operation`. Runtime target
changes live under an injection unit's `hooks` and therefore have no operation
discriminator. Runtime sources, fragments, imports, relocations, and ABI
metadata live under that unit's `payload`. Multiple catalog leaves may
reference the same shared injection unit.

Root edit and injection identities use `e__` and `i__` prefixes. Definition
maps and unordered nested
maps are serialized alphabetically and unit tests enforce that source
convention without making source order a loader requirement. Hook and payload
fragment identities are concise within their owning injection. Payload
fragment numeric `order` values remain explicit, validated declaration data;
final payload placement is deterministic by fragment kind, owner, and semantic
symbol. Edit, injection, and hook descriptions are optional definition-local
documentation; a present description must be nonempty and never affects
execution.

## Internal execution

Reusable engines remain internal under `modules/` and are not represented in catalog or configuration data. The builder derives internal engine invocations in this stable order:

1. `translation_importer`
2. `string_patcher`
3. `runtime_injector`
4. `texture_patcher`
5. `binary_patcher`

The localization importer invokes the string patcher as a derived consumer.
Selected injection payload declarations are compiled and linked into the shared
resident `PRG/228.BIN`; resolved hooks then become guarded in-memory binary
replacements. The binary patcher applies selected edits last.

## Resource fingerprinting

The build-resource fingerprint covers the base and selected JSON and
character-override configurations,
`.modcat` sources, edits, injections, settings and path configuration, shared targets,
the character reference, applicable binary operation definitions, referenced assets and sources, and
selected localization TSV inputs. Release packaging inventories the same
closure for every selectable catalog node, including disabled nodes.
Documentation is not an executable builder input.

## Current release configuration

Feature files are discovered in alphabetical filename order. Module execution
within each feature remains derived from the stable internal engine order above.

Release packaging applies `release.overrides` to `base.features`, then writes
one editable JSON configuration named `config.json` containing only the
materialized `features` tree. It also materializes the layered base and release
character values as editable `character_overrides.tsv` with every reference
ID/name row present, and writes one
consolidated, inert `catalog.modcat`
reference with the same public hierarchy, types, constraints, unions, and
descriptions but no patch mappings or implementation details. `README.md`
explains the editable files in simple terms.

The packaged EXE validates `config.json` against its embedded complete catalog
and never reads the external catalog reference. It contains resources for every selectable
catalog node, including nodes disabled by the default release selection.
Catalog-owned runtime C sources have packaged objects, so end users do not need
the project PS2 toolchain. Invalid configuration errors identify the exact path,
supplied value, and expected type or shape. After a failure, the EXE creates or
replaces `builder-error.log` with full exception details and stack traces rather
than showing them in the user-facing window. Successful runs create no log.

## Build

```powershell
& scripts/na228/build.ps1
```

`scripts/na228/build.ps1` resolves the `builder` package set from
`packages.json` and uses `configurations/dev.json` for normal builds or
`configurations/test.json` for Manual and E2E outputs. Worker builds default to
`test` and accept `--configuration <id>`.

The public `-f` option applies to ordinary Latest and Manual build routes,
including build-only and build-and-run commands. It keeps building when a
non-critical validation or bookkeeping step fails: preflight and retained-record
lookup, configuration/build-record metadata, registry updates, and obsolete
Manual-record pruning. The default Latest build-and-run route may also launch a
fully verified hash-named cached image when only promotion to the retained
Latest path fails. Every bypassed failure remains visible as a warning.

Force mode never bypasses checks required to construct a valid image. Catalog
and configuration structure, compilation and linking, source and patch guards,
edit conflicts, resident-payload layout, image layout, and final image-content
verification remain fatal. `-f` is not valid for a pure launch, a
worker build, E2E, unit tests, or release packaging.

The public `na228` development commands present configuration failures as one
concise path/value/expectation message. Their existing `latest.log` and
`rolling.log` records retain the corresponding traceback under
`technical_details`; catalog-authoring and internal failures remain developer
errors and keep their existing presentation.

`na228 worker [--configuration <id>] work/<task>/build/<name>.iso` reuses an
exact verified registry identity or runs full composition and physical image
verification, then publishes a hardlink to the canonical hash-named image.

Latest, Manual, E2E, and worker builds share one byte-affecting
fingerprint registry under `@logs/na228/preflight/`. A physical miss is assembled
to a unique incoming path, verified, atomically registered as
`@work/cache/isos/<SHA-256>.iso`, and then promoted to its requested role.
The hash-named image remains canonical; physical Latest, Previous, Manual, E2E,
and worker outputs are ordinary hardlinks to it. Distinct fingerprints that
produce the same SHA-256 share that image identity and all verified locations.
Latest rotation hardlinks the outgoing Latest identity to Previous and updates
both image-location records. If a destination is locked, the invocation reports
pending and retains the verified cached image; the next matching request retries
promotion without rebuilding. Physical candidates hold exclusive activity
locks, so a later build can reclaim crash-orphaned incoming ISOs without
touching live parallel builds.

Preflight fingerprints both canonical source ISOs, ISO-composing Python code,
the exact selected configuration resources, product/path configuration, active
Python/Zlib/Zopfli versions, and the EE compiler components whenever selected C
sources require them. `scripts/module_pipeline.py` prepares internal invocations
and shared payload contributions; `scripts/build_configuration.py` composes
them; `scripts/composer.py` closes typed image operations; and
`image_assembler/` alone stages and verifies the ISO.

The development injector reads the feature files under `catalog/` with
`configurations/dev.json` and the layered base/dev character-override TSVs.
