# Native chakra and guard state

This document maps the clean *Narutimate Accel 2* v2.28 (`SLPS-25837`)
fighter-side chakra and guard state used while `BTL.BIN` is active. It is a
static disassembly result, not a UI interpretation: values such as `5.0` and
`15.0` below are raw native `float32` units. No claim is made that one raw unit
corresponds to a particular number of pixels, icons, bars, or displayed
percent.

The analysis intentionally excludes Adventure, substitution-specific paths,
damage scaling, frame-rate work, widescreen/layout, media, and localization.
Only clean read-only binaries and their existing Ghidra exports were inspected.

## Research coverage

- **Assigned scope:** clean `BTL.BIN` battle-time native chakra and guard
  resource state: fighter fields, current/maximum values, gain/spend/clamp and
  reset lifecycle, representative non-substitution callers, and any provable
  guard durability/break state. The output was limited to this document.
- **Exploration depth:** the clean `SLPS_258.37` resident image,
  `PRG/BTL.BIN`, and their existing `.c`/`.txt` Ghidra exports; resident chakra
  core `FUN_002254A0..FUN_002260D0`; combined and lifecycle paths
  `FUN_00227850`, `FUN_00227CE0`, `FUN_00227EE0`, `FUN_002369D0`,
  `FUN_00237060`, `FUN_0023A9A0`, `FUN_00244F80`, `FUN_00245340`,
  `FUN_00248EC0`, `FUN_00249D70`, and `FUN_0024C440`; temporary-effect
  construction/update/scanners `FUN_00304910..FUN_00307B20`; manager/event
  callers `FUN_0035AF20` and `FUN_00374190`; guard entry, exit, input, and hit
  routes centered on `FUN_002209A0`, `FUN_00228130..FUN_00229B80`,
  `FUN_00232B80`, and `FUN_00248580..FUN_0024DA50`; and the specifically
  listed loaded-overlay event, debit, guard-setter, and attack-dispatch paths.
  **Exhaustive coverage within explicit bounds:** all 138 authored temporary
  effect definitions (`0x00..0x89`) were read for the documented chakra blocker
  bits and relevant fields; all 74 static configuration containers passed by
  direct calls to `FUN_002151E0` were checked for initial chakra and base
  recovery data; direct resident syntax writers of fighter `+0x70` and
  `+0x95A/+0x95C` were censused; the entire aligned clean `BTL.BIN` was scanned
  for direct JALs to the documented add/subtract/affordability and guard-setter
  targets; and the resident image was directly scanned for the documented
  constructor/reset and canonical add/subtract call sites. All overlay address
  triples recorded here were audited against `file = export - 0x006B3EC0` and
  `live = export + 0x40`.
  **Bounded or sampled coverage:** all direct canonical-adder sites and all
  seven direct overlay simple-subtractor sites were followed far enough to
  recover their raw amounts or formulas and gate arguments. The 18 direct
  overlay affordability imports were counted exhaustively, but their individual
  controller/action meanings were not all recovered. Inline resident current
  writers were classified exhaustively by direct fighter-field syntax, while
  higher-level action semantics were followed only where needed to establish
  resource ownership, lifecycle, and representative non-substitution use.
  Guard coverage follows the shared input/stance route, the representative
  resident guarded-hit router, all proven direct guard-counter writers, and the
  two loaded overlay dispatchers documented below; it does not claim every
  character script was semantically reconstructed.
- **Confirmed coverage:** fighter `+0x70` is the sole proven native
  current-chakra field and raw `15.0` is its literal maximum; all 74 directly
  instantiated clean configurations author initial `15.0`; gain, affordability,
  and ordinary spend use deliberately different effect/status gates; the
  `+0x7C/+0x80/+0x82/+0x84` reservation transaction can record, release, or
  commit even when arithmetic is suppressed; the upper/lower clamps, recovery
  multipliers, temporary-effect lifecycle, and representative resident/overlay
  callers are mapped. Guard uses temporal state `+0x95A/+0x95C`, stance
  `(0,5)`, guarded responses `(0,6)/(0,7)`, and per-hit invalidation/branch
  flags; no cumulative guard-durability pool was established in the traced
  system.
- **Unresolved or untested:** indirect-call coverage; semantics of every
  unrecovered overlay switch case and every affordability caller; player-facing
  names for temporary-effect IDs and attack flags `0x00400000`, `0x00800000`,
  and `0x01000000`; the full cross-system meanings of negative guard sentinels and
  fighter gates `+0x168/+0x169`; and possible character-specific or scripted
  guard exceptions. A future durability claim still requires a field with a
  proven initialization, guarded-hit decrement, clamp, and break consumer.
- **Deliberate exclusions and overlap:** Adventure; substitution
  mechanics/cost and substitution-bar design; damage scaling; 60-FPS work;
  widescreen/layout; media and localization; physical controller bindings; UI
  units; player-facing action, effect, or stage naming; and support-gauge design
  beyond rejecting fighter `+0x74` as a guard-resource false lead.
- **Evidence limitations:** this is static evidence from clean read-only binaries,
  raw instruction/data checks, and existing disassembly exports. No emulator
  execution, runtime watchpoint, savestate experiment, or injected patch was
  used. Raw-byte/JAL checks mitigate omitted or overlapping Ghidra functions,
  but static analysis cannot establish dynamic call frequency, timing units,
  UI representation, or the absence of every indirect/scripted exception.

## Source identity and address model

| Image | Size | SHA-256 |
| --- | ---: | --- |
| `SLPS_258.37` | `5,273,256` bytes | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |
| `PRG/BTL.BIN` | `2,237,184` bytes | `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` |

Resident fighter/resource routines are in `SLPS_258.37`, even though the
battle overlay calls them. For the first ELF load segment used here:

```text
ELF file offset = EE runtime address - 0x000FFF00
```

Live memory retains the complete `0x40`-byte `MWo3` header at header base
`0x006B3F00`; payload therefore begins at `0x006B3F40`. The preserved Ghidra
baseline omitted that header and placed payload bytes/functions `0x40` too
low. For an overlay-local address in that export:

```text
BTL file offset       = Ghidra export address - 0x006B3EC0
loaded EE address     = Ghidra export address + 0x40
loaded EE address     = 0x006B3F00 + BTL file offset
```

Imported resident targets such as `0x002254A0` are already EE runtime
addresses and do **not** receive the overlay `+0x40` adjustment. Encoded
absolute pointers and JAL targets inside the raw overlay are also already live
values. Consequently, a local JAL can target live `X` while Ghidra attaches
the name `FUN_X` to bytes whose true live address is `X+0x40`; the callee's
corresponding export bytes are at `X-0x40`.

One direct cross-image check is the `BTL.BIN` instruction at file offset
`0x0005D9CC`: clean bytes `28 95 08 0C` encode a `jal 0x002254A0`.
The export labels that instruction `0x0071188C`; it executes loaded at
`0x007118CC`.

## Fighter and action-record fields

All fighter offsets are relative to the live fighter object.

