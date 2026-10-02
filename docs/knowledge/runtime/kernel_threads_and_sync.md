# EE kernel threads and synchronization outside the task list

Several EE kernel threads and semaphores in the retail NA2 (`SLPS-25837`)
resident run outside the [resident task system](task_system.md). They create
threads or semaphores directly, keep their IDs in their own globals, and never
allocate, append, or flag a `0x4C` task record. This document records their
construction, synchronization, and teardown contracts: the
`SceKerneltopThread` dispatch queue, the alarm-backed `SceKernelDelayThread`
delay and its RCNT2 timer library, the MPEG buffer semaphore, the CD callback
thread and semaphore set, and the six CRI-owned threads. Binary identity and
address conversion follow
[Retail game file identities](../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** resident EE kernel threads and synchronization objects
  that do not use the `0x4C` task record: the kernel dispatch queue, the
  alarm-backed delay with its timer mode admission, conversion, and record
  pools, the MPEG buffer semaphore, the CD callback thread and semaphores, and
  the CRI-owned threads with their priority sources and stop/done protocol.
- **Exploration depth:** the dispatcher constructor, three producers, and
  consumer; the delay wrapper, both conversion helpers, timer mode admission,
  both record pools, callback-return dispatch, and both cancellation variants;
  all nine MPEG semaphore users and teardown; the CD constructor, semaphore
  creation, interrupt completion, callback thread, both registration setters,
  and teardown; and the six CRI constructors, their entries, status helpers,
  and five cleanup helpers were read in instructions. Unanalyzed CD and CRI
  entries were read from instruction bytes. `CreateThread` and
  `ExitDeleteThread` call-word scans counted only aligned resident matches.
- **Confirmed coverage:** the dispatcher ring layout and command set; the
  delay's conversion arithmetic, boot-selected RCNT2 mode `2`, reader and
  interrupt shift agreement in mode `2` and disagreement in mode `3`, compare
  grouping, two-pool lifetime, and callback-return and cancellation
  contracts; MPEG semaphore ownership, including the zero-flag branch that
  keeps the semaphore; CD semaphore roles, callback dispatch, teardown order,
  and the independence of its two registrations; and CRI thread identities,
  priority sources, stop/done protocol, and the bounded wake/resume handshake.
- **Unresolved or untested:** callers of the dispatcher's rotate and suspend
  producers; physical alarm-counter frequency and observed delay; persistence
  of RCNT2 mode `2` outside the inspected timer family; behavior when
  `WaitSema` fails; whether MPEG callbacks reach the semaphore-keeping branch;
  reachability and selected priority of the CD callback-thread constructor;
  caller paths of the two optional CRI constructors; and successful
  callback/shutdown interleavings.
- **Deliberate exclusions and overlap:** the task record, manager, task waits,
  and root pacing belong to [Resident task system](task_system.md); file and
  CD request semantics belong to
  [Resident file and archive services](../game/files/runtime_services.md); PSS
  media selection belongs to
  [Audio and video replacement](../game/files/audio_video_replacement.md). CRI
  vendor workloads were not reverse engineered.
- **Evidence limitations:** static analysis of the clean resident only, with no
  runtime trace. Kernel scheduling, elapsed time, queue overrun, and
  failure-path behavior are not observed.

## Separate kernel dispatch queue and semaphore

`FUN_0015EAB8`, called by the early bootstrap `FUN_00168058`, constructs an
EE thread outside the task-record list. Its descriptor names it
`SceKerneltopThread`, installs entry `FUN_0015E9E0`, uses fixed stack
`0x0060DCC0` of size `0x400`, `$gp = 0x0060A9F0`, and initial priority 0.
The descriptor store at `0x0015EB3C` confirms priority zero; no `0x4C` record
allocation, append, name setter, or task-start flags occur. It starts through
the shared `FUN_0015EE20` wrapper with argument `0x0060E0C8`, then changes
its bootstrap caller's priority to 1. Later the ordinary root changes that
priority to `0x78`, as described in
[Resident task system](task_system.md#manager-pass-and-ordering-boundary).

The dispatcher owns semaphore ID word `0x0060E0C0`, thread ID
`0x003F78F8`, read/write index words `0x0060E0C8/0x0060E0CC`, and 512
two-byte command slots beginning at `0x0060E0D0`. Creation writes maximum
semaphore count `0xFF` and initial count 0. Each producer uses
`(write_index & 0x1FF) * 2`, replaces the stored index with the masked value
plus one, stores command/operand bytes, then calls `iSignalSema`.
`FUN_0015E9E0` waits on that semaphore, advances the read index by the same
rule, and dispatches one slot:

| Command byte | Consumer operation | Recovered producer |
| ---: | --- | --- |
| 0 | `WakeupThread(operand)` | `FUN_0015EBA8` |
| 1 | `RotateThreadReadyQueue(operand)` | `FUN_0015EC40`, requiring unsigned operand `< 0x80` |
| 2 | `SuspendThread(operand)` | `FUN_0015ECC0` |

Wake/suspend producers obtain the interrupt-context thread ID with raw syscall
selector `-0x2F` and compare it with the requested ID. When they differ, they
call `_iWakeupThread` or `_iSuspendThread` directly; when equal, they enqueue
only if the unsigned ID is `< 0x100` and the dispatcher ID word is nonzero.
Instruction `0x0015EBB4` and the branch at `0x0015EBC0`, followed by command
and byte-operand stores at `0x0015EC1C/0x0015EC24`, corroborate the wake
path despite the decompiler's unresolved `in_v0` syscall result.

The recovered direct wake callers are the display interrupt callback
`FUN_00108CE0` and CRI thread-status helper `FUN_0012E530`. The latter calls
the wake wrapper only for a nonzero thread ID whose `iReferThreadStatus`
status is 4 or `0xC`. Direct xrefs expose no callers for the rotate/suspend
producers; this is a bounded xref result, not proof against unrecognized or
indirect calls. The dispatcher never reads task record `+0x10`, so its command
2 does not supply the task manager's missing
[runtime-`0x0010`](task_system.md#runtime-flags-at-0x10) producer.

The producer/consumer family has no queue-full comparison, pending-slot
ownership check, or retry on `iSignalSema` failure. Semaphore creation failure
stops construction; thread creation failure deletes the semaphore. Once the
thread starts, this family has no recovered normal teardown. These are the
visible storage and failure contracts, not evidence that a queue overrun
occurs. A kernel dispatcher semaphore wake is a separate event from
`FUN_001D0560` waking the ordinary task manager.

## Alarm-backed delay semaphore

`FUN_0015ED58`, identified by descriptor string `SceKernelDelayThread`, is
another independent wait mechanism. With CPU status bit `0x10000` clear it
returns an error. Otherwise it creates a private semaphore with maximum count
1 and initial count 0, calls `FUN_00169880(0, requested_delay)`, and registers
callback `0x0015EF98` through `FUN_00169A30`. Successful registration leads to
`WaitSema(id)`, then `DeleteSema(id)` and return 0; failed registration also
deletes the semaphore. Callback `FUN_0015EF98` calls `iSignalSema` with the ID
received in `a3`, then executes `sync; ei` and returns zero.

Converter `FUN_00169880` builds full 64-bit unsigned products with
`multu1/multu` at `0x00169898/0x0016989C`, using multiplier
`0x08CA0000` (147,456,000). It passes the second product to the unsigned
division helper `FUN_00170290` with divisor 1,000,000, then adds the first
product. The recovered arithmetic is therefore
`u32(a0) * 147456000 + floor(u32(a1) * 147456000 / 1000000)`;
this delay caller supplies `a0 = 0`. The HI/LO assembly preserves both
halves of each product; the decompiler's apparent truncation of the first
product is not the instruction contract. The numeric scale alone does not
establish the alarm timer's physical unit or measured delay.

Alarm registration `FUN_00169A30` removes a record from the free list at
`0x00615780` under an interrupt guard, allocates a timer through
`FUN_00169038`, and stores its callback/context at record `+0x08/+0x0C`.
It installs `FUN_001699D0` as the timer trampoline through
`FUN_00169758`, then calls `FUN_001692D0`. A failed timer allocation
returns the record to the free list. The trampoline passes the stored context
as its fourth callback argument; when the callback returns zero, it returns
the record to that same free list, clears its timer ID at `+0x04`, and
returns `-1`. Thus this delay callback has a one-shot record lifetime as well
as a separately deleted semaphore. Registration does not check the results
of its two timer-configuration calls. Selected timer allocation, admission,
dispatch, and cancellation contracts are recovered below; this is not a
complete timer-library census.

The selected backend path does identify a hardware-counter source.
`FUN_00169660`, called through `FUN_00169758`, stores the converted
duration at timer `+0x20`; start helper `FUN_00169220` snapshots
`FUN_00168EF8` into `+0x10` and inserts the timer through `FUN_00168B90`.
That clock helper reads RCNT2 count/mode at `0x10001000/0x10001010`,
combines the count with the overflow accumulator at `0x003F8FA8` shifted
left 16 bits, corrects for pending mode bit `0x800`, and applies a
mode-dependent shift. The queue orders the
unsigned deadline `duration + start - timer[+0x18]`; `FUN_00168A00`
uses that queue and counter to select the compare value. Thus the converted
argument feeds a counter-based alarm deadline, not a count of manager wakes.
The selected boot configuration and its limits are detailed below. This path
does not establish actual elapsed delay.

### Counter mode admission and conversion units

The boot helper `FUN_00168058` calls `FUN_001686B0` at `0x00168078`
with `a0 = 2` in the delay slot at `0x0016807C`. The initializer rejects an
already installed handler (`0x003F8FB0 >= 0`), initializes timer storage,
registers `FUN_00168C50` on interrupt channel `0x0B`, and then writes RCNT2
mode. At `0x00168790..0x001687A0`, its exact mode expression is
`(old_mode & ~3) | caller_mode | 0x300`. If resulting bit `0x80` is clear,
it additionally clears count, writes target `0xFFFF`, and ORs `0xC80`
before the mode write at `0x001687C0`. It does not range-check or mask the
caller argument to two bits. Thus mode `2` is concretely selected on this
boot path, while a general claim that the API rejects mode `3` is false.
An already enabled counter preserves its count/target in this initializer.
The sole recovered direct initializer xref is this boot call; no claim that
all subsequent counter-mode writes have been excluded follows from it.
Boot's next call to `FUN_001688F0` admits a stopped counter by setting bit
`0x80` and clearing `0xC00`, preserving the low mode bits; an already active
counter returns `1`. The selected stop helper `FUN_00168980` also preserves
those low bits. Uninstallation `FUN_00168808` refuses a nonzero allocated
timer count before removing its handler/resetting mode. This constrains this
library's own mode lifetime while a timer is allocated, without excluding an
external writer or proving a successful boot installation.

Let `m = RCNT2_MODE & 3`, and let `C` be the overflow-extended counter before
normalization. Instruction evidence gives these shifts:

| `m` | Clock reader `FUN_00168EF8` and guarded reader `FUN_00168F48` | Interrupt consumer `FUN_00168C50` |
| ---: | ---: | ---: |
| 0 | `C << 0` | `C << 0` |
| 1 | `C << 4` | `C << 4` |
| 2 | `C << 8` | `C << 8` |
| 3 | `C << 16` | `C << 12` |

The reader uses `m == 0 ? 0 : (2 << m)` as its shift count
(`0x00168F24..0x00168F38`); the interrupt uses `m << 2`
(`0x00168D10..0x00168D20`, repeated at `0x00168E60..0x00168E74`).
Mode `2` therefore agrees across start/deadline consumption. The mode-`3`
disagreement is a confirmed static contract difference, not a demonstrated
retail failure or evidence of reachable mode-`3` alarms.

The inverse conversion `FUN_001697D8` divides a 64-bit count by 147,456,000
for its first output and scales the remainder by 1,000,000 for its second.
Together with `FUN_00169880`, this establishes a whole-unit/subunit pair:
the second input/output represents millionths of the first unit, with integer
truncation in the ordinary range. The inverse narrows the whole-unit quotient
to 32 bits at `0x00169800..0x00169804` before multiplying it back for the
remainder, and stores only 32 bits for either output. Its remainder scaling
also uses 64-bit wrapping arithmetic. It is therefore not an unrestricted
mathematical inverse for arbitrarily large 64-bit counts.
`FUN_0015ED58` supplies the requested delay solely as that second
input. **Inference, strong for the numeric convention:** these are nominal
seconds/microseconds in a 147,456,000-count-per-second convention. Physical
counter frequency, persistence of mode `2`, and observed delay duration are
not established by the arithmetic or boot argument alone.

Timer configuration accepts duration zero and does not enforce a minimum
there. Compare programming `FUN_00168A00` has its own admission granularity:
it walks forward through deadlines while each next deadline is less than
the selected deadline plus `0x7333`, replacing the selected deadline each
time (`0x00168A84..0x00168AE0`). If selected deadline minus supplied current
count is signed-less-than `0x7333`, it programs current raw count plus
`0x7333 >> (m << 2)`; in mode `2` that increment is `0x73` raw counter
steps. Otherwise it programs the selected absolute deadline shifted right
by `m << 2`. This separate grouping/compare rule does not alter the stored
duration, but it prevents equating conversion arithmetic with a guaranteed
exact wake instant, especially for zero or small requests. No physical
minimum delay is inferred from these integer thresholds.

### Two record pools and callback lifetime

Initialization uses separate pools: `FUN_001686B0` clears and links 128
`0x40`-byte timer records at `0x00613380..0x0061537F`, while
`FUN_00169980` links 64 `0x10`-byte alarm records at
`0x00615380..0x0061577F`. The respective free-list roots are
`0x003F8FBC` and `0x00615780`. Timer allocation `FUN_00168FC8` resets
callback `+0x28`, flags `+0x0C`, and adjustment `+0x18`, then installs an
odd generation value `((++generation & 0x1FF) << 1) | 1` at `+0x08`.
Its handle is `(timer_address << 4) | generation`; timer APIs recover the
record with `(handle >> 10) << 6` and check the low ten bits. The alarm handle
uses `(alarm_address << 4) | (timer_handle & 0xFE) | 1`, retaining only the
low-byte generation comparison in the inspected cancellation API. Neither
handle encodes a task-record pointer or an EE thread ID.
The timer generation has 512 values; the alarm comparison retains 128 of
those low-byte patterns. These are allocation-generation cycles across the
timer pool, not timer durations or per-alarm invocation counts.

At timer configuration `FUN_00169660`, a negative/mismatched timer handle is
rejected, as is the currently dispatched handle at `0x003F8FC4`. Existing
armed bit `0x02` selects unlinking before reconfiguration; that branch does
not additionally check started bit `0x01`. A null callback clears bit `0x02`;
otherwise duration `+0x20`, callback `+0x28`, saved `$gp` `+0x2C`, and
context `+0x30` are installed, bit `0x02` is set, and an already started
record is reinserted. Start `FUN_00169220` separately sets bit `0x01` and
snapshots the clock into `+0x10`; an already started record returns `1`.
This is timer-state admission, independent of ordinary task control flags.

The interrupt removes the due timer from its queue before `jalr`
`0x00168D74`, loads its saved `$gp` at `0x00168D5C`, and passes the timer
handle, configured duration, elapsed count adjusted by `+0x18`, and stored
context. `FUN_001699D0` translates the handle for the alarm callback and
passes the alarm's own context as argument four. The two return protocols
must be kept distinct:

| Alarm callback return | Alarm trampoline / timer backend consequence |
| --- | --- |
| 0 | Trampoline links the alarm record back into its free list, clears alarm timer ID `+0x04`, and returns `-1`; backend then clears timer generation/flags, returns the timer record to its free list, and decrements allocated-timer count. This is the delay callback's path. |
| Nonzero other than `-1` | Alarm record stays allocated; backend adds `max_unsigned(return, 0x3999)` to stored duration and reinserts the same timer. Start and adjustment are preserved. |
| `-1` | Trampoline leaves the alarm record allocated but forwards `-1`; backend frees the timer record. This return does not itself recycle the alarm record. No selected delay callback returns this value. |

The general timer backend also accepts return `0` to clear armed bit `0x02`
without freeing the timer (`0x00168D80..0x00168D9C`), but the alarm
trampoline maps its user's zero to `-1`, so a completed alarm callback cannot
select that timer-only result through a normal zero return. Repeating alarm
callbacks retain both records. The minimum repeat count `0x3999` is an
integer counter quantity; no measured minimum duration is claimed.

Cancellation `FUN_00169C50` decodes the alarm record, validates the low-byte
handle relation under DI/EI, calls guarded timer-free `FUN_00169120`, then
recycles the alarm record without checking that free result. Its unguarded
counterpart `FUN_00169CF8` recycles only when `FUN_00169080` returns zero.
The timer-free helper rejects the currently dispatched timer; it otherwise
removes an armed record, clears generation/flags, and frees it. These
differences establish local cancellation and record-reuse boundaries, not a
safe concurrent cancellation interleaving. Generation fields wrap, and these
APIs alone do not establish indefinite stale-handle protection.

Alarm registration stores callback/context values directly; it does not copy,
retain, or free the pointed-to context. Recycling clears timer ID `+0x04`
and changes the free-list link, while callback/context remain until the next
registration overwrites them. The delay's context is the semaphore ID, so the
callback record does not own semaphore deletion. The wrapper keeps no live
alarm handle after its registration-result check and does not cancel the
alarm. It ignores `WaitSema`'s result at `0x0015EDF8` before deleting the
semaphore at `0x0015EE00` and returning zero. This makes successful wait and
callback completion an assumption of that local lifetime, not a checked
guarantee under kernel failure.

This family does not call the task wait helpers or publish task runtime
`0x0008`; its argument is forwarded into an alarm conversion/registration
path rather than decremented once per task wake.
Direct resident xrefs identify ten delay-calling function owners, including
file-service retry routines and `FUN_00172B10/FUN_00172BB0`; their local
retry semantics are not task-cycle counts. The file service contracts remain
in
[Resident file and archive services](../game/files/runtime_services.md).

## MPEG buffer semaphore ownership

The two barrier-exempt MPEG tasks share a decoder/buffer object rather than a
semaphore in either task record. Creator `FUN_001057B0` allocates the outer
`0xB8`-byte object, saved at global `0x00607414`, and initializes it through
`FUN_001020E0`. That initializer passes its embedded object at `outer+0x48`
to `FUN_00103660`, which creates a semaphore with maximum and initial count
both 1 and stores the ID at `embedded+0x40` (`outer+0x88`). The embedded
record is a distinct layout; its `+0x14` byte-count bookkeeping is unrelated
to the task record's wake/hold gate at the same numeric displacement.

All nine recovered direct wait/signal users of this embedded semaphore were
read in full:

| Users | Established protected operation |
| --- | --- |
| `FUN_001021F0`, `FUN_001024E0` | Consume/publish metadata records. |
| `FUN_00102870`, `FUN_001028E0` | Align byte bookkeeping or read occupied-byte count. |
| `FUN_001029A0`, `FUN_00102EA0` | Restore or snapshot IPU/DMA transfer state. |
| `FUN_00102FB0`, `FUN_001032A0`, `FUN_00103310` | Commit data, advance byte accounting, or obtain free buffer spans. |

Every ordinary completed branch balances its wait with a signal, with one
confirmed exception. `FUN_00102FB0` waits at `0x00102FEC`, checks embedded
word `+0x44`, and when zero calls the no-op `FUN_00104340`, returns 0, and
jumps directly to the epilogue (`0x00103018 -> 0x0010326C`). Its signal is
only in the nonzero branch at `0x00103260`. Thus the zero branch retains the
acquired semaphore; it is not a decompiler omission or an exception raised
by the diagnostic helper. Reset `FUN_00103480` initializes `+0x44 = 1`, while
`FUN_00102EA0` clears it before a restore. The direct caller
`FUN_00101A60` supplies `outer+0x48`; whether its callbacks reach this branch
between stop and restore is not established. This is a static failure
contract, not an observed playback failure.

Teardown `FUN_00105320` removes `MPEG VIDEO DEC` and `MPEG MAIN` through
`FUN_001D0220` before `FUN_00101FA0(outer)` reaches
`FUN_00102940(outer+0x48)` and deletes the semaphore. It then releases the
outer object. The task manager does not own, signal, or delete this semaphore;
its lifetime is controlled by the MPEG owner. PSS selection/media contracts
remain in [Audio and video replacement](../game/files/audio_video_replacement.md).

## CD callback thread and semaphore set

The sole direct `jal ExitDeleteThread` belongs to resident
`FUN_00172100`, named by descriptor string `SceCdCallbackThread` at
`0x005BDC18`. Its constructor at `0x001721D0` is not a defined Ghidra
function; its instruction bytes `0x001721D0..0x00172268` establish a static
descriptor at `0x00615A98`
with entry `0x00172100`, caller-supplied priority/stack/stack-size in
`a0/a1/a2`, explicit `gp_reg = 0`, and the name pointer. It creates the
kernel thread at `0x00172228`, stores ID `0x003F9054`, and starts it with
argument zero. An existing nonzero ID instead receives a priority change.
No task record or list append occurs. A direct resident byte search found
no `jal`, tail `j`, or literal pointer to the constructor; its selected
priority and reachable installation remain unresolved.

`FUN_00172328` creates these four semaphores when any of the three request
ID words is `-1`:

| ID word | Descriptor name | Maximum / initial count | Established owner role |
| --- | --- | --- | --- |
| `0x003F9068` | `SceCdNcmdSema` | 1 / 1 | Request serialization; interrupt completion `FUN_00172060` signals it. |
| `0x003F906C` | `SceCdScmdSema` | 1 / 1 | Separate request semaphore; complete operation family not classified here. |
| `0x003F9070` | `SceCdRcmdSema` | 1 / 1 | Polled/released by `FUN_00173328`, one [engine-gate](task_system.md#engine-gate-bit-0x04) dependency. |
| `0x003F9060` | `SceCdCallbackSema` | 1 / 0 | Callback-thread event consumed by `FUN_00172100`. |

Interrupt completion copies its incoming word to `0x003F90A0/0x003F90A4`.
Value `0xB` clears busy word `0x003F9074` without signaling. Other values
signal the request semaphore, then signal the callback semaphore only when
the callback-thread ID and callback pointer at `0x00615A80` are nonzero;
otherwise they clear busy directly. The completion handler finally clears
`0x003F90A0`. This is one shared publication and semaphore event, not a
task-record queue or per-task completion token.

The callback thread waits on `0x003F9060`. For ordinary events it invokes
the installed callback only if both pointer and published argument are
nonzero, then clears busy. Its MIPS saves `$gp`, loads callback `$gp` from
`0x00615A84` for the `jalr` at `0x001721B8`, and restores it afterward;
the decompiler omits that context change. A zero argument consequently still
consumes the semaphore wake while skipping the callback. For publication
`0x003F90A0 == -1`, it clears busy, publication, thread ID, and word
`0x00615A94`, then calls `ExitDeleteThread`.

Owner teardown `FUN_00172410` publishes `-1` and signals the callback
semaphore only when the thread ID is nonzero, then immediately deletes all
four semaphores and removes its registered SIF callback. It has no done-spin
or join with `FUN_00172100` before deleting them. This differs from the CRI
done-word cleanup and the task manager's two-pass removal. The static order
is established; successful delivery and shutdown interleaving are not.
The distinct SIF callback path `FUN_00172588 -> FUN_00172530` uses pointer
`0x00615A88` and argument `0x00615A90`, rather than the thread callback
pointer/argument above. Their registrations must not be merged merely because
they belong to the same CD library.

A raw resident search for `B8 76 05 0C` finds nine distinct aligned
`jal CreateThread` instructions: six CRI constructors, the kernel dispatcher,
this unanalyzed CD constructor, and `FUN_001CFF00`. Ghidra's analyzed xrefs
omit the CD constructor. The number is a count of call instructions, not
nine concurrently live threads: `FUN_001CFF00` serves all ordinary records
and the manager, constructors can be repeated, and the CD constructor's
reachability is unresolved. The task-record destruction census in
[Resident task system](task_system.md#termination-destruction-and-ownership)
counts the matching `ExitDeleteThread` call words. General file/CD operation
contracts remain in
[Resident file and archive services](../game/files/runtime_services.md).

### Callback registration and constructor reachability

The two CD registrations are independent of the thread constructor.
`FUN_00171FF8` first performs nonblocking readiness probe
`FUN_00172B10(1)`. Only result zero admits registration; under DI/EI it
returns the previous callback, stores the new pointer at `0x00615A80`, and
captures `$gp` at `0x00615A84`. Probe failure returns zero without installing
it, so zero alone cannot distinguish a failed registration from replacing a
null callback. This setter calls no `CreateThread`, start routine, or
`0x001721D0`; installing a callback is not an implicit thread construction.

`FUN_001724B0` instead ensures the SIF callback registration through
`FUN_00172588`, then stores callback/context/`$gp` at
`0x00615A88/0x00615A90/0x00615A8C` respectively. `FUN_00172588` installs
`FUN_00172530` for SIF command `0x80000012`, bracketed by registration-busy
word `0x003F9064`. Its dispatch helper skips a null callback or nonzero busy
word, loads the saved `$gp`, passes context in `a0`, invokes the callback,
and restores `$gp`. The resident engine's concrete registration of
`FUN_00108AF0` uses this path and zero context; it creates no kernel thread.
[Resident task system](task_system.md#callback-installation-and-selected-engine-aliases)
owns that callback's effect on the engine gate.
General SIF/CD request semantics remain with the linked file-service owner.

The constructor bytes preserve `a0` as priority, `a1` as stack, and `a2` as
stack size across the ID check. Zero ID constructs the descriptor and starts
the resulting ID; a nonzero ID takes `ChangeThreadPriority(existing_id,a0)`
at `0x0017224C`, leaving stack and stack size unchanged. The newly created
branch returns literal `1` after the start call, while the existing-ID branch
returns the priority-change result. Neither creation nor start result is
validated here. This does not demonstrate successful creation on a real path.

The aligned resident `sw` encodings with displacement `0x9054` recover only
the constructor's ID publication at `0x00172234` and the entry's ID clear
at `0x00172174`. The callback-pointer displacement `0x5A80` similarly
recovers only the setter at `0x00172030`. Xrefs expose no caller of that
setter or of the constructor. In addition to the already recorded direct
call/pointer negatives, the resident has no `addiu` or `ori` construction
of low half `0x21D0`.
Thus the saved callback pointer, constructor priority, and caller-supplied
stack are still not connected to a reachable installation. The live SIF
engine registration cannot fill that gap because it writes the other callback
slots. A computed address or copied callback/ID alias remains an unresolved
lead; the selected priority cannot be established from these registrations.

## CRI-owned kernel threads

The 24-record [direct creation inventory](task_system.md#direct-resident-creation-inventory)
is not a count of every EE thread in the resident game. Besides the kernel dispatcher, six CRI constructors directly
call `CreateThread` and use external global handles, caller/fixed stack
storage, and `FUN_0015EE20(id, 0)`. None allocates/appends a task record or
sets task lifecycle flags. Complete constructor and entry-family inspection
establishes the following identities:

| Constructor | Entry | ID word | Default fixed stack / size | Assigned priority word |
| --- | --- | --- | --- | --- |
| `FUN_0012E6B0` | `FUN_0012E038` | `0x003D6A88` | `0x003D6B20 / 0x800` | `0x003D6A04` |
| `FUN_0012E758` | `FUN_0012E090` | `0x003D6A8C` | `0x003D7320 / 0x1000`; optional caller stack/size | `0x003D6A08` |
| `FUN_0012E810` | `FUN_0012E128` | `0x003D6A90` | `0x003D8320 / 0x1000` | `0x003D6A0C` |
| `FUN_0012E898` | unanalyzed `0x0012E230` | `0x003D6A94` | `0x003D9320 / 0x1000` | `0x003D6A10` |
| `FUN_0012E920` | `FUN_0012E320` | `0x003D6A9C` | `0x003DA320 / 0x2000` | `0x003D6A18` |
| `FUN_0012E9B8` | `FUN_0012E458` | `0x003D6AA0` | `0x003DC320 / 0x2000`; optional caller stack/size | `0x003D6A1C` |

Each descriptor's initial priority comes from saved word `0x003DE328`;
the constructor starts the thread and then calls `ChangeThreadPriority` with
the row's assigned-priority word. `FUN_0012EAC0` populates the saved word from
the creator's `ReferThreadStatus.current_priority`, not a literal zero.
Consequently the zero bytes in the retail data image do not establish initial
runtime priority. The function also remembers the creating thread ID at
`0x003D6A98` and changes that caller to configured priority word
`0x003D6A14` after creating four of the six worker variants.

The actual root path `FUN_001BD380` supplies the six-word configuration
`[1, 8, 0x10, 0x12, 0x78, 0x7A]` to `FUN_0012EAC0`, which creates
`0x0012E038`, `0x0012E128`, `0x0012E230`, and `0x0012E320`. Their assigned
priorities become 8, `0x10`, `0x12`, and `0x7A`; the root remains at `0x78`.
This corroborates the later `PAD`/`MOTHER`
[deferred-start comparison](task_system.md#manager-pass-and-ordering-boundary)
and explains
why the direct task-record priority range is not the whole kernel priority
range. The optional constructors' priority words are not supplied by that
six-word initialization, and their selected caller/creation paths remain
unresolved here.

CRI wait helper `FUN_0012E5D0` is a plain `SleepThread`; it does not publish
task runtime `0x0008`. `FUN_0012E580` wakes a nonzero ID only for statuses
4 or `0xC`; `FUN_0012E5E8` resumes only for 8 or `0xC`; and
`FUN_0012E650` suspends only when neither 8 nor `0xC` is already reported.
The interrupt-safe wake counterpart is `FUN_0012E530`, linked to the
dispatcher above. These helpers operate directly on CRI IDs rather than
using manager-owned record lookup.

CRI owns separate stop/done publications. Entry variants
check stop words at `0x003D6AA8`, `0x003D6AB8`, `0x003D6AC8`,
`0x003D6AD8`, `0x003D6AE8`, and `0x003D6AF8`, publish corresponding done
words eight bytes later, and tail-jump to `ExitDeleteThread`. Shutdown
`FUN_0012EC50` sets all six stop words. The five inspected cleanup helpers
`FUN_0012ED38`, `FUN_0012EE08`, `FUN_0012EED8`, `FUN_0012EFA8`, and
`FUN_0012F1A8` spin until their respective done publication, repeatedly
setting stop, boosting priority to 1, waking and conditionally resuming the
thread, then clear stop/done/handle. `FUN_0012EFA8` instead uses a pure
done-spin when activity word `0x003D6A40 == 1`; its retry counter at
`0x003D6B1C` is a count of loop iterations, not elapsed time. There is no
timeout in these inspected loops. Library release `FUN_0012ECA0` invokes
four of those cleanup helpers and restores the saved creator priority.

Another CRI handshake has an explicit iteration bound rather than a timer.
`FUN_0012DEE8(id, restored_priority)` sets shared request word
`0x003D6A34 = 1`, changes the target to configured priority
`0x003D6A00`, then repeatedly calls the status-gated wake and resume
helpers until the request clears. With no clear, loop indices run from 0
through 200,000,000 inclusive before `FUN_0014DC00` is called: 200,000,001
wake/resume pairs, not 200,000,000 time units. MIPS loads bound
`0x0BEBC1FF` (199,999,999) at `0x0012DF28/0x0012DF34`, compares
`bound < counter` at `0x0012DF58`, increments in the branch delay slot,
and repeats while that comparison is false. After the diagnostic returns,
it restores the supplied priority; the handshake contains no clock read or
sleep of its own. Worker entries `FUN_0012E320/FUN_0012E458` clear the
request after their service operation. Registered callbacks
`FUN_0012DFD0/FUN_0012DFF8` pass those worker IDs and their configured
restored priorities to this helper. This does not set task runtime `0x0010`
or join task-record destruction.

The missing analyzed entry `0x0012E230` is corroborated by instruction bytes across
`0x0012E230..0x0012E31C`: its body calls `FUN_0012E5D0` at
`0x0012E2D4`, writes done word `0x003D6AE0`, and tail-jumps at
`0x0012E318`. This family does not unlink/free a task record and does not
produce the task manager's pending-resume flag. Full vendor workload internals
and runtime reachability of the two optional constructors remain outside
this thread-lifetime finding.

## Evidence confidence

| Finding | Confidence | Basis / remaining limit |
| --- | --- | --- |
| Alarm conversion, mode admission, and two-pool lifetime | High for instruction contracts; nominal time-unit interpretation is inference | Boot selects mode `2`; reader/consumer agree there and differ for mode `3`. Conversion establishes whole units and millionths; callback returns and cancellation determine separate timer/alarm reuse. Physical frequency, mode persistence beyond the inspected family, wait-failure behavior, and actual interleavings remain unresolved. |
| CD callback registration and constructor boundary | High for inspected interface; caller reachability unresolved | Setter, constructor bytes, saved `$gp` dispatch, SIF registration, and selected ID/pointer writers agree; no reachable constructor or selected priority was recovered. |
| Separate semaphore ownership and lifetimes | High for static order | Dispatcher ring, alarm delay, all nine MPEG users, and CD semaphore/callback families; zero-flag MPEG branch retains its semaphore, and CD teardown does not join its callback thread. |
| CRI thread construction, priority sources, and stop/done protocol | High for inspected families | Six constructors/entries, root priority configuration, status helpers, five cleanup loops, and raw tail-jump words agree; optional creator reachability is incomplete. |
