# Storm-style substitution bar for NA2 v2.28

This document defines the researched behavior and current candidate implementation of a
100-point substitution gauge with four equal recovery increments in NA2 v2.28. It covers the gameplay state,
native hook boundaries, builder integration, in-battle HUD, and validation
needed to reproduce the system used from *Ultimate Ninja Storm 3* onward.

The builder implementation exists, builds, and passes static tests; runtime
gameplay and visual acceptance remain user-run. Sections explicitly distinguish
official later-game behavior, community-measured behavior, confirmed NA2
evidence, and the implemented NA2 contract.
The existing substitution timing/reliability investigation remains in
[Substitution knowledge](substitution.md).

## Research coverage

- **Assigned scope:** this task covers the substitution-stock system used from
*Ultimate Ninja Storm 3* onward and its code- and UI-level implementation in
NA2 v2.28: later-game behavior and visual conventions, NA2 state ownership and
native hook boundaries, deterministic timing, damage recovery, lifecycle/reset
behavior, builder configuration, the in-battle HUD, and validation.

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
the rejected top-HUD prototype seam, the native support-gauge controller and
draw chain, the per-side top-HUD dispatcher and its parent visibility gate,
existing injection conflicts, and current builder mechanisms. It
was not a whole-program, whole-overlay, or every-later-release audit.

- **Confirmed coverage:** official sources establish a separate limited-use
gauge, empty-gauge rejection, gradual/time-based recovery, other recovery
means, one displayed notch per performance in *Storm 4*, and full gauges at a
new *Storm 4* round. Community measurements establish the configurable numeric
reference model and cinematic game-time behavior without promoting those
numbers to official facts. Clean NA2 evidence establishes the exact
resource-only eligibility splice, charged-spend block, common success
notification, two native free-transition classes, normalized HP field,
per-fighter HP-sample seam, once-per-battle recovery-clock seam and timer-flag
semantics, initial-battle construction reset, resident two-slot ownership, the
native fighter support value at `+0x74`, controller fields `+0x0A..+0x10`, and
the guarded BTL controller-update hook, the native support renderer's mirrored
X/shared Y anchors and post-bar decoration boundary, its primary sprite object
and three `$gp`-relative bar rectangle records, the top-HUD dispatcher byte
`+0x54` gate and downstream primary-child call, the common X/Y/scale/side
layout consumed by HP/chakra and the name renderer, and the Battle HUD character-name
renderer's independent Y anchor. It also establishes the eight-entry
Control Settings action map, the two native Guard-to-substitution searches, the
BTL instruction that folds the second Guard binding into logical block, and the
support-bar instructions that select the displayed action-map button and draw
the native fixed-50% red marker. The design below carries those findings
through state pseudocode, ABI responsibilities, exact hook guards and
continuations, builder-facing settings, independent native-texture reuse,
implementation order, and static, pure-state, runtime, and visual validation.

- **Unresolved or untested:** the user reported that the first candidate's
gameplay worked, but rejected its custom rectangle UI. The replacement
independent textured renderer is statically traced and built as a new candidate
but still requires user runtime validation. The user established that its
first support-controller-owned draw lifecycle was wrong and that the first
parent-gated version did not inherit the native slide or Ultimate-Jutsu shake.
The corrected shared-layout draw candidate still needs runtime confirmation.
Runtime work must also prove
callback cadence at native 30 FPS, initial-battle reset coverage, Unlimited-time behavior,
throw/Ultimate Jutsu and other cinematic clock suppression, COM and free-route
behavior at zero stock, action-index `7` remapping, index-`6`-only block input,
block-held Substitution after the legacy 16-frame cutoff, the per-player
top-HUD gauge placement, Gauge-mode 11-unit name shift, independent renderer visibility
across battle states, and supported aspect modes. Variable per-character
spending and its dynamic red threshold also require runtime comparison across
representative tiers. The
`14 s`, one-quarter-bar-per-second, and `0.3125`
normalized-damage defaults remain community-derived tuning inputs.

- **Deliberate exclusions and overlap:** this task does not alter substitution
input windows, reliability, reactions, or COM policy already owned by
[Substitution knowledge](substitution.md); add a PNACH or new settings
mechanism; copy copyrighted later-game textures; audit unrelated combat/HUD
systems; or claim indirect-call completeness outside the scoped traces.
- **Evidence limitations:** manual prose describes user-visible behavior, not internal
algorithms; community measurements can be version/platform dependent; static
disassembly proves control flow and clean bytes but not live cadence or visual
composition; and the independent textured renderer still requires a runtime
capture from the user-selected validation route.

## Outcome

When the feature is enabled, one shared runtime enum is exposed as
`Substitution: Chakra | Gauge | Free` in both pre-battle and Practice Settings:

- `Chakra` retains the native chakra gate, spend-suppression call, subtraction,
  and bookkeeping, and does not draw the substitution gauge;
- `Gauge` gives each side an independent 100-point gauge, and a successful
  ordinary, chargeable substitution spends that fighter's
  resolved `substitution_cost` percentage from the character-override table;
- `Free` accepts the resource gate without spending chakra or gauge and does
  not draw the substitution gauge;
- a native deliberately free substitution spends no stock but still restarts
  recovery delay only while `Gauge` is selected;
- an attempted input that does not produce a substitution spends nothing;
- gauge recovery begins after a delay from the last successful substitution;
- taking effective damage can restore gauge stock;
- the gauge starts full when a new battle begins; and
- an independent mirrored renderer reuses NA2's textured bar pieces to show
  the aggregate resource and place the red marker at the current fighter's
  executable cost, including continuous partial recovery.

Recovery and damage awards preserve the later games' four equal increments.
Spending deliberately uses NA2's existing per-character balance values. The
chosen UI adaptation uses one independent continuous textured bar per side
rather than reproducing the later games' four-cell artwork.

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
- modify the native Chakra Unlimited row;
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
- **Implemented NA2 candidate**: behavior present in the builder and statically
  validated, but not promoted to runtime-confirmed behavior until user
  acceptance.

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
timing in native battle-time counts at its fixed 30 FPS cadence.

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

### Control Settings and substitution input

When `features.battle.control_settings_rework` is enabled, Control Settings action-map
index `7` is the dedicated **Substitution** action, replacing the second native
Guard row. The feature redirects that row's label-pointer slot at raw ELF
`0x4B26AC` from
the native Guard string pointer (`40466000`) to resident ASCII `Substitution`.
The saved per-player mapping continues to own the physical button. Action index
`5` remains Linked Attack, and index `6` remains the sole Guard action. The
owned default map binds index `7`
Substitution to L1, index `6` Guard to R1, index `4` Item Select to L2, and
index `5` Linked Attack to R2 for both players. Players can remap every action
through the native screen without changing the patch.

The resident default at ELF raw `0x4C07A0` and the BTL input object's bootstrap
default at raw `0x1E4250` both contain the clean action-order bytes
`10002000400080000400080001000200`. The Control Settings patch replaces each
with `10002000400080000100020008000400`. Manager construction copies the
resident map into all three runtime banks and then into both saved player maps;
the BTL table supplies the same layout before the later configured-map refresh.

