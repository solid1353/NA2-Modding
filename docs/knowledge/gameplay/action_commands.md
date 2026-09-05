# Battle action-command and input interpretation

This document records the clean NA2 battle input path from the resident pad
abstraction through `BTL.BIN` history matching and back into the resident
action-table dispatcher. It deliberately describes the game's native masks,
not emulator key, controller, or profile bindings.

## Research coverage

- **Assigned scope:** this lane covered reusable clean-battle command and input
interpretation: native pad representation, `ccCommand` history and static
records, matching/order/leniency semantics, logical-input translation, the
resident bridge into action selection, and representative ordinary and jutsu
dispatch callers. It owned only this document.

- **Exploration depth:** coverage was bounded, deep static analysis,
not an exhaustive audit of `BTL.BIN` or the resident executable. The primary
assets were the clean `PRG/BTL.BIN` and `SLPS_258.37` identified below, their
preserved Ghidra C/text exports, and raw EE objdump disassembly used to repair
missed function starts and audit the overlay-header address bias. In the
overlay, analysis followed the contiguous `ccCommand` implementation from live
`0x006EF390` through `0x006F1040`, its controller/list plumbing around live
`0x006D67A0..0x006D67E0` and `0x00709240..0x00709F40`, both static command
tables and their descriptor array at live `0x00898180..0x008981CF`, and both
direction jump tables at live `0x008C2FC0..0x008C301F`. In the resident image,
the traced boundary included pad production (`FUN_00113710`), analog/digital
direction conversion (`FUN_00114d90`/`FUN_00114e60`), battle construction and
virtual scheduling (`FUN_001ef330`, `FUN_001ef8f0`, `FUN_001f0290`, and
`FUN_001f03e0`), configured bindings (`FUN_001f3dc0`/`FUN_001f3f10`), the
input bridge and direct matcher consumers, and the action-selection chain from
`FUN_00217320`/`FUN_00229130` through `FUN_00239530`, `FUN_0023a390`,
`FUN_0023a9a0`, and the relevant `FUN_0024xxxx` synthesis/update callers.
Direct clean callers of the generic matcher family and all 13 direct
clean-overlay direction-predicate calls were enumerated. The two static
`ccCommand` tables and descriptor bytes were decoded completely; surrounding
unrelated battle systems were sampled only as needed to close callers and
callees.

- **Confirmed coverage:** the documented results include the
live/export/file address convention; native pad masks and configurable binding
layout; `ccCommand`/`ccCommandCtrl` identity, object fields, construction,
virtual update route, circular history records, normalization, and edge
recomputation; exact boolean and count matcher ABIs, scan order, wrapping,
comparison modes, diagonal repair, and caller hazards; direction-selector and
logical-mask mappings; both two-step cardinal command tables and their ordered
matching semantics; resident post-translation synthesis; action-signature
construction and equivalence rewrites; action-record layout and ordinary,
fixed-chain, fixed-slot, and jutsu-class selection partitions; validation,
fallback, and final dispatch; and representative default-binding Circle and
Triangle-to-jutsu paths.

- **Unresolved or untested:** static evidence did not establish
the user-facing names of object-relative direction selectors, a producer or
active use for dormant `ccCommand +0x8C/+0x90`, the semantic reason for the
history-capacity divisor, or character-specific action-record contents and
visible move names.
- **Deliberate exclusions and overlap:** detailed character/jutsu data belongs to the separately
scoped table/jutsu lanes; this document overlaps only at the generic selection
and dispatch boundary. Adventure, substitution-specific behavior, damage
formulas/scaling, timing or 60-FPS work, widescreen, localization, and PCSX2
infrastructure were deliberately excluded. Emulator/host bindings were not
used to infer native game masks.
- **Evidence limitations:** findings were cross-checked statically between clean
binary bytes, raw disassembly, exported decompilation, encoded calls/pointers,
and table data. No runtime instrumentation, controlled input playback, live
history capture, or per-character action-table dump was performed in this
lane. Consequently, structural and bit-level claims are evidence-backed, but
runtime cadence, player-facing move labels, and data-dependent outcomes remain
unvalidated unless explicitly stated otherwise below.

## Evidence identity and address convention

The clean resident and BTL inputs are identified in
[Standard game file identities](../game/files/file_identities.md).

Absolute pointers and JAL targets encoded in the overlay already contain live
addresses. Ghidra can therefore attach an intra-overlay call to a label 0x40
past the callee's exported byte start. The tables below state both conventions.
Resident ELF addresses are unaffected.

## Native pad domain and battle bindings

The resident controller layer forms a 16-bit, active-high game mask from the
standard active-low PS2 pad packet. The native domain is:

| Mask | Native control | Mask | Native control |
| ---: | --- | ---: | --- |
| `0x0001` | L2 | `0x0100` | Select |
| `0x0002` | R2 | `0x0200` | L3 |
| `0x0004` | L1 | `0x0400` | R3 |
| `0x0008` | R1 | `0x0800` | Start |
| `0x0010` | Triangle | `0x1000` | Up |
| `0x0020` | Circle | `0x2000` | Right |
| `0x0040` | Cross | `0x4000` | Down |
| `0x0080` | Square | `0x8000` | Left |

These names describe game-native pad bits only. PCSX2 or host-device bindings
are a separate layer and are not evidence for this mapping.

Resident `FUN_00113710` is the concrete producer. Once the pad is in its
readable state, it concatenates the two packet button bytes and XORs them with
`0xFFFF`. The fields of that resident pad object consumed by the battle input
path are:

| Offset | Size | Native-pad value |
| ---: | ---: | --- |
| `+0x49` | 1 | left-stick magnitude |
| `+0x4A` | 1 | right-stick magnitude |
| `+0x4C` | 4 | left-stick angle in radians |
| `+0x50` | 4 | right-stick angle in radians |
| `+0x64` | 4 | held/current mask |
| `+0x68` | 4 | newly pressed mask, `~previous & current` |
| `+0x6C` | 4 | newly released mask, `previous & ~current` |
| `+0x70` | 4 | resident repeat stream after a 15-update hold delay |
| `+0x74` | 4 | previous held mask |

The battle overlay copies every field in this table except `+0x70` into its
history; it later recomputes pressed and released edges after direction
normalization.

The clean overlay's default eight-entry battle binding array is at live
`0x00898150`, file `0x1E4250` (exported byte location `0x00898110`):

```text
0010 0020 0040 0080 0004 0008 0001 0002
```

