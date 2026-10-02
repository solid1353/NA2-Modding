# Resident task system

The resident task framework in the retail NA2 (`SLPS-25837`) boot ELF,
centered on `FUN_001cfe50` through `FUN_001d0590`, coordinates real EE kernel
threads. A task record does not contain per-pass update and draw callbacks.
Its function pointer at `+0x0C` is passed to `CreateThread`, and the resident
start wrapper ultimately calls `_StartThread(thread_id, task_record)`, so the
entry runs once as an independent thread and receives its own task record in
`a0`. The manager is another task record and also serves as the head sentinel
of a flat, singly linked list: the global head is at `0x00607504` and the tail
is at `0x00607508`. Ordinary records are appended in creation order. There is
no framework parent pointer, child list, priority-sorted list, semaphore, or
central update/draw dispatch. This is a static-analysis result, not a timing
trace. Binary identity and resident address conversion follow
[Retail game file identities](../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** the resident task framework around `FUN_001cfe50`
  through `FUN_001d0590`: allocation and registration, the task record and
  callback layout, statically provable manager ordering, ownership, wait/wake
  behavior, termination and destruction, and representative resident callers;
  the root pacing and engine gate that control manager service; and the
  creator ancestry of the playback companion and sound tasks.
- **Exploration depth:**
  - Exhaustive within the core range: every instruction of the 13 core
    functions in the [core function map](#core-function-map) was traced and
    compared with the decompiler. Constructor stores, kernel calls, flag
    precedence, both list traversals, both destruction sequences, and the
    manager-entry installation were checked against raw MIPS.
  - Exhaustive for direct resident calls and constructions: aligned
    instruction-word scans classified every direct `jal` to the family, and
    all 24 ordinary constructions were followed through creator setup and
    their entry functions. Every static task name was decoded from the clean
    ELF bytes. Dynamically synthesized calls are not covered.
  - Exhaustive for explicit encodings, bounded by aliasing: whole-resident
    scans covered head/tail references, `TerminateThread`/`DeleteThread`
    pairs, task-control halfword reads, `+0x14` and runtime `0x0010` stores,
    cleanup registration, and core API address materializations.
  - Bounded overlay coverage: clean `BTL.BIN` and `ETC.BIN` were searched
    only for direct calls and static references to the family.
  - Sampled cross-version corroboration: the NUN5 family for record shape,
    state transitions, immediate removal, and manager structure; the NUN3
    family only for its shifted record, gate predicates, and
    suspend/pending-resume helper.
  - Root pacing and engine gate: the pacing helper, counter interrupt
    callback, registration, gate state machine, SIF `+0x506` producer,
    embedded engine aliases, and all 13 aligned `addiu ...,0x500` candidates
    were read in instructions. `+0x192` and `+0x500` store scans covered
    aligned resident, BTL, and ETC instructions. The playback-companion and
    sound-descendant creator paths were read completely.
- **Confirmed coverage:** the `0x4C` record map, exact core function and file
  addresses, list globals and ownership boundary, start/defer rules, manager
  transition and barrier order, wait/wake predicates, two-pass termination,
  cleanup ABI and call order, the immediate-removal quirk, all direct resident
  creator lifecycles, static call counts, and the absence of a central
  update/draw callback. The interrupt-count root pacing path, engine
  bit-`0x04` gate transition order, the SIF callback's engine `+0x506` store,
  MPEG's separate low-two-bit consumer, playback companion publication, sound
  creator ancestry, and the direct `TerminateThread`, `DeleteThread`, and
  `ExitDeleteThread` call counts are also established. Negative conclusions
  are qualified to their scan boundary.
- **Unresolved or untested:** the producer, unit, and domain meaning of
  `+0x14`; the domain meaning of control `0x0002`; any reachable producer of
  runtime `0x0010`; meanings of opaque `+0x44/+0x48/+0x4A`; reachability of
  the force-wake wrapper; behavior under real allocation or kernel-call
  failures; non-exempt natural-return behavior; indirect or runtime-generated
  callers; actual independent-thread execution, update/draw, or presentation
  order; measured root pacing cadence; producers and domain meanings of engine
  gate bits `0x01/0x02`; and any nonzero installation of engine callback
  `+0x500`.
- **Deliberate exclusions and overlap:** Adventure code was not inspected.
  Threads and semaphores that do not use the task record belong to
  [EE kernel threads and synchronization](kernel_threads_and_sync.md);
  display submission to [Render submission](rendering/render_submission.md); scene
  evaluation to [Scene playback owners](scene_playback_owners.md); audio
  service to [Battle audio](../gameplay/session/battle_audio.md); file loading to
  [Resident file and archive services](../game/files/runtime_services.md);
  controller routing to [Controller input](controller_input.md); and
  Save/Load behavior to [Save data](../game/save_data.md). Representative
  callers were followed only far enough to establish task ownership and
  lifetime.
- **Evidence limitations:** no runtime trace, scheduler log, or timing capture
  exists. Addresses, instruction order, field accesses, and direct static call
  graphs have strong static evidence; kernel scheduling, cadence, runtime
  reachability, pointer aliasing, and overlay behavior outside the BTL/ETC
  reference scans are not established.

## Task record

`FUN_001d0090`, `FUN_001d0110`, and `FUN_001d04f0` allocate exactly `0x4C`
bytes. `FUN_001cfe50` initializes that record and allocates its stack.

| Offset | Size | Established meaning | Constructor value / evidence |
| ---: | ---: | --- | --- |
| `+0x00` | 4 | Next task record | Zero; the global tail appends through this field. |
| `+0x04` | 4 | Name string pointer | Defaults to `NO NAME` at `0x00602C18`; `FUN_00105d70` and many task entries replace it. |
| `+0x08` | 2 | Signed EE initial priority | Constructor argument; copied into the `ee_thread_t.initial_priority` field. |
| `+0x0A` | 2 | EE kernel thread ID | `-1` until `CreateThread`; the returned ID is stored as a halfword. |
| `+0x0C` | 4 | EE thread entry pointer | Constructor argument; copied into `ee_thread_t.func`. |
| `+0x10` | 2 | Runtime/lifecycle flags | Zero; interpreted by the manager as detailed below. |
| `+0x12` | 2 | Control/policy flags | Zero; callers OR bits through `FUN_00105d80` or direct stores. |
| `+0x14` | 4 | Signed wake/hold gate | Zero. Waits return when it is `<= 0`; the manager auto-wakes a sleeping task only when it is exactly zero. Its producer and unit are unresolved. |
| `+0x18` | 4 | Effective stack allocation size | `max(requested, 0x800) + 0x400`; passed to `CreateThread`. |
| `+0x1C` | 4 | Allocated stack pointer | Result of `FUN_00117700(effective_size)`. |
| `+0x20` | 4 | Cleanup callback argument | Zero; passed as the sole argument to the callback at `+0x24`. |
| `+0x24` | 4 | Cleanup callback pointer | Zero; called after unlinking and before terminating/deleting the thread. |
| `+0x28..+0x40` | `0x1C` | Seven caller-owned payload words | Zero. Direct resident creators and entries use various subsets; the manager never interprets them. |
| `+0x44` | 4 | Opaque word | Zero; no direct use was found in the 24 resident task paths inventoried below. |
| `+0x48` | 2 | Opaque tail field | Zero; no core interpretation found. |
| `+0x4A` | 1 | Opaque tail field | Zero; no core interpretation found. |
| `+0x4B` | 1 | Padding or opaque byte | Not written by the constructor. |

The two callback fields are confirmed independently by `FUN_001e0ee0`, whose
`MOTHER` entry installs `LAB_001e0ed0` at `+0x24` and zero at `+0x20`.
`LAB_001e0ed0` is a no-op `jr ra`, but the manager and immediate-removal path
both invoke it using the established `callback(context)` ABI.

Among all 24 inventoried direct creators and entries, this is the only
confirmed cleanup-callback registration. The ABI is therefore live even
though its only statically recovered resident registration has no side effect.

Caller-defined relationships live in the payload or in an owning object. For
example, `FUN_001a0890` creates a primary play task and a forced-start
`PlayLock` task, then places the primary task pointer in the `PlayLock` record
at `+0x28`. That is an application convention, not a generic parent/child
link. The save worker similarly keeps its task handle in its owning object's
`+0x5C` field rather than in a framework-owned relationship.

All 24 recognized direct resident creation paths and their entry functions
were checked for payload conventions. Confirmed uses reach through `+0x40`;
no direct use of `+0x44`, `+0x48`, or `+0x4A` was found outside constructor
initialization. This is a scoped negative result rather than proof against an
indirect alias or excluded overlay.

NUN5 preserves the same `+0x48` halfword and `+0x4A` byte zeroing, while
the older NUN3 layout preserves the pattern at shifted offsets `+0x4C/+0x4E`.
The fields are therefore inherited storage, but no framework-level
meaning is established; byte `+0x4B` (and NUN3 `+0x4F`) remains untouched.

## Flags

### Runtime flags at `+0x10`

| Mask | Static meaning | Transitions |
| ---: | --- | --- |
| `0x0001` | Deferred start | `FUN_001cff00` sets it instead of immediately starting a task whose signed numeric priority value is smaller than the caller's. The manager clears it and calls `FUN_0015ee20(thread_id, record)`. |
| `0x0002` | Termination requested | `FUN_001d01b0` sets it. The manager handles it before resume or wake states. |
| `0x0004` | Termination observed | On the first eligible pass with `0x0002`, the manager sets this bit. On the next eligible pass it unlinks and destroys the task. |
| `0x0008` | Cooperative sleep/yield state | Both wait helpers set it before `SleepThread`. The manager clears it and calls `WakeupThread` when `+0x14 == 0`. |
| `0x0010` | Pending-resume state retained from the older framework | The NA2 manager clears it and calls `ResumeThread`, but no NA2 resident producer was found. The older NUN3 homolog has an explicit helper that sets this bit and suspends the target, confirming the state-machine role without proving normal NA2 use. |
| `0x0020` | One-pass barrier-bypass token | Immediate starts and `FUN_001d02f0` set it. The manager's barrier pass consumes and clears it instead of waiting for the task that pass. It is not a persistent “started” state. |

### Control flags at `+0x12`

| Mask | Static meaning | Evidence and limit |
| ---: | --- | --- |
| `0x0001` | Protect from the ordinary termination-request API | `FUN_001d01b0` is a no-op while this bit is set. It does not protect against `FUN_001d0220` or destruction after `0x0002` has already been set. |
| `0x0002` | Written but resident-task-layer inert; domain meaning unknown | It is set on several long-lived tasks. An exhaustive resident scan found no task-control read that interprets it, and `FADE END` leaves it set while successfully self-requesting termination. |
| `0x0004` | Cooperative-barrier exemption | The manager does not spin waiting for this task to reach a lifecycle state. Background MPEG, load/decode, and save-worker tasks use it. |
| `0x0008` | Engine-gate bypass | The manager services this task even when `(*(u8 *)(*0x006073FC + 0x192) & 7) != 0`. Without it, lifecycle service is deferred while those low three bits are nonzero. The engine state itself is not named here. |

Normal startup makes the first ordinary record entry `FUN_00113530`. The main
initializer pre-sets control bit `0x0008`, and the entry later ORs `0x0007`, so
the persistent task ends with control value `0x000F`. Its name becomes `PAD`
at `0x00602A18`. The next record is entry `FUN_001e0ee0`, named `MOTHER` at
`0x00602CE0`. The list therefore begins `NO NAME` manager -> `PAD` ->
`MOTHER` in the normal boot path.

The bit-`0x0002` negative result covers all 40 signed-halfword and 11
unsigned-halfword reads at offset `+0x12` in the clean resident listing. The
only task-layer consumers are the bit-`0x0001` check in `FUN_001d01b0` and
the bit-`0x0008`/`0x0004` checks in `FUN_001d0590`. Indirectly aliased access
or excluded Adventure code remains outside that claim.

Within the 24 direct resident entries, `PAD` is the only record that acquires
control `0x0008`. Protected finite entries demonstrate the bit-`0x0001`
protocol directly: `FADE END` and `ZgBreakScreen` clear protection before
self-requesting termination, whereas persistent protected tasks leave it set.

## Core function map

Addresses are clean resident EE virtual addresses. File offsets follow the
[address conventions](../game/files/file_identities.md#address-conventions).
Names in the “export symbol” column are retained exactly so the
evidence can be found again without relying on the semantic labels.

| EE VA | ELF offset | Export symbol | Established role, callers/callees, and side effects |
| ---: | ---: | --- | --- |
| `0x001CFE50` | `0xCFF50` | `FUN_001cfe50` | Initializes a caller-supplied `0x4C` record and allocates its stack through `FUN_00117700`. Called by both allocation helpers and manager initialization. |
| `0x001CFF00` | `0xD0000` | `FUN_001cff00` | Builds an `ee_thread_t` from record `+0x0C/+0x1C/+0x18/+0x08`, calls `CreateThread`, stores `+0x0A`, and either starts through `FUN_0015ee20` or sets deferred-start bit `0x0001`. `FUN_0015ee20` validates thread state and ultimately calls `_StartThread(thread_id, record)`. |
| `0x001D0000` | `0xD0100` | `FUN_001d0000` | Explicit-record cooperative wait. Sets runtime bit `0x0008` and calls `SleepThread`; it calls no timer, VBlank, or semaphore API. |
| `0x001D0090` | `0xD0190` | `FUN_001d0090` | Allocates, constructs, and appends a dormant record. Ghidra's C prototype incorrectly says `void`; the MIPS ABI returns the record in `v0`, as its callers expect. |
| `0x001D0110` | `0xD0210` | `FUN_001d0110` | Allocates, constructs, appends, and calls `FUN_001cff00(record, 0)`. The base ELF has three recognized direct call sites. |
| `0x001D01B0` | `0xD02B0` | `FUN_001d01b0` | Asynchronously requests termination unless control bit `0x0001` is set. A self-request sleeps immediately; an external requester returns without joining or freeing. |
| `0x001D0220` | `0xD0320` | `FUN_001d0220` | Immediate unlink/callback/thread termination/thread deletion/stack free/record free. Its only resident direct caller is `FUN_00105320`, at two MPEG teardown call sites. It starts its search at the second ordinary record, as detailed below. |
| `0x001D02F0` | `0xD03F0` | `FUN_001d02f0` | Force-wake helper: writes `+0x14 = 0`, clears runtime `0x0008`, sets `0x0020`, and calls `WakeupThread(+0x0A)`. Its sole resident direct xref is `FUN_001ce870`. |
| `0x001D0340` | `0xD0440` | `FUN_001d0340` | Gets the current kernel thread ID, disables interrupts with `FUN_00167da0`, scans ordinary records for matching `+0x0A`, restores interrupts through `FUN_00167df0`, then performs the same cooperative wait. If the thread is unregistered it executes one plain `SleepThread` and returns only after an external wake. |
| `0x001D0440` | `0xD0540` | `FUN_001d0440` | Under the same DI/EI guard, returns the first ordinary record whose `+0x04` string equals the query through `FUN_0017c238`; otherwise returns null. No direct base-ELF caller is recognized. Adventure callers were intentionally not inspected. |
| `0x001D04F0` | `0xD05F0` | `FUN_001d04f0` | Creates the manager/head record with entry `FUN_001d0590`, priority `0x18`, requested stack `0x1000`, force-starts it, writes `0x00607504`, and initializes the tail at `0x00607508` to the same record. Called once by `FUN_001c13f0`. |
| `0x001D0560` | `0xD0660` | `FUN_001d0560` | Calls `WakeupThread` on the manager's thread ID. Its only resident caller is the main loop in `FUN_001c13f0`. The clean call is at `0x001D0570`; `0x001D0578` is function epilogue, not a task/update/draw callback. |
| `0x001D0590` | `0xD0690` | `FUN_001d0590` | Manager thread entry. Runs the lifecycle traversal and cooperative barrier, brackets them with `FUN_001081b0` and `FUN_00108490`, then sleeps until the next wake. Installed only as the manager entry pointer. |

An aligned-word scan of the clean ELF, cross-checked against the raw listing,
gives this complete direct-`jal` census. It avoids relying on Ghidra's
incomplete xref headers:

| Target | Resident `jal` instructions | Interpretation |
| --- | ---: | --- |
| `FUN_001cfe50` | 3 | The two ordinary allocators and manager initialization. |
| `FUN_001cff00` | 22 | All ordinary starts plus the allocate-and-start and manager-init internals; one call is absent from Ghidra's xref header. |
| `FUN_001d0000` | 42 | Explicit-record waits; constant arguments are classified below. |
| `FUN_001d0090` / `FUN_001d0110` | 21 / 3 | Exactly the 24 ordinary constructions inventoried below. |
| `FUN_001d01b0` | 18 | Eleven self-requests and seven external request sites. |
| `FUN_001d0220` / `FUN_001d02f0` | 2 / 1 | Two MPEG immediate removals and the one force-wake wrapper. |
| `FUN_001d0340` | 51 | Current-task waits; constant arguments are classified below. |
| `FUN_001d0440` | 0 | No direct resident name lookup. |
| `FUN_001d04f0` / `FUN_001d0560` | 1 / 1 | One initialization and one manager-wake site. |
| `FUN_001d0590` | 0 | It is installed as an entry pointer at `0x001D0514`, not called with `jal`. |

A second clean-byte scan looked for aligned absolute pointer words and nearby
MIPS `lui` plus `addiu`/`ori` address constructions. No context-valid indirect
reference to the constructor, allocators, start, wait, termination, removal,
force-wake, lookup, init, or wake APIs was found in the resident, BTL, or ETC
images. The sole core address construction is `FUN_001d0590` at
`0x001D0510..0x001D0514`, where manager initialization installs its entry.
Apparent words equal to `0x001D0000` occur inside packed scalar data tables and
have no code xref or address construction. The 24 ordinary creations are
therefore complete for the recovered in-scope static call graph, while runtime
or excluded-overlay synthesis remains possible.

`FUN_00105d40` is a thin `FUN_001cff00(record, 0)` wrapper;
`FUN_00105d70` writes the name at `+0x04`; and `FUN_00105d80` ORs control
bits at `+0x12`. These small wrappers are used by the MPEG task setup at
`FUN_001057b0`.

`FUN_001ce870` loads the task handle at its owner object's `+0x9C` and passes
it to force wake. `FUN_001ce8a0` assigns the `PlayDecode` task to that exact
owner field, so the force-wake target is established even though no static
invocation of the wrapper was recovered.

Name lookup returns a borrowed record pointer; there is no reference count or
uniqueness check, and the first equal name in append order wins. A newly
appended dormant record initially has the shared `NO NAME` pointer. Depending
on the caller, its final name is installed either before start or by the entry
after it begins running, so the name is descriptive metadata rather than a
stable registration key enforced by the framework.

The name setter stores the pointer directly: it does not copy or own the
string, and neither destruction path frees it. Most recovered names are static
strings, while the primary play task points at an owner-resident string. Any
dynamic name storage must therefore outlive lookup use by caller convention.

Name installation is split across both sides of the start boundary. Thirteen
records receive their final recovered name before `FUN_001cff00`: both MPEG
tasks, the primary play task and `PlayLock`, `LoadingInfo`, the three persistent
play workers, the three one-shot load-stage workers, `LoadBg`, and
`SP Skill Play`. The other eleven enter their task function with the shared
`NO NAME` value and replace it there: `PAD`, `MOTHER`, `SOUND`,
`Load ROFS_Data`, `SAVE SYS`, `FADE END`, `ZgBreakScreen`, `Load File All`,
`SND_RPC`, `SND_RPC2`, and `MC_CHECKDIR`. A lookup during the append-to-entry
window can consequently observe or match `NO NAME`; the framework has no
atomic named-registration operation.

No direct call or aligned absolute function-pointer word for
`FUN_001d0440` was found in the resident, BTL, or ETC binaries. That makes
name lookup unreachable by the recovered in-scope static call graph, not safe
to call concurrently or proven globally unused; Adventure is excluded.

## Allocation, registration, and starting

The ordinary construction path is:

1. Allocate `0x4C` bytes through `FUN_00117150`.
2. Initialize the record and allocate its stack through `FUN_001cfe50`.
3. Store the record into the old tail's `+0x00` and make it the new global
   tail. No priority sorting occurs.
4. Start separately with `FUN_001cff00`, or use `FUN_001d0110` to request this
   immediately after append.

This path presupposes one successful `FUN_001d04f0` initialization. Ordinary
append writes through the global tail without checking it; manager wake and
ordinary-record lookup likewise dereference the global root. The core has no
uninitialized-state guard or second-initialization teardown.

With start argument bit zero set, `FUN_001cff00` always starts the thread and
sets runtime token `0x0020`. With that argument clear, it obtains the caller's
`ee_thread_t.current_priority` through `ReferThreadStatus`. If the new record's
signed priority is numerically less than the caller's current priority, it
sets deferred-start bit `0x0001`; otherwise it starts immediately and sets
`0x0020`. The manager later clears `0x0001` and starts deferred records in list
order.

“Deferred” applies only to the start syscall. `CreateThread` has already run,
the halfword thread ID is installed, and the kernel thread is dormant. If a
record has both deferred-start `0x0001` and termination-request `0x0002` when
the manager sees it, start precedence clears `0x0001` and starts the entry;
termination begins on a later pass rather than canceling creation.

Setting deferred-start bit `0x0001` does not wake the manager. Deferred work
waits for the independently driven `FUN_001d0560` manager wake, whose only
resident caller is the root loop.

Both the record allocator and stack allocator request `0x10` alignment from
their underlying heap routine. `FUN_001cff00` copies the current `$gp` into
`ee_thread_t.gp_reg`. It stores the signed 32-bit `CreateThread` result in the
record as a halfword and later consumers sign-extend that field.

The stack-local `ee_thread_t` passed to `CreateThread` has only `func`,
`stack`, `stack_size`, `gp_reg`, and `initial_priority` explicitly written.
Its `status`, `current_priority`, `attr`, and `option` words contain ambient
stack data at that call. The later `ReferThreadStatus` call populates the same
buffer before `current_priority` is read. This documents writes visible in the
binary; it does not assert which ignored/reserved inputs the EE kernel consumes.

The resident start wrapper `FUN_0015ee20` performs its own guarded
`ReferThreadStatus` and calls `_StartThread(thread_id, record)` only when the
reported status word is exactly `0x10`; otherwise it returns an error. Task
creation and the manager ignore that return and update lifecycle flags as if
the requested transition completed.

The code assumes successful allocation and kernel-thread creation:

- `FUN_001d0090` appends a null allocation and changes the global tail to null
  on failure; a later append would write through null.
- `FUN_001d0110` additionally calls `FUN_001cff00(0, 0)` after such a failure.
- `FUN_001d04f0` similarly stores a null head and calls the start function.
- `FUN_001cfe50` does not reject a failed stack allocation, and
  `FUN_001cff00` does not branch on `CreateThread` or `ReferThreadStatus`
  failure. It and the manager also ignore the start wrapper's return value.

Deletion skips kernel termination/deletion only when the stored halfword ID is
exactly `-1`. A different negative `CreateThread` error would therefore be
truncated into the record, passed to the start wrapper, and later treated as a
thread ID by teardown. This remains a failure-path consequence, not an
observed normal-run failure.

These are static failure-path facts. They do not establish that an allocation
failure occurs in normal play.

Ordinary allocation appends the fully initialized but still dormant record
before the caller writes its name/control/payload and invokes start. There is
no separate “construction complete” bit or list lock, so the framework relies
on scheduling/ownership discipline during that window. Allocate-and-start
helper `FUN_001d0110` likewise appends before calling the start routine.

The resident call patterns respect the API distinction. Every task needing
creator-supplied payload uses dormant `FUN_001d0090`, fills the payload, and
then starts it. The three `FUN_001d0110` uses are `SND_RPC`, `SND_RPC2`, and
`MC_CHECKDIR`; their entries install their own names/control or result fields
and require no creator write after the helper returns. `FUN_001d0110` offers no
post-start initialization window if the new kernel thread is immediately
scheduled.

A raw-machine-code start audit closes the construction inventory. The 21
`FUN_001d0090` constructions are covered by 19 task-specific start call sites
plus the shared MPEG start wrapper, which is invoked for two records. One call
inside `FUN_001d0110` covers its three callers, and manager initialization has
one force-start call, for 22 resident `jal FUN_001cff00` instructions in all.
Ghidra's function xref header lists 21 because it omits the `Load File All`
start at `0x003B37CC`; the clean ELF bytes there are
`C0 3F 07 0C 00 00 00 00`, the expected `jal 0x001CFF00` plus `nop` delay
slot. Thus every one of the 24 ordinary construction paths has a recovered
start path; none is merely appended and intentionally left uncreated.

## Manager pass and ordering boundary

Each iteration of `FUN_001d0590` has this statically established order:

1. Call `FUN_001081b0(*0x006073FC)`.
2. Traverse from `manager->next` toward the tail in append order. A record is
   eligible when the engine gate's low three bits are zero or its control
   `0x0008` bit is set. For each eligible record, handle exactly one state in
   precedence order: deferred start, termination, resume, then cooperative
   wake.
3. Change the manager thread's priority from `0x18` to `0x76`.
4. Traverse ordinary records again. Consume `0x0020` when present. Otherwise,
   unless control `0x0004` exempts the record, spin until
   `(runtime_flags & 0x001B) != 0`.
5. Restore the manager priority to `0x18`.
6. Call `FUN_00108490(*0x006073FC)`.
7. Call `SleepThread`; `FUN_001d0560` supplies the next manager wake.

The engine-byte predicate gates only the first lifecycle-transition traversal.
The second barrier traversal still visits every ordinary record; its only
per-record exemption is control `0x0004`, apart from consuming a one-pass
`0x0020` token.

The first traversal's exact one-action precedence is:

| Predicate on an eligible record | Mutation and side effect |
| --- | --- |
| runtime `& 0x0001` | Clear `0x0001`; call the start wrapper. Other pending bits wait for a later manager pass. |
| else runtime `& 0x0002`, without runtime `0x0004` | Set termination-observed bit `0x0004`. |
| else runtime `& 0x0002`, with runtime `0x0004` | Unlink, callback, delete thread, and free. |
| else runtime `& 0x0010` | Clear `0x0010`; call `ResumeThread`. |
| else `gate == 0` and runtime `& 0x0008` | Clear `0x0008`; call `WakeupThread`. |
| otherwise | No lifecycle action. |

The barrier mask `0x001B` contains deferred-start, termination-request,
cooperative-sleep, and pending-resume bits; it excludes the observed bit
`0x0004` and token `0x0020`. Immediate start sets `0x0020`, so the next barrier
consumes that token without requiring a yield. Manager-started deferred tasks
do not receive `0x0020`; unless control `0x0004` exempts them, they must run and
reach one of the mask states before the same manager iteration can finish.

The barrier is a literal load/test/back-branch spin with no timeout,
`SleepThread`, ready-queue rotation, or kernel-status check. This connects two
otherwise separate failure facts. If the start wrapper fails for a deferred,
non-exempt record, the manager has already cleared `0x0001` and can spin in the
same iteration because the task never publishes another mask bit. A failed
immediate start still receives `0x0020`, buying one barrier pass, but the next
manager iteration can spin after consuming it. A non-exempt entry that returns
with no lifecycle bit has the same terminal state. Control `0x0004` avoids the
spin, but the framework still retains the failed or naturally returned record.

On the EE kernel, a smaller numeric priority has higher scheduling priority.
Changing the manager from `0x18` to `0x76` gives ordinary non-exempt tasks an
opportunity to run while the manager's barrier loop has an empty spin body.
Every directly created task with a numeric value above `0x76` (`0x7D`,
`0x7E`, or `0x7F`) sets control `0x0004`; such a task could not outrank the
manager at `0x76`, so its barrier exemption is structurally necessary. This
explains the predicate but still does not establish update/draw or timing
semantics.

Direct ordinary priorities span `0x14` through `0x7F`. `SAVE SYS` at `0x14`
is the only inventoried ordinary task with a numerically smaller (higher)
priority than the manager's normal `0x18`; every other direct task is `0x19`
or larger. This constrains possible preemption but still does not convert list
order into execution order.

`FUN_001c13f0` initializes this manager, appends `PAD`, appends `MOTHER`, and
then repeatedly executes `FUN_001083a0(engine)` followed by `FUN_001d0560`.
This proves call sequence, not cadence.

The boot sequence is more specific than a generic append: the main thread
first changes its priority to `0x78`. `FUN_001d04f0` stores the new root at
`0x00607504`, force-starts its priority-`0x18` manager, and only after the
start call returns stores the same pointer as the tail at `0x00607508`. It then
appends `PAD` (`0x19`) and `MOTHER` (`0x23`). Both numeric priorities are
smaller than the creator's `0x78`, so both start requests become deferred flag
`0x0001`; a later manager pass starts them in append order. This static
bootstrap sequence does not by itself prove when a kernel context switch
occurs inside the start call.

List order therefore proves only lifecycle-service and barrier-scan order. It
does not prove task execution order, update order, draw order, VBlank cadence,
or a frame rate. Task entries are independent EE threads with their own kernel
priorities, and task-specific work occurs inside those entries. The record has
no update/draw function slots. The `FUN_001081b0` and `FUN_00108490` calls are
known pre/post boundaries, but assigning every operation inside them or the
task threads to a universal update/draw phase would exceed the static evidence.

The manager/head record is excluded from both traversals. Its force-start path
sets runtime `0x0020`, but no ordinary traversal consumes that token. The root
therefore remains a sentinel with a manager-only lifecycle; no root teardown
or other root-token clearer was found.

Every direct resident reference to the head/tail globals is confined to
`FUN_001d0090`, `FUN_001d0110`, `FUN_001d0220`, `FUN_001d0340`,
`FUN_001d0440`, `FUN_001d04f0`, `FUN_001d0560`, and `FUN_001d0590`. The head
has one writer, manager initialization, and is never cleared. Tail writers are
initialization, the two append helpers, and the two removal paths. This exact
global-reference audit strengthens the negative manager-teardown result while
remaining subject to dynamically computed or aliased accesses.

## Root pacing and the engine gate

The root loop's wait is separate from a task record's `+0x14` gate and from
the two task sleep helpers. `FUN_001083a0(engine)` reads display-owned
bytes, with these complete branch contracts:

| Engine field / predicate | Root pacing behavior |
| --- | --- |
| `+0x2AD != 0` | Return immediately; no counter wait. |
| `+0x2AD == 0`, `+0x02 == 0` | Busy-poll unsigned byte `+0x00` until it is at least unsigned threshold `+0x01`. Then publish `+0x1B8` from GS CSR bit 13 when `+0x03 == 1`, otherwise publish 1. |
| `+0x2AD == 0`, `+0x02 != 0` | Call `FUN_0012F3F8` and `FUN_0012F540` on every polling iteration until the same unsigned counter/threshold predicate passes. The latter's CRI path performs a plain kernel sleep as detailed below. |

The unsigned loads and compare/back-branches are visible at
`0x001083E4..0x00108400` and `0x00108410..0x0010842C`.
`FUN_00107560(engine, threshold)` writes the threshold byte and resets the
counter. Initialization `FUN_00107F80` selects threshold 1 and polling mode 1.
It temporarily sets `+0x2AD = 1`, then calls display-configuration helper
`FUN_00107340`, which clears it to zero before `FUN_001065A0` installs the
interrupt callback. The completed initialization therefore enables the
counter wait. Later `MOTHER` initialization selects threshold 2 at call
`0x001E11C4` after its readiness barrier. This is a byte-count setting,
not a duration argument. `FUN_00107340` also writes configuration fields
`+0x2A8/+0x2AA/+0x2AC`; none is a task-record field.

The counter producer is `FUN_00108CE0`, installed by
`FUN_001065A0 -> FUN_00150578(0x00108CE0)`. The registration helper removes
any prior handler and calls `AddIntcHandler(2, callback, -1)` before enabling
interrupt channel 2. On each callback invocation, `FUN_00108D70(engine, 1)`
increments byte `+0x00`, wrapping through its byte store. The manager's next
`FUN_001081B0` resets that byte to zero before incrementing the independent
32-bit cycle counter at engine `+0x194`. Interrupt invocations accumulated
between that reset and the root's threshold comparison are therefore distinct
from task sleep/wake cycles and from the engine cycle counter.

The interrupt callback also checks the boot/root thread ID at `0x006074D4`.
When byte `0x00607498` is zero, it calls `iReferThreadStatus` and invokes
`FUN_0015EBA8(root_id)` only for status exactly 4. Otherwise it calls
`FUN_0012F3E0(0)`. This is an additional conditional root-thread wake;
`FUN_001083A0` itself contains no `SleepThread`, and neither branch calls
`FUN_001D0560` directly. The ordinary root loop issues the manager wake after
the pacing helper returns.

The nonzero-`+0x02` branch does not merely busy-poll while servicing opaque
callbacks. `FUN_0012F540` calls `FUN_0014E798`, `FUN_0012F410`,
`FUN_0012FA18`, `FUN_0012F518`, and `FUN_0014E7C8` in that order.
`FUN_0014E798`, `FUN_0012FA18`, and `FUN_0014E7C8` use registered
function pointers; `FUN_0012F410` conditionally resumes/wakes CRI IDs
`0x003D6A9C` and `0x003D6AA0`.
`FUN_0012F518` writes request word `0x003D6A4C = 1` at
`0x0012F530`, then tail-jumps to the plain `SleepThread` wrapper
`FUN_0012E5D0`. It does not set a task record flag. The root cannot reach
the counter comparison or later manager wake until some kernel wake lets
this call return.

The recovered worker-side wake is
`FUN_0012E128 -> FUN_0012F498`. That helper requires the request word to be
1 and the saved creator/root thread at `0x003D6A98` to have status 4 or
`0xC`; it calls `WakeupThread` and clears the request only when the syscall
returns the requested ID. The display interrupt's active-CRI branch
`FUN_0012F3E0 -> FUN_0012F2B8` wakes CRI IDs `0x003D6A90/0x003D6A94`
when their activity flags are clear, and optionally `0x003D6A8C` when the
library mode predicate permits it. It also runs its mode-dependent service
path and optional callback. This separates the root sleep request, worker
wake, interrupt counter increment, and ordinary task-manager wake; none is
a framework parent/child wake protocol.

**Inference, high confidence for this call chain:** the root's manager-wake
requests are bounded by an interrupt-count predicate when pacing is enabled.
This does not establish a one-to-one relation between wake requests, completed
manager passes, task handshakes, displayed frames, or elapsed time. Counter
wrap, the bypass byte, MPEG's alternate threshold settings, independent kernel
wakes, and work before/after the barrier prevent replacing those counts with
a measured time unit. Display submission and completion remain owned by
[Render submission](rendering/render_submission.md#completion-and-packet-lifetime).

### Engine gate bit `0x04`

The low-three-bit gate read by the manager is refreshed before lifecycle
service: `FUN_001081B0` calls `FUN_001086C0(engine)` before the manager's
first task traversal. That state machine unconditionally clears bit `0x04`
at `0x00108718..0x00108724`, advances signed state byte `+0x504`, optionally
calls engine callback `+0x500`, and finally sets bit `0x04` when that callback
pointer is non-null and the resulting signed state is at least 2
(`0x0010894C..0x00108974`). The gate describes the post-transition state in
the same manager iteration, not merely the state at entry.

| Entry state `+0x504` | Established transition |
| ---: | --- |
| 0 | Read `FUN_00133988`; results 1 or `0x20`, with byte `+0x506 == 0`, select state 1. |
| 1 | Select state 2. |
| 2 | Call `FUN_00173328(1)`; result 2 selects state 3 and calls `FUN_00133958(0)`. |
| 3 | `FUN_00173890` results `0x12..0x14` select state 4; all other values select state 2. |
| 4 | Null `+0x508` selects state 0. Otherwise `FUN_00172900(stack_buffer, +0x508)` result 1 selects 0, all other results select 2. |

The initial call `FUN_00133958(state < 3)` forwards that boolean to
`FUN_001407D0`, which stores it at `0x003E5800`; `FUN_00133988` forwards the
word at `0x003E5804` through `FUN_001407B0`. These are observed status/control
dependencies. No player-facing name is assigned to these state numbers here.
With callback `+0x500 == 0`, the state can advance but this routine leaves
gate bit `0x04` clear. With a callback installed, it invokes the callback for
any resulting nonzero state, including state 1, then rereads the state before
deciding whether to gate ordinary tasks. Callback mutation can therefore
affect the final gate value.

A resident direct-displacement scan of byte/halfword/word stores at
`+0x192` and `addiu base, 0x192` found the engine initialization store and
these bit-`0x04` writes. Other aligned matches belong to different object
families; unaligned matches and mirrored program spaces were discarded.
No direct engine producer of bits `0x01/0x02` was established by this bounded
scan. It does not cover a copied pointer, a computed displacement, a wider
overlapping store, or excluded code. The manager continues to test all three
bits, and the independent record gate `+0x14` remains unresolved.

### Callback installation and selected engine aliases

The recovered resident constructor `FUN_00105FC0` allocates `0x530` bytes,
publishes the result at `0x006073FC`, and calls `FUN_00107F80`. That
initializer explicitly clears `+0x500` at `0x00107FCC`, `+0x508` at
`0x00107FD4`, state/control bytes `+0x504..+0x506`, and gate byte `+0x192`
at `0x00108010`. Constructor `FUN_001062A0` initializes only embedded
objects at engine `+0x110/+0x150`; it does not install the engine callback.
The final registration at `0x00108130..0x00108138` supplies
`FUN_00108AF0` and zero to `FUN_001724B0`. As established in the
[CD callback interface](kernel_threads_and_sync.md#callback-registration-and-constructor-reachability),
this is the separate SIF registration, not engine `+0x500` or the
`SceCdCallbackThread` callback.

That registered SIF callback is concrete: `FUN_00108AF0` loads the published
engine pointer through `gp-0x35F4` and stores `1` to engine `+0x506` at
`0x00108AFC`. It takes no task record and does not write the gate byte or
`+0x500`. In state 0, `FUN_001086C0` requires `+0x506 == 0` before entering
state 1; a callback arriving after the state has already advanced is not an
immediate state reset in the recovered transition table. Dispatch is under
the SIF owner's saved `$gp`, so this global lookup is not an unexplained
ambient-register assumption. SIF delivery order remains unresolved.

Aligned byte searches for all four register-base encodings of
`sw ...,0x500(base)` in the resident found only the initializer's zero store.
All 13 low-address aligned `addiu ...,base,0x500` candidates were checked
against their instructions: none forms `engine+0x500`. They load scalar type
values or allocation sizes, or materialize the independent data address
`0x00540500`. The apparent `addiu ...,base,0x192` candidate at
`0x0013F15C` is instead `li a1,0x192` before an indirect device call; it
does not take the engine address. These instruction checks extend the search
beyond a decompiler field spelling, without proving every computed alias.

The actual embedded aliases were also followed. `FUN_001062E0`, including
its `FUN_00110340(base+8)` constructor, and `FUN_0010A1D0` /
`FUN_00109C70` / `FUN_00109FB0` initialize/register the engine's two
`0x40`-byte objects at `+0x110/+0x150`; their inspected local accesses do
not reach engine `+0x192` or `+0x500`. Packet preparation
`FUN_001079C0` rebases the engine by `(+0x194 & 1) * 0x60`, but the scoped
writes then cover `+0x1E0..+0x23F` relative to that rebased pointer, not
either target field. [Render submission](rendering/render_submission.md) owns the
packet details.

The BTL/ETC word-store search adds no engine installation: ETC has no aligned
`sw ...,0x500(base)` match; BTL's sole aligned match is preserved address
`0x00785598` (live `0x007855D8`, complete-file offset `0xD16D8`), storing
literal `2` at an unrelated object offset. The bytes there are
`00 05 22 AE`, preceded by `02 00 02 24`; its surrounding object initialization
also uses fields beyond the engine's `0x530` allocation and does not load the
engine global. No aligned BTL/ETC `sb ...,0x192(base)` match was found.
Overlay address conversion follows
[Retail game file identities](../game/files/file_identities.md#address-conventions).

**Confirmed limit:** the selected resident initialization leaves callback
`+0x500` null; no nonzero installer or engine bit-`0x01/0x02` producer was
recovered through the inspected constructors, aliases, or registrations.
This does not prove that the callback is globally unused. A multi-step rebase,
bulk copy, indirect writer, or excluded code could still supply it. The
pending evidence is a concrete write or copied source value reaching the
published engine object; the existence of a `jalr` consumer alone is not an
installation path. A clearing or teardown path for a nonzero installed
callback also remains unrecovered.

### Other consumers of engine bits `0x01/0x02`

The MPEG main entry tests a narrower mask:
`0x00104090..0x001040A0` loads the same published engine, reads `+0x192`,
tests `& 3`, and branches back to its loop at `0x00103F44` when either low
bit is set. It skips the subsequent `FUN_00103AE0` / `FUN_00103E10`
service calls on that branch, while bit `0x04` alone does not select it.
Both `0x01/0x02` therefore participate in an MPEG scheduling gate as well as
the manager's `& 7` lifecycle gate. Their individual producers and domain
meanings are still unestablished; this consumer is insufficient to name
either bit as a particular pause or shutdown state.

The manager's surrounding helpers also consume `& 7`.
`FUN_001081B0` calls optional engine callback `+0x520` only when that gate
is clear, after `FUN_001086C0`; `+0x520` is a different callback slot.
`FUN_00108490` gates its selected post-barrier service pair, the pointer
copies `+0x80 -> +0x7C` / `+0xF8 -> +0xF4`, and its RCNT0 snapshot at
`+0x04`, while still executing its other surrounding calls. This is a
shared selective gate, not proof that every operation or every independent
thread pauses. The established control-`0x0008` exception applies specifically
to the task manager's first traversal.

## Wait and wake semantics

`FUN_001d0000(record, n)` uses `n` as a local count:

- While `n > 0`, it decrements `n`, marks runtime `0x0008`, and sleeps.
- Once `n <= 0`, it returns only when signed `record->gate <= 0` and
  termination bit `0x0002` is clear.
- If the gate is positive or termination has been requested, it marks
  `0x0008` and sleeps again. A terminating task is consequently left asleep
  for manager destruction rather than returning through ordinary code.

`FUN_001d0340(n)` locates the current record by kernel thread ID and then uses
the same loop. The positive count describes completed sleep/wake cycles,
normally serviced by the manager but also satisfiable by the explicit
force-wake path or another kernel wake. It is not statically established as
frames, milliseconds, refreshes, or VBlanks.

If the current thread is not an ordinary registered record—including the
manager sentinel itself—the helper ignores `n`, executes exactly one
`SleepThread`, and returns only after some external wake. This also happens for
zero or negative `n`; it is not the same fast-return predicate as
`FUN_001d0000(record, n)`.

The clean resident's machine-code call sites use only small positive constants:
the 42 direct `FUN_001d0000` calls pass `n = 1` at 39 sites, `2` at two sites,
and `3` at one site. The 51 direct `FUN_001d0340` calls pass `1` at 45 sites,
`3` at three sites, and `5`, `10`, or `0x3C` once each. Three explicit-record
calls for which the decompiler omitted the second argument were resolved from
live `a1 = 1` in raw MIPS. These counts characterize API use only; the values
still have no statically proven time or frame unit.

The manager's wake predicate is slightly narrower than the wait helper's
return predicate: it wakes a sleeping record only for `+0x14 == 0`, while a
running wait would accept any signed value `<= 0`. An exhaustive in-scope
resident scan found no nonzero writer, incrementer, or decrementer for task
`+0x14`; the only confirmed stores are constructor initialization and the
explicit zero-and-wake path in `FUN_001d02f0`. Pointer aliasing or excluded
overlays could still hide a producer.

This comparison asymmetry is inherited rather than an NA2 decompiler accident.
The older NUN3 `0x50`-byte record keeps the same field at shifted offset
`+0x10`: its wait accepts signed values below one and its manager wakes only on
exact zero. NUN5 preserves the NA2 `+0x14` layout and predicates. None of
that establishes a unit or producer, so “wake/hold gate” remains deliberately
neutral terminology.

The core family uses `SleepThread`, `WakeupThread`, and `ResumeThread`; it does
not implement these waits with an EE semaphore. `FUN_00167da0` and
`FUN_00167df0`, used around current-task and name lookup, are DI/EI interrupt
guards.

## Kernel threads and synchronization outside the task list

The resident also runs EE kernel threads and semaphores that never use the
`0x4C` record: the `SceKerneltopThread` dispatch queue, the alarm-backed
`SceKernelDelayThread` delay, the MPEG buffer semaphore, the CD callback
thread and semaphore set, and six CRI-owned threads. Their contracts belong to
[EE kernel threads and synchronization](kernel_threads_and_sync.md). None adds
a semaphore, parent link, or lifecycle flag to the task record, and none
produces runtime `0x0010`.

## Creator ancestry

### Playback companion and sound descendants

The primary playback record and `PlayLock` are siblings created by
`FUN_001A0890`; the primary entry does not create its companion. The owner
keeps the primary handle at owner `+0x40`, the primary keeps its owner at task
`+0x2C`, and the companion borrows the primary pointer at task `+0x28`.
Primary task `+0x40` has this caller-owned publication protocol:

| Value | Primary publication / companion response |
| ---: | --- |
| 0 | Initial value and value before the cooperative wait; `PlayLock` performs its own one-count task wait. |
| 1 | Primary's update/submission region; `PlayLock` repeatedly loads this field without sleeping. |
| 2 | Primary teardown has finished; `PlayLock` self-requests termination. |

The primary sets 1 at `0x001A0574`, zero at the delay-slot store
`0x001A06C0`, and 2 at `0x001A0850` after `FUN_001A2280`.
`FUN_001A0980` requests primary termination only after `FUN_001A0120`
returns. The companion's exact spin is `0x001A09EC..0x001A0A00`; its wait
at `0x001A0A10` still has live `a1 = 1`, although the decompiler prints only
one argument. No semaphore, framework parent pointer, join, or reference
count is added by this relationship. The primary's numeric priority `0x1B`
is higher than the companion's `0x1E`, but that static relation alone does
not prove a safe interleaving or pointer lifetime under every cancellation.
Scene evaluation and submission remain owned by
[Scene playback callers and owners](scene_playback_owners.md#streamed-worker-scheduling).

Sound has a different creator chain:
`MOTHER` entry `FUN_001E0EE0 -> SOUND` entry `FUN_001D2570 -> SND_RPC`
and `SND_RPC2`. The sound entry writes its shared readiness byte before
calling the two allocate-and-start helpers at `0x001D2720/0x001D2738`.
Those child priorities `0x71/0x72` are numerically larger than the creator's
`0x70`, so the ordinary start routine takes its immediate-start path if that
creator priority has not changed. The caller stores neither returned task
handle; no ancestry is retained in the framework.

`SND_RPC` initializes shared state and repeatedly waits once before doing its
service work. The unanalyzed `SND_RPC2` entry at `0x001D29F0` was recovered
from instruction bytes through `0x001D2A6C`, ending before the next
function at `0x001D2A70`. It installs name pointer `0x003FD718` and control
3, repeatedly calls `FUN_001DA3B0` with a one-count wait while that result is
zero, then waits until shared owner byte `+0x21` is nonzero, calls
`FUN_001D9930`, and repeats. Byte sequences at `0x001D2A28/0x001D2A48`
are `00 40 07 0C` (`jal 0x001D0000`), each preceded by `a1 = 1`.
These are independent task handshakes, not evidence that RPC calls are issued
at a fixed time interval. Audio service meaning belongs to
[Battle audio](../gameplay/session/battle_audio.md).

## Termination, destruction, and ownership

Ordinary termination is asynchronous:

1. `FUN_001d01b0` checks control `0x0001`, sets runtime `0x0002` once, and
   sleeps immediately only when a task requests its own termination.
2. On the next eligible manager pass, `FUN_001d0590` adds runtime `0x0004`.
3. On the following eligible pass, it unlinks the record and repairs the tail
   if needed.
4. It invokes `record->cleanup(record->cleanup_arg)` when non-null.
5. If the thread ID is not `-1`, it calls `TerminateThread` and `DeleteThread`.
6. It frees the stack through `FUN_00117c40` and the record through
   `FUN_00117000`.

The self-request sleep does not set cooperative-sleep bit `0x0008`. A repeated
request after `0x0002` is already set returns without sleeping because the
self-sleep is inside the first-set branch. Neither the request helper nor the
force-wake helper wakes the manager; the resident root loop drives manager
wakes through `FUN_001d0560`.

Unlinking and tail repair happen before the cleanup callback. During the
callback the record and EE thread still exist, but the record is no longer
reachable from the task list. Normal cleanup callbacks execute on the manager
thread; an immediate-removal callback executes synchronously on the
`FUN_001d0220` caller's thread. Both paths ignore the callback's return value,
then terminate/delete the target thread and free its stack before its record.
They also ignore `TerminateThread` and `DeleteThread` results and proceed with
both frees, so kernel-deletion failure has no recovery path in this layer.
The callback and frees still run when the record's thread ID is the constructor
sentinel `-1`; only the two kernel thread calls are skipped. A dormant record
can therefore be destroyed before `CreateThread` if a caller reaches one of
the removal paths during its construction window.

Because teardown unconditionally continues after a cleanup callback, that
callback is not an ownership transfer: it must not free the task record or its
stack itself. Tail repair occurs before callback dispatch, so a callback that
creates another task would at least append through the repaired tail, although
the only confirmed resident callback is the no-op `MOTHER` registration and no
such reentrant use was found.

The engine gate can delay both termination passes for records without control
`0x0008`. An external requester is not joined with destruction; for example,
`FUN_001e1d20` requests termination of the `SAVE SYS` worker and clears the
owner's handle immediately, while actual freeing remains manager-owned.

All 18 resident request sites divide into 11 self-requests and seven external
requests. The external group comprises three play-worker requests in
`FUN_001cde10` plus one each for `LoadingInfo`, a load-context worker,
`SAVE SYS`, and `MC_CHECKDIR`. Several owners wait for a task-owned completion
field before requesting termination; `FUN_001cde10` then releases shared
buffers, and `FUN_001e7940` drops the completed `MC_CHECKDIR` handle entirely.
These are caller protocols, not a core join: the task manager supplies no
completion event, reference count, or synchronous destruction guarantee.

`FUN_001d0220` performs the unlink/callback/kernel-delete/free sequence in its
caller instead of setting the two termination flags. It has a material list
quirk that is visible in the raw MIPS and not a decompiler artifact:

- predecessor begins as `manager->next`;
- candidate begins as `(manager->next)->next`;
- matching therefore starts at the second ordinary record.

It cannot remove the manager or the first ordinary record, and it dereferences
`manager->next` before a null check. Normal startup makes that skipped record
the persistent `PAD` task, which explains the practical precondition but does
not prove the design intent. The only resident direct caller, `FUN_00105320`,
uses immediate removal for the later `MPEG VIDEO DEC` and `MPEG MAIN` records
and then clears their external handles.

Append, manager traversal/removal, and `FUN_001d0220` do not take the DI/EI
guard used by lookup. `FUN_001d0220` also bypasses control-bit protection and
the two-pass runtime protocol. The core therefore assumes cooperative or
external serialization for list mutation; it does not provide an internal
list lock.

The whole resident listing contains exactly two direct `jal TerminateThread`
instructions and exactly two direct `jal DeleteThread` instructions. They are
the paired calls in
`FUN_001d0220` and `FUN_001d0590`; no third direct task-record destruction
route exists in the base executable. `ExitDeleteThread` has one resident
direct `jal` at `0x00172178` in the
[CD callback thread](kernel_threads_and_sync.md#cd-callback-thread-and-semaphore-set),
plus six direct tail `j` instructions in
[CRI entries](kernel_threads_and_sync.md#cri-owned-kernel-threads) at
`0x0012E088`, `0x0012E120`, `0x0012E224`, `0x0012E318`, `0x0012E450`, and
`0x0012E524`. Searches for exact words `C8 76 05 0C` and `C8 76 05 08`,
restricted to aligned low-address resident matches and discarding the two
mirrored copies, establish this distinction. All seven paths are outside
task-record destruction. Indirect syscall wrappers remain outside this count.

No manager teardown path was found. Natural return of an entry is also not a
generic destruction contract: many finite task entries self-request
termination. `PAD` provides a concrete natural-return case: after its
initialization waits, `FUN_00113530` reaches an ordinary return with control
`0x000F` and no termination request. The framework neither polls kernel exit
state nor unlinks it, so its record remains registered; control `0x0004` keeps
that dormant record from blocking the barrier. A non-exempt natural-return
case still needs runtime or caller-specific evidence before assuming cleanup.

Across the 24 direct resident entries, `PAD` is the only confirmed ordinary
return without a termination request, and it is barrier-exempt. Every recovered
non-exempt entry instead remains in a cooperative wait loop or reaches a
self-request protocol. No direct resident example demonstrates safe natural
return for a non-exempt record.

## Direct resident creation inventory

The clean base ELF has 21 direct calls to dormant allocator
`FUN_001d0090` and three direct calls to allocate-and-start helper
`FUN_001d0110`, for 24 ordinary task constructions. The table records the
creator call address so each row can be recovered independently. “Req -> eff”
is requested stack size followed by the constructor's allocated size. A dagger
marks the three `FUN_001d0110` calls; all other rows use `FUN_001d0090` and a
separate start.

| Create call | Entry and installed name | Priority; stack req -> eff | Confirmed control, payload, and lifecycle evidence |
| ---: | --- | --- | --- |
| `0x00105C80` | `FUN_00103ee0`; `MPEG MAIN` (`0x003D1848`) | `0x7D`; `0x4000 -> 0x4400` | Control `0x0004`; external global owns handle; `FUN_00105320` destroys it immediately through `FUN_001d0220`. |
| `0x00105CCC` | `FUN_00101ac0`; `MPEG VIDEO DEC` (`0x003D1858`) | `0x7D`; `0x4000 -> 0x4400` | Control `0x0004`; same external-handle and immediate-destruction pattern. |
| `0x001A08CC` | `FUN_001a0980`; owner-supplied name | `0x1B`; `0x1000 -> 0x1400` | `+0x2C` owner and `+0x30..+0x3C` caller arguments; finite entry self-requests termination. |
| `0x001A0930` | `FUN_001a09d0`; `PlayLock` (`0x003FB668`) | `0x1E`; `0x800 -> 0xC00` | `+0x28` links the primary task; force-started with `FUN_001cff00(record, 1)`; self-requests termination. |
| `0x001C147C` | `FUN_00113530`; `PAD` (`0x00602A18`) | `0x19`; `0x800 -> 0xC00` | Caller pre-sets control `0x0008`, entry ORs `0x0007`; naturally returns after initialization and remains registered. |
| `0x001C14B0` | `FUN_001e0ee0`; `MOTHER` (`0x00602CE0`) | `0x23`; `0xC000 -> 0xC400` | Control `0x0003`; `+0x28/+0x2C` hold boot arguments; installs the no-op cleanup callback; long-lived main task. |
| `0x001CE91C` | `FUN_001cd930`; `LoadingInfo` (`0x003FC050`) | `0x28`; `0x800 -> 0xC00` | No control bits set; cooperative loop; externally terminated. |
| `0x001CED4C` | `LAB_001ce3e0` -> `FUN_001ce410`; `PlayDecode` (`0x003FC060`) | `0x1A`; `0x1000 -> 0x1400` | Control `0x0004`; `+0x28` owner, `+0x2C` completion; signals completion then waits until external termination. |
| `0x001CEDA4` | `FUN_001cdf10`; `PlayRead` (`0x003FC070`) | `0x1D`; `0x1000 -> 0x1400` | Control `0x0004`; same owner/completion and external-termination protocol. |
| `0x001CEDFC` | `LAB_001ce240` -> `FUN_001ce270`; `PlayGzip` (`0x003FC080`) | `0x1C`; `0x10000 -> 0x10400` | Control `0x0004`; `+0x28` owner; cooperative loop until external termination. |
| `0x001CF638` | `FUN_001cf190`; `LoadGzip` (`0x003FC090`) | `0x7E`; `0x10000 -> 0x10400` | Control `0x0004`; `+0x28` context; self-requests termination. |
| `0x001CF770` | `FUN_001cf060`; `LoadRead` (`0x003FC0A0`) | `0x74`; `0x1000 -> 0x1400` | Control `0x0004`; `+0x28` context; self-requests termination. |
| `0x001CF7B4` | `FUN_001cf210`; `LoadDecode` (`0x003FC0B0`) | `0x7F`; `0x1000 -> 0x1400` | Control `0x0004`; `+0x28` context; self-requests termination. |
| `0x001CFD00` | `FUN_001cfb50`; `LoadBg` (`0x00602C10`) | `0x73`; `0x1000 -> 0x1400` | `+0x28` current item, `+0x2C` stop/cancel, `+0x30` progress mode; self-requests termination through the saved global handle. |
| `0x001E100C` | `FUN_001d2570`; `SOUND` (`0x00602C38`) | `0x70`; `0x1000 -> 0x1400` | Control `0x0003`; creates both RPC tasks below, then remains in its cooperative loop. |
| `0x001E103C` | `FUN_001bd970`; `Load ROFS_Data` (`0x003FB940`) | `0x28`; `0x4000 -> 0x4400` | Control `0x0006`; readiness/load waits, then self-requests termination. |
| `0x001E1CC8` | `FUN_001e1c60`; `SAVE SYS` (`0x00404858`) | `0x14`; `0x1000 -> 0x1400` | Control `0x0004`; owner stores handle at `+0x5C`; infinite worker externally terminated without a join. |
| `0x0035B030` | `FUN_0035c890`; `FADE END` (`0x005AC0C0`) | `0x29`; `0x800 -> 0xC00` | `+0x28` fade ID; control `0x0003`; performs five one-handshake waits, clears protection bit `0x0001`, then self-requests termination. |
| `0x0035D0FC` | `FUN_00359b50`; `SP Skill Play` (`0x005AC148`) | `0x40`; `0x1000 -> 0x1400` | `+0x28` context; finite entry self-requests termination. |
| `0x003736C8` | `FUN_00373240`; `ZgBreakScreen` (`0x005AFEA0`) | `0x28`; `0x800 -> 0xC00` | Creator sets `+0x2C/+0x30`; control `0x0001`, later cleared before self-termination. |
| `0x003B3798` | `FUN_003b37f0`; `Load File All` (`0x005B3D30`) | `0x73`; `0x1000 -> 0x1400` | Control `0x0004`; `+0x28` completion, `+0x2C` byte argument, `+0x40` start gate; self-requests termination. |
| `0x001D2720`† | `FUN_001d28c0`; `SND_RPC` (`0x00602C40`) | `0x71`; `0x1000 -> 0x1400` | Control `0x0003`; long-lived RPC loop. |
| `0x001D2738`† | `LAB_001d29f0`; `SND_RPC2` (`0x003FD718`) | `0x72`; `0x800 -> 0xC00` | Control `0x0003`; long-lived RPC loop. |
| `0x001E7960`† | `FUN_001e7870`; `MC_CHECKDIR` (`0x004049D0`) | `0x64`; `0x800 -> 0xC00` | `+0x28` completion and `+0x2C` result bitmask; after completion waits indefinitely until the caller externally requests termination. |

This inventory also illustrates ownership and lifetime boundaries. Play
decode/read workers publish completion and remain alive until their owner
requests termination; the owner can therefore control the lifetime of context
stored in payload fields. In contrast, many finite load workers request their
own termination. Neither pattern is imposed by the core record.

The 24 entries form a complete static lifecycle census:

- 11 normally self-request termination: the primary play task, `PlayLock`,
  three one-shot load stages, `LoadBg`, `Load ROFS_Data`, `FADE END`,
  `SP Skill Play`, `ZgBreakScreen`, and `Load File All`;
- six use an external request after a completion/stop protocol:
  `LoadingInfo`, the three persistent play workers, `SAVE SYS`, and
  `MC_CHECKDIR`;
- two MPEG records are destroyed by immediate-removal API `FUN_001d0220`;
- five have no recovered ordinary teardown: naturally returned `PAD` plus the
  long-lived `MOTHER`, `SOUND`, `SND_RPC`, and `SND_RPC2` records.

These classes describe the recovered normal paths. A context destructor can
also request a normally self-terminating load task during cancellation, so the
categories are not claims that an entry has only one possible requester.

## Cross-version corroboration and overlay boundary

The clean NUN5 `SLES_556.05` resident retains an
instruction-shape-identical family at these corresponding addresses:

| Role | NUN5 EE VA |
| --- | ---: |
| Constructor | `0x001D5050` |
| Start | `0x001D5100` |
| Explicit-record wait | `0x001D5200` |
| Allocate / allocate-and-start | `0x001D5280` / `0x001D5300` |
| Termination request / immediate removal | `0x001D53A0` / `0x001D5410` |
| Force wake / current-task wait / name lookup | `0x001D54F0` / `0x001D5540` / `0x001D5640` |
| Manager init / wake / entry | `0x001D56F0` / `0x001D5760` / `0x001D5790` |

The NUN5 resident also preserves the immediate-removal search beginning at
`(manager->next)->next`. The skipped-first-record behavior is therefore not an
NA2 decompiler artifact or a one-build instruction accident, although its
source-level design name remains unknown.

The older clean NUN3 `SLUS_217.27` family has a different `0x50`-byte record
layout, so it is not ABI-compatible, but its runtime state machine resolves an
otherwise orphaned NA2 state. NUN3 `FUN_001786d0` sets its homologous runtime
bit `0x0010` and calls a suspend-thread wrapper; its manager later clears that
bit and calls `ResumeThread`. Callers use the helper after thread-status checks.
This establishes the historical pending-resume meaning. NA2 retains only the
manager consumer in the inspected code: an exhaustive resident scan found no
task-layout store that produces bit `0x0010`, and resident `SuspendThread`
calls belong to CRI-managed thread IDs (`FUN_0012e650`) and the resident
[kernel dispatch queue](kernel_threads_and_sync.md#separate-kernel-dispatch-queue-and-semaphore)
(`FUN_0015e9e0` / `FUN_0015ecc0`) rather than this task list.

For in-scope NA2 overlays, clean `BTL.BIN` has no direct references to this
task family. Clean `ETC.BIN` has exactly two calls to
`func_0x001d0340(1)`, both in `FUN_006c0d40`, and no recognized creator or
termination call. Adventure was not inspected. Consequently,
negative caller/producer claims in this document cover the resident, BTL, and
ETC static exports, not Adventure or dynamically constructed calls.

All 24 recognized entry pointers therefore target resident code. Within the
inspected overlays, ETC borrows the current resident task's wait API rather
than registering an overlay-owned thread entry, and no task record statically
retains a BTL/ETC entry address.

`FUN_001ce870`, the sole direct caller of force-wake helper
`FUN_001d02f0`, has no recognized static xref. Raw scans of the resident,
BTL, and ETC binaries found no absolute little-endian pointer word or nearby
MIPS address-materialization sequence for either function. The same detector
does recover the manager-entry construction above, so the negative is useful,
but the wrapper's installation or reachability remains unresolved rather than
proven unused.

## Evidence confidence and open questions

| Finding | Confidence | Basis / remaining limit |
| --- | --- | --- |
| Binary identity and ELF mapping | High | Direct clean-file size/hash, program mapping, and exported instruction addresses. |
| `0x4C` layout, entry/callback ABI, stack rule, globals, and flat-list ownership | High | Constructor stores, `ee_thread_t` ABI, append code, start descriptor, and both cleanup paths agree. |
| Runtime/control bit predicates and transition precedence | High | Direct halfword tests/stores and kernel calls in `FUN_001cff00`, `FUN_001d0000`, `FUN_001d01b0`, `FUN_001d02f0`, `FUN_001d0340`, and `FUN_001d0590`. |
| Two-pass termination and callback-before-thread-delete order | High | Both manager removal and immediate removal contain the same ordered sequence. |
| `FUN_001d0220` skipping the first ordinary record | High | Raw prologue loads `manager->next` as predecessor and its `next` as the first candidate. |
| All inventoried static task names and addresses | High | Each string was decoded again directly from the clean ELF bytes using the established VA/file mapping; dynamic primary-play naming is separately identified. |
| Semantic label “wake/hold gate” for `+0x14` | Medium | Its exact comparisons are proven; its producer, decrement protocol, and domain meaning are not. |
| Runtime `0x0010` pending-resume role | High for state role; medium for NA2 reachability | NA2 manager behavior and the NUN3 set/suspend/resume homolog agree; no in-scope NA2 producer or reachable helper was found. |
| Control `0x0002` resident behavior | High for no direct consumer; domain meaning unknown | Every resident halfword read at task offset `+0x12` was classified; indirect aliasing and excluded Adventure code remain limits. |
| Direct resident creator inventory | High | All 21 `FUN_001d0090` and three `FUN_001d0110` direct xrefs were traced through creator setup and entry behavior. |
| Root pacing and engine gate `0x04` | High for local contract; bounded reachability | Full root wait/counter/registration and gate state-machine paths, SIF `+0x506` producer, selected engine aliases, and MPEG low-two-bit consumer; nonzero `+0x500` installation, low-bit producers/meanings, and actual cadence remain unresolved. |
| Playback companion and sound creator ancestry | High for direct call relationships | Complete creator/entry bodies and bounded sound-entry bytes; no generic parent pointer or semaphore is implied. |
| Update/draw order, manager cadence, and frame-rate relationship | Not established | Interrupt-counter pacing does not identify measured presentation cadence, kernel scheduling, or independent-thread execution order. |

Other unresolved points are allocation-failure behavior in a real run,
natural-return handling for every entry class, the contract that serializes
unguarded append/immediate-removal operations, and any indirect callers not
recoverable from the resident export. None of those unknowns changes the
confirmed record layout or manager state machine above.
