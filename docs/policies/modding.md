# Modding and source policy

## Canonical builder contract

- Before modifying profiles, features, modules, composition, or image assembly,
  read `na228_builder/README.md` and the affected module/feature README. Those
  files are canonical for the current schema and pipeline; do not recreate
  retired schemas or assumptions from history.
- `na228_builder/profiles/default.tsv` is the normal reproducible build
  definition. Root `product.json` owns canonical inputs and output identity.
  `bypass_check=1` is temporary local development only; accepted reproducible
  checkpoints require the actual pin and `bypass_check=0`.
- Only the user may change profile `bypass_check` values. Agents preserve every
  existing value exactly and never toggle, reset, normalize, or otherwise edit
  that field.
- Use annotated Git tags for accepted reproducible checkpoints whose profile
  pins, canonical inputs, and documentation agree.
- Reusable engines/schemas/tools belong under `na228_builder/modules/`;
  reproducible feature-owned inputs belong under the owning feature.
- Feature module directories must contain actual executable inputs. Never keep
  placeholder directories/files, identity manifests, `.gitkeep`, or header-only
  tables solely to invoke or register an engine.
- Every reusable module README states its downstream modules or that it invokes
  none.
- `payload_builder` is mandatory shared infrastructure. Feature engines
  contribute fragments and symbols but do not choose final `PRG/228.BIN`
  offsets, own global loader/memory integration, or construct the final file.
- Translation checkpoints tag the complete project state; do not duplicate
  mappings into snapshots. Accepted normal builds continue using
  `na228_builder/features/localization/translation_importer/mappings.tsv` as the
  sole translation source of truth.

## Binary and donor changes

- Never edit binaries manually. All binary changes go through scripts.
- Preserve file sizes unless explicitly instructed. Do not expand DATA.CVM,
  ELF, BIN, AFS, CCS, or ISO structures without explicit instruction.
- Prefer verified canonical NUN5 data/bytes when suitable. Binary replacement
  bytes are allowed when a donor is unsuitable or intended NA2 behavior differs;
  document the reason and evidence.
- Log every binary patch: file, offset, original bytes, replacement bytes, and
  reason.
- String patches check encoded byte length before writing. `[S]` `shorten`
  mappings are manual fit exceptions only when they retain an exact official
  NUN5 source reference. Prefer Shift-JIS/CP932-compatible text unless proven
  otherwise.
- Do not include `ADV.bin` in release builds unless explicitly requested. Do
  not delete or rename PSS files blindly.

## Source media

- Everything under `@source/`, including extractions, is read-only reference
  material unless the user explicitly authorizes a specific modification.
- Keep untouched archives under `@source/` and their extractions beside them as
  `<archive filename>.files`. Preserve the extracted structure exactly.
- Never place generated files, logs, probes, manifests, or metadata under
  `@source/`. Keep Windows read-only attributes applied.
- Copy any original-derived file outside `@source/` before changing it.
- Keep temporary imported archives under the active task's `temp/`, normalize
  useful data, verify it, then delete it or preserve an irreplaceable copy
  outside the repository.

## PNACH

- PNACH is authoritative only for emulator settings, runtime-only patches, and
  temporary hypotheses not yet expressible as file-backed modules. Permanent
  file-backed changes belong in named binary-patcher patch sets.
- A PNACH item is enabled only when its executable `patch=` or setting line is
  uncommented; `// [Name]` is only a label.
- Fixed-address hypothesis writes require a boot ELF or another region proven
  resident and stable for the write lifetime.
- Never make unguarded fixed writes to load/unload overlays such as `BTL.BIN`
  or `ETC.BIN`; patch the file through scripts and rebuild instead.
- Runtime overlay PNACH testing is exceptional and requires a proven load-state
  or signature guard. Avoid dynamic heap writes without proven allocation,
  address, and lifetime.
- Keep active PNACH files to confirmed named sections plus active temporary
  hypotheses at the top. Temporary hypotheses use comment-only names and
  disabled `// patch=` lines except while actively testing.
