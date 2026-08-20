# Resident task system

## Scope and binary identity

This record covers the resident task framework in the clean NA2 boot ELF,
centered on `FUN_001cfe50` through `FUN_001d0590`. It is a static-analysis
result, not a timing trace. Adventure-mode code was deliberately excluded.

| Property | Value |
| --- | --- |
| Game / executable | *Naruto Shippuuden: Narutimate Accel 2*, `SLPS-25837` / `SLPS_258.37` |
| Clean source | `@source_na2/SLPS_258.37` |
| Size | 5,273,256 bytes |
| SHA-256 | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |
| Disassembly | Ghidra 12.1.2 `r5900:LE:32:default` exports under `@disassembly/NA2/exports/SLPS_258.37/` |
| Executable mapping | ELF file `0x100` -> EE VA `0x00100000`; resident file offset = VA `- 0x000FFF00` |

The framework is a coordinator for real EE kernel threads. A task record does
not contain per-pass update and draw callbacks. Its function pointer at
`+0x0C` is passed to `CreateThread`, and the resident start wrapper ultimately
calls `_StartThread(thread_id, task_record)`. The entry therefore runs once as
an independent thread and receives its own task record in `a0`.

The manager itself is another task record and also serves as the head sentinel
of a flat, singly linked list. The global head is at `0x00607504` and the tail
is at `0x00607508`. Ordinary records are appended in creation order. There is
no framework parent pointer, child list, priority-sorted list, semaphore, or
central update/draw dispatch.

## Research coverage

- **Assigned scope:** the resident task/object framework around
`FUN_001cfe50` through `FUN_001d0590`: allocation and registration, the task
record and callback layout, statically provable manager ordering, ownership,
wait/wake behavior, termination and destruction, and representative resident
callers. The output scope was this document only; the clean binaries and
`@disassembly` exports remained read-only.

- **Exploration depth:** coverage was divided as follows:

  **Exhaustive within the core range:** every instruction in
  `FUN_001cfe50`, `FUN_001cff00`, `FUN_001d0000`, `FUN_001d0090`,
  `FUN_001d0110`, `FUN_001d01b0`, `FUN_001d0220`, `FUN_001d02f0`,
  `FUN_001d0340`, `FUN_001d0440`, `FUN_001d04f0`, `FUN_001d0560`, and
  `FUN_001d0590` was traced in the clean resident listing and compared with
  the decompiler export. Constructor stores, kernel calls, flag precedence,
  both list traversals, both destruction sequences, and the boot installation
  of the manager entry were checked against raw MIPS.
  **Exhaustive for direct resident call instructions:** aligned clean-ELF
  instruction-word scans classified every direct `jal` to the family. This
  includes 21 dormant allocations, three allocate-and-start calls, 22 start
  call instructions, 42 explicit-record waits, 51 current-task waits, 18
  termination requests, two immediate removals, one force wake, no name
  lookup call, one manager initialization, and one manager wake. Raw addresses
  were cross-checked with the listing, including the start call at
  `0x003B37CC` omitted from Ghidra's xref header.
  **Exhaustive for the recovered direct creation set:** all 24 ordinary
  resident constructions were followed through creator setup and their entry
  functions. The inventory records entry addresses, names, priorities,
  requested/effective stacks, control bits, observed payload slots, owner
  handles, and normal lifetime class. Every static name in that table was
  decoded again from the clean ELF bytes. “Exhaustive” here means all direct
  `FUN_001d0090`/`FUN_001d0110` paths in the clean resident, not dynamically
  synthesized calls.
  **Exhaustive for explicit encodings, bounded by aliasing:** whole-resident
  scans covered direct head/tail global references, direct
  `TerminateThread`/`DeleteThread` pairs, task-control halfword reads, obvious
  task-layout stores to the `+0x14` gate and runtime `0x0010` state, direct
  cleanup-field registration, and literal/MIPS address materializations of
  core APIs. These scans establish the documented direct negatives, but a
  task pointer copied to another base register or reached through opaque data
  can evade a layout-pattern search.
  **Bounded overlay coverage:** clean `BTL.BIN` and `ETC.BIN` were searched for
  direct calls and static address references to this family. BTL contributes
  none; ETC contributes the two documented `FUN_001d0340(1)` calls. Their
  feature logic was not otherwise reverse engineered for this task.
  **Sampled cross-version corroboration:** the homologous NUN5/NUN6 core
  families were checked for record shape, state transitions, the skip-first
  immediate-removal behavior, and manager structure. The older NUN3 family
  was inspected only where its shifted record, gate predicates, and explicit
  suspend/pending-resume helper clarify inherited states. This was not a
  whole-program task census for those games.

- **Confirmed coverage:** the `0x4C` record map, exact core
function/file addresses, list globals and ownership boundary, start/defer
rules, manager transition and barrier order, wait/wake predicates, two-pass
termination, cleanup ABI and call order, immediate-removal quirk, all direct
resident creator lifecycles, static call counts, and the absence of a central
update/draw callback. Negative conclusions are qualified to their actual scan
boundary.

- **Unresolved or untested:** the producer, unit, and domain meaning of
`+0x14`; the domain meaning of control `0x0002`; any reachable NA2 producer for
runtime `0x0010`; meanings of opaque `+0x44/+0x48/+0x4A`; reachability of the
force-wake wrapper; safe behavior under real allocation/kernel-call failures;
non-exempt natural-return behavior; indirect or runtime-generated callers;
and actual independent-thread execution, update/draw, or presentation order.

