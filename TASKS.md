# Tasks

## In Progress

### Project
- Regroup features.
- Decide on TEXTENG.BIN usage policy.
- Consider retiring cheats.
- [Develop a release process (deferred indefinitely)](docs/RELEASE_PROCESS.md).
- Investigate cross-platform development/deployment possibilities.
- Work folder cleanup?

### [Font](docs/plans/font.md)
- Make font identical to UN5.
- Implement proper autofit/positions everywhere.

### [UI Translation](docs/plans/ui_translation.md)
- Deal with remaining issues/regressions.
- Investigate upscaling.

### String translation
- Polish, using the audit.

## Backlog

### Game Decompilation
- Reconstruct materially analyzed game functions and types as curated C/C++-style knowledge, preserving game/binary identity, address, meaningful names, low/medium/high confidence, callers/callees, side effects, evidence, cross-game equivalents, and unresolved hypotheses. Raw Ghidra projects/exports remain under @analysis; canonical tracked reconstructions and an index belong under docs/knowledge/. Every chat doing substantive disassembly must contribute to this shared knowledge instead of leaving findings only in chat/logs.

### EE Runtime Memory Map
- Map the game-wide EE address space across relevant states: resident and dynamically loaded binaries/modules, heaps, stacks, static data, overlays, allocator behavior, lifetimes, persistent and phase-specific free regions, and safe capacity/address ranges for injected code/data. TEXTENG.BIN is one investigated allocation, not the workstream's defining subject.
- Investigate free EE space.

### Code Injection Architecture
- Design reusable injection across any suitable game binary: target selection, hooks, trampolines, relocations, ABI/calling conventions, linker layout, symbols, code/data lifetime, feature coexistence, scripted integration, and verification. MOD.BIN is one possible target, not the defining constraint. Consume confirmed Game Decompilation and EE Runtime Memory Map findings.

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
