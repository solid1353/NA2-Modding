# Research and knowledge policy

**Applies when:** investigating disassembly, decompilation, live memory, game
files, reverse-engineered behavior, hypotheses, or reusable research tooling.

- Prefer reproducible CLI/scripted workflows when practical. State the tools
  used; if the correct tool/input is uncertain or a user-provided savestate,
  dump, screenshot, or file would materially improve the investigation, ask for
  it rather than pursuing a substantially less efficient substitute.
- Read the relevant topic/component knowledge before repeating research. For
  game-file investigations, begin with
  [`../knowledge/game/files/README.md`](../knowledge/game/files/README.md).
- Reuse and update preserved analysis under
  `@analysis/disassembly/<target>/`; do not repeatedly disassemble the same
  binary from scratch.
- Keep observations, inferences, hypotheses, contradictions, confidence, and
  discriminating experiments distinct. A plausible interpretation is not a
  fact or an implementation model another agent must inherit.
- Confirmed function roles, callers/callees, state behavior, mappings, runtime
  observations, and useful negative results belong in `docs/knowledge/` or
  beside canonical component data.
- New unresolved hypotheses belong in a topic-local hypothesis document beside
  the relevant subsystem or research area.
- Every substantive disassembly, decompilation, or live-memory task promotes
  reusable findings before cleanup. Record game/binary identity, ranges,
  file/runtime mapping, reconstructed behavior, meaningful names,
  callers/callees, side effects/state, cross-game equivalents, evidence, useful
  negative results, and explicit confidence.
- Before committing an implementation derived from reverse engineering, include
  its reusable knowledge update in the same delivery. Do not discard supporting
  analysis until every reusable finding and useful negative result is promoted.
- Optional reusable analysis, diagnostic, extraction, or research tools may be
  promoted to an existing research/tooling area under the implementation
  boundary in [`interaction.md`](interaction.md). Do not preserve ordinary
  scratch scripts or integrate a tool into production/build/CI/runtime without
  authorization.
- `@tools/CCSFileExplorerMSF` is the default CCS explorer. Treat `@tools/old/` as
  untrusted historical material; inspect a selected tool before execution.
- Keep reusable Ghidra projects or focused exports under
  `@analysis/disassembly/<target>/`. Do not preserve unfiltered listings or
  transient guesses merely to satisfy documentation.
