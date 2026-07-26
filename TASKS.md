# Tasks

## In Progress

### General
- Create notifications.
- Collapse font, UI/string translation into localization workstream.

### [Font](docs/workstreams/font/README.md)
- [Investigate](work/__sstates/translation/font)
    * Implement proper autofit/positions everywhere.
    * Ninja Song: change SJIS numbers to ASCII.
    * Load/Save Modal: change datetime format to EU.

### [UI Translation](docs/workstreams/ui_translation/README.md)
- [Investigate](work/__sstates/translation/UI)
    * Deal with remaining issues (items, awakenings, etc.).
    * Document shop minigame and UJ prompts as intentionally not fixed.

### [String Translation](docs/workstreams/string_translation/README.md)
- [Investigate](work/__sstates/translation/strings)
    * Redo the translation from scratch, using existing data as a reference, touching only what is displayed with the help of savestates. Not everything is translated currently (MAX Damage label, etc.).

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