Control Settings has two additional native paths which the initial candidate
incorrectly left untouched. Select in `FUN_00387E10` restores nine 32-bit row
selections from virtual `0x005D5250`, raw ELF `0x4D5350`. Its clean values are
`1,0,3,2,4,5,6,7,1`; the shoulder rows therefore restore the original paired-
Guard layout instead of the owned action defaults. The candidate changes them
to `1,0,3,2,7,6,4,5,1`, leaving the face-button rows and vibration value
unchanged while making Select restore L1 Substitution, R1 Guard, L2 Item
Select, and R2 Linked Attack.

The native assignment helper `FUN_00387B90`, virtual `0x00387B90` / raw ELF
`0x287C90`, also contains explicit special cases for rows `4/5` and `6/7`.
Selecting any member of those groups can rewrite both members, because the
original UI assumes indices `6` and `7` are one two-button Guard action. The
candidate replaces the function entry with a guarded jump to the resident
`control_settings_assign_action` implementation. It assigns the chosen action
to only the selected physical-button row and swaps the displaced action into
the one row that previously owned the choice. This preserves the eight-action
permutation and keeps every button functional without Guard-pair coupling.
On edit entry, `FUN_00387E10` saves the row's original action at controller
offset `+0x5C + side*4`; the selector mutates the selected row directly. Cancel
restores that saved original, while confirmation must leave the selected row's
new action intact and write the saved original only into the other row that
previously owned the new action.

Two surrounding editor instructions encode the same retired assumption.
`FUN_00387E10` stores `6` over a selected row when that row currently contains
action `7`; the candidate nops that store at raw `0x287FBC`. In
`FUN_003881F0`, shoulder rows cycle through action indices `4..6`; changing the
upper immediate at raw `0x2883FC` from `6` to `7` makes Substitution selectable.
The face-button action range and vibration row remain unchanged.

The action-map order is Item Select at index `4`, Linked Attack at index `5`,
and the two native Guard entries at indices `6` and `7`. The substitution input
predicate's two native history searches select indices `6` and `7` at raw ELF
offsets `0x129740` and `0x12977C`. With Control Settings selected, one guarded
instruction edit changes the first selector to index `7`; the second selector
already selects index `7` and remains clean:

```text
0x129740: 06000524 -> 07000524  # li a1,6 -> li a1,7
0x12977C: 07000524               # native li a1,7 retained
```

Both arms then inspect the same new-press history for the configured
Substitution action. A hit returns through the first arm; a miss repeats the
same search harmlessly. Index `6` cannot satisfy the predicate, so pressing or
holding the remaining Guard action does not itself cause a substitution. NA2's
native predicate also rejects every substitution request after Guard has been
held for 16 frames. That rule coupled blocking and substitution only because
both native Guard bindings served both actions. The feature's guarded edit at
raw ELF `0x129720` replaces `slti v0,v0,0x10` (`10004228`) with `li v0,1`
(`01000224`), so the following native branch always reaches the action-`7`
history search. A fresh Substitution press can therefore be accepted while
Guard remains held for any duration. The remaining native timing-window,
reaction-state, and forbidden-state gates are preserved; Guard never requests
a substitution by itself.

NA2's BTL input translator natively folds both action indices `6` and `7` into
the same logical Guard bit. The guarded BTL edit at raw `0x3C02C` replaces
`lh v0,0xE(s1)` (`0E002286`) with `move v0,zero` (`2D100000`). Index `7`
therefore stops contributing to block while index `6` remains fully functional
as Guard.

The native support-bar draw loads its displayed button from action-map offset
`+0x0A`, which is index `5`. The top-HUD candidate never enters that renderer:
the substitution feature draws its own bar and marker without a button path,
flushes that draw, and restores the complete borrowed sprite command state
before the native support draw can run later in the same HUD pass. When No
Support is enabled, its separate hook suppresses the native support draw; when
disabled, the native lower bar and index-`5` prompt draw normally. Raw `0x69184`
therefore remains clean, and no binding prompt is added beside the independent
top-HUD bar. Control Settings still exposes and remaps action index `7` as
Substitution.

The Control Settings patch is independent of the gauge: it can expose separate
Guard and Substitution actions while ordinary substitutions still use native
chakra behavior. The gauge requires Character Overrides only. No Support is an
independent choice: disabling it retains native field support, its lower gauge,
and Linked Attack while the substitution bar remains available; enabling it
suppresses field support and the native support gauge without suppressing the
independent substitution bar. No Support intentionally does not erase selected
support data, which remains available to linked Jutsu.

### Baseline values

Use the following defaults for the first runtime implementation:

| Parameter | Default | Reason |
| --- | ---: | --- |
| Capacity | `100.0` | Matches the measured later-game representation |
| Recovery increment | `25.0` | Four equal recovery/damage-award increments |
| Successful-use cost | Character `substitution_cost / 100` | Shared normalized balance source |
| Post-use recovery delay | `14.0 s` | Repeatedly measured in the series |
| Natural recovery | `25.0/s` | Console-era baseline of one stock per second |
| Damage threshold | `0.3125` normalized HP | Provisional mapping of `31.25/100` |
| Damage award | `25.0` | One stock per threshold |
| Starting value | `100.0` | Four stocks |

All numeric values are generated configuration data rather than literals inside
hook shims. Capacity and the recovery increment remain fixed together for the
parity mode; tuning normally changes delay, natural rate, or damage threshold.
The character table stores `substitution_cost` as percentage points in
`0..100`. Authoritative gauge state remains integer counts, and one rounded
integer cost is shared by eligibility, spending, and the visible marker.

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
cost_counts = round(capacity_counts * resolved_substitution_cost / 100)
```

The proposed catalog steps make the first three products exact integers. At
the default, one stock is `60` counts, capacity is `240`, and delay is `840`.
The familiar debug value is derived only when needed as
`100 * meter_counts / capacity_counts`.

For each player slot, maintain `meter_counts`, `recovery_delay_counts`,
`damage_accumulator_q16`, `last_hp_q16`, and identity/reset metadata. Convert
native HP once per sample with
`round(clamp(current_hp, 0, 1) * 65536)`; this prevents floating accumulation
and prevents negative knockout HP from manufacturing extra damage.

The authoritative update is:

```text
on successful charged substitution:
    require meter_counts >= cost_counts
    meter_counts -= cost_counts

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
    require system_context[1] == 2 for NA2's native 30 FPS update
    advance = 2 native display counts
    for each active slot:
        delay_consumed = min(recovery_delay_counts, advance)
        recovery_delay_counts -= delay_consumed
        remaining_advance = advance - delay_consumed
        meter_counts = min(capacity_counts, meter_counts + remaining_advance)
        if meter_counts == capacity_counts:
            damage_accumulator_q16 = 0
