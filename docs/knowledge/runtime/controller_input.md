# Controller input runtime

This note reconstructs the resident controller stack in the clean
*Naruto Shippuuden: Narutimate Accel 2* v2.28 boot ELF. It covers the two
resident pad records, Sony `libpad` boundary, polling and derived-button
semantics, analog and pressure decoding, the front-end analog-to-D-pad adapter,
disconnect/configuration handling, and vibration. Adventure-mode consumers are
out of scope.

All behavioral conclusions below are **static-only** unless explicitly stated
otherwise. No controller trace or live-memory capture was used. Confidence is
high where the listing directly exposes loads, stores, branches, constants, and
call order. Strongly identified Sony-style `scePad*` names are high-confidence
library identifications, but the stripped ELF's original Ghidra symbols remain
the listed `FUN_*` names.

## Research coverage

- **Assigned scope:** this task covered the clean `SLPS_258.37` resident
controller stack: initialization and update order; both per-port records and
globals; raw packet, button-edge/repeat, stick, and pressure derivation;
connection/configuration behavior; clearly identifiable analog/digital
compatibility helpers; vibration scheduling and transport; and a bounded check
for resident controller-combination reset handling. The requested binary and
evidence identity, function addresses, original stripped-export labels, call
relationships, confidence, and useful negative results are recorded here.

- **Exploration depth:** overall coverage is **bounded, high-depth static
coverage**, not an exhaustive survey of every input consumer or every IOP
instruction. Within the resident core, the `0x78`-byte record layout and the
paths through `FUN_00113480`, `FUN_001134e0`, `FUN_00113530`,
`FUN_00113710`, `FUN_00113b80`, `FUN_00113c70`, `FUN_00113f40`,
`FUN_00114850`, `FUN_001148c0`, `FUN_00114930`, and
`FUN_00114b40..FUN_00114e60` were followed at instruction/field level.
Scheduler placement was traced through `FUN_001081b0`, `FUN_00108490`, and
`FUN_001d0590`. The linked EE `libpad` function sequence from entry
`0x00174098` through `FUN_00175588` was inspected as one bounded library unit,
including unpromoted helpers and raw J/JAL/stored-pointer checks where an
unused-helper negative is claimed. The active front-end adapter
`FUN_001e0d20`, its direct caller, the instruction-level twin
`FUN_0037d7c0`, and the reverse helper `FUN_00114e60` were checked without
expanding into general menu/gameplay consumer analysis. Constant data included
the sector table at `0x005B54D0`, the reverse-direction table at `0x005B5490`,
and the 21-entry vibration table at `0x00408050`.

Supporting IOP work was **targeted/sampled**, not module-wide: the exact
`padman` IRX embedded at `MODULES.BIN` offset `0x2000` was used to verify the
EE snapshot producer, packet builder/pressure reconciliation, read/query
disconnect workers, direct-actuator consumer and power cap, main RPC
dispatcher, and RPC-`0x18` completion-command path. The concrete link-relative
functions are enumerated in the matching IOP function map below. Soft-reset
coverage was likewise bounded: canonical combo constants, reset/relaunch
strings, direct code/pointer references to the resident relaunch wrappers, and
the static intersection of controller-reader and exit/relaunch call ancestry
were checked; this was not an overlay-wide proof.

- **Confirmed coverage:** the note records the exact two-record layout
and update ordering; full packet/button/edge/repeat behavior; polar stick math
and adapter thresholds/sectors; pressure copying and IOP consistency rules;
wrapper plus IOP disconnect/reconfiguration transitions; the configuration
state machine and retry quirks; the vibration override timeline, shipped
presets, EE/IOP transport, and power limiting; the embedded `libpad` API and DMA
layouts; and evidence-backed negative results for resident soft reset,
right-stick conversion, multitap use, and several linked-but-unused helpers.

- **Unresolved or untested:** record byte `+0x46`, snapshot
`val_c6`, the resident writer (if any) of lifecycle value 2, and the exact
public Sony name of the RPC-`0x18` callback-registration API remain unresolved.
Computed/indirect callers cannot be excluded by raw direct-reference scans.
The rest of PADMAN/SIO2MAN, general menu/gameplay input consumers, overlays,
and replacement-module behavior were not exhaustively analyzed.
- **Deliberate exclusions and overlap:** Adventure was explicitly excluded.
Save/load, controller routing outside this wrapper, and
resident file/resource services were left to their separately scoped research
owners; no index, other canonical note, source, binary, or preserved
disassembly was edited.

- **Evidence limitations:** all conclusions are static. No PCSX2 session, physical
controller capture, live-memory trace, disconnect/reconnect trial, pressure
sample, rumble observation, or timing measurement was performed. Accordingly,
instruction-visible formulas and ordering are high confidence, while real-time
cadence, device/emulator presentation, rare failure behavior, and practical
effects of latent counter/queue edges remain unverified dynamically.

## Binary and evidence identity

| Item | Value |
| --- | --- |
| Game | *Naruto Shippuuden: Narutimate Accel 2* v2.28 |
| Serial / resident binary | `SLPS-25837` / `@source_na2/SLPS_258.37` |
| Size | `5,273,256` bytes |
| SHA-256 | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |
| Preserved evidence | `@disassembly/NA2/exports/SLPS_258.37/SLPS_258.37.c` and `.txt` |
| Export | Ghidra `12.1.2`, R5900 little-endian, 8,427 functions |
| Research date | 2026-08-20 |

The ELF's first load segment maps file `0x00000100` to EE runtime
`0x00100000`; for addresses in that segment:

```text
file offset = runtime address - 0x000FFF00
```

The binary contains the library tag `PsIIlibpad  3000` and diagnostic strings
from `libpad`. The disassembly manifest independently records the same source
hash and size. The matching IOP implementation is also present in the clean
disc extraction:

| Supporting IOP evidence | Value |
| --- | --- |
| Container | `@source_na2/MODULES/MODULES.BIN` |
| Container size / SHA-256 | `315,392` bytes / `0CDEA9EF15E3FFE8B70B6305A67F9A37015FF12B08815EE4CA16358A4C93BA9D` |
| Embedded module | container `0x00002000..0x0000CFFF`, `45,056` bytes |
| Embedded-module SHA-256 | `0DFC9FCBE832D10B172CAAE862920561EB919426307EEE671A1679A9D138CD64` |
| Module identity | ELF32 little-endian MIPS R3000 IRX, module `padman`, entry `0x3304`, tag `PsIIpadman  3000` |

The embedded-module range includes its alignment padding through the next IRX
at container offset `0xD000`; its hash therefore identifies the exact bytes
used for this analysis. It was extracted only to a task-local temporary
directory and analyzed as a relocatable IOP image. Addresses stated for that
module below are IRX link-relative, not its eventual IOP load addresses.

### Confidence guide

- **High, direct static evidence:** addresses, record/global offsets, call
  order, packet transformation, edge/repeat formulas, stick math, pressure
  copy/clear condition, configuration branches, vibration stack operations,
  and DMA-half selection.
- **High, ABI-correlated:** the `scePad*` identities, standard button/pressure
  names, and conventional `libpad` state labels. These match the compiled
  behavior and bundled PS2SDK source but are not symbols retained by the ELF.
- **Unproven dynamically:** real-time cadence, hardware/emulator presentation,
  observed pressure/rumble values, and whether statically unreferenced helpers
  can be reached through a computed mechanism.

## Ownership, initialization, and update order

Runtime address `0x006073FC` (`gp-0x35F4`, with `gp=0x0060A9F0`) is the global
that holds the dynamically allocated system-context pointer. It is a pointer
slot, not the context itself.

`FUN_00105fc0` allocates a `0x530`-byte system context, constructs it through
`FUN_001062a0`, stores the pointer at `0x006073FC`, and calls
`FUN_00107f80`. The latter reaches `FUN_001134e0`, which initializes these two
embedded `0x78`-byte records:

| Port | Record base | DMA area | Port / slot |
| --- | ---: | ---: | --- |
| 0 | `context+0x1C` | `0x00608B80` | `0 / 0` |
| 1 | `context+0x94` | `0x00608C80` | `1 / 0` |

At call site `0x001C1470`, `FUN_001c13f0` creates `FUN_00113530` as the
independent pad initialization/configuration worker with priority `0x19` and
stack size `0x800`. That worker repeatedly initializes `libpad`, opens both
ports, advances both configuration state machines, and yields. It therefore
does not perform the ordinary per-update packet decode.

