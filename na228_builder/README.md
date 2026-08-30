# NA2.28 builder

The builder creates a reproducible product from one configuration and the
integrated catalog data.

## Canonical data

- `catalog.modcat` owns the complete nested selectable hierarchy. Its
  `features` object contains every direct feature child. The custom
  declarative syntax uses JSON-like objects and TypeScript-like value types and
  is parsed directly by the Python builder.
  [Catalog reference](../docs/catalog.md) is the complete authoring and
  configuration-semantics reference.
- Catalog settings and structural blocks may contain one singular `patch`
  reference. Dotted patch IDs describe catalog ownership; their implementation
  capability is determined by the referenced definition, not by an ID prefix.
  Implementation details never appear in the release catalog reference.
- `patches/*.json` owns unified patch definitions, split by the first segment
  of each dotted patch ID. One definition may contain a primitive `edit` or an
  `edits` group, runtime `hooks` and `payload`, one semantic `string_patch`,
  required `modules`, and launch metadata. This keeps one catalog identity for
  one selected behavior while the existing executors continue to process each
  mechanism. C and assembly sources remain separate files referenced by their
  payload declarations.
- The catalog loader expands fixed-stride `replace_table` records into ordinary
  guarded replacements before composition. A typed setting may feed its
  validated value to a declared binary adapter instead of storing fixed
  replacement bytes.
- `configurations/base.jsonc` contains the complete shared `features` tree and
  is the canonical development configuration. `test.jsonc`, `e2e.jsonc`, and
  `release.jsonc` contain concrete `overrides`. Each overrides object may be
  empty or partially mirror the catalog's feature tree directly. The loader
  applies the concrete configuration's `overrides` to `base.features`. Every
  top-level configuration JSONC is available to the development commands
  automatically. Root `game.json` may map a configuration to a unique alias;
  an aliased configuration is selected only by that alias. E2E selects
  `e2e.jsonc` internally; only release packaging uses `release.jsonc`.
- `configurations/overrides/base.character_overrides.tsv` contains the required
  `base` and `step` metadata rows and shared per-character overrides. These two
  rows are not characters, so their `base_id`, `character`, and `tier` cells
  are empty. `release.character_overrides.tsv` layers nonempty cells over it by
  row identity. Test and E2E use the base layer directly. Empty cells inherit;
  numeric zero is an explicit value. Release packaging materializes the resolved feature and
  character-override layers into one external JSONC configuration and one
  external character-override TSV.
- `@resources/character_data.tsv` is the repository-owned ID/name and native-value
  reference used to validate character rows. Its
  `support_id` cells contain the native support-roster ID corresponding to each
  playable character, written in hexadecimal; an empty cell means that the
  character has no native support entry. Its
  `awakening_ids` cells contain comma-separated native IDs such as
  `0x61,0x62`. They are the union of the character's fighter-controller effect
  associations, nonempty Ultimate-Jutsu post-effects, hard-coded
  transformed-form initialization effects, and character-specific direct or
  successor effect applications, so membership does not imply a particular
  activation route; an empty cell means none of those native sources supplies
  an effect. `linked_uj` and `linked_jutsu` contain the native
  support IDs associated with each character by the corresponding BTL tables;
  empty cells mean no relationship of that type. These metadata columns are
  not builder catalog inputs. The file is not an override file.
- `@repository/launch_profiles/practice/movesets.tsv` contains ordered
  moveset-test metadata. `case_id` is the stable Practice launcher selector;
  input lookup is case-insensitive and table spelling is canonical. Physical
  row numbers are not an interface. Each character block starts with its plain
  primary ID or its `-2nd` case. A primary form's `-rev` case follows the plain
  ID immediately, then any `-awk-N`, `-luj-N`, and `-lj-N` cases.
  Primary IDs use the short character stem, Classic IDs use `bName`, and second
  forms append `-2nd`. Other cases append `-rev`, `-awk-N`, `-luj-N`, or
  `-lj-N`; numbered slots are append-only. Runtime IDs belong only in their
  dedicated columns.
  `character_id`, `awakening_id`, and `support_id` are runtime inputs. E2E
  resolves each display name from `@resources/character_data.tsv` by
  `character_id`. Empty `awakening_id` and `support_id` cells mean no starting
  awakening and No Support. Nonempty cells record hexadecimal awakening or
  support IDs.
  A `-rev` suffix selects the native Half starting-HP mode. Every case has an
  authoritative E2E `capture_policy`: an empty cell means no capture; populated
  values are `base`, `specials`, `base, specials`, or
  `base, parent-specials`. The last value belongs to `-2nd`: it captures
  that form in its own Base grid and the preceding primary form's Specials
  grid. The file is not a builder catalog input.