| Offset | Type | Proven role | Evidence and limits | Confidence |
| ---: | --- | --- | --- | --- |
| `+0x61` | `uint8` | Fighter status flags; bit `3` enables canonical chakra gain | `FUN_00214A40` clears bit `3`; `FUN_002151E0` sets it immediately before the configured initial-chakra add. `FUN_002254A0` returns without any arithmetic or requested side effects while the bit is clear. Other bits have unrelated fighter-state roles. | High for bit `3` operation |
| `+0x62` | `uint8` | Fighter resource/action status flags | Bit `0` blocks the canonical chakra adder. Bit `1` blocks canonical and inline ordinary debits. Bit `3` selects the flat-`5.0` branch of staged-input eligibility instead of the selected tier amount. Construction clears these bits; no player-facing names are inferred. | High for these bit operations |
| `+0x70` | `float32` | Current chakra | Read, added to, subtracted from, and clamped by the native resource routines. | High |
| — | literal `float32` | Chakra maximum `15.0` | `FUN_002254A0` upper-clamps to literal `15.0`; no separate per-fighter maximum field was found. | High |
| `+0x7C` | `float32` | Pending/refundable chakra reservation claim | `FUN_00225F50` records the requested amount here even when a spend-blocking effect suppresses the corresponding debit. `FUN_002260D0` attempts to add the amount back through the canonical adder, then clears it whether or not that adder is gated. | High |
| `+0x80` | `int16` | Reservation class index | Set to `1..3` with a reservation and cleared on release. No UI meaning is inferred. | High for operation; Medium for label |
| `+0x82` | `int16` | Reservation lifetime counter | Initialized to raw `0x3C` when a reservation is created and decremented by fighter maintenance until release at zero; an active effect flag `0x40` instead triggers immediate release. No time-unit conversion is inferred. | High for operation; Medium for label |
| `+0x84` | `int16` | Post-release staged-input lockout counter | Construction clears it. `FUN_002260D0(fighter, mode)` sets raw `0x3C` when `mode != 0`; `FUN_00225B60` rejects staged input while it is nonzero; `FUN_0024C440` decrements it during fighter maintenance. No time-unit conversion is inferred. | High for operation; Medium for label |
| `+0x164` | `float32` | Base chakra-recovery multiplier | Copied by `FUN_002151E0` from character-record word `0x36` (record byte `+0xD8`); used by charge and recovery paths. | High |
| `+0x168` | `uint8` | Staged-input inhibit | Initialized to `0` by `FUN_00216440`, updated by `FUN_00216460`, and blocks `FUN_00225B60` when nonzero. No player-facing setting name is inferred. | High for operation; Medium for label |
| `+0x169` | `uint8` | Ordinary-debit inhibit | Initialized to `0` by `FUN_00216440` and updated by `FUN_00216460`. An exact value of `1` blocks the simple subtractors and the reviewed inline/combined debit branches without necessarily blocking their surrounding action logic. | High for operation; Medium for label |
| `+0x18C` | `int16` | Authored chakra-cost tier selector | Initialized to `0`; `FUN_002449C0` copies a selected table entry's tier byte here. Observed values `0/1/2` select raw costs and crossing thresholds `5.0/10.0/15.0`. This is a native tier, not a UI-unit claim. | High for operation; Medium for label |
| `+0x1A0` | `float32` | Chakra threshold-history old/baseline value | `FUN_00225A40` records the old sample here when processing threshold crossings. Native spend paths overwrite it with `15.0`. It is not established as a timer. | High for behavior; Medium for label |
| `+0x1A4` | `float32` | Chakra threshold-history new value | Paired with `+0x1A0` by `FUN_00225A40`. | High for behavior; Medium for label |
| `+0x1A8` | `uint8` | Full-threshold feedback latch | Initialized/rearmed to `1` and cleared after the charge path reports a `15.0` crossing. It gates feedback, not chakra storage. | High for operation; Medium for label |
| `+0x8C4` | `int32` | Temporary-effect count | Iteration bound used by `FUN_00307230`. | High |
| `+0x8C8` | pointer | First temporary-effect entry | List head used by `FUN_00307230`; active entries contribute their `+0x94` chakra modifier. | High |
| `+0x18E` | `int16` | Major action/state class | The guard stance uses class `0`. | High |
| `+0x190` | `int16` | Action/state within the class | State pair `(0,5)` is entered from the guard input path. | High |
| `+0x338` | `uint32` | Current logical input flags | Bit `0x08000000` drives the staged-chakra eligibility/debit path and bit `0x10000000` drives the guard input updater. This does not identify physical controller bindings. | High |
| `+0x95A` | `int16` | Guard-active/eligible hold-age state | Increments while guard is held and accepted, saturates at `0x7FFF`, clears on release/ineligibility, and is tested by hit routing (`<1` versus `>=1`). Some hit properties set the sentinel `-1`. It is not durability. | High |
| `+0x95C` | `int16` | Guard-input age/timing state | Increments while the same logical guard bit is held, clears on release, and counts negative sentinel values back toward zero. It is reused by other eligibility logic and is not durability. | High for operations; Medium for broader meaning |

The generic action-record array begins at fighter `+0xA54`; records are
`0x54` bytes. Action-record `+0x20` is a native chakra cost `float32` consumed
by `FUN_0023A9A0`. Attack/hit record `+0x14` also contains at least three
guard-sensitive flags. Two invalidate `+0x95A`; a third preserves it while
selecting a distinct overlay-processing branch. They are documented under
guard rather than assigned unproven player-facing names.

Temporary-effect entries reached through fighter `+0x8C8` expose these
additional chakra fields:

| Effect-entry offset | Type | Proven operation | Confidence |
| ---: | --- | --- | --- |
| `+0x68` | `int32` | Authored effect-definition ID copied from definition record `+0x00`. | High |
| `+0x6C` | `int32` | Lifecycle/duration state; the modifier aggregators treat nonzero as active. | High for operation |
| `+0x70` | `uint32` | Effect behavior flags. Across active entries, bit `0x10` blocks staged-input eligibility, bit `0x40` blocks chakra gain and affordability, and bit `0x80` blocks ordinary spend. Adjacent bit `0x20` has an exact scanner but no chakra role was established. | High for scans and chakra gates |
| `+0x94` | `float32` | Recovery-factor contribution used as `value - 1.0`. | High |
| `+0xA4` | `float32` | Signed chakra delta applied when `FUN_00304910` constructs/attaches the entry. | High for timing and operation |
| `+0xA8` | `float32` | Signed chakra delta applied by `FUN_00304E90` during entry cleanup. | High for timing and operation |
| `+0xB4` | `float32` | Signed delta accumulated by the per-fighter effect update. | High |
| `+0xB8` | `float32` | Current-chakra boundary used to suppress a `+0xB4` aggregate after the current value is already beyond the authored boundary. It is not a maximum field. | High for operation; Medium for label |

## Chakra routine map

