# Build, PCSX2, and runtime-testing policy

Read `scripts/README.md`, `docs/PROJECT_CONTEXT.md`, and `docs/LOGGING.md` for
the current command implementation and build records. Do not duplicate their
drift-prone implementation details here.

## Test workflow

### Default workflow

1. Form a hypothesis.
2. Implement a candidate.
3. Validate it manually or with candidate-specific automation.
4. Obtain valid runtime evidence and explicit user acceptance.
5. Add permanent tests only when they provide meaningful regression
   protection.

### Candidate validation

- Hypotheses, candidates, and unconfirmed fixes must not add to or alter the
  permanent tracked test suite.
- Agents may run existing tests and create automated candidate checks.
- Candidate checks remain task-owned and outside normal test discovery and
  builds until acceptance.
- Compilation, agent testing, screenshots, and candidate checks do not
  establish user acceptance.

### TDD exception

- TDD may be used only when explicitly declared in the task plan and approved
  by the user.
- The plan identifies the exact behavior or safety contract and the
  independent evidence establishing it.
- TDD may define an already-established requirement; it must not invent
  expected behavior for an unresolved hypothesis.
- Passing a TDD test proves implementation compliance, not that the requirement
  itself was correct.
- If investigation changes the requirement, revise or remove the obsolete test
  before continuing. Approved TDD tests may enter the permanent suite with the
  implementation.

### Acceptance gate

- User-visible or gameplay behavior requires explicit user acceptance of that
  exact result before permanent tests are added.
- Static-only or nonvisual acceptance requires explicit user approval.
- Plan approval, agent runtime evidence, matching screenshots, successful
  compilation, and passing checks never imply user acceptance.

### Permanent tests

- Do not add stupid checks. Every check must have a clear, decision-relevant
  failure meaning tied to accepted behavior or a documented safety contract.
- Permanent tests are optional. Add one only when it independently detects a
  meaningful regression in accepted behavior or a documented safety contract.
- Tests must not merely restate the current implementation or require chosen
  values, addresses, constants, hashes, structures, algorithms, or complete
  generated output to remain unchanged.
- A test must not reconstruct the implementation and compare it with itself.
- Automated inspection of compiled instructions is allowed when it verifies
  documented machine-code requirements necessary for the shipped patch.
- Exact instruction bytes may be frozen only when independently established as
  the required contract and explicitly approved by the user.

### Lifecycle and execution

- After acceptance, useful candidate checks may be promoted into permanent
  tests; the rest are discarded.
- Remove tests for rejected, reverted, or superseded approaches with those
  approaches.
- When an accepted implementation changes, review its tests against accepted
  behavior; never mechanically update expectations merely to make the new
  implementation pass.
- Run the full suite at meaningful integration boundaries, not repeatedly
  during hypothesis iteration.

Core principle: test approved behavior and independently established safety
requirements, not whatever implementation happens to exist today.

## ISO builds

- Shared `build/` contains only Latest, at most Previous, and when needed
  Test. Latest and Test builds stage beside their destination as
  `.building` and remove staging files on failure.
- A standard build discards an identical verified candidate without rotation
  or atomically promotes a changed candidate and rotates history. Candidate
  composition in Test mode updates Test only.
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
  `na228 worker work/<task title>/build/<name>.iso`, with staging beside the output
  and structured records under the same task's `logs/`. Agents never invoke
  bare `na228`, `na228 b`, or bare `na228 t`.
- In compact recipes, `t` runs Test and `bt` builds then runs Test. Explicit
  `na228 build t` builds Test without launching. Isolated output
  uses the explicit `worker` command.
  Neither mode runs the test suite. Run the builder
  suite only with `.\tests\run.ps1`.
  Verify every validation command's documented semantics before running it;
  never infer behavior from a short flag.
- Worker-output builds never touch Latest, Previous, Test, promotion,
  preflight, shared records, PNACH aliases, actualization, or PCSX2.
- Temporary or hypothesis ISOs remain under the owning task while they have a
  named future use and are deleted when useless.
- Standard logs report `ISO result: unchanged|updated` and rotation. Test
  logs report `ISO result: test`, whether it changed, `rotation: no`, and
  that PCSX2 was left running.

## User PCSX2 and agent runtimes

- Runtime injection is development evidence, not release acceptance. User
  interactive injection and isolated workstream testing are separate
  workflows: users may use the maintained watcher, while agents use only the
  maintained savestate-based test command against a task-owned runtime.
- Every development runtime-injection candidate, including user watcher and
  agent test candidates, compiles and links `src/hot_reload_message.c`, installs
  its visible marker call, and treats that source as a rebuild input. The marker
  is development-injection infrastructure and never enters normal profile or
  release composition.
- `@pcsx2_dev` and `@pcsx2_stable` are the user's protected read-only
  installations. Agents may read and copy from them but never create, modify,
  move, delete, link, launch, control, or write through hardlinks into either
  installation, except for an ISO launch explicitly requested by the user.
- When the user explicitly asks to launch an ISO, use `@pcsx2_dev` by default;
  use `@pcsx2_stable` only when the user requests stable or the exact task is an
  approved stable compatibility/release check. Do not substitute an isolated
  worker PCSX2. That request authorizes only the requested launch, not other
  user-PCSX2 changes or control.
- `@pcsx2_dev/sstates/`, `@pcsx2_stable/sstates/`, and their `snaps/`
  directories are user read-only libraries. Copy chosen inputs with provenance
  into the task's `inputs/sstates/` or `inputs/screenshots/`. When a workstream
  needs a savestate that the user has not supplied, stop and ask the user for
  that exact state; do not create or navigate to a substitute state.
