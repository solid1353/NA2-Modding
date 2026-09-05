# Battle support mechanics

This note reconstructs the resident/BTL boundary for ordinary battle support
characters in clean NA2. It covers ownership, request gates, the support gauge,
per-side selection state, the active-object lifecycle, and teardown. It does not
cover support-specific combat behavior, battle AI, action-command matching,
projectiles, generic entity registries, statuses, damage scaling, outcomes,
Practice, or Adventure.

## Research coverage

- **Assigned scope:** this lane was limited to ordinary BTL/resident team and
support-character mechanics: ownership, pre-battle support selection, manual
summon/re-request gates, gauge-backed availability, manager/object update
lifecycle, and teardown.

- **Exploration depth:** the work was static against the exact clean
images identified below. Coverage was:

- a bounded resident call-graph trace through fighter initialization
  `FUN_002151E0`, the normal manual-request/update chain
  `FUN_00238340` / `FUN_00238540` / `FUN_00238600` / `FUN_00238720`, its
  `FUN_0024DA50` caller, and subsystem entry/transition/dispatch functions
  `FUN_001EC7A0`, `FUN_001EC890`, `FUN_001EDD10`, `FUN_001EDB00`, and
  `FUN_001F03E0`;
- an exhaustive clean-BTL reference/store audit for singleton pointer
  `0x00607888` and manager active slots `+0x04/+0x08`, plus bounded raw
  instruction traces of the manager wrappers and core functions at live
  `0x00885210..0x008854D0`, `0x00886950`, and
  `0x00886BB0..0x00887990` (these are listed functions, not a claim that every
  byte in the enclosing numeric intervals was analyzed);
- exhaustive row decoding of the 62-by-8 candidate table at raw `0x21E790`,
  the 66-by-3 support-code table at raw `0x21DB50`, the 912-by-3 recharge-class
  table at raw `0x21DCB0`, and both 66-entry pointer tables at raw `0x21EC30`
  and `0x21EE50`; the direct-call audit of the candidate resolver covered all
  seven BTL and fourteen resident direct call sites;
- a bounded factory/vtable audit covering all 14 final vtables produced by the
  clean factory and their common or overriding slots `+0x10`, `+0x1C`,
  `+0x24`, `+0x40`, `+0x48`, `+0x50`, and `+0x58`, followed through common
  lifecycle routines at live `0x00887FD0`, `0x00888720`, `0x00888FE0`,
  `0x008890A0`, `0x008890D0`, `0x00889540`, `0x00889C10`, `0x0088A7C0`, and
  `0x0088A890`; and
- a bounded teardown trace from the resident wrappers through manager
  deleting destruction, all-slot clear, terminal-byte advancement, virtual
  deletion, and owner-slot clearing. The six per-side BSS halfwords at live
  `0x008DCE90` were reference-audited only far enough to exclude them from the
  request, gauge, terminal test, and teardown gates.

- **Confirmed coverage:** the documented facts establish a two-side
manager with one active object per side; deterministic setup-time selection
with candidate `0` used for the actual `0x26` replacement; one resolved object
code and recharge class per side; exact resident input, gauge, and global
request gates; recharge/drain arithmetic and ordering; the object-local active
re-request latch; all clean request return states; the three scheduled manager
passes; the common zero-gauge-to-terminal chain; identifier allocation and BSS
bookkeeping boundaries; and both natural and enclosing-subsystem teardown.
Useful negative results include no runtime rotation among three candidate
members, no second ordinary-support slot, and no independent resident cooldown
counter in the audited path.

- **Unresolved or untested:** this is not exhaustive coverage of every support
subclass. The specialized combat bodies behind the audited vtable overrides,
the conditions that set object byte `+0xF1` or return every class to the open
re-request pair, the battle meaning of unresolved manager/global predicates,
the UI name of side-record selector `+1`, the semantic meanings of the second
and third BSS halfwords, and caller-specific meanings of auxiliary signed gauge
deltas remain unresolved. No character names were mapped to numeric IDs.

- **Deliberate exclusions and overlap:** battle AI, action-command matcher internals,
projectile internals, generic entity registries, statuses, damage scaling,
combat outcomes, Practice, and Adventure were excluded. Those areas were not
used to fill gaps or assign names here; overlap was stopped at the proven
support-owner interfaces described in this document.

- **Evidence limitations:** raw bytes, direct-call encodings, table dimensions,
slice hashes, address arithmetic, and IEEE-754 single-precision update counts
were mechanically checked against the clean files. No live-memory capture or
runtime request trace was performed in this lane. Consequently update ordering
and invocation counts are static facts, while wall-clock durations, visible
animation timing, scheduler frequency, and runtime behavior of unreachable or
extreme allocator states remain unvalidated.

## Evidence identity and address conventions

The clean resident and BTL inputs and their address conversions are defined in
[Standard game file identities](../game/files/file_identities.md). The
maintained names are synthetic Ghidra labels, not original symbols.

Evidence used here is the maintained Ghidra C/listing export, checked against
raw clean-file bytes where the omitted header caused missed or split functions.
No runtime capture was used, so timing is stated in update calls rather than
seconds.

## Ownership model

Support state is split across three owners:

1. The resident global pointer slot at live `0x00607600` holds the battle setup
   object that supplies the selected-side records. The resident fighter object
   owns the gauge and request input.
2. A BTL-owned `0x24`-byte two-side manager is heap allocated. Its pointer is
   held in the resident/global slot at live `0x00607888` (`gp - 0x3168`; the
   export calls it `iGpffffce98`).
3. The manager owns at most one active support object per side. Those two
   pointers are manager `+0x04` and `+0x08`.

This is a direct two-side owner, not a scan through the game's generic entity
population. The manager constructor at BTL live `0x00886CB0` (raw `0x1D2DB0`,
export `0x00886C70`) clears both active-object pointers and initializes two
three-byte side records at `+0x0C` and `+0x0F` to `{0, 1, 0}`. Manager `+0x14`
is an embedded identifier allocator: its word `+0x18` begins at `1` and its
byte `+0x1C` begins at zero. Byte `+0x20` is a one-shot pass-1 flag and begins
at `1`.

A raw-store audit of the manager region, cross-checked against every BTL
reference to the singleton, found only four active-slot mutation paths:
constructor clear (the loop store is live `0x00886D0C`, raw `0x1D2E0C`), a
successful request store (live `0x008876C8`, raw `0x1D37C8`), pass-1 terminal
clear (live `0x00887160`, raw `0x1D3260`), and the shared explicit delete/clear
routine. Other singleton references read a slot or side metadata; they do not
install or replace an active object. This bounds the one-object-per-side owner
claim to the complete clean BTL reference set rather than one decompiled
function.

The side record fields currently established are:

| Side-record byte | Proven use |
| --- | --- |
| `+0` | Support color variant `0..2`. Battle setup derives it from the two selected support identities, the two primary-fighter identities, and the primary fighters' color indices. A support object's resource path reads this byte; nonzero variants `1` and `2` request an alternate resource through virtual `+0x68`. |
| `+1` | Request/input selector. It is initialized to `1`, read by BTL live `0x00882630`, and written by live `0x00882670`. When an active support object exists and the fighter's packed role is zero, the resident request handler uses value `1` to select input mask `0x40000000`; every other value selects `0x20000000`. Other packed roles use `0x20000000` without reading this selector. |
| `+2` | Recharge-rate class. Fighter construction maps values `0..4` to `0.8, 0.9, 1.0, 1.1, 1.2`; any other value falls back to `1.0`. |

The byte getter at live `0x00882630` is raw BTL `0x1CE730`. It lies in an
undefined gap in the preserved export, whose corresponding display address is
`0x008825F0`. Raw instructions prove that it returns
`manager[0x0D + side * 3]`. The writer at live `0x00882670` is raw `0x1CE770`
(export `FUN_00882630` at `0x00882630`) and stores the supplied byte to that
same field. This raw-byte check avoids confusing the writer with the getter.
Neither helper is null-safe: when the singleton is absent, each forms a zero
record pointer and then reads or writes byte address `1`. Their traced callers
therefore rely on manager creation order; manager absence is not represented by
a harmless selector value.

The selector is also round-tripped by a paired BTL parameter snapshot/restore
path. At live `0x00881070` (raw `0x1CD170`, corresponding export address
`0x00881030`), the reader takes the side index from setup-object word `+0x18`
and saves the selector in local-record byte `+0x7C`. The sole direct call to
the writer is at live `0x0088126C` (raw `0x1CD36C`, corresponding export
address `0x0088122C`); it restores that local byte for the same setup-derived
side. This establishes the byte as preserved battle-parameter state, but does
not establish a menu or UI label for it.

## Setup and selected support

Resident `FUN_001F4DD0` finalizes the two player records and calls BTL live
`0x00886250` (raw `0x1D2350`, export `FUN_00886210` at `0x00886210`). That BTL
routine consumes the two `0x28`-byte side records rooted in the resident battle
setup object. The selected support-list ID is the word at side-relative
`+0x68`; the resolved support code later consumed by the support-object factory
is the byte at side-relative `+0x6C`.

The setup routine resolves the special selection value `0x26`, derives the two
side-record `+0` color variants, and maps each side's selected support data into
side-record `+2`. This proves that the manager's per-side metadata is chosen
before fighter construction and that the fighter's recharge multiplier is
selection-derived.

Special value `0x26` is resolved deterministically, not by a random-number
call. BTL live `0x00885C30` (raw `0x1D1D30`, export `FUN_00885BF0` at
`0x00885BF0`) first canonicalizes the primary-fighter identity with resident
`FUN_001F7E70`, then scans 62 unique eight-byte records at encoded live
`0x008D2690`, raw `0x21E790` (length `0x1F0`, slice SHA-256
`6BAF266E15ECBF6F95B17DDFBE8A65AF3C1900C4153404F5936F1EC9C9CF4977`).
Each record is `[s32 primary identity, candidate 0, candidate 1, candidate 2,
zero pad]`. Known callers supply candidate indices `0..2`; battle setup uses
index `0`. The helper returns `0` if the primary identity has no row.