Initialization and teardown are serialized across ports. The worker does not
start either configuration machine or publish lifecycle state 1 until port 0
and then port 1 have both returned open result 1. A persistent port-1 open
failure can therefore leave an already opened/readable port 0 classified by
the core poll but stuck without worker-driven configuration. Teardown likewise
waits for port 0 to close before attempting port 1, and waits for both before
`scePadEnd`. There is no per-port failure isolation or timeout in these loops.

The ordinary engine-update ordering is:

```text
FUN_001d0590 scheduler-cycle top
  -> FUN_001081b0 system update
       -> display/flush work
       -> 0x0010829C: FUN_00113480
            -> FUN_00113b80(port 0)  vibration-duration maintenance
            -> FUN_00113b80(port 1)
            -> FUN_00113710(port 0)  packet poll and field derivation
            -> FUN_00113710(port 1)
       -> FUN_00106500
       -> FUN_00108390
       -> FUN_001086c0
       -> registered callback at context+0x520, when enabled
  -> scheduled worker/task processing
  -> FUN_00108490 end-of-update work
       -> copy public held to previous-public-held, when the normal-frame gate is open
```

Thus held/pressed/released/repeat fields are refreshed before the registered
game callback and before scheduled task consumers. `FUN_00108490` later copies
port 0 `context+0x80` to `context+0x7C`, and port 1 `context+0xF8` to
`context+0xF4`. This late snapshot is not used to calculate the core edges;
`FUN_00113710` uses its own raw-history field at record `+0x74`.

The core poll sits outside the engine's `context+0x192 & 7` normal-frame gate.
The scheduler runs an individual task during a gated cycle only when its task
flags include bit `0x08`; `FUN_001c13f0` explicitly sets that bit on the pad
worker. The registered callback, late held snapshot, and ordinary front-end
adapter task are gated. Consequently core pad fields and configuration can
advance on a scheduler cycle in which those higher-level consumers do not run.
On an ungated front-end cycle, the adapter runs before `FUN_00108490`, so
record `+0x60` captures adapter-augmented public held; record `+0x74` remains
the physical/core history used by the next poll. The registered callback is
earlier than scheduled tasks, so it observes the core poll result before
`FUN_001e0d20` can add stick-derived D-pad bits that cycle.

The listing establishes an engine/scheduler update cycle. It does not by
itself prove that every cycle corresponds one-for-one with a displayed frame
under all skip/stall modes.

## Per-port record

Offsets below are relative to either `0x78`-byte record. Context-relative
columns make the two resident instances explicit.

| Record | Port 0 context | Port 1 context | Size | Meaning |
| ---: | ---: | ---: | ---: | --- |
| `+0x00` | `+0x1C` | `+0x94` | 4 | pointer to the port's aligned `0x100`-byte DMA area |
| `+0x04` | `+0x20` | `+0x98` | 4 | last `scePadGetState` result |
| `+0x08` | `+0x24` | `+0x9C` | `0x20` | latest variable-length `scePadRead` packet |
| `+0x28` | `+0x44` | `+0xBC` | 6 | actuator direct/alignment bytes |
| `+0x2E` | `+0x4A` | `+0xC2` | 1 | actuator substate / availability |
| `+0x2F` | `+0x4B` | `+0xC3` | 1 | vibration override depth, `0..3` |
| `+0x30` | `+0x4C` | `+0xC4` | `0x10` | four vibration records; index 0 is the stop sentinel |
| `+0x40` | `+0x5C` | `+0xD4` | 1 | actuator failure/retry count |
| `+0x41` | `+0x5D` | `+0xD5` | 1 | pressure-mode negotiation flag |
| `+0x42` | `+0x5E` | `+0xD6` | 1 | cached packet mode/type nibble |
| `+0x43` | `+0x5F` | `+0xD7` | 1 | wrapper configuration state |
| `+0x44` | `+0x60` | `+0xD8` | 1 | core repeat-delay counter |
| `+0x45` | `+0x61` | `+0xD9` | 1 | configuration retry count |
| `+0x46` | `+0x62` | `+0xDA` | 1 | opaque flags; the poll preserves only bits 0 and 1 |
| `+0x47` | `+0x63` | `+0xDB` | 1 | physical port number |
| `+0x48` | `+0x64` | `+0xDC` | 1 | slot number; both are zero in NA2 |
| `+0x49` | `+0x65` | `+0xDD` | 1 | left-stick magnitude, `0..255` |
| `+0x4A` | `+0x66` | `+0xDE` | 1 | right-stick magnitude, `0..255` |
| `+0x4B` | `+0x67` | `+0xDF` | 1 | alignment/padding byte; no clean-resident access found |
| `+0x4C` | `+0x68` | `+0xE0` | 4 | left-stick angle in radians |
| `+0x50` | `+0x6C` | `+0xE4` | 4 | right-stick angle in radians |
| `+0x54` | `+0x70` | `+0xE8` | 12 | native pressure bytes |
| `+0x60` | `+0x7C` | `+0xF4` | 4 | late previous-public-held snapshot |
| `+0x64` | `+0x80` | `+0xF8` | 4 | public held/current mask |
| `+0x68` | `+0x84` | `+0xFC` | 4 | newly pressed mask |
| `+0x6C` | `+0x88` | `+0x100` | 4 | newly released mask |
| `+0x70` | `+0x8C` | `+0x104` | 4 | initial/change and delayed-repeat mask |
| `+0x74` | `+0x90` | `+0x108` | 4 | core raw-held history/latch |

The masks are stored as 32-bit words, but the packet-derived domain is the low
16 bits. The front-end adapter described below may temporarily rewrite the
public words while deliberately leaving the raw-history latch unchanged.

### Initializer defect

`FUN_00114930` intends to clear the 12 pressure bytes, but the R5900 listing
confirms that its 12-iteration loop repeatedly executes `sb zero,0x54(record)`;
it never adds the loop index. This is a real static initializer defect, not a
decompiler artifact. The normal poll subsequently either copies all 12 native
pressure bytes or clears all 12, so no persistent runtime effect is established.

The constructor also does not explicitly clear raw packet bytes `+0x08..+0x27`
or configuration-retry byte `+0x45`; padding byte `+0x4B` has no access at all.
Every normal path that can increment the retry byte first resets it, so no
behavioral use of an indeterminate initial value is established. The packet
omission is more observable to memory tools: until a full-length packet has
been copied, bytes beyond the latest reported length need not describe the
current read. Allocation-time heap contents were not assumed.

The initializer clears only flag bits 0 and 1 in each four-byte vibration
entry, preserving the upper six bits of the existing byte. All runtime tests
and writes in this subsystem likewise use only bits 0/1, so those preserved
upper bits have no proven effect. Together with the pressure-loop defect, this
means the constructor is not a bytewise zero-initializer even though all
derived input masks, stick outputs, vibration durations/intensities, and the
repeat counter do receive explicit initial values.

## Raw PS2 packet and game mask

`scePadRead` copies the selected DMA snapshot's recorded byte count to record
`+0x08`. The wrapper uses this standard packed layout:

| Packet | Record | Meaning |
| ---: | ---: | --- |
| `+0` | `+0x08` | reply/status byte |
| `+1` | `+0x09` | packet ID; high nibble is pad type/mode |
| `+2..+3` | `+0x0A..+0x0B` | active-low digital buttons |
| `+4` / `+5` | `+0x0C` / `+0x0D` | right stick X / Y |
| `+6` / `+7` | `+0x0E` / `+0x0F` | left stick X / Y |
| `+8..+19` | `+0x10..+0x1B` | native pressure bytes |
| `+20..+31` | `+0x1C..+0x27` | reserved by this wrapper; no decode found |

Neither EE layer adds a local size guard. The embedded `scePadRead` trusts the
DMA snapshot's 32-bit length and copies exactly that many bytes into the
caller's 32-byte packet area. `FUN_00113710` tests only whether the returned
length is nonzero before reading packet ID and button bytes; it does not require
a minimum of four bytes (or eight before reading sticks). A malformed short
snapshot could therefore mix newly copied and stale packet bytes, while a
length above 32 would overrun the wrapper packet field. The wrapper also never
checks packet status byte `+0`; state, nonzero read length, and packet ID alone
control classification/decode.

The exact bundled IOP `padman` producer narrows that concern on the ordinary
unmodified path. Its link-relative `FUN_00003af4` returns exactly 32 and writes
status byte 0 when its per-slot data-ready word equals 1; otherwise it writes a
leading `0xFF`, zeroes the other 31 staging bytes, and returns length 0. Thus
this producer gives the EE client only complete 32-byte packets or no packet,
not partial lengths. The unchecked EE boundary still matters for corruption,
hooks, or a replacement IOP producer; it was not exercised dynamically.