| Symbol | EE runtime | ELF file | Role |
| --- | ---: | ---: | --- |
| `FUN_002145D0` | `0x002145D0` | `0x001146D0` | Base fighter-object constructor; constructs subordinate state and calls the fighter resource/state reset. |
| `FUN_00214A40` | `0x00214A40` | `0x00114B40` | Base fighter initialization; clears current chakra and related threshold history. |
| `FUN_002151E0` | `0x002151E0` | `0x001152E0` | Applies character configuration, base recovery multiplier, and configured initial chakra. |
| `FUN_002254A0` | `0x002254A0` | `0x001255A0` | Canonical chakra adder and upper clamp. |
| `FUN_00225780` | `0x00225780` | `0x00125880` | Canonical simple subtractor and lower clamp. |
| `FUN_00225830` | `0x00225830` | `0x00125930` | Feedback-selecting direct subtractor and lower clamp. |
| `FUN_00225940` | `0x00225940` | `0x00125A40` | Chakra affordability predicate. |
| `FUN_00225A40` | `0x00225A40` | `0x00125B40` | Detects threshold crossings and maintains `+0x1A0/+0x1A4`. |
| `FUN_00225B60` | `0x00225B60` | `0x00125C60` | Eligibility and affordability predicate for staged chakra input. |
| `FUN_00225F50` | `0x00225F50` | `0x00126050` | Records a pending reservation at `+0x7C`; its corresponding debit is conditional on spend gates. |
| `FUN_002260D0` | `0x002260D0` | `0x001261D0` | Attempts a refund through the canonical adder, then clears the reservation and metadata unconditionally. |
| `FUN_00227850` | `0x00227850` | `0x00127950` | Combined action/effect helper whose second float is a conditionally applied chakra debit. |
| `FUN_00227CE0` | `0x00227CE0` | `0x00127DE0` | Combined affordability, conditional spend, feedback, and authored-effect/event helper. |
| `FUN_00227EE0` | `0x00227EE0` | `0x00127FE0` | Chakra-charge action update. |
| `FUN_002369D0` | `0x002369D0` | `0x00136AD0` | General recovery-event router; can recover chakra and/or HP. |
| `FUN_00237060` | `0x00237060` | `0x00137160` | Event/action helper that releases a reservation through the conditional refund path, emits an event/effect, then conditionally consumes a small discrete chakra amount. |
| `FUN_0023A9A0` | `0x0023A9A0` | `0x0013AAA0` | Generic action-record dispatcher; conditionally consumes record `+0x20` chakra cost. |
| `FUN_002449C0` | `0x002449C0` | `0x00144AC0` | Maintains the selected authored cost tier at `+0x18C` and the corresponding dynamic action-record cost. |
| `FUN_00244F80` | `0x00244F80` | `0x00145080` | Finalizes a matching staged action by releasing the reservation and conditionally charging the selected `5/10/15` tier. |
| `FUN_00245340` | `0x00245340` | `0x00145440` | Action-phase path that releases a reservation, then conditionally charges the active action record's `+0x20` cost. |
| `FUN_00248EC0` | `0x00248EC0` | `0x00148FC0` | Fighter input update; includes the logical `0x08000000` staged-chakra debit path. |
| `FUN_00249D70` | `0x00249D70` | `0x00149E70` | Input-history/action gate with a gated raw `0.008333334` chakra debit. |
| `FUN_0024C440` | `0x0024C440` | `0x0014C540` | Fighter maintenance; expires pending reservations and implements the gated Practice Chakra Unlimited refill. |
| `FUN_00304910` | `0x00304910` | `0x00204A10` | Temporary-effect construction; applies entry `+0xA4` as an immediate signed chakra delta. |
| `FUN_00304D60` | `0x00304D60` | `0x00204E60` | Temporary-effect lifetime tick; at zero, applies cleanup, invokes the entry's expiry callback, and signals removal. |
| `FUN_00304E90` | `0x00304E90` | `0x00204F90` | Temporary-effect cleanup; applies entry `+0xA8` as a signed chakra delta. |
| `FUN_00305270` | `0x00305270` | `0x00205370` | Effect-list replace/create helper; constructs a new entry and inserts it only after construction returns. |
| `FUN_003059B0` | `0x003059B0` | `0x00205AB0` | Per-fighter temporary-effect update; routes the aggregate from `FUN_00307020`. |
| `FUN_00305C30` | `0x00305C30` | `0x00205D30` | Higher-level authored-effect application path; supplies the definition lifetime and calls the list helper. |
| `FUN_00306220` | `0x00306220` | `0x00206320` | Signed chakra-delta router to the canonical adder or subtractor. |
| `FUN_00307020` | `0x00307020` | `0x00207120` | Aggregates active temporary-effect `+0xB4` deltas and applies `+0xB8` boundary gating. |
| `FUN_00307230` | `0x00307230` | `0x00207330` | Aggregates temporary chakra-recovery modifiers. |
| `FUN_003073A0` | `0x003073A0` | `0x002074A0` | Reports any active temporary-effect entry with behavior flag `0x10`; used as a staged-input blocker. |
| `FUN_00307410` | `0x00307410` | `0x00207510` | Reports any active temporary-effect entry with behavior flag `0x20`; no chakra role is assigned here. |
| `FUN_00307480` | `0x00307480` | `0x00207580` | Reports any active temporary-effect entry with behavior flag `0x40`; blocks chakra gain and affordability. |
| `FUN_003074F0` | `0x003074F0` | `0x002075F0` | Reports any active temporary-effect entry with behavior flag `0x80`; blocks ordinary spend unless a caller explicitly bypasses it. |
| `FUN_00307B20` | `0x00307B20` | `0x00207C20` | Reports presence of effect-entry ID `0x0B`, `0x3B`, or `0x41` without testing `+0x6C`; the staged-action commit path uses it to bypass the `0x80` spend-block scan. |
| `FUN_0035AF20` | `0x0035AF20` | `0x0025B020` | Manager callback with a positive-only, target-minus-current chakra top-up path. |
| `FUN_00374190` | `0x00374190` | `0x00274290` | Battle-event object dispatcher; event type `0x0C` adds raw `15.0`, while other recovery-class events route through `FUN_002369D0`. |

The clean function starts were also checked directly in the binary. Examples
are `A0 FF BD 27 ...` at ELF `0x001255A0` (`FUN_002254A0`),
`D0 FF BD 27 ...` at `0x00125880` (`FUN_00225780`), and
`90 FF BD 27 ...` at `0x0013AAA0` (`FUN_0023A9A0`).

Representative direct imports from the battle overlay are mapped under both
address conventions here:

| Export bytes/function | Ghidra export | `BTL.BIN` file | Loaded EE | Chakra operation |
| --- | ---: | ---: | ---: | --- |
| `FUN_0070BBE0` | `0x0070BBE0` | `0x00057D20` | `0x0070BC20` | Event dispatcher; event byte `0x0C` adds raw `15.0`, while recovery-class events call `FUN_002369D0`. |
| `FUN_007116E0` | `0x007116E0` | `0x0005D820` | `0x00711720` | Table-driven event handler; event `0x5D` adds raw `2.5` through `FUN_002254A0`. |
| `FUN_00790830` | `0x00790830` | `0x000DC970` | `0x00790870` | Controller-object path that passes its positive raw `+0x5E8` amount to `FUN_00225780` for fighter pointer `+0x31C`. |
| `FUN_007C47A0` | `0x007C47A0` | `0x001108E0` | `0x007C47E0` | Small wrapper that requests a raw `7.5` subtraction from fighter pointer `+0x4CC`. |
| `FUN_007C6500` | `0x007C6500` | `0x00112640` | `0x007C6540` | When object `+0x550 -> +0x14` bit `0` is set, requests a raw `5.0` subtraction from fighter pointer `+0x4CC`. |
| `FUN_007F0C00` | `0x007F0C00` | `0x0013CD40` | `0x007F0C40` | Controller path that conditionally requests its raw `+0x10D8` amount from fighter pointer `+0x31C`. |
| `FUN_007FDE00` | `0x007FDE00` | `0x00149F40` | `0x007FDE40` | Larger controller update that passes a computed aggregate to the subtractor for fighter pointer `+0x4CC`. |
| `FUN_00818340` | `0x00818340` | `0x00164480` | `0x00818380` | Requests raw `5.0`, or raw `2.5` when its object gate is clear and fighter `+0x95A` is nonzero, from fighter pointer `+0x9D4`. |
| `FUN_00847030` | `0x00847030` | `0x00193170` | `0x00847070` | Controller update that requests a raw `1.25` subtraction from fighter pointer `+0x31C`. |

An aligned raw-word census over the clean overlay gives the complete direct-JAL
counts below. File offsets are listed because the address formulas above map
each one unambiguously to export and loaded addresses.

| Resident target | Clean instruction bytes | Count | `BTL.BIN` file offsets |
| --- | --- | ---: | --- |
| `FUN_002254A0` | `28 95 08 0C` | 2 | `0x00057EF8`, `0x0005D9CC` |
| `FUN_00225780` | `E0 95 08 0C` | 7 | `0x000DCA14`, `0x001108F8`, `0x00112674`, `0x0013CE00`, `0x0014A370`, `0x00164544`, `0x001933CC` |
| `FUN_00225940` | `50 96 08 0C` | 18 | `0x0003E984`, `0x00044E20`, `0x00045850`, `0x00045950`, `0x000473C8`, `0x000474A0`, `0x000487B0`, `0x00048AB8`, `0x00048DA4`, `0x00049718`, `0x00049840`, `0x0004A720`, `0x0004B0CC`, `0x0004CBD8`, `0x0004D57C`, `0x0004E008`, `0x0004E21C`, `0x00050D4C` |

All listed words occur in decoded call contexts, not unexecuted table padding.
The decompiler both duplicates some overlapping blocks and omits other
unrecovered blocks, so its textual call counts are not used as evidence. The
raw census does not cover indirect calls.

The resident ELF has four aligned direct JALs to `FUN_00225780`, at file
offsets `0x0011E44C`, `0x0018F5F0`, `0x002064A4`, and `0x0025BBC8`
(runtime `0x0021E34C`, `0x0028F4F0`, `0x003063A4`, and `0x0035BAC8`). At all
four resident sites and all seven overlay sites, the call setup passes zero in
`a1`, the subtractor's effect-scan bypass argument. Thus no direct caller in
either clean image exercises a nonzero bypass. The overlay site at file
`0x00164544` falls in a Ghidra-undefined gap, but the raw preceding word at
`0x00164540` is `0x0000282D` (`move a1, zero`) and the JAL word itself is
`0x0C0895E0`, so that missing decompiler context does not weaken the result.

