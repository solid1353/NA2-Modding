# Storm-style substitution bar for NA2 v2.28

This document defines the researched behavior and proposed implementation of a
four-stock substitution gauge in NA2 v2.28. It covers the gameplay state,
native hook boundaries, builder integration, in-battle HUD, and validation
needed to reproduce the system used from *Ultimate Ninja Storm 3* onward.

This is an implementation guide, not a statement that the feature already
exists. Sections explicitly distinguish official later-game behavior,
community-measured behavior, confirmed NA2 evidence, and proposed NA2 design.
The existing substitution timing/reliability investigation remains in
[Substitution knowledge](substitution.md).

## Research coverage

- **Assigned scope:** this task covered the substitution-stock system used from
*Ultimate Ninja Storm 3* onward and a code- and UI-level implementation design
for the separate four-stock gauge in NA2 v2.28. The requested outcome was
documentation, not a runtime implementation: later-game behavior and visual
conventions, NA2 state ownership and native hook boundaries, deterministic
timing, damage recovery, lifecycle/reset behavior, builder configuration, the
in-battle HUD, and validation requirements are all in scope.

- **Exploration depth:** later-game research was a targeted high-depth
review of the official *Storm 3 Full Burst*, *Storm Revolution*, and *Storm 4*
manual sections that define substitution use and show the battle HUD, plus the
official *Storm Connections* 1.20 change notes. Relevant manual pages for
*Storm 3* and *Revolution* were text-extracted, rendered, and visually checked;
the relevant *Storm 4* text was cross-checked against an indexed manual copy
when the official host did not complete a stable download. Community evidence
was bounded to a debug-tool-based *Storm 4* mechanics guide, a contemporary
empirical *Storm Generations* test, terminology support, and representative HUD
screenshots. NA2 work was a targeted deep static trace against the exact clean
hashed `SLPS_258.37` and `BTL.BIN`: the native eligibility and resource-commit
blocks, all five direct substitution-transition callers, both deliberate free
routes, fighter HP sampling, battle countdown/suppression, battle-graph reset,
the selected top-HUD draw chain, existing injection conflicts, and the current
builder catalog/runtime mechanisms. It was not a whole-program, whole-overlay,
or every-later-release audit.

- **Confirmed coverage:** official sources establish a separate limited-use
gauge, empty-gauge rejection, gradual/time-based recovery, other recovery
means, one displayed notch per performance in *Storm 4*, and full gauges at a
new *Storm 4* round. Community measurements establish the configurable numeric
reference model and cinematic game-time behavior without promoting those
numbers to official facts. Clean NA2 evidence establishes the exact
resource-only eligibility splice, charged-spend block, common success
notification, two native free-transition classes, normalized HP field,
per-fighter HP-sample seam, once-per-battle recovery-clock seam and timer-flag
semantics, battle/rematch construction reset, resident two-slot ownership, and
the guarded per-side BTL HUD insertion point. The design below carries those
findings through state pseudocode, ABI responsibilities, exact hook guards and
continuations, builder-facing UI/schema, HUD geometry/fill behavior,
implementation order, and static, pure-state, runtime, and visual validation.

- **Unresolved or untested:** none of the proposed hooks or HUD primitives has
been built or run in this task. Runtime work must still prove callback cadence
at supported frame rates, Practice and round-reset coverage, Unlimited-time
behavior, throw/Ultimate Jutsu and other cinematic clock suppression, COM and
free-route behavior at zero stock, exact BTL draw-state/alpha inheritance,
alternate-HUD coverage, final pixel anchors, and absence of overlap at every
supported aspect mode. The `14 s`, one-stock-per-second, and `0.3125` normalized
damage defaults remain community-derived tuning inputs; damage-source policy,
rounding, and final art remain proposed until runtime acceptance.

- **Deliberate exclusions and overlap:** this task did not alter substitution
input windows, reliability, reactions, or COM policy already owned by
[Substitution knowledge](substitution.md); implement production code; add a
PNACH or new settings mechanism; copy copyrighted later-game textures; audit
unrelated combat/HUD systems; or claim indirect-call completeness outside the
scoped traces.
- **Evidence limitations:** manual prose describes user-visible behavior, not internal
algorithms; community measurements can be version/platform dependent; static
disassembly proves control flow and clean bytes but not live cadence or visual
composition; and the UI proposal uses current NA2 renderer/build interfaces
whose exact runtime presentation remains to be captured.

## Outcome

When the feature is enabled, each side gets an independent four-stock gauge:

- a successful ordinary, chargeable substitution spends exactly one stock;
- a native deliberately free substitution spends no stock but still restarts
  recovery delay;
- an attempted input that does not produce a substitution spends nothing;
- substitution no longer consumes NA2's chakra resource;
- natural recovery begins after a delay from the last successful substitution;
- taking effective damage can restore stocks;
- the gauge starts full at the appropriate match or round boundary; and
- four mirrored cells below the existing chakra HUD show full, empty, and
  partially recovering stock.

The implementation must remain deterministic. Recovery advances in nominal
battle display-count units from NA2's once-per-battle countdown path, never
host wall-clock time. Proven NA2 scheduler suppression and terminal gates stop
those units. Local fighter hit-stop is not independently treated as a clock:
the gauge follows whatever the native battle clock does during that state.
Unclassified cinematic states remain runtime-validation cases rather than
assumed behavior.

### Non-goals

This feature does not:

- widen or replace NA2's substitution input/timing predicate;
- change reaction, held-input, attack, COM-policy, or forbidden-state gates;
- persist gauge state in save data or across battles;
- add another Practice Settings row or reinterpret Chakra Unlimited;
- turn per-character chakra costs into variable stock costs;
- require a PNACH, a second builder configuration store, or a graphical
  builder editor; or
- copy later-game textures into NA2.

## Evidence labels

This document uses four evidence classes:

- **Official later-game behavior**: stated by a publisher-provided manual.
- **Measured later-game behavior**: a community measurement or debug-tool
  observation. Useful numeric reference, but not an official specification.
- **Confirmed NA2 evidence**: established from clean binaries, maintained
  disassembly exports, existing runtime captures, or current implementation.
- **Proposed NA2 contract**: the recommended implementation. It remains a
  proposal until code, runtime evidence, and user acceptance promote it.

## What the later games do

### Official contract

The official *Storm 3 Full Burst* manual describes substitution as a
limited-use action, identifies the HUD element that tracks remaining uses,
states that substitution is unavailable when the gauge is empty, and says the
gauge refills gradually. The *Storm Revolution* and *Storm 4* manuals preserve
that contract and explicitly say the gauge fills over time and by other means.
The *Storm 4* manual additionally says every performed substitution removes one
notch, and that both the round winner's and loser's substitution gauges refill
to maximum for the next round.

Bandai Namco's official *Storm Connections* 1.20 notes are useful engineering
evidence rather than a specification for *Storm 3*: they call recovery speed
varying with frame rate an issue, report fixing it, and separately shorten the
delay before recovery begins. This establishes that recovery rate and delay are
distinct tunable behaviors and that a frame-rate-dependent refill should be
treated as a defect, not series parity.

The official material supports the following product behavior:

| Behavior | Confidence |
| --- | --- |
| Substitution has a separate gauge | Official |
| The gauge exposes a countable number of uses | Official |
| Each ordinary performance consumes one displayed notch | Official in *Storm 4* |
| Empty gauge prevents substitution | Official |
| Gauge recovers over time | Official |
| Later variants can recover it by another mechanism | Official, mechanism not numerically specified |
| A new *Storm 4* round refills both players to maximum | Official |
| Recovery should not vary with frame rate | Official fix in the later *Connections* implementation |

The manuals do **not** publish a complete numeric model. The internal `0..100`
scale and `25`-unit encoding for the visible one-notch cost, recovery delay,
recovery rate, and damage threshold below come from visual inspection and
community measurement and therefore remain configurable in NA2 where noted.

### Measured numeric model

A detailed *Storm 4* mechanics guide reports values observed with the PC debug
application:

- the internal meter spans `0..100`;
- a substitution costs `25`, giving four stocks;
- every successful use restarts the automatic-recovery delay;
- the guide's switch-buffered free substitution also restarts that delay even
  though it does not spend a stock;
- automatic recovery waits about 14 seconds;
- after the delay, recovery continues stock by stock until full;
- receiving about `31.25` damage units grants one stock in the guide's
  normalized model; and