For an exact `0x79` pressure packet, that same IOP routine also reconciles each
of packet bytes `+8..+19` with its corresponding active-low digital bit. If the
button is not held it forces the pressure byte to 0; if the button is held but
the pressure byte is 0 it raises it to 1; all other nonzero pressure values are
preserved. The mapping is the standard order in the pressure section below.
Consequently a pressure-ready packet delivered by this bundled module cannot
represent a released button with nonzero pressure or a held button with
exactly zero pressure.

The held mask is formed exactly as:

```text
held = ~((packet[2] << 8) | packet[3]) & 0xFFFF
```

That explicit byte order makes the game's masks byte-swapped relative to a
little-endian `padButtonStatus.btns` word:

| Game mask | Button | Game mask | Button |
| ---: | --- | ---: | --- |
| `0x0001` | L2 | `0x0100` | Select |
| `0x0002` | R2 | `0x0200` | L3 |
| `0x0004` | L1 | `0x0400` | R3 |
| `0x0008` | R1 | `0x0800` | Start |
| `0x0010` | Triangle | `0x1000` | Up |
| `0x0020` | Circle | `0x2000` | Right |
| `0x0040` | Cross | `0x4000` | Down |
| `0x0080` | Square | `0x8000` | Left |

The raw transformation is directly proven. Button names follow the standard
PS2 pad packet and are corroborated by resident consumers, including menu code
that treats `0x1000/0x4000` as vertical directions and `0x20/0x40` as
accept/cancel.

## Held, edges, and repeat

For a newly decoded 16-bit `held` value, `FUN_00113710` computes:

```text
pressed  = ~raw_history & held
released =  raw_history & ~held
```

It then updates repeat state as follows:

1. If `held` is zero or differs from `raw_history`, `repeat=held` and the
   one-byte counter is reset to zero.
2. On the next 15 unchanged nonzero updates, the counter advances from 0 to 15
   and `repeat=0`.
3. On the 16th and every later unchanged update, `repeat=held`; the counter
   remains 15.
4. Finally, both public held (`+0x64`) and raw history (`+0x74`) receive
   `held`.

Consequently `+0x70` is not a periodic pulse. It exposes the full held mask on
the initial/change update, suppresses it for 15 unchanged updates, and then
exposes it continuously until the mask changes. A change in any held button
puts the entire new held mask in `repeat`, not only the newly pressed bits.

## Connection and configuration behavior

The wrapper-facing `scePadGetState` values are the usual `libpad` states:

| Value | State |
| ---: | --- |
| `0` | disconnected |
| `1` | finding pad |
| `2` | finding controller protocol (`FINDCTP1`) |
| `3` / `4` | reserved/unnamed in this client |
| `5` | executing command |
| `6` | stable |
| `7` | error |
| `99` | NA2's unopened-port sentinel from `FUN_001748a8` |

The compiled debug-name table at `0x003FAC18` literally contains
`DISCONNECT`, an empty string for state 1, `FINDCTP1`, empty strings for 3 and
4, then `EXECCMD`, `STABLE`, and `ERROR`. “Finding pad” for value 1 is the
ABI-correlated conventional name rather than a retained literal. The adjacent
request-state table names 0 `COMPLETE`, 1 `FAILED`, and 2 `BUSY`.

The embedded `scePadGetState` normally returns snapshot byte `+0x70`, but it
maps raw stable state 6 plus request-busy byte `+0x71 == 2` to exposed state 5.
Thus a configuration request in flight deliberately makes an otherwise stable
pad non-readable to `FUN_00113710`, producing the zero-derived frame described
below. `scePadGetReqState` returns complete (0) for an unopened slot.

`FUN_00113710` accepts packet data only in states 2 and 6. State 0 resets the
wrapper state to 1 and clears the cached mode. Every update starts with zero
held, zero stick outputs, and—unless an exact pressure packet is accepted—zero
pressure. Therefore a disconnect, configuration interval, failed/empty read,
or other non-readable state clears public held. On the first such update,
released is the preceding raw-held mask; later zero-input updates have no
release edge. Reconnection does not expose input until mode negotiation returns
to ready state `0x40`.

The raw packet storage at record `+0x08` is not cleared on disconnect or a
non-readable update. It may remain stale while all derived/public outputs are
zero; consumers should use the derived fields or validate state rather than
treating the packet buffer as fresh.

The exact bundled IOP driver explains the lower-level transition into those
states. Its per-slot update worker at link-relative `0x00002530` accepts a read
reply only when the transport succeeds, response marker byte 2 is `0x5A`,
response ID byte 1 equals the cached controller ID, and that ID is not `0xF3`.
An accepted response copies all 32 bytes to the stable button buffer, marks data
ready, and exposes state 2 while `modeConfig == 1` or state 6 otherwise. It
also completes a busy ordinary request only after the slot's run-task word has
returned to zero.

A transport/read failure instead clears data-ready, exposes state 7, increments
the cumulative `findPadRetries` word exported at snapshot `+0x5C`, and adds the
driver's reported error contribution to a local accumulator. The accumulator
resets after a successful read; once it reaches at least 10, the update worker
hands the slot to its query worker. A successful transport with a bad marker,
mismatched ID, or ID `0xF3` skips that threshold and hands over immediately in
state 5. The query worker at link-relative `0x000026C0` clears cached mode,
model, capabilities, button masks, direct-actuator size, data-ready, and retry
count before probing. While no supported pad is found it repeatedly publishes
state 0 and marks the slot disconnected; once a pad is found it enters state 5
and rebuilds configuration.

This creates a useful distinction at the resident layer. Transient IOP state 7
or 5 zeroes all derived input but does not itself change wrapper configuration
state `+0x43`; only eventual exposed state 0 performs the wrapper's disconnect
reset to state 1/mode 0. During that transient interval the wrapper can still
look ready to its vibration enqueue/state-machine gates even though input is
zero. The IOP query takeover itself clears its six live actuator bytes and
restores alignment `[00,01,FF,FF,FF,FF]`; that is internal-state evidence, not
a measured guarantee about when a detached physical motor stops.

Disconnect does not immediately clear the vibration stack or send an actuator
stop. The wrapper changes only configuration state/mode there, while
`FUN_00113b80` continues aging the current vibration segment each update and
the worker stops entering its ready-state actuator branch. On an ordinary
DualShock reconnection, successful actuator alignment resets depth to zero,
marks the stop sentinel dirty, and causes the state machine to submit a zeroed
motor pair before accepting new queued effects. This sequence is statically
proven; behavior of a physically detached motor was not tested.

That reset is path-dependent. Neither disconnect nor classification state 2
clears actuator substate `+0x2E` or override depth `+0x2F`; the common path into
actuator probe state `0x30` clears the substate, and successful alignment later
clears the depth. Pad type 5 instead jumps straight from classification to
ready, and the 21-immediate-failure pressure fallback also jumps directly to
ready. Those two paths can therefore inherit the preceding actuator substate,
stack, and dirty flags after a reconnect or reconfiguration. The ready-state
actuator branch immediately resumes processing whatever survived. This is a
static state-persistence result; whether a replacement type-5 device responds
to an inherited direct command was not tested.

The wrapper state at record `+0x43` advances as follows:

| State | Static role |
| ---: | --- |
| `0x00` | unstarted; ordinary poll skips `libpad` |
| `0x01` | port opened or disconnect observed; wait for a readable packet |
| `0x02` | classify the packet mode and start/restart configuration |
| `0x10..0x12` | turn a digital pad type 4 toward locked DualShock mode with `scePadInfoMode`, `scePadSetMainMode(1,3)`, and request-state waits |
| `0x20..0x22` | probe and enter native pressure mode for type 7 |
| `0x30` | probe the two expected actuators |
| `0x31..0x32` | align actuators with `[00,01,FF,FF,FF,FF]` and wait for completion |
| `0x40` | ready; packet decode and vibration enqueue are enabled |
| `0x50` | port closed; ordinary poll skips `libpad` |

Pad type 5 is accepted directly as ready. Type 7 takes the pressure path. Type
4 uses main-mode negotiation and then restarts classification. The actuator
probe requires two actuators with exact `(function,subfunction,size)` tuples
`(1,2,0)` and `(1,1,1)` before vibration is enabled. A stable controller that
does not match that exact capability signature becomes ready with vibration
disabled.

Configuration retry byte `+0x45` is narrower than a general timeout. It is
reset on entry to the main-mode, pressure, and actuator-alignment stages. The
three setter-call paths increment it after an immediate call failure, retry
while it is below `0x15`, and fall back when it reaches `0x15`. A request-state
result of failed instead moves back one setter state without itself incrementing
the byte; busy simply waits. Consequently repeated request failures can cycle
indefinitely even though immediate setter failures have the `0x15` fallback.
The pad worker's init/open/close/end loops are independently unbounded.

