# Build, PCSX2, and runtime-testing policy

Read `scripts/README.md`, `docs/PROJECT_CONTEXT.md`, and `docs/LOGGING.md` for
the current command implementation and build records. Do not duplicate their
drift-prone implementation details here.

## ISO builds

- Shared `build/` contains only Current, at most Previous, and when needed
  Candidate. Standard and Candidate builds stage beside their destination as
  `.building` and remove staging files on failure.
- A standard build discards an identical verified candidate without rotation
  or atomically promotes a changed candidate and rotates history. Candidate
  mode updates Candidate only.
- Agents decide whether a full ISO is necessary from scope, risk, and required
  evidence. Use narrower validation when sufficient.
- Agent builds use only
  `na2 -t work/<task title>/build/<name>.iso`, with staging beside the output
  and structured records under the same task's `logs/`. Agents never invoke
  bare `na2`, `na2 -b`, or bare `na2 -t`.
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
  `inputs/screenshots/`. Agent-created states belong under task artifacts.
- When PCSX2 is needed, copy the complete read-only `@pcsx2_clean` template to
  `work/<task title>/pcsx2/`, assign a PINE port unique among live agent
  instances, and operate only that copy. Other workstream copies/processes are
  off-limits.
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