- the observed refill rate differed between 30 and 60 FPS builds.

The same guide reports approximately one second per stock at 30 FPS and half a
second per stock at 60 FPS. Bandai Namco later classified frame-rate-dependent
substitution recovery as an issue in *Storm Connections* 1.20. The measured
discrepancy therefore must not be copied as an NA2 rule. NA2 should express all
timing in battle-time seconds and validate identical results at every supported
frame rate.

An empirical *Storm Generations* test, relevant because that game introduced
the stock system inherited by *Storm 3*, also reports four stocks, no spending
on an input that does not actually substitute, a roughly 14-second post-use
delay, continuous recovery to full, and recovery from damage. It is a
translated community test, so it corroborates the shape of the state machine
without upgrading any exact number to official status. The same test reports
that throw and Ultimate Jutsu demonstration animations suspend game time, so
real-world recovery takes longer across those cinematics. That is useful
later-game timing evidence, but NA2 must implement it through its own proven
battle-clock gates rather than a list of guessed animation states.

### Visual language

Official manual diagrams and battle screenshots show a consistent information
hierarchy across the later series:

- four immediately countable cells sit directly beneath the chakra bar;
- Player 1 and Player 2 layouts mirror one another;
- available cells are bright orange/gold;
- spent cells remain visible as a dark frame or background;
- recovery can be communicated by a partial fill of the next cell; and
- a platform-specific substitution-input reminder may sit on the outer side.

*Storm 3* uses a connected segmented rail. Later games use four more distinct
capsules. NA2 should reproduce the information and behavior, not copy another
game's texture artwork.

## Recommended NA2 gameplay contract

### Baseline values

Use the following defaults for the first runtime implementation:

| Parameter | Default | Reason |
| --- | ---: | --- |
| Capacity | `100.0` | Matches the measured later-game representation |
| Stock size | `25.0` | Four equal uses |
| Successful-use cost | `25.0` | Exactly one stock |
| Post-use recovery delay | `14.0 s` | Repeatedly measured in the series |
| Natural recovery | `25.0/s` | Console-era baseline of one stock per second |
| Damage threshold | `0.3125` normalized HP | Provisional mapping of `31.25/100` |
| Damage award | `25.0` | One stock per threshold |
| Starting value | `100.0` | Four stocks |

All numeric values should be generated configuration data rather than literals
inside hook shims. Capacity and stock size should remain fixed together for the
parity mode; tuning should normally change delay, natural rate, or damage
threshold. The `0..100` values are the external/debug model, not a requirement
to store authoritative state as floating point.

The `0.3125` damage threshold is deliberately provisional. NA2 stores fighter
HP as a normalized float at `fighter + 0x6C`, so it is a sensible first mapping
of the measured later-game value. Runtime comparison must establish whether it
feels and behaves like the intended title before the value becomes accepted
balance data.

### State machine

Use the native display-count quantum as the authoritative recovery unit. At
configuration generation time compute:

```text
stock_counts = refill_seconds_per_stock * 60
capacity_counts = 4 * stock_counts
delay_total_counts = recovery_delay_seconds * 60
damage_threshold_q16 = round((damage_percent_per_stock / 100) * 65536)
```

The proposed catalog steps make the first three products exact integers. At
the default, one stock is `60` counts, capacity is `240`, and delay is `840`.
The familiar debug value is derived only when needed as
`100 * meter_counts / capacity_counts`.

For each player slot, maintain `meter_counts`, `recovery_delay_counts`,
`damage_accumulator_q16`, `last_hp_q16`, and identity/reset metadata. Convert
native HP once per sample with
`round(clamp(current_hp, 0, 1) * 65536)`; this prevents frame-rate-dependent
floating accumulation and prevents negative knockout HP from manufacturing
extra damage.

The authoritative update is:

```text
on successful charged substitution:
    require meter_counts >= stock_counts
    meter_counts -= stock_counts

on every successful substitution transition, including a free one:
    recovery_delay_counts = delay_total_counts

on fighter update:
    bind or reset the slot if its battle generation changed
    current_hp_q16 = quantize_clamped_hp(current_hp)
    received_q16 = max(0, last_hp_q16 - current_hp_q16)
    last_hp_q16 = current_hp_q16
    add received_q16 to damage_accumulator_q16 only when damage recovery is on
        and meter_counts < capacity_counts
    while damage_accumulator_q16 >= damage_threshold_q16
          and meter_counts < capacity_counts:
        damage_accumulator_q16 -= damage_threshold_q16
        meter_counts = min(capacity_counts, meter_counts + stock_counts)

    if meter_counts == capacity_counts:
        damage_accumulator_q16 = 0

on eligible battle-clock callback:
    if timer_flags_at_entry & (0x01 | 0x04):
        return
    if engine_update_ordinal was already processed:
        return
    advance = system_context[1]
    for each active slot:
        delay_consumed = min(recovery_delay_counts, advance)
        recovery_delay_counts -= delay_consumed
        remaining_advance = advance - delay_consumed
        meter_counts = min(capacity_counts, meter_counts + remaining_advance)
        if meter_counts == capacity_counts:
            damage_accumulator_q16 = 0
```

`last_hp_q16` is initialized without awarding damage when a slot first binds.
Healing or a Practice reset raises the baseline but never subtracts from the
accumulator. Damage taken while a cinematic temporarily suspends ordinary
fighter updates is captured as the net HP decrease on the next valid update.
HP sampling and damage awards are independent of the battle-clock callback, so
local hit-stop does not create duplicate awards or become an invented recovery
clock rule.

Carrying `advance` past the end of the delay is required. For example, a
15-count delay processed by two-count 30 FPS updates leaves one count of refill
on the eighth update; discarding it would make the same configured delay one
count longer than sixty one-count updates. Integer meter counts also make a
stock become spendable on exactly the same cumulative display count at 30 and
60 FPS.

Do not bank damage while the meter is full. Otherwise a player could take
damage at full gauge, spend later, and receive an immediate hidden stock that
the later-game UI never communicated. Remainder carry and more than one award
from a large HP decrease are proposed NA2 behavior; the community source
establishes the `31.25` threshold but does not publish those rounding details.
Keep both behaviors covered by tests and treat them as runtime-tuning findings,
not sourced *Storm 4* facts.

### Spending rules

Only the native path that commits a real, resource-charging substitution may
spend the new gauge. In particular:

- raw guard/substitution input does not spend;
- an input outside the accepted timing window does not spend;
- an ineligible fighter state does not spend;
- a call variant that native NA2 intentionally treats as free does not spend;
- a native free route remains available at zero meter because it either calls
  the acceptance predicate with resource validation disabled or bypasses that
  predicate entirely;
- every committed free or charged substitution resets the natural-recovery
  delay, matching the measured later-game behavior;
- a successful ordinary substitution spends once, even if the move that hit
  the fighter has multiple hit packets; and
- damage recovery does not restart the post-use timer.

The gauge changes only the resource gate. It must preserve the attack-specific
input history, held-input limit, reaction whitelist, forbidden state checks,
and other eligibility logic already documented in
[Substitution knowledge](substitution.md).

### Lifecycle rules

The full gauge must be initialized at a proven battle/round boundary, not only
when a fighter pointer happens to change. This matters because allocators can
reuse a fighter object across Practice reset, retry, or a later round.

Required lifecycle behavior:

| Event | Result |
| --- | --- |
| New match | Both slots reset to full |
| New round | Both slots reset to full, matching the documented *Storm 4* rule |
| In-match transformation with the same player slot | Gauge is preserved |
| Fighter pointer replacement inside the same player slot | Rebind without duplicating state; preserve only when confirmed to be a transformation |
| Practice reset/restart | Both slots reset to full |
| Return to menu or no live manager | State is invalidated |
| Active start menu or other scheduler suppression | Timer flag `0x01` stops natural delay/refill; do not catch up afterward |
| Round timer disabled / no time limit | Timer flag `0x02` stops only the native countdown; substitution recovery continues |
| Round timer expired | Timer flag `0x04` and the outer terminal gates stop natural delay/refill |
| Ordinary actor hit-stop | Follow the once-per-battle clock; do not add a separate `fighter + 0x20C` rule |
| Cinematic/selective scheduler state | Follow the proven native clock call and still capture a runtime trace before acceptance |

