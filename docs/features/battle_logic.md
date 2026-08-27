# Battle logic

The `battle_logic` catalog subtree selects guarded definitions through patch
IDs. Its character-override node loads layered TSV data and emits one resident
table shared by current and future per-character battle hooks.

## Ultimate Jutsu

`features.battle_logic.ultimate_jutsu` owns two independent settings:

- `contest_disabled` blocks both players' contest inputs and suppresses the
  contest meter, prompts, and result messages while retaining the native
  contest lifecycle.
- `hud_hidden` hides and restores the complete battle HUD through the same
  native transition used by ordinary Jutsu. Native motion, timing, visibility,
  and restoration apply to the existing HUD and injected children, including
  the substitution bar.

Either setting can be enabled without the other. The base configuration enables
both.

## Substitution cost

`configurations/overrides/base.character_overrides.tsv` supplies the shared
base and character rows. The selected profile's matching TSV in that directory
layers nonempty cells over it. Character IDs and names are validated against
`@resources/character_data.tsv`. `base_id` records form relationships as
human-readable configuration metadata. `tier` records the balancing tier and
is serialized as fixed-width table metadata for the Character Select balance
overlay. Empty cells inherit, while zero remains an explicit value.

The `base` row's `substitution_cost` is a literal value. In a character row, an
unsigned value such as `3` is also literal, while an explicitly signed value
such as `+0.5` or `-0.5` is a delta from the resolved base cost. Profile layers
inherit both the number and its literal-or-delta mode when the cell is empty.
Other numeric fields remain nonnegative literal float32 values.

The builder serializes four-byte tier labels, presence and delta flags, and
float32 values into a dense ID-indexed resident table. The
substitution hook at ELF offset `0x1299C0` maps the incoming fighter to its
player slot and reads that slot's match-start character ID. A directly selected
form therefore uses its form row, while a base character transformed during
the match keeps its base row. The shared base
`character_select_balance_overlay` setting reads the same table and draws
`TIER` and resolved `SUB` values in separate left and right top-screen blocks
without player labels or numeric IDs. The clean instruction at `0x1299BC` is
no longer edited. The current TSV selects base cost `2.5` and tier deltas from
D `+0.0` through S+++ `+3.5` in `0.5` steps.

`tier` is consumed by the Character Select overlay, and `substitution_cost` is
consumed by both the overlay and the battle hook. `hp`, damage, and recovery
columns are present for later hooks and currently have no runtime consumers.

## Combo damage scaling design

