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
- `configurations/base.json` contains the shared `features` setting and its
  `overrides`. `development.json`, `test.json`, and `release.json` contain
  concrete `overrides`. Each overrides object may be empty or partially mirror
  the catalog's feature tree directly. The loader applies `base.features`, then
  `base.overrides`, then the concrete configuration's `overrides`. Normal local
  builds use `development.json`; Manual Test, worker, and E2E builds use
  `test.json`; only release packaging uses `release.json`.
- `catalog/implementation/targets.tsv` is the single target registry used by
  edits and injection hooks.
- `modules/binary_patcher/operations/*.tsv` defines the allowed fields and basic types for each binary operation.
- `localization/assets/` owns edit-referenced localization binary assets.
- Enabling `features.localization` includes the retained translation-importer and texture-patcher inputs under `localization/`; they are real inputs, not empty catalog selector nodes.
- `scripts/` contains every builder Python implementation file. Reusable engines and their code-only contracts remain under `modules/`.
- Root `release_manifest.json` owns release packaging metadata and remains
  outside the catalog.
- Root `product.json` owns the product title, explicit output boot path, source
  inputs, and named build variants.

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

The grammar supports `bool`, `int`, `decimal`, and `string`, literal types,
closed object types with optional fields, disjoint `|` unions, numeric `&`
comparisons, ranges, and steps, parentheses, `//` comments, and trailing
commas. It rejects every unlisted construct, including `null`.

Binary edit definitions always contain an explicit `operation`. Runtime target
changes live under an injection unit's `hooks` and therefore have no operation
discriminator. Runtime sources, fragments, imports, relocations, and ABI
metadata live under that unit's `payload`. Multiple catalog leaves may
reference the same shared injection unit.

Root edit and injection identities use `e__` and `i__` prefixes. Definition
maps and unordered nested
maps are serialized alphabetically and permanent tests enforce that source
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
`.modcat` sources, edits, injections, product and path configuration, shared targets,
applicable binary operation definitions, referenced assets and sources, and
selected localization TSV inputs. Release packaging inventories the same
closure for every selectable catalog node, including disabled nodes.
Documentation is not an executable builder input.

## Current release configuration

Feature files are discovered in alphabetical filename order. Module execution
within each feature remains derived from the stable internal engine order above.

Release packaging applies `base.features`, `base.overrides`, and
`release.overrides`, then writes one editable JSON configuration named
`config.json`. It also writes one consolidated, inert `catalog.modcat`
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
`configurations/test.json` for test, worker, and E2E outputs. The public
development dry run uses:

```powershell
na228 build -d
```

It exposes the builder's existing `--compose-only` path: configuration loading,
patch guards, compilation and linking, derived changes, and full composition
conflict checks run against the source ISO, while no ISO or build record is
created. Temporary compiler artifacts are removed by the builder. This does not
validate final image assembly, boot, or runtime behavior.

The public `na228` development commands present configuration failures as one
concise path/value/expectation message. Their existing `latest.log` and
`rolling.log` records retain the corresponding traceback under
`technical_details`; catalog-authoring and internal failures remain developer
errors and keep their existing presentation.

`na228 worker --ephemeral work/<task>/build/<name>.iso` runs the full worker
composition and image verification through a sparse virtual overlay. It records
the logical ISO size and SHA-256 without creating `.building` or destination ISO
files. Ordinary worker and user builds keep physical staging.

Preflight fingerprints both canonical source ISOs, ISO-composing builder code, the exact selected configuration resources, product/path configuration, and active Python/Zlib/Zopfli versions. `scripts/module_pipeline.py` prepares internal invocations and shared payload contributions; `scripts/build_configuration.py` composes them; `scripts/composer.py` closes typed image operations; and `image_assembler/` alone stages and verifies the ISO.

The development injector reads the feature files under `catalog/` with
`configurations/development.json`. It no longer has a separate runtime TSV
registry.
