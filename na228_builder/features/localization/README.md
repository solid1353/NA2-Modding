# Localization feature

This feature owns the canonical declarative inputs for the accepted English
localization. Reusable engines remain under `na228_builder/modules/`; enabling
Localization enables every module directory present here.

Owned module inputs:

- `translation_importer/`: canonical text mappings and donor provenance;
- `runtime_injector/`: resident Font/layout and numeric-formatting code;
- `texture_patcher/`: source-derived English UI containers;
- `binary_patcher/`: guarded Font, UI-layout, and regional-input edits.

The importer invokes the shared string-patcher engine as a derived consumer, so
there is no placeholder `string_patcher/` directory. Module group IDs remain
local to their module and do not declare cross-module dependencies.

Substantial documentation is under
[`docs/features/localization/`](../../../docs/features/localization/README.md),
including the translation contract/history, UI texture and layout derivation,
compact external strings, Font integration, and regional input behavior.
