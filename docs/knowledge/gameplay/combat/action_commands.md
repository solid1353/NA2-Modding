# Battle action-command and input interpretation

This document records the retail NA2 (`SLPS-25837`) battle input path from
the resident pad abstraction through `BTL.BIN` history matching and back into
the resident action-table dispatcher. It describes the game's native masks.

## Research coverage

- **Assigned scope:** battle command and input interpretation: native pad
  representation, `ccCommand` history and static records, matching, order and
  leniency semantics, logical-input translation, the resident bridge into
  action selection, action-table setup and the static action-data census, and
  representative ordinary and jutsu dispatch callers.
- **Exploration depth:** bounded, deep static analysis, not an exhaustive
  audit of `BTL.BIN` or the resident executable.
  - Overlay: the contiguous `ccCommand` implementation from live `0x006EF390`
    through `0x006F1040`, its controller/list plumbing around live
    `0x006D67A0..0x006D67E0` and `0x00709240..0x00709F40`, both static command
    tables and their descriptor array at live `0x00898180..0x008981CF`, and
    both direction jump tables at live `0x008C2FC0..0x008C301F`.
  - Resident: pad production (`FUN_00113710`), analog/digital direction
    conversion (`FUN_00114d90`/`FUN_00114e60`), battle construction and
    virtual scheduling (`FUN_001ef330`, `FUN_001ef8f0`, `FUN_001f0290`,
    `FUN_001f03e0`), configured bindings (`FUN_001f3dc0`/`FUN_001f3f10`),
    the input bridge and direct matcher consumers, and the action-selection
    chain from `FUN_00217320`/`FUN_00229130` through `FUN_00239530`,
    `FUN_0023a390` and `FUN_0023a9a0`, including the mode and entry-gate
    functions, the eligibility-mask builder and its PRNG helper, validation,
    dispatch, and the relevant synthesis/update callers.
  - Enumerations: direct callers of the generic matcher family, all 13 direct
    overlay direction-predicate calls, and all 23 direct input-template copy
    callers of `FUN_00247dc0`.
  - Data: all 78 distinct character definitions selected by the 94-row
    resident table, all 3,444 records in their action arrays, and all 1,064
    distinct nonempty display-name strings; setup through `FUN_002151e0`,
    `FUN_00219620`, `FUN_00218fe0` and `FUN_00218d30`; later category
    mutation in `FUN_002449c0`, `FUN_002b49c0` and `FUN_0029c1e0`.
  - Writers: the 321 distinct callbacks reached by the definitions' callback
    tables were screened for secondary-word writers (272 analyzed functions,
    49 instruction-byte reads), and bounded direct-offset store searches
    covered the mode, interval and pending fields.
- **Confirmed coverage:** the address convention; native pad masks and
  configurable binding layout, including the width each binding reader
  tests; `ccCommand`/`ccCommandCtrl` identity, object fields, construction,
  virtual update route, circular history records, normalization, and edge
  recomputation; exact boolean and count matcher ABIs, scan order, wrapping,
  comparison modes, diagonal repair, and caller hazards; direction-selector
  and logical-mask mappings, native and angular magnitude thresholds and
  mixed-input precedence; both two-step cardinal command tables, their
  ordered matching semantics, exact two-press age bounds, per-step request
  reset and retained recognition; resident post-translation synthesis and
  constructor hold/release and multi-press settings; action-signature
  construction and equivalence rewrites; action-record layout and the
  ordinary, fixed-chain, fixed-slot, and jutsu-class selection partitions;
  all recovered selector modes, major/substate entry gates, per-candidate
  chain masks and PRNG calls; the 16-bit pending field and its overwrite
  rules; validation, the caller's acceptance of validator -1, fallback, and
  final dispatch; representative default-binding Circle and
  Triangle-to-jutsu paths; the pacing byte that sizes the history ring;
  relative-reference angle producers; action-array setup and later mutation;
  shared slot fields with their complete character exceptions; named
  action-record examples; and the checked secondary-word mutations' effects
  on the two eligibility groups.
- **Unresolved or untested:** user-facing labels of object-relative
  direction selectors; a producer or active use for dormant `ccCommand
  +0x8C/+0x90`; every indirect or character-specific change to action
  eligibility after common setup; complete visible command sequences for
  every named record; the player-facing roles of attached-object IDs 0/1 and
  each selector mode; simultaneous reachability of the remaining mode-0
  competing pending matches; mode/secondary writes outside the stated search
  and callback bounds; and observed selection frequencies. No pending-action
  duration can be derived from history age alone.
- **Deliberate exclusions and overlap:** this document owns input
  interpretation, action signatures, and record selection, including the
  relevant data variants. [Character assets](../../game/character_assets.md)
  owns character assets and jutsu-resource tables;
  [Combat action execution](combat_action_execution.md) owns action
  execution, pending dispatch and interruption;
  [Character action callbacks](../characters/character_action_callbacks.md) owns callback
  dispatch and timeline control; [Extra Hit](extra_hit.md) owns the exchange
  roles behind selector modes 2/3; [Battle AI](../session/battle_ai.md) owns AI state
  dispatch and retained action queues; [Ultimate Jutsu](../characters/ultimate_jutsu.md)
  owns that execution; [Substitution](../characters/substitution.md) and [Damage](damage.md)
  own their mechanics; [Controller input](../../runtime/controller_input.md)
  owns pad production and publication;
  [Battle Command List and move chart](../../localization/ui/battle/command_list_and_move_chart.md)
  owns binding presentation and the action-chart display.
- **Evidence limitations:** findings were cross-checked statically between
  clean binary bytes, disassembly, decompilation, encoded calls/pointers,
  and table data. The character census reads shipped static arrays; common
  setup can copy, disable, or rewrite those records before selection.
  Untraced eligibility changes and observed action outcomes require their own
  evidence. Direct-offset searches cannot exclude adjusted-base or bulk
  stores; the callback screen does not cover every transitive helper or
  virtual call. No dynamic history capture or controlled input playback was
  used.

## Evidence identity and address convention

Binary identities and address conventions are in
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
Ghidra can attach an intra-overlay call to a label 0x40 past the callee's
exported byte start; `D` below means the Ghidra imported byte address
(`live = D + 0x40`).

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

Resident `FUN_00113710` is the concrete producer. Once the pad is in its
readable state, it concatenates the two packet button bytes and XORs them with
`0xFFFF`. The resident pad record exposes these native-input fields:

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
| `+0x74` | 4 | raw held history used by resident edge production |

