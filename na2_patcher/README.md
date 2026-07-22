# NA2 modular patcher

The patcher builds the active reproducible image from enabled features rather
than independently configured module instances.

Each profile directory contains:

- `roots.tsv`: repository-relative source bindings or `@root/...` aliases.
- `features.tsv`: enabled feature IDs in composition order and each feature's
  exact aggregate canonical-input SHA-256.
- `identity.tsv`: the clean/output boot paths, `SYSTEM.CNF` path, and guarded
  memory-card title that define the final output identity.

The profile ID is its directory name. Omission disables a feature. Profiles do
not contain manifests, module tables, module paths, module IDs, module orders,
or separate module pins.

## Feature and module discovery

Feature inputs live under the configured `@features/` root. A feature's folder
name is its ID, it contains exactly one root `README.md`, and every direct child
directory must match a registered engine under `na2_patcher/modules/`.
Enabling a feature enables all of its module directories.

Feature rows define feature order. Within a feature, the engine registry uses
this deterministic order:

1. `translation_importer`
2. `string_patcher`
3. `texture_patcher`
4. `binary_patcher`

Derived module IDs use `<feature_id>.<module_type>`. The composer resolves
declared module-artifact dependencies while retaining stable feature/module
order for independent peers. A translation importer invokes the generic
string-patcher consumer as a derived stage; no placeholder feature directory or
file is created when the feature owns no local strings.

## Hashing

One feature pin covers the union of all canonical executable inputs owned by
that feature, including each canonical file's feature-relative path. Root
READMEs, engine code, and non-input authoring helpers are excluded.

- `binary_patcher`: `targets.tsv`, `groups.tsv`, `patches.tsv`, `edits.tsv`,
  and every blob referenced by `blob_path`.
- `string_patcher`: `strings.tsv`, only for a feature that owns local string
  declarations.
- `translation_importer`: `config.tsv`, `mappings.tsv`, and `references.tsv`.
- `texture_patcher`: `containers.tsv`, `mappings.tsv`, and `strategies.tsv`.

Binary package identity is derived from its feature/module path. Binary
packages have no `manifest.tsv`; normal composition applies their
`default_enabled` patches. Explicit patch IDs remain focused CLI/research
inputs only.

## Current composition

The current profile enables, in order:

1. Localization: importer with a derived string-patcher consumer, texture
   patcher, native NUN5-derived font, regional menu input, and UI binary patches.
2. QoL: accepted startup, Practice, and mode-selection behavior.
3. Battle logic: accepted battle-rule behavior.

The profile's `identity.tsv` separately declares the equal-length
`SLPS_258.37` to `SLPS_222.28` boot rename and the CP932 memory-card title.
Output identity is profile configuration, not a feature or module.

Rendering remains an available feature folder but is omitted from the current
profile. The former generic Testing feature was retired: feature IDs express
ownership or a coherent capability, while patch `status` and `confidence`
express maturity and certainty. Experimental patches belong to their owning
feature; contextless leads belong in `docs/HYPOTHESES.md` until ownership and
an executable hypothesis are clear.

## Build

```powershell
python -m pip install -r na2_patcher/requirements.txt
& scripts/na2/build.ps1
```

Before staging, `na2_patcher/build_preflight.py` hashes both canonical source
ISOs, the complete `na2_patcher/` tree except generated Python caches, the
selected profile path, and active Python/Zlib/Zopfli versions. A valid receipt
and matching Current ISO produces the normal unchanged/no-rotation result
without module derivation or a `.building` file.

On a miss, `na2_patcher/module_pipeline.py` prepares feature artifacts, derived
consumers, and shared payload contributions. `na2_patcher/build_profile.py`
applies that pipeline and asks `na2_patcher/composer.py` to close its results
plus the profile identity into typed operations. `na2_patcher/payload_builder/` links contributed code
and data into the shared resident `PRG/228.BIN`, owns its global loader/memory
integration, and records its symbol map. `na2_patcher/image_assembler/` alone
stages and verifies
`build/NA2.28 - Current.iso.building`. `scripts/na2/build.ps1` discards an
identical candidate without rotation or atomically promotes a changed one.
File sizes remain fixed except for the separately approved filesystem insertion
support used by compact external strings, which preserves total ISO size and
validates both ISO9660 and UDF trees.

The ordinary `na2` command builds and launches PCSX2 without changing PNACH
aliases. `na2 -c` launches Current without rebuilding; `na2 -p` launches
Previous; `na2 act` performs on-demand PNACH alias maintenance for runtime tests.
Profile-run logs record the enabled feature pins and the complete derived module
result inventory.
