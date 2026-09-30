# Battle-session and stage lifecycle

Static ownership, construction, per-update dispatch, and teardown evidence for
a retail NA2 battle: the resident battle process, the `0x38`-byte battle
session, its BTL object graph, the stage owner, and the order in which they are
created, run, and destroyed. It deliberately does not assign AI,
status-effect, match-outcome, Practice, or Adventure semantics to the
structural objects.

The clean BTL input and its address conversion are defined in
[Standard game file identities](../game/files/file_identities.md). Its
internal name is `BTL_product.bin`. Unless stated otherwise, BTL addresses
below are live addresses (preserved Ghidra address + `0x40`), and resident
addresses are ELF virtual addresses.

## Research coverage

- **Assigned scope:** the structural life of one battle: resident process
  states that load resources and build the session, the session object and its
  owned children, the BTL object graph and node callback contract, the
  per-update dispatch order, stage-owner binding and per-update stage work,
  teardown, and continuation rebuilds.
- **Exploration depth:** resident process states `1..0x0E`, session
  constructor `FUN_001EF330`, session destructor `FUN_001EEFD0`, continuation
  rebuild states `0x17/0x18`, and the per-update dispatcher `FUN_001F03E0`
  were read completely. The BTL graph builder, broadcast, generic container
  walkers, container/node vtables and RTTI names for all four graph registries,
  the root initializer and its two phase callbacks, and the `ccField`
  per-update methods were decoded from raw instructions. Direct `jal` scans
  covered the root cluster, the broadcast, and the generic walkers across the
  resident ELF and BTL. Child objects were not traced beyond the calls listed.
- **Confirmed coverage:** setup order from resource preparation through
  session publication; session field ownership; graph registry and node class
  identities; the node lifecycle-callback slots; per-update phase order
  relative to the camera controller, fighters, and stage; root phase gating by
  byte `+0x21`; the stage's update and draw passes; the per-stage inputs a
  battle consumes; the full session teardown order; and the fact that
  continuation encounters rebuild the whole session instead of resetting it in
  place.
- **Unresolved or untested:** semantic names of the non-polymorphic root
  children; the purpose of the per-phase fighter walk `0x007065E0` and of
  setup helpers `0x00776B80` and `0x00778830`; whether phase 2 is a draw pass
  for registries other than the stage; and how many battle-service updates
  occur per video frame.
- **Deliberate exclusions and overlap:** AI, statuses, outcomes, Practice,
  pause-mask semantics, and Adventure were excluded. Mask construction and the
  per-bit consumer table are owned by
  [Pause and replay](pause_and_replay.md); end-sequence and result states by
  [Match outcomes](match_outcomes.md); archive loading and stage objects by
  [Stages](stages.md); fighter and transient-actor ownership by
  [Battle entities](battle_entities.md); frame pacing by
  [Resident task system](../runtime/task_system.md).
- **Evidence limitations:** no runtime allocation trace, stage swap,
  continuation, or teardown capture was performed. Ordering and ownership are
  strong static results; update-to-frame timing is not established here.

## Battle update cadence

Native battle gameplay advances fighter updates at 30 Hz at nominal speed.
PCSX2 can report 60 VPS while the game still advances those fighter updates at
30 Hz; emulator turbo changes their wall-clock rate without changing the
gameplay cadence expressed in updates.

