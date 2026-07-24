# Tasks

## In Progress

### General
- Create notifications.

### [Scripting](docs/workstreams/scripting/README.md)
- Return actualization workflow + actualize gamesettings as well, must run for any user-initiated build and delete stale files. Files are at pcsx2_files. Each user-initiated build method should use a different memcard copy that is named accordingly, Mcd001_NA228.ps2 is the base that exists just for copying.

### [Font](docs/workstreams/font/README.md)
- [Investigate](work/__sstates/translation/font)
    * Make font identical to UN5.
    * Implement proper autofit/positions everywhere.

### [UI Translation](docs/workstreams/ui_translation/README.md)
- [Investigate](work/__sstates/translation/UI)
    * Deal with remaining issues (items, awakenings, etc.).

### [String translation](docs/workstreams/string_translation/README.md)
- [Investigate](work/__sstates/translation/strings)
    * Consolidate mappings and references under one file, add source, donor, replacement and prefix fields, the need for externalization should be decided at build/link time by something. Source and donor fields should be purely informational.
    * Redo the translation from scratch, using existing data as a reference, touching only what is displayed with the help of savestates. Not everything is translated currently (MAX Damage label, etc.).

## Backlog

### Project
- Investigate cross-platform development/deployment possibilities.
- Global cleanup.

### Bugs
- Practice menu entries (like Damage) flicker again (unstable).
- Flicker on save.

### Logic
- Make knj cost selective.
- Make xDash cost 1 chakra.
- Add damage scaling?
- [Improve substitution reliability](docs/knowledge/substitution.md).
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

### Code Injection

### Decompilation

### EE Runtime Memory Map
