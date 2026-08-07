# Tasks

## In Progress

### General
- Create notifications.
- Restructure pcsx2 stuff.
- [Make startup load the first save automatically](docs/workstreams/general/2026-08-07-auto-load-first-save-resume.md).

### [Font](docs/workstreams/font/README.md)
- Layout/autofit.

## Backlog

### [Project](docs/workstreams/project/README.md)
- Release: add feature/group/patch config + instructions + default release config.
- Investigate cross-platform development/deployment possibilities.
- Global cleanup - preserve/promote what is needed, delete the rest.

### Docs
- Review and reorganize the large localization, Font, UI, and other technical
  documents; move substantial documentation under the root `docs/` hierarchy
  where useful while keeping code directories uncluttered.
- Migrate `docs/HYPOTHESES.md` item by item: promote confirmed findings, move
  useful unresolved hypotheses beside their owning subsystem, delete obsolete
  material, then remove the general file.

### Bugs
- **UI Translation:** long character names.
- **String Translation:** save message.
- **General:** practice menu entries (like Damage) flicker again (unstable).

### Logic
- Make knj cost selective.
- Make xDash cost 1 chakra.
- Add damage scaling?
- [Improve substitution reliability](docs/knowledge/localization/substitution.md)
- Add substitution bar.
- Fix extra hit floating animation (or maybe not?).

### QoL
- Disable UJ overlay and inputs.
- Replace selected character with no support on character select screen.
- Replace support selector with Team J/UJ selector.
- Move support bar upwards.
- Integrate save into the game, simplify the entry menu and replace old slps references in the ELF.

### Visuals
- Create a proper widescreen patch.
- Create an upscaled texture pack for pcsx2 (currently blocked by UI translation).

### Testing
- Decouple E2E execution from permanent/unit tests and split the CLI: keep
  `na228 test` for permanent/unit tests; add global `na228 e2e [-s]`; move E2E
  create/rename/delete under `na228 e2e`.
- Isolate and promote runtime-proven patches.
- Test translation thoroughout the whole game.

## Archive

### [UI Translation](docs/workstreams/ui_translation/README.md)

### [String Translation](docs/workstreams/string_translation/README.md)

### Code Injection

### Decompilation

### EE Runtime Memory Map

### PCSX2
