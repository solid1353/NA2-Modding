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

## Default validation

- Documentation-only changes require no validation.
- For code changes, run unit tests.
- After implementation and earlier checks are complete, build changes that can
  affect built bytes. Any later byte-affecting change requires another build.
- Agents build only through `na228 build <config>`, using `b` by default. Never
  use build-and-launch commands for validation.
- PCSX2 fork is built using its repository instructions.

## Runtime validation

- Agents must not directly launch, attach to, command, screenshot, probe, or
  close any PCSX2 process.
  Runtime validation is outside the agent's reasoning, responses, and actions
  unless the user explicitly instructs the agent to use a specific maintained
  [E2E](../workflows/e2e_validation.md),
  [input-recording with markers](../workflows/input_recording_with_markers.md), or
  [input-recording without markers](../workflows/input_recording_without_markers.md) workflow.
  Agents invoke only the requested workflow's entrypoints and inspect its
  outputs; the workflow owns emulator control. Execution is not user acceptance.

## Validation behavior and tests

- After user acceptance, fix every failing maintained test discovered during
  the work before committing, unless evidence shows that a concurrent task or
  another task's uncommitted changes caused it. In that case, leave it unchanged
  and report the conflicting ownership.
- A script may fail or discard its output only when validation shows the primary
  result is invalid, unsafe, or unusable. Report other validation failures as
  warnings; making them fatal requires explicit user approval.
- Before `ver`, do not propose, plan, create, or modify tests.
  Modifying tests for PCSX2 fork is allowed.
- Keep candidate-specific documentation provisional until acceptance; retain
  only documentation for the accepted result.
- Unit tests must detect a meaningful regression in accepted behavior or a
  documented safety contract using the smallest practical isolated inputs. Do
  not restate source data, freeze incidental implementation details, mirror the
  implementation, or rerun the production pipeline.

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