The same aligned scan found no direct overlay JAL to
`FUN_00225830`, `FUN_00225B60`, `FUN_00225F50`, `FUN_002260D0`,
`FUN_00227850`, or `FUN_00227CE0`. Thus the reviewed overlay imports the
simple add/subtract/affordability surface directly, while staged-reservation
creation, release, and commit remain resident-owned in the proven paths. This
is a direct-call negative result, not a claim about every possible indirect
dispatch.

### Initialization, maximum, and reset/refill

`FUN_00214A40` clears fighter `+0x70`, reservation fields `+0x7C/+0x80/+0x82`,
threshold history `+0x1A0/+0x1A4`, and guard counters `+0x95A/+0x95C` during
base construction. `FUN_002151E0` then:

1. copies character-record word `0x36` to fighter `+0x164`;
2. calls the HP initializer with configuration word `param_2[7]`; and
3. calls `FUN_002254A0(param_2[8], fighter, 0, 0, 1)`.

Thus configuration word `param_2[8]` (container byte `+0x20`) is the native
initial-chakra input. Because construction starts at zero, the adder establishes
the initial current value while applying its normal maximum and threshold
logic. The initializer itself does not hard-code “start full.”

The direct-call lifecycle is bounded by clean raw-JAL censuses. The resident
ELF contains exactly one direct call to `FUN_00214A40`, at file
`0x00114910` / runtime `0x00214810`, inside base constructor
`FUN_002145D0`. It contains 74 direct calls to `FUN_002151E0`, distributed
across the specialized fighter constructors that supply their static
configuration records. The clean battle overlay contains no direct JAL to
either routine. Therefore the proven direct lifecycle is base zeroing followed
by configured initialization; the overlay does not directly reset or
reconfigure chakra. This is not a claim about possible indirect calls.

Those 74 direct calls supply 74 distinct static configuration containers. An
exhaustive clean-data read found `0x41700000` (`15.0`) at container `+0x20`
for every one. Thus all directly instantiated clean fighter configurations
observed here are authored to start at the raw maximum, even though
`FUN_002151E0` itself accepts a general value and does not hard-code “full.”
Each container's word `+0x00` points to the copied character record whose
`+0xD8` word becomes fighter recovery multiplier `+0x164`; those 74 records
have this exact distribution:

| Raw `+0x164` multiplier | IEEE-754 bits | Configuration count |
| ---: | ---: | ---: |
| `0.80` | `0x3F4CCCCD` | 4 |
| `0.85` | `0x3F59999A` | 3 |
| `0.90` | `0x3F666666` | 11 |
| `0.95` | `0x3F733333` | 2 |
| `1.00` | `0x3F800000` | 32 |
| `1.10` | `0x3F8CCCCD` | 9 |
| `1.15` | `0x3F933333` | 5 |
| `1.20` | `0x3F99999A` | 5 |
| `1.50` | `0x3FC00000` | 3 |

The counts total 74 and keep the authored recovery factor distinct from the
initial fill and maximum. They imply neither a UI scale nor a time conversion.

The proven native maximum is raw `15.0`. `FUN_002254A0` stores exactly
`15.0` when the sum is above `15.0` or within `0.001` of it. The same code uses
raw thresholds `5.0`, `10.0`, and `15.0` for threshold-crossing feedback; these
constants are not evidence for a particular UI representation.

The threshold selected by the adder is not inferred from current chakra.
`FUN_002449C0` obtains an authored byte through `FUN_00372CB0` (table byte
`0x005AEC49 + index * 0x14`) and stores it at fighter `+0x18C`. For tiers
`0/1/2`, it writes raw `5.0/10.0/15.0` to the selected dynamic action record's
`+0x20` cost. `FUN_002254A0` uses the same tier-to-value mapping when its
threshold flag is enabled. Constructor `FUN_00214A40` starts the tier at zero;
a selected-record change in `FUN_002449C0` also releases any pending
reservation before replacing the dynamic record data.

`FUN_0024C440` has the persistent Practice Chakra Unlimited refill. It first
requires manager pointer `0x00607600` to be nonnull with manager `+0x0C == 3`.
The fighter must not be in major action `8`, `5`, or `6`; fighter `+0xB00`
must be zero; the low five bits of word `0x006073FC + 0x194` must be clear;
and pending reservation `+0x7C` must be zero. If
`FUN_001F6420(manager, 2) == 1` (Practice Chakra key `2`, Unlimited), it calls
`FUN_002254A0(15.0, fighter, 0, 0, 0)`. For an ordinary nonnegative current
value this saturates the fighter to full through the standard clamp. The
reservation check prevents this maintenance refill from injecting chakra into
an active staged-cost transaction. No independent per-fighter maximum field
or separate mid-round direct “reset to max” setter was found in the reviewed
native path.

### Gain and clamp behavior

`FUN_002254A0(amount, fighter, effect_flag, event_flag, threshold_flag)` is the
central gain function:

- it returns without changing chakra when any active temporary-effect entry has
  behavior flag `0x40`, fighter byte `+0x62` bit `0` is set, or fighter byte
  `+0x61` bit `3` is clear;
- otherwise it stores `fighter[+0x70] + amount` and upper-clamps to raw
  `15.0`;
- it does **not** lower-clamp. Native callers use it as a nonnegative adder;
- `threshold_flag` enables the `5/10/15` crossing test through
  `FUN_00225A40`, plus its associated sound/effect calls;
- `effect_flag` emits resource feedback through `FUN_001D87C0` and
  `FUN_0033CCD0`; and
- `event_flag` calls `FUN_002040D0(fighter, 0x19, -1, 1)`.

The flag names describe observed side effects rather than recovered original
names.

More exactly, `FUN_00225A40(old, new, threshold, fighter)` reports an upward
crossing only for `old < threshold <= new`, and a downward crossing only for
`new <= threshold < old`. It does nothing when `old == new`, when the threshold
is outside the closed old/new interval, or while the nested battle-manager
state at manager `+0x14` is nonzero. On an otherwise eligible interval it uses
`+0x1A0/+0x1A4` to suppress a repeated transition that ends at the same `new`
sample without advancing beyond the prior baseline, then stores `(old,new)`
back to that pair. Thus the pair is last-eligible-transition history, not a
second chakra value or timer. Spend paths deliberately write `15.0` only to
`+0x1A0`, biasing the next duplicate-suppression comparison while leaving
current chakra at `+0x70`.

`+0x1A8` is a separate one-byte feedback latch. Construction sets it to `1`;
`FUN_00227EE0` rearms it when the charge action's `+0x1B8` condition fires,
and clears it after the charge path accepts a raw `15.0` crossing. The adder
also consults it for the full-threshold feedback while action `(0,4)` is
active. No resource arithmetic uses this byte.

`FUN_00307230(fighter)` produces the temporary recovery factor. It starts at
`1.0`, walks `fighter[+0x8C8]` for `fighter[+0x8C4]` entries, and for each
active entry (`entry+0x6C != 0`) adds `entry[+0x94] - 1.0`. Multiple active
effects therefore stack as deviations from `1.0`, not as a product.

The clean authored effect-definition table makes the blocking flags concrete.
`FUN_003047C0` accepts definition IDs `0x00..0x89`; their records are
`0x64` bytes at runtime `0x0059E2A8` / ELF file `0x0049E3A8`.
`FUN_00304910` copies definition `+0x00/+0x04/+0x08` to entry
`+0x68/+0x6C/+0x70`. An exhaustive read of all 138 clean records found:

| Entry `+0x70` high flags | Definition IDs | Raw `+0x6C` lifetime | Relevant authored deltas |
| --- | --- | ---: | --- |
| `0x10`, `0x20`, and `0x40` (`0x72` including low flag `0x02`) | `0x0A`, `0x7C` | `0x0A`: `450`; `0x7C`: `-1` | ID `0x0A`: attach `0`, cleanup `0`; ID `0x7C`: attach `-15.0`, cleanup `-15.0`. |
| `0x80` (`0x82` including low flag `0x02`) | `0x0B`, `0x0E`, `0x0F`, `0x21`, `0x27..0x2B`, `0x38` | `0x0B`: `300`; all others: `600` | ID `0x0B`: attach/cleanup `0`; IDs `0x0E`, `0x0F`, `0x27..0x2B`, `0x38`: attach `+15.0`, cleanup `-15.0`; ID `0x21`: attach `+15.0`, cleanup `0`. |