The pressure fallback has a further static quirk. State `0x21` sets the record's
pressure-configured flag `+0x41` to 1 *before* calling the press-mode setter. If
21 consecutive immediate setter calls fail, the state machine enters ready
state `0x40` without clearing that flag. A continuing `0x73` packet therefore
causes the next core poll to return the record to classification state 2 and
publish a zero-derived frame, after which the worker starts another pressure
attempt batch. The `0x15` limit is consequently not a permanent fallback from
an attached pressure-capable pad: persistent immediate failures can produce
repeated 21-attempt batches separated by zero-input reclassification frames.

Actuator probe state `0x30` contains a distinct branch oddity. It normally
checks the capability tuple only when the last exposed pad state stored at
`+0x04` is stable (6). If that value is not 6, it increments `+0x45` once; a
value below `0x15` then advances directly to actuator alignment, clears the
counter, and attempts `[00,01,FF,FF,FF,FF]` without having proven the tuple.
Only a value already reaching `0x15` takes the vibration-disabled ready
fallback. All ordinary entrances to state `0x30` first clear `+0x45`, so the
21-count non-stable fallback is not normally reachable: the first non-stable
pass takes the alignment branch. This conclusion follows the raw branch
targets at `0x00114294..0x00114458`, not the decompiler's higher-level shape.

When pressure negotiation has succeeded, a later ready-state packet ID `0x73`
forces reconfiguration. Packet ID `0x79` is the only packet for which pressure
values are retained. Reclassification is checked before the ready-state decode,
so the triggering `0x73` frame publishes zero held/sticks/pressure and produces
release edges for the preceding held mask. The first readable packet after
state 1, and a newly observed transition to mode nibble 7, are likewise used
only to enter configuration rather than as an input frame.

The mode-change test is asymmetric: while already configured, a changed packet
nibble forces classification only when the new nibble is 7. A changed nibble
of 4 or 5 without an intervening exposed disconnect does not update the cached
mode or restart setup; the current packet still controls whether sticks are
decoded, and pressure is cleared unless the exact ID is `0x79`. Normal device
replacement is expected to pass through state 0, so this hot-swap edge remains
static-only.

`FUN_00113530` owns the broader worker lifecycle byte at `0x006073B0`: it sets
0 while records are initialized, 1 after both ports open, waits for an external
2 shutdown request, then closes both ports, calls `scePadEnd`, and writes 3. No
direct writer of value 2 was found in the clean resident export.

## Stick conversion

For each stick, `FUN_00114b40` (`0x00114B40`) receives unsigned X/Y bytes,
stores a float angle and byte magnitude, and returns whether magnitude is
nonzero. `FUN_00113710` routes packet `[6,7]` to the left outputs and `[4,5]`
to the right outputs when the mode nibble is 5 or 7.

Let `dx=x-128`, `dy=y-128`. Each axis is adjusted independently:

```text
raw 0..71    -> adjusted = raw - 72       (-72..-1)
raw 72..184  -> adjusted = 0
raw 185..255 -> adjusted = raw - 184      (+1..+71)
```

Magnitude is:

```text
min(255, floor(sqrt(adjusted_x^2 + adjusted_y^2) * 255 / 72))
```

The square per-axis deadzone is therefore inclusive `-56..+56`; radial
magnitude outside it is capped at 255. If the result is zero, angle and
magnitude are both zero. Otherwise the angle convention is:

| Direction | Representative raw X/Y | Angle |
| --- | --- | ---: |
| Up | `128,0` | `+pi` or `-pi` |
| Right | `255,128` | `-pi/2` |
| Down | `128,255` | `0` |
| Left | `0,128` | `+pi/2` |

The endpoint scaling is slightly asymmetric. Raw 0 maps to adjusted `-72`, so
a negative full-scale cardinal axis reaches magnitude 255. Raw 255 maps to only
`+71`, so a positive full-scale cardinal axis truncates to magnitude 251.
Either first sample outside the deadzone (raw 71 or 185 on one axis) maps to
magnitude 3. Diagonal values can still hit the 255 cap on either side.

A subtle implementation detail is that magnitude uses the deadzone-adjusted
axes, while angle uses the original centered `dx/dy`. An off-axis component
that falls inside the per-axis deadzone can therefore still tilt the reported
angle whenever the other axis makes the total magnitude nonzero.

## Native pressure

Only a ready-state packet whose ID byte is exactly `0x79` copies packet
`+8..+19` to record `+0x54..+0x5F`. All 12 outputs are cleared on every other
update. Their standard packet order is:

```text
Right, Left, Up, Down,
Triangle, Circle, Cross, Square,
L1, R1, L2, R2
```

The order is established both by the `libpad` packet contract and by the exact
IOP producer's per-byte reconciliation against game-order digital masks
`2000,8000,1000,4000,0010,0020,0040,0080,0004,0008,0001,0002`.
The resident wrapper itself treats the range as an opaque 12-byte copy and no
distinct pressure consumer was needed to establish polling behavior.

## Analog-to-D-pad compatibility

### Active front-end path

`FUN_001e0d20` (`0x001E0D20`) has one direct call, at `0x001E11D8` inside
front-end task `FUN_001e0ee0`. It runs at the top of that task's steady loop,
before its state-specific handlers and before the task yields. This proves its
placement for that front-end task only; it is not part of the core poll and is
not proven to run for every resident/overlay consumer.

For each port it:

1. Reads public held. If physical D-pad bits `0xF000` are already nonzero, it
   gives them priority, resets its private repeat counter, and snapshots the
   full public mask without synthesizing anything.
2. Calls `FUN_00114d90` with the left-stick angle and magnitude.
3. Synthesizes a D-pad direction only when magnitude is strictly greater than
   `0xA0`.
4. Replaces only D-pad bits in pressed and released, updates public held, and
   recreates the same 15-update repeat delay with private history.

It does not touch the right stick, core raw-history field `+0x74`, or the
physical packet. Its repeat comparison uses the full augmented mask, not only
the D-pad nibble. A simultaneous non-D-pad button change can therefore reset
this adapter's repeat delay and can put the complete augmented held mask in
the repeat field. Keeping private history even on physical-D-pad frames also
lets a transition from a physical direction to the same synthesized stick
direction avoid a false release/press pair.

Under `FUN_00114b40`'s scaling, `magnitude > 0xA0` requires adjusted radial
distance large enough to truncate to at least 161 (about 45.46 adjusted units).
On a single cardinal axis the first qualifying raw value is therefore 26 on
the negative side or 230 on the positive side; diagonal motion can qualify
with smaller per-axis components.

Private state is at runtime `0x006075E0` (two counters) and `0x006075E8` (two
saved masks). Both arrays lie in the zero-filled portion of the resident load
segment, so their initial state is zero without an explicit constructor.
`FUN_00114d90` chooses and ORs a sector with:

```text
sector = ((((int)(((angle + pi) * 8) / pi)) + 1) & 0xF) >> 1
held |= DAT_005B54D0[sector]
```

This produces eight nominal 45-degree sectors with boundaries halfway between
the canonical directions; sector 0 wraps across `-pi/+pi`.

The sector table at `DAT_005B54D0` is:

| Sector | Canonical angle | Mask | Direction |
| ---: | ---: | ---: | --- |
| 0 | `+/-pi` | `0x1000` | Up |
| 1 | `-3pi/4` | `0x3000` | Up + Right |
| 2 | `-pi/2` | `0x2000` | Right |
| 3 | `-pi/4` | `0x6000` | Right + Down |
| 4 | `0` | `0x4000` | Down |
| 5 | `+pi/4` | `0xC000` | Down + Left |
| 6 | `+pi/2` | `0x8000` | Left |
| 7 | `+3pi/4` | `0x9000` | Left + Up |

### Unreferenced twin and reverse helper

`FUN_0037d7c0` (`0x0037D7C0`) is a `0x1B0`-byte instruction-level clone of
`FUN_001e0d20`. Only seven of its 108 words differ, all references to separate
zero-filled private counters at `0x00607798` and saved masks at `0x006077A0`. The export
has no XREF, and a raw-ELF scan found neither a direct JAL encoding nor a stored
little-endian pointer. Its intended context is unproven.

`FUN_00114e60` (`0x00114E60`) performs the reverse conversion: it maps valid
D-pad nibbles to the same angle convention with magnitude `0xFF`; zero,
opposite pairs, and three-/four-way combinations return angle/magnitude zero.
It likewise has no export XREF, direct JAL, or stored pointer. It is an
identified compatibility helper, not a proven active NA2 path.

