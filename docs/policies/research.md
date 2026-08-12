# Research and knowledge policy

- Prefer reproducible CLI/scripted workflows when practical and state the tools
  used.
- Read the relevant topic/component knowledge before repeating research. For
  game-file investigations, begin with
  [`../knowledge/game/files/README.md`](../knowledge/game/files/README.md).
- Treat the entire `@disassembly/` tree as a read-only evidence
  archive. Inspect its existing projects and exports without modifying their
  contents or metadata. Never open a Ghidra project there in write mode,
  reanalyze it, rename its symbols, regenerate or replace its exports, change
  its filesystem protection, or bypass that protection through a writable copy.
  Do not preserve unfiltered listings or transient guesses merely to satisfy
  documentation.
- Keep observations, inferences, hypotheses, contradictions, confidence, and
  discriminating experiments distinct. A plausible interpretation is not a
  fact or an implementation model another agent must inherit.
- Record new unresolved hypotheses as explicitly labelled sections in the
  relevant domain-owned knowledge document.
- Every substantive disassembly, decompilation, or live-memory task promotes
  confirmed function roles, callers/callees, state behavior, mappings, runtime
  observations, and useful negative results to the
  [domain-owned knowledge hierarchy](../knowledge/README.md) or canonical
  component data before presenting a derived result and before cleanup. Derived
  implementations include that knowledge in the same delivery. Record
  game/binary identity, ranges, file/runtime mapping, reconstructed behavior,
  meaningful names with original symbols and addresses, side effects,
  cross-game equivalents, evidence, and confidence without writing names back
  into the disassembly archive. An instruction to stop or skip validation does
  not defer promotion; do not discard supporting analysis before it is complete.
- `@tools/CCSFileExplorerMSF` is the default CCS explorer.
