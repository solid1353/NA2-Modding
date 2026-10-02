# Practice position reset

This document records provisional research for a Practice position-reset
feature. No position-reset feature or input binding is implemented by this
research. The retail snapshot API cannot supply a position bookmark. Native
initial placement and recovery share a stage placement helper, which supplies
a concrete candidate building block.

## Research coverage

- **Assigned scope:** Research feasibility and design options for a Practice position-reset feature.
- **Exploration depth:** Read-only GhidrAssist inspection covered the complete
  resident resource-snapshot pair, its identified reconstruction callers,
  native placement and recovery, all 74 table-selected fighter initialization
  slots, common action transitions and major-state exit dispatch, neutral
  phase/animation selection, movement/contact updates, and paired geometry.
- **Confirmed coverage:** Resource snapshots omit position, orientation,
  stage section and action state. Reconstruction restores resource snapshots
  separately from its battle-object setup. All audited fighters share native
  initial placement. The field matrix identifies the state that a proposed
  in-place reset must preserve, reset or refresh, and its ordering constraints.
- **Unresolved or untested:** No complete in-place reset or arbitrary-action
  interruption contract is established. Character-specific callbacks,
  surviving projectiles/support objects, contact refresh after relocation,
  exchanged spatial sides, and arbitrary airborne/wall/corner bookmarks remain
  unproved. Bookmark eligibility and lifetime are proposed constraints.
- **Deliberate exclusions and overlap:** Implemented Practice behavior remains
  owned by [Practice](../practice.md). Retail architecture remains owned by
  [Practice-mode knowledge](../../knowledge/gameplay/practice_mode.md),
  [movement](../../knowledge/gameplay/movement_and_physics.md),
  [stages](../../knowledge/gameplay/stages.md),
  [target selection](../../knowledge/gameplay/target_selection.md) and
  [hit response](../../knowledge/gameplay/hit_response.md).
- **Evidence limitations:** Findings are static against clean NA2
  `SLPS_258.37` and `BTL.BIN`, identified in
  [Retail game file identities](../../knowledge/game/files/file_identities.md).
  The preserved BTL import omits the `0x40`-byte header; raw call operands
  remain live addresses. Incomplete function boundaries and xrefs limit
  conclusions from decompilation or missing references alone.

## Resource snapshot and reconstruction implications

