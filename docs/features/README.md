# Feature documentation

Feature contracts live here. The builder has no physical `features/`
directory: selectable structure is split by feature under
`na228_builder/catalog/`, while guarded edits, runtime units, and targets live
under `na228_builder/catalog/implementation/`. Non-inline executable inputs and
assets live under their concrete builder data area. Catalog-only features
require no directory.

- [Battle logic](battle_logic.md)
- [Localization](localization/README.md)
- [Quality of life](qol.md)
- [Rendering](rendering.md)