The battle/rematch reset seam is established statically below. A separate
in-object round transition has not been identified in NA2. Runtime validation
must still check every supported mode, especially any Practice action that
resets fighters without rebuilding the battle graph. Pointer-change heuristics
alone are not an acceptable substitute for the construction hook.

`FUN_00214a40` is the confirmed fighter-object initializer. It clears HP at
`+0x6C`, chakra at `+0x70`, the resource-bookkeeping fields at `+0x1A0` and
`+0x1A4`, and the rest of the fighter's transient state. The maintained export
has one direct reference, from the fighter constructor immediately before that
constructor returns. This is a sound new-object initialization signal, but it
does not prove that retry, rematch, Practice reset, or any round transition
constructs a new object. It therefore cannot replace a separately proven
battle-generation/reset signal.

### Interactions

- **Chakra:** substitutions must not read or write chakra once the feature is
  active. Jutsu, chakra dash, X-dash, and ordinary chakra regeneration remain
  unchanged.
- **CPU:** Player 2/COM uses the same gate, cost, and recovery logic. The bar is
  a battle rule, not a human-input-only affordance.
- **Transformations:** state belongs to the player slot and battle generation,
  not the current character ID. Transformations must not refill it.
- **Per-character costs:** later-Storm parity is one uniform stock. The broader
  NA2.28 character-override feature can remain selected, but its
  `substitution_cost` column has no runtime effect while this mode bypasses the
  native chakra-cost block. A separate non-parity extension would be needed to
  turn those values into variable stock costs.
- **Substitution-doll items:** item/status behavior remains native and does not
  silently grant meter. The confirmed item/status-ID `9` path triggers a native
  substitution transition with charging disabled, so the successful-spend
  hook must preserve that free classification.
- **Practice resource options:** any native Practice unlimited-resource mode
  must be traced and mapped deliberately. NA2's substitution row is not an
  unlimited-resource switch: row `14`, manager key `0x11` / packed bit
  `manager+0x9F4` bit 7, is `Normal` versus `Don't use` and is enabled only
  for COM status. Because the gauge replaces only the native resource
  sub-block, the surrounding native policy check must continue to suppress COM
  substitutions when this bit requests `Don't use`. The separate Chakra
  `Unlimited` option must not refill substitution stocks.
- **Replays and recordings:** use game state plus scaled update time only; never
  use a host clock.

## Confirmed NA2 implementation boundary

### Binary identity and mapping