Its raw 16-float table at `DAT_005B5490` uses `4.0` as the invalid sentinel.
The only accepted high-nibble values are exact: `1=Up (+pi)`,
`2=Right (-pi/2)`, `3=Up+Right (-3pi/4)`, `4=Down (0)`,
`6=Right+Down (-pi/4)`, `8=Left (+pi/2)`, `9=Left+Up (+3pi/4)`, and
`C=Down+Left (+pi/4)`. Every other nibble returns inactive.

## Vibration and actuator scheduling

`FUN_00113c70(record, small_on, large_intensity, milliseconds)` is the
per-port enqueue function. The first actuator byte is masked to one bit and is
sent as the small-motor on/off command; the second byte is the large-motor
intensity. This is more precise than treating the first argument as a generic
actuator index. The resident table at `0x00408050` includes small+large records
such as `(1,128,125)`, small-only `(1,0,125)`, and large-only `(0,215,125)`,
which confirms the paired-byte interpretation.

`FUN_0024c230` indexes that table as packed
`{ uint8 small_on; uint8 large_intensity; uint16 milliseconds; }` records:

| Index | Small | Large | ms | Index | Small | Large | ms |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 128 | 125 | 11 | 1 | 0 | 125 |
| 1 | 1 | 152 | 150 | 12 | 1 | 0 | 126 |
| 2 | 1 | 176 | 175 | 13 | 1 | 0 | 127 |
| 3 | 1 | 208 | 200 | 14 | 1 | 0 | 128 |
| 4 | 1 | 240 | 250 | 15 | 1 | 0 | 129 |
| 5 | 1 | 255 | 200 | 16 | 0 | 215 | 125 |
| 6 | 1 | 64 | 125 | 17 | 0 | 225 | 135 |
| 7 | 1 | 80 | 137 | 18 | 0 | 235 | 145 |
| 8 | 1 | 96 | 150 | 19 | 0 | 245 | 155 |
| 9 | 1 | 112 | 175 | 20 | 0 | 255 | 165 |
| 10 | 1 | 128 | 200 |  |  |  |  |

An enqueue is accepted only when:

- the global gate at `0x00602A00` is nonzero;
- the record is ready (`+0x43 == 0x40`); and
- actuator state `+0x2E` is nonzero.

The clean ELF initializes `0x00602A00` to 1. Its only direct clean-resident
reference is this read in `FUN_00113c70`; no resident writer was found. It is
therefore an enabled-by-default enqueue gate whose external/overlay control, if
any, remains unproven.

Milliseconds become nominal 60 Hz ticks using:

```text
ticks = (milliseconds * 3 + 25) / 50
```

For table indices 0 through 20 above, the resulting tick counts are
`[8,9,11,12,15,12,8,8,9,11,12,8,8,8,8,8,8,8,9,9,10]`. Every shipped
preset therefore begins above the actuator worker's `remaining > 5` send
threshold. For a custom nonnegative duration, 92 ms is the first value that
converts to six ticks; 0..91 ms converts to at most five and can never itself
pass that send test, although such an enqueue can still prune/subtract older
segments and change dirty flags. A zero-tick top is removed by the next
maintenance pass before it can be transmitted.

Each four-byte override entry is `{ uint16 remaining; uint8 flags; uint8
large_intensity; }`. Flag bit 0 means the entry must be sent when it becomes
top; bit 1 is the small-motor on/off byte. Entry 0 at record `+0x30` is a stop
sentinel. Live entries 1..3 form a maximum-depth-three LIFO override timeline:

- on enqueue, every older entry with remaining time less than or equal to the
  new duration is deleted;
- the new duration is subtracted from every older entry that would outlast it;
- the surviving entries are compacted and the new command is pushed on top;
- the previous top is marked dirty so that its residual tail is resent after
  the override ends.

Older commands therefore do not pause. Their residual tails represent how
long they would still have been active after the newer override's time span.
Only the current top is aged by `FUN_00113b80`, saturating at zero;
zero-duration tops are popped at the start of the next maintenance pass.

The decrement is exactly the byte returned by `FUN_00105da0`, system-context
`+0x01`. `FUN_00107560` sets that byte and resets context `+0x00`, the counter
which `FUN_001083a0` waits to reach `+0x01`. Initialization sets the value to 1;
the front-end task sets it to 2 immediately before entering its permanent main
state loop. This establishes that vibration durations are stored in 60 Hz
display ticks rather than update-call counts: a front-end update normally ages
the active segment by two ticks while the update loop is paced by two display
counts. The same distinction does **not** apply to the button repeat counter,
which increments once per `FUN_00113710` poll. Real elapsed timing still awaits
runtime validation.

At full depth, if all three older tails survive pruning, the code cannot push a
fourth entry even though it has already reduced those tails and marked the old
top dirty. The requested new command is dropped, while the shortened old top
can be retransmitted. This edge case is statically visible but has not been
reproduced at runtime.

`FUN_00113f40` owns configuration and actuator transmission. Once configured,
its actuator substates are:

| `+0x2E` | Meaning |
| ---: | --- |
| `0` | unavailable/disabled |
| `1` | idle; inspect the stop sentinel or current top |
| `2` | submit the zero/stop pair |
| `3` | submit the current active pair |
| `4` | one-worker-pass delay that samples the ordinary `libpad` request result after a successful EE-side submit |

It sends a dirty live top only while more than five ticks remain. When the
stack empties, dirty entry 0 causes `[0,0]` to be sent. The lower-level call is
`scePadSetActDirect`; alignment earlier established
`[00,01,FF,FF,FF,FF]`.

`scePadSetActDirect` itself does not mark request state busy: it starts the
separate direct-DMA path. Substate 4 nevertheless reads the ordinary pad
request state on the following worker pass. Complete returns to idle, failed
returns to idle and increments record `+0x40`, and busy leaves substate 4 in
place. Because neither the EE direct-DMA submitter nor the exact IOP direct
consumer changes that request state, this is not an acknowledgement of the
motor command. On the normal ready path it merely observes the completed
ordinary configuration request left by actuator alignment. An active-pair
EE-side submission failure also increments `+0x40` and routes through the stop
state; a stop submission failure simply remains in the stop state. No threshold
or other consumer of `+0x40` was found in the resident, so it is a wrapping
diagnostic count rather than a retry limit.

The active command's dirty bit is cleared before the submit attempt. Therefore
an active-pair return of zero—including the lower layer merely reporting that
its previous SIF DMA is still in flight—is not retried as an active command.
The wrapper increments `+0x40`, enters stop substate 2, and keeps retrying the
zero pair until it can be submitted; when it returns to idle, the still-live
top is no longer dirty. By contrast a failed stop retains substate 2 and is
retried. This makes direct-DMA contention capable of dropping a vibration
segment and replacing it with an eventual stop, not merely delaying the
segment.

The exact bundled IOP module exposes the other half of this transport. Port
open returns link-relative record `+0x80` as the direct-command destination;
the two `0x20`-byte halves are therefore record `+0x80` and `+0xA0`.
Link-relative `FUN_00000000`, called from the per-slot polling worker
`FUN_00002530`, compares their 32-bit sequence words as unsigned values and
selects half 1 only when `seq0 < seq1`, with a tie favoring half 0. If the
selected block's command word at `+0x04` is nonzero, it passes exactly six
payload bytes from `+0x0C` to `FUN_00004228` and then clears the command word.
It does not validate the block's size word at `+0x08`, and it clears the command
even when `FUN_00004228` refuses it.

The IOP apply routine accepts a direct command only while its slot is in
configuration level greater than 1 and current-task state 1. Before copying the
six bytes to the live actuator data it enforces a cross-controller power budget.
`FUN_00002298` sums the term-4/current value for every nonzero aligned actuator
on all other open slots; `FUN_00002404` then considers the current slot's six
alignment entries in order and zeroes any requested actuator byte that would
raise the cumulative value above `0x3C`. Any nonzero intensity consumes the
actuator's whole reported term-4 value for this test; it is not scaled by the
large-motor byte. With NA2's `[00,01,FF,FF,FF,FF]` alignment, the small motor is
considered before the large motor. A command can consequently be accepted by
the EE DMA layer yet be silently discarded by IOP state gating or partially
zeroed by the PADMAN power cap.

The IOP command-half comparison has the same non-modular-counter limitation as
the EE input-half selector. When a direct-command sequence wraps from
`0xFFFFFFFF` to 0, the freshly written even half appears older; the following
sequence selects the other half and the wrapped command can be lost before its
half is overwritten. This requires roughly 2^32 direct submissions and is a
latent static edge, not a practical observed failure.

## Resident soft-reset check

