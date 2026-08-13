# Collection localization polish

## Scope

This pass covers every maintained Collection E2E section, in this fixed order:

| Order | Section | E2E suite | Status |
| ---: | --- | --- | --- |
| 1 | Characters | `collection/characters` | Done |
| 2 | Figures | `collection/figures` | Done |
| 3 | Miscellaneous | `collection/misc` | Done |
| 4 | Opponents | `collection/opponents` | Done |
| 5 | Ultimate Jutsu | `collection/ultimates` | Done |
| 6 | Voice | `collection/voice` | Done |

Each section covers all visible localization differences represented by its
paired captures:

- non-matching English translations;
- horizontal font spacing differences;
- text positioning differences;
- incorrect localized texture placement.

The Font stack's non-collapsed glyph height is intentional and must be
preserved.

## Texture-placement families

The known non-repeating texture-placement defects are limited to these two
families unless new capture evidence proves otherwise:

- `collection/misc` capture `022`: controls are hidden in both versions, but
  NA2.28 resolves the Display state prompt to a malformed texture substring;
- `collection/figures` captures represented on blend-grid pages `09` through
  `11`: the Diorama viewer's controls are visible in both versions, but
  NA2.28 selects and places the wrong localized state prompt and clips the two
  upper control labels.

When one repeated family is corrected, the correction is made at the shared
owner and the complete global E2E run is used to validate the whole family.

## Completion rule

Only one section is active at a time. A section is complete only after all of
its paired captures have been reviewed, its in-scope differences have been
resolved, the global `na228 e2e` run succeeds, and every generated capture
change has been inspected and explained. Work then advances to the next section.

The complete six-section result was accepted with `ver` on 2026-08-13. Its
generated capture history is consolidated through `na228 e2e commit`, and the
accepted implementation is delivered as the matching main-repository commit.