- `modules/targets.tsv` is the single builder-wide target registry used by
  edits and injection hooks.
- `modules/binary_patcher/operations/*.tsv` defines the allowed fields and basic types for each binary operation.
- `patches/localization/` owns localization patch inputs by patch ID:
  Font assets under `font/glyphs/`, translations under `strings/`, and UI
  texture inputs under `ui/`.
- `features.localization.strings` selects the translation importer, while
  `features.localization.ui` atomically selects its layout patches and the
  matching texture patcher. Release builds always require the clean
  NA2 ISO and require the clean NUN5 ISO only when the resolved module list
  includes the texture patcher.
- `@scripts/` contains every builder Python implementation file. Reusable
  engines and their code-only contracts remain under `modules/`; non-inline
  feature inputs remain with their owning feature. Do not use placeholder
  engine directories, identity manifests, `.gitkeep`, or header-only files
  merely to register an engine. Each reusable module README states its
  downstream module invocations or that it invokes none.
- Root `release_manifest.json` owns release packaging metadata and remains
  outside the catalog.
- Root `game.json` owns the product title, explicit output boot path, optional
  configuration aliases, base launch settings, and direct named launch-profile
  overrides. Each named override
  declares a profile; its matching `launch_profiles/<profile>/` directory owns
  optional profile behavior and assets.

JSON configurations select features. The paired character-override TSVs are
the separate per-character build inputs for battle values.

The `-l <profile>` launcher option is optional. Without it, the base fields
apply. A selected direct profile inherits every base field it does not override.
Profile names are not a closed set. A configured profile may own executable
argument handling in `@repository/launch_profiles/<profile>/launch.ps1`.
Profiles without that script are settings-only and accept no profile arguments.
Executable profiles return their additional Workshop launch parameters through
a `LaunchParameters` dictionary.

## Edit per-character battle values

1. Put shared defaults and agreed character values in
   `configurations/overrides/base.character_overrides.tsv`.
2. Put release-only values in `release.character_overrides.tsv` in the same
   directory. Only nonempty cells replace the base layer.
3. Keep each numeric `id` paired with the exact `character` name from
   `@resources/character_data.tsv`. `base_id` identifies a form's base
   character, and `tier` records the human-readable balance tier. Tier labels
   use at most four ASCII characters because the resident table stores a
   fixed-width four-byte field. Rows retain the order written in the base TSV
   so forms can stay directly below their base characters.
4. Keep the `base` and `step` rows' `base_id`, `character`, and `tier` cells
   empty. Write the `base` substitution cost as a literal percentage from `0`
   through `100`, and write `step` as an explicitly positive, signed increment.
   The canonical values are `20` and `+5`.
5. Leave a character's `substitution_cost` empty to derive it from `tier` as
   `base + tier_index * step`: D `0`, C `1`, B `2`, A `3`, S `4`, S+ `5`,
   S++ `6`, and S+++ `7`. Write an unsigned value such as `30` for a literal
   `30/100` per-character override. Write an explicitly signed value such as
   `+5` or `-5` to adjust that character's tier-derived cost. The resolved
   result must remain in `0..100`.
6. Leave a profile value cell empty to inherit the lower-layer character cell,
   including its literal-or-signed mode. `0` is a literal zero-cost override;
   `+0.0` is a zero adjustment.
