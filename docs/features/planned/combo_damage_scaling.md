# Combo damage scaling

The design has been investigated and validated with a transient two-site
scaling hook for one normal string, but is not implemented in the builder. The
native combo and damage evidence is canonical in
[`damage.md`](../../knowledge/gameplay/damage.md#combo-hit-state-and-damage-path);
the recording and traces behind it are under
[Reference recording and traces](#reference-recording-and-traces).
No current catalog node, payload fragment, hook, or runtime consumer changes
damage by combo hit index.

## Recommended configuration

Use one typed object named `combo_damage_scaling`, rather than a marker list
or per-move input sequence. Its catalog and patch ownership remain unresolved;
`general` ownership is rejected:

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
the separately selectable `defaults.match_setup.character_balance` node is
enabled, and it has no
runtime consumer today. Activating it as an implicit part of combo scaling
would broaden this task and make the typed combo setting depend silently on
another setting. Leave it dormant in phase 1. If that feature is approved
later, resolve its base/character precedence by match-start identity and
compose it in this same damage shim, rather than competing for the same native
call sites.

## Runtime hook

The runtime-proven minimum is to guard and replace the clean `jal` instructions
at ELF offsets `0x134B80` and `0x131798` (runtime `0x00234A80` and
`0x00231698`; expected bytes `8C93080C` at both). The first is ordinary
attack-record damage. The second is the fixed `0.02` response/contact-stage
event exercised by hit three. At both boundaries raw damage is in `f12`,
defender is in `a0`, native flags are in `a1`, and the original result must be
returned in `f0`.

The same contact initializer has a statically confirmed `0.04` sibling at ELF
offset `0x131734` (runtime `0x00231634`, also `8C93080C`). It was not exercised
by this movie. A production `combo_damage_scaling` setting must
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

## Builder changes required for implementation

Implementation should stay inside the existing battle-logic mechanisms:

- after its catalog and patch ownership are decided, add the typed
  `combo_damage_scaling` object to `@builder/catalog.modcat` and select the
  accepted values in `@builder/configurations/base.jsonc` so existing profile
  overrides inherit them;
- add `@builder/patches/defaults/battle_mechanics/combo_damage_scaling/combo_damage_scaling.py`,
  following the configuration-fragment pattern of
  `substitution_resource/substitution_gauge.py`, to emit the read-only curve
  symbol as `<2f>`, then import and prepend that fragment with the other
  battle-mechanics fragments in `module_pipeline.py`;
- add `combo_damage_scaling.c` in the same directory with a multiplier entry
  that imports the curve symbol and reads the proven native combo state;
- add the three guarded call-site hooks, compiled helper fragment, and one
  shared ABI shim to the `defaults` patch definitions in
  `@builder/patches/defaults/defaults.json`;
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

## Coverage and validation

Phase 1 must claim only damage demonstrated by a counter replay. The
[positive-control replay](#calculator-call-site-traces) recorded eight
invocations at runtime `0x00234A80`, one at `0x00231698`, and none at the
other eight calculator call sites. The earlier candidate `0x00228D18` is therefore excluded
for this string, not merely unproven; static tracing further identifies it as
guarded-hit damage. Globally wrapping either the calculator or HP subtractor
would scale unrelated damage while a combo happens. The complete ten-caller
matrix and its source-category limits are canonical in
[`damage.md`](../../knowledge/gameplay/damage.md#damage-caller-coverage).

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
native resets, three later calls all resolved to tier one. The native per-call
baseline is in [calculator call-site traces](#calculator-call-site-traces).
Practice displayed the resulting
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
  `HIT_s08are00_hit_s3` group 2. The [stage-only control](#stage-only-s08-control)
  loaded those triangles but invoked the `0.04` caller zero times. The
  replacement sequence must
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

The deterministic validation baseline is the exact Practice-row-9
[reference recording](#input-recording). Markers
are capture checkpoints only; the movie supplies the full attack sequence frame
by frame. Validation should prove all of the following:

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

## Reference recording and traces

### Input recording

The maintained
[deterministic controller stream](../../../pcsx2_files/input_recordings/damage_scaling.p2m2)
contains 3,619 input frames and 13 actionable rising edges of the `L3+R3`
marker chord. Its Practice setup (row 9) selects Sakura (ID `58`), No Support
(`0x25`), and no starting effect, against Naruto (ID `57`) on Practice's
bootstrap stage, load slot 6 (`S07.CCS`).

Every attack input already exists in the movie's per-frame controller stream.
The marker chord identifies the recorded comparison frames; it does not
sequence the attacks.

The stream has 3,620 records of 36 bytes, including the format's all-zero frame
zero. Controller 2 remains neutral; Controller 1's analog bytes remain centered
and every pressure-capable digital press has the corresponding full-pressure
byte. The actionable input is reproduced by these inclusive frame runs; all
buttons not named for a frame are released and all unlisted frames are neutral
except for overlaps among the listed runs:

| Control | Inclusive movie-frame runs |
| --- | --- |
| `L3+R3` marker chord | `2673-2680`, `2802-2809`, `2813-2816`, `2828-2833`, `2929-2936`, `2939-2948`, `2950-2953`, `2987-2990`, `3061-3066`, `3171-3176`, `3207-3210`, `3249-3256`, `3502-3506` |
| `Circle` attack | `2751-2757`, `2766-2770`, `2776-2783`, `2789-2792`, `2803-2808`, `2814-2818`, `2827-2831`, `2841-2850`, `2942-2947`, `2955-2967`, `2972-2979`, `2983-2987`, `3025-3028`, `3149-3157`, `3193-3201`, `3239-3245`, `3268-3274` |
| `Cross` | `3461-3466`, `3471-3477`, `3480-3488` |
| `Right` | `2692-2734`, `2770-2866`, `2892-2924`, `3084-3095`, `3117-3124`, `3351-3362`, `3375-3413` |
| `Down` | `2922-3023` |
| `Left` | `3309-3352`, `3362-3376` |

The runs preserve simultaneous inputs, including the five frames where `Left`
and `Right` overlap and the marker/attack overlaps. Recombining active controls
at every change boundary yields the exact Controller 1 stream. Decoding the
movie establishes its inputs, not every intermediate animation or memory state.

### Marker timeline

Synchronized screenshots and runtime memory establish this timeline:

| Marker | Movie frame | Visible result | Naruto HP | Current / record combo | Timer words `+0x14/+0x18/+0x1C` |
| ---: | ---: | --- | ---: | ---: | --- |
| `0001` | 2673 | Baseline | `1.000000000` | `0 / 0` | `0/0/0` |
| `0002` | 2802 | 2 hits, displayed `6.5%` | `0.934000015` | `2 / 0` | `90/88/87` |
| `0003` | 2813 | Same 2-hit result | `0.934000015` | `2 / 0` | `90/82/81` |
| `0004` | 2828 | Same 2-hit result | `0.934000015` | `2 / 0` | `90/75/74` |
| `0005` | 2929 | 3 hits, displayed `15.3%` | `0.846000016` | `3 / 0` | `90/44/43` |
| `0006` | 2939 | Same 3-hit result | `0.846000016` | `3 / 0` | `90/39/38` |
| `0007` | 2950 | Same 3-hit result | `0.846000016` | `3 / 0` | `90/34/33` |
| `0008` | 2987 | 4 hits, displayed `18.0%` | `0.819599986` | `4 / 0` | `90/79/78` |
| `0009` | 3061 | 5 hits, displayed `20.0%` | `0.799799979` | `5 / 0` | `90/64/63` |
| `0010` | 3171 | Fresh 1-hit attack, displayed `2.6%` | `0.973600030` | `1 / 5` | `90/86/85` |
| `0011` | 3207 | Same 1-hit result | `0.973600030` | `1 / 5` | `90/90/89` |
| `0012` | 3249 | Native current-combo reset | `0.973600030` | `0 / 5` | `90/69/68` |
| `0013` | 3502 | Next hit counted before HP subtraction | `1.000000000` | `1 / 5` | `90/84/83` |

The pending byte was zero at every marker because the manager had already
consumed it. The stable root at EE `0x00607600` pointed to `0x00CA4700`. Its
live-fighter pointers were Sakura at `0x00E36CA0` and Naruto at `0x00E44CE0`
in every exact capture. These are allocation-specific addresses; a hook must
follow the pointers rather than embed them.

### Calculator call-site traces

A focused trace of the guarded-hit call at runtime `0x00228D18` recorded zero
calls while the HP timeline matched the baseline.

A positive-control replay redirected all ten retail calculator call sites
through one resident logger while retaining native behavior. The cumulative
invocation counts at markers `0001` through `0013` were
`0, 2, 2, 2, 4, 4, 4, 5, 6, 7, 8, 8, 9`. Eight events came from runtime
`0x00234A80`, one came from runtime `0x00231698`, and the other eight sites
recorded zero. Every event targeted Naruto at `0x00E44CE0`. The active
instrumentation and positive counts rule out a code-cache artifact.

A focused replay then hooked only runtime `0x00234A80` and `0x00231698` and
logged each call before and after the original calculator. Every record
resolved attacker `0x00E36CA0`, side zero, manager `0x00E40A90`, and matching
manager owner `0x00E36CA0`:

| Event | Site | Raw | Flags | Current / pending | Hit index | Native result |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `0x00234A80` | `0.02` | `0x133` | `0 / 1` | 1 | `0.0264` |
| 2 | `0x00234A80` | `0.03` | `0x133` | `1 / 1` | 2 | `0.0396` |
| 3 | `0x00234A80` | `0.05` | `0x133` | `2 / 1` | 3 | `0.0660` |
| 4 | `0x00231698` | `0.02` | `0x122` | `3 / 0` | 3 | `0.0220` |
| 5 | `0x00234A80` | `0.02` | `0x133` | `3 / 1` | 4 | `0.0264` |
| 6 | `0x00234A80` | `0.015` | `0x133` | `4 / 1` | 5 | `0.0198` |
| 7 | `0x00234A80` | `0.02` | `0x133` | `0 / 1` | 1 | `0.0264` |
| 8 | `0x00234A80` | `0.02` | `0x133` | `0 / 1` | 1 | `0.0264` |
| 9 | `0x00234A80` | `0.02` | `0x133` | `0 / 1` | 1 | `0.0264` |

Across all 13 checkpoints the focused trace matched baseline HP and native
current/record counts, while establishing input state, native return value,
manager ownership, and reset behavior at the exact call boundary. It does not
exercise every static reset condition.

### Stage-only `S08` control

At marker `0001` on the recording's `S07` stage, a runtime walk found exactly
1,125 active environment primitives and none with bit `0x400`, matching the
authored archive. A stage-only control then loaded slot 7 (`S08.CCS`) and
traced runtime `0x00231634` across all 13 checkpoints. It found 395 active
environment primitives, including two with runtime flags `0x40959595`, the
orientation-augmented form of authored `0x00959595`; the call count remained
zero.

The unchanged input movie did not navigate to those triangles. Both live
fighter position vectors at `+0x30` kept component 1 at zero, and component 2
stayed between 0 and approximately 180, while the flagged authored vertices
occupy component-1 range `736..923` and component-2 range `1059..1124`.
Those coordinates agree with `S08`'s side-1 combo anchors at component 1 `800`
and component 2 `1030`; the movie remained in the lower side-0 region visible
in its screenshots. Naruto's marker substates were only `0`, `0x29`, `0x2B`,
`0x48`, and `0x5D`, never `0x42..0x47`. His `+0xBB0/+0xBB4/+0xBBC` values
were respectively `0`, `0x200060C1`, and `0` at every marker, so none contained
bit `0x400`. The stage control therefore establishes resource availability
without executing the `0.04` branch.
