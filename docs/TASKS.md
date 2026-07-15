# Tasks

## In Progress

### Translation
- Translate remaining strings.
- Test extensively.

### Swap buttons in menus.
- Collect GPT's TSVs with hypotheses.
- Decide on a format.
- Teach Codex to apply it.
- Test.

### Raw binary patcher

- Define repository-owned TSV schemas for mappings, candidates, patches, and edits.
- Convert the existing proven font changes into named binary patches.
- Build a raw binary patcher with hash, expected-byte, size, conflict, atomicity, and logging checks.
- Verify that the patcher reproduces the current font outputs byte-for-byte.
- Update the main build scripts to call the patcher while preserving their existing entry points.
- Review GPT-produced UN5-to-NA2 mapping TSVs and approve candidates before application.
- Later integrate texture, sound, data-pack, and translation modules under the same orchestrator.

## Backlog

### Logic

- Develop a safer substitution reliability change as a temporary always-on PNACH hypothesis block, without mutating the known-working `[Sub cost = 3/15]` section.
- Analyze old files.
- Add substitution bar.
- Fix extra hit floating animation.
- Disable support.

### ISO

- Translate UI elements.
- Resume GF4 renderer work in the dedicated GF4 task, starting from the recorded v22/v23 results rather than another blind resource swap.