The boot-ELF evidence refers to clean
`@source/NA2.iso.files/SLPS_258.37`, SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`.
Its relevant load mapping places file offset `0x100` at runtime
`0x00100000`; therefore raw file offsets below are virtual address minus
`0x000FFF00`.

The battle-overlay evidence refers to
`@source/NA2.iso.files/PRG/BTL.BIN`, SHA-256
`56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C`,
archived live base `0x006B3F00`. The maintained Ghidra BTL project omits its
40-byte file header, so its exported address is archived live address minus
`0x40`.

### `fighter + 0x70` is chakra, not a substitution gauge

Static inspection corrects an earlier narrow label: `fighter + 0x70` is
NA2's shared chakra resource.

- `FUN_002254a0` adds to the field, clamps it to `15.0`, and handles crossings
  of the `5`, `10`, and `15` thresholds.
- `FUN_00227ee0` performs ordinary per-fighter regeneration through that
  helper.
- multiple native actions check and subtract costs from the same field.
- `FUN_002297d0` subtracts the native substitution cost from it and clamps the
  result to zero.

The field at `fighter + 0x1A0` is also part of native resource bookkeeping and
threshold handling. It is written to `15.0` on the ordinary substitution spend
path. It is not a proven cooldown field and must not be repurposed.

Consequently, changing the existing substitution cost to zero would only stop
chakra loss. It would not create stock eligibility, recovery, independent
state, or a correct HUD.

### Eligibility gate

`FUN_00229130`, virtual `0x00229130` / raw ELF offset `0x129230`, is the
confirmed substitution acceptance predicate. Its ordinary resource sub-block
is virtual `0x00229710..0x00229738` / raw
`0x129810..0x129838`. It currently:

1. loads the float at `fighter + 0x70`;
2. compares it with `1.0`; and
3. produces Boolean `v0`, which is normalized at raw `0x12983C` before the
   existing accept/reject branch.

The clean first 16 bytes at raw `0x129810` are
`700081C6803F023C0000824400000000`, corresponding to the load and constant
setup. Guard and replace only the first eight bytes,
`700081C6803F023C`, with a generated `jal` plus `move a0,s4` in its delay
slot. The resident shim calls `substitution_gauge_can_spend(fighter)` and then
tail-jumps, preserving `v0`, to virtual `0x0022973C` / raw `0x12983C`, where
the native `andi v0,v0,0xff` normalization begins. The original function's
saved return address is restored by its native epilogue, so the shim neither
returns to the overwritten float sequence nor fabricates a whole-function
result.

This hook changes availability while retaining all timing and reliability
gates. Returning true from the entire function would be incorrect.

### Successful spend

`FUN_002297d0`, virtual `0x002297D0` / raw ELF offset `0x1298D0`, owns the
transition and native conditional resource spend. Its ordinary spend block is
virtual `0x002298B8..0x002298EC` / raw
`0x1299B8..0x1299EC`; continuation is raw `0x1299F0`.

That block subtracts the cost from `fighter + 0x70`, clamps it to zero, and
writes the resource-bookkeeping field at `fighter + 0x1A0`. It is reached only
after `param_3` and the function's other native free/suppression conditions
permit a charge. That makes it the correct semantic boundary for a
`substitution_gauge_spend(fighter)` adapter.

All five direct callers divide as follows:

| Caller | Transition | `param_3` | Resource behavior |
| --- | ---: | ---: | --- |
| `FUN_0021F610` ordinary path | `0x11` | `1` | Requests a charge after ordinary resource validation |
| `FUN_002209A0` branch | `0x41` | `1` | Requests a charge after ordinary resource validation |
| `FUN_002209A0` branch | `0x21` | `1` | Requests a charge after ordinary resource validation |
| `FUN_0021F610` temporary-effect-`9` path | `0x211` | `0` | Deliberately free; its preceding predicate call disables resource validation |
| `FUN_00236C70` item/status ID `9` | `2` | `0` | Deliberately free item/status substitution |

The two numeric `9` domains are unrelated. Temporary-effect ID `9` belongs to
the Kurenai awakening exception documented in the substitution research; its
first predicate call supplies `param_5 = 0`, which bypasses the resource block
containing the new eligibility hook. Item/status ID `9` calls
`FUN_002297D0(fighter, 2, 0)` directly and never calls the predicate. Its exact
user-facing inventory name is not needed by the gauge hook. Both free routes
therefore remain usable at zero meter and never enter the native chakra-spend
block. Hooking that block preserves them without a caller whitelist, while
hooking every call to `FUN_002297D0` would incorrectly charge them.

The current per-character cost feature hooks raw `0x1299C0` inside this block
and then resumes native subtraction. The gauge hook can coexist without an
overlapping edit: guard raw `0x1299B8..0x1299BF`, whose clean bytes are
`700061C6803F023C`, and replace them with a generated `jal` plus
`move a0,s3` in its delay slot. The resident shim calls
`substitution_gauge_spend(fighter)` and tail-jumps to virtual `0x002298F0` /
raw `0x1299F0` instead of returning to `0x1299C0`.

With the gauge disabled, that new hook is absent and the existing
per-character cost hook behaves byte-for-byte as it does now. With the gauge
enabled, both guarded writes may still compose because their byte ranges do
not overlap, but control skips the legacy hook and the entire native chakra
subtraction/bookkeeping sequence. This is a runtime policy bypass, not a
catalog conflict and not a reason to disable the broader character-override
table.

`substitution_gauge_spend` should defensively clamp and report an invariant
failure if called below one stock, but the upstream gate remains the normal
source of eligibility.

Spending and delay reset are deliberately separate. Immediately after the
conditional spend block, raw `0x1299F0` restores `a0 = s3` and raw
`0x1299F4..0x1299FB` unconditionally calls `FUN_0022D5B0`; the clean call and
delay slot are `6CB5080C00000000`. Wrap that call with
`substitution_gauge_success_shim`: save the fighter pointer, call
`substitution_gauge_note_success(fighter)` to reset the delay, restore `a0`,
call displaced virtual `0x0022D5B0` once, and return to virtual `0x002298FC`.
All five callers pass this point, so charged substitutions spend then reset the
delay, while the two native free variants only reset the delay.

### Per-fighter HP-sample seam

NA2.28 already owns a guarded hook at raw ELF offset `0x14DB80` for
`xdash_pre_update_shim`. It runs resident C before the native fighter update
continues and receives the live fighter pointer. Adding a second independent
hook at the same instruction would conflict, while refactoring it would change
disabled-profile payload bytes unnecessarily.

The clean function provides a better non-overlapping seam immediately after
that hook. Raw `0x14DB88` is `move a0,s3`; raw `0x14DB8C..0x14DB93` is the
native `jal FUN_002449C0; nop`, with clean bytes
`7012090C00000000`. Replace only that call and delay slot with a guarded call
to `substitution_gauge_pre_update_shim`. The shim must:

1. save the fighter pointer already supplied in `a0`;
2. call `substitution_gauge_sample_hp(fighter)`;
3. restore `a0` and call displaced native virtual `0x002449C0` exactly once;
4. preserve the native ABI and return to virtual `0x0024DA94`.

Both adjacent calls occur on the same active-fighter path in
`FUN_0024DA50`, so this retains the established callback cadence without
modifying the X-dash injection. Gauge state lives in resident `228.BIN` data
so the BTL overlay can be loaded or unloaded without losing or owning gameplay
state.

The seam is before, not inside, NA2's local hit-stop gate. The next clean
instruction at raw `0x14DB94` is `lh v0,0x20C(s3)`; the following comparison and
branch divert positive counts to the function's secondary maintenance path.
The existing frame-rate research establishes `fighter + 0x20C` as the current
count in the actor `+0x200` hit-stop/pause timer. This placement is safe because
the new consumer samples HP only. It must not advance natural recovery or use
`+0x20C` as a second battle clock. Repeated samples of unchanged HP produce a
zero delta, so the stored-HP comparison is itself idempotent without a
per-fighter update-ordinal guard.

### Once-per-battle recovery-clock seam

The running controller path has a stronger time owner. Its only direct call to
`FUN_001F10F0(controller)` occurs after `FUN_001F0290` has recomputed scheduler
suppression and after `FUN_001F03E0` has dispatched the selective battle
update, but before `FUN_001F0B10` checks terminal state. `FUN_001F10F0` calls
the native battle-countdown accumulator only when all of these conditions hold:

- manager fighter pointers `+0xDE4` and `+0xDE8` are both non-null;
- both fighters have zero at `+0xB00`;
- both fighters retain life bit `+0x61 & 0x08`;
- resident `FUN_00250820()` and BTL live `0x007064B0()` both return zero;
- outcome global `0x00607670` is zero; and
- controller byte `+0x00` has bit `0x02` set.

At virtual `0x001F11B8` / raw ELF `0x0F12B8`, the eligible path calls
`FUN_001EBA80(0x006B28D0)`. The clean call and delay-slot bytes are
`A0AE070C00000000`; the preceding instructions have already materialized the
timer pointer in `a0`. Replace that pair with a guarded call to
`substitution_gauge_battle_clock_shim`. The shim must save the timer pointer,
conditionally call `substitution_gauge_advance_battle(timer)`, restore `a0`, call
displaced virtual `0x001EBA80` exactly once, preserve its `v0`, and return to
virtual `0x001F11C0`.

The timer flag byte at entry has three distinct meanings that the adapter must
not collapse:

| Mask | Native meaning | Substitution-clock treatment |
| ---: | --- | --- |
| `0x01` | Scheduler suppression, recomputed by `FUN_001F0290` from the current allowed/suppressed masks | Do not advance |
| `0x02` | Native countdown freeze; established setup paths use it for the `100`/Unlimited battle-time setting | Ignore this bit and advance, because an unlimited round must still recover substitution stocks |
| `0x04` | Countdown expired / terminal timer state | Do not advance |

This deliberately does not reproduce `FUN_001EBA80`'s full early-return test.
Copying `(flags & 0x07) == 0` would strand the gauge forever in an Unlimited
battle. Instead, advance only when `(flags_at_entry & 0x05) == 0`; the already
passed outer gate supplies the remaining battle-lifecycle conditions. The
native countdown call still runs for every flag combination and remains the
last value-producing call in the shim, so its return ABI is unchanged.

Global pointer slot `0x006073FC` owns the live system context.
`FUN_00105DA0(context)` returns its byte `+0x01`; the clean function bytes at
raw ELF `0x5EA0` are `010082900800E00300000000`
(`lbu v0,1(a0); jr ra; nop`). That byte is the number of nominal 60 Hz display
counts consumed by one engine update:

- ordinary battle sets it to `2`, so one advancing update is nominally
  `2 / 60 = 1 / 30` second;
- the researched one-VBlank mode sets it to `1`, so one update is nominally
  `1 / 60` second; and
- native rumble maintenance already subtracts this exact value from durations
  stored in display-count units, independently confirming its time meaning.

Use `context[1]` directly as `advance_counts`; convert it to seconds only for
logging. System-context `+0x194` is the engine-update ordinal incremented by
`FUN_001081B0`. Keep one global last-clock ordinal plus a separate validity bit
and advance both active slots at most once for an ordinal. Zero is valid and
the counter can wrap, so do not use zero as an initialization sentinel. If an
eligible clock callback is skipped, do not catch up from the ordinal difference
on resume.

`FUN_00307230` is **not** a time source. It starts at `1.0`, walks the fighter's
active-effect list at `+0x8C4`/`+0x8C8`, and combines each active effect's
float at `+0x94`. Native chakra regeneration multiplies that status-effect
scalar by fighter rate `+0x164` and a fixed `0.05` per update. Reusing it as
elapsed time would make substitution recovery speed depend on status effects.
Host time, floating `battle_dt`, and a hard-coded `1/30` under every profile are
wrong for the same deterministic or frame-rate reasons.

This seam means ordinary actor hit-stop follows NA2's battle clock rather than
an invented per-fighter pause rule. The *Generations* community test says later
games freeze recharge during throw and Ultimate Jutsu demonstration time, but
the static NA2 evidence does not prove which outer predicate handles each
equivalent cinematic. Runtime acceptance must record the call, flags, ordinal,
and meter in every supported cinematic. If the native timer call still occurs
where later-title parity requires a freeze, classify the responsible NA2 state
and add the narrow proven gate; do not key off animation names.

### Battle/rematch reset seam

`FUN_001EF330`, virtual `0x001EF330` / raw ELF offset `0x0EF430`, is the
heavy battle-graph constructor already documented by the stage lifecycle. When
its battle bundle at controller `+0x18` is absent, it constructs that bundle,
publishes the two returned fighter pointers to manager `+0xDE4` and `+0xDE8`,
and continues building the graph. The corresponding `FUN_001EEFD0` teardown
clears manager `+0xDE0..+0xDE8`, clears `+0xDEC..+0xDF4`, destroys the bundle,
and sets controller `+0x18` to null. The documented rematch/stage-switch path
tears the old graph down and returns through construction.

Immediately after both fighter pointers are published, virtual
`0x001EF41C` / raw `0x0EF51C` calls live `0x007096E0`; the clean call and
delay-slot bytes are `B8251C0C00000000`. A guarded wrapper at this call should:

1. increment the resident battle generation and reset both gauge slots to
   `capacity_counts` using manager pointer `s0`;
2. retain the original bundle argument that is already in `a0`;
3. call displaced live function `0x007096E0`; and
4. return its `v0` unchanged for the native store to controller `+0x14`.

Because the call is inside the `controller + 0x18 == null` construction branch,
it is not executed on every later `FUN_001EF330` update. It is therefore a
better reset owner than lazy fighter-pointer binding. Runtime tracing must
confirm one call per initial battle and rematch.

The known Practice restart paths also return through this seam. Practice
controller state `23` (`FUN_001EE1C0`) snapshots resources, destroys the old
battle session, prepares the next side state, and returns to construction state
`13`. State `24` (`FUN_001EE500`) does the corresponding rematch/stage-or-side
switch work, destroys the old session, and also returns to state `13`.
Construction state `14` reaches `FUN_001EC3B0`, which creates the new session
and enters `FUN_001EF330`. An aligned resident-instruction scan found only the
two stores in this constructor that publish manager fighter pointers
`+0xDE4/+0xDE8`; no second fighter-replacement owner was found.

Do not confuse those restart paths with live BTL `0x00880F30`, the reset used
when opening the Practice Settings child. That function resets and snapshots
the menu's phase, selection, animation, input, and page fields; it does not
reconstruct fighters or reset HP/chakra. Opening or cancelling that menu must
therefore preserve the gauge. Runtime acceptance should still exercise the
user-visible Practice restart command, but static evidence no longer supports
adding an extra speculative in-place gauge-reset hook.

### Damage recovery without a new damage hook

Existing captures establish normalized HP at `fighter + 0x6C`. Sampling it
once in the shared fighter update avoids a second invasive hook in the hit or
damage pipeline:

```text
current_hp_q16 = round(clamp(fighter_hp, 0, 1) * 65536)
received_damage_q16 = max(0, previous_hp_q16 - current_hp_q16)
```

This captures only committed net HP loss, naturally combines multi-hit changes
between updates, and cannot award twice for the same stored value. Reset and
healing transitions must update `previous_hp` without granting a stock. If
runtime tracing finds a native path that changes HP without reaching the
shared update before a reset, use the proven HP-commit site instead; do not add
one based only on animation or hit-count events.

This deliberately attributes all net HP loss, not an attacker or move. Poison,
stage hazards, chip that actually lowers HP, and self-inflicted HP loss will
all count; guard-only damage will not. The later-game sources establish
recovery from damage but do not publish source filters, so this inclusive rule
is a proposed first implementation. It also has two explicit blind spots:
damage followed by healing between accepted samples is visible only as the net
decrease, and a direct Practice HP edit downward would look like damage unless
the responsible reset path rebaselines the slot. Include both cases in runtime
capture before accepting the damage feature.

## Resident state and API

Use a fixed two-slot payload structure rather than appending fields to native
fighter objects:

```c
typedef struct SubstitutionGaugeSlot {
    void *fighter;
    unsigned int meter_counts;              /* 0..capacity_counts */
    unsigned int recovery_delay_counts;     /* nominal 60 Hz counts */
    unsigned int damage_accumulator_q16;    /* normalized HP Q16 */
    unsigned int last_hp_q16;
    unsigned int battle_generation;
    unsigned char hp_valid;
    unsigned char active;
} SubstitutionGaugeSlot;

