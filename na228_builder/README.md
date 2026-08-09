# NA2.28 builder

The builder creates a reproducible product from one configuration and the
integrated catalog data.

## Canonical data

- `catalog/*.json` owns the complete nested selectable hierarchy. Each file is
  named for one direct child of the logical top-level `features` parent and
  contains that child's node. Files are discovered in alphabetical filename
  order; root files named `__*.json` are metadata rather than selectable
  features. Catalog leaves contain `edits` and
  `injections` ID arrays; there is no `groups`, `patches`, `children`, or
  module wrapper.
- `catalog/__reference.json` is the sparse canonical owner of selectable-node
  descriptions. It mirrors only described catalog paths and is merged into the
  self-documenting configuration distributed with releases.
- `catalog/implementation/edits.json` is the direct root map of guarded binary
  edit definitions.
- `catalog/implementation/injections.json` is the direct root map of runtime
  injection units. Each unit contains `hooks`, `payload`, or both.
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
- Root `product.json` owns source inputs, output identity, and named build variants.

JSON configurations are the only build definitions. There is no separate pin or enablement table.

## Catalog nodes

Catalog nodes may nest to any depth. `proven` is metadata; `edits` and
`injections` are implementation-reference arrays allowed only on leaves. Every
other object key is a selectable child. Node descriptions do not live in the
selectable files: `catalog/__reference.json` may partially mirror the tree with
nonempty `description` strings, and every referenced path must exist.

Migrated nodes may contain only `"proven": false`; the field is removed when
proof is complete and is never added to new values.

Binary edit definitions always contain an explicit `operation`. Runtime target
changes live under an injection unit's `hooks` and therefore have no operation
discriminator. Runtime sources, fragments, imports, relocations, and ABI
metadata live under that unit's `payload`. Multiple catalog leaves may
reference the same shared injection unit.

Root edit and injection identities use
`<catalog_path>__<semantic_identity>`. Definition maps and unordered nested
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
catalog, edits, injections, product and path configuration, shared targets,
applicable binary operation definitions, referenced assets and sources, and
selected localization TSV inputs. Release packaging inventories the same
closure for every selectable catalog node, including disabled nodes.
Documentation is not an executable builder input.

## Current release configuration

Feature files are discovered in alphabetical filename order. Module execution
within each feature remains derived from the stable internal engine order above.

Release packaging applies `base.features`, `base.overrides`, and
`release.overrides`, then writes exactly one editable, self-documenting
configuration named `config.json`. It contains `features` and `overrides`;
every selectable feature node is an object with an `enabled` boolean, its
direct children, and its canonical description when one exists. A false branch
disables its complete subtree; a true branch descends into its child settings. Neither
repository configuration source nor a separate reference file is distributed.
The packaged EXE unwraps the enabled tree, applies `overrides`, and validates it
against its embedded catalog. It contains resources for every selectable
catalog node, including nodes disabled by the default release selection.
Catalog-owned runtime C sources have packaged objects, so end users do not need
the project PS2 toolchain.

## Build

```powershell
& scripts/na228/build.ps1
```

`scripts/na228/build.ps1` resolves the `builder` package set from
`packages.json` and uses `configurations/development.json` for normal builds or
`configurations/test.json` for test, worker, and E2E outputs. Direct development
composition uses:

```powershell
& .\scripts\lib\run_python.ps1 `
  -PackageSet builder `
  -Module na228_builder.scripts.build_configuration `
  -ArgumentList @(
    '--source', '<NA2.iso>',
    '--configuration', 'na228_builder/configurations/development.json',
    '--compose-only'
  )
```

Preflight fingerprints both canonical source ISOs, ISO-composing builder code, the exact selected configuration resources, product/path configuration, and active Python/Zlib/Zopfli versions. `scripts/module_pipeline.py` prepares internal invocations and shared payload contributions; `scripts/build_configuration.py` composes them; `scripts/composer.py` closes typed image operations; and `image_assembler/` alone stages and verifies the ISO.

The development injector reads the feature files under `catalog/` with
`configurations/development.json`. It no longer has a separate runtime TSV
registry.