```

`last_hp_q16` is initialized without awarding damage when a slot first binds.
Healing or an explicit HP restoration raises the baseline but never subtracts from the
accumulator. Damage taken while a cinematic temporarily suspends ordinary
fighter updates is captured as the net HP decrease on the next valid update.
HP sampling and damage awards are independent of the battle-clock callback, so
local hit-stop does not create duplicate awards or become an invented recovery
clock rule.

Carrying `advance` past the end of the delay is required. For example, a
15-count delay processed by two-count 30 FPS updates leaves one count of refill
on the eighth update; discarding it would make the same configured delay one
count longer than the configured battle-time interval. At NA2's native 30 FPS,
each advancing update contributes two counts: the default 840-count delay is
420 updates, and a 60-count stock refill is 30 updates.

Do not bank damage while the meter is full. Otherwise a player could take
damage at full gauge, spend later, and receive an immediate hidden stock that
the later-game UI never communicated. Remainder carry and more than one award
from a large HP decrease are implemented NA2 candidate behavior; the community source
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

The full gauge must be initialized at the proven new-battle construction
boundary, not only when a fighter pointer happens to change. NA2 has no round,
rematch, or Practice-restart lifecycle in this contract.

Required lifecycle behavior:

| Event | Result |
| --- | --- |
| New battle | Both slots reset to full |
| In-match transformation with the same player slot | Gauge is preserved |
| Fighter pointer replacement inside the same player slot | Rebind without duplicating state; preserve only when confirmed to be a transformation |
| Return to menu or no live manager | State is invalidated |
| Active start menu or other scheduler suppression | Timer flag `0x01` stops natural delay/refill; do not catch up afterward |
| Battle timer disabled / no time limit | Timer flag `0x02` stops only the native countdown; substitution recovery continues |
| Battle timer expired | Timer flag `0x04` and the outer terminal gates stop natural delay/refill |
| Ordinary actor hit-stop | Follow the once-per-battle clock; do not add a separate `fighter + 0x20C` rule |
| Cinematic/selective scheduler state | Follow the proven native clock call and still capture a runtime trace before acceptance |

The new-battle reset seam is established statically below. Pointer-change
heuristics alone are not an acceptable substitute for that construction hook.

`FUN_00214a40` is the confirmed fighter-object initializer. It clears HP at
`+0x6C`, chakra at `+0x70`, the resource-bookkeeping fields at `+0x1A0` and
`+0x1A4`, and the rest of the fighter's transient state. The maintained export
has one direct reference, from the fighter constructor immediately before that
constructor returns. This is a sound new-object initialization signal, but it
does not prove the start of a new battle. It therefore cannot replace the
separately proven battle-construction signal.

### Interactions

- **Chakra:** substitutions must not read or write chakra once the feature is
  active. Jutsu, chakra dash, X-dash, and ordinary chakra regeneration remain
  unchanged.
- **CPU:** Player 2/COM uses the same gate, cost, and recovery logic. The bar is
  a battle rule, not a human-input-only affordance.
- **Transformations:** state belongs to the player slot and battle generation,
  not the current character ID. Transformations must not refill it.
- **Per-character costs:** the gauge requires the NA2.28 character-override
  feature and resolves its `substitution_cost` by match-start identity. The
  table value is percentage points on `0..100`; both eligibility and spending
  use the same rounded `capacity_counts * cost / 100` value. A transformation
  retains its match-start cost just as the native-chakra path does.
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
result. The predicate reproduces the native `fighter + 0x70 >= 1.0` comparison
in `Chakra`, checks the character-resolved resident cost in `Gauge`, and
returns true for the resource check in `Free`.

This hook changes availability while retaining all timing and reliability
gates. Returning true from the entire function would be incorrect.

### Successful spend

`FUN_002297d0`, virtual `0x002297D0` / raw ELF offset `0x1298D0`, owns the
transition and native conditional resource spend. `param_3 == 0` branches
directly to the common transition at virtual `0x002298F0`; a charged
`param_3 != 0` route first performs two native transition-setup calls, then
reaches the resource-suppression call at virtual `0x00229884` / raw
`0x129984`. Its ordinary spend block is virtual
`0x002298B8..0x002298EC` / raw `0x1299B8..0x1299EC`; continuation is raw
`0x1299F0`.

That block subtracts the cost from `fighter + 0x70`, clamps it to zero, and
writes the resource-bookkeeping field at `fighter + 0x1A0`. It is reached only
when native chakra spending is not suppressed. Runtime testing established
that Infinite Chakra suppresses this block; placing the gauge adapter there
therefore allowed a charged substitution to succeed without consuming gauge.
The correct semantic boundary is the charged-route call at virtual
`0x00229884`: it is after native transition setup, is unreachable for
`param_3 == 0`, and precedes every native chakra-spend suppression condition.

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
therefore remain usable at zero meter and branch to the common transition
before the new spend hook. Hooking the charged-route seam preserves them
without a caller whitelist, while hooking every call to `FUN_002297D0` would
incorrectly charge them.

The current per-character cost feature hooks raw `0x1299C0` inside the native
spend block and then resumes native subtraction. The gauge hook can coexist
without an overlapping edit: guard the `jal FUN_003074F0` and its delay slot at
raw `0x129984..0x12998B`, whose clean bytes are
`3C1D0C0C00000000`, and replace the call with a generated `jal` to the resident
shim. The preceding native instruction already places `s3` (the fighter) in
`a0`. The shim calls `substitution_gauge_route_spend(fighter)`. In `Chakra`
mode it restores `a0 = s3`, calls the displaced `FUN_003074F0`, and resumes at
virtual `0x0022988C`, preserving the complete native suppression, subtraction,
per-character cost hook, and bookkeeping path. In `Gauge` mode it charges the
resident gauge and jumps to virtual `0x002298F0`; in `Free` mode it spends
nothing and takes that same no-chakra continuation.

With the gauge disabled, that new hook is absent and the existing
per-character cost hook behaves byte-for-byte as it does now. With the gauge
enabled, both guarded writes still compose because their byte ranges do not
overlap. `Chakra` resumes through the existing per-character chakra-cost hook;
`Gauge` and `Free` skip it because neither mode spends chakra. This is runtime
resource routing, not a catalog conflict or a reason to disable the broader
character-override table.

`substitution_gauge_route_spend` resolves the same rounded character cost again
in `Gauge` mode and leaves the meter unchanged if it is called below that
amount; the upstream gate remains the normal source of eligibility. A valid
zero cost is affordable and subtracts zero.

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
| `0x02` | Native countdown freeze; established setup paths use it for the `100`/Unlimited battle-time setting | Ignore this bit and advance, because an unlimited battle must still recover substitution stocks |
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
(`lbu v0,1(a0); jr ra; nop`). Native battle sets that byte to `2`. Native rumble
maintenance already subtracts this value from durations stored in display-count
units, independently confirming its time meaning. The gauge supports NA2's
native 30 FPS runtime only: require `context[1] == 2` and advance by exactly two
counts. Any other value fails closed instead of being treated as another frame
rate.

System-context `+0x194` is the engine-update ordinal incremented by
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

### New-battle reset seam

`FUN_001EF330`, virtual `0x001EF330` / raw ELF offset `0x0EF430`, is the
heavy battle-graph constructor already documented by the stage lifecycle. When
its battle bundle at controller `+0x18` is absent, it constructs that bundle,
publishes the two returned fighter pointers to manager `+0xDE4` and `+0xDE8`,
and continues building the graph. The corresponding `FUN_001EEFD0` teardown
clears manager `+0xDE0..+0xDE8`, clears `+0xDEC..+0xDF4`, destroys the bundle,
and sets controller `+0x18` to null.

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
better new-battle reset owner than lazy fighter-pointer binding. Runtime tracing
must confirm one call when a battle begins. Opening or cancelling Practice
Settings must preserve the gauge; no separate Practice reset hook is part of
this feature.

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

The candidate exposes a deliberately small resident API:

```c
float battle_logic_substitution_cost_fraction(void *fighter);
void substitution_gauge_reset_battle(void *manager);
void substitution_gauge_sample_hp(void *fighter);
void substitution_gauge_advance_battle(void *timer);
int  substitution_gauge_can_spend(void *fighter);
int  substitution_gauge_route_spend(void *fighter);
void substitution_gauge_note_success(void *fighter);
```

The runtime ownership is intentionally one-way:

```text
battle construction ------------------------------> reset both slots
fighter callback ---------------------------------> sample committed HP
battle-clock callback ----------------------------> advance both slots
eligibility hook ------------------------------read-> can_spend
charged spend hook ----------------------------route-> native chakra, gauge cost, or free
common success hook ---------------------------write-> restart delay
state publication ----------------------------write-> resident fill and cost mirrors
BTL support-controller hook --------------------read-> fill mirror into native +0x0C
BTL marker hook --------------------------------read-> cost mirror into marker X
```

Only the battle-clock callback advances natural recovery; fighter callbacks
only sample committed HP. Only confirmed transition hooks spend or restart
delay. The renderer is never an update owner, which prevents hidden extra
recovery when a side is drawn more than once or not drawn at all.

`substitution_gauge_advance_battle` validates the fixed native timer pointer,
entry flags, resident manager, system context, native `context[1] == 2`, and
global ordinal, then passes two counts to a native-independent two-slot state
transition. Keeping those native-memory reads in the adapter leaves the state
engine testable with an explicit count. `substitution_gauge_sample_hp` maps only
manager-owned fighter pointers and is idempotent for an unchanged HP sample.
The cost resolver uses the same match-start character identity as native
substitution-cost overrides. Invalid sides, manager mismatch, and inactive
slots publish zero. The renderer must not advance timers, infer damage, or
mutate gameplay state.

Do not use `last_clock_ordinal == 0` as an uninitialized sentinel because zero
is a valid counter value and the native ordinal can wrap. Track validity
separately, accept the first observed ordinal, and suppress only an equal
subsequent ordinal. Reset validity at every battle-generation reset. If the
manager is null or a fighter does not match manager `+0xDE4/+0xDE8`,
`can_spend` must fail closed and HP sampling must do nothing rather than
silently binding arbitrary objects.

## HUD implementation

### Chosen NA2 adaptation

Draw an independent substitution bar below each top chakra bar while reusing
NA2's already-loaded native outer-frame, inner-fill, and marker rectangles plus
its resident sprite primitives. The candidate owns mirrored X bases `64/448`,
shared Y `38`, fill width, cost-marker position, visibility, and draw order. It
shifts both Battle HUD character names down by 11 logical units. Recovery still uses four
equal increments, but spending is per-character and the bar displays aggregate
`0.0..1.0` fill continuously instead of drawing four new cells. The complete
native support renderer, including its coordinates, button badge, and support
decorations, remains byte-clean and is independently controlled by No Support.

The raw 1244×933 PCSX2 capture
`SLOP-NA228 [_]_SLOP-NA228_20260827103726.png` measured the Player 1 custom
frame at `x=197..399, y=147..181`. Normalizing the user-supplied reference to
the same viewport put it at approximately `x=198..401, y=113..148`.
Horizontal placement and dimensions therefore remain unchanged. The first
correction moved the bar from Y offset `50` to `36` and the character-name anchor from
`60` to `50`. A 4× inspection of the subsequent raw capture
`SLOP-NA228 [_]_SLOP-NA228_20260827105156.png` showed the bar's marker/frame
4–5 pixels above the reference and the name's upper edge about 13 pixels above
it. The capture pair measures about 2.43 pixels per bar unit and 2.5 pixels per
character-name-anchor unit, refining the anchors to bar Y `38` and character-name Y `55` while
leaving X and every bar dimension unchanged.

The feature depends only on `features.battle.character_overrides`, which
provides the single normalized cost source. No Support remains independent and
controls only native field support and its lower gauge. The supported build-time
combinations are:

| No Support | Character Overrides | Substitution gauge | Result |
| --- | --- | --- | --- |
| `false` | either | `false` | Clean native support behavior; no combined hook selected |
| `true` | either | `false` | No Support behavior; native support gauge forced hidden |
| `false` | `true` | enabled | Native field support and its lower gauge remain available; the independent substitution bar appears alongside it only when runtime mode is Gauge |
| `true` | `true` | enabled | Native support remains suppressed by No Support; the independent substitution bar appears only when runtime mode is Gauge |
| either | `false` | enabled | Invalid configuration |

### Confirmed native controller contract

The per-side draw wrapper exported as `FUN_0071D230` first calls the native
controller update, then reads controller byte `+0x0A`; it calls the dedicated
`TEX_xgauge` draw only when that byte is nonzero. The complete-file update call
is BTL `0x69380`, guarded by `04 72 1C 0C`; the unchanged native draw call is
BTL `0x69398`, guarded by `BC 72 1C 0C`. Their header-omitting export addresses
are `0x0071D240` and `0x0071D258` respectively.

The encoded update target is live `0x0071C810`. Because BTL's complete file has
a `0x40`-byte header, its physical exported function begins at
`FUN_0071C7D0`; do not add another `0x40` to the encoded call target. Static
tracing establishes these controller fields:

| Field | Native role |
| ---: | --- |
| `+0x00` | side index, `0` or `1` |
| `+0x04` | fighter pointer used by the native update |
| `+0x0A` | visibility state tested by the draw wrapper |
| `+0x0B` | fill/animation state: `0` hidden, `1` below full, `2` full |
| `+0x0C` | current normalized support fill |
| `+0x10` | prior fill saved by the native update |
| `+0x18` | primary support-gauge render object used by the native draw |

The native update copies fighter support value `+0x74` into controller
`+0x0C`. The native draw scales its foreground width by `controller[+0x0C] *
64.0`, mirrors the second side, and uses the `+0x0A/+0x0B` states for
visibility, color, and full/partial presentation. A selected No Support record
has an out-of-range native support ID, so the clean update sets `+0x0A = 0`.
The independent renderer does not overwrite any of those controller fields.

The native red marker is fixed at half bar: fill geometry starts at X offset
`20.0`, spans `64.0`, and the marker loads offset `52.0`, so
`(52 - 20) / 64 = 0.5`. Its draw call is live `0x0071CFD0`, BTL raw `0x69110`,
with clean bytes `10EF0D0C`. The candidate leaves that call and its complete
native renderer clean. Its own draw uses the same resident sprite primitive
and computes marker X from the current side's executable cost fraction.

The native lower-support marker tint comes from resident `0x0040BFC8`. Clean
`SLPS_258.37` stores `12 00 00 00 FF FF FF FF` there, and BTL live
`0x0071CF60..0x0071CF9C` packs its first three channel bytes as RGB
`(0x12, 0x00, 0x00)`. User runtime testing showed that this dark native tint
appears black on the independent top-HUD bar. The current candidate therefore
keeps the native marker rectangle but tints only its independent copy with
normal-intensity red `(0x7F, 0x00, 0x00)`; the native support marker remains
unchanged.

The same clean renderer loads Player 1/Player 2 X bases `120.0/392.0` at BTL
raw `0x68C24/0x68C88` and shared Y base `340.0` at `0x68C6C`; the candidate
leaves all three constants clean. Raw `0x69124`, which begins the later
button/support-decoration tail, also remains clean. The independent renderer
instead owns mirrored bases `64.0/448.0` and Y `38.0`, and contains no button
or support-decoration path.

The controller's primary bar sprite is the initialized object at `+0x18`.
Native code addresses the outer-frame, cost-marker, and inner-fill rectangles
as BTL `$gp - 0x5CD8`, `$gp - 0x5CD0`, and `$gp - 0x5CC0`. The candidate
captures BTL `$gp` at the guarded update-call boundary and passes those records
to its own geometry code. It reuses resident sprite commit/draw/flush primitives
at `0x001CC350`, scaled rectangle draw `0x0037BD00`, and `0x001CC070`, then
restores every borrowed command field before the later native support draw:
flags, alpha, offsets, destination geometry, source geometry/mode, and packed
colors. The independent and native gauges can therefore serialize draws through
the same initialized sprite without leaking top-HUD geometry into the lower
support renderer.

The Battle HUD character-name renderer begins at BTL raw `0x67F20`. The
substitution feature does not hook or replace its X path. Its shared Y load is
the pair at raw `0x67F60..0x67F67`, clean `8C00023CDC4240C4`, and also remains
untouched. The current candidate replaces only the following multiplication
and side-byte load at raw `0x67F68..0x67F6F`, clean
`820001460C00A290`, with a guarded `jal; nop` to a resident ABI shim. The shim
passes the already loaded Y to C, preserves the live `v1` name destination,
`a1` layout pointer, scale `f1`, and live `f3..f5` results, then reproduces the
displaced `mul.s f2,f0,f1` and `lbu v0,12(a1)`. The C adjuster returns Y
unchanged in Chakra and Free modes and returns `Y + 11.0` in Gauge mode. This
works with whichever Y the renderer loaded and gives the substitution feature
no X coordinate, absolute Y coordinate, or localization dependency.

### Independent renderer hook behavior

The first candidate drew from the BTL `0x69380` support-controller update hook.
User runtime testing on 2026-08-27 proved that callback does not share the
top-HUD lifecycle: the custom bar appeared while ordinary Jutsu hid HP/chakra
and disappeared while Ultimate Jutsu retained the ordinary top HUD. The
current candidate keeps `0x69380` only to capture BTL `$gp`, call live
`0x0071C810` exactly once, and cache each controller by its native side field.
It does not draw there and does not change controller `+0x0A`, `+0x0B`,
`+0x0C`, fighter `+0x74`, or the native renderer. Publication continues to
write `meter_counts / capacity_counts` and rounded executable
`cost_counts / capacity_counts` to separate resident two-float mirrors.

The top-HUD dispatcher at BTL raw `0x673E0` reads parent byte `+0x54` and skips
all child draws when it equals `1`. Its primary-child draw call is downstream
of that gate at raw `0x67434`, guarded by `C86D1C0C`; the encoded displaced
target is live `0x0071B720`. The replacement calls that renderer once, obtains
the shared layout from child `+0x00`, and selects the matching cached controller
from layout side byte `+0x0C`. The primary HP/chakra renderer and the name
renderer at raw `0x67F20` both consume that layout's X, Y, scale, and side fields
at `+0x00/+0x04/+0x08/+0x0C`.

The first parent-gated runtime candidate inherited visibility but retained fixed
custom coordinates. User testing on 2026-08-27 established that the native
HP/chakra/name group moved upward and off-screen while the custom bar stayed
fixed, and that the bar missed the Ultimate-Jutsu shake. The corrected renderer
computes its steady anchors as layout X plus mirrored `64.0 * scale` and layout
Y plus `38.0 * scale`, applies the same scale to every offset and dimension,
and uses the primary HUD sprite's current alpha for its draw. This attaches the
custom bar to the same per-side visibility, translation, shake, scale, and alpha
state without listing or guessing Jutsu/animation states in resident code.

No Support separately replaces only the native support draw call at BTL
`0x69398` with its no-op. With the substitution feature disabled, no battle-
logic hook exists at either `0x69380` or `0x67434`; No Support therefore retains
its accepted single-call suppression. With the feature enabled, `0x69380`
caches the clean controller-update result, `0x67434` draws only after the native
top-HUD gate, and the later native support call remains suppressed. This does
not revive the rejected BTL `0x6745C` post-chakra hook, support-controller mode
word, cross-module fill buffer, native marker hook, or any substitution-specific
edit inside the support renderer.

Apply the hook through the builder's guarded BTL target, never as a fixed PNACH
write: the overlay loads and unloads. Static evidence establishes the dataflow
and clean bytes, but only runtime capture can establish whether every desired
battle state presents the native bar acceptably.

## Builder and configuration integration

### Current user-facing surface

NA2.28 does not currently have a graphical feature editor. The released
builder is a console executable; the user edits `config.json`, while the inert
`catalog.modcat` beside it documents valid paths and values. Therefore this
feature must not invent a second settings store or claim that a GUI exists.
Its actual user interfaces are:

1. the `config.json` selection used at build time; and
2. the shared `Substitution: Chakra | Gauge | Free` row in pre-battle and
   Practice Settings; and
3. the independent textured bar rendered only while `Gauge` is selected.

If a graphical catalog editor is added later, it should render the same
catalog object and its required default plus optional advanced fields. It must
not introduce another schema.

### Catalog shape and defaults

Add `features.battle.substitution.gauge` under the shared substitution group in
`catalog/catalog.modcat` as an object-valued setting. This uses existing
catalog semantics to support two build-time states:

- `false`: disabled;
- an object: enabled with a required runtime default and optional advanced
  tuning values.

Every enabled form requires
`features.battle.character_overrides = true`; reject an enabled gauge
when that dependency is false. `features.battle.support_disabled` is not a
dependency and must not be silently enabled: `false` keeps native field support
and its lower gauge, while `true` suppresses them independently. Do not
create a second configuration field.

The Control Settings declaration is structurally equivalent to:

```text
control_settings_rework: setting {
  description: "Expose Guard and Substitution as independent remappable actions and default both players to L1 Substitution, R1 Guard, L2 Item Select, and R2 Linked Attack.",
  patches: ["e__battle__control_settings_rework", "i__battle__control_settings_rework"],
},
```

The gauge declaration is structurally equivalent to:

```text
gauge: setting<{
    default: "chakra" | "gauge" | "free",
    recovery_delay_seconds?: decimal & 0..60 & step 0.25,
    refill_seconds_per_stock?: decimal & >0 & <=10 & step 0.05,
    damage_recovery?: bool,
    damage_percent_per_stock?: decimal & >0 & <=100 & step 0.25,
  }> {
    description: "Install selectable Chakra, Gauge, and Free substitution resource modes with an independently rendered 100-point gauge.",
    patches: ["i__battle__settings_rework", "i__battle_logic__substitution__gauge"],
  },
