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
- Treat the entire `@analysis/disassembly/` tree as a read-only evidence
  archive. Inspect its existing projects and exports without modifying their
  contents or metadata. Never open a Ghidra project there in write mode,
  reanalyze it, rename its symbols, regenerate or replace its exports, change
  its filesystem protection, or bypass that protection through a writable copy.
  Do not preserve unfiltered listings or transient guesses merely to satisfy
  documentation.
- Keep observations, inferences, hypotheses, contradictions, confidence, and
  discriminating experiments distinct. A plausible interpretation is not a
  fact or an implementation model another agent must inherit.
- Confirmed function roles, callers/callees, state behavior, mappings, runtime
  observations, and useful negative results belong in the
  [domain-owned knowledge hierarchy](../knowledge/README.md) or beside
  canonical component data. Record meaningful function and variable names
  there with the original disassembly symbol and address; do not write those
  names back into the disassembly archive.
- Record new unresolved hypotheses as explicitly labelled sections in the
  relevant domain-owned knowledge document.
- Every substantive disassembly, decompilation, or live-memory task promotes
  reusable findings before any derived implementation candidate or research
  result is presented, and before cleanup. Record game/binary identity, ranges,
  file/runtime mapping, reconstructed behavior, meaningful names,
  callers/callees, side effects/state, cross-game equivalents, evidence, useful
  negative results, and explicit confidence. An instruction to stop or skip
  validation does not defer this promotion requirement.
- Before committing an implementation derived from reverse engineering, include
  its reusable knowledge update in the same delivery. Do not discard supporting
  analysis until every reusable finding and useful negative result is promoted.
- Optional reusable analysis, diagnostic, extraction, or research tools may be
  promoted to an existing research/tooling area under the implementation
  boundary in root
  [`AGENTS.md`](../../AGENTS.md#implementation-boundaries). Do not preserve
  ordinary scratch scripts or integrate a tool into
  production/build/CI/runtime without authorization.
- `@tools/CCSFileExplorerMSF` is the default CCS explorer.
