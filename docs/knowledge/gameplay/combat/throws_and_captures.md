# Throws and captures

This document investigates throw and capture control in retail NA2
(`SLPS-25837`).

## Research coverage

- **Assigned scope:** Native throw/capture entry, participant selection, escape/release, paired action transitions, and interruption lifetimes.
- **Exploration depth:** Inspected complete resident category/attachment, approach, contact, held-response, entry/cleanup and direct-classifier-consumer bodies. Recovered the computed approach and attachment arithmetic from EE/VU instructions and their math helpers. Read nine representative complete action arrays, selected complete phase sequences, release/input callbacks, and IDs 39/47/50/84 pre-attachment and destruction paths. Corroborated masks, stores, callback tables, anchor names and jump-table branches with instructions/data bytes; checked BTL direct-call references and byte patterns.
- **Confirmed coverage:** Captures use the existing paired fighter, ordinary contact admission and conditional substitution, phase-dependent classification, flag-dependent guard bypass, authored capture-to-release continuations, anchor attachment, and scheduled receiver handoff. Equations distinguish computed sender movement, corrected receiver position, relative-scale full transforms and Euler rotation. Selected records/callbacks establish guard exceptions, chained releases, live damage mutation, repeat-dependent response overrides and category-disable release. The inspected input request has a grounded prerequisite rather than a held-substate blacklist; selected destruction differs from state cleanup.
- **Unresolved or untested:** Guaranteed anchor/partner-model availability, ordinary-play reachability of every sampled branch, authored producers and meanings of mask bits `0x400/0x800`, address-zero lookup-failure consequences, zero-distance/scale inputs, isolated participant removal ordering, and escape/destruction paths outside the inspected families remain unresolved. Visible durations and outcomes were not measured; equations describe the inspected branch's arithmetic and velocity writes, not a measured complete trajectory.
- **Deliberate exclusions and overlap:** This document owns retail category-`0x100/0x200` capture coordination and its attachment variants. [Target selection](target_selection.md) owns target/provenance contracts; [Combat action execution](combat_action_execution.md) owns ordinary action execution and the separate `+0xB10` paired contest; [Hit response](hit_response.md) owns the complete receiver response matrix; [Extra Hit](extra_hit.md) owns the paired exchange; [Substitution](../characters/substitution.md) owns its full eligibility predicate; [Damage](damage.md) owns damage arithmetic/application. Existing complete censuses are linked rather than repeated.
- **Evidence limitations:** Static retail code and data establish bounded control paths, not measured timing or player-facing move names. Reported xrefs do not cover every indirect or computed transfer. Vector-heavy decompilation was used for bounded ownership/control observations; exact vector arithmetic is recorded only where instructions corroborate it.

## Evidence and address conventions

Binary identities and address conventions belong to
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
Function labels are analysis names rather than recovered source names.

BTL reported no xrefs or matching direct `jal` instruction bytes for
`FUN_0023E250/E2E0/E3C0/E420/E430/E440/E460/E500/E910/EAA0`,
`FUN_002316D0`, or `FUN_0023EF30/EF50`. This bounds direct calls to these
specific `jal` targets in the inspected overlay; it does not exclude callbacks,
jump-table dispatch or other indirect transfers. The descriptor-driven
receiver handoff remains documented in [Hit response](hit_response.md).

## Capture family and participant boundary

**Observation:** The common capture-related category service is resident
`FUN_0023E250`, not fighter paired-contest field `+0xB10`. It resolves the
current action only in major state 8 when its explicit record argument is
null. Category `record[+0x10] & 0x100` returns 1 in phase 0 and 2 in any
other phase; category `0x200` returns 3 in phase 0 and 4 otherwise. The
`0x200` check follows the `0x100` check and overrides its result if both
bits are present. These are internal classifications, not player-facing
move names.
The motion and attachment predicates use the wider mask `0xF00`; the
classifier's return branches here recognize only `0x100/0x200`.

`FUN_0023E2E0` returns 1 only when that classification is nonzero and
record behavior `+0x14 & 0x4000` is set. The contact-side consumer
`FUN_00220690` uses this result to suppress its ordinary guard branch.
This proves a category/flag-specific guard bypass, not universal
unguardability of everything entering a held response. Hit admission,
response selection and damage application remain separate gates owned by
[Hit response](hit_response.md) and [Damage](damage.md).

