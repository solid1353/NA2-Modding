# Battle

Battle menu defaults and Character Overrides live under `features.defaults`.
`features.defaults.match_setup.character_balance` loads layered TSV data and emits one
resident table shared by its current per-character battle consumers.

## Battle Settings

`features.defaults.battle_settings` defines defaults for every retained native Battle
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
`features.defaults.battle_mechanics`, in config key order; Confirm commits
the complete Battle transaction and closes from the launcher as it does from
every ordinary row. Cancel returns to the launcher; Cancel on the root retains
the native close behavior. Entering or leaving the child page restarts the
selected row's help-text animation. Select restores configured defaults for
every setting on the current page, including rows outside the visible scroll
window, and names that page in the reset notice. Resetting the Battle Settings
root leaves its Battle Mechanics child values intact; each nested page also
resets independently.

Battle and Practice use the same page descriptor, page-selection, logical-row,
`Open <iconSQUARE>` value, normal launcher-label presentation, and scalable
Practice backing renderer. Launcher rows retain their ordinary menu presentation.
A Battle child page loads the native `PRAC.CCS` backing,
draws its orange section header and olive opponent rows, and uses the same
six-row origin, cursor alignment, and scroll indicators as a Practice child
page. Each menu keeps only its controller-specific navigation, table, and
Handicap integration.

The initial Battle pack is applied immediately after the native mode-2 manager
assignment at clean ELF offset `0xEA7B4`. This is separate from the
Practice-only startup/reset path.

The `features.defaults.battle_mechanics` object owns runtime defaults used by Battle
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
shared runtime enum and is restored when its page is reset in either menu;
changing and confirming it in either menu updates the other menu.

`no_contest` keeps the native contest object's creation, updates, and teardown
but never draws it, so neither player sees a meter, prompt, or result. The
native render path also advances the contest timer and result display, so the
contest never resolves: no input changes the outcome, and the jutsu deals its
full record damage. The intro also runs its full countdown instead of ending
early when the Ultimate Jutsu voice line stops. `no_hud` includes that behavior and hides and restores the complete
battle HUD through the same native transition used by ordinary Jutsu. Native
motion, timing, visibility, and restoration apply to the existing HUD and
injected children, including the substitution bar. Both custom values retain
`command` as the underlying native selector value.

In `no_hud`, the native HP damage trail is held through the hidden animation
and the HUD's return slide. Current HP continues updating normally. Once the
bar is back onscreen, its usual countdown and shrink animation resume, showing
the accumulated damage in the existing colored segment. An already-visible
damage trail is retained too. Other Ultimate Jutsu modes keep native behavior.