No other clean definition sets any of bits `0x10/0x20/0x40/0x80`. All of
these blocker definitions author recovery modifier `+0x94` as `1.0`; their
effect on chakra therefore comes from the gates and listed signed deltas, not
from recovery-factor scaling. These are raw IDs and values, not inferred
player-facing effect names.

Effect lifetime is also explicit but remains in raw update units.
`FUN_00304D60` decrements `+0x6C` only while it is positive. When it reaches
zero, that helper calls `FUN_00304E90`, invokes the entry's virtual expiry
callback, and returns the removal signal; the enclosing `FUN_003059B0` update
then removes the entry from the fighter list. The cleanup delta is therefore
routed after this entry's active state has become zero, so its own
`0x40/0x80` flag no longer blocks that delta; another still-active entry can
still gate the canonical resource call. A negative lifetime such as ID
`0x7C`'s `-1` does not count down or expire through this path. No wall-clock
conversion is inferred.

Creation has the complementary ordering. `FUN_00305C30` substitutes the
definition's raw `+0x04` lifetime when its lifetime argument is `-1`, then
calls `FUN_00305270` on the fighter's `+0x8C4` list. The list helper removes a
replaceable same-ID entry, constructs the replacement through
`FUN_00304910`, and inserts it only after construction returns. Consequently,
the new entry's own behavior flags are not yet visible to the active-entry
scanners when its `+0xA4` attach delta is routed. Other entries already in the
fighter list can still block that delta. Together with the zero-before-cleanup
ordering above, this proves that an effect's own `0x40/0x80` flag does not
suppress its own attach or ordinary expiry delta.

Temporary effects also have a direct signed-delta path. `FUN_00304910`
applies nonzero entry `+0xA4` on construction/attachment, while
`FUN_00304E90` applies nonzero `+0xA8` during cleanup. During ordinary fighter
updates, `FUN_003059B0` calls `FUN_00307020`; that helper sums active-entry
`+0xB4` values and uses `+0xB8` boundaries to suppress an aggregate once the
fighter's current `+0x70` is already beyond the applicable boundary.

All three direct calls then use
`FUN_00306220(signed_amount, -1.0, fighter)`. The router first requires fighter
byte `+0x62` bit `0` clear, `FUN_00244110() == 0`,
`FUN_00244130(fighter) == 0`, and the same predicate to be zero for the linked
fighter at `fighter+0x20`. It then sends a positive amount to
`FUN_002254A0` with flags `(0,0,0)` and the magnitude of a negative amount to
`FUN_00225780` with flag `0`. Those canonical callees still enforce effect
flags `0x40` and `0x80`, respectively. The
canonical `15.0` upper clamp and `0.0` lower floor therefore still own the
actual resource bounds. The router contains a second-argument boundary gate,
but all three static callers pass `-1.0`; even when enabled, assembly shows
that this gate only suppresses the call or passes the original amount, rather
than trimming the amount to that boundary.

One exact side effect follows a successful negative delta of magnitude
`15.0`: if fighter `+0x7C` is nonzero, the router clears `+0x7C` and calls
`FUN_002260D0(fighter, 0)`. Because it clears the pending reservation first,
the reset helper cannot refund it; the reservation metadata is still cleared.

Representative non-substitution gain callers are:

- `FUN_00227EE0`, dispatched by `FUN_00249640` for action `(0,4)`, performs
  one charge-action update of
  `fighter_or_linked_source[+0x164] * 0.05 * FUN_00307230(fighter)` and calls
  the adder with flags `(0,0,1)`. This is an update formula only; no per-second
  conversion is inferred.
- `FUN_002369D0(base, fighter, event)` checks the event classification and,
  for a chakra-recovery event, adds
  `base * fighter[+0x164] * FUN_00307230(fighter)` with flags `(1,1,1)`.
- Loaded `BTL.BIN` function `0x00711720` (export
  `FUN_007116E0`, file `0x0005D820`) handles table-driven event IDs. Event
  byte `0x5D` calls resident `FUN_002254A0` with literal `2.5` and flags
  `(1,1,1)`, then invokes local overlay feedback when its controller pointer
  exists. That local JAL's encoded/live target is `0x0070D5F0`; the target
  bytes are at export `FUN_0070D5B0` / file `0x000596F0`, although the
  displaced Ghidra call reference is labeled `FUN_0070D5F0`. The resident
  chakra call instruction is loaded at `0x007118CC` (export `0x0071188C`,
  file `0x0005D9CC`).
- Loaded `FUN_0070BC20` (export `FUN_0070BBE0`, file `0x00057D20`) is a
  second event entry. It passes its computed base and event byte to
  `FUN_002369D0`; when that event byte is `0x0C`, it additionally calls the
  canonical adder with raw `15.0` and flags `(1,0,1)`. That add instruction is
  at export/file/live `0x0070BDB8/0x00057EF8/0x0070BDF8`. Its call to the
  recovery router is at `0x0070BCF8/0x00057E38/0x0070BD38`.
- Resident battle-event dispatcher `FUN_00374190` handles its event type
  `0x0C` by adding raw `15.0` with adder flags `(1,0,1)`. Other event types
  classified by the adjacent recovery predicates route to
  `FUN_002369D0`; this is another non-substitution event entry into the same
  canonical recovery machinery.
- Resident manager callback `FUN_0035AF20` has a positive-only synchronization
  path. When manager `0x00607600` exists with `+0x0C != 6` and
  `FUN_00373790() == 2`, it chooses fighter pointer `manager+0xDE8` for side
  index `0` or `manager+0xDE4` otherwise. If callback-state `+0x1C` exceeds
  that fighter's current `+0x70`, it passes exactly `target - current` to the
  adder with flags `(0,0,1)`. It does nothing to chakra when the target is not
  higher, so this is a gated top-up rather than an assignment or downward
  reset.

An aligned direct-JAL census accounts for every direct canonical-adder import
in the two clean images: eight in the resident ELF and two in `BTL.BIN`. The
resident sites are configured initialization, reservation release, charge,
general recovery, Practice refill, the signed effect router's positive branch,
the manager top-up, and event type `0x0C`; the two overlay sites are the
`0x0C` and `0x5D` event paths above. No other direct adder caller is omitted
from this map. Indirect dispatch remains outside that census.

### Spend, affordability, and lower clamp

`FUN_00225940(amount, fighter)` is a pure affordability predicate in the
reviewed path: zero cost succeeds, while nonzero cost fails when any active
temporary-effect entry has behavior flag `0x40` or
`fighter[+0x70] < amount`.

The three principal gate surfaces are intentionally different:

| Operation | Temporary-effect gate | Fighter-field gates | Result when blocked |
| --- | --- | --- | --- |
| Canonical add `FUN_002254A0` | active flag `0x40` | `+0x62` bit `0` must be clear; `+0x61` bit `3` must be set | Void return before resource arithmetic and before all requested feedback/event side effects. |
| Affordability `FUN_00225940` | active flag `0x40`, except an exactly zero cost bypasses the scan | No `+0x169` or `+0x62` bit `1` test | Returns `0` for a blocked nonzero request; it does not prove that a later debit gate will pass. |
| Simple debit `FUN_00225780` | active flag `0x80` only when `bypass_flag == 0` | `+0x169 != 1`; `+0x62` bit `1` must be clear | Returns `0` without arithmetic. A nonzero bypass skips only the effect scan, never the two fighter-field gates. |

This explains why “affordable” and “debited” are not equivalent: flag `0x40`
owns availability/gain, while flag `0x80` and the two fighter status fields own
ordinary spend. Staged-input eligibility adds its own flag-`0x10`, `+0x168`,
and `+0x84` gates before either surface.

`FUN_00225780(amount, fighter, bypass_flag)` is the central simple subtractor.
Unless its resource/status gates reject the operation, it performs:

```text
fighter[+0x70] = max(fighter[+0x70] - amount, 0.0)
fighter[+0x1A0] = 15.0
```

