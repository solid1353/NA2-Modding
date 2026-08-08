# Feature documentation

Feature contracts and history live here. The builder has no physical `features/`
directory: selectable structure lives in `na228_builder/catalog.json`, while
guarded edits and runtime units live in `na228_builder/edits.json` and
`na228_builder/injections.json`. Non-inline executable inputs and assets live
under their concrete builder data area. Catalog-only features require no
directory.

- [Battle logic](battle_logic.md)
- [Localization](localization/README.md)
- [Quality of life](qol.md)
- [Rendering](rendering.md)
