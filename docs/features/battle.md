# Battle

Battle menu defaults and Character Overrides live under `features.settings`.
`features.settings.character_overrides` loads layered TSV data and emits one
resident table shared by its current per-character battle consumers.

## Battle Settings

`features.settings.ingame.battle_mode` defines defaults for every retained native Battle
row:

| Field | Values |
| --- | --- |
| `time` | `10`, `20`, `30`, `40`, `50`, `60`, `70`, `80`, `90`, `99`, `unlimited` |
| `difficulty` | `simple`, `easy`, `normal`, `hard`, `insane`, `ultimate` |
| `handicap` | integer `0..10` for Player 1; Player 2 receives `10 - handicap` |

The complete base configuration supplies every field. These values initialize
the Battle manager and replace the corresponding local values when Return to
Defaults is used. All three fields are required. Chakra, Items, and Ultimate Jutsu are
injected battle mechanics shared by both menus instead of native Battle fields, so
Battle and Practice cannot configure conflicting defaults for them.

The Handicap number is also its native menu index: `3` displays `3-7`, and
`10` displays `10-0`.

The base config places `Battle Mechanics` first, followed by Time, Difficulty,
and Handicap. Moving those config entries changes their visible order.
Square on the launcher opens a child page containing every enabled leaf under
`features.settings.ingame.battle_mechanics`, in config key order; Confirm commits
the complete Battle transaction and closes from the launcher as it does from
every ordinary row. Cancel returns to the launcher; Cancel on the root retains
the native close behavior. Entering or leaving the child page restarts the
selected row's help-text animation.

Battle and Practice use the same page descriptor, page-selection, logical-row,
`Open <iconSQUARE>` value, orange launcher-label renderer, and scalable Practice
backing renderer. Launcher rows retain their ordinary menu geometry and recolor
only the label panel. A Battle child page loads the native `PRAC.CCS` backing,
draws its orange section header and olive opponent rows, and uses the same
six-row origin, cursor alignment, and scroll indicators as a Practice child
page. Each menu keeps only its controller-specific navigation, table, and
Handicap integration.

The initial Battle pack is applied immediately after the native mode-2 manager
assignment at clean ELF offset `0xEA7B4`. This is separate from the
Practice-only startup/reset path.

The `features.settings.ingame.battle_mechanics` object owns runtime defaults used by Battle
Settings and Practice Settings. The base config places `chakra` first; it accepts `normal`,
`unlimited`, or a decimal regeneration rate from `0.1` through `10.0` in steps
of `0.1`. `normal` preserves native spending and gain; `unlimited` restores both
active fighters to the native `15.0` maximum after every fighter update; and a
numeric value regenerates that percentage of the full gauge per second, capped
at `15.0`. The menus display numeric values as `Regen N.N%/s`. At the native
30 Hz battle cadence, the base value `0.5` adds `0.0025` per update, regenerates
`5.0` chakra in about 66.7 seconds, and fills the gauge in 200 seconds. Both
native menus keep their underlying Chakra key at Normal so only this shared
runtime setting owns the behavior.

Its `ultimate_jutsu` selector accepts the six native values
`no_use`, `random`, `command`, `timing`, `turn`, and `combo`, followed by the
custom values `no_contest` and `no_hud`. The configured value initializes the
shared runtime enum and is restored by either menu's reset action; changing and
confirming it in either menu updates the other menu.

`no_contest` blocks both players' contest inputs and suppresses the contest
meter, prompts, and result messages while retaining the native contest
lifecycle. `no_hud` includes that behavior and hides and restores the complete
battle HUD through the same native transition used by ordinary Jutsu. Native
motion, timing, visibility, and restoration apply to the existing HUD and
injected children, including the substitution bar. Both custom values retain
`command` as the underlying native selector value.