It returns `1` on that mutation and `0` when gated. The helper itself floors an
overspend instead of rejecting it, so callers that require affordability check
before invoking it. `FUN_00227CE0` is one such combined helper: it checks the
available amount and returns `0` on failure. On acceptance it emits feedback,
but performs the subtract/floor operation and `+0x1A0 = 15.0` write only when
effect flag `0x80`, fighter `+0x169 == 1`, and fighter `+0x62` bit `1` do not
block it. It calls `FUN_00305C30` with the requested authored-effect/event
arguments and returns `1` even when one of those later spend gates suppressed
the arithmetic. A zero requested amount goes directly to that effect/event
call and successful return.

`FUN_00225830(amount, fighter, feedback_mode)` is a second direct subtractor.
Modes `0` and `1` select different pre-debit feedback; modes `2..4` return
without spending. After its status gates it subtracts, floors at zero, and
sets `+0x1A0` to `15.0`, but it does not perform its own affordability check.
Representative callers `FUN_0025DCC0` (`0x0025DCC0`, ELF `0x0015DDC0`) and
`FUN_002B9400` (`0x002B9400`, ELF `0x001B9500`) first call
`FUN_00225940(1.5, fighter)` and only then use mode `0` to request raw `1.5`.

`FUN_00227850(other_delta, chakra_delta, fighter, cadence_mode, ..., ...)`
combines chakra mutation with separate action/effect work. In mode `0` it
requires affordability for `chakra_delta`, emits failure feedback otherwise,
then reaches a conditional subtract/floor branch. In mode `1` it rejects an
exactly empty chakra field but does not require the full requested amount. In
both modes, effect flag `0x80`, fighter `+0x169 == 1`, or fighter `+0x62` bit
`1` can suppress the debit and its `+0x1A0 = 15.0` history write without
rejecting the helper: its cadence feedback, separate `+0x6C` mutation, and
successful return can still proceed. The first float is the `+0x6C` delta and
must not be mistaken for the chakra argument. Several character-action
handlers call this helper with raw authored deltas; no substitution caller is
included here.

`FUN_0023A9A0(fighter, action_index, mode)` is the representative generic
action spend path. It resolves
`record = fighter[+0xA54] + action_index * 0x54`, reads raw chakra cost from
`record+0x20`, and, for the applicable record flag classes, emits the selected
feedback before reaching the debit branch. The debit, zero floor, and
`+0x1A0 = 15.0` write occur only when effect flag `0x80`, fighter
`+0x169 == 1`, and fighter `+0x62` bit `1` do not block them. Spend suppression
alone does not abort the subsequent action-dispatch machinery. Its larger call
graph covers ordinary action-record dispatch; no substitution-specific cost
path is included here.

`FUN_00225F50(amount, fighter, reservation_class)` is a distinct
reserve path used when the selected action record has one of flags
`0x00100000..0x00800000`. It accepts class values `2..4` and refuses a new
reservation when existing `+0x7C >= 15.0`. When no active effect has behavior
flag `0x80`, fighter byte `+0x169` is not `1`, and fighter byte `+0x62` bit `1`
is clear, it also subtracts and floors the requested amount and writes
`+0x1A0 = 15.0`. Crucially, failure of those spend gates does **not** fail the
reservation operation: the helper still stores the amount at `+0x7C`, stores
`class - 1` at `+0x80`, initializes `+0x82` to raw `0x3C` when that counter was
zero, emits its feedback, and returns `1`. It performs no independent
affordability test.

The ordinary input update has a second, inline staging path. When logical
input bit `0x08000000` is present and `FUN_00225B60` accepts the fighter,
`FUN_00248EC0` proposes either `(fighter[+0x18C] + 1) * 5.0` or, under its
alternate fighter-flag branch, a flat `5.0`. The predicate blocks staging when
an active effect has flag `0x10`, and its affordability portion blocks on
effect flag `0x40`; it checks the required current amount but does not check
spend-block flag `0x80`. The inline body therefore mirrors
`FUN_00225F50`: it subtracts/floors only if effect flag `0x80` and the two
fighter spend gates permit it, but still writes the staged amount to `+0x7C`,
advances/stores the class in `+0x80`, initializes `+0x82` to raw `0x3C` if
needed, and emits feedback regardless of whether those spend gates suppress
the debit. These
are raw native units and a logical input flag; no physical binding or UI scale
is inferred.

`FUN_002260D0(fighter, mode)` releases that state. Clean ELF bytes at file
`0x001261EC` decode as `lwc1 f12, 0x7C(a0)`; when nonzero, that amount is
passed to `FUN_002254A0` with zeroed flags. This is a **refund attempt**, not a
guaranteed add: the canonical adder can reject it on active effect flag `0x40`
or its fighter gates. The release helper then clears `+0x7C` regardless and
always clears `+0x80/+0x82`; it receives no success result from the void adder.
Consequently, the reservation is a refundable transaction claim rather than a
second chakra pool, and its recorded amount is not proof that an initial debit
occurred or a later refund succeeded.

Ordinary fighter maintenance makes this asymmetry explicit. While `+0x82` is
nonzero and the applicable active action record is not in a staged flag class,
`FUN_0024C440` decrements the counter only while effect flag `0x40` is absent.
It releases at zero; if flag `0x40` is present, it releases immediately. In
that immediate path the same flag blocks the refund adder, so the metadata is
cleared without restoration. A successful temporary-effect delta of exactly
`-15.0` instead clears `+0x7C` *before* calling `FUN_002260D0`, deliberately
discarding the pending refund while still resetting its metadata.

Two action-side consumers complete the staged-reservation lifecycle.
`FUN_00244F80` recognizes a matching active record in the staged flag classes,
calls `FUN_002260D0` to release the pending claim, and then conditionally
charges the selected `+0x18C` tier (`0/1/2 -> 5.0/10.0/15.0`) with the normal
zero floor and `+0x1A0 = 15.0` history write. The charge requires the two
fighter spend gates and either no active effect flag `0x80` or the special
entry-presence predicate `FUN_00307B20 == 1`; it is skipped when those gates do
not pass even though the action transition continues. The routine also
releases the linked fighter's reservation before that transition. Separately,
`FUN_00245340` handles an active class-`8` action phase: when its phase and
animation-marker gates pass, it releases the reservation, emits feedback, and
charges the active record's raw `+0x20` cost only when effect flag `0x80` and
the fighter spend gates permit it. These paths show that the selected action
can reach its commit transition even when a refund or committed debit was
suppressed; successful arithmetic remains owned by the ordinary chakra field.

Two other representative direct consumers are intentionally kept in raw
per-invocation terms:

- `FUN_00249D70` recognizes specific masked input-history patterns in fighter
  `+0xBB4`. Inside the admitted path it separately evaluates affordability or
  the presence of a pending reservation, updates surrounding counters/result
  state, and reaches a raw `0.008333334` debit branch. Effect flag `0x80`,
  fighter `+0x169 == 1`, or fighter `+0x62` bit `1` suppresses that arithmetic
  without necessarily suppressing the surrounding state progression. A
  performed debit floors current chakra at zero and stores `15.0` to `+0x1A0`.
  This is an invocation formula, not a rate conversion.
- `FUN_00237060` first releases any pending `+0x7C` reservation through the
  conditional refund path. It selects an integer in `3..5`, proposes
  `integer * 0.375`, reduces that amount to the
  available chakra when necessary, performs its associated event/effect call,
  then conditionally subtracts, floors at zero, and stores `15.0` to `+0x1A0`.
  Effect flag `0x80`, fighter `+0x169 == 1`, or fighter `+0x62` bit `1` can
  suppress the arithmetic after the event/effect has already occurred.
- Loaded overlay `FUN_00790830` (export bytes at `0x00790830`) requests
  positive raw amount stored in its controller object at `+0x5E8`, after its
  component/state gates pass. Loaded `FUN_007C47A0` unconditionally calls the
  subtractor with raw `7.5` when that wrapper is called, while loaded
  `FUN_007C6500` requests raw `5.0` only under its object-bit gate.
- Loaded `FUN_007F0C40` (export `FUN_007F0C00`) conditionally passes raw object
  `+0x10D8` to the subtractor for fighter pointer `+0x31C`; the direct call is
  at file/live `0x0013CE00/0x007F0D00`. Loaded `FUN_007FDE40` passes a computed
  aggregate to the same subtractor for fighter pointer `+0x4CC`, at
  `0x0014A370/0x007FE270`.
