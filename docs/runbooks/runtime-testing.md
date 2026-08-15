# Runtime testing runbook

This runbook owns exact safety and execution procedures for NA2 builds, PCSX2,
savestate intake, direct-PINE injection, and runtime screenshots. Read it
only when those operations are part of the task. Validation selection and patch
acceptance remain canonical in
[`../policies/testing.md`](../policies/testing.md).

## PCSX2 installation

- `@pcsx2_dev` is the only PCSX2 installation agents may use. Do not create,
  copy, select, launch, or control another PCSX2 installation or runtime,
  including `@pcsx2_fork` or a chat-owned copy.
- `@pcsx2_dev` remains protected and user-owned. Agents may read it or copy
  individual evidence from it, but do not create, modify, move, delete, or link
  anything inside it unless the user explicitly requests the exact action.
- An explicit PCSX2 operation uses `@pcsx2_dev` and authorizes only the exact
  requested operation. It does not authorize probing, closing, or otherwise
  controlling an existing PCSX2 process.

## Runtime ISO provenance

- For agent PCSX2 operations against a pre-existing ISO, do not open shared
  Latest, Previous, Manual, or E2E Test ISO paths directly. Use the selected
  verified hash-cache image directly.
- Preserve the ISO's SHA-256, serial, CRC, applicable build record,
  payload hashes, and symbol map before relying on it for runtime evidence.
- Do not substitute the newest shared ISO when the required identity or
  metadata is absent. Ask for the smallest exact missing input.

## Agent ISO builds

- Use `na228 build -c <configuration>`. It builds or reuses the canonical
  hash-named cache image and keeps operational and
  structured records under `work/<chat title>/logs/`.
- Use the canonical cached ISO path directly. Do not create a task-owned
  ISO or hardlink, and do not delete the shared cache image after validation.
- They do not touch Latest/Previous, Manual/E2E Test outputs or their role
  records, promotion, PNACH, GameSettings, or PCSX2 state.

Current shared-build and user-facing command behavior is documented by
`na228 help`, [`../../scripts/README.md`](../../scripts/README.md), and
[`../../e2e/README.md`](../../e2e/README.md), not redefined here.

## Input-recording candidate replay

The complete lifecycle is in the
[input-recording validation workflow](../workflows/input_recording_validation.md).
When that workflow requires candidate replay, use the cached ISO and
an explicit task-owned capture path:

```powershell
ws <cached-iso-path> -s <recording> <task-owned-candidate-path>
```

Do not omit the candidate capture path or use Workshop's default capture path.

## Screenshots and evidence

- Extract `Screenshot.png` from an existing savestate when that frame is enough;
  do not create a complete state solely to obtain a screenshot.
- For a fresh runtime frame, run
  `@pcsx2_scripts/pine.py screenshot` against the explicitly authorized
  `@pcsx2_dev` PINE port and poll that installation's `snaps/` tree for the new
  PNG.
- Do not use window capture, screenshot hotkeys, window messages, or
  foregrounding as substitutes.