Statically, one call of `FUN_001F03E0` runs the camera controller, every graph
registry, and the stage owner at most once each, in the order given in
[Per-update dispatch](#per-update-dispatch). They therefore share one cadence.
Which scheduler invokes the battle process per frame is outside this document.

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
| stage-owner factory | `0x007099E0` | `0x00709A20` | `0x55B20` |
| stage-owner constructor | `0x00708760` | `0x007087A0` | `0x548A0` |
| stage-owner destructor | `0x00708860` | `0x007088A0` | `0x549A0` |
| constructor-only owner reset | `0x007089E0` | `0x00708A20` | `0x54B20` |
| `ccField` phase-1 update | `0x00708980` | `0x007089C0` | `0x54AC0` |
| `ccField` phase-2 callback | `0x00708BB0` | `0x00708BF0` | `0x54CF0` |
| controller global registration | `0x006C1A00` | `0x006C1A40` | `0xDB40` |
| stage select/controller setup | `0x006C1A10` | `0x006C1A50` | `0xDB50` |
| controller zero-initialization | `0x006C2890` | `0x006C28D0` | `0xE9D0` |
| stage global cleanup | `0x006C2960` | `0x006C29A0` | `0xEAA0` |
| controller deep cleanup | `0x006C29A0` | `0x006C29E0` | `0xEAE0` |
| stage path table | `0x008909D0` | `0x00890A10` | `0x1DCB10` |

The preserved symbol near the stage factory is shifted into the wrong body;
the raw prologue begins at export `0x007099E0`.

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
Entry type 2 additionally creates the `0xA8`-byte object at `0x00607658`.

`FUN_001EF330` then builds in this fixed order:

1. `FUN_001F4030(-1)`, `FUN_001BEA00`, `FUN_001DC6E0`, and `FUN_00309090(1)`,
   which creates the BTL auxiliary global at `0x00607844`.
2. When session `+0x18` is empty: allocate the `0x10`-byte graph, publish it at
   `0x00607654`, build it with `0x00709480`, publish the per-side command
   nodes (`0x00709800`) and fighters (`0x007099C0`) into manager
   `+0xDF0/+0xDF4` and `+0xDE4/+0xDE8`, and store the registry-A camera
   returned by `0x007096E0` at session `+0x14`.
3. Always call the node-start broadcast `0x007095E0`.
4. Create the camera controller at session `+0x1C` and publish it through
   `0x006DBD60`; see [Battle camera](battle_camera.md#shared-controller-entry-points).
5. Create the `0xC8`-byte resident object at session `+0x20`
   (`FUN_00373A20`).
6. Call BTL `0x00735E70` (transient-actor manager), `0x007063F0`,
   `0x00776B80`, and `0x00778830`. `0x007063F0` clears the two-side record
   block at BTL global `0x008D6A10`; teardown clears it again.
7. For continuation phase 2 only, call `FUN_001ECDE0`.
8. Create one `0x68`-byte per-side object for sides 1 and 2 through
   `0x0071A840` at session `+0x24/+0x28`.
9. Create the `0x44`-byte object at `+0x2C` (`0x0087E880`), the `0x70`-byte
   root at `+0x30`, and the `0xC`-byte object at `+0x34` (`0x006B4BA0`).
10. Call `FUN_0035CE20` with both character IDs.
11. Create, if absent, the `0x6C0`-byte battle-sequence object at
    `0x00607834`, initialize it through `0x0076E9D0(seq, P1, P2, slot)`, copy
    per-side flags, store the stage slot at sequence `+0x0E`, and call
    `0x0076EC10`.

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
| `+0x20` | owned `0xC8`-byte resident object |
| `+0x24/+0x28` | owned per-side `0x68`-byte objects |
| `+0x2C` | owned `0x44`-byte object |
| `+0x30` | owned `0x70`-byte BTL root |
| `+0x34` | owned `0xC`-byte object |

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
meaning of four slots:

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
calls `0x0076EF60(seq, P1 character, 0, 0)` on the battle-sequence object,
substate 2 waits for its byte `+0x10` to clear, and substate 3 clears its bit 0
and emits event 8 when no result is latched. Services run during those
substates as well.

`FUN_001F03E0` runs in this order. Mask bits and exceptions are in
[Pause and replay](pause_and_replay.md#selective-update-gating).

1. Battle-sequence pre-work `0x0076EF90`, then the camera controller update
   `0x006DC3B0(session+0x1C)`, both skipped while manager `+0x14 == 1`.
2. BTL `0x00706420`. This and the later `0x00706450` and `0x00706480` all
   run `0x007065E0` on the block at `0x008D6A10`, which walks both primary
   fighters from manager `+0xDE4/+0xDE8`.
3. Phase 1: `ccCameraCtrl`, `ccCommandCtrl`, the auxiliary global's work,
   `ccPlayerCtrl`, `ccBuddyAtkCtrl`, `ccFieldCtrl`, the transient-actor
   manager, and resident `FUN_00309190`, then battle-sequence post-work
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
| `+0x1C` | `0x34` | resident-owned singleton | resident `0x001F8F00` |

Every paired array is immediately registered with side IDs 0 and 1. Public
accessors at `0x006B3FB0`, `0x006B4000`, `0x006B4050`, and `0x006B40B0` read
the root through session global `0x00607604` and expose the arrays. None of the element constructors installs a vtable, so RTTI supplies
no names for these children.

Both root callbacks return immediately when byte `+0x21 == 1`. Otherwise the
first callback updates `+0x14` and `+0x1C` and then both sides of the six
paired arrays; the second updates both sides, then `+0x1C` and `+0x14`.
Initialization ends with `+0x21 = 0` and `+0x20 = 1`. The initializer store
`0x006B47A8` is the only direct byte store to `+0x21` in the root cluster, and
no resident or BTL site loads the root through the session global and then
writes `+0x20` or `+0x21`. In the clean game the gate is therefore always open
after initialization; an indirect writer is not excluded.

## Teardown order

Outer state `0x10` destroys the session through `FUN_001EECD0(session, 1)`
before state `0x11` releases the archives. `FUN_001EEFD0` destroys, in order:

1. the battle-sequence object at `0x00607834` (after `0x0076ECF0`);
2. the camera controller, then clears its published pointer;
3. session `+0x20`, `+0x24/+0x28`, `+0x2C`, the root at `+0x30`, and `+0x34`;
4. `FUN_00376B40`, the object at global `0x00607668` (after BTL
   `0x0087B160`), and the transient-actor manager (`0x00735F30`);
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

## Continuation encounters rebuild the session

There is no in-place round reset. Result `8` continuations leave outer state
`0x10` for `0x17` (`FUN_001EE1C0`) or `0x18` (`FUN_001EE500`). Both destroy
the whole session through `FUN_001EECD0`, rebuild fighter resources, and set
outer state `0x0D`; states `0x0D` and `0x0E` then load and construct a new
session exactly as for a first battle. State `0x17` only copies the incoming
slot `+0x9A` into `+0x98` and keeps the loaded stage archive; state `0x18`
releases the stage archive through `0x006C3160` and queues the next one
through `0x006C31D0`. Every stage-bound object described below is therefore
recreated for each encounter.

## Stage content binding

The stage factory allocates a `0x90`-byte `ccField`, constructs it with
fallback stage ID zero, and inserts it into `ccFieldCtrl`. The owner allocates
a `0xAD0`-byte controller whose vtable at controller `+0xA30` is
`ccBgControl` (`0x005DD6A0`), initializes it at `0x006C28D0`, publishes it
through `0x006C1A40` to global `0x006077E4`, stores it at owner `+0x70`, and
calls `0x006C1A50`.

When battle-manager global `0x00607600` exists, the signed stage ID comes from
manager byte `+0x98`; otherwise it uses the constructor fallback. Stage setup
mirrors the ID to manager `+0x98`, a second subsystem `+0x0E` when present, and
controller `+0x0C`. It indexes table `0x00890A10 + id * 4`, loads the path
through resident `SUB_001AA4B0`, stores the resource handle at controller
`+0x00`, and allocates a `0x150`-byte child at `+0x04`.

The table contains exactly slots 0 through 23, mapping to `stage/s01.ccs`
through `stage/s24.ccs`. The preserved export's shifted data mapping makes the
encoded live address appear to begin at its `s21` label; the raw file table
begins at offset `0x1DCB10` with the `s01` pointer. There is no range check
before indexing; the caller must constrain the slot.

Owner construction finishes through `0x00708A20`, which clears owner fields
`+0x74/+0x78`, snapshots controller `+0x10` to `+0x7C`, calls the empty
routine `0x006C1B80` on the controller, and clears `+0x80` and byte `+0x84`. A full direct-`jal` scan found this function only in the constructor.

### Per-update stage work

`ccField` is updated only through the node slots. Its phase-1 update
`0x007089C0` calls `ccBgControl` slot `+0x08` (the empty `0x006C1650`) and then
slot `+0x10` (`0x006C17C0`) with argument 0, and always returns 0, so the stage
owner is never removed by the walker. Its phase-2 callback `0x00708BF0` calls
`ccBgControl` slot `+0x0C` (`0x006C1660`). Its phase-3 slot is empty. The
background work those slots perform is owned by
[Stages](stages.md#live-environment-ownership-and-construction).

The two stage passes differ in kind. Phase 1 ends in resident
`FUN_003ACAD0`, which calls each background object's vtable `+0x08` over five
lists. Phase 2 ends in resident `FUN_003ACBF0`, which sets render state and,
for each of the scene's 12 selector groups, installs that group's view object
in resident `0x006073F4`, calls each object's vtable `+0x0C`, and finally
restores `0x006073F4` to the battle cameras' output object `0x00609160`. For
the stage, phase 1 is therefore an update pass and phase 2 a draw pass. That
the same split holds for every registry is an inference.

Stage-owner destruction calls controller deep cleanup at `0x006C29E0`, then
`0x006C29A0`, which resets the related resident subsystem and clears global
`0x006077E4`. It frees optional controller field `+0xA88`, frees the
controller, clears owner `+0x70`, and tears down the owner's member and base.

## Stage-specific inputs

A battle consumes these per-stage inputs, all keyed by the raw slot at manager
`+0x98`:

- the stage archive path from the 24-entry table at `0x00890A10`;
- the stage-associated archive from resident `FUN_00207E20(slot)`;
- the archive's `BIN_bgdata` records and `DMY_*` line/boundary nodes, read by
  `ccBgControl`; see [Stages](stages.md);
- the per-stage camera record selected by `ccCamera01`; see
  [Battle camera](battle_camera.md#per-stage-camera-record);
- the slot passed to the battle-sequence object (`0x0076E9D0`, sequence
  `+0x0E`).

## Limits and negative results

- No top-level round-reset path exists: continuation encounters destroy and
  rebuild the session.
- Root byte `+0x21` has no direct writer other than its initializer.
- The stage-owner destructor is virtual and has no direct `jal` caller; its
  container/vtable teardown chain supplies the evidence.
- Findings are static; no runtime validation was performed.