Thus indices 0 through 7 default to Triangle, Circle, Cross, Square, L1, R1,
L2, and R2. The input object initially copies this table. Its binding-refresh
method later calls resident `FUN_001f3f10` with controller side 1 or 2 and
copies the returned eight halfwords, so command interpretation uses the
game's configured binding array rather than assuming those defaults forever.
Resident `FUN_001f3dc0` owns updates to that configured array and calls the
overlay's eight-halfword copy helper for an existing battle input object.
The resident defaults at `0x005C06A0` are byte-for-byte identical to the
overlay table. `FUN_001f3f10(1)` and `(2)` return the mutable side arrays at
`0x006B2B20` and `0x006B2B30`, respectively; a nonpositive side returns null.

Adjacent static identifiers are `controller1` at live `0x00898160`, file
`0x1E4260`, and `controller2` at live `0x00898170`, file `0x1E4270`.

## Battle input object and circular history

The useful confirmed fields of the battle input object are:

| Offset | Size | Meaning |
| ---: | ---: | --- |
| `+0x14` | 4 | static identifier pointer: `controller1` for side 0, `controller2` for side 1 |
| `+0x20` | 4 | owning fighter pointer used by state and facing logic |
| `+0x24` | 4 | other fighter pointer used by relative-angle calculation |
| `+0x60` | 4 | controller-side selector, zero based |
| `+0x64` | 4 | resident pad pointer, `global pad storage + 0x1C + side * 0x78` |
| `+0x68` | `0x10` | eight signed-halfword battle bindings |
| `+0x7C` | 4 | divisor copied from global battle state byte `+1` |
| `+0x84` | 4 | camera/fighter-relative angle computed during history advance |
| `+0x88` | 4 | opponent/fighter-relative angle computed during history advance |
| `+0x8C` | 4 | validity/presence word gating the alternate angle at `+0x90` |
| `+0x90` | 4 | alternate direction-reference angle used by selectors 10 through 13 |
| `+0x94` | 4 | circular history-record pointer |
| `+0x98` | 4 | previous record index |
| `+0x9C` | 4 | current record index |
| `+0xA0` | 4 | record capacity, initialized as `300 / object[+0x7C]` |
| `+0xA4` | 4 | direction-sector threshold used with selectors 4 and 5 |
| `+0xA8` | 4 | direction-sector threshold used with selectors 2 and 3 |
| `+0xAC` | 4 | translated battle logical mask |
| `+0xB0` | 4 | normalized left-stick magnitude, `record[+0x14] / 255.0` |
| `+0xB4` | 4 | left-stick angle copied from history record `+0x0C` |

The outer constructor clears `+0x60`, `+0x64`, `+0x84`, and `+0x88`, installs
the input object's class pointer, initializes the angular thresholds, and then
enters the history constructor. The threshold initializer writes pi/2
(`0x3FC90FDB`) to `+0xA8` and approximately 5pi/6 (`0x40278B7F`) to `+0xA4`.
A separate setter accepts those values as `f12` and `f13`, respectively, but
no direct clean-overlay caller of that setter was found. Resident callers do
exist: `FUN_0020d030` at `0x0020D360` and `FUN_0020d910` at `0x0020DAD8`
set both thresholds to `0x40060723` (approximately 2.09419 radians) for two
fighter-state cases. Resident call sites `0x0020DDA4`, `0x0020DFA8`,
`0x0020E1A0`, and `0x0020E458` restore the defaults through live
`0x006F09E0`. The raw setter ABI is object in `a0`, `f12` to `+0xA8`, and
`f13` to `+0xA4`.

The installed class table is resident `0x005DDD30`. Its confirmed overlay
entries are destructor live `0x006EF560`, binding refresh live `0x006F0DF0`,
and complete update live `0x006F0EA0`. Thus the latter two have no direct JAL
caller in the overlay: they are reached through resident-owned object
dispatch. The remaining history/matcher/translator calls described below are
direct overlay calls.

RTTI establishes the original class identities. Resident vtable `0x005DDD30`
points to overlay RTTI descriptor live `0x008C3048`, export-byte
`0x008C3008`, file `0x20F148`; that descriptor points to the name literal
`ccCommand` at live `0x008981E0`. Thus the per-side input/history object is the
original `ccCommand` class. Its list owner is `ccCommandCtrl`: resident vtable
`0x005DDD10` points to RTTI live `0x008C3030`, export-byte `0x008C2FF0`, file
`0x20F130`, whose name pointer is live `0x008981D0`. Live constructor
`0x006F0F90` installs that vtable in the controller allocated at battle-owner
`+0x04`, and live `0x00709780` registers each new `ccCommand` in its list.

The two virtual lifecycle paths can be separated exactly. After creating the
battle graph, resident `FUN_001ef330` calls live `0x007095E0` at
`0x001EF42C`. That overlay routine applies list phase live `0x00709BF0` to
each non-null controller at battle-owner `+0x00/+0x04/+0x08/+0x0C`. For the
`ccCommandCtrl` at `+0x04`, this phase invokes each registered `ccCommand`
object's vtable slot `+0x0C`, which is binding refresh live `0x006F0DF0`.
This is the setup/refresh path, not the history-advance path.

The complete update has a separate, also proven, virtual chain. The
`ccCommandCtrl` vtable slot `+0x0C` points to live `0x006D67E0`; that wrapper
calls list phase live `0x00709C70`, which invokes slot `+0x10` of every
registered child. Resident vtable `0x005DDD30` maps that child slot to complete
`ccCommand` update live `0x006F0EA0`. The update explicitly returns zero, so
the phase's remove-on-nonzero branch does not remove it. The controller's next
two slots similarly route through live `0x006D67A0 -> 0x00709D60` and live
`0x006D67C0 -> 0x00709DE0`; those phases reach child slots `+0x14/+0x18`, the
no-op entries live `0x006D6780/0x006D6790`.

The higher caller is resident `FUN_001f03e0`. It loads the four-part owner from
its scheduling object `+0x18`, selects owner pointer `+0x04`, and invokes that
controller's vtable slot `+0x0C` at `0x001F051C`. The call occurs when either
the resident object at `iGpffffce54` has byte `+0xA50 == 1` or the scheduler's
first 16-bit enable mask at `+0x02` has bit `0x0002`; a null controller is
skipped. In the active branch of resident `FUN_001ef8f0`, input-mask collection
`FUN_001f0290` runs at `0x001EF970`, then `FUN_001f03e0` runs at
`0x001EF97C`. This proves the history update's place in the resident input
phase without assuming a host-frame or seconds conversion. The same dispatcher
later invokes controller slot `+0x10` at `0x001F0728` when its second enable
mask `+0x04` has bit `0x0002`, and slot `+0x14` at `0x001F0860` when the first
mask has bit `0x0002`; for `ccCommand` children those two phases reach the
confirmed no-ops.