No statically recognizable resident software-reset/controller-combination path
was found in the clean boot ELF. In particular:

- canonical six-button IGR literals `0x0F09`, byte-swapped `0x090F`,
  `0x0F08`, `0x0F06`, and `0x0F0F` are absent from both preserved exports;
- no game reset/reboot string was found;
- `FUN_00168410` can reach `_LoadExecPS2` at `0x0015D920`, and
  `FUN_00168480` can reach `_ExecOSD` at `0x0015E100`, but neither wrapper has
  a Ghidra caller XREF, direct J/JAL reference, or stored pointer in the raw
  ELF; and
- a static call-graph intersection between controller readers and exit/relaunch
  ancestors produced only a false lead: `FUN_001e0980` handles pressed Start
  (`0x0800`) as a front-end/slideshow state change, while its separate exit
  ancestry is a vector-bounds fatal path.

This is a high-confidence **negative static result**, not proof that a computed
indirect path or an overlay cannot implement reset. No overlay, including
Adventure, was inspected for this check.

## Embedded `libpad` boundary

The following API identities are strongly inferred from exact behavior,
constants, packet layout, RPC command usage, the embedded library strings, and
matching PS2SDK source. They are not literal symbols recovered from the
stripped ELF and were not written back into the read-only disassembly.

| Runtime | Original export symbol | Strong ABI identification |
| ---: | --- | --- |
| `0x00174098` | `FUN_00174098` | `scePadInit` |
| `0x001741D8` | `FUN_001741d8` | internal SIF command callback |
| `0x00174220` | `FUN_00174220` | `scePadPortInit` |
| `0x00174300` | `FUN_00174300` | `scePadEnd` |
| `0x00174388` | `FUN_00174388` | internal actuator SIF-DMA submit |
| `0x001744A0` | `FUN_001744a0` | `scePadPortOpen` |
| `0x00174688` | `FUN_00174688` | `scePadPortClose` |
| `0x00174740` | `FUN_00174740` | select newest DMA snapshot |
| `0x001747A0` | no Ghidra function symbol | `padGetFrameCount` / `scePadGetFrameCount`-style helper |
| `0x001747F0` | `FUN_001747f0` | `scePadRead` |
| `0x001748A8` | `FUN_001748a8` | `scePadGetState` |
| `0x00174970` | no Ghidra function symbol | `padStateInt2String` |
| `0x001749A8` | `FUN_001749a8` | `scePadSetReqState` |
| `0x00174A50` | `FUN_00174a50` | `scePadGetReqState` |
| `0x00174AA0` | no Ghidra function symbol | `padReqStateInt2String` |
| `0x00174AD8` | `FUN_00174ad8` | `scePadInfoAct` |
| `0x00174BF8` | no Ghidra function symbol | legacy `scePadInfoComb` |
| `0x00174D18` | `FUN_00174d18` | `scePadInfoMode` |
| `0x00174E50` | `FUN_00174e50` | `scePadSetMainMode` |
| `0x00174F08` | `FUN_00174f08` | `scePadSetActDirect` |
| `0x00174FC8` | `FUN_00174fc8` | `scePadSetActAlign` |
| `0x001750A0` | `FUN_001750a0` | `scePadGetButtonMask` |
| `0x00175158` | `FUN_00175158` | `scePadSetButtonInfo` |
| `0x00175208` | `FUN_00175208` | `scePadInfoPressMode` |
| `0x00175268` | `FUN_00175268` | `scePadEnterPressMode` |
| `0x001752C0` | no Ghidra function symbol | `scePadExitPressMode` |
| `0x00175318` | `FUN_00175318` | `scePadSetVrefParam` |
| `0x001753E8` | `FUN_001753e8` | `scePadGetPortMax` |
| `0x00175450` | `FUN_00175450` | `scePadGetSlotMax` |
| `0x001754B8` | `FUN_001754b8` | `scePadGetModVersion` |
| `0x00175520` | `FUN_00175520` | `scePadSetWarningLevel` |
| `0x00175588` | `FUN_00175588` | unreferenced pad-DMA-completion callback registration using RPC `0x18`; exact public API name unknown |

`scePadInit(0)` binds SIF RPC clients at `0x00615D40` and `0x00615D68` to
servers `0x80000100` and `0x80000101`, checks that the pad-module version's
high byte is 4, then calls the port initializer. Both bind loops have no
timeout. The library initialized word is set to 1 before either bind begins;
this compiled client never reads it and clears it only after a logical-success
reply from `scePadEnd`. The adjacent diagnostic-enable word is initialized to
1 and gates the version-mismatch, bad-alignment, already-open, and direct-DMA
failure messages.

On a nonnegative port-initializer RPC transport result, the client registers
SIF command handler `0x80000019` even if the returned logical result is zero.
Conversely, any nonnegative `scePadEnd` transport result removes that handler
before the logical result is examined; only result 1 also clears the initialized
word. These orderings matter only on unusual logical-failure replies and were
not exercised dynamically. The embedded client globals relevant to this path
are:

| Runtime | Size/layout | Role |
| ---: | --- | --- |
| `0x003FAC10` | 4 bytes | write-only library initialized bookkeeping word |
| `0x003FAC14` | 4 bytes | enabled-by-default diagnostic-print gate |
| `0x00615D40` / `0x00615D68` | `0x28` each | SIF RPC client objects |
| `0x00615D90` | `port*0x70 + slot*0x1C` | per-slot client records for two ports by four slots |
| `0x00615E80` | `port*0x80 + slot*0x20` | direct-actuator command blocks |
| `0x00615F80..0x00615FFF` | `0x80` | shared synchronous RPC buffer |
| `0x00616000` | 4 bytes | saved GP for the optional command callback |
| `0x00616004` | 4 bytes | optional command callback pointer |

Each `0x1C`-byte per-slot client record at `0x00615D90` contains: caller EE
DMA-area pointer `+0x00`, local direct-command-block pointer `+0x04`, returned
IOP command destination `+0x08`, last direct-DMA ID `+0x0C`, and open flag
`+0x10`. Words `+0x14/+0x18` are cleared by port initialization but have no
identified linked-client use.

Each caller-provided DMA area must be `0x40`-byte aligned and is exactly
`0x100` bytes: two `0x80`-byte snapshots. `FUN_00174740` invalidates the area,
compares signed generation words at snapshot `+0x58`, and selects half 1 only
when `frame0 < frame1`; otherwise it selects half 0.
The selected snapshot stores packet length at `+0x60`, state at `+0x70`, and
request state at `+0x71`; `scePadRead` copies precisely the recorded packet
length. On open, both snapshots begin with generation 0, length 0, state 5,
request state 2, and packet bytes `+0x00..+0x1F` filled with `0xFF`.

The complete ABI-correlated snapshot layout is below. Names in the middle
column come from the matching PS2SDK `pad_data` layout; the last column states
what this exact compiled client proves. This distinction matters because the
PS2SDK homolog calls the trailing eleven bytes padding while this newer client
directly uses four of them for the pressure-button mask.

| Snapshot | ABI-correlated field | Direct clean-client evidence |
| ---: | --- | --- |
| `+0x00..+0x1F` | `data[32]` | raw packet bytes copied unchanged by `scePadRead` |
| `+0x20..+0x27` | `actDirData[2]` | exact IOP producer copy of its current direct-actuator data; not read by the linked EE client |
| `+0x28..+0x2F` | `actAlignData[2]` | exact IOP producer copy of its current actuator alignment; not read by the linked EE client |
| `+0x30..+0x4F` | `actData[8][4]` | exact IOP producer copy of four actuator records followed by four `combData[4][4]` records; queried by `scePadInfoAct`/`scePadInfoComb` |
| `+0x50..+0x57` | `modeTable[4]` | exact IOP producer copy of four `uint16` mode entries queried by `scePadInfoMode` |
| `+0x58..+0x5B` | `frame` | signed 32-bit generation word used for active-half selection |
| `+0x5C..+0x5F` | `findPadRetries` | exact IOP producer copy; not read by the linked EE client |
| `+0x60..+0x63` | `length` | valid packet length used by `scePadRead` |
| `+0x64` | `modeConfig` | exact IOP producer byte; configuration level required by mode/actuator queries |
| `+0x65` | `modeCurId` | exact IOP producer byte; current controller ID whose high nibble supplies the public mode |
| `+0x66` | `model` | exact IOP producer byte; controller/model value and a prerequisite for button-mask access |
| `+0x67` | `buttonDataReady` | low byte of the exact IOP producer's data-ready word |
| `+0x68` | `nrOfModes` | exact IOP producer byte; mode-table entry count |
| `+0x69` | `modeCurOffs` | exact IOP producer byte; current mode-table offset |
| `+0x6A` | `nrOfActuators` | exact IOP producer byte; actuator count |
| `+0x6B` | `numActComb` | exact IOP producer byte; combination count returned by `scePadInfoComb` |
| `+0x6C` | `val_c6` | exact copy of an internal word's low byte; cleared on open and set to 1 at the end of one configuration worker, but its external meaning remains unresolved |
| `+0x6D` | `mode` | exact IOP producer byte; not read by the linked EE client |
| `+0x6E` | `lock` | exact IOP producer byte; not read by the linked EE client |
| `+0x6F` | `actDirSize` | low byte of the exact IOP producer's direct-actuator-size word; not read by the linked EE client |
| `+0x70` | `state` | pad state returned by `scePadGetState` |
| `+0x71` | `reqState` | request state read and locally changed by setters |
| `+0x72` | `currentTask` | must equal 1 before mode, actuator, or button-mask metadata is trusted |
| `+0x73` | `runTask` | low byte of the exact IOP producer's run-task word; not read by the linked EE client |
| `+0x74` | `stat70bit` | low byte of the exact IOP producer's `stat70bit` word; not read by the linked EE client |
| `+0x75..+0x78` | requested button-information mask | exact IOP producer copy of the value submitted by `scePadSetButtonInfo`; no linked-client reader identified |
| `+0x79..+0x7C` | supported button-information mask | exact IOP producer copy, assembled little-endian by `scePadGetButtonMask` |
| `+0x7D..+0x7F` | reserved | no writer in the exact IOP snapshot-construction path and no linked-client reader |

