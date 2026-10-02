# Battle AI

This document owns reverse-engineering knowledge about the battle AI of retail
NA2 (`SLPS-25837`): controller ownership, lifecycle, configuration, target and
spatial inputs, action selection, state dispatch, logical-input synthesis,
direct action queues, and random-number use. State names and physical button
meanings are deliberately not invented where the binary only establishes raw
IDs or masks.

The findings below are static unless explicitly described otherwise. The
resident and BTL files are identified in
[Retail game file identities](../../game/files/file_identities.md).

## Research coverage

- **Assigned scope:** the retail NA2 (`SLPS-25837`) battle AI in `BTL.BIN`:
  controller ownership, decision/action dispatch, difficulty and configuration
  inputs, primary and alternate target selection, state transitions, directly
  established RNG use, and lifecycle boundaries. Resident `SLPS_258.37` was
  followed only where needed to prove the BTL caller, settings accessors,
  random generator, command bridge, direct-action queue consumers, and selected
  numeric character-exception admission paths.
- **Exploration depth:** exhaustive within bounded assets: all 43 dispatcher
  entries at live `0x008C3810`; all direct BTL writes to state word `+0x34`;
  all 12 direct calls to the action-record selector and all 14 to resident
  queue `FUN_0021D380`; all 167 aligned RNG-wrapper calls in the live AI
  cluster `0x006F0000..0x00706500`; all 40 parameters of the six selectable
  Strength rows and the unselectable seventh row; the `10 x 40` secondary
  modifier matrix; the six-row phase table; the 96-entry per-character and
  descriptor tables; and the 74 resident calls to the shared tick. Bounded
  structural tracing covered the main tick, initializer, target refresh,
  spatial classifier, route planner, alternate-target producers and consumers,
  the three world-object searches, the state-18 guard helper, the settings
  loader/apply path and COM toggle, the fighter-list scheduler, command bridge,
  and queue admission/consumption. The opening planner, state-14, main, and
  opponent-support reactions, both incoming-action reactions, the scripted
  Practice tail, the post-dispatch path, descriptor/profile address paths, both
  profile-installation copies, and selected numeric-exception admission paths
  were followed in aligned instruction bytes. Four character wrappers were
  compared instruction by instruction; other large reaction helpers were
  decoded only far enough to establish state writes, profile consumers, RNG
  sites, target/route effects, and direct queues.
- **Confirmed coverage:** resident virtual-method ownership and same-update
  command consumption; the two static AI slots and their cross-side
  initialization behavior; native Practice settings and six Strength profiles;
  deterministic primary-opponent binding; ordered, random-gated alternate
  target sources; the complete dispatcher and direct constructor map; selector,
  resident queue, and four-category queue lifecycle; the continue-screen
  modifier input and the continue-choice labels that increment it; the AI's
  use of the shared resident RNG, its phase cursors, tables, and audited call
  sites; the single direct Confirm-branch caller of settings apply; the
  per-pass command-triple clear that precedes the AI tick; and the absence of
  a recovered session override separating that clear from fighter updates.
  The world-object searches have distinct ordering and distance rules,
  including an unreachable kind-2 resource check in the radius search. State
  18's guard gates, Practice override, and two random-gated departures are
  established separately from the remaining unnamed reaction branches. The
  recovered sequence establishes decision-stage precedence, effective Strength
  threshold transformations, own-side versus opponent-support arbitration,
  scripted-Practice candidate producers and priority, post-dispatch command
  clearing, descriptor-bit consumers, and numeric character exceptions. It
  also establishes profile-24/31 installation and transformation without
  decision consumers, retention of a scripted `+0x126` value across a
  non-reinitializing switch to COM, the working-row gate on ID-36 indices
  4..6, and conditional resident transitions into ID-49 action 34.