Status: investigated and validated with a transient two-site scaling hook for
one normal string, but not implemented in the builder. The native combo and
damage evidence is
canonical in
[`battle.md`](../knowledge/gameplay/battle.md#combo-hit-state-and-damage-path).
No current catalog node, payload fragment, hook, or runtime consumer changes
damage by combo hit index.

### Recommended configuration

Use one typed object under `features.battle_logic`, rather than a marker list or
per-move input sequence:

```json
"combo_damage_scaling": {
  "decay_per_additional_hit": 0.10,
  "minimum_multiplier": 0.30
}
```

Both values are finite `float32` numbers constrained to `[0, 1]`. The feature
can use the catalog's existing typed-object setting support, conceptually
`setting<{ decay_per_additional_hit: decimal & 0..1,
minimum_multiplier: decimal & 0..1 }>`. Setting the node to `false` disables
the injection, consistent with other typed catalog settings. The multiplier
for one-based hit index `h` is:

```text
combo_multiplier(h) = max(
    minimum_multiplier,
    1.0 - decay_per_additional_hit * (max(h, 1) - 1)
)
```

The recommended starting values retain 100% damage on hit 1, then 90%, 80%,
70%, 60%, 50%, 40%, and 30% on hits 2 through 8, with 30% thereafter. These
are initial balance values, not behavior inferred from the native game. A decay
of zero makes every hit 100%; a minimum of one also makes the feature a
no-op. The builder should reject non-finite values and should encode the two
values once as a read-only, four-byte-aligned pair of little-endian float32s.

Phase 1 should apply only the combo factor, so the raw damage presented to the
native calculator becomes:

```text
scaled_raw = native_raw * combo_multiplier(hit_index)
```

Applying the factor before `FUN_00224e30` deliberately preserves native
offense, durability, temporary battle factors, and the final `[0, 1]` clamp.
It also prevents the feature from duplicating HP subtraction or Practice damage
display.

The existing `damage_multiplier` column in the dense character-override table
is a separate future outgoing-character feature. Its table is loaded only when
the separately selectable `character_overrides` node is enabled, and it has no
runtime consumer today. Activating it as an implicit part of combo scaling
would broaden this task and make the typed combo setting depend silently on
another setting. Leave it dormant in phase 1. If that feature is approved
later, resolve its base/character precedence by match-start identity and
compose it in this same damage shim, rather than competing for the same native
call sites.

### Runtime hook

The runtime-proven minimum is to guard and replace the clean `jal` instructions
at ELF offsets `0x134B80` and `0x131798` (runtime `0x00234A80` and
`0x00231698`; expected bytes `8C93080C` at both). The first is ordinary
attack-record damage. The second is the fixed `0.02` response/contact-stage
event exercised by hit three. At both boundaries raw damage is in `f12`,
defender is in `a0`, native flags are in `a1`, and the original result must be
returned in `f0`.

The same contact initializer has a statically confirmed `0.04` sibling at ELF
offset `0x131734` (runtime `0x00231634`, also `8C93080C`). It was not exercised
by this movie. A production setting named general `combo_damage_scaling` must
either validate and hook that sibling too or state a narrower two-path scope;
otherwise equivalent contact-stage damage would scale according to a native
flag branch. Guarded-hit damage at runtime `0x00228D18` is a separate path and
is excluded unless guard/chip scaling is explicitly requested.

A small assembly shim is safer than relying on the C compiler to reproduce
this mixed float/register calling convention. It should:

1. Save `ra`, `a0`, `a1`, and raw `f12` on a 16-byte-aligned stack frame.
2. Call a C helper with the defender pointer and receive a multiplier in `f0`.
3. Restore raw damage, multiply it by that multiplier, and restore `a0/a1`.
4. Call the original `FUN_00224e30` at runtime `0x00224E30`.
5. Restore `ra` and return without modifying the native result in `f0`.

The helper should use a combo factor of `1.0` whenever native combo state is
unavailable. It follows defender `+0x20` to the attacker, reads side as
`attacker[+0x60] & 1`, loads the native combo object from
`0x006076B8 + side * 4`, and verifies that object `+0x00` is the same attacker.
It reads signed current count at object `+0x34` and signed pending count at
attacker `+0xA45`, clamps a negative pending count to zero, and computes:

```text
hit_index = max(1, current_count + max(pending_count, 0))
```

It then applies the configured curve. Do not create a second combo timer or
reset flag: the native manager already
owns accepted-hit aggregation, the 90-frame timer, battle-state termination,
current-count reset, and record-count update. The record at object `+0x36`
must never affect damage; after a reset, the next attack is hit 1 even though
the record remains nonzero.

The helper's complete decision can remain stateless:

```c
attacker = *(fighter **)(defender + 0x20);
if (attacker == NULL)
    return 1.0f;

side = attacker[0x60] & 1;
combo = *(combo_manager **)(0x006076B8 + side * 4);
if (combo == NULL || combo->owner_at_0x00 != attacker)
    return 1.0f;

current = *(signed short *)(combo + 0x34);
pending = *(signed char *)(attacker + 0xA45);
hit_index = current + (pending > 0 ? pending : 0);
if (hit_index < 1)
    hit_index = 1;

multiplier = 1.0f - decay * (float)(hit_index - 1);
if (multiplier < minimum_multiplier)
    multiplier = minimum_multiplier;
return multiplier;
```

The production C should use byte-pointer arithmetic and volatile scalar reads
for the live fields rather than declaring partial native structs whose padding
could imply an ABI that has not been established.

### Builder changes required for implementation

Implementation should stay inside the existing battle-logic mechanisms:

- add the typed `combo_damage_scaling` object under `features.battle_logic` in
  `@builder/catalog/catalog.modcat`, pointing to new injection ID
  `i__battle_logic__combo_damage_scaling`, and select the accepted values in
  `@builder/configurations/base.json` so existing profile overrides inherit
  them;
- add `@builder/scripts/combo_damage_scaling.py`, analogous to
  `xdash_chakra_cost.py`, to emit read-only symbol
  `battle_logic_combo_damage_scaling` as `<2f>`, then import and prepend that
  fragment in the existing battle-logic branch of `module_pipeline.py`;
- add `src/battle_logic/combo_damage_scaling.c` with a multiplier entry that
  imports the curve symbol and reads the proven native combo state;
- add the three guarded call-site hooks, compiled helper fragment, and one
  shared ABI shim to `@builder/catalog/injections.json`;
  the third hook at ELF `0x131734` remains a deployment gate until its natural
  `0.04` path has a positive capture (response target `0x42..0x47` with the
  applicable fighter `+0xBB0/+0xBBC/+0xBB4` bit `0x400` set). The clean-stage
  resource scan narrows that capture to load slot 7 / logical stage 8 /
  `S08.CCS`: it is the only one of the 24 clean stage archives whose authored
  `0x0B00` collision-mesh flags contain `0x400`; and
- add `tests/na228_builder/test_combo_damage_scaling.py` for catalog values,
  exact float32 encoding, absent-state and owner-mismatch fallback, signed
  current/pending hit-index, floor, relocations, all expected bytes, disabled
  output, and output determinism. Existing package/integration tests should
  also assert that the disabled node leaves all three clean calls unchanged.

This would introduce one new persistent configuration contract. It should not
be implemented until the curve semantics and default values above are accepted.
No new workflow, manifest, generator, or runtime state is needed.

### Coverage and validation

Phase 1 must claim only damage demonstrated by a counter replay. A positive-
control replay redirected all ten clean native calculator callers and retained
native behavior. Across the exact 13-marker movie, runtime `0x00234A80`
recorded eight invocations and runtime `0x00231698` recorded one; all other
sites recorded zero. The earlier candidate `0x00228D18` is therefore excluded
for this string, not merely unproven; static tracing further identifies it as
guarded-hit damage. Globally wrapping either the calculator or HP subtractor
would scale unrelated damage while a combo happens. The complete ten-caller
matrix and its source-category limits are canonical in `battle.md`.

The `0x00231698` event used raw `0.02`, flags `0x122`, and occurred alongside
the third visible hit's main raw `0.05` event. Focused logging established that
the main event saw `(current, pending) = (2,1)` and the secondary event saw
`(3,0)`. The proposed formula produces hit index three for both, so the same
stateless shim can cover both calls without incrementing the tier twice or
introducing a latch. Hooking `0x00234A80` alone would instead leave the
secondary event's `0.022` native damage unscaled.

An end-to-end transient test applied the recommended `0.10` decay / `0.30`
floor curve at both sites. The five accepted hits used tiers
`100%, 90%, 80%, 70%, 60%`; both hit-three events used `80%`. Exact HP after
hits two through five was `0.937960029`, `0.867560029`, `0.849080026`, and
`0.837200046`, while every native combo checkpoint matched baseline. After
native resets, three later calls all resolved to tier one. Captures and exact
per-call floats are recorded in `battle.md`; Practice displayed the resulting
`6.2%`, `13.2%`, `15.0%`, and `16.2%` through the unchanged native path. A
raw-state audit additionally proved that the manager pointer, owner, current
and record counts, and all three timer words matched baseline at every marker.
This validates the runtime mechanism's decay and reset behavior, not a
production builder implementation. The movie reaches only hit five, so a
natural eight-or-more-hit replay or a controlled helper test is still required
to exercise the configured `30%` floor at runtime.

Before extending scope, capture one isolated example of each desired category
(projectile, Jutsu, Ultimate Jutsu, throw, support) and one example of each
excluded category (status, self, scripted, or environmental damage), then use a
temporary per-call-site counter to classify its actual route.

The minimum new input needed depends on the intended public scope:

- no new input is needed to implement and honestly label the already proven
  two-path Sakura normal-string scope;
- one natural contact transition to target `0x42..0x47` with its applicable
  `0x400` flag is needed before the `0.04` sibling can join a general
  ordinary/contact claim. The current load-slot-6 / `S07.CCS` replay cannot
  produce that condition: its 1,125 authored and runtime-active environment
  primitives contain no such flag. Use load slot 7 / logical stage 8 /
  `S08.CCS`, and make contact with the two flagged triangles in
  `HIT_s08are00_hit_s3` group 2. A stage-only control loaded those triangles
  but invoked the `0.04` caller zero times: the unchanged movie stayed in the
  lower side-0 region and never entered response `0x42..0x47` or copied bit
  `0x400` into the applicable fighter field. The replacement sequence must
  naturally navigate to `S08`'s upper/side-1 region near authored components
  `(component1, component2) = (800, 1030)` before driving the launch/contact;
- one natural eight-or-more-hit string is preferable for an end-to-end floor
  check, although an exact helper test can validate the curve clamp itself;
- one guarded hit is needed only if blocked/chip damage should scale; and
- isolated projectile, Jutsu, Ultimate Jutsu, throw, and support sequences are
  needed only for categories the setting is intended to cover.

Markers are optional for every one of these sequences. A complete input movie
or PINE-driven full-pad state/frame sequence is sufficient to execute it;
markers only provide convenient deterministic before/after checkpoints. A
verbal attack recipe can be converted to PINE inputs, but exact hold/release
timing must be observed and corrected frame by frame, so a saved movie remains
the stronger reusable regression artifact once the sequence works.

The deterministic validation baseline is the exact Manual-cache Practice-row-9
replay documented in `battle.md`. Markers are capture checkpoints only; the
movie supplies the full attack sequence frame by frame. Validation should
prove all of the following:

- with the feature disabled, all 13 screenshots and extracted HP/combo fields
  match the synchronized baseline;
- hit 1 remains unscaled, later hits use the configured tiers, and the native
  current count and 90-frame reset timing remain unchanged;
- marker `0012` resets the scaling index even though record count stays five,
  and the next registered hit is again index 1;
- the main and secondary events of hit three both use tier three, while native
  combo current count still advances only once;
- a missing attacker/manager, mismatched manager owner, or nonpositive derived
  index safely uses hit index one; a negative pending byte contributes zero;
- hit eight and all later hits clamp to the configured `30%` floor; and
- damage display, HP delta, KO clamp, Practice nonlethal clamp, and the disabled
  path are compared against expected float32 values, not rounded HUD text.

The current recording proves native count/reset ownership and execution-traces
one Sakura normal string through its main and secondary damage calls. It does
not establish coverage for the other damage categories, so category captures
remain required before claiming or broadening the feature's scope.
