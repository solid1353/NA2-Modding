# Research and knowledge policy

- Prefer CLI/scripted workflows over GUI-only workflows when practical. State
  the tools used; if the correct tool is uncertain or unavailable, ask the
  user to provide or approve one.
- Read `docs/knowledge/game/files/README.md` before investigating a game file.
  Update it when file roles or evidence improve; keep exhaustive paths, offsets,
  and sizes in its linked inventories.
- Reuse and update preserved analysis under
  `@analysis/disassembly/<target>/`; do not repeatedly disassemble the same
  binary from scratch.
- Confirmed function roles, callers/callees, state behavior, mappings, runtime
  observations, and useful negative results belong in `docs/knowledge/` or
  beside canonical module data. Unresolved candidates and speculative
  interpretations belong in `docs/HYPOTHESES.md`.
- Every substantive disassembly, decompilation, or live-memory task preserves
  reusable findings as they stabilize and before cleanup. Record the game and
  binary identity, function/range boundaries, file/runtime mapping, practical
  C/C++ reconstruction, meaningful names, callers/callees, side effects/state,
  cross-game equivalents, evidence, useful negative results, and explicit
  low/medium/high confidence.
- No implementation, patch, generator, or test derived from disassembly,
  decompilation, or live-memory analysis may be committed until its reusable
  findings are documented in canonical knowledge. Include that knowledge
  update in the same commit as the first dependent implementation. Do not
  delete or discard the supporting analysis artifacts until confirming that
  every reusable finding and useful negative result was promoted.
- Keep reusable Ghidra projects or focused exports under
  `@analysis/disassembly/<target>/`. Do not dump unfiltered listings or
  transient guesses merely to satisfy documentation.
