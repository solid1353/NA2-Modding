# Validation and testing policy

## Default validation

- Documentation-only changes require no validation.
- For code changes, run unit tests.
- After implementation and earlier checks are complete, build changes that can
  affect built bytes as final validation. Any later byte-affecting change
  requires another build.
- For output-preserving refactors, build identical pre-change baseline and
  candidate inputs and compare their recorded SHA-256 hashes.
- Agents build only through `na228 build -c <configuration>`, using `base` by
  default. Never use normal user build routes or alter their outputs and records.
- Build or reuse the canonical cached ISO only when selected validation requires
  assembly. An exact verified-registry hit is sufficient evidence; never create
  a task ISO or hardlink.
- Runtime execution of the cached ISO is limited to the
  [input-recording validation workflow](../workflows/input_recording_validation.md);
  E2E is separately selected.

## Runtime validation

- When the user provides an input recording for the task, follow the
  [input-recording validation workflow](../workflows/input_recording_validation.md).
  Its agent replay is runtime validation, not user acceptance of the result.
- A standalone savestate may support diagnosis but does not validate a change.
- For agent PCSX2 operations, use the selected verified hash-cache image rather
  than shared role paths or an arbitrarily newer ISO.
- Before relying on an ISO as runtime evidence, verify its identity and
  provenance from the available SHA-256, serial, CRC, build record, payload
  hashes, and symbol map. Request any required missing metadata.
- `@pcsx2_dev` is the only PCSX2 installation agents may use. Do not create,
  copy, select, launch, or control another installation or runtime, including
  `@pcsx2_fork` or a chat-owned copy.
- An explicit PCSX2 operation authorizes only the requested operation. It does
  not authorize probing, closing, or otherwise controlling an existing PCSX2
  process. Every agent-launched PCSX2 process must run in the background.
- Extract `Screenshot.png` from an existing savestate when that frame is enough;
  do not create a complete state solely to obtain a screenshot.
- For a fresh runtime frame, request a PINE screenshot from the explicitly
  authorized `@pcsx2_dev` port and poll that installation's `snaps/` tree for
  the new PNG.
- Do not use window capture, screenshot hotkeys, window messages, or
  foregrounding as substitutes.

## Validation behavior and tests

- After user acceptance, fix every failing maintained test discovered during
  the work before committing, unless evidence shows that a concurrent task or
  another task's uncommitted changes caused it. In that case, leave it unchanged
  and report the conflicting ownership.
- A script may fail or discard its output only when validation shows the primary
  result is invalid, unsafe, or unusable. Report other validation failures as
  warnings; making them fatal requires explicit user approval.
- Do not create or modify tests for a task result before user acceptance.
- Keep candidate-specific documentation provisional until acceptance; retain
  only documentation for the accepted result.
- Unit tests must detect a meaningful regression in accepted behavior or a
  documented safety contract using the smallest practical isolated inputs. Do
  not restate source data, freeze incidental implementation details, mirror the
  implementation, or rerun the production pipeline.
- Real-source, production-scale, or full-pipeline tests require explicit
  approval and must cover a regression the normal build cannot detect.