7. Save the file as UTF-8 TSV and run the normal build for that profile.

For example, these rows set base `20` and step `+5`. Naruto's empty cost is
inferred from tier S as `40/100`; Sakura's unsigned `25` is a literal
per-character override:

```tsv
id	base_id	character	tier	substitution_cost	hp	damage_multiplier	health_recovery_multiplier	chakra_recovery_multiplier
base				20
step				+5
57		Naruto Uzumaki	S
58		Sakura Haruno	A	25
```

The builder rejects unknown IDs, invalid base IDs, mismatched names, duplicate
rows, malformed columns, non-finite numbers, and negative literal values before
composition. Signed per-character adjustments may be negative, but every
resolved substitution cost must remain inside `0..100`. With the gauge feature
disabled, or with its runtime setting on `Chakra`, the runtime charges
`cost / 100` of NA2's 15-point chakra capacity. `Gauge` charges the same
fraction of the independent resource and places the top-HUD textured bar's red
marker at the exact rounded executable cost. `Free` charges neither resource.

## Catalog nodes

Catalog nodes may nest to any depth. A bare `setting` accepts `true` to apply
its patch and `false` to disable it. `setting<T>` accepts a typed scalar or
closed object value; when `T` accepts `{}`, `true` is its empty-object shorthand
and the selected value is normalized to `{}`. Typed boolean settings accept
`false` as data and remain selected.

`false` disables a node only when its type does not accept `false`. Structural
parents otherwise require explicit objects; `true` never expands a structural
parent. A structural container may own one common patch for its nested tree; the
patch receives the selected object and is applied once. Plain containers merge
recursively through configuration overrides, while settings and node unions
replace atomically.
Patch IDs are unique across the complete catalog. Shared patches belong on the
lowest common structural ancestor, and nested settings consumed by that patch
may omit their own `patch` field.
Structural-block and leaf-setting descriptions are optional and are retained
only when they add meaning beyond the node name and type.
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

An internal patch may declare startup launch timing as
`startup_fast_forward_frames: { "additive": N, "override": N }`, with either
key or both. Additives are signed integers; overrides are positive UInt64 frame
counts. Resolution starts from the non-negative base value under `game.json`
`launch_settings`, applies the selected direct profile override, then applies
the selected build target's configuration metadata: the sole enabled catalog
override replaces the baseline when present, and every enabled additive is
summed. Source-only launches have no build configuration modifier. More than one
enabled patch override or a final result outside UInt64 is a configuration
error. A zero result omits timed fast-forward. Disabled settings contribute
nothing. This launch metadata is omitted from the public release catalog along
with patch implementation references.

Every binary edit contains an explicit `operation`. A unified patch contains
either one primitive `edit` or a nonempty, one-level `edits` map;
each semantic child is either an ordinary primitive edit or a fixed-stride
`replace_table`. Table records resolve to concrete `replace` edits before
operation validation. Runtime target changes live under the same patch's
`hooks` and therefore have no operation discriminator. Runtime sources,
fragments, imports, relocations, and ABI metadata live under its `payload`.

Unified patch identities use dotted catalog ownership paths. Grouped edit
children use concise semantic identities within their patch; destination
addresses remain data rather than identity. Genuinely unordered definition
maps are serialized alphabetically. Feature declarations, payload source maps,
and source fragment maps retain file declaration order; the injection builder
derives fragment positions from that order instead of numeric `order` fields.
Hook and payload fragment identities are concise within their owning patch.
Final resident-payload placement is deterministic by fragment kind, owner, and
semantic symbol. Patch, edit, and hook descriptions are optional definition-local
documentation; a present description must be nonempty and never affects
execution.

## Internal execution

Reusable engines remain internal under `modules/`. Catalog settings may select
an engine by module type without exposing its implementation in the public
release catalog. The builder derives internal engine invocations in this stable
order:

1. `translation_importer`
2. `runtime_injector`
3. `texture_patcher`
4. `binary_patcher`

The localization importer derives its in-memory string-patcher plan directly;
there is no separate string-patcher module invocation or data interface.
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

