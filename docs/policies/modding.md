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

## Research and evidence

- Use GhidrAssist MCP for substantive disassembly and decompilation. Follow the
  [shared runbook](<../../../UN Workshop/docs/runbooks/ghidrassistmcp.md>).
- Distinguish observations, inferences, hypotheses, contradictions, confidence,
  and experiments; never present hypotheses as facts or required implementation
  models.
- Every knowledge document must contain a `## Research coverage` section with
  these bullets:
  - **Assigned scope:** what the document investigates.
  - **Exploration depth:** how thoroughly each part was investigated.
  - **Confirmed coverage:** what the investigation established.
  - **Unresolved or untested:** what remains incomplete or unknown.
  - **Deliberate exclusions and overlap:** the document's ownership boundaries.
  - **Evidence limitations:** what the available evidence cannot establish.
- During any investigation that requires disassembly inspection record
  reverse-engineering findings and only the evidence needed to assess
  them in the relevant knowledge document. Do not record temporary file names
  or other details that do not affect the finding.
- `@tools/CCSFileExplorerMSF` is the default CCS explorer.
