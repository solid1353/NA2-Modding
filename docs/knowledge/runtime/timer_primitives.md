# Shared timer and frame-event primitives

This document records the shared timer and frame-event primitives in the
retail NA2 (`SLPS-25837`) boot ELF: a fractional integer-cursor block with
its event predicates, a fixed-point remaining/elapsed countdown block, and an
integer time-unit conversion. Resident addresses are ELF runtime addresses;
complete-file offsets and overlay addresses follow the
[address conventions](../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** Shared countdown/count-up/fractional timer implementations, arithmetic/rounding/wrap/sentinels, reset/arming and event-crossing tests, including exact call contracts and selected caller classifications.
- **Exploration depth:** All fractional helpers `0x00211730..0x00211F80` and fixed-point helpers `0x001EB9B0..0x001EBBC8` were read; arithmetic and predicates were checked in decompilation and instructions. All eight recovered resident forward-advance sites, six countdown sites and five divide-by-60 sites were examined in their callers. The additional direct BTL forward caller, selected event consumers, session/startup resets, boot FCSR clear and local maintenance ordering were examined.
- **Confirmed coverage:** Both block layouts, exact accumulator loops, current/previous/predicted views, flag/reset/arming contracts, forward reserved-value retreat, five event/range predicates, fixed-point terminal and cap ordering, stored-step quantization and signed integer division below.
- **Unresolved or untested:** Fixed-point `+0x18` consumer meaning, complete indirect-call coverage and exceptional delta/divisor inputs are not established. Wall-clock duration of a timer count, and whether these are every retail timer implementation, are not established.
- **Deliberate exclusions and overlap:** This document owns reusable timer contracts. Fighter-specific phase meanings belong to [Hit response](../gameplay/hit_response.md), combo ownership to [Damage](../gameplay/damage.md), and countdown presentation/suppression to [Pause and replay](../gameplay/pause_and_replay.md). CCS playback belongs to [Animation runtime](animation_runtime.md); presentation fades/easing to [UI animation](ui_animation.md); cue behavior to [Battle audio](../gameplay/battle_audio.md); EE FPU rounding to [Randomness](randomness.md#ee-hardware-conversion-and-software-packing). Complete-file identities remain in [Retail game file identities](../game/files/file_identities.md).
- **Evidence limitations:** Evidence is static retail NA2 `SLPS_258.37` code. Preserved function boundaries and xrefs are incomplete; a negative xref result is not a whole-program proof. No display cadence or exceptional-input caller guarantee is inferred from the helpers alone.

## Fractional integer-cursor block

`FUN_00211730(a0=block)` stores `0x005DA070` at `+0x20`, calls the reset helper,
and returns the original pointer. Its owned footprint is `0x24` bytes; the
reset and arithmetic helpers touch `+0x00..+0x1F`, preserving `+0x20`.

| Offset | Representation | Established contract |
| --- | --- | --- |
| `+0x00` | `u16` | Reset to zero; not consumed by the scoped arithmetic/event helpers. |
| `+0x02` | `u16` flags | Bits `0/1` are set on integer advance or explicit assignment, cleared when an update extracts no whole unit. Bit `1` has a separate clear helper. Bit `2` survives advancement; bit `3` is cleared by advancement. |
| `+0x04` | `s32` | Integer value copied by explicit assignment; neither advance helper changes it. |
| `+0x08` | `s32` | Previous integer value, refreshed only when at least one whole unit is extracted. It can remain older than the immediately previous call. |
| `+0x0C` | `s32` | Current integer cursor/count. |
| `+0x10` | `float32` | Previous call's fractional position. |
| `+0x14` | `float32` | Current position: signed integer `+0x0C` converted to float plus remainder `+0x1C`. |
| `+0x18` | `float32` | Predicted next position, current position plus forward delta or minus countdown delta; countdown prediction is clamped at zero. |
| `+0x1C` | `float32` | Fractional remainder accumulated by repeated addition/subtraction of `1.0`. |
| `+0x20` | pointer word | Constructor stores `0x005DA070`; semantic type name is not recovered. |

### Reset, assignment and flag contracts

| Resident routine / complete-file offset | Call contract | Mutation |
| --- | --- | --- |
| `0x00211730` / `0x111830` | `a0=block`, `v0=block` | Initializes pointer `+0x20`, then resets. |
| `0x00211770` / `0x111870` | `a0=block` | Clears `+0x00`, all three integer words and all four float words; assigns flags `3`. |
| `0x002117A0` / `0x1118A0` | `a0=block`, `a1=s32 value` | Copies value to `+0x04/+0x08/+0x0C`, converts it with `cvt.s.W` to `+0x10/+0x14/+0x18`, clears remainder, and assigns `(flags | 3) & 0xFFF3`. |
| `0x00211F70` / `0x112070` | `a0=block` | Clears only flags bit `1`; leaves positions/remainder unchanged. |

Reset/assignment arm the exact-integer event path even though no advancement
has occurred. Assignment clears both pending bit `2` and bit `3`; reset does
not preserve old flags. Signed integer-to-float conversion is an actual
`cvt.s.W` instruction, not a float-to-integer truncation of elapsed time.

### Forward and reverse arithmetic

Both advance routines use `a0=block`, `f12=float delta`. They do not read an
external clock, a scheduler, a pause word or their own pending flag.

`0x00211D80..0x00211E60` (file `0x111E80..0x111F60`) adds delta to remainder.
If remainder is at least `1.0`, it first snapshots current integer to previous
integer, then repeatedly subtracts `1.0` and increments the integer. Reaching
integer `0x7FFFFFFF` immediately replaces it with `0x7FFFFFFD`
(`0x00211DD0..0x00211DF0`). This is a two-step retreat from that reserved
value, not saturation and not reset to zero. No other integer wrap check
appears in this routine. If no whole unit is extracted, bits `0/1` are cleared;
otherwise both are set. The routine then copies old fractional current to
previous, computes current as integer plus remainder, predicts current plus
delta, and clears bit `3`.

`0x00211E70..0x00211F60` (file `0x111F70..0x112060`) subtracts delta from
remainder. If remainder is at most `-1.0`, it snapshots the integer, repeatedly
adds `1.0` and decrements the integer, then clamps a negative integer to zero.
The clamp occurs only in this whole-unit branch; the helper does not
unconditionally clear a negative count. Flags and float-history updates follow
the forward pattern, but prediction is current minus delta and is clamped at
zero. The current float and remainder themselves are not clamped at zero.

For finite nonnegative deltas whose unit loops terminate, and a reset/assigned
block, forward extraction leaves remainder in `[0,1)` and countdown extraction
in `(-1,0]`. **Inference from these loops:** a delta of `0.5` changes the
integer every second call,
while fractional views change each call. Countdown integer zero can coexist
with a negative fractional current after an overshoot. These are invocation
units; the helpers do not establish seconds or display-frame units.

The instructions use `addiu` for integer steps and `add.S/sub.S` for fractional
steps. There is no float-to-integer conversion, automatic rounding to nearest
integer, delta validation or loop-iteration cap. The scoped callers' valid
delta domain requires separate evidence. EE FPU rounding is fixed in hardware,
as recorded in
[Randomness](randomness.md#ee-hardware-conversion-and-software-packing).

Boot entry `0x00100118` (file `0x218`) explicitly clears FCSR. Its bytes are
`00 F8 C0 44`, the `ctc1 zero,fcsr` encoding which Ghidra displays as
`clear fcsr`. Searching `00 F8 ?? 44` in the three exposed in-scope binaries
and filtering to aligned CTC1 encodings recovers this write; the other aligned
boot hit at `0x0010010C` is `mtc1 zero,f31`, a data-register clear. This
establishes the boot control value `0`. It does not select a rounding mode,
because the EE rounding-mode bits are hardwired. None of the scoped timer
helpers writes FCSR.

### Event and interval predicates

All five predicates below return Boolean `0/1` in `v0` and leave the block
unchanged. They contain no event-consumption store. Their instruction bounds
are `0x002117F0..0x00211898`, `0x002118A0..0x00211A14`,
`0x00211A20..0x00211B94`, `0x00211BA0..0x00211C70`, and
`0x00211C80..0x00211D74` respectively.

| Routine / complete-file offset | Arguments | Exact contract for ordinary non-wrapping integer differences |
| --- | --- | --- |
| `0x002117F0` / `0x1118F0` | `a0=block`, `a1=event` | If current minus previous integer is at least `2`, searches previous-exclusive/current-inclusive increasing integers; if at most `-2`, searches the corresponding decreasing integers. For differences `-1/0/1`, compares only current to event. Ignores flags and all floats. |
| `0x002118A0` / `0x1119A0` | `a0=block`, `a1=event` | Fractional predicate described below, exact-integer path enabled by flags bit `0`. |
| `0x00211A20` / `0x111B20` | `a0=block`, `a1=event` | Identical fractional predicate, exact-integer path enabled by flags bit `1`. |
| `0x00211BA0` / `0x111CA0` | `a0=block`, `a1=low`, `a2=high` | Uses the same integer traversal as `0x002117F0`, succeeding if any visited integer is inside inclusive `[low,high]`; for `-1/0/1` differences, checks only current. |
| `0x00211C80` / `0x111D80` | `a0=block`, `a1=low`, `a2=high`, `a3=period` | Applies signed MIPS `div` remainder separately to previous/current integers; when previous remainder is nonzero and current remainder zero, substitutes period for current. Then applies the same inclusive-range traversal to these two values. No divisor guard or whole-cycle reconstruction exists here. |

Integer predicates subtract with `subu` and choose direction through signed
comparisons. The table does not claim sensible elapsed-time semantics after a
32-bit difference overflows. The modulo helper is not a general circular
interval algorithm: direction follows the reduced endpoints, and a complete
cycle whose two remainders coincide is indistinguishable from no movement.
Only the explicit nonzero-to-zero endpoint case is adjusted.

For either fractional predicate, let `C` be integer current, `R` remainder,
`P/F/N` previous/current/predicted float positions, and `E` the signed event
converted to float. For finite comparable values the branch contract is:

1. With the selected flag set, `C == event` and `R == 0` succeeds immediately.
   With that flag clear and `R == 0`, it fails immediately.
2. All remaining paths fail for event `0` or `P == F`.
3. For increasing `P < F`, require `P < E < N`. Normally also require
   `F <= E <= N`. Event `1` with previous integer `0` instead requires
   `P <= E <= F`.
4. For decreasing `F < P`, require `N < E < P` and `N <= E <= F`.

Thus the usual increasing interval can report a nonzero event before current
has reached it, but excludes the predicted endpoint. The special event-`1`
case waits for current to reach it. Reverse uses a predicted-exclusive,
current-inclusive lower window. Event `0` succeeds only through step 1; a
clamped integer zero with a nonzero remainder is insufficient. There is no
epsilon comparison and no hidden one-shot latch in either routine.

**Inference:** repeated queries without mutation return the same result.
Clearing bit `1` with `0x00211F70` suppresses `0x00211A20` at an exact
integer/remainder-zero boundary while leaving `0x002118A0` enabled by bit `0`.
It does not disable either predicate's fractional paths when remainder is
nonzero. This distinction matters when a caller skips advancement but still
runs event consumers.

### Bounded callers and scheduling ownership

Resident xrefs recover eight forward-advance call instructions in six
functions and six countdown calls in two functions. Every one was examined in
its containing function. A direct-JAL byte search of the exposed BTL import
adds one forward caller and one bit-`1` clear call in the same function. ETC
has no match for those forward/countdown/bit-clear encodings in this search.
These sets do not exclude indirect calls or unexamined timer implementations.

| Owner / block address relative to owner | Calls and rate source | Local gate/order |
| --- | --- | --- |
| Fighter `0x0024D5E0`, blocks `+0x1B8/+0x1DC` | `0x0024D608` uses fighter `+0x1AC`; `0x0024D6D8/0x0024D6F0` use `(u16 +0xB90 / 256) * +0x1AC`, with exact `0x100` handled directly. | Current pause count `+0x20C > 0` skips both advances and clears each block's bit `1`. A separate `+0xB98` reset request can zero the secondary block instead of advancing it. |
| Combo manager `0x0020C420`, block `+0x10` | Countdown at `0x0020C4F4` uses literal `1.0`; assignment at `0x0020C570` uses `90`. | Decrement only while block current `manager+0x1C` is nonzero; decrement precedes pending-count consumption/rearming in the same call. [Damage](../gameplay/damage.md) owns combo meaning. |
| Fighter maintenance `0x0024C440`, blocks `+0x248/+0x26C/+0x290` | Countdown calls `0x0024C7DC/0x0024C838/0x0024C8AC` use fighter `+0x1AC`. | Inside fighter flags-byte bit `1` branch and only when pause current `+0x20C < 1`. First block checks integer nonzero; second/third query fractional event `0` before updating. Second can perform pending activation instead. |
| Same maintenance, block `+0x224` | `0x0024C908` uses saved `f20=1.0`. | Under the preceding gates, queries event `0`, then decrements or activates. With pause positive, a pending block can still activate at `0x0024C970..0x0024CA08`, but is not decremented. [Hit response](../gameplay/hit_response.md#accepted-hit-rejection-countdown) owns the rejection role. |
| Same maintenance, block `+0x200` | `0x0024CA74` uses literal `1.0`. | Runs after the flags-byte bit `1` branch; queries event `0`, then decrements or activates. It is later than the three rate-scaled channels in this function. [Hit response](../gameplay/hit_response.md#fighter-update-pause-and-action-lock) owns the pause/action-lock consequences. |
| Auxiliary tracker `0x002662A0`, fighter `+0x5084` | `0x002663DC`: model-pointer `fighter+0x5114`, its `u16 +0x94 / 256`. | Advances only when `0x00224650(fighter)==0`; otherwise clears bit `1` at `0x002663F0`. |
| Auxiliary trackers `0x0029F3F0`, fighter `+0x5528/+0x55A8` | `0x0029F5A0` in a two-element loop: corresponding model `u16 +0x94 / 256`. | Same pause predicate; two bit-clear calls through loop site `0x0029F5DC`. |
| Auxiliary trackers `0x002A9AA0`, fighter `+0x5BF8/+0x5C78` | `0x002A9C08` in a two-element loop: corresponding model `u16 +0x94 / 256`. | Same predicate; bit-clear loop site `0x002A9C44`. |
| Auxiliary tracker `0x002AF360`, fighter `+0x4E68` | `0x002AF4E4`: model-pointer `fighter+0x4EF4`, its `u16 +0x94 / 256`. | Same predicate; clear at `0x002AF4F8`. |
| Auxiliary tracker `0x002DC390`, fighter `+0x6168` | `0x002DCA6C` uses fighter `+0x1AC`. | Same predicate; clear at `0x002DCA80`. |
| BTL linked-node manager, preserved function `0x007243A0`, node block `+0x10` | Preserved `0x00724708` / live `0x00724748` / file `0x70848`: forward delta `max(node+0x5C, fighter+0x1AC)`. | Before advancement, `0x00211BA0(block, signed node+0x08, 0x7FFF)` checks the duration range. A successful range check takes the expiry callback path instead. Otherwise the same pause predicate chooses forward advance or bit-clear at preserved `0x0072471C` / live `0x0072475C` / file `0x7085C`. |

`0x00224650..0x0022465C` is exactly the signed comparison
`fighter+0x20C > 0`. Auxiliary tracker pause behavior above therefore has
instruction evidence rather than an inferred function name. These trackers
are distinct embedded instances, not one shared global cursor. Their
character/puppet meanings remain with gameplay ownership.

Pending activation is caller code, not a generic advance-helper feature.
Maintenance tests block bit `2`, negates current integer, copies that value to
all three integer views and its float conversion to all three float views,
clears remainder, and uses `(flags | 3) & 0xFFF3`. It takes this branch instead
of calling the decrement helper. The pending bit therefore does not itself
freeze a direct call to `0x00211E70`; the caller must select the activation
path. In `+0x26C/+0x224/+0x200`, the event-`0` query also precedes the
pending-bit branch, so an enabled zero assignment can skip that branch.

Two selected event-consumer classes show that the caller chooses the helper:

- `0x0021A6D0`, callsites `0x0021A7C8/0x0021A7EC`, chooses fractional
  `0x002118A0` or integer `0x002117F0` according to its third argument.
  Descriptor bits choose fighter primary or secondary block; this caller
  handles its own signed frame-relative values and `0x7FFF` omission sentinel.
  Those are caller policies, not generic timer sentinels.
- `0x0021FC70`, callsites `0x0021FEF4/0x0021FF34`, chooses modulo
  `0x00211C80` when animation descriptor `+0x28 & 2` is set, otherwise ordinary
  range `0x00211BA0`. The period is descriptor integer `+0x0C - 1`, narrowed
  and sign-extended as a signed halfword before being passed in `a3`.
  Animation rates below `0x100` have an additional authored-frame comparison
  in the caller which can replace the predicate result; the timer helper alone
  does not determine that consumer's final decision.

The independently enabled exact boundary is also used by `0x002092D0` at
`0x002092F4` (`0x00211A20(fighter+0x1B8,0)`) before its action-dependent
effect dispatch, and by `0x0020D690` at `0x0020D73C` on secondary block event
`0`. [Awakening](../gameplay/awakening.md) owns the latter gameplay contract.

### Selected outer order

`0x0024FD80` traverses its fighter list with `0x0024C440` as the first pass
(`0x0024FDD0`). This establishes countdown maintenance before that function's
later state/contact passes. Separately, `0x0024DE40` performs its own gated
contact-range work, the virtual callback at fighter table `+0x2C`, and
`0x00217670(fighter,6)` before calling timeline advance at `0x0024E018`.
Its early-return and flags gates can omit the advance entirely.

`0x0024DA50` calls effect producer `0x002092D0` at `0x0024DB6C`, then audio
producer `0x00204610` at `0x0024DB78`, outside its inner positive-pause branch
but inside fighter flags-byte bit `1`. The selected audio event-`0` call at
`0x00204698` uses `0x00211A20(fighter+0x1B8,0)`; major action `8` instead
supplies its descriptor-authored event. These consumers do not advance the
timer by calling the predicate. [Battle audio](../gameplay/battle_audio.md)
owns emitted cues and their other gates. The local order above does not alone
establish how often the outer scheduler invokes the three owner functions.

## Fixed-point remaining/elapsed block

`0x001EBA80..0x001EBB64` (file `0x0EBB80..0x0EBC64`) operates on a different
`0x20`-byte record, with `a0=block` and Boolean terminal result in `v0`.
The examined retail instance begins at `0x006B28D0`; it is not interchangeable
with the float-remainder block above.

| Offset / global address | Representation | Established role |
| --- | --- | --- |
| `+0x00` / `0x006B28D0` | flags byte | Bit `0` suppresses work, bit `1` freezes the paired arithmetic, bit `2` is terminal. Other bits are preserved by the inspected reset and flag setters. |
| `+0x04` / `0x006B28D4` | signed-tested 32-bit fixed-point | Remaining value; initialized by integer source shifted left `24`. |
| `+0x08` / `0x006B28D8` | unsigned-capped 32-bit fixed-point | Elapsed value; capped at `0x63000000` before terminal handling. |
| `+0x0C/+0x10` / `0x006B28DC/0x006B28E0` | words | Cleared by session/startup reset, not used by `0x001EBA80`; their snapshot use belongs to [Practice mode](../gameplay/practice_mode.md). |
| `+0x14` / `0x006B28E4` | integer word | Initial configured whole-unit count; terminal branch replaces elapsed with this value shifted left `24`. |
| `+0x18` / `0x006B28E8` | word | Session/startup reset assigns `-1`; no behavioral consumer is established. |
| `+0x1C` / `0x006B28EC` | fixed-point delta word | Subtracted from remaining and added to elapsed; initialized to `0x00044444` by session/startup reset. |

The remaining/elapsed representation has 24 fractional bits, established by
initialization's left shift, terminal replacement's left shift and consumers'
right shift. The stored step is integer-quantized:
`0x00044444 = floor(2^24 / 60)`. **Arithmetic consequence:** sixty eligible
updates sum to `0x00FFFFF0`, sixteen fixed-point units less than `1 << 24`.
This establishes a nominal sixty-update whole-unit scale; it does not by itself
establish display or wall-clock cadence.

### Advance, suppression and terminal ordering

The complete local sequence is:

1. If terminal bit `2` is already set, return `1` immediately without touching
   remaining/elapsed, even if suppression bit `0` is set.
2. Otherwise, initialize return `0`; suppression bit `0` returns it without
   any remaining/elapsed check.
3. With bit `0` clear, bit `1` skips subtraction/addition. Otherwise perform
   32-bit `subu/addu`: remaining minus delta and elapsed plus delta. Clamp
   elapsed to `0x63000000` only if its new **unsigned** value exceeds that
   constant.
4. Regardless of bit `1`, check remaining as signed. A negative value is
   clamped to zero, terminal bit `2` is set, elapsed is overwritten with
   `initial_integer << 24`, and return becomes `1`.

The endpoint comparison at `0x001EBB04..0x001EBB10` is `remaining < 0`, not
`<= 0`. Therefore an exact zero reached by arithmetic leaves bit `2` clear
until a later eligible decrement; a previously negative remaining value can
terminate even while bit `1` freezes arithmetic. The terminal overwrite of
elapsed happens after its cap, so the helper does not guarantee the cap for an
arbitrary caller-provided initial integer. It does not validate delta or
prevent 32-bit wrap.

### Clear versus configured reset

| Routine / instruction bounds | Exact reset/arming contract |
| --- | --- |
| Generic clear `0x001EBA10..0x001EBA78` (file `0x0EBB10..0x0EBB78`) | `a0=block`; clears flags bits `0/1/2`, preserving the remaining byte bits; zeros every word `+0x04..+0x1C`, including delta. It does not install `0x00044444`. |
| Cleanup-shaped wrapper `0x001EB9B0..0x001EBA0C` | With nonnull `a0`, calls the generic clear. A positive signed low halfword of `a1` additionally calls `0x00117000(a0)`. Returns original pointer. This is not the session's configured reset. |
| Session reset `0x001ED16C..0x001ED210` inside `0x001ED110` | Global block: clears bits `0/1/2`, remaining, elapsed and both snapshot words; assigns initial integer `99`, `+0x18=-1`, and delta `0x00044444`. |
| Startup `0x005D833C..0x005D83E0` inside `0x005D82F0` | Same global-block values as the session reset, corroborated in instructions and bytes. |
| Round initialization `0x001EEE4C..0x001EEEE0` inside `0x001EEE30` | Sets bit `0`, clears bit `2`, assigns initial integer from manager selector `6`, sets remaining to that result `<<24`, sets terminal bit if the shifted remaining is zero, and clears elapsed. Preserves delta and bit `1`. |

[Pause and replay](../gameplay/pause_and_replay.md#battle-countdown-gate-and-presentation)
owns the battle use and presentation. Its configured reset is `0x001ED110`;
the generic clear has the separate zero-delta contract shown above.

`0x001EBBA0..0x001EBBC8` writes global flags bit `1` from `a0 & 1`, preserving
all other bits. `0x001F0290` assigns bit `0` at
`0x001F0350..0x001F0394` from the two suppression words before complementing
them into the controller masks. The sole recovered resident advance call is
`0x001F11B8` in `0x001F10F0`; that caller has additional fighter/session gates.
No claim that these bits alone determine all scheduling follows from the
generic helper. `0x001F0B10` consumes terminal bit `2` and publishes the expiry
latch; [Collision](../gameplay/collision.md) owns that latch's combat use.

## Integer time-unit conversion

`0x001EBB70..0x001EBB98` (file `0x0EBC70..0x0EBC98`) is the separate pure
conversion `a0=s32 count`, `v0=count / 60`, truncating toward zero. Instructions
use signed multiply-high by `0x88888889`, add the original count, arithmetic
shift right `5`, then add the original sign bit. It has no record, reset,
fractional remainder or scheduler access.

All five recovered direct callsites were examined in `0x00223450`:
`0x00223C84/0x00223CC8` consume fighter signed halfword `+0x546`,
`0x00223D0C` consumes `+0x542`, and `0x00223D50/0x00223D90` consume `+0x54A`.
They compare the converted result to `4/6/60/1/3` respectively. These are
counter-to-unit classifiers, not calls which advance or reset the counters.
The gameplay meanings and producer coverage belong to
[Match outcomes](../gameplay/match_outcomes.md).

## Confidence and remaining evidence limits

The arithmetic, branch endpoints, ABI registers and field writes have high
confidence because they are visible in the scoped instructions. The functional
labels describe those operations; no retail source type names were recovered.
The caller table is bounded evidence, not an exhaustive whole-program timer
inventory. The preserved BTL decompiler truncates some paths after calls it
misclassifies as non-returning; its relevant advance/flag-clear interval was
therefore corroborated in disassembly.

No alternative arithmetic model is needed to explain the inspected helpers.
Unknowns remain explicitly open: the fixed-point word initialized to `-1` has
no established consumer here; no proof of positive nonzero period reaches all
modulo calls has been made; and unusual signed/large/non-finite float inputs
are outside the established caller contracts. The helpers use native FPU
operations and contain no explicit rounding-control change; EE rounding is
fixed in hardware, as recorded in
[Randomness](randomness.md#ee-hardware-conversion-and-software-packing).
