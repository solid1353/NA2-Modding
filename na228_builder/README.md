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
  `development.json`, `test.json`, and `release.json` contain
  concrete `overrides`. Each overrides object may be empty or partially mirror
  the catalog's feature tree directly. The loader applies the concrete
  configuration's `overrides` to `base.features`. Normal local builds use
  `development.json`; Manual, worker, and E2E builds use `test.json`; only
  release packaging uses `release.json`.
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

JSON configurations are the only build definitions. There is no separate pin or enablement table.

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

The build-resource fingerprint covers the base and selected configurations,
`.modcat` sources, edits, injections, settings and path configuration, shared targets,
applicable binary operation definitions, referenced assets and sources, and
selected localization TSV inputs. Release packaging inventories the same
closure for every selectable catalog node, including disabled nodes.
Documentation is not an executable builder input.

## Current release configuration

Feature files are discovered in alphabetical filename order. Module execution
within each feature remains derived from the stable internal engine order above.

Release packaging applies `release.overrides` to `base.features`, then writes
one editable JSON configuration named `config.json` containing only the
materialized `features` tree. It also writes one consolidated, inert `catalog.modcat`
reference with the same public hierarchy, types, constraints, unions, and
descriptions but no patch mappings or implementation details. `README.md`
explains both files in simple terms.

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
`packages.json` and uses `configurations/development.json` for normal builds or
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
`configurations/development.json`. It no longer has a separate runtime TSV
registry.
