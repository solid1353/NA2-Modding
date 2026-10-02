# Battle audio and cue scheduling

This document owns EE-side battle audio requests and their scheduling in
retail NA2 (`SLPS-25837`). Complete-file identities and overlay
address conventions are in [Retail game file identities](../game/files/file_identities.md).

## Research coverage

- **Assigned scope:** EE-side battle voice and SFX requests, command queues, selectors, archive/bank/member resolution, animation/action/event cue producers, interruption and lifetime.
- **Exploration depth:** Bounded static coverage includes all
  202 voice controls, 423 SFX controls, 93 event-pointer pairs, 94 character-bank
  records, three sound-task loops, compact append/DMA/RPC consumers and bank
  state machines. Local cue blocks were examined in all recovered resident
  caller sets of 35 direct-event, 53 pseudo-event and five direct-control
  functions. The central fighter scheduler, four BTL queued-voice callsites,
  cinematic row consumer and guide scheduler/constructor were also inspected;
  guide coverage includes all 94 selector entries and fifteen cue rows, the
  concrete parent allocation/publication, command-owner update gate, event
  trigger and local teardown. Cinematic coverage includes the selected resident
  row binding and match-category-6 admission; it is not a complete resource
  inventory. The selected deferred voice producer's eight-byte row stride,
  inline FIFO copy and consumption-time binding were also traced.
- **Confirmed coverage:** Fighter events select compact control records, while
  explicit BTL requests resolve filename voice numbers to PLVOICE members.
  Queues have bounded capacity and distinct consumers; failed appends/drains
  are not retained for retry. Pending stream replacement stops the prior slot
  before selection succeeds. Literal cooldown/countdown units, action-cursor gates,
  surface selectors, bank sharing, token capacity and cached activity contracts
  are established below. The guide event trigger sets a five-call countdown;
  its condition query is a constant-zero retail stub, and the recovered guide
  allocation does not initialize its prior-member halfword. Selected cinematic
  rows retain resident pointers; deferred voice producers copy numbers into
  an eight-entry FIFO and bind fighter/slot at consumption. Category 6 uses
  a separate key lookup and common-packet request with a fighter-derived
  program byte.
- **Unresolved or untested:** `SNDBASE.IRX` command decoding, program-to-sample
  identity, audible sample duration, IOP priorities and audible lifetime remain unknown. Inter-task
  wall-clock cadence, complete authored cinematic/dialogue resources and every
  indirect or character-specific owner are not established.
  Successful descriptor admission does not prove that the requested resource
  starts or remains audible. The initial guide allocation payload, complete
  guide state-writer coverage and remaining cinematic row producers are
  unresolved.