Features are read from `catalog.modcat` in declaration order. Module
execution within each feature remains derived from the stable internal engine
order above.

Release packaging applies `release.overrides` to `base.features`, then writes
one editable JSONC configuration named `config.jsonc` containing only the
materialized `features` tree. It also materializes the layered base and release
character values as editable `character_overrides.tsv` with every reference
ID/name row present, and writes one
consolidated, inert `catalog.modcat`
reference with the same public hierarchy, types, constraints, unions, and
descriptions but no patch mappings or implementation details. `README.md`
explains the editable files in simple terms.

The packaged EXE validates `config.jsonc` against its embedded complete catalog
and never reads the external catalog reference. It contains resources for every selectable
catalog node, including nodes disabled by the default release selection.
Catalog-owned runtime C and assembly sources have packaged objects, so end users do not need
the project PS2 toolchain. Invalid configuration errors identify the exact path,
supplied value, and expected type or shape. After a failure, the EXE creates or
replaces `builder-error.log` with full exception details and stack traces rather
than showing them in the user-facing window. Successful runs create no log.

## Build

```powershell
na228 build b
```

Every top-level JSON under `configurations/` is discovered automatically. A
configuration without an alias uses its filename stem as its command selector.
Root `game.json` assigns `b`, `t`, `r`, and `e` to the base, test, release, and
E2E configurations; those configurations are selected only by their aliases.
`na228 <config>` launches the newest cached build. Prefixing the selector with
`b` builds or reuses it before launch, and `na228 build <config>` builds without
launching. Selectors must not conflict with commands, sources, or another
selector's build and watch forms. Bare `na228` is equivalent to `na228 bb`.

The public `na228` development commands present configuration failures as one
concise path/value/expectation message. Their existing `latest.log` and
`rolling.log` records retain the corresponding traceback under
`technical_details`; catalog-authoring and internal failures remain developer
errors and keep their existing presentation.

Completed operational invocations maintain `@logs/na228/latest.log` and the
newest 20 bounded sections in `@logs/na228/rolling.log`. Help output is not
logged. Persistent command logs omit transcript boilerplate, normalize
configured roots to aliases, and record mode, timing, outcome, ISO result, and
the configuration record when applicable.

All configurations share one byte-affecting fingerprint registry under
`@logs/na228/preflight/`. A miss is assembled and verified at a unique path
under `@build/.incoming/`, then moved to
`@build/NA v2.28 - <local timestamp> - <12-character SHA-256 prefix>.iso` and
registered. A later build removes stale incoming candidates left by interrupted
processes without touching live builds.

Distinct fingerprints and configurations that produce the same full SHA-256
reuse the existing ISO. The registry points every matching entry to that one
file; it does not rename, copy, or hardlink the image.

`@logs/na228/preflight/registry.json` stores byte-affecting fingerprint state,
configuration, full ISO SHA-256, verification time, verified image size, and path;
`preflight/records/<fingerprint>/` stores reusable structured provenance.
The registry retains at most 10 unique ISOs. Pruning removes every fingerprint
and provenance record that refers to an evicted image. A missing or corrupt
registry causes a complete verified build and is recreated only after success.

When `NA228_TASK_WORK_ROOT` is set, builds keep their operational and structured
records below the acting chat's `logs/` directory.

Preflight fingerprints both canonical source ISOs, ISO-composing Python code,
the exact selected configuration resources, product/path configuration, active
Python/Zlib/Zopfli versions, and the EE compiler components whenever selected C
sources require them. `@scripts/module_pipeline.py` prepares internal invocations
and shared payload contributions; `@scripts/build_configuration.py` composes
them; `@scripts/composer.py` closes typed image operations; and
`image_assembler/` alone stages and verifies the ISO.

The preflight dependency closure covers every input capable of changing the
selected ISO. A build-affecting input or dependency change updates that closure
and its existing invalidation coverage in the same change.

The development injector reads unified definitions under `patches/` with
`configurations/base.jsonc` and `base.character_overrides.tsv`.