The complete resident pair `FUN_001ECC00` / `FUN_001ECDE0` consumes only mask
bits `0x01`, `0x02`, `0x10` and `0x20`. Its fields and item-cache behavior
are owned by [Discrete Practice-controller reset](../../knowledge/gameplay/practice_mode.md#discrete-practice-controller-reset).
The position-reset implication is confirmed: invoking that pair does not
capture or restore fighter transform `+0x30/+0x40`, stage section `+0x9F6`,
motion, target, or action state. A position bookmark would need its own
explicit contract rather than an unused mask bit passed to this API.

The identified capture callers `FUN_001EE1C0` and `FUN_001EE500` tear down
battle owners after saving resources. The latter chooses a selected-side
mask from the controller state; restore caller `FUN_001EF330` reconstructs
the battle before applying its resource mask. Direct-JAL byte searches found
no calls to either snapshot routine in the preserved BTL import. That bounded
negative does not exclude indirect calls or establish a whole-game absence
of another position-storage mechanism.

Resident reconstruction `FUN_001EF330` first creates/adopts the battle owner,
publishes fighter pointers to manager `+0xDE4/+0xDE8`, resets its owner through
BTL live `0x007095E0`, and then restores resources when the saved-battle
condition is `2`. Its two masks differ only in the global timer bit. The
remaining construction includes inventory, camera and other battle objects;
this is broader than an in-place position setter. Its fighter initialization
entry is described below; invoking the entire reconstruction would reset other
owners as well.

## Native placement as a candidate

The stage-node storage and recovery consumers are owned by
[Stages](../../knowledge/gameplay/stages.md#resident-generic-factories-and-mandatory-records)
and [Timed downed recovery](../../knowledge/gameplay/hit_response.md#timed-downed-recovery-and-get-up-choices).
For this feature, the useful confirmed contract is a tuple of position
`vec4`, orientation `vec4`, and section. BTL live `0x00708FD0` (imported
`0x00708F90`, complete-file `0x0550D0`) copies side 0/1 node positions,
adds `200.0` to component 2, forces component 3 to `1.0`, and returns section
`1` for native stage slot `12`, otherwise `0`. Side 0/1 orientation component
2 is `+pi/2` / `-pi/2`. The helper's complete body through live `0x007090AC`
was corroborated with MCP bytes because the imported disassembly boundary
ends prematurely at a branch.

Resident `FUN_00216920` wraps this helper; `FUN_00216970` and recovery
`FUN_00235690` use its live `0x007090B0` wrapper. The latter recovery path
can also apply section projection through live `0x007090D0`. A direct-JAL
audit additionally identified consumers at BTL live `0x007945E0` and
`0x00797980`: both obtain the two side tuples and compute a midpoint with
opposite offsets before editing objects selected by their `+0x31C/+0x4CC`
slots. The second explicitly writes section/target-section fields. Their
complete enclosing gameplay roles remain unclassified; these uses do not
establish a general Practice reset entrypoint.

### Initial placement is shared by all table-selected fighters

Resident `FUN_0024D830`, the common fighter initialization virtual method,
calls live `0x00708FD0` at resident `0x0024D860`, passing fighter `+0x28`,
side bit `+0x60 & 1`, and destinations `+0x30/+0x40`. It stores the result
at `+0x9F6` and sets byte `+0x61` bit `0x40`. This establishes the initial
placement consumer separately from the recovery paths.

The complete set of 74 concrete final vtables listed in
[Battle entities](../../knowledge/gameplay/battle_entities.md#complete-table-selected-concrete-lifetime-paths)
was checked through MCP memory at resident `0x005DA140..0x005DB1A0`.
Every table's `+0x0C` entry is `0x0024D830`; there is no alternative entry
in that bounded table-selected fighter set. Resident reconstruction reaches
it through live BTL `0x007095E0` and the generic list virtual-`+0x0C` pass.

The method additionally zeroes planar/vertical speed `+0x994/+0x998`
through a direct snap or unit-factor approach, calls the AI initializer for
nonzero controller bits `+0x60[5..8]`,
refreshes a shared render field through live `0x00708C30`, clears motion mode
`+0x988` and retained motion scalar `+0x9B0`, derives all three facing
halfwords `+0x98C/+0x98E/+0x990` from orientation `+0x48`, clears retained
attack pointer `+0xE54`, fills eight position-history vectors
`+0x840..+0x8BF`, and requests neutral `(0,0)` through `FUN_00217E40`.
This is a confirmed placement-and-initialization recipe, not proof that
calling it during any active attack cancels every dependent object safely.

### Action transition requirements

The complete `FUN_00217E40` path runs current-action exit dispatch
`FUN_00217BD0`, then destination setup `FUN_00217D30`, before changing state.
On a changed major/substate it resets the primary timeline and invokes BTL
live `0x0071EEF0`; it then selects action descriptor `+0xA30` and initializes
the action's ground/air history. Same-state `(0,0)` requests can return zero
without restarting the timeline unless forced. A proposed reset needs a
deliberate decision about restarting neutral, rather than assuming a state
assignment does it.

The neutral descriptor at BTL live `0x0089AEB0` points to `ACT_NUT_0` and
the phase record at live `0x00899E90`: animation slot `0x29`, start `0`,
rate `0x100`. Phase consumer live `0x0071F640` selects the animation through
`FUN_00218190` and sets its start/rate fields `+0xB94/+0xB90` when the
secondary-timeline event is eligible. This supplies a native neutral
animation path; relocation alone does not perform that phase processing.

Neutral setup `FUN_00226F10` synchronizes the three facing halfwords and
calls paired Extra Hit teardown `FUN_00243EF0` when the caller has a nonzero
exchange word. That teardown edits both fighters' exchange state and resets
related rate/continuation fields. Ordinary-response exit `FUN_00230A70`
clears retained response fields and has special `0x4F` cleanup; recovery exit
`FUN_00235200` changes the accepted-hit countdown for `0x5E..0x60`. These
side effects make native transitions materially different from overwriting
major/substate fields. Their gameplay ownership remains in
[Hit response](../../knowledge/gameplay/hit_response.md).

Major-state exit inspection also found section-transfer continuation cleanup
in `FUN_0022F110` and substantial skill/action release work in
`FUN_00238D00`: paired state, descriptor-dependent helpers, countdowns,
action-associated side objects and queue entries. The skill exit may force
the partner to neutral. These effects constrain pair transition order and
prevent treating the two fighters' reset operations as independent. They do
not establish that every projectile, support or character-owned callback is
cancelled by a generic neutral transition.

The constructor reset `FUN_00214A40` is unsuitable as a position-only reset
without a reconstruction contract: it clears resources, side/controller bits,
action and animation pointers, status/effect state, and other initialized
storage. It is called by the common constructor `FUN_002145D0`; later
`FUN_002151E0` installs character records and allocates dependent objects.
Reusing construction-time zeroing would therefore exceed the proposed
placement operation.

## State required by an in-place reset

This matrix separates the confirmed retail field use from the proposed reset
contract. It is not an implementation-ready list of unconditional writes.
Movement ownership belongs to
[Movement and physics](../../knowledge/gameplay/movement_and_physics.md), and
paired/borrowed pointer lifetime to
[Battle entities](../../knowledge/gameplay/battle_entities.md#ownership-model).

| State | Evidence relevant to reset | Provisional treatment |
| --- | --- | --- |
| Position/orientation `+0x30/+0x40`; section `+0x9F6` | Shared initial/recovery placement supplies all three; a transform alone omits stage membership. | Restore as one tuple for each existing fighter. |
| Side bit `+0x60 & 1`; partner/control/field pointers `+0x20/+0x24/+0x28` | Initial graph links these once; the placement helper reads a side argument without changing fighter ownership. | Preserve identity and links, including when exchanging spatial sides. |
| Facing `+0x98C/+0x98E/+0x990`; orientation component `+0x48` | `FUN_0024D830` and `FUN_0021B930` derive the halfwords from the orientation sign. Native direction table `0x005C16B0` begins `+pi/2,-pi/2`. | Keep the three facing fields consistent with the selected orientation. |
| Planar/vertical speed `+0x994/+0x998`; input-derived speed `+0x99C`; mode `+0x988`; retained scalar `+0x9B0`; next-pass gravity `+0x9B4` | `FUN_0024A660` integrates speed by `+0x1AC`, chooses mode-specific gravity, and restores the gravity argument to `1.0`; `FUN_002173D0` updates `+0x99C` from live input. | A neutral placement resets motion rather than retaining a launch/jump impulse. Clearing only `+0x994/+0x998` is insufficient proof. |
| Added motion vectors `+0x4D0/+0x4E0` | `FUN_0024A660` adds these to displacement; `+0x4E0` remains active in branches that omit `+0x4D0`. Initial placement does not clear either vector. `FUN_0024DA50` resets both after movement/animation processing, including its paused/disabled paths. | Account for the reset's position within that pass and subsequent producers; a retained vector must not move the new tuple. |
| Contact/orientation family `+0x9B8 & 3`, grounded byte `+0x63 & 0x80`, contact words `+0xBB0/+0xBB4/+0xBB8/+0xBBC`, probe scalars `+0xBA0/+0xBA4/+0xBA8`, history `+0xB9A/+0xB9C` | `FUN_0024A660` rebuilds contact flags/probes, branches on prior grounded/contact state, and latches action ground/air history. | Refresh for the destination; copying stale source contact state is not established safe. |
| Position history `+0x840..+0x8BF`, ring cursor `+0x8C0`, previous transform `+0x970`, prior facing `+0x980..+0x986` | Native initialization fills all eight vectors; `FUN_0024C440` rotates the ring and copies current position/facing at the end of maintenance. | Avoid a history spanning the old and reset locations. Initial placement fills vectors but does not reset the ring cursor or prior-transform copy. |
| Target-derived section/direction/scalars `+0x324/+0x326/+0x328..+0x334` | `FUN_002174A0` refreshes paired or target-mode geometry; its direction update is conditional on the bearing. The exact contract is owned by [Target selection](../../knowledge/gameplay/target_selection.md#paired-opponent-and-geometry-refresh). | Refresh after both destination tuples exist; preserve the partner pointer and account for direction/facing consistency. |
| Major/substate `+0x18E/+0x190`, phase `+0x192`, primary/secondary timeline, descriptor `+0xA30`, animation selection/end `+0xB8C/+0xB8E/+0xB88` | Native transition and phase/animation consumers act together; changing state alone does not directly reset every animation field. | Enter/restart neutral through a complete transition and phase path, with an explicit interruption policy. |
| Pause/rejection/lock blocks `+0x200/+0x224/+0x248` | Maintenance `FUN_0024C440` activates pending negative counts as well as decrementing active counts. Initial placement does not clear these blocks; recovery exits can write rejection counts. | A reset intended to be immediately actionable must address active and pending channel state, not just current positive counts. |
| Hit/exchange state `+0xE3C`, retained hit/source `+0xE54/+0xE58`, repeat `+0xE5C`, Extra Hit `+0xB00` family | Native init clears `+0xE54` only; hit resolution consumes the other pending fields, while native exchange teardown edits both fighters. | Remove obsolete hit requests through proved cleanup; do not keep a one-sided exchange after moving the pair. |
| Resources, character/moveset, controller Status and settings | Resource snapshot and manager/Practice policies are separate from placement. | Preserve unless a later accepted feature requirement explicitly combines resets. |

### Pair ordering and lifetime

`FUN_002174A0(fighter,0)` reads partner current transform and section. Its
alternate path reads partner previous transform; changing only one side or
refreshing caches before both are placed can mix old and new coordinates.
The proposed tuple restore must therefore complete both placements before
deriving pair-relative state. This is an inference from the consumer order,
not a confirmed reset entrypoint.

Neutral dispatch `FUN_00248580` immediately chooses falling state `(3,0x1E)`
when the grounded flag is absent, or running when directional input duration
`+0x98A` is positive. Input processing also refreshes desired facing and
input-derived speed. Therefore the proposed placement/contact/transition
order must account for the next ordinary update and currently held input.
No input suppression or reset scheduling point is selected by this research.

The native `+0x61` bit `0x40` set by placement is cleared at the end of
`FUN_0024C440`, after previous-position/facing copies. It is a transient
placement-associated flag in these paths; its complete consumer meaning is
not yet established. A new reset cannot assume it is a lasting validity bit.

Manager primary aliases are borrowed. A saved-position record can retain
values, but keeping fighter pointers across battle reconstruction is unsafe
under the confirmed ownership lifetime. A proposed bookmark is limited to
the current match/stage lifetime and reacquires the existing side objects.
This is a design constraint derived from teardown/publication, not evidence
that retail already has a position bookmark.

## Provisional placement options

| Option | Evidence support | Remaining condition |
| --- | --- | --- |
| Native initial positions | Shared stage helper and all 74 initialization slots prove the source, orientation and section tuple. | The native `+200` component-2 offset means this is initial placement, not a proved grounded snap. Full in-place neutral cleanup remains necessary. |
| Exchange the two native spatial placements | The helper accepts explicit side `0` or `1`; selecting the opposite tuple does not write the fighter's identity bit. | Recompute pair direction/facing and confirm section/contact handling; no arbitrary mirror transform is established. |
| Return to a captured pair of positions | Transform and section fields are identified; the existing resource API supplies no position storage. | Define a match-local value record and eligible capture state. Arbitrary active-action or airborne snapshot restoration is outside the established contract. |
| Ground placement in an existing section | Live BTL `0x007090D0` checks its destination config index and delegates to live `0x006C1E50`, which maps the position into section configuration and line geometry. Native recovery uses it after the stage helper. | This helper maps between section configurations; it is not a blanket safe-coordinate predicate. Ground/contact refresh and placement eligibility remain separate. |
| Fixed spacing or wall/corner placement | Stage boundary clamp and floor-profile queries exist in [Stages](../../knowledge/gameplay/stages.md#boundary-and-floor-profile-data). | No universal fixed center, wall distance, mirror rule or obstacle-free placement was established. These remain hypotheses, not available feature choices. |

The best-supported initial design candidate is paired native placement with
an explicit neutral-state reset contract. A captured settled pair is a
separate candidate once capture eligibility and value lifetime are defined.
Calling the existing full battle reconstruction is also possible as an
existing restart path, but its other owner/resource resets would need to be
part of the accepted requirement; it is not a position-only shortcut.

No key combination, menu row, persistence mechanism or executable hook is
selected here. Those choices require later feature design and implementation
authorization.