The complete clean direct-call set makes the distinction sharper. All seven
BTL calls and three of fourteen resident calls pass constant index `0`. Each
of the other eleven resident calls is inside a loop bounded by `index < 3` and
uses candidates `0..2` only in equality tests against another selection. No
BTL caller requests candidate `1` or `2`, and neither the request handler nor
the manager calls this resolver at all. Thus candidates `1` and `2` participate
in resident selection validation/comparison, while the battle setup's actual
`0x26` replacement is candidate `0`; they are not three runtime summon slots.

All candidate bytes in the clean table are support-list IDs `0..33`, so the
setup branch that calls the helper again if its first result is still `0x26`
cannot be reached from this table. As with the other encoded data pointers,
Ghidra's same-number `0x008D2690` label lands `0x40` after the raw table.

The concrete support-object code is selected through 66 three-byte records at
encoded live `0x008D1A50`, raw `0x21DB50` (length `0xC6`, slice SHA-256
`25D4DC03376390ED930A47CF1611DBD990CAFAAD38AD6EFF02963793EB9A247C`).
Each record is `[support-list ID, primary-fighter ID or 0xFF, object code]`.
There is one wildcard-primary record for each support-list ID `0..33`; 32 later
primary-specific records override their earlier wildcard because the scan does
not stop at the first match. The input pairs are unique and object codes span
`0..65` exactly once each.

The resulting object code is written to side-relative `+0x6C`, except that
code `49` is normalized to `0`. Two independent raw paths establish this rule.
The resolver passes its result through BTL live `0x00885880` (raw `0x1D1980`,
corresponding preserved-export address `0x00885840`, where no function was
recognized). That helper accepts only codes `0..65` and dispatches through 66
encoded-live pointers at `0x008D2B30`, raw `0x21EC30`: indices other than `49`
target live `0x008858B0` and return zero, while index `49` targets live
`0x008858B4` and returns one. Its callers replace a nonzero-tested code with
zero. Independently, the setup routine's jump table at encoded live
`0x008D2D50`, raw `0x21EE50`, points code `49` to live `0x00886410` and all
other codes `0..65` to live `0x00886400`, again selecting a zero result only
for code `49`. A missing resolver match reaches an explicit store through
address zero rather than a graceful unavailable result. The Ghidra data labels
with the same numeric addresses refer `0x40` later than these raw tables and
must not be used to read their contents.

The sole mapping row that produces code `49` is numeric record
`[support-list ID 23, primary 0xFF, code 49]`, and ID `23` has no
primary-specific override. It therefore always normalizes to object code `0`
in the clean table; support-list ID `0` independently maps directly to code
`0`. No character names are inferred from these numeric IDs.

Recharge class uses a separate 912-record table at encoded live `0x008D1BB0`,
raw `0x21DCB0` (length `0xAB0`, slice SHA-256
`FDD36E924D53D38C035A33624AFE88661C243F02B173C0A0AF67C7BB2B421875`).
Each unique record is `[support-list ID, primary-fighter ID, class]`; there are
no wildcard IDs or duplicate input pairs. Lookup begins at class `2` and an
exact pair overrides it. The table contains only class `0` (475 records),
class `1` (46), class `3` (293), and class `4` (98), so `2` is exclusively the
default for pairs absent from the table.

The color resolver is one continuous raw function at BTL live `0x00885CE0`
(raw `0x1D1DE0`, export start `FUN_00885CA0` at `0x00885CA0`). The preserved
export incorrectly splits its zero-fill loop at display `0x00885CE0`, exactly
where an encoded live call target lands. With sides `0` and `1`, it first sets
both support variants to zero, then applies these rules in order:

```text
if support_identity[0] == primary_identity[1]:
    support_variant[0] = (primary_color[1] + 1) % 3
if support_identity[1] == primary_identity[0]:
    support_variant[1] = (primary_color[0] + 1) % 3
if support_identity[1] == support_identity[0]:
    support_variant[1] = (support_variant[0] + 1) % 3
```

Primary identities first pass through resident `FUN_001F7E70` when that
resolver returns a value other than `-1`. The source color words are the battle
setup side fields `+0x54` and `+0x7C`. Their meaning is independently fixed by
the character-select path: it copies each selector object's color field into
those words and increments the second modulo three when both sides select the
same resolved primary identity and color. The selected support IDs likewise
pass through the BTL support-identity resolver before the comparisons above.
Thus side-record `+0` is a collision-resolved support color, not another active
object slot or a cooldown field.

Only the resolved byte at side-relative `+0x6C` selects the support-object
implementation during a field request. The factory rejects values `>= 0x44`.
Because the clean mapping above produces each code `0..65` exactly once, this
range rejection is not an ordinary clean-selection availability gate; it
requires noncanonical or corrupted resolved state.
For accepted values it chooses one of several specialized object sizes and
constructors; no speculative character or class names are assigned here.
The common initialization interface receives `(object, resolved code, side)`.
Its implementation at BTL live `0x00887FD0` (raw `0x1D40D0`, export
`FUN_00887F90` at `0x00887F90`) stores the side byte at object `+0xE4` and the
resolved code byte at object `+0x60`. Subsequent owner-fighter lookups use that
stored side, rather than reselecting a team member from a global registry.

### Request-time side and member selection