```

The simple release configuration is:

```json
"substitution": {
  "frames_before": 4,
  "frames_after": 4,
  "gauge": {
    "default": "gauge"
  }
}
```

The equivalent explicit configuration is:

```json
"substitution": {
  "frames_before": 4,
  "frames_after": 4,
  "gauge": {
    "default": "gauge",
    "recovery_delay_seconds": 14.0,
    "refill_seconds_per_stock": 1.0,
    "damage_recovery": true,
    "damage_percent_per_stock": 31.25
  }
}
```

Capacity `100`, recovery/damage award `25`, and per-character cost from the
normalized override table stay fixed and do not appear as sliders. The base
configuration selects `Gauge`; omitted recovery fields retain the parity
defaults. Because `default` is mandatory, bare `true` is invalid.

### Generated constants and resident ownership

Follow the existing `xdash_chakra_cost.py` pattern rather than embedding
configuration literals in assembly. A focused
`@builder/scripts/substitution_gauge.py` reader should find exactly one
selected catalog node, merge omitted object fields with the defaults above,
revalidate the resolved values defensively, and emit one aligned read-only
fragment such as:

```c
typedef struct SubstitutionGaugeConfig {
    unsigned int stock_counts;          /* seconds-per-stock * 60 */
    unsigned int capacity_counts;       /* 4 * stock_counts */
    unsigned int recovery_delay_counts; /* configured seconds * 60 */
    unsigned int damage_threshold_q16;  /* normalized HP */
    unsigned int damage_recovery_enabled;
    unsigned int default_mode;          /* Chakra 0, Gauge 1, Free 2 */
} SubstitutionGaugeConfig;
```

Parse catalog decimals from their source spelling with an exact decimal type,
not through a binary float. Require
`refill_seconds_per_stock * 60` and
`recovery_delay_seconds * 60` to be integral after catalog-step validation;
reject instead of silently truncating. Compute the Q16 threshold as
`ROUND_HALF_UP((damage_percent_per_stock / 100) * 65536)` and range-check every
result before packing it as little-endian `u32`. Bare `true` and an explicit
empty object are invalid because they omit `default`; the base object must emit
exact words `(60, 240, 840, 20480, 1, 1)` in the structure order above. Tests
should feed decimal strings such as `0.05`, `0.25`, and `31.25` to prevent a
future encoder from reintroducing host-float drift or Python's implicit
ties-to-even rounding.

`module_pipeline.py` adds that fragment to the selected battle-logic runtime
package just as it adds the X-dash scalar. The battle-logic injection owns
zero-initialized `substitution_gauge_state`, the two-float fill and cost mirrors,
the per-side cached display source, the independent renderer, and its native
ABI shims. The existing character-override payload exports one resolver that
returns a clamped `0..1` cost
fraction from match-start identity. No QOL-owned configuration word or cross-
module display buffer is required, and fighter support field `+0x74` remains
exclusively native.

### Exact builder hook map

Add `i__battle__control_settings_rework` and
`i__battle_logic__substitution__gauge` definitions in
`catalog/injections.json`. All targets already exist in
`catalog/targets.tsv`; no new target registry or patching
mechanism is needed.

| Hook | Target/offset | Clean guard | Replacement template | Adapter behavior |
| --- | --- | --- | --- | --- |
| Eligibility | `na2_elf` `0x129810` | `700081C6803F023C` | `000000002D208002`, `jal26` relocation at `0x0` | `jal` shim + `move a0,s4`; call `can_spend`; tail-jump to virtual `0x22973C` |
| Successful spend | `na2_elf` `0x129984` | `3C1D0C0C00000000` | default eight zero bytes, `jal26` relocation at `0x0` | replace `jal FUN_003074F0` after charged-transition setup; preceding native instruction supplies `a0 = s3`; call `route_spend`; Chakra calls the displaced native helper and resumes at `0x22988C`, while Gauge and Free continue at `0x2298F0` |
| Successful-use notification | `na2_elf` `0x1299F4` | `6CB5080C00000000` | default eight zero bytes, `jal26` at `0x0` | reset the delay for charged and free transitions; call displaced virtual `0x22D5B0`; return to `0x2298FC` |
| HP sample | `na2_elf` `0x14DB8C` | `7012090C00000000` | default eight zero bytes, `jal26` at `0x0` | sample HP from saved `a0`; call displaced virtual `0x2449C0`; return to `0x24DA94` |
| Battle clock | `na2_elf` `0x0F12B8` | `A0AE070C00000000` | default eight zero bytes, `jal26` at `0x0` | conditionally advance both slots; call displaced virtual `0x1EBA80`; preserve `v0`; return to `0x1F11C0` |
| Battle reset | `na2_elf` `0x0EF51C` | `B8251C0C00000000` | default eight zero bytes, `jal26` at `0x0` | reset generation/slots; call displaced live `0x7096E0`; preserve `v0` |
| Battle HUD character-name Y adjustment | `na2_btl` `0x67F68` | `820001460C00A290` | default eight zero bytes, `jal26` at `0x0` | receive the already loaded Y, add `11.0` only in Gauge mode, preserve all live name-renderer state, and reproduce the displaced scale multiplication and side-byte load |
| Independent HUD render-source cache | `na2_btl` `0x69380` | `04721C0C` | default four zero bytes, `jal26` at `0x0` | capture BTL `$gp`; call displaced live `0x71C810`; cache the initialized controller by side; return to the unchanged support-visibility test without drawing |
| Independent HUD draw | `na2_btl` `0x67434` | `C86D1C0C` | default four zero bytes, `jal26` at `0x0` | after the native parent HUD visibility gate and non-null primary-child check, call displaced live `0x71B720`, resolve the shared layout and side, and draw the independent outer frame, fill, and marker from the cached controller and resident fractions through the native X/Y/scale transform and primary-sprite alpha |

The eligibility hook must set `replacement_hex` exactly as shown; otherwise
the catalog loader's default zero template would turn its required
register-move delay slot into a `nop`. The spend hook uses the native preceding
`move a0,s3`, so its generated `jal` intentionally has a `nop` delay slot. The
other four battle-logic hooks wrap
existing `jal; nop` pairs. The name-Y hook replaces the post-load multiplication
and side-byte load, and its shim preserves the caller-live name-renderer state
around the relative C adjustment before reproducing both displaced instructions.
Omitting `replacement_hex` intentionally produces an
eight-byte zero template before each symbolic `jal26` relocation is applied.
Each independent-renderer hook replaces one four-byte `jal`. Every continuation
and displaced target belongs in a symbolic relocation or a reviewed native-
address constant; do not write final resident payload addresses into the
catalog.

The separate Control Settings injection owns the resident label and assignment
implementation. Its guarded direct-edit patch `e__battle__control_settings_rework`
owns the two construction defaults, the Select-reset table, and three isolated
input changes:

| Purpose | Target/offset | Clean guard | Replacement |
| --- | --- | --- | --- |
| Label action index 7 as Substitution | `na2_elf` `0x4B26AC` | `40466000` (native Guard string pointer) | `abs32` relocation to resident NUL-terminated `Substitution` |
| Own both players' resident defaults | `na2_elf` `0x4C07A0` | `10002000400080000400080001000200` | `10002000400080000100020008000400` |
| Own the BTL bootstrap defaults | `na2_btl` `0x1E4250` | `10002000400080000400080001000200` | `10002000400080000100020008000400` |
| Own the Control Settings Select reset | `na2_elf` `0x4D5350` | `1,0,3,2,4,5,6,7,1` as little-endian `u32` values | `1,0,3,2,7,6,4,5,1` |
| Replace native paired assignment | `na2_elf` `0x287C90` | `8030050001000324` | `j26` relocation to `control_settings_assign_action`; `nop` delay slot |
| Preserve Substitution when opening its selector | `na2_elf` `0x287FBC` | `0000A3AC` (`sw v1,0(a1)`) | `00000000` |
| Include Substitution in the shoulder selector | `na2_elf` `0x2883FC` | `06000324` (`li v1,6`) | `07000324` (`li v1,7`) |
| Allow a fresh Substitution press while Guard remains held | `na2_elf` `0x129720` | `10004228` (`slti v0,v0,0x10`) | `01000224` (`li v0,1`) |
| Route the first substitution history arm from Guard 1 to Substitution | `na2_elf` `0x129740` | `06000524` (`li a1,6`) | `07000524` (`li a1,7`) |
| Stop the second native Guard entry from also producing block | `na2_btl` `0x3C02C` | `0E002286` (`lh v0,0xE(s1)`) | `2D100000` (`move v0,zero`) |

Keeping the direct replacements in `catalog/edits.json` makes their clean
behavior independently auditable. The Control Settings injection independently
owns the resident Substitution label, the replacement assignment helper, and
their symbolic relocations. The gauge injection owns only the two character-
name anchors and the gauge renderer that uses their layout.

The new spend range ends at `0x1299BF`, immediately before the current
character-override hook at `0x1299C0`. When enabled, its shim skips that later
code; when disabled, no new hook exists. Composition tests must assert both
the non-overlap and the two selection outcomes.

### Files and release documentation

The minimal implementation touches these existing ownership points:

| Purpose | Canonical location |
| --- | --- |
| Public setting and descriptions | `features.battle` in `@builder/catalog/catalog.modcat` |
| Guarded input routing edits | `@builder/catalog/edits.json` |
| Hook and payload declarations | `@builder/catalog/injections.json` |
| Default/profile selection | `@builder/configurations/*.json` |
| Config-to-fragment encoder | `@builder/scripts/substitution_gauge.py` and `module_pipeline.py` |
| Gameplay state, independent renderer, and native adapters | `src/battle_logic/substitution_gauge.c` and `substitution_gauge_abi.S` |
| Independent battle-support suppression | `src/qol/battle_support_disabled.c` |
| Control Settings ownership and composition tests | `tests/na228_builder/test_control_settings.py` |
| Gauge builder/state tests | `tests/na228_builder/test_substitution_gauge.py` and focused pure-C/state tests |
| End-user explanation | `@scripts/release/README.md` |

The release README and catalog descriptions must state the observable
consequences: one setting selects Chakra, Gauge, or Free resource behavior;
Gauge uses the resolved normalized `character_overrides.tsv` cost for spending
and the red threshold; and only Gauge draws the independent bar.

## Implementation order

Implement and prove the feature in the following order so each new consumer
has one observable responsibility:

1. **Confirm lifecycle and independent-renderer ownership.** Runtime-confirm the
   established `0x0EF51C` construction wrapper for initial battle construction
   and statically confirm the BTL `0x69380` controller-update cache seam plus
   the parent-gated `0x67434` top-HUD draw seam.
2. **Add pure state logic.** Compile the two-slot state and deterministic update
   functions with no native behavior change.
3. **Add the HP-sample wrapper.** Wrap raw `0x14DB8C` and verify both
   that its displaced native call executes once and that raw `0x14DB80` remains
   the unchanged X-dash hook.
4. **Add the battle-clock wrapper.** Wrap raw `0x0F12B8`; prove the displaced
   countdown call and return value, the `0x05` flag mask, Unlimited-time
   recovery, global ordinal guard, and native 30 FPS progression.
5. **Own Control Settings.** Rename action-map index `7` from the second Guard
   row to Substitution, replace the native paired assignment helper, patch the
   Select-reset table, route both predicate history searches to index `7`,
   remove only its contribution to the logical block bit, retain index `6` as
   the sole Guard and index `5` as Linked Attack, and make every default path
   restore L1 Substitution, R1 Guard, L2 Item Select, and R2 Linked Attack.
6. **Replace the resource gate.** Route only the `fighter + 0x70 >= 1.0`
   sub-block through `can_spend`.
7. **Replace successful spending.** Resolve the character's normalized cost,
   round it once to meter counts, spend that amount on the charged block, and
   skip native chakra/bookkeeping writes without overlapping the current cost
   hook.
8. **Notify every successful transition.** Wrap raw `0x1299F4` so both charged
   and free substitutions restart the delay without double spending.
9. **Enable damage recovery.** Validate normalized HP sampling, healing,
   multi-hit, cinematic, and Practice HP-edit cases.
10. **Draw independent display state.** Mirror the normalized resident meter
    and executable cost into resident fill/cost fractions; wrap BTL `0x69380`
    to retain the native controller update and cache its per-side render source;
    wrap the parent-gated BTL `0x67434` primary HUD draw to render an independent
    textured frame, fill, and marker below the chakra HUD; shift the names down;
    leave the complete native support renderer unchanged and independently
    suppressed by No Support.
11. **Run runtime acceptance.** Validate the textured gauge at full, stock
    boundaries, empty, and partial recovery, then promote only observed results
    to current feature documentation.

## Validation plan

### Pure state tests

Add host-side tests for:

- initialization at `capacity_counts` and a derived debug value of `100`;
- normalized character costs rounded to meter counts, including the current
  tier-derived `20/100`, `25/100`, `30/100`, `35/100`, `40/100`, `45/100`,
  `50/100`, and `55/100` costs;
- repeated variable-cost spends, exact affordability at the boundary, rejection
  one count below it, and a configured zero-cost substitution;
- no spend or timer reset for an unsuccessful event;
- no spend but a full delay reset for each native free transition class;
- both native free transition classes still succeed at zero meter;
- `840`-count delay restart on every successful transition, including a free
  transition, with parity defaults;
- exact delay overshoot carry, including a 15-count delay under two-count
  updates;
- continuous integer recovery and clamp at `capacity_counts`;
- exactly 420 native `context[1] == 2` updates for the default delay and 30
  updates for one stock refill;
- duplicate battle-clock calls with the same system-context `+0x194` ordinal;
- ordinal zero, wraparound, and first-sample validity;
- no pause catch-up when the ordinal advances without a clock callback;
- zero natural advance for timer flags `0x01` and `0x04`, continued recovery
  for Unlimited-time flag `0x02`, and all flag combinations;
- HP sampling and damage awards independent of natural clock advancement;
- normalized partial-bar values between stock boundaries;
- published marker fraction equals the exact rounded cost counts divided by
  capacity, for both players independently;
- HP clamp/Q16 conversion, damage threshold, multiple thresholds in one
  update, and remainder carry;
- no banked damage at full meter;
- healing without a damage award;
- pointer rebind and explicit battle-generation reset; and
- independent Player 1 and Player 2 state.

Builder-facing tests should separately cover the Control Settings/gauge
selection matrix; both owned default tables and their clean guards; `false`,
rejected bare `true` and empty objects, each default mode, partial overrides,
and a complete gauge object; the supported
gauge-enabled/No-Support-disabled and rejected
gauge-enabled/Character-Overrides-disabled combinations;
exact packed configuration words; invalid ranges/steps; all selected hook
guards, all three input direct-edit guards, and both injected character-name-anchor
load guards; the No Support draw
suppression at BTL `0x69398`; clean native support-renderer bytes at `0x68C24`,
`0x68C6C`, `0x68C88`, `0x69110`, and `0x69124`; removal of the retired `0x6745C` hook;
non-overlap with raw `0x1299C0`; and public-catalog projection without patch
IDs.

Prefer testing the state engine as ordinary C logic with native memory access
isolated in thin adapters.

### Static/build validation

- Verify clean SHA-256 identities before deriving guards.
- Verify every hook's exact expected bytes.
- Assert the independently selected Control Settings patch makes action index
  `7` display `Substitution`, restores L1 Substitution / R1 Guard / L2 Item
  Select / R2 Linked Attack for both players, follows later saved remapping,
  and makes index `7` the only ordinary action accepted by both
  substitution history searches; index `6` remains the only action that
  produces the logical Guard bit, and index `5` remains Linked Attack.
- Assert the candidate bypasses the native 16-frame held-Guard rejection before
  the separate action-`7` search without weakening the remaining predicate
  gates.
- Assert the independent renderer's raw `0x69380` hook retains live
  `0x71C810` once and only caches the per-side render source. Assert raw
  `0x67434` retains live `0x71B720` once and draws downstream of the parent
  `+0x54` visibility gate using child layout `+0x00/+0x04/+0x08/+0x0C` and
  primary-sprite alpha. Leave the complete native support renderer clean,
  including raw `0x69184` and its Linked Attack button lookup.
- Assert the substitution feature leaves the complete name-X path and raw
  `0x67F60..0x67F67` Y load untouched. Its sole name-position hook must replace
  only raw `0x67F68..0x67F6F`, preserve the loaded Y and every live renderer
  value, add `11.0` only in Gauge mode, and reproduce the native Y-scale
  multiplication and side-byte load.
- Assert the spend hook occupies raw `0x129984..0x12998B`, after the charged
  transition setup and before every native chakra-spend suppression test. It
  must remain unreachable from the two `param_3 == 0` free routes, must not
  overlap the current raw `0x1299C0` cost hook, and must skip that native spend
  block only when the gauge is selected. Verify Infinite Chakra does not
  suppress gauge spending.
- Assert the HP-sample shim calls its resident consumer and displaced native
  function once while leaving the adjacent X-dash hook unchanged.
- Assert the battle-clock shim sees entry flags, suppresses only mask `0x05`,
  advances at most once per ordinal, and returns the displaced countdown
  helper's exact `v0`.
- Assert No Support replaces only raw `0x69398`, while the substitution renderer
  never writes controller visibility, fill-state, or current-fill fields. Assert
  the independent renderer restores all borrowed sprite command fields before
  the later native support draw when No Support is disabled.
- Validate all code/data placements and relocation targets through the normal
  builder.
- Rebuild twice and compare produced artifacts for determinism.
- Confirm No Support with the gauge disabled remains visually hidden through
  its isolated raw-`0x69398` draw suppression.
- Confirm No Support disabled with the substitution gauge enabled retains the
  native support bar/action and displays the independent substitution bar/action
  at the same time.

### Runtime gameplay matrix

For both P1 and COM/P2, record:

| Scenario | Expected observation |
| --- | --- |
| Control Settings | Separate `Substitution` and `Guard` rows remain remappable; Select restores L1 Substitution, R1 Guard, L2 Item Select, and R2 Linked Attack for both players |
| Guard input only | The remaining Guard action blocks normally and never substitutes |
| Substitution input | A valid new press inside the native reaction window requests substitution; pressing it alone does not block or invoke field support |
| Substitution while blocking | After holding Guard for longer than 16 frames, a fresh Substitution press is still accepted without releasing Guard |
| Shared settings row | Pre-battle and Practice Settings each show one `Substitution: Chakra | Gauge | Free` row and no separate visibility or unlimited row |
| Chakra mode | Gauge hidden; ordinary substitutions retain native chakra eligibility, suppression, subtraction, and bookkeeping |
| Gauge mode | Gauge shown; ordinary substitutions use only the independent resource |
| Free mode | Gauge hidden; ordinary substitutions pass the resource gate and spend neither chakra nor gauge |
| Top-HUD placement | Independent textured bars sit below the chakra bars at mirrored X bases `64/448` without overlapping the shifted names |
| Battle HUD character names | With the gauge selected, both localized names use gauge-owned X `74.0` and Y `55.0`; atlas rectangles and width fitting remain unchanged |
| Gauge button/support decorations | No lower button badge or support-specific decoration is drawn; Control Settings remains the binding reference |
| Native support enabled | With No Support disabled, the native lower support gauge and field-support action remain functional alongside the independent substitution bar/action |
| Linked Attack | Retains its native row and mapping; its field-support effect follows No Support while selected support data remains available to linked Jutsu |
| Start/reset | Top-HUD substitution bar full |
| Successful substitution | Independent bar loses the fighter's resolved `x/100` cost exactly once; chakra unchanged |
| Failed or ineligible input | No meter change |
| Temporary-effect-`9` free substitution | Still succeeds at zero meter; no stock spent; recovery delay restarts |
| Item/status-ID-`9` free substitution | Still succeeds at zero meter; no stock spent; recovery delay restarts |
| Repeated successes | Every use subtracts the same character-resolved cost until the remainder is below that cost |
| Empty-gauge attempt | Native transition rejected; no chakra change |
| Natural recovery | No movement before delay, then continuous textured-bar fill to full |
| Use during recovery | Spend the resolved character cost and restart delay |
| Damage received | Stock award at configured normalized threshold |
| Multi-hit damage | Award from net HP loss, without duplicate counting |
| Jutsu/X-dash | Native chakra spending remains correct |
| Transformation | Gauge preserved |
| New battle load/reset | Gauge full and stale damage cleared |
| Start menu | Natural delay/refill freezes with no catch-up after closing |
| Unlimited battle time | Native battle countdown stays frozen; substitution delay/refill continues |
| Actor hit-stop | Recovery follows the native battle-clock call; HP loss is still sampled exactly once |
| Throw/Ultimate Jutsu and other cinematics | Record clock call, entry flags, ordinal, outer-gate state, and meter; require later-title-equivalent cinematics to freeze before acceptance |

Trace `fighter + 0x70` alongside the new state. The critical proof is that a
successful ordinary substitution changes the new meter by the selected
character's resolved cost while leaving chakra unchanged, that the red marker
matches that exact cost, and that native chakra actions still change `+0x70`
normally. Repeat with at least two characters whose costs differ.

### Visual acceptance

Capture full, empty, partial recovery, and several non-quarter variable-cost
states for both sides. Confirm:

- mirrored placement and fill direction;
- quarter-step recovery increments, variable-cost spending, matching red
  marker placement, and continuous partial recovery;
- native texture, color, animation, and alpha;
- correct visibility through battle entrance, cinematics, pause, and results;
- Practice, ordinary VS, and supported alternate battle HUDs;
- Chakra, Gauge, and Free runtime settings, plus the feature-disabled build; and
- native support enabled and disabled while the substitution gauge is enabled;
- every supported aspect configuration at native 30 FPS.

Runtime visual validation requires the project's selected E2E or user-driven
path. Static tracing cannot prove the final presentation.

## Acceptance boundary and open questions

The architecture is sufficiently constrained to implement, but these items
must be resolved with runtime evidence before the feature is called complete:

- one-call-per-new-battle confirmation for the established battle-graph
  construction seam;
- once-per-update runtime confirmation for the `0x0F12B8` battle-clock hook and
  system-context `+0x194` ordinals at native 30 FPS;
- outer-gate and timer-flag classification for each supported cinematic or
  selective pause-controller state, especially throw and Ultimate Jutsu
  demonstrations;
- whether `0.3125` normalized HP matches the desired later-title damage rate;
- corrected independent-bar slide-off, Ultimate-Jutsu shake, visibility, scale,
  and alpha through ordinary Jutsu, Ultimate Jutsu, and alternate-HUD states
  after consuming the common layout at the BTL `0x67434` top-HUD child seam;
  and
- whether the aggregate textured bar communicates quarter-step recovery and
  variable spending clearly enough with the dynamic cost marker.

These are implementation tasks, not permission to guess. The eligibility and
successful-spend addresses, shared chakra ownership, two-slot state model,
normalized independent-bar publication, and isolated hook ownership are already
strong enough to prevent the common incorrect implementations.

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