- **Unresolved or untested:** player-facing names for most raw states and
  action-record classes; exhaustive semantics for every branch of the large
  decision/reaction helpers; the role of the seventh profile row and profile
  parameters 24 and 31; consumers or meanings for descriptor bits
  `0x02/0x40`; an ordinary-mode positive producer of slot `+0x126` beyond the
  established retention path; complete entry conditions and move names for
  the recovered numeric character exceptions, including which configured
  `+0x188` selection ([Action commands](../combat/action_commands.md#action-table-source-and-setup))
  makes ID 36's indices 4..6 available in a given match; the player-facing
  name of the setup mode that bypasses the secondary modifier; and whether an
  unrecognized alias can write the session's first-phase filter and separate
  fighter updates from command clearing. These are recorded as negatives or
  hypotheses rather than inferred names.
- **Deliberate exclusions and overlap:** Adventure, substitution, damage
  formulas, frame timing, camera projection, media, and localization are
  excluded. Shared contracts are owned elsewhere:
  [Action commands](../combat/action_commands.md) (logical masks, command bridge, and
  action-table setup); [Practice mode](../modes/practice_mode.md) (settings rows, apply
  order, and dummy-status bridge);
  [Pause and replay](pause_and_replay.md#selective-update-gating) (update masks
  and session filters);
  [Target selection](../combat/target_selection.md#paired-opponent-and-geometry-refresh)
  (fighter geometry refresh);
  [Combat action execution](../combat/combat_action_execution.md) and
  [Character action callbacks](../characters/character_action_callbacks.md) (action entry
  and per-character callbacks); [Chakra and guard](../combat/chakra_and_guard.md)
  (resources and guard); [Battle support mechanics](../characters/support_mechanics.md);
  [Resident randomness](../../runtime/randomness.md) (the PRNG); and
  [MWo3 overlay ABI](../../runtime/overlay_abi.md) with
  [Retail game file identities](../../game/files/file_identities.md#address-conventions)
  (address mapping).
- **Evidence limitations:** all findings come from static analysis of the
  hashed retail files; no AI runtime trace, live field watch, input replay, or
  probability experiment was run. Execution order, addresses, direct calls,
  tables, and static side effects are high-confidence; player-facing intent and
  timing-sensitive runtime consequences are not established.

## Address convention and overlay mapping

The BTL header, layout, and `0x40` preserved-import shift are owned by
[MWo3 overlay ABI](../../runtime/overlay_abi.md#file-runtime-and-preserved-ghidra-addresses)
and [Retail game file identities](../../game/files/file_identities.md#address-conventions).
This document writes BTL addresses as `D/L/F`:

- `D`: preserved Ghidra/export address (`L - 0x40`);
- `L`: live EE address;
- `F`: byte offset in retail `BTL.BIN` (`L - 0x006B3F00`).

Resident `SLPS_258.37` addresses and absolute BSS addresses are already live
and take no correction. For example, the main tick's instruction at
`D 0x00705320` encodes a call to live `0x006FB840`, whose bytes are the
prologue of preserved `FUN_006FB800`; the preserved export instead labels the
continuation at `D 0x006FB840` as the callee.

## Principal function map

`Preserved symbol` is the export symbol at the real byte entry.

| Role | Preserved symbol | D | L | F |
| --- | --- | ---: | ---: | ---: |
| target-position source selector | `FUN_006F1DB0` | `0x006F1DB0` | `0x006F1DF0` | `0x3DEF0` |
| action-record selector | `FUN_006F2B40` | `0x006F2B40` | `0x006F2B80` | `0x3EC80` |
| ten-step RNG phase gate | `FUN_006F3100` | `0x006F3100` | `0x006F3140` | `0x3F240` |
| route/path planner | `FUN_006F3770` | `0x006F3770` | `0x006F37B0` | `0x3F8B0` |
| neutral/reset helper | unnamed | `0x006F3F40` | `0x006F3F80` | `0x40080` |
| 43-state action dispatcher | `FUN_006FB800` | `0x006FB800` | `0x006FB840` | `0x47940` |
| spatial classifier | `FUN_00702E20` | `0x00702E20` | `0x00702E60` | `0x4EF60` |
| main per-fighter AI tick | `FUN_00704D00` | `0x00704D00` | `0x00704D40` | `0x50E40` |
| AI initializer | `FUN_00705D30` | `0x00705D30` | `0x00705D70` | `0x51E70` |
| self/opponent refresh | unnamed | `0x00706310` | `0x00706350` | `0x52450` |
| settings-object loader | `FUN_00880F70` | `0x00880F70` | `0x00880FB0` | `0x1CD0B0` |
| settings apply | `FUN_00881160` | `0x00881160` | `0x008811A0` | `0x1CD2A0` |
| COM controller toggle | `FUN_008813B0` | `0x008813B0` | `0x008813F0` | `0x1CD4F0` |
| profile UI bound helper | `FUN_00881950` | `0x00881950` | `0x00881990` | `0x1CDA90` |

## Controller ownership and lifecycle

The AI is called by resident per-character fighter wrappers rather than by a
BTL-internal caller. Representative resident `FUN_00250DA0` is installed in a
fighter-class vtable at `0x005DB18C`. Its exact control flow is:

- `0x00250DA8`: load `u16 fighter+0x60`;
- `0x00250DAC..0x00250DB0`: extract `((value >> 5) & 0xF)`;
- `0x00250DB4`: skip the AI call when that nibble is zero;
- `0x00250DBC` (SLPS file `0x150EBC`): `jal 0x00704D40`, preserving the
  fighter pointer in `a0`.

An aligned scan of clean `SLPS_258.37` finds exactly 74 direct `jal` instructions
to `L 0x00704D40` in analogous character wrappers. This broad fan-in establishes
the true ownership boundary: controller nibble zero is the human/no-AI path;
any nonzero value invokes the shared BTL AI tick.

Four spread-out resident wrappers were compared instruction by instruction:
`FUN_00250DA0`, `FUN_0026F930`, `FUN_0029B250`, and `FUN_002EE330`.
Each has the same 14-instruction body, differing only in its own branch address:
extract that nibble, conditionally call the shared tick with the original
fighter pointer, and return zero. None adds a character-specific profile,
command mask, or decision callback. This is a four-wrapper structural sample,
not proof that every other wrapper or later fighter consumer is identical.

The generic caller is resident fighter-list update `FUN_0024FD80` (runtime
`0x0024FD80`, SLPS file `0x14FE80`). For each eligible fighter it loads the
vtable from fighter `+0x50`, loads method slot `+0x1C`, and executes `jalr` at
runtime `0x00250094` (file `0x150194`) with the fighter in `a0`. Eligibility at
that point requires fighter byte `+0x00` bit 1 and `s32 fighter+0x20C <= 0`.
Representative `FUN_00250DA0` occupies exactly that vtable slot and always
returns zero after its conditional AI call.

The scheduler then makes a second eligible-fighter pass. It calls resident
`FUN_00217320` at `0x0025011C` to copy command-controller
`+0xAC/+0xB0/+0xB4` into fighter `+0x338/+0x33C/+0x340`, followed by the
ordinary input consumers. Thus the BTL AI tick synthesizes this update's
command triple before the resident bridge consumes it; there is no extra-frame
queue at this ownership boundary. `FUN_0024FD80` itself is called by resident
`FUN_002504B0` at `0x00250658` (file `0x150758`).

The bridge is also the first resident arbitration boundary. Fighter byte
`+0x61` bit `0x80` or byte `+0x62` bit 0 makes it zero all three fighter-side
outputs and halfword `+0x98A` instead of copying. After a normal copy, if the
mask contains both `0x00001000` and `0x01000000`, it clears `0x01000000`.
Consequently BTL output is proposed input, not an unconditional action; the
resident fighter state can suppress it and this specific mask conflict is
resolved before later consumers.

The Practice settings path controls that nibble. Its rows, keys, value
labels, count table, apply order, and dummy-side selection are owned by
[Practice mode](../modes/practice_mode.md#rows-local-values-and-manager-storage) and
its [dummy-status bridge](../modes/practice_mode.md#dummy-status-bridge). The
AI-facing settings are Status (key `0x0C`), Strength (`0x0B`), Attack
(`0x0D`), Guard (`0x0E`), Move (`0x0F`), Linked Attack (`0x12`), and Extra Hit
Counter (`0x10`). Snapshot child `FUN_00880EF0` calls the settings loader at
`D/L/F 00880F38/00880F78/1CD078`. Apply `FUN_00881160` calls the bridge
`FUN_008813B0` at `D 0x00881310` and `D 0x0088132C`, passing a force flag when
requested Strength `+0x94` differs from the normalized stored key `0x0B`. On
the selected fighter, Manual clears bits 5..8 of `u16 +0x60` with `& 0xFE1F`;
every non-Manual Status installs controller kind 1 with `| 0x20` and calls the
initializer when the old nibble was zero or the force flag is nonzero.

The initializer call is at `D/L/F 00881490/008814D0/1CD5D0` and targets live
`0x00705D70`. Selecting Manual does not clear the static AI state and calls no
destructor or free routine. The next Manual fighter tick simply stops entering
the AI; selecting a non-Manual Status again initializes when the controller
nibble was zero.

Settings apply is reached directly, not indirectly. An aligned raw-JAL scan of
clean BTL finds exactly one call to live `0x008811A0`, at
`D/L/F 008816B4/008816F4/1CD7F4`, in the Practice settings child's input
handler (live `0x00881660`). It runs only on that handler's new-press bit
`0x20` (Confirm) branch; the Cancel branch closes without applying. The AI
therefore sees Practice Status and Strength changes only when the settings
menu is confirmed. The menu's input, staging, and apply ordering are owned by
[Practice mode](../modes/practice_mode.md#confirmapply-side-effects).

No heap allocation, per-AI object constructor, AI destructor, or AI free path
was found: controller state is two static BSS slots.

## Per-side state block

The slots are live BSS and have no file offsets:

```text
side 0: 0x008D6590
side 1: 0x008D6770
stride: 0x1E0
```

The tick chooses the slot from fighter `+0x60` bit 0. Confirmed fields are:

| Offset | Width | Established use |
| ---: | ---: | --- |
| `+0x00` | `f32` | synthesized movement magnitude; copied to command controller `+0xB0` |
| `+0x04` | `f32` | synthesized direction/angle; copied to command controller `+0xB4` |
| `+0x08` | `s16` | refreshed from fighter `+0x326`, the target/facing-side value |
| `+0x0C` | `f32` | refreshed from fighter `+0x32C`, planar opponent distance |
| `+0x10` | `u32` | synthesized logical command mask; copied to command controller `+0xAC` |
| `+0x1C` | pointer | controlled fighter (`self`) |
| `+0x20` | pointer | primary opponent selected from manager `+0xDE4/+0xDE8` |
| `+0x24/+0x26` | 2 `s16` | per-character AI values refreshed each tick from live table `0x008C3460 + character_id*4`; `+0x26` gates alternate-target candidates |
| `+0x30` | `s32` | spatial bucket; the main classifier writes `0..5` |
| `+0x34` | `u32` | current dispatcher state ID, valid dispatch range `0..0x2A` |
| `+0x38` | `s32` | countdown initialized to `90` and decremented by the tick |
| `+0x3C` | `u32` | route/path submode, cleared by reset and planner entry |
| `+0x40..+0x4C` | 4 words | cached controlled-fighter position from the spatial classifier |
| `+0x54` | `s32` | alternate world-object handle; `-1` means absent |
| `+0x58` | `s32` | secondary handle/ID; initialized and reset to `-1` |
| `+0x5C` | `s32` | selector used by target-position source mode 2; initialized to `-1` |
| `+0x68` | `u32` | target-position source mode (`0`, `1`, or `2`) |
| `+0x80/+0x84` | `s32` | initialized from fighter `+0x9F6`; later used in route/platform logic |
| `+0x90` | byte | decision/request-occupied latch; set beside many state transitions, but not equivalent to `state != 0` |
| `+0x94..+0x10C` | 31 `u32` | countdown/cooldown bank; every nonzero entry is decremented each tick |
| `+0xB4` | `s32` | randomized initialization timer, `150 + rand(0..120)` |
| `+0x104` | `s32` | initialized to `120` |
| `+0x110` | `s32` | retry countdown used by state 27; an invalid mode-2 point seeds it to `30` |
| `+0x114/+0x118` | `s32` | initialized to `90` and `60`; both are decremented when nonzero |
| `+0x128` | `s32` | special-action cooldown produced by the action selector and decremented by tick |
| `+0x144/+0x148` | `s32` | mode-2 near/far target deadlines, seeded to `30/210` by its constructor |
| `+0x160..+0x1AF` | 40 `s16` | selected behavior-profile parameters |
| `+0x1B0` | `s32` | first usable fighter action slot among slots 4..9, or `-1` |
| `+0x1B4/+0x1B8/+0x1BC` | `s32` | ten-step RNG phase cursors, initialized to `-1` |

The initializer makes these writes for both slots before applying a profile
only to the selected side:

- zero: `+0x0C`, `+0x30`, `+0x34`, `+0x3C`, `+0x50`, `+0x60`, `+0x64`,
  `+0x68`, `+0x88`, `+0x8C`, byte `+0x90`, all 31 words `+0x94..+0x10C`,
  `+0x11C`, `+0x120`, byte `+0x124`, bytes `+0x125/+0x126`, `+0x128`,
  `+0x144`, `+0x148`, byte `+0x14C`, byte `+0x14E`, halfword `+0x150`,
  `+0x1D0`, and bytes `+0x1D4/+0x1D5/+0x1D6`;
- `-1`: `+0x54`, `+0x58`, `+0x5C`, `+0x1B4`, `+0x1B8`, `+0x1BC`,
  `+0x1C0`, `+0x1C4`, and `+0x1C8`;
- constants: `+0x38=90`, `+0x104=120`, `+0x114=90`, `+0x118=60`, and
  byte `+0x14D=0xFF`;
- fighter-derived: `+0x80` and `+0x84` receive signed fighter `+0x9F6`;
- randomized: `+0xB4 = 150 + FUN_00180210(120)`;
- in Practice manager mode, `+0xAC` is set to `60` unless setting key `0x0C`
  equals 1.

This is the initializer's write set, not a claim that every unknown field has
been semantically identified. Notably, the per-tick output clear owns
`+0x00/+0x04/+0x10`.

The two-slot reset is a cross-side lifecycle effect. Reinitializing either
fighter clears the transient state, handles, source/route submodes, latches,
and cooldowns listed above in **both** static slots, then copies a new profile only into the
selected fighter's slot. It does not clear the unselected slot's existing
`+0x160..+0x1AF` profile row. Thus forcing one COM setting can interrupt the
other side's in-progress AI state without replacing that side's parameters.

The neutral/reset helper at `D/L/F 006F3F40/006F3F80/40080` performs a smaller
current-side reset. It writes `+0x54=-1`, `+0x58=-1`, `+0x34=0`, byte
`+0x90=0`, `+0x3C=0`, `+0x120=-1`, `+0x04=0`, `+0x10=0`, `+0x00=0`,
`+0x94=0`, `+0x9C=0`, `+0xD8=0`, and bytes `+0x1D4/+0x1D5=0`.

The per-character source is a 96-entry table of two signed halfwords at
`D/L/F 008C3420/008C3460/20F560`, ending immediately before the secondary
modifier matrix. The tick indexes it directly with fighter character ID
`+0x68` and performs no local bounds check. In the clean table `+0x24` ranges
from 0 through 3 and participates in state/region reaction choices;
`+0x26` ranges from 0 through 90 and is used only as the inclusive-100-roll
threshold in the mode-1 and mode-2 alternate-target searches described below.

## Main tick and output boundary

`FUN_00704D00` first selects current and opposite side indices from fighter
`+0x60` bit 0. It then:

1. returns immediately if outer-graph global `0x00607654` is null;
2. calls resident `FUN_00216820`, which returns the value reached through
   `0x00607654 -> +0x08 -> +0x14`; a nonzero value resets the current AI slot
   and returns;
3. when request latch `+0x90==1` but state `+0x34==0`, resets the inconsistent
   slot and continues;
4. refreshes self, opponent, facing-side, and planar-distance fields;
5. returns unless fighter byte `+0x61` bit `0x08` is set for both self and
   opponent, or when resident `FUN_001EC290()` reports the nonzero
   timeout/end-reason marker at `0x00607674`;
6. decrements the state countdowns and cooldown bank;
7. hot-reloads the base profile in Practice mode when manager key `0x0B`
   changes;
8. clears `+0x00`, `+0x04`, and `+0x10`;
9. runs the spatial classifier and scans fighter action slots 4..9;
10. runs the decision stages, state dispatcher, and post-dispatch reactions;
11. commits the logical output triple to the fighter's command controller.

The returns in steps 1, 2, and 5 branch to the epilogue before both the output
clear and final command-controller stores. Step 2 clears the internal slot via
the reset helper first; the null-graph, inactive-fighter, and terminal-marker
paths do not.

These early returns do not leave the previous update's command triple in
place. The AI's command controller is the fighter's own `ccCommand` input
object: battle setup live `0x00709480` stores each input object at its
fighter's `+0x24` and the fighter at the input's `+0x20` (stores at live
`0x0070951C/0x00709520` for side 0 and `0x00709540/0x00709544` for side 1).
The `ccCommand` update at live `0x006F0EA0` passes a suppression flag to the
logical translator whenever that fighter's controller nibble (`+0x60` bits
5..8) is nonzero, and the translator (live `0x006EFDC0`) then stores zero to
`+0xAC/+0xB0/+0xB4` at live `0x006EFE18..0x006EFE20` instead of translating
the pad. The AI never needs to clear the controller itself for this reason.

The ordering is fixed by the resident phase dispatcher `FUN_001F03E0`. The
four-part battle owner built at live `0x00709240` holds `ccCommandCtrl` at
`+0x04` and `ccPlayerCtrl` at `+0x08` (constructor `FUN_0024E0B0` at live call
`0x00709350`; the class table `0x005D9FC0` names RTTI `ccPlayerCtrl`, and its
slot `+0x0C` is fighter-list update `FUN_002504B0`, the caller of
`FUN_0024FD80`). In the first phase the dispatcher updates owner `+0x04`
before owner `+0x08`. For a COM fighter, one pass is therefore: zero the
triple, run the AI tick, and copy the triple to the fighter in the bridge. An
early AI return leaves zeros, which the bridge copies as no input.

This guarantee holds when both phase bits run together. Owner `+0x04` runs
when allowed-mask bit `0x0002` is set or auxiliary byte `+0xA50==1`; owner
`+0x08` runs on bit `0x0004`. Every suppression producer documented in
[Pause and replay](pause_and_replay.md#proven-btl-suppression-writers)
allows or suppresses those two bits together, and the `+0xA50` override
suppresses the fighter phase while allowing the command phase.

Session-local filters `+0x06/+0x08` further restrict those masks: each final
allowed mask is `~suppression & session_filter`, with `FUN_001F0290` reading
the filters at `001F0304/001F0308`. Mask construction, the `0xFFFF` filter
reset, and the second-phase setter at `001EC620` are owned by
[Pause and replay](pause_and_replay.md#controller-fields-and-mask-construction)
and its [session-local override writer](pause_and_replay.md#session-local-override-writer).
That setter writes only filter `+0x08` and changes only bit `0x10`, so it
cannot change the first-phase `0x0002/0x0004` relationship. The recovered
resident and BTL references to session pointer `0x00607604` (through accessor
`FUN_001EC2F0`, `001EC2F0/0EC3F0`, and direct `gp-0x33EC` loads) contain no
writer to first-phase filter `+0x06`, so no recovered session override
separates first-phase command clearing from fighter updates. An indexed or
otherwise unrecognized pointer alias is not excluded.

The principal decision-call sequence in live naming is:

```text
FUN_00702E60                     spatial classifier
FUN_006FFEC0
FUN_00703170 / FUN_00703A70      mode-dependent
FUN_00703D20
FUN_006FDF30
FUN_006FF410                     one mode path
  or FUN_006FE720 + FUN_006FEAC0 another mode path
FUN_006FB840                     43-state dispatcher
FUN_006FF9C0                     mode-dependent post-dispatch stage
```

Two boundary helpers in that sequence are established structurally, without
move names:

- Pre-dispatch `D/L/F 006FFE80/006FFEC0/4BFC0` detects two paired transient
  fighter-state patterns: both actors at `+0x190` value `0x5B/0x5C`, or self
  `+0xA3C==0x13` with both actors' `+0x9BA/+0x9BC` equal to 3. When one is
  present and cooldown `+0x104` is zero, an inclusive `0..100` roll below
  profile parameter 25 resets the AI state and ORs logical mask `0x1000`;
  failure sets `+0x104=5`. Outside those patterns, self `+0xB10==2` with an
  expired `+0x104` resets, selects quotient `0..2` from
  `FUN_00180210(29)/10`, and calls resident `FUN_00245D90(self,quotient)`.
  The adjacent `+0xB10==4` path refreshes route-region fields `+0x80/+0x84`.
- Post-dispatch movement/environment correction
  `D/L/F 006FF980/006FF9C0/4BAC0` runs only in ordinary modes or Practice
  Status COM, and only when output direction mask `+0x10 & 3` is nonzero. It
  clears byte `+0x1D6`, scans the same-region object list rooted at the object
  manager's `+0x14`, and predicts self X movement using fighter radius
  `+0x994 * 3` plus an object radius. A predicted overlap can set latch
  `+0x90`, OR mask `0x00010000`, and set `+0x1D6=1`; under the alternate raw
  fighter gates (`+0x998<0`, `+0x1C4>10`) it instead selects state 10 and ORs
  `0x00020000`. A separate object-flag path within distance `900` writes a
  target region to `+0x80`, selects state 8, and sets the latch. This is an
  environmental correction of an already synthesized direction, not primary
  opponent selection.

The mode gates around that sequence are also exact:

- `FUN_006FFEC0` always runs after the classifier/action-slot scan. Resident
  `FUN_00247D30` at runtime/file `00247D30/147E30` is exactly a load of signed
  fighter halfword `+0xB10`; a positive value skips the remaining decision and
  dispatch stages and goes directly to output commit. Because output fields
  were already cleared, only commands synthesized by the prepass can survive
  on this path.
- `FUN_00703170` and `FUN_00703A70` run in non-Practice modes. In Practice
  (`manager+0x0C==3`) they run only for Status COM (`key 0x0C==1`).
- `FUN_00703D20` and `FUN_006FDF30` run on every path that reaches the main
  decision sequence. `FUN_00703D20` itself ends with the sole direct call to
  the Practice-specific stage `D/L/F 00702460/007024A0/4E5A0`, at call site
  `00704CD0/00704D10/50E10`; that stage returns immediately outside Practice
  or for Status COM.
- Practice with scripted Status Stand/Jump/Double-jump (`key 0x0C=2..4`) next
  runs `FUN_006FF410` only. All ordinary modes, and Practice Status COM,
  normally run `FUN_006FE720` then `FUN_006FEAC0`; the one exception is
  Practice Linked Attack frequent/random (`key 0x12==2`), which substitutes
  `FUN_006FF410`.
- The dispatcher then runs. `FUN_006FF9C0` runs after it in ordinary modes and
  for Practice Status COM, but is skipped for scripted Practice Status values.

Exact main-tick call sites are:

```text
callee          D          L          F
FUN_00702E60    0070500C   0070504C   05114C
FUN_006FFEC0    007050B8   007050F8   0511F8
FUN_00703170    00705144   00705184   051284
FUN_00703A70    0070514C   0070518C   05128C
FUN_00703D20    00705154   00705194   051294
FUN_006FDF30    0070515C   0070519C   05129C
FUN_006FF410    007051CC   0070520C   05130C
FUN_006FF410    00705274   007052B4   0513B4
FUN_006FE720    00705284   007052C4   0513C4
FUN_006FEAC0    0070528C   007052CC   0513CC
FUN_006FB840    00705320   00705360   051460
FUN_006FF9C0    00705394   007053D4   0514D4
```

The Practice-only `FUN_007024A0` consumes the scripted-dummy controls in the
order described under [Scripted-Practice reaction priority](#scripted-practice-reaction-priority).

The final output stores are exact:

| Operation | D | L | F |
| --- | ---: | ---: | ---: |
| load `self` from slot `+0x1C` | `0x0070572C` | `0x0070576C` | `0x5186C` |
| load command controller from `self+0x24` | `0x00705730` | `0x00705770` | `0x51870` |
| store slot `+0x10` to controller `+0xAC` | `0x00705738` | `0x00705778` | `0x51878` |
| store slot `+0x00` to controller `+0xB0` | `0x00705740` | `0x00705780` | `0x51880` |
| store slot `+0x04` to controller `+0xB4` | `0x00705748` | `0x00705788` | `0x51888` |

BTL contains the class string `ccCommandCtrl`, and the human command-controller
paths use the same `+0xAC/+0xB0/+0xB4` representation. The AI therefore owns a
logical command source rather than a separate fighter-motion executor. Some AI
paths also queue action-record indices directly through resident
`FUN_0021D380`; the two dispatch mechanisms coexist.

### Decision priority and ordinary-plan replacement

The opening planner is `D/L/F 00703130/00703170/4F270`; its complete
instruction body ends at live `0x00703A64`. It returns immediately when byte
`+0x90==1`. Otherwise it saves the old state, clears `+0x34`, and chooses a
replacement. This differs from the later reaction stages: they can replace a
state while that byte is already set. The latch is therefore a gate for
specific stages, not a global first-decision-wins lock.

The planner's ordered choices are:

1. If self X lies outside its region bounds, an expired `+0x94` is reloaded
   to `60`; a parameter-20 roll and resident `FUN_0023BEE0(self)==1` can
   select state 10 and set the latch. The function then continues through its
   remaining checks, rather than returning at that write.
2. In spatial buckets 0/1, expired `+0xAC` is reloaded from parameter 32.
   Absolute actor/target `+0x38` separation below `200` gives a parameter-14
   state-11 attempt; separation at least `200` instead gives a state-10
   attempt followed by a state-28 attempt if the first roll fails. Each selected
   branch sets latch `1`, seeds `+0x94=30`, and returns; state 10 additionally
   clears route submode `+0x3C`. Both state-10/state-28 rolls use parameter 14.
3. For a nonzero spatial bucket, expired `+0x9C` is reloaded from parameter
   32. Parameter-10 success either selects state 11 in the nearby/small-height
   case, or copies the primary target position, sets source mode 0, and calls
   the route planner. A nonzero route result becomes state 5 only if resident
   `FUN_00307610(target)==0`; otherwise the slot resets. Parameter-10 failure
   selects state 1, sets latch `1`, and loads `+0xD8` from parameter 34.
4. In bucket 0 with absolute `+0x38` separation at most `200`, raw RNG modulo 20
   sends results `0..5` to a state-11 attempt gated by expired `+0x9C`.
   Results `6..19` clear the state, set latch `1`, and seed `+0x94` from
   parameter 32; when the saved old state was 7, this path first calls facing
   correction. The six-pointer table is `D/L/F
   008C38B0/008C38F0/20F9F0`, and all six entries are live `0x0070399C`.

The next stage, `D/L/F 00703A30/00703A70/4FB70`, first calls the Extra Hit
Counter selector and `FUN_00700190`, then applies its own reactions, calls
`FUN_007004B0`, and finishes with two additional state-11 checks. Its
parameter-9 branch selects state 14, resets the slot, and deliberately clears
the request latch. The branch requires target `+0x95A!=0`, target action class
other than 6, bucket 0, and either absolute `+0x38` separation below `20` or
both fighters in classes 2/3. A failed parameter-9 roll can instead pass a
parameter-14 roll, reset, and write output mask `0x1020`. These alternatives
are followed by `FUN_007004B0`, so their state/output effects are still subject
to that later helper. The final checks use self class 0/action ID 8 with
parameter 4, or target action ID 3/4 with parameter 14 while state is 0/1;
success writes state 11, latch `1`, and `+0x94=60` or `30`, respectively.

### Main reaction stage and later rewrites

The complete main reaction body is `D/L/F
00703CE0/00703D20/4FE20..50E30`; the effects below come from its aligned
instruction bytes. The body begins by
resetting states 2/3/4/24/26 **only when self class `+0x18E` is 5**. Scripted
Practice Status values then jump directly to the Practice-specific tail
`FUN_007024A0`. Ordinary modes and Practice COM run the following ordered
families before that tail:

| Live branch range | Established gates and effects |
| --- | --- |
| `703E98..703F2C` | Self class 8, self `+0xB00==0`, current-record `+0x14 & 0x380`, pointed `+0xA50` word bit `0x10`, and expired `+0xBC`: parameter 11 success resets, selects state 12, and sets the latch; failure reloads `+0xBC=60`. Both outcomes continue. |
| `70404C..70429C` | `FUN_0022D5B0(target)==1`, state 0/1/5, and target `+0x9F0==0` use `trunc(parameter14/2)` as the first threshold. Surviving branches can select states 10, 25, 5, or 1. A separate target-class-8/different-region branch uses the same half-parameter threshold to select state 25. |
| `7042A0..7043E0` | Bucket 2, state 0/1, and target current-record word `+0x10 & 2`: a first fixed threshold 50 chooses between an `+0xAC`/parameter-14 state-10 attempt and an `+0xD4`/parameter-29 state-18 attempt. The cooldowns reload before their respective second rolls, from parameters 32 and 3. State 18 also sets latch `1` and `+0x94=90`. |
| `7043E4..704488` | Self action ID `+0x190==0x5D`, state other than 15: a roll is made before checking `+0xB8`; when that cooldown is zero it is reloaded to 150. Results below 30 select state 33, results 30..59 select state 15, and 60..100 select neither. A selected state resets first, sets latch `1`, and seeds `+0x94=150`. This branch jumps past the remaining main reactions to the final current-action check. |
| `704490..7046CC` | Target class 8, state 0, bucket below 3, self region equal to self `+0x324`, and the target-facing/X comparison: normally reset into state 11 with `+0x94=30`. The target-ID-36 exception described below uses a parameter-22 state-6 attempt and a later parameter-5 state-18 attempt; the latter can overwrite state 6 in the same pass. |
| `7046D0..704844` | Call `FUN_00701140`; with expired `+0xB0`, scan the linked object list for raw kind 2 in self's region, distance below 900, and signed `+0x1F8 != -1` and `<30`. Parameter 29 success selects state 8, sets latch `1`, seeds `+0xB0=120`, and writes route-region field `+0x80` from the self-region-zero condition. Enumeration continues, so there can be additional rolls during the same scan. |
| `704858..704958` | Self class 5, parameter 19, `FUN_002118A0(target+0x1B8,1)==1`, clear latch, and expired `+0x94` can select state 35 with timer 30. States 11/14 then separately consult `FUN_00307610(target)`; result 1 resets first, and parameter 14 success selects state 25, sets latch `1`, and timer 30. |
| `70495C..704CA0` | Call alternate-target stage `FUN_00701BD0`. Only with byte `+0x124==0` and state 0/1 does the `FUN_00701ED0()==0` path roll `0..60`: results 0/1 call facing correction; 2/3 attempt the parameter-22 short-history movement mask `0x40000` after a position-validity check; 4/5 attempt state 22 using parameter 20; 6..14 can select state 21 when bucket is at least 3, the 12.0 affordability check fails, and `+0xDC` is zero; 15..60 select none here. The six-entry table is `D/L/F 008C38D0/008C3910/20FA10`. |
| `704CA4..704D10` | Call `FUN_006FD2D0`, then inspect self current-record word `+0x10 & 0x200`. With expired `+0xBC`, parameter 11 success calls resident `FUN_0021DDB0(self)`; either outcome sets `+0xBC=60`. Finally call the scripted-Practice tail. |

In the small `0..60` selection, the state-22 attempt reloads `+0x94` to
`12+rand(0..3)` and `+0xDC` to `300+rand(0..150)` even when its parameter-20
roll fails. The state-21 branch instead seeds `+0x94=38+rand(0..30)` and
`+0xDC=210+rand(0..150)`. Thus an attempted branch can impose a later retry
delay without successfully changing the state.

Resident `FUN_0022D5B0` is exactly `(fighter byte +0x9B8 & 3) > 1`. The main
stage uses it for both fighters, including direct low-bit-2/3 facing corrections
paced by `+0xF0=70`. This predicate is kept numeric: its body does not name a
player-facing condition. The ordinary-mode self-predicate/state-0-or-1 path
ORs mask 8 and returns before all later main-stage reactions; it still returns
to the main tick's subsequent decision stages and dispatcher.

The following `D/L/F 006FDEF0/006FDF30/4A030` stage provides further evidence
that later writes have precedence. After its entry predicate and early facing
return, the ordinary reaction branch converts states 21/22 to state 25 before
its distance/reaction logic. The conversion is at live
`0x006FE224..0x006FE244`; it does not require a clear request latch.
Its later branches can select states 9/17/34/11/20. Consequently a main-stage
constructor for state 21 or 22 does not, by itself, prove that its dispatcher
handler runs on that same update. The linked/reactive stages still follow this
stage before dispatch, and their own gates must also be considered.

### Final support-dependent arbitration

The two final ordinary-mode stages inspect different support owners. Main-tick
stores at live `0x00704D78..0x00704D8C` write the current side to
`gp-0x5EB8` and the opposite side to `gp-0x31F4`. The active-object accessor
`D/L/F 00886710/00886750/1D2850` returns
the pointer stored at `support_manager + 4 + supplied_side*4`, or null when
the manager is absent.
`FUN_006FE720` supplies the current side; `FUN_006FEAC0` supplies the opposite
side. Thus the former schedules an own-side request, while the latter reacts
to the **opponent's** active support object. The support object's general
lifecycle remains owned by [Battle support mechanics](../characters/support_mechanics.md).

`D/L/F 006FE6E0/006FE720/4A820` seeds `+0xF4` from parameter 38 plus an
inclusive roll bounded by that parameter. After its availability and context
gates, parameter 21 success selects state 38 and clears the request latch.
The support-selector and Practice handshake details are owned by
[Practice mode](../modes/practice_mode.md#linked-attack-and-extra-hit); they are not a
second general Strength selector. State 38's latch can consequently be clear
when the following reaction stage starts.

The complete opponent-support reaction is `D/L/F
006FEA80/006FEAC0/4ABC0..4B504`. Its entry and common gates are established
from the full instruction body:

- A null opponent support clears the latch for existing states 39..42 and
  returns. It leaves those state IDs intact.
- An existing support must pass live `FUN_0088B980(object,0)`. That helper
  compares absolute Y separation from the fighter opposite object side byte
  `+0xE4` and requires it to be below `50`; its parameter zero selects that
  fighter. It does not test X or the AI's planar-distance cache.
- When cooldown `+0xF8` is zero, the stage clears the latch; otherwise an
  already-set latch makes it return. It also returns for support reason byte
  `+0xE6` outside `0..2`, or self action class 8. Support selector 4 requires
  raw Strength at least 4 before the remaining branches.
- The stage measures self-to-support and self-to-opponent planar distances
  through resident `FUN_001806F0`. With opponent distance at most `250`,
  parameter-14 rolls and resident fighter predicates can select state 11 or
  10 and return before the support-range branch.

Inside support range `object float +0x130`, reason 2 and selector 4 form a
distinct direct-queue path. Parameter 28 first gates the attempt. If object
halfword `+0x114==0`, the AI corrects facing toward the support and calls the
action selector with distance to that support, mask `0xFFF0FFFF`, category
range `1..1`, and directional gate enabled. A valid index, self outside
classes 5/6, and parameter-14 success reset the slot and queue that index
through resident `FUN_0021D380`. Failed selection falls into an expired-
`+0x94`, parameter-10 state-5 attempt; a rejected attempt resets and returns.
This is the selector/queue pair at live `0x006FEED4/0x006FEF3C` already
listed in the direct-queue census.

The other branches establish the state-39..42 constructors precisely:

| Opponent-support context | Profile gate and result |
| --- | --- |
| Inside range, reason 2, selector other than 4, expired `+0xD4` | Reload `+0xD4=parameter33`, `+0xF8=90`; parameter 5 success selects state 40, sets latch `1`, and `+0x94=60`. Failure returns. |
| Same reason/selector, `+0xD4` nonzero, expired `+0xFC`, affordable `1.0` | First seed `+0xFC=1+rand(0..parameter30)`. Parameter 1 success selects state 39, sets latch `1`, `+0xF8=30`, and `+0xFC=parameter3`; failure replaces `+0xFC` with another short roll. Either outcome returns. |
| Inside range, reason 0/1, object `+0x114==0`, live `FUN_008890D0(object)==1`, expired `+0xAC`, self-support distance at most `250` | Set `+0xAC=32`, `+0xF8=30`; parameter 14 success selects state 42, sets latch `1`, and `+0x94=30`. |
| Same availability branch after `+0xAC` becomes nonzero, expired `+0xA0`, live `FUN_008891E0(object)==0` | Set `+0xA0=30`, `+0xF8=30`; parameter 8 success selects state 41, sets latch `1`, and `+0x94=30`. |
| Outside range, reason 1, self-support distance at most `400`, object `+0x114==0`, expired `+0xA0` | Seed `+0xA0/+0xF8=30`; parameter 8 plus `FUN_008891E0(object)==0` selects state 41 with latch `1` and `+0x94=30`. |

The live `FUN_008891E0` predicate is exactly `object word +0x368 != 0`.
Other inside/outside-range branches can select state 34 using parameter 28 or
state 6 using parameter 22, and set their own cooldowns before returning.
These returns are branch-local priority boundaries: the full support stage is
not an unconditional state overwrite. Its result is what reaches the shared
dispatcher on the ordinary path.

### Incoming-action reactions and effective Strength gates

Two complete bodies were followed through all their branches: live
`FUN_007004B0..0x00701138` (called from the state-14/reaction stage) and
`FUN_00701140..0x00701BC4` (called from the main reaction stage). Both can
replace already selected states. Their entry, profile transformations, and
departure priorities are established; player-facing names for the raw action
and object types remain unresolved.

`FUN_007004B0` clears slot byte `+0x125` each pass. It combines the primary
opponent's current action with attack-object queries from the live
`FUN_00777780/007777F0/00778550` family. AI helpers
`D/L/F 006F1380/006F13C0/3D4C0` and
`006F1690/006F16D0/3D7D0` inspect attack-shape records, rather than inventing
a second primary opponent. The first scans indices `0..31` and all exposed
shape records, projecting their center by a direction-dependent `0.9*radius`
and testing planar distance against cached self radius plus `1.8*shape_radius`.
The second returns raw classification `0/1/2`, with extra kind-specific
distance checks; kind `0x2D` accepts outside buckets 4/5, kinds `3/0x0B/0x35`
use `800`, and kind `0x3A` uses `500`. These are attack-object kinds, not
fighter character IDs. Broader payload ownership is outside this AI document.

The reaction magnitude starts at parameter 5. Exact target current-record
word `+0x10` values `0x10000/0x20000` select parameter 6; values
`0x100000/0x200000/0x400000` select parameter 7. Those latter values also
reduce the separate parameter-1 threshold to `cvt.w.s(0.8*parameter1)` unless
self `+0x6C - target +0x6C <= 0.5` and self `+0x6C <= 0.7` both hold.
An attack-object overlap or the 32-index scan can instead select parameter 6
and set `+0x125=1`. The exact-equality tests must not be replaced by bit tests.

After facing/shape and character-distance gates, the reaction's priority is:

1. With expired `+0x98` and an affordable `1.0`, scale the current parameter-1
   threshold with the signed action-record scalar returned by
   `FUN_006F1060`, compare the inclusive roll, and on success reset into state
   20, set the latch, reload `+0x98` from parameter 3, and skip the next
   reactions. Failure seeds a short retry at
   `+0x98=(parameter30+1)+rand(0..parameter30+1)`.
2. The alternate self-byte-`+0x63` bit-7 branch seeds `+0x108=15+rand(0..15)`
   and `+0x10C=60+rand(0..60)`; parameter 22 success resets into state 6.
3. Otherwise the selected parameter-5/6/7 magnitude feeds the ten-step phase
   helper. A true phase result **or** a surviving nonzero classification
   reaction flag resets into state 18 with latch `1` and `+0x94=30`.
4. With expired `+0xD0`, reload it to 90 and compare a further roll with
   `trunc(selected_magnitude/3)`. A resident mask-`0x02000000` index lookup
   other than `-1` resets into state 23. Thus the phase-selected state 18 can
   be replaced before returning.
5. A separate expired-`+0xE8`, parameter-29 gate calls `FUN_006FD970`.
   Finally, when `+0x125==0` and state is 18/20, current target-record and
   spatial branches can replace that state with 16/10/25/5/28, clear output,
   or reset. The target-ID-49/action-index-34 exception takes this reset path.

The record-scalar transform uses EE `adda.s` followed by `madd.s`: its float
is `base + base*scalar`, then converted with `cvt.w.s` before the roll.
The scalar helper reads signed byte `+0x1A` of the target's current action
record in class 8. Values `-3..3` map to `-0.5,-0.3,-0.1,0,0.1,0.3,0.5`
through the seven-pointer table at `D/L/F 008C3730/008C3770/20F870`;
other values, a missing record, or another class return zero. This is an
action-dependent threshold adjustment, not an extra random draw. The same
transform is used for parameter 1 in `FUN_006FDF30` and parameter 2 in
`FUN_00701140`.

`FUN_00701140` clears `+0x124` before querying resident
`FUN_00222DF0(self,550.0)`. That helper delegates to a closest matching
collision-registry lookup with side-specific masks, then rejects two raw
object cases. The AI marks `+0x124` directly for returned subtype `+0x7A`
in `{0x24,0x25,0x26,0x29,0x2A,0x2E,0x33}`; other objects are queried again
with radius `450` for type `+0x78` 12/25 or `250` otherwise. With a marked
candidate and state other than 20, it applies the type-based resident predicate
and compares a roll as a float with **`1.9*parameter5`**, before subsequent
eligibility, resource, cooldown, and subtype decisions. This float comparison
is distinct from the integer phase-gate consumer of parameter 5.

The parameter-2/scalar state-20 attempt reloads `+0x98` from parameter 3
before rolling. If it does not select state 20, type 25 selects state 8.
Other types require expired `+0xCC`: the listed subtypes reset and can select
state 34 below planar distance 450 or state 8 farther away; subtype `0x4B`
has additional parameter-29, opposite-X-side, and 400-unit separation gates
before selecting state 5 plus mask `0x10000` or state 10. The default subtype
path chooses state 10 with parameter 13 when self's region matches
`+0x324` and opponent planar distance is at most 500, except subtype `0x2B`;
otherwise it selects state 18 and `+0x94=60`. These are collision-object
subtypes, not new AI character identities.

### Scripted-Practice reaction priority

The full tail is `D/L/F 00702460/007024A0/4E5A0..4EF54`. It returns outside
Practice or for Status COM, clears all three candidate bytes
`+0x124/+0x125/+0x126`, then calls the Extra Hit Counter selector. A return
value of 1 there terminates the tail before Guard, movement, or attack choices.
The settings transaction and option architecture remain owned by
[Practice mode](../modes/practice_mode.md).

Guard Yes with equal actor/target region collects three distinct candidate
flags: `+0x124` from resident `FUN_00222DF0(self,550.0)`; `+0x125` from the
opponent's 32 attack-object indices or its separate queried attack object;
and `+0x126` from the opponent support reason `+0xE6==2`. The 32-index path
requires a self-region match, with raw attack kind `0x8B` using its own region
predicate. The separate attack object is ignored when its property bit 4 is
set. If self is outside action classes 7/8 and either target is class 8 or
one of those candidate flags is set, the tail resets into state 18, sets latch
`1`, seeds `+0x94=30`, and returns. It therefore outranks the jump/attack
choices below; it does not make every dispatcher guard state unconditional.

Move Follow can maintain or construct state 5 with source mode 0 and a primary-
target route. Several surviving route paths return before scripted jumping or
attacking. Status Jump/Double-jump then preserves state 18, resetting other
states before consulting `+0x114`. Both require that countdown to be zero and
self outside classes 7/8. Double-jump on self class 0 selects state
36 with `+0x114=18`; when self is class 2 and action ID is
`0x18/0x22/0x24`, it selects the same state with timer 90. Jump selects state
36 with timer 90 without those Double-jump-specific class/action branches.
These state writes are at live `0x00702C38`, `0x00702C84`, and
`0x00702CA0`; the state's dispatcher resets and emits mask `0x10000`.
After reaching the expired-countdown jump branch, the tail returns before
Attack even when no Double-jump class/action combination selected state 36.

Status Stand resets an existing state-5 route when Move is not Follow.
When the tail reaches Attack, a value other than No requires expired `+0x118`
before selecting state 37. The class-2/3 branch additionally checks negative fighter `+0x998`,
`+0x1C4>=11`, and state outside 28/37/5; the other branch requires state 0.
This establishes where the scripted-dummy gates enter the same dispatcher and
why their priority cannot be reconstructed from the menu's option values alone.

### Post-dispatch output replacement

Dispatch is followed by additional state and output writes before publication.
In ordinary modes and Practice COM, the environment helper runs first, then
the main tick inspects self action ID `0x15/0x16`. With state 0 and source
mode 0, an inclusive roll uses fixed threshold 50 when per-character field
`+0x24` is 0/1/2, or 30 otherwise. Success resets, optionally emits `0x1000`
when `+0xC8` is zero, selects state 11, sets latch `1`, and timer 30, then
reloads `+0xC8=60`. The branch is live `0x007053DC..0x00705528`. Since the
dispatcher already ran, this newly selected state is not dispatched again in
the same tick; only the directly written output can be published immediately.

The next object-property path is live `0x0070552C..0x007055E0`, using the
previously queried attack object. Property bit `0x80` plus slot `+0x128!=0`
resets the AI and writes object `+0x13C=2`. Property bit `0x100` resets the
AI **before** rolling against parameter 27; success writes object `+0x13C=1`,
but failure still leaves the reset's output clear in effect. Both bits can be
processed on one object. Thus the parameter-27 path can discard an already
dispatched command even when its random gate fails. Scripted Practice bypasses
this entire post-dispatch block at live `0x007053CC` and proceeds to the paired-
AI check and final publication.

The paired-AI state-5 reset described in the RNG section runs after those
branches and before the three final stores. When its random choice selects the
current side, its inline reset clears the current outputs; when it selects the
opposite side, that side's internal slot is cleared. The code does not rerun
either dispatcher. This ordering limits what can be inferred from a successful
state constructor or dispatch call alone.

### Character descriptors and hard-coded exceptions

The character descriptor flag byte is live
`0x008C3052 + character_id*4`, independently of the per-character two-halfword
table. Reading all 96 descriptor records establishes the flag sets below. A
bounded whole-BTL search for aligned `addiu ...,0x3052` finds four formations,
at `D/L 006F9EC8/006F9F08`, `0070039C/007003DC`,
`00704B2C/00704B6C`, and `00706128/00706168`; each was followed through
its surrounding branch. An alternative base-plus-offset or aliased reader is
not excluded by this search.

| Descriptor bit | Established consumer | Character IDs carrying the bit |
| --- | --- | --- |
| `0x01` | Initializer multiplies parameter 16 by `1.2`. | `1..6,12..15,17,22,34..38,46..57,63..65,67,68,70,73,75,80,85,87,90..93` |
| `0x04` | Initializer multiplies parameter 8 by `1.2`. | `13,66` |
| `0x08` | Initializer multiplies parameter 24 by `1.2`; all selectable raw rows have zero there. | `6,60,65,72,86` |
| `0x10` | Two state-22 constructors and one suppression gate described below. | `5,7,16..19,46,58,59,61,62,64,67..71,77..84,87,89,91,92` |
| `0x02` | Present in the table; no meaning assigned by these four readers. | `12,76` |
| `0x40` | Present in the table; no meaning assigned by these four readers. | `10,11,39..43,85` |

These are current fighter-ID reads and initializers, not proof of selectable
roster status or named awakening behavior. Representative contrasts are ID 57
with flag `0x01`, ID 58 with `0x10`, ID 64 with `0x11`, IDs 13/66 with the
parameter-8 multiplier, and ID 73 with `0x01`. The descriptor's first halfword
can be `0xFFFF` even while its flag byte is nonzero, including IDs 46 and 59;
that halfword does not justify discarding the flag reads. Character-name and
selection evidence remains in [Character identity in battle](../characters/character_ids.md).

Computed accesses in aligned BTL text bytes through `D 0x0088F5BC`, following
`lui`/low-address formations, register addition, shifted indices, and loads
covering the descriptor range, also lead only to the four byte readers above.
Each reaction reader masks `0x10`; the initializer uses only `0x01/0x04/0x08`.
No recovered reader copies the whole descriptor byte into an AI slot or passes
it to a further helper for `0x02/0x40` interpretation. No literal pointer to
table start `L 0x008C3050` or flag start `L 0x008C3052` was found in the
whole-program byte search. This narrows the open question to an unrecognized
address/pointer path or data without a recovered consumer; it does not name
either bit or prove universal non-use. The profile-side copied and computed
accesses are detailed under
[Computed profile copies and unresolved parameters](#computed-profile-copies-and-unresolved-parameters).

Bit `0x10` has three recovered action-stage effects:

- In state-11 helper `FUN_006F9B20`, the target-class-6/action-ID-`0x5D`
  path can pass a parameter-20 roll, require self byte `+0x63` bit 5 clear,
  and then require descriptor bit `0x10`. Success writes state 22, latch `1`,
  timer `12+rand(0..3)`, and cooldown `300+rand(0..150)`; this helper also
  directly writes direction mask 4 after that construction.
- In `FUN_00700190`, target class 6 reaches a parameter-20 attempt after its
  earlier state-7/state-11/facing branches. The same self-bit-5-clear and
  descriptor-bit-`0x10` gates construct state 22 with those timer ranges.
- The main reaction's `0..60` results 4/5 branch blocks its state-22 attempt
  when descriptor bit `0x10` and self bit 5 are **both** set. The descriptor
  alone does not block it; unlike the two preceding constructors, the ordinary
  attempt also does not require that descriptor bit to be present.

Hard-coded target IDs additionally override reaction geometry:

| Location | Numeric exception and consequence |
| --- | --- |
| `FUN_007004B0`, live `70092C..700AB8` | In its no-shape-classification branch, target IDs `{4,57,64}` require cached planar distance `<=650`; `{35,48,53,60,73}` use `<=800`; `{18,19,39,47,54,61,77}` use `<=1200`. Other IDs use spatial bucket below 3. These gates precede the parameter-1/scalar and phase reactions; they are not profile-row changes. |
| `FUN_006FDF30`, live `6FE2D0..6FE354` | Target IDs 59/64 with target byte `+0x63` bit 5 set take a special expired-`+0x94`, parameter-10 state-9 attempt. That branch stores a context-dependent distance at slot `+0x64` and bypasses the general nearby state-17/state-34 choices. |
| `FUN_00703D20`, live `704590..7046CC` | Target ID 36 with current action index `+0xA3C` in `{4,5,6,21,22}` diverts the otherwise state-11 facing/X reaction. It resets, seeds `+0x94=60`, can select state 6 using parameter 22 when `+0x10C` is expired, reloads `+0x10C=60+rand(0..60)`, then independently attempts state 18 with parameter 5. It always finishes this branch with handle `+0x54=-1` and latch `1`. |
| `FUN_007004B0`, live `700D70..700D8C` | Target ID 49 whose resident current-action-index accessor returns 34 takes the reset/departure branch instead of the remaining class-8 record reaction. |

The supplied static bodies establish these numeric differences, including
representative IDs 57, 64, and 73. They do not establish the move names behind
those action indices, the reason the author chose each threshold, or that every
listed combination is reachable in retail play.

### Numeric-exception admission and working records

The selected exceptions were followed beyond the AI's numeric comparisons.
ID 36's resident definition at `0x00476B70` counts 37 action records and
points to `0x00475F30`; ID 49's definition at `0x004B2110` counts 49 and
points to `0x004B10D0`. Every selected index below is inside its counted
`0x54`-byte source array:

| Target ID / index | Authored resident record | Word `+0x10` | Float `+0x20` |
| --- | --- | --- | ---: |
| 36 / 4 | `0x00476080` | `0x00100000` | 5 |
| 36 / 5 | `0x004760D4` | `0x00200000` | 10 |
| 36 / 6 | `0x00476128` | `0x00400000` | 15 |
| 36 / 21 | `0x00476614` | `0x00000001` | 0 |
| 36 / 22 | `0x00476668` | `0x00000001` | 0 |
| 49 / 34 | `0x004B1BF8` | `0x02000000` | 0 |

These source rows alone do not prove that their types remain enabled in the
fighter's working array. Common setup `FUN_00219620` retains only one index
among 4..9 according to the configured selection in fighter halfword `+0x188`
and zeroes record word `+0x10` for the others; that setup, the
selection-to-slot table, its derived-field helpers, and the later slot-4..9
rewrite by `FUN_002449C0` are owned by
[Action commands](../combat/action_commands.md#action-table-source-and-setup). Through
the common action-start path, ID 36's indices 4/5/6 therefore need the
configured selection that retains them (values `0/1/2`): a zero type word is
rejected. The AI's index comparison does not itself test this selection, so
this gate does not exclude a different current-index writer. Nonzero authored
words are insufficient admission evidence. Indices 21/22 and ID 49's 34 are
outside this zeroing range. Shared record layout and general execution remain
in [Character assets](../../game/character_assets.md#action-records) and
[Combat action execution](../combat/combat_action_execution.md#action-entry-and-state-ownership).

**Positive conditional route for ID 49:** its definition's callback-table
pointer is `0x004AC720`, whose slot 2 contains `FUN_00283A70`. Callback
dispatch is owned by
[Character action callbacks](../characters/character_action_callbacks.md#evidence-convention-and-ownership);
the current indices involved here exceed 3 and therefore take no
configured-provider remapping. When the current-action accessor returns 33
or 43, fighter phase `+0x192` is 2, and `FUN_002118A0(fighter+0x1DC,0x12)`
reports the cursor event, this callback calls `FUN_0023A9A0(fighter,34,0)` at
resident `0x002848C4` or `0x00284E84`, respectively. The marker query is a
cursor crossing/event check; the constant alone is not proof of elapsed frame
18.

For record 34 as installed by common setup, the generic start path's
`0x00F00000` prerequisite is absent: classifier `FUN_00244190` returns
`0xFFFFFFFF` because type mask `0x000F0000` is zero, and `FUN_0023A9A0`
accepts that result. Its zero `+0x20` also bypasses the later nonzero-cost
branch, so the start stores current index 34 at `+0xA3C` through the common
class-8 entry. Accessor `FUN_00217860` remaps only indices 0..3
([Combat action execution](../combat/combat_action_execution.md#character-execution-callbacks)),
so it returns 34 unchanged. This proves a conditional entry route, not every
antecedent needed to reach actions 33/43 and their phase-2 cursor event.

The callback re-evaluates the current index after that entry. Its index-34
path can immediately request action 35 or enter class 6/substate `0x5F`,
depending on the retained fighter fields. Thus a producer of index 34 does
not by itself prove that an AI tick subsequently observes that index.

The AI exception itself requires candidate `+0x125==0`, existing AI state
18 or 20, target class 8, ID 49, and accessor result 34 at
`D 00700CF4..00700D4C`. It branches to the reset at `D 00700FC8` before
the remaining class-8 record checks. This changes a concrete branch outcome:
record 34's type `0x02000000` lacks bit `0x08`, so the subsequent general
record path would otherwise end without that reset. After resetting, the
helper still checks the Practice override and can select state 11 through
its ordinary near-bucket/parameter-14 departure. Later decision stages can
replace that result under the established precedence. ID 49 also has type
`0x02000000` at authored index 35; this equality does not include index 35
in the exact-index-34 exception.

**Remaining admission limits:** this establishes the working-row gate for
ID 36 and a concrete conditional producer for ID 49's index 34. It does not
establish which configured `+0x188` selection a given match uses for ID 36,
complete entry paths for all
five of its selected indices, every context behind the other numeric
geometry/bit-5 exceptions, or move names from these raw words.

## Primary target and spatial classification

The self/opponent refresh is called from the main tick at
`D/L/F 00704DB8/00704DF8/50EF8`. It writes:

```text
slot+0x08 = *(s16 *)(fighter+0x326)
slot+0x0C = *(f32 *)(fighter+0x32C)
slot+0x1C = fighter
slot+0x20 = manager+0xDE8 when fighter+0x60 bit0 == 0
            manager+0xDE4 when fighter+0x60 bit0 == 1
```

Thus ordinary one-on-one target ownership is deterministic: every tick the AI
independently binds the opposite manager fighter. It does not search a fighter
list, consult reciprocal fighter `+0x20`, or use RNG to choose its primary
fighter target.

The source fields are written by resident geometry refresh `FUN_002174A0`,
owned by [Target selection](../combat/target_selection.md#paired-opponent-and-geometry-refresh):
fighter `+0x326` is the target/facing side and `+0x32C` the planar opponent
distance. The AI's cached `+0x0C` is therefore specifically planar opponent
distance.

The spatial classifier at `D/L/F 00702E20/00702E60/4EF60`, called at
`D/L/F 0070500C/0070504C/5114C`, caches current position at slot
`+0x40..+0x4C` and writes slot `+0x30`:

- equal fighter `+0x324` and `+0x9F6` indices: bucket `0` at distance `<=150`,
  `1` at `<=250`, `2` at `<=400`, and `3` above `400`;
- higher or lower target index: bucket `4` or `5`;
- buckets below `3` are forced to `3` when the absolute `+0x38` position
  component difference exceeds `400`.

The facing-correction helper at `D/L/F 006F1B20/006F1B60/3DC60` compares the
primary target and current X coordinates with fighter `+0x98C`. A wrong-facing
right case writes angle `-pi/2`, mask `1`, magnitude `0`; wrong-facing left
writes `+pi/2`, mask `2`, magnitude `0`. These are raw logical mask values, not
yet mapped to named controller buttons.

## Alternate target-position sources and path states

Primary fighter ownership remains fixed, but navigation can request a position
from three sources through slot `+0x68`. Live `FUN_006F1DF0` selects:

- mode `0`: copy four words at primary opponent `+0x30..+0x3C`;
- mode `1`: resolve alternate world-object handle slot `+0x54` through resident
  `FUN_00376610` and `FUN_00375760`;
- mode `2`: look up a record selected by slot `+0x5C` through live BTL
  `FUN_006F1D00` (`D/F 0x006F1CC0/0x3DE00`) and copy its first four words.

Direct calls to this source selector are at
`D/L/F 006F37BC/006F37FC/3F8FC` and
`006F67E8/006F6828/42928`.

Both alternate modes have direct producers:

- live `FUN_006FC480` (`D/F 006FC440/48580`), the first world-object search
  described below, supplies the mode-1 handle, vector, and region. Its sole
  direct call is live `0x00701C60` inside
  `FUN_00701BD0` (`D/L/F 00701B90/00701BD0/4DCD0`). That caller requires state
  0/1, an expired slot `+0x94`, and profile-parameter-28 success; it then
  resets, sets active, writes source mode `1` and state `24`, and invokes the
  route planner. State 27 independently calls live `FUN_006FC7F0(120.0)`
  (`D/F 006FC7B0/488F0`), which can populate the same handle/vector/region
  fields before that handler writes mode `1`, state `24`, and plans a route.
- live `FUN_006FCE00` (`D/F 006FCDC0/48F00`) is the direct mode-2 constructor.
  With slot `+0xA8` expired and profile-parameter-0 success, it walks every
  region and both point lists exposed by live `FUN_00708E10/00708E40`. A
  candidate must pass its validity test, the same exact
  `rand(0..100) < slot+0x26` gate, and be closer to self than to the primary
  opponent. It likewise retains the first passing point in region/list order;
  manager stage byte `+0x98==0x16` explicitly excludes region index 0 from one
  of the two point lists. Success resets the slot,
  sets active, source mode `2`, state `26`, stores the flattened point index at
  `+0x5C`, the point at `+0x70..+0x7C`, and its region at `+0x80`, then invokes
  the route planner. Planner success restores state `26` and sets
  `+0x144=30`, `+0x148=210`; no candidate sets `+0xA8=60`. Its sole direct call
  is `D/L/F 00701D54/00701D94/4DE94` in `FUN_00701BD0`, which is itself called
  from the main decision stage at `D/L/F 0070491C/0070495C/50A5C`.

`FUN_006F1D00` enumerates those same two point lists in the same region-first
order and returns the record at flattened index `+0x5C`. This closes the
mode-2 producer/consumer chain; the cached vector is a planning input, while
the flat index is what lets later target refresh find the live record again.

The three world-object searches share enumeration through resident
`FUN_00375840(manager,-1)`, `FUN_00375800(manager,index)`, and
`FUN_00375760(manager,handle,record)`. The latter reaches live BTL
`FUN_0070C350` (`D/F 0070C310/58450`), which writes the record's kind byte at
`+0x00` through resident `FUN_003765B0(object byte +0x61)`, copies the object's
four-word position from `+0x20` to record `+0x10`, and copies object word
`+0x08` to record `+0x20`. The searches require a region-bound match through
`FUN_006FC360` (`D/F 006FC320/48460`), then cache that position and record
word `+0x20` in slot `+0x70..+0x7C` and `+0x80`. The kind numbers below are
raw record values; their player-facing object names are unresolved.

Each search returns zero immediately if slot handle `+0x54` is already
different from `-1`. Their candidate-selection rules differ:

| Helper D/L/F | Candidate rule and stopping condition |
| --- | --- |
| `006FC440/006FC480/48580` | Skip kind `7`; require `rand(0..100) < slot+0x26` and strictly smaller planar distance to self than to the primary opponent. Retain the first passing candidate. A failed random/distance gate sets slot `+0x94=90` and continues enumeration. |
| `006FC7B0/006FC7F0/488F0` | Skip kind `2`; require planar distance to self strictly below the supplied radius. Retain the first eligible candidate without RNG or an opponent-relative comparison. State 27 supplies radius `120.0`. |
| `006FCA90/006FCAD0/48BD0` | Require kind equal to the argument and distance strictly below the supplied limit. Each accepted candidate lowers the limit to its own distance. Stop at the first accepted candidate at distance `<=400.0`; otherwise retain the closest accepted candidate encountered before enumeration ends. No RNG is used. |

The third search's sole direct call is
`D/L/F 0070239C/007023DC/4E4DC` in live `FUN_00701ED0`, with kind `2` and
initial limit `3000.0`. A nonzero search result takes that caller's success
return without a new source-mode/state-24 write there. On zero, the caller
selects state `21`, sets request latch `+0x90=1`, and seeds `+0x94` with
`rand(0..30)+38` and `+0xDC` with `rand(0..60)+150`. Thus this helper's stored
handle alone does not establish that its caller starts mode-1 navigation.

The shared kind-specific gates can terminate the entire search rather than
skip only the current candidate. For kind `2`, either resident
`FUN_00306420(self,10/11)==1` or `FUN_00225940(self,5.0)==1` returns zero.
The latter is an affordability predicate, so an affordable `5.0` check rejects
this path. For kind `3`, the search returns zero when
`FUN_00375A60(world,AI-side)` returns an object for which live
`FUN_0070FC80` returns one. Resource formulas belong to
[Chakra and guard](../combat/chakra_and_guard.md).

The three physical affordability call sites are
`D/L/F 006FC670/006FC6B0/487B0`,
`006FC978/006FC9B8/48AB8`, and `006FCC64/006FCCA4/48DA4`. The middle call
is unreachable on the recovered radius-search enumeration path: its earlier
kind-2 branch at `D/L/F 006FC860/006FC8A0/489A0` jumps to the next candidate,
and intervening calls receive the position vector, not the kind byte. It must
not be counted as another executable kind-2 selection path merely because its
instruction remains in the function.

The route planner at `D/L/F 006F3770/006F37B0/3F8B0` clears `+0x3C`, resolves
the requested target source and current actor region, and writes raw dispatcher
states:

- state `3` when actor and target resolve to the same region or a stage-specific
  direct case applies;
- state `4` when distinct regions require route fields to be populated;
- state `5` or `0` when a target/region cannot be resolved, depending on the
  stage and fighter-state gates.

These are structural meanings only and do not imply player-facing move names.

Their consumers establish more precise structural labels. State-3 helper
`D/L/F 006F7E30/006F7E70/43F70` compares actor region with target region
`+0x80`. A region mismatch emits the corresponding vertical/region-transition
logical masks; in the same region it drives left/right movement toward cached
target X at `+0x70`, using output magnitude `1.0` and angle `+/-pi/2`, and
returns to state zero at its distance/height completion gates. State-4 helper
`D/L/F 006F6360/006F63A0/424A0` consumes the planner's segment indices,
segment interpolation, and route phase fields to synthesize traversal input;
when no active segment remains it delegates to the same direct-position helper.
State-5 helper `D/L/F 006F53D0/006F5410/41510` runs that route executor, then
copies the primary opponent's live `+0x30..+0x3C` position to slot
`+0x70..+0x7C` and its `+0x9F6` region to `+0x80`, replans when the route or
region changes, and restores state 5 plus latch `+0x90` on a surviving path.
Thus states 3, 4, and 5 are respectively direct target-point motion,
route-segment traversal, and moving-primary-target route maintenance. Those
are code-level roles, not player-facing action names.

The two alternate-source dispatcher consumers close their lifecycle loops:

- State-24 helper `D/L/F 006F4BD0/006F4C10/40D10` first resolves mode-1
  handle `+0x54`; failure resets immediately. It runs the shared route
  executor, replans against cached target vector `+0x70..+0x7C` and region
  `+0x80` whenever execution returns the dispatcher state to zero or the actor's current route
  region changes, and resets if replanning cannot produce a state. A surviving
  pass explicitly restores state 24. Thus the handle is validated each tick,
  not trusted indefinitely.
- State-26 helper `D/L/F 006F4220/006F4260/40360` re-resolves flattened point
  `+0x5C` through `FUN_006F1D00`. A missing point resets; one invalidated-point
  condition also clears `+0x5C`, selects state 27, seeds retry `+0x110=30`,
  and sets latch `+0x90`. Within planar distance `115` and the target region,
  it enters direct facing/action logic under deadline `+0x144`; a vertical
  separation above `100` can ask resident `FUN_0021DF60` for mask-8 action and
  queue it when no action is pending. Outside that near case, deadline
  `+0x148` expires to reset; otherwise the shared route executor runs and the
  route is rebuilt when its region identity changes. A surviving pass restores
  state 26 and the request latch. The constructor's `+0x144=30` and
  `+0x148=210` writes are therefore active near/far lifetimes, not unexplained
  constants.

## Action-state dispatcher

The dispatcher loads slot `+0x34` at `D 0x006FB828`, rejects values above
`0x2A`, and jumps through a 43-entry table. The table bytes are at
`D/L/F 008C37D0/008C3810/20F910`. Every raw entry is a live handler pointer;
the preserved handler bytes are pointer minus `0x40`.

In the table below, `reset` means live `FUN_006F3F80`; `actor` and `target`
mean slot `+0x1C` and `+0x20`. Masks remain deliberately numeric.

| State | Handler D/L/F | Directly established behavior |
| ---: | --- | --- |
| `0` | `006FC30C/006FC34C/4844C` | shared return; no action |
| `1` | `006FB854/006FB894/47994` | reset when slot `+0xD8` is zero |
| `2` | `006FB9E4/006FBA24/47B24` | call live `FUN_006F6080`: reset if target X is outside its cached region bounds; otherwise spatial buckets 0/1 delegate to `FUN_006F9B20`, buckets 2/3 synthesize left/right movement from facing field `+0x08`, and buckets 4/5 emit masks `0x00080000/0x00100000` |
| `3` | `006FB9F4/006FBA34/47B34` | call live `FUN_006F7E70`, the direct cached-target-position mover |
| `4` | `006FBA04/006FBA44/47B44` | call live `FUN_006F63A0`, the route-segment executor |
| `5` | `006FBA14/006FBA54/47B54` | call live `FUN_006F5410`, the moving-primary-target route maintainer |
| `6` | `006FB87C/006FB8BC/479BC` | when slot `+0x108` is nonzero, OR mask `0x00040000`; depending on actor `+0x63` bit 6 and planar distance versus `400`, either retain or clear slot `+0x94` and `+0xD8` |
| `7` | `006FBA24/006FBA64/47B64` | call live `FUN_006F75E0` |
| `8` | `006FBA34/006FBA74/47B74` | call live `FUN_006F7CE0` |
| `9` | `006FBA44/006FBA84/47B84` | call live `FUN_006FAA50` |
| `10` | `006FBA64/006FBAA4/47BA4` | call live `FUN_006F9180` |
| `11` | `006FBB54/006FBB94/47C94` | call live `FUN_006F9B20` |
| `12` | `006FBB74/006FBBB4/47CB4` | require actor `+0xB00==0`, state halfword `+0x18E==8`, actor `+0xA4C/+0xA50` flag gates; then resident `FUN_0021DDB0(actor)`, otherwise reset |
| `13` | `006FBC70/006FBCB0/47DB0` | switch on actor `+0xB00 & 0xFF00`; `0` resets, and `0x100/0x400/0x1000` reset then call `FUN_0021DDB0(actor)` |
| `14` | `006FB920/006FB960/47A60` | target `+0x18E==6` resets; otherwise query resident `FUN_00230CE0(target,-1)`, reset on success, or OR mask `0x1080` |
| `15` | `006FBA74/006FBAB4/47BB4` | actor `+0x190==0x60` calls live `FUN_006F8810`; `0x5D` emits `0x1000`; otherwise reset |
| `16` | `006FBAE4/006FBB24/47C24` | reset when slot `+0x94` is zero or actor `+0x18E` is 4/5; otherwise emit `0x1000` |
| `17` | `006FBA54/006FBA94/47B94` | call live `FUN_006FB0D0`, a selector/queue path |
| `18` | `006FBB64/006FBBA4/47CA4` | call live `FUN_006FA590`: conditional guard output, with reset/action-selection departures described below |
| `19` | `006FBBE8/006FBC28/47D28` | actor `+0xB00` high byte zero resets; `0x100/0x400` reset then `FUN_0021DDB0(actor)` |
| `20` | `006FBD3C/006FBD7C/47E7C` | reset unless target `+0x18E==8` or slot byte `+0x124` is nonzero; in Practice, key `0x11==1` selects state 18 and returns; otherwise resident `FUN_00229B70(actor,-2)` |
| `21` | `006FBEF4/006FBF34/48034` | resident `FUN_00306420(actor,10/11)` success resets; otherwise emit `8`, resetting when slot `+0x94` expires |
| `22` | `006FBFB8/006FBFF8/480F8` | emit `4`, reset when slot `+0x94` expires |
| `23` | `006FBE50/006FBE90/47F90` | resident `FUN_0021DF60(actor,1,0x02000000,-2)` chooses an index; if valid and no action is queued, queue it with `FUN_0021D380` |
| `24` | `006FBFF4/006FC034/48134` | call live `FUN_006F4C10`, which validates the mode-1 handle and maintains/replans its route |
| `25` | `006FC004/006FC044/48144` | call live `FUN_006F4F10`, the [item-use handler](../projectiles_and_items/battle_item_inventory.md#na2-cpu-item-use) |
| `26` | `006FC1BC/006FC1FC/482FC` | call live `FUN_006F4260`, which refreshes the mode-2 point, enforces near/far deadlines, and maintains/replans its route |
| `27` | `006FC014/006FC054/48154` | decrement slot `+0x110`; on expiry reset, test live `FUN_006FC7F0(120.0)`, and on success set active, source mode 1, state 24, then invoke the route planner |
| `28` | `006FC12C/006FC16C/4826C` | call live `FUN_006F5CB0` |
| `29` | `006FC30C/006FC34C/4844C` | shared return; no action |
| `30` | `006FC30C/006FC34C/4844C` | shared return; no action |
| `31` | `006FC30C/006FC34C/4844C` | shared return; no action |
| `32` | `006FC30C/006FC34C/4844C` | shared return; no action |
| `33` | `006FC170/006FC1B0/482B0` | actor `+0x190==0x5D` emits `0x00010000`; otherwise reset |
| `34` | `006FC13C/006FC17C/4827C` | reset, then emit `0x00010000` |
| `35` | `006FC1CC/006FC20C/4830C` | call live `FUN_006F4080` |
| `36` | `006FC1DC/006FC21C/4831C` | reset, then emit `0x00010000` |
| `37` | `006FC210/006FC250/48350` | call live `FUN_006F95B0`, another selector/queue path |
| `38` | `006FC220/006FC260/48360` | emit `0x20000000`; clear request latch `+0x90` when slot halfword `+0x150==2` |
| `39` | `006FC268/006FC2A8/483A8` | resident `FUN_00229B70(actor,-2)` |
| `40` | `006FC28C/006FC2CC/483CC` | emit `0x10000000` |
| `41` | `006FC2A8/006FC2E8/483E8` | emit `0x01000000` |
| `42` | `006FC2C4/006FC304/48404` | call the action selector with `(distance=0, mask=0, range=1..1, directional gate on)`, then queue the returned index with `FUN_0021D380` |

The state numbers come from the table entries; the preserved export's
recovered switch cases are shifted `0x40` late and do not match them.

The guard-age setter calls are at actual states **20 (`0x14`)** and
**39 (`0x27`)**. Their raw table entries are respectively
`D/L/F 008C3820/008C3860/20F960 -> L 006FBD7C` and
`008C386C/008C38AC/20F9AC -> L 006FC2A8`; the call sites are
`006FBE40/006FBE80/47F80` and `006FC27C/006FC2BC/483BC`.
State **38 (`0x26`)** instead has entry
`008C3868/008C38A8/20F9A8 -> L 006FC260` and emits `0x20000000`.
Consequently `0x26` is not the state number of the direct `-2` guard-age
setter.

State 20's Practice branch calls manager key `0x11` at
`D/L/F 006FBDD8/006FBE18/47F18`. Value `1` writes state `18` (`0x12`) at
`006FBE10/006FBE50/47F50` and returns before the `-2` setter. The setting's
native labels and fighter-side effect are owned by
[Practice mode](../modes/practice_mode.md#substitution-jutsu). This establishes the AI
transition to the conditional guard handler without expanding that mechanic's
ownership here.

The numeric masks above can be related to the configurable input translator
without assigning move names. With the native default bindings,
`0x00001000` is a newly pressed Circle binding, `0x00010000` Cross,
`0x01000000` Square, `0x20000000` R1, and held L2 or R2 produces the logical
guard bit `0x10000000`. Low bits `4` and `8` are opposite direction sectors;
`0x00040000` is a short-history Cross-plus-direction modifier rather than an
independent button. These mappings come from the shared command-controller
pipeline documented in
[Action commands](../combat/action_commands.md#logical-mask-translation); bindings
remain user-configurable.

### State-18 guard reaction

The complete helper is `D/L/F 006FA550/006FA590/46690`, ending at
`D 0x006FAA0C`. It emits logical guard bit `0x10000000` conditionally; state
40 emits that same bit unconditionally. Guard input and fighter-side counters
are owned by [Chakra and guard](../combat/chakra_and_guard.md#guard-input-and-action-lifecycle).

The first gate checks the target's action class `+0x18E`. When it is `8`,
target current-action pointer `+0xA4C` has word `+0x14 & 0x02000000` tested
at `D 0x006FA59C..0x006FA5AC`; a set bit resets immediately. The helper then
builds a Practice override when manager mode is `3`, Status key `0x0C` is
other than COM (`1`), and Guard key `0x0E` is Yes (`1`). The override affects
the later guard gates and suppresses both random-gated action departures.

- When target class is not `8`, any of slot bytes `+0x124/+0x125/+0x126`
  equal to `1` emits guard and returns. Otherwise the helper resets. For
  spatial bucket `+0x30<3`, it can then select state `11`, set latch
  `+0x90=1` and timer `+0x94=30`, and call facing correction plus live
  `FUN_006F8810`. This requires no Practice override and an inclusive
  `0..100` roll below parameter 14 plus `10` when Strength key `0x0B` is
  nonzero, or parameter 14 alone when it is zero. The state and timer writes
  are at `D 0x006FA83C/0x006FA850`.
- When target class is `8`, guard is emitted if its current record word
  `+0x10` contains bit `2`, the spatial bucket is `0/1`, one of the three
  slot bytes equals `1`, or the Practice override is active with a bucket
  other than `4/5`. Without any such gate the helper returns without adding
  guard. The common guard store is `D/L/F 006FA934/006FA974/46A74`.
- After that common guard store, a non-override path rechecks target current
  record word `+0x10 & 0x100`. If set and slot cooldown `+0xD0` is zero, it
  reloads that cooldown to `30` at `D 0x006FA9A4`, then rolls `0..100`
  against parameter 14. Success calls reset, facing correction, and
  `FUN_006F8810` at `D/L/F 006FA9E0/006FAA20/46B20`,
  `006FA9E8/006FAA28/46B28`, and `006FA9F0/006FAA30/46B30`.
  Reset clears the guard output just added; this is a departure from the
  guard path, not a second guard-mask producer.

The target-record accesses use resident `FUN_00217930(target,-3/-1)`, which
returns the current-action pointer for either negative argument while the
target is in class `8`. These literal arguments therefore do not establish
different target action records. Player-facing action names for record bits
`2`, `0x100`, and `0x02000000` remain unresolved; the branch effects above do
not depend on naming them.

### Candidate-byte lifetime across Practice Status changes

**Observation:** The scripted tail clears `+0x126` at
`D/L/F 00702508/00702548/4E648` and writes `1` at
`007026D8/00702718/4E818` after obtaining the opposite-side support and
checking its reason byte `+0xE6==2`. The initializer also clears the byte at
`00705E64/00705EA4/51FA4`, using `sb zero,0xF6(s1)` where
`s1=slot+0x30`. This shifted pointer is a real alias write that an exact
`+0x126` instruction search alone would miss.

The full recovered ordinary incoming-action bodies refresh `+0x125` and
`+0x124`, respectively, but do not refresh `+0x126`. The opponent-support
stage constructs states 39..42 without writing this byte. The state-18
consumer forms its absolute byte address `0x008D66B6 + side*0x1E0` at
`D 006FA730/006FA8F8`, so those reads are also absent from a search for
literal slot offset `0x126`. The neutral reset has no write to any of these
three bytes.

**Static consequence:** A scripted-to-COM Status change can preserve a
previous `+0x126==1`. Settings apply writes Status and Strength before
comparing requested Strength with the normalized stored Strength. When they
match, it supplies force zero to the controller toggle. A fighter already
using the nonzero controller nibble is then left initialized as it was; the
toggle does not reinitialize merely because one non-Manual Status changed to
another. The Practice tail subsequently returns for Status COM before its
candidate-byte clears. Thus the same slot can retain a scripted support flag
on the COM path until an initializer or another recovered scripted-tail pass
clears it. A transition through Manual followed by COM does reinitialize,
because Manual clears the controller nibble. Settings transaction ownership
remains in [Practice mode](../modes/practice_mode.md#confirmapply-side-effects).

This establishes a retained-byte route to an ordinary COM consumer, not a new
ordinary producer of `1`. The full AI cluster through preserved
`0x007064FC`, absolute candidate-byte formations, shifted slot stores, and
the three ordinary reaction bodies above contain no recovered ordinary
producer. An unrecognized external alias remains unresolved;
the finding does not establish that every ordinary match can produce this
flag.

### Direct state constructors

A handler's presence does not prove that BTL ever selects it. Direct writes
to slot `+0x34` in BTL text give this constructor map. Entries are **live**
function starts (see [Address convention](#address-convention-and-overlay-mapping)).
Repeated writers inside one function are collapsed.

```text
state  direct BTL writer function(s)
 0     6F37B0 6F3F80 6F6080 6F63A0 6F7E70 6F8810 6F9180 6FAA50
       6FB840 6FDF30 7024A0 703170 704D40 705D70
 1     703170 703D20
 2     none found
 3     6F37B0 6FD970
 4     6F37B0 6F63A0
 5     6F37B0 6F5410 6FEAC0 7004B0 701140 7024A0 703170 703D20
 6     6FD970 6FEAC0 7004B0 701ED0 703D20
 7     700190
 8     6FD2D0 6FF9C0 7004B0 701140 701ED0 703D20
 9     6FAA50 6FB0D0 6FDF30
10     6F5410 6F9B20 6FD970 6FEAC0 6FF9C0 7004B0 701140 703170 703D20
11     6F5410 6F98C0 6FA590 6FDF30 6FEAC0 700190 7004B0 703170
       703A70 703D20 704D40
12     703D20
13     6FF650 (dynamic value selected from actor state flags)
14     703A70
15     703D20
16     6F5410 7004B0
17     6FDF30
18     6FB840 7004B0 701140 7024A0 703D20
19     6FF650 (dynamic value selected from actor state flags)
20     6FDF30 7004B0 701140
21     6FD2D0 701ED0 703D20
22     6F9B20 6FD2D0 700190 703D20
23     7004B0
24     6F4C10 6FB840 701BD0
25     6F5410 6F8810 6F9B20 6FD2D0 6FD970 6FDF30 7004B0 701BD0 703D20
26     6F4260 6FCE00
27     6F4260
28     6F8E50 6FD2D0 7004B0 703170
29     none found
30     none found
31     none found
32     none found
33     703D20
34     6FDF30 6FEAC0 701140
35     703D20
36     7024A0
37     7024A0
38     6FE720
39     6FEAC0
40     6FEAC0
41     6FEAC0
42     6FEAC0
```

`FUN_006FF650` selects state 13 for actor `+0xB00 & 0xFF00` values `0x1000`
or `0x400`, and state 19 for `0x100`, before applying the phase gate. No direct
constant constructor was found for state 2. More strongly, states 29 through
32 have neither a direct constructor nor an active handler in clean BTL; all
four table entries are the shared no-op return. External/aliased writes remain
possible, so state 2 is “untraced,” while 29..32 are best described as
apparently reserved under current static evidence.

## Action-record selection and direct queues

`FUN_006F2B40` scans the controlled fighter's action-record list and builds a
local array of eligible indices. Eligibility includes caller mask, record
range/category byte, distance threshold, fighter-state flags, and
live `FUN_006F26C0(record)` (`D/L/F 006F2680/006F26C0/3E7C0`). The local array
has 128 entries. No eligible record
returns `-1`; otherwise the call at
`D/L/F 006F2E6C/006F2EAC/3EFAC` selects by modulo as:

```text
eligible[(FUN_001801E0() ^ 0x80000000) % eligible_count]
```

The filter inputs are exact:

- it scans `s16 self+0xA38` records through resident
  `FUN_00217930(self,index)`;
- caller mask zero becomes default mask `0x000F000D`;
- caller range zero takes profile parameters 36 and 37 as the inclusive
  minimum/maximum for signed record byte `+0x19`;
- record word `+0x10` must intersect the selected mask;
- record float `+0x34` must be one of the sentinels `-17320.508`/`10000.0`, or
  must be at least the requested distance;
- record word `+0x1C` and signed fighter byte `+0x63` impose a directional
  eligibility gate;
- a nonzero fourth argument adds a 100-unit vertical-separation comparison;
- live `FUN_006F26C0` applies actor/target-state exclusions. In Practice,
  Attack Combo (`key 0x0D==2`) additionally rejects records with mask bits
  `0xF0000` or category zero. Its profile-parameter-15 random gate is skipped
  only for scripted Status Stand/Jump/Double-jump.

These are record-layout and branch facts, not names for the underlying moves.

The function returns the selected action-record index. For specially flagged
mapped actions, it calls live `FUN_00772870` and creates slot `+0x128` as a
percentage of that helper's result. The percentage ranges by spatial bucket
are:

| slot `+0x30` | bounded RNG | added base | percentage range |
| ---: | ---: | ---: | ---: |
| `0` | `0..30` | `10` | `10..40` |
| `1` | `0..40` | `20` | `20..60` |
| `2` | `0..50` | `30` | `30..80` |
| other | `0..60` | `40` | `40..100` |

The stored value is integer truncation of `mapped_value * percentage / 100`.

An exact raw-JAL scan finds 12 BTL calls to the selector's live entry:

```text
F       D          L          containing path
044E88  006F8D48   006F8D88   state-15 helper
044ED8  006F8D98   006F8DD8   state-15 helper
044F14  006F8DD4   006F8E14   state-15 helper
0457B4  006F9674   006F96B4   state-37 helper
0457D8  006F9698   006F96D8   state-37 helper
0458D4  006F9794   006F97D4   state-37 helper
0458FC  006F97BC   006F97FC   state-37 helper
047438  006FB2F8   006FB338   state-17 helper
047460  006FB320   006FB360   state-17 helper
047824  006FB6E4   006FB724   state-17 helper
048414  006FC2D4   006FC314   state-42 handler
04AFD4  006FEE94   006FEED4   reactive decision stage
```

An exact scan also finds 14 BTL calls to resident queue routine
`FUN_0021D380`:

```text
F       D          L
04077C  006F463C   006F467C
044B10  006F89D0   006F8A10
044C80  006F8B40   006F8B80
044E38  006F8CF8   006F8D38
044EA8  006F8D68   006F8DA8
044EEC  006F8DAC   006F8DEC
044F28  006F8DE8   006F8E28
0457EC  006F96AC   006F96EC
045978  006F9838   006F9878
0474C8  006FB388   006FB3C8
047844  006FB704   006FB744
048024  006FBEE4   006FBF24
048444  006FC304   006FC344
04B03C  006FEEFC   006FEF3C
```

The resident side establishes what “queue” means. `FUN_0021D250` at
runtime/file `0021D250/11D350` is a five-instruction predicate that returns
whether fighter halfword `+0xB34` is not `-1`. The queue reset helper
`FUN_0021D200` at runtime/file `0021D200/11D300` writes `-1` to `+0xB34` and
the four halfwords `+0xB36..+0xB3C`, writes zero to `+0xB3E`, and writes `-1`
to current-action halfword `+0xA3E`.

`FUN_0021D380` itself is resident runtime/file `0021D380/11D480`. It
sign-extends the requested index and rejects a negative value or a value above
fighter halfword `+0xA38`. It also returns zero while fighter byte `+0x61`
bit `0x80` is set, words `+0xB00` or halfword `+0xB10` are nonzero, the global
`0x00607654 -> +0x08 -> +0x14` gate is nonzero, or resident
`FUN_00239E50(fighter,0)` fails. The selected `0x54`-byte record is reached
through fighter pointer `+0xA54`; record word `+0x10` must be nonzero and must
exclude `0x02000000` and `0x0000F000`. Further record/fighter mode checks and
`FUN_00225940` enforce the action's resource requirement before installation.

On its normal success path the routine puts the requested index in `+0xB34`,
follows signed record byte `+0x18` as the next-record link for at most four
records, and writes each index into one of `+0xB36..+0xB3C` selected by signed
record byte `+0x19`; `+0xB3E` is reset to zero. A special fighter-state/record
flag path can instead replace current-action halfword `+0xA3E`. The function
returns one only after one of those installations, and zero on every admission
failure. Therefore state 42's unconditional call is safe when the selector
returns `-1`, and the resident layer remains the final authority even after a
BTL selector has chosen an index.

The queue is consumed by resident `FUN_0021DAE0` at runtime/file
`0021DAE0/11DBE0`. Its sole direct caller is logical-command interpreter
`FUN_0023A390` (`0023A390/13A490`), which has call sites
`00249414/149514` and `0024DB0C/14DC0C`. At the latter, resident bridge
`FUN_00217320` ran immediately before at `0024DAFC/14DBFC`. If queue root
`+0xB34` is not `-1`, `FUN_0023A390` calls the queue consumer and returns zero
instead of interpreting the supplied logical mask. A direct AI action queue
therefore has same-update precedence over the AI's command-mask path.

With phase `+0xB3E==0`, the consumer validates the fighter, starts slot
`+0xB36` through `FUN_0023A9A0(fighter,index,0)`, optionally installs
`+0xB38` as current action `+0xA3E`, and sets phase 2. Whenever `+0xA3E`
later becomes `-1`, it advances through `+0xB3A` and `+0xB3C`, incrementing
the phase. Fighter byte `+0x61` bit `0x80`, a failed admission predicate, an
exhausted/invalid slot, or leaving resident fighter state `+0x18E==8` clears
`+0xB34..+0xB3C`, `+0xB3E`, and `+0xA3E`. This proves the queue is a bounded
four-category action chain rather than an unbounded command FIFO.

State-15 live helper `FUN_006F8810` is representative: after target/context
gates and a no-action-queued test, it selects and queues an action-record index.
Special height branches instead ask resident `FUN_0021DF60` for an index using
masks `0x212`, `0x10A`, or `0x86`, then queue that result.

One cached-action branch has a distinct AI precheck before the resident queue's
own admission checks. Resident `FUN_00217930(self,slot halfword +0x1B0)`,
called at `D/L/F 006F8BE0/006F8C20/44D20`, returns that index's action record.
At `D 0x006F8CBC` the AI loads record float `+0x20`, converts it with
`cvt.w.s`, and passes the integer to resident `FUN_00372CB0`. That accessor
returns the signed byte at `0x005AEC49 + index*0x14`. The AI converts the
returned byte directly to a float and passes it to `FUN_00225940` at
`D/L/F 006F8CE0/006F8D20/44E20`; there is no multiplication by `5.0` in this
precheck. Only a nonzero result reaches queue call
`006F8CF8/006F8D38/44E38`, with cached index `+0x1B0`. This establishes an
intermediate AI selection gate, while the queue still independently enforces
the selected action's requirement. The shared resource interpretation is
owned by [Chakra and guard](../combat/chakra_and_guard.md).

## Configuration and behavior profiles

Resident `FUN_001F6EA0(manager)` calls `FUN_001F6420(manager,0x0B)` and returns
its `v0` unchanged. The key-`0x0B` handler selects the manager settings block
appropriate to manager mode and returns its byte `+7`. This directly proves
that the BTL initializer's profile index is raw manager key `0x0B`, not a
transformed derivative.

The key is normalized to `0..5`. Count-table entry 10 is live
`0x008D18E8`, displayed bytes `0x008D18A8`, file `0x21D9E8`, and contains `6`.
`FUN_00881950` normally uses maximum `5`, but lowers it to `4` when resident
feature key `0x6A` is unavailable. Profile 5 is therefore unlock-gated.

The initializer indexes the profile table at
`D/L/F 008C31F0/008C3230/20F330` with stride `0x50` and copies 40 signed
16-bit values to slot `+0x160..+0x1AF`. Raw selectable rows, in parameter-index
order `0..39`, are:

```text
profile 0: 50,0,0,240,0,20,0,0,60,10,60,0,0,0,10,0,0,180,180,0,0,0,0,50,0,0,0,0,20,40,0,380,60,240,40,8,0,1,200,30
profile 1: 45,0,0,210,0,30,25,0,40,15,60,0,30,0,30,35,0,150,150,30,0,0,0,15,0,0,0,0,35,55,0,360,45,180,35,6,0,2,170,25
profile 2: 30,0,0,180,0,35,35,25,40,30,70,40,40,0,65,45,0,120,100,40,0,0,0,50,0,35,0,30,40,60,0,300,60,150,35,6,0,3,150,20
profile 3: 20,10,20,150,25,40,35,35,40,40,70,50,60,45,60,55,50,90,100,50,10,0,0,50,0,35,40,40,40,60,3,300,50,120,35,5,0,3,120,15
profile 4: 15,15,20,120,45,50,45,40,40,50,70,60,70,55,70,60,60,80,80,50,25,30,50,50,0,40,45,45,45,65,2,240,40,90,30,5,0,3,110,10
profile 5: 15,20,30,90,60,60,55,50,50,60,80,70,70,60,80,70,70,70,80,70,40,50,70,50,0,50,45,45,50,70,1,180,35,75,20,4,0,3,85,5
```

A seventh contiguous `0x50` row exists after profile 5, but the confirmed
normal key bound cannot select it. Its role remains unresolved; the row does
not establish a seventh ordinary difficulty level.
Its exact location is `D/L/F 008C33D0/008C3410/20F510`, and its raw 40 values
are:

```text
15,30,35,60,80,65,70,60,50,70,90,80,80,70,90,80,80,60,80,80,
60,70,85,50,0,60,50,50,60,80,0,120,30,60,15,4,0,3,60,3
```

An aligned full-file scan found no absolute pointer to any individual profile
row and no code construction of row 6. The only constructions of table base
live `0x008C3230` are at file/live `0x510EC/0x00704FEC` (Practice hot reload)
and `0x52094/0x00705F94` (initializer); both add the accessor-provided index.
Under clean static evidence, therefore, row 6 is data without a confirmed
selector.

### Direct profile-parameter consumers

The following ledger transposes the six selectable rows and records only uses
that are direct in clean BTL text. Function addresses in this table are **live**
addresses (see [Address convention](#address-convention-and-overlay-mapping)).
`P0..P5` means profile rows 0 through 5.

Most random gates compare a profile value with
`FUN_00180210(100)`, whose result is inclusive `0..100`. A branch
`roll < value` accepts exactly the `value` result values `0..value-1` out of
the 101-value output domain; it is not a `value%` test. This document does not
call that an exact `value/101` probability because the wrapper uses modulo and
does not remove modulo bias. The ledger consequently says “0..100 threshold”
rather than “percent.”

| Index | Slot offset | P0/P1/P2/P3/P4/P5 | Direct structural use |
| ---: | ---: | --- | --- |
| 0 | `+0x160` | 50/45/30/20/15/15 | `0..100` gate in `L 0x006FCE00` before its environment-point scan can build a route and enter state 26. |
| 1 | `+0x162` | 0/0/0/10/15/20 | Contextual `0..100` threshold in `L 0x006FDF30`, `0x006FEAC0`, and `0x007004B0`; the first and third apply the [action-record scalar transform](#incoming-action-reactions-and-effective-strength-gates), and the third can first multiply the base by `0.8`. |
| 2 | `+0x164` | 0/0/0/20/20/30 | In `L 0x00701140`, an action-record scalar adjusts this `0..100` threshold before a transition to state 20. |
| 3 | `+0x166` | 240/210/180/150/120/90 | Countdown seed written to slot `+0x98`, `+0xD4`, or `+0xFC` by reactive paths in `L 0x006FDF30`, `0x006FEAC0`, `0x007004B0`, `0x00701140`, and `0x00703D20`. |
| 4 | `+0x168` | 0/0/0/25/45/60 | `0..100` threshold in `L 0x006FDF30` and `0x00703A70`. |
| 5 | `+0x16A` | 20/30/35/40/50/60 | Contextual threshold magnitude in `L 0x006FEAC0`, `0x007004B0`, `0x00701140`, and `0x00703D20`; `0x007004B0` can pass it to the ten-step phase gate, while `0x00701140` compares a float roll against `1.9*value`. |
| 6 | `+0x16C` | 0/25/35/35/45/55 | Alternate ten-step phase-gate input in `L 0x007004B0`, selected for particular incoming-action classes. |
| 7 | `+0x16E` | 0/0/25/35/40/50 | Another incoming-action-class phase-gate input in `L 0x007004B0`. |
| 8 | `+0x170` | 60/40/40/40/40/50 | `0..100` threshold in `L 0x006F9B20`, `0x006FB0D0`, `0x006FEAC0`, `0x007004B0`, and `0x00701BD0`. |
| 9 | `+0x172` | 10/15/30/40/50/60 | `0..100` threshold in `L 0x00703A70` before state 14. |
| 10 | `+0x174` | 60/60/70/70/70/80 | `0..100` threshold in `L 0x006FB0D0`, `0x006FDF30`, `0x006FEAC0`, `0x007004B0`, and `0x00703170`. |
| 11 | `+0x176` | 0/0/40/50/60/70 | `L 0x006F33A0` divides it by 10 to select a ten-step pattern row; it is also a direct `0..100` threshold in `L 0x006FF650` and `0x00703D20`. |
| 12 | `+0x178` | 0/30/40/60/70/70 | `L 0x006FF650` writes `100-value` to slot countdown `+0xC0`. |
| 13 | `+0x17A` | 0/0/0/45/55/60 | `0..100` branch in `L 0x00701140` choosing state 10 instead of state 18 for one nearby-action reaction. |
| 14 | `+0x17C` | 10/30/65/60/70/80 | Common `0..100` threshold across `L 0x006F5410`, `0x006FA590`, `0x006FB0D0`, `0x006FDF30`, `0x006FEAC0`, `0x007004B0`, `0x00703170`, `0x00703A70`, and `0x00703D20`. |
| 15 | `+0x17E` | 0/35/45/55/60/70 | Practice-aware eligibility gate in `L 0x006F26C0`; also controls a masked action-family attempt in state-15 helper `L 0x006F8810`. |
| 16 | `+0x180` | 0/0/0/50/60/70 | `0..100` threshold for cached-action reuse in `L 0x006F8810` and another reactive branch in `L 0x006FDF30`. |
| 17 | `+0x182` | 180/150/120/90/80/70 | Reload value for slot countdown `+0x100` in `L 0x006F8810`. |
| 18 | `+0x184` | 180/150/100/100/80/80 | Reload value for slot countdown `+0xB4` in `L 0x006F8810`. |
| 19 | `+0x186` | 0/30/40/50/50/70 | `0..100` threshold in `L 0x00703D20`. |
| 20 | `+0x188` | 0/0/0/10/25/40 | `0..100` threshold in `L 0x006F9B20`, `0x006FD2D0`, `0x00700190`, and `0x00703D20`. |
| 21 | `+0x18A` | 0/0/0/0/30/50 | `0..100` threshold for state 38 in `L 0x006FE720` and for synthesized mask `0x20000000` in `L 0x006FF410`. |
| 22 | `+0x18C` | 0/0/0/0/50/70 | `0..100` threshold in `L 0x006FD970`, `0x006FEAC0`, `0x007004B0`, `0x00701ED0`, and `0x00703D20`. |
| 23 | `+0x18E` | 50/15/50/50/50/50 | `0..100` gate in `L 0x006FD2D0` before a target-side movement/state-8 reaction. |
| 24 | `+0x190` | 0/0/0/0/0/0 | No direct clean-BTL read found. Character flag mask `0x08` still applies its `x1.2` transform here, which is a no-op for all six selectable base rows. |
| 25 | `+0x192` | 0/0/35/35/40/50 | `0..100` gate in `L 0x006FFEC0`; on success that path resets and ORs synthesized mask `0x1000`. |
| 26 | `+0x194` | 0/0/0/40/45/45 | `0..100` gate in `L 0x006F9B20` before state 25 and its route helper. |
| 27 | `+0x196` | 0/0/30/40/45/45 | Post-dispatch `0..100` gate at `D/L/F 00705584/007055C4/516C4`; object property bit `0x100` resets the AI before the roll, and success writes `1` to object `+0x13C`. Failure still clears the dispatched output. |
| 28 | `+0x198` | 20/35/40/40/45/50 | Widespread `0..100` threshold in `L 0x006F8810`, `0x006FEAC0`, `0x007004B0`, `0x00701BD0`, and `0x00703170`. |
| 29 | `+0x19A` | 40/55/60/60/65/70 | `0..100` gate in `L 0x007004B0`, `0x00701140`, and `0x00703D20`; one success invokes `L 0x006FD970`. |
| 30 | `+0x19C` | 0/0/0/3/2/1 | Inclusive bounded-RNG argument in `L 0x006FEAC0` and `0x007004B0`, used to seed short retry countdowns `+0xFC` and `+0x98`. |
| 31 | `+0x19E` | 380/360/300/300/240/180 | No direct clean-BTL load or absolute reference found. Unlike index 24 it carries meaningful-looking values, so its role is unresolved rather than presumed unused. |
| 32 | `+0x1A0` | 60/45/60/50/40/35 | General countdown seed written to slot `+0x94`, `+0x9C`, or `+0xAC` in `L 0x00703170` and `0x00703D20`. |
| 33 | `+0x1A2` | 240/180/150/120/90/75 | Countdown seed for slot `+0xD4` or `+0xE0` in `L 0x006FEAC0` and `0x007004B0`. |
| 34 | `+0x1A4` | 40/35/35/35/30/20 | State-1 countdown seed at slot `+0xD8` in `L 0x00703170`. |
| 35 | `+0x1A6` | 8/6/6/5/5/4 | In `L 0x006FFD50`, controls a directional randomized interval at slot `+0xE4`; the next value combines this base, `rand(0..base/2)`, and sometimes signed `rand(0..base)`. |
| 36 | `+0x1A8` | 0/0/0/0/0/0 | Default minimum allowed action-record category byte `+0x19` in selector `L 0x006F2B80`. |
| 37 | `+0x1AA` | 1/2/3/3/3/3 | Default maximum allowed action-record category byte `+0x19` in selector `L 0x006F2B80`. |
| 38 | `+0x1AC` | 200/170/150/120/110/85 | In `L 0x006FE720`, seeds slot `+0xF4` to `value + rand(0..value)` before another state-38 evaluation. |
| 39 | `+0x1AE` | 30/25/20/15/10/5 | In `L 0x006FF650`, seeds slot `+0xBC` to `value + rand(0..value)` on one state-19 reaction path. |

For the two negative rows above, the full BTL text disassembly gives index 31
no direct
`lh/lhu/lw/lwu/ld/lq/lwc1` load using slot offset `0x19E`, and no absolute
formation of live `0x008D672E`; index 24 likewise has no identified decision
consumer. Indexed access through an unrecognized pointer cannot be excluded,
so neither field is assigned a semantic name.

The initializer then applies three other input layers:

- Unless manager mode is 2 or 3, an unidentified BTL predicate returns 1, or
  resident `FUN_001FDC30()` is nonpositive, values `1..10` from that resident
  scalar select rows `0..9` of a 10-by-40 signed-byte percentage matrix at
  `D/L/F 008C35A0/008C35E0/20F6E0`; values at least 11 clamp to row 9. Each
  profile value becomes `value + trunc(value * signed_percent / 100)`.
- Character flag byte `L 0x008C3052 + character_id*4`
  (`D/F 0x008C3012/0x20F152`) applies `x1.2`: mask `0x01` to profile offset
  `+0x20`, mask `0x04` to `+0x10`, and mask `0x08` to `+0x30`.
- The normalizer at `D/L/F 00705770/007057B0/518B0` replaces negative
  selected parameters with exact per-index defaults: `p1=40`, `p2=40`,
  `p5=80`, `p8=90`, `p9=80`, `p10=80`, `p11=80`, `p12=80`, `p14=90`,
  `p15=70`, `p16=70`, and `p18=150`. Other indices are not normalized there.

The secondary matrix is below in parameter-index order `0..39`:

```text
row 0: -3,-5,-6,3,-3,-5,-5,-5,-3,-3,-3,-3,-3,-3,-3,-3,-3,5,5,-3,-3,-8,-10,0,-3,-3,-3,-3,-3,-3,5,3,5,0,0,5,0,0,5,0
row 1: -8,-9,-10,8,-8,-10,-10,-10,-8,-8,-4,-5,-8,-8,-8,-8,-8,10,10,-8,-8,-15,-15,0,-8,-8,-8,-8,-8,-8,8,5,10,5,3,10,0,0,10,5
row 2: -15,-14,-15,12,-12,-15,-15,-15,-10,-12,-8,-10,-10,-12,-12,-12,-12,15,15,-12,-12,-20,-20,-10,-8,-8,-8,-8,-8,-8,12,15,10,10,8,15,0,0,15,10
row 3: -20,-18,-20,18,-18,-20,-20,-20,-15,-16,-13,-14,-14,-18,-18,-18,-18,20,20,-18,-18,-25,-25,-10,-14,-14,-14,-14,-14,-14,18,20,15,15,10,20,0,0,15,15
row 4: -30,-22,-25,25,-25,-25,-35,-35,-20,-20,-18,-18,-18,-25,-25,-25,-25,25,25,-25,-25,-30,-30,-15,-20,-20,-20,-20,-20,-20,20,30,20,15,15,25,0,0,20,20
row 5: -40,-28,-30,30,-30,-30,-35,-35,-25,-24,-24,-20,-20,-30,-30,-30,-30,30,30,-30,-30,-40,-35,-15,-20,-20,-20,-20,-20,-20,25,35,25,20,20,30,0,0,20,25
row 6: -50,-34,-35,35,-35,-35,-40,-40,-25,-28,-28,-24,-24,-35,-35,-35,-35,35,35,-35,-35,-50,-35,-20,-20,-20,-20,-20,-20,-20,30,35,30,25,20,35,0,0,25,30
row 7: -60,-39,-40,40,-40,-40,-45,-45,-30,-32,-30,-28,-28,-40,-40,-40,-40,40,40,-40,-40,-55,-40,-20,-25,-25,-25,-25,-25,-25,35,35,30,30,25,40,0,0,25,35
row 8: -70,-45,-45,45,-45,-45,-45,-45,-30,-36,-30,-32,-32,-45,-45,-45,-45,45,45,-45,-45,-65,-45,-30,-25,-25,-25,-25,-25,-25,40,40,35,35,30,45,0,0,30,40
row 9: -80,-50,-50,50,-50,-50,-50,-50,-35,-40,-30,-35,-35,-50,-50,-50,-50,50,50,-50,-50,-70,-50,-30,-30,-30,-30,-30,-30,-30,45,40,35,35,35,50,0,0,30,45
```

Resident `FUN_001FDC30` is only `lw v0,-0x335C(gp); return`. The clean ELF
`.reginfo` value is `gp=0x0060A9F0`, placing the counter at resident BSS
`0x00607694`; it has no file offset. Its source is the resident continue flow:

- `FUN_001FED10` (runtime/file `001FED10/0FEE10`) allocates a `0x3C`-byte
  object and initializes it through `FUN_001FBA30` (`001FBA30/0FBB30`), whose
  resource lookup is the literal string `"continue"` at runtime/file
  `00406AA0/306BA0`;
- when that object completes, its result word `+0x08` values `0` and `2`
  increment `0x00607694`, while value `1` does not;
- `FUN_001FE300` and `FUN_001FE390` clear the counter during construction and
  teardown of the surrounding resident flow. No other clean resident writes
  were found.

The choice labels are established by the resident renderer `FUN_001FC5C0`
(runtime/file `001FC5C0/0FC6C0`). It indexes the three-pointer table at
runtime/file `00406530/306630` with the same `+0x08` value that
`FUN_001FED10` consumes. The strings are Shift-JIS; the third retains native
ruby markup:

| Result `+0x08` | Label bytes at runtime/file | Native label | Counter effect |
| ---: | --- | --- | --- |
| `0` | `006030A0/5031A0` | `はい` (Yes) | increment |
| `1` | `006030A8/5031A8` | `いいえ` (No) | unchanged |
| `2` | `00406510/306610` | `キャラクター<ruby変更\|へんこう>` (Change character) | increment |

`FUN_001FBD60` (`001FBD60/0FBE60`) sets the choice count at `+0x0C` to
two or three according to `FUN_001FDBF0()`. Input handler `FUN_001FC020`
(`001FC020/0FC120`) bounds `+0x08` to that count, moves it with native
Up/Down, and accepts it on new-press mask `0x20`. There is no timeout write
that substitutes another result in this handler. Thus Change character is an
optional third choice, not an unnamed automatic result. The exact conditions
that expose that choice are outside the AI counter's ownership.

This establishes a continue-screen completion counter incremented by Yes and
Change character, but not No. It chooses the ten percentage rows above; it is
not the ordinary Strength key and should not be called a global difficulty
setting.

The BTL predicate that can bypass this modifier is structurally bounded.
`D/L/F 006EE510/006EE550/3A650` merely returns a global byte. Its setter
`006EED90/006EEDD0/3AED0` has one direct BTL caller, at
`006EEC64/006EECA4/3ADA4`. That caller loads its setup pointer from owner
`+0x1C`, reads setup word `+0x0C` at `D 0x006EEC20`, copies that value to
owner `+0x04`, and calls the setter only for value `2`. This setup field is a
separate namespace from manager mode `+0x0C`, so their equal numbers do not
establish an equal mode meaning.

When owner child `+0x24` is absent, the setter allocates `0x1C` bytes and
initializes them through resident `FUN_001FE260`, obtains resident data pointer
`0x006B3010` through `FUN_001FDC20`, binds that data into the setup flow, and
sets the bypass byte to `1` at `D 0x006EEE38`. The byte is cleared by the
mode-2 completion path in `006EEEE0/006EEF20/3B020`. The AI initializer reads
it at `00706014/00706054/52154`. This proves the bypass's setup value and
resident-data dependency, but not a safe player-facing name for that setup
value. It is not named by substituting the manager's mode-2 label.

In manager mode `+0x0C==3` (Practice), the main tick detects a changed key
`0x0B` and hot-copies the new raw `0x50` row. This hot reload does not rerun the
secondary percentage modifier, character multipliers, normalizer, two-slot
reset, or initializer-only randomized timers.

### Computed profile copies and unresolved parameters

**Observation:** Both unresolved parameters participate in two real indexed
copies that the direct-reader ledger intentionally does not treat as decision
consumers. The initializer's `D 00705F70..00705F8C` and Practice hot reload's
`D 00704FD8..00704FF4` each copy two signed halfwords per iteration, advancing
both pointers by four and iterating 20 times. Their destination is precisely
`0x008D66F0 + side*0x1E0`, the selected slot's 40-parameter row. Parameter 24
is the first halfword of iteration 12; parameter 31 is the second halfword of
iteration 15, counting from zero. Neither copy exports a new row or pointer
to another owner.

The initializer's secondary modifier loop at
`D/L/F 00706064/007060A4/521A4` computes the selected row address plus
`parameter_index*2`, reads the halfword at `D 007060C0`, applies that index's
signed-byte percentage, and writes it back at `D 007060EC`. Its loop bound
is 40. Thus index 31 is copied and arithmetically adjusted even though no
later decision consumer has been recovered. Index 24 is copied and adjusted
too, then descriptor bit `0x08` can multiply it at
`D 00706210..00706230`. All seven authored base rows have zero at index 24;
the modifier and multiplier both preserve zero. The two recovered profile
installation paths therefore install zero there under their authored inputs.

**Bounded negative:** Following the row-base formations, shifted slot aliases,
overlapping loads, and surviving pointer registers through the AI cluster
found no additional decision use of either index and no outgoing copy of the
row. The classifier after hot reload obtains its own slot from the side
global; the initializer's bypass predicate takes no profile input; and the
normalizer takes a side index and touches its explicitly listed parameters,
which exclude 24/31. A profile pointer left in a caller-saved register after
the copy is consequently not evidence that those helpers consume it. The
whole-BTL address pass likewise found no recovered formation for the second
side's absolute parameter addresses `0x008D6900/0x008D690E` that adds another
consumer. Unknown aliases and indirect external access remain open. These
results establish installation and transformation, not semantic meanings or
universal non-use.

## RNG ownership and confirmed uses

BTL has no local PRNG state. Every confirmed AI call enters one of two
resident wrappers around the shared MT19937 core `FUN_0017FD90`; the core,
its state, the wrappers' exact reductions, and seeding are owned by
[Resident randomness](../../runtime/randomness.md#mt19937-core), with its
[MT wrappers](../../runtime/randomness.md#mt-wrappers) and
[initialization and reseeding](../../runtime/randomness.md#coordinated-initialization-and-reseeding):

```text
FUN_001801E0()      -> raw PRNG value
FUN_00180210(bound) -> (raw ^ 0x80000000) % (abs(bound) + 1)
```

The bounded result is inclusive `0..abs(bound)` and keeps modulo bias, so a
comparison such as `rand(0..100) < value` is a threshold over 101 results,
not an exact percentage. Confirmed AI uses include:

- modulo selection among filtered action records, described above;
- special-action cooldown percentage generation, described above;
- both-slot initialization timer slot `+0xB4 = 150 + rand(0..120)`;
- a ten-step phase gate rather than an independent Bernoulli roll on every
  evaluation;
- a paired-AI branch in the main tick that, under a specific both-controlled,
  both-state-5, differing-region condition, tests `rand(0..100) < 20`, then
  uses `rand(0..1)` to reset one of the two slots. A deadlock/stalemate-breaker
  purpose is plausible but remains a hypothesis.

The generator state is shared game-wide, not stored per AI side, and many
non-AI resident paths call the same wrappers. Consequently AI results depend
on the shared call order, including intervening non-AI consumers and resets;
equal AI slot contents alone do not imply the same next decision.

An exact aligned-JAL audit of the identified AI cluster from live
`0x006F0000..0x00706500` finds **167** direct RNG-wrapper calls: 10 raw calls to
`FUN_001801E0` and 157 inclusive-bounded calls to `FUN_00180210`. Counts by
live containing function are:

```text
function       raw  bounded    function       raw  bounded
006F26C0         0      1      006F2B80         1      4
006F3140         2      0      006F33A0         2      0
006F4F10         0      1      006F5410         0      4
006F8810         0      3      006F98C0         0      3
006F9B20         4      7      006FA590         0      2
006FB0D0         0      9      006FC480         0      1
006FCE00         0      3      006FD2D0         0      4
006FD970         0      3      006FDF30         0      9
006FE720         0      3      006FEAC0         0     19
006FF410         0      4      006FF650         0      2
006FFD50         0      3      006FFEC0         0      3
00700190         0      4      007004B0         0     14
00701140         0      4      00701BD0         0      2
00701ED0         0      7      00703170         1      5
00703A70         0      5      00703D20         0     23
00704D40         0      4      00705D70         0      1
```

The ten raw call sites and their exact mappings are:

```text
F       D          L          established use
03EFAC  006F2E6C   006F2EAC   modulo eligible-action selection
03F3E8  006F32A8   006F32E8   phase-cursor seed/reseed modulo 10
03F424  006F32E4   006F3324   phase-cursor seed/reseed modulo 10
03F5AC  006F346C   006F34AC   second phase-cursor seed/reseed modulo 10
03F5E8  006F34A8   006F34E8   second phase-cursor seed/reseed modulo 10
046108  006F9FC8   006FA008   five-way behavior branch
04631C  006FA1DC   006FA21C   five-way behavior branch
0464FC  006FA3BC   006FA3FC   five-way behavior branch
046618  006FA4D8   006FA518   five-way behavior branch
04FA58  00703918   00703958   twenty-way branch in `FUN_00703170`
```

All four `FUN_006F9B20` raw results are reduced modulo 5. The
`FUN_00703170` result is reduced modulo 20; cases 0 through 5 take one branch
and the other 14 values take the default branch. This audit also shows that RNG
is pervasive in decision stages even though primary fighter-target ownership
is deterministic.

The ten-step phase helper is `D/L/F 006F3100/006F3140/3F240`. Its sole direct
caller is `D/L/F 00700BC8/00700C08/4CD08` inside
`D/L/F 00700470/007004B0/4C5B0`. It buckets integer input divided by 10, selects
one of cursors `+0x1B4/+0x1B8/+0x1BC`, seeds a `-1` cursor or reseeds at wrap
with raw RNG modulo 10, otherwise advances it deterministically, and reads a
boolean from `D/L/F 008C3190/008C31D0/20F2D0`:

```text
row 0: 0 1 0 0 0 1 0 0 0 0
row 1: 0 1 0 0 0 1 0 1 0 0
row 2: 0 1 0 1 0 1 0 1 0 0
row 3: 0 1 0 0 1 1 0 1 0 1
row 4: 0 1 0 1 1 1 0 1 0 1
row 5: 0 1 1 1 1 1 0 1 0 1
```

Its raw RNG call sites are
`D/L/F 006F32A8/006F32E8/3F3E8` and
`006F32E4/006F3324/3F424`. A positive result contributes to a transition to
raw state `0x12`, sets request latch `+0x90=1`, and timer `+0x94=30`. The exact
action name is unresolved.

A second consumer of the same six-row, ten-column boolean table is
`D/L/F 006F3360/006F33A0/3F4A0`. It takes Strength-profile parameter 11
implicitly rather than a function argument and chooses table row/cursor as:

```text
floor(parameter11 / 10)  table row  cursor
0..1                     0          +0x1B4
2..3                     1          +0x1B4
4..5                     2          +0x1B4
6..7                     4          +0x1B8
8 or greater             5          +0x1BC
```

It seeds, advances, and wraps the cursor exactly like `FUN_006F3140`. Its sole
direct call is `D/L/F 006FF92C/006FF96C/4BA6C` in
`D/L/F 006FF610/006FF650/4B750`, the Extra Hit Counter response selector.
For the Normal setting, response flag families choose candidate state 13 or
19, apply their cooldown and random gates, and commit the candidate only when
this phase helper's current table cell is nonzero. Practice setting Always
return bypasses the phase helper and commits the candidate immediately after
clearing the corresponding cooldown. Thus the three phase cursors are shared
across at least two distinct reaction-selection paths.

Preserved `FUN_006F1020` (`D/L/F 006F1020/006F1060/3D160`) is not an RNG
helper: it maps a target action-record byte in `-3..3` to floats from `-0.5`
through `+0.5`.

## Evidence limits, negative results, and hypotheses

Confirmed negative results:

- No BTL ASCII class identifier contains `AI`, `CPU`, `brain`, or `think`;
  identification is structural. Relevant named strings include
  `ccCommandCtrl`, not an AI-specific class name.
- There is no BTL-internal call to the main tick. Resident character wrappers
  own 74 direct calls.
- Ordinary primary-opponent binding performs no search and uses no RNG.
- COM disable performs no state reset, destructor, free, or deallocation.
- No AI heap allocation was identified; the two state blocks are static BSS.
- Native default bindings establish the named logical-mask sources listed
  above; unlisted masks and move-specific meanings remain unresolved.
- State IDs have not been assigned behavior names beyond direct handler effects.

Useful hypotheses, kept separate from established facts:

- the conditional random reset of one of two AI slots likely prevents a
  two-controller stalemate;
- the seventh contiguous profile row is likely reserved for a special mode or
  inaccessible tier, but no confirmed caller selects it;
- the continue-screen counter drives a progressively stronger signed profile
  adjustment, but whether its design intent is specifically adaptive easing is
  an inference; the incrementing choices themselves are established above.