The support choice is fixed before fighter construction. At request time the
resident handler derives only a side index from `fighter[+0x60] & 1`; the BTL
manager then addresses exactly `active[side]` and battle-setup
`resolved_code[side]`. If that slot is populated, it calls the existing
object's virtual `+0x24` query. It neither rotates through candidate slots
`0..2` nor replaces the object with another candidate.

The packed fighter role `((u16 fighter[+0x60] & 0x1FF) >> 5)` affects the input
mask for an occupied slot, as detailed below. Manager side-record `+1` selects
Circle versus R1 only for packed role zero; it does not select a support-list
ID, object code, color variant, or second manager slot. No request-time scan of
multiple support team members exists in this ownership path.

## Gauge state and availability

The resident fighter owns these support fields:

| Fighter offset | Meaning | Evidence |
| --- | --- | --- |
| `+0x74` | Gauge, clamped to `[0.0, 1.0]` | Initialized to `1.0`; read by the request gate; updated by `FUN_00238600`, `FUN_00238720`, `FUN_00238830`, and `FUN_00238950`. |
| `+0x78` | Recharge multiplier | Initialized once from manager side-record `+2` by `FUN_002380C0`; a missing manager or unrecognized class yields `1.0`. |
| `+0x338` | Current input-bit field | Tested by the request handler. |

Fighter setup `FUN_002151E0` supplies `1.0` to the clamped gauge setter at
live call `0x00215530`, then calls the recharge-class resolver at live
`0x0021553C` and stores its result to `+0x78`. A clean-resident direct-call
scan finds no other callers of either initialization helper. Later gauge
changes use the update/delta writers below rather than rerunning selection.

Resident `FUN_00238540` runs immediately after the support request handler in
the normal fighter update. The enclosing update reaches both calls only while
fighter byte `+0x00` has flag `0x02` set. Within that outer invocation,
`FUN_00238540` updates the gauge only while fighter `+0xB00` is zero, fighter
`+0xB10` is zero, and the resident global gate reached through `0x00607654 ->
+0x08 -> +0x14` is null.

The update rule is exact per invocation:

```text
if manager.active[side] == null:
    gauge = clamp(gauge + recharge_multiplier / 450.0, 0.0, 1.0)
else:
    gauge = clamp(gauge - 1.0 / 300.0, 0.0, 1.0)
```

Crossing upward to full in the no-active-object path can emit resident event
`0x2D`, subject to the fighter-role and global gates in `FUN_00238600`.
`FUN_00238830` and `FUN_00238950` can also apply a caller-supplied signed delta,
but only while no active support object exists; they use the same clamp. Their
caller-specific reasons are outside this note.

No separate resident cooldown counter was found in this traced path. For an
empty slot, availability uses the normalized fighter gauge and `0.5` is an
entry threshold. An active re-request bypasses that threshold but has the
object-local `+0xE6/+0xE8` latch documented below. Drain versus recharge still
depends only on slot presence, even while that active-request latch is closed.
The request does not directly subtract `0.5` or reset the gauge: an active
object drains it on subsequent updater calls. When a request creates an object
in the normal fighter update, the immediately following updater sees the
populated slot and applies the first `1.0 / 300.0` drain in that same outer
invocation if its gates still pass. Conversely, an object notification or
terminal-state byte does not by itself select recharge: the updater continues
to choose drain until the owning manager slot is actually cleared. This is a
static fact about these writers, not a claim about the visible duration of
every specialized support object.

The following counts are a derived IEEE-754 single-precision reproduction of
the clean operations, starting from exactly `0.0` for recharge or exactly
`1.0` for drain. They are not runtime timing measurements:

| Class | Multiplier | Recharge invocations to `>= 0.5` | Recharge invocations to clamped `1.0` |
| ---: | ---: | ---: | ---: |
| `0` | `0.8` | 282 | 563 |
| `1` | `0.9` | 250 | 501 |
| `2` | `1.0` | 226 | 450 |
| `3` | `1.1` | 205 | 410 |
| `4` | `1.2` | 188 | 376 |

Starting from `1.0`, the active drain reaches clamped `0.0` on invocation 301.
The one-invocation differences from ideal real-number division are float32
accumulation effects. In the normal fighter update the request handler runs
before the gauge updater, so crossing `0.5` in an updater call can only satisfy
a later request-handler call. Any frame in which the outer gates suppress the
updater does not advance these counts.

Gauge exhaustion is a notification, not an immediate owner-side free. The
resident gauge getter at live `0x00238070` (file `0x138170`) is a three-
instruction leaf that returns fighter `float +0x74`. One support-object state
routine at BTL live `0x00889C10` (raw `0x1D5D10`, export `FUN_00889BD0` at
`0x00889BD0`) calls it for the owning side; when the result is exactly `0.0`,
the routine invokes that object's virtual `+0x48` with argument `3`. It does
not clear the manager slot.

The request factory can leave 14 distinct final object vtables. All 14 put the
state routine above in slot `+0x50`. Nine map virtual `+0x48` directly to BTL
live `0x00889540` (raw `0x1D5640`, export `FUN_00889500` at `0x00889500`);
the five specialized overrides call that same common handler first. It records
the supplied reason at object `+0xE6` and resets its internal state, but does
not write terminal byte `+0xF2` or the manager slot. Thus zero gauge reaches
the common reason-`3` handler for every clean factory class.

