# Reverse-engineering research policy

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
- Record reverse-engineering findings and only the evidence needed to assess
  them in the relevant knowledge document. Do not record temporary file names
  or other details that do not affect the finding.
- `@tools/CCSFileExplorerMSF` is the default CCS explorer.
