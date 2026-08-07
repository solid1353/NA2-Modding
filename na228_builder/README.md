# NA2.28 builder

The builder creates a reproducible product from a selected profile of features.

Root `product.json` owns the product title, serial, canonical source inputs,
output identity, and named build variants. Profiles are single TSV files under
`profiles/`; `profiles/default.tsv` is the normal build definition. Each row
contains a feature ID, an explicit `enabled` switch, its exact aggregate
canonical-input SHA-256, and a separate per-feature `bypass_check` development
switch. Disabled features remain visible in the profile but are neither hashed
nor composed.

The profile ID is the TSV filename stem. Profiles do not contain source roots,
identity data, manifests, module tables, module paths, module IDs, module
orders, or separate module pins.

## Feature and module discovery

Feature inputs live under the configured `@features/` root. A feature's folder
name is its ID, it contains the structurally required root `README.md`, and
every direct child directory must match a registered engine under
`na228_builder/modules/`. The root README is a concise feature contract and
index; substantial feature documentation lives under the repository root `docs/`
hierarchy; see [`docs/features/`](../docs/features/README.md). Enabling a feature enables all of its module directories.

`features/targets.tsv` is the single canonical registry of verified binary
targets shared by every feature. Binary-patcher and runtime-injector modules
reference target IDs from that registry and retain only the rows they use.

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

- `binary_patcher`: shared `features/targets.tsv`, local `groups.tsv`,
  `patches.tsv`, `edits.tsv`, and every blob referenced by `blob_path`.
- `runtime_injector`: shared `features/targets.tsv`, local `groups.tsv`,
  `patches.tsv`, `fragments.tsv`, `relocations.tsv`, `edits.tsv`, and every
  fragment blob referenced by `blob_path`.
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

The default profile enables, in order:

1. Localization: importer with a derived string-patcher consumer, resident
   font-renderer logic, texture patcher, native NUN5-derived font, regional menu
   input, and UI binary patches.
2. QoL: accepted startup, Practice, and mode-selection behavior.
3. Battle logic: accepted battle-rule behavior.
4. Rendering: verified native 16:9 horizontal scaling through the shared
   rendering-state writer.

Root `product.json` separately declares the equal-length
`SLPS_258.37` to `SLOP_NA2.28` boot rename and the CP932 memory-card title.
Output identity is product configuration, not a feature or module.

The former generic Testing feature was retired: feature IDs express ownership
or a coherent capability, while patch `status` and `confidence` express
maturity and certainty. Experimental patches belong to their owning feature; new unresolved leads
belong in topic-local hypothesis documents beside the relevant subsystem.

## Build

```powershell
python -m pip install -r na228_builder/requirements.txt
& scripts/na228/build.ps1
```

The current `na228 test` implementation prepares the E2E Test build and
couples permanent tests with emulator-driven replay. Validation policy treats
those as independently selectable; `TASKS.md` tracks the command/execution-lane
split. `-s` prepares the same-sized internally shifted payload build for strict
qualification. The normal and shifted outputs have independent preflight
receipts and build records; neither rotates Latest or Previous.

Before staging, `na228_builder/build_preflight.py` hashes both canonical source
ISOs, ISO-composing builder code and schemas, the exact selected profile
resources, product/path configuration, and active Python/Zlib/Zopfli versions.
Documentation, generated Python caches, preflight implementation, and
release-only files do not invalidate ordinary ISO builds. Each ISO-producing
mode has its own receipt; a valid receipt, matching output ISO, and retained
build record return the normal unchanged result without module derivation or a
`.building` file.

On a miss, `na228_builder/module_pipeline.py` prepares feature artifacts, derived
consumers, and shared payload contributions. `na228_builder/build_profile.py`
applies that pipeline and asks `na228_builder/composer.py` to close its results
plus the profile identity into typed operations. `na228_builder/payload_builder/` links contributed code
and data into the shared resident `PRG/228.BIN`, owns its global loader/memory
integration, and records its symbol map. `na228_builder/image_assembler/` alone
stages and verifies
the catalog-derived Latest ISO staging path. `scripts/na228/build.ps1` discards an
identical staged image without rotation or atomically promotes a changed one.
File sizes remain fixed except for the separately approved filesystem insertion
support used by compact external strings, which preserves total ISO size and
validates both ISO9660 and UDF trees.

The ordinary `na228` command builds and launches Latest. `na228 l`, `na228 p`,
and `na228 mt` launch Latest, Previous, and Manual Test without rebuilding;
`bl` and `bmt` are the corresponding build-and-run recipes. Shared builds do
not rewrite GameSettings. Configured launches select the catalog-derived
memory-card path whose name uses the selected build postfix. The standalone
`act` command regenerates input profiles.
Profile-run logs record the enabled feature pins and the complete derived module
result inventory.
