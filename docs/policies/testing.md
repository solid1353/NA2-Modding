# Build, PCSX2, and runtime-testing policy

Read `scripts/README.md`, `docs/PROJECT_CONTEXT.md`, and `docs/LOGGING.md` for
the current command implementation and build records. Do not duplicate their
drift-prone implementation details here.

## Permanent tests

- Hypotheses, candidates, and fixes awaiting runtime confirmation or explicit
  user acceptance must not add to or alter the tracked permanent test suite.
- Workers may check them manually or with disposable task-owned checks. Such
  checks stay outside normal build/test discovery, are not committed as
  permanent coverage, and are deleted when no longer needed.
- Permanent coverage begins only after the exact behavior is confirmed.
  Static-only coverage requires the user's explicit approval.
- Permanent tests enforce documented accepted behavior, not an address,
  constant, byte sequence, hash, structure, or algorithm merely because the
  current candidate uses it. Remove coverage for a rejected or superseded
  approach with that approach.

## ISO builds

- Shared `build/` contains only Current, at most Previous, and when needed
  Candidate. Standard and Candidate builds stage beside their destination as
  `.building` and remove staging files on failure.
- A standard build discards an identical verified candidate without rotation
  or atomically promotes a changed candidate and rotates history. Candidate
  mode updates Candidate only.
- Agents decide whether a full ISO is necessary from scope, risk, and required
  evidence. Use narrower validation when sufficient.
- Never build an agent ISO merely because executable inputs changed or for
  generic validation. Before building, identify the exact runtime fact that
  only the ISO run can establish, prove that every required input or savestate
  will exercise the newly built bytes, and confirm that narrower validation
  cannot establish the same fact. If any condition fails, do not build.
- An agent ISO build is permitted only when an already available compatible
  savestate reaches the exact target without navigation, the test concerns
  boot/startup behavior requiring no navigation, or the user explicitly
  requests that ISO build. Otherwise, do not build.
- Before savestate-based validation of file-backed overlay or resident-payload
  changes, determine whether loading that state restores the modified
  executable regions. If it does, do not build or launch until an
  exact-guarded task-owned conversion or a user-supplied post-build state is
  available. An unconverted stale state cannot validate the patch.
- Agent builds use only
  `na2 -t work/<task title>/build/<name>.iso`, with staging beside the output
  and structured records under the same task's `logs/`. Agents never invoke
  bare `na2`, `na2 -b`, or bare `na2 -t`.
- In both `na2 -t` and `_na2.ps1 -t`, `-t` is an ISO-build switch: without an
  output path it builds and actualizes Candidate; with a worker output path it
  builds that isolated ISO. It is never a test-suite switch. Run the patcher
  suite only with
  `python -B -m unittest discover -s na2_patcher/tests -p 'test_*.py'`.
  Verify every validation command's documented semantics before running it;
  never infer behavior from a short flag.
- Worker-output builds never touch Current, Previous, Candidate, promotion,
  preflight, shared records, PNACH aliases, actualization, or PCSX2.
- Temporary or hypothesis ISOs remain under the owning task while they have a
  named future use and are deleted when useless.
- Standard logs report `ISO result: unchanged|updated` and rotation. Candidate
  logs report `ISO result: candidate`, whether it changed, `rotation: no`, and
  that PCSX2 was left running.

## User PCSX2 and agent runtimes

- `@pcsx2_user` and the repository-root `pcsx2` convenience link are the user's
  protected installation. Agents may read and copy from it but never create,
  modify, move, delete, link, launch, control, or write through hardlinks into
  it, except for an ISO launch explicitly requested by the user.
- When the user explicitly asks to launch an ISO, launch that ISO through
  `@pcsx2_user`; do not substitute an isolated worker PCSX2. That request
  authorizes only the requested launch, not other user-PCSX2 changes or control.
- `@pcsx2_user/sstates/` and `snaps/` are user read-only libraries. Copy chosen
  inputs with provenance into the task's `inputs/sstates/` or
  `inputs/screenshots/`. When a workstream needs a savestate that the user has
  not supplied, stop and ask the user for that exact state; do not create or
  navigate to a substitute state.
- When PCSX2 is needed, copy the complete read-only `@pcsx2_clean` template to
  `work/<task title>/pcsx2/`, assign a PINE port unique among live agent
  instances, and operate only that copy. Other workstream copies/processes are
  off-limits.
- Agent-only PCSX2 testing stays hidden. PINE and maintained operation plans
  may load a user-supplied state, capture output, or perform bounded memory
  operations, but never navigate emulator or game menus. Do not inject window
  messages or keystrokes to manufacture a required game position. A worker
  instance may be visible only when the user must personally inspect or
  interact with it; before launch, state exactly what is required from the
  user. Never expose, restore, activate, or foreground an instance merely for
  agent automation.
- Builds and single-ISO launch commands never probe or close any PCSX2 process.
- Bare `na2`, launch selectors, standalone `act`, `na`, and UI pair-launch
  commands are user-only.

## Actualization

- User-owned Current/Previous/Candidate workflows may run the maintained
  actualization pipeline automatically; worker builds never actualize.
- `act na2` manages only the configured NA2.28 Current/Previous/Candidate
  identities, CRC cheat links, and GameSettings. Current keeps the template's
  `[MemoryCards]` section; Previous and Candidate omit it. Identity collisions
  are deduplicated with Current taking precedence. The configured memory card
  is never copied or modified.
- `act input` regenerates the configured NA2 comparison input profile.
- `act links` creates/verifies only configured project-to-user-PCSX2 file
  hardlinks and refuses differing occupied counterparts without deleting
  unrelated user files.