The later route is also common. The scheduled update dispatches state byte
`+0xE6 == 1` through virtual `+0x50`, where the zero-gauge test occurs; after
reason `3` is recorded, a later enabled update dispatches `+0xE6 == 3` through
virtual `+0x58`. All 14 final vtables map `+0x58` to BTL live `0x0088A890`
(raw `0x1D6990`, export `FUN_0088A850` at `0x0088A850`). When object halfword
`+0xE8` is zero and byte `+0xF1` is nonzero, that handler invokes virtual
`+0x40`, the common terminal setter below. If either condition is false, that
invocation does not request terminal state.

All 14 vtables map virtual `+0x40` to the terminal setter at BTL live
`0x008890A0` (raw `0x1D51A0`, export `FUN_00889060` at `0x00889060`), which
writes object byte `+0xF2 = 1`. Twelve map scheduled virtual `+0x10` directly
to BTL live `0x00888720` (raw `0x1D4820`, export `FUN_008886E0` at
`0x008886E0`); the two overrides call that common update first. With
`+0xF2 == 1`, it advances the byte to `2`, after which the manager's pass-1
owner logic deletes the object and clears its slot. When the reason-`3` state
handler calls `+0x40` from inside the current `+0x10` update, the update has
already entered its `+0xF2 == 0` branch; the new value `1` therefore advances
to `2` on the next enabled pass, not the same call.

## Manual request gates and return states

Resident `FUN_00238340` at live `0x00238340` (resident file `0x138440`) is the
per-fighter manual support request handler. Its only direct caller is the normal
fighter update `FUN_0024DA50`; the call is live `0x0024DCA4`, resident file
`0x14DDA4`. That caller reaches the request handler and immediately following
gauge updater only while `fighter[+0x00] & 0x02` is nonzero.

The request path is:

1. Determine whether this side already has an active support object through
   BTL live `0x008854D0` (raw `0x1D15D0`, export `FUN_00885490` at
   `0x00885490`). Its manager callee at live `0x00887810` (raw `0x1D3910`,
   corresponding export address `0x008877D0`) is a five-instruction predicate:
   it returns whether `manager.active[side]` is non-null.
2. With no active object, require input bit `0x20000000`. With an active object,
   most fighters still use `0x20000000`; fighters whose packed `+0x60` role
   field `((value & 0x1FF) >> 5)` is zero instead use `0x40000000` when the
   side-record request selector is `1` and `0x20000000` otherwise. Under the
   default binding map those logical bits are Circle and R1, respectively.
3. With no active object, require `gauge >= 0.5`. An existing active object
   bypasses this threshold. A failed low-gauge attempt can emit resident event
   `0x2C` for packed role zero.
4. Require fighter `+0xB00 == 0`, fighter `+0xB10 == 0`, and the same resident
   global chain `0x00607654 -> +0x08 -> +0x14` to resolve null.
5. Call BTL live `0x00885490` (raw `0x1D1590`, export `FUN_00885450` at
   `0x00885450`), which forwards to the manager request at live `0x008872E0`
   (raw `0x1D33E0`, export `FUN_008872A0` at `0x008872A0`).

The manager request returns a compact state:

| Return | Proven path |
| ---: | --- |
| `0` | Resolved support code is out of range, or an existing object's virtual `+0x24` query returns zero. |
| `1` | The side slot was empty; the factory allocated and initialized a support object, stored it in that side slot, and enabled object-flag masks `0x02` and `0x04`. |
| `2` | The side slot was already populated and its virtual `+0x24` query returned nonzero. |

All 14 final factory vtables use the same virtual `+0x24` implementation at
BTL live `0x00888FE0` (raw `0x1D50E0`, export `FUN_00888FA0` at
`0x00888FA0`). Its raw predicate at live `0x008890D0` (raw `0x1D51D0`,
corresponding unrecognized export address `0x00889090`) returns true exactly
when object byte `+0xE6 == 1` and signed halfword `+0xE8 == 0`. On true, the
common query calls BTL live `0x0088A7C0` (raw `0x1D68C0`, export
`FUN_0088A780` at `0x0088A780`) with argument zero; that writes object
`+0xE8 = 3`, and the manager maps the true query to return `2`. On false it
leaves the object in place and the manager returns `0`.

This is an object-local active-request latch, not a fixed resident cooldown.
The common state routine branches on halfword states `0..3`; it does not
decrement `+0xE8` once per update. After a successful active request, another
request remains unavailable while the state pair differs from
`(+0xE6, +0xE8) = (1, 0)`. It can reopen only if later lifecycle returns to
that exact pair; no fixed update count is established.

While this latch is closed, slot presence still selects the active-object input
mask and bypasses the half-gauge threshold. The manager nevertheless returns
`0`; the resident handler leaves fighter byte `+0xB58` unchanged but still
returns its outer `1` once the resident gates have passed. An open latch yields
manager return `2` and clears `+0xB58`.

Creation does not begin in the queryable state. The common base constructor
leaves object `+0xE6 = 0` and `+0xE8 = 0`. Every final factory class uses the
common virtual `+0x1C` initializer at live `0x00887FD0`, directly or through
one of two overrides that call it first; none changes those two state fields.
Consequently manager return `1` makes the slot immediately active for gauge
drain, but an active re-request initially returns `0` until scheduled object
state reaches `+0xE6 = 1`.