typedef struct SubstitutionGaugeState {
    void *manager;
    unsigned int battle_generation;
    unsigned int last_clock_ordinal;
    unsigned char clock_ordinal_valid;
    SubstitutionGaugeSlot player[2];
} SubstitutionGaugeState;
```

The exact padding is an implementation detail, but the two-slot ownership is
not. Map a fighter to a slot through live manager `0x00607600` and manager
fields `+0xDE4`/`+0xDE8`, as the current X-dash and per-character selector code
already does.

Expose a deliberately small resident API:

```c
typedef struct SubstitutionGaugeSnapshot {
    unsigned int meter_counts;
    unsigned int stock_counts;
} SubstitutionGaugeSnapshot;

void substitution_gauge_reset_battle(void *manager);
void substitution_gauge_sample_hp(void *fighter);
void substitution_gauge_advance_battle(void *timer);
int  substitution_gauge_can_spend(void *fighter);
int  substitution_gauge_spend(void *fighter);
void substitution_gauge_note_success(void *fighter);
int  substitution_gauge_snapshot_for_side(
    unsigned int side,
    SubstitutionGaugeSnapshot *out
);
```

The runtime ownership is intentionally one-way:

```text
battle construction ------------------------------> reset both slots
fighter callback ---------------------------------> sample committed HP
battle-clock callback ----------------------------> advance both slots
eligibility hook ------------------------------read-> can_spend
charged spend hook ----------------------------write-> spend one stock
common success hook ---------------------------write-> restart delay
BTL top-HUD hook -------------------------------read-> immutable snapshot
```

Only the battle-clock callback advances natural recovery; fighter callbacks
only sample committed HP. Only confirmed transition hooks spend or restart
delay. The renderer is never an update owner, which prevents hidden extra
recovery when a side is drawn more than once or not drawn at all.

`substitution_gauge_advance_battle` validates the fixed native timer pointer,
entry flags, resident manager, system context, and global ordinal, then passes
`context[1]` to a native-independent two-slot state transition. Keeping those
native-memory reads in the adapter leaves the state engine testable with an
explicit count. `substitution_gauge_sample_hp` maps only manager-owned fighter
pointers and is idempotent for an unchanged HP sample. The snapshot call returns
false for an invalid side, manager mismatch, or inactive slot. The renderer
must not advance timers, infer damage, or mutate gameplay state.

Do not use `last_clock_ordinal == 0` as an uninitialized sentinel because zero
is a valid counter value and the native ordinal can wrap. Track validity
separately, accept the first observed ordinal, and suppress only an equal
subsequent ordinal. Reset validity at every battle-generation reset. If the
manager is null or a fighter does not match manager `+0xDE4/+0xDE8`,
`can_spend` must fail closed, HP sampling must do nothing, and the HUD accessor
must return an inactive result rather than silently binding arbitrary objects.

## HUD implementation

### Layout

Place the new strip immediately below each native chakra bar and mirror it by
side:

```text
screen-left                                                    screen-right

[P1 portrait][ health / chakra ]          [ health / chakra ][P2 portrait]
             [S][1][2][3][4]              [4][3][2][1][S]
                       -> center      center <-
