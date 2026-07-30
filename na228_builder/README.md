# NA2.28 builder

The builder creates the active reproducible image from enabled features rather
than independently configured module instances.

Each profile directory contains:

- `roots.tsv`: repository-relative source bindings or `@root/...` aliases.
- `features.tsv`: enabled feature IDs in composition order and each feature's
  exact aggregate canonical-input SHA-256, plus a separate per-feature
  `bypass_check` development switch.
- `identity.json`: structured image, memory-card, and game-title policy for the
  final output identity.

The profile ID is its directory name. Omission disables a feature. Profiles do
not contain manifests, module tables, module paths, module IDs, module orders,
or separate module pins.

## Feature and module discovery

Feature inputs live under the configured `@features/` root. A feature's folder
name is its ID, it contains exactly one root `README.md`, and every direct child
directory must match a registered engine under `na228_builder/modules/`.
Enabling a feature enables all of its module directories.

Feature rows define feature order. Within a feature, the engine registry uses
this deterministic order:

1. `translation_importer`
2. `string_patcher`
3. `runtime_injector`
4. `texture_patcher`
5. `binary_patcher`

Derived module IDs use `<feature_id>.<module_type>`. The composer resolves
declared module-artifact dependencies while retaining stable feature/module
order for independent peers. A translation importer invokes the generic
string-patcher consumer as a derived stage; no placeholder feature directory or
file is created when the feature owns no local strings.

## Hashing

One feature pin covers the union of all canonical executable inputs owned by
that feature, including each canonical file's feature-relative path. Root
READMEs, engine code, and non-input authoring helpers are excluded.

For a temporary manually edited feature, set only that row's `bypass_check` to
`1`; `0` enforces the stored hash. The loader still calculates the aggregate
hash, and the build log records both the expected and actual hashes with
`hash_check` set to `bypassed`. Set the row back to `0` and update its expected
hash once the edit is ready to pin. Do not use bypassed checks for an accepted
reproducible checkpoint.

- `binary_patcher`: `targets.tsv`, `groups.tsv`, `patches.tsv`, `edits.tsv`,
  and every blob referenced by `blob_path`.
- `runtime_injector`: `targets.tsv`, `groups.tsv`, `patches.tsv`,
  `fragments.tsv`, `relocations.tsv`, `edits.tsv`, and every fragment blob
  referenced by `blob_path`.
- `string_patcher`: `strings.tsv`, only for a feature that owns local string
  declarations.
- `translation_importer`: canonical `mappings.tsv`, including its folded pointer
  inventory.
- `texture_patcher`: `containers.tsv`, `mappings.tsv`, and `strategies.tsv`.

Binary package identity is derived from its feature/module path. Binary
packages have no `manifest.tsv`; normal composition applies patches whose
group and patch `enabled` switches are both `1`. Explicit patch IDs remain
focused CLI/research inputs only and override those switches.

## Current composition

The current profile enables, in order:

1. Localization: importer with a derived string-patcher consumer, resident
   font-renderer logic, texture patcher, native NUN5-derived font, regional menu
   input, and UI binary patches.
2. QoL: accepted startup, Practice, and mode-selection behavior.
3. Battle logic: accepted battle-rule behavior.
4. Rendering: verified native 16:9 horizontal scaling through the shared
   rendering-state writer.

The profile's `identity.json` separately declares the equal-length
`SLPS_258.37` to `SLOP_NA2.28` boot rename and the CP932 memory-card title.
Output identity is profile configuration, not a feature or module.

The former generic Testing feature was retired: feature IDs express ownership
or a coherent capability, while patch `status` and `confidence` express
maturity and certainty. Experimental patches belong to their owning feature;
contextless leads belong in `docs/HYPOTHESES.md` until ownership and an
executable hypothesis are clear.

## Build

```powershell
python -m pip install -r na228_builder/requirements.txt
& scripts/na228/build.ps1
```

`na228 validate` runs the same module derivation, edit composition, payload
linking, identity closure, and insertion/replacement planning against the real
source images, but bypasses preflight reuse and stops before ISO staging. It
does not promote or rotate images, update build receipts, actualize PCSX2
files, or launch PCSX2.

Before staging, `na228_builder/build_preflight.py` hashes both canonical source
ISOs, the complete `na228_builder/` tree except generated Python caches, the
selected profile path, and active Python/Zlib/Zopfli versions. A valid receipt
and matching Current ISO produces the normal unchanged/no-rotation result
without module derivation or a `.building` file.

On a miss, `na228_builder/module_pipeline.py` prepares feature artifacts, derived
consumers, and shared payload contributions. `na228_builder/build_profile.py`
applies that pipeline and asks `na228_builder/composer.py` to close its results
plus the profile identity into typed operations. `na228_builder/payload_builder/` links contributed code
and data into the shared resident `PRG/228.BIN`, owns its global loader/memory
integration, and records its symbol map. `na228_builder/image_assembler/` alone
stages and verifies
the catalog-derived Current ISO staging path. `scripts/na228/build.ps1` discards an
identical candidate without rotation or atomically promotes a changed one.
File sizes remain fixed except for the separately approved filesystem insertion
support used by compact external strings, which preserves total ISO size and
validates both ISO9660 and UDF trees.

The ordinary `na228` command builds and launches PCSX2. `na228 c` launches Current
without rebuilding; `na228 p` launches Previous. User-owned shared-image
workflows automatically run `act na228`; the standalone `act` command also
provides `na2`, `input`, and `links` modes.
Profile-run logs record the enabled feature pins and the complete derived module
result inventory.