The enclosing battle manager creates both sides in live `0x00709480`
(export `0x00709440`, file `0x055580`). It allocates side-0 and side-1 input
objects through live `0x00709780`, then links each input `+0x20` to its owning
fighter and `+0x24` to the other fighter. Resident `FUN_001ef330` invokes that
manager setup at `0x001EF3C0`, retrieves side 0 and side 1 through live
`0x00709800` at `0x001EF3D0` and `0x001EF3E4`, and retains the returned input
pointers in battle-global slots `+0xDF0` and `+0xDF4`. This construction chain
independently fixes the `+0x20/+0x24` ownership meanings above.

The history constructor loads the global battle-state pointer from resident
small-data slot `iGpffffca0c`, copies its byte `+1` to object `+0x7C`, and
computes `capacity = 300 / divisor`. It then allocates
`capacity * 0x18 + 0x10`, constructs `capacity` records with stride `0x18`,
stores their pointer at `+0x94`, and clears both indices. Side 0 and side 1 set
the `+0x14` identifiers named above; the same side argument is stored at
`+0x60` and selects the resident pad record using the exact `0x78`-byte stride.
The constructor does not validate the divisor before the integer division and
does not assign a known identifier for a side other than 0 or 1. Clean battle
setup passes only sides 0 and 1; the exact semantic reason for the global
divisor was not pursued.

Each history record is:

| Offset | Size | Meaning after normalization |
| ---: | ---: | --- |
| `+0x00` | 4 | held/current native pad mask |
| `+0x04` | 4 | newly pressed mask, `current & ~previous` |
| `+0x08` | 4 | newly released mask, `previous & ~current` |
| `+0x0C` | 4 | left-stick angle in radians |
| `+0x10` | 4 | right-stick angle in radians |
| `+0x14` | 1 | normalized left-stick magnitude |
| `+0x15` | 1 | right-stick magnitude |
| `+0x16` | 2 | trailing padding, not initialized by the record constructor |

The per-update method first advances the ring: old `+0x9C` becomes `+0x98`,
the current index increments, and it wraps to zero at `+0xA0`. It then copies
the resident pad record's held/pressed/released words, two stick angles, and
two magnitudes into the new current record. The overlay recomputes the two edge
words after stick/direction normalization rather than trusting the copied edge
words.

Raw record initializer live `0x006EF390` clears the three masks, both angles,
and bytes `+0x14/+0x15`, stopping before `+0x16`. Neither the update,
normalizer, translator, boolean matcher, counter, nor `ccCommand` classifier
reads or writes the final two bytes. They are therefore confirmed stride
padding in this subsystem rather than unresolved input fields.

Left-stick magnitudes below `0x40` become zero. Values `0x40..0x7F` become
`((value - 0x40) * 3) / 2 + 0x20`; values at least `0x80` are retained. If the
held word lacks any `0xF000` direction bit, resident `FUN_00114d90` derives a
direction from the left-stick angle and normalized magnitude. If magnitude is
zero while a digital direction exists, resident `FUN_00114e60` derives the
left-stick angle and magnitude from that direction. Digital and analog input
therefore enter history through one native direction representation.

The update passes a nonzero suppression flag to the logical translator when
the owning fighter exists and bits 5 through 8 of fighter halfword `+0x60` are
nonzero. Suppression zeroes `+0xAC`, `+0xB0`, and `+0xB4`; it does not stop the
history ring from advancing and recording the pad state.

## Generic history matcher

The generic matcher begins at live `0x006EFAC0`, file `0x03BBC0`. Ghidra did
not define the prologue at export `0x006EFA80`; its calls instead appear to
target `thunk_FUN_006efbe0` at export `0x006EFAC0`, which is 0x40 into the
actual live function. The omitted prologue loads the current ring index and
rewinds it by the initial skip count with circular wrap.

Its effective ABI is:

```text
a0 = battle input object
a1 = requested mask
a2 = history word selector: 0 held, 1 newly pressed, 2 newly released
a3 = maximum distance from the post-skip starting record, inclusive
t0 = initial number of records to skip
t1 = comparison mode: 0 subset, nonzero exact
t2 = candidate filter mask
return = 1 on first match, otherwise 0
```

The matcher examines `a3 + 1` records, newest to oldest from the post-skip
start, and wraps through index zero. It first applies `candidate &= t2`.
Subset mode accepts `(candidate & requested) == requested`; exact mode accepts
`candidate == requested`.

There is one direction-specific repair for newly pressed words. If the request
contains diagonal nibble `0x3000`, `0x6000`, `0xC000`, or `0x9000`, and the
candidate pressed word has any direction edge, the matcher replaces that
candidate's direction nibble with the same record's held-word direction nibble
before filtering. This lets a diagonal request retain already-held cardinal
context when only the newly changing direction generated an edge. It is not a
general leniency rule for cardinal requests.

The wrapper at live `0x006EFC40`, export `FUN_006efc00` at `0x006EFC00`, file
`0x03BD40`, replaces the requested mask with one selected binding before
calling the matcher. Several Ghidra functions around this matcher are split at
the wrong live targets; call-site register setup and raw bytes are authoritative.

These primitives trust their callers. The binding accessor and wrappers do not
check an index against the eight-entry array, and the matcher has defined loads
only for word selectors 0, 1, and 2. Neither initial skip nor inclusive distance
is clamped to ring capacity: decrementing wraps each time through zero, so a
window longer than the capacity revisits records. The counting sibling below
can consequently count the same physical record more than once. Clean callsites
use valid binding/word selectors and request at most 16 examined records.

### Count-across-window sibling

A sibling primitive at live `0x006EFC70`, file `0x03BD70` (exported byte start
`0x006EFC30`, which Ghidra leaves undefined) uses the same object, requested
mask, word selector, inclusive distance, initial skip, exact/subset flag, and
filter registers. Instead of returning at the first match, it scans the whole
window and returns the number of matching records. Unlike the boolean matcher,
it does not replace a pressed diagonal with the record's held direction.

Its binding-selecting wrapper begins live `0x006EFD90`, export
`FUN_006efd50` at `0x006EFD50`, file `0x03BE90`. The clean overlay contains
one direct call from that wrapper to the counter and no direct in-overlay call
to the wrapper itself. Resident `FUN_0024ccd0` does call the wrapper at
`0x0024CD0C`, so its live battle use is established; that consumer is decoded
below.

### Other resident matcher callers

Resident `FUN_00229130` reads configured bindings 6 and 7 through live
`0x006EF7F0` at `0x00229644` and `0x00229680`, then calls the generic matcher
at `0x00229668` and `0x002296A4`. It accepts a newly pressed occurrence of
either binding over a metadata-derived maximum distance clamped to 0 through
3, with no initial skip, subset comparison, and filter `0xFFFFFFFF`. This is a
confirmed ordinary battle consumer of configurable trigger bindings; its
higher-level move meaning is deliberately not inferred here.

