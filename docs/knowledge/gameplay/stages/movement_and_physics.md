# Movement and physics

This document records ordinary fighter movement in unmodified retail NA2
(`SLPS-25837`).

## Research coverage

- **Assigned scope:** Ordinary locomotion: walk/run, jump, aerial movement, velocity/acceleration integration, landing, floor contact, facing, stage constraints and state transitions, including concrete character variations.
- **Exploration depth:**
  - The shared resident update, complete running handlers, ordinary jump request/selection/impulse paths, aerial steering and landing handlers, surface-axis entry/exit consumers, gravity, contact correction, and construction and placement initialization, with critical integration, jump, and mode-`3` instructions read directly.
  - All 94 character-table entries, all 78 distinct movement parameter blocks, and all 25 ordinary descriptors at substates `0x0E..0x26`.
  - The Gaara/Deidara controller-marker producers and cleanup joined to movement scheduling and contact history; all direct immediate-offset halfword selector writers in resident code and selected exchange/Ultimate Jutsu reset paths.
- **Confirmed coverage:** Ordinary state transitions and scheduling gates, direction versus facing, proportional acceleration/braking, first/second/wall jump selection and impulses, descent and landing, displacement-before-gravity ordering, collision masks/contact outputs, contact history, native initialization, dedicated-record character variation ranges, controller-marker retention across ordinary movement, and distinct special-selector integration/reset contracts.
- **Unresolved or untested:** A complete inventory of every character-specific callback that can replace ordinary motion; wider/computed writes to the special `+0x63 & 0x20` marker and physics selector; reachability of combinations of that marker, special physics modes, and rotated axes; a concrete mode-`4` producer; names of all polygon attribute combinations; exact elapsed landing times over arbitrary stage geometry; and the complete stage-boundary service caller set. The fighter environment query `FUN_00211420` and its walker `FUN_00210D80` (registry walk, distance retention, and result storage) are not yet documented in [Collision](../combat/collision.md).
- **Deliberate exclusions and overlap:** Hit-specific motion belongs to [Hit response](../combat/hit_response.md), X-dash to [X-dash](../combat/xdash.md), environment-query infrastructure to [Collision](../combat/collision.md), polygon attribute production and classification to [Stage surface attributes](stage_surface_attributes.md), stage data to [Stages](stages.md), and entity lifetime to [Battle entities](../session/battle_entities.md). [Awakening](../characters/awakening.md) owns marker activation, effects and character variants; [Combat action execution](../combat/combat_action_execution.md) owns exchange choreography, [Character action callbacks](../characters/character_action_callbacks.md) callback coverage, [Projectiles](../projectiles_and_items/projectiles.md) carrier motion, [Section transfers](section_transfers.md) transfer choreography, and [Battle lifecycle](../session/battle_lifecycle.md) session scheduling/reconstruction. This document owns ordinary fighter movement and its selected consumers and reset boundaries, without repeating those owners' investigations.
- **Evidence limitations:** Static control flow and retail data establish arithmetic and dispatch contracts; they do not establish observed animations or elapsed wall-clock timings. Incomplete analysis references cannot prove that an indirect path is absent.

## Evidence and address conventions