These return states assume the ownership preconditions used by the resident
caller. The side is always reduced to `fighter[+0x60] & 1`; the manager does
not defensively convert another index to an unavailable return. The empty-slot
factory also assumes its heap allocation succeeds. A null allocation reaches
the common slot store at live `0x008876C8` and then dereferences object
`+0x50`; it is not converted to return `0`.

For a new object the manager also builds a two-entry list containing the two
current slot identifiers (zero for an empty slot), supplies that list to its
embedded allocator at manager `+0x14`, and stores the returned identifier at
object `+0x120`.

The allocator itself is BTL live `0x00886950` (raw `0x1D2A50`; the preserved
export has no recognized function at corresponding display address
`0x00886910`). Its only direct call is the request path at live `0x00887778`
(raw `0x1D3878`). In the initial state (`manager[+0x1C] == 0`) it returns the
current word at manager `+0x18` and then increments that word. If the current
word is `-1`, that call still returns `-1`, but it sets byte `+0x1C = 1`, resets
the word through zero, and leaves the next word as `1` after the common
increment. Once byte `+0x1C` is set, the function compares the current word
against the two supplied identifiers. A non-colliding word is returned and
incremented. A collision takes the function's zero fallback and still
increments the current word; it does not reject or postpone object creation,
because the caller unconditionally stores that return at object `+0x120` and
continues. The collision loop rescans the same current word up to the supplied
count plus one; no alternate candidate is selected inside that call. These are
identifier-allocation facts only: no request, gauge, terminal-state, or slot
gate reads object `+0x120` in the paths audited here.

It then increments the first of three per-side halfwords at live
`0x008DCE90 + side * 6`. This storage is in BTL BSS, not in the raw file: the
header establishes file-backed end `0x008D6200` and BSS span
`0x008D6200..0x008DD080`. The constructor and BTL live `0x00886BB0` (raw
`0x1D2CB0`, corresponding export address `0x00886B70`) zero all three
halfwords for both sides. The request and gauge gates read none of these six
halfwords, so the creation counter is bookkeeping rather than availability or
cooldown state.

An exhaustive raw-address and direct-call audit bounds the remaining uses. The
first-halfword getter is BTL live `0x00886C20` (raw `0x1D2D20`); its sole
direct caller is resident live `0x00224280`, outside the request and gauge
chains. The second halfword has one inline increment, at BTL live
`0x00889850` (raw `0x1D5950`). The third is changed through the signed-add
helper at BTL live `0x00886C60` (raw `0x1D2D60`), whose sole direct caller is
BTL live `0x00886B3C` (raw `0x1D2C3C`). None of the six fields feeds the
request gates, drain/recharge selection, pass-1 terminal test, or explicit
teardown. The semantic purposes of the latter two counters are not assigned:
doing so would require tracing the deliberately excluded per-object combat or
outcome behavior.

The resident handler clears fighter byte `+0xB58` only for manager return `1`
or `2`. Once all resident gates above have passed, however, it returns `1` even
if the manager returned `0`. Callers must not treat the resident boolean as
proof that a support object was created.

Manager absence is one concrete instance of that mismatch. Both null-safe BTL
wrappers report no active object / request return `0`, so the normal handler
does not enter its selector-read branch and the gauge updater selects recharge.
If input, gauge, and the other resident gates pass, the resident handler can
still return `1` without creating an object.

## Scheduled lifecycle and teardown

The resident battle dispatcher `FUN_001F03E0` gives support manager bit
`0x0008` in its subsystem masks. In its three ordered passes it calls these BTL
wrappers:

| Pass | BTL live / raw / export wrapper | Manager work reached |
| --- | --- | --- |
| 1 | `0x00885400` / `0x1D1500` / `FUN_008853C0` at `0x008853C0` | live `0x00886ED0`, export `FUN_00886E90` at `0x00886E90` |
| 2 | `0x00885430` / `0x1D1530` / `FUN_008853F0` at `0x008853F0` | live `0x008871A0`, export `FUN_00887160` at `0x00887160` |
| 3 | `0x00885460` / `0x1D1560` / `FUN_00885420` at `0x00885420` | live `0x00887250`, export `FUN_00887210` at `0x00887210` |

Pass 1 refreshes object-flag masks `0x02` and `0x04` from current battle state.
It begins with both enabled. If the fighter pointer held at battle-setup
`+0xDE4` has nonzero `+0xB00` or `+0xB10`, it disables both; a separate
unresolved global-predicate chain can disable `0x02` alone. These scheduled
object flags are distinct from the fighter byte-`+0x00` outer-update flag
described above. For an object with `0x02` enabled, pass 1 invokes virtual
`+0x10` and then checks object byte `+0xF2`. When that byte equals `2`, it
invokes virtual destructor slot `+0x08` with deleting flag `1` and clears the
owning manager slot. Pass 2 invokes virtual `+0x14` for objects with `0x04`
enabled. It temporarily writes pointer value `0x00609160` to the shared global
pointer slot at live `0x006073F4`, then restores that slot's prior value. Pass
3 invokes virtual `+0x18` for objects with `0x02` enabled.