- **Deliberate exclusions and overlap:** Adventure was deliberately excluded. Controller routing, Save/Load behavior,
battle/render/audio feature internals, file/resource loading internals, and
60-FPS or other timing modifications belonged to other scopes; representative
callers were followed only far enough to establish task ownership and lifetime.
- **Evidence limitations:** no runtime PCSX2 trace, injected instrumentation, scheduler log, or timing
capture was performed. Consequently, addresses, instruction order, field
accesses, and direct static call graphs have strong static evidence, while
kernel scheduling, cadence, runtime reachability, pointer aliasing, and overlay
behavior outside BTL/ETC reference scans remain validation limits.

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

NUN5/NUN6 preserve the same `+0x48` halfword and `+0x4A` byte zeroing, while
the older NUN3 layout preserves the pattern at shifted offsets `+0x4C/+0x4E`.
The fields are therefore deliberate inherited storage, but no framework-level
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

Addresses are clean resident EE virtual addresses. File offsets use the ELF
mapping above. Names in the “export symbol” column are retained exactly so the
evidence can be found again without relying on the semantic labels.

| EE VA | ELF offset | Export symbol | Established role, callers/callees, and side effects |
| ---: | ---: | --- | --- |
| `0x001CFE50` | `0xCFF50` | `FUN_001cfe50` | Initializes a caller-supplied `0x4C` record and allocates its stack through `FUN_00117700`. Called by both allocation helpers and manager initialization. |
| `0x001CFF00` | `0xD0000` | `FUN_001cff00` | Builds an `ee_thread_t` from record `+0x0C/+0x1C/+0x18/+0x08`, calls `CreateThread`, stores `+0x0A`, and either starts through `FUN_0015ee20` or sets deferred-start bit `0x0001`. `FUN_0015ee20` validates thread state and ultimately calls `_StartThread(thread_id, record)`. |
| `0x001D0000` | `0xD0100` | `FUN_001d0000` | Explicit-record cooperative wait. Sets runtime bit `0x0008` and calls `SleepThread`; it calls no timer, VBlank, or semaphore API. |
| `0x001D0090` | `0xD0190` | `FUN_001d0090` | Allocates, constructs, and appends a dormant record. Ghidra's C prototype incorrectly says `void`; the MIPS ABI returns the record in `v0`, as its callers expect. |
| `0x001D0110` | `0xD0210` | `FUN_001d0110` | Allocates, constructs, appends, and calls `FUN_001cff00(record, 0)`. The base ELF has three recognized direct call sites. |
| `0x001D01B0` | `0xD02B0` | `FUN_001d01b0` | Asynchronously requests termination unless control bit `0x0001` is set. A self-request sleeps immediately; an external requester returns without joining or freeing. |
| `0x001D0220` | `0xD0320` | `FUN_001d0220` | Immediate unlink/callback/thread termination/thread deletion/stack free/record free. Its only resident direct caller is `FUN_00105320`, at two MPEG teardown call sites. It deliberately starts its search at the second ordinary record, as detailed below. |
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
exact zero. NUN5/NUN6 preserve the NA2 `+0x14` layout and predicates. None of
that establishes a unit or producer, so “wake/hold gate” remains deliberately
neutral terminology.

The core family uses `SleepThread`, `WakeupThread`, and `ResumeThread`; it does
not implement these waits with an EE semaphore. `FUN_00167da0` and
`FUN_00167df0`, used around current-task and name lookup, are DI/EI interrupt
guards.

## Termination, destruction, and ownership

Ordinary termination is deliberately asynchronous:

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

The whole resident listing contains exactly two direct `TerminateThread`
calls and exactly two direct `DeleteThread` calls. They are the paired calls in
`FUN_001d0220` and `FUN_001d0590`; no third direct task-record destruction
route exists in the base executable. The one resident `ExitDeleteThread` call
belongs to a separate thread path and does not unlink or free a task record.
This is a direct-call negative and does not rule out an indirect syscall
wrapper outside the recovered graph.

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

The clean NUN5 `SLES_556.05` and NUN6 `SLUS_556.06` residents retain an
instruction-shape-identical family at these corresponding addresses:

| Role | NUN5 / NUN6 EE VA |
| --- | ---: |
| Constructor | `0x001D5050` |
| Start | `0x001D5100` |
| Explicit-record wait | `0x001D5200` |
| Allocate / allocate-and-start | `0x001D5280` / `0x001D5300` |
| Termination request / immediate removal | `0x001D53A0` / `0x001D5410` |
| Force wake / current-task wait / name lookup | `0x001D54F0` / `0x001D5540` / `0x001D5640` |
| Manager init / wake / entry | `0x001D56F0` / `0x001D5760` / `0x001D5790` |

Both later residents also preserve the immediate-removal search beginning at
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
calls belong to CRI-managed thread IDs (`FUN_0012e650`) and the resident kernel
dispatch queue (`FUN_0015e9e0` / `FUN_0015ecc0`) rather than this task list.

For in-scope NA2 overlays, clean `BTL.BIN` has no direct references to this
task family. Clean `ETC.BIN` has exactly two calls to
`func_0x001d0340(1)`, both in `FUN_006c0d40`, and no recognized creator or
termination call. Adventure was deliberately not inspected. Consequently,
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
| Update/draw order, manager cadence, and frame-rate relationship | Not established | Static list and syscall order do not identify presentation cadence or independent-thread execution order. Runtime tracing would be required. |

Other unresolved points are allocation-failure behavior in a real run,
natural-return handling for every entry class, the contract that serializes
unguarded append/immediate-removal operations, and any indirect callers not
recoverable from the resident export. None of those unknowns changes the
confirmed record layout or manager state machine above.
