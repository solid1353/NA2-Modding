# Feature documentation

Feature contracts live here. The builder has no physical `features/`
directory: selectable structure lives in
`na228_builder/catalog/catalog.modcat`, while guarded edits, runtime units, and
targets live beside it. Non-inline executable inputs and
assets live under their concrete builder data area. Catalog-only features
require no directory.

- [Battle logic](battle_logic.md)
- [General](general.md)
- [Localization](localization/README.md)
- [Quality of life](qol.md)
- [Rendering](rendering.md)
