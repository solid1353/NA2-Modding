# PCSX2 workflows draft

Status: tracked discussion draft. This is not yet canonical policy or an
implementation contract.

In discussion, **UW** means user workflow and **WW** means workstream workflow.

## Boundary

- User interactive work and agent work are separate workflows.
- Agents do not work with cheats or PNACH files at all: they do not inspect,
  copy, create, modify, install, actualize, enable, or remove them.
- The Injection Lab compiler/linker remains useful. Its user watcher and its
  cheat-based transport are not part of WW.
- Runtime injection is development evidence, not release acceptance. Accepted
  behavior still needs a clean normal build and the appropriate integration
  validation.

## User workflow

1. Launch the visible development PCSX2 installation.
2. Navigate the game, create savestates, and capture screenshots manually.
3. For interactive C iteration, optionally run the user-only Injection Lab
   watcher against the user-owned PCSX2 environment.
4. Edit and save canonical C; the watcher recompiles, relinks, refreshes the
   user's runtime candidate, and reports failures in the console.
5. Use stable PCSX2 only for explicit compatibility or release validation.

UW may use the user's own shared cheat setup. Nothing in WW depends on or
alters it.

## Workstream workflow

1. Create or refresh only the workstream's task-owned PCSX2 clone from
   `@pcsx2_clean`; assign a unique PINE port and keep the process hidden.
2. Copy only assets required by the concrete task, including a user-supplied
   savestate when runtime positioning is needed. Keep cheats disabled and do
   not access any cheat directory.
3. Load the supplied state while emulation is stopped.
4. Compile and link canonical C plus the task-owned overlay plan through the
   Injection Lab frontend into a transport-neutral process-local build result:
   - linked image bytes and base address;
   - resolved symbol addresses;
   - dispatchers and active-entry pointers;
   - guarded data and caller writes.
5. In the same process, apply those addressed writes directly through PINE to
   the task-owned PCSX2. No intermediate transport file is required.
6. If executable memory that may already have been translated was changed,
   invalidate the affected EE recompiler/JIT state, then resume emulation. Pure
   data writes do not require JIT invalidation.
7. Capture evidence through the maintained hidden-worker screenshot interface.
8. If the supplied state has already passed the code that must be changed,
   request an earlier state instead of adding a workaround.
9. After user acceptance, integrate the same canonical source and declarations
   through the normal builder and validate a clean launch/build as required.

Agents do not use the watcher, filesystem synchronization, install/restore
state, shared PCSX2 installations, or task-local wrapper scripts for this flow.

## Transport-neutral build result

The result is an ordinary Python object that exists only while the production
adapter is running. It is not shared memory, EE memory, a daemon, or a
persistent artifact.

The compiler/linker constructs the result once. The selected consumer then
uses it immediately:

- WW direct mode sends its addressed writes through PINE.
- UW compatibility mode serializes the same result through its existing
  interactive transport.
- Candidate checks may inspect it without contacting PCSX2.

When the adapter process exits, the object disappears.

## Direct-PINE application

The current production adapter already computes the linked image, symbol
addresses, dispatchers, active pointers, and resolved caller replacements. It
then converts those values into PNACH text. WW replaces only that final
transport stage:

1. Connect to the task-owned PCSX2 PINE port.
2. Read and validate every guarded caller range before changing memory.
3. Write the linked code and data into the selected inactive bank.
4. Write the fixed dispatchers and their active-entry pointers.
5. Write the guarded caller hooks or resident redirects.
6. Invoke code-cache invalidation when executable addresses that may already
   have run were changed.
7. Read back guarded writes and report a concise result.

## Implementation plan

1. Replace contradictory PCSX2/C-injection rules in `AGENTS.md` and the testing
   policy with UW, WW, and the absolute no-cheats boundary for agents.
2. Refactor the existing Injection Lab production adapter so compile/link
   returns the transport-neutral process-local build result instead of coupling
   the linker result to PNACH generation.
3. Add direct PINE application to that existing adapter entry point:
   compile/link, apply linked image and guarded overlay writes, invalidate
   executable code when required, and return a concise result. Do not add
   another wrapper script or persistent install-state lifecycle.
4. Preserve the current user watcher and its user-owned interactive behavior.
   It may consume the same transport-neutral result through its existing path.
5. Ensure WW never reads or writes cheat directories and never emits PNACH
   files.
6. Validate WW against the current Font candidate using only an isolated
   task-owned PCSX2 clone: load the supplied state stopped, apply the candidate,
   invalidate executable changes, resume, capture, and verify that no cheat
   file changed.
7. Update the maintained Injection Lab documentation and give Font the exact
   command and sequencing contract.

## Constraints

- Do not modify Font-owned canonical files or task artifacts.
- Do not add identity/hash enforcement, backups, cleanup commands, restart
  rituals, or recovery state unless they are functionally required and
  explicitly approved.
- Do not create a general-purpose runtime protocol or a new script around two
  direct operations.
- Preserve backward compatibility for existing one-entry and multi-entry
  overlay plans where it does not retain the WW PNACH dependency.

Recommended implementation effort: High.
