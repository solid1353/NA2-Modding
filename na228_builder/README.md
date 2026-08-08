# NA2.28 builder

The builder creates a reproducible product from one configuration and one integrated catalog.

## Canonical data

- `catalog.json` owns the complete nested selectable hierarchy plus binary edits, runtime hooks, and runtime payload declarations under its one top-level `features` parent. There is no `groups`, `patches`, `children`, or module wrapper.
- `configurations/test.json`, `release.json`, and `development.json` contain `"features": true` plus an `overrides` object. Overrides may be empty or partially mirror the selectable structure under `features`; the loader recursively applies them over the base setting.
- `targets.tsv` is the single target registry used by catalog edits and hooks.
- `modules/binary_patcher/operations/*.tsv` defines the allowed fields and basic types for each binary operation.
- `localization/assets/` owns the catalog-referenced localization binary assets.
- Enabling `features.localization` includes the retained translation-importer and texture-patcher inputs under `localization/`; they are real inputs, not empty catalog selector nodes.
- `scripts/` contains every builder Python implementation file. Reusable engines and their code-only contracts remain under `modules/`.
- Root `product.json` owns source inputs, output identity, and named build variants.

JSON configurations are the only build definitions. There is no separate pin or enablement table.

## Catalog nodes

Catalog nodes may nest to any depth. `description`, `proven`, `edits`, `hooks`, and `payload` are reserved implementation or metadata fields; every other object key is a selectable child.

`description` is optional and ignored by the parser. Migrated nodes may contain only `"proven": false`; the field is removed when proof is complete and is never added to new values.

Binary edits always contain an explicit `operation`. Runtime target changes live under `hooks` and therefore have no operation discriminator. Runtime sources, fragments, imports, relocations, and ABI metadata live directly under the nearest owning `payload`; declarations are extracted only when multiple selectable nodes actually share them.

## Internal execution

Reusable engines remain internal under `modules/` and are not represented in catalog or configuration data. The builder derives internal engine invocations in this stable order:

1. `translation_importer`
2. `string_patcher`
3. `runtime_injector`
4. `texture_patcher`
5. `binary_patcher`

The localization importer invokes the string patcher as a derived consumer. Runtime payload declarations are compiled and linked into the shared resident `PRG/228.BIN`; resolved hooks then become guarded in-memory binary replacements. The binary patcher applies catalog edits last.

## Resource fingerprinting

The build-resource fingerprint covers the selected configuration, catalog, product and path configuration, shared targets, applicable binary operation definitions, catalog-referenced assets and sources, and selected localization TSV inputs. Release packaging inventories the same closure for every selectable catalog node, including disabled nodes. Documentation is not an executable builder input.

## Current release configuration

The release configuration composes, in order:

1. Localization text import, resident font/layout and numeric logic, textures, native font assets, regional input, and UI edits.
2. QoL startup, Practice, mode-selection, and Save/Load behavior.
3. Battle-logic behavior.
4. Rendering behavior.

Release packages include this configuration as editable
`Narutimate Accel v2.28.json`. The
packaged EXE validates that external file against its embedded catalog and
contains resources for every selectable catalog node, including nodes disabled
by the default release selection. Catalog-owned runtime C sources have packaged
objects, so end users do not need the project PS2 toolchain.

## Build

```powershell
& scripts/na228/build.ps1
```

`scripts/na228/build.ps1` resolves the `builder` package set from
`packages.json` and uses `configurations/release.json`. Direct composition uses:

```powershell
& .\scripts\lib\run_python.ps1 `
  -PackageSet builder `
  -Module na228_builder.scripts.build_configuration `
  -ArgumentList @(
    '--source', '<NA2.iso>',
    '--configuration', 'na228_builder/configurations/release.json',
    '--compose-only'
  )
```

Preflight fingerprints both canonical source ISOs, ISO-composing builder code, the exact selected configuration resources, product/path configuration, and active Python/Zlib/Zopfli versions. `scripts/module_pipeline.py` prepares internal invocations and shared payload contributions; `scripts/build_configuration.py` composes them; `scripts/composer.py` closes typed image operations; and `image_assembler/` alone stages and verifies the ISO.

The development injector reads `catalog.json` with `configurations/development.json`. It no longer has a separate runtime TSV registry.