Resident addresses below are EE addresses. BTL addresses are explicitly
labeled live; preserved import addresses and complete-file offsets follow
[Retail game file identities](../../game/files/file_identities.md#address-conventions).

## Shared movement fields and ordering

| Fighter field | Established role and evidence |
| --- | --- |
| `+0x30..+0x3C` | Position vector; `FUN_0024A660` integrates movement into it. Ordinary vertical motion uses component `+0x38`; the final pass forces displacement component `+4` to zero. |
| `+0x18E`, `+0x190`, `+0x192` | Major action, substate, and phase. `FUN_00217E40` owns major/substate changes and resets action timeline state when they change. |
| `+0x1AC` | Fighter update-rate scalar, multiplied into speed-derived displacement. |
| `+0x988` | Physics-mode selector consumed by the shared pass; mode `0` is the ordinary gravity branch. |
| `+0x98C` | Direction-table index for planar speed; `FUN_0024A660` resolves its angle through resident `0x005C16B0`. |
| `+0x994`, `+0x998` | Directional speed and vertical speed. The shared pass constructs planar displacement from `+0x994` and adds `+0x998` as component `+8`. |
| `+0x99C` | Smoothed input-motion value maintained by `FUN_002173D0`; this is separate from the integrated directional speed. |
| `+0x9B0`, `+0x9B4` | Saved/auxiliary vertical speed and per-pass gravity multiplier. |
| byte `+0x63`, bit `0x80` | Grounded/contact flag, cleared and recomputed by the movement pass. |
| `+0xB9A` | Signed consecutive-grounded update count; increments up to `0x7FFF` while grounded and clears while airborne. |
| byte `+0xB9C` | Action-entry contact history: low nibble `1` means grounded at entry, `2` airborne. Movement latches `0x10` when an air-entered action reaches ground, and `0x20` when a ground-entered action becomes airborne. |

`FUN_0024DA50`, fighter virtual slot `+0x10`, calls `FUN_0024CFD0` and then
animation advancement `FUN_0024D1C0` only while pause count `+0x20C < 1`.
`FUN_0024CFD0` adjusts orientation for physics-axis mode and calls the shared
movement pass `FUN_0024A660` (preserved function body
`0x0024A660..0x0024C18B`). In the ordinary
axis mode (`byte +0x9B8 & 3` is `0` or `1`), the vertical axis is component
`+8`; modes `2/3` rotate the displacement and use component `+0` for their
surface-contact calculation. The final stored world position still has no
component-`+4` displacement.

The pass constructs the displacement from the current speeds times `+0x1AC`,
adds transient vector contributions from `+0x4D0/+0x4E0`, resolves side/floor/
ceiling contact, and applies gravity to the speed for the next pass. Additional
overlap and segment corrections precede the final position write.
`FUN_0024DA50` clears both transient vectors afterward. Thus the gravity
subtraction does not change the current
pass's already-constructed vertical displacement. The pause and hit-specific
update ordering are owned by [Hit response](../combat/hit_response.md#hit-update-order-and-elapsed-updates).

## Gravity and input smoothing

`FUN_002151E0` copies 55 words from character record `+0x00..+0xD8` to
fighter `+0x8C..+0x164`. `FUN_002183D0(multiplier,fighter,speed)` reads the
copied record for ordinary major states; major `8` instead reads the static
record selected by current character ID through resident `0x005A2904 + id*8`.
For ordinary motion the next speed is:

```text
v_next = max(v - multiplier * record[+0x6C] * 3 * fighter[+0x1AC], terminal)
terminal = -record[+0x70] * 3                 when multiplier == 1
terminal = -FLT_MAX                         when multiplier != 1
```

A zero multiplier skips the entire gravity update. Major `5`, nonzero word
`+0xB00`, or byte `+0x61` bit `0x80` selects the separate fixed-gravity
contract documented in [Hit response](../combat/hit_response.md#gravity-and-airtime).
In ordinary physics mode `0`, `FUN_0024A660` resets `+0x9B4` to `1.0` after
the gravity branch, so this multiplier is a one-pass request. Airborne physics
mode `3` instead jumps past that reset and subsequent overlap corrections.

`FUN_002173D0` prioritizes input bit `1` over bit `2`, writes desired direction
`+0x98E` as `0/1`, and increments signed input-duration field `+0x98A`; when
neither bit is present it clears the duration. Grounded input uses fighter `+0xEC` as the target
and `+0xF4` as the release approach factor; airborne input uses `+0x100` and
`+0x108`. With directional input, the approach factor comes from `+0x33C`.
The helper `FUN_00218250` rate-scales the factor unless it is exactly `1.0`,
caps it at `1.0`, and uses `FUN_00180CE0` to approach the target in `+0x99C`;
values already within `0.1` are snapped to the target. The state handlers,
rather than this input smoother, decide how `+0x99C` becomes actual speed.

The approach operation is proportional, not constant acceleration:
`FUN_00180CE0(target,factor,&value)` writes
`value += (target - value) * factor`. Its consumers normally cap the factor at
one and snap the last `0.1` of error. At unit fighter rate, ground acceleration
`0.3` therefore closes 30% of the remaining speed difference each update.

## Ordinary state dispatch

The unpaused ordinary loop in `FUN_0024FD80` publishes controller input through
`FUN_00217320`, smooths it through `FUN_002173D0`, processes existing-state
transitions in `FUN_00248580`, processes new requests in `FUN_00248EC0`, then
applies the selected state's motion in `FUN_00249640`. These are distinct
passes: a request can replace the state whose earlier transition handler ran.
The movement/animation virtual pass follows as documented in
[Hit response](../combat/hit_response.md#hit-update-order-and-elapsed-updates).

The following names are retail descriptor strings. They are obtained from the
eight-byte substate table at BTL live `0x0089AEB0` and its string pointers;
they are not inferred from function names. This bounded table covers every
ordinary running, jump, falling, and landing substate `0x0E..0x26`.

| Major/substate | Retail descriptor | Shared consumers |
| --- | --- | --- |
| `(0,0)` | `ACT_NUT_0` | Neutral; loses ground into `(3,0x1E)`, starts directional locomotion into major `1`. |
| `(1,0x0E..0x11)` | `ACT_RUN_0`, `ACT_RUN_1`, `ACT_RUN_2`, `ACT_RUN_3` | `FUN_0022C700` transitions; `FUN_0022CCC0` motion. |
| `(1,0x12..0x14)` | `ACT_WMV_0..2` | Surface-axis movement; `FUN_0022DD60` transitions, `FUN_0022E320` motion. |
| `(1,0x15/0x16)` | `ACT_LIN_0/1` | Section-transfer motion; `FUN_0022E950`. |
| `(2,0x17)` | `ACT_JMP_0` | Jump preparation; `FUN_0022F8C0` waits for character startup count or loss of ground. |
| `(2,0x18/0x19)` | `ACT_JMP_V1/V2` | First/second jump, ordinary low directional-input variant. |
| `(2,0x1A/0x1B)` | `ACT_JMP_F1/F2` | First/second jump, directional variant selected by the gates below. |
| `(2,0x1C/0x1D)` | `ACT_JMP_B1/B2` | B1 changes direction at selection; B2 also depends on the previous jump variant. |
| `(3,0x1E/0x1F)` | `ACT_FAL_0/FT` | Ordinary fall and input-triggered faster descent. |
| `(3,0x20..0x25)` | `ACT_FAL_V1/V2`, `ACT_FAL_F1/F2`, `ACT_FAL_B1/B2` | Corresponding post-jump aerial states. |
| `(4,0x26)` | `ACT_LND_0` | Landing; `FUN_002305D0` transitions and `FUN_00249640` deceleration. |

### Ground motion and facing

`FUN_00248580` selects running major `1` once grounded neutral has one held
direction update.
Matching current and desired direction selects `0x0E`; changed direction
selects `0x10` unless current speed divided by its ground target exceeds `0.5`,
in which case it selects `0x11`. The ordinary consumers inspected here use the
same `ACT_RUN_0` state for weak and strong directional input; no separate
walk-state branch is present in these bounded consumers. Input amount changes
the approach factor toward the same ground target; `ACT_RUN_0` then approaches
that smoothed value. This does not assert that every character-specific callback
is absent.

`FUN_0022CCC0` implements the four running variants:

- `0x0E` approaches `+0x99C` using ground acceleration `+0xF0`; it publishes
  desired direction to `+0x98C/+0x990` on entry or direction change.
- `0x0F` approaches zero using ground braking `+0xF4`. Releasing input in
  `0x0E` enters this variant while speed remains above half the target,
  otherwise goes directly to neutral.
- `0x10` is the neutral-entry turn: it approaches zero with `+0xF4`, and the
  transition handler allows running after input duration reaches four updates
  or returns to neutral on descriptor completion.
- `0x11` is the high-speed reversal: above half the ground target it brakes
  using `+0xF4 * 0.66`; below that threshold it approaches negative ground
  target using `+0xF0 * 1.8`. Its exit callback `FUN_0022C4D0` flips negative
  speed to positive and publishes the new direction.

A side-contact flag (`+0x63 & 0x40`) with contact-side byte `+0xB9F` equal to
current direction makes each running variant snap directional speed to zero.
Loss of ground from any of these running variants enters `(3,0x1E)`.
While already running in `0x0E`, `FUN_0022C700` selects `0x11` on a direction
change only above the half-target threshold. A slower direction change remains
in `0x0E`, whose motion handler publishes the new direction. It does not repeat
neutral's `0x10` entry route.

Facing and movement direction are separate fields. `+0x98C` is the movement
angle-table index, `+0x98E` desired direction, and `+0x990` facing index.
Resident angle table `0x005C16B0` contains `{+pi/2,-pi/2,0,-pi}`; ordinary
indices `0/1` therefore generate positive/negative position-`+0x30` movement.
Facing consumers write orientation `+0x48` through `FUN_001809D0`.
Neutral-entry `FUN_00226F10` derives all three indices from the sign of
`+0x48`, first negating directional speed when movement and facing disagree.
Entering the same major/substate is not a pure no-op: `FUN_00217E40` calls
old-state exit and new-state preparation before its same-state early return.

### Jump requests and state selection

`FUN_00248EC0` routes published input bit `0x10000` to `FUN_0022F200`.
That helper rejects major `8` and nonzero action lock `+0x254`, and admits the
following bounded ordinary sources:

| Source | Result |
| --- | --- |
| neutral `0`, substates `3/4/5`, running `0x0E..0x11`, landing `0x26` | Enter preparation `(2,0x17)` via `FUN_0022F3D0(...,0)`. Landing first initializes directions from orientation. |
| first-jump `0x18/0x1A/0x1C`, first post-jump `0x20/0x22/0x24`, ordinary fall `0x1E` | Request second jump with `FUN_0022F3D0(...,2)`. |
| second-jump `0x19/0x1B/0x1D`, second post-jump `0x21/0x23/0x25`, faster fall `0x1F` | Only a qualifying side surface (`+0x63 & 0x40`, `+0xBB0 & 0x100`, desired direction differs from `+0xB9F`) admits another jump. |
| surface states `0x12/0x13` | Leave the rotated surface axis, set `+0x9B8 & 4`, enter second directional jump `(2,0x1B)`. |
| preparation `0x17`, surface `0x14`, section transfers `0x15/0x16` | No jump admitted by this helper. |

Preparation `0x17` approaches zero speed with `0.33` times the ground braking
factor. `FUN_0022F8C0` selects the first-jump variant when primary action cursor
`+0x1C4 >= signed word +0x10C`, or immediately if ground was lost. In
`FUN_0022F3D0`, first-jump selection with matching direction uses `V1` unless
input amount `+0x33C >= 0.3` and input bits `0x10/0x20` are both clear, then
uses `F1`; changed direction uses `B1` and publishes the desired direction.
For second-jump selection, let directional input qualify when `+0x33C >= 0.3`
and both input bits `0x10/0x20` are clear. `FUN_0022F3D0(...,2)` selects:

| Movement/desired direction | Source `B1` or `FAL_B1` (`0x1C/0x24`) | Other admitted source |
| --- | --- | --- |
| Equal | `B2` if input qualifies, otherwise `V2` | `F2` if input qualifies, otherwise `V2` |
| Different | `F2` if input qualifies, otherwise `V2` | `B2` regardless of input amount |

Changed-direction second selection publishes desired direction to `+0x98C`.
Qualifying wall contact sets byte `+0x9B8` bit `4`; otherwise selection clears
that bit.

### Jump impulses and aerial control

On crossing primary-timeline event zero, `FUN_0022FAD0` installs the impulse.
With `g = fighter[+0xF8] * 3`, its vertical formula is:

```text
v_first  = sqrt(H1 * effect_height_factor * g * 2) - g/2
v_second = sqrt(H2 * effect_height_factor * g * 2) - g/2
H1 = fighter[+0x110]     H2 = fighter[+0x114]
```

Ground primitive flag `0x800` doubles `H1` when the first impulse is initialized
while grounded. For a second jump with `+0x9B8 & 4` set, the formula instead
uses fixed height `300` and full aerial directional target `+0x100`. Otherwise
second directional speed is `+0x100 * normalized_input * 0.75`, against
`+0x100 * normalized_input` for the first jump. `normalized_input` is
`+0x99C / +0xEC` while grounded and `+0x99C / +0x100` while airborne.
No divide-by-zero guard exists at that normalization site; the 74 dedicated
fighter records examined have nonzero targets.

At the first impulse, `V1/F1` publish desired direction to movement and facing
(`+0x98C/+0x990`); `B1` publishes only movement direction. The distinction
allows movement direction to differ from facing within the ordinary jump paths.

`FUN_00306E80` supplies the effect height factor, starting at `1` and adding
`effect[+0x80] - 1` for each active effect in the fighter's `+0x8C4/+0x8C8`
list. Effects therefore add deviations from one rather than multiplying
individual factors. Effect identity and writers belong to
[Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md).

On jump updates without the impulse-event crossing, and during falling,
`FUN_0021A140(fighter,variant)` applies aerial steering. Input amount below
`0.3` brakes toward zero with
`+0x108`; matching-direction variant `0` can approach `+0x99C` with `+0x104`.
Opposite direction or an input target below current speed instead approaches
`current_speed - +0x99C` with `+0x104` and uses a negative aerial clamp.
Variants `1/2` retain the current speed when no braking/reversal branch applies.
The helper stores the selected variant in byte `+0x992`. A wall-jump flag with
primary cursor at most `9`, or current speed above aerial target, skips these
ordinary approach branches. This is a stateful steering rule, not simply an
assignment of stick input to velocity.

Descriptor completion maps first/second jump pairs into their corresponding
falling pairs (`0x18/19 -> 0x20/21`, `0x1A/1B -> 0x22/23`,
`0x1C/1D -> 0x24/25`). Ground contact takes jump and ordinary falling
states to `(4,0x26)`. `FUN_00249640` decelerates landing motion with
`+0xF4 * 0.8`. In `FUN_002305D0`, desired direction matching either movement
or facing permits locomotion at cursor `>= 5` with input duration `>= 4`.
When it differs from both, cursor `< 5`, duration `>= 4`, and speed
`> ground_target * 0.3` first snap speed to the ground target and enter `0x11`;
otherwise this direction case waits for cursor `>= 8` and duration `>= 4`.
The later locomotion selection still applies the half-target reversal threshold.
Descriptor completion subsequently returns to neutral, even if a locomotion
branch changed state earlier in that call. Loss of ground returns to ordinary
fall immediately.

Faster descent `0x1F` has separate rules. At timeline event zero,
`FUN_00249640` sets vertical speed to `-(+0xFC * 3 * 0.6)` and halfword
`+0x9C0` to `10`, then uses ordinary variant-`0` aerial steering. Its transition
handler `FUN_00230150` examines auxiliary distance `+0xBA4` and flags `+0xBAC`:
when distance is unavailable but flags are nonzero it retains this state;
otherwise distance below half scaled fighter height permits landing only when
grounded, and no such nearby floor changes it to `(3,0x22)`.

## Character movement parameters

This census covers every one of resident table `0x005A2900`'s 94 eight-byte
entries and every distinct record's `+0x58..+0x8F`. The 74 dedicated
fighter records supply the ranges below. Filler rows and the four zero-valued
auxiliary metadata records are excluded from playable variation ranges; their
identity belongs to [Character identity](../characters/character_ids.md#character-definition-table).

| Record / copied fighter field | Consumer contract | Dedicated-record range |
| --- | --- | --- |
| `+0x58 / +0xE4` | Contact height dimension, multiplied by `+0x2F0` in movement queries | `120..180` |
| `+0x5C / +0xE8` | Contact width dimension, multiplied by `+0x2F0` | `100..160` |
| `+0x60 / +0xEC` | Ground directional target | `7..30` |
| `+0x64 / +0xF0` | Ground proportional acceleration | `0.125..0.35` |
| `+0x68 / +0xF4` | Ground proportional braking | `0.2..0.35` |
| `+0x6C / +0xF8` | Gravity factor; actual decrement is three times this at unit rate | `0.95..1.5` |
| `+0x70 / +0xFC` | Terminal downward-speed magnitude factor; actual magnitude is three times this | `10..20` |
| `+0x74 / +0x100` | Aerial directional target | `10..16` |
| `+0x78 / +0x104` | Aerial proportional steering factor | `0.02..0.06` |
| `+0x7C / +0x108` | Aerial proportional braking factor | `0.01..0.05` |
| `+0x80 / +0x10C` | Integer jump-preparation action-cursor threshold | `2..7` |
| `+0x84 / +0x110` | First-jump height parameter | `250..400` |
| `+0x88 / +0x114` | Second-jump height parameter | `200..300` |

Floats are rounded to their authored decimal values in these tables. Speeds
are game-space units per active movement update before rate scaling, not units
per second. Heights are inputs to the retail impulse formula, not guaranteed
measured jump-apex heights above arbitrary stage geometry.

| ID / record | Ground target | Gravity decrement | Terminal magnitude | Air target | Preparation | H1 / H2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Naruto `57`, `0x004DAD80` | `21` | `3` | `34.5` | `16` | `3` | `290 / 220` |
| Sakura `58`, `0x004E01B0` | `24` | `2.85` | `33` | `15` | `3` | `300 / 250` |
| Nine-Tailed Fourth Awakened State `73`, `0x00535D50` | `26` | `3` | `34.5` | `16` | `3` | `290 / 210` |
| Might Guy `69`, `0x00520470` | `30` | `4.05` | `60` | `14` | `4` | `400 / 300` |
| Sasori (Hiruko) `76`, `0x005403A0` | `7` | `4.5` | `45` | `10` | `7` | `250 / 200` |
| Second Stage Kidomaru `53`, `0x004C5D70` | `19.5` | `3` | `36` | `12` | `4` | `400 / 250` |

These are record-level variations in the shared movement rules. They do not
constitute a complete audit of every character's special action callbacks.

## Floor, side surfaces, and limits

Ordinary movement is not resolved against one global floor height. The shared
pass calls resident `FUN_00211420(start,end,mask,0)`, which queries registered
environment objects, returns nearest retained distance, changes the endpoint
to the winning point, and publishes its primitive flags at `0x0061F6E8`.
No hit returns `-1.0`. [Collision](../combat/collision.md) owns the primitive
structures and the generic query `FUN_001BF100`; this fighter query and its
walker `FUN_00210D80` are not yet documented there. Their attribute predicate
is in
[Stage surface attributes](stage_surface_attributes.md#query-eligibility-and-contact-classes).
The following fields are movement's consumers.

| Movement output | Established meaning |
| --- | --- |
| `+0xBA0`, `+0xBB0`, byte `+0xB9F` | Side-probe distance, winning side-contact primitive flags, side selector. `FUN_0021BCC0` can probe both directions up to `1.5 * width`; direct movement contact uses `FUN_0021C050` to publish its distance and side. |
| `+0xBA4`, `+0xBAC` | Downward auxiliary-probe distance and flags, supplied by `FUN_0021C240`. Its ray starts half a scaled height above position and ends two heights below position. |
| `+0xBB4` | Primitive flags for the movement pass's ground-contact decision. This is distinct from auxiliary-probe flags `+0xBAC`. |
| `+0xBA8`, `+0xBBC` | Upward clearance distance and direct ceiling-contact flags; `FUN_0021C3C0` supplies the auxiliary upward distance. |
| bytes `+0x63/+0x64` | Side contact bit `+0x63 & 0x40`, ground bit `+0x63 & 0x80`, ceiling bit `+0x64 & 1`. The pass clears/recomputes these. |

Probe distances use float sentinel `0xC6875104` (`-17320.5078125`) when
unavailable. That sentinel is neither a world height nor a valid distance.
With ordinary axis `0/1`, the pass uses side mask `0x40000000`, downward mask
`0x20000000`, and upward mask `0x80000000`. Rotated axes `2/3` change those
to `0xA0000000`, `0x40000000`, and `0x40000000`, with opposite signs for the
axis-2/axis-3 surface normal. Disassembly `0x0024A80C..0x0024A85C` establishes
these exact constants and axis indices.

The downward movement ray differs from the auxiliary probe: it follows the
candidate displacement and extends by a fraction of fighter height when
vertical motion is zero. If the first query misses, ordinary-axis motion
retries after a planar offset of `width * 0.25` when previously grounded or
`width * 0.125` when previously airborne. An accepted floor contact stores
the pre-contact vertical speed in `+0x9B0` when the grounded count was zero,
clears `+0x998`, sets the grounded flag, and replaces the vertical displacement
with the hit-point delta. These stores are at `0x0024B294..0x0024B30C`.

Primitive flag `0x10000` has a separate acceptance branch. During major `2/3`,
input bit `8` or faster-fall substate `0x1F` skips grounding on it. Other
state/phase gates can also skip it. This establishes a selectively passable
surface contract; its player-facing surface name is not established here.
`FUN_00249D70` further classifies selected attributes and can decline ordinary
grounding; its hit-specific fall/recovery consequences remain in
[Hit response](../combat/hit_response.md#response-exits-contact-stages-and-downed-handoff).

An upward collision changes the vertical displacement to the ceiling hit delta
minus fighter height and halves positive vertical speed. After the probes,
ordinary motion uses the auxiliary distances to correct under-floor or
over-ceiling overlap, unless the current major-8 attack record carries
`+0x10 & 0xC0000`. It also performs a final movement-segment query with mask
`0xE0000000`; a hit applies its positional correction and approaches directional
speed to zero with factor `min(1,0.25 * +0x1AC)`.

### Surface-axis movement and special character gate

Running state `0x0E` calls `FUN_0022DB10`. Axis `1` with more than three
held-direction updates becomes axis `2` or `3`, offsets position by
`0.75 * scaled_width` horizontally and `0.25 * scaled_height` vertically,
and enters `(1,0x12)`. Aerial `FUN_0022DC10` additionally requires side flags
`+0xBB0 & 0x100` before selecting a rotated axis and entering surface state
`0x12` or `0x13`. These are state/attribute-gated paths, not general free-axis
movement.

The surface motion handler `FUN_0022E320` approaches smoothed input with ground
acceleration for `0x12`, snaps speed to zero for `0x13`, and brakes for `0x14`.
`FUN_0022D6C0` checks a projected surface segment through `FUN_001BF100` using
mask `0x40000001`; a missing hit is treated as attribute `0x100`, and a hit
requires its `0x100` attribute to retain eligibility. The transition handler
`FUN_0022DD60` routes missing eligibility, changed input, side contact, release,
and descriptor completion to stop, detach, or ordinary running/falling.

`FUN_0022E5D0` resets the low two axis bits. Requested detach additionally
offsets X by half scaled width away from axis `2/3`, publishes ordinary facing,
and clears grounded. A changed-direction detach from surface state `0x13`
can enter `(2,0x1B)` with a fixed-height-`100` impulse and set primary action
cursor to `1`; this deliberately skips the normal zero-event jump impulse.
It is distinct from the fixed-height-`300` ordinary wall-jump event path.

For Kazekage Gaara (`59`) and Deidara (`64`), `FUN_0024A660` reads byte
`+0x63` bit `0x20` before clearing contact flags. When set, ordinary physics
mode `0` subtracts gravity from the magnitude of a downward speed and then
restores its sign, suppressing a sign reversal; positive speed is likewise
clamped at zero after gravity would make it negative. It also forces the final
ground flag outside major `2` and uses an additional 40-unit downward probe
offset. Its controller lifetime and movement dispatch are joined below;
animation presentation is not established by these static consumers.

Final world-component-`+0x38` limits are independent of stage profile:
`FUN_0024A660` caps it at `3000` when byte `+0x61` bit `0x80` is clear, clearing
positive vertical speed, and clamps it at `-500` with grounded set and zero
vertical speed. The Gaara/Deidara gate clamps at `-460` outside majors `5/6`.
The next request pass at height at most `-500` enters native recovery `(6,0x61)`
unless already in recovery `0x61/0x62`. The native stage boundary and floor-line
services are separately documented in [Stages](stages.md#boundary-and-floor-profile-data);
they are not established as the source of every movement probe.

### Gaara and Deidara marker lifetime and ordinary dispatch

**Confirmed observations:** the movement gate is the controller's awakened
marker, rather than either character's separate variant byte. Its producers,
associated effects, and cleanup are owned by
[Awakening](../characters/awakening.md#per-fighter-dispatch), with character variants in
[Deidara and Gaara character variants](../characters/awakening.md#deidara-and-gaara-character-variants).
`FUN_0020D910`, `FUN_0020D030`, `FUN_0020E280`, `FUN_0020DD20`, and
`FUN_0020DDC0` join those owners to this exact consumer:
ordinary entry sets `+0x63 & 0x20`; Deidara also has the effect-presence adoption
route. Association reconciliation and controller suppression can clear it.
The paired `0x10` cleanup does not clear `+0x988` or either actual speed.
Consequently marker removal is not itself a full movement reset.

The exact ordinary trigger gate is `(major,substate,phase) = (0,3,2)`,
`+0x956 == 0`, and secondary-timeline predicate
`FUN_002118A0(fighter+0x1DC,selector)` with selector `0` for Gaara and `6`
for Deidara. The bytes of their descriptor rows at resident
`0x005C1C3C/0x005C1C50` establish flags `0x10/0x11`; Deidara's additional
bit `1` admits the adoption path. The shared substate-`3` row at BTL live
`0x0089AEC8` names `ACT_PRV_0` through string pointer `0x0089A890`.
This is an exact retail descriptor identity, not a player-facing name inferred
from the trigger. The predicate and insertion/reconciliation details remain
in [Awakening's raw state predicate](../characters/awakening.md#raw-state-predicate) and
[ordinary controller entry](../characters/awakening.md#ordinary-controller-entry).

`FUN_00214A40` explicitly clears the marker with byte mask `0xDF` during
construction. `FUN_0024A660` instead preserves it through contact masks
`0x7F/0xBF` and its later low-bit cleanup; `FUN_0024DA50` clears only byte
`+0x63` bit `0` at its tail. The ordinary state-change routine
`FUN_00217E40` has no direct marker store. These inspected paths establish a
retained controller state across ordinary movement updates and state changes,
not a per-pass flag or a fixed frame duration. Effect lifetimes and other
controller exits remain in
[Controller exit and reconciliation](../characters/awakening.md#controller-exit-and-reconciliation).

The placement of the consumers is exact. With fighter root bit `+0x00 & 2`
set, `FUN_0024DA50` runs `FUN_0020E280` before testing pause count `+0x20C`.
Only the unpaused branch then calls altitude consumer `FUN_0020EAE0`, movement
wrapper `FUN_0024CFD0`, and animation advancement, in that order. Thus the
controller can reconcile or clear the marker even on a pass whose movement is
paused. `FUN_0024A660` samples the ID/marker predicate once on entry, before
clearing ground and side-contact bits.

`FUN_0020EAE0` writes vertical speed and the one-pass gravity multiplier using
the same ID/marker predicate. Its held-up/down control accepts major `1`, or
major `0` with substate `0/4`; majors `6/8` skip the whole altitude adjustment.
The remaining admitted states take its neutral approach-to-zero path. The
authored float records, input-sector interpretation, and exact altitude
arithmetic belong to
[Awakening's command-input bridge](../combat/action_commands.md#logical-mask-translation).
The movement consequence is that `+0x998/+0x9B4` are prepared immediately
before displacement is constructed, while the sampled marker independently
changes mode-`0` gravity and contact behavior. `FUN_00248EC0` also uses the
marker to bypass its ordinary held-up entry to `(0,3)` and held-down entry to
`(0,4)`. Its later jump-input branch remains outside those bypasses.

The additional downward probe subtracts `40` from the query endpoint and adds
`40` back to the accepted hit-point displacement. It does not add a constant
40-unit displacement when the query misses. Primitive attribute `0x10000` is
rejected by this marker path at the later acceptance gate. After integration
and the world-height clamps, the pass updates grounded count `+0xB9A` and
entry-contact history `+0xB9C`; only afterward, at
`0x0024C10C..0x0024C138`, it forces `+0x63 & 0x80` when major is not `2`.
**Inference from this ordering:** a forced final ground bit alone does not
prove that the count/history recorded an actual floor contact on that pass.
The forced bit and the contact counters must be interpreted separately.

These are independently gated mechanisms: controller marker, associated
effect, character variant byte, physics selector, and surface-axis bits.
Their separate consumers do not establish that every combination is reachable.

## Special physics selector and return to ordinary motion

**Confirmed observations:** `FUN_0021BC40(fighter,mode)` stores halfword
`+0x988`. It snapshots current vertical speed to `+0x9B0` for modes `1/2`,
and clears that auxiliary speed for modes `0/3/4`. The shared movement pass
does not automatically clear the selector after one update. The multiplier
`+0x9B4` has the separate one-pass contract described above.

| Selector | Exact shared consumer contract |
| --- | --- |
| `0` | Ordinary side, auxiliary floor/ceiling, and direct vertical contact; ordinary gravity, with the Gaara/Deidara marker branch described above. |
| `1` | Keeps side and auxiliary queries but skips direct vertical contact. While ungrounded, applies unit-multiplier gravity to `+0x998`, clamps a negative result to zero, and separately applies gravity to saved speed `+0x9B0`. |
| `2` | Keeps side and auxiliary queries but skips direct vertical contact. While ungrounded, approaches actual vertical speed to zero with factor `min(1,0.25 * +0x1AC)` and the usual `0.1` snap, while gravity advances `+0x9B0`. |
| `3` | Skips the initial side/auxiliary/direct contact block. While ungrounded, applies unit-multiplier gravity to actual speed, then branches directly to final integration, bypassing multiplier reset and later overlap/segment corrections. |
| `4` | `FUN_0024CFD0` first snaps both actual speeds to zero and clears transient vectors. The shared pass still admits the ordinary contact block; its ungrounded gravity switch has no mode-`4` branch. A concrete producer is unresolved. |

Mode `1/2` therefore distinguishes the visible/integrated speed from a
separately gravity-updated saved speed. No restoration of saved speed is
implied by the setter. All rows still reach final world-height limits and
contact bookkeeping. Mode `3`'s early integration branch is conditional on
the recomputed ground bit being clear; it is not an unconditional return from
the whole function. Instructions `0x0024B440..0x0024B65C` establish selector
dispatch and the distinct mode-`3` continuation.

### Selected producer and reset boundaries

The bounded resident halfword-store search for immediate offset `0x988`
found 27 instruction sites after memory aliases were folded; all lie in
`FUN_00214A40`, `FUN_0021BC40`, `FUN_00230A70`, `FUN_00234DA0`,
`FUN_002426C0`, `FUN_00243040`, `FUN_00243920`, `FUN_00243EF0`,
`FUN_0024D830`, or `FUN_0024ED40`. The corresponding immediate-offset
halfword search in `BTL.BIN` returned no matches. This establishes these
direct stores, not the absence of wider, displaced-base, or computed writes.
It is not an unrestricted character-callback audit.

Construction and native placement explicitly clear selector and saved speed;
their contracts are retained below. Ordinary neutral entry `FUN_00226F10`
only reaches selector cleanup through `FUN_00243EF0` when `+0xB00 != 0`.
The inspected running preparation/exit and landing exit helpers have no
selector store. `FUN_00217E40` calls old-state cleanup and requested-state
preparation before its same-state early return, but contains no universal
selector reset. **Inference:** a selector reset must be attributed to its
specific producer/cleanup contract, rather than to the mere fact that the
fighter entered neutral, running, jumping, or landing.

`FUN_00230A70` clears `+0x988/+0x9B0` only when `+0xB00 == 0`.
`FUN_00234DA0` conditionally selects mode `1` and snapshots vertical speed,
or selects mode `0` and clears saved speed, from its action-row motion gate.
Their response-specific meanings are owned by
[Hit response](../combat/hit_response.md); they are not ordinary jump producers.
The exchange writers `FUN_00243040/FUN_00243920` select modes `1/2`
and later clear both fighters in their completion phases. Their direct
dispatcher `FUN_0023BAC0` requires a nonnull current action record, gives
`+0xB00 & 3` priority for the first writer, and otherwise selects the second
when `+0xB00 & 0xC` or `& 0x30` is nonzero. These physics writes therefore
have an exchange-state gate independent of the Gaara/Deidara marker.
`FUN_00243EF0` clears both selectors only inside its outer test that at least
one fighter's `+0xB00` is nonzero; `FUN_002426C0` supplies additional targeted
clear paths. Exchange admission and choreography belong to
[Combat action execution](../combat/combat_action_execution.md#continuation-and-common-exit-decisions)
and [Action commands](../combat/action_commands.md#mode-bit-producers-and-progress-interval-lifetime).
`FUN_002424E0` reaches this cleanup before returning to neutral/fall when its
terminal argument is nonzero, its own recovery substate is `0x61/0x62`, or
the paired fighter is in major `6`. Recovery preparation `FUN_00235100`
for `0x61/0x62` and neutral preparation `FUN_00226F10` call cleanup only
when their own `+0xB00` is nonzero. These are concrete conditional exit
contracts, rather than a universal selector reset on interruption.

The only direct reference reported to `FUN_0021BC40` is
`FUN_00216EA0`, which passes the paired fighter and literal mode `3` at
`0x00216F70..0x00216F78` while installing the Ultimate Jutsu sequence owner.
Its inspected caller `FUN_00244F80` establishes the connected current-record
route; the complete admission and presentation belong to
[Ultimate Jutsu](../characters/ultimate_jutsu.md#start). `FUN_0024ED40` explicitly clears that paired
fighter's selector and saved speed on its state-`1` continuation before its
later ordinary-state handoff (`0x0024EFB0..0x0024EFB8`). Its failed-precondition
branch at `0x0024ED54..0x0024ED88` clears sequence fields `+0x14..+0x20`
and returns without a fighter-selector store. **Bounded observation:** that
local branch is not the normal state-`1` reset; its reachability after a live
mode-`3` entry and any surrounding cleanup remain unresolved. This is not
evidence of a universal interruption cleanup or a mode-`4` entry.

Contact handling itself retains `+0x988`: ordinary accepted ground contact
can replace `+0x9B0` with pre-contact vertical speed and clear actual speed,
while final world-height clamps clear actual speed without clearing the
selector. Construction and placement are the proven reconstruction/reset
stores examined here; the wider rebuild and isolated-participant-removal
ordering remain with [Battle lifecycle](../session/battle_lifecycle.md) and
[Battle entities](../session/battle_entities.md). Open leads are wider/computed selector
or marker writes, a concrete mode-`4` producer, restoration consumers of saved
speed beyond these selected paths, and combined-mode reachability. No named
authored action is assigned to an untraced producer.

## Initialization, history, and descriptor lifetime

Construction initializer `FUN_00214A40` clears physics mode `+0x988`, input
duration `+0x98A`, all three direction/facing halfwords, actual and input speeds
`+0x994/+0x998/+0x99C`, and auxiliary vertical speed `+0x9B0`. It initializes
gravity multiplier `+0x9B4` and dimension scale `+0x2F0` to `1`, clears the low
three axis/wall-jump bits of `+0x9B8`, clears contact history `+0xB9A..+0xB9F`,
and sets all three probe distances to the unavailable sentinel. This is a
construction contract; it is not evidence that neutral action entry repeats
the entire initializer.

Native fighter-placement virtual entry `FUN_0024D830` calls BTL live
`0x00708FD0` with shared field `+0x28` and side `+0x60 & 1`, passing position
`+0x30` and orientation `+0x40` as outputs. It stores returned section at
`+0x9F6`, sets byte `+0x61` bit `0x40`, snaps both actual speeds to zero,
clears auxiliary speed and physics mode, initializes direction/facing from
the sign of `+0x48`, clears retained hit record `+0xE54`, fills eight vec4
position-history entries at `+0x840..+0x8BF`, and enters neutral through
`FUN_00217E40`. The independently traced section and spawn data are owned by
[Stages](stages.md). Per-update maintenance `FUN_0024C440` separately snapshots
position at `+0x970..+0x97F` and directions/contact side at `+0x980..+0x986`;
its paired geometry consumer is in
[Target selection](../combat/target_selection.md#paired-opponent-and-geometry-refresh).

Major/substate changes reset primary cursor block `+0x1B8`, then BTL live
`0x0071EEF0` sets phase `+0x192` to zero and resets secondary block `+0x1DC`.
The ordinary descriptor phase consumer is BTL live `0x0071F160`, whose complete
body is displayed as `FUN_0071F120`. It reads the current eight-byte phase row,
advances phase for its condition, and reports completion when the new row's
animation index is `-1`. All ordinary jump impulse variants `0x18..0x1D` and
landing `0x26` have one animation-end condition (`s16 +2 == -0x10`) followed
by that sentinel; running `0x0E` and ordinary fall `0x1E` instead have condition
zero and retain their phase. Ordinary completion therefore depends on the
animation or contact handler, not a universal number of elapsed frames.

The impulse event predicate `FUN_002118A0` queries a timeline crossing; it does
not consume or clear the event. Its fractional and rate behavior belongs to
[Timer primitives](../../runtime/timer_primitives.md#event-and-interval-predicates).
State change, pause gating, animation completion, environment contact, and
per-pass multiplier reset must be kept distinct when interpreting elapsed
motion updates.

## Confidence and evidence limits

**High static confidence:** the shared state and field contracts, complete
ordinary descriptor interval, all record-level ranges, jump arithmetic, native
placement stores, surface-axis transitions, integration/contact/gravity order,
exact limit constants, marker/altitude scheduling, final-ground-bit ordering,
and the selected selector producer/cleanup contracts. The integration disassembly spans
`0x0024A660..0x0024C188`; the first/second impulse instructions are at
`0x0022FC90..0x0022FD08` and `0x0022FE64..0x0022FF70`.

**Bounded interpretation:** retail `RUN/JMP/FAL/LND` names and the observed
input/contact transitions support the ordinary locomotion labels above. The
selectively passable surface and the IDs `59/64` movement branch remain described
by their exact predicates; the flag's controller ownership is established,
but no additional animation or player-facing mode name is inferred. Low-input running
was established in the shared consumer; a distinct animation presentation or
special callback remains a separate question.

**Analysis limitation:** instructions `0x0021B730..0x0021B7CC` of
`FUN_0021B730` contain selector branches and `v0` assignments whose direction
conversion is not established; this document relies on actual stores in the
movement callers instead. Missing direct references are not treated as
evidence that a computed caller or character override cannot exist.