The exact IOP producer builds this snapshot in the first `0x80` bytes of each
link-relative record at `0x00008160 + port*0x710 + slot*0x1C4`. For every open
slot, it stores the current 32-bit frame value at snapshot `+0x58`, increments
the internal counter, and sends the snapshot to the caller's EE area: an even
pre-increment frame goes to half 0 and an odd frame goes to half 1. This is the
producer-side counterpart of `FUN_00174740`'s signed newest-half selection.
All of the table entries called exact IOP copies above come directly from this
construction loop, not only from a homologous SDK structure.

`scePadInfoMode` returns zero unless the slot is open, `currentTask == 1`, and
the request state is not busy. Selector 1 returns the high nibble of
`modeCurId`, except exact ID `0xF3` maps to zero. Selector 2 returns the current
`modeTable` entry and selector 3 returns `modeCurOffs`; both reject
`modeConfig == 1`. Selector 4 returns `nrOfModes` for index `-1`, or an indexed
16-bit mode-table entry when configuration permits and the signed index is
less than `nrOfModes`. It does not reject negative indices other than treating
`-1` specially, so out-of-contract values below `-1` read before the table.

`scePadInfoAct` likewise requires an open slot and `currentTask == 1`, and also
requires `modeConfig >= 2`. Actuator index `-1` returns `nrOfActuators`;
otherwise terms 1 through 4 return the four bytes at
`actData[index][term-1]`. The linked NA2 wrapper uses only the count and terms
1 through 3 for its exact two-actuator capability test. Here too, the only
lower-bound special case is `-1`; a more-negative out-of-contract actuator
index can address before `actData`.

Instructions `0x00174BF8..0x00174D10` are another valid standalone function
that the Ghidra export did not promote. They match legacy `scePadInfoComb`:
after the same open/current-task/mode-configuration checks, combination index
`-1` returns `numActComb`; selectors `-1,0,1,2` return the four bytes of
`combData[index]` at snapshot `+0x40 + index*4`. This explains the historical
layout: the IOP producer copies four actuator records followed immediately by
four combination records, while the EE actuator accessor treats the contiguous
region as eight actuator records. The combination helper also accepts negative
indices below `-1` because it has only an upper-bound comparison. Raw-ELF scans
found no direct J/JAL instruction or stored pointer to `0x00174BF8`, so the API
is linked but unused by NA2.

`scePadGetButtonMask` returns zero unless the slot is open, `currentTask == 1`,
`modeConfig >= 2`, and `model >= 2`; otherwise it assembles bytes
`+0x79..+0x7C` into a 32-bit mask. `scePadInfoPressMode` tests that result for
exact equality with `0x0003FFFF`.

The instructions at `0x001747A0..0x001747EC` form a valid standalone
frame-count helper even though the export did not create a `FUN_*` symbol. It
returns zero for a closed slot; otherwise it calls the half selector and returns
snapshot `frame`. The matching PS2SDK source explicitly calls the omitted API
`padGetFrameCount`. Raw-ELF scans found no direct J/JAL instruction or stored
pointer to `0x001747A0`, so it is linked but unused by NA2.

Two other unpromoted standalone routines format those state tables:
`0x00174970..0x001749A4` accepts state values below 8, and
`0x00174AA0..0x00174AD4` accepts request values below 4; each tail-calls the
resident string copy with the indexed name and otherwise writes an empty
destination string. The request-name table has only three valid pointers and a
null fourth word, so passing request value 3 reaches string copy with a null
source. Neither formatter has a Ghidra XREF, raw J/JAL encoding, or stored
pointer in the clean ELF, making this a latent unused-library defect.

The unpromoted instructions at `0x001752C0..0x00175310` are likewise the
standard `scePadExitPressMode` wrapper: they return zero when the slot is closed
and otherwise call `scePadSetButtonInfo(port, slot, 0)`. No direct J/JAL or
stored pointer targets the helper, so NA2 enters pressure mode during setup but
never invokes the linked exit wrapper.

Successful RPC configuration setters mark request state busy; callers poll for
complete or failed. `scePadSetActDirect` is different: it copies six bytes to
the per-slot `0x20` command block and submits a direct SIF DMA transfer. It does
not use the shared synchronous RPC buffer.

That direct block is `{ uint32 sequence; uint32 command; uint32 size;
uint8 payload[6]; ... }`; `scePadSetActDirect` writes command 1 and size 6.
`FUN_00174388` submits only when the saved DMA ID is zero or
`sceSifDmaStat(id) < 0`, increments the sequence, cache-syncs all `0x20` bytes,
and sends them to `IOP_base + ((sequence & 1) * 0x20)`. An in-flight previous
transfer or a zero ID from `sceSifSetDma` returns failure without queuing a
second transfer. This double-destination command path is separate from the
two-half input snapshot.

`scePadSetActDirect` checks snapshot `currentTask == 1` but does not first test
the per-slot open flag. On an out-of-contract call before open it can select
through a null DMA-area pointer; after close it can reuse the stale pointers
that port initialization/close leave in the slot record. NA2's ready/substate
gates prevent such a call on its ordinary path, but the library function is not
self-protecting in the way `scePadRead`, `scePadGetState`, and the metadata
queries are.

The shared `0x80` synchronous RPC buffer has no internal lock in this client.
NA2 avoids a proven collision by routing init/open/configuration/close/end
through the single pad worker; ordinary state/read calls consume the DMA
snapshot instead. Direct actuator submission uses the per-slot command block,
not the shared RPC buffer. This is call-graph serialization, not a general
thread-safety guarantee for hypothetical additional callers.

The unreferenced `FUN_00175588` preserves enough behavior to describe without
guessing its public name: passing null clears the saved callback and repeatedly
issues RPC command `0x18` with value 0 until transport submission succeeds;
installing the first non-null callback similarly sends value 1, then stores the
callback and caller GP under an interrupt-safe critical section. It returns the
previous callback. `FUN_001741d8`, registered for SIF command `0x80000019`,
invokes that callback with incoming command data at `+0x0C` while restoring the
saved GP.

The exact bundled IOP dispatcher maps RPC `0x18` to a one-argument setter for
its link-relative global at `0x00008FBC`. Its snapshot-transfer loop proves the
event semantics. With that value unequal to 1 it submits the open slots' input
snapshots through the ordinary SIF-DMA path and sends no command. With value 1,
it submits the whole snapshot batch through a completion-aware DMA path, waits
for that batch to finish, stores the current IOP VBlank counter in word `+0x0C`
of a 16-byte command packet, and sends command `0x80000019`. It does this only
when at least one slot contributed a snapshot. The EE callback argument is
therefore the IOP VBlank counter associated with a completed pad-DMA batch,
not a port number or pad-state pointer. The client sends only values 0 and 1.
This resolves the callback's event meaning, although its exact public Sony API
name remains unresolved. Neither the registration function nor its handler has
an NA2 caller beyond the handler registration performed by port initialization.