Pass 1 has two additional manager-level actions before the virtual `+0x10`
loop. If manager byte `+0x20` is set, it checks each side's resolved code with
the raw code-table predicate at live `0x00885B70` (raw `0x1D1C70`,
corresponding export address `0x00885B30`) and may emit event
`(side + 1, 0x18, 1)`, then clears `+0x20`. Under a separate unresolved BTL
global-predicate chain it can also broadcast virtual `+0x40` to both active
objects through manager live `0x008878F0` (raw `0x1D39F0`, export
`FUN_008878B0` at `0x008878B0`). The vtable audit above proves this is a
terminal request for every factory class. Because the broadcast precedes the
per-object `+0x10` loop, an object can advance `+0xF2` from `1` to `2` and be
deleted in that same pass when flag `0x02` remains enabled. If `0x02` is
disabled, the terminal byte remains `1` until a later enabled pass. The global
predicate's battle meaning remains unresolved.

Resident `FUN_001EC7A0` initializes the subsystem through BTL live
`0x00885210` (raw `0x1D1310`, export `FUN_008851D0` at `0x008851D0`). Raw bytes
show that this wrapper deletes any prior manager, allocates exactly `0x24`
bytes, runs the manager constructor, and stores the new pointer at
`0x00607888`. Resident `FUN_001EC890` and resident cleanup call sites at live
`0x001F20F0` and `0x001F360C` call BTL live `0x00885290` (raw `0x1D1390`,
export `FUN_00885250` at `0x00885250`), which invokes the manager's deleting
destructor and clears `0x00607888`. Those are the only three resident direct
calls to this destroy wrapper in the clean binary.

Later battle-phase entry `FUN_001EDB00` calls BTL live `0x008852E0` (raw
`0x1D13E0`, export `FUN_008852A0` at `0x008852A0`). If the manager exists, this
resets its embedded allocator through manager live `0x00886EB0` (raw
`0x1D2FB0`, export `FUN_00886E70` at `0x00886E70`), writing manager
`+0x18 = 1` and `+0x1C = 0`. The wrapper can also reset the six BSS halfwords
above under its resident-mode predicates. This is initialization/bookkeeping;
it is not a per-request cooldown reset.

The manager deleting destructor at BTL live `0x00886DE0` (raw `0x1D2EE0`,
export `FUN_00886DA0` at `0x00886DA0`) deletes each non-null per-side support
object through virtual slot `+0x08` and clears both slots. Therefore both
natural object completion and enclosing battle-subsystem teardown have
explicit ownership paths; overlay replacement is not relied upon as object
cleanup.

There is also a clear-without-manager-destruction path. Resident
`FUN_001EDD10` calls BTL live `0x008853D0` (raw `0x1D14D0`, export
`FUN_00885390` at `0x00885390`). Its manager callee at live `0x00886E70`
(raw `0x1D2F70`, export `FUN_00886E30` at `0x00886E30`) calls the all-sides
delete routine at live `0x00887990` (raw `0x1D3A90`, export `FUN_00887950` at
`0x00887950`). That routine deletes both non-null objects through virtual
`+0x08` with flag `1`, clears both slots, and leaves the `0x24`-byte manager
allocated. The manager callee then sets manager byte `+0x20 = 1`; pass 1
performs and clears the one-shot resolved-code checks described above.

## Limits and useful negative results

- The analysis proves one manager-owned active object per side. It found no
  second simultaneous ordinary-support slot in this path.
- No independent resident cooldown timer was found beside fighter `+0x74` and
  `+0x78`; the active-object pointer itself selects drain versus recharge.
  Active re-request has a separate object-state latch, not a decrementing
  timer.
- Zero gauge is passed to an object as virtual reason `3`; it is not itself the
  manager's deletion condition. The manager frees only terminal byte
  `+0xF2 == 2` while pass-1 flag `0x02` is enabled.
- Manager side-record `+1` is proven operationally but its upstream UI label is
  not assigned. Static evidence establishes its effect on the active-object
  request input; it does not establish a safe user-facing name for the setting.
- The specialized support subclasses and their internal combat decisions were
  deliberately not traced. Active-request return `0` versus `2` is nevertheless
  common across all 14 final vtables and is fixed by object `+0xE6/+0xE8` as
  described above.
- Static code establishes update counts and ordering, not wall-clock duration.
  Any conversion to seconds requires the actual scheduler rate of the tested
  runtime mode.
- Earlier BTL seams at raw `0xC5A5C` and `0xC5E64` were already runtime-negative
  for the recorded manual support call. The direct resident handler and manager
  request above are the supported ownership path.

## Function map