The battle overlay copies neither resident repeat `+0x70` nor raw held
history `+0x74`. Complete update live `0x006F0EA0` copies only `+0x64/+0x68/+0x6C`,
`+0x4C/+0x50`, and `+0x49/+0x4A`, as corroborated by its load/store bytes at
Ghidra D `0x006F0EDC..0x006F0F14` (live `0x006F0F1C..0x006F0F54`). It then
recomputes pressed and released edges against the preceding normalized battle
history held word. Thus the comparison source is a retained battle sample,
not pad `+0x74`; see [Controller input](../../runtime/controller_input.md#publication-lifetime-and-consumer-snapshots).

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

Binding consumers use the full 16-bit value. The translator (Ghidra BTL
`FUN_006efdc0`, containing D `0x006F0500`) loads the eight copied bindings at
input-object `+0x68..+0x76` as signed halfwords and ANDs each with the 32-bit
held or pressed pad word, so a binding to Select, L3, or R3 is tested like any
other bit. The three BTL readers of binding index 1, D `0x00796A50`,
`0x007FF520`, and `0x00806680`, AND it with the 32-bit word at
`0x78 * side + [gp-0x35F4] + 0x84` in the same way.

The remaining readers map bindings to fixed button sets for presentation
instead; they are listed in
[Battle Command List and move chart](../../localization/ui/battle/command_list_and_move_chart.md#binding-presentation-readers).

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
| `+0x7C` | 4 | construction-time copy of system-context display-count pacing byte `+0x01` |
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

The higher caller is resident `FUN_001f03e0`, which reaches the
`ccCommandCtrl` at owner pointer `+0x04` in its three phases: slot `+0x0C` at
`0x001F051C`, slot `+0x10` at `0x001F0728`, and slot `+0x14` at
`0x001F0860`; for `ccCommand` children only the first reaches the history
update. The enable masks and auxiliary-byte exception that gate each phase are
owned by [Pause and replay](../session/pause_and_replay.md#selective-update-gating). In
the active branch of resident `FUN_001ef8f0`, mask collection `FUN_001f0290`
runs at `0x001EF970`, then `FUN_001f03e0` at `0x001EF97C`. This places the
history update in the resident input phase without a seconds conversion.

The enclosing battle manager creates both sides in live `0x00709480`
(export `0x00709440`, file `0x055580`). It allocates side-0 and side-1 input
objects through live `0x00709780`, then links each input `+0x20` to its owning
fighter and `+0x24` to the other fighter. Resident `FUN_001ef330` invokes that
manager setup at `0x001EF3C0`, retrieves side 0 and side 1 through live
`0x00709800` at `0x001EF3D0` and `0x001EF3E4`, and retains the returned input
pointers in battle-global slots `+0xDF0` and `+0xDF4`. This construction chain
independently fixes the `+0x20/+0x24` ownership meanings above.

The history constructor loads the system-context pointer from resident
slot `0x006073FC` (`gp-0x35F4`, exported as `iGpffffca0c`), copies its byte
`+0x01` to object `+0x7C`, and
computes `capacity = 300 / divisor`. It then allocates
`capacity * 0x18 + 0x10`, constructs `capacity` records with stride `0x18`,
stores their pointer at `+0x94`, and clears both indices. Side 0 and side 1 set
the `+0x14` identifiers named above; the same side argument is stored at
`+0x60` and selects the resident pad record using the exact `0x78`-byte stride.
The constructor does not validate the divisor before the integer division and
does not assign a known identifier for a side other than 0 or 1. Clean battle
setup passes only sides 0 and 1.

The divisor is the engine's display-count pacing threshold, 1 after engine
initialization and 2 once the front-end task starts; its setters,
interrupt-counter producer and wait are owned by
[Task system](../../runtime/task_system.md#root-pacing-and-the-engine-gate),
system-context ownership by [Controller input](../../runtime/controller_input.md),
and the resulting update cadence by
[Battle lifecycle](../session/battle_lifecycle.md#battle-update-cadence).

Thus a divisor of 2 allocates 150 records (`0xE20` bytes including the array
overhead), while 1 allocates 300 (`0x1C30` bytes). **Inference:** dividing 300
by the display-count interval keeps the nominal history span constant across
those pacing settings, provided the input phase advances once per paced
update. The byte is copied only at construction; the history updater does not
read it again or resize the ring. Matcher windows remain record counts:
the 16-record boolean windows and 13/17/31-record count windows are not
divided by this value. Actual battle cadence and the designer's intended
duration are not established by this static connection alone.

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
left-stick angle and magnitude from that direction. This normalization does
not force digital direction and a nonzero stick angle to agree.

### Direction magnitude, source precedence, and invalid nibbles

The analog-to-D-pad helper synthesizes bits only for magnitude **strictly
greater than `0xA0`**, established by resident `slti ... 0xA1` at
`0x00114DAC`. In this normalizer the helper receives the remapped magnitude.
The angular predicate instead tests only whether that magnitude equals zero:
BTL bytes at D `0x006EF7DC..0x006EF7EC` compare `f13` with zero before its
selector table. Consequently, with no existing digital directions, raw
left-stick magnitudes `0x40..0xA0` can support angular logical direction
tests without producing any native `0xF000` history direction bits. Raw
`0x40` becomes `0x20`, raw `0x7F` becomes `0x7E`, and raw `0x80..0xA0`
remain unchanged. At raw `0xA1` and above, synthesis can supply native bits.
These conditional results distinguish angular selection from the native
press recognizers; they are not measured stick travel or player-facing zones.

An existing native direction nibble skips analog-to-D-pad synthesis. If
normalized magnitude is nonzero, the normalizer also skips the reverse
digital-to-angle helper, retaining both the incoming angle and incoming
digital nibble. Thus digital bits determine the history match while the
angle determines angular predicates in that mixed-input case. If magnitude
is zero, the reverse helper sets magnitude to `0xFF` and supplies the table
angle for cardinal/adjacent-diagonal nibbles `1,2,3,4,6,8,9,12`.

The 16-float reverse table at resident `0x005B5490..0x005B54CF` contains
sentinel 4.0 for nibble `0,5,7,10,11,13,14,15`. On one of those entries,
`FUN_00114e60` writes angle zero and magnitude zero and returns false.
The caller does not clear the held native nibble or recompute edges again:
normalizer bytes at D `0x006EF434..0x006EF47C` establish edge stores before
the reverse-helper call. Therefore an invalid opposing-direction combination
is not silently rewritten to a cardinal held mask in this path. This states
the helper's behavior for its input domain without asserting a live occurrence
of those combinations.

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
The binding accessor at live `0x006EF7F0` returns a zero binding unchanged,
and such a binding satisfies the subset comparison for every candidate.

There is one direction-specific repair for newly pressed words. If the request
contains diagonal nibble `0x3000`, `0x6000`, `0xC000`, or `0x9000`, and the
candidate pressed word has any direction edge, the matcher replaces that
candidate's direction nibble with the same record's held-word direction nibble
before filtering. This lets a diagonal request retain already-held cardinal
context when only the newly changing direction generated an edge. It is not a
general leniency rule for cardinal requests.

The wrapper at live `0x006EFC40`, export `FUN_006efc00` at `0x006EFC00`, file
`0x03BD40`, replaces the requested mask with one selected binding before
calling the matcher. It loads the binding from input-object `+0x68` itself
rather than through the accessor. The counting sibling below has the same
wrapper at live `0x006EFD90`, export `FUN_006efd50`, file `0x03BE90`. Several Ghidra functions around this matcher are split at
the wrong live targets; call-site register setup and raw bytes are authoritative.

These primitives trust their callers. The binding accessor and wrappers do not
check an index against the eight-entry array, and the matcher has defined loads
only for word selectors 0, 1, and 2. Neither initial skip nor inclusive distance
is clamped to ring capacity: decrementing wraps each time through zero, so a
window longer than the capacity revisits records. The counting sibling below
can consequently count the same physical record more than once. The examined
clean callsites use valid binding/word selectors. Boolean callers request at
most 16 examined records; constructor-configured count windows extend to 31
records, as documented under resident synthesis below.

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
Its two held-trigger checks (bindings 6 and 7) run with `a0` holding the
logical bits accumulated from the earlier bindings; the second check at live
`0x006EFF2C` adds its result to that `a0` value before the logical mask is
stored. The confirmed binding-to-logical mapping is:

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

### Relative-reference producers and their geometric meaning

The history advance at live `0x006F0A00` computes both reference angles before
translation. Let `P` be the owning fighter's vector at `+0x30`, `Q` the other
fighter's vector at `+0x30`, and `W(a)` the routine's single-turn wrap into
`[-pi, pi]`. Resident `FUN_001805a0(P,Q)` returns
`W(atan2(Q.y-P.y, Q.x-P.x) + pi/2)`, while `FUN_00180680(P,Q)` returns
`r = sqrt((Q.x-P.x)^2 + (Q.y-P.y)^2)`; its disassembly explicitly clears the
third difference component before the squared-length calculation.

Resident `FUN_001f1370` retrieves the camera/reference object used here. Its
rotation vector `+0x40` supplies `c = reference[+0x40]` and
`g = reference[+0x48]`; a missing reference supplies zeros. The updater first
forms horizontal reference `h = W(g - (yaw + pi))` when `c >= 0`, or
`h = W(g + yaw)` otherwise. It then forms
`q = W(atan2(r, Q.z-P.z) + pi)` and stores
`+0x88 = W(q)` when `h < 0`, or `W(-q)` otherwise. The store is live
`0x006F0CF4`, file `0x03CDF4` (Ghidra `0x006F0CB4`). This reference therefore
includes opponent elevation, with horizontal sign determined by the view.
At equal height and nonzero horizontal separation its target is native Right
for `h < 0` and native Left otherwise. Selectors 6 and 7 test that reference
and its opposite; selectors 8 and 9 remove its vertical component through
the documented sign collapse. These are geometric descriptions, not recovered
menu labels.

The second store, live `0x006F0DC0`, file `0x03CEC0` (Ghidra
`0x006F0D80`), writes `+0x84 = W(g - (fighter[+0x48] + pi))` when `c >= 0`,
or `W(g + fighter[+0x48])` otherwise. Selectors 14 and 15 therefore use the
horizontal signs of the owning fighter's orientation relative to the view,
rather than the opponent-elevation calculation. Input logical `0x40/0x80`
and `0x100/0x200` can consequently differ; they do not encode one redundant
pair of direction tests.

The dormant reference has no initialization in the recovered `ccCommand`
constructors: the outer constructor clears `+0x84/+0x88` but leaves
`+0x8C/+0x90` alone, and its base constructor live `0x00709AA0` initializes
only its own fields through `+0x5C`. The history constructor, advance, binding
refresh and complete update also do not write that pair. A byte-level audit of
the direct JAL encoding for live predicate `0x006EF810` finds exactly 13 calls
in BTL and zero in the resident and ETC programs; all 13 are the translator
calls listed above. No BTL absolute pointer to that predicate was found.
This establishes non-use in that bounded input path without treating the
uninitialized pair as a valid alternate reference or asserting that every
possible computed call has been excluded.

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
respectively, with no skip, subset comparison, and filter `0xFFFFFFFF`.
Fighter halfword `+0xB4A` is both its nonzero enable gate and progress cap.
The routine also requires a zero release latch `+0xB4C`, major state other
than 5 or 6, and an input object. Signed cooldown `+0xB40` approaches zero
by one per eligible invocation and clears held count `+0xB44` while nonzero.
With zero cooldown, held input increments that count toward threshold
`+0xB46`; loss of held input clears it. At and beyond the threshold the
routine adds logical `0x00002000` and increments progress `+0xB48` to the
`+0xB4A` cap, then overflow count `+0xB4E` to `0x7FFF`. Once progress is
nonzero, release or loss of held input adds logical `0x00004000`. Any such
logical bit latches the progress in `+0xB4C` (or 1 when progress is zero),
clears progress and overflow, and prevents further synthesis until the latch
is reset. Default initializer `FUN_00247f00` sets `+0xB4A` to zero, so this
sequencer is enabled by action/fighter configuration rather than universally.

The action consumer `FUN_00248020` supplies a concrete cooldown/reset route.
When the current major-8 action record has category bits in `0x000F0000`,
it removes logical `0x2000`, reloads `+0xB40` from `+0xB42`, and clears
held count, progress, release latch, and overflow. Thus `+0xB42` is a reload
value, while synthesis decrements or increments `+0xB40` toward zero.

`FUN_0024ccd0` is the proven consumer of the count-across-window wrapper live
`0x006EFD90`. Its call at `0x0024CD0C` counts newly pressed binding-1 records
over the inclusive distance in fighter `+0xB52`, with no skip, subset
comparison, and filter `0xFFFFFFFF`. Default initializer `FUN_00248540` sets
the count threshold at `+0xB50` to 2 and maximum distance `+0xB52` to 12.
Consequently the default detector activates when more than two presses occur
among the newest 13 records. Once active it remains active while at least two
remain, increments latch `+0xB54`, and adds logical `0x00008000`.

### Constructor input-parameter overrides

`FUN_00247d40` initializes a 24-byte parameter template using
`FUN_00247f00` and `FUN_00248540`. `FUN_00247dc0` copies its twelve
halfwords to fighter `+0xB40..+0xB56` and the corresponding shadow at
`+0x918..+0x92E`. All 23 direct resident callers were inspected and their
character IDs resolved through the definition records, rather than inferred
from nearby function names. Nine constructors enable hold/release synthesis:

| Character ID | Constructor | Cooldown reload `+0xB42` | Hold threshold `+0xB46` | Progress cap `+0xB4A` | Copy call |
| ---: | --- | ---: | ---: | ---: | --- |
| 40 | `FUN_00278930` | 2 | 2 | 60 | `0x002789F8` |
| 48 | `FUN_00280de0` | 24 | 24 | 60 | `0x00280EC0` |
| 53 | `FUN_00288d60` | 24 | 12 | 36 | `0x00288E2C` |
| 54 | `FUN_0028bfa0` | 24 | 24 | 60 | `0x0028C068` |
| 57 | `FUN_00295db0` | 16 | 16 | 30 | `0x00295E90` |
| 64 | `FUN_002b37e0` | 2 | 2 | 36 | `0x002B3998` |
| 77 | `FUN_002d7d70` | 16 | 8 | 90 | `0x002D7E9C` |
| 84 | `FUN_002ee1a0` | 16 | 12 | 90 | `0x002EE284` |
| 85 | `FUN_002effd0` | 16 | 5 | 60 | `0x002F009C` |

These are exactly the nine definitions with hold/release signature families
in the complete static action-array census below. Fifteen constructors
override the multi-press window; each retains threshold `+0xB50 = 2`:

| Inclusive distance `+0xB52` | Examined records | Character IDs | Copy calls, in matching ID order |
| ---: | ---: | --- | --- |
| 16 | 17 | 14, 38, 49, 51, 62, 66, 67, 69, 76, 86 | `0x0025F084`, `0x00275434`, `0x00283344`, `0x00286964`, `0x002A9078`, `0x002B8C3C`, `0x002BD004`, `0x002C1D38`, `0x002D43DC`, `0x002F1030` |
| 30 | 31 | 6, 16, 65, 75, 77 | `0x00258F64`, `0x00261054`, `0x002B7354`, `0x002D2B24`, `0x002D7E9C` |

ID 77 overrides both groups, explaining the 23 distinct copy calls. These
values describe constructor setup, not immutable fighter constants:
`FUN_002ee380` also writes ID 84's progress cap to 60 in its mode-1 branch
and 90 in its mode-0 branch, at `0x002EE4C0` and `0x002EE5E0`.

With the default binding table these are Circle-derived signals, but all three
tests resolve binding index 1 dynamically. Logical `0x00002000` and
`0x00004000` feed the resident action-signature contributions documented
below. No conversion of record counts to seconds is assumed here.

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

The requested mask resets for each step. Raw instruction `move s1, zero`
at D `0x006F0730` (live `0x006F0770`, bytes `2D 88 00 00`) is the outer
step-loop target. The inner nearest-match trials reload that step's mask,
facing-rewrite it, and OR it into `s1` at D `0x006F07A0`; they do not carry
a newer step's mask into the next step. The cumulative value across steps is
the history skip in `s5`, not the requested mask.

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

### Exact age bounds and retained matches

Let age zero be the current normalized battle-history record. For either
shipped table, let `n` be the newer press age and `o` the older press age.
The classifier's growing inclusive trials establish exactly:

```text
0 <= n <= 15
n + 1 <= o <= n + 16
```

Thus the full pair can reach age 31, although each individual step examines
at most 16 records. The second search starts at age `n+1`; its final trial
includes another 15 records. These are bounds in consumed history samples,
with no seconds or host-frame conversion. A held direction alone cannot
satisfy either press step. A release between identical direction presses is
implicit in normalized edge production, but the classifier does not match
an explicit release record or impose any extra neutral-duration condition.

No history-consumption or success-latch write occurs in the classifier or
the generic matcher. The classifier's scratch success bytes and ages are
rebuilt for each call; only the scratch allocator pointer is temporarily advanced and
restored. **Inference from the exact scan and lack of consumption:** the
same pair remains recognizable on later updates while its newer press stays
within ages 0..15 and the other conditions still hold. This is retained
recognition, not an independently queued attack. The translator rebuilds its
logical output on each update, and suppression can zero that output while
history continues advancing. If both direction groups qualify, comparison
uses the newer press's age, prefers the larger age, and preserves group 0 on
a tie; it does not compare the older press or total pair span.

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

Low direction bits `0x4/0x8` also have a proven consumer outside ordinary
action selection: resident `FUN_0020eae0` adjusts vertical velocity for the
awakened Gaara/Deidara branch. Its gates and constants belong to
[Awakening](../characters/awakening.md#resident-ownership-and-the-btl-boundary).

The active-fighter update in resident `FUN_0024fd80` calls this bridge at
`0x0025011C`, before input action dispatcher `FUN_00248ec0` at `0x00250140`;
the complete per-fighter order is owned by
[Combat action execution](combat_action_execution.md#ordinary-dispatch-order).

`FUN_00248ec0` snapshots fighter `+0x338` at `0x00248EE4`, processes the
Triangle logical bit `0x08000000` through `FUN_00225b60` at `0x002490F0`,
allows `FUN_0022b630` to rewrite the local mask at `0x002493F0`, and calls
`FUN_0023a390` with the resulting mask at `0x00249414`.

The `FUN_0022b630` rewrite is specific to the binding-2 history modifier
`0x00040000`. When fighter halfwords `+0x9F6` and `+0x324` differ, it clears
`0x00040000` and substitutes `0x00020000`; the base `0x00010000` then reaches
the special `0x02000000` action-signature variant below. When those halfwords
are equal, the current-action gates documented in
[Combat action execution](combat_action_execution.md#input-interruption-of-an-executing-action)
can instead accept `0x00040000` as a separate state transition. In that case
the helper returns 1 and leaves the
modifier itself set, but its final mask write clears `0x00010000`,
`0x00020000`, and low direction bits `0x1/0x2`; the caller invokes
`FUN_0022ba30`. Otherwise it returns zero without changing that modifier. This
proves the bit-level routing while leaving the transition's user-facing move
name unspecified.

That routine exposes an important ordering boundary. Before Triangle it passes
the snapshot to `FUN_00228320` at `0x002490D0`; that helper directly consumes
held-trigger logical `0x10000000`
([guard input lifecycle](chakra_and_guard.md#guard-input-and-action-lifecycle)).
After action-table selection, the possibly rewritten binding-2/Cross family
has parallel consumers: base `0x00010000` calls `FUN_0022f200` at
`0x00249434` ([jump requests](../stages/movement_and_physics.md#jump-requests-and-state-selection)),
native-Up modifier `0x00080000` calls `FUN_0022e760(fighter, 1)` at
`0x0024945C`, and native-Down modifier `0x00100000` enters the
`FUN_002302c0` / `FUN_0022e760(fighter, -1)` branch at `0x00249484` /
`0x002494EC`; the two modifiers' section-transfer requests belong to
[Section transfers](../stages/section_transfers.md#input-order-and-selected-action).
Their consumption occurs after, and in addition to, `FUN_0023a390`.

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

Within that ordinary direction branch, the first group is an ordered choice:
logical `0x10`, then `0x20`, then `0x40`, then `0x80`. The facing group
chooses `0x100` before `0x200`. Double-tap `0x400` takes priority over
`0x800`, replaces all direction groups with its signature as already
described, and additionally resets the selector mode to 0. Thus a double-tap
can switch an otherwise mode-1 request from the fixed-chain route into the
ordinary scan. Modes 2/3 never enter this branch and retain their existing
mode. These priorities are taken from `FUN_0023a390`'s branches rather than
inferred from the bit-to-signature mapping alone.

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

### Selection mode and eligibility windows

The selector mode is computed by resident `FUN_0023a0d0` before the input-mask
gate. It is not an input-history age. Its complete recovered return domain is
`-1, 0, 1, 2, 3`; its sole recovered direct resident caller is
`FUN_0023a390`. First, `FUN_00306a60(fighter)` searches the fighter's list at
`+0x8C4/+0x8C8` for an object whose ID word `+0x68` equals 0 or 1. A found
object forces mode 0. List ownership belongs to
[Battle entities](../session/battle_entities.md#common-fighter-owned-children); this
inspection does not assign those IDs a player-facing meaning.

With that bypass false, the branches are:

| Fighter state | Mode result and requirement |
| --- | --- |
| `+0xB00 == 0` | Mode 1 only for major 8, a current record with secondary `+0x14 & 0x380`, no category `+0x10 & 0xF00000`, and a non-null current payload whose first word has `0x10`; otherwise mode 0 |
| `+0xB00 & 0x100` | Mode 2 only when pending `+0xA3E == -1` and `FUN_00239250(other fighter, s16(+0xB0A)) != -1.0`; otherwise -1 |
| no `0x100`, but `+0xB00 & 0x400` | The same pending/progress gates, producing mode 3 or -1 |
| neither preceding bit, but `+0xB00 & 0x1000` | The same gates, producing mode 2 or -1 |
| other nonzero `+0xB00` | Mode 0 |

The priority is `0x100`, then `0x400`, then `0x1000`. A tested progress
value is stored at fighter `+0xB0C`, or zero on the `-1.0` result. The
successful `0x100` branch additionally clears the fighter's action-lock
block at `+0x248` (its stores span `+0x24A..+0x264`); this is a different
block from the `+0x224` rejection countdown that the exchange writers clear
([Extra Hit](extra_hit.md#receiver-response-and-exchange-limit)). Thus mode
calculation can change state even when the
subsequent input-mask gate rejects selection. `FUN_00239250` requires a
current phase payload and phase row, payload bit `0x2`, and a valid animation
unless payload bit `0x4` directly supplies 1. Its other result depends on
the row endpoint, requested interval, playback rate and cursor, including
the fractional cursor boundary. These are authored execution-window gates,
not a universal button-buffer duration; their execution ownership remains in
[Combat action execution](combat_action_execution.md#input-interruption-of-an-executing-action).

`FUN_00239e50(fighter, mode)` adds a separate entry gate. A nonzero signed
word `+0x254` rejects every major. With that word zero, its two jump tables
at resident `0x005C2B50/0x005C2B70` and branch instructions establish:

| Major `+0x18E` | Accepted substates/conditions |
| ---: | --- |
| 0 | Substate `+0x190` in `{0,3,4,5,7}` |
| 1 | Substate `0x0E..0x14`, inclusive |
| 2, 3, 4 | Accepted without an additional substate gate here |
| 5 | Substate `0x5B/0x5C`, or mode 2 for any other substate |
| 6 | Substate `0x60` with primary cursor `+0x1C4 >= 3`, or `0x5F` with cursor `>= 8`; all others reject |
| 8 | `FUN_002440c0 == 0`, equivalent here to the current record lacking category mask `0xC0000` (a null current record also returns zero) |
| all others | Rejected |

These cursor bounds count the action timeline, not command-history samples.
The additional `FUN_002455b0` gate can intercept logical binding-1 input for
paired state before ordinary selection; its paired-state execution is owned
by [Combat action execution](combat_action_execution.md#continuation-and-common-exit-decisions).

### Mode-bit producers and progress-interval lifetime

The high-byte receiving roles `0x100/0x400/0x1000` that select modes 2/3 are
written by Extra Hit role writer `FUN_00241F10`, which also writes the
opposite fighter's counter window `+0xB0A` from its exchange count `+0xB08`.
Receiver handler `FUN_002426C0` consumes those roles and discards a pending
counter at exchange count 15, and teardown `FUN_00243EF0` retires them. The
producer table, window formula, initialization and teardown are owned by
[Extra Hit](extra_hit.md#exchange-state-at-fighter-0xb00).

For selection, `+0xB0A` is only the interval argument passed to the opposite
fighter's `FUN_00239250` window calculation; it is not decremented, and
teardown clears neither it nor cached progress `+0xB0C`. A retained interval
therefore does not prove that a mode is still admitted: the mode-word and
pending gates apply first. `FUN_0023A0D0` can also leave the cached progress
untouched when it skips the progress call because a pending index already
exists. The roles are retired independently of the history ring.

### Pending-field width and bounded writer search

The pending selection at `+0xA3E` is one signed **16-bit** field. `+0xA3F`
is its high byte in the inspected little-endian layout, not a separately
established flag. The resident direct-offset search found no aligned byte
access at `+0xA3F`; it found 27 aligned halfword stores at `+0xA3E`.
This count includes initialization, input selectors, exchange consumption,
automatic selection and explicit clears; it does not imply 27 independent
selection algorithms. In particular, storing -1 writes `FF FF` across
`+0xA3E/+0xA3F`, while ordinary small nonnegative indices write high byte
zero. The action-entry and cleanup lifetime belongs to Combat action
execution, linked above.

The search covered the aligned resident block `0x00100000..0x0060737F`
with all four register-base encodings of `sw` at `+0xB00`, `sh` at
`+0xB0A/+0xA3E`, and `sb` at `+0xA3F`; each of these precise searches is
complete, and byte-mapped mirrors of the same instructions are not extra
writers. A broader `+0xB00` byte-pattern search is incomplete and supplies no
completeness claim. These bounds do not exclude adjusted-base aliases,
bulk/wider stores, computed pointers or overlay writers. The active producer
families were read in full rather than inferred from a matched immediate
alone.

The recovered pending writers outside the three input selectors have these
distinct contracts:

| Writer family | Pending-field effect |
| --- | --- |
| `FUN_00214A40`, `FUN_0021D200`, major-8 entry/cleanup | Initialize or clear to -1; execution entry/cleanup remain in Combat action execution |
| `FUN_0021D380`, `FUN_0021DAE0` | Replace, fill or clear pending through the retained direct-action chain; admission, cursor and consumption belong to [Battle AI](../session/battle_ai.md#action-record-selection-and-direct-queues) |
| `FUN_0021DDB0` | Recalculate cached progress, require empty pending and no attached-object bypass, build a category/secondary mask for exact exchange groups `0x100/0x400/0x1000` or mode-1 eligibility, then stage the first full-array match from `FUN_0021DF60` |
| `FUN_002260D0` | Clear pending only when its resolved record has category `0xF00000`; cancel staged amount/tier independently |
| `FUN_00226FA0` | Clear nonempty pending in its attached-object branch when fighter byte `+0x62 & 0x10` is clear |
| `FUN_00229B80` | Its internal state 7 clears the **other fighter's** pending field before its transition work |
| `FUN_0022BA30`, `FUN_002378F0` | Explicit clear following their common action-exit calls |
| `FUN_0023B280` | Stage a validated outcome-driven continuation; the existing execution owner describes its admission |
| `FUN_002426C0` | Discard at the exchange-count gate or consume through the paired mode producer described above |
| ID 49 channel 3 `FUN_00283A70` | Local action `0x22`, phase 0: resolve the pending companion/cost and replace the pending index with `0x23` if the cost predicate fails |

`FUN_0021DF60` requires `(category & requested_category) == requested_category`
and `(secondary & requested_secondary) == requested_secondary`, with secondary
request `0xFFFFFFFF` bypassing the latter comparison. These require all
requested bits, unlike the input chain scan's nonempty intersections. A zero
secondary request therefore accepts every secondary word here, while the
input chain scan's zero secondary mask rejects every candidate.
For its `param_4 == -2` call from `FUN_0021DDB0`, the local comparison
value simply remains -2: it does not read a record's continuation byte in
that negative-argument branch. Also, `FUN_0021DDB0` computes progress but
does not reject its -1 result before the mask/record scan. Its admission
must not be equated with input selector modes 2/3. It calls the mask builder
once before the full-array scan; the input fixed-chain path calls it for each
candidate. Where that builder draws from the PRNG, this placement changes
the draw count.

No direct resident caller or resident absolute pointer was found for
`FUN_0021D380` or `FUN_0021DDB0`. However, encoded JAL searches in
`/BTL.BIN` found 14 and five callsites respectively, so neither is a
resident-only dead-code conclusion. The queue callers belong to Battle AI's
linked census. The five `FUN_0021DDB0` calls are byte-confirmed at BTL
export addresses `0x006FBBC8`, `0x006FBC50`, `0x006FBCE4`, `0x006FBD1C`,
and `0x00704CC0`; their live callsites are each export address plus `0x40`,
while their resident target remains `0x0021DDB0`. They occur in AI states
12, 19 and 13 (two calls), and the main reaction stage. Their caller gates
belong to [Battle AI](../session/battle_ai.md#action-state-dispatcher). This closes
the recovered direct overlay call family without equating AI selection
with the input mode gate. `FUN_0021DAE0` has the proven resident input-dispatch
caller when `+0xB34 != -1`, meaning that a retained chain bypasses construction
of a fresh input signature in that call.

### Fixed-chain eligibility masks

`FUN_00239b00` zeroes both output masks before **each** candidate and calls
`FUN_00240c40` inside the ascending 10..18 loop. The resulting first mask
intersects candidate category `+0x10`; the second intersects candidate
secondary `+0x14`. The complete relevant outputs are:

| Mode/current record | Category mask | Secondary mask |
| --- | ---: | --- |
| 1, current record present | `0x1000` | Current secondary group `+0x14 & 0x380`: exact `0x80/0x100/0x200` becomes `0x400/0x800/0x1000`; any other combination gives zero |
| 1, no current record | zero | zero |
| 2 or 3, no current record | `0x2000` | If the other fighter's **low byte** `+0xB00` is nonzero, take its current record's exact `+0x14 & 0x1C00` value `0x400/0x800/0x1000`; otherwise zero |
| 2 or 3, current category `& 0xF000` equals `0x1000` or `0x2000` | `0x2000` for PRNG result zero, `0x4000` otherwise | Current record's exact `+0x14 & 0x1C00` value `0x400/0x800/0x1000`, or zero |
| 2 or 3, current category group equals `0x4000` | `0x4000` for PRNG result zero, `0x2000` otherwise | Same secondary rule |
| 2 or 3, any other current category group | `0x4000` | Same secondary rule |

The random helper is `FUN_00180210(3)`: its instructions preserve the bound
from `a0` in `t0`, call stateful generator `FUN_0017fd90`, then use unsigned
remainder modulo 4. The decompiler incorrectly omits that input argument;
the call and `divu` instructions establish the bounded `0..3` result.
Because the builder runs inside the candidate loop, qualifying current
categories draw again for each examined candidate. The scan does not choose
one category mask for its entire duration. This is a static algorithm result,
not an observed frequency or proof that every row is reachable.

Mode 1 has one pre-scan signature rewrite when the current record has category
`0x200` and secondary `0x80`: it clears signature `0x3000`, then adds `0x1000`
only when `FUN_00239250(fighter,-1) >= 0.75` and the incoming `0xC000` group
equals `0x4000` for nonzero `FUN_0023e3c0(fighter,0)`, or `0x8000` for zero.
Below that progress value its comparison sentinel is `0x000FFF00`, which
cannot equal the incoming masked `0xC000` group. Modes 2/3 instead remove
the candidate's and request's `0x000FFF00` group when the candidate uses it,
as described in the fixed-chain scan below.

Representative shipped bytes were read for all nine slots of Naruto ID 57,
Kazekage Gaara ID 59, and Deidara ID 64, at `0x004DA098..0x004DA38B`,
`0x004E4FA8..0x004E529B`, and `0x00500E78..0x0050116B`. Naruto and Deidara's
secondary fields are `0x480/0xA00/0x1100` for each consecutive three-slot
group; Gaara's are `0x2480/0x2A00/0x3100`. Mask `0x1C00` therefore selects
`0x400/0x800/0x1000` identically in these three variants; Gaara's extra
`0x2000` does not affect this mask intersection. This is a representative
secondary-field check, not a repeated whole-character census or a claim that
other secondary consumers ignore that extra bit.

### Secondary-word mutation after setup

The static `+0x14` values are not universally immutable. A bounded screen
of the seven callback slots in all 78 character definitions found the
following direct writer families. Channel numbers use the callback owner's
definition; its [dispatch census](../characters/character_action_callbacks.md#complete-bounded-classslot-census)
owns their installation and invocation. Unless stated otherwise, the
destination is the current record returned by `FUN_00217930(fighter,-3)`.
Local action indices below are hexadecimal.

| Character ID / callback | Local action and secondary-word effect | Instruction evidence |
| --- | --- | --- |
| 40 / channel 3 `FUN_00279EB0` | `0x19`, phase 0, secondary event 4: set `0x400000` for input ratio 1, otherwise clear it | `0x0027A6FC..0x0027A724` |
| 48 / channel 3 `FUN_00280FF0` | `0x2A`, phase 2: clear `0x40000` when the other fighter's signed byte `+0x63` is negative, otherwise set it | `0x00281BEC..0x00281C1C` |
| 58 / channel 3 `FUN_0029B430` | `0x2A`, primary event 0: set `0x100000` while signed count `+0x560C < 1`, otherwise clear it, then increment the count | `0x0029B83C..0x0029B864` |
| 64 / channel 3 `FUN_002B5250` | `0x2B/0x2C/0x2D`: set `0x8000` only with count `+0xB64 < 2` and outcome `+0xA40 == 1`, otherwise clear it. `0x17` restores the whole word from default-array `+0x7A0` | `0x002B57D0..0x002B57D8`, `0x002B6024..0x002B6270` |
| 64 / response `FUN_002B68F0` | `0x2C`: clear `0x80000`, then conditionally set it in its response-count branches | `0x002B6B00..0x002B6BAC` |
| 66 / channel 3 `FUN_002B9660` | `0x25`, primary event 0: clear `0x80000` while its signed character count is below 1, otherwise set it, then increment the count | `0x002BAB54..0x002BAB7C` |
| 67 / channel 3 `FUN_002BDF80` | `0x33`: primary event 0 toggles `0x80000` by signed count `+0x67FD < 1`, then increments it. `0x27` toggles `0x8000` with the count/outcome gate above. `0x29/0x1E` replace low bits `& 3` with 2; each inactive embedded record is reset to low value 1 | `0x002BE02C..0x002BE070`, `0x002BE7F4..0x002BE808`, `0x002BECD8..0x002BED20`, `0x002BEF18..0x002BEF2C`, `0x002BF7D0..0x002BF7F8` |
| 67 / response `FUN_002BF9A0` | `0x36`: clear `0x80000` while signed count `+0x67FC < 1`, otherwise set it; response argument 2 increments that count | `0x002BFFAC..0x002BFFD4` |
| 69 / channel 3 `FUN_002C4710` | `0x34`, primary event 0: clear `0x80000` while signed count `+0x69A4 < 1`, otherwise set it, then increment the count | `0x002C4FD4..0x002C4FFC` |
| 69 / response `FUN_002C55B0` | `0x25`: set `0x100000` while signed count `+0x69B0 < 2`, otherwise clear it | `0x002C590C..0x002C5934` |
| 76 / channel 3 `FUN_002D4C10` | `0x1E`: restore the whole word from default-array `+0x9EC`, then OR `0x800000` in phase 1 | `0x002D4F68..0x002D4F70`, `0x002D4FC8..0x002D4FD4` |
| 84 / channel 3 `FUN_002EE660` | `0x1D`, primary event 0: ratio 1 selects `0x400000`, ratio at least 0.5 selects `0x800000`, and a lower ratio clears both | `0x002EE9EC..0x002EEA74` |

All listed bitwise updates preserve the selector groups `0x380` and
`0x1C00`. That statement does not extend to whole-word restores. ID 64's
source is action `0x17` secondary word at `0x005012D0`, bytes
`05 01 00 00`, value `0x105`: its restore reinstates mode-1 group
`0x100` and sets group `0x1C00` to zero. ID 76's source is
`0x0054005C`, bytes `11 40 24 00`, value `0x244011`, reached through
default-array pointer `0x0053F670` at definition `0x005403CC`. Its restore
sets both selector groups to zero; the phase-1 OR preserves those zeros.
These are effects on the secondary gates only, not proof that the record
passes the mode, payload, category or state requirements.

ID 67's inactive-record writes use fighter `+0xBC`, adding `0xD74` or
`0x9D8` before accessing record `+0x14` (instructions
`0x002BE008..0x002BE070`). They therefore modify embedded actions `0x29`
and `0x1E` even when those actions are not current; treating every write
as current-record-only would miss this lifetime. The masked low-bit reset
still preserves both eligibility groups.

This screen establishes twelve direct callback writers, not every possible
action-array writer. It covered analyzed callback bodies and the full
instructions of the 49 entries without analyzed functions. It did not close
every called helper, adjusted-base
alias, virtual callback or bulk record copy. Timeline and response-counter
algorithms remain in the callback owner; this section owns the resulting
secondary-word changes and their selection consequences.

### Action-table source and setup

Resident `FUN_002151e0` copies the static character record into fighter
`+0x8C..+0x164`, stores record `+0x28` as counts `+0xA38/+0xA3A`, and takes
its action-array pointer from record `+0x30` when nonzero, otherwise from
`+0x2C`. It installs that pointer at `+0xA54/+0xA58/+0xA4C`. The table and
record ownership are documented in
[Character assets](../../game/character_assets.md#character-records).

The alternate pointer is zero in all 78 shipped static definitions, but this
does not imply selection runs against the static array. Character constructors
patch it before the common loader: for example Classic Naruto's
`FUN_00250c50` writes record `+0x30 = fighter +0x1150` before calling
`FUN_002151e0`. The pointer then selects the fighter's writable embedded
copy, populated by the setup described below.

That pointer alone does not describe the actions later scanned. Setup
`FUN_00219620`, called by the loader, rewrites the first four records using
the configured jutsu selectors at fighter `+0x184/+0x186`. Selector value 1
copies the null action record at `0x00407B90` into the corresponding pair.
Otherwise `FUN_00307eb0(selector)` gives the source character ID by shifting
right one, and the low selector bit determines whether source slots 0/1 or
2/3 supply the destination pair. Moving between pairs adjusts a nonnegative
continuation byte `+0x18` by two and rewrites nonzero direction-signature
group `0x000F0000` to `0x00010000` for the second pair or `0x00020000` for
the first. Thus the runtime records 0..3 can differ from the selected
character's shipped first four records.

Setup then copies slots 4 through `count-1` from the character's default
array (record `+0x2C`, fighter `+0xB8`) and specializes slots 4..9 using
fighter halfword `+0x188`:

| Configuration value | Retained slot |
| ---: | ---: |
| 0 / 1 / 2 | 4 / 5 / 6 |
| 4 / 5 / 6 | 7 / 8 / 9 |
| other | none |

For every other slot in 4..9 it clears category field `+0x10`, which makes
the special selector's `0x00F00000` gate fail. For the retained slot it replaces
display-name pointer `+0x08` through `FUN_00372ae0`, indexing the name table
at `0x005AEC40` with the side's configured ID. The generic scan's
highest-matching-index rule remains exact, but after this setup at most one of
these six slots retains its category flags. Character-specific changes after
setup require their own evidence; the six shipped entries must not be assumed
simultaneously eligible.

Later resident `FUN_002449c0` rewrites category, display-name pointer, and
cost in slots 4..9, retaining one selected slot or disabling all six. Its
write loop does not replace input signature `+0x1C` or continuation
`+0x18`: the reusable selector still matches those fields, while cleared
categories fail its eligibility gate. Tier, class, selected-record metadata,
and the exact write loop belong to [Ultimate Jutsu](../characters/ultimate_jutsu.md).
This is a confirmed post-setup mutation, so the static census does not imply
that eligibility, names, or costs remain equal to the shipped array.

The final setup calls also alter other fields. `FUN_00218fe0` converts record
`+0x50` from a `0x4C`-row index into a pointer; slots 0..3 instead use fixed
row indices 0, 4, 6, and 10. `FUN_00218d30` resolves sentinel float
`-17320.508` (`0xC6875104`) at `+0x34/+0x38` when the record's category and
secondary gates allow it, using its continuation chain and associated row
data, or fighter `+0x124` for category bit `0x2`. These transformations are
another reason that shipped threshold values are not necessarily the values
seen by selection and validation.

### Complete static action-data census

The 94-row definition table occupies resident `0x005A2900..0x005A2BEF`.
Its 78 distinct nonzero definition pointers select 3,444 action records.
Four auxiliary definitions (IDs 26, 29, 30, and 31) have only four records;
the remaining 74 definitions have 37..62 records, totaling 3,428. Repeated
definition rows were counted once. Every array was read in full.
Character-definition and resource ownership stay in
[Character assets](../../game/character_assets.md#character-records).

All 74 full fighter definitions share the following selection fields. This
table asserts equality only for the four displayed fields, not all 84 bytes
of each record:

| Slot | Category `+0x10` | Signature `+0x1C` | Continuation `+0x18` | Cost `+0x20` |
| ---: | ---: | ---: | ---: | ---: |
| 7 | `0x00100000` | `0x00100112` | -2 | 5 |
| 8 | `0x00200000` | `0x00100112` | -2 | 10 |
| 9 | `0x00400000` | `0x00100112` | -2 | 15 |
| 10 | `0x00001000` | `0x00101011` | -2 | 0 |
| 11 | `0x00001000` | `0x00100211` | -2 | 0 |
| 12 | `0x00001000` | `0x00100411` | -2 | 0 |
| 13..15 | `0x00002000` | `0x00101011` | -2 | 0 |
| 16..18 | `0x00004000` | `0x00101011` | -2 | 0 |
| 19 | `0x00000002` | `0x02000011` | -1 | 0 |
| 20 | `0x04000000` | `0x02000011` | -1 | 0 |

Slots 4 and 5 normally have the same signatures, continuation, and costs as
7 and 8, and category `0x00100000/0x00200000`. Their category is instead
zero for exactly IDs `47,48,49,50,51,52,54,55,56,73`. Slot 6 has category
`0x00400000`, continuation -2, and cost 15 for every full fighter definition;
its signature is `0x00100111` for exactly IDs `19,48,61`, and `0x00100112`
otherwise. These are complete shipped-data exceptions, before common setup
clears unselected slots.

Slot 21 is category `1`, signature `0x00100012`, and continuation -1 except
for ID 53 (`0x004C5764`: category 1, signature `0x00100212`, continuation
-1) and ID 70 (`0x005252D4`: category 0, signature `0x00110012`, continuation
-2). A universal first-ordinary-action assumption therefore fails even before
later character-specific changes.

Among slots 20 and above, the signature's high family mask `0xFFF00000`
has this complete distribution: `0x02000000` in 74 records,
`0x00100000` in 1,627, `0x08000000` in 209, `0x00200000` in 16,
`0x00400000` in 11, and `0x00800000` in 11. The two hold/release families
occur only in IDs `40,48,53,54,57,64,77,84,85`; ID 53 contributes three
pairs and each other ID one. Presence of a signature does not itself enable
the synthesis gate or satisfy the action-state validator. Nor does this
count label the `0x08000000` records as a direct button contribution: that
family is not built by the direct mapping in `FUN_0023a390` above.

All 3,444 debug-name pointers at `+0x00` point to empty resident string
`0x006031F0`. Display names at `+0x08` instead refer to 1,064 distinct
nonempty Shift-JIS strings or that same empty string. The exact named
examples below omit only the renderer's `<r...|...>` reading markup:

| Definition / slot | Record address | Signature | Continuation | Display string pointer / text |
| --- | ---: | ---: | ---: | --- |
| Naruto, ID 57 / 24 | `0x004DA530` | `0x00100211` | 23 | `0x004D9B90`: `飛影昇撃` |
| Naruto / 25 | `0x004DA584` | `0x00104011` | 23 | `0x0040C9E0`: `特攻蹴撃` |
| Naruto / 35 | `0x004DA8CC` | `0x00800112` | 34 | `0x004D9C80`: `風魔追撃` |
| Kazekage Gaara, ID 59 / 44 | `0x004E5AD0` | `0x00100012` | -1 | `0x004E4BB0`: `漠撃・圧葬` |
| Kazekage Gaara / 45 | `0x004E5B24` | `0x00100212` | -1 | `0x004E4BE0`: `漠撃・滅葬` |
| Kazekage Gaara / 46 | `0x004E5B78` | `0x00104012` | -1 | `0x004E4C10`: `漠撃・天葬` |
| Kazekage Gaara / 47 | `0x004E5BCC` | `0x00100412` | -1 | `0x004E4C40`: `豪砂甚雨` |
| Deidara, ID 64 / 29 | `0x005014B4` | `0x00800112` | 28 | `0x00500930`: `起爆粘土・蜘蛛` |
| Deidara / 42 | `0x005018F8` | `0x00100012` | -1 | `0x00500930`: `起爆粘土・蜘蛛` |
| Deidara / 43 | `0x0050194C` | `0x00100212` | -1 | `0x00500AA0`: `大型鳥粘土・翔` |
| Deidara / 44 | `0x005019A0` | `0x00100412` | -1 | `0x00500AD0`: `大型鳥粘土・襲` |
| Deidara / 45 | `0x005019F4` | `0x00104012` | -1 | `0x00500B00`: `大型鳥粘土・突` |

Naruto's full source array is `0x004D9D50..0x004DAD63` (49 records),
Gaara's is `0x004E4C60..0x004E5C1F` (48), and Deidara's is
`0x00500B30..0x00501A47` (46). All named rows in the table have category 1
except Naruto slot 35 and Deidara slot 29, which have category `0x10`.
The additional Gaara and Deidara entries establish static alternatives with
no predecessor requirement. Their working-array category switches were
corroborated in `FUN_0029c1e0` and `FUN_002b49c0`: disabled rows have zero
category and fail the ordinary selector's nonzero-category gate. Enabled
rows still require signature, continuation, state, and dispatch validation.
Constructor disabling, activation, deferral, and restoration gates belong to
[Awakening](../characters/awakening.md#deidara-and-gaara-character-variants).

### Command List and action chart

The battle Command List and the character move chart present bindings and
action records; they do not take part in input interpretation. The chart
derives its rows from the fighter's current action arrays through
`FUN_00217930`/`FUN_00217990`, not from the two static `ccCommand` sequences,
and its display scan is not the action-state validator. Both displays, their
binding-to-token rules, renderers and native text are documented in
[Battle Command List and move chart](../../localization/ui/battle/command_list_and_move_chart.md).

### Ordinary signature matching

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
`FUN_00244190` to validate it. Only return zero causes the outer retry:
constructed signature bits `0x000F0000` are cleared and selection repeats.
Every nonzero return, including -1, reaches `FUN_0023a9a0`. The latter
checks the same validator again: zero rejects dispatch, 2 or 3 invoke
`FUN_002445d0` before proceeding, and 1 or -1 proceed without that call.
Raw branches at `0x0023AA88..0x0023AAE8` explicitly accept -1. Thus -1 is
not rejection at this boundary: the validator returns it when masked category
`+0x10 & 0x000F0000` is outside its four handled single-bit cases, or when its
`0x10000/0x20000` case cannot find the required chained companion. This is
an acceptance-by-caller fact, not proof that downstream gates cannot reject.

### Pending selection and priority boundaries

The selectors retain one signed-halfword pending index at fighter `+0xA3E`,
not an input event or a queue. Ordinary mode-0 continuation selection normally
requires major 8, current payload bit `0x10`, candidate continuation
`+0x18 == current index +0xA3C`, and normalized signature equality. Candidate
continuation -2 takes the current index only for candidate category mask
`0x000F0000`; this branch rejects a missing current record or current category
`0xF000`, and enables staging when the current record lacks `0x000F0000`.
The alternate `FUN_0023bf80` predicate can route an active major-8 fighter
through immediate selection instead: it requires current category bit `0x2`,
halfwords `+0x9BA == 3`, `+0x9BC == 2`, and `+0x9C2 >= 5`.

Neither ordinary mode-0 staging nor jutsu staging checks that `+0xA3E` is
empty before writing it. The deferred mode-1/2/3 route does check emptiness,
and its first qualifying 10..18 slot wins. Modes 2/3 can reject even earlier
in mode calculation when a pending index exists. Therefore these branches
have different overwrite rules; a single universal first-input-wins rule is
not supported.

The special selector is called first, but a major-8 jutsu match writes the
pending slot and returns -1. `FUN_00239530` then continues to its ordinary,
deferred, or fixed-slot branch. An ordinary mode-0 match can overwrite that
staged slot, whereas the deferred route sees it occupied and skips its scan.
The fixed-slot-19 branch remains a separate immediate route. These are proven
function-level orderings; this inspection does not establish simultaneous
reachability of every competing match in a shipped configuration.

The complete special-admission helper `FUN_00244EA0` narrows that boundary.
It rejects nonzero fighter byte `+0x168`, nonzero `FUN_003073A0`, nonzero
signed halfword `+0x84`, **any nonzero `+0xB00`**, and an executing record
whose category contains `0xF00000`. Its zero-mode-word branch and the
full-word load at `0x00244EF8..0x00244F0C` are instruction-confirmed.
Therefore jutsu staging cannot compete with the input modes 2/3 in this
unchanged call chain: those modes require a nonzero mode word. For mode 1,
a major-8 special match occupies pending before the deferred scan, which
then skips. For mode 0, the ordinary branch can still overwrite a staged
special match if its separate continuation/signature gates pass. These are
admission exclusions and conditional priority, not an exhaustive census of
reachable simultaneous matches.

The selection functions do not attach an age, expiry counter, or captured
direction to the pending slot. Pending execution, replacement through action
entry, interruption and cleanup belong to
[Combat action execution](combat_action_execution.md#continuation-and-common-exit-decisions).
That owner's execution gates must be applied before inferring an action
from a pending index. History retention, logical output suppression, and
pending-record lifetime are separate boundaries.

### Representative ordinary attack path

With default bindings, a new Circle press creates logical `0x00001000` and
`0x40000000`. `FUN_0023a390` converts the former to action-signature bit
`0x00100000`. With selector mode 0 and no immediately returned special
action, `FUN_00239530` takes the ordinary ascending action-record scan
described above. The accepted record
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
indices 4 through 9 as the jutsu-class action slots. Their shipped fields,
complete exceptions, and common setup's one-slot specialization are documented
above; their retained display name comes from the configured name table rather
than the shipped empty slot name. Ultimate-Jutsu behavior is covered in
[Ultimate Jutsu](../characters/ultimate_jutsu.md).

State entry through `FUN_00217e40` is owned by
[Combat action execution](combat_action_execution.md#action-entry-and-state-ownership).

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
  output fields; resident bridge; action-record stride and dispatch call chain;
  system-context history divisor; complete static action-data census and its
  selection-field exceptions; common action-array setup; constructor input
  settings; interval lifetime for selection; pending-field width and bounded
  writer families; special-mode
  admission exclusions; and the twelve checked callback flag writers.
- **Supported:** semantic names for the two relative-angle fields and the
  jutsu-class label for indices 4 through 9. Their data flow is exact, while
  the names follow their consumers rather than exported symbols.
- **Unresolved:** user-facing compass names for the object-relative direction
  selectors, the dormant producer/meaning of object `+0x8C/+0x90`, the
  designer's intended history duration, mode-0 simultaneous competing matches,
  and eligibility changes outside the stated direct-store and callback bounds.
  Static record contents and named examples are
  established; complete visible command sequences are not.
- The clean static `ccCommand` data contains only two two-step cardinal
  double-tap tables. No general attack-string table was found there.
- The count-across-window helper has no direct caller beyond its binding
  wrapper. That wrapper has no in-overlay caller but has the proven resident
  multi-press caller `FUN_0024ccd0`.
- Jutsu selection is a resident action-table path mediated by staged fighter
  state, not a hidden third `ccCommand` sequence.
