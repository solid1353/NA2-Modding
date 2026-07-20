# NA2 modular patcher

Profiles replace implicit newest-package selection with explicit, reproducible module inputs.

Each profile directory contains:

- `manifest.tsv`: schema version, profile ID, and description.
- `roots.tsv`: repository-relative bindings or `@root/...` aliases resolved from
  `project-paths.json`.
- `features.tsv`: enabled states plus exact hashes and paths for reusable feature
  packages under `na2_patcher/features/`.
- `modules.tsv`: globally ordered module instances with exact input hashes.

Feature-to-module selections do not live in profiles. Each reusable feature
package owns its declarative module inputs, ordered `selections.tsv`, and one
root README; reusable engines remain under `na2_patcher/modules/`.
Binary-patcher selections may target groups or patches, while every current
feature uses groups only.

Profile schema v2 supports declarative `binary_patcher`, `translation_importer`,
`string_patcher`, `texture_patcher`, `external_translation`, and
`disc_identity` modules. Package and ZIP-overlay workflows are retired;
profiles consume only repository-owned declarative inputs.

Profiles never select the newest file implicitly. Enabled features contribute
module selections; a module runs when at least one enabled feature selects it.
Enabled feature packages and active module inputs are content-hashed before
composition. Disabled features and unselected modules remain visible without
blocking the active build when their contents change.

Feature hashes cover only the package's `manifest.tsv` and `selections.tsv`.
Adjacent feature documentation and schemas do not affect profile pins.

For `binary_patcher` modules, the profile hash covers only executable package
inputs:

- `manifest.tsv`
- `targets.tsv`
- `groups.tsv`
- `patches.tsv`
- `edits.tsv`
- every blob referenced by `blob_path`

Adjacent documentation and authoring tools do not affect the profile pin.
`string_patcher` hashes only its semantic `strings.tsv`; its compiler and
README are excluded. At composition time those local declarations and the
validated rows from a preceding `translation_importer` become one in-memory
binary-patcher package.
Texture-patcher hashes cover only the three declarative inputs `containers.tsv`,
`mappings.tsv`, and `strategies.tsv`; replacements are derived directly from
the hash-pinned NA2 and NUN5 source members and checked against the hashes in
those files. Parser code and adjacent documentation are excluded from the
module-content pin. Translation-importer hashes cover its feature-owned
`manifest.tsv` and `mappings.tsv`; disc-identity inputs are hashed as exact files.

The current profile composes:

1. the runtime-proven native 14x20 NUN5-derived secondary font, Controls
   shrink-only fit, and character-modal alignment through the standalone
   `font` binary-patcher package, while preserving clean NA2 GF4C;
2. the runtime-proven menu-input handler set through `binary_patcher`;
3. separate `QoL` and `Battle logic` binary-patcher sections using their preserved default states;
4. hash-pinned v35 mappings through `translation_importer`, which imports and
   validates official strings without writing game payloads;
5. the fixed-size memory-card title plus imported BTL/ETC/SLPS strings through
   `string_patcher`, delegated to the shared `binary_patcher` engine;
6. 34 fixed-size source-derived official NUN5 UI container imports through
   `texture_patcher` (33 whole-container imports and one declared mapped import);
7. the 13 paired UI renderer/table corrections through `binary_patcher`;
8. the generated `PRG/MOD.BIN` and `PRG/TEXTENG.BIN` payloads and their guarded
   loader/pointer edits through `external_translation`;
9. the declared equal-length `SLPS_258.37` to `SLPS_222.28` boot identity
   change through `disc_identity`.

The disabled `Testing` section remains a separate binary-patcher package. The empty
`Rendering` patch set remains listed as a disabled module until populated.

Migrated PNACH structure uses one binary-patcher package per former section, groups for
related controls, atomic patch rows for independently selectable behavior, and
one or more exact edit rows per patch. The patch's `default_enabled` value
preserves whether that behavior was enabled.

Build the configured current profile with:

```powershell
python -m pip install -r na2_patcher/requirements.txt
& scripts/na2/build.ps1
```

Before staging, `na2_patcher/build_preflight.py` hashes both canonical source
ISOs, the complete `na2_patcher/` tree except generated Python caches, the
selected profile path, and the active Python/Zlib/Zopfli versions. A matching
successful receipt is accepted only when the configured Current ISO also
matches the receipt's size and SHA-256. That hit returns the ordinary
`unchanged`/no-rotation build result without module derivation or a `.building`
file. A missing, stale, malformed, or tampered receipt safely falls through to
the full verified build.

`na2_patcher/build_profile.py` writes the candidate ISO as `build/NA2.28 - Current.iso.building`, verifies it completely, fsyncs it, and writes the profile log before returning. `scripts/na2/build.ps1` compares the candidate with `NA2.28 - Current.iso`; an identical candidate is discarded without touching `NA2.28 - Current.iso` or `NA2.28 - Previous.iso`, while a changed candidate atomically replaces `NA2.28 - Previous.iso` with the outgoing `NA2.28 - Current.iso` and becomes the new `NA2.28 - Current.iso`. A failed promotion restores the outgoing ISO when safe, and any caught failure removes `.building`. Only a successful build and promotion may atomically update the preflight receipt.

File-size changes are always rejected. The disc-identity module permits only
its declared equal-length boot-file rename and verifies the resulting tree;
all other tree changes are rejected. Structural expansion requires a separately
designed and approved implementation rather than a build flag.

The ordinary `na2` command dispatches the profile build, then delegates mandatory PNACH actualization and PCSX2 launch to `scripts/na2/launch.ps1`. `na2 -c` launches `NA2.28 - Current.iso` without rebuilding, and `na2 -p` launches `NA2.28 - Previous.iso` without rebuilding. Translation and UI texture transplantation are invoked only as pinned profile modules and record their review plans or per-container patch tables inside the profile log.

The profile references `na2_patcher/features/translation/translation_importer/mappings.tsv`
directly and pins its exact hash. Updating that table therefore requires an
explicit profile-pin update. The importer emits no binary writes; the selected
imports are compiled and applied only by the following `string_patcher` module.