`FUN_00175520` likewise has no caller: it sends its single argument with RPC
command `0x14`, returns reply word `+0x08`, and returns zero on transport
failure. Bundled PS2Dis PADMAN RPC metadata maps command `0x14` to
`scePadSetWarningLevel`; the exact IOP dispatcher independently confirms that
the command stores the supplied warning/diagnostic gate and returns 1. This
makes the API identity strong even though the stripped ELF retains no symbol.

The embedded client allocates bookkeeping for two ports and four slots per
port, but NA2 directly uses only ports 0 and 1, slot 0. No
multitap/secondary-slot path was identified in the resident wrapper. The
bundled PADMAN RPC metadata names command `0x11` as `scePadGetConnection`, but
this linked client contains no command-`0x11` wrapper or call. Moreover, the
exact embedded PADMAN dispatcher has no `0x11` case and routes it to its invalid
function-code default, so that legacy connection call is not implemented by
this matched module either. Resident connectivity is derived exclusively from
`scePadGetState`. The compiled client routines do not bounds-check port/slot
indices, the active-half selector uses signed `slt(frame0, frame1)` with ties
favoring half 0, and no modular frame-counter handling is evident. In
particular, a transition from `0x7FFFFFFF` to `0x80000000` can make the newly
written half appear older for one selection interval; reaching that edge under
normal operation would require an extremely long-lived counter.

Port open/close bookkeeping has a static failure trap. After a nonnegative RPC
transport result, `scePadPortOpen` marks the EE slot open and installs its
pointers before returning the IOP reply; `scePadPortClose` similarly clears the
EE open flag before returning the reply. NA2's worker insists on reply 1 and
retries otherwise, but a second open on an EE-marked-open slot or close on an
EE-marked-closed slot returns 0 without another RPC. An unexpected logical
reply 0 after successful transport can therefore wedge the corresponding
worker retry loop.

The game wrapper changes its own record state only on reply 1, so these cases
also split the two state layers. A logical-zero open leaves the wrapper at
state 0 while the low-level slot is marked open; core polling therefore skips
that otherwise-open slot. A logical-zero close clears the low-level open flag
but leaves the wrapper's prior state, potentially `0x40`; core polling then
sees unopened sentinel 99 and publishes zero-derived input without resetting
the wrapper state. If actuator substate remains nonzero, vibration enqueues can
still pass the wrapper's ready gate while the close-retry loop no longer runs
the actuator machine, so they only modify/age the local stack. No occurrence
was runtime-observed.

As static cross-game corroboration, the clean NUN5 `SLES_556.05` and NUN6
`SLUS_556.06` residents contain the same tag and an instruction-identical
`libpad` function sequence shifted by `+0xDC0` (for example, NA2
`0x00174098` corresponds to `0x00174E58`). This corroborates the library
identity; it does not establish that those games use the same higher-level
wrapper behavior.

### Matching IOP PADMAN function map

The supporting module is stripped too. These are link-relative addresses and
the temporary Ghidra labels used to state direct evidence; the suggested roles
are not recovered original symbols.

| IOP link address | Temporary label | Direct static role |
| ---: | --- | --- |
| `0x00000000` | `FUN_00000000` | select and consume the newest direct-actuator command half |
| `0x00000360` | `FUN_00000360` | construct and SIF-DMA all open slots' EE input snapshots |
| `0x000008E0` | `FUN_000008e0` | VBlank handler that increments the callback counter and wakes pad work |
| `0x00002298` | `FUN_00002298` | sum active actuator-current terms on other open slots |
| `0x00002404` | `FUN_00002404` | enforce the `0x3C` aggregate actuator-current cap |
| `0x00002530` | `FUN_00002530` | per-slot read/update worker |
| `0x000026C0` | no promoted `FUN_*` symbol | per-slot discovery/query/configuration worker |
| `0x00003304` | `FUN_00003304` | module entry/initialization path |
| `0x00003778` | `FUN_00003778` | port-open implementation and per-slot worker creation |
| `0x00003A24` | `FUN_00003a24` | port-close implementation |
| `0x00003AF4` | `FUN_00003af4` | build the outgoing 32-byte packet and normalize pressure consistency |
| `0x00003F04` | `FUN_00003f04` | actuator-info implementation |
| `0x00004004` | `FUN_00004004` | actuator-combination-info implementation |
| `0x000040F0` | `FUN_000040f0` | mode-info implementation |
| `0x00004228` | `FUN_00004228` | accept/power-limit/copy six direct-actuator bytes |
| `0x000046D4` | `FUN_000046d4` | set the warning/diagnostic gate for RPC `0x14` |
| `0x000046E4` | `FUN_000046e4` | set ordinary-DMA versus completion-command mode for RPC `0x18` |
| `0x00007648` | `FUN_00007648` | main service `0x80000100` RPC dispatcher |

## Resident function map

Suggested semantic names here are documentation-only.

| Runtime | Original symbol | Suggested role | Direct relationship |
| ---: | --- | --- | --- |
| `0x00105FC0` | `FUN_00105fc0` | allocate system context | caller of context constructor and `FUN_00107f80` |
| `0x001081B0` | `FUN_001081b0` | system update | calls `FUN_00113480` before registered callback |
| `0x00108490` | `FUN_00108490` | end-of-update snapshot | copies public held into record `+0x60` |
| `0x00113480` | `FUN_00113480` | update both pads | ages both vibration stacks, then polls both pads |
| `0x001134E0` | `FUN_001134e0` | initialize both records | calls `FUN_00114930` twice |
| `0x00113530` | `FUN_00113530` | pad worker | init/open/configure/actuate/close/end lifecycle |
| `0x00113710` | `FUN_00113710` | poll/decode one pad | calls get-state, read, and stick conversion |
| `0x00113B80` | `FUN_00113b80` | age vibration top | called for each pad before packet polling |
| `0x00113C70` | `FUN_00113c70` | enqueue vibration override | called by resident effect/gameplay wrappers |
| `0x00113F40` | `FUN_00113f40` | configuration/actuator machine | calls mode, pressure, actuator, and request APIs |
| `0x00114850` | `FUN_00114850` | close wrapper | calls `scePadPortClose` |
| `0x001148C0` | `FUN_001148c0` | open wrapper | calls `scePadPortOpen` with record DMA pointer |
| `0x00114930` | `FUN_00114930` | initialize one record | called only by `FUN_001134e0` |
| `0x00114B40` | `FUN_00114b40` | stick polar conversion | called twice per readable analog packet |
| `0x00114D90` | `FUN_00114d90` | analog-to-D-pad sector | called by the active and cloned adapters |
| `0x00114E60` | `FUN_00114e60` | D-pad-to-analog helper | statically unreferenced |
| `0x001D0590` | `FUN_001d0590` | scheduler loop | calls system update before tasks |
| `0x001E0D20` | `FUN_001e0d20` | active front-end adapter | called once from `FUN_001e0ee0` |
| `0x0037D7C0` | `FUN_0037d7c0` | duplicate adapter | statically unreferenced |

## Useful negative results and remaining uncertainty

- The work is static-only. Update cadence, disconnect presentation, pressure
  values, vibration timing, and adapter behavior have not been live-tested.
- Record `+0x46` remains semantically opaque. `FUN_00114930` initializes it to
  zero; `FUN_00113710` merely snapshots it and writes back `value & 3` without
  branching on either surviving bit. No other direct clean-resident access to
  the two context instances was found, so bits 0/1 are preserved storage with
  no proven resident effect.
- No clean-resident writer of pad-worker lifecycle value 2 at `0x006073B0` was
  found. An overlay or indirect path may own shutdown.
- No statically recognizable resident soft-reset/controller combo was found;
  the resident OS relaunch wrappers are unreferenced library code.
- `FUN_0037d7c0` and `FUN_00114e60` are byte/code-level matches for useful
  compatibility operations but have no proven caller in the clean ELF.
- No active right-stick-to-digital adapter was found; the proven adapter uses
  only the left stick.
- The wrapper reserves 32 raw packet bytes, but only offsets through pressure
  byte 19 have a proven resident decode.
- `scePadSetVrefParam`, `scePadSetWarningLevel`, the port/slot maxima queries,
  `scePadExitPressMode`, and the callback/RPC-`0x18` path have no NA2 caller.
- `scePadInit` can wait indefinitely for both RPC binds; the pad worker's
  init/open/close/end retry loops likewise have no static timeout.
- Adventure-mode input consumers were deliberately not inspected.

## Provenance

The evidence archive was inspected read-only with PowerShell, `rg`, the
preserved Ghidra decompiler/listing exports, and the bundled EE
`readelf`/`objdump` tools. Raw ELF reads verified the load mapping and the
direction/vibration tables. Findings from independent read-only inspections of
the wrapper, embedded `libpad`, and compatibility adapters were reconciled
against the same clean ELF before promotion here.