| Image | Live address | File/raw offset | Preserved export | Established role |
| --- | ---: | ---: | --- | --- |
| Resident | `0x001EC7A0` | `0x0EC8A0` | `FUN_001ec7a0` | Initialize battle subsystem and create/reset BTL support manager. |
| Resident | `0x001EC890` | `0x0EC990` | `FUN_001ec890` | Enclosing cleanup that destroys the BTL support manager. |
| Resident | `0x001EDD10` | `0x0EDE10` | `FUN_001edd10` | Transition path that clears both active slots but retains the manager. |
| Resident | `0x001F03E0` | `0x0F04E0` | `FUN_001f03e0` | Three-pass battle subsystem dispatcher. |
| Resident | `0x00238070` | `0x138170` | unrecognized three-instruction leaf | Return fighter support gauge `+0x74`. |
| Resident | `0x002380C0` | `0x1381C0` | `FUN_002380c0` | Map selected support's manager class byte to fighter recharge multiplier. |
| Resident | `0x00238340` | `0x138440` | `FUN_00238340` | Manual support input and request gates. |
| Resident | `0x00238540` | `0x138640` | `FUN_00238540` | Select recharge or active drain. |
| Resident | `0x00238600` | `0x138700` | `FUN_00238600` | Recharge and clamp. |
| Resident | `0x00238720` | `0x138820` | `FUN_00238720` | Active-object drain and clamp. |
| BTL | `0x00885210` | `0x1D1310` | `FUN_008851D0` / `0x008851D0` | Recreate two-side manager. |
| BTL | `0x008852E0` | `0x1D13E0` | `FUN_008852A0` / `0x008852A0` | Reset manager identifier state and, conditionally, BSS creation bookkeeping. |
| BTL | `0x00885490` | `0x1D1590` | `FUN_00885450` / `0x00885450` | Null-safe global wrapper for manager request. |
| BTL | `0x008854D0` | `0x1D15D0` | `FUN_00885490` / `0x00885490` | Null-safe global wrapper for active-object predicate. |
| BTL | `0x00885880` | `0x1D1980` | unrecognized start / `0x00885840` | Validate an object code and identify code `49` for normalization to zero. |
| BTL | `0x00885C30` | `0x1D1D30` | `FUN_00885BF0` / `0x00885BF0` | Resolve a canonical primary identity to one of three support-list candidates. |
| BTL | `0x00885CE0` | `0x1D1DE0` | `FUN_00885CA0` / `0x00885CA0` | Resolve per-side support color variants without identity/color collisions. |
| BTL | `0x00886250` | `0x1D2350` | `FUN_00886210` / `0x00886210` | Normalize selected support data and initialize per-side metadata. |
| BTL | `0x00886950` | `0x1D2A50` | unrecognized start / `0x00886910` | Allocate object `+0x120` identifier from manager `+0x18`, with post-wrap active-ID collision fallback. |
| BTL | `0x00886BB0` | `0x1D2CB0` | unrecognized start / `0x00886B70` | Reset three BSS bookkeeping halfwords for each side. |
| BTL | `0x00886CB0` | `0x1D2DB0` | unrecognized start / `0x00886C70` | Construct `0x24`-byte two-side manager. |
| BTL | `0x00886DE0` | `0x1D2EE0` | `FUN_00886DA0` / `0x00886DA0` | Delete active objects and, for a deleting call, free the manager. |
| BTL | `0x00886E70` | `0x1D2F70` | `FUN_00886E30` / `0x00886E30` | Delete both active objects, retain manager, and arm one-shot setup. |
| BTL | `0x00886EB0` | `0x1D2FB0` | `FUN_00886E70` / `0x00886E70` | Reset the embedded identifier allocator to its initial state. |
| BTL | `0x008872E0` | `0x1D33E0` | `FUN_008872A0` / `0x008872A0` | Validate resolved code; create or query the side's support object. |
| BTL | `0x00887810` | `0x1D3910` | unrecognized start / `0x008877D0` | Return whether a side has an active support object. |
| BTL | `0x00887990` | `0x1D3A90` | `FUN_00887950` / `0x00887950` | Delete and clear one side or both sides; reset path supplies `-1`. |
| BTL | `0x00887FD0` | `0x1D40D0` | `FUN_00887F90` / `0x00887F90` | Initialize common object identity fields, including resolved code and owning side. |
| BTL | `0x00888720` | `0x1D4820` | `FUN_008886E0` / `0x008886E0` | Common scheduled object update; advance terminal byte `1` to `2`. |
| BTL | `0x00888FE0` | `0x1D50E0` | `FUN_00888FA0` / `0x00888FA0` | Common active-object request query; test and latch object state. |
| BTL | `0x008890A0` | `0x1D51A0` | `FUN_00889060` / `0x00889060` | Common virtual `+0x40` terminal setter; write object `+0xF2 = 1`. |
| BTL | `0x008890D0` | `0x1D51D0` | unrecognized start / `0x00889090` | Return whether object `+0xE6 == 1` and `+0xE8 == 0`. |
| BTL | `0x00889540` | `0x1D5640` | `FUN_00889500` / `0x00889500` | Common virtual `+0x48` reason/state-reset handler. |
| BTL | `0x00889C10` | `0x1D5D10` | `FUN_00889BD0` / `0x00889BD0` | Common object state routine; notify virtual `+0x48` with reason `3` at zero gauge. |
| BTL | `0x0088A7C0` | `0x1D68C0` | `FUN_0088A780` / `0x0088A780` | Set active-request latch halfword `+0xE8 = 3`. |
| BTL | `0x0088A890` | `0x1D6990` | `FUN_0088A850` / `0x0088A850` | Common reason-`3` state handler; conditionally invoke terminal setter. |
