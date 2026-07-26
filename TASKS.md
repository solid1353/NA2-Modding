# Tasks

## In Progress

### General
- Create notifications.

### [Font](docs/workstreams/font/README.md)
- [Investigate](work/__sstates/translation/font) and implement proper autofit/positions everywhere.
- Ninja Song: convert all dynamically generated output still selecting Shift-JIS digits or symbols to ASCII equivalents, including the renderer-table multiplication glyph if it remains reachable after static string changes.
- Special Controls / Practice Settings ON/OFF: split the shared T37/T38 presentation so ss1 retains compact uppercase ON/OFF while ss8 uses title-case Off/On, matching NUN5 letter spacing in both contexts.
- Load/Save Modal: change datetime format to EU.

### [UI Translation](docs/workstreams/ui_translation/README.md)
- Document shop minigame and UJ prompts as intentionally not fixed.
- [Cleanup](work/__sstates/translation/UI) - preserve what is needed, delete the rest.

### [String Translation](docs/workstreams/string_translation/README.md)
- [Cleanup](work/__sstates/translation/strings) - preserve what is needed, delete the rest.

## Backlog

### Project
- Rename default_enabled, add enable switch for groups and patches.
- Investigate cross-platform development/deployment possibilities.
- Global cleanup.

### Bugs
- Practice menu entries (like Damage) flicker again (unstable).
- Flicker on save.

### Logic
- Make knj cost selective.
- Make xDash cost 1 chakra.
- Add damage scaling?
- [Improve substitution reliability](docs/knowledge/localization/substitution.md).
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
- Isolate and promote runtime-proven patches.
- Test translation thoroughout the whole game.

## Archive

### [Scripting](docs/workstreams/scripting/README.md)

### Code Injection

### Decompilation

### EE Runtime Memory Map