- **Deliberate exclusions and overlap:** [Character assets](../game/character_assets.md#voice-archive)
  owns the complete player-voice inventory and filename-number lists;
  [Audio and video replacement](../game/files/audio_video_replacement.md#actual-codec-and-archive-map)
  owns archive and codec contracts; [Startup](../game/startup.md#audio-initialization-bottleneck)
  owns eager initialization; [Task system](../runtime/task_system.md) owns
  cooperative task semantics. [Scene playback callers and owners](../runtime/scene_playback_owners.md)
  owns scene cursor progression; [Ultimate jutsu](ultimate_jutsu.md) owns
  the presentation and [Ultimate Jutsu cinematics](ultimate_jutsu_cinematics.md)
  the cinematic selection; [Stage surface attributes](stage_surface_attributes.md)
  owns the surface values that select surface SFX. This document owns battle request
  consumers and scheduling, and does not duplicate those inventories.
- **Evidence limitations:** static analysis covers the resident ELF and BTL/ETC
  overlays, not `SNDBASE.IRX`. EE command construction does not establish IOP
  command execution, audible timing or sound identity. Preserved analysis has
  incomplete xrefs and false function boundaries, so direct-caller sets are not
  completeness claims.

## Fighter voice-event selection

**Observation:** Resident `FUN_002040D0` accepts event indices `0..32` and
does nothing when `FUN_00217860()` returns `4`, `5` or `6`. Events `0x18`
and `0x19` additionally reject fighter state halfwords `+0x18E == 5/6` or a
nonzero `+0x19A`, then set `+0x19A` to `0x3C`. `FUN_00214A40` initializes
the halfword to zero. `FUN_0024C440` decrements it by one when nonzero,
under fighter node flag `+0 & 2`, before its positive-pause branch. Instructions
`0x0024C768..0x0024C778` establish the literal decrement; this cooldown does
not multiply by the action-rate scalar. Its unit is an admitted housekeeping
call, not an established wall-clock second.

`FUN_00203E90` selects one of two pointers per fighter from resident
`0x00406CE0`, indexed by `(fighter.+0x68 - 1) * 8`. It switches to the second
pointer when the following action predicates are true. Other identities use
the first pointer.

| Fighter ID | `FUN_00306420(fighter, action)` predicates selecting the second list |
| ---: | --- |
| `1` | `0x0E` |
| `2` | `0x0F` |
| `3` | `0x10` |
| `0x39` | `0x39`; the argument survives from `li a1,0x39` at `0x00203EC4` to the call at `0x00203F5C` |
| `0x43` | `0x44` or `0x45` |
| `0x45` | `0x47` or `0x48` |

The selected list supplies a halfword control index. `FUN_002040D0` routes
that index to `FUN_001D4400(index, fighter_id, position, parameter)` when
its fourth argument is zero, otherwise to
`FUN_001D4080(index, fighter, parameter)`. Neither index is an AFS member.

### Complete event-list coverage

**Observation:** All 93 pointer pairs at `0x00406CE0..0x00406FC7` select only
three 33-halfword lists: `0x005C16C0`, `0x005C1710`, `0x005C1760`.
The second and third lists are respectively the first list plus 110 and 160
in every slot. Normal pointers use `0x005C1760` for IDs `47..56,73..75`
and `0x005C16C0` for all other IDs. Alternate pointers use `0x005C1760` for
ID 1, `0x005C1710` for IDs `2,3,20,57,67,69`, and `0x005C16C0` otherwise.
The selector above only activates six identities' alternate pointers; a
different pointer stored for ID 20 does not establish that this selector
reaches it.

| Event slots, inclusive | First-list control indices in order |
| --- | --- |
| `0x00..0x08` | `0,1,2,3,4,5,6,7,8` |
| `0x09..0x16` | `12,13,14,15,16,17,18,19,20,21,22,23,24,25` |
| `0x17..0x20` | `28,26,27,38,39,40,23,36,37,41` |

Controls for event `0x20` are disabled in all three lists. Event `0x19`
selects disabled control 27 only in the first list; its second/third-list
controls 137/187 are enabled. This is established table suppression,
independent of the shared event cooldown.

`FUN_00204220` additionally accepts pseudo-events `-2`, `-3`, `-4`: it calls
`FUN_00180210(3)` and converts returned `0..2` into event groups `6..8`,
`3..5`, `0..2`, respectively; returned 3 suppresses the request. Event `-1`
also suppresses it. `FUN_002043E0` bypasses the event lists and supplies a
control index directly, retaining the same object-versus-ID dispatcher choice.

## Compact battle commands

**Observation:** `FUN_001D4080` and `FUN_001D4400` accept control indices
`0..201` in the eight-byte table at resident `0x003FC350`. A negative signed
byte at record `+0` suppresses emission. Both reject fighter ID `0x27`.
The object-based route first calls the suppression predicate
`FUN_001D3F90`; it chooses handle `0x00607528` or `0x00607538` from fighter
`+0x60` bit zero. The ID-based route compares the ID with the audio context's
halfwords `+0x0A/+0x0C`, alternating its `+0x10` selector between 1 and 2 when
both IDs are equal. An unmatched ID returns without emitting.

`FUN_001D3F90`, instructions `0x001D3F90..0x001D4078`, suppresses requests
when the command/RPC context is absent or its bank-transaction byte `+0x20`
is nonzero. It also suppresses coordinator state 6/substate 0 while context
`+0xD8 == 1`. The coordinator getters `FUN_00250820/50/80` return words
`+0x14/+0x18/+0x1C` through the global owner and its `+8` child, or `-1`
when absent.

**Instruction observation:** The state-3 branch at
`0x001D4028..0x001D4060` requires one substate read to be nonpositive,
then a second read of the same getter to be at least 2, before testing counter
`< 30`. With an unchanged getter source those conditions cannot both hold.
This is the actual retail branch, not evidence of a normal substate `0..1`
suppression window; no intervening yield or source update is present in this
branch's inspected instructions.

The record's signed byte `+4` caps the value produced by `FUN_001D2FD0`
from position; a negative result suppresses emission. Position also feeds
`FUN_001D32A0`, which supplies a low-halfword scalar and an upper byte.
An out-of-range caller byte selects record `+3` instead.

| Emission order | Constructed bytes and source |
| ---: | --- |
| 1 | Two bytes: `0xC0 | record[2]`, `record[0] & 0x7F`; appended to stream `record[1]` through `FUN_00177018`. |
| 2 | Five-byte form beginning `F9 01 record[2]`, followed by the helper's upper byte and zero. |
| 3, conditional | Five-byte form `F9 02 record[2] 78 3F` when the helper's low halfword is strictly between `0x4000` and `0xC000` and position is supplied. |
| Last | Seven-byte form beginning `FD 10 record[2]`, followed by selected caller/record byte, zero, capped positional value, zero. |

Instructions at `FUN_00177140`, `0x00177168..0x00177178`, explicitly select
five bytes for `F9` and seven for `FD`. These are observed encodings, not
decoded IOP operations.

`FUN_00177018` accepts leading nibbles `80/90/A0/B0/C0/D0/E0`; the `80/C0/D0`
forms append two bytes, and `90/A0/B0/E0` append three. `FUN_00176F80` resolves a selected stream through
`handle.+4 -> stream-count +8 / stream-table +0x0C`, then an eight-byte table
row's `+4` buffer pointer. Buffer `+0` is capacity, `+4` is used byte count,
and payload begins at `+8`. It appends only if `used + length + 8 <= capacity`,
returns zero on success and `-1` otherwise. It does not overwrite old bytes or
grow the buffer. The battle dispatchers do not inspect the append return.

### Complete control-table census

**Observation:** The complete `0x650` bytes at `0x003FC350..0x003FC99F`
contain 202 records: 123 enabled and 79 disabled. Every record has `+1 == 0`,
`+2 == 0`, `+4 == 0x7F`, `+5 == 0x7F`, and signed halfword `+6 == 0x0100`.
Thus this table always emits to stream zero/channel byte zero; variability is
the signed program byte `+0` and default byte `+3`. Disabled records have
`+0 == 0xFF`; enabled program bytes span `0..0x39` with holes. The default
byte's complete distribution is `0x3C:94`, `0x3D:47`, `0x3E:46`,
`0x3F:4`, `0x40:4`, `0x41:3`, and one each of `0x42..0x45`, including
disabled records. Repeated program bytes paired with different default bytes
are actual distinct controls; the control index alone is not a clip number.

### Position-dependent command parameters

**Observation:** `FUN_001D2FD0` obtains a reference XYZ vector through
`FUN_001D2E80` and computes full three-dimensional Euclidean distance `d`.
With no position or no reference it returns `127`. Otherwise:

```text
scale = 100                              when d < 700
scale = ((2700 - d) / 20) * record.s16[6] / 256  otherwise
value = CVT_W_S(record.s8[4] * scale / 100)
value = -1 when value < 1; capped at 127 otherwise
```

The dispatcher additionally caps this at record `+4`. **Inference (high
confidence):** this is an attenuation scalar. Its use in an `FD` command is
proven; the IOP-side unit and mixing equation are not.

`FUN_001D32A0` also obtains two reference vectors, computes two planar
`FUN_0016F4C0` angles from their first two coordinates, converts their difference
to a wrapping 16-bit angle and combines it with
`CVT_W_S(63 - FUN_0016F2E8(angle_in_radians) * 63)` in the upper halfword.
The dispatcher sends its upper byte value in the `F9 01` packet and uses its
low-halfword range to select `F9 02`. With no reference, or the first angle
equal to zero, it returns `0x003F0000`; its null-position path returns only
`0x3F`. **Inference (medium confidence):** these encode direction-dependent
stereo parameters. The helper's coordinate convention and IOP interpretation
remain unresolved; the apparent first-two-coordinate plane is retained rather
than silently replacing it with an assumed XZ plane.

`CVT_W_S` above denotes the actual `cvt.w.S` instruction, observed at
`0x001D30EC` and `0x001D3420`; the helper's angle conversions also use it at
`0x001D3354/0x001D33B4`. None of these inspected bodies changes FCSR.
The rounding mode throughout their caller lifetime is not established, so
decompiler integer casts are not treated as proof of truncation toward zero.

## Pending streamed requests

**Observation:** `FUN_001D2570` allocates a `0x78`-byte audio context and
initializes it through `FUN_001D24C0`. Four request rows begin at context
`+0x14`, with stride `0x14`. Each row's first four words initialize to `-1`
and its pending byte initializes to zero.

| Row-relative offset | `FUN_001D2C20` consumer contract |
| ---: | --- |
| `+0x00` | Descriptor/bank index used when alternate field is zero |
| `+0x04` | Physical inner member |
| `+0x08` | Stream slot, stopped before the replacement request |
| `+0x0C` | Zero selects family 3; nonzero is the family-0 descriptor index |
| `+0x10` | Pending byte; nonzero consumed and cleared |

`FUN_001D2C20` scans rows 0..3 in order, calls `FUN_001D9900(slot)` first,
then `FUN_001D97D0(bank, member, slot, family)`, and clears pending regardless
of the returned result. This is a bounded pending array, not evidence of a
FIFO or retry mechanism.

`FUN_001D97D0` accepts stream slots `0..2` and families `0`, `2` and `3`.
Its descriptor base comes from `0x003FE2E0[family]`; records have stride eight.
The bases are `0x003FDCD0` (SOUND), `0x003FDD50` (RPGVOICE), and
`0x003FDFF0` (PLVOICE). It rejects negative bank/member values, compares the
bank with inclusive bounds `13/82/93`, and rejects
`member >= signed_halfword(record.+6)`. The inclusive endpoint of each family
selects an all-`0xFF` sentinel with negative member count, so it cannot accept
a nonnegative member. bytes at `0x003FDD38`, `0x003FDFE0` and
`0x003FE2D8` corroborate the sentinels; initialized family bounds 82/93 are
at `0x00602C50/+4`.
When global `iGpffffCBA4` is nonzero it returns zero without starting; otherwise
it calls `FUN_001D6F60(manager, slot, record.+0, member, record.+4)` and returns
one. Family 3's 93 player descriptors and their archive mapping are owned by
[Character assets](../game/character_assets.md#voice-descriptors-and-filename-number-lists).

**Observation:** Bytes at `0x001D2DE0..0x001D2E7C` confirm the
filename-number lookup fragment: it indexes `0x003FF900` by character ID,
scans a signed-halfword list to `-1`, retains the matched physical index or
`-1`, and writes row `slot * 0x14` with character ID minus one, member,
slot, alternate-family zero and pending one. It checks only `character < 94`
at entry; this is not a demonstrated public range contract. The fragment is
not a recognized Ghidra function. Its recovered BTL callers below establish
explicit queued voice requests, but do not establish that compact battle
commands feed this queue.

### Recovered BTL PLVOICE producers

**Observation:** A direct-JAL byte search for `0x001D2DE0` finds four BTL
calls; their callsite bytes give these arguments:

| Live BTL call / Ghidra address / complete-file offset | Request fields |
| --- | --- |
| `0x0076FF04` / `0x0076FEC4` / `0xBC004` | Signed voice number loaded from a selected row; slot from owner `+0x150`. The immediate-versus-deferred path can instead append to owner `+0xD4` through live `0x00770640`. |
| `0x007702C0` / `0x00770280` / `0xBC3C0` | Fighter ID from the object at argument `+0x44`, field `+0x68`; signed voice number from live `0x008CB760 + owner.+0x90*8 + index*2`; slot from the other supplied owner `+0x58`. |
| `0x00770558` / `0x00770518` / `0xBC658` | Cached mono-idle gate, then pop a signed voice number through live `0x007706B0(owner+0xD4)`; slot from owner `+0x150`. |
| `0x00770610` / `0x007705D0` / `0xBC710` | Another cached mono-idle/pop branch in the same bounded body; slot from its owner `+0x150`. |

The first, third and fourth calls use fighter ID zero when owner byte
`+0x189` is zero or `FUN_003083A0(owner.+0x11C)` returns zero. Otherwise
they load fighter ID from that child object's `+0x68`. Instructions at Ghidra
`0x0076FE80..0x0076FEC8`, `0x007704D4..0x0077051C` and
`0x0077058C..0x007705D4` establish those alternatives; the code continues past
`0x003083A0`.

The filename-list pointer for ID zero at `0x003FF900` is null, so the
inspected lookup returns without changing a pending row on these zero-ID
paths. **Consequence of the inspected queue contract:** When a nonnull list
lacks the requested number, it writes member `-1`; consumption still stops
the selected slot before family-3 validation rejects that member. These callsites
therefore do not establish successful playback for every queued request.
No dialogue meaning or complete row-resource inventory is inferred here.
The same JAL encoding has no match in the exposed resident/ETC programs;
that bounded search does not exclude indirect callers.

**Observation:** `FUN_001D9620` explicitly forces family zero at
`0x001D9628`. Match-result selector `FUN_001D2D20` maps values
`0,1,3,4` to family-zero descriptor 10, physical members `2,1,3,4`, slot zero;
value 2 and other values emit nothing. This is separate from player-voice
family 3. [Match outcomes](match_outcomes.md) owns the producers' result-state
conditions.

### Selected deferred voice-value lifetime

**Instruction observation:** The producer at live `0x0076FE50` (Ghidra
`0x0076FE10..0x0076FEEC`) reads a signed voice halfword through row selector
live `0x00770240` (Ghidra `0x00770200`). That selector returns
`0x008CB760 + supplied_root.+0x56C*8`; its complete body at Ghidra
`0x00770200..0x00770218` contains no allocation or row copy. The row scaling
word at Ghidra `0x00770204` is `0x000218C0`, `sll v1,v0,3`; the other
producer uses the same word at Ghidra `0x0077025C` on field `+0x90`. Both
therefore select eight-byte rows, not a 64-byte stride. Cue `-1` suppresses
the first producer.
A nonzero fourth producer argument selects the immediate request already
identified above; zero instead copies the selected voice number into the
target owner's inline queue at `+0xD4` through live `0x00770640`.
The preceding coordinator pointer chain `global iGpffffCC64 -> +8 -> +0x14`
suppresses the producer when its final word is nonzero. Neither this local
row selection nor the deferred append establishes the table's whole semantic
inventory or an unrestricted index range.

The deferred queue is distinct from the resident four pending request rows.
Push bytes Ghidra `0x00770600..0x00770664` and pop bytes
`0x00770670..0x007706D0` establish eight inline value slots, stride eight,
with the copied word at each slot `+4`, head word `+0x40` and tail word
`+0x44`. Empty is head/tail `-1`. Push advances and wraps the tail at 8;
when it collides with the current head, it advances that head before storing.
**Consequence of these instructions:** a ninth unconsumed push overwrites
the oldest value and retains the most recent eight in FIFO order. Pop returns
`-1` when empty, clears both cursors after the last entry, otherwise advances
and wraps the head. The inspected producer copies only the voice number,
not its source row pointer, fighter ID or stream slot.

At both recovered pop/request branches in live `0x00770490` (Ghidra
`0x00770450..0x007705F0`), a selected owner's nonzero object predicate and a
cached mono-idle check precede the pop. After a non-`-1` value is removed,
the consumer resolves fighter ID from that owner's **current** `+0x189`
byte and `+0x11C` child, and reads its **current** slot word `+0x150`.
It then queues the resident filename-number request. A zero-ID path or later
member-validation rejection therefore does not restore the popped value;
the source-row lifetime is irrelevant to the copied number, but the eventual
fighter/slot binding is deferred until consumption. Changes to those fields
over every possible owner lifetime and this inline queue's construction/reset
callers remain unestablished. No audible dialogue identity is inferred.

## SFX selectors and loaded sound banks

**Observation:** Compact battle audio also uses `DATA/SNDDATA.BIN`, distinct
from the four CRI AFS archives. Resident string `0x003FE310` is
`\DATA\SNDDATA.BIN;1`. The shallow `IECS` bank format is owned by
[Disc inventory](../game/files/disc_files.md#data-fonts-graphics-sound-and-archives).

`FUN_001D4BD0` resolves an event to an eight-byte control. Its complete
accepted ranges and table bounds are:

| Audio mode `context.+0x54` | Event range | Table and complete record count |
| ---: | --- | --- |
| Any | `0..0x5C` | `0x003FC9A0..0x003FCC87`; 93 common controls |
| `0` | `0x1000..0x103A` | `0x003FCC90..0x003FCE67`; 59 controls |
| `1` | `0x2000..0x20B0` | `0x003FCE70..0x003FD3F7`; 177 controls |
| `2` | `0x4000..0x4006` | `0x003FD6C0..0x003FD6F7`; 7 controls |
| `3` | `0x3000..0x3056` | `0x003FD400..0x003FD6B7`; 87 controls |

All 423 records in these five accepted tables have nonnegative program bytes
and stream/channel bytes zero. Their program/default/attenuation fields vary.
Common controls have program bytes `0..83`, with repeats; mode-zero controls
have programs `0..49`; mode-one controls `0..56`; mode-three controls `0..120`
with holes. The seven mode-two records all have program zero and defaults
`0x3C..0x42`. These program values do not directly establish sample identities.

`FUN_001D7CF0` first invokes the suppression predicate `FUN_001D3F90`.
Events below `0x1000` return zero to let the common path continue; bank-specific
events invoke `FUN_001D4D70`, `FUN_001D4E00` or `FUN_001D4EE0` and return one.
The mode-specific wrappers require audio context `+0x3C != 0` and a valid
control. `FUN_001D4800` emits through the common packet handle constructed
by `FUN_001DABC0`, adding `B0` three-byte commands before/after `C0`, `F9`
and `FD` forms. Its mode 2 supplies explicit caller bytes; modes 0/1 use
position-derived parameters. Mode 1, or control channel byte 1, obtains a
request token through `FUN_001DB900`; other requests use token zero.

### Character bank loading

**Observation:** `FUN_001D3470(2/3)` establishes battle audio mode zero,
loads the two selected fighter IDs from match context `+0x4C/+0x74`, requests
each through `FUN_001DA7D0(context,3, fighter | side<<16)`, waits cooperatively
for `context.+0x20` to clear, and stores those IDs in the request context's
`+0x0A/+0x0C`. `FUN_001D3450(id)` returns `0x003FD830 + id*12`.
`FUN_001DB060` consumes that selected record; its high-halfword selects side
0 or 1. No ID decrement occurs in this bank lookup, unlike PLVOICE's
character-ID-minus-one descriptor path.

**Complete table observation:** All 94 rows at `0x003FD830..0x003FDC97`
were read. IDs `0,8,20,21,23..33,74,88` have three `-1` words;
the other 77 rows have three populated words, forming 64 distinct triples.
The exact shared triples are `1=39=47`, `2=48`, `3=49`, `4=50`, `14=51`,
`34=52`, `35=53`, `36=54`, `37=55`, `38=56`, `57=73`, `63=75`.
No partially null row occurs. ID 9 has a populated SNDDATA bank despite its
null PLVOICE archive; IDs 39/51 reuse other SNDDATA banks despite null
PLVOICE archives. The two inventories have different ownership contracts.

| Load state `context.+0x58` | EE-side operation |
| ---: | --- |
| `0` | Set state 2. |
| `2` | Allocate record word `+4` bytes in IOP; retain handle at `context.+0x30 + side*4`. Build descriptor at `0x006B23C0` using record words `+0/+4/+8`, current IOP placement `context.+0x44`, and the SNDDATA filename. Request RPC command `0x9400`; set loading byte `+0x1D` and state 3. |
| `3` | Wait until completion word `0x006B2300` equals descriptor word `0x006B23CC`; clear `+0x1D` and enter state 4. |
| `4` | Bind using RPC `0x9052 + side`, descriptor `{IOP allocation, placement}`; call `FUN_001D9370(side+2,0,1)`. Advance placement by record word `+8 + 0x10`; enter state 5. |
| `5` | Call `FUN_001D93F0(2,0)`, reset auxiliary sound state through `FUN_001DB5C0`, then clear transaction byte `+0x20`. |

**Inference (high confidence):** the three record words select a file offset,
bank/header allocation size and sample-data extent. EE code proves their
positions and usage; `SNDBASE.IRX` is needed to decode command `0x9400` and
the actual bank/program/sample resolution. A compact program value therefore
cannot be equated with a physical PLVOICE member.

`FUN_001DB2A0` is the corresponding mode-bank replacement state machine,
using one of four 12-byte descriptors at `0x003FDCA0..0x003FDCCF`. It first
resets sound state, sends command `0x140`, waits until all three cached
family-zero streamed busy flags are clear, allocates and loads the new
descriptor via `0x9400`, binds it through `0x9051`, and finally clears the
transaction. Its current allocation is at context `+0x3C`. The descriptor
values and IOP interpretation do not identify every contained cue.

### Interrupted and identified requests

**Observation:** `FUN_001D4F90(event,token)` resolves the current control,
appends `FD 10 channel default token 00 00`, then releases the token through
`FUN_001DB960`. `FUN_001D5060` updates a positive token with position-derived
`FD 01` and `FD 00` commands, optionally `FD 02`; `FUN_001D5280` updates its
scalar using `CVT_W_S(record.s8[4] * caller_float) & 0x7F`, with conversion
at `0x001D52F4`. These establish
token-directed EE request maintenance and zero-scalar termination encoding,
not a decoded IOP priority or interruption policy.

`FUN_001DB900` scans all eight token-state bytes for the first `0xFF`, stores
and returns the corresponding token `1..8`, or returns `0xFF` when full.
`FUN_001DB960` scans the same eight entries for an equal token and restores
that byte to `0xFF`. Thus token capacity and reuse are proven on EE; neither
automatic audible completion release nor priority stealing is established.

`FUN_001DB520` clears queued update/fade state and requests a stop via `+0x4E`.
When retention byte `+0xBC` is zero it frees positive IOP allocations at
`+0x30/+0x34/+0x3C` and restores placement `+0x44` from `+0x40`.
`FUN_001DB5C0` sets eight token-state bytes `+0x15D..+0x164` to `0xFF`,
clears retention byte `+0xBC`, and resets request context `+0x6C` to `-1`.
It does not clear all four pending stream rows; `FUN_001D2C00` changes only
that context field.

## Transport and stream-poll scheduling

**Observation:** Resident sound ownership is split between request context
pointer `0x0060753C`, CRI stream manager pointer `0x00607558`, and command/RPC
context pointer `0x0060755C`. The three long-lived cooperative tasks are
documented in [Task system](../runtime/task_system.md). Their inspected loop
ordering is:

| Task | EE operations after its cooperative wait |
| --- | --- |
| `SOUND`, `FUN_001D2570` | `FUN_001D27C0` for common, player-one and player-two compact packets, in that order. |
| `SND_RPC`, `FUN_001D28C0` | Fade/update work; clear the sixteen-word auxiliary array at `0x00620060`; service queued parameter commands; cinematic stop check when context `+0xD8` is set; consume all pending stream rows through `FUN_001D9580 -> FUN_001D2C20`; process stop byte `+0x4E` with command `0x140`; advance the bank transaction through `FUN_001DA860`; consume the separate operation slot at context `+0x178`. |
| `SND_RPC2`, bytes `0x001D29F0..0x001D2A6C` | Wait for audio-ready byte `+0x1C`, then poll `FUN_001D9930` only when context `+0x21` is nonzero. |

The loop bodies establish relative order inside each task. Their inter-task
wall-clock cadence and the point at which IOP executes a command remain
unestablished here.

### Bounded compact packet drain

**Observation:** `FUN_001DABC0` constructs the common append handle at
`0x006B21C0`, with payload packet `0x006B2200`. `FUN_001D2A70` constructs
player append handles `0x00620000/0x00620030`, with packets
`0x0061FE00/0x0061FF00`. Each packet begins with capacity `0xF4`, used count
zero, and has trailer word 1 at `+0xFC`. All three are initialized with a
`C0 00` command.

`FUN_001D27C0` checks packet `+4` for nonzero, passes the packet and byte
length `0x100` to `FUN_001DA560`, then clears `+4` without checking the return.
`FUN_001DA560` fills one SIF DMA descriptor at `0x006B2400`, flushes the cache,
calls `sceSifSetDma`, and polls `sceSifDmaStat` for at most `0x2711`
iterations. It returns `-1` for DMA ID zero and records a polling-limit flag;
the producer does not retain packet usage for retry. Consequently a request
can be discarded after an append-capacity failure or unsuccessful packet
submission. EE evidence does not establish whether the IOP acknowledges,
reorders or rejects a submitted command.

### Immediate RPC and bank transactions

**Observation:** `FUN_001DA620` returns `-1` when context load byte `+0x1D`
is nonzero or RPC lock byte `+0x4C` is already one. Otherwise it holds that
lock while using one of two client descriptors at `0x003FE2F0` (stride eight).
The stored service IDs are `0x00012346` and `0x00012347`. Commands without
bit `0x1000` send a 16-byte word buffer at `0x006B2300`; commands with that
bit send 64 caller-supplied bytes. Commands `0xB0`, `0x9200`, `0x9210` and
`0x9400` explicitly poll completion through `FUN_00161E28`. Return payload
length is normally zero, 64 for command bit `0x8000`, and `0xF8` for `0x80C0`.
The command word and descriptor layout are observed; the IOP service remains
undecoded.

`FUN_001DA7D0` is a single bank-transaction slot, not a FIFO: it writes busy
byte `+0x20`, operation byte `+0x59`, argument word `+0x5C` and resets state
byte `+0x58`. `FUN_001DA860` consumes operations 0..4. The battle setup waits
for each transaction before requesting the next side, preventing that caller
from replacing its own unfinished transaction.

### Cached stream activity and replacement

**Observation:** `FUN_001D9930` polls three stereo stream handles followed by
three mono voice handles through `FUN_001D70A0`. The stereo results populate
manager bytes `+0x6F4..+0x6F6`; mono results populate `+0x6F7..+0x6F9`.
`FUN_001D99B0(0/1,slot)` reads those cached bytes. A query does not itself
advance playback or refresh the cache.

For mono handles `FUN_001D7270` returns zero while CRI state is below 2,
otherwise `(FUN_00135E08(handle)+1)&1`. Stereo `FUN_001D71C0` recognizes
states 3,4,6, calls `FUN_00135D18`, and uses the same completion predicate.
These are activity flags, not sample cursors. The underlying CRI end state is
owned by [Audio and video replacement](../game/files/audio_video_replacement.md#resident-menu-music-selection).

`FUN_001D9900(slot) -> FUN_001D6A30` sets the mono slot's CRI level to `-960`
and calls `FUN_00134650` to stop it. `FUN_001D6F60` then starts an archive
member through `FUN_001371F0` on handle `manager.+0x2C + slot*0x10` and
sets its level to zero through `FUN_001D6FD0`. The descriptor `+4` value
supplied as a fifth caller argument is not consumed by this start helper's
inspected instructions. A pending request therefore replaces that slot's
previous stream before knowing whether archive selection will succeed.

## Fighter action cue production

**Observation:** Resident `FUN_0024DA50` calls effect presentation
`FUN_002092D0`, then sound/voice scheduler `FUN_00204610`, under fighter node
flag `+0 & 2`. That sound call is outside the positive `+0x20C` pause branch.
The complete major-state switch in `FUN_00204610`, `0x00204610..0x00205404`,
contains cue branches for majors 0,1,2,5,6,8; other majors emit nothing from
this scheduler. It reads major `+0x18E`, minor `+0x190`, primary timeline
`+0x1B8`, action record `+0xA4C` and the response/attack record returned by
`FUN_00222B20`. [Combat action execution](combat_action_execution.md) owns
action and phase dispatch; [Animation runtime](../runtime/animation_runtime.md)
and [Timer primitives](../runtime/timer_primitives.md) own cursor updates.

Most branches use `FUN_00211A20(primary,0)`. The inspected instructions
`0x00211A20..0x00211AB8` prove that this zero event succeeds only when timeline
flag `+2 & 2` is set, integer `+0x0C` equals zero, and float `+0x1C` equals
zero. It is an action-timeline entry event, not an arbitrary animation sample.
Major 8 instead supplies the action record's signed halfword `+0x44` as
event time. Its nonzero crossing behavior is owned by
[Timer primitives](../runtime/timer_primitives.md#event-and-interval-predicates).

| Major | Complete local audio branches |
| ---: | --- |
| `0` | Minors 6/7 at entry select a mapped SFX from response `+0x4A`, or `+0x46` when response flag `+0x14 & 0x01000000` is set; fighter ID 4 folds six groups of three selectors into `0x60..0x62`. Minor 8 requires `+0x966 == 2`, `+0x968 == 0` and `+0x964 & 0xF == 1`, then requests voice `0x1A + random(2)`. Minors 9/10 at entry request SFX at `0x0040700A` and voice event `0x1D`. Minors `0x0B..0x0D` at entry request SFX at `0x00407008`. |
| `1` | Minors `0x0E/0x12` request surface-dependent SFX when `+0x63 & 0x10` is clear, timeline `+0x1BA & 1` is set, and integer `+0x1C4 % period == 0`. |
| `2` | Minors `0x18/0x1A/0x1C` at entry select mapped SFX index `0x10` and voice event `0x13`; minors `0x19/0x1B/0x1D` select mapped SFX index `0x11` and event `0x14`. |
| `5` | At entry, `FUN_00205410` produces response SFX and voice comes from response `+0x4E`, with the random defaults below. Voice additionally requires `FUN_00222BD0(fighter) < 2` and `fighter.+0x61 & 0x08`. |
| `6` | At entry, minors `0x5E/0x5F` request voice `0x13` and mapped SFX `0x10`; `0x60` requests voice `0x14` and mapped SFX `0x11`; `0x61` emits SFX `0x00406FF8` except when the masked surface value is `0xE0E000/0xE0A000`. |
| `8` | At action `+0x44` event, when action flags `+0x10 & 2` are clear, action `+0x40` supplies mapped SFX and `+0x42` supplies voice/pseudo-event. With that flag set, the branch instead emits SFX `0x00407006` when fighter `+0x9BA == 2` and `+0x9C2 == 0`. |

**Instruction observation:** Minor 9 really falls into minor 10's code:
`0x00204820..0x002048BC` contains two zero-event checks and two voice-`0x1D`
calls with no intervening branch out. When both checks succeed, two voice
requests are emitted; the second SFX is conditional on `fighter.+0xA48 == 0`.

At minor 8's random call, `a0 == 2` survives the comparison at
`0x002047CC..0x002047F8`. Resident
`FUN_00180210`, instructions `0x00180218..0x00180248`, takes the magnitude
of its argument and uses unsigned remainder with divisor `argument + 1`.
For the positive bounds used here, `random(n)` therefore returns `0..n`,
inclusive. This establishes the voice group `0x1A..0x1C` and the deliberate
no-request outcome 3 in the three-choice voice groups above.

### Periodic and response selectors

**Observation:** `FUN_002044F0` returns periodic divisors by fighter ID:
`7` for `0x12/0x22/0x51`; `8` for `0x15/0x18/0x3C/0x53`; `20` for `0x4C`;
`6` for `0x0B/0x11`; `11` for `4/0x0E`; `12` for `0x32`; `5` otherwise.
The modulo input is integer primary cursor `+0x1C4`; these divisors are cursor
units, not independent sound-worker countdowns.

The complete 102-halfword SFX map at `0x00406FD0..0x0040709B` translates
action/response SFX selectors before `FUN_001D87C0` dispatch. `FUN_00205410`
accepts response `+0x46` only in `0..0x65`, suppresses it for minors
`0x42..0x46/0x5A`, adds mapped SFX `0x4D/0x4E` for minors `0x4F/0x50`, and
uses explicit cues `0x3C/0x1005` for minor `0x3E`. Every common mapped event
fits `0..0x5C`; every bank-specific mapped event fits the mode-zero
`0x1000..0x103A` table. Their audible identity is not established by the map.
The common post-map branch additionally requests SFX `0x100F` when the
selected map index is `0x0C` and fighter ID is `0x11`.

For major 5, response voice `+0x4E == -2` suppresses voice, nonnegative values
supply explicit events, and other negative values select a minor-dependent
random group using `FUN_00180210(3)`; returned 3 suppresses the request.
Minors `0x27..0x2A` use `9..11`; `0x2B..0x35`, `0x4A..0x50` and
`0x5B/0x5C` use `12..14`; `0x36..0x39`, `0x3C/0x3D/0x3F..0x41` and
`0x51..0x59` use `15..17`; minor `0x3E` uses `17..19`. Within this negative
fallback path, event `0x12` replaces the result when fighter `+0x62 & 1`
is clear, `FUN_00230C70(fighter,-1) != 1`, the response exists, its flags
`+0x10 & 0x000C0000` are nonzero, and its byte `+0x2C` is one of
`0x0F,0x10,0x11,0x12,0x14,0x15,0x1D,0x1E,0x1F,0x20`.

### Other recovered fighter cue producers

**Observation:** Resident direct xrefs recover 35 caller functions for
`FUN_002040D0`, 53 for `FUN_00204220` and five for `FUN_002043E0`.
Their local cue blocks were examined, including the central scheduler above.
These are recovered direct-caller sets, not a whole-program completeness claim.
They establish several additional request contracts:

| Producer | Established local voice gate or source |
| --- | --- |
| `FUN_00224D10` | Optional event `0x18` when its request argument is nonzero, fighter `+0x62 & 1` is clear and `+0x61 & 0x08` is set. HP-gain ownership is in [Damage](damage.md#character-durability-and-effective-base-hp). |
| `FUN_002254A0` | Optional event `0x19` under the same fighter bits, additionally rejected when `FUN_00307480()` is nonzero. [Chakra and guard](chakra_and_guard.md) owns its resource contract. `FUN_002369D0` calls this path and separately requests event `0x16` or resource-gain event `0x18`, according to its source-record predicates. |
| `FUN_00227320`, `FUN_00227EE0` | Primary `+0x1B8` fractional event `0` through `FUN_002118A0` requests `0x1E` and `0x1F`, respectively. |
| `FUN_0020D910`, `FUN_0020E280` | In their admitted transformation branches, a 94-row four-byte table at `0x005C1B50..0x005C1CC7` supplies the signed event halfword. Every event is `0x1F` or disabled `-1`; companion halfword semantics belong to [Awakening](awakening.md). |
| `FUN_002466D0` | Copies 94 words from `0x00407E70..0x00407FE7`, indexes by fighter ID and supplies the result as an event. Every retail word is one of `4,5,7,8`, so this table selects explicit events despite the helper's pseudo-event branches. |
| `FUN_0020A210` | Primary enabled flag `+0x1BA & 1`, integer cursor zero and nonzero `FUN_00247E90()` result request event `0x1F`. Subsequent SFX use cursor modulo `8` or scalar-selected divisors `12/11/10/8`; these remain action-cursor units. |

Character-specific blocks also query the **secondary** timeline `+0x1DC`.
For example, `FUN_00262350` requests event `0x14` at secondary events
`6/3/7` in its action-selector branches `0x22/0x19/0x17`, each with phase
`+0x192 == 0`. `FUN_002607D0` instead requests `0x14` at primary event 6
for selector `0x1A/0x19`, and `0x13` at primary event 8 for selector `0x16`.
Those branches use `FUN_002118A0`, while the central scheduler uses
`FUN_00211A20`; their exact-boundary enabling differs as documented in
[Timer primitives](../runtime/timer_primitives.md#event-and-interval-predicates).
One shared primary cursor is therefore insufficient to explain all voice cues.

The `+0x61` mask above is corroborated by `dsll32 ...,0x1C` followed by
`dsrl32 ...,0x1F` at `0x00204F58..0x00204F60`,
`0x00224D38..0x00224D40` and `0x002254F0..0x002254F8`: these isolate
byte bit 3, mask `0x08`.

The five direct-control callers use these control indices, bypassing the event
lists and event cooldown. Object dispatch still applies its own suppression
predicate. These controls are neither event IDs nor physical voice members:

| Caller | Controls in its inspected cue blocks |
| --- | --- |
| `FUN_0028FC20` | `0x50..0x55`, at branch-specific secondary events |
| `FUN_00272770` | `0x56`, with a random-indexed caller parameter |
| `FUN_00279EB0` | `0x32,0x33,0x34/0x35,0x36,0x3C,0x3D/0x3E,0x40`; slash pairs use `random(1)` |
| `FUN_00292990` | `0x46` |
| `FUN_00279350` | `0x33,0x37,0x40` |

The 53 pseudo-event callers include literal events, random groups and
record-authored values; most inspected cue blocks query primary or secondary
`FUN_002118A0`, with additional phase, action-selector or random-bit gates.
Examples include `FUN_002D9AA0` obtaining its event from `FUN_00204030`,
and `FUN_002EE660` using a data-authored primary event time at `0x0056F970`.
Their individual character-action identities and all associated resource
records are not inferred from these local audio blocks.

### Surface-dependent SFX

**Observation:** `FUN_001D53F0` masks the surface value with `0xF0F0F0` and
selects a common SFX event. The surface value's source belongs to
[Stage surface attributes](stage_surface_attributes.md). `FUN_001D5560` uses it in the periodic branch;
`FUN_001D5690` is a separate related selector. Their complete differing maps
are retained without assuming physical material names:

| Masked value | `FUN_001D53F0` | `FUN_001D5690` |
| --- | ---: | ---: |
| `0` | Suppressed | Suppressed |
| `0x00D0D0`, `0xF0F0F0` | Suppressed | `0x53` |
| `0x202020` | `0x42` | `0x42` |
| `0x80D0F0` | `0` | `0` |
| `0x0010C0`, `0x003060` | `1` | `1` |
| `0x005000` | `1` | `0x56` |
| `0xE0E090` | `5` | `0x53` |
| `0xE0A000`, `0xE0E000` | `5` | `5` |
| `0x00D000` | `2` | `2` |
| `0x0060C0` | `6` | `6` |
| `0x90B0C0` | `4` | `4` |
| `0xF0D0D0`, `0x606060`, `0xE000E0` | `3` | `3` |
| `0x8080F0` | `3` | `0x53` |
| Any other nonzero value | `0x53` | `0x53` |

The periodic route overrides the selected control's default byte to `0x3A`
for IDs `4,0x0E,0x15,0x51`, `0x3B` for `0x18`, `0x39` for `0x32`,
`0x3C` otherwise. IDs `0x15/0x53` additionally emit SFX `0x43`.

## Cinematic and guide voice schedulers

### Authored cinematic frame rows

**Observation:** Resident `FUN_0035B740` consumes a counted eight-byte row
array from its owner `+0x10`, with next-row index `+0x14`. At
`0x0035B7F0..0x0035B7F8` it compares the row's signed halfword `+0` for exact
equality with scene object's integer `+0x90`. Only on equality does it read
signed cue byte `+3`, skip `-1`, remap cue `0x0C..0x14` to `0xAC..0xB4`
when `FUN_001F7BC0(owner.+0x38)` is nonzero, call `FUN_001D5820`, and
increment the index once. There is no catch-up loop in this row consumer.
**Inference (high confidence):** skipping the authored integer value can
leave that row unconsumed; the actual caller's cursor progression is owned
by [Scene playback callers and owners](../runtime/scene_playback_owners.md).

`FUN_001D5820` obtains scene side and fighter IDs through `FUN_0035DAD0`,
checks them against the audio request context's stored IDs, and emits `C0`
followed by `90 channel default attenuation` on the corresponding player
packet. The second append occurs only when the first succeeds. This cinematic
route lacks the ordinary fighter-event state/cooldown gate. Its separate
match-category-6 route is described below; the complete cue-row resource
inventory remains unresolved.

The streamed ultimate intro's completion latch and authored countdowns are
already owned by [Ultimate jutsu](ultimate_jutsu.md#presentation-state-machine);
they query cached mono activity through `FUN_001D99B0(1,0)`. The shared audio
meaning of that query is established above.

#### Selected row binding and resident lifetime

**Observation:** `FUN_0035CF00` first permits the variant resolver
`FUN_0035CA80` to replace the requested scene selector when it returns a value
other than `-1`. The creator stores the resulting selector at the owner
halfwords `+0x3A/+0x3C`, then binds owner `+0x10` to
`0x005D3D20 + selector*8` and clears the next-row index `+0x14`.
Instructions `0x0035D210..0x0035D270` prove that binding and the special
initial index 999 when the bound array's first signed frame halfword is 1.
The inspected creator does not copy the authored rows into its allocated
owner: the descriptor and row storage remain resident ELF data. The consumer
at `0x0035B770..0x0035B79C` dereferences that descriptor on each invocation.
Other resource payload copies in scene initialization are separate from this
audio row pointer.

Three selected descriptor/row bindings were read completely; selector numbers
are the post-resolution table indices, not asserted character or jutsu names:

| Selector / descriptor address | Count / row pointer | Ordered `(signed frame, signed cue byte)` values |
| --- | --- | --- |
| `1` / `0x005D3D28` | `3` / `0x005C9500` | `(91,0x0D), (121,0x0E), (195,0x12)` |
| `2` / `0x005D3D30` | `4` / `0x005C9520` | `(132,0x0F), (165,0x0D), (222,0x10), (329,0x12)` |
| `3` / `0x005D3D38` | `1` / `0x005C9540` | `(220,0x12)` |

The binder registers `FUN_0035B740` as scene callback `+0x8C` at
`0x0035D0C8..0x0035D0D0`; a recovered direct creator call is BTL Ghidra
`0x0076A0CC` (live `0x0076A10C`). Scene selection, worker execution and cursor
lifetimes belong to [Ultimate jutsu](ultimate_jutsu.md) and
[Scene playback callers and owners](../runtime/scene_playback_owners.md).
This evidence establishes selected audio bindings, not all creator reachability
or all resource variants. `FUN_0035A070`'s inspected initialization retains
the bound audio pointer while initializing other scene resources.

#### Match-category-6 request admission

**Instruction observation:** `0x001D5834..0x001D585C` routes directly to
`FUN_001D5A40` when the match context exists and word `+0x0C == 6`, before
the ordinary control-index range check and stored-fighter-ID comparison.
`FUN_001D5A40`, `0x001D5A4C..0x001D5A98`, scans thirteen exact four-byte
keys at `0x003FD790`: `0x0C..0x14`, `0`, `3`, `4`, `0x16`. An unmatched
request returns without emitting. Consequently the consumer's remapped
`0xAC..0xB4` cues are not admitted by this category's lookup.

For a matching key, it copies eight bytes from `0x003FD6C0 + match_index*8`
to a stack control. `FUN_0035DAD0` must then find the published scene owner;
scene side `+0x28 == 0` selects fighter halfword `+0x2C`, other values select
`+0x2A`. Fighter `0x27` suppresses the request. The transformed-ID predicate
`FUN_001F7BC0` can select `FUN_001F7E70`'s base-ID mapping, after which the
temporary control's program byte becomes `selected_fighter_id - 1`.
It calls `FUN_001D4800(stack_control,0,0,-1,-1,-1)` at `0x001D5BBC`.
Thus this path uses the common compact packet with no positional input and
the copied default byte; it does not request a PLVOICE AFS member.
`FUN_001D4800` still rejects a negative signed program byte. Specifically,
ID `0x4A` passes `FUN_001F7BC0` but its mapping returns `-1`, making the
temporary byte `0xFE` and suppressing this request. General form identities
belong to [Character assets](../game/character_assets.md).

**Table boundary observation:** The seven mode-two controls already counted
above occupy only `0x003FD6C0..0x003FD6F7`. The lookup's indices `7..12`
for keys `0x13,0x14,0,3,4,0x16` instead copy the adjacent bytes
`0x003FD6F8..0x003FD727`, which contain `cdrom0:\`, `DATA\`, `snddata.bin`,
`SND_RPC2` and padding. This caller has no seven-record bound check. Those six
matches must not be presented as six additional authored controls or silently
assigned the valid table's defaults. The exact copied bytes and the common
packet helper are established; successful or audible requests for those
matches are not.

This category-6 caller bypasses the ordinary object suppression predicate and
the mode wrapper's `context.+0x3C != 0` gate. It does not itself wait for a
mode-bank transaction or check the loaded bank's availability. The inspected
common helper still applies signed program suppression and bounded packet
append contracts. Whether any admitted request has a valid IOP program/sample
depends on the loaded bank and undecoded `SNDBASE.IRX`; this EE construction
does not establish that resource identity or lifetime.

### Guide Ninja Sound

**Observation:** BTL live `0x00728F80` (Ghidra `0x00728F40`, complete-file
`0x75080`) is the idle guide-voice scheduler; it continues past its call to
`FUN_00180210` through selection and request (`0x00728F40..0x00729098`).
It proceeds only when native setting key `0x0A` is nonzero and cached mono
stream slot 2 is idle. Under those gates, a nonzero context halfword `+0x0A`
decrements by one. At zero it indexes a 13-byte row at live `0x008C4540`
(Ghidra `0x008C4500`) using signed selector byte `+5`.

It chooses one of two three-member groups at row `+7..+9` or `+10..+12`,
using `FUN_00180210(2)`, and retries at most ten selections to avoid repeating
context halfword `+8`. It requests `FUN_001D9620(4, member, 2)`, hence SOUND
descriptor 4 on mono slot 2, not PLVOICE. That descriptor at `0x003FDCF0`
has archive handle 4 and physical member count 99. It stores member at
context `+6/+8`, clears `+0x0C`, and seeds `+0x0A` with
`150 + FUN_00180210(90)`, hence `150..240` eligible-call units. The idle
countdown pauses while either gate is closed.

The constructor at BTL live `0x00728DD0..0x00728E60` (Ghidra
`0x00728D90..0x00728E20`) stores the fighter ID at context `+0`, clears
state `+4`, and chooses selector `+5` from a 94-byte fighter map at live
`0x008C44E0` (Ghidra `0x008C44A0`). All 94 entries and all fifteen 13-byte
rows at live `0x008C4540..0x008C4602` were read: selectors span `0..14`,
and every member candidate in row `+1..+12` is `3..82`, below descriptor
4's member count 99. The constructor's signed `fighter < 94` check chooses
fallback selector 11 otherwise; it does not prove negative IDs are safe.
It seeds the initial countdown with literal 90 through live `0x00728F30`
(Ghidra `0x00728EF0`). That helper stores a nonzero caller value directly,
otherwise uses `150 + random(90)`. It does not clear the prior-member field
`+8`; an initial value for that field is not established in this constructor.

The owner body at BTL live `0x00729130..0x007292E4` (Ghidra
`0x007290F0..0x007292A4`) dispatches state byte `+4`. State zero calls the
idle scheduler; state one becomes state two; state two chooses from row
`+1..+6`, retries until the member differs from `+8`, plays the same descriptor/slot, then
enters state three. State three decrements the countdown and returns to zero
only when it is zero and cached slot 2 is idle, reseeding with the same
`150 + random(90)`. State four emits nothing in this body. The state-three
decrement has no key-`0x0A` gate in the inspected owner; the setting gate is
inside the idle scheduler and trigger routine, not a universal stop operation.
The state-two repeat loop has no ten-attempt bound; that bound belongs only
to the idle scheduler. All fifteen six-member candidate groups contain at
least two different values, so no stored previous member makes every candidate
equal, although the loop has no deterministic attempt limit.

BTL live `0x00728EA0` (Ghidra `0x00728E60`) is the event trigger: setting key
`0x0A` gates a query through resident `0x0020BAA0`. **Instruction
observation:** `0x0020BAA0..0x0020BAA8` is `daddu v0,zero,zero; jr ra; nop`,
so this retail query always returns zero. With state `+4` zero, the trigger
sets state two and calls live `0x00728F30` (Ghidra `0x00728EF0`) with 5.
The JAL word `0x0C1CA3CC` at Ghidra `0x00728EC8` proves the countdown-setter
target, which stores 5 at `+0x0A`. A nonzero query would set state four, but
this constant-zero callee cannot select that branch. The setting's menu
contract belongs to [Practice mode](practice_mode.md).

#### Guide allocation, publication and dispatch

**Observation:** Resident `FUN_001EC3B0` admits this owner only within its
nonnull match-context / absent coordinator-child branch and with its argument
equal to 2. When global `0x00607658` is null, instructions
`0x001EC4F0..0x001EC514` allocate `0xA8` bytes through `FUN_00117150`, call
BTL live `0x007278D0` (Ghidra `0x00727890`) when allocation is nonnull, then
publish the result at `0x00607658`. A nonnull published owner is initialized
through live `0x00728620` (Ghidra `0x007285E0`). This is a retained child of the
command-display owner, not a separately registered guide task.

The parent initializer's omitted tail, Ghidra `0x00728978..0x00728A20`, stores
the low byte of match word `+0x18` at parent `+2`. Zero selects fighter object
`+0xDE4` and ID word `+0x4C`; a nonzero stored byte selects object `+0xDE8`
and ID word `+0x74`. The ID is stored as parent byte `+1`. It allocates the
command tracking object at parent `+0xA0`, then requests a separate
`0x0E`-byte guide object. On a nonnull allocation it calls live `0x00728D90`
(Ghidra `0x00728D50`), publishes
the pointer at parent `+0xA4`, and calls the guide constructor live
`0x00728DD0` with the unsigned parent byte `+1`.

**Initialization observation:** The allocation initializer at Ghidra
`0x00728D50..0x00728D64` clears only guide bytes `+3/+4/+5` and halfword
`+0x0A`. The subsequent constructor writes fighter ID `+0`, selector `+5`,
state `+4`, countdown `+0x0A`, and byte `+2`. Its query wrapper live
`0x00728E70` (Ghidra `0x00728E30`) calls the same constant-zero resident stub,
so byte `+2` becomes zero. Neither initializer writes halfword `+8`.
`FUN_00117150 -> FUN_001180D0` and its two placement helpers
`FUN_00118610/FUN_001186A0` construct allocation headers without clearing the
returned payload; the general arena contract belongs to
[Allocator and capacity](../runtime/ee_memory_map/allocator_and_capacity.md#allocator-model).
Thus this recovered creation path leaves the first repeat comparison's
prior-member value unspecified; zero is not an established initial value.
The first selected idle/event request writes `+8`. The parent's unsigned
byte load bounds this constructor caller to `0..255`; it does not establish
the constructor's safety for unrestricted signed callers.

**Dispatch observation:** Resident `FUN_001EDB70` requires its preceding
`FUN_001EF8F0` result to be zero, coordinator argument word `+0x14 == 2`,
and global `0x00607658 != 0`. Nonzero `FUN_001F4790(match,1)` or a nonzero
coordinator-state getter `FUN_00250820()` selects live `0x00728CD0`
(Ghidra `0x00728C90`); this wrapper calls guide stop helper live `0x007290E0`
(Ghidra `0x007290A0`). When both reads of the coordinator getter are zero and
the match predicate is zero, it selects command update live `0x00728B00`
(Ghidra `0x00728AC0`). Setting key 1 controls the additional draw call; it does
not itself select whether this update or stop branch runs.
The predicate compares match word `+0x14` with 1; literal argument 1 survives
from `0x001EDBB0` to the call at `0x001EDC1C`.

Command update requires the match context and parent `+0xA0` to be nonnull,
then calls `FUN_0020BBB0` with two output words initially `-1/0`. Only its
nonzero low-byte result admits the guide update at Ghidra `0x00728B50..54`,
before the command-display maintenance and key-1 clear/hide handling.
`FUN_0020BBB0` chooses the current side's fighter for match `+0x18 == 0/1`
and returns zero when that selected object is null. Its command-record
tracking semantics belong to [Practice mode](practice_mode.md). A successful
call can output command index `-1` yet still admit guide update; a new command
is not required for every idle countdown decrement.

The one recovered direct event-trigger caller is command-display helper live
`0x00728080` (Ghidra `0x00728040`). At Ghidra `0x00728250..0x007282CC`, it requires
the display countdown `+0x88 == 0`, tracking object `+0xA0 != 0`, nonnegative
command index `+4`, and nonnull command record `+8`. It marks the command's
parent `+0x10` entry, starts the display countdown from `+0x8A`, and calls
the guide trigger on parent `+0xA4`. The guide setting and state-zero gates
then apply. A trigger can therefore arm state two after that invocation's
guide update has already run; no inter-call time interval is inferred.

#### Guide interruption and local teardown

**Observation:** Guide state two calls `FUN_001D9620(4,member,2)` directly,
without the idle scheduler's cached-slot-idle check. It then stores the member
at `+6/+8`, clears `+0x0C`, and enters state three without inspecting the
request return. Its event countdown remains the trigger's 5. State three
waits for both countdown zero and cached mono slot 2 idle before reseeding.
Unlike the pending-row consumer, this direct request does not first invoke
`FUN_001D9900`; it reaches `FUN_001D6F60 -> FUN_001371F0` on the existing
slot handle. The EE path establishes a same-handle member-start request;
whether that call replaces, rejects or audibly overlaps a still-active member
is not established by these EE request bytes.

Guide stop helper live `0x007290E0`, Ghidra `0x007290A0..0x007290E8`, calls
`FUN_00250820`; getter results 1, 2 or 6 return without stopping, while other
values call `FUN_001D9B60(2) -> FUN_001D6A30(manager,2)`, the mono slot-2
level/stop operation described above. The literal slot 2 survives from Ghidra
`0x007290BC` to the call at `0x007290D4`. This helper does not write guide
state or countdown in this body.

**Request admission observation:** Descriptor 4 bytes at `0x003FDCF0` are
`04 00 01 00 01 00 63 00`; its archive handle and member bound admit all
established guide candidates. `FUN_001D9620 -> FUN_001D97D0` can reject
invalid descriptor/member/slot arguments or return zero under global
`iGpffffCBA4`. After those gates it calls the stream start helper and returns
one without checking whether CRI accepted the archive member. Neither the
guide callers nor that descriptor admission checks the command context's RPC
lock, bank transaction or audio-ready byte. Static member bounds therefore
establish request eligibility, not available/playing audio, priority or audible
completion. Archive registration and startup availability are owned by
[Startup](../game/startup.md#audio-initialization-bottleneck) and
[Audio and video replacement](../game/files/audio_video_replacement.md#actual-codec-and-archive-map).

Parent teardown live `0x007279A0` (Ghidra `0x00727960`) continues past each
free; Ghidra `0x00727960..0x00727AB8` shows that, after
other parent-owned resources, nonnull parent `+0xA4` is passed to guide
cleanup live `0x00728DB0` (Ghidra `0x00728D70`), then `FUN_00117000`, and the
pointer is cleared. That guide cleanup clears only bytes `+3/+4/+5` and
countdown `+0x0A`; it emits no stream stop. The parent then reruns its base
initializer live `0x007278D0`. This local freeing path establishes guide
memory lifetime, not a guarantee that an accepted audio stream has ended.

Resident `FUN_001EC540`, instructions `0x001EC570..0x001EC59C`, calls that
parent teardown, frees the parent itself and clears `0x00607658`.
The same local sequence is recovered in `FUN_001EDD10`, `FUN_001EE1C0`,
`FUN_001EE500` and `FUN_001F2020`; their enclosing battle transitions belong
to [Battle lifecycle](battle_lifecycle.md). These callers establish retirement
of the published owner without broadening the guide into a separate task.

**Bounded limits:** No nonzero writer of state one or four has been established
outside the inspected owner; the trigger's state-four alternative is dormant
under its constant-zero query. The actual first allocation payload at `+8`,
all possible indirect callers, and the interval between admitted command-owner
updates remain unresolved.

Direct-JAL searches for the guide constructor, event trigger and update body
found the single BTL callsite for each identified above and no matches in the
exposed resident or ETC programs. These byte searches do not establish
unrestricted indirect reachability or cover the excluded overlay.