```

`S` represents an optional NA2-native substitution icon. It must not reuse the
Xbox `LT` artwork visible in some *Storm 3* references. If no existing
cross-atlas icon can be drawn safely, omit it in the first implementation; the
four cells are the required information.

Recommended prototype geometry in NA2's 512-by-384 logical coordinate space:

| Element | Starting value | Finalization rule |
| --- | ---: | --- |
| Cell width | `12` | Tune against captures |
| Cell height | `5` | Tune against native chakra-bar weight |
| Gap | `1` | Keep cells countable at 640-by-480 output |
| Four-cell strip width | `51` | `4 * width + 3 * gap` |
| Vertical offset | chakra bottom `+ 3` | Remain inside top HUD stack |

These are prototype values, not confirmed coordinates. The implementation
must first trace the native chakra-bar anchor for each side and derive the strip
from that live anchor. Hard-coded screenshot coordinates would break native
HUD entrance motion, mirroring, or aspect handling.

The first stock is adjacent to the outer-side icon/portrait and subsequent
stocks progress toward screen center. Player 2 reverses geometry and fill
direction. Verify this order in side-by-side captures before acceptance.

### Fill computation

Draw every cell's dark frame/background, then clip its bright fill by:

```text
cell_progress = clamp(meter_counts - stock_counts * i, 0, stock_counts)
fill[i] = cell_progress / stock_counts, i = 0..3
```

This produces:

- four bright cells at `100`;
- three bright cells at `75`;
- no bright cells at `0`; and
- a continuously growing next cell during natural recovery.

For Player 1 the fill clip grows left-to-right; for Player 2 it grows
right-to-left. Convert the integer ratio to float only in the local renderer;
do not round it to a whole stock. A brief pulse when a cell completes is
optional and must not obscure the count.

### Color, visibility, and motion

- Sample orange/gold and dark frame colors from NA2's existing battle gauge so
  the addition looks native.
- Preserve a visible empty-cell outline; absence of bright fill alone is too
  ambiguous over varied stages.
- Inherit the parent top-HUD alpha, slide offset, and visibility state.
- Hide with the native battle HUD during cinematics, transitions, pause-owned
  overlays, and results.
- Do not attach visibility to the lower support gauge; NA2.28 can hide that
  element independently.
- Avoid a numeric label. Four cells are faster to read and match the source
  interaction.

### Native assets

The clean source container is
`@source/NA2.iso.files/DATA/DATA.CVM.files/DATA.CVM.iso.files/BATTLEGAUGE.CCS`.
Read-only inspection found a gzip-compressed `134,543`-byte file,
`469,568` bytes after decompression, with 32 texture entries. Relevant names
include:

- `x/battle/tex/xgauge.bmp` (`TEX_xgauge`, `256x128`);
- `x/battle/tex/xgauge2.bmp` (`128x128`); and
- `x/battle/tex/xgauge3.bmp` (`128x64`).

`TEX_xgauge` contains the main ornate health/chakra HUD parts, and the related
atlases contain circular and pill-like gauge elements. This establishes a
native visual vocabulary; it does not prove that apparently blank atlas space
is unused.

Prototype with existing safe rectangles or simple native renderer primitives.
For final art, either:

1. prove an unused atlas rectangle by reference tracing and place an authored
   NA2-style cell there; or
2. replace a proven dedicated rectangle without changing texture dimensions,
   palette contract, container size rules, or another screen's source pixels.

Route final texture work through the existing deterministic
`texture_patcher` package and guarded builder outputs. Do not hand-edit a built
ISO, emit an unguarded binary, or import copyrighted cell artwork from a later
game.

### Draw hook

BTL resolves `battlegauge.ccs` and `TEX_xgauge`; the resource lookup around
archived runtime `0x0071CD60` proves the relevant atlas family but is not by
itself a draw-hook contract. The known lower support-gauge draw path at BTL
file offset `0x68BF0` has different visibility and must not own the new top
gauge.

Static tracing now identifies the correct per-side controller and a narrow
post-chakra wrapper seam. `FUN_001EF330` allocates two `0x68`-byte controller
objects and calls live BTL constructor `0x0071A840` with side selectors `1`
and `2`. The constructor normalizes those to parent byte `+0x0C` values `0`
and `1` and binds manager fighter pointers `+0xDE4` and `+0xDE8` at parent
`+0x14`. This is presentation state for both human and COM-controlled sides;
it is not input ownership.

The per-side draw dispatcher has these address forms:

| Form | Address |
| --- | ---: |
| Complete BTL file offset | `0x673E0` function start; `0x6745C` hook |
| Loaded EE | `0x0071B2E0` function start; `0x0071B35C` hook |
| Header-omitting Ghidra/export | `FUN_0071B2A0`; `0x0071B31C` hook |

At entry it returns without drawing when parent byte `+0x54 == 1`. Otherwise
it computes current parent `x/y` at `+0x00/+0x04` from base position
`+0x30/+0x34` plus animated offsets `+0x38/+0x3C`, then draws these children
in order:

| Parent field | Native component | Call target in the clean instruction |
| ---: | --- | ---: |
| `+0x20` | portrait/frame group | `0x0071B720` |
| `+0x24` | health bar; samples fighter `+0x6C` | `0x0071C0E0` |
| `+0x28` | chakra bar/effects; samples fighter `+0x70/+0x7C` | `0x0071EE70` |
| `+0x2C` | character name | `0x0071BE20` |

The chakra child stores its parent pointer at child `+0x00`. Its full native
draw at live `0x0071EE70` calls the chakra-bar body at live `0x0071E100`,
optional effects, and then flushes its three sprite objects. The clean parent
call and delay slot at complete-file `0x6745C..0x67463` are:

```text
9C 7B 1C 0C 00 00 00 00    jal 0x0071EE70; nop
```

The header correction matters here. Ghidra displays the call instruction at
`0x0071B31C`; it executes at `0x0071B35C`. The encoded target is already the
live address `0x0071EE70`, whose physical body is exported forty bytes lower
as `FUN_0071EE30`. Do not add `0x40` to an encoded target or patch Ghidra's
header-stripped offset as though it were a complete-file offset.

Replace only that `jal` with a generated call to a resident adapter and retain
the `nop` delay slot. The adapter must:

1. save the chakra-child pointer received in `a0`;
2. call the displaced native function at live `0x0071EE70` exactly once;
3. recover `parent = *(child + 0x00)`;
4. select gauge slot from parent side byte `+0x0C`, with parent `+0x14` as a
   fighter-binding cross-check;
5. draw the four cells from a read-only meter snapshot; and
6. restore every callee-saved register and return to live `0x0071B364`, where
   the unchanged name draw continues.

This placement is after native health and chakra, once per visible side, while
the top-HUD draw context is still active. Parent `+0x00/+0x04`, scale `+0x08`,
side `+0x0C`, and the animated offsets used to produce the current position
are therefore available without hard-coded screen coordinates. The clean
atlas record at live `0x008C4338` is `(u=108, v=73, width=108, height=8)`, and
the native relative chakra anchor at live `0x008C4340` is `(78.0, 30.0)`.
Use the live parent transform and scale, then place the prototype at the
chakra anchor plus `(0, 8 + 3)` logical units vertically. For side `1`, negate
the relative horizontal geometry before adding the parent position, matching
the native child draw.

For an asset-independent prototype, reuse the resident solid-rectangle path
already proven by the startup counter: setup `0x001830A0`, color conversion
`0x00182A20`, four-vertex submission `0x001822B0`, and flush `0x00182F50`.
Each cell outline/background and each nonzero fill must run its own complete
setup/submit/flush sequence. Primitive type `5` joins submissions as a
triangle strip; batching several disconnected cells under one setup produces
diagonal wedges. Draw order should be four dark cells first, followed by up
to four bright fractional fills, so a partial cell cannot erase its outline.

The existing compiled implementation establishes the exact primitive recipe:

1. call `setup(5, 0)`;
2. read render-context pointer `0x0060745C` and abort the rectangle if null;
3. set context depth `+0xE8` to `0.0`, OR flags `+0x170` with `2` and
   `0x20000`, and pass context color `+0x100` plus the packed color to
   `0x00182A20`;
4. write each vertex's `x/y` to context `+0xE0/+0xE4` and call
   `0x001822B0(0)` in top-left, top-right, bottom-left, bottom-right order;
5. call `0x00182F50()`.

Use a `12x5` dark outer cell and a maximum `10x3` bright inner rectangle
inset by one logical unit. Multiply every dimension and gap by parent scale
`+0x08`. For P1, the inner rectangle's left edge stays fixed while its right
edge advances by `10 * fill`; for P2, its right edge stays fixed while its
left edge retreats by the same amount. Snapshot side, activity, meter counts,
and stock counts once before drawing so all four cells represent one state.
Native color sampling remains the final authority; the prototype needs a
high-contrast gold fill and a dark, nontransparent empty cell.

An inactive snapshot draws nothing; an active snapshot with zero meter draws
all four dark cells. Keeping those states distinct prevents an unbound manager
or stale fighter pointer from masquerading as a legitimately empty gauge.

The static seam proves side selection, current anchor, entrance/exit motion,
draw order, and coarse visibility through `+0x54`. It does **not** yet prove a
continuous cinematic alpha value or that every alternate HUD mode reaches the
same dispatcher. Capture-test those cases. If the native render context does
not automatically apply a fade, trace the alpha consumed by the chakra sprites
and multiply both prototype colors by it; do not invent a second visibility
timer.

Apply the edit through the builder's BTL-overlay target with the clean BTL hash
and the eight-byte guard above. The adapter may live in resident `228.BIN`, but
a fixed PNACH write to `0x0071B35C` is not safe because the overlay loads and
unloads.

## Builder and configuration integration

### Current user-facing surface

NA2.28 does not currently have a graphical feature editor. The released
builder is a console executable; the user edits `config.json`, while the inert
`catalog.modcat` beside it documents valid paths and values. Therefore this
feature must not invent a second settings store or claim that a GUI exists.
Its actual user interfaces are:

1. the `config.json` selection used at build time; and
2. the four-cell in-battle HUD specified above.

If a graphical catalog editor is added later, it should render the same
catalog node as an on/off control and reveal the same advanced fields. It must
not introduce another schema.

### Catalog shape and defaults

Add `features.battle_logic.storm_substitution_gauge` to
`features.battle_logic` in `catalog/catalog.modcat` as a union of a bare setting
and an object-valued
setting. This uses existing catalog semantics to support all three useful
states:

- `false`: disabled;
- `true`: enabled with parity defaults; or
- an object: enabled with explicitly tuned advanced values.

The intended declaration is structurally equivalent to:

```text
storm_substitution_gauge:
  setting {
    description: "Use a separate four-stock substitution gauge with parity defaults; substitutions no longer consume chakra.",
    patches: ["i__battle_logic__storm_substitution_gauge"],
  }
  |
  setting<{
    recovery_delay_seconds: decimal & 0..60 & step 0.25,
    refill_seconds_per_stock: decimal & >0 & <=10 & step 0.05,
    damage_recovery: bool,
    damage_percent_per_stock: decimal & >0 & <=100 & step 0.25,
  }> {
    description: "Use the four-stock gauge with advanced recovery tuning; substitutions no longer consume chakra.",
    patches: ["i__battle_logic__storm_substitution_gauge"],
  },
