# Battle stage gameplay knowledge

This document owns established and unresolved knowledge about retail NA2
(`SLPS-25837`) battle-stage resources, live environment objects, stage
geometry, geometry-driven movement, and stage teardown. It does not cover
Stage Select presentation or Adventure mode.

## Research coverage

- **Assigned scope:** the retail NA2 battle-stage implementation in
  `PRG/BTL.BIN` and the resident executable: load-slot/resource mapping,
  archive and object lifecycle, stage-authored geometry and configuration,
  background transitions, reactive or damaging objects, and unload/cleanup.
  Stage Select was in scope only where needed to prove the raw-slot handoff.
- **Exploration depth:**
  - Exhaustive over fixed tables and assets: all 24 stage-path entries and
    the 24-entry logical-ID mapper; every `STAGE/S01.CCS`..`S24.CCS`
    `BIN_bgdata` payload, structurally validated; the record counts of every
    named background factory; and the four authored line/config records of
    every archive. This is not a semantic decode of all 129 non-null
    factory-table entries.
  - Exhaustive for exact encoded targets: the surface/effect classifier's
    eight BTL and seven resident consumers, the BTL calls to resident
    fighter-hit entry `FUN_002335F0`, and the direct calls to both line
    accessors.
  - Bounded traces: resident controller states 9..17 and 23/24 with the four
    BTL archive helpers, graph construction, teardown, and switching;
    `ccField`/`ccBgControl` construction, scene parsing/dispatch, the owning
    and selector lists, and the named BTL factory methods and destructors;
    resident factories 10, 17, 31, 33, and 34 and their consumers; line
    construction and the cached attribute pass; the route planner's direct
    callers and AI tick gate; the two damaging objects through the resident
    HP subtractor; and the footprint, LandingTree/Mangrove, CrashBreak, and
    wire methods.
  - Sampled: the configuration-string table shows representative unique
    records rather than every string from every stage.
- **Confirmed coverage:** the load-slot/logical-ID distinction; stage and
  `n_rash` archive ownership; raw selection initialization and handoff;
  `BIN_bgdata` framing, factory routing, and per-stage census; scene
  ownership; boundary/floor line construction, active head 0 with count 1 per
  populated section, and cached polygon-attribute provenance; surface-effect classification; proximity transitions;
  navigation data and the AI gating of its ordinary route planner; generated
  wire environment registration, dirty refresh, and unregister/free;
  breakable, reborn, deformable, and reactive props, including foot-contact
  placement/fade and LandingTree/Mangrove displacement; the two explicit
  stage-object-to-HP paths; normal, switch, and emergency teardown ordering;
  the mandatory per-archive records; native player-node placement
  initialization and recovery placement; fog consumption; and factory-17
  model-rendering consumption. Scene update restrictions and selected
  visibility/factor consumers bound the units used by the documented counters
  and animation steps.
- **Unresolved or untested:**
  - no semantic reader of cached line attribute `+0x2C` was identified in the
    navigation, direct-accessor, or line-head alias paths; computed or
    indirect consumers remain open;
  - writers of the line active-index bytes beyond the control initializer's
    zero stores, through unaligned partial stores or untraced pointer
    arithmetic;
  - original names for other factory-table entries, numeric route/effect
    codes, surface-effect variant materials, and factory-17's two render
    coefficients;
  - the direct-call censuses are not proof against every indirect caller;
  - other writers of scene factor `scene+8`; local update counts do not
    establish elapsed time;
  - the exact context-scaled HP delta of the two damaging stage objects.
