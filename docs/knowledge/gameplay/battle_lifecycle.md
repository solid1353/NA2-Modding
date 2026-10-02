# Battle-session and stage lifecycle

Static ownership, construction, per-update dispatch, and teardown evidence for
a retail NA2 (`SLPS-25837`) battle: the resident battle process, the
`0x38`-byte battle session, its BTL object graph, the stage owner, the order in
which they are created, run, and destroyed, and the continuation routes that
destroy and rebuild a session. It deliberately does not assign AI,
status-effect, match-outcome, Practice, or Adventure semantics to the
structural objects.

The clean BTL input and its address conversion are defined in
[Retail game file identities](../game/files/file_identities.md#address-conventions).
Its internal name is `BTL_product.bin`. Unless stated otherwise, BTL addresses
below are live addresses (preserved Ghidra address + `0x40`), and resident
addresses are ELF virtual addresses.

## Research coverage

- **Assigned scope:** the structural life of one battle: resident process
  states that load resources and build the session, the session object and its
  owned children, the BTL object graph and node callback contract, the
  per-update dispatch order, stage-owner binding and per-update stage work,
  teardown, and the values and resources retained across continuation
  rebuilds.
- **Exploration depth:**
  - Read completely: resident process states `1..0x0E`, session constructor
    `FUN_001EF330`, destructor `FUN_001EEFD0`, continuation rebuild states
    `0x17/0x18`, the per-update dispatcher `FUN_001F03E0`, and the
    continuation save/restore helpers `FUN_001ECC00/FUN_001ECDE0`.
  - Decoded from instructions: the BTL graph builder, broadcast, generic
    container walkers, container/node vtables and RTTI names for all four
    graph registries, the root initializer and its two phase callbacks, and
    the `ccField` per-update methods.
  - Direct `jal` scans of the root cluster, the broadcast, and the generic
    walkers across the resident ELF and BTL.
  - Phases 2 and 3 across every graph registry, the support and auxiliary
    service wrappers, all 74 concrete fighter phase-2/phase-3 slots, and six
    representative character tails; the three fighter-override channels and
    both post-publication setup helpers.
  - The fighter statistics save/reload helpers and their bank-address and
    stride aliases in both programs.
- **Confirmed coverage:** setup order from resource preparation through
  session publication; session field ownership; graph registry and node class
  identities; the node lifecycle-callback slots; per-update phase order
  relative to the camera controller, fighters, and stage; root allocation and
  phase gating by byte `+0x21`; persistent override application at all three
  phase boundaries; post-graph resource preparation and the complete nine-row
  model cache; empty camera/command phase-2 callbacks, shared fighter
  rendering and secondary callback/retirement work; the stage's update and
  draw passes; the full session teardown order, reverse element destruction
  within root arrays, nested root allocations, and final collision-result
  production after phase 3; and the different retained values, statistics
  banks, and timer behavior of the two continuation routes.
- **Unresolved or untested:** original class names of the non-polymorphic
  root children; actual elapsed timing under stalls or other scheduling
  conditions; character tails beyond the six scoped examples; differently
  derived or indirect statistics copies. No whole-graph field census or
  exhaustive indirect-caller search was performed.
- **Deliberate exclusions and overlap:**
  - Mask construction and the per-bit consumer table belong to
    [Pause and replay](pause_and_replay.md); end-sequence and result states to
    [Match outcomes](match_outcomes.md).
  - HUD and root-forest presentation roles belong to
    [Battle HUD](battle_hud.md); audio and guide objects to
    [Battle audio](battle_audio.md).
  - `ccEffectManager` and `ccSkillCtrl` internals belong to
    [Battle auxiliary services](battle_auxiliary_services.md).
  - Archive loading and stage objects belong to [Stages](stages.md); fighter
    and transient-actor ownership to [Battle entities](battle_entities.md);
    puppet banks to [Puppet control](puppet_control.md).
  - Gameplay-list behavior belongs to
    [Battle items and status effects](battle_items_and_status_effects.md);
    per-slot inventory/cache rules to
    [Battle item inventory](battle_item_inventory.md); character-specific
    form replacement to [Awakening](awakening.md); archive sharing/release to
    [Character assets](../game/character_assets.md).
  - Query-list semantics belong to [Collision](collision.md); scheduler
    mechanics to [Resident task system](../runtime/task_system.md); input
    polling and vibration to [Controller input](../runtime/controller_input.md);
    attack-bridge selection to
    [Combat action execution](combat_action_execution.md); skill contribution
    semantics to [Combo accounting](combo_accounting.md); general scene/render
    mechanics to [Scene playback owners](../runtime/scene_playback_owners.md)
    and [Render submission](../runtime/render_submission.md).
- **Evidence limitations:** conclusions are static. Shared virtual entries
  establish dispatch but not all downstream semantics; the pacing chain
  establishes counts and ordering, not measured elapsed timing or one-to-one
  displayed-image timing. Direct-call and address searches do not exclude
  indirect, computed, or other-overlay callers.

## Battle update cadence

The ordinary front-end loop is paced by two VBlank-start counts per manager
cycle. One eligible front-end iteration selects one battle-process callback;
an active battle-service invocation in turn runs each phase-1 registry
callback at most once. At a nominal 60 Hz display-interrupt rate this gives
30 battle-service iterations per second. This is the static pacing rule,
not a measurement of elapsed timing or proof that every display refresh
contains a newly rendered battle image. The VBlank counter, threshold, and
cooperative yield are described in
[Resident task system](../runtime/task_system.md#root-pacing-and-the-engine-gate),
and the front-end thread ordering in
[Overlay ABI](../runtime/overlay_abi.md#front-end-thread-ordering-and-its-limit).

Thus the three graph phases are ordered parts of one battle-service call,
not three independent fighter updates. The camera controller, fighters, and
stage share that service cadence subject to their documented masks. A
delayed or gated task can miss a service opportunity, and work taking longer
than two interrupts can delay the next pass. The same threshold is consumed by
tick-counted vibration; see
[Controller input](../runtime/controller_input.md#vibration-and-actuator-scheduling).

## Address map

| Role | Export | Live | File offset |
| --- | ---: | ---: | ---: |
| `mwo3_entry` (root accessor) | `0x006B3F40` | `0x006B3F80` | `0x80` |
| root constructor | `0x006B4140` | `0x006B4180` | `0x280` |
| root embedded-member constructor | `0x006B41A0` | `0x006B41E0` | `0x2E0` |
| root destructor | `0x006B41F0` | `0x006B4230` | `0x330` |
| root one-time initialization | `0x006B44A0` | `0x006B44E0` | `0x5E0` |
| root first-phase callback | `0x006B48A0` | `0x006B48E0` | `0x9E0` |
| root second-phase callback | `0x006B49D0` | `0x006B4A10` | `0xB10` |
| outer graph constructor | `0x00709200` | `0x00709240` | `0x55340` |
| outer graph destructor | `0x00709240` | `0x00709280` | `0x55380` |
| graph build/link | `0x00709440` | `0x00709480` | `0x55580` |
| graph node-start broadcast | `0x007095A0` | `0x007095E0` | `0x556E0` |
| per-container node-start walk | `0x00709BB0` | `0x00709BF0` | `0x55CF0` |
| generic phase-1 walk (update/remove) | `0x00709C30` | `0x00709C70` | `0x55D70` |
| generic phase-2 walk | `0x00709D20` | `0x00709D60` | `0x55E60` |
| generic phase-3 walk | `0x00709DA0` | `0x00709DE0` | `0x55EE0` |
| `ccField` phase-1 update | `0x00708980` | `0x007089C0` | `0x54AC0` |
| `ccField` phase-2 callback | `0x00708BB0` | `0x00708BF0` | `0x54CF0` |

Stage-owner, `ccBgControl`, and stage-table addresses are indexed in
[Stages](stages.md#address-index).

## Resident setup order

The resident battle process at `0x00607620` (entry and return contract in
[Mode flow](../game/mode_flow.md#btl-handoff-and-return)) is dispatched by
`FUN_001EC960`. BTL is already selected synchronously by `FUN_001EC7A0`
before state 1. States `1..0x0E` prepare one battle:

| State | Handler | Established work |
| ---: | --- | --- |
| 1 | `FUN_001ECF80` | Entry type 2 queues `prac.ccs` when absent and starts a loader fence. |
| 2 | `FUN_001ED000` | Waits for the fence, initializes manager battle fields, clears timer globals `0x006B2900..0x006B2914`. |
| 3 | `FUN_001ED110` | Resets the timer structure at `0x006B28D0` (limit `99`) and calls BTL `0x0070F1E0`. |
| 4, 5 | `FUN_001ED230`, `FUN_001ED300` | Queue, then adopt, `charsel1.ccs`, `mapsel1.ccs`, and `setting.ccs`. |
| 6..9 | see [Mode flow](../game/mode_flow.md) and [Stages](stages.md#archive-preload-adoption-and-switching) | Character Select, then stage selection; state 9 writes the raw stage slot to manager `+0x98`. |
| 10 | `FUN_001ED880` | Releases the three selection archives, snapshots the manager, and calls `FUN_001E9520(1)`. |
| 11, 12 | see [Stages](stages.md#archive-preload-adoption-and-switching) | Wait for the loader and readiness gates. |
| 13 | `FUN_001EDA50` | Calls `FUN_001E86C0` for sides 1 and 2, BTL `0x00769110`, and stage adoption `0x006C3210(slot, 0)`. |
| 14 | `FUN_001EDB00` | When both resident gates are ready, builds the session through `FUN_001EC3B0(type)`, calls support post-create `0x008852E0`, and enters state `0x0F`. |

`FUN_001E9520(1)` is the single resource-queue point for a battle. It queues
`cmn/2cmnbod1.ccs`, `pl/1cmnbod1.ccs`, `modename/mode1cmn.ccs`, and
`battlegauge.ccs` when absent; calls BTL `0x00769050` with both selected
character IDs; queues the stage archive through BTL `0x006C31D0(slot, 0)`;
queues both fighters through `FUN_001E80F0(manager, side, 0x1FF, 1)`; queues
the stage-associated archive named by `FUN_00207E20(slot)`; and starts one
loader fence. The only stage-specific inputs at this point are the raw slot at
manager `+0x98`, the 24-entry path table, and the `FUN_00207E20` mapping.

## Session construction

`FUN_001EC3B0(type)` runs only when manager `0x00607600` exists and session
global `0x00607604` is empty. It sets `0x0060766C = 1`, sets timer flag bit 1
when `FUN_001F6420(manager, 6) == 100`, calls BTL `0x00715F60` unless
continuation phase `0x00607678` is 2, allocates the `0x38`-byte session,
initializes it through `FUN_001EEC80` (`FUN_001EED40`, then
`FUN_001EEE30(session, type)`), publishes it, and calls `FUN_001EF330`.
Entry type 2 additionally creates the `0xA8`-byte object at `0x00607658`,
the guide owner described in
[Battle audio](battle_audio.md#guide-allocation-publication-and-dispatch).

`FUN_001EF330` then builds in this fixed order:

1. `FUN_001F4030(-1)`, `FUN_001BEA00`, `FUN_001DC6E0`, and `FUN_00309090(1)`,
   which creates the BTL auxiliary global at `0x00607844`.
2. When session `+0x18` is empty: allocate the `0x10`-byte graph, publish it at
   `0x00607654`, build it with `0x00709480`, publish the per-side command
   nodes (`0x00709800`) and fighters (`0x007099C0`) into manager
   `+0xDF0/+0xDF4` and `+0xDE4/+0xDE8`, and store the registry-A camera
   returned by `0x007096E0` at session `+0x14`. Publication is described in
   [Battle entities](battle_entities.md#battle-state-and-hub-publication).
3. Always call the node-start broadcast `0x007095E0`.
4. Create the camera controller at session `+0x1C` and publish it through
   `0x006DBD60`; see [Battle camera](battle_camera.md#shared-controller-entry-points).
5. Create the `0xC8`-byte resident item manager at session `+0x20`
   (`FUN_00373A20`).
6. Call BTL `0x00735E70` (transient-actor manager), `0x007063F0`,
   `0x00776B80`, and `0x00778830`. These reset the fighter override bank,
   prepare the auxiliary systems against the newly published fighters, and
   cache selected character model resources, as detailed below.
7. For continuation phase 2 only, call `FUN_001ECDE0`.
8. Create one `0x68`-byte per-side object for sides 1 and 2 through
   `0x0071A840` at session `+0x24/+0x28`.
9. Create the `0x44`-byte object at `+0x2C` (`0x0087E880`), the `0x70`-byte
   root at `+0x30`, and the `0xC`-byte object at `+0x34` (`0x006B4BA0`).
10. Call `FUN_0035CE20` with both character IDs.
11. Create, if absent, the `0x6C0`-byte pause controller at `0x00607834`
    ([Pause and replay](pause_and_replay.md#shared-ownership-and-controller-lifecycle)), initialize it through
    `0x0076E9D0(controller, P1, P2, slot)`, copy per-side flags, store the
    stage slot at controller `+0x0E`, and call `0x0076EC10`.

### Session fields

| Offset | Established use |
| ---: | --- |
| `+0x02/+0x04` | allowed-update masks built each update; see [Pause and replay](pause_and_replay.md#controller-fields-and-mask-construction) |
| `+0x06/+0x08` | session-local mask overrides |
| `+0x0A` | inner end-sequence substate; see [Match outcomes](match_outcomes.md#inner-end-sequence) |
| `+0x0C` | entry type, stored by `FUN_001EEE30` |
| `+0x10` | inner end-sequence delay |
| `+0x14` | borrowed `ccCamera01` main camera |
| `+0x18` | owned graph |
| `+0x1C` | owned camera controller |
| `+0x20` | owned `0xC8`-byte resident item manager |
| `+0x24/+0x28` | owned per-side `0x68`-byte top HUD panels |
| `+0x2C` | owned `0x44`-byte battle-clock display |
| `+0x30` | owned `0x70`-byte BTL root |
| `+0x34` | owned `0xC`-byte object |

The HUD objects at `+0x20..+0x30` and their update/draw order are described
in [Battle HUD](battle_hud.md#battle-session-ownership-and-order).

### Setup helpers after fighter publication

Live BTL `0x00776B80` (Ghidra `0x00776B40`, file `0x0C2C80`) has two
ordered calls. If auxiliary global `0x00607844` is nonnull, it calls live
`0x0077E460` on that object; it then calls resident `FUN_00309040`
unconditionally. The first initializes the already allocated auxiliary object
against the new fighter aliases: it resets its embedded `+0x210` object,
clears byte `+0xA50`, clears both `0x314`-byte pointer banks beginning at
`+0xBA8`, and calls live `0x0077DE10` with each primary fighter. That helper
uses fighter halfwords `+0x184/+0x186` to select allocation descriptors and
preallocates entries for both sides when absent. It also processes one
character-specific descriptor row. This is post-graph resource initialization,
not construction of another fighter or invocation of a fighter update.
The complete allocation-descriptor semantics are outside this lifecycle note.

Resident `FUN_00309040` operates only when global `0x006076F0` is nonnull.
It calls `FUN_0030C360`, `FUN_0030C5E0`, and `FUN_0030C4A0`, in that order.
The first builds a seven-entry archive/animation lookup list from both
fighters' character IDs using table `0x005C7CC0`; the second resolves two
registered resource lists to fields `+0x08/+0x0C`; the third resolves the
available entries of the 20-pointer table `0x005A3280` into records at
object `+0x2F0` and stores their count at `+0x3F0`. Thus the helper prepares
two existing resource systems after fighter publication: `ccSkillCtrl` and
`ccEffectManager`, whose constructor/RTTI joins and callback ownership are
described in [Battle auxiliary services](battle_auxiliary_services.md).

Live `0x00778830` (Ghidra `0x007787F0`, file `0x0C4930`) separately clears
nine model pointers in BTL BSS `0x008DAA70..0x008DAA93`. It walks side 0,
then side 1, and every row of the nine-record table at live `0x008AE270`
(Ghidra `0x008AE230`, file `0x1FA370`, stride `0x10`). Rows contain
character ID, model-name pointer, attachment-name pointer, and archive-path
pointer. The setup helper uses the ID, model name, and archive path; it does
not read the attachment field. All matching rows are processed:

| Row | Fighter character ID | Archive path | Model name |
| ---: | ---: | --- | --- |
| 0 | `0x03` | `2rocbod1.ccs` | `MDL_2roc00t0 hair1` |
| 1 | `0x03` | `2rocbod1.ccs` | `MDL_2roc00t0 hair2` |
| 2 | `0x0A` | `2hakbod1.ccs` | `MDL_2hak00t0 mask` |
| 3 | `0x0A` | `2hakbod1.ccs` | `MDL_2hak00t0 sen0` |
| 4 | `0x1C` | `2kbtbod1.ccs` | `MDL_2kbt00t0 glas` |
| 5 | `0x43` | `2rowbod1.ccs` | `MDL_2row00t0 hair1` |
| 6 | `0x43` | `2rowbod1.ccs` | `MDL_2row00t0 hair2` |
| 7 | `0x45` | `2guwbod1.ccs` | `MDL_2guw00t0 hair1` |
| 8 | `0x45` | `2guwbod1.ccs` | `MDL_2guw00t0 hair2` |

For a match it looks up the archive with resident `FUN_001AA4B0`, resolves
the model with `FUN_001A8F00(handle, name, 0)`, and stores that returned
pointer at `cache + row*4`. If both fighters match one row, the second lookup
overwrites the same slot. Neither the manager nor the fighter aliases are
null-checked in this helper; graph publication is a required preceding step.
The model lookup and cache store are at live `0x007788E0..0x00778914` (file
`0x0C49E0..0x0C4A14`). The table and strings are direct retail BTL evidence;
character asset identities are owned by
[Character assets](../game/character_assets.md).

## Graph registries and node contract

The graph owns four registries. Their vtables are resident data and resolve
through RTTI to these names:

| Graph field | Registry (vtable) | Node class (vtable at node `+0x50`) |
| ---: | --- | --- |
| `+0x00` | `ccCameraCtrl` (`0x005DDB40`) | `ccCamera01` (`0x005DDBE0`); later camera-controller objects `ccDummyCamera` and `ccPMCCamera` |
| `+0x04` | `ccCommandCtrl` (`0x005DDD10`) | `ccCommand` (`0x005DDD30`), one per side |
| `+0x08` | `ccPlayerCtrl` (`0x005D9FC0`) | fighters; see [Battle entities](battle_entities.md) |
| `+0x0C` | `ccFieldCtrl` (`0x005DDD60`) | `ccField` (`0x005DDD80`), the stage owner |

[Battle entities](battle_entities.md) calls these registry A, the per-side
control registry, the fighter registry, and the shared-match registry. Its
cross-reference table therefore means: the main camera points at both fighters,
each fighter points at its opponent, its `ccCommand` node, and the `ccField`
stage owner.

Graph nodes carry their vtable at node `+0x50`. The container walkers fix the
meaning of five slots:

| Node slot | Caller | Contract |
| ---: | --- | --- |
| `+0x08` | container destructor | destroy |
| `+0x0C` | `0x00709BF0`, from the broadcast | node start, run once after graph build |
| `+0x10` | `0x00709C70`, container phase 1 | update; a nonzero return unlinks and destroys the node, as does node flag bit 0 before the call |
| `+0x14` | `0x00709D60`, container phase 2 | second-phase callback |
| `+0x18` | `0x00709DE0`, container phase 3 | third-phase callback |

`ccCommandCtrl` and `ccFieldCtrl` use the generic thunks `0x006D67E0`,
`0x006D67A0`, and `0x006D67C0` for container slots `+0x0C/+0x10/+0x14`;
`ccCameraCtrl` uses `0x006D59D0`, which calls the same phase-1 walk. The
start slot `+0x0C` is the empty return `0x006D6770` for `ccCamera`,
`ccDummyCamera`, `ccPMCCamera`, `ccCamera01`, and `ccField`; `ccCommand`
supplies `0x006F0DF0`. The broadcast is therefore a node-start hook, not a
round reset.

## Per-update dispatch

While the inner battle is active, outer state `0x0F` calls `FUN_001EF8F0`,
which runs `FUN_001F0290` (mask construction), `FUN_001F03E0` (dispatch),
`FUN_001F10F0` (timer), and `FUN_001F0B10` (terminal detection) whenever the
inner machine returns 0. Inner substates 1 to 3 are the opening: substate 1
calls `0x0076EF60(controller, P1 character, 0, 0)` on the pause controller,
substate 2 waits for its byte `+0x10` to clear, and substate 3 clears its bit 0
and emits event 8 when no result is latched. Services run during those
substates as well.

`FUN_001F03E0` runs in this order. Mask bits and exceptions are in
[Pause and replay](pause_and_replay.md#selective-update-gating).

1. Pause-controller pre-work `0x0076EF90`, then the camera controller update
   `0x006DC3B0(session+0x1C)`, both skipped while manager `+0x14 == 1`.
2. BTL `0x00706420`. This and the later `0x00706450` and `0x00706480` all
   run `0x007065E0` on the override bank at `0x008D6A10`, applying pending
   flag values to both primary fighters from manager `+0xDE4/+0xDE8`.
3. Phase 1: `ccCameraCtrl`, `ccCommandCtrl`, the auxiliary global's work,
   `ccPlayerCtrl`, `ccBuddyAtkCtrl`, `ccFieldCtrl`, the transient-actor
   manager, and resident `FUN_00309190`, then pause-controller post-work
   `0x0076F020`.
4. BTL `0x00706450`, then phase 2 over the same registries in the same order.
5. BTL `0x00706480`, then phase 3 in the same order, without the
   transient-actor manager.
6. Session children `+0x20`, `+0x24/+0x28`, `+0x2C`, and the root, each with
   a first and a second callback gated by the two masks; then resident
   `FUN_001DE1C0`.

**Inference:** because the camera controller and `ccCamera01` run before
`ccPlayerCtrl` in phase 1, the camera computes each update from the fighter
positions left by the previous update.

The dispatcher also services resident object `FUN_0036B6C0()` through
`FUN_0036BF10(0)` and `FUN_0036BFF0(0)` after phase 3 and before session
`+0x20`. The first/second masks gate these two calls; their mask semantics
belong to [Pause and replay](pause_and_replay.md#selective-update-gating).
Session `+0x34` has construction and teardown here but no direct per-update
call in `FUN_001F03E0`.

### What phase 2 guarantees

Phase 2 is a dispatch boundary, not a second full fighter update or a
universally pure draw pass. The generic walker calls node slot `+0x14`;
individual containers and nodes determine its work:

| Consumer | Established phase-2 behavior |
| --- | --- |
| `ccCameraCtrl` | The four scoped camera classes (`ccCamera`, `ccDummyCamera`, `ccPMCCamera`, `ccCamera01`) use the empty live BTL `0x006D6780` at node `+0x14`. |
| `ccCommandCtrl` | `ccCommand` also uses empty live `0x006D6780`; its input/command update is in phase 1. |
| `ccPlayerCtrl` | Resident `FUN_00250690` performs the generic node pass, a separate gameplay-list callback pass, optional presentation bookkeeping, and the registry's auxiliary presentation. |
| `ccBuddyAtkCtrl` | Live `0x00885430` calls `0x008871A0`: temporarily installs view `0x00609160`, invokes each nonnull side object's node `+0x14` when node flag bit 2 is set, then restores the prior view. |
| `ccFieldCtrl` | `ccField` reaches the stage render pass described in [Per-update stage work](#per-update-stage-work). |
| Auxiliary global `0x00607844` | Live `0x00779020` calls `0x00870CA0` on its embedded `+0x210` object. That routine installs presentation globals/views and invokes its subordinate virtual callbacks. |
| Transient-actor manager | Live `0x00734D30` invokes active actors' node `+0x48` with argument 1 under view `0x00609160`, then dispatches its `+0x1C` child under the auxiliary view. Manager byte `+0x21` suppresses this work. |
| Resident auxiliary service | `FUN_003091E0` installs the auxiliary view, calls live BTL `0x00776C10`, then `FUN_0030BF00`; the latter visits up to `0x300` active resource slots and a second registered list through virtual callbacks, restoring its saved view. |

The empty camera/command target is established by resident vtable bytes at
`0x005DDB10`, `0x005DDB80`, `0x005DDBB0`, `0x005DDBE0`, and
`0x005DDD30`, together with the bytes at live `0x006D6780` (file
`0x22880`): `jr ra; nop`. This rules out treating the
generic slot itself as proof of drawing.

Every one of the 74 final concrete fighter tables selected by the 94-row
character-definition table uses resident `FUN_0024DD70` at node `+0x14`.
This was checked across the complete resident table interval
`0x005DA140..0x005DB18F`; concrete construction and selector coverage are
owned by [Battle entities](battle_entities.md#complete-table-selected-concrete-lifetime-paths).
The shared callback runs only while fighter flag bit 2 is set. It submits
the model at fighter `+0xE70` through `FUN_001BB790`, brackets that work
with auxiliary calls, then invokes the embedded `+0xEA4` object's
slot `+0x10` and the fighter's own slot `+0x28`. Sharing this entry does not
make the downstream virtual methods identical for all characters.

After the generic fighter-node pass, `FUN_00250690` walks the same fighter
list again through `FUN_00305C00`; the callsite is resident `0x00250758`
(ELF file `0x150858`). That helper invokes slot `+0x10` on the embedded
gameplay-list object at fighter `+0x8C4`. Its secondary node callbacks and
auxiliary-list details are owned by
[Battle items and status effects](battle_items_and_status_effects.md#update-expiry-and-removal).
The container then visits fighters with nonnull `+0xB30` and nonzero
halfword `+0xB10` through `FUN_002091B0`, before calling
`FUN_002070D0` on its own `+0x30` auxiliary object.

`FUN_002091B0` is direct evidence that phase 2 includes lifecycle work:
besides model submission, it decrements an owned object's halfword `+0x1C`
and, on expiry, destroys and frees every linked child at `+0x10`.
Consequently a phase-2 callback can draw, run subordinate callbacks, or
retire presentation objects. The stage's update/draw distinction cannot be
extended to every registry without inspecting those consumers.

### Phase 3 and the final collision boundary

Phase 3 uses the first mask again, after the second-mask phase-2 passes.
Generic live BTL `0x00709DE0` calls every visited node's vtable `+0x18`;
it does not test the node flag byte or remove a node based on the callback's
return. A derived callback supplies its own gate. Like phase 2, the walk
captures the container count and head at entry and obtains node `next` after
the callback. This differs from phase 1's saved-next removal loop; no
general permission for a phase-3 callback to destroy its current node follows
from this walker.

| Consumer | Established phase-3 work |
| --- | --- |
| `ccCameraCtrl`, `ccCommandCtrl`, `ccFieldCtrl` | Generic walk through live `0x006D67C0`; scoped camera, command, and stage node slot `+0x18` is empty live `0x006D6790`. |
| `ccPlayerCtrl` | Resident `FUN_00250800` reaches the same walk; all 74 table-selected concrete fighters use `FUN_0024DE40`. |
| `ccBuddyAtkCtrl` | Live `0x00885460` reaches live `0x00887250`, visiting the two nonnull side slots and calling node `+0x18` only with node flag bit 1 set. |
| Auxiliary global `0x00607844` | Live `0x00779050` calls live `0x00870ED0` on embedded `+0x210`; it visits a two-by-four pointer bank at embedded `+0x7D0`, invoking each nonnull object's vtable `+0x14`. |
| Resident auxiliary service | `FUN_00309270` calls live BTL `0x00776C60`, then `FUN_0030BE30` when resident auxiliary global `0x006076F0` exists. |

The empty node target is corroborated by resident vtable bytes at
`0x005DDB10..0x005DDBF8`, `0x005DDD30`, and `0x005DDD80`, and the bytes at
live `0x006D6790` (file `0x22890`): `jr ra; nop`.
The fighter third-phase slot was checked for every final table identified by
[Battle entities](battle_entities.md#complete-table-selected-concrete-lifetime-paths)
within resident `0x005DA140..0x005DB18F`.

`FUN_0024DE40` is substantive late gameplay work. With fighter `+0x63` bit 0
clear and node update bit 1 set, it processes combo bookkeeping, attack
registration, class slot `+0x2C`, character callback selector `6`, and action
timeline work before appending the current three command words to the
32-entry ring at `+0x344` with cursor `+0x4C4`. When fighter `+0x61` bit 4
is clear, the callback sets it and returns before that full tail. Positive
fighter pause count `+0x20C` suppresses the ordinary attack/timeline portion;
it does not make every subsequent operation in the common callback vanish.
The exact gates and timeline ordering belong to
[Hit response](hit_response.md#hit-update-order-and-elapsed-updates), and
attack publication to [Combat action execution](combat_action_execution.md#ordinary-attack-registration).

Sharing the outer callback does not make character tails identical.
Representative slot-`+0x2C` consumers establish three different shapes:
ID `4`'s `FUN_00257320` adjusts two vectors at `+0xCA0/+0xCF0` in major state `8`;
ID `60`'s `FUN_002A39C0` reaches the puppet attack/animation bridge; and
ID `92`'s `FUN_002FD920` invokes live BTL `0x007243E0` on owned field
`+0x5308` (allocated by `FUN_002FD620`, freed by `FUN_002FD7A0`). The
common default `FUN_0024E0A0` is `jr ra; nop`, corroborated
by its resident bytes. Puppet bank ordering belongs to
[Puppet control](puppet_control.md#root-movement-remains-coupled-to-the-primary).
These are representative downstream consumers, not an exhaustive semantic
classification of every character tail.

Three additional tails establish how the shared phase reaches resources owned
by the concrete fighter:

| Character ID / final table | Third-phase tail | Retained resource interface and cleanup |
| --- | --- | --- |
| `18` / `0x005DADC0` | `FUN_0026A990` calls `FUN_002662A0` | Constructor `FUN_00265B10` and binder `FUN_00265D70` provide a separate model wrapper at `+0x5110`, scene at `+0x5114`, embedded timer at `+0x5084`, and control object at `+0x5374`. The tail passes the scene and timer to the attack bridge, then independently advances or holds the timer. Destructor `FUN_00265CD0` reaches `FUN_00266220`, which destroys and clears the scene, model wrapper, and control object. |
| `59` / `0x005DA8C0` | `FUN_0029D010` | Constructor `FUN_0029BC70` allocates three `0x120`-byte scenes through the array constructor, storing them at `+0x57A0`. In major state `8`, the tail adds retained vector `+0x57C0` to both attack-position vectors, then selects a scene using character-local state. Destructor `FUN_0029BE80` separately destroys scene `+0x57E4`, destroys the three-element array through `FUN_00119180(..., FUN_001B7570)`, and clears both pointers before common fighter cleanup. |
| `91` / `0x005DA1E0` | `FUN_002FB560` calls live BTL `0x007243E0` | Constructor `FUN_002FB220` allocates a `0x2C`-byte `pl91WoodCtrl` at `+0x5AAC`, initializes it through live `0x00723990`, and binds the fighter plus 15 descriptor rows at resident `0x005C5C20` through live `0x007239D0`. Destructor `FUN_002FB3E0` calls live `0x00723C40`, then frees and clears this controller before common fighter cleanup. |

ID `18`'s timer pass uses scene halfword `+0x94 / 256.0` with
`FUN_00211D80` when `FUN_00224650` returns zero, otherwise
`FUN_00211F70`. It follows the gated attack-registration loop rather than
being contained in it. ID `59`'s tail returns outside major state `8` and
uses its retained vector before later attack-eligibility gates. These are
different resource/state interfaces behind the common third-phase callback.
The selected scene pointers are resources owned by the concrete fighter,
separate from its primary scene. Exact attack admission and temporary
scene-rate overrides belong to
[Combat action execution](combat_action_execution.md#character-specific-scene-and-timer-selection),
and general scene advancement to
[Scene playback owners](../runtime/scene_playback_owners.md).

ID `91`'s controller table `0x005DA230` is installed at child `+0x28`;
RTTI `0x005C7180` points to the retail literal `pl91WoodCtrl` at
`0x005A2CE0`. It shares the late helper used by the ID `92`
example through its own fighter field and retained binding.
The constructor also owns separate allocations at `+0x5AA8/+0x5AB0`;
its destructor releases and clears both. This establishes the selected
controller's session/fighter lifetime without classifying every linked
resource or downstream callback in the shared BTL helper.

The resident auxiliary service's BTL wrapper has three ordered calls: empty
live `0x00778B30`, live `0x0077E9F0`, then live `0x00778B60`.
The middle call dispatches the two auxiliary objects through vtable-at-object
`+0x110` slot `+0x12C` when their `+0x14 & 3` is clear; visits two banks of
32 subordinate pointers through node slot `+0x64` when subordinate byte
`+0x8B0` is zero; then calls the two primary auxiliary objects' slot `+0x138`.
The final call runs their slot `+0x120`, marks pending flag states, maintains
two resident scalar pairs, and enters live `0x00777DD0`. That helper's
complete instruction path loops over two sides and conditionally resolves
manager fighter aliases while handling auxiliary records at
`+0x3268/+0x3270`. Their contribution/flush contract belongs to
[Combo accounting](combo_accounting.md#per-side-accumulated-contribution-route);
this document owns the call's position after the virtual phase-3 passes.
The helper continues past its call to live `0x007063E0`, which returns the
override bank pointer (live `0x00777DD0..0x00777F84`, file
`0x0C3ED0..0x0C4084`).
Separately, `FUN_0030BE30` invokes vtable `+0x14` for eligible entries of its `0x300`-slot
resource array and node-vtable `+0x1C` for its registered list. The concrete
pool callbacks and their resource-retirement boundary are described in
[Battle auxiliary services](battle_auxiliary_services.md).

Only after these passes and the session-child callbacks does `FUN_001F03E0`
call resident `FUN_001DE1C0`. It clears prior query results and produces new
directional registration-overlap results; the query contract belongs to
[Collision](collision.md#resident-query-list-boundary). Thus the common
phase-3 attack publication precedes this service call's result production,
while the fighter coordinator's phase-1 result consumption precedes it.
This establishes the static producer/consumer ordering. It does not establish
an elapsed display delay, nor prove that every collision or gameplay query
uses this particular result chain.

### Fighter overrides at phase boundaries

The bank at live BTL BSS `0x008D6A10` contains three two-side channels.
Each side record is eight bytes: a requested byte value at `+0` and a request
mask at `+4`. Live `0x007065E0` (Ghidra `0x007065A0`, file `0x0526E0`)
copies a channel's value only when its mask is nonzero and the corresponding
manager fighter alias is nonnull:

| Bank record for side `s` (`0..1`) | Fighter destination | Applied value |
| --- | --- | --- |
| `bank + 0x08 + s*8` | flag byte `+0x00`, bit 1 | requested byte bit 0 |
| `bank + 0x18 + s*8` | flag byte `+0x00`, bit 2 | requested byte bit 0 |
| `bank + 0x28 + s*8` | flag byte `+0x61`, bit 7 | requested byte bit 0 |

All other bits are preserved. The mask predicates are live
`0x00706CA0`, `0x00706E20`, and `0x00706FB0` (file
`0x052DA0`, `0x052F20`, and `0x0530B0`). Each rejects side indices outside
`0..1` and otherwise tests the corresponding word at `+0x0C`, `+0x1C`, or
`+0x2C` plus `s*8`, and returns a Boolean.

The three phase wrappers reach the same walk through live
`0x00706780/0x007067A0/0x007067C0` (file
`0x052880/0x0528A0/0x0528C0`). Neither those thunks nor the walk clears the
request masks. A zero mask preserves the fighter's current bit rather than
forcing it to zero. Requests can therefore survive and be reapplied at all
three boundaries in one service update. Session setup and teardown call live
`0x007063F0`, which reaches the bank reset at live `0x00706580` (file
`0x052680`): it clears the two leading words, all six value/mask records,
and the trailing record at `+0x38/+0x3C`. This is an override application
pass, not an additional fighter update or a separate fighter registry.
Gameplay meanings of these flag bits belong to their consumers.

## Root component forest

Session `+0x30` is the `0x70`-byte root returned by `mwo3_entry`. The root
constructor initializes its embedded `+0x30` member through resident
`SUB_00119290(member, 0x006B41E0, 0x0010A0F0, 0x40, 1)`, clears byte `+0x20`,
and enters one-time initialization. The initializer registers the embedded
member and allocates this fixed forest:

| Root field | Allocation | Shape | Element constructor |
| --- | ---: | --- | --- |
| `+0x04` | `0xB10` | two `0x580` objects | `0x006B4850` |
| `+0x00` | `0x98` | two `0x44` objects | `0x006B4820` |
| `+0x08` | `0x650` | two `0x320` objects | `0x006B7580` |
| `+0x14` | `0x28` | singleton | `0x006B8290` |
| `+0x10` | `0xF0` | two `0x70` objects | `0x006B4810` (returns only) |
| `+0x18` | `0xB0` | two `0x50` objects | `0x006B47E0` |
| `+0x0C` | `0x90` | two `0x40` objects | `0x006B47D0` (returns only) |
| `+0x1C` | `0x34` | resident-constructed singleton owned by the root | resident `0x001F8F00` |

Every paired array is immediately registered with side IDs 0 and 1. Public
accessors at `0x006B3FB0`, `0x006B4000`, `0x006B4050`, and `0x006B40B0` read
the root through session global `0x00607604` and expose the arrays. None of
the element constructors installs a vtable, so RTTI supplies no original
class names. Their presentation roles, bindings, and prompt placement are
described in [Battle HUD](battle_hud.md#remaining-ordinary-presentation-forest).

Both root callbacks return immediately when byte `+0x21 == 1`. Otherwise the
first callback updates `+0x14` and `+0x1C` and then both sides of the six
paired arrays. The second invokes the draw callbacks in field order
`+0x00`, `+0x04`, `+0x08`, `+0x10`, `+0x0C`, `+0x18` for each side,
then `+0x1C` and `+0x14`. There are two additional root-level draw gates:
when manager word `+0x0C == 3`, combo digits are drawn only for the side
selected by manager `+0x18`; numeric-history draws run only when
`+0x0C == 3`. Individual children also have their own active/fade gates.
Initialization ends with `+0x21 = 0` and `+0x20 = 1`. The initializer store
`0x006B47A8` is the only direct byte store to `+0x21` in the root cluster, and
no resident or BTL site loads the root through the session global and then
writes `+0x20` or `+0x21`. The traced direct paths therefore leave this gate
open after initialization; an indirect writer is not excluded.

## Teardown order

After its countdown (the end sequence described in
[Match outcomes](match_outcomes.md#cleanup-boundaries)), outer state `0x10`
(`FUN_001EDD10`) first calls `FUN_00201ED0`, destroys both slotted support
objects through live BTL `0x008853D0`
([Support mechanics](support_mechanics.md#scheduled-lifecycle-and-teardown)),
and releases the guide owner at `0x00607658`
([Battle audio](battle_audio.md#guide-allocation-publication-and-dispatch)). For route
`8`, it then selects state `0x17` or `0x18`, leaving session destruction to
that handler. Other routes destroy the session through
`FUN_001EECD0(session, 1)` before state `0x11` releases the archives.
`FUN_001EEFD0` destroys, in order:

1. the pause controller at `0x00607834` (after `0x0076ECF0`);
2. the camera controller, then clears its published pointer;
3. session `+0x20`, `+0x24/+0x28`, `+0x2C`, the root at `+0x30`, and `+0x34`;
4. `FUN_00376B40`, the start-menu object at global `0x00607668` (after BTL
   `0x0087B160`; see
   [Pause and replay](pause_and_replay.md#resident-ownership-and-top-level-result-routing)), and the transient-actor manager (`0x00735F30`);
5. the six manager alias words;
6. the graph through `0x00709280(graph, 1)`, then global `0x00607654`;
7. `FUN_0035CE90`, `FUN_00309110` (auxiliary global), `FUN_001DC700`, and BTL
   `0x007063F0`.

The root destructor destroys paired arrays in field order `+4`, `+0`, `+8`,
`+0x10`, `+0x18`, `+0x0C`; destroys and frees `+0x14` and `+0x1C`; tears down
embedded `+0x30`; and frees the root when its signed 16-bit delete flag is
positive. The graph destructor destroys `ccCameraCtrl`, `ccCommandCtrl`,
`ccPlayerCtrl`, and `ccFieldCtrl` in that order. The stage-owner destructor is
reached through `ccFieldCtrl` vtable `0x005DDD60` and `ccField` vtable
`0x005DDD80` to `0x007088A0`.

Session `+0x20` is the resident item manager. Its destructor
`FUN_00373E00` destroys its field-object chain before its auxiliary handles
and both inventory panels at `+0x6C/+0x70`. The panel allocations and slot
contract belong to [Battle item inventory](battle_item_inventory.md#na2-ownership).
Consequently the saved inventory cache survives independently of the old
panels; no inventory-panel pointer is transferred to the replacement session.

After deep cleanup, `FUN_001EECD0` calls the same `FUN_001EED40` used by the
session constructor, then frees the session when the signed delete flag is
positive. This resets the four mask halfwords to `0xFFFF`, inner substate and
delay to zero, default entry type to `1`, and every pointer at `+0x14..+0x34`
to null. The outer caller clears global `0x00607604` after the destructor
returns. These resets do not copy a previous session into its replacement.

### Root resource ownership and nested cleanup

The paired arrays have a 16-byte allocation header written by resident
`FUN_00119380`: element size, count, and element-destructor pointer precede
the returned first element. Root cleanup uses `FUN_00119180`, which invokes
that stored destructor from the last element back to the first with delete
flag `-1`, then frees the header allocation. Thus root field order and
within-array side order differ: each paired field destroys side `1` before
side `0`. The embedded-array helper `FUN_00119220` similarly tears down
embedded elements without separately freeing their storage.

| Root field | Element cleanup (live unless marked resident) | Established nested ownership |
| ---: | ---: | --- |
| `+0x04` | `0x006B4F80` | Optional layer at element `+0x540`, embedded animation at `+0x420`, and four embedded `0xF8` sprite objects at `+0x38`. |
| `+0x00` | `0x006B4480` -> `0x006B6A60` | Layer at element `+0x30`, sprite at `+0x38`, and animation handle at `+0x40`. |
| `+0x08` | `0x006B75D0` | Three embedded `0xF8` sprite objects beginning at element `+0x08`. |
| `+0x10` | `0x006B9C00` | Every nonnull pointer in the 26-child bank at element `+0x08`; each child is freed and its slot cleared. |
| `+0x18` | `0x006B4420` -> `0x006BB350` | Sprite at element `+0x00`, then every node in the linked popup chain at `+0x04` through `0x006BC060`; next is saved before each free. |
| `+0x0C` | `0x006B43D0` | No nested free in the element destructor; it only frees the element when its delete flag is positive. The root array deletion uses `-1`. |
| `+0x14` | `0x006B82D0`, then parent free | Five separately allocated sprites at `+0x00..+0x10`, layers at `+0x14/+0x1C`, and animation handle at `+0x18`. |
| `+0x1C` | resident `FUN_001F90B0`, then parent free | Layer, `0x80`-byte subordinate object, and two separately allocated notice sprites; all four fields are cleared. |

The five shared-icon pointers are sprite **wrappers**, rather than direct
texture-payload ownership. Resident `FUN_0037B670` allocates a `0xF8` wrapper,
looks up the named payload with `FUN_001A8F00`, and binds it; its paired
destructor `FUN_001CBDF0` frees only that wrapper when requested.
`FUN_0037B5B0` supplies the corresponding path/name-based wrapper. Likewise,
`FUN_0037D5B0` allocates a `0x120` animation handle and binds a looked-up
payload. The root's shared-icon cleanup frees these handles and layers; the
later archive-release state owns the archive allocation. Marker children
borrow the shared bundle and have no nested destructor for its sprites.

In the root cleanup (live `0x006B4230..0x006B43C8`, file `0x330..0x4C8`) and
the element cleanups at live `0x006B4F80`, `0x006B9C00`, `0x006B82D0`, and
`0x006BC060` (file `0x1080`, `0x5D00`, `0x43D0`, `0x8160`), each resident
free returns into slot clearing, the remaining children, and parent cleanup.

### Archive lifetime is separate from session lifetime

Normal outer state `0x11` (`FUN_001EDEE0`) releases the three shared battle
archive entries, the gauge archive, the BTL archive bank through live
`0x007691A0`, the stage archive, both sides' selected resource mask `0x1FF`, and the
stage-associated resident archive after the old session has been destroyed.
Continuation states `0x17/0x18` bypass that ordinary full-release state and
perform their own selective preparation. A newly allocated fighter graph
therefore does not imply that every underlying CCS archive was unloaded.

Both continuation handlers call `FUN_001E8EE0` after session destruction.
Its pending-side resource behavior, cross-side sharing checks, and distinction
from full masked release are established in
[Character assets](../game/files/asset_dependencies.md#pending-side-release-preserves-the-other-sides-resources).
State `0x18` additionally compares its selected saved side's pending and
active identity words and runs full mask `0x1FF` plus `FUN_001EE3E0` only
when they differ. The separate other side is prepared and queued afterward.
These comparisons concern manager identities and archive handles, not
retention of an old fighter allocation.

## Continuation encounters rebuild the session

The audited continuation paths do not reset the session in place. Route `8`
continuations leave outer state `0x10` for `0x17` (`FUN_001EE1C0`) or `0x18`
(`FUN_001EE500`). Both destroy the whole session through `FUN_001EECD0`,
rebuild fighter resources, and set
outer state `0x0D`; states `0x0D` and `0x0E` then load and construct a new
session through the ordinary construction entrypoints. State `0x17` copies
pending stage `+0x9A` into active stage `+0x98` only when it is not `-1` and
does not release the loaded stage archive. State `0x18` releases the stage
archive through `0x006C3160` and the stage-associated resident resource only
when those two stage bytes differ. It queues replacements through
`0x006C31D0` and the resident loader only when the changed pending stage is
not `-1`. Keeping an archive does not keep its stage-bound objects: the
`ccField` and background controller are recreated in either route.

### Values crossing the reconstruction boundary

The resident save/restore helpers are `FUN_001ECC00` (save before session
destruction) and `FUN_001ECDE0` (restore in the new `FUN_001EF330`). Side
argument `-2` iterates sides `1` and `2`; the mask has these consumed bits:

| Mask bit | Save before destruction | Restore after fighter publication |
| ---: | --- | --- |
| `0x01` | Fighter `+0x6C` (HP) to continuation-object `+0x1C + side*8` | Copy that word directly to new fighter `+0x6C` |
| `0x02` | Fighter `+0x70` (chakra) to continuation-object `+0x20 + side*8` | Copy that word directly to new fighter `+0x70` |
| `0x10` | Timer words `0x006B28D4/0x006B28D8` to `0x006B28DC/0x006B28E0`, if at least one side resolved | Copy both saved words back |
| `0x20` | `FUN_00375FD0(active_item_manager,side_mask)` | `FUN_00376050(active_item_manager,side_mask)` |

HP and chakra are restored by direct float loads/stores at
`0x001ECEA4..0x001ECEC0`, not through damage, recovery, or character-stat
scaling; a new character's static durability does not rescale the saved
normalized HP. The timer words are the remaining and elapsed counters; the
helpers do not copy the timer flags byte or configured limit. The item
wrappers reach BTL live `0x007109F0` and `0x00710B00` (complete-file
`0x5CAF0/0x5CC00`), the same compact-cache helpers Practice uses: they rebuild
the per-side item cache, then restore eligible entries into the new inventory
panels, without transferring gameplay effect nodes. Slot layout, filtering,
and restore compaction belong to
[Battle item inventory](battle_item_inventory.md#item-cache).

The two callers use that contract differently:

| Route and entry condition | Save before session destruction | Restore in new `FUN_001EF330` |
| --- | --- | --- |
| State `0x17`, re-entry variant `1` | Both sides (`-2`), mask `-1`: HP, chakra, timer counters, and inventory | Both sides, mask `-1` |
| State `0x18`, outer entry type `4` | One selected side, mask `-17` (`~0x10`): HP, chakra, and inventory | Both sides, mask `-17`; timer counters excluded |
| State `0x18`, other outer entry types | One selected side, mask `0x20`: inventory only | Both sides, mask `-17`; timer counters excluded |

In state `0x18`, the selected saved side is `1` when manager `+0x50 == 0`
and `2` otherwise; the other side is prepared separately for the next
encounter. Supplying a single side to `FUN_001ECC00` first initializes
**both** continuation value pairs to HP `1.0` and chakra `15.0` and calls live
BTL `0x0070F1E0` (file `0x5B2E0`) to clear both sides' three compact
inventory records. Only then does it copy the selected side's requested
values (`0x001ECC6C..0x001ECCB8`, then the guarded copies at
`0x001ECCFC..0x001ECD24`). Therefore entry type `4` retains that side's
HP/chakra while the other pair remains at the defaults; the other entry types
leave both pairs at the defaults.

`FUN_001EEE30` initializes the new session's timer counters and limit before
graph construction. State `0x17` later copies back the two saved counter
words; state `0x18` leaves those new counters in place. Timer representation
and advancement belong to [Match outcomes](match_outcomes.md#timer-path).
The restore runs after both new fighter aliases and the new item manager are
published, but before the remaining per-side presentation objects and root
are built. It does not retain command nodes, gameplay-node pointers, or the
old graph; their owners are destroyed in the order above.

Fresh construction resets the remaining fighter state. `FUN_00214A40` and
`FUN_002151E0` reset the selected Ultimate Jutsu effect `+0x18A`, the
major/substate/phase and progress trackers, command word `+0x338`, pending-hit
byte `+0xA45`, counter `+0xB78`, and controller/special bits; neither
save/restore helper copies them. Both sides also receive new native combo
objects through `FUN_0020C270 -> FUN_0020C320 -> FUN_0020C3D0`, with current
`+0x34`, maximum `+0x36`, and the combo timer reset. Combo-object semantics
belong to [Combo accounting](combo_accounting.md).

Both continuation handlers finish by writing phase `0x00607678 = 2`,
clearing pending character words at manager `+0x50/+0x78` and pending stage
byte `+0x9A` through `FUN_001F4F20`, and selecting state `0x0D`.
`FUN_001EC3B0` skips the event-bank reset in phase `2` and changes the phase
to `3` after its reconstruction attempt. That phase store is outside the
allocation-success branch: phase `3` alone does not establish that a new
session exists. Character-dependent form adoption is described in
[Awakening](awakening.md#static-reconstruction-order).

The direct resident save callsites are `0x001EE1EC`, `0x001EE56C`, and
`0x001EE588`; the restore callsites are `0x001EF528` and `0x001EF54C`. This
is a direct-call set, not proof that another overlay or an indirect call
cannot use the helpers.

### Fighter statistics across reconstruction

External fighter statistics are retained through a different route. Teardown
`FUN_00215720` first calls `FUN_00223040` at `0x00215740`, saving all 24
current/high-water pairs to `0x006B31D0 + side_index*0x2D6`. Constructor
`FUN_00222F00` clears the new local pairs, but skips clearing that external
block when `FUN_001EC2C0()` reports phase `2`; it then reloads pairs through
`FUN_002230A0`. The generic statistic contract belongs to
[Hit response](hit_response.md#hit-count).

Both directions select the bank as
`0x006B31D0 + (fighter byte +0x60 & 1)*0x2D6` (save `0x00223040..0x0022304C`,
reload `0x002230A0..0x002230AC`) and copy exactly 24 pairs of signed
halfwords, current at pair `+0` and high-water at `+2`. Teardown keeps the
fighter argument in `a0` across its call (`0x0021573C..0x00215744`), so an
established side-two fighter saves to bank one.

The reload's ordering differs from per-side restoration. `FUN_00214A40`
clears side bit `fighter +0x60:0x01` at `0x00214A64..0x00214A78` and calls
`FUN_00222F00` at `0x00214E9C`; only later does `FUN_002151E0` assign the
setup side at `0x0021542C..0x00215444`. Every fighter constructor reaches the
common base constructor before that setup. The constructor reload therefore
reads bank zero even for a fighter that will become side two; both external
banks are preserved, but the reload does not select bank one. The common setup
and continuation restore helpers contain no correcting reload. The only
direct calls are `0x0022301C -> FUN_002230A0` and
`0x00214E9C -> FUN_00222F00`, and only `FUN_00222F00`, `FUN_00223040`, and
`FUN_002230A0` form the bank address in searches for its low immediate,
literal pointer, stride, and second-bank immediate in both programs.

**Static consequence, high confidence within this chain:** if both old
fighters save distinguishable pair values, both new common constructors
initially receive the old side-one pairs. A later ordinary teardown saves each
fighter's then-current local pairs to its assigned side's bank, so side-two's
prior bank contents are not protected against that later save. This describes
the traced dataflow, not a measured player-visible statistics result; an
untraced differently derived copy could change the intervening local values.
The transformed-form adoption increment is described in
[Awakening](awakening.md#reconstruction-adoption-increment).

The `0x2D6` stride spans two local layouts. `FUN_00222F00` first clears 24
pairs (`0x60` bytes), then calls `FUN_00223250` for indices `0..62`, clearing
five halfwords per index at `block+0x60+index*10` (`0x276` more bytes; fighter
`+0x550..+0x7C5` for the ordinary local block). These action-indexed counters
are accessed by `FUN_002232B0/FUN_00223320`. Both save/reload loops and the
external clearing loop stop after the first `0x60` bytes, so construction
resets all 63 local action rows even during phase `2`. Direct `sh/sw` stores
with displacement `+0x4F0` in both programs are only the reload and
`FUN_0023A9A0`'s capped local action-statistic increment; these searches do
not cover every derived local-block pointer or wider store.

## Stage content binding

The `ccField` stage owner, its `0xAD0`-byte `ccBgControl`, the 24-slot path
table at `0x00890A10` (`stage/s01.ccs` through `stage/s24.ccs`, indexed without
a range check), and the background constructor are described in
[Stages](stages.md#live-environment-ownership-and-construction). The
constructor publishes the controller through `0x006C1A40` to global
`0x006077E4`. Owner construction finishes through `0x00708A20`, which clears
owner fields `+0x74/+0x78`, snapshots controller `+0x10` to `+0x7C`, calls
the empty routine `0x006C1B80` on the controller, and clears `+0x80` and byte
`+0x84`; a direct-`jal` scan finds this function only in the constructor.

### Per-update stage work

`ccField` is updated only through the node slots. Its phase-1 update
`0x007089C0` calls `ccBgControl` slot `+0x08` (the empty `0x006C1650`) and then
slot `+0x10` (`0x006C17C0`) with argument 0, and always returns 0. It therefore
does not request removal through its return value; the generic node flag-bit-0
removal rule still applies. Its phase-2 callback `0x00708BF0` calls
`ccBgControl` slot `+0x0C` (`0x006C1660`). Its phase-3 slot is empty. For the
stage, phase 1 is an update pass (resident `FUN_003ACAD0` over five object
lists) and phase 2 a draw pass (resident `FUN_003ACBF0` over 12 selector-group
views, restoring view `0x00609160`); the background work behind those slots is
owned by [Stages](stages.md#update-eligibility-and-local-timing). Other
registries have the narrower contracts established in
[What phase 2 guarantees](#what-phase-2-guarantees).

Stage-owner destruction is described in
[Stages](stages.md#destruction-and-archive-release); its cleanup
`0x006C29A0` clears global `0x006077E4`.

## Stage-specific inputs

A battle consumes these per-stage inputs, all keyed by the raw slot at manager
`+0x98`:

- the stage archive path from the 24-entry table at `0x00890A10`;
- the stage-associated archive from resident `FUN_00207E20(slot)`;
- the archive's `BIN_bgdata` records and `DMY_*` line/boundary nodes, read by
  `ccBgControl`; see [Stages](stages.md#boundary-and-floor-profile-data);
- the per-stage camera record selected by `ccCamera01`; see
  [Battle camera](battle_camera.md#per-stage-camera-record);
- the slot passed to the pause controller (`0x0076E9D0`, controller
  `+0x0E`).

## Limits and negative results

- Both audited route-`8` continuations destroy and rebuild the session;
  their retained-value masks differ and neither transfers the old graph.
- Root byte `+0x21` has no direct writer other than its initializer.
- The stage-owner destructor is virtual and has no direct `jal` caller; its
  container/vtable teardown chain supplies the evidence.