- Loaded block `0x00818380` (export `FUN_00818340`) starts with raw request
  `5.0`. When object `+0x9D8` is zero and the fighter reached through object
  `+0x9D4` has nonzero `+0x95A`, it multiplies that amount by `0.5`, yielding
  raw `2.5`; it then calls the subtractor at
  `0x00164544/0x00818444`. This is a proven guard-state/chakra interaction,
  but no player-facing action name is inferred.
- Loaded `FUN_00847070` (export `FUN_00847030`) requests raw `1.25` from fighter
  pointer `+0x31C` at file/live `0x001933CC/0x008472CC`.

All seven loaded direct debit sites pass subtractor bypass flag `0`, so active
effect flag `0x80` and the canonical fighter spend gates can suppress their
arithmetic. They use the standard zero floor. No player-facing action names or
rate conversions are inferred from these controller-local paths.

A direct-store census of the clean resident decompiler, restricted to pointers
proven to be fighter objects by their surrounding fighter fields, found current
chakra writes only in constructor `FUN_00214A40`, canonical routines
`FUN_002254A0/FUN_00225780/FUN_00225830`, reserve helper `FUN_00225F50`,
combined helpers `FUN_00227850/FUN_00227CE0`, discrete consumer
`FUN_00237060`, action-record spend `FUN_0023A9A0`, commit paths
`FUN_00244F80/FUN_00245340`, input staging `FUN_00248EC0`, and the small
direct consumer `FUN_00249D70`, plus the separately excluded owner below.
Recovery, configuration, effect, maintenance-refill, and loaded-controller
paths reach this same field through those canonical/inline writers rather than
introducing another max or shadow current field. Unrelated structures also use
offset `+0x70`; they were not counted merely from the numeric offset.

The excluded substitution-specific direct debit is not folded into these
generic paths; its separate owner is `FUN_002297D0`.

The repeated write of `15.0` to `+0x1A0` is not a resource refill: current
chakra remains at `+0x70`. It resets or biases the later threshold-crossing
history. `FUN_00225A40` supplies the strongest evidence for this limited label,
because on a crossing it compares `+0x1A0/+0x1A4` with the old/new samples and
then writes those samples back to the pair.

## Guard routine map

| Symbol | EE runtime | ELF file | Role |
| --- | ---: | ---: | --- |
| `FUN_00217BD0` | `0x00217BD0` | `0x00117CD0` | Action-exit dispatcher; routes guard stance `(0,5)` to `FUN_00228130`. |
| `FUN_002209A0` | `0x002209A0` | `0x00120AA0` | Hit router that selects guarded versus ordinary response from `+0x95A`. |
| `FUN_00228130` | `0x00228130` | `0x00128230` | Guard-stance exit cleanup. |
| `FUN_00228250` | `0x00228250` | `0x00128350` | Direct setter for guard state `+0x95A`. |
| `FUN_00228260` | `0x00228260` | `0x00128360` | Guard-entry eligibility predicate. |
| `FUN_00228320` | `0x00228320` | `0x00128420` | Per-update guard input and counter state machine. |
| `FUN_00228550` | `0x00228550` | `0x00128650` | Exit cleanup for guarded-response actions `(0,6)/(0,7)`. |
| `FUN_00228760` | `0x00228760` | `0x00128860` | Guarded-hit response; enters `(0,6)` or `(0,7)` and applies response side effects. |
| `FUN_00228B50` | `0x00228B50` | `0x00128C50` | Guarded-response follow-up; one callee exposed the false `+0x74` guard-gauge lead. |
| `FUN_00228E90` | `0x00228E90` | `0x00128F90` | Leaves guard stance or selects a response according to current hit state. |
| `FUN_00229130` | `0x00229130` | `0x00129230` | Adjacent action-eligibility helper that clears a positive `+0x95C` when another fighter-state mask is active; its broader mechanics are outside this document. |
| `FUN_00229B70` | `0x00229B70` | `0x00129C70` | Direct setter for timing state `+0x95C`. |
| `FUN_00229B80` | `0x00229B80` | `0x00129C80` | Multi-stage action update whose terminal cleanup clears `+0x95A` before `FUN_00228E90`. |
| `FUN_00232B80` | `0x00232B80` | `0x00132C80` | Ordinary, non-guarded hit response selected when `+0x95A < 1`. |
| `FUN_00238950` | `0x00238950` | `0x00138A50` | Mutates the linked fighter's support gauge at `+0x74`; not guard durability. |
| `FUN_00248580` | `0x00248580` | `0x00148680` | Action-state maintenance; leaves guard stance through `FUN_00228E90` after `+0x95A` clears. |
| `FUN_00248EC0` | `0x00248EC0` | `0x00148FC0` | Fighter input update; passes `fighter[+0x338]` to `FUN_00228320`. |
| `FUN_00249640` | `0x00249640` | `0x00149740` | Per-action update dispatcher; `(0,5)` performs the stance's interpolation/animation update. |
| `FUN_0024DA50` | `0x0024DA50` | `0x0014DB50` | Alternate maintenance path; duplicates only the `+0x95C` guard-input timing update while normal fighter processing is suppressed. |

The clean function starts at ELF `0x00120AA0` (`FUN_002209A0`) and
`0x00128420` (`FUN_00228320`) were checked directly against their exported
prologues.

The battle overlay also has a guard-sensitive attack dispatcher:

| Export bytes/function | Ghidra export | `BTL.BIN` file | Loaded EE | Role |
| --- | ---: | ---: | ---: | --- |
| `FUN_006FB840` | `0x006FB840` | `0x00047980` | `0x006FB880` | Large generated switch dispatcher; two cases call the resident `+0x95C` setter with sentinel `-2`. |
| `FUN_0072E590` | `0x0072E590` | `0x0007A6D0` | `0x0072E5D0` | Tests attack-record `+0x14` flags `0x00400000`, `0x00800000`, and `0x01000000` against fighter `+0x95A`, then conditionally invokes local attack processing. |
| `FUN_0072E700` | `0x0072E700` | `0x0007A840` | `0x0072E740` | Actual start of the local processing callee selected by the dispatcher. It consumes the guard-present selector and tests fighter `+0x95A` again. |

The local call at export `0x0072E698` / file `0x0007A7D8` executes at live
`0x0072E6D8`. Its clean bytes `D0 B9 1C 0C` encode the already-live target
`0x0072E740`; the corresponding callee bytes begin at export `0x0072E700`.
Ghidra's extra `FUN_0072E740` label is therefore `0x40` into that exported
function, not a second live-address mapping. The two imported setter calls at
export `0x0072E5F8` / `0x0072E624` (files `0x0007A738` / `0x0007A764`, live
`0x0072E638` / `0x0072E664`) contain `94 A0 08 0C` and directly target the
resident `FUN_00228250` at `0x00228250`.

The generated switch function has two additional indirect guard-state writes.
At export/file/live `0x006FBE40/0x00047F80/0x006FBE80` and
`0x006FC27C/0x000483BC/0x006FC2BC`, clean bytes `DC A6 08 0C` encode
`jal 0x00229B70`. Both sites load a fighter pointer from the per-slot table at
`0x008D65AC + slot * 0x1E0`, place raw `-2` in `a1`, and call the resident
direct setter for fighter `+0x95C`. The decompiler did not recover the parent
switch table, so no player-facing names are assigned to those two cases. They
establish character/overlay control of the timing sentinel, not a durability
decrement.

### Guard input and action lifecycle

`FUN_00248EC0` reads the current input word from fighter `+0x338` and calls
`FUN_00228320(fighter, input)`. In that function, bit `0x10000000` is the
logical guard input:

- while held, `+0x95C` increments; on release it becomes zero; a negative
  value increments toward zero instead;
- if the fighter passes the state, lock, and eligibility checks, holding guard
  enters `FUN_00217E40(fighter, 0, 5, 0)` and increments `+0x95A` up to
  `0x7FFF`;
- releasing guard clears `+0x95A`; ineligible states also clear it; and
- action-state maintainer `FUN_00248580` checks `(0,5)` and calls
  `FUN_00228E90` when `+0x95A` is zero, leaving the stance or selecting the
  appropriate response state. `FUN_00249640` separately performs the
  stance's interpolation/animation update.