```

The simple release configuration is:

```json
"storm_substitution_gauge": true
```

The equivalent explicit configuration is:

```json
"storm_substitution_gauge": {
  "recovery_delay_seconds": 14.0,
  "refill_seconds_per_stock": 1.0,
  "damage_recovery": true,
  "damage_percent_per_stock": 31.25
}
```

Capacity `100`, stock cost `25`, damage award `25`, and four HUD cells stay
fixed in parity mode and do not appear as sliders. The catalog should initially
select `false` in `configurations/base.json`; qualification profiles may opt in
explicitly. Changing the distributed default after acceptance is a product
decision, not an implementation side effect.

### Generated constants and resident ownership

Follow the existing `xdash_chakra_cost.py` pattern rather than embedding
configuration literals in assembly. A focused
`@builder/scripts/substitution_gauge.py` reader should find exactly one
selected catalog node, expand bare `true` to the defaults above, revalidate an
explicit object defensively, and emit one aligned read-only fragment such as:

```c
typedef struct SubstitutionGaugeConfig {
    unsigned int stock_counts;          /* seconds-per-stock * 60 */
    unsigned int capacity_counts;       /* 4 * stock_counts */
    unsigned int recovery_delay_counts; /* configured seconds * 60 */
    unsigned int damage_threshold_q16;  /* normalized HP */
    unsigned int damage_recovery_enabled;
} SubstitutionGaugeConfig;
```

Parse catalog decimals from their source spelling with an exact decimal type,
not through a binary float. Require
`refill_seconds_per_stock * 60` and
`recovery_delay_seconds * 60` to be integral after catalog-step validation;
reject instead of silently truncating. Compute the Q16 threshold as
`ROUND_HALF_UP((damage_percent_per_stock / 100) * 65536)` and range-check every
result before packing it as little-endian `u32`. Bare `true` must therefore emit
exact words `(60, 240, 840, 20480, 1)` in the structure order above. Tests
should feed decimal strings such as `0.05`, `0.25`, and `31.25` to prevent a
future encoder from reintroducing host-float drift or Python's implicit
ties-to-even rounding.

`module_pipeline.py` should add that fragment to the selected battle-logic
runtime package just as it adds the X-dash scalar. The injection unit owns a
zero-initialized writable `substitution_gauge_state` fragment and compiled
resident sources under `src/battle_logic/`; native ABI shims remain small
static code fragments. The renderer reads the same resident state. It does not
store gameplay state in `BTL.BIN`.

### Exact builder hook map

Add one `i__battle_logic__storm_substitution_gauge` definition in
`catalog/injections.json`. All targets already exist in
`catalog/targets.tsv`; no new target registry or patching
mechanism is needed.

| Hook | Target/offset | Clean guard | Replacement template | Adapter behavior |
| --- | --- | --- | --- | --- |
| Eligibility | `na2_elf` `0x129810` | `700081C6803F023C` | `000000002D208002`, `jal26` relocation at `0x0` | `jal` shim + `move a0,s4`; call `can_spend`; tail-jump to virtual `0x22973C` |
| Successful spend | `na2_elf` `0x1299B8` | `700061C6803F023C` | `000000002D206002`, `jal26` relocation at `0x0` | `jal` shim + `move a0,s3`; call `spend`; tail-jump to virtual `0x2298F0` |
| Successful-use notification | `na2_elf` `0x1299F4` | `6CB5080C00000000` | default eight zero bytes, `jal26` at `0x0` | reset the delay for charged and free transitions; call displaced virtual `0x22D5B0`; return to `0x2298FC` |
| HP sample | `na2_elf` `0x14DB8C` | `7012090C00000000` | default eight zero bytes, `jal26` at `0x0` | sample HP from saved `a0`; call displaced virtual `0x2449C0`; return to `0x24DA94` |
| Battle clock | `na2_elf` `0x0F12B8` | `A0AE070C00000000` | default eight zero bytes, `jal26` at `0x0` | conditionally advance both slots; call displaced virtual `0x1EBA80`; preserve `v0`; return to `0x1F11C0` |
| Battle reset | `na2_elf` `0x0EF51C` | `B8251C0C00000000` | default eight zero bytes, `jal26` at `0x0` | reset generation/slots; call displaced live `0x7096E0`; preserve `v0` |
| Per-side HUD | `na2_btl` `0x6745C` | `9C7B1C0C00000000` | default eight zero bytes, `jal26` at `0x0` | call displaced live `0x71EE70`; draw read-only cells; return to live `0x71B364` |

The eligibility and spend hooks must set `replacement_hex` exactly as shown;
otherwise the catalog loader's default zero template would turn the required
register-move delay slot into a `nop`. The other five wrap existing `jal; nop`
pairs, so omitting `replacement_hex` intentionally produces an eight-byte zero
template before the symbolic `jal26` relocation is applied. Every continuation
and displaced target belongs in a symbolic shim relocation or a reviewed
native-address constant; do not write final resident payload addresses into the
catalog.

The new spend range ends at `0x1299BF`, immediately before the current
character-override hook at `0x1299C0`. When enabled, its shim skips that later
code; when disabled, no new hook exists. Composition tests must assert both
the non-overlap and the two selection outcomes.

### Files and release documentation

The minimal implementation touches these existing ownership points:

| Purpose | Canonical location |
| --- | --- |
| Public setting and descriptions | `features.battle_logic` in `@builder/catalog/catalog.modcat` |
| Hook and payload declarations | `@builder/catalog/injections.json` |
| Default/profile selection | `@builder/configurations/*.json` |
| Config-to-fragment encoder | `@builder/scripts/substitution_gauge.py` and `module_pipeline.py` |
| Gameplay state and native adapters | `src/battle_logic/substitution_gauge*.c` plus declared ABI shims |
| Builder/state tests | `tests/na228_builder/test_substitution_gauge.py` and focused pure-C/state tests |
| End-user explanation | `@scripts/release/README.md` |

The release README and catalog descriptions must state both observable
consequences: substitution uses the four-stock gauge, and ordinary successful
substitution no longer consumes chakra. They must also say that
`character_overrides.tsv`'s `substitution_cost` cells are ignored while the
mode is on; the rest of the character-override table remains active. A later
non-parity feature can deliberately map those values to stock cost.

Use solid renderer primitives for the accepted first version. That keeps the
HUD within the existing runtime-injection path. If bespoke atlas art is later
approved, add battle-logic texture inputs through the existing
`texture_patcher` engine and its guarded mapping format rather than creating a
new image-patching path.

## Implementation order

Implement and prove the feature in the following order so each new consumer
has one observable responsibility:

1. **Confirm lifecycle and HUD runtime coverage.** Runtime-confirm the
   established `0x0EF51C` construction wrapper for initial battle/rematch and
   the user-visible Practice restart, and capture-confirm the static BTL
   `0x6745C` top-HUD seam in ordinary and alternate HUD states.
2. **Add pure state logic.** Compile the two-slot state and deterministic update
   functions with no native behavior change.
3. **Add the HP-sample wrapper.** Wrap raw `0x14DB8C` and verify both
   that its displaced native call executes once and that raw `0x14DB80` remains
   the unchanged X-dash hook.
4. **Add the battle-clock wrapper.** Wrap raw `0x0F12B8`; prove the displaced
   countdown call and return value, the `0x05` flag mask, Unlimited-time
   recovery, global ordinal guard, and equal 30/60 FPS progression.
5. **Replace the resource gate.** Route only the `fighter + 0x70 >= 1.0`
   sub-block through `can_spend`.
6. **Replace successful spending.** Spend one stock on the charged block and
   skip native chakra/bookkeeping writes without overlapping the current cost
   hook.
7. **Notify every successful transition.** Wrap raw `0x1299F4` so both charged
   and free substitutions restart the delay without double spending.
8. **Enable damage recovery.** Validate normalized HP sampling, healing,
   multi-hit, cinematic, and Practice reset cases.
9. **Prototype the HUD.** Draw simple cells from the proven top-HUD hook and
   validate geometry, mirroring, alpha, and fractional fill.
10. **Finalize art and configuration.** Add guarded texture-patcher data only
   after the prototype is accepted.
11. **Run runtime acceptance.** Promote only observed results to current
    feature documentation.

## Validation plan

### Pure state tests

Add host-side tests for:

- initialization at `capacity_counts` and a derived debug value of `100`;
- four successful `stock_counts` spends to zero and rejection of a fifth;
- no spend or timer reset for an unsuccessful event;
- no spend but a full delay reset for each native free transition class;
- both native free transition classes still succeed at zero meter;
- `840`-count delay restart on every successful transition, including a free
  transition, with parity defaults;
- exact delay overshoot carry, including a 15-count delay under two-count
  updates;
- continuous integer recovery and clamp at `capacity_counts`;
- identical results for thirty `context[1] == 2` updates and sixty
  `context[1] == 1` updates;
- duplicate battle-clock calls with the same system-context `+0x194` ordinal;
- ordinal zero, wraparound, and first-sample validity;
- no pause catch-up when the ordinal advances without a clock callback;
- zero natural advance for timer flags `0x01` and `0x04`, continued recovery
  for Unlimited-time flag `0x02`, and all flag combinations;
- HP sampling and damage awards independent of natural clock advancement;
- fractional next-cell values;
- HP clamp/Q16 conversion, damage threshold, multiple thresholds in one
  update, and remainder carry;
- no banked damage at full meter;
- healing without a damage award;
- pointer rebind and explicit battle-generation reset; and
- independent Player 1 and Player 2 state.

Builder-facing tests should separately cover `false`, bare `true`, and the
advanced object; exact packed configuration words; invalid ranges/steps; all
seven hook guards; the non-overlap with raw `0x1299C0`; and public-catalog
projection without patch IDs.

Prefer testing the state engine as ordinary C logic with native memory access
isolated in thin adapters.

### Static/build validation

- Verify clean SHA-256 identities before deriving guards.
- Verify every hook's exact expected bytes.
- Assert the spend hook ends at raw `0x1299BF`, does not overlap the current
  raw `0x1299C0` cost hook, and skips it only when the gauge is selected.
- Assert the HP-sample shim calls its resident consumer and displaced native
  function once while leaving the adjacent X-dash hook unchanged.
- Assert the battle-clock shim sees entry flags, suppresses only mask `0x05`,
  advances at most once per ordinal, and returns the displaced countdown
  helper's exact `v0`.
- Validate all code/data placements and relocation targets through the normal
  builder.
- Rebuild twice and compare produced artifacts for determinism.
- Confirm disabled profiles are byte-identical to their pre-feature outputs.

### Runtime gameplay matrix

For both P1 and COM/P2, record:

| Scenario | Expected observation |
| --- | --- |
| Start/reset | Four full cells |
| Successful substitution | One cell spent exactly once; chakra unchanged |
| Failed or ineligible input | No meter change |
| Temporary-effect-`9` free substitution | Still succeeds at zero meter; no stock spent; recovery delay restarts |
| Item/status-ID-`9` free substitution | Still succeeds at zero meter; no stock spent; recovery delay restarts |
| Four consecutive successes | Values `75`, `50`, `25`, `0` |
| Empty-gauge attempt | Native transition rejected; no chakra change |
| Natural recovery | No movement before delay, then continuous fill to full |
| Use during recovery | Spend one stock and restart delay |
| Damage received | Stock award at configured normalized threshold |
| Multi-hit damage | Award from net HP loss, without duplicate counting |
| Jutsu/X-dash | Native chakra spending remains correct |
| Transformation | Gauge preserved |
| Practice reset/new round | Gauge full and stale damage cleared |
| Start menu | Natural delay/refill freezes with no catch-up after closing |
| Unlimited battle time | Native round countdown stays frozen; substitution delay/refill continues |
| Actor hit-stop | Recovery follows the native battle-clock call; HP loss is still sampled exactly once |
| Throw/Ultimate Jutsu and other cinematics | Record clock call, entry flags, ordinal, outer-gate state, and meter; require later-title-equivalent cinematics to freeze before acceptance |

Trace `fighter + 0x70` alongside the new state. The critical proof is that a
successful ordinary substitution changes the new meter by `25` while leaving
chakra unchanged, and that native chakra actions still change `+0x70` normally.

### Visual acceptance

Capture at least full, three-stock, two-stock, one-stock, empty, and partial
recovery states for both sides. Compare:

- mirrored placement and fill direction;
- spacing below the chakra bar;
- visibility over bright and dark stages;
- HUD entrance/exit and cinematic alpha;
- Practice, ordinary VS, and supported alternate battle HUDs;
- support-gauge enabled and disabled variants; and
- every supported aspect/frame-rate configuration.

Runtime visual validation requires the project's selected E2E or user-driven
path. Static texture previews cannot prove an in-game hook, alpha inheritance,
or overlap.

## Acceptance boundary and open questions

The architecture is sufficiently constrained to implement, but these items
must be resolved with runtime evidence before the feature is called complete:

- user-visible confirmation that Practice restart passes the established
  battle-graph construction seam (no second static fighter-publication path
  was found);
- once-per-update runtime confirmation for the `0x0F12B8` battle-clock hook and
  system-context `+0x194` ordinals at 30 and supported 60 FPS;
- outer-gate and timer-flag classification for each supported cinematic or
  selective pause-controller state, especially throw and Ultimate Jutsu
  demonstrations;
- whether `0.3125` normalized HP matches the desired later-title damage rate;
- continuous native alpha behavior and alternate-HUD coverage at the exact
  BTL `0x6745C` per-side post-chakra hook;
- final anchors and dimensions from NA2 captures; and
- whether a safe existing atlas rectangle can be reused or final art needs a
  dedicated proven rectangle.

These are implementation tasks, not permission to guess. The eligibility and
successful-spend addresses, shared chakra ownership, two-slot state model,
four-cell fill formula, and hook-conflict requirements are already strong
enough to prevent the common incorrect implementations.

## Web sources

Accessed 2026-08-20:

- [Official *Naruto Shippuden: Ultimate Ninja Storm 3 Full Burst* PC manual](https://cdn.akamai.steamstatic.com/steam/apps/234670/manuals/NS3FB_PC_MANUAL_GBqs_HR.pdf), especially battle controls and HUD on page 8.
- [Official *Naruto Shippuden: Ultimate Ninja Storm Revolution* PC manual](https://cdn.steamstatic.com/steam/apps/272510/manuals/Naruto_Storm_Revolution_PC_manual_ENG.pdf?t=1580312767), battle gauge descriptions on pages 4-5.
- [Official *Naruto Shippuden: Ultimate Ninja Storm 4* PC manual](https://media-center.namcobandaigames.eu/manuals/nsuns4/game/pc/NSUNS4_PC_manual_GB.pdf), next-round state, battle HUD, and one-notch substitution cost on pages 12-16.
- [Official *Naruto x Boruto: Ultimate Ninja Storm Connections* 1.20 notes](https://en.bandainamcoent.eu/naruto/news/naruto-x-boruto-ultimate-ninja-storm-connections-patch-120-notes), official confirmation that frame-rate-dependent substitution recovery was a bug and that the pre-recovery delay is independently adjustable.
- [*Storm 4* mechanics and strategy guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2085597351), community debug-tool measurements for the `0..100` meter, cost, delay, refill, and damage recovery.
- [*Storm Generations* substitution-system test](https://gl.ali213.net/html/2012/27197.html), translated empirical predecessor evidence for stocks, delayed refill, and damage recovery.
- [*Storm Revolution* terminology guide](https://www.gamepressure.com/narutoninjastormrevolution/in-game-terminology/zf6b1f), secondary explanation of the segmented gauge and post-use recovery.
- [*Storm 3 Full Burst* HUD screenshot](https://www.konsolinet.fi/tuotekuvat/1200x1200/1289475-naruto-shippuden-ultimate-ninja-storm-3-full-burst-10_1.jpg), visual reference for the connected four-cell rail and mirrored layout.
- [*Storm Connections* HUD screenshot](https://primagames.com/wp-content/uploads/pcinvasion/2023/11/how-to-stop-enemy-attacks-in-naruto-ultimate-ninja-storm-connections-subtitution.jpg), visual reference for the later separated-cell presentation.