The comparative no-object behavior is documented in
[NUN6 battle mechanics](nun6/gameplay/battle.md#ultimate-jutsu-contest).

The implementation preserves native contest allocation and updates while
replacing the resident call at ELF offset `0xF0A40` with a NOP to skip the
common contest renderer. The input calls at BTL offsets `0xB6094` and
`0xB62F0` are routed through zero-returning helpers. The complete-HUD mode
edge-detects the contest object around the BTL call at offset `0x67030` and
uses native hide/show requests `0x001F1820(-1)` and `0x001F1A20(-1)`.
Runtime testing confirmed hidden contest presentation, blocked input for both
players, restored post-Ultimate-Jutsu awakening, and native HUD restoration.

The same object accepts `shadowblur: "off" | "on"`. Its `Shadowblur Extra Hit`
row appears in both menus. The gate preserves the native predicate result but
skips its side effects while `Off`.

Runtime validation of Extra Hit behavior remains outstanding:
`extra_hit` accepts `"off"`, `"on"`, or integers `-100..-5` in steps of `5`.
Both menus display `Off`, `On`, `-5% Chakra`, `-10% Chakra`, through
`-100% Chakra`, in that order. The base value remains `"off"`. Confirm and
Return to Defaults use the shared runtime value.

Off blocks Extra Hit without charging chakra. On retains native behavior.
Negative values block Extra Hit and charge the initiating fighter that
percentage of the full `15.0` chakra capacity when the native eligibility
check would accept the attempt. Remaining chakra is clamped to zero; low
chakra does not exempt the attempt from the penalty. Repeated checks during
one source attack cannot charge again; entering a new native attack resets
that fighter's charge latch. The shared Unlimited Chakra mode still restores
chakra after the fighter update.

`src/battle_logic/extra_hit_settings.c` wraps native eligibility at ELF file
`0x0013B6DC` and the attack initializer at `0x00117F28`. Off and penalty modes
return native rejection instead of jumping past action-exit handling. The
native recovery path therefore remains reachable after a blocked attempt.
See [native Extra Hit control flow](../knowledge/gameplay/hit_response.md#extra-hit-eligibility-and-action-exit)
for the traced branches and lifecycle boundary.

The object also owns `sub_active_frames`, `xdash_chakra_cost`, `support`, and
`substitution`. They appear as
`Sub Active Frames: Default | 1..15`, `Substitution: Chakra | Gauge | Free`, and
`X-dash Chakra Cost: 0% | 5% | ... | 100%`, plus `Support: Off | Nerfed | Normal | Unlimited`. Each
configuration value is the direct initial and reset value shown by both menus;
both menus snapshot, stage, reset, and commit the same runtime values.

Battle pages render the exact active visible row count. Root pages without
Handicap use up to seven rows; child pages use the shared six-row Practice
viewport. A root page containing the terminal Handicap row uses up to six
logical rows because Handicap retains the original double-height panel. Its
panel, shuriken display, arrows, cursor, label, and value graphics move to the
Handicap row's current visible slot. Scrolling and backing-strip composition
derive from the generated page instead of a fixed root or child row count.

## Catalog-generated menu pages

The generated menu structure is:
`features.settings.ingame.battle_mode` and `practice_mode` define the two menu
roots. Config key order controls visible row order throughout these roots and
their nested and shared pages. The catalog defines types, allowed values, and
submenu structure. Move entries within a config object to reorder its page;
no catalog edit is needed. Omitted optional fields retain default rows after
the explicitly configured fields. Container overrides replace values without
moving existing base keys; a complete object-setting replacement supplies its
own nested key order. The base config places Practice's Health, Commands, and
Damage after its Battle Mechanics and Opponent Settings launchers.

The shared builder in `na228_builder/scripts/menu_pages.py` walks catalog
containers and typed object fields. Scalars use registered value handlers.
Objects without `value` form submenus. Objects with `value` use the selector's
literal choices; child objects named after those choices form Square submenus.
Bare launcher settings resolve their name only against shared definitions
directly under `ingame`; a missing target or a reference cycle is an error.
`battle_mechanics: true` exposes that shared page in either mode, while `false`
hides its launcher without disabling the shared gameplay settings.

The same traversal discovers Chakra, Gauge, and Custom Items pages. Item
toggles sit directly under `battle_mechanics.items.custom`; the base config
places `availability` first.
`menu_options.py` owns value presentation and runtime bindings, independently
of page topology. Native row handlers, rendering, and transaction behavior
remain shared with their existing consumers.

## Control Settings

`features.settings.new_controls` owns the Control Settings action split and
default shoulder-button layout independently of the substitution gauge. Action
index `6` remains Guard and is the sole source of the logical block bit. Action
index `7` is labelled Substitution, is searched by both native substitution
history arms, and does not contribute to block. A fresh Substitution press is
therefore accepted while Guard remains held without making Guard request a
substitution.

The setting owns both clean default-binding tables. Their shared action-order
map defaults both players to L1 Substitution, R1 Guard, L2 Item Select, and R2
Linked Attack. An owned assignment helper replaces the native editor's hard-
coded coupling of the two Guard rows. Changing any action performs one ordinary
permutation swap, so Guard, Substitution, Item Select, and Linked Attack remain
separate actions. Saved per-player maps retain the resulting assignments. The
Select action uses an independently guarded reset table and restores the same
owned layout.

## Simple Display

`features.settings.simple_display` selects whether battles start with
the native Simple Display setting `"off"` or `"on"`. The base configuration
selects `"off"`. The setting owns only the guarded main-ELF initializer
instruction at offset `0xE7BAC`.

## X-dash chakra cost

`features.settings.ingame.battle_mechanics.xdash_chakra_cost` is expressed as normalized
percentage points on the inclusive `0..100` scale in 5-point steps. The menu
therefore exposes `0%`, `5%`, through `100%`. The runtime consumer converts the
selected `x/100` value to NA2's native 15-point chakra gauge as `x * 15 / 100`.
The base value `5` spends `0.75` native chakra. `0` is free and `100` consumes a
full native chakra gauge. The selector does not add an affordability gate.

The resident hook replaces the call to `FUN_0020E280(fighter)` at boot-ELF
runtime `0x0024DA80` (file offset `0x14DB80`). It checks the entering state,
preserves that native call, and deducts only for major action `8`, action index
`0x13`, action phase `1`, and internal X-dash substate `2`. A two-side latch
blocks repeat deductions while the movement state persists and resets outside
it. This boundary follows the final cancellation opportunity and precedes the
phase-2 hit transition.

The implementation clamps the resulting chakra to zero and does not add an
affordability gate; native action-record type `2` bypasses the ordinary cost
check. Runtime replay confirmed one deduction for a completed dash and none for
either early or final-frame cancellation. The native state-machine evidence is
in [X-dash knowledge](../knowledge/gameplay/xdash.md).

## Substitution

`features.settings.ingame.battle_mechanics` owns two substitution settings:

- `sub_active_frames` accepts `"default" | 1..15`. `"default"` preserves vanilla
  per-attack timing, including its random checks. A number selects the total
  input-history window: `1` checks only the current frame, and `N` checks it
  plus `N - 1` earlier frames. The maximum total window is 15 frames.
- `substitution` installs one shared `Substitution: Chakra | Gauge | Free` setting in
  both the pre-battle and Practice menus. Its required `value` field selects
  the value used initially and by each menu's reset action. Optional object
  fields configure recovery delay, refill time per stock, damage recovery, and
  damage percentage per stock.

The base configuration uses `5` and `{"value": "gauge"}`. `Chakra`
uses the configurable minimum described below and retains native suppression,
spending, and bookkeeping; `Gauge` uses the independent 100-point resource and
displays its HUD; `Free`
uses no resource and hides the gauge. Both menus stage and commit the same
runtime enum rather than separate visibility and unlimited flags. The active-
frames setting changes only the timing policy inside the native eligibility
predicate. Numeric values bypass attack-authored random and clamped timing;
`Default` resumes those native branches with the original attack timing value.
The hook rejoins the held-Guard, response-state, resource,
attack-flag, history-search, and transition gates.

The active-frame limit and selected resource mode are independent runtime
values. Runtime confirmation of the active-frame selector remains pending.

## Minimum Chakra

Runtime validation of the Minimum Chakra behavior remains outstanding:
Square on `Substitution: Chakra` opens Chakra Settings in Battle and Practice.
Its `Minimum Chakra` row accepts `Match Cost`, then `5%..100%` in steps of `5`.
The config field is
`features.settings.ingame.battle_mechanics.substitution.chakra.minimum_chakra`:
`"match_cost"` (the default), or integers `5..100` in steps of `5`.

Match Cost invokes the same per-fighter cost resolver used by spending when
Character Overrides is enabled. With overrides disabled, it requires the
native `1.0` out of `15.0` chakra. Numeric values independently set the required
percentage of the full gauge; they do not change the amount deducted. Thus a
minimum below the actual cost permits substitution and the native spend clamps
remaining chakra to zero. A zero actual cost also has a zero Match Cost minimum.

The generated resource configuration links override resolvers only when
Character Overrides is enabled. Otherwise Chakra uses native cost, and Gauge
uses its normalized `1/15` equivalent. The existing menu transaction handles
the minimum alongside the other shared substitution options.

## Substitution cost

`configurations/overrides/base.character_overrides.tsv` supplies the required
`base` and `step` metadata rows plus the shared character rows. `base` and
`step` are not characters: their `base_id`, `character`, and `tier` cells are
empty. The selected profile's matching TSV in that directory layers nonempty
cells over it. Numeric character IDs and names are validated against
`@resources/character_data.tsv`. `base_id` records form relationships as
human-readable configuration metadata. `tier` records the balancing tier and
is serialized as fixed-width table metadata for
`features.character_select.balance_overlay`. Empty cells inherit, while zero
remains an explicit value.

All substitution costs are percentage points on the inclusive `0..100` scale.
The `base` row is a literal cost and the explicitly positive, signed `step` row
is the increment between tiers. An empty character cost is inferred from its
tier as `base + tier_index * step`, using D `0`, C `1`, B `2`, A `3`, S `4`,
S+ `5`, S++ `6`, and S+++ `7`. An unsigned character value such as `30` is a
literal per-character override. An explicitly signed character value such as
`+5` or `-5` adjusts that character's tier-derived cost. Profile layers inherit
the character cell and its literal-or-signed mode when empty. The builder
rejects an invalid metadata row or resolved result outside `0..100`. Other
numeric fields remain nonnegative literal float32 values.

The builder serializes four-byte tier labels, presence and delta flags, and
float32 values into a dense ID-indexed resident table. The
substitution hook at ELF offset `0x1299C0` maps the incoming fighter to its
player slot and reads that slot's match-start character ID. A directly selected
form therefore uses its form row, while a base character transformed during
the match keeps its base row.

`features.character_select.balance_overlay` independently reads the same
complete table. It always draws `TIER` in separate left and right top-screen
blocks. It draws the resolved `SUB x%` value only when
`features.settings.character_overrides` is enabled, omitting trailing decimal
zeroes. It never draws player labels or numeric IDs.

Every runtime consumer uses that normalized value. With the runtime mode set to
`Chakra`, the battle hook converts
`x/100` to the native 15-point chakra resource as `x * 15 / 100`. In `Gauge`
mode, the same value is rounded once to `capacity_counts * x / 100`;
eligibility, spending, and the independent top-HUD textured bar's red threshold
all use that executable integer cost. `Free` bypasses both resource spends. The
current TSV uses base `20` and step `+5`, so its empty character cost cells
resolve from their tiers as D `20`, C `25`, B `30`, A `35`, S `40`, S+ `45`,
S++ `50`, and S+++ `55`, all over `100`.

`tier` is consumed whenever the Character Select overlay is enabled.
`substitution_cost` is consumed by the overlay only when character overrides
are enabled, and by the native chakra-cost and substitution-gauge battle hooks.
With Character Overrides disabled, substitution uses the native cost rather
than the configured override table.
`support` independently selects field-support behavior and its lower gauge;
see [Battle support](#battle-support).
`hp`, damage, and recovery columns have no runtime consumers.

## Battle support

`features.settings.ingame.battle_mechanics.support` selects the initial and reset value of
the shared `Support: Off | Nerfed | Normal | Unlimited` row in Battle and
Practice Battle Mechanics. The base configuration remains `"off"`.

Runtime validation of Battle support behavior remains outstanding:

| Value | Field support |
| --- | --- |
| `"off"` | Disables support-button calls and hides the lower support gauge. |
| `"nerfed"` | Requires a full gauge for one summon and starts its attack automatically. Another request waits until the active support object is gone and the gauge is full again. |
| `"normal"` | Native NA2 support requests, half-gauge entry threshold, recharge, and active drain. |
| `"unlimited"` | Native support controls with the gauge restored to full during each eligible fighter update, in Battle and Practice. |

Nerfed reuses the native summon setup and the class-specific state-`2`
attack transition. It skips the intermediate waiting/approach state instead
of requiring a second button press. Its entry threshold and active drain
follow the [NUN6 support reference](nun6/gameplay/battle.md#support).
The first active drain caps the gauge at `0.099609375`, then subtracts
the float encoded by `0x3B839930` on later active updates until zero.
NA2's recharge rate is retained. The native object owns attack completion
and teardown. This is an NA2 implementation of the requested immediate attack;
the linked comparison does not establish an identical summon-to-attack bypass.

The native gauge's readiness test uses the selected mode's threshold. The
half-gauge marker appears only in Normal; Nerfed and Unlimited hide it.
No replacement palette is used.

`src/qol/battle_support.c` owns the mode routing. The guarded hooks replace
the fighter's support-request and gauge-update calls, the active-drain call,
the HUD readiness predicate, the marker draw, and the support-gauge draw.
The separate Practice key-`3` refill block is bypassed, so its stored native
bit cannot override the shared mode. General Settings no longer exposes
`linked_attack`; the opponent's `linked_attack` still controls dummy behavior.

Selected support data and linked Jutsu retain their existing behavior.

The setting is independent of
`features.character_select.support_selection`. Either feature may be enabled
without the other.
