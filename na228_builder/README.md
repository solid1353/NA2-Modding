# NA2.28 builder

The builder creates a reproducible product from one configuration and the
integrated catalog data.

## Canonical data

- `catalog.modcat` owns the nested selectable feature hierarchy and its patch
  references. [Catalog format](../docs/catalog.md) owns the authoring grammar,
  configuration semantics, patch mappings, and release projection.
- `patches/*.json` owns unified patch definitions, split by the first segment
  of each dotted patch ID. Referenced C and assembly sources remain separate
  files.
- `configurations/base.jsonc` owns the complete shared `features` tree.
  `test.jsonc`, `e2e.jsonc`, and `release.jsonc` contain partial
  `overrides`. Root `game.json` may assign a unique command alias; E2E and
  release packaging select their dedicated configurations internally.
- `configurations/overrides/base.character_overrides.tsv` owns shared
  per-character values and the required `base` and `step` metadata rows.
  Profile TSVs layer nonempty cells over the base by row identity. Empty cells
  inherit, while numeric zero is explicit. The editing contract is documented
  below.
- `@resources/character_data.tsv` owns the repository ID/name and native-value
  reference used to validate character rows. `support_id` stores the native
  support-roster ID. `awakening_ids` stores the union of fighter-controller
  effect associations, nonempty Ultimate-Jutsu post-effects, hard-coded
  transformed-form initialization effects, and character-specific direct or
  successor effect applications; membership does not imply one activation
  route. `linked_uj` and `linked_jutsu` store the corresponding BTL
  relationship-table support IDs. Empty cells mean no recorded value. These
  columns are references, not catalog or override inputs.
- `@repository/launch_profiles/practice/movesets.tsv` owns ordered Practice
  test cases. `case_id` is the stable case-insensitive launcher selector;
  physical row numbers are not an interface. Each character block starts with
  its plain primary ID or `-2nd` case; a primary form's `-rev` case follows the
  plain ID, then any `-awk-N`, `-luj-N`, and `-lj-N` cases. Primary IDs use the
  short character stem, Classic IDs use `bName`, second forms append `-2nd`,
  and numbered slots are append-only. `character_id`, `awakening_id`, and
  `support_id` are runtime inputs; E2E resolves display names from
  `@resources/character_data.tsv`. Empty awakening and support IDs mean no
  starting awakening and No Support. A `-rev` case selects native Half
  starting HP. `capture_policy` is empty for no capture or contains `base`,
  `specials`, `base, specials`, or `base, parent-specials`; the last value
  captures a `-2nd` case in its own Base grid and its primary form's Specials
  grid. The file is test metadata, not a catalog input.
- `modules/targets.tsv` is the builder-wide target registry.
  `modules/binary_patcher/operations/*.tsv` defines primitive binary
  operations.
- `patches/localization/` owns Font assets under `font/glyphs/`,
  translations under `strings/`, and UI texture inputs under `ui/`.
  `features.localization.ui` selects its layout and texture work atomically.
- `@scripts/` owns builder implementation. Reusable engines and their
  code-only contracts live under `modules/`; each reusable module README
  states its downstream invocation or that it invokes none. Do not create
  placeholder engine directories or files merely to register an engine.
- `release_manifest.json` owns release packaging metadata. `game.json` owns
  the product title, boot path, configuration aliases, base launch settings,
  and named launch-profile overrides.

JSON configurations select features. Character-override TSVs are separate
per-character build inputs.

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
resolved substitution cost must remain inside `0..100`.

Runtime consumption of the resolved values and Chakra, Gauge, and Free behavior
are documented in the [Battle feature](../docs/features/battle.md#substitution-cost).

## Catalog

[Catalog format](../docs/catalog.md) is the canonical reference for node types,
configuration merging, constraints, patch mappings, launch metadata, definition
validation, and public release projection.

## Internal execution

Reusable engines remain internal under `modules/`. Catalog settings may select
an engine by module type without exposing its implementation in the public
release catalog. The builder derives internal engine invocations in this stable
order:

1. `translation_importer`
2. `runtime_injector`
3. `texture_patcher`
4. `binary_patcher`

The configuration pipeline derives an in-memory string-patcher plan from the
localization importer's output. `string_patcher` is a derived stage, not a
separately selected module or file-backed interface.
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

## Release configuration

The [release process](../docs/runbooks/release.md) owns package contents,
external configuration and character overrides, embedded resources, end-user
validation and error behavior, and production publication.

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

When [`NA228_TASK_WORK_ROOT`](../docs/policies/work_directories.md)
is set, builds keep their operational and structured records below the acting
chat's `logs/` directory.

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
