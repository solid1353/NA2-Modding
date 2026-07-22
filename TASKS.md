# Tasks

## In Progress

### Project
- [Develop a release process (deferred indefinitely)](docs/RELEASE_PROCESS.md).
- Investigate cross-platform development/deployment possibilities.
- Work folder cleanup?

### [Font](docs/plans/font.md)
- Make font identical to UN5.
- Implement proper autofit/positions everywhere.

### [UI Translation](docs/plans/ui_translation.md)
- Deal with remaining issues/regressions.
- Investigate upscaling.

### EE Runtime Memory Map
- Establish and document the game-wide EE runtime memory map across representative states: resident and dynamically loaded binaries/modules, heaps, stacks, static data, overlays, allocator behavior, lifetimes, persistent and phase-specific free regions, and safe capacity/address ranges for injected code/data. Quantify worst-observed headroom and the capacity impact of the current whole-TEXTENG.BIN reservation versus direct inline patches, a compact external string pool, and a shared code/data reservation; provide evidence and constraints for the separate TEXTENG.BIN policy and Code Injection Architecture decisions.

## Backlog

### Bugs
- Practice menu entries (like Damage) flicker again (unstable).

### Logic
- Make knj cost selective.
- Make xDash cost 1 chakra.
- Add damage scaling?
- Replace support selector with J/UJ selector.
- [Improve substitution reliability](docs/knowledge/substitution.md).
- Add substitution bar.
- Fix extra hit floating animation (or maybe not?).

### QoL
- Integrate save into the game, simplify the entry menu and replace old slps references in the ELF.

### Testing
- Basically everything.

## Archive

### Code Injection

### Decompilation

### String translation
