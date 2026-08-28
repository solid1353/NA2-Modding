# Game modding and research policy

## Modding

### Builder, binary, and donor changes

- Before modifying builder composition, use the relevant sections of
  `@builder/README.md` and the affected
  [feature documentation](../features/README.md) as the canonical contract. Do
  not recreate retired schemas or assumptions from historical notes.
- Never edit binaries manually. All binary changes go through reproducible
  scripts and guarded canonical data.
- Prefer one injection over multiple binary edits when they implement one
  behavior and a stable guarded hook can express it clearly in C or assembly.
  Keep isolated constant or instruction replacements as direct edits.
- Preserve file sizes unless the user explicitly approves expansion of the
  affected DATA.CVM, ELF, BIN, AFS, CCS, or ISO structure.
- Prefer verified canonical NUN5 data/bytes when suitable. When donor data is
  unsuitable, document the intended NA2 behavior and evidence for replacement
  bytes.

### PNACH

- Use PNACH mainly to test runtime hypotheses and adjust the runtime logic of
  other source games.
- Fixed-address writes require a region proven resident and stable for their
  lifetime. Runtime overlay tests require a proven load-state or signature
  guard; never make unguarded overlay or dynamic-heap writes.

## Research and knowledge

- Distinguish observations, inferences, hypotheses, contradictions, confidence,
  and experiments; never present hypotheses as facts or required implementation
  models.
- Every request requiring substantive disassembly, decompilation, or live-memory
  research authorizes and requires promotion of confirmed function roles,
  callers/callees, state behavior, mappings, runtime
  observations, and useful negative results to the
  [domain-owned knowledge hierarchy](../knowledge/README.md) or canonical
  component data before presenting a derived result and before cleanup. Derived
  implementations include that knowledge in the same delivery. Record
  game/binary identity, ranges, file/runtime mapping, reconstructed behavior,
  meaningful names with original symbols and addresses, side effects,
  cross-game equivalents, evidence, and confidence without writing names back
  into the disassembly archive. Record unresolved hypotheses as such in the
  relevant domain knowledge document. An instruction to stop or skip validation
  does not defer promotion; do not discard supporting analysis before it is complete.
- `@tools/CCSFileExplorerMSF` is the default CCS explorer.