Resident `FUN_00248020` reads binding 1 at `0x00248094` and tests its newly
released word at `0x002480B8` using only the current record. Under its
action-chain gates, that release can reinsert logical `0x00001000`. This is a
concrete consumer of the release-history word, separate from the translator's
new-press path.

## Logical-mask translation

The translator reads the current history record and writes object `+0xAC`.
The confirmed binding-to-logical mapping is:

| Native condition | Logical output |
| --- | ---: |
| newly pressed binding 0, default Triangle | `0x08000000` |
| newly pressed binding 1, default Circle | `0x00001000` and `0x40000000` |
| newly pressed binding 2, default Cross | `0x00010000`, plus modifiers below |
| newly pressed binding 3, default Square | `0x01000000` |
| newly pressed binding 4, default L1 | `0x02000000` |
| newly pressed binding 5, default R1 | `0x20000000`, while clearing `0x04000000` |
| held binding 6 or 7, default L2 or R2 | `0x10000000` |

A binding-2 press can additionally produce `0x00080000` or `0x00100000` from
the current direction sector: native Up (selector 2) adds `0x00080000` and
native Down (selector 3) adds `0x00100000`, both with pi/2 tolerance. The
translator also searches exactly record ages 1 through 7 for an earlier press
containing the same configured binding. If found, current selector 9 with
pi/2 tolerance adds `0x00040000` on success or `0x00020000` otherwise. This is
a separate short-history binding-2 modifier, not either static `ccCommand`
table.

Direction predicates produce a compact low-bit sector mask:

| Direction selector/test | Logical bit |
| --- | ---: |
| selector 5 / selector 4 at object `+0xA4` | `0x00000001` / `0x00000002` |
| selector 2 / selector 3 at object `+0xA8` | `0x00000004` / `0x00000008` |
| selector 2 / selector 3 at pi/2 | `0x00000010` / `0x00000020` |
| selector 6 / selector 7 at `0x40278B7F` | `0x00000040` / `0x00000080` |
| selector 14 / selector 15 at `0x40278B7F` | `0x00000100` / `0x00000200` |

The direction predicate ABI is input object in `a0`, selector in `a1`, current
left-stick angle in `f12`, magnitude in `f13`, and full angular tolerance in
`f14`; it returns a boolean in `v0`. A zero magnitude succeeds only for
selectors 0 and 1. Its nonzero-magnitude target selection is recovered from
the raw primary jump table at live `0x008C2FE0`, export-byte
`0x008C2FA0`, file `0x20F0E0`, and secondary table at live `0x008C2FC0`,
export-byte `0x008C2F80`, file `0x20F0C0`:

| Selector | Target angle before the secondary 8-through-15 adjustment |
| ---: | --- |
| 0, 1 | no fixed target; with zero magnitude these are the only true selectors |
| 2 | pi: native Up |
| 3 | zero: native Down |
| 4 | positive pi/2: native Left |
| 5 | negative pi/2: native Right |
| 6, 8 | object `+0x88` |
| 7, 9 | object `+0x88` plus pi, wrapped to `[-pi, pi]` |
| 10, 12 | object `+0x90`, only when object `+0x8C` is nonzero |
| 11, 13 | opposite of object `+0x90`, with the same validity requirement |
| 14 | object `+0x84` |
| 15 | opposite of object `+0x84` |

Selectors 8 through 15 then take a secondary branch. Selectors 8, 9, and
12 through 15 choose a sign-dependent positive or negative pi/2 reference;
selectors 10 and 11 fall through directly. All recovered nonzero-magnitude
paths finish in resident `FUN_00180d10`, which wraps the difference between
the current and target angles into `[-pi, pi]` and accepts it only when its
absolute value is less than half the supplied tolerance. This establishes the
angular-sector test. The fixed compass names are independently proven by
resident native-direction-to-angle table `0x005B5490`: direction nibbles 1, 2,
4, and 8 map to pi, negative pi/2, zero, and positive pi/2, respectively.
Resident angle-to-direction table `0x005B54D0` contains the corresponding
eight sectors `1000,3000,2000,6000,4000,C000,8000,9000`. User-facing names for
the object-relative selectors remain deliberately unnamed.

The secondary operation is exact: for selectors 8, 9, 12, 13, 14, and 15,
the primary target becomes negative pi/2 when it is strictly below zero and
positive pi/2 otherwise. Thus zero takes the positive branch. Selectors 8 and
9 are the sign collapses of object `+0x88` and its wrapped opposite;
selectors 12 and 13 do the same for valid `+0x90`; selectors 14 and 15 do the
same for `+0x84`. This is a half-plane reduction before the common angular
tolerance test, not an additional history leniency.

All 13 direct clean-overlay calls to the predicate are in the translator and
pass selectors 2, 3, 4, 5, 6, 7, 9, 14, or 15. No direct clean resident call
was found, and no call passes selector 10 through 13. Therefore the
`+0x8C/+0x90` alternate-reference facility is present in the generic predicate
but is unused by the recovered clean battle-input path; its absent producer is
not needed for any logical-mask mapping documented here.

Selectors 0 and 1 are meaningful as the zero-magnitude sentinel case; with a
nonzero magnitude their primary entries leave that magnitude in the target-angle
register. Selectors at least 16 take the same fallthrough. No clean callsite
uses either behavior, so they should not be treated as additional named
directions.

Finally the two-table classifier described below contributes `0x00000400` for
result 0 or `0x00000800` for result 1. Its proven return domain is only `-1`,
0, and 1. The translator nevertheless contains a defensive result-`-2`
branch that would clear logical `0x00001000`; that branch is unreachable from
the clean classifier implementation.

### Resident post-translation synthesis

The translator is not the final writer of every logical action bit. In the
first per-fighter pass of resident `FUN_0024fd80`, call site `0x0024FDD0`
enters `FUN_0024c440`. Before the later input bridge and action-selection pass,
that routine calls `FUN_0024cda0` at `0x0024C610` and `FUN_0024ccd0` at
`0x0024C61C`.

`FUN_0024cda0` is a configurable binding-1 hold/release sequencer. At resident
call sites `0x0024CE34` and `0x0024CE5C` it uses the binding-selecting boolean
wrapper live `0x006EFC40` to test the current held and newly released words,
respectively, with no skip, subset comparison, and filter `0xFFFFFFFF`. When
enabled by fighter halfword `+0xB4A`, it increments held count `+0xB44` toward
threshold `+0xB46`. At and beyond the threshold it adds logical
`0x00002000`; after progress has accumulated in `+0xB48`, release or loss of
held input adds logical `0x00004000` and latches the progress in `+0xB4C`.
Default initializer `FUN_00247f00` sets `+0xB4A` to zero, so this sequencer is
enabled by action/fighter configuration rather than universally.

