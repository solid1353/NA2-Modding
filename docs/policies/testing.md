# Validation and testing policy

## Default validation

- Documentation-only changes require no validation.
- For code changes, run unit tests.
- After implementation and earlier checks are complete, build changes that can
  affect built bytes as final validation. Any later byte-affecting change
  requires another build.
- Agents build only through `na228 build <config>`, using `b` by default. Never
  use build-and-launch commands for validation.
- Build or reuse the canonical cached ISO only when selected validation requires
  assembly. An exact verified-registry hit is sufficient evidence; never create
  a task ISO or hardlink.
- Runtime execution of the cached ISO is limited to the
  [input-recording validation workflow](../workflows/input_recording_validation.md);
  E2E is separately selected.

## Runtime validation

- Agents must not directly launch, attach to, command, screenshot, probe, or
  close any PCSX2 process. Runtime execution is permitted only through the
  maintained E2E and input-recording validation workflows; agents invoke their
  entrypoints and inspect their outputs, while the workflows own emulator
  control.
- When the user provides an input recording for the task, follow the
  [input-recording validation workflow](../workflows/input_recording_validation.md).
  Its agent replay is runtime validation, not user acceptance of the result.
- A standalone savestate may support diagnosis but does not validate a change.
- Before relying on an ISO as runtime evidence, verify that it is the intended
  build using the minimum sufficient evidence. Do not request or record extra
  identity metadata.
- Extract `Screenshot.png` from an existing savestate when that frame is enough;
  do not create a complete state solely to obtain a screenshot.

## Validation behavior and tests

- After user acceptance, fix every failing maintained test discovered during
  the work before committing, unless evidence shows that a concurrent task or
  another task's uncommitted changes caused it. In that case, leave it unchanged
  and report the conflicting ownership.
- A script may fail or discard its output only when validation shows the primary
  result is invalid, unsafe, or unusable. Report other validation failures as
  warnings; making them fatal requires explicit user approval.
- Before `ver`, do not propose, plan, create, or modify tests.
- Keep candidate-specific documentation provisional until acceptance; retain
  only documentation for the accepted result.
- Unit tests must detect a meaningful regression in accepted behavior or a
  documented safety contract using the smallest practical isolated inputs. Do
  not restate source data, freeze incidental implementation details, mirror the
  implementation, or rerun the production pipeline.
- Real-source, production-scale, or full-pipeline tests require explicit
  approval and must cover a regression the normal build cannot detect.
