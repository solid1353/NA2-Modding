# Tasks

## In Progress

### Translation
- Test translated strings extensively and deal with remainders.
- Fix flickering bug on Damage line in Practice mode.
- Deal with unresolved (mappings.tsv and ChatGPT's history).
- Replace UI textures (consider already upscaled or upscaling them myself).

### Swap buttons in menus.
- `ELF-M001`, `ELF-M002`, and `ELF-M003` each produced no changes when tested alone across the title/load/save matrix. Keep all three disabled but testable; the combined family result is interaction-dependent.
- After the translation/orchestrator migration, isolate pairwise save/load handler combinations instead of discarding the statically matched patches.
- Identify loading behavior separately if it remains unchanged after the save/load-family test.
- Keep Master Mode outside the current button-swap scope.
- Review and approve additional named handler groups individually; do not reapply the broad ETC package.

### Raw binary patcher
- Keep existing font ZIP composition until a texture/data asset module handles `GF4.BIN` and related resources.
- Convert newly approved GPT mappings into named patch groups instead of replacement binaries.
- Later integrate texture, sound, data-pack, and translation modules under the same orchestrator.

### Modular patching
- Integrate the translator as a formal module instead of the compositor's final special-case stage.
- Explore other necessities.

## Backlog

### Logic
- Develop a safer substitution reliability change as a temporary always-on PNACH hypothesis block, without mutating the known-working `[Sub cost = 3/15]` section.
- Analyze old files.
- Add substitution bar.
- Fix extra hit floating animation.
- Disable support.

### Other
- Resume GF4 renderer work in the dedicated GF4 task, starting from the recorded v22/v23 results rather than another blind resource swap.