`FUN_0024ccd0` is the proven consumer of the count-across-window wrapper live
`0x006EFD90`. Its call at `0x0024CD0C` counts newly pressed binding-1 records
over the inclusive distance in fighter `+0xB52`, with no skip, subset
comparison, and filter `0xFFFFFFFF`. Default initializer `FUN_00248540` sets
the count threshold at `+0xB50` to 2 and maximum distance `+0xB52` to 12.
Consequently the default detector activates when more than two presses occur
among the newest 13 records. Once active it remains active while at least two
remain, increments latch `+0xB54`, and adds logical `0x00008000`.

With the default binding table these are Circle-derived signals, but all three
tests resolve binding index 1 dynamically. Logical `0x00002000` and
`0x00004000` feed the resident action-signature contributions documented
below. No conversion of record counts to seconds, host frames, or emulator
timing is assumed here.

## Static `ccCommand` records and ordered matching

The only two clean static command tables are adjacent to the identifiers
`ccCommandCtrl` and `ccCommand`:

| Group | Live table | Export-byte start | File offset | Two identical records |
| ---: | ---: | ---: | ---: | --- |
| 0 | `0x00898180` | `0x00898140` | `0x1E4280` | `{ 0, 0x00004000, 1, 16 }` |
| 1 | `0x008981A0` | `0x00898160` | `0x1E42A0` | `{ 0, 0x00001000, 1, 16 }` |

The descriptor array at live `0x008981C0`, export-byte `0x00898180`, file
`0x1E42C0`, is exactly:

```text
{ table = 0x00898180, count = 2 }
{ table = 0x008981A0, count = 2 }
```

The adjacent literal identifiers are `ccCommandCtrl` at live `0x008981D0`,
export-byte `0x00898190`, file `0x1E42D0`, and `ccCommand` at live
`0x008981E0`, export-byte `0x008981A0`, file `0x1E42E0`.

Each command step is a 12-byte record:

| Offset | Type | Proven use |
| ---: | --- | --- |
| `+0x00` | `s32` | overlap/advance marker; `-2` suppresses the normal one-record advance after a match |
| `+0x04` | `u32` | requested native mask |
| `+0x08` | `s16` | history word selector |
| `+0x0A` | `s16` | number of nearest-match trials |

The classifier is live `0x006F0650`, export `FUN_006f0610` at `0x006F0610`,
file `0x03C750`. It returns `-1` when the input object has no fighter pointer.
Otherwise it evaluates descriptor groups 0 then 1 and walks each group's
records from the highest address backward. Storage order is therefore the
reverse of match order.

For one step it tries offsets `k = 0..limit-1`. Each trial invokes the generic
matcher with exact comparison, direction filter `0xF000`, the step's word
selector, the accumulated skip from newer steps, and maximum distance `k`.
Because trials grow from zero, the first success identifies the nearest match
within `limit` candidates. It adds `k` to the cumulative skip, then normally
adds one so the next, older step cannot reuse the same history record. A
`+0x00` value of `-2` omits only that final increment. Every step must match.

The requested mask is also cumulative across steps: while walking backward,
the classifier facing-rewrites the current record's mask and ORs it into the
request already accumulated from newer records. Thus an older step is matched
against the union of its own request and all newer-step requests. This has no
additional effect in the clean tables because each group's two records are
identical, but it is part of the reusable record format's proven semantics.

Before matching, requested Right `0x2000` becomes Left `0x8000` when fighter
halfword `+0x326` is 1; requested Left becomes Right when `+0x326` is 0. This is
the proven facing-relative horizontal rewrite. The clean Up and Down tables do
not trigger it.

Both clean groups therefore recognize two distinct exact direction presses:

- group 0: two Down (`0x4000`) newly pressed records;
- group 1: two Up (`0x1000`) newly pressed records.

Each step accepts the nearest press among 16 candidate records. Since both
step markers are zero, the two presses must occupy different history records.
Only the direction nibble is compared, so unrelated button bits do not matter;
a diagonal direction nibble is not equal to either cardinal request.

On group success the classifier stores the cumulative age of the first
processed record, which is the command's newer stored step. If one group
succeeds it returns that group index. If both succeed, the larger stored age
wins; equal ages retain group 0 because replacement is strict-greater only.
The translator maps group 0 to logical `0x400` and group 1 to `0x800`.

These tables are double-tap direction recognizers. They are not general attack
strings and are not the resident jutsu selector.

## Function map