The partner is always the fighter already at `+0x20` in the common paths
examined here. They neither search a target list nor replace that pointer.
Accepted-hit source pointers have their own
[Target selection contract](target_selection.md#accepted-hit-source-boundary).
The attachment service does not use source `+0xE58` to choose its partner.

### Wide-mask bits without a classified capture

**Observation:** Bits `0x400/0x800` have a bounded common-code contract even
though their authored meanings remain unidentified. A record containing
either bit but neither `0x100` nor `0x200` passes the attachment category gate
and the broad `FUN_0023E3C0` predicate (when behavior `& 0x7C` is zero), but
`FUN_0023E250` returns zero. Such a record does not receive classifier-based
guard bypass. Entry `0x00238B24..0x00238B58` and cleanup
`0x00238F90..0x00238FC4` call only the `0x100/0x200` category helpers;
there is no matching wide-mask-only snapshot/position-cleanup dispatch there.
`FUN_0023E500` still consumes the row motion, but its facing events and
computed-approach selection require the classified `0x100/0x200` cases.

For a held receiver whose partner remains in major 8 with such a record,
`FUN_002316D0` enters `(0,0)` if behavior `0x04000000` is clear: the current
record exists, but both classified category bits fail. When that behavior
bit is set, the same updater retains the receiver without checking those
two category bits. Thus the broad attachment mask alone does not establish
a complete starter/release lifecycle for `0x400/0x800`.

The two additional complete arrays for IDs 39/47 inspected below contain
`0x100/0x200` in this group and no `0x400/0x800`. Aligned immediate-mask
searches and selected containing-body reads also expose identical numeric
masks in input/exchange or movement fields; those are not evidence of an
action-category producer. No concrete authored `0x400/0x800` capture record
or writer has been established by this bounded trace. Their retail purpose,
indirect producers, and reachability remain open rather than assigned names.

## Sender-side attachment

Resident `FUN_0023EAA0` requires a nonnull major-8 action with category
mask `0xF00`, the partner in major 5 substate `0x4A..0x4E`, and equal
tier halfwords `self[+0x9F6] == partner[+0x9F6]`. These gates distinguish
attachment from generic collision or merely having a current action.

It obtains the sender's effect-anchor name from `+0xA4` and resolves it
inside the sender's scene/model object `+0xE70` through `FUN_001BAB40`.
The caller contains a name-owner branch on `FUN_00307A50(sender)`, but the
complete retail helper is `move v0,zero; jr ra; nop`; bytes at
`0x00307A50..0x00307A5B` establish that this path always uses the sender's
name. A missing sender model, empty name, or failed anchor lookup prevents
all partner position/model updates in the body. Character anchor ownership
is recorded in [Character assets](../../game/character_assets.md#character-records).

With an anchor, it copies the anchor transform, derives the partner position
from its translation, and subtracts half the partner's scaled height in Z
except for response `0x4E`. `FUN_0021C640` can correct the derived planar
position against the sender's geometry. The partner's position vector
`+0x30..+0x3C` is then overwritten. The remaining handling has three forms:

| Partner/action condition | Additional attachment operation |
| --- | --- |
| Response other than `0x4E`, behavior `0x04000000` clear | Refresh partner model through `FUN_0024D3C0` |
| Response other than `0x4E`, behavior `0x04000000` set | Extract Euler angles through `FUN_0023E910`, add pi to the third angle with wrap, write partner rotation `+0x40..+0x4C`, then refresh its model |
| Response `0x4E` | Apply partner/sender scale ratios to the copied transform, write it directly into partner model `+0x40..+0x7F`, and set that model's byte `+0x8D` to 1 |

After a successful anchor path, the function clears partner grounded bit
`+0x63 & 0x80` and clamps negative vertical speed `+0x998` to zero.
Its local transform workspace pointer is restored before return. It does
not store an additional participant pointer or install an allocation owner.
This establishes the static position/model binding; it does not establish
the visible animation or which resource supplies every anchor. The direct
`0x4E` model-write branch has no explicit partner-model null check; the
investigation does not establish that model pointer's availability under
every possible interruption.

Instructions `0x0023ECAC..0x0023ED60` corroborate vector initialization,
height subtraction, the correction query, and the partner position store;
`0x0023EDF0..0x0023EF04` corroborates the full-transform branch, rotation
branch, grounded-bit clear and vertical-speed clamp.

### Attachment equations and lookup failure

**Observation:** In column-vector notation, let A be the resolved anchor
world matrix with translation t, and let
`H = 0.5 * partner[+0xE4] * partner[+0x2F0]`. The initial bound position is
`p = t + (0,0,-H,0)` for responses `0x4A..0x4D`, or `p = t` for `0x4E`.
The correction query receives `(p.x, sender.position.y, p.z, 1)` and the
sender's scaled `+0xE4/+0xE8` dimensions. On success it replaces only
`p.x/p.z`; the stored partner position keeps the anchor-derived Y and W.
Thus correction does not simply replace the entire anchor translation.

For `0x4E`, a successful correction also replaces A's entire translation
column with p; without correction it leaves A's translation untouched.
The final partner-model matrix is
`A * diag(partner.scaleX/sender.scaleX, partner.scaleY/sender.scaleY,
partner.scaleZ/sender.scaleZ, 1)`, using fields `+0x2E0/+0x2E4/+0x2E8`.
`FUN_00152020` reads the four A columns and multiplies each diagonal-matrix
column, confirming that basis columns are scaled and translation is retained.
There is no denominator-zero or partner-model-null branch in this path.

For the flagged rotation path, `FUN_0023E910` copies A and extracts
`rx = -atan2(A[+0x24], A[+0x28])`,
`ry = asin(A[+0x20])`. If `abs(cos(ry))` exceeds the double constant
`0x3F1A36E2E0000000` (the promoted float approximately 0.0001), it uses
`rz = -asin(A[+0x10]/cos(ry))`, replacing rz with `pi-rz` when
`A[+0] < 0`. Otherwise it uses
`rx = -atan2(A[+0x18],A[+0x14])`, the same ry, and `rz = 0`.
The caller adds pi to rz, wraps once into `[-pi,pi]`, writes
`(rx,ry,rz,0)` to partner `+0x40`, then calls the ordinary model refresh.
The unflagged `0x4A..0x4D` path leaves those rotation fields alone.

The anchor is borrowed for this call, not retained in a fighter field:
`FUN_001BAB40` searches the sender scene's named entries and the optional
type-`0x100` nested `+0x94` object. Its required-lookup failure with argument
2 equal to zero executes `sw zero,0(zero)` at `0x001BAC2C` before returning
null. `FUN_0023EAA0` supplies zero. Its later null branch prevents attachment
stores, but does not prove that a missing authored anchor is harmless. The
effect of the address-zero write and ordinary-play reachability of such a
missing anchor are unresolved. The name pointer itself is dereferenced
without a null-pointer check after the nonnull sender-model gate.

## Common entry, handoff and interruption

Category-`0x100` entry/cleanup helpers `FUN_0023E420/FUN_0023E430` are
empty. Category-`0x200` entry `FUN_0023E440` snapshots the partner's
position into partner `+0xAE0..+0xAEC`; cleanup `FUN_0023E460` independently
runs the tier-aware `0x007090D0` position query for each fighter with
nonnull `+0x28`, replacing its Y coordinate only on a successful query.
It does not null fighter `+0x20` or free the partner.

The common major-8 updater `FUN_0023BAC0` dispatches category `0xF00`
to `FUN_0023E500` after exchange and positive `+0xB10` branches.
That body normally uses authored row motion through `FUN_0021ACB0`, but a
category-`0x100` action with behavior bit `0x2` instead uses `FUN_0023F5D0`.
It also performs phase-specific facing changes. Ordinary entry, phase
progression, continuation and terminal exit remain in
[Combat action execution](combat_action_execution.md).

The held receiver's `FUN_002316D0` uses partner major state, category,
behavior `0x04000000` and phase-payload bits to decide retention, another
response, or release. The complete receiver matrix belongs to
[Hit response](hit_response.md#response-exits-contact-stages-and-downed-handoff).
The matrix is conditional on the paired fighter's execution; it is not an
independent fixed-duration hold. Loss of the partner's major-8 current
record can restore receiver position from `+0xAE0` before its next state.

Major-8 cleanup `FUN_00238D00` runs category cleanup while the old action
record is still installed. When the requested next major is not 8, it also
releases a partner specifically held in `(5,0x50)` to `(0,0)`; this branch
is distinct from attachment responses `0x4A..0x4E`. It does not immediately
force those attachment responses to neutral. Their following response
updates consult the partner's resulting state through `FUN_002316D0`.
This proves a scheduled handoff, not complete protection against every
possible participant destruction or indirect callback.

### Facing and sender approach

`FUN_0023E500` has two capture-specific facing events. In category `0x100`
phase 0, primary event 0 plus behavior `0x40` and grounded bit `+0x63 & 0x80`
copies opponent-facing halfword `+0x326` into `+0x98C/+0x98E/+0x990`, refreshes
rotation, and moves planar/vertical speeds toward zero. In category `0x200`
phase 1, secondary event 0 reverses those facing halfwords when
`FUN_0023E3C0` is false. That predicate is true exactly for category mask
`0xF00` with behavior mask `0x7C` zero. Thus the phase-1 reversal is authored
behavior dependent; it is not a mandatory operation for every release.

The alternative sender movement `FUN_0023F5D0` snapshots its own position
`+0xAE0..+0xAEC` at primary event 0, copies `+0xA46` to `+0xA47`, and clears
`+0xA46/+0xA48`. It uses the already paired fighter, current phase motion
and attack payload, animation length, facing, distance, current/previous
contact outcomes `+0xA40/+0xA41`, and record byte `+0x19` to choose between
ordinary row motion and a computed approach. A successful computed path
stores a target vector in `+0xAF0..+0xAFC` and derives sender velocities
`+0x994/+0x998`; its allocated scratch pointer is restored. This is sender
movement toward the existing partner, separate from the receiver's anchor
attachment. The instruction-derived equations below separate the computed
path from ordinary motion and braking.

### Computed approach equations

**Observation:** The complete 1,080-instruction body of `FUN_0023F5D0`
provides the following bounded calculation. Let `S` be the sender, `P` its
existing `+0x20` partner, `O = S[+0xAE0]` the primary-event-0 position
snapshot, `h = +0xE4 * +0x2F0` and `w = +0xE8 * +0x2F0` for each fighter.
These names denote scaled fields used by these instructions, not a new
physical interpretation of all character parameters.

Before selecting the computed path, it measures XYZ distance between
`S.position + (0,0,hS/2)` and `P.position + (0,0,hP/2)` and uses comparison
radius `(hS+wS+hP+wP)/4`. `FUN_001806F0` explicitly subtracts its two
vectors and takes `sqrt(dx²+dy²+dz²)`. The selection also checks facing,
range field `S+0x138`, current/prior outcomes, record byte `+0x19`, and the
secondary timer. Null partner/current record, missing motion/attack data,
negative animation slot, or absent animation object returns before computing
new velocities. Motion flags `& 0x10`, and behavior `0x08000000` with current
outcome 1, choose ordinary `FUN_0021ACB0` instead.

The duration parameter `N` defaults to 8. When attack-payload flags lack
`4/8` and have `1/2`, its signed halfword `+6` selects an animation-relative
value: `-0x7FFF` uses animation length minus 2. Otherwise `0x7FFF` first
becomes -1, and every resulting negative value uses
`value + length - 1 - animation-row[+4]`; nonnegative values are used directly.
It then clamps `N` to `[4,6]`, including the default 8. This is an authored
calculation parameter, not a measured hold duration.

At `0x0023F878..0x0023F954`, the timer gate is `S[+0x1E8] <= N`.
Let E denote the computed-approach eligibility result. If record byte `+0x19`
is zero, E is simply prior outcome `S[+0xA41] != 0`; that branch overrides
the earlier facing/range checks. Otherwise E requires equal
`S[+0x990]/S[+0x326]`, centered distance at most `S[+0x138]`, current
outcome other than -2, and prior outcome 1. In this latter case E is cleared
when P is grounded and centered distance is less than `0.75` times the
comparison radius. This is the actual byte-dependent predicate, not a
single range check shared by every authored variant.

For the target-refresh branch, start with `T = P.position`. If P's grounded
bit is set, replace `T.x` with
`T.x - sign(S+0x326) * (wS/2 + wP/4)`, where facing 0 supplies +1 and
facing 1 supplies -1. For exact behavior group `record[+0x14] & 0x7C == 0x10`,
also add `(hS+hP)/4` to `T.z`. Other groups do not add this height offset.
The target-refresh branch requires E; its alternative reuses `S+0xAF0`.

At `0x002400D4..0x002401EC`, set `d = T-O`, `r = lengthXYZ(d)` and
`C = S+0x13C`. If `r > C`, use `d = C*d/r` and retained length `L = C`.
Otherwise use `d = (1+wS/r)*d` and retain `L = r`. Reverse only `d.x`
when `S+0x990 != S+0x326`, then store `O+d` at `+0xAF0`. No zero-distance
guard precedes the `wS/r` division; these instructions do not establish
which authored/play states avoid that input.

The next stage sets the intermediate vector's Y to zero and computes
`a = wrap(pi/2 + atan2(d.z,d.x))`. Here `wrap` subtracts `2*pi` once above
`pi` and adds it once below `-pi`; the constants are float words
`0x3FC90FDB/0x40490FDB/0x40C90FDB`. Select center `c = pi/2` for `a > 0`,
otherwise `-pi/2`. The angular half-width is `0x3F9C61AB` when behavior bit
2 is set and P is ungrounded, otherwise `0x3F5F66F3`. Clamp `a` into
`[c-half_width,c+half_width]`, then set
`alpha = wrap(-wrap(a-pi/2))`. The final stored target is
`O + RY(alpha)*(L,0,0,0)`, where the column-vector rotation maps
`(x,y,z)` to `(Crot*x+Srot*z,y,-Srot*x+Crot*z)`.

`FUN_00152508/00152340` construct `Crot/Srot` through a VU polynomial and
square root, so replacing them with ideal trigonometric functions is an
approximation. Its polynomial coefficients are the four float words at
`0x003F7680`: `0x362E9C14/0xB94FB21F/0x3C08873E/0xBE2AAAA4`.
More explicitly, for input alpha it sets
`beta = pi/2 + alpha` if alpha is negative, otherwise `pi/2 - alpha`.
The VU computes `p = beta + c3*beta^3 + c5*beta^5 + c7*beta^7 + c9*beta^9`
in that successive-add order, with c3/c5/c7/c9 given by the preceding words
in reverse order. It sets `Crot = p` and
`Srot = sign(alpha)*sqrt(1-p*p)`, using the nonnegative sign at zero.
`FUN_00151FF0` confirms the column-vector multiplication. The intermediate
rotation/`atan2` result at scratch `+0x84` is not used to choose the final
angle; the later facing-angle lookup overwrites that scratch word.

Finally, with update scalar `dt = S+0x1AC`, advance
`q = min(S[+0xA48] + (pi/2)*dt/(N+1), pi/2)` and store q at `+0xA48`.
The envelope is `g = 0.25*cos(q-pi/4)*min(B,1.25)`, where
`B = FUN_00307320(S)` starts at 1 and adds `node[+0x84]-1` for each
enabled node (`node+0x6C != 0`) in S's `+0x8C4/+0x8C8` list.
For final displacement `v = target-O`, store
`S[+0x994] = max(g*v.x / sin(facing_angle[S+0x98C]), 0)` and
`S[+0x998] = g*v.z`. The scalar cosine and sine are
`FUN_0016EFB8` and `FUN_0016F2E8`; their small-angle kernels and quadrant
branches distinguish the two. These are velocity writes, not direct position
integration or proof of a player-visible trajectory.

The gating/branch lifetime is explicit at `0x0023F998..0x0023FA58`:
secondary event 0 with clear `+0xA46` selects bit 2 only while the timer
window and E both hold; otherwise it sets bit 1.
Loss of either gate turns bit 2 into bit 4. The computed workspace path
requires nonzero `+0xA46` with neither bit 1 nor bit 4. The other paths may
use row motion or reduce prior velocities; they must not be represented by
the computed equation. Scratch allocation advances the shared `+0x1C0`
cursor by `0xA0`, and `0x0024066C..0x00240670` restores it after the computed
path. It owns no persistent partner allocation.

Related reset helper `FUN_0023EF30` clears `+0xA46/+0xA47/+0xA48`.
It is called by base fighter initialization `FUN_00214A40`, action exit
`FUN_0023BDC0`, the zero-motion-classification exit in `FUN_0023C230`,
and a character callback `FUN_00283A70`. These fields have per-execution
lifetime rather than storing another participant.

The sole reported direct caller of `FUN_0023EF50` is `0x002485A0` in
`FUN_00248580`, after that caller rejects fighter byte `+0x63` bit `0x1`.
For behavior `0x04000000` plus category `0x200` and primary cursor below 5,
the helper clears grounded bit `0x80` and moves a negative vertical speed
toward zero. This is sender-side handling of the same flag used to retain
and rotate the held receiver. It complements the attachment pass, which
always clears the attached receiver's grounded bit and clamps its negative
vertical speed.

The other direct caller of `FUN_0023E3C0`, `FUN_00239B00` at
`0x00239BDC`, adjusts a chain-selection signature for mode 1 when the
current action is category `0x200` with behavior `0x80`. It clears signature
bits `0x3000` and, when current progress is at least `0.75`, adds `0x1000`
only for a direction pair `0x4000` if the predicate is true or `0x8000`
if false. The interval `0x00239B74..0x00239C08` confirms this logic.
The progress value is the shared authored-window query, not unconditional
elapsed action time. Full chain matching belongs to
[Action commands](action_commands.md#fixed-chain-eligibility-masks).

## Contact admission and substitution boundary

`FUN_0021ED70` sends each surviving attack-side contact bit `0x100` to
`FUN_0021F610(sender)`. That function resolves the sender's current record,
uses `FUN_0023E2E0` for the guard decision, applies ordinary source/receiver
admission, rejects positive receiver `+0x230`, and calls
`FUN_00222C10(receiver, record)`. The last helper admits a nonnull record
when the receiver's cached record differs/is null, or when a matching cached
record has repeat count `+0xE5C > 1`. A same-record final repetition is
therefore not a fresh admitted connection at this stage.

Its outcomes are `0` rejected, `1` ordinary connection, `-1` guarded, and
`-2` intercepted by substitution. Before publishing the result through
`FUN_002391D0`, it asks `FUN_00229130` about substitution with the
anticipated receiver major/substate. Both the ordinary and the alternate
effect-backed paths can produce `-2`; their timing, resource gates and
source kinds belong to [Substitution](../characters/substitution.md). Capture category
alone does not bypass this predicate.

The instruction interval `0x0021F7B0..0x0021F844` confirms the two
substitution calls, their final argument `0/1`, and the commits
`FUN_002297D0(receiver, 0x211, 0)` or
`FUN_002297D0(receiver, 0x11, 1)`. Arbitration removes the corresponding
attack/receive bits after outcome `-2` and clears the receiver's record
through `FUN_00222BB0`. On an ordinary surviving receive bit 1 it instead
installs the paired fighter in `+0xE58` and publishes the sender's record
through `FUN_00222A80`, before accepted-hit routing.

`FUN_002391D0` writes outcome byte `+0xA40`, updating outcome auxiliaries
when requested. The common automatic continuation, which requires outcome 1
and the partner's resolved accepted-hit record to equal the sender's current
record, is owned by
[Combat action execution](combat_action_execution.md#continuation-and-common-exit-decisions).
In the sampled records below it is the capture-to-release link: the release
record's continuation byte names the starter and its signature contains
`0x08000000`. It does not select a new participant.

### Other direct category consumers

The resident classifier xrefs report eight callsites in seven functions.
Their complete containing bodies were inspected. These additional consumers
show why category classification is broader than guard handling:

| Consumer / callsite | Capture-specific effect |
| --- | --- |
| `FUN_0021B460 / 0x0021B5EC` | Classification 3 uses the sender's facing, reversed when action float `+0x3C` is negative, to derive the receiver's facing; `FUN_0023E3C0` and float `+0x28` can further change the result |
| `FUN_002297D0 / 0x00229824` | For substitution code low nibbles `0x11`, the extra code bit `0x100` is added under a facing match only when the partner's capture classification is zero |
| `FUN_00221600 / 0x002220A0` | Its major-5 branch checks the partner's capture classification before consulting ordinary reaction helper `FUN_00230FF0` |
| `FUN_002222F0 / 0x00222418, 0x00222430` | Either fighter's nonzero classification prevents this ordinary paired body-separation block |
| `FUN_002302C0 / 0x00230490` | Classifications 3/4 reject the request whose caller would clear retained hit provenance and enter `(3,0x1F)` |
| `FUN_00276CC0 / 0x002782A0` | The Yellow Flash's callback can dispatch pending `+0xA3E` during classification 1 under its action/cursor gates |
| `FUN_0027F9B0 / 0x0027F9D0` | Classic Naruto's Nine-Tailed form callback dispatches a pending index other than `-1` during classification 1 before its action-specific effects |

The request/cancel contracts remain in
[Combat action execution](combat_action_execution.md#input-interruption-of-an-executing-action).
These code paths do not establish a universal escape command or a separate
target-selection mechanism.

For a receiver in major 5, that separate `FUN_002302C0` request checks
`FUN_00230CE0(receiver,-1)`, which returns zero for every held substate
`0x4A..0x4E`. Instructions `0x00230414..0x00230438` and the five matching
jump-table words at `0x005C25A0..0x005C25B0` establish that held substates
are not explicitly blacklisted there. Its outer gates still require zero
`+0xB00/+0xB10`, grounded bit `+0x63 & 0x80`, capability `+0xBB4 & 0x10000`,
and logical request `0x100000` or both `0x8/0x10000`.
Successful attachment clears that grounded prerequisite. Thus this request
is excluded by the bound receiver's grounded state after the attachment
pass, not by a universal no-escape flag. Reachability before attachment or
with an absent anchor is unresolved. The two ordinary input-recovery state
lists also omit `0x4A..0x4E`; their complete conditions remain in
[Hit response](hit_response.md#input-driven-recovery-actions-during-ordinary-response).

The first callback's table is `0x00481FB0` for definition ID 39
`0x004877D0`; its pending dispatch additionally requires secondary cursor
greater than 0 for source indices `0x1D/0x20/0x2D`, or greater than 2 for
`0x23`. ID 47 definition `0x004A68A0` instead has slot 2 at table
`0x004A13C0` pointing to `FUN_0027F9B0`, with no corresponding cursor
threshold at its initial pending-dispatch branch. These are concrete
character differences in how a selected release can begin.

## Representative capture and release records

This bounded sample read the complete action arrays for IDs 57, 58, 61,
18 and 51, then inspected relevant category records and selected complete
phase sequences. It does not repeat or extend the all-definition census
owned by [Action commands](action_commands.md#complete-static-action-data-census)
and [Combat action execution](combat_action_execution.md#complete-authored-array-census).
Character ID names follow [Character identity](../characters/character_ids.md).

| Definition / capture to release indices | Capture record / phase start | Release record / phase start | Authored receiver selector `+0x2C` / release repeat `+0x2E` |
| --- | --- | --- | --- |
| 57, Naruto / `0x24 -> 0x25` | `0x004DA920 / 0x004D8F10` | `0x004DA974 / 0x004D8FF4` | `0x17 -> 0x16` / 3 |
| 58, Sakura / `0x21 -> 0x22` | `0x004DFD54 / 0x004DE4E8` | `0x004DFDA8 / 0x004DE5CC` | `0x18 -> 0x13` / 1 |
| 61, Temari / `0x20 -> 0x21` | `0x004F0540 / 0x004EEC84` | `0x004F0594 / 0x004EED68` | `0x17 -> 0x12` / 1 |
| 18, Classic Kankuro / `0x21 -> 0x22` | `0x0045CBF4 / 0x0045B614` | `0x0045CC48 / 0x0045B744` | `0x19 -> 0x12` / 1 |
| 51, Super Choji / `0x17 -> 0x18` | `0x004BBDCC / 0x004B9F20` | `0x004BBE20 / 0x004BA004` | `0x19 -> 0x14` / 1 |

All five displayed starters have category `0x100`, zero raw damage
`+0x24`, and repeat 1; their finishers have category `0x200`, raw damage
bits `0x3D4CCCCD` (`0.05`), signature family `0x08000000`, and continuation
byte naming the starter. Raw damage is an input to the common calculator,
not an observed HP loss. The zero-damage starter still has collision and
response data; it can select held state `0x4A/0x4B/0x4C` through the ordinary
response selector. Character callbacks may override that selector.

The first four displayed starters set behavior `0x4000`; Super Choji's
`0x17` starter has behavior `0x5` and lacks it. His additional starters
`0x19` at `0x004BBE74` and `0x1C` at `0x004BBF70` also have `0x5`.
They therefore do not obtain the common category-specific guard bypass
from `FUN_0023E2E0`. His separate starter `0x24` at `0x004BC210` does have
`0x4041`. The category is shared across both kinds; the guard result cannot
be inferred from category alone.

Sakura and Temari's displayed sequences have two nonterminal phases
(both animation-end condition `-16`, rate `0x100`) followed by terminal
`animation == -1`. Classic Kankuro's sequences include a third
nonterminal animation slot `0x3B` before the terminal. Naruto's starter
uses animation slots `0x83/0x84` with rates `0x128/0x100`; its phase-0
payload is `0x12`, phase 1 is `0x28`. His release uses slots `0x85/0x86`
with the same rates, phase-0 payload `0x12` with bank-0 attack interval
15..15 and bank-1 interval 6..6, and phase-1 payload `0x2A` with bank-0
interval 0..0. The animation-name pointers at
`0x004D603C..0x004D604B` identify these four slots as
`ANM_pnrwhol00..ANM_pnrwhol03`. These are native asset identifiers,
not measured hold durations or recovered player-facing move names.

The sampled airborne signature-context variants also preserve capture and
release pairs, but differ in receiver selector and behavior. Naruto's
`0x2C -> 0x2D` pair uses `0x18 -> 0x12` and release repeat 1;
Sakura's `0x29 -> 0x2A` pair uses `0x18 -> 0x15` and release behavior
`0x00104242`. Complete substitution
eligibility still depends on the common predicate and current state.

### Naruto's release callback changes the live record

The displayed `0x25` release's clean `0.05` value is not the value retained
through every response-selection call. Definition `0x004DAD80` has callback
table `0x004D56D0`; slot 3 contains `FUN_0029AC50`. For source action index
`0x25`, that complete callback obtains the remaining-repeat value through
`FUN_00231BF0(sender, receiver)` and the live current record through
`FUN_00217930(sender, -3)`, then writes these fields:

| Repeat-helper result | Live raw damage `+0x24` | Record halfwords `+0x46 / +0x48` | Response override |
| --- | --- | --- | --- |
| Below 2 | `0x3D99999A` (`0.075`) | `0x32 / -1` | `-1`, allowing common selection |
| Exactly 2 | `0x3D99999A` (`0.075`) | `0x30 / 3` | `0x3F` |
| At least 3 | zero | `-1 / 0` | `0x29` |

These record writes are outside the callback's mode-2 gate; only its receiver
motion writes `+0x9A0/+0x9A8/+0x9AC` are restricted to that mode. The
disassembly interval `0x0029AE84..0x0029AF38` confirms the two data-backed
response words and all record stores. Startup `0x00100198..0x001001C0`
sets `gp = 0x0060A9F0`; the words at `gp - 0x7498 / gp - 0x7494`
are therefore `0x00603558 / 0x0060355C`, whose clean bytes contain
`0x3F / 0x29`. `FUN_00232B80` calls response selection
with mode 2 before its damage wrapper `FUN_00224510`, so this is a concrete
capture-release example where live callback data must be considered before
using the clean raw-damage table. The repeat-helper result is conditional on
the receiver's cached source record and remaining count; it is not an elapsed
frame count. Damage division and scaling belong to [Damage](damage.md).

In mode 2, repeat result 2 also writes receiver `+0x9AC = 0.8`; result
at least 3 writes `+0x9A8 = -0.2`. Their float words at
`0x00603560/0x00603564` accompany the response constants above. The order
and meaning of the common receiver motion modifiers belong to
[Hit response](hit_response.md#velocity-modifier-order).

### Full-transform and hold-preserving variants

Two additional complete action arrays, IDs 50 and 84, supply examples of the
attachment branches not used by the first table:

| Definition / pair | Capture / release records | Capture selector / behavior | Release selector / behavior |
| --- | --- | --- | --- |
| 50, Possessed Gaara / `0x20 -> 0x21` | `0x004B6DE0 / 0x004B6E34` | `0x1B / 0x4041` | `0x13 / 0x4041` |
| 84, Tsunade / `0x2D -> 0x2E` | `0x0056F674 / 0x0056F6C8` | `0x1A / 0x4042` | `0x15 / 0x04004242` |

Possessed Gaara's authored selector `0x1B` maps to held response `0x4E`,
which receives the full anchor transform with relative scale and model flag
`+0x8D`. Callback slot 3 `FUN_002860D0` returns `-1` for action `0x20`, so
it supplies no character response override for that starter. The phase
sequences at `0x004B5898 / 0x004B597C` each contain two animation-end rows
and a terminal; release payloads are `0x12/0x28`. The held updater can
reselect a response on the second payload's `0x8` bit because release
behavior `0x04000000` is clear. Other common selector gates still apply.

Tsunade's starter maps selector `0x1A` to held response `0x4D`. Its rows
at `0x0056E210` are two animation-end rows and a terminal. Release rows at
`0x0056E2F4` have condition `-17`, payload `0x13`, then condition `1`,
payload `0x2A`, then terminal. Her response callback `FUN_002EF7E0` has no
`0x2D/0x2E` override. The release's `0x04000000` flag prevents the shared
held updater from using payload `0x8` for reselection while that action is
current. In callback `FUN_002EE660`, action `0x2E` phase 1 secondary event 0
calls `FUN_0031E490`, but that entire retail helper is `jr ra; nop` at
`0x0031E490..0x0031E497`. It supplies no receiver transition. Ordinary
action exit and contact routing must therefore be considered separately
from a presumed callback release; no additional callback release is proved
by this call.

### Additional authored release families

Two further complete arrays for definitions 39 and 47 were read, with
selected complete phase sequences and both response callbacks. They add to
the representative capture sample, not to the owning documents' complete
action or response censuses.

| Definition / pair | Capture / release records | Phase starts | Capture / release behavior | Selector low bytes / release repeats |
| --- | --- | --- | --- | --- |
| 39, The Yellow Flash / `0x1D -> 0x1E` | `0x004870C4 / 0x00487118` | `0x00485114 / 0x004851F8` | `0x9 / 0x109` | `0x18 / 0x14`, 2 |
| 39 / `0x20 -> 0x21` | `0x004871C0 / 0x00487214` | `0x004853C0 / 0x004854A4` | `0x60011 / 0x60091` | `0x17 / 0x10`, 1 |
| 39 / `0x23 -> 0x24` | `0x004872BC / 0x00487310` | `0x0048566C / 0x00485750` | `0x60021 / 0x600A1` | `0x17 / 0x12`, 1 |
| 39 / `0x25 -> 0x26` | `0x00487364 / 0x004873B8` | `0x00485834 / 0x00485918` | `0x4041 / 0x4242` | `0x17 / 0x15`, 4 |
| 47, Classic Naruto's Nine-Tailed form / `0x22 -> 0x23` | `0x004A6438 / 0x004A648C` | `0x004A48D4 / 0x004A49B8` | `0x4041 / 0x4201` | `0x19 / 0x15`, 1 |
| 47 / `0x2A -> 0x2B` | `0x004A66D8 / 0x004A672C` | `0x004A5124 / 0x004A5208` | `0x4042 / 0x40C2` | `0x18 / 0x12`, 1 |

Each displayed release has category `0x200`, clean raw damage `0.05`,
signature bit `0x08000000`, and continuation byte naming its category-`0x100`
starter. The first three ID-39 starters lack behavior `0x4000` and have
nonnegative predecessor bytes `0x1C/0x1F/0x22`; they are authored chained
capture variants rather than independent starter records. Their callback's
pending-release dispatch thresholds are recorded above. The ID-39 `0x25`
starter and both ID-47 starters have predecessor -1 and behavior `0x4000`.
The common automatic handoff still requires outcome 1 and matching accepted
source record; a continuation byte by itself does not establish connection.

The `0x25/0x26` sequences use ID-39 animation slots `0x8A/0x8B` and
`0x8C/0x8D`. Capture conditions are `-16/-16`, release conditions `-16/-18`,
each followed by terminal -1; both have payloads `0x12/0x28`. The release
phase 0 attack intervals are bank 0 `7..19` and bank 1 `10..19`. ID-47's
`0x22/0x23` sequences use slots `0x79/0x7A` and `0x7B/0x7C`, both
conditions `-16/-16` and terminal, with payloads `0x12/0x28`; release phase
0 uses rate `0x80`, then `0x100`. These are static rows and event windows,
not visible-duration measurements. Phase start addresses derive from the
definition's row base plus its clean record `+0x50` row index times `0x4C`;
the clean value is not already a runtime phase pointer.

ID-39 release `0x26` also demonstrates a response override through bounded
slot-3 target `FUN_00278310`: repeat-helper result below 2 selects `0x40`;
otherwise PRNG bit 0 selects `0x2C` when clear or `0x2B` when set. Mode 2
writes receiver motion multiplier `+0x9A0 = 1.5` or `0.005`, respectively.
`0x00278690..0x002786F0` and `0x00278830..0x00278898` corroborate selection
and the mode-gated store. This branch does not change the record's category
or free either participant. The clean selector `0x15` therefore does not
fix the release's final response. The wider callback response contract is in
[Hit response](hit_response.md#character-response-callbacks).

ID-47 response callback `FUN_002806A0` has no override for either displayed
pair. Its channel-3 callback's initial classification-1 dispatch consequently
changes the pending action through the normal setter, while channel 5 later
changes scene bone transforms before common attachment. The pending release,
receiver response and model transform are separate operations, not one
unconditional character callback that destroys the hold.

### Category changes also call cleanup

`FUN_0023E460` has three resident callsites outside major-8 cleanup:
`0x002EE520/0x002EE534` in `FUN_002EE380`, and `0x002E8FFC` in
`FUN_002E8E90`. Both complete helpers change which live action categories
are enabled and call position cleanup before disabling an active capture
variant. Neither helper searches for or replaces a participant.

Tsunade's `FUN_002EE380` reacts to a changed byte `+0x5944`. On its zero
mode, current release indices `0x21/0x27`, or current starter indices
`0x20/0x26` with outcome 1, call capture cleanup. It then restores category
words for indices `0x1E/0x1F/0x24/0x25` from the table at fighter `+0xB8`
and zeros them for `0x20/0x21/0x26/0x27`. The tables at
`0x0056F910..0x0056F92F` establish these index sets. Mode 1 swaps which set
is restored/zeroed. Callback `FUN_002EE600` supplies the mode from fighter
`+0x63` bit `0x20` for ID 84. This category-changing cleanup
does not alter the separate `0x2D/0x2E` pair above.

The clean `0x20/0x21` records at `0x0056F230/0x0056F284` have category
`0x100/0x200` and behavior `0x9/0x1`; neither has `0x04000000`.
After the zero-mode helper clears those live category words, common
attachment no longer passes `0xF00`. A still-held receiver whose partner
remains in major 8 reaches the missing-`0x100/0x200` branch of
`FUN_002316D0` and enters `(0,0)` on that updater. Position cleanup, category
disabling and receiver transition are separate operations; the helper does
not synchronously free the partner or clear its participant pointer.

For ID 81, `FUN_002E8E90` reacts to changed byte `+0x6238`. On its zero
mode, a current category-`0x200` record, or category `0x100` with outcome 1,
calls capture cleanup before restoring category words for indices
`0x15..0x2A` and zeroing them for `0x2B..0x37`. Mode 1 swaps the
enabled sets. The direct caller `FUN_002E9AB0` gates this helper on fighter
ID `0x51` and supplies the same `+0x63` bit `0x20` mode. This establishes
an interruption path during category activation changes, without assigning
a player-facing name to that mode.

## Attachment scheduling

The sole direct resident xref reported for `FUN_0023EAA0` is call
`0x0025034C` in `FUN_00250230`. That list pass refreshes every fighter's
model, runs every fighter virtual slot `+0x20`, runs callback channel 5 for
every fighter, then runs attachment for every fighter. Attachment therefore
uses the transforms resulting from those preceding passes. Its loop is not
restricted by positive pause at the callsite; the attachment body's own
state/category/partner/anchor gates still apply.

This order proves when the position binding is applied relative to the
examined model callbacks. It does not prove every indirect invocation or
all frame scheduling; [Battle lifecycle](../session/battle_lifecycle.md) owns the
coordinator schedule.

### Selected pre-attachment callbacks and model lifetime

**Observation:** The complete virtual tables for IDs 39, 47, 50 and 84 at
`0x005DAC40/0x005DAB20/0x005DAA90/0x005DA340` all select `0x002504A0`
for the pre-attachment virtual slot `+0x20`. No function is defined at that
address; its bytes `08 00 E0 03 00 00 00 00` establish `jr ra; nop`.
There is no character-specific model replacement in that particular slot.

Callback channel 5 reads table offset `+0x10` (jump-table word
`0x005C2084 = 0x002177E0`). For these current-action indices (all at least
4) the dispatcher uses the fighter's own `+0xA8` table; its contract is
owned by [Character assets](../../game/character_assets.md#per-character-code).

| Definition / channel-5 table | Target before attachment | Bounded effect |
| --- | --- | --- |
| 39 / `0x00481FB0` | null | No channel-5 call |
| 47 / `0x004A13C0` | `FUN_00280BA0` | Under node bit 1 and fighter `+0x61 & 0x20`, calls `FUN_0027EE80`, then hides two optional named objects in its auxiliary scene `+0x582C` by zeroing basis columns and setting `+0x8D`; it does not free a fighter or clear `+0xE70` |
| 50 / `0x004B2500` | `FUN_002862D0` | Hides one optional object for actions `0x18/0x1C/0x1D` at cursor gates; its `0x20/0x21` capture pair does not meet those gates |
| 84 / `0x0056A3D0` | null | No channel-5 call |

The full ID-47 helper `FUN_0027EE80` includes authored `0x22/0x23` and
`0x2A/0x2B` capture events, derives reach offsets, and writes selected bone
matrices in its primary and auxiliary scenes. It resolves optional names
with argument 2 equal to 1 and skips absent objects. It stores no new
participant and contains no model-destruction call. This is a concrete
pre-attachment transform producer; it does not prove every anchor matrix is
always present. General skeleton binding remains in
[Model and skeleton runtime](../../runtime/rendering/model_runtime.md#animation-binding-to-scene-nodes).

The four record-provided anchor strings are respectively
`OBJ_eff_dummy_fouhol0`, `OBJ_eff_dummy_nrvhol0`,
`OBJ_eff_dummy_gavhol0`, and `OBJ_eff_dummy_tnwhol0`, with pointers at
`0x00481EF8/0x004A1398/0x004B2450/0x0056A3A8`. The bytes confirm nonempty
names, not successful lookup in every loaded scene.

Successful common setup `FUN_00215950` allocates and publishes `+0xE70`
before returning success; `FUN_002151E0` then initializes `(0,0)` and enables
node update bit 1. The initial reciprocal participant graph and its separate
registry owners are established in
[Battle entities](../session/battle_entities.md#initial-cross-reference-graph).
However, `FUN_00250230` itself checks only each list node's presence before
its model/attachment passes, not update bit 1. `FUN_0023EAA0` reads partner
state without first checking `+0x20` for null. Successful construction plus
ordinary scheduling explains the intended prerequisites; it is not a proof
of availability under every malformed or interrupted graph.

The selected virtual-`+0x1C` functions
`FUN_00276C70/0027EB40/002856C0/002EE330` all return zero after an optional
packed-mode BTL call. They do not request removal by their return values.
Their concrete destructors
`FUN_00276BF0/0027EA60/00285630/002EE2B0` all reach common
`FUN_00215720 -> FUN_00215E70`, then `FUN_00214840`, before freeing the
fighter. ID 47 first destroys its auxiliary scene/model trio; ID 50 first
releases its 17-entry geometry bank. The instance ownership is documented in
[Common fighter-owned children](../session/battle_entities.md#common-fighter-owned-children).

For capture lifetime specifically, those destructors and the inspected
common teardown contain no call to `FUN_00238D00/0023E460` and no explicit
held-partner release or reciprocal `+0x20` invalidation. `FUN_00215E70`
destroys and clears `+0xE70` at `0x00215E80..0x00215E98`, but does not clear
the other fighter's pointer. The current-state setter's interruption cleanup
and whole-fighter destruction are therefore distinct paths. The normal
form replacement rebuilds both participants, as recorded in
[Awakening](../characters/awakening.md#static-reconstruction-order); an isolated participant
removal between receiver update and attachment remains unproved. Neither
the local anchor scratch pointer nor the full-transform write establishes
general stale-pointer protection.