- **Deliberate exclusions and overlap:** Adventure mode, localization, and
  fighter mechanics outside the documented stage consumers. Stage Select beyond
  the slot handoff belongs to [Native Stage Select](../../game/stage_select.md). NUN3 stages belong to
  [NUN3 battle stages](nun3_stages.md). Controller/state ownership belongs to
  [Battle AI](../session/battle_ai.md); the general collision queries, including the
  boundary clamp and floor-profile query over stage lines, belong to
  [Collision](../combat/collision.md#stage-query-functions); polygon attribute
  production and contact-code consequences belong to
  [Stage surface attributes](stage_surface_attributes.md); fighter section
  changes belong to [Section transfers](section_transfers.md); damage
  calculation and HP application belong to [Damage](../combat/damage.md); stage-object
  battle-statistic credit belongs to
  [Match outcomes](../session/battle_statistics.md#ninja-tools-and-stage-objects); the
  `0x6C0` pause controller that carries a stage-slot tag belongs to
  [Pause and replay](../session/pause_and_replay.md#shared-ownership-and-controller-lifecycle);
  battle-session state order belongs to
  [Battle lifecycle](../session/battle_lifecycle.md); per-stage camera records belong to
  [Battle camera](../session/battle_camera.md).
- **Evidence limitations:** validation was static against the retail
  `BTL.BIN`, resident `SLPS_258.37`, and the retail `STAGE/` archives, whose
  sizes match their `GZLIST.TXT` entries. No runtime validation was performed,
  so indirect runtime behavior beyond the encoded targets remains open.

## Evidence and address convention

Retail input identities and BTL/resident address conversions are defined in
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
BTL addresses below name the preserved Ghidra location, complete-file offset,
and live address where relevant.

Claims described as **confirmed** follow directly from raw bytes and control or
data flow. **Supported** interpretations additionally use RTTI, resource names,
or surrounding behavior. **Unresolved** interpretations are retained only as
leads.

## Stage identity and resource mapping

The battle manager byte at `+0x98` is the active zero-based **load slot**, not
the one-based logical stage ID. The pending load slot used by stage switching
is at `+0x9A`. `FUN_006c1a10` copies its slot argument to manager `+0x98` and
to `ccBgControl+0x0C` before indexing the archive table. Controller mode 2's
fixed slot `6` (BTL entry type 2, Practice in
[Mode flow](../../game/mode_flow.md#mode-select-result-table); handoff below)
therefore selects `stage/s07.ccs`, not `stage/s06.ccs`.

The 24 archive strings occupy raw file `0x1DC990 + 0x10 * slot`, live
`0x00890890 + 0x10 * slot`. Their pointer table occupies file
`0x1DCB10 + 4 * slot`, live `0x00890A10 + 4 * slot`. Each raw pointer is the
live address of the corresponding string.

The raw ID mapper begins at Ghidra-located bytes `0x006C14A0`, file
`0x00D5E0`, live `0x006C14E0`, and returns the following logical IDs for slots
`0..23`:

```text
1, 2, 23, 24, 5, 6, 7, 8, 9, 10, 11, 12,
13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 3, 4
```

The same sequence is independently present as
the first word of the 24 Stage Select records at Ghidra/file/live
`0x008C3AD0 / 0x20FC10 / 0x008C3B10`. Their second word is a preview index,
equal to the slot in every retail row; the records belong to
[Native Stage Select](../../game/stage_select.md#stage-records).

| Logical ID | Load slot | Archive |
| ---: | ---: | --- |
| 1 | 0 | `stage/s01.ccs` |
| 2 | 1 | `stage/s02.ccs` |
| 23 | 2 | `stage/s03.ccs` |
| 24 | 3 | `stage/s04.ccs` |
| 5 | 4 | `stage/s05.ccs` |
| 6 | 5 | `stage/s06.ccs` |
| 7 | 6 | `stage/s07.ccs` |
| 8 | 7 | `stage/s08.ccs` |
| 9 | 8 | `stage/s09.ccs` |
| 10 | 9 | `stage/s10.ccs` |
| 11 | 10 | `stage/s11.ccs` |
| 12 | 11 | `stage/s12.ccs` |
| 13 | 12 | `stage/s13.ccs` |
| 14 | 13 | `stage/s14.ccs` |
| 15 | 14 | `stage/s15.ccs` |
| 16 | 15 | `stage/s16.ccs` |
| 17 | 16 | `stage/s17.ccs` |
| 18 | 17 | `stage/s18.ccs` |
| 19 | 18 | `stage/s19.ccs` |
| 20 | 19 | `stage/s20.ccs` |
| 21 | 20 | `stage/s21.ccs` |
| 22 | 21 | `stage/s22.ccs` |
| 3 | 22 | `stage/s23.ccs` |
| 4 | 23 | `stage/s24.ccs` |

The pointer table's preserved Ghidra location is `0x008909D0`; its first entry,
at raw file `0x1DCB10`, is `0x00890890`, the live `s01` string.

## Archive preload, adoption, and switching

The resident battle controller orchestrates the archive resource-node lifetime.
Its complete state order belongs to
[Battle lifecycle](../session/battle_lifecycle.md#resident-setup-order). The confirmed
stage-archive sequence is:

1. Controller state 9, `FUN_001ed6d0`, writes the selected load slot to manager
   `+0x98`. State 10, `FUN_001ed880`, releases selection/common handles and
   calls `FUN_001e9520(1)`.
2. Resident `FUN_001e9520(async)` prepares common resources, both fighters' archives,
   the selected stage archive, and a second stage-associated resource returned
   by `FUN_00207e20(slot)`. Its synchronous branch calls live BTL
   `0x006C3100`; its asynchronous branch calls live `0x006C31D0` and starts a
   loader fence with `FUN_001cfcd0(1)`.
3. Controller state 11, `FUN_001ed980`, waits for `FUN_001cfd70() == 0` and
   finalizes the queue with `FUN_001cfd90`. State 12, `FUN_001ed9e0`, polls
   `FUN_00200670` and `FUN_00201ef0` and advances when either is nonzero.
4. State 13, `FUN_001eda50`, constructs and registers both fighters, then calls
   live BTL `0x006C3210`. That helper obtains the selected archive with
   resident `FUN_001aa4b0(path)` and stores the handle in BTL GP slot
   `gp-0x3210`.
5. State 14, `FUN_001edb00`, waits for the final gates and calls
   `FUN_001ec3b0` only when both `FUN_00201ef0` and `FUN_00203ae0` are nonzero;
   its heavy graph constructor is `FUN_001ef330`.
6. State 15 repeatedly calls `FUN_001ef8f0` until the main graph reports ready.
   This is whole-battle readiness; the evidence does not isolate it as an
   environment-only update.

No direct caller of the `FUN_001e9520(0)` synchronous branch was found.

The state-9 handoff is a raw slot handoff, not a logical-ID conversion. State 9
runs the BTL Stage Select object described in
[Native Stage Select](../../game/stage_select.md); on success its getter at
live `0x00714810` returns the raw slot of the current choice, and state 9 stores
its low byte directly at manager `+0x98`. The retail choice list is all 24 raw
slots in ascending order, and controller mode 2 preselects slot 6.

The initializer itself reads manager snapshot byte `+0x114` and preselects that
slot. State 9 then calls the selection setter again at runtime `0x001ED770`.
For entry type 2 it passes fixed slot `6`, so this second call replaces the
initializer's restored snapshot selection. Other entry types obtain the second
call's argument from active slot `+0x98`; when that byte is `0xFF`, resident
code changes the argument to slot `0` before calling the setter.

The corresponding resident callsites are `0x001ED734`, `0x001ED744`,
`0x001ED770`, `0x001ED784`, `0x001ED7C4`, `0x001ED80C`, and `0x001ED7E8`;
their preserved Ghidra targets are respectively `0x00713A10`, `0x00713D80`,
`0x00714780`, `0x007157F0`, `0x007147D0`, `0x00715C80`, and `0x00713AE0`. The
manager write is runtime `0x001ED7D0`.

Manager `+0x98`, `+0x99`, and `+0x9A` are a contiguous three-byte configuration
group at the end of the block beginning at `+0x20`; resident `FUN_001f4b60`
initializes all three to `0xFF`, and `FUN_001f4dd0` snapshots them at
`+0x114..+0x116`. Lifecycle code proves `+0x98` is the active stage/load slot
and uses `+0x9A` as the incoming slot in transition states 23/24. The lifecycle
meaning of `+0x99` is unobserved beyond initialization, snapshot, and restore.
`FUN_001f2ac0(..., 0)` generates `+0x9A`, and `FUN_001f4f20` resets it.

Other confirmed writers are:

| Writer | Runtime / ELF file | Proven write |
| --- | --- | --- |
| state-9 success | `0x001ED7D0 / 0x0ED8D0` | selected raw slot -> `+0x98` after getter callsite `0x001ED7C4` |
| `FUN_001f2ac0`, nonzero second argument | `0x001F2C14 / 0x0F2D14` | generated slot -> `+0x98` |
| `FUN_001f2ac0`, zero second argument | `0x001F2C24 / 0x0F2D24` | generated slot -> `+0x9A` |
| transition state 23 | `0x001EE384 / 0x0EE484` | guarded `+0x9A -> +0x98`; normally a no-op because this path does not generate `+0x9A`, and no archive swap is present |
| transition state 24 | `0x001EE7B4 / 0x0EE8B4` | guarded non-`-1` `+0x9A -> +0x98`, followed by stage enqueue at `0x001EE7C4` and `n_rash` selection at `0x001EE7D0` |
| `FUN_001fe540` | `0x001FE6F4 / 0x0FE7F4` | imported record `+0x128` loaded four bytes earlier, then stored to `+0x98` and snapshotted; sole direct caller `0x001FF108` |
| `FUN_001f4ed0` | function runtime `0x001F4ED0` | restore all three bytes from `+0x114..+0x116` |
| live BTL `0x006C1A50` | write live `0x006C1A74`, file `0x00DB74`, Ghidra `0x006C1A34` | ccField loader slot -> manager `+0x98` |

`FUN_001f2ac0` first calls `FUN_001f4f20`, which clears `+0x9A`. Its sole
zero-second-argument caller is runtime `0x001F3284`, guarded on lifecycle state
`0x18` (decimal 24); this is the path that generates the next fighter at
`+0x78` and next stage/load slot at `+0x9A`. The nonzero call at runtime
`0x001F31DC` is guarded on state 4/result 1 and writes the initial fighter and
active slot instead. Its ordinary branch uses a random value modulo 24; its
scripted branch trusts byte 2 of a three-byte fighter/stage record without a
range check. State 16 selects state 24 for mode 8/submode 2, but state
23 for submode 1. Therefore the ordinary state-23 guarded copy sees `0xFF` and
does nothing. A restored snapshot could populate `+0x9A`, but adopting a
different value in state 23 would violate the visible resource invariant
because that function performs no stage or associated-archive swap. State 24
is the proven generated-next-stage load path.

### Stage-grouped `n_rash` battle animation/effect archive

The second resource selected by resident `FUN_00207e20(slot)` is a confirmed
stage-grouped battle animation/effect archive. The selector is runtime `0x00207E20`, ELF
file `0x00107F20`; its six-pointer table is runtime `0x00407390`, ELF file
`0x00307490`:

| Table index | Path runtime | Path | Slots returned by `FUN_00207e20` |
| ---: | ---: | --- | --- |
| 0 | `0x00407328` | `n_rash.ccs` | every slot not listed below, and out-of-range values |
| 1 | `0x00407338` | `n_rash1.ccs` | never returned |
| 2 | `0x00407348` | `n_rash2.ccs` | never returned |
| 3 | `0x00407358` | `n_rash3.ccs` | 10, 13 |
| 4 | `0x00407368` | `n_rash4.ccs` | 18 |
| 5 | `0x00407378` | `n_rash5.ccs` | 0, 1, 6, 19, 20 |

`FUN_00207ee0` implements the same mapping but accepts `-1` as "use active
slot," falling back to slot 0 if no active slot is available. Indices 1 and 2
exist in the table but neither selector can return them. Their path pointers
occur in the retail resident ELF only in these two table words, with no decoded
code xrefs; `ANM_rash_c/d` are likewise unreachable through the selected-index
path. This is a strong static negative, not proof against every hypothetical
dynamic name lookup.

Resident `FUN_00208cf0`, runtime `0x00208CF0`, ELF file `0x00108DF0`, asserts
both `2cmnbod1` and the selected `n_rash` archive, resolves `ANM_rash_p1`, and
selects the parallel animation with the same group index. Reachable pairs are
index 0 -> `ANM_rash_b`, 3 -> `ANM_rash_e`, 4 -> `ANM_rash_f`, and 5 ->
`ANM_rash_g`; `c`/`d` correspond to unreachable indices 1/2. The archive role
is broader than that family: `FUN_00205620` resolves `ANM_gear1_la/ra`,
`ANM_gear2_la/ra`, `ANM_wait1_la/ra`, `ANM_wait2_la/ra`, and `ANM_kizu_a`,
while `FUN_002068a0` resolves `ANM_xrush_ca`, `ANM_start`,
`ANM_fight_01a/02a/03a`, and `TEX_xrush`. All three consumers perform borrowed
resource lookups without a reference increment. This supports a stage-grouped
battle animation/effect archive, not generic stage geometry.

The archive is looked up and loaded/enqueued beside the stage archive in
`FUN_001e9520`, but no dedicated handle is retained. Normal teardown and
central cleanup recompute its path from active `+0x98`, look it up, and call
`FUN_001a9790(handle, 1)`. A stage switch unloads the old path before replacing
`+0x98`, then enqueues the new path if absent. Consequently, changing between
two slots in the same group still unloads and re-enqueues the same path.
Consumers own only the derived animation/effect objects: their destructors tear
those children down but contain no archive-handle release. This is why graph
and fighter destruction must precede the state-17 archive unload.

The four BTL archive helpers use the same slot-to-path table:

| Preserved symbol | Ghidra | File | Live | Confirmed behavior |
| --- | ---: | ---: | ---: | --- |
| `FUN_006c30c0` | `0x006C30C0` | `0x00F200` | `0x006C3100` | Look up with `FUN_001aa450`; if absent load synchronously with `FUN_00116de0(path, 0)`; store the handle at `gp-0x3210`. |
| `FUN_006c3120` | `0x006C3120` | `0x00F260` | `0x006C3160` | Release the stored handle with `FUN_001a9790(handle, 1)` and clear it. |
| `FUN_006c3190` | `0x006C3190` | `0x00F2D0` | `0x006C31D0` | Enqueue `FUN_001cf9e0(path, 0)`. |
| `FUN_006c31d0` | `0x006C31D0` | `0x00F310` | `0x006C3210` | Adopt the post-fence handle through `FUN_001aa4b0(path)` and store it at `gp-0x3210`. |

With resident GP `0x0060A9F0`, `gp-0x3210` is global `0x006077E0`. The BTL
stage helpers index their 24-entry path table directly and perform no range or
sentinel check, so every acquire/enqueue/adopt or field-construction call
requires a live slot in `0..23`. This differs from the defensive default in
`FUN_00207e20`. Retail selection and the ordinary random generator produce a
slot in `0..23`, and the normal state-24 generator runs before that state can
dispatch. Imported-record, scripted-record, and snapshot-restore paths instead
copy trusted slot bytes without an upper-bound check; they reject or overwrite
`-1` where their control flow requires it, but malformed values outside
`0..23` could still index this table out of bounds.

Stage and `n_rash` archive paths assume exclusive lifecycle ownership. The
stage sync helper stores an already-present lookup node just like a newly
loaded one, and release later destroys it unconditionally; `n_rash` loading
skips a preexisting node but teardown still looks it up and destroys it. There
is no loaded-by-this-controller bit. By contrast, the adjacent four-resource
common bundle tracks one ownership bit per member and preserves preexisting
members. This is further evidence against a shared reference-count contract for
the stage paths.

The final store in `FUN_006c31d0` is raw Ghidra `0x006C31F4`, file
`0x00F334`, live `0x006C3234`: `sw v0,-0x3210(gp)`. No direct BTL `jal` or function-pointer word targets these
four helpers. Their confirmed callers are resident code using the live overlay
addresses.

`FUN_001ee500` (state 24) owns the stage-changing result-8 continuation path;
its session rebuild belongs to
[Battle lifecycle](../session/battle_lifecycle.md#continuation-encounters-rebuild-the-session)
and its outcome routing to
[Match outcomes](../session/match_outcomes.md#higher-level-sequence-counter-and-result-8-continuation).
It compares active slot `+0x98` with incoming stage slot `+0x9A` after
destroying the old runtime graph. When they differ, it releases the old archive and `FUN_00207e20` resource
before testing the incoming slot against `-1`. Only a non-`-1` incoming slot
is then copied to `+0x98`, enqueued with its associated resource, fenced, and
returned to state 13 construction. The normal generator ordering supplies a
valid incoming slot before state 24 dispatch; that invariant is necessary
because the release precedes the sentinel guard. This is resource switching;
it is not evidence for an in-arena stage transition.

## Live environment ownership and construction

RTTI and installed vtables establish the following ownership chain:

```text
resident graph root +0x18 -> BTL field owner (size 0x10)
  owner +0x0C -> ccFieldCtrl (allocated size 0x10; count/head/tail/vtable)
    list member -> ccField (allocated size 0x90; prev/next at +0x18/+0x1C)
      +0x60 -> embedded ccGameObjCtrl (vptr at +0x6C)
      +0x70 -> ccBgControl (allocated size 0xAD0)
                 +0x00 -> borrowed/lookup stage archive handle
                 +0x04 -> ccBgSystem (allocated size 0x150)
                 +0x0C -> zero-based load slot
```

| Type | Installed vtable | RTTI/name evidence |
| --- | ---: | --- |
| `ccField` | `0x005DDD80` at object `+0x50` | RTTI `0x008C3958`; name pointer `0x00604B58` spells `ccField` in the resident ELF. |
| `ccFieldCtrl` | `0x005DDD60` at control `+0x0C` | RTTI `0x008C3940`; name at live `0x00898B10`, BTL file `0x1E4C10`. This is a separately allocated object stored at owner `+0x0C`. |
| embedded `ccGameObjCtrl` | `0x005DDB60` at `(ccField+0x60)+0x0C`, hence `ccField+0x6C` | RTTI descriptor `0x008C2348`, name pointer `0x00891500`; constructed by live `0x00709BC0`. It is not the separately allocated `ccFieldCtrl`. |
| `ccBgControl` | `0x005DD6A0` at inner `+0xA30` | RTTI `0x008C1FE8`; name at Ghidra/file/live `0x00890C08 / 0x1DCD48 / 0x00890C48`. |
| `ccBgSystem` | `0x005DD688` at scene `+0x140` | RTTI `0x008C1FE0`; name at Ghidra/file/live `0x00890BF8 / 0x1DCD38 / 0x00890C38`. |

Resident `FUN_001EF330` is the sole direct integration caller found for the BTL
field-graph builder: runtime/file callsite `0x001EF3C0 / 0x0EF4C0` targets live
`0x00709480`, actual preserved `FUN_00709440`, file `0x055580`. The resident
root allocates the `0x10`-byte owner at root `+0x18` and initializes it through
live `0x00709240` (preserved `FUN_00709200`, file `0x055340`). That owner
allocates four subobjects; its standalone `ccFieldCtrl` is constructed through
live `0x00709150` (preserved `FUN_00709110`, file `0x055250`).

The builder creates several peers and the `ccField`, cross-links them at peer
`+0x20/+0x24`, and appends the field to `ccFieldCtrl` through live
`0x00709E60` (preserved raw `0x00709E20`, file `0x055F60`). The append writes
field prev/next at `+0x18/+0x1C` and updates controller head, tail, and count.
This establishes direct resident-graph ownership rather than a free global
environment singleton.

RTTI ancestry agrees with the construction: `ccFieldCtrl` derives from
`ccGameObjCtrl`, while `ccField` derives from descriptor `0x008C2328`,
`ccGameObj`, and embeds a separate `ccGameObjCtrl` at `+0x60`; `ccField` does
not derive from `ccFieldCtrl`.

The `ccField` factory is preserved `FUN_007099e0`, Ghidra `0x007099E0`, file
`0x055B20`, live `0x00709A20`. It is called from preserved `FUN_00709440` at
Ghidra/file/live callsite `0x007094C4 / 0x055604 / 0x00709504`. The
factory allocates `0x90` bytes, calls the live `ccField` constructor at
`0x007087A0`, and then live `0x00709E60`.

The `ccField` constructor is preserved `FUN_00708760`, Ghidra
`0x00708760`, file `0x0548A0`, live `0x007087A0`. Its raw code proves that it:

- allocates a `0xAD0`-byte `ccBgControl` and initializes it with live
  `0x006C28D0`;
- publishes that control through a tiny live helper at `0x006C1A40`;
- when the battle manager exists, passes manager `+0x98`, `+0x4C`, and `+0x74`
  into the background constructor at file callsite `0x05494C`, live
  `0x0070884C`; the fallback call at file `0x05496C`, live `0x0070886C`, uses
  the caller's slot and `-1` identity values;
- stores the control at `ccField+0x70` and performs post-construction setup.

The background constructor is preserved `FUN_006c1a10`, Ghidra
`0x006C1A10`, file `0x00DB50`, live `0x006C1A50`. Its raw code confirms this
sequence:

1. Copy the slot to manager `+0x98`, the pause controller's `+0x0E`
   when present (see below), and `ccBgControl+0x0C`.
2. Index the live archive pointer table at `0x00890A10`, call resident
   `FUN_001aa4b0(path)`, and store the returned handle at `ccBgControl+0x00`.
3. Allocate and initialize a `0x150`-byte `ccBgSystem`; store it at
   `ccBgControl+0x04`.
4. Call resident `FUN_003AC740(scene, handle, "BIN_bgdata")`. The literal is at
   file `0x1DCB70`, live `0x00890A70`.
5. Initialize the stage-specific objects, line/config containers, flags, and
   ten small state blocks. Confirmed defaults include `+0x08 = 0`,
   `+0xE4 = -1`, `+0xE8 = -1`, and `+0xE0 = 0`.

Resident `FUN_003AC740` resolves `BIN_bgdata` with
`FUN_001A8F00(handle, name, 0)` and passes the object to `FUN_003AC7A0`.
That routine stores the archive handle at scene `+0x38`, the named object at
`+0x3C`, allocates collections at `+0xCC`, `+0xD0`, and `+0x108`, then calls
`FUN_003AD9A0`, `FUN_003ADE40`, `FUN_003AE220`, and `FUN_003AE170` to build
the environment object graph.

### `BIN_bgdata` records and factory dispatch

Resident `FUN_003ADE40`, runtime `0x003ADE40`, ELF file `0x002ADF40`, parses
the object behind `scene+0x3C`. It uses that object's byte length at `+0x04`,
skips three `|` delimiters, parses a record count, copies `count * 6` bytes of
three-`int16` records, and expands each record to a `0x10`-byte entry in the
array at `scene+0xC4`:

| Entry offset | Proven representation/use |
| ---: | --- |
| `+0x00` | sign-extended first source `int16`; high-level role unresolved |
| `+0x04` | sign-extended second source `int16`; factory/type index |
| `+0x08` | sign-extended third source `int16`; one of 12 scene-list selectors |
| `+0x0C` | optional following string pointer |

Resident `FUN_003AE220`, runtime `0x003AE220`, ELF file `0x002AE320`, passes
`(scene, &entry)` to the function pointer at
`PTR_FUN_005B3970[entry+0x04]`; the raw dispatch callsite is runtime
`0x003AE268`. Resident `FUN_003AC4D0`, runtime `0x003AC4D0`, copies the four
entry fields to object `+0x08/+0x0C/+0x10/+0x14`, stores the scene at object
`+0x04`, and appends an eight-byte object link to
`scene+0x44 + 4 * object->list_selector`. The class factories then call the
new object's virtual initializer at vtable `+0x14`. These 12 selector
collections are non-owning registration/link lists. A separate set of five
owning lists begins at scene `+0x74`; the first entry field chooses one of
those lists, and all named factory records in the retail archives use owner
list 4.

The dispatch table is resident runtime `0x005B3970`, ELF file `0x004B3A70`,
and has 129 non-null entries at indices 0 through 128. The following entries
are tied directly to named BTL classes through their installed vtables and
RTTI. Table words are live BTL pointers; the preserved Ghidra entry is always
`live - 0x40`.

| Factory index | Class | Preserved Ghidra / file / live factory | Vtable |
| ---: | --- | --- | ---: |
| 40 | `ccBgTransObject` | `0x006C7BD0 / 0x013D10 / 0x006C7C10` | `0x005DDA40` |
| 41 | `ccBgBreakDollBattle` | `0x006C71A0 / 0x0132E0 / 0x006C71E0` | `0x005DDA70` |
| 43 | `ccElectricWire` | `0x006C9A50 / 0x015B90 / 0x006C9A90` | `0x005DD9E0` |
| 48 | `ccBgLandingTreeBattle` | `0x006CA790 / 0x0168D0 / 0x006CA7D0` | `0x005DD990` |
| 50 | `ccBgBreakObjectBattle` | `0x006C5570 / 0x0116B0 / 0x006C55B0` | `0x005DDAE0` |
| 55 | `ccBgCrashBreakBattle` | `0x006CB250 / 0x017390 / 0x006CB290` | `0x005DD960` |
| 68 | `ccBgSuspensionBridge` | `0x006CD0E0 / 0x019220 / 0x006CD120` | `0x005DD910` |
| 75 | `ccBgEscapeBirdBattle` | `0x006CD540 / 0x019680 / 0x006CD580` | `0x005DD8E0` |
| 77 | `ccTumbleGrass` | `0x006CDC70 / 0x019DB0 / 0x006CDCB0` | `0x005DD8A0` |
| 78 | `ccBgBreakObjectRebornBattle` | `0x006CE070 / 0x01A1B0 / 0x006CE0B0` | `0x005DD870` |
| 79 | `ccBgTransObject2` | `0x006CE3F0 / 0x01A530 / 0x006CE430` | `0x005DD840` |
| 80 | `ccBgBreakObjectFallBattle` | `0x006CE9E0 / 0x01AB20 / 0x006CEA20` | `0x005DD810` |
| 81 | `ccBgBreakObjectMoveBattle` | `0x006CF3F0 / 0x01B530 / 0x006CF430` | `0x005DD7E0` |
| 82 | `ccHandRowShip` | `0x006CFCF0 / 0x01BE30 / 0x006CFD30` | `0x005DD7B0` |
| 83 | `ccCraneTruck` | `0x006D04B0 / 0x01C5F0 / 0x006D04F0` | `0x005DD780` |
| 84 | `ccHadesMarshSnake` | `0x006D21A0 / 0x01E2E0 / 0x006D21E0` | `0x005DD750` |
| 93 | `ccBgFootMarkBattle` | `0x006D3BB0 / 0x01FCF0 / 0x006D3BF0` | `0x005DD6F0` |
| 95 | `ccBgMangroveBattle` | `0x006D4280 / 0x0203C0 / 0x006D42C0` | `0x005DD6C0` |
| 102 | `ccBgBreakObjectBattleAnm` | `0x006C6790 / 0x0128D0 / 0x006C67D0` | `0x005DDAA0` |
| 103 | `ccBgBreakObjectBattleChandelier` | `0x006D3800 / 0x01F940 / 0x006D3840` | `0x005DD720` |
| 107 | `ccBgTransAnm` | `0x006C83D0 / 0x014510 / 0x006C8410` | `0x005DDA10` |

`ccGrassInfluence`, `ccWireHitModel`, and `ccBgAttackHit` do not occur as
top-level named entries in this factory linkage and are likely embedded/helper
types. That is a construction fact, not proof that they are unused.

### Resident generic factories and mandatory records

Factory indices 0 through 32 and several later indices point into the
resident ELF rather than BTL. They belong to a resident `ccBg*` scene-object
library whose class names are embedded near runtime `0x005B3330..0x005B3BF0`.
**Supported:** the class installed by each resident factory, identified by the
last RTTI-named vtable address loaded before the factory's
`FUN_003AC4D0` registration call, is:

| Factory indices | Class |
| --- | --- |
| 0 / 1 / 2 / 3 / 4 | `ccBgDrawObject` / `ccBgDrawClump` / `ccBgDrawAnm` / `ccBgDrawEff` / `ccBgDrawEffAnm` |
| 5 / 6 / 7 / 8 | `ccBgSwingTree` / `ccBgClothFlag` / `ccBgSwingGrass` / `ccBgRotateSky` |
| 11 / 12 / 18 | `ccBgGlareFilter` / `ccBgColorFilter` / `ccBgLightDistant` |
| 23 / 24 / 25 | `ccBgCurtain` / `ccBgClutAnmAlpha` / `ccBgClutAnmIndex` |
| 27 / 28 / 29 / 30 | `ccBgDrawShadowAnm` / `ccBgCelShadeAnm` / `ccBgUVAnm` / `ccBgWindBell` |
| 45 / 56 / 66 / 73 | `ccBgLantern` / `ccBgFloatingLightCtrl` / `ccBgDrawAnimationSpc1` / `ccBirdFly` |
| 57 / 58 / 59 / 60 / 61 / 62 | `ccBgDrawObjectGroup` / `ccBgDrawClumpGroup` / `ccBgDrawAnmGroup` / `ccBgSwingTreeGroup` / `ccBgSwingGrassGroup` / `ccBgSwingLeaf` |
| 85 / 86 / 87 / 88 / 114 | `ccBgCameraTraceObject` / `Clump` / `Animation` / `Eff` / `UVAnm` |
| 89 / 90 / 91 / 92 | `ccBgExtDrawObject` / `Clump` / `Anm` / `Eff` |
| 96 / 108 / 111 / 112 / 113 | `ccBgS13Effect` / `ccBgCamFallLeaf` / `ccBgEventProgDrawObj` / `Clump` / `Anm` |

The same heuristic names BTL entries 50, 84, and 102 as the embedded helper
`ccBgAttackHit` rather than the classes in the preceding table, so it can
select an embedded helper. The rows above are therefore supported class
identities, not decoded constructors.

The following non-class records are confirmed from their factory bodies:

| Factory | Confirmed behavior | Retail use |
| ---: | --- | --- |
| 10 (`0x00398A90`) | Packs tokens 0..2 as an RGB byte triple, parses token 3 as a float and tokens 4..6 as integers converted to floats, and stores the fog record at scene `+0xD4..+0xE4` through `FUN_003ACFE0`. | one per archive, e.g. `S01`: `125,200,190,0,40,0,100000` |
| 17 (`0x00399340`) | Converts two float tokens and stores them to globals `0x00618EE8` and `0x00618EE4`. | 21 archives, e.g. `0.45,0.35` |
| 31 (`0x0039D2B0`) | Resolves the configuration string in the scene archive through `FUN_001A8F00` and, when the result is neither 0 nor 4, stores it at `+0x08` of the selector owner `scene+0x44 + 4 * list_selector`. | every archive has `BLT_bg` and `BLT_obj`; `S03`, `S04`, `S10`, `S18`, and `S19` add `BLT_bg2`, `BLT_efe`, `BLT_hnd`, or `BLT_obj2` |
| 33 / 34 (BTL live `0x006C44C0` / `0x006C4520`) | Through live `0x006C3EE0`, resolve `DMY_pp1_010` / `DMY_pp2_010` (names at live `0x00890BE8` / `0x00890BF8`) and copy the node's position `vec4` to `ccBgControl+0xAB0` / `+0xAC0`. The lookup result is dereferenced without a null or sentinel check. | every archive, string `-1` |

Every retail archive has one record each for factories 10, 18, 33, 34, 35, 36,
37, and 38, at least the two factory-31 records above, and one factory-11
record (`S10` has two); 21 of 24 also have factory 17. Factory 18's configuration names the light animation
and light, for example `ANM_stalig00,255,255,255,LGT_dis_0`.

The `DMY_pp*_010` consumer is **confirmed**: field helper preserved
`0x00708F90`, file `0x0550D0`, live `0x00708FD0`, and its wrapper preserved
`0x00709070`, file `0x0551B0`, live `0x007090B0`, return a placement vector,
orientation vector, and section value. Side 0 copies control `+0xAB0` and
sets orientation component 2 to `+pi/2`; side 1 copies `+0xAC0` and uses
`-pi/2`. The helper adds `(0,0,200,1)` to the position, then forces its
component 3 to one. Its returned section is zero except for slot 12 (`S13`),
where it is one. This is a fighter recovery-position path: resident
`FUN_00235690`, action cases `0x61/0x62`, calls live `0x007090B0` with the
fighter's side bit and outputs at fighter `+0x30/+0x40`, then stores the
returned section to fighter section field `+0x9F6`, the same field that
[Section transfers](section_transfers.md#request-admission-and-retained-destination)
change. Case `0x62` additionally projects through live
`0x007090D0`. Resident `FUN_00216970` wraps the same operation, and its
confirmed caller `FUN_002C8690` uses it when the paired fighter has major
state 6/action `0x61`.

The native placement initializer is also confirmed: resident `0x0024D830`
calls live `0x00708FD0` with fighter side bit and outputs at `+0x30/+0x40`,
then stores the returned section at `+0x9F6`. It sets fighter `+0x61` bit
`0x40`, derives the facing fields `+0x98C/+0x98E/+0x990` from orientation
`+0x48`, clears retained attack `+0xE54`, fills eight position-history
vectors at `+0x840`, and enters major/substate `(0,0)` through `0x00217E40`.
The ordinary graph constructor `0x001EF330` calls live `0x007095E0` at
resident callsite `0x001EF42C`; its four-registry pass calls live `0x00709BF0`,
which invokes each node's vtable `+0x0C`. The representative concrete fighter
table `0x005DB170` contains `0x0024D830` at that slot. This connects the
authored player nodes to ordinary construction as well as recovery. The wider
fighter construction/registry inventory belongs to
[Battle entities](../session/battle_entities.md#primary-fighter-factory-and-lookup).

Factory 17 writes two **confirmed render coefficients**, rather than combat
values. They are fields `+0x28/+0x24` of the default light/render descriptor at
resident `0x00618EC0`. `FUN_001EB850` initializes that descriptor with
`FUN_0018FF40`, binds its resource through `FUN_0018FE90`, and sets the two
defaults to `0.4/0.3`. Resident phase dispatcher `FUN_001F03E0` selects the
descriptor through global `0x00602A60`; `FUN_001982B0` and `FUN_00198340`
copy that pointer to draw-parameter `+0x24C`. The packet builder
`FUN_0018F900` reads descriptor `+0x28`, multiplies it by 128 (and, for
draw flag `0x20000`, by draw opacity), and packs it into the color word's high
byte; descriptor `+0x24` is copied to packet word `+0x204`. This bounds both
stage-authored values to model rendering. Original semantic names for the
two coefficients are not established. BTL draw paths preserved
`0x00723250` and `0x00724AB0` temporarily adjust these globals and restore
them; factory 17 is therefore the authored base, not every draw's final value.

In retail `S01`, `BLT_bg` and `BLT_obj` are object-table names with no typed
section of their own, so the factory-31 store depends on what the resident
lookup returns for a section-less record; that value was not traced.

Factory 10's downstream meaning is **confirmed** by resident
`FUN_003ACBF0` -> `FUN_003AE390` -> `FUN_0010D0D0`. The scene draw routine
applies this record before drawing its 12 selector lists, and afterward calls
`FUN_003AE3D0` -> `FUN_0010D200`. The latter clears the drawing context's
`+0xE8` word. The fog record is:

| Scene offset | Source token | Consumer meaning |
| ---: | ---: | --- |
| `+0xD4` | 5 | near distance |
| `+0xD8` | 6 | far distance |
| `+0xDC` | 3 | near percentage |
| `+0xE0` | 4 | far percentage |
| `+0xE4` | 0, 1, 2 | packed RGB, low byte first |

`FUN_0010D0D0` stores the four floats in drawing-context
`+0xF0..+0xFC`, converts each percentage `p` to `(100-p)*2.55`, and stores
the linear distance ramp's slope/intercept at `+0x108/+0x10C`; packed color
goes to `+0x110`. Thus S01's authored example means distances `0..100000`
and percentages `0..40`. This consumer establishes the same fog role as
[NUN3 category 1](nun3_stages.md#nun3-scene-record-dispatch), while preserving
the games' different token ordering.

### Per-stage `BIN_bgdata` factory census

The retail extracted `STAGE/S01.CCS` through `S24.CCS` archives were
gzip-decompressed and parsed. Every archive contains exactly one CCS
object named `BIN_bgdata`, stored in a section whose full marker is
`0xCCCC2400` (low tag `0x2400`). Every payload validated the same framing:

```text
takaCreateBackGround|1.00|N|  N * { int16 field0, int16 factory, int16 list }
||  N pipe-terminated configuration strings
```

The two literal `|` bytes after the triple array are not record strings;
configuration string zero begins after both. This was checked on all 24 blobs:
each yielded exactly `N` triples and `N` aligned strings before section padding.
For every named factory below, `field0` is 4. The scene-list selector is 2 for
the ordinary background types and 4 for `ccBgTransObject`,
`ccBgTransObject2`, and `ccBgTransAnm`.

The census below is exhaustive for the named factory indices in the
preceding table. `N` includes all `BIN_bgdata` records, including generic types
whose compiled factories have not yet been named.

Factory 27 (`ccBgDrawShadowAnm`) has no record among the 1,487 entries across
these 24 payloads. This does not establish absence of ordinary stage shadows
or of that class through other construction routes. Its separate ownership
and draw path belong to
[Shadows](../../runtime/rendering/shadow_rendering.md#background-controller-and-fighter-consumers).

| Archive / load slot | N | Named factory records |
| --- | ---: | --- |
| `S01 / 0` | 85 | `TransObject x1`, `BreakObject x6`, `BreakReborn x3`, `BreakAnm x4`, `EscapeBird x10` |
| `S02 / 1` | 85 | `BreakDoll x3`, `BreakObject x5`, `BreakFall x10`, `EscapeBird x8`, `TransObject2 x2` |
| `S03 / 2` | 55 | `LandingTree x1`, `BreakDoll x2`, `BreakObject x1`, `TransObject x1` |
| `S04 / 3` | 61 | `BreakObject x5`, `BreakDoll x2`, `CrashBreak x3`, `TransAnm x1` |
| `S05 / 4` | 66 | `BreakObject x1`, `BreakDoll x5` |
| `S06 / 5` | 59 | `LandingTree x1`, `BreakDoll x4`, `BreakObject x1` |
| `S07 / 6` | 75 | `BreakDoll x4`, `BreakObject x1`, `LandingTree x1` |
| `S08 / 7` | 62 | `LandingTree x2`, `BreakObject x4`, `BreakDoll x1`, `BreakReborn x5` |
| `S09 / 8` | 52 | `BreakDoll x1`, `BreakObject x1` |
| `S10 / 9` | 57 | `BreakObject x1`, `BreakDoll x2`, `SuspensionBridge x1`, `TransObject x2` |
| `S11 / 10` | 93 | `BreakObject x4`, `BreakDoll x2`, `EscapeBird x3`, `LandingTree x1` |
| `S12 / 11` | 43 | `BreakDoll x4`, `BreakObject x1`, `FootMark x1` |
| `S13 / 12` | 63 | `BreakObject x1`, `BreakDoll x2`, `HandRowShip x1`, `CraneTruck x1`, `BreakFall x11`, `TransObject x1`, `Mangrove x1` |
| `S14 / 13` | 55 | `BreakObject x1`, `BreakDoll x3`, `LandingTree x2` |
| `S15 / 14` | 51 | `HadesMarshSnake x1`, `BreakObject x1`, `BreakDoll x1` |
| `S16 / 15` | 70 | `BreakObject x7`, `BreakDoll x4`, `FootMark x1`, `TumbleGrass x1` |
| `S17 / 16` | 33 | `BreakDoll x4`, `BreakObject x1`, `TransObject x1` |
| `S18 / 17` | 42 | `BreakDoll x4`, `BreakObject x1`, `FootMark x1` |
| `S19 / 18` | 65 | `ElectricWire x1`, `LandingTree x1`, `BreakDoll x4`, `BreakObject x1`, `EscapeBird x7` |
| `S20 / 19` | 72 | `BreakAnm x6`, `BreakFall x5`, `BreakObject x3`, `BreakDoll x2`, `TransObject x2` |
| `S21 / 20` | 59 | `ElectricWire x3`, `BreakChandelier x6`, `BreakAnm x4`, `TransAnm x2` |
| `S22 / 21` | 52 | `BreakDoll x4`, `BreakObject x1` |
| `S23 / 22` | 47 | `BreakObject x3`, `BreakDoll x4`, `TransObject x1` |
| `S24 / 23` | 85 | `BreakObject x13`, `BreakDoll x2`, `ElectricWire x3` |

This table is a physical-resource assignment. Convert its load slots to the
logical IDs used by stage selection with the mapping near the start of this
document; in particular logical IDs 3/4 use `S23/S24`, while logical IDs 23/24
use `S03/S04`.

Selected unique records preserve enough author data to make the assignments
concrete without guessing their visual names:

| Archive, record | Factory | Exact configuration string |
| --- | --- | --- |
| `S10 #53` | `ccBgSuspensionBridge` | `OBJ_gim02,17,0,DMY_hasi,TEX_s10obj22,DMY_hasira_a,DMY_hasira_b,120,180` |
| `S12 #38` | `ccBgFootMarkBattle` | `s12.ccs,OBJ_s12efe05,2` |
| `S13 #33` | `ccHandRowShip` | `OBJ_obj_010_,OBJ_obj_011_,DMY_fune_dummy` |
| `S13 #34` | `ccCraneTruck` | `-1` |
| `S13 #51` | `ccBgMangroveBattle` | `OBJ_obj_120,3,DMY_dummy_010,1,1,300,200,OBJ_obj_121,DMY_ki_dummy` |
| `S15 #27` | `ccHadesMarshSnake` | `-1` |
| `S16 #59` | `ccBgFootMarkBattle` | `s16.ccs,OBJ_s16efe00_,2` |
| `S16 #69` | `ccTumbleGrass` | `OBJ_kusa_000,DMY_kusa_010,5,80` |
| `S18 #35` | `ccBgFootMarkBattle` | `s18.ccs,OBJ_s18efe05,2` |
| `S19 #44` | `ccElectricWire` | `DMY_dummy_010,DMY_dummy_020,TEX_s19obj40` |
| `S21 #53` | `ccBgTransAnm` | `ANM_s21gim100,DMY_dmy_020,1,DMY_s21has00,250,1,3` |
| `S21 #54` | `ccBgTransAnm` | `ANM_s21gim00_a0,DMY_dmy_030,1,DMY_s21has01,250,1,9` |

`S21` records 39 through 41 instantiate three `ccElectricWire` objects using
three dummy-node endpoint pairs and `TEX_s21obj05`; records 43 through 48 are
six separately configured chandelier break objects. `S24` records 82 through
84 similarly use three endpoint pairs and `TEX_s24obj42`. These records prove
construction and configuration, but the class methods still determine whether
contact is visual, reactive, or damaging.

The resident heavy graph also allocates, at runtime/file
`0x001EF6A4 / 0x0EF7A4`, the separate `0x6C0`-byte pause controller
at global `0x00607834`; its ownership and behavior belong to
[Pause and replay](../session/pause_and_replay.md#shared-ownership-and-controller-lifecycle).
Its BTL constructor, live `0x0076E9D0`, stores the low/high bytes of the
scalar fighter/character identifiers from manager `+0x4C/+0x74` at object
`+0x04..+0x07` and mirrors the selected slot at `+0x0E`; no stage operation
uses that slot. Refresh live `0x0076EC10` passes it to live `0x006C2F10`
(preserved `FUN_006c2ed0`, file `0x00F010`), which overwrites the argument,
clears byte `+0x6B8`, and calls resident `FUN_001C8830` on the object at
`+0x6BC`. No stage table, archive, `ccField`, geometry, or boundary operation
is reached.

`ccField` update at live `0x007089C0` dispatches `ccBgControl` vtable slots
`+0x08` and `+0x10`; the latter is live `0x006C17C0`, preserved
`FUN_006c1780`. Another field entry at live `0x00708BF0` dispatches vtable
`+0x0C`, live `0x006C1660`, preserved `FUN_006c1620`. These virtual calls
explain the lack of ordinary direct xrefs, but the evidence does not justify
calling any one of them the per-frame environment update.

### Update eligibility and local timing

Control method live `0x006C17C0` consults resident `0x003AE660`. A true result
on transition disables object update field `+0x1C` for factory identities
2 and `0x30` (48) through `0x003ACF20`; a false result on transition restores
them. That helper walks all five owning lists and matches object `+0x0C`.
This is a selected-type update restriction. The method always calls scene
update `0x003ACAD0`, whose scene flag bit 1 skips the five object loops and
whose ordinary loops invoke virtual `+8` only for nonzero object `+0x1C`.
Scene bits 2/4/8 independently gate the three auxiliary controllers.
`0x003AE660` combines scene/control predicates, menu/sequence state, fighter
markers, and terminal-state queries; this trace does not assign one universal
pause meaning to it.

Scene initializer resident `0x003AD510` sets float `scene+8` to `1.0`.
`ccBgTransAnm` live `0x006C80E0` computes its animation step as
`u16(original_step * configured_multiplier * scene_factor)`; CrashBreak
live `0x006CA8A0` sets the active model step to `u16(256 * scene_factor)`.
Both supply that step to resident advance `0x001BB210`, whose unit is 1/256
animation frame. They therefore consume the scene factor; fixed fade changes,
cooldowns, and sampled table indices have separate per-invocation units.
The complete set of writers to `scene+8` is not established. Common advance
and absolute-seek semantics belong to
[Scene playback callers](../../runtime/scene_playback_owners.md#playback-families).

Eligibility can also be local. Resident `ccBgRotateSky` update `0x00398510`
retains bounds classification `0x001926A0` and advances/wraps angle by
configured `+0x50` only when retained. `ccBgUVAnm` update `0x0039B910`
similarly gates both UV-coordinate increments, multiplying their speeds by
`scene+8` and wrapping to `0..1`. The sway owner at `0x003997C0` gates its
phase increment `speed * scene_factor`, while the two-model owner at
`0x0039C160` skips countdown, random draws, and transform work when both
classification results reject. The classification mechanism and its limits
belong to [Visibility](../../runtime/rendering/visibility.md#bounded-resident-caller-inventory).
These statements concern the inspected methods, not every callback that could
modify an object.

In the object descriptions below, a tick means an eligible invocation of the
particular object's update method. Fixed counters/fades do not by themselves
prove a wall-clock frame rate. Animation frame numbers denote the separate
model playback cursor.

## Boundary and floor-profile data

### Line construction

Preserved `FUN_006c3380`, Ghidra `0x006C3380`, file `0x00F4C0`, live
`0x006C33C0`, builds linked line records from named nodes in the stage archive.
Direct callers are preserved `FUN_006c4600` and `FUN_006c4660`; they obtain the
background system through `FUN_006c1640` and use resident
`FUN_003947C0` as a fallback when it is absent.

A descriptor type at `+0x04` selects the side:

| Descriptor type | Side | Count byte | Pointer-array field |
| ---: | ---: | ---: | ---: |
| `0x25` | 0 | `ccBgControl+0xA8C` | `+0xA90` |
| `0x26` | 1 | `ccBgControl+0xA8D` | `+0xA94` |

The background control holds two line families for each side:

| Family | Group-count bytes | Active-index bytes | Pointer arrays |
| --- | --- | --- | --- |
| first | `+0xA8C/+0xA8D` | `+0xA8E/+0xA8F` | `+0xA90/+0xA94` |
| second | `+0xA98/+0xA99` | `+0xA9A/+0xA9B` | `+0xA9C/+0xAA0` |

`FUN_006c2890` zeros all these fields during control initialization. Each
allocated record is `0x30` bytes:

| Offset | Confirmed field |
| ---: | --- |
| `+0x00` | first endpoint, `vec4` |
| `+0x10` | second endpoint, `vec4` |
| `+0x20` | next record, or zero |
| `+0x24` | line flag, initially zero |
| `+0x28` | side/category, `0` or `1` |
| `+0x2C` | cached collision-polygon attribute word, initially zero |

The builder obtains a descriptor count, allocates `count * 0x30`, formats
three node names per record, resolves them through resident `FUN_001A8F00`,
and copies two resolved node vectors into the endpoints. The relevant format
strings are:

| String | Ghidra | File | Live |
| --- | ---: | ---: | ---: |
| `DMY_%scl_%d_nor` | `0x00890AF0` | `0x1DCC30` | `0x00890B30` |
| `DMY_%scl_%d_ewr` | `0x00890B00` | `0x1DCC40` | `0x00890B40` |
| `DMY_%scl_%d_mov` | `0x00890B10` | `0x1DCC50` | `0x00890B50` |
| `DMY_line_010` | `0x00890B48` | `0x1DCC88` | `0x00890B88` |
| `DMY_line_020` | `0x00890B58` | `0x1DCC98` | `0x00890B98` |
| `DMY_linemin01` | `0x00890B68` | `0x1DCCA8` | `0x00890BA8` |
| `DMY_linemax01` | `0x00890B78` | `0x1DCCB8` | `0x00890BB8` |
| `DMY_linemin02` | `0x00890B88` | `0x1DCCC8` | `0x00890BC8` |
| `DMY_linemax02` | `0x00890B98` | `0x1DCCD8` | `0x00890BD8` |

The first-family builder above is complemented by the actual routine beginning
at preserved `FUN_006c3710`, file `0x00F850`, live `0x006C3750`. Raw callers
at preserved `FUN_006c4540` and `FUN_006c45a0` target the live start. This routine consumes
descriptor type `0x23` or `0x24`, selecting base node name `DMY_line_010` or
`DMY_line_020`. It consumes the descriptor's node count in pairs and resolves
names in raw order: the base name, `_1`, `_2`, and so on. No even-count guard
is visible, so valid archive data is expected to supply pairs.

For the current sequential group index at control `+0x10`, it sets the
second-family count byte at `+0xA98+index` to one, allocates that group's
pointer array at `+0xA9C+4*index`, and allocates `(node_count / 2) * 0x30`
line records. Those records use the same layout above, with `+0x28` set to the
current group index. The function then increments control `+0x10`.

The same routine creates one `0x40`-byte section-config object and appends its
pointer to the vector whose size/data fields are control `+0xA84/+0xA88`:

| Config offset | Confirmed field |
| ---: | --- |
| `+0x00` | pointer to a separately allocated 12-byte vector header whose elements point to separately allocated `0x20`-byte endpoint pairs |
| `+0x10` | first boundary endpoint, `vec4` |
| `+0x20` | second boundary endpoint, `vec4` |
| `+0x30` | pointer to config `+0x10` |
| `+0x34` | pointer to config `+0x20` |
| `+0x38` | absolute component-0 span between the two endpoints |

The control vector is initialized with capacity two, matching the two named
line groups. The builder also resolves `DMY_linemin01`, `DMY_linemax01`,
`DMY_linemin02`, and `DMY_linemax02` into control vectors
`+0xA40/+0xA50/+0xA60/+0xA70`, then derives overall boundary vectors at
control `+0x20/+0x30` by component-0 comparison. These are archive node
positions, not a static global stage table.

The config's endpoint pairs copy only the two endpoint `vec4`s; they are not
aliases of the `0x30`-byte linked records and have no cached attribute tail.
The complete builder bytes corroborate the `0x20` allocation at preserved
`0x006C3968/0x006C396C`, the separate endpoint copies at
`0x006C3AC4..0x006C3AE0`, and pointer insertion at `0x006C3C60..0x006C3C84`.
Consequently the config's piecewise boundary resolver does not receive line
`+0x2C` through that vector. The resolver and general query contract belong to
[Collision](../combat/collision.md#stage-query-functions).

The first four records in every retail `BIN_bgdata` blob are exactly factory
indices `0x23`, `0x24`, `0x25`, and `0x26`. Their aligned configuration strings
therefore give the authored line counts per archive. For `0x23/0x24` the value
is a node count and the builder creates half as many second-family records; for
`0x25/0x26` it is the first-family record count directly. (`S06`'s `0x23`
string is `6, , , `; its parsed first token is 6.)

| Archive | Second family 0 | Second family 1 | First family 0 | First family 1 |
| --- | ---: | ---: | ---: | ---: |
| `S01` | 1 | 1 | 1 | 1 |
| `S02` | 5 | 3 | 1 | 2 |
| `S03` | 1 | 6 | 1 | 3 |
| `S04` | 5 | 1 | 1 | 1 |
| `S05` | 7 | 11 | 1 | 2 |
| `S06` | 3 | 5 | 1 | 2 |
| `S07` | 5 | 5 | 1 | 2 |
| `S08` | 7 | 5 | 3 | 1 |
| `S09` | 5 | 5 | 5 | 5 |
| `S10` | 5 | 12 | 5 | 5 |
| `S11` | 1 | 6 | 2 | 4 |
| `S12` | 1 | 1 | 1 | 1 |
| `S13` | 3 | 3 | 3 | 3 |
| `S14` | 1 | 1 | 1 | 3 |
| `S15` | 2 | 7 | 2 | 7 |
| `S16` | 1 | 5 | 1 | 1 |
| `S17` | 1 | 1 | 1 | 1 |
| `S18` | 1 | 1 | 1 | 1 |
| `S19` | 1 | 3 | 1 | 5 |
| `S20` | 1 | 1 | 1 | 1 |
| `S21` | 1 | 1 | 2 | 3 |
| `S22` | 1 | 1 | 1 | 1 |
| `S23` | 1 | 4 | 3 | 10 |
| `S24` | 7 | 7 | 8 | 9 |

Preserved `FUN_006c1b80`, file `0x00DCC0`, live `0x006C1BC0`, walks every
record in both families and sides, queries a vertical segment through each
segment midpoint, and on a hit caches the selected collision polygon's `+0x0C`
attribute word (the same word the query's include/exclude mask tests use) at
record `+0x2C`. The line therefore stores polygon attributes, not a collider
pointer or distance; a missed query preserves the previous cached value. The
query parameters and the resident source path of that word belong to
[Collision](../combat/collision.md#stage-query-functions).

### Cached line attribute consumers

**Confirmed accessor identities:** complete bytes at preserved
`0x00708D20..0x00708D9C` distinguish two superficially similar getters:

| Preserved entry / file / live | Returned head |
| --- | --- |
| `0x00708D20 / 0x054E60 / 0x00708D60` | first-family table `+0xA90 + 4*section`, indexed by byte `+0xA8E + section` |
| `0x00708D60 / 0x054EA0 / 0x00708DA0` | second-family table `+0xA9C + 4*section`, indexed by byte `+0xA9A + section` |

Both return zero when `ccField+0x70` is absent and otherwise return the chosen
head without reading a record's attributes. Encoded JAL targets are live
addresses, so an annotation naming `FUN_00708d60` does not by itself identify
the second getter.

**Bounded direct-call coverage:** the aligned words of the whole BTL text
mapping (complete-file `0x40..0x1DB6FF`) contain ten direct calls to the first
getter and one to the second. The resident ELF adds two first-getter calls and
none to the second; ETC contains neither target, and BTL holds no literal
pointer word for either getter. This enumerates direct encodings, not computed
calls.

| Consumer | Established fields and consequence |
| --- | --- |
| Three nearest-line queries, preserved `0x006F1F20`, `0x006F2160`, `0x006F24A0` | First-family endpoints, next `+0x20`, and filter word `+0x24`; return a selected line pointer. Their direct BTL callers all remain within the audited navigation interval. |
| Planner, executor, AI proximity path, and line-map initialization; getter calls at preserved `0x006F3BF4`, `0x006F3C78`, `0x006F71B0`, `0x006FC398`, `0x007059F0` | First-family identity, endpoints, and next links. Initialization stores line pointers in `0x008D6500` and derives section extrema from endpoints; route code uses those pointers and compiled adjacency records. |
| Preserved `0x006F75E0` continuation, getter call `0x006F77BC` | Second-family head endpoints determine which side of its midpoint the fighter occupies; this path does not classify its cached polygon word. |
| Preserved `0x0082E810..0x0082EA34`, live entry `0x0082E850`, getter call `0x0082E860` | First-family endpoint extrema and next links clamp a supplied position; subsequent floor-profile and fresh environment queries use the position, rather than cached line attributes. |
| Preserved `0x00849150..0x00849328`, live entry `0x00849190`, getter call `0x00849220` | First-family endpoint vectors and next links choose an endpoint nearest the supplied component-0 position and copy it to the output. No line attribute tail is copied. |
| Resident `0x002DEEC0` and `0x002DEFE0`, getter calls `0x002DEF04/0x002DF0A8` | Endpoints and next links map current/stored fighter positions to line indices. The second helper compares indices and consults a stage/section/index table; neither reads cached attributes. Their inspected callers use the index or boolean result. |

The complete byte intervals of the two late-BTL functions above show loads from
endpoint offsets `0/0x10`, scalar endpoint components, and next `+0x20`, with
no line `+0x2C` read; the resident functions show the same field distinction.
Their original player-facing roles are not named here.

**Bounded alias result:** exact `+0xA90/+0xA94/+0xA9C/+0xAA0` head-table
loads and address formations in the BTL text resolve to the builders, cached
midpoint pass, floor-profile query, destruction, and these two getters.
Two other `+0xA90` formations belong to the separate interaction-manager
layout, and the apparent `+0xAA0` formation in stage-specific setup is part of
an absolute resource-name address. They supply no additional line consumer.
Within preserved navigation `0x006F1140..0x0070639F`, the sole scalar load
with displacement `+0x2C` is stack halfword `0x00700108`; there is also no
non-stack quadword load at `+0x20` or doubleword load at `+0x28` covering the
cached word. No semantic reader was identified through these direct calls and
aliases. Arbitrary pointer arithmetic, partial/unaligned loads, and indirect
consumers remain outside this bounded negative result.

### Selected-index writers and neighboring aliases

An audit of all 486,832 aligned words in BTL file interval `0x40..0x1DB6FF`
checked byte, halfword, word, scalar-float, doubleword, and quadword stores
whose encoded displacement overlaps the active-index bytes
`+0xA8E/+0xA8F/+0xA9A/+0xA9B`, together with `addi/addiu/daddiu` instructions
that form those exact byte addresses. No exact-address formation was found.
Twelve store instructions overlap the offsets; following their base objects
separates the two stage stores from ten stores to other layouts:

| Live store instruction(s) | Proven owner and write |
| --- | --- |
| `0x006C2904`, `0x006C2918` | Control initializer: byte zero at `ccBgControl+section+0xA8E` and `+0xA9A`, in the two-section loop. |
| `0x007772B4`, `0x007772B8` | Interaction-manager initialization: two `vf0` quadwords at manager `+0xA80/+0xA90`. |
| `0x0077AA2C` | Interaction-manager update: copies its `+0xB00` vec4 to manager `+0xA80`; the base comes from the manager global `iGpffffce54`. |
| `0x0077F3B0`, `0x0077F3B4` | Auxiliary-object initialization: `vf0` quadwords at auxiliary `+0xA80/+0xA90`. |
| `0x00781734/0x00781738`, `0x007819AC/0x007819B0` | Auxiliary-object geometry paths: a quadword at `+0xA80`, followed by scalar w at `+0xA8C`. |
| `0x0078E0C0` | Primary snapshot reset: clears the word at `primary+0xA8C+index*0x40` while clearing the four 0x40-byte [snapshot banks](../combat/collision.md#query-result-and-snapshot-records). |

The adjacent stage aliases have narrower destinations. The first-family
builder forms the count pointers `ccBgControl+0xA8C/+0xA8D` at live
`0x006C34E0/0x006C34F8`, then writes **one byte** with value 1 through that
pointer at live `0x006C3508`. Its `+0xA90/+0xA94` aliases hold separately
allocated four-byte head tables. The second-family builder similarly writes
count 1 at `+0xA98+index` and allocates a one-entry head table at
`+0xA9C+index*4`. Each head can lead to multiple line records; the count is
not the number of records. Neither builder writes the active-index bytes.

The vector alias `ccBgControl+0xA80` reaches live `0x006C4370`, raw
`0x010470`. Its complete reserve body writes only header capacity `+0x00` and
data pointer `+0x08`, reads size `+0x04`, and copies heap entries; it does not
overwrite the count or active-index bytes beyond that 0x0C header. The
destructor's `+0xA90/+0xA9C` aliases free the heap head tables. The two
[getters](#cached-line-attribute-consumers) at live `0x00708D60/0x00708DA0`
load the active index, dereference its head-table entry, and return without
stores. Initialization and these builders therefore support active head 0 with
count 1 for each populated section; they do not establish an authored choice
among multiple heads.

The audit covers the recovered adjacent aliases and ordinary wider stores, not
unaligned partial stores or arbitrary pointer arithmetic that reaches these
bytes without an identified base. The complete active-index writer set remains
unresolved outside the traced paths.

### Boundary clamp and floor-profile queries

The boundary clamp (preserved `FUN_006c22d0`, live `0x006C2310`, wrapper live
`0x00708A80`), the piecewise boundary resolver, and the floor-profile query
(preserved `FUN_006c2570`, live `0x006C25B0`, wrapper live `0x00708CE0`) over
these records belong to [Collision](../combat/collision.md#stage-query-functions). In
summary, the clamp limits component 0 of a `vec4` to a selected config's two
endpoints, and the floor-profile query interpolates component 2 over the
selected section's lines, returning `-32768.0` when no line or background
control applies.

## Stage-specific configuration and numeric branches

### Combo/skill anchor table

A separate 24-record table supplies stage-specific position anchors to
`ccSkillComboBase`. Its actual Ghidra location is `0x008C1D80`, file
`0x20DEC0`, live `0x008C1DC0`. Each `0x10`-byte record is:

| Offset | Type | Meaning |
| ---: | --- | --- |
| `+0x00` | live pointer | side-0 `vec4` array |
| `+0x04` | live pointer | side-1 `vec4` array |
| `+0x08` | `u8` | side-0 element count |
| `+0x09` | `u8` | side-1 element count |
| `+0x0A..+0x0F` | zero padding | no observed payload |

The pointed arrays occupy file `0x1DBAD0..0x1DC98F` (live
`0x0088F9D0..0x0089088F`). Every stored vector has component 3 equal to
`1.0`. The order below is the raw order and therefore also preserves the
tie-break order. `c1` and `c2` mean vector components 1 and 2; the engine's
axis names are not assumed.

| Slot / logical / archive | Side 0 anchors | Side 1 anchors |
| --- | --- | --- |
| 0 / 1 / S01 | `c0=[600,500,400,300,200,100,0,-100,-200,-300,-400,-500,-600] @ (c1,c2)=(0,0)` | `c0=[400,300,200,100,0,-100,-200,-300,-400] @ (c1,c2)=(1000,699)` |
| 1 / 2 / S02 | `c0=[-100,0,100] @ (c1,c2)=(0,-50)` | `c0=[-100,0] @ (c1,c2)=(1000,-50)` |
| 2 / 23 / S03 | `c0=[-500,-400,-200,0,200,400,500] @ (c1,c2)=(0,0)` | `c0=[0] @ (c1,c2)=(1050,-50)` |
| 3 / 24 / S04 | `c0=[0] @ (c1,c2)=(0,-50)` | `c0=[0] @ (c1,c2)=(750,0)` |
| 4 / 5 / S05 | `c0=[-400,-300,-200,-100,0,100] @ (c1,c2)=(0,5)` | `c0=[-50] @ (c1,c2)=(1000,16)` |
| 5 / 6 / S06 | `c0=[400,300,200,100,0,-100,-200,-300] @ (c1,c2)=(0,0)` | `c0=[300,200,100,0] @ (c1,c2)=(1000,127)` |
| 6 / 7 / S07 | `c0=[-400,-300,-200,-100,0] @ (c1,c2)=(0,75)` | `c0=[450] @ (c1,c2)=(1100,75)` |
| 7 / 8 / S08 | `c0=[-480] @ (c1,c2)=(0,53)` | `c0=[0,100,200,300,400] @ (c1,c2)=(800,1030)` |
| 8 / 9 / S09 | `c0=[300] @ (c1,c2)=(1000,600)` | `c0=[300] @ (c1,c2)=(1000,600)` |
| 9 / 10 / S10 | `c0=[0] @ (c1,c2)=(987,360)` | `c0=[0] @ (c1,c2)=(987,360)` |
| 10 / 11 / S11 | `c0=[200,100,0,-100,-200,-300,-400,-500,-600] @ (c1,c2)=(0,0)` | `c0=[-300] @ (c1,c2)=(800,0)` |
| 11 / 12 / S12 | `c0=[-500,-400,-300,-200,-100,0,100,200,300,400,500,600] @ (c1,c2)=(0,0)` | `c0=[-500,-400,-300,-200,-100,0,100,200,300,400,500] @ (c1,c2)=(1000,0)` |
| 12 / 13 / S13 | `c0=[0,100,200,300,400,500,600] @ (c1,c2)=(0,0)` | `c0=[-500,-400,-300,-200,-100,0,100,200,300,400,500] @ (c1,c2)=(1250,450)` |
| 13 / 14 / S14 | `c0=[-750,0,750] @ (c1,c2)=(0,0)` | `c0=[-750,0,750] @ (c1,c2)=(0,0)` |
| 14 / 15 / S15 | `c0=[-50,50,150] @ (c1,c2)=(0,60)` | `c0=[0] @ (c1,c2)=(1250,60)` |
| 15 / 16 / S16 | `c0=[0] @ (c1,c2)=(800,0)` | `c0=[0] @ (c1,c2)=(800,0)` |
| 16 / 17 / S17 | `c0=[-500,-400,-300,-200,-100,0,100,200,300,400,500] @ (c1,c2)=(0,0)` | `c0=[-500,-400,-300,-200,-100,0,100,200,300,400,500] @ (c1,c2)=(1000,0)` |
| 17 / 18 / S18 | `c0=[-500,-400,-300,-200,-100,0,100,200,300,400,500] @ (c1,c2)=(0,0)` | `c0=[-300,-200,-100,0,100,200,300,400,500] @ (c1,c2)=(1000,0)` |
| 18 / 19 / S19 | `c0=[100,0,-100,-200] @ (c1,c2)=(0,0)` | `c0=[0] @ (c1,c2)=(1000,0)` |
| 19 / 20 / S20 | `c0=[400,300,200,100,0,-100,-200,-300,-400,-500,-600] @ (c1,c2)=(0,0)` | `c0=[400,300,200,100,0,-100,-200,-300,-400,-500,-600] @ (c1,c2)=(0,0)` |
| 20 / 21 / S21 | `c0=[300,200,100,0,-100,-200,-300] @ (c1,c2)=(0,0)` | `c0=[300,200,100,0,-100,-200,-300] @ (c1,c2)=(1000,0)` |
| 21 / 22 / S22 | `c0=[100,0,-100] @ (c1,c2)=(0,0)` | `c0=[200,100,0,-100,-200] @ (c1,c2)=(0,0)` |
| 22 / 3 / S23 | `c0=[0] @ (c1,c2)=(1050,375)` | `c0=[0] @ (c1,c2)=(1050,375)` |
| 23 / 4 / S24 | `c0=[-200,-100,0,100] @ (c1,c2)=(0,0)` | `c0=[-200,-100,0,100] @ (c1,c2)=(0,0)` |

The table consumer begins at preserved `FUN_006c12c0`, file `0x00D400`,
live `0x006C1300`. Given output vector, query vector, and side byte, it selects
the active slot from manager `+0x98`, scans that side's array, copies the
strictly nearest anchor to the output, and returns a side byte. Equal distance
keeps the earlier raw-table element. If no live field/background exists, it
leaves a zero vector and returns side 0.

The raw call at Ghidra `0x00798E58`, file `0x0E4F98`, live `0x00798E98`, is
inside preserved `FUN_00798df0` (file `0x0E4F30`, live `0x00798E30`). That
method feeds object `+0x330` as the query, reads the associated fighter's
section with signed `lh` at `+0x9F6` (or uses zero), masks the helper argument
to one byte, writes the returned side to object
`+0x39C` and `+0x54C`, and later copies the chosen anchor back to `+0x330`.
Its wrapper at preserved `FUN_0079c100`, file `0x0E8240`, live `0x0079C140`,
is resident vtable `0x005FB240` slot `+0xBC`. The vtable's RTTI descriptor
points to live string `ccSkillComboBase` at `0x008BB6B0` (actual Ghidra
`0x008BB670`, file `0x2077B0`). This establishes a combo/skill placement use;
it is not evidence for generic fighter spawn points.

After choosing an anchor, slots 13, 19, 21, and 23 force returned side 0;
slots 8, 9, 15, and 22 force side 1. Other slots retain the requested side.
The forced values do not change which side array was searched.

### Background classifier and slot-specific objects

Preserved `FUN_006c2400`, file `0x00E540`, live `0x006C2440`, classifies a
small set of load slots from `ccBgControl+0x0C`. The usable wrapper is preserved
`FUN_00708c30`, file `0x054D70`, live `0x00708C70`. If no active background control exists, the wrapper returns
code 1 without calling the classifier.

The classifier returns:

- slot 6 (`s07`) -> `0`;
- slot 12 (`s13`) -> `2`;
- slot 13 (`s14`) with no position -> `4`;
- slot 13 with `abs(position.component0 - -700.0) < 200.0` -> `3`;
- slot 13 with `abs(position.component0 - 700.0) < 200.0` -> `6`; this second
  test wins if both were ever true;
- every other case -> `0`.

The two full anchor vectors are at file/live `0x1DCB80 / 0x00890A80` and
`0x1DCB90 / 0x00890A90`: `(-700, 950, 400, 0)` and
`(700, 950, 400, 0)`; their preserved Ghidra locations are `0x00890A40` and
`0x00890A50`.

The consumer chain resolves the high-level role: these values are
stage/position-dependent surface or background **effect-variant columns**, not
geometry-transition codes. Resident `FUN_00336630` calls `FUN_00336660`, then
`FUN_003136A0` (runtime/file `0x003136A0 / 0x002137A0`). The latter copies the
two-by-seven `u32` table at runtime/file `0x005A4B50 / 0x004A4C50`; its rows
are effect IDs `0x7B..0x81` and `0x82..0x88`. It finally calls
`FUN_0030F610(effect_object+0xA0, table[row*7 + classifier_code], 0)`. The row
is selected through `FUN_001771A0(FUN_001801E0() & 1)`. Static data does not
name the material represented by either row.

Audited BTL consumers at preserved Ghidra/file/live
`0x006CA524/0x016664/0x006CA564`,
`0x006CA5CC/0x01670C/0x006CA60C`,
`0x006CA664/0x0167A4/0x006CA6A4`, and
`0x006CA704/0x016844/0x006CA744` pass the code from a landing-tree proximity
helper to `FUN_00336630` with effect count 10. Other consumers at
`0x007A2854`, `0x007B6D9C`, and `0x007BB25C` derive `code + 0x22` for spawned
object field `+0x228`; `0x007C0188` passes it to `FUN_00336660`. Resident
direct callsites at `0x002B26AC`, `0x002D0860`, `0x002EC6B4`, `0x0030CED0`,
`0x0032F8B0`, `0x00338D7C`, and `0x0033BE38` have the same two uses.

The seven-column table supports codes 0 through 6. The BTL classifier produces
`0/2/3/4/6`; code 1 is the no-background wrapper fallback; no audited path
produces code 5. Exact visual/material names remain unresolved.

Preserved `FUN_006c2de0`, file `0x00EF20`, live `0x006C2E20`, is another
confirmed stage-specific setup. Only slot 14 (`s15`) resolves
`ANM_s15efe04` through `FUN_001A8F00(handle, name, 1)` and stores the returned
object at control `+0xF8`; all other slots clear that field. The string is at
file `0x1DCBA0`, live `0x00890AA0`.

Other numeric exceptions are confirmed but their visual/gameplay names are
not:

| Slot/archive | Function | Confirmed exception |
| --- | --- | --- |
| 1/`s02`, 7/`s08`, 18/`s19`, 20/`s21` | `FUN_006f1f20` | Force the line-query extent to `1100.0` instead of `argument * 10`. |
| 5/`s06`, 22/`s23` | `FUN_006f4040` | When fighter `+0x18E == 5`, call resident `FUN_00218810` before common handling. |
| 7/`s08` | `FUN_006f3770` | Source line 1 or 2 may accept direct state 3 when a target or route is absent. |
| 7/`s08` | `FUN_006f7e70` | Lines 1/2 receive special handling around component-2 threshold `800`. |
| 12/`s13` | `FUN_006f4f10` | Special handling uses fighter section `+0x9F6` and action IDs `0x30`, `0x2C`, `0x27`, and `0x25`. |
| 18/`s19` | `FUN_006f3770` | Source line 5 may accept direct state 3. |
| 20/`s21` | `FUN_006f3770` | Source line 1 may accept direct state 3. |

All numbers in this table are load slots. In particular, slot 22 is logical
stage ID 3 and archive `s23`.

### Proximity-driven background transitions

The three compiled `ccBgTrans*` classes are reversible model/animation
transitions driven by fighter proximity. They do not switch the loaded stage
archive or move a fighter between arenas.

`ccBgTransObject` parser preserved `0x006C74D0`, file `0x013610`, live
`0x006C7510`, constructs the visual/animation from configuration tokens 0/1,
uses token 2 as uniform scale, copies the token-3 node/resource position to
object `+0x40`, and stores token 4 as proximity radius `+0x50`. Update preserved
`0x006C78C0`, file `0x013A00`, live `0x006C7900`, measures three-dimensional
distance from that point to both fighters. If either is inside the radius it
eases blend `+0x54` toward 0; otherwise toward 1, at rate `0.2`. The model frame
is `blend * FUN_003AE5B0(700.0, model+0x70)`. Override `+0x58 >= 0` can write a
frame directly once, then resets to `-1`. Render preserved `0x006C7AB0`, file
`0x013BF0`, live `0x006C7AF0`, chooses one of endpoint controllers `+0x28/+0x2C`
around frame 1. No fighter state is written.

`ccBgTransAnm` retains the same position/radius/blend behavior. Its parser is
preserved `0x006C7C90`, file `0x013DD0`, live `0x006C7CD0`; token 5 supplies a
multiplier at `+0x5C`, while token 6 selects an animation index (`-1` chooses
through `FUN_00180210`). Update preserved `0x006C80A0`, file `0x0141E0`, live
`0x006C80E0`, also writes model `+0x94` from the original value times that
multiplier and the update context before applying the same proximity easing.

`ccBgTransObject2` derives from `ccBgTransObject`. Parser preserved
`0x006CE210`, file `0x01A350`, live `0x006CE250`, calls the base parser, maps
token 5 to target value `+0x60`, and starts blend `+0x54` at zero. Update
preserved `0x006CE270`, file `0x01A3B0`, live `0x006CE2B0`, eases toward
`+0x60` while either fighter is inside the radius and toward zero outside,
again at rate `0.2`; it writes that value directly as the model frame.

The complete authored instances are:

| Archive, record | Class | Configuration |
| --- | --- | --- |
| `S01 #44` | `ccBgTransObject` | `OBJ_obj_040_,DMY_s01has01,1,DMY_s01has00,200` |
| `S02 #79` | `ccBgTransObject2` | `OBJ_efe_040_,DMY_has2_000,1,DMY_has2_000,700,0.8` |
| `S02 #80` | `ccBgTransObject2` | `OBJ_efe_050_,DMY_has2_010,1,DMY_has2_010,700,1` |
| `S03 #51` | `ccBgTransObject` | `OBJ_obj_300_,DMY_has00,1,DMY_has00,0` |
| `S04 #56` | `ccBgTransAnm` | `ANM_s04efe10,DMY_s04has00a,1,DMY_s04has00b,0,0.9,1` |
| `S10 #54` | `ccBgTransObject` | `OBJ_obj_070_,DMY_hnd_00_,1,DMY_has00_hit,350` |
| `S10 #55` | `ccBgTransObject` | `OBJ_obj_080_,DMY_hnd_01_,1,DMY_has10_hit,350` |
| `S13 #48` | `ccBgTransObject` | `OBJ_obj_300_,DMY_gmk_a0,1,DMY_s13has00_hit,100` |
| `S17 #28` | `ccBgTransObject` | `OBJ_obj_010_,DMY_has00,1,DMY_has00,0` |
| `S20 #66` | `ccBgTransObject` | `OBJ_obj_100_,DMY_has00,1,DMY_has00,0` |
| `S20 #67` | `ccBgTransObject` | `OBJ_obj_110_,DMY_has01,1,DMY_has01,0` |
| `S21 #53` | `ccBgTransAnm` | `ANM_s21gim100,DMY_dmy_020,1,DMY_s21has00,250,1,3` |
| `S21 #54` | `ccBgTransAnm` | `ANM_s21gim00_a0,DMY_dmy_030,1,DMY_s21has01,250,1,9` |
| `S23 #30` | `ccBgTransObject` | `OBJ_obj_110_,DMY_gmk_a0,1,DMY_s23_has_hit,100` |

## Geometry-driven navigation graph

The first-family accessor at preserved `0x00708D20`, file `0x054E60`, live
`0x00708D60`, returns the active first-family line list for a section.
Preserved `FUN_006f1f20`,
`FUN_006f2160`, and `FUN_006f24a0` scan those linked segments with
`FUN_006f1180` and select the nearest intersecting line. When fighter/object
flags at `+0xBB4` contain `0x800`, a candidate additionally requires line
record `+0x24 == 1`.

Preserved `FUN_006f3770`, file `0x03F8B0`, live `0x006F37B0`, maps current and
target line pointers to indices in a maximum-32-pointer BSS array, then finds
each line's side/section by walking the active lists. A side mismatch sets
per-agent state 4 and cancels the route. The runtime tables are:

| Encoded live base | Shape | Role |
| ---: | --- | --- |
| `0x008D6500` | up to 32 line pointers | line-to-index map |
| `0x008D6200` | 64 records of `0x0C` bytes | navigation adjacency records |
| `0x008D69D0` | 64 visited bytes | recursive route search state |

These BSS addresses are encoded absolute operands; see the
[address conventions](../../game/files/file_identities.md#address-conventions).

Each adjacency record contains signed source line index at `+0x00`, signed
destination line index at `+0x01`, a `float` point fraction at `+0x04`, and a
route/action type byte at `+0x08`. Preserved `FUN_006f3510` and
`FUN_006f3550` recursively search the records. A chosen point is reconstructed
as `endpointA + (endpointB - endpointA) * fraction`.

Preserved entry `0x006F6360`, file `0x0424A0`, live `0x006F63A0`, consumes the
chosen route/type and writes movement yaw near `+/- pi/2`, direction/state
flags `1`, `2`, and `0x100000`, while consulting fighter section `+0x9F6`.
The route chooser's 15 direct BTL JAL callsites all fall within preserved
`0x006F493C..0x0070375C`, the AI decision/dispatch region: AI dispatcher state
4 calls this route executor at preserved `0x006FBA04`, and its route helpers
call planner live `0x006F37B0`. No direct planner JAL exists in the retail
resident ELF or ETC overlay. **Confirmed:** the planner produces AI traversal
input on the ordinary battle path, and the AI tick runs only for fighters with
a nonzero controller nibble
([Battle AI](../session/battle_ai.md#controller-ownership-and-lifecycle)); this does not
exclude indirect callers. The tick, its command output, and the route states
belong to [Battle AI](../session/battle_ai.md#main-tick-and-output-boundary) and
[path states](../session/battle_ai.md#alternate-target-position-sources-and-path-states).

## Animated and breakable-background evidence

Preserved `FUN_006c4770`, file `0x0108B0`, live `0x006C47B0`, advances a
background object's model/animation list using count `+0x34`, active index
`+0x30`, threshold `+0x38`, and model array/count `+0x28/+0x2C`. It caps the
count at 99. At the configured threshold it clamps to the final model, enables
the transform/effect blocks at `+0x160/+0x170`, and calls resident
`FUN_001D7E20` with event/effect ID `0x22`. A threshold of `-1` loops the model
sequence; before a finite threshold it clamps to the penultimate model and
restarts its animation.

Direct vtable linkage identifies the owner as `ccBgBreakObjectBattle`.
Its resident vtable `0x005DDAE0` slot `+0x08` is live `0x006C4AD0`, the actual
body beginning at preserved `FUN_006c4a90`, file `0x010BD0`. This method
performs contact tests and animation handling, calls `FUN_006c4770` on an
accepted contact, and stores playback state at `+0x180`. When count `+0x34`
reaches threshold `+0x38`, it also calls battle-statistic adder live
`0x00715F90` (preserved `FUN_00715f50`, file `0x062090`) with
`(bit(contact+0x60, 0) + 1, 0x0C, 1)`, adding one to metric 12 for the
contacting fighter's side; the credit rules belong to
[Match outcomes](../session/battle_statistics.md#ninja-tools-and-stage-objects).
Vtable slot `+0x14` is live `0x006C5190`, preserved `FUN_006c5150`, which
parses the configuration fields.

The confirmed factory/constructor begins at preserved `FUN_006c5570`, file
`0x0116B0`, live `0x006C55B0`. It allocates `0x190` bytes, installs base
`ccBgObject` vtable `0x005DD650` and then class vtable `0x005DDAE0`, constructs
collision subobjects at `+0x40` and `+0xD0`, zeros the list/counter fields, and
finishes through virtual slot `+0x14`.

Those two collision subobjects are directly identified as `ccBgAttackHit`.
Its compact resident vtable is `0x005DDAC8`; word zero is descriptor
`0x008C2308`, slot `+0x08` is only a destructor/reset thunk at live
`0x006C5770` (preserved `0x006C5730`, file `0x011870`), and slots
`+0x0C/+0x10/+0x14` are null. Each receiver is initialized through resident
`FUN_001DD8D0` and `FUN_001BEA30`, with fields `+0x24 = 0`, `+0x48 =
0x43020000`, `+0x4C = 0`, `+0x80 = 0x224`, and `+0x84 = 2`.

The full break-object update treats them as contact receivers. One enumerates
the two global combatant slots through `FUN_003769C0`; the other is queried
through `FUN_001DDD80(receiver, 1)` and resolved through `FUN_001DD1A0`,
`FUN_001DCA40`, and `FUN_00222A40`. It rejects candidates whose `+0x10` has
mask `0x00F00000` or bit 2, or whose `+0x14` has bit `0x02000000`. An accepted
candidate advances only the background break state and battle statistic. This
class method contains no fighter-health/state write or class-specific damage
call, and `ccBgAttackHit` has no damage/update vtable slot. It is therefore
documented as a reusable contact receiver rather than an attack implementation.
The generic breakable users do not hit a fighter through this path; the Hades
snake class below consumes the same receiver differently.

A parallel state machine, preserved `FUN_006c57c0`, file `0x011900`, live
`0x006C5800`, uses count `+0x48`, active index `+0x44`, threshold `+0x4C`,
model array/count `+0x3C/+0x40`, and playback `+0x190`. It dispatches `0x22`
except on slots 0 (`s01`) and 19 (`s20`), where it dispatches `0x26`.
The high-level meaning of these numeric events is unresolved.

Preserved `FUN_006c5b20`, Ghidra/file/live
`0x006C5B20 / 0x011C60 / 0x006C5B60`, is resident vtable `0x005DDAA0` slot
`+0x08` for `ccBgBreakObjectBattleAnm`. It implements a timed
animation/fade/reset cycle using state `+0x28`, count `+0x2C`, timer `+0x30`,
opacity `+0x38`, list `+0x3C`, active index `+0x44`, flag `+0x48`, and config
`+0x4C`. Its accepted-contact path repeats the same receiver-mask filtering,
calls actual trigger `FUN_006c57c0`, and adds metric 12 through statistic
adder live `0x00715F90` when `+0x48` is nonzero. In state 0 with a nonzero
remaining count, it waits more
than `0x78` ticks, resets model/index/playback `+0x190` and opacity, decrements
a finite count, and enters state 1. State 1 raises opacity by `0.05` per tick
to `1.0`, then clears state/opacity/flag and fixes model opacity at one.
Vtable slot `+0x0C` is live `0x006C6200`, preserved `FUN_006c61c0`, and slot
`+0x14` is live `0x006C6350`, preserved `FUN_006c6310`. Its factory begins at
preserved `FUN_006c6790`, file `0x0128D0`, live `0x006C67D0`, allocates
`0x1A0` bytes, and installs vtable `0x005DDAA0`.

`ccBgBreakObjectRebornBattle` is a distinct class at resident vtable
`0x005DD870`. Its slot `+0x08` is live `0x006CDD80`, actual preserved body
`0x006CDD40`, file `0x019E80`; this separate method also contains an explicit
`0.05` opacity rise and `>0x78` reset/reborn timer. It first runs the base
break update. Only at the final break stage does it wait more than 120 ticks, reset
model zero/index/playback `+0x180`, decrement the finite repeat count at
`+0x194`, and fade back in. Completion clears the state and restores break
count `+0x34` to zero. Parser slot `+0x14`, actual preserved `0x006CE020`, maps
descriptor entry 9 to the repeat count. Its factory begins at
preserved `0x006CE070`, file `0x01A1B0`, live `0x006CE0B0` and allocates
`0x1A0` bytes. This proves a timed finite-or-repeating rebirth mechanic, but
the archive census further limits its construction to `S01` and `S08`. All
three S01 and all five S08 authored strings end in repeat value `-1`, the
nondecrementing repeat sentinel, so every retail instance is configured to
rebirth indefinitely.

Other class-specific state behavior is statically distinct:

- `ccBgBreakDollBattle` repeats the contact filtering, resets its animation and
  collider on acceptance, spawns its configured effect, and sets byte `+0x190`
  to `FUN_00180210(0x3C) + 0x3C`; while nonzero the update only decrements this
  randomized-helper-plus-60 cooldown.
- `ccBgBreakObjectMoveBattle` advances a cubic-Bezier model mover at actual
  preserved `0x006CF160`, then runs the base break update. On full break it sets
  `+0x230 = FUN_00180210(0x1E) + 0x1E`; expiry resets active model, playback,
  and break count. This is a randomized-helper-plus-30 reset delay.
- `ccBgBreakObjectFallBattle` runs the base update, raycasts predicted downward
  motion with mask `0x20000000`, subtracts `3.0` from vertical velocity while
  unsupported, and propagates the resulting transform to every model and
  effect. At the final break stage it advances/enables all models instead.
- `ccBgCrashBreakBattle` update preserved/file/live
  `0x006CA860 / 0x0169A0 / 0x006CA8A0` scans both fighters only while break
  count differs from threshold, and requires fighter section `+0x9F6` to equal
  object `+0x184`. Flag `+0x190` bit 1 accepts major state 5 with substate
  `0x42/0x43/0x48`, a nonzero animation predicate `0x002118A0`, and absolute
  component-0 distance from object `+0x160` below `+0x194`. Bit 2 instead
  accepts substates `0x45/0x46/0x49` and component-2 distance from `+0x168`
  greater than half `+0x198`. Each accepted path calls the base break trigger
  once and leaves the fighter scan. Reaching the threshold calls `0x001BAEE0`
  on every model and adds one to battle metric `0x13` (19) through statistic
  adder live `0x00715F90`; side argument 1 is selected when the responding
  fighter's side bit is set, otherwise 2, crediting the opposite side
  ([Match outcomes](../session/battle_statistics.md#ninja-tools-and-stage-objects)). The update then sets
  the active model step from the scene factor and advances it. This method
  contains no direct fighter-damage write.

Two S13-only moving props have separate mechanics. `ccHandRowShip` record 33
uses factory preserved `0x006CFCF0`, file `0x01BE30`, live `0x006CFD30`, and
update preserved `0x006CF990`, file `0x01BAD0`, live `0x006CF9D0`. Each tick
it tests both fighters against an axis-aligned region around ship center
`+0x50`: component deltas below `160`, `30`, and `150`. Entry sets an
object-owned per-fighter contact flag, clamps bounce velocity to at most
`-2.5`, and resets phase; one fighter state clears contact and sets velocity
`-5`. The update applies damped sinusoidal rocking, vertical bob/bounce, and
copies transforms to its two models. It reads fighter state but neither writes
a fighter nor calls combat-hit code, supporting a reactive moving-platform
interpretation.

`ccCraneTruck` record 34 uses factory preserved `0x006D04B0`, file `0x01C5F0`,
live `0x006D04F0`, and update preserved `0x006D0040`, file `0x01C180`, live
`0x006D0080`. Its parser ignores the authored string `-1` and resolves the
hardcoded `ANM_s13cra00_a0/a1` resources into `+0x30/+0x34`. It also creates a
separate, scene-owned `ccBgBreakObjectBattle` through static attach record
`{owner=4, factory=50, selector=2}` and retains its pointer at `+0x38`; the
crane destructor deliberately does not delete that object. When the linked
break object's count reaches its threshold, the crane switches animation;
completion restores its initial animation and resets the linked object's
model/playback/break state. Frames 410/350/250/206/60/0 emit effect `0x1017`.
Its destructibility comes from that ordinary break-receiver path; this update
has no explicit fighter hit.

`ccElectricWire`, instantiated by S19, S21, and S24, owns reactive wire
simulation, visual geometry, and registered environment-query geometry. Its
factory is preserved `0x006C9A50`, file `0x015B90`, live `0x006C9A90`,
allocating `0x100` bytes.
Parser preserved `0x006C8490`, file `0x0145D0`, live `0x006C84D0`, resolves
three configured resources/models, establishes endpoints at `+0xD0/+0xE0`,
fixes interior-node count `+0x54` to 15, allocates node arrays `+0x60/+0x64/+0x68`
and sixteen collision segments at `+0xF0`, and initializes per-fighter indices
`+0x94/+0x98` to `-1`.

**Confirmed construction and refresh:** segment builder preserved/file/live
`0x006C88D0 / 0x014A10 / 0x006C8910` allocates `(+0x54 + 1)` elements
of `0x1F0` bytes. Its callback at live `0x006C8C50` installs
`ccWireHitModel` vtable `0x005DD9D0` and invokes resident initializer
`0x003A8490`. Each endpoint pair is passed to resident `0x003A8520`, which
stores the endpoints at element `+0x1A0/+0x1B0`, calls `0x003A88A0`, and
registers the element's environment object through `0x001BEFA0(object,0)`.
That mode selects the already-world-space path. The object at element
`+0x180` points back to the element's packed bounds/triangle hierarchy;
element `+0x1C0` separately owns the four-vertex visual model. Resident
`0x003A8BE0` builds one group containing two triangles and updates aggregate
and group bounds. Both generic segment queries and the fighter query walk
the registered environment chain; their selection rules belong to
[Collision](../combat/collision.md#resident-segmentenvironment-broad-and-narrow-phases)
and [Stage surface attributes](stage_surface_attributes.md#query-eligibility-and-contact-classes).

The wire's attribute word at wire `+0x28`, its copy to each element, and the
attributes of the initial and rebuilt triangles belong to
[Generated wire polygon attributes](stage_surface_attributes.md#generated-wire-polygon-attributes).
Configuration sets dirty byte `+0xF4 = 1` and invokes the installed update
slot before appending the wire to the scene's owning list. The update
returns without refreshing when resident `0x003AE660` is nonzero; the shared
predicate is bounded under [Update eligibility and local timing](#update-eligibility-and-local-timing).
Otherwise both zero- and nonzero-amplitude branches call dirty-refresh helper
preserved/file/live `0x006C9550 / 0x015690 / 0x006C9590`. If dirty, it walks
all sixteen endpoint pairs and calls resident `0x003A85A0`, which replaces
the endpoints and rebuilds through `0x003A8BE0`; it then clears the dirty
byte. The nonzero-oscillation branch sets that byte again after the refresh.

Update preserved `0x006C8EC0`, file `0x015000`, live `0x006C8F00`, invokes
fighter-reaction helper preserved `0x006C8CE0`, live `0x006C8D20`, which scans
both fighters. A candidate must be within 20 units of the endpoint's component
1, within the endpoints' component-0 range, within 150 units of endpoint
component 2, and have retained polygon
word `fighter+0xBB8 == wire+0x28`; this is full-word equality, not a masked
contact-code comparison. Fighter state/action `+0x18E` selects a reaction case.
Helper preserved `0x006C9650`, live `0x006C9690`, retains the last node index
whose component 0 is strictly below the fighter's component 0 and writes only
wire excitation, sag, and per-fighter tracking fields. The sole fighter-side
call in the class range is
`FUN_002118A0(fighter+0x1B8, 0)`, a read-only animation/frame-state predicate.
A raw JAL audit over preserved `0x006C8490..0x006C9AFF` finds no
`FUN_002335F0` and no other fighter hit/damage call. The compiled class reacts
physically/visually to fighter movement but does not directly hit or modify a
fighter. That absence applies to the class's explicit hit path: it does not
exclude consequences when generic fighter movement selects the generated
polygons. The helper elements' destructor-only vtable does not make them
visual-only; their resident helpers also create, rebuild, register, and
release the environment-query objects described above. Neither this trace
nor the attribute word alone establishes fighter damage or a measured contact
outcome.

The sole S10 `ccBgSuspensionBridge` is likewise a deformable surface, not a
proved hazard. Factory preserved `0x006CD0E0`, file `0x019220`, live
`0x006CD120`, allocates `0xA0` bytes. Parser preserved `0x006CBA10`, file
`0x017B50`, live `0x006CBA50`, maps its exact configuration to 17 segments,
fighter/stage key 0, anchor `DMY_hasi`, texture `TEX_s10obj22`, endpoint
resources `DMY_hasira_a/b`, and floats 120/180. It allocates node, rope, and
helper arrays from those values.

The geometry/physics pass begins at preserved `0x006CCB60`, file `0x018CA0`,
live `0x006CCBA0`. For each fighter it requires fighter section/key `+0x9F6`
to equal bridge `+0x40`, finds the supporting segment from fighter position,
and, when fighter flag `+0x63` bit 7 is set, applies a `-10` load to a bridge
node and spreads it outward with `0.8` attenuation. A support change near the
center starts sag/oscillation with fields `+0x90 = 0.02` and `+0x94 = -25`,
damped by `0.999`. The complete class path writes only bridge nodes and render
state: it contains no `ccBgAttackHit`, fighter write, or combat-hit call.

`ccBgEscapeBirdBattle` instances in S01, S02, S11, and S19 are proximity
escape effects. Factory preserved `0x006CD540`, file `0x019680`, live
`0x006CD580`, allocates `0x50` bytes. Parser preserved `0x006CD190`, file
`0x0192D0`, live `0x006CD1D0`, maps configured origin/destination transforms,
trigger radius, arrival/speed scalar, resource archive, and idle/escape models
into a resident child controller. The outer update only copies the two fighter
positions. Child state 0 waits until either is within the trigger radius, state
1 selects the escape model and moves toward the destination, and state 2 keeps
moving while fading by `0.05` per tick to inert state 3. No attack receiver or
fighter-impact call is present.

The sole S16 `ccTumbleGrass` record is a trajectory- and wind-reactive clump
system. Factory preserved `0x006CDC70`, file `0x019DB0`, live `0x006CDCB0`,
allocates `0x34` bytes; parser preserved `0x006CD650`, file `0x019790`, live
`0x006CD690`, maps the retail `...,5,80` tokens to five optional visual
variants and 80 `0x30`-byte `ccGrassInfluence` clumps. Update preserved
`0x006CD9A0`, file `0x019AE0`, live `0x006CD9E0`,
tests each fighter trajectory within radius 150 and writes only clump reaction
angles. When neither fighter affects a clump it applies ambient wind in the
static `(1,0,0,1)` direction for randomized 10--19-tick bursts, otherwise
damps the motion, and clamps angular fields to `+/- pi/3`. It has no fighter
write, attack receiver, transition, or damage call.

The `ccBgFootMarkBattle` records in S12, S16, and S18 are also tied to their
authored resources. Parser preserved `0x006D39C0`, file `0x01FB00`, live
`0x006D3A00`, resolves the configured archive and model name and passes the
integer token to resident `FUN_003A6A70`. The token is a surface-selection
bitmask at object `+0x28`, not a pool-size count. Construction always creates
30 `0x30`-byte mark nodes per foot for each of two fighters: four pools and
120 nodes, each owning a `0xB0` model. Every node starts inactive with opacity
limit `0.5` and fade decrement `0.01`.

The class update, preserved/file/live `0x006D39E0 / 0x01FB20 / 0x006D3A20`,
requires a non-null battle global at resident `0x00607600` and a zero result
from live BTL `0x007064B0`. Until both fighter-binding flags `+0x3F0/+0x3F4`
are set, helper live `0x006D3B00` retries binding each available fighter's
`+0xE6C` model collection to `OBJ_2cmn00t0 l foot` and
`OBJ_2cmn00t0 r foot`. These are borrowed foot-model pointers.

Resident update `0x003A6550` queries each bound foot from component-2 offsets
`+5` to `-100` through `0x001BF100`, mask `0x20000001`. A result other than
`-1` and at most 20 establishes contact only when surface predicate
`0x003A6CC0` accepts the query's attribute word for selection bitmask `+0x28`;
its code table belongs to
[Footprint surface selection](stage_surface_attributes.md#footprint-surface-selection).
Accepted contact caches the foot transform and
surface normal. A later missing or more distant result emits one mark if the
previous contact latch was set, then clears the latch. Merely remaining in
contact does not continuously emit marks, and a close unselected surface does
not take that emission branch.

Placement helper `0x003A6300` takes the first inactive node from that foot's
30-node pool; a full pool skips emission. It uses the retained orientation and
surface normal, raises component 2 by 4, sets opacity to `0.5`, and writes the
mark model's transform. In the same eligible update, all pool nodes lose
`0.01` opacity and become inactive below `0.01`. Pool exhaustion, contact
edges, and fade are therefore explicit local state, with no fighter write or
fighter-impact call in this path.

The sole S13 `ccBgMangroveBattle` derives its construction from
`ccBgLandingTreeBattle`. Derived parser preserved `0x006D3CA0`, file
`0x01FDE0`, live `0x006D3CE0`, calls base parser preserved `0x006C9B60`, then
uses the remaining `OBJ_obj_121,DMY_ki_dummy` tokens. The base tokens create
three `0xB0` elements from formatted `OBJ_obj_120_a%d` names around
`DMY_dummy_010`; the derived half creates another three from
`OBJ_obj_121_a%d` and applies the `DMY_ki_dummy` transform.

LandingTree update preserved/file/live
`0x006C9F70 / 0x0160B0 / 0x006C9FB0` calls the complete reaction helper at
live `0x006CA310` (preserved `0x006CA2D0`). It checks both fighters against
the current tree center: absolute component-0 distance at most half configured
`+0x54`, component-2 distance at most `+0x58`, and component-1 distance at most
200. Out-of-range fighters clear their individual latches at `+0x5C/+0x5D`.
In range, fighter `+0xBB4 & 0x2000D801` must be nonzero. Major states 0/1
and 4 can arm a new latched reaction; state 2 reacts only with an existing
latch, nonzero fighter `+0x998`, and substate other than 23, then clears the
latch. Other major states require fighter `+0xB9A == 1` and a clear latch.
For states 0/1, `+0xB9A >= 9` pre-arms the latch and suppresses a new impulse.
The accepted paths queue amplitude `-50`, initialize it immediately if idle,
and call resident `0x00336630` with the stage surface classifier's result,
configured width, scalar 2, and integer 10. The numeric effect's visual name
is unresolved; this helper contains no fighter hit call or fighter write.

The displacement update samples a shared resident float table using index
`+0x50`, advances that index by 4 per invocation, and multiplies the sample
by amplitude `+0x64` into component-2 displacement `+0x78`. At the table's
signed-halfword length it adopts a queued stronger negative impulse or halves
the amplitude, and resets the index; magnitude below `0.5` clears the motion.
It then applies the displaced center to every inherited model. Mangrove's
derived update, preserved/file/live
`0x006D3F90 / 0x0200D0 / 0x006D3FD0`, first runs that update, then positions
its second model group at `derived_origin - (current_center - original_center)`.
The two groups thus move in opposite directions under the same reaction.

`ccHadesMarshSnake`, constructed only by `S15 #27`, is the proved exception to
the breakable-only receiver behavior. Its factory is preserved
`0x006D21A0`, file `0x01E2E0`, live `0x006D21E0`; it allocates `0x250` bytes
and embeds `ccBgAttackHit` receivers at `+0x110` and `+0x1A0`. Parser/init
preserved `0x006D0590`, file `0x01C6D0`, live `0x006D05D0`, ignores the
authored string `-1` and resolves ten hardcoded `ANM_s15dai00_*` animations at
`+0x2C..+0x50`, a model at `+0x28`, state bytes `+0x55/+0x56/+0x57`, and an
attack descriptor at `+0x58`.

Its update is preserved `0x006D08B0`, file `0x01C9F0`, live `0x006D08F0`,
with states 0 through 9. States 0/1/2 run idle and contact-detection cycles;
receiver `+0x1A0` selects left/right reaction state 4/5. State 6 chooses attack
state 7 through 9 with `FUN_00180210(2) + 7`, configures the attack descriptor
through preserved `0x006D1F30`, and enables receiver `+0x110`. The three attack
states open integer animation-frame windows 27..29, 26..27, and 46.

During those windows, helper preserved `0x006D1650`, file `0x01D790`, live
`0x006D1690`, tests both fighters for membership in receiver `+0x110`, applies
fighter-state exclusions, and calls resident
`FUN_002335F0(fighter, snake+0xB0, snake+0x58)`, then emits effect `0x1F`.
`FUN_002335F0` records the attacker and attack descriptor, calls
`FUN_00232B80`, resets hit-motion fields, and invokes fighter reaction
callbacks. This proves that the S15 snake enters the combat hit-state pipeline.
The stage-object method and `FUN_002335F0` itself perform no HP arithmetic,
but the synchronous common-response chain reaches a proved HP subtraction as
described below.

`ccBgBreakObjectBattleChandelier`, instantiated six times by S21, is a second
explicit receiver-to-fighter-hit consumer. Its factory is preserved
`0x006D3800`, file `0x01F940`, live `0x006D3840`, allocating `0x350` bytes;
update is preserved `0x006D2DB0`, file `0x01EEF0`, live `0x006D2DF0`. The
object embeds three `ccBgAttackHit` receivers at `+0x50/+0xE0/+0x170`, an
attack source at `+0x260`, and attack descriptor/config at `+0x200`.

Its state at `+0x2E8` drives a complete drop/impact cycle:

1. State 0 uses receiver `+0xE0` only to swing and receiver `+0x50` to accept a
   filtered contact, add metric 12 through statistic adder live `0x00715F90`
   ([Match outcomes](../session/battle_statistics.md#ninja-tools-and-stage-objects)), and
   enter state 1.
2. State 1 applies acceleration `9.8`, lowers the current transform, advances
   the break model on impact, spawns debris/effects, and enters state 2.
3. For its first 61 ticks, state 2 enables receiver `+0x170`; every eligible
   fighter in that receiver is passed to
   `FUN_002335F0(fighter, chandelier+0x260, chandelier+0x200)` and effect
   `0x1001`. It then disables the receiver, removes debris, and enters state 3.
4. State 3 restores the initial transform after break state `+0x48` clears.

An independent rebirth loop waits more than 120 ticks while broken, resets
model zero, decrements a finite repeat count, and fades opacity in by `0.05`
per tick before clearing the broken state. This proves that the S21 chandelier
drops, enters fighter hit processing during a 61-tick impact window, cleans
up, can respawn when configured, and reaches the common HP path below.

A raw-overlay scan finds exactly two BTL JAL encodings of resident
`FUN_002335F0`: file/preserved/live callsites
`0x01DA7C / 0x006D193C / 0x006D197C` for the snake and
`0x01EE8C / 0x006D2D4C / 0x006D2D8C` for the chandelier. They are therefore
the only statically proved stage-object users of this explicit fighter-hit
entry in the retail BTL overlay.

### Proven stage-object hit-to-HP path

Resident `FUN_002335F0` calls ordinary-response initializer
`FUN_00232B80` at runtime/file callsite
`0x00233754 / 0x00133854`, then invokes the fighter action dispatcher
`FUN_00249640` at `0x00233834 / 0x00133934` in the same call. The initializer
selects major state 5 and arms the primary response timeline; it contains no
HP store. The immediate dispatcher sends major state 5 to
`FUN_00234DA0`, whose armed event-zero path calls ordinary damage consumer
`FUN_002346B0` at `0x00234DD4 / 0x00134ED4`. That consumer calls calculator
`FUN_00224E30` at `0x00234A80 / 0x00134B80` and HP subtractor
`FUN_00225050` at `0x00234A94 / 0x00134B94`, whose Practice, ordinary, and
zero-clamp HP stores are runtime/file `0x00225174 / 0x00125274`,
`0x002251C0 / 0x001252C0`, and `0x002251DC / 0x001252DC`. The consumer's
record reads, the calculator, and HP application belong to
[Native damage calculation](../combat/damage.md#native-damage-calculation),
[Calculator formula](../combat/damage.md#calculator-formula), and
[Damage application](../combat/damage.md#damage-application).

Both stage classes build records that pass the
[ordinary-hit damage gates](../combat/damage.md#ordinary-hit-damage-gates). The Hades
snake initializes record `+0x24 = 0.05`, `+0x2E = 1`, response selector
`+0x2C = 0x12` and `+0x28 = 1.8` for attack states 7/8, or selector `0x15`
and `+0x28 = 1.0` for state 9. The chandelier uses `+0x24 = 0.05`,
`+0x2E = 1`, `+0x28 = 1.0`, and selector `+0x2C = 0x1E`. These map to
ordinary response families rather than the excluded `0x42..0x49` range. For
both records, `FUN_002346B0` supplies calculator flags `0x122` and the base
value is exactly `0.05 / 1`, so the HP delta is scaled by the defender's
durability, reservation, temporary-effect, and handicap factors and clamped
to `0..1`; its exact value is contextual.

A source response callback does not bypass these stage hits. Both source
objects are constructed with source `+0x0C = -1`; the optional callback path
requires that field to be zero. Normal fighter `+0xB00 == 0` proceeds, and all
observed fallback response IDs also remain outside the damage routine's
excluded `0x42..0x49` range. No stage-source response bypass of the HP path was
found.

Named assets tie the generic machinery to at least some stage-specific
backgrounds:

- `FUN_006c61c0` uses `ANM_s13cra00_a1` at file/live
  `0x1DCE90 / 0x00890D90` and `DMY_s13hak00_hit` at
  `0x1DCEBC / 0x00890DBC`;
- the `s15` pool includes `ANM_s15dai00_d1`, `_d2`, `_a1`, `_a2`, `_a3`, and
  `_a4` at file `0x1DCFD0..0x1DD020`, live
  `0x00890ED0..0x00890F20`.

Direct BTL-name -> BTL-RTTI-descriptor -> resident-vtable linkage establishes
the following compiled background types. The vtable address is the installed
resident vtable whose first word is the listed live BTL descriptor. This is
stronger than a loose name-pool hit, but by itself still does not prove a
stage assignment or behavior. The factory and archive tables above provide
those additional links where established.

| Type | Resident vtable | Live RTTI | Name Ghidra / file / live |
| --- | ---: | ---: | --- |
| `ccBgMangroveBattle` | `0x005DD6C0` | `0x008C2088` | `0x008911B0 / 0x1DD2F0 / 0x008911F0` |
| `ccBgLandingTreeBattle` | `0x005DD990` | `0x008C2068` | `0x008911D0 / 0x1DD310 / 0x00891210` |
| `ccBgFootMarkBattle` | `0x005DD6F0` | `0x008C20C8` | `0x008911F0 / 0x1DD330 / 0x00891230` |
| `ccBgBreakObjectBattleChandelier` | `0x005DD720` | `0x008C20E0` | `0x00891230 / 0x1DD370 / 0x00891270` |
| `ccHadesMarshSnake` | `0x005DD750` | `0x008C20F8` | `0x00891250 / 0x1DD390 / 0x00891290` |
| `ccCraneTruck` | `0x005DD780` | `0x008C2110` | `0x00891268 / 0x1DD3A8 / 0x008912A8` |
| `ccHandRowShip` | `0x005DD7B0` | `0x008C2128` | `0x00891278 / 0x1DD3B8 / 0x008912B8` |
| `ccBgBreakObjectMoveBattle` | `0x005DD7E0` | `0x008C2168` | `0x00891290 / 0x1DD3D0 / 0x008912D0` |
| `ccBgBreakObjectBattle` | `0x005DDAE0` | `0x008C2140` | `0x008912B0 / 0x1DD3F0 / 0x008912F0` |
| `ccBgBreakObjectFallBattle` | `0x005DD810` | `0x008C2188` | `0x008912D0 / 0x1DD410 / 0x00891310` |
| `ccBgTransObject2` | `0x005DD840` | `0x008C21C8` | `0x008912F0 / 0x1DD430 / 0x00891330` |
| `ccBgTransObject` | `0x005DDA40` | `0x008C21A0` | `0x00891310 / 0x1DD450 / 0x00891350` |
| `ccBgBreakObjectRebornBattle` | `0x005DD870` | `0x008C21E8` | `0x00891320 / 0x1DD460 / 0x00891360` |
| `ccTumbleGrass` | `0x005DD8A0` | `0x008C2200` | `0x00891340 / 0x1DD480 / 0x00891380` |
| `ccGrassInfluence` | `0x005DD8C8` | `0x008C2208` | `0x00891350 / 0x1DD490 / 0x00891390` |
| `ccBgEscapeBirdBattle` | `0x005DD8E0` | `0x008C2220` | `0x00891370 / 0x1DD4B0 / 0x008913B0` |
| `ccBgSuspensionBridge` | `0x005DD910` | `0x008C2238` | `0x00891390 / 0x1DD4D0 / 0x008913D0` |
| `ccBgCrashBreakBattle` | `0x005DD960` | `0x008C2288` | `0x008913F0 / 0x1DD530 / 0x00891430` |
| `ccWireHitModel` | `0x005DD9D0` | `0x008C2290` | `0x00891408 / 0x1DD548 / 0x00891448` |
| `ccElectricWire` | `0x005DD9E0` | `0x008C22A8` | `0x00891418 / 0x1DD558 / 0x00891458` |
| `ccBgTransAnm` | `0x005DDA10` | `0x008C22C0` | `0x00891428 / 0x1DD568 / 0x00891468` |
| `ccBgBreakDollBattle` | `0x005DDA70` | `0x008C22E8` | `0x00891440 / 0x1DD580 / 0x00891480` |
| `ccBgBreakObjectBattleAnm` | `0x005DDAA0` | `0x008C2300` | `0x00891460 / 0x1DD5A0 / 0x008914A0` |
| `ccBgAttackHit` | `0x005DDAC8` | `0x008C2308` | `0x00891480 / 0x1DD5C0 / 0x008914C0` |

The RTTI parent links make the hierarchy precise: `BreakMove`, `BreakFall`,
`BreakReborn`, `CrashBreak`, and `BreakDoll` derive from
`ccBgBreakObjectBattle`; `ccBgTransObject2` derives from `ccBgTransObject`.
Despite their names, `BreakAnm` and `BreakObjectBattleChandelier` do not carry
that BreakBase parent link and implement their own state machines.

The combined evidence proves stage-specific animated, breakable, transition,
and contact-driven background systems. It proves that the S15 snake and S21
chandeliers use `ccBgAttackHit` receivers to enter fighter hit processing and,
on the normal authored path, reach the resident HP subtractor. The exact
context-scaled numeric delta remains unresolved. The S19/S21/S24 wire class
instead has a proved reactive path with no direct fighter hit. No background
hit-points field or item drop behavior was established.

## Destruction and archive release

The `ccField` destructor is preserved `FUN_00708860`, Ghidra
`0x00708860`, file `0x0549A0`, live `0x007088A0`. It restores the derived
vtable, obtains `ccField+0x70`, installs the `ccBgControl` vtable, and executes
raw JAL targets live `0x006C29E0` then `0x006C29A0`. It then frees remaining
vector storage at control `+0xA88`, frees the control, clears `ccField+0x70`,
tears down the embedded `ccGameObjCtrl` at `ccField+0x60`, and finally
tears down/frees the `ccField` when requested. Those targets resolve to preserved `FUN_006c29a0`, the large
control cleanup, and `FUN_006c2960`, the global deregistration helper; live
`0x006C2A20` is not called here.

The control cleanup walks and destroys every element in the config vector,
frees every linked line list and both sides' pointer arrays, and invokes the
`ccBgSystem` virtual destructor before clearing control `+0x04`. The preserved
`ccBgSystem` destructor wrapper is `FUN_006c2c80`, file `0x00EDC0`, live
`0x006C2CC0`. Resident `FUN_003AD5E0` walks the five `0x10`-byte owning-list
containers at scene `+0x74..+0xBC`, follows object `+0x20`, and calls each
object's virtual destructor at vtable `+0x24`. It then calls
`FUN_003ADC60`, which destroys all 12 non-owning selector owners at
`scene+0x44` and their 12 associated objects at `scene+0x10C`, before tearing
down the remaining auxiliary structures at scene `+0x108`, `+0xD0`, and
`+0xCC`.

For the resolved stage-specific classes below, vtable slot `+0x20` is a
no-op and slot `+0x24` is the actual virtual destructor. Their local cleanup
confirms that scene destruction owns the derived objects while archive-node
destruction remains centralized:

| Class | Destructor Ghidra / file / live | Confirmed owned cleanup |
| --- | --- | --- |
| `ccBgMangroveBattle` | `0x006D4420 / 0x020560 / 0x006D4460` | destroy derived `+0x90` elements, then inherited LandingTree `+0x2C` elements |
| `ccBgFootMarkBattle` | `0x006D4510 / 0x020650 / 0x006D4550` | destroy its two-by-two footprint-node arrays through the resident base controller |
| `ccHadesMarshSnake` | `0x006D47A0 / 0x0208E0 / 0x006D47E0` | destroy model `+0x28`, both attack receivers, and generic node `+0xB0` |
| `ccCraneTruck` | `0x006D48D0 / 0x020A10 / 0x006D4910` | destroy model/controller `+0x2C`; leave the separately scene-owned break object at `+0x38` to the scene |
| `ccHandRowShip` | `0x006D4980 / 0x020AC0 / 0x006D49C0` | destroy both owned model/controller objects at `+0x28/+0x2C` |
| `ccTumbleGrass` | `0x006D4DD0 / 0x020F10 / 0x006D4E10` | destroy clump array `+0x2C`, release variant resources, and free `+0x30` |
| `ccBgEscapeBirdBattle` | `0x006D4F00 / 0x021040 / 0x006D4F40` | unregister and destroy the resident child at `+0x28` |
| `ccBgSuspensionBridge` | `0x006D4FB0 / 0x0210F0 / 0x006D4FF0` | destroy node array `+0x2C` and rope/helper arrays `+0x30/+0x34` |
| `ccElectricWire` | `0x006D51A0 / 0x0212E0 / 0x006D51E0` | destroy `ccWireHitModel` vector `+0xF0` and free node buffers `+0x60/+0x64/+0x68` |

None of these destructors releases the scene/archive handle; each finishes
through the common `ccBgObject` teardown and optional self-free.

The wire vector's element callback is live BTL `0x006C8860`, preserved
`0x006C8820`, file `0x014960`. It calls resident `0x003A84C0` before
destroying the embedded visual helper. Resident cleanup releases environment
object `element+0x180` through `0x001BEF30(object,1)`; its active-object
branch invokes `0x001BF020`, which unlinks it from the environment chain,
updates head/tail/count, and clears registration state before freeing it.
Cleanup separately destroys visual model `+0x1C0` through `0x001996B0` and
clears both pointers. This proves collision deregistration as well as visual
cleanup for the wire's ordinary local destruction path.

The standalone `ccFieldCtrl` is destroyed by its parent owner, not by the
field's embedded-control teardown. Root destruction calls live `0x00709280`
(preserved `FUN_00709240`, file `0x055380`), whose owner teardown at live
`0x007093A0` dispatches `ccFieldCtrl` virtual `+0x08`, live `0x007091A0`.
That method walks the member list through live `0x00709F40` and invokes each
member's virtual destructor, reaching `ccField` live `0x007088A0` before the
standalone controller itself is released.

The complete session teardown order belongs to
[Battle lifecycle](../session/battle_lifecycle.md#teardown-order). On the normal path,
controller state 16 `FUN_001edd10` destroys the battle graph through
`FUN_001eecd0` (whose `FUN_001eefd0` destroys the pause controller,
the graph, and the manager's fighter-pointer arrays) and proceeds to state 17.
The result-8 continuation instead branches to state 23 or 24; those handlers,
`FUN_001ee1c0` and `FUN_001ee500`, perform the same graph teardown first, and
state 24 does so before releasing or switching either archive.

Only afterward does state 17, `FUN_001edee0`, release common resources, the
four-resource BTL bundle (`shade.ccs`, `gauge.ccs`, `strmcmn.ccs`, and
`ougi.ccs`) through live `0x007691A0`, the selected stage archive through live
BTL `0x006C3160`, both players' fighter-resource handles, and the
`FUN_00207e20(slot)` stage-associated resource; see
[archive lifetime](../session/battle_lifecycle.md#archive-lifetime-is-separate-from-session-lifetime).
The same archive-release helper is called by central cleanup `FUN_001e9730`
and by the stage-switch path `FUN_001ee500`. This proves graph-before-archive
ordering for the orderly state-16-to-17 path and for state-24 switching.

It is not a universal emergency-cleanup guarantee. Two higher-level destructor
paths call central cleanup `FUN_001e9730` before conditionally destroying a
still-nonnull main graph: `FUN_001f2020` at callsites `0x001F2038` then
`0x001F2134`, and `FUN_001fe390` at `0x001FE3AC` then through
`FUN_001ec540`. Those paths may normally arrive after the graph is already
null, but their static order is archive-first if it is not.

No explicit archive-release call appears in the `ccBgControl` destructor.
Its `+0x00` handle and the scene's `+0x38` handle behave as lookups/borrowed
references; BTL global owner slot `0x006077E0` (`gp-0x3210`) is the handle
released and cleared after graph teardown on the orderly and switch paths.
Resident `FUN_001aa450` and `FUN_001aa4b0`
strip directory components and the final extension to a basename stem, then
traverse global resource-list head `0x00607488`; neither performs a count
increment or ownership store. `FUN_001a9790(handle, 1)` unlinks the exact node,
invalidates `#` dependency records in every remaining node by restoring
sentinel 4 at `+0x2C`, clearing halfword `+0x2A`, and propagating dirty state,
tears down its child/container
contents, and frees it. The observed path is full destruction after borrowed
lookups, not a reference-count decrement.

## NUN3 battle stages compared with NA2

The retail NUN3 battle-stage archives, compiled scene-record tables, summon
scenes, and their correspondence with the NA2 records above are documented in
[NUN3 battle stages](nun3_stages.md). That comparison lists the NA2 archives
that reuse NUN3 stage content in
[Stage content shared with NA2](nun3_stages.md#stage-content-already-shared-with-na2).

## Address index

### BTL functions

| Preserved symbol | Ghidra | File | Live | Role |
| --- | ---: | ---: | ---: | --- |
| `FUN_006c1a10` | `0x006C1A10` | `0x00DB50` | `0x006C1A50` | select archive and construct `ccBgSystem` |
| `FUN_006c1b80` | `0x006C1B80` | `0x00DCC0` | `0x006C1BC0` | line midpoint raycast pass |
| `FUN_006c22d0` | `0x006C22D0` | `0x00E410` | `0x006C2310` | config interval clamp |
| `FUN_006c2400` | `0x006C2400` | `0x00E540` | `0x006C2440` | slot-specific numeric classifier |
| `FUN_006c2570` | `0x006C2570` | `0x00E6B0` | `0x006C25B0` | floor-profile interpolation |
| `FUN_006c2890` | `0x006C2890` | `0x00E9D0` | `0x006C28D0` | `ccBgControl` initialization |
| `FUN_006c2960` | `0x006C2960` | `0x00EAA0` | `0x006C29A0` | background-control global deregistration |
| `FUN_006c29a0` | `0x006C29A0` | `0x00EAE0` | `0x006C29E0` | large control cleanup |
| `FUN_006c2c80` | `0x006C2C80` | `0x00EDC0` | `0x006C2CC0` | `ccBgSystem` destructor wrapper |
| `FUN_006c2de0` | `0x006C2DE0` | `0x00EF20` | `0x006C2E20` | `s15` animation-object lookup |
| `FUN_006c30c0` | `0x006C30C0` | `0x00F200` | `0x006C3100` | synchronous stage-archive acquire |
| `FUN_006c3120` | `0x006C3120` | `0x00F260` | `0x006C3160` | owned stage-archive destroy |
| `FUN_006c3190` | `0x006C3190` | `0x00F2D0` | `0x006C31D0` | asynchronous stage enqueue |
| `FUN_006c31d0` | `0x006C31D0` | `0x00F310` | `0x006C3210` | post-fence archive adoption |
| `FUN_006c3380` | `0x006C3380` | `0x00F4C0` | `0x006C33C0` | line-record builder |
| `FUN_006c3710` | `0x006C3710` | `0x00F850` | `0x006C3750` | paired-node line/config builder |
| `FUN_006c4770` | `0x006C4770` | `0x0108B0` | `0x006C47B0` | base break-state trigger |
| `FUN_006c4a90` | `0x006C4A90` | `0x010BD0` | `0x006C4AD0` | full `BreakObject` contact/update method |
| `FUN_006c5150` | `0x006C5150` | `0x011290` | `0x006C5190` | base break-object config parser |
| `FUN_006c57c0` | `0x006C57C0` | `0x011900` | `0x006C5800` | `BreakAnm` trigger |
| `FUN_006c5b20` | `0x006C5B20` | `0x011C60` | `0x006C5B60` | `BreakAnm` contact/reset/fade update |
| `FUN_006c61c0` | `0x006C61C0` | `0x012300` | `0x006C6200` | named `s13` background objects |
| `FUN_006c74d0` | `0x006C74D0` | `0x013610` | `0x006C7510` | `TransObject` config parser |
| `FUN_006c78c0` | `0x006C78C0` | `0x013A00` | `0x006C7900` | `TransObject` proximity update |
| `FUN_006c7c90` | `0x006C7C90` | `0x013DD0` | `0x006C7CD0` | `TransAnm` config parser |
| `FUN_006c80a0` | `0x006C80A0` | `0x0141E0` | `0x006C80E0` | `TransAnm` proximity update |
| `FUN_006c8490` | `0x006C8490` | `0x0145D0` | `0x006C84D0` | `ElectricWire` config parser |
| `FUN_006c88d0` | `0x006C88D0` | `0x014A10` | `0x006C8910` | construct wire segment array |
| `FUN_006c8ec0` | `0x006C8EC0` | `0x015000` | `0x006C8F00` | `ElectricWire` reactive update |
| `FUN_006c9550` | `0x006C9550` | `0x015690` | `0x006C9590` | refresh dirty wire collision geometry |
| `FUN_006c9a50` | `0x006C9A50` | `0x015B90` | `0x006C9A90` | `ElectricWire` factory |
| `FUN_006cba10` | `0x006CBA10` | `0x017B50` | `0x006CBA50` | suspension-bridge parser |
| `FUN_006ccb60` | `0x006CCB60` | `0x018CA0` | `0x006CCBA0` | bridge geometry/physics pass |
| `FUN_006cd0e0` | `0x006CD0E0` | `0x019220` | `0x006CD120` | suspension-bridge factory |
| `FUN_006cdd40` | `0x006CDD40` | `0x019E80` | `0x006CDD80` | reborn-breakable update |
| `FUN_006ce210` | `0x006CE210` | `0x01A350` | `0x006CE250` | `TransObject2` parser |
| `FUN_006ce270` | `0x006CE270` | `0x01A3B0` | `0x006CE2B0` | `TransObject2` proximity update |
| `FUN_006cf990` | `0x006CF990` | `0x01BAD0` | `0x006CF9D0` | hand-row-ship reactive update |
| `FUN_006d0040` | `0x006D0040` | `0x01C180` | `0x006D0080` | crane-truck break/animation update |
| `FUN_006d08b0` | `0x006D08B0` | `0x01C9F0` | `0x006D08F0` | Hades-snake state update |
| `FUN_006d1650` | `0x006D1650` | `0x01D790` | `0x006D1690` | Hades-snake attack-window helper |
| `FUN_006d2db0` | `0x006D2DB0` | `0x01EEF0` | `0x006D2DF0` | chandelier drop/hit update |
| `FUN_006d3800` | `0x006D3800` | `0x01F940` | `0x006D3840` | chandelier factory |
| `FUN_006f1f20` | `0x006F1F20` | `0x03E060` | `0x006F1F60` | nearest intersecting line query |
| `FUN_006f2160` | `0x006F2160` | `0x03E2A0` | `0x006F21A0` | nearest intersecting line query |
| `FUN_006f24a0` | `0x006F24A0` | `0x03E5E0` | `0x006F24E0` | vertical intersecting line query |
| `FUN_006f3770` | `0x006F3770` | `0x03F8B0` | `0x006F37B0` | line-index and route selection |
| actual route-executor entry | `0x006F6360` | `0x0424A0` | `0x006F63A0` | consume navigation route/type |
| `FUN_00708760` | `0x00708760` | `0x0548A0` | `0x007087A0` | `ccField` constructor |
| `FUN_00708860` | `0x00708860` | `0x0549A0` | `0x007088A0` | `ccField` destructor |
| `FUN_00708a40` | `0x00708A40` | `0x054B80` | `0x00708A80` | field boundary-clamp wrapper |
| `FUN_00708c30` | `0x00708C30` | `0x054D70` | `0x00708C70` | field classifier wrapper |
| `FUN_00708ca0` | `0x00708CA0` | `0x054DE0` | `0x00708CE0` | field floor-profile wrapper |
| raw accessor entry | `0x00708D20` | `0x054E60` | `0x00708D60` | active first-family line accessor |
| `FUN_00708d60` | `0x00708D60` | `0x054EA0` | `0x00708DA0` | active second-family line accessor |
| `FUN_00709440` | `0x00709440` | `0x055580` | `0x00709480` | construct linked camera/command/player/field graph |
| `FUN_007099e0` | `0x007099E0` | `0x055B20` | `0x00709A20` | `ccField` factory/list attachment |

### Resident lifecycle and scene functions

| Function | Runtime | ELF file | Role |
| --- | ---: | ---: | --- |
| `FUN_001e9520` | `0x001E9520` | `0x0E9620` | common/fighter/stage preload |
| `FUN_001e9730` | `0x001E9730` | `0x0E9830` | central resource cleanup |
| `FUN_001ed6d0` | `0x001ED6D0` | `0x0ED7D0` | state 9 selected-slot handoff |
| `FUN_001ed880` | `0x001ED880` | `0x0ED980` | state 10 preload entry |
| `FUN_001ed980` | `0x001ED980` | `0x0EDA80` | controller state 11 loader-fence wait |
| `FUN_001ed9e0` | `0x001ED9E0` | `0x0EDAE0` | controller state 12 readiness wait |
| `FUN_001eda50` | `0x001EDA50` | `0x0EDB50` | state 13 fighter construction and stage adoption |
| `FUN_001edb00` | `0x001EDB00` | `0x0EDC00` | state 14 graph construction |
| `FUN_001edb70` | `0x001EDB70` | `0x0EDC70` | state 15 graph readiness/update |
| `FUN_001edd10` | `0x001EDD10` | `0x0EDE10` | state 16 graph teardown |
| `FUN_001edee0` | `0x001EDEE0` | `0x0EDFE0` | state 17 archive and fighter-resource-handle release |
| `FUN_001ee500` | `0x001EE500` | `0x0EE600` | result-8 continuation stage-switch resource path |
| `FUN_001eefd0` | `0x001EEFD0` | `0x0EF0D0` | main battle-graph teardown |
| `FUN_001ef330` | `0x001EF330` | `0x0EF430` | heavy battle-graph construction |
| `FUN_001ef8f0` | `0x001EF8F0` | `0x0EF9F0` | main graph readiness driver |
| `FUN_00207e20` | `0x00207E20` | `0x107F20` | select stage-grouped `n_rash` archive |
| `FUN_00225050` | `0x00225050` | `0x125150` | subtract/clamp fighter HP |
| `FUN_00232b80` | `0x00232B80` | `0x132C80` | initialize ordinary hit-response state |
| `FUN_002335f0` | `0x002335F0` | `0x1336F0` | enter fighter hit-state processing |
| `FUN_002346b0` | `0x002346B0` | `0x1347B0` | process response event zero and dispatch damage |
| `FUN_00234da0` | `0x00234DA0` | `0x134EA0` | drive the active ordinary response |
| `FUN_00249640` | `0x00249640` | `0x149740` | dispatch current fighter action update |
| `FUN_003ac4d0` | `0x003AC4D0` | `0x2AC5D0` | attach a `BIN_bgdata` object to a scene list |
| `FUN_003ac740` | `0x003AC740` | `0x2AC840` | resolve and initialize `BIN_bgdata` for a scene |
| `FUN_003ad5e0` | `0x003AD5E0` | `0x2AD6E0` | destroy the five owning stage-object lists and scene auxiliaries |
| `FUN_003adc60` | `0x003ADC60` | `0x2ADD60` | destroy 12 selector owners and 12 associated selector objects |
| `FUN_003ade40` | `0x003ADE40` | `0x2ADF40` | parse `BIN_bgdata` triple/string records |
| `FUN_003ae220` | `0x003AE220` | `0x2AE320` | dispatch records through the factory table |

Important resident callsites are stage enqueue at runtime/ELF
`0x001E964C / 0x0E974C`, synchronous acquire at
`0x001E9668 / 0x0E9768`, post-fence adoption at
`0x001EDAD0 / 0x0EDBD0`, normal stage release at
`0x001EDFB4 / 0x0EE0B4`, central-cleanup release at
`0x001E9834 / 0x0E9934`, and stage-switch release/enqueue at
`0x001EE67C / 0x0EE77C` and `0x001EE7C4 / 0x0EE8C4`.

## Remaining questions

- Identify a semantic reader of cached line `+0x2C` beyond the navigation,
  direct-accessor, and head-table alias paths audited above; no reader is
  established by those paths.
- Name factory-17's render coefficients from their material/lighting context,
  beyond the established packet writes.
- Resolve the unexamined NA2 factories and numeric route/effect codes.
- Identify remaining writers of scene factor `scene+8` and the unassigned
  update-restriction, effect, and surface-code semantics without inferring
  elapsed-time units.