| Role | Ghidra/export start | Raw file | Live/linked entry | Original export label or note |
| --- | ---: | ---: | ---: | --- |
| normalize record, synthesize direction, recompute edges | `0x006EF380` | `0x03B4C0` | `0x006EF3C0` | `FUN_006ef380`; export also splits/names its body `FUN_006ef390` at `0x006EF390` |
| outer input-object constructor | `0x006EF4A0` | `0x03B5E0` | `0x006EF4E0` | export entry `FUN_006ef4a0`; installs defaults then calls the history constructor |
| input-object destructor | `0x006EF520` | `0x03B660` | `0x006EF560` | `FUN_006ef520` |
| construct battle input/history | `0x006EF5C0` | `0x03B700` | `0x006EF600` | `FUN_006ef5c0` |
| initialize default bindings | `0x006EF740` | `0x03B880` | `0x006EF780` | `FUN_006ef740` |
| copy eight binding halfwords | `0x006EF770` | `0x03B8B0` | `0x006EF7B0` | export missed entry and labels its loop `FUN_006ef780` |
| get binding by index | `0x006EF7B0` | `0x03B8F0` | `0x006EF7F0` | `FUN_006ef7b0` |
| direction-sector predicate | `0x006EF7D0` | `0x03B910` | `0x006EF810` | `FUN_006ef7d0` |
| generic circular-history matcher | `0x006EFA80` | `0x03BBC0` | `0x006EFAC0` | export missed entry; misleading `thunk_FUN_006efbe0` target |
| binding-selecting matcher wrapper | `0x006EFC00` | `0x03BD40` | `0x006EFC40` | `FUN_006efc00` |
| count matches across a history window | `0x006EFC30` | `0x03BD70` | `0x006EFC70` | export missed entry; later split labels are misleading |
| binding-selecting count wrapper | `0x006EFD50` | `0x03BE90` | `0x006EFD90` | `FUN_006efd50` |
| build logical mask and analog outputs | `0x006EFD80` | `0x03BEC0` | `0x006EFDC0` | `FUN_006efd80` |
| evaluate the two `ccCommand` tables | `0x006F0610` | `0x03C750` | `0x006F0650` | `FUN_006f0610` |
| set the two angular thresholds | `0x006F0990` | `0x03CAD0` | `0x006F09D0` | export missed the short entry |
| restore default angular thresholds | `0x006F09A0` | `0x03CAE0` | `0x006F09E0` | export missed the short entry |
| advance history and calculate relative angles | `0x006F09C0` | `0x03CB00` | `0x006F0A00` | `FUN_006f09c0` |
| refresh configured bindings | `0x006F0DB0` | `0x03CEF0` | `0x006F0DF0` | `FUN_006f0db0` |
| complete input-object update | `0x006F0E60` | `0x03CFA0` | `0x006F0EA0` | `FUN_006f0e60` |
| construct `ccCommandCtrl` list owner | `0x006F0F50` | `0x03D090` | `0x006F0F90` | `FUN_006f0f50`; installs resident vtable `0x005DDD10` |
| construct four-part battle owner | `0x00709200` | `0x055340` | `0x00709240` | `FUN_00709200`; allocates `ccCommandCtrl` into owner `+0x04` |
| create and cross-link both battle sides | `0x00709440` | `0x055580` | `0x00709480` | `FUN_00709440`; links input `+0x20/+0x24` to the two fighters |
| refresh all four battle-owner lists | `0x007095A0` | `0x0556E0` | `0x007095E0` | `FUN_007095a0`; list phase reaches child vtable slot `+0x0C` |
| allocate and register a 0xC0-byte input object | `0x00709740` | `0x055880` | `0x00709780` | `FUN_00709740`; calls the outer constructor at live `0x007097B4` |
| retrieve input object by side | `0x007097C0` | `0x055900` | `0x00709800` | export missed the entry; resident imports it as `func_0x00709800`; compares registered objects' `+0x60` |
| generic list slot-`+0x0C` phase | `0x00709BB0` | `0x055CF0` | `0x00709BF0` | `FUN_00709bb0`; Ghidra mislabels the encoded live call target inside its body |
| generic list slot-`+0x10` phase | `0x00709C30` | `0x055D70` | `0x00709C70` | `FUN_00709c30`; removes a child only when that virtual call returns nonzero |
| `ccCommandCtrl` slot-`+0x0C` wrapper | `0x006D67A0` | `0x0228E0` | `0x006D67E0` | `FUN_006d67a0`; routes to list slot `+0x10` |

The BTL export renders several imported names as `SUB_` or `func_0x`; their
resident export labels and roles are:

| Resident entry | Original export label | Role in this path |
| ---: | --- | --- |
| `0x00113710` | `FUN_00113710` | invert packet button bytes and produce held/pressed/released pad words |
| `0x00114D90` | `FUN_00114d90` | derive native direction bits from analog angle/magnitude |
| `0x00114E60` | `FUN_00114e60` | derive analog angle/magnitude from native direction bits |
| `0x00180D10` | `FUN_00180d10` | wrap an angular difference and apply the strict half-tolerance test |
| `0x001F3DC0` | `FUN_001f3dc0` | update configured binding arrays and notify an existing battle input object |
| `0x001F3F10` | `FUN_001f3f10` | return the configured eight-binding array for a controller side |
| `0x001EF330` | `FUN_001ef330` | create the overlay battle graph and retain both input-object pointers |
| `0x001EF8F0` | `FUN_001ef8f0` | active battle-loop branch that collects scheduler masks and runs the input phase |
| `0x001F0290` | `FUN_001f0290` | collect the two resident scheduler enable masks |
| `0x001F03E0` | `FUN_001f03e0` | dispatch the three virtual phases across the four-part battle owner |
| `0x00217E40` | `FUN_00217e40` | enter a major action state and selected action index |
| `0x00225B60` | `FUN_00225b60` | gate the Triangle-initiated staged-chakra path |
| `0x00229130` | `FUN_00229130` | direct trigger-binding history-matcher consumer |
| `0x00217320` | `FUN_00217320` | copy translated input outputs to the fighter |
| `0x0022B630` | `FUN_0022b630` | optionally rewrite the local logical mask before action selection |
| `0x0022BA30` | `FUN_0022ba30` | consume the state-gated `0x00040000` binding-2 route |
| `0x00239530` | `FUN_00239530` | special-first then ordinary action-record selection |
| `0x00239920` | `FUN_00239920` | scan jutsu-class action slots 4 through 9 |
| `0x00239B00` | `FUN_00239b00` | stage the first qualifying chain slot 10 through 18 |
| `0x0023A390` | `FUN_0023a390` | build an action signature and drive selection/validation |
| `0x0023A9A0` | `FUN_0023a9a0` | gate and dispatch an accepted action index |
| `0x00240C40` | `FUN_00240c40` | build the two mode-specific eligibility masks for the chain scan |
| `0x00244190` | `FUN_00244190` | validate an action-table candidate before dispatch |
| `0x00248020` | `FUN_00248020` | current-record binding-1 release matcher consumer |
| `0x00248EC0` | `FUN_00248ec0` | ordered consumer of the translated logical mask |
| `0x0024C440` | `FUN_0024c440` | run resident post-translation synthesis |
| `0x0024CCD0` | `FUN_0024ccd0` | synthesize a multi-press logical bit from the count helper |
| `0x0024CDA0` | `FUN_0024cda0` | synthesize hold/release logical bits through boolean wrapper calls |
| `0x0024FD80` | `FUN_0024fd80` | fighter-list update containing synthesis, bridge, consumption, and state update passes |

Resident addresses require no overlay correction.

## Resident bridge and action dispatch

Resident `FUN_00217320` copies input-object `+0xAC/+0xB0/+0xB4` to fighter
`+0x338/+0x33C/+0x340`. If the copied mask contains both `0x00001000` and
`0x01000000`, it clears `0x01000000`, giving the former path priority.

The active-fighter update in resident `FUN_0024fd80` calls:

```text
0x0025011C  FUN_00217320   copy translated input to fighter
0x00250128  FUN_002173d0   maintain related direction state
0x00250134  FUN_00248580
0x00250140  FUN_00248ec0   consume action input
0x0025014C  FUN_00249640   update the selected action state
```

`FUN_00248ec0` snapshots fighter `+0x338` at `0x00248EE4`, processes the
Triangle logical bit `0x08000000` through `FUN_00225b60` at `0x002490F0`,
allows `FUN_0022b630` to rewrite the local mask at `0x002493F0`, and calls
`FUN_0023a390` with the resulting mask at `0x00249414`.

