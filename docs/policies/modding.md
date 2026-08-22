# Modding and source policy

## Canonical builder contract

- Before modifying builder composition, read the relevant sections of
  `@builder/README.md` and the affected
  [feature documentation](../features/README.md). Do not recreate retired
  schemas or assumptions from historical notes.
- `@builder/configurations/base.json` owns the complete shared `features`
  tree. Each buildable target in root `game.json` owns its configuration;
  retained targets inherit the configuration of their rotation source. Cache
  builds use their explicitly selected configuration, and only release
  packaging uses `release.json`.
  Loading applies the selected configuration's `overrides` directly to the base
  features. Matching `base`, `dev`, `test`, and `release`
  `.character_overrides.tsv` files under `configurations/overrides/` layer
  nonempty per-character battle values by ID. Release packaging materializes
  both selected layers into one external JSON configuration and one external
  character-override TSV.
  `@builder/catalog/catalog.modcat` owns selectable definitions; the JSON
  and TSV files beside it own guarded binary edits, runtime hooks and payload
  declarations, and targets. Root `game.json` owns output
  identity, build targets, their configuration and rotation relationships, and
  project launch settings. Configurations never select build targets or launch
  profiles.
- Each named `game.json` launch-setting override declares a launch profile.
  Its matching `launch_profiles/<profile>/` directory owns optional profile
  behavior and assets.
- `e2e/config.json` owns E2E-only variant properties and references build
  targets by name. Build targets do not own E2E comparison or payload-shift
  settings.
- JSON files under `@builder/configurations/` exclusively own feature
  enablement and nested selection. Paired character-override TSVs exclusively
  own per-character battle values; there is no feature-pin table.
- Reusable engines, operation definitions, and tools belong under
  `@builder/modules/`; executable definitions belong in
  `catalog/edits.json` or `catalog/injections.json`; catalog leaves reference
  them by ID, and non-inline inputs remain under the owning feature.
- Remaining feature engine directories contain executable inputs, not placeholders,
  identity manifests, `.gitkeep`, or header-only files used only to register an
  engine.
- Each reusable module README identifies its downstream module invocations or
  states that it invokes none.
- `payload_builder` owns final shared `PRG/228.BIN` layout and loader/memory
  integration. Feature engines contribute fragments/symbols but do not choose
  global offsets or construct the final file.
- Localization normal builds use
  `@builder/localization/translation_importer/mappings.tsv` as the
  sole translation source of truth.
- Preflight dependency closure covers every input capable of changing the
  selected ISO. Any build-affecting input/dependency change updates the closure
  and its existing invalidation coverage in the same change.

## Binary and donor changes

- Never edit binaries manually. All binary changes go through reproducible
  scripts and guarded canonical data.
- Prefer one injection over multiple binary edits when they implement one
  behavior and a stable guarded hook can express it clearly in C or assembly.
  Keep isolated constant or instruction replacements as direct edits.
- Preserve file sizes unless the user explicitly approves expansion of the
  affected DATA.CVM, ELF, BIN, AFS, CCS, or ISO structure.
- Prefer verified canonical NUN5 data/bytes when suitable. When donor data is
  unsuitable, document the intended NA2 behavior and evidence for replacement
  bytes.
- The translation importer's `replacement` field is user-only. Agents leave it
  blank; if a translation cannot be expressed through a verified donor and
  centralized importer behavior, report that limitation to the user.
- Every binary edit records its target, offset, destination guard, and
  replacement operation. Rationale and evidence belong in documentation, not
  executable fields.
- Check encoded byte length before writing strings. Prefer
  Shift-JIS/CP932-compatible text unless proven otherwise.
- Do not delete or rename PSS files blindly.

## Source media

- Everything under `@source/`, including extracted views, is read-only unless
  the user explicitly authorizes an exact modification.
- Keep original archives under `@source/` and extracted contents beside them as
  `<archive filename>.files`, preserving structure exactly.
- Never place generated files, logs, probes, manifests, or metadata under
  `@source/`. Copy original-derived files outside it before changing them.
- Keep the active source ISOs and extraction trees Windows read-only. Restore
  those attributes with the maintained command described by the extraction
  runbook when needed.
- Temporary imported archives live under the active task's `temp/` tree until
  normalized, verified, and either promoted or removed.
- Use the canonical extraction procedure in
  [`../runbooks/source-extraction.md`](../runbooks/source-extraction.md).

## PNACH

- PNACH owns emulator settings, confirmed resident/runtime patches, and bounded
  temporary hypotheses not yet expressible as file-backed modules. File-backed
  changes belong in named binary-patcher patch sets.
- A PNACH item is enabled only when its executable `patch=` or setting line is
  uncommented; `// [Name]` is only a label.
- Fixed-address hypothesis writes require a boot ELF or another region proven
  resident and stable for the write lifetime.
- Never make unguarded fixed writes to load/unload overlays such as `BTL.BIN` or
  `ETC.BIN`; patch the file and rebuild instead.
- Runtime overlay PNACH testing is exceptional and requires a proven load-state
  or signature guard. Avoid dynamic heap writes without proven allocation,
  address, and lifetime.
- Keep active PNACH files to confirmed named sections plus active temporary
  hypotheses at the top. Temporary hypotheses use comment-only names and
  disabled `// patch=` lines except while actively testing.
