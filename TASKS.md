# Tasks

## In Progress

### General
- Create notifications.

### [Font](docs/workstreams/font/README.md)
- [Investigate](work/__sstates/translation/font) and implement proper autofit/positions everywhere.
- Ninja Song: convert all dynamically generated output still selecting Shift-JIS digits or symbols to ASCII equivalents, including the renderer-table multiplication glyph if it remains reachable after static string changes.
- Special Controls ON/OFF: use the paired `ss01_NA2.p2s` + `ss01_NUN5.p2s` files under `work/String translation/inputs/sstates/2026-07-26-ss1-7-8-sjis-pass-2/`; Practice Settings ss8 is user-verified fixed with title-case `Off`/`On`, but ss1 Special Controls still does not match NUN5's compact uppercase-looking `ON`/`OFF` letter spacing and the current ninth-call v2 adapter has no visible effect.

### Project
- Release: add feature/group/patch config + instructions + default release config.
- Investigate cross-platform development/deployment possibilities.
- Global cleanup - preserve what is needed, delete the rest. Project should ask corresponding chats for specifics. Includes, but not limited to:
    * [UI Translation](work/__sstates/translation/UI).
    * [String Translation](work/__sstates/translation/strings).

## Backlog

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

### [Localization](docs/workstreams/localization/README.md)

### [Scripting](docs/workstreams/scripting/README.md)

### [UI Translation](docs/workstreams/ui_translation/README.md)

### [String Translation](docs/workstreams/string_translation/README.md)

### Code Injection

### Decompilation

### EE Runtime Memory Map