The `FUN_0022b630` rewrite is specific to the binding-2 history modifier
`0x00040000`. When fighter halfwords `+0x9F6` and `+0x324` differ, it clears
`0x00040000` and substitutes `0x00020000`; the base `0x00010000` then reaches
the special `0x02000000` action-signature variant below. When those halfwords
are equal, a set of current-action gates can instead accept `0x00040000` as a
separate state transition. In that case the helper returns 1 and leaves the
modifier itself set, but its final mask write clears `0x00010000`,
`0x00020000`, and low direction bits `0x1/0x2`; the caller invokes
`FUN_0022ba30`. Otherwise it returns zero without changing that modifier. This
proves the bit-level routing while leaving the transition's user-facing move
name unspecified.

That routine exposes an important ordering boundary. Before Triangle it passes
the snapshot to `FUN_00228320` at `0x002490D0`; that helper directly consumes
held-trigger logical `0x10000000`. After action-table selection, the possibly
rewritten binding-2/Cross family has parallel consumers: base `0x00010000`
calls `FUN_0022f200` at `0x00249434`, native-Up modifier `0x00080000` calls
`FUN_0022e760(fighter, 1)` at `0x0024945C`, and native-Down modifier
`0x00100000` enters the `FUN_002302c0` / `FUN_0022e760(fighter, -1)` branch at
`0x00249484` / `0x002494EC`. These helper roles were not given game-facing
move names here; the useful fact is that their consumption occurs after, and
in addition to, `FUN_0023a390`.

### Input mask to action signature

`FUN_0023a390` enters its table-driven selection only when the logical mask
contains some bit in `0x0003F000`. Proven contributions to the constructed
action signature are:

| Logical input | Action-signature contribution |
| ---: | ---: |
| `0x00001000` | `0x00100000` |
| `0x00002000` | `0x00400000` |
| `0x00004000` | `0x00800000` |
| `0x00008000` | no direct bit; satisfies the selector's `0x0003F000` entry gate |
| `0x00010000` | `0x01000000`, or `0x02000000` with logical `0x00020000` |
| `0x01000000` | `0x10000000` |
| `0x00000010/20/40/80` | `0x00000200/400/1000/2000` |
| `0x00000100/200` | `0x00004000/8000` |
| `0x00000400/800` | `0x00010000/20000` and replacement of higher direction context |

The five direct action families are an ordered choice, not five independent
OR operations: logical `0x00001000` has priority over `0x00010000`, which has
priority over `0x01000000`, then `0x00002000`, then `0x00004000`. If more
than one survives earlier consumers, only the first contributes its action
family. The synthesized multi-press bit `0x00008000` has no corresponding
signature bit, but by itself it passes the `0x0003F000` gate and can therefore
request selection using only the contextual and direction signature assembled
around it. Logical `0x00020000` is likewise a modifier: it selects the
`0x02000000` variant only when base logical `0x00010000` is present.

The low direction contribution also has a context branch. When
`FUN_0023a0d0` returns 2 or 3, only logical direction bit `0x40` is considered
and it contributes signature `0x1000`; the other low direction bits and both
`ccCommand` double-tap results are ignored for that selection. Other return
values use the complete low-direction mapping in the table.

The mask test is only one part of the entry gate. Selection also requires
fighter halfword `+0xB34 == -1`, a non-`-1` return from `FUN_0023a0d0`, a
zero return from `FUN_002455b0`, and acceptance by `FUN_00239e50` for the
current major/minor action state. When `+0xB34` is not `-1`, the routine calls
`FUN_0021dae0` and returns false without constructing a signature.

The signature also includes side, target-height, facing, and current-state
context. `FUN_0023a390` calls `FUN_00239530` at `0x0023A8F8`, then validates
an accepted index through `FUN_00244190` and dispatches it through
`FUN_0023a9a0`.

The per-character action array is at fighter pointer `+0xA54`, its signed
halfword count at `+0xA38`, and its record stride is `0x54`. Confirmed fields
used by this path are:

| Record offset | Use |
| ---: | --- |
| `+0x10` | action type/category flags |
| `+0x14` | secondary flags |
| `+0x18` | signed-byte chaining or continuation selector |
| `+0x1C` | normalized input signature |
| `+0x20` | float action cost |
| `+0x34` | contextual threshold |

For the ordinary scan, `FUN_00239530` walks indices upward and excludes
records whose `+0x10` contains type bits `0x2`, `0xF000`, or `0xF00000`. It
then canonicalizes the constructed signature according to the candidate
record and requires exact equality with record `+0x1C`. The confirmed
record-directed rewrites are:

| Candidate `+0x1C` condition | Rewrite applied to the constructed signature |
| --- | --- |
| bit `0x00000001` set | collapse bits `0x0000000F` to `0x00000001` |
| bit `0x00000010` set | collapse bits `0x000000F0` to `0x00000010` |
| bit `0x00000100` set | collapse bits `0x000FFF00` to `0x00000100` |
| either bit in `0x00003000` set | clear constructed bits `0x0000C000` |
| either bit in `0x0000C000` set | clear constructed bits `0x00003000` |
| bit `0x00200000` set while constructed `0x00100000` is set | replace constructed `0x00100000` with `0x00200000` |

These are deliberate candidate-controlled equivalence classes followed by an
equality test, not a subset match. The jutsu scan uses the same rewrites.

The signature begins with exact contextual bits before adding input-derived
bits. Its low context group is `0x4` when `(fighter[+0x9B8] & 3) >= 2`;
otherwise it is `0x2` when signed byte `fighter[+0x63]` is negative and `0x4`
when that byte is nonnegative. It then adds exactly one of `0x20`, `0x40`, or
`0x80` from the two fighters' vertical centers. `0x40` is the center band with
absolute separation below 150; outside that band, the other fighter's center
less than this fighter's center contributes `0x80`, and the opposite ordering
contributes `0x20`. The `ccCommand` results replace, rather than merely
supplement, ordinary direction context: logical `0x400/0x800` first reduce the
signature to its low byte, preserving those contextual bits, then add
`0x00010000/0x00020000`.

One late, record-aware rewrite means the low-direction table above is not
always the final signature. When constructed bit `0x2000` is present,
`FUN_0023a390` asks `FUN_0021df60` for category `0x41` if signed fighter byte
`+0x63` is negative or `0x42` otherwise. If a record is found, its signature
and the constructed signature must agree under mask `0xFFF03000`. The rewrite
is blocked only when fighter halfwords `+0x9F6/+0x324` are equal, record float
`+0x34` is nonzero, and that float is greater than fighter float `+0x32C`
(negative-byte branch) or `+0x330` (nonnegative branch). When the comparison
accepts, constructed `0x2000` is cleared; logical bit `0x1` or `0x2` then adds
constructed `0x1000`. The two search calls are at `0x0023A750` and
`0x0023A814`, and the final rewrite begins at `0x0023A8C8`. This is a
state/candidate equivalence before action-table selection, not history-matcher
leniency.