- When PCSX2 is needed, create the task-owned runtime only with
  `@pcsx2_scripts/copy_worker.ps1 -WorkerRoot work/<task title>`. It copies the
  read-only compiled `@pcsx2_clean` template and the required shared BIOS into
  `work/<task title>/pcsx2/`; agents never assemble that base runtime manually.
  An agent may then copy any other shared assets for which it has a concrete
  task- or test-related reason from `@pcsx2_files`. Any asset category,
  including input profiles, recordings, memory cards, cheats, and
  GameSettings, is allowed. Assign a PINE port unique among live agent
  instances and operate only that copy. Other workstream copies/processes are
  off-limits.
- Shared Latest, Previous, and Test ISOs are mutable user files. A worker
  PCSX2 process, injection build, or other worker command must never open those
  shared paths. Pass only an independent full copy under
  `work/<exact task title>/inputs/isos/` to worker launch and injection
  commands; no other worker ISO location is valid. Never use a symlink or
  hardlink.
- Treat each NA2 savestate batch and its runtime dependencies as one atomic
  intake bundle. Before implementation or runtime iteration begins, preserve:
  the independent compatible ISO; its SHA-256, serial, and CRC; the hashes of
  every resident or overlay payload whose addresses the planned work imports;
  and either the exact matching payload-builder record and `symbol_map.tsv` or
  a complete set of independently verified resident-symbol overrides for all
  selected closures. Copy rotation-sensitive records into
  `work/<exact task title>/inputs/runtime-records/<payload-sha256>/` while they
  still exist, and link that path from the batch provenance. A reference-game
  state needs its own state/screenshot provenance but no NA2 payload map.
- A batch is not injection-ready merely because its state and ISO load. If its
  required payload identity or linking metadata is absent, report that at
  intake and request the smallest exact replacement input immediately; do not
  begin implementation and discover the deficiency during candidate testing.
  Never use the newest Latest or produce a replacement build as a substitute.
- Keep every ISO copy and runtime-metadata bundle required by an active
  compatible batch or current test. Delete a superseded worker ISO only after
  no active case references it. Delete remaining worker ISOs when runtime work
  ends only when no active batch still requires them. Preserve provenance and
  the small runtime-metadata records after obsolete images are removed.
- If `work/<task title>/pcsx2/` already exists when new runtime work begins,
  its owning task inspects it before reuse. The inspection covers PCSX2
  configuration and PINE port, Injection Lab or other hot-reload PNACH state,
  savestates, screenshots and `snaps/`, logs, caches, memory cards, cheats,
  GameSettings, input profiles, and input recordings.
- Preserve anything still needed in the task's proper `inputs/`, `outputs/`,
  `logs/`, reusable scripts, canonical patch data, or knowledge before deleting
  the old runtime. Generated PNACH and hot-reload outputs are disposable once
  their useful source changes and evidence have been promoted. Rerun the
  maintained copy command to recreate the whole portable copy from
  `@pcsx2_clean`, add only concretely required assets, and configure its unique
  PINE port before launch. No coordinator or other workstream performs bulk
  replacement.
- Agent-only PCSX2 testing stays hidden. The maintained worker launcher uses
  PCSX2 no-GUI mode, suppresses any remaining render window, and verifies after
  launch that the launched process owns no visible top-level windows. Passing
  `-WindowStyle Hidden`, passing `-nogui`, or intending a hidden launch is not
  sufficient evidence. If the read-back check finds a visible worker window or
  the launcher cannot keep the process hidden, terminate only that newly
  launched worker process and fail the launch.
- PINE and maintained operation plans may load a user-supplied state, capture
  output, or perform bounded memory operations, but never navigate emulator or
  game menus. Do not inject window messages or keystrokes to manufacture a
  required game position. A worker instance may be visible only when the user
  must personally inspect or interact with it; before launch, state exactly
  what is required from the user. Never expose, restore, activate, or foreground
  an instance merely for agent automation.
- Agent savestate-based C iteration uses only
  `scripts/injection/inject_candidate.ps1`. The script receives the task-owned compatible
  ISO, canonical source/entry, task-owned overlay plan, supplied savestate slot,
  and task-owned PINE port; it builds the candidate, reloads the state and
  waits for completion, applies the candidate, invalidates the JIT, and
  resumes. Agents do not invoke `build.py` and `apply.py` separately for
  runtime testing. The agent path does not generate or install PNACH files,
  synchronize cheat directories, maintain install/restore records, invoke
  specialized intermediate writers, or use filesystem watchers.
- `scripts/injection/watch.ps1` is user-only interactive convenience.
  It may automate the same compile/link and direct-PINE operations for the user,
  but agents never run or depend on it.
- Never save or serialize a complete savestate solely to obtain a screenshot.
  Extract an existing state's embedded `Screenshot.png` directly. For a fresh
  runtime frame, invoke `@pcsx2_scripts/pine.py screenshot` against the
  task-owned PINE port and poll that worker's `snaps/` tree recursively for the
  fresh PNG. Agents never use window capture, screenshot hotkeys, window
  messages, or foregrounding. Capture a new savestate only when the state
  itself is a required artifact.
- Builds and single-ISO launch commands never probe or close any PCSX2 process.
- Bare `na228`, direct game-selector launches, and input-profile generation
  through `workshop input [profile]` are user-only.

## Input-profile synchronization

- Builds and launches never generate CRC-specific PNACH or GameSettings files.
  NA2.28 uses the serial-wide files documented in the repository policy.
- `workshop input` regenerates every input-profile combination from canonical
  overrides without changing GameSettings assignments. `workshop input
  <profile>` also regenerates every combination, then assigns the selected
  profile variants in every configured GameSettings file.
