# Composition attachment dynamics

This document investigates how retail NA2 (`SLPS-25837`) executes the
composition-child attachment block that the `0x2300` resource installs at a
composition descriptor: chain construction from the composition hierarchy, the
three per-chain coefficients, child-anchored collision volumes, per-step
integration, rebase and destruction, and the recovered direct callers of the
step. Addresses are resident `SLPS_258.37` EE addresses unless an overlay is
named; see [address conventions](../../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** Runtime construction, coefficients, collision volumes,
  integration order, rebase, destruction and direct step callers of
  composition-child attachment chains.
- **Exploration depth:** Construction, coefficient storage, collision-node
  construction, the complete manager step, rebase, destruction and the
  following-point correction were traced through decompilation with instruction
  corroboration where the decompiler misrecovers arguments. All seven recovered
  direct step callers in the resident executable and `BTL.BIN` were inspected;
  a direct-call search of `ETC.BIN` found none. Broader scene-wrapper
  scheduling was not traced.
- **Confirmed coverage:** Attachment blocks create hierarchy-derived chains with
  three consumed coefficients (velocity retention, segment-length correction,
  authored-shape attraction) and child-anchored transformed unit-sphere
  collision volumes. One step refreshes collision nodes, optionally rebases,
  integrates each point with a global force and Z lower bound, then applies
  attraction and length correction. Rebase, step and manager destruction are
  distinct operations.
- **Unresolved or untested:** The writers of the global force vector
  `0x00618F50` and Z lower bound `0x00618F60`, every outer scheduling owner,
  coefficient ranges across the authored CCS corpus, and visible consequences
  of zero center-distance or singular collision scale remain unresolved.
- **Deliberate exclusions and overlap:** [CCS object types](../../game/files/ccs_object_types.md)
  owns `0x2300` parsing and the installed compact arrays;
  [Model runtime](model_runtime.md#composition-hierarchy-and-matrix-lifetime)
  owns composition hierarchy and skeleton matrices;
  [Effect-generator commands](../effect_generator_commands.md) owns authored
  generator actions and their anchors; [Scene playback owners](../scene_playback_owners.md)
  and [Timer primitives](../timer_primitives.md) own broader caller timing.
- **Evidence limitations:** Static retail code only; no live instance state was
  observed. Decompiler signatures misrecover the float coefficient arguments, so
  instructions take precedence. Direct-call negatives do not exclude indirect
  calls, wrapper owners or other encodings. No seconds or displayed-frame
  frequency is assigned to a step.

## Construction and ownership

**Observation, high confidence.** The `0x2300` finalized attachment structure
at composition descriptor `+0x18` has two separately consumed arrays.
`FUN_001952F0` constructs the composition's scene-child vector `+0x98` with count
`+0x9C`, evaluates it through `FUN_00195600` and `FUN_00195510`, then passes the
attachment structure to `FUN_00189B60`. The returned `0x0C`-byte manager is stored
at composition runtime `+0x94`; byte `+0x9E` bit `0x01` marks its ownership.
This system changes scene-child transforms. It neither interprets action command
bytes nor creates a particle generator.

## Chain coefficients and anchoring

For the first array, `FUN_00189B60` creates a temporary `0x30`-byte hierarchy
builder through `FUN_0018A3C0`. The builder creates `0x28` bytes per composition
child, copies the child's source record and runtime pointer, and links each child
under the parent index in the composition descriptor; `-1` selects its root.
Each finalized `0x10`-byte attachment entry selects one child by its signed
halfword at `+0x0C`. Its three floats are forwarded in registers `f12..f14`
at `0x00189BFC..0x00189C10`. `FUN_0018A570` stores those floats and the selected
child index in a parameter node. The decompiler recovers these as integer
arguments; the instructions establish float registers.

`FUN_0018A1E0` walks the hierarchy three times with `FUN_0018A090`,
`FUN_0018A050`, and `FUN_0018A000`. A child's parameter node overrides an
inherited parent node. A newly marked child without an already marked parent
starts a separate `0x20`-byte chain group; participating children receive
`0xA0`-byte states. `FUN_0018AFA0` stores the child scene pointer at state
`+0x80` and the first child's state pointer at `+0x98`; the flattened traversal
list uses state `+0x9C`. `FUN_0018B200`/`FUN_0018B240` establish hierarchy-node
`+0x00` as parent, `+0x04` as first child, and `+0x08/+0x0C` as sibling links;
`FUN_0018A050` reads first-child `+0x04`, not parent `+0x00`, for state `+0x98`.
Thus authored composition hierarchy supplies the attachment
chain. The temporary hierarchy and parameter nodes are freed after construction;
the chain states retain the resolved runtime pointers and coefficient values.

| Authored float within the finalized `0x10` entry | Downstream contract |
| ---: | --- |
| `+0x00` | `FUN_0018AE20` stores it at the first-child state's `+0x88` when that state exists. `FUN_0018AC80` multiplies state velocity `+0x70` by this coefficient each attachment step before adding the global force vector. It is a per-step velocity-retention coefficient. |
| `+0x04` | Stored at current state `+0x8C`. `FUN_0018A840` multiplies `(rest_length - current_segment_length)` by it to correct the following point along the segment direction. It is a segment-length correction coefficient. |
| `+0x08` | Stored at current state `+0x90`. When nonzero, `FUN_0018A840` moves the following point toward the transformed authored segment endpoint by this fraction before length correction. It is an authored-shape attraction coefficient. |

`FUN_0018AE40` initializes current and previous points (`+0x50`, `+0x60`) from
the scene child's evaluated position, retains its local transform, derives the
rest direction from the first child's local translation, and stores the direction's
length at `+0x84`. The parameters operate on these runtime points rather than on
CCS records or numeric bone IDs.

## Authored offsets and collision volumes

**Observation, high confidence.** The second array uses finalized `0x1C`-byte
entries. `FUN_00189B60` reads the child index at entry `+0x18`, resolves it in
the composition's scene-child vector, and sends the first and second float
triples to `FUN_00189E20`. The resulting `0xD0`-byte node retains that child at
`+0xC0` and links through `+0xC8` in manager `+0x04`.

`FUN_0018B090` builds a local matrix at node `+0x80`: the first triple becomes
translation `+0xB0/+0xB4/+0xB8`, and the second triple becomes diagonal scale
`+0x80/+0x94/+0xA8`; `+0xBC` is one. `FUN_0018AFE0` combines it with the child's
evaluated transform, or copies the local matrix when there is no child, then
computes the inverse at node `+0x40` through `FUN_00190BC0`.

`FUN_0018AC80` transforms each chain point by that inverse. If squared XYZ
length is less than one, instructions `0x0018AD30..0x0018ADDC` normalize it onto
the unit-radius surface and transform it back by the node's forward matrix.
They set state byte `+0x94` and node byte `+0xC4` bit `0x01` on a correction.
The second array therefore specifies child-anchored transformed unit-sphere
collision volumes; translation and diagonal scale provide authored center offsets
and axis extents. This geometric contract is established by the consumer, not by
the CCS explorer's independent `Dynamics` label. Zero center-distance and singular
scale are not guarded in these inspected branches; no claim is made that retail
data contains them.

## Attachment step, rebase, and destruction

`FUN_00194360` calls `FUN_00189D10` when composition runtime `+0x94` is nonzero.
The complete manager step has this ordering:

1. Refresh every second-array collision node with `FUN_0018AFE0`, including
   its inverse and clearing its per-step correction byte.
2. If manager byte `+0x08` is set, clear it and call `FUN_0018A6D0` for every
   chain. That routine computes the displacement from the chain's retained first
   point to its anchor's current position and adds that same displacement to
   every current and previous chain point. It rebases positions; it does not
   clear every velocity or rebuild a chain.
3. For every chain, `FUN_0018A5F0` evaluates the anchor and initializes the
   first point, then calls `FUN_0018AC80` for each point. The direct update is
   `previous = current`, `velocity = velocity * coefficient + force`, then
   `current += velocity`, followed by collision-volume correction and a Z lower
   bound. Instructions `0x0018AC9C..0x0018AD08` and `0x0018ADF0..0x0018ADF8`
   corroborate these operations. The force vector is read from `0x00618F50` and
   the Z lower bound from float `0x00618F60`.
4. For every state that has a following state, call `FUN_0018A840`. It applies
   the attraction/length corrections and writes a reconstructed local transform
   to child `+0x40..+0x7F`, setting child byte `+0x8D` to one. Terminal points
   are integrated but do not execute this following-point transform path.

Within `FUN_0018A840`, instructions `0x0018AAB4..0x0018AAD4` also replace the
current state's velocity with `current - previous`. Collision projection and
the Z bound occur before attraction/segment correction; that correction pass
does not repeat the collision-volume search. The first-child link supplying rest
shape and the flattened next link supplying a corrected point are separate
fields; their equality is not assumed for every branching hierarchy.

There is no delta-time argument or frame-count loop in `FUN_00189D10`; this is
one integration/correction pass per invocation. `FUN_00194340` sets the rebase
latch at manager `+0x08`; it does not immediately run the step. Global force and
lower-bound writer ownership is not established by their absent direct xrefs.

`FUN_00194290` destroys an owned attachment manager through `FUN_00189F80`,
clears composition `+0x94`, and clears ownership bit `0x01`. Composition
destructor `FUN_001951A0` also destroys an owned manager before destroying
its children. The manager destructor frees chain groups and their states through
`FUN_00189F20`/`FUN_0018A7A0`, frees collision nodes through `FUN_00189EC0`, and
then frees the manager for a positive destructor argument. No emitter object is
part of this teardown.

## Bounded caller coverage

Resident direct callers of `FUN_00194360` comprise the animation-scene wrapper
`FUN_001BB6F0` (walks scene composition list `+0xE4`), auxiliary composition owner
`FUN_002B3D70` (owner field `+0xEE0`), and `FUN_002CE0D0` (first owner word).
Both latter routines write the composition's local transform before stepping it.
`FUN_002CE0D0` suppresses that path when owner halfword `+0x30` bit `0x01` is
set; it also prepares the global force vector used by attachment integration.

All four direct `jal FUN_00194360` matches in retail NA2 `BTL.BIN` were inspected:

| Imported address / live call address | Owner and condition |
| --- | --- |
| `0x007261B8` / `0x007261F8` | Imported function `FUN_00725FF0`, live entry `0x00726030`: when owner `+0x24` composition exists, evaluates owner `+0x28` anchor, publishes the composed local transform, and steps `+0x24`. Fighter byte `+0x61` bit `0x40` requests rebase first. |
| `0x007262DC` / `0x0072631C` | Imported `FUN_007262A0`, live entry `0x007262E0`: for nonzero owner `+0x24`, calls virtual slot `+0x20`, requests rebase, and immediately steps the composition. |
| `0x007270C8` / `0x00727108` | Imported `FUN_00726E90`, live entry `0x00726ED0`: composition at owner `+0x28`; publishes its transform, then steps. Fighter byte `+0x61` bit `0x40` requests rebase. An additional branch tests fighter halfword `+0xB8C == 0x29`, saved owner halfword `+0x24 == 0x31`, fighter `+0x192 == 0`, and `FUN_002118A0`, then calls `FUN_00194B60` and requests rebase. These state numbers are not assigned action names here. |
| `0x007271EC` / `0x0072722C` | Imported `FUN_007271B0`, live entry `0x007271F0`: same virtual-call/rebase/step pattern for owner `+0x28`. |

BTL/ETC imports omit the `0x40` MWo3 header; live operands are retained, so only
imported addresses/entry labels receive that adjustment. The exact direct-call
byte search found no `FUN_00194360` call in `ETC.BIN`. Composition construction
has many additional callers; construction itself does not establish that a
given owner has a nonzero attachment block or steps it.