`FUN_0024DA50` has a secondary maintenance branch for an active fighter whose
normal `+0x20C < 1` processing path is unavailable. It repeats the same
negative-toward-zero, release-to-zero, held-increment update for `+0x95C`, but
does not increment `+0x95A` or enter stance `(0,5)`. This independently
separates the input-age counter from the accepted guard-state counter.

The action-exit dispatcher `FUN_00217BD0` independently routes `(0,5)` to
`FUN_00228130`. That cleanup restores orientation/interpolation state when the
fighter is no longer in the guarded action. Response actions `(0,6)` and
`(0,7)` route to `FUN_00228550`.

These relationships prove that `(0,5)` is the active guard stance and that
`+0x95A/+0x95C` are temporal guard/input state. Neither field behaves like a
finite durability pool: both rise with held time rather than fall under
guarded hits.

### Guarded-hit selection and break-like flags

`FUN_002209A0` is a representative hit-routing path. After collision and
attack-property checks, it selects:

```text
fighter[+0x95A] < 1   -> FUN_00232B80(...)  ordinary hit response
fighter[+0x95A] >= 1  -> FUN_00228760(...)  guarded-hit response
```

The guarded response enters action `(0,6)` or `(0,7)` according to the
direction/state calculation, updates reaction state, and calls
`FUN_00228B50`. Detailed damage behavior is outside this document.

Before the resident branch, two attack-record `+0x14` flags can invalidate
guard state:

- `0x00800000`, under the facing/state condition visible in the router, changes
  a nonzero `+0x95A` to sentinel `-1`; and
- `0x00400000` clears `+0x95A` to zero.

Either result is `<1`, so that hit follows the ordinary-response branch even
if guard input had been active. This is a proven break/bypass *mechanism* at
the code level, but the static evidence does not establish which flag, if
either, is named “guard break,” “unblockable,” or something else by the game
data authoring format.

Loaded overlay `FUN_0072E590` independently confirms both writes and exposes
a third guard-sensitive flag. Its decision order is:

- `0x00400000`: call `FUN_00228250(fighter, 0)`, then process the record;
- otherwise `0x00800000`: call `FUN_00228250(fighter, -1)`, then process it;
- otherwise `0x01000000`: process it regardless of `+0x95A`; pass selector
  `1` when `+0x95A` is nonzero and `0` when it is zero; and
- with none of those flags: process it only when `+0x95A` is zero.

The third flag does not clear, decrement, or refill `+0x95A`; it preserves the
field and tells the downstream overlay routine whether guard was present. The
dispatcher finishes by setting its owning object's `+0x20C` word to `1`.
Those are proven code effects, but they do not establish player-facing names
for any of the three flags.

An exact static scan of the clean `BTL.BIN.c` export found 34 direct textual
reads of fighter `+0x95A` and no direct textual field access to `+0x95C`.
However, a raw-JAL census found the two `FUN_00229B70` calls above, so the
overlay does set `+0x95C` indirectly. This distinction is why decompiler text
alone is insufficient for a writer census. The same raw scan found exactly
two calls to the `+0x95A` setter, at files `0x0007A738/0x0007A764`, and exactly
two calls to the `+0x95C` setter, at files `0x00047F80/0x000483BC`.

A complete direct-writer census in the clean resident export found only nine
routines touching either guard counter: constructor `FUN_00214A40`, hit router
`FUN_002209A0`, setters `FUN_00228250`/`FUN_00229B70`, input updater
`FUN_00228320`, adjacent eligibility helper `FUN_00229130`, terminal action
cleanup `FUN_00229B80`, ordinary response `FUN_00232B80`, and alternate input
updater `FUN_0024DA50`. The battle overlay has no direct assignment to either
field; it invokes the resident `+0x95A` setter with `0/-1` and the resident
`+0x95C` setter with `-2`. Apart from the arbitrary-value
setters, the resident writes are initialization/clear, `-1` sentinel, or
one-step increment (including a negative `+0x95C` moving toward zero). No
writer performs attack-strength subtraction or any other decrement toward a
break threshold. This census includes direct field syntax and the byte-pair
zero used by `FUN_0024DA50` for `+0x95C`.

### No proven guard-durability resource

No persistent guard-durability accumulator or maximum was established in the
reviewed native guard path. In particular:

- no guarded-hit path decrements `+0x95A` or `+0x95C` by attack strength;
- no clamp-to-zero or cumulative break threshold exists on those fields;
- the branch to an ordinary hit after the state-invalidating attack flags is per-hit state
  invalidation, not depletion of a meter; and
- action `(0,5)` performs stance/animation work but no resource decrement;
  overlay flag `0x01000000` likewise selects a branch without changing either
  guard counter.

This is a strong negative result for the traced guard entry, exit, and
representative hit paths, not a mathematical proof that no character-specific
or scripted exception exists anywhere in the program.

## Rejected candidates and remaining hypotheses

### `ccEffCond_AbsGuard` is an effect class, not a durability pool

The resident image contains the exact internal class string
`ccEffCond_AbsGuard` at runtime `0x005A5C20` / ELF file `0x004A5D20`, and its
vtable begins at runtime `0x005DB240` / file `0x004DB340`. Clean bytes confirm
both the string and vtable rather than relying only on Ghidra labels. The class
constructor is `FUN_00345FF0` (runtime `0x00345FF0`, file `0x002460F0`), with
destructor `FUN_00346100` and virtual updates `FUN_00346210` and
`FUN_003462A0`.

This named class owns a visual/effect object at class `+0xA0` and an owner
pointer at class `+0xA8`. Its update optionally copies owner `+0x310` into the
effect object when owner byte-zero bit `2` is set, then updates effect position
and transform data. The class does not read or write fighter `+0x95A`,
`+0x95C`, or chakra; it has no decreasing counter, maximum, or break
transition. The name is useful corroboration that the game has an authored
“AbsGuard” effect concept, but it is not evidence for a persistent native
guard-durability resource.

### Fighter `+0x74` is support, not guard

The most plausible false lead was fighter `+0x74`. It is initialized to `1.0`
by `FUN_002151E0` through `FUN_00238080`, read by the support-button handler
`FUN_00238340`, and clamped to `[0.0,1.0]`. More decisively,
`FUN_00238950` follows fighter `+0x20` to the linked fighter, adds a hit-derived
amount to that linked fighter's `+0x74`, and clamps it to `[0.0,1.0]`.
`FUN_00228B50` calls this from guarded-response work, which is why a shallow
caller trace can make the field look like guard durability. It is the support
resource and is not part of the guard-state map.

The adjacent `+0x78` is initialized from `FUN_002380C0` and participates in
support-gauge recovery. It is likewise not a guard maximum.

### Hypotheses requiring new evidence

- Attack-record `+0x14` flags `0x00800000` and `0x00400000` are likely two
  authored guard-bypass/guard-invalidation categories, while `0x01000000`
  explicitly selects a guard-present overlay branch. Naming any of them
  requires correlating clean attack records with isolated runtime outcomes.
- Negative sentinels in `+0x95A` and `+0x95C` clearly change short eligibility
  windows, but their complete cross-system meanings are broader than guard and
  were intentionally not followed here.
- A character-specific or scripted guard exception may exist outside the
  representative native routes. Any future claim of a durability meter should
  first show a per-fighter field that is initialized, decremented by guarded
  hits, clamped, and consumed by a break transition. None of those four links
  was found together here.

## Confidence summary

- **High:** clean binary identity; address/file-offset mappings; current
  chakra at `+0x70`; literal maximum `15.0`; recovery multiplier `+0x164`;
  add/subtract clamps; constructor, charge, recovery, generic action-cost, and
  `BTL.BIN` event call paths.
- **High:** logical guard bit `0x10000000`; guard stance `(0,5)`; temporal
  fields `+0x95A/+0x95C`; guarded versus ordinary hit branch; exact effects of
  attack flags `0x00800000` and `0x00400000` on `+0x95A`; overlay branch
  selection by `0x01000000`.
- **Medium:** descriptive names for the threshold-history pair and the two
  guard timing counters.
- **Medium negative confidence:** the traced native system has no cumulative
  guard-durability meter. Character-specific and scripted exceptions remain
  unverified.