The comparative no-object behavior is documented in
[NUN6 battle mechanics](nun6/gameplay/battle.md#ultimate-jutsu-contest).

The implementation preserves native contest allocation and updates while
wrapping the resident call at ELF offset `0xF0A40` to skip the contest render
dispatcher in the two custom modes. The presentation's two voice-stream status
reads at BTL offsets `0xB6094` and `0xB62F0` are routed through zero-returning
helpers, so its voice-started latch stays clear. The complete-HUD mode
edge-detects the contest object around the BTL call at offset `0x67030` and
uses native hide/show requests `0x001F1820(-1)` and `0x001F1A20(-1)`.
Before the displaced HUD update, it keeps each HP child's damage-trail delay
at its native `100` while held. Per-side ownership prevents carrying a hold
to a different HP child or fighter. The trail uses cached HP from before the
native update samples the current frame's damage. The native field and timing
evidence is in [Battle HUD](../knowledge/gameplay/session/battle_hud.md#hp-and-name-bindings).

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

`@builder/patches/defaults/battle_mechanics/extra_hit/extra_hit_settings.c`
wraps native eligibility at ELF file
`0x0013B6DC` and the attack initializer at `0x00117F28`. Off and penalty modes
return native rejection instead of jumping past action-exit handling. The
native recovery path therefore remains reachable after a blocked attempt.
See [native Extra Hit control flow](../knowledge/gameplay/combat/extra_hit.md#eligibility-and-action-exit)
for the traced branches and lifecycle boundary.

The object also owns `substitution_input`, `xdash_chakra_cost`, `support`, and
`substitution_resource`. They appear as
`Substitution Input: Default | Hold | 1..15 frames`, `Substitution Resource: Chakra | Gauge | Free`, and
`X-dash Chakra Cost: 0% | 5% | ... | 100%`, plus `Support: Off | Nerfed | Normal | Unlimited`. Each
configuration value is the direct initial and reset value shown by both menus;
both menus snapshot, stage, reset, and commit the same runtime values.

Practice Settings uses the same page-scoped Select reset and notice. Its root
reset leaves Opponent Settings and Battle Mechanics child values intact.

Battle pages render the exact active visible row count. Root pages without
Handicap use up to seven rows; child pages use the shared six-row Practice
viewport. A root page containing the terminal Handicap row uses up to six
logical rows because Handicap retains the original double-height panel. Its
panel, shuriken display, arrows, cursor, label, and value graphics move to the
Handicap row's current visible slot. Scrolling and backing-strip composition
derive from the generated page instead of a fixed root or child row count.

## Catalog-generated menu pages

The generated menu structure is:
`features.defaults.battle_settings` and
`features.defaults.practice_settings` define the two menu
defaults. Config key order within `defaults` controls each page's
rows: value rows, nested pages, and launcher rows mix freely. The
catalog defines types, allowed values, and nested submenu structure. Move
entries within the corresponding config object to reorder them; no catalog
edit is needed. Omitted optional fields retain default rows after
the explicitly configured fields. Container overrides replace values without
moving existing base keys; a complete object-setting replacement supplies its
own nested key order. The base config places Practice's Health, Commands, and
Damage after its Battle Mechanics and Opponent Settings launchers.

The shared builder in `na228_builder/patches/defaults/menu_pages.py` walks catalog
containers and typed object fields. Scalars use registered value handlers.
Objects without `value` form submenus. Objects with `value` use the selector's
literal choices; child objects named after those choices form Square submenus.
A launcher row is a plain `<group>_submenu` switch in a menu's root group,
where `<group>` is a top-level `defaults` group or a native screen such
as Control Settings; it opens that group's shared page or the screen. A nested
group, such as Opponent Settings, is its own submenu row, and turning it off
also disables its settings. `battle_mechanics_submenu: true` exposes that
shared page in either mode, while `false` hides its launcher without disabling
the shared gameplay settings. Launchers appear only on their own menu's root
page, so Mod Settings exposes Battle and Practice defaults without repeating
their Battle Mechanics launchers; its Match Setup launcher comes first in the
base order.

The same traversal discovers Chakra, Gauge, and Custom Items pages. Item
toggles, each `"off"` or `"on"`, sit directly under
`battle_mechanics.items.custom`; the base config
places `availability` first. When availability is None, the individual item
toggles are greyed out and cannot be changed in Mod, Battle, or Practice
Settings. Changing availability restores editing without resetting those
choices; the dependency follows the staged menu value immediately.
`menu_options.py` owns value presentation and runtime bindings, independently
of page topology. Native row handlers, rendering, and transaction behavior
remain shared with their existing consumers.

In both Battle and Practice Settings, Back from any submenu returns to its
parent page with the option-switch sound (`0x35`), matching submenu opening.
Back at the root closes without applying and uses the cancel sound (`0x33`).

## Control Settings

Control bindings, including Item Select L and R, are documented in
[Controls](controls.md).

## Extended Items

`features.defaults.match_setup.extended_items` accepts
`"off"` or `"on"`; the base and release configurations use `"on"`. Its
`Extended Items: Off | On` row appears only on the Mod Settings Match Setup
page, so it cannot change during a battle or a Practice session. Save appendix
field `0005` stores it.

When off, every inventory routine runs the native three-slot code, and the
wheel origin, item alignment, selection-badge offsets, and count placement stay
native. When on, each fighter holds five item slots:

- pickups stack up to nine per slot and fill an empty inventory slot. Each new
  item enters the cyclic wheel order at the next alternating arm;
- used or lost items leave inventory gaps while the surviving items retain
  their cyclic order;
- the HUD wheel keeps the selection in the middle and fills the remaining
  positions in occupied-item order along a mirrored sweep, with empty frames
  for unused positions;
- Practice captures and restores every configured slot.

CPU item use keeps the native rule that only the selected item and the items
one step away are reachable.

The panel constructor latches the toggle before it seeds starting items,
so a changed value applies from the next battle. Native inventory
behavior, addresses, and the HUD formula are documented in
[Battle item inventory](../knowledge/gameplay/projectiles_and_items/battle_item_inventory.md).

### Implementation

`@builder/patches/defaults/match_setup/extended_items/extended_items.c`
owns the setting state, the latched toggle, the added slots, and the five-slot
routines. The panel keeps its three native slot objects as slots
`0..2`; slots `3` and `4` are two resident 8-byte slots per side with the
native layout. A per-side permutation of the five slot indexes owns the cyclic
order without moving item codes or counts between physical slots. Selection,
item relations, and automatic reselection walk that same order, skipping empty
slots. New items enter at forward rank `(occupied_count + 2) / 2` from the
selection, so pickups fill inner left, inner right, outer left, then outer
right for P1, mirrored for P2, while existing items keep their positions.
The Practice capture stores items in the alternating insertion sequence, so
restore reproduces their cyclic order. It uses a resident two-side, five-entry
cache and clears the native cache with it.

`extended_items_abi.S` holds two kinds of guarded BTL hooks, all declared under
`defaults.match_setup.extended_items` in
`@builder/patches/defaults/defaults.json`:

- Entry hooks on every slot routine test the latched toggle. When off they
  replay the displaced native instructions and continue into the native routine;
  when on they tail-call the C routine with the native arguments.
- Site hooks replace the native three-slot loops and selected-slot loads inside
  activation, the panel update, and the selection-indicator choice. They call
  the same C helpers, which use only the native slots when the latched toggle is
  off.

The five-slot wheel draw retains the native background, foreground, empty-frame,
and count calls. Occupied items use NUN4's spacing, height interpolation, scale,
and edge-opacity formula with NA2's item sprites.
Five slots use positions `-2..2` around the selection. The next `count / 2`
occupied items take positive positions, and the remaining items take negative
positions in the same cyclic order. This keeps the forward neighbor on P1's
left and the reverse neighbor on its right; P2 mirrors those directions.
With two items, the one other item is shared by both selection directions and
appears on P1's left or P2's right. Empty inventory slots are skipped:

- positions `1` and `2` rise at offsets `(42, -9)` and `(60, -25)` from the
  selection; positions `-1` and `-2` extend below it at `(43, 8)` and `(70, 7)`.
  Positive positions are on P1's left and P2's right. These are the empty-frame
  points; their placement and scale remain unchanged;
- occupied items use horizontal distances `35.2` and `64`. Their height is
  interpolated by horizontal distance through the NUN4 layout points, including
  P2's `-50` far rising point. Item scale is `1.2 - 0.6|x| / 96`. Opacity is
  full inside the count-dependent inner boundary and falls linearly to zero at
  the outer boundary. Distances up to `0.5` past the inner boundary count as
  inside, because NUN4's `35` boundaries round the `35.2` step; resting items
  one step away therefore stay fully opaque. The NUN4 fade bands are mirrored for P1's even occupied
  counts to preserve the alternating population's extra item on its forward
  arm. A one-item cycle fades to zero at one step on either side;
- selection animation blends positions by physical slot identity in cyclic
  order. Signed steps are captured before the native offset is clamped. Each
  new press restarts the blend from its current positions, retaining complete
  turns and both fading wrap copies, including with two occupied items. The
  blend advances by `0.2` per panel update independently of the native offset.
  Removal also blends the occupied span and its fade bands so surviving items
  keep their preceding positions and fades while the shorter cycle takes shape.
  The auxiliary NA2 model draw, which adds the special item's highlight, has no
  opacity input and runs only for fully opaque item copies, so it cannot cover
  a fading sprite with an opaque model. Like retail, it appears on the special
  item in any resting position, not only when selected.

When on, a constructor-tail hook moves the wheel origin from the native
`x = 66` and `446` to `77.4` and `434.6`, mirrored in the 512-unit HUD space.
It moves the Item Select L badge from its native `(-38, 16)` to `(-50, 30)`
for both players; the Item Select R badge mirrors it. The draw raises the
entire wheel, including the selected item and frame, side items, empty
frames, and quantity indicator and its frame, by `6` HUD units. The badges
retain their positions; the count stays `27` units below the wheel center.
The sweep uses NUN4's recorded layout points, documented in
[Battle item inventory](../knowledge/gameplay/projectiles_and_items/item_wheels_nun3_nun4.md#nun4-item-wheel).

| Hook kind | BTL file offsets |
| --- | --- |
| Constructor latch, wheel origin, and badge position | `0x5B840`, `0x5BBBC` |
| Entry: full, selected count, find, code at step, selected code, count copy, room | `0x5BD80`, `0x5BDB0`, `0x5BE40`, `0x5BE90`, `0x5BEE0`, `0x5BF70`, `0x5BFF0` |
| Entry: add, consume by code, consume selected, clear | `0x5C140`, `0x5C3D0`, `0x5C570`, `0x5C6C0` |
| Entry: occupied and empty steps, cache build and restore | `0x5C7D0`, `0x5C950`, `0x5CAF0`, `0x5CC00` |
| Entry: count, relation, category, use code, two occupied, cache clear | `0x5CD70`, `0x5CDF0`, `0x5CF20`, `0x5D2C0`, `0x5DBC0`, `0x5B2E0` |
| Site: activation count and selected slot | `0x5D4D8`, `0x5D6FC` |
| Site: panel update blend/count and selected code | `0x5E4A0`, `0x5E840` |
| Entry: wheel draw | `0x5DF50` |
| Site: selection indicator | `0x5E8D4` |

## Simple Display

`features.defaults.mod_settings.simple_display` selects whether battles start with
the native Simple Display setting `"off"` or `"on"`. The base configuration
selects `"off"`. The setting owns the guarded main-ELF initializer
instruction at offset `0xE7BAC`.

The pause-menu Simple Display selector opens on the active value. Its BTL hook
at file offset `0x1C3A04` reads the shared value through the native getter and
selects On for enabled or Off for disabled, then resumes the native initializer.
The native getter and setter entries at ELF offsets `0xF6EB0` and `0xF6E80`
delegate to the shared [Mod Settings](mod_settings.md) accessors. Confirmation
therefore commits the same value used by the main menu and save appendix;
cancellation retains the current value. The hook writes the selected row, not
the list's automatic-completion mode: a nonzero mode with no delay completes
the window immediately. The native menu and getter are documented in
[Simple Display selection](../knowledge/gameplay/session/pause_and_replay.md#simple-display-selection).

## X-dash chakra cost

`features.defaults.battle_mechanics.xdash_chakra_cost` is expressed as normalized
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
in [X-dash knowledge](../knowledge/gameplay/combat/xdash.md).

## Substitution

`features.defaults.battle_mechanics` owns two substitution settings:

- `substitution_input` accepts `"default" | "hold" | 1..15` and appears in the
  menus as Default, Hold, and 1 to 15 frames. `"default"` uses vanilla logic:
  per-attack timing, including its random checks, and a fresh press. A number
  `N` accepts a fresh press on the hit's frame or the `N - 1` frames before it,
  without random checks. `"hold"` accepts the Substitution button whenever it
  is down when the hit lands, also without random checks. Only Hold accepts a
  held button.
- `substitution_resource` installs one shared `Substitution Resource: Chakra | Gauge | Free` setting in
  both the pre-battle and Practice menus. Its required `value` field selects
  the value used initially and by each menu's reset action. Optional object
  fields configure recovery delay, refill time per stock, damage recovery, and
  damage for a full refill in 5% steps.

The base configuration uses `"hold"` and `{"value": "gauge"}`. `Chakra`
uses the configurable minimum described below and retains native suppression,
spending, and bookkeeping; `Gauge` uses the independent 100-point resource and
displays its HUD; `Free`
uses no resource and hides the gauge. Both menus stage and commit the same
runtime enum rather than separate visibility and unlimited flags. Substitution
Input changes only the timing policy inside the native eligibility predicate. Numeric values and Hold bypass attack-authored random and clamped
timing; `Default` resumes those native branches with the original attack timing
value. The hook rejoins the held-Guard, response-state, resource,
attack-flag, history-search, and transition gates. The Substitution button's
check, described in [Controls](controls.md#battle-input), comes before the
held-Guard limit, so it also works while Guard is held.

The Substitution Input value and selected resource mode are independent runtime
values. Runtime confirmation of the Substitution Input selector remains pending.

## Minimum Chakra

Runtime validation of the Minimum Chakra behavior remains outstanding:
Square on `Substitution Resource: Chakra` opens Chakra Settings in Battle and Practice.
Its `Minimum Chakra` row accepts `Match Cost`, then `5%..100%` in steps of `5`.
The config field is
`features.defaults.battle_mechanics.substitution_resource.chakra.minimum_chakra`:
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
empty. The selected profile's `<name>.character_overrides.tsv` in that directory
layers nonempty cells over it. Release packaging uses the base character values.
Numeric character IDs and names are validated against
`@resources/character_data.tsv`. `base_id` records form relationships as
human-readable configuration metadata. `tier` records the balancing tier and
is serialized as fixed-width table metadata for
`features.defaults.match_setup.balance_overlay`. Empty cells inherit, while zero
remains an explicit value. Tier labels use at most four ASCII characters. Rows
retain the base TSV order so forms can stay directly below their base characters.
Save the file as UTF-8 TSV and run the normal build for that profile.

All substitution costs are percentage points on the inclusive `0..100` scale.
The `base` row is a literal cost and the explicitly positive, signed `step` row
is the increment between tiers. An empty character cost is inferred from its
tier as `base + tier_index * step`, using D `0`, C `1`, B `2`, A `3`, S `4`,
S+ `5`, S++ `6`, and S+++ `7`. An unsigned character value such as `30` is a
literal per-character override. An explicitly signed character value such as
`+5` or `-5` adjusts that character's tier-derived cost. Profile layers inherit
the character cell and its literal-or-signed mode when empty. `0` is a literal
zero-cost override; `+0.0` is a zero adjustment. The builder rejects unknown IDs,
invalid base IDs, mismatched names, duplicate rows, malformed columns, invalid
metadata, non-finite numbers, negative literal values, and resolved costs outside
`0..100` before composition. Other numeric fields remain nonnegative literal
float32 values.

For example, these rows set base `20` and step `+5`. Naruto's empty cost is
inferred from tier S as `40/100`; Sakura's unsigned `25` is a literal
per-character override:

```tsv
id	base_id	character	tier	substitution_cost	hp	damage_multiplier	health_recovery_multiplier	chakra_recovery_multiplier
base				20
step				+5
57		Naruto Uzumaki	S
58		Sakura Haruno	A	25
```

The builder serializes four-byte tier labels, presence and delta flags, and
float32 values into a dense ID-indexed resident table. The
substitution hook at ELF offset `0x1299C0` maps the incoming fighter to its
player slot and reads that slot's match-start character ID. A directly selected
form therefore uses its form row, while a base character transformed during
the match keeps its base row.

`features.defaults.match_setup.balance_overlay` independently reads the same
complete table. It always draws `TIER` in separate left and right top-screen
blocks. It draws the resolved `SUB x%` value only when
`features.defaults.match_setup.character_balance` is `"overrides"`, omitting trailing decimal
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

`features.defaults.battle_mechanics.support` selects the initial and reset value of
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

The feature replaces the
[native support block](../knowledge/gameplay/session/battle_hud.md#support-gauge)
with a slim bar under the item wheel:

- The bar is `54` by `6` HUD units with a `1`-unit black edge, centered on the
  item panel's wheel origin and `31` units below it, between the item count and
  the bottom of the item-select badges. Its edge, backing, and fill have
  semicircular ends, drawn as six nested full-span strips whose heights follow
  a circle; overlapping strips leave no pixel gaps between quads.
  It follows the wheel's Extended Items
  position and the panel slide, and draws only when the native support draw
  would.
- A dark backing holds the fill, tinted with the native palette entry for the
  gauge state. P2's fill grows toward the screen center.
- While support is ready, the native icon's readiness pulse brightens the
  whole fill by blending its tint toward white.
  Normal marks its half-gauge threshold with a light `1`-unit line inside a black
  pin that extends `1` unit beyond the bar's edge on every side.
- The icon, button badge, and textured frame are not drawn. Each strip is the
  native fill column `0x00604D30` stretched and tinted. Each layer is flushed
  separately, because a sprite drops queued quads past its limit until a flush.
- Off draws nothing.

`@builder/patches/defaults/battle_mechanics/support/battle_support.c`
owns the mode routing. The guarded hooks replace
the fighter's support-request and gauge-update calls, the active-drain call,
the HUD readiness predicate, and the support-gauge draw.
The separate Practice key-`3` refill block is bypassed, so its stored native
bit cannot override the shared mode. General Settings no longer exposes
`linked_attack`; the opponent's `linked_attack` still controls dummy behavior.

Selected support data and linked Jutsu retain their existing behavior.

The setting is independent of
`features.defaults.match_setup.support_selection`. Either feature may be enabled
without the other.
