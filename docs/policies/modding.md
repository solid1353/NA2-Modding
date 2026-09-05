# Game modding policy

## Builder, binary, and donor changes

- Before modifying builder composition, use the relevant sections of
  `@builder/README.md` and the affected feature document as the canonical
  contract. Do not recreate retired schemas or assumptions from historical
  notes.
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

## PNACH

- Use PNACH mainly to test runtime hypotheses and adjust the runtime logic of
  other source games.
- Fixed-address writes require a region proven resident and stable for their
  lifetime. Runtime overlay tests require a proven load-state or signature
  guard; never make unguarded overlay or dynamic-heap writes.
