# Tasks

## In Progress

### String translation
- Test translated strings extensively and deal with remainders.
- Fix flickering bug on Damage line in Practice mode.
- Deal with unresolved (mappings.tsv and ChatGPT's history).

### UI Translation
- Replace UI textures (consider already upscaled or upscaling them myself).

### Menu restructuring
- Analyze differences against UN6 and remove adventure mode.

### Raw binary module
- Maintain the exact atomic font m01 `GF4.BIN` and ELF reconstruction as the current baseline.
- Convert newly approved GPT mappings into named patch groups instead of replacement binaries.
- Add future texture, sound, and structured data-pack modules under the same orchestrator.

### Modular patching
- Replace the raw GF4 ranges with structured format-aware operations only after the container format is understood well enough to improve safety or authoring.
- Add sound and structured data-pack modules using the same profile contract.
- Explore other necessities.

## Backlog

### Logic
- Develop a safer substitution reliability change as a temporary resident-ELF PNACH hypothesis block, without mutating the known-working `[Sub cost = 3/15]` patch. Do not use this workflow for on-demand `BTL.BIN` or `ETC.BIN` addresses.
- Analyze old files.
- Add substitution bar.
- Fix extra hit floating animation.
- Disable support.

### Other
- Resume GF4 renderer work in the dedicated GF4 task, starting from the recorded v22/v23 results rather than another blind resource swap.