In the ordinary immediate path, record `+0x18` must be `-1` or `-2`; the
first accepted ascending record is returned. While major action state 8 is
already active, a matching record can instead be staged at fighter `+0xA3E`
as a continuation keyed by fighter `+0xA3C` and record `+0x18`. That staging
path returns no immediate index. Character data, not the resident executable,
supplies the actual ordinary attack index.

A separate deferred selector handles nonzero modes returned by
`FUN_0023a0d0`. `FUN_00239530` calls `FUN_00239b00` when no action is already
staged at `+0xA3E`; it scans fixed slots 10 through 18 in ascending order and
never returns an immediate action. For each slot it applies the same
candidate-directed signature equivalences, requires available action cost,
and calls `FUN_00240c40` to build two eligibility masks. A slot qualifies only
when those masks intersect record fields `+0x10` and `+0x14`, respectively,
and the normalized signature equals record `+0x1C`; the first qualifying slot
is written to `+0xA3E`. Modes 2 and 3 additionally discard signature bits
`0x000FFF00` from both sides when the candidate uses any of that group. This
fixed 10-through-18 chain scan is distinct from both the immediate ordinary
scan and the jutsu-class 4-through-9 scan.

There is one fixed-slot exception to the ascending ordinary scan. Constructed
signature bit `0x02000000`—the binding-2/Cross contribution selected when
logical `0x00020000` is also present—bypasses that scan and tests only action
index 19. It returns slot 19 when record type `+0x10` has bit `0x2` and
`FUN_0023bee0` accepts the fighter state. In the ordinary scan, records with
type bit `0x02000000` are additionally ineligible when signed byte `+0x18` is
`-1`.

After `FUN_00239530` returns an index, `FUN_0023a390` asks
`FUN_00244190` to validate it. A rejection clears constructed signature bits
`0x000F0000` and repeats selection; an accepted index is dispatched. This is
the one proven resident fallback at this boundary. `FUN_0023a9a0` then checks
the same validator again: return 0 rejects dispatch, return 1 proceeds, and
returns 2 or 3 first invoke `FUN_002445d0` before proceeding. Thus the outer
check selects the fallback behavior, while the inner check can request
additional preparation as well as reject.

### Representative ordinary attack path

With default bindings, a new Circle press creates logical `0x00001000` and
`0x40000000`. `FUN_0023a390` converts the former to action-signature bit
`0x00100000`. When no staged special action is selected, `FUN_00239530` takes
the ordinary ascending action-record scan described above. The accepted record
then reaches `FUN_0023a9a0`, which resolves
`fighter[+0xA54] + index * 0x54` and ultimately enters it through
`FUN_00217e40(fighter, 8, index, mode)` at `0x0023AE84`. The mode is passed
through from `FUN_0023a9a0`'s third argument; the `FUN_0023a390` caller passes
zero.

This proves the reusable ordinary-attack caller path without claiming one
universal record index: indices are character-table data.

### Representative chakra/jutsu path

The jutsu route is stateful and is not encoded in the two `ccCommand` tables.
With default bindings:

1. A new Triangle press produces logical `0x08000000`.
2. `FUN_00248ec0` calls `FUN_00225b60`. On success, its caller stages chakra
   amount/tier in fighter `+0x7C/+0x80` and initializes `+0x82`; this branch
   does not directly enter an action record.
3. A subsequent Circle action produces the same `0x00100000` signature used
   by the ordinary path.
4. `FUN_00239530` first calls the special selector `FUN_00239920` at
   `0x00239564`. When fighter `+0x7C` is nonzero and the state gates accept,
   that selector scans fixed action indices 4 through 9. It requires
   `record[+0x10] & 0x00F00000 != 0`, requires record float `+0x20` not to
   exceed the staged amount, applies the candidate-directed signature
   normalization above, and requires equality with record `+0x1C`. The loop
   does not stop on a match: if multiple slots qualify, the highest matching
   index wins.
   If major action state 8 is already active, the selected slot is staged in
   fighter `+0xA3E` and the selector returns no immediate index.
5. An immediately accepted index again passes through `FUN_00244190` and
   `FUN_0023a9a0`. The latter applies special-record gates through
   `FUN_00244ea0` and `FUN_00244e00`, then calls
   `FUN_00217e40(fighter, 8, index, mode)`.

The staged-chakra selection and `0x00F00000` category strongly identify
indices 4 through 9 as the jutsu-class action slots. A specific character's
visible jutsu name or exact record contents were not independently decoded in
this investigation.

`FUN_00217e40` writes major action state at fighter `+0x18E` and action index
at `+0x190`. For major state 8 it points fighter `+0xA30` at the active record
already held in `+0xA4C`.

An alternate resident caller exists in `FUN_0024da50`: it calls
`FUN_00217320` at `0x0024DAFC` and then passes fighter `+0x338` directly to
`FUN_0023a390` at `0x0024DB0C`. The following code separately tests logical
`0x10000000`. This confirms that the bridge and action selector are reusable
outside the main `FUN_0024fd80` sequence; the exact purpose of that alternate
update branch was not assigned here.

## Confidence, boundaries, and useful negative results

- **High confidence:** overlay/file/live mapping; native pad masks; default and
  refreshed binding representation; input object and 0x18-byte history layout;
  held/press/release recomputation; generic matcher ABI and wrap/order rules;
  all static `ccCommand` bytes and descriptors; double-tap semantics; logical
  output fields; resident bridge; action-record stride and dispatch call chain.
- **Supported:** semantic names for the two relative-angle fields and the
  jutsu-class label for indices 4 through 9. Their data flow is exact, while
  the names follow their consumers rather than exported symbols.
- **Unresolved:** user-facing compass names for the object-relative direction
  selectors, the dormant producer/meaning of object `+0x8C/+0x90`, the
  semantic reason for the history capacity divisor, and character-specific
  ordinary/jutsu record contents.
- The clean static `ccCommand` data contains only two two-step cardinal
  double-tap tables. No general attack-string table was found there.
- The count-across-window helper has no direct caller beyond its binding
  wrapper. That wrapper has no in-overlay caller but has the proven resident
  multi-press caller `FUN_0024ccd0`.
- Jutsu selection is a resident action-table path mediated by staged fighter
  state, not a hidden third `ccCommand` sequence.
- No emulator input mapping, Adventure code, runtime patch, or writable
  disassembly operation was used. No conclusion here depends on substitution,
  damage scaling, localization, widescreen, or emulator infrastructure.
