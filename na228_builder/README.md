# NA2.28 builder

The builder composes the selected configuration and patch data into a verified
NA2.28 ISO. Use `na228 build [config] [-f]`; command details and cache behavior
are in the [build runbook](../docs/runbooks/build.md).

## Inputs

| Input | Purpose |
| --- | --- |
| `catalog.modcat` | Selectable feature tree, value types, and patch references |
| `configurations/base.jsonc` | Complete shared development configuration |
| `configurations/{jp,test,e2e}.jsonc` | Partial overrides of the base configuration |
| `configurations/overrides/*.character_overrides.tsv` | Separate per-character build inputs |
| `patches/<feature>/<feature>.json` | Patch definitions grouped by the first segment of each patch ID |
| `patches/<feature>/` | Feature-owned Python, C, assembly, and assets |
| `infrastructure/targets.tsv` | Shared binary target registry |
| `infrastructure/modules/binary_patcher/operations/*.tsv` | Primitive binary operations |
| `resources/mod_strings.tsv` | Mod-authored localized text |
| `resources/save_appendix.tsv` | Persistent setting IDs and saved-value encodings |
| `resources/release_manifest.json` | Release packaging metadata |
| `../resources/character_data.tsv` | Character identity and native-value reference; not an override input |
| `../game.json` | Product title, configuration aliases, and launch settings |

Release packaging derives its defaults from the base configuration and optional
catalog `release_value` overrides. The exported configuration contains only
public settings; development configurations retain the full feature tree.

## Build pipeline

`infrastructure/orchestration/` owns composition and shared builder utilities.
Reusable engines and their code contracts live in `infrastructure/modules/`.
Each module README states its downstream invocation or that it invokes none.
Do not create placeholder engine directories merely to register an engine.

The selected engines run in this order:

1. `translation_importer`
2. `runtime_injector`
3. `texture_patcher`
4. `binary_patcher`

The pipeline derives the in-memory string-patcher plan from imported text;
`string_patcher` is not a separately selected module or file-backed interface.
Injection payloads compile and link into the shared resident `PRG/228.BIN`.
Their resolved hooks become guarded binary replacements, applied with the
selected direct edits by the binary patcher last. The texture patcher verifies
checked-in CCS assets and inserts indexed `PRG/228_UI.BIN` without changing
source `DATA/DATA.CVM`. The image assembler stages and verifies the final ISO.

## Documentation

- [Build and launch](../docs/runbooks/build.md): commands, profiles, inputs, logs, and cache reuse.
- [Catalog format](../docs/features/catalog.md): configuration types, merging, patch mappings, and release export.
- [Character values](../docs/features/battle.md#substitution-cost): TSV editing and runtime consumption.
- [Save appendix](../docs/features/memory_card.md#save-appendix-schema): field IDs, encoding, and version rules.
- [Character reference](../docs/knowledge/gameplay/character_ids.md#confirmed-ids): identity and native relationship columns.
- [Mod strings](../docs/features/localization/mod_strings.md): shared localized text.
- [Localization](../docs/features/localization.md): language selection and shared components.
- [Practice cases](../e2e/README.md#practice-case-table): case naming, ordering, and capture metadata.
- [Release process](../docs/runbooks/release.md): packaging, external configuration, and publication.
