# Battle stage gameplay knowledge

This document owns established and unresolved knowledge about battle-stage
resources, live environment objects, stage geometry, geometry-driven movement,
and stage teardown. It does not cover Stage Select presentation or Adventure
mode.

## Research coverage

- **Assigned scope:** the clean NA2 battle-stage implementation in
`PRG/BTL.BIN`: load-slot/resource mapping, archive and object lifecycle,
stage-authored geometry/configuration, background transitions and reactive or
damaging objects, and unload/cleanup. Stage Select presentation was in scope
only where needed to prove the raw-slot handoff; its UI layout and rendering
were not investigated.

- **Exploration depth:** coverage depth was as follows:

  **Exhaustive within fixed tables/assets:** all 24 stage-path entries and the
  24-entry logical-ID mapper were decoded; all `STAGE/S01.CCS` through
  `S24.CCS` archives were gzip-decoded in memory; every archive's sole
  `BIN_bgdata` payload was structurally validated; all records belonging to
  the 20 RTTI/vtable-linked named background factories were counted; and the
  four authored line/config records in every archive were decoded into the
  per-stage line-count table. This is not an exhaustive semantic decode of all
  129 non-null factory-table entries.
  **Exhaustive targeted callsite scans:** the stage surface/effect classifier's
  eight BTL and seven resident consumers were enumerated, and the clean BTL was
  scanned for the resident fighter-hit entry `FUN_002335F0`, yielding exactly
  the documented snake and chandelier callsites. These statements are
  exhaustive for the exact encoded targets in the clean binaries, not for
  hypothetical dynamic name lookups or externally altered code.
  **Bounded lifecycle trace:** resident controller states 9 through 17 and
  transition states 23/24 were followed through `FUN_001e9520`, the four BTL
  archive helpers `FUN_006c30c0..FUN_006c31d0`, graph construction through
  `FUN_001ef330`, orderly teardown, stage switching, and the known central and
  higher-level cleanup callers. This established normal-path ordering and the
  explicitly documented emergency-cleanup caveat; it was not a whole-program
  proof over every indirect destruction path.
  **Bounded environment/object trace:** `ccField`/`ccBgControl` construction,
  `FUN_003ac740..FUN_003ae220` scene parsing/dispatch, five owning lists, 12
  selector collections, the named factory/vtable methods from roughly
  preserved BTL `0x006C4770..0x006D51A0`, and their local destructors were
  inspected where directly tied to clean stage records. Generic render,
  physics, and collision helpers were followed only far enough to establish
  the documented side effects or a concrete no-hit result.
  **Bounded geometry and combat trace:** line construction/query code
  `FUN_006c1b80`, `FUN_006c22d0..FUN_006c2570`,
  `FUN_006c3380/FUN_006c3710`, and the route/collision consumers beginning at
  `FUN_006f1f20` were traced through their record layouts and numeric
  exceptions. The two proved damaging stage objects were followed from BTL
  contact receivers through resident `FUN_002335F0`, response event zero,
  `FUN_00224E30`, and the HP stores in `FUN_00225050`.
  **Sampled authored detail:** the factory census is complete for the named
  types, but the displayed configuration-string table intentionally contains
  representative unique records rather than every string from every stage.
  Visual/material names were not assigned when static code supplied only a
  numeric effect, list selector, route type, or model resource.

- **Confirmed coverage:** the load-slot/logical-ID distinction;
stage and `n_rash` ownership; raw selection handoff; `BIN_bgdata` framing,
factory routing, and per-stage census; scene ownership; boundary/floor lines;
surface-effect classification; proximity transitions; navigation data;
breakable, reborn, deformable, and reactive props; the two explicit
stage-object-to-HP paths; and normal/switch/emergency teardown behavior.

- **Unresolved or untested:** whether the
line-route planner is CPU-only or shared, the exact downstream meaning of line
record `+0x2C`, semantic naming of the other factory-table entries and numeric
route/effect codes, and runtime-visible confirmation of the statically derived
behaviors. The separate `0x6C0` aggregate was bounded as a non-polymorphic
battle special-sequence/presentation owner with only a stored stage tag; no
unsupported original class name was assigned.

- **Deliberate exclusions and overlap:** Adventure mode, Stage Select presentation beyond
the slot handoff, camera/projection/layout work, localization, media
replacement, damage-scaling modifications, substitution, and 60-FPS work.
Generic fighter mechanics were entered only to prove the downstream effect of
the two stage-owned hit sources. No other task's canonical document or index
was edited.

- **Evidence limitations:** validation was static against the exact clean `BTL.BIN`, resident
`SLPS_258.37`, and 24 clean CCS archives identified below. No runtime capture,
instrumented play session, or emulator-visible validation was performed. The
BTL `+0x40` import defect was audited against raw bytes and encoded live
targets, but indirect runtime behavior remains subject to that static-analysis
limit.

## Evidence and address convention

The clean resident and BTL inputs and their address conversions are defined in
[Standard game file identities](../game/files/file_identities.md).
The analysis was static; no new runtime capture was made for this document.
Every BTL address below distinguishes the preserved Ghidra location, raw file
offset, and live address where relevant.

Claims described as **confirmed** follow directly from raw bytes and control or
data flow. **Supported** interpretations additionally use RTTI, resource names,
or surrounding behavior. **Unresolved** interpretations are retained only as
leads.

## Stage identity and resource mapping

The battle manager byte at `+0x98` is the active zero-based **load slot**, not
the one-based logical stage ID. The pending load slot used by stage switching
is at `+0x9A`. `FUN_006c1a10` copies its slot argument to manager `+0x98` and
to `ccBgControl+0x0C` before indexing the archive table. A captured Practice
value of `6` therefore selects `stage/s07.ccs`, not `stage/s06.ccs`.

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

The preserved export misbinds the body around `FUN_006c14e0`; the raw start
and table are authoritative. The same sequence is independently present as
the first word of 24 `0x10`-byte records at Ghidra/file/live
`0x008C3AD0 / 0x20FC10 / 0x008C3B10`; their second word is the zero-based slot.
The remaining record fields are outside this document's gameplay scope and
are not assigned semantics here.

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

The table appears at Ghidra `0x008909D0`, not at the same-numeric
`PTR_s_stage_s21_ccs_00890a10` label used by the decompiler. At raw file
`0x1DCB10`, the first entry is `0x00890890`, the live `s01` string. Reading
the decompiler label literally shifts the table by 16 entries and produces a
false `s21` base.

## Archive preload, adoption, and switching

The resident battle controller orchestrates the archive resource-node lifetime.
The confirmed sequence is:

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
   This is whole-battle readiness; the current evidence does not isolate it as
   an environment-only update.

No direct current caller of the `FUN_001e9520(0)` synchronous branch was found.

The state-9 handoff is a raw slot handoff, not a logical-ID conversion. Live
BTL `0x00714460` (preserved `FUN_00714420`, file `0x060560`) clears the
selection object's choice count, tests slots 0 through 23 in ascending order
with resident `FUN_001f58b0(manager, slot)`, and appends each accepted raw slot
to the choice array at object `+0x14`. State 9 initializes the `0x16C`-byte
selection object through live BTL `0x00713A50` and `0x00713DC0`, scans for the
initial choice through live `0x007147C0`, polls live `0x00715830`, and on
success invokes the getter at live `0x00714810`. That getter indexes the
object's choice array from its current index at `+0x74`; state 9 stores the low
byte of the selected entry directly at manager `+0x98`. While selection remains
in progress it calls live `0x00715CC0`; before freeing the object it calls live
`0x00713B20`. Controller mode 2 requests/preselects slot 6; the setter first
clears index `+0x74`, scans the available choice array for value 6, and leaves
index zero when it is absent. Resident setup initializes the slot bitset at
runtime `0x00607688` from the exact byte sequence `0..23`, and no decoded clear
path exists; consequently the clean choice list is all 24 raw slots in order
and mode 2 hands off slot 6. Mechanically, an externally altered bitset that
omitted 6 would make the setter fall back to the first choice.

The corresponding resident callsites are `0x001ED734`, `0x001ED744`,
`0x001ED770`, `0x001ED784`, `0x001ED7C4`, `0x001ED80C`, and `0x001ED7E8`.
Their actual preserved Ghidra targets are respectively `0x00713A10`,
`FUN_00713d80`, the unlabeled routine at `0x00714780`, `FUN_007157f0`, the
unlabeled getter at `0x007147D0`, `FUN_00715c80`, and `FUN_00713ae0`. The
manager write is runtime `0x001ED7D0`. This target list is another concrete
case where accepting the export's same-numeric internal labels would move each
BTL callee `0x40` bytes late.

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
occur in the clean resident ELF only in these two table words, with no decoded
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
`FUN_00207e20`. Clean selection and the ordinary random generator produce a
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

The preserved C export omits the final store in `FUN_006c31d0`; raw Ghidra
`0x006C31F4`, file `0x00F334`, live `0x006C3234` is
`sw v0,-0x3210(gp)`. No direct BTL `jal` or function-pointer word targets these
four helpers. Their confirmed callers are resident code using the live overlay
addresses.

`FUN_001ee500` owns a stage-changing rematch/switch path. It compares active
slot `+0x98` with incoming stage slot `+0x9A` after destroying the old runtime
graph.
When they differ, it releases the old archive and `FUN_00207e20` resource
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
Ghidra/file/live callsite `0x007094C4 / 0x055604 / 0x00709504`. Ghidra also
places the false label `FUN_00709a20` `0x40` inside the real factory. The
factory allocates `0x90` bytes, calls the live `ccField` constructor at
`0x007087A0`, and then live `0x00709E60`.

The `ccField` constructor is preserved `FUN_00708760`, Ghidra
`0x00708760`, file `0x0548A0`, live `0x007087A0`. Its export is truncated by a
bad no-return classification. Raw code proves that it:

- allocates a `0xAD0`-byte `ccBgControl` and initializes it with live
  `0x006C28D0`;
- publishes that control through a tiny live helper at `0x006C1A40`;
- when the battle manager exists, passes manager `+0x98`, `+0x4C`, and `+0x74`
  into the background constructor at file callsite `0x05494C`, live
  `0x0070884C`; the fallback call at file `0x05496C`, live `0x0070886C`, uses
  the caller's slot and `-1` identity values;
- stores the control at `ccField+0x70` and performs post-construction setup.

The background constructor is preserved `FUN_006c1a10`, Ghidra
`0x006C1A10`, file `0x00DB50`, live `0x006C1A50`. Raw code, beyond the
truncated decompiler body, confirms this sequence:

1. Copy the slot to manager `+0x98`, a secondary stage-aware controller
   `+0x0E` when present, and `ccBgControl+0x0C`.
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
those lists, and all named factory records in the clean archives use owner
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

### Per-stage `BIN_bgdata` factory census

The clean extracted `STAGE/S01.CCS` through `S24.CCS` archives were
gzip-decompressed and parsed in memory. Every archive contains exactly one CCS
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

The census below is exhaustive for the 20 named factory indices in the
preceding table. `N` includes all `BIN_bgdata` records, including generic types
whose compiled factories have not yet been named.

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

The resident heavy graph also allocates a separate `0x6C0`-byte aggregate at
runtime/file `0x001EF6A4 / 0x0EF7A4`, stores it in global `0x00607834`, and
calls BTL live constructor `0x0076E9D0` with two scalar fighter/character
identifiers from manager `+0x4C/+0x74` and the selected slot. The constructor
stores the low/high bytes of those two values at object `+0x04..+0x07`; they
are not pointers. It installs no top-level vtable, and no RTTI class name is
established. Direct APIs and fields instead identify a non-polymorphic battle
special-sequence/presentation aggregate: `+0x0D` is an idle-or-sequence-kind
byte, `+0x10` is a three-phase state, and `+0x1C` owns a mode-specific backend.

The selected slot is merely mirrored at `+0x0E`. Refresh live `0x0076EC10`
reads it but passes it to a short callee at live `0x006C2F10` (preserved
`FUN_006c2ed0`, file `0x00F010`) that overwrites the argument, clears byte
`+0x6B8`, and calls resident `FUN_001C8830` on the object referenced by
`+0x6BC` without changing that pointer. No stage table, archive,
`ccField`, geometry, or boundary operation is reached. The main constructor
and refresh entries are preserved `FUN_0076e990` and `FUN_0076ebd0`, files
`0x0BAAD0` and `0x0BAD10`; the destructor is preserved `FUN_0076ecb0`, file
`0x0BADF0`, live `0x0076ECF0`. Thus this aggregate carries a stage-slot tag
but is not the environment or geometry owner.

`ccField` update at live `0x007089C0` dispatches `ccBgControl` vtable slots
`+0x08` and `+0x10`; the latter is live `0x006C17C0`, preserved
`FUN_006c1780`. Another field entry at live `0x00708BF0` dispatches vtable
`+0x0C`, live `0x006C1660`, preserved `FUN_006c1620`. These virtual calls
explain the lack of ordinary direct xrefs, but the evidence does not justify
calling any one of them the per-frame environment update.

## Boundary and floor-profile data

### Line construction

Preserved `FUN_006c3380`, Ghidra `0x006C3380`, file `0x00F4C0`, live
`0x006C33C0`, builds linked line records from named nodes in the stage archive.
The exporter spuriously starts `FUN_006c33c0` `0x40` bytes inside this routine.
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
| `+0x2C` | raycast-associated value, initially zero |

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
at preserved `FUN_006c3710`, file `0x00F850`, live `0x006C3750`. The exporter
splits it at same-numeric `FUN_006c3750`; raw callers at preserved
`FUN_006c4540` and `FUN_006c45a0` target the live start. This routine consumes
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
| `+0x00` | pointer to a separately allocated 12-byte vector header whose elements are pointers to this config's second-family line records |
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

The first four records in every clean `BIN_bgdata` blob are exactly factory
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
record in both families and sides. It raycasts vertically from 100 units above
the segment midpoint's component 2 to 100 units below through resident
`FUN_001BF100`; on a hit it stores resident `0x0061F6E8` at record `+0x2C`.
The exact downstream meaning of that stored value is not yet established.

### Boundary clamp

Preserved `FUN_006c22d0`, file `0x00E410`, live `0x006C2310`, obtains a
caller-selected `0x40`-byte config from the vector at control `+0xA80`. It compares
input component 0 with the component-0 values of config vectors `+0x10` and
`+0x20`. An underflow copies the whole `vec4` at `+0x10` to the input; an
overflow copies the whole `vec4` at `+0x20`; either clamp returns zero. A value
inside the interval returns one.

The usable wrapper is preserved `FUN_00708a40`, Ghidra `0x00708A40`, file
`0x054B80`, live `0x00708A80`. It works on a copy, optionally returns the
clamped vector, and returns one when `ccField+0x70` is absent. Its second
argument is passed through as the config index.

### Floor-profile query

The raw routine beginning at preserved `FUN_006c2570`, file `0x00E6B0`, live
`0x006C25B0`, scans the active second-family list for the selected side and
then all active first-family lines. For a segment satisfying
`endpointA.component0 < query.component0 < endpointB.component0`, it linearly
interpolates endpoint component 2 and keeps the lowest candidate. No match
returns `-32768.0`. The output otherwise copies the query, replaces component
2 with the result, and sets component 3 to `1.0`.

The usable wrapper is preserved `FUN_00708ca0`, file `0x054DE0`, live
`0x00708CE0`; it returns the same sentinel when the background control is
absent. The exporter-created `FUN_006c25b0` is a phantom start `0x40` inside
the real routine. Component roles are stated numerically because static code
alone does not prove the engine's axis names.

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
live `0x006C1300`; the exporter's apparent `FUN_006c1300` is the continuation
`0x40` inside it. Given output vector, query vector, and side byte, it selects
the active slot from manager `+0x98`, scans that side's array, copies the
strictly nearest anchor to the output, and returns a side byte. Equal distance
keeps the earlier raw-table element. If no live field/background exists, it
leaves a zero vector and returns side 0.

The raw call at Ghidra `0x00798E58`, file `0x0E4F98`, live `0x00798E98`, is
inside preserved `FUN_00798df0` (file `0x0E4F30`, live `0x00798E30`). That
method feeds object `+0x330` as the query, uses zero or the associated fighter's
section byte at `+0x9F6` as the side, writes the returned side to object
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
`FUN_00708c30`, file `0x054D70`, live `0x00708C70`; apparent wrappers
`FUN_00708b20` and `FUN_00708bf0` are false target annotations caused by the
overlay shift. If no active background control exists, the wrapper returns
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
`(700, 950, 400, 0)`. Their correct Ghidra-located items are
`0x00890A40` and `0x00890A50`; the same-numeric `DAT_00890a80/90` annotations
are wrong.

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

Preserved `FUN_00708d60`, file `0x054EA0`, live `0x00708DA0`, returns the
active second-family line list for a side. Preserved `FUN_006f1f20`,
`FUN_006f2160`, and `FUN_006f24a0` scan those linked segments with
`FUN_006f1180` and select the nearest intersecting line. When fighter/object
flags at `+0xBB4` contain `0x800`, a candidate additionally requires line
record `+0x24 == 1`.

Preserved `FUN_006f3770`, file `0x03F8B0`, live `0x006F37B0`, maps current and
target line pointers to indices in a maximum-32-pointer BSS array, then finds
each line's side/section by walking the active lists. A side mismatch sets
per-agent state 4 and cancels the route. The runtime tables are:

| Ghidra | Live | Shape | Role |
| ---: | ---: | --- | --- |
| `DAT_008d6500` `0x008D6500` | `0x008D6540` | up to 32 line pointers | line-to-index map |
| `DAT_008d6200` `0x008D6200` | `0x008D6240` | 64 records of `0x0C` bytes | navigation adjacency records |
| `DAT_008d69d0` `0x008D69D0` | `0x008D6A10` | 64 visited bytes | recursive route search state |

Each adjacency record contains signed source line index at `+0x00`, signed
destination line index at `+0x01`, a `float` point fraction at `+0x04`, and a
route/action type byte at `+0x08`. Preserved `FUN_006f3510` and
`FUN_006f3550` recursively search the records. A chosen point is reconstructed
as `endpointA + (endpointB - endpointA) * fraction`.

Preserved `FUN_006f63a0`, file `0x0424E0`, live `0x006F63E0`, consumes the
chosen route/type and writes movement yaw near `+/- pi/2`, direction/state
flags `1`, `2`, and `0x100000`, while consulting fighter section `+0x9F6`.
Direct users of the route chooser include `FUN_006f63a0`, `FUN_006f7e70`, and
`FUN_006fb800`. This is confirmed as a line- and section-driven fighter
navigation planner. Static evidence does not yet distinguish CPU-only
navigation from a shared player/CPU section-crossing mechanism, so it is not
called an arena transition system here.

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
body beginning at preserved `FUN_006c4a90`, file `0x010BD0`; Ghidra's phantom
start at `0x006C4AD0` truncates the export. This full method performs contact
tests and animation handling, calls `FUN_006c4770` on an accepted contact,
and stores playback state at `+0x180`. When count `+0x34` reaches threshold
`+0x38`, it also calls live `0x00715F90` (preserved `FUN_00715f50`, file
`0x062090`) with `(bit(contact+0x60, 0) + 1, 0x0C, 1)`.
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
candidate advances only the background break state and event counter. This
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
calls actual trigger `FUN_006c57c0`, and emits live `0x00715F90` (preserved
`FUN_00715f50`, file `0x062090`) when `+0x48` is nonzero. In state 0 with a nonzero remaining count, it waits more
than `0x78` frames, resets model/index/playback `+0x190` and opacity, decrements
a finite count, and enters state 1. State 1 raises opacity by `0.05` per frame
to `1.0`, then clears state/opacity/flag and fixes model opacity at one.
Vtable slot `+0x0C` is live `0x006C6200`, preserved `FUN_006c61c0`, and slot
`+0x14` is live `0x006C6350`, preserved `FUN_006c6310`. Its factory begins at
preserved `FUN_006c6790`, file `0x0128D0`, live `0x006C67D0`, allocates
`0x1A0` bytes, and installs vtable `0x005DDAA0`.

`ccBgBreakObjectRebornBattle` is a distinct class at resident vtable
`0x005DD870`. Its slot `+0x08` is live `0x006CDD80`, actual preserved body
`0x006CDD40`, file `0x019E80`; this separate method also contains an explicit
`0.05` opacity rise and `>0x78` reset/reborn timer. It first runs the base
break update. Only at the final break stage does it wait 120 frames, reset
model zero/index/playback `+0x180`, decrement the finite repeat count at
`+0x194`, and fade back in. Completion clears the state and restores break
count `+0x34` to zero. Parser slot `+0x14`, actual preserved `0x006CE020`, maps
descriptor entry 9 to the repeat count. Its factory begins at
preserved `0x006CE070`, file `0x01A1B0`, live `0x006CE0B0` and allocates
`0x1A0` bytes. This proves a timed finite-or-repeating rebirth mechanic, but
the archive census further limits its construction to `S01` and `S08`. All
three S01 and all five S08 authored strings end in repeat value `-1`, the
nondecrementing repeat sentinel, so every clean instance is configured to
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
- `ccBgCrashBreakBattle` is combatant-state/proximity driven and invokes the
  base break trigger on separate paths for the two combatants. Its class method
  likewise contains no direct fighter-damage write.

Two S13-only moving props have separate mechanics. `ccHandRowShip` record 33
uses factory preserved `0x006CFCF0`, file `0x01BE30`, live `0x006CFD30`, and
update preserved `0x006CF990`, file `0x01BAD0`, live `0x006CF9D0`. Each frame
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

`ccElectricWire`, instantiated by S19, S21, and S24, is a reactive wire
simulation rather than a proved damaging hazard. Its factory is preserved
`0x006C9A50`, file `0x015B90`, live `0x006C9A90`, allocating `0x100` bytes.
Parser preserved `0x006C8490`, file `0x0145D0`, live `0x006C84D0`, resolves
three configured resources/models, establishes endpoints at `+0xD0/+0xE0`,
fixes segment count `+0x54` to 15, allocates node arrays `+0x60/+0x64/+0x68`
and collision segments `+0xF0`, and initializes per-fighter indices
`+0x94/+0x98` to `-1`.

Update preserved `0x006C8EC0`, file `0x015000`, live `0x006C8F00`, scans both
fighters. A candidate must be within about 20 units of endpoint Y, between the
endpoint X values, within 150 units of endpoint Z, and carry the matching key
at fighter `+0xBB8`; fighter state/action `+0x18E` selects a reaction case. The
helper chooses a nearest segment and writes only wire excitation, sag, and
per-fighter tracking fields. The sole fighter-side call in the class range is
`FUN_002118A0(fighter+0x1B8, 0)`, a read-only animation/frame-state predicate.
A raw JAL audit over preserved `0x006C8490..0x006C9AFF` finds no
`FUN_002335F0` and no other fighter hit/damage call. The compiled class reacts
physically/visually to fighter movement but does not directly hit or modify a
fighter. Its `ccWireHitModel` elements are also visual proxies: their vtable
has only a destructor, while resident helpers create/update/submit a
four-vertex primitive from each segment's two endpoints.

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
`0x006CD690`, maps the clean `...,5,80` tokens to five optional visual
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
integer variant/count token to resident `FUN_003A6A70`. That helper constructs
two-by-two arrays of `0x30`-byte nodes, each owning a `0xB0` model object. This
proves the construction behind the class name; its exact placement/update
policy remains outside the recovered path.

The sole S13 `ccBgMangroveBattle` derives its construction from
`ccBgLandingTreeBattle`. Derived parser preserved `0x006D3CA0`, file
`0x01FDE0`, live `0x006D3CE0`, calls base parser preserved `0x006C9B60`, then
uses the remaining `OBJ_obj_121,DMY_ki_dummy` tokens. The base tokens create
three `0xB0` elements from formatted `OBJ_obj_120_a%d` names around
`DMY_dummy_010`; the derived half creates another three from
`OBJ_obj_121_a%d` and applies the `DMY_ki_dummy` transform. This is exact
resource construction, not evidence of fighter impact.

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
   filtered contact, emit the preserved `FUN_00715f50` event, and enter state 1.
2. State 1 applies acceleration `9.8`, lowers the current transform, advances
   the break model on impact, spawns debris/effects, and enters state 2.
3. For its first 61 ticks, state 2 enables receiver `+0x170`; every eligible
   fighter in that receiver is passed to
   `FUN_002335F0(fighter, chandelier+0x260, chandelier+0x200)` and effect
   `0x1001`. It then disables the receiver, removes debris, and enters state 3.
4. State 3 restores the initial transform after break state `+0x48` clears.

An independent rebirth loop waits more than 120 frames while broken, resets
model zero, decrements a finite repeat count, and fades opacity in by `0.05`
per frame before clearing the broken state. This proves that the S21 chandelier
drops, enters fighter hit processing during a 61-frame impact window, cleans
up, can respawn when configured, and reaches the common HP path below.

A raw-overlay scan finds exactly two BTL JAL encodings of resident
`FUN_002335F0`: file/preserved/live callsites
`0x01DA7C / 0x006D193C / 0x006D197C` for the snake and
`0x01EE8C / 0x006D2D4C / 0x006D2D8C` for the chandelier. They are therefore
the only statically proved stage-object users of this explicit fighter-hit
entry in the clean BTL overlay.

### Proven stage-object hit-to-HP path

Resident `FUN_002335F0` calls ordinary-response initializer
`FUN_00232B80` at runtime/file callsite
`0x00233754 / 0x00133854`, then invokes the fighter action dispatcher
`FUN_00249640` at `0x00233834 / 0x00133934` in the same call. The initializer
selects major state 5 and arms the primary response timeline; it contains no
HP store. The immediate dispatcher sends major state 5 to
`FUN_00234DA0`, whose armed event-zero path calls `FUN_002346B0` at
`0x00234DD4 / 0x00134ED4`.

`FUN_002346B0` reads the retained attack record at fighter `+0xE54`, including
raw damage at record `+0x24` and the signed repeat/sample value at `+0x2E`.
It calls calculator `FUN_00224E30` at `0x00234A80 / 0x00134B80`, then calls
HP subtractor `FUN_00225050` at `0x00234A94 / 0x00134B94`. The subtractor writes
fighter floating-point HP at `+0x6C`: its Practice-mode subtraction store is
runtime/file `0x00225174 / 0x00125274` and floors at `0.01`; its ordinary
subtraction store is `0x002251C0 / 0x001252C0`; its zero clamp is
`0x002251DC / 0x001252DC`, which also clears fighter `+0x61` bit `0x08`.

Both stage classes build records that pass the statically visible normal
damage gates. The Hades snake initializes record `+0x24 = 0.05`, `+0x2E = 1`,
response selector `+0x2C = 0x12` and `+0x28 = 1.8` for attack states 7/8, or
selector `0x15` and `+0x28 = 1.0` for state 9. The chandelier uses
`+0x24 = 0.05`, `+0x2E = 1`, `+0x28 = 1.0`, and selector `+0x2C = 0x1E`.
These map to ordinary response families rather than the excluded
`0x42..0x49` range. The target must still be living/active, the two
attack-disable bits must be clear, and the relevant mode query must not return
6.

For both records, `FUN_002346B0` supplies calculator flags `0x122` and the
base value is exactly `0.05 / 1`. `FUN_00224E30` omits attacker-offense scaling
for these flags, then multiplies by a piecewise defender-durability factor from
clamped fighter `+0x14C`: `2-d` below 1, a linear `1 -> 0.5` segment over
`1..1.5`, and a linear `0.5 -> 0.3` segment over `1.5..3`. It multiplies that
by `1.5` when defender `+0x80` is nonzero; by
`max(0.1, 2.0 - FUN_00306C80(defender))`; and by the paired-fighter factor at
`(*(defender+0x20))+0x16C` times defender `+0x170`. The final calculator result
is clamped to `0..1` before HP subtraction. Thus the exact delta is contextual,
but its full static scaling path is established rather than untraced.

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
control cleanup, and `FUN_006c2960`, the global deregistration helper. The
export's same-numeric `FUN_006c29e0` and `FUN_006c29a0` call annotations are
shifted and wrong; live `0x006C2A20` is not called here.

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

The standalone `ccFieldCtrl` is destroyed by its parent owner, not by the
field's embedded-control teardown. Root destruction calls live `0x00709280`
(preserved `FUN_00709240`, file `0x055380`), whose owner teardown at live
`0x007093A0` dispatches `ccFieldCtrl` virtual `+0x08`, live `0x007091A0`.
That method walks the member list through live `0x00709F40` and invokes each
member's virtual destructor, reaching `ccField` live `0x007088A0` before the
standalone controller itself is released.

On the normal path, controller state 16 `FUN_001edd10` calls `FUN_001eecd0`,
clears the main runtime-object global, and proceeds to state 17. Mode 8 instead
branches directly to state 23 or 24; those handlers, `FUN_001ee1c0` and
`FUN_001ee500`, perform the same graph teardown first. State 24 does so before
releasing or switching either archive. `FUN_001eefd0`, called by the graph
destructor, invokes the BTL stage-aware controller destructor at live
`0x0076ECF0`, destroys the rest of the battle graph, and clears the manager's
fighter-pointer arrays.

Only afterward does state 17, `FUN_001edee0`, release common resources, the
four-resource BTL bundle (`shade.ccs`, `gauge.ccs`, `strmcmn.ccs`, and
`ougi.ccs`) through live `0x007691A0`, the selected stage archive through live
BTL `0x006C3160`, both players' fighter-resource handles, and the
`FUN_00207e20(slot)` stage-associated resource. The same
archive-release helper is called by central cleanup `FUN_001e9730` and by the
stage-switch path `FUN_001ee500`. This proves graph-before-archive ordering for
the orderly state16-to-17 path and for state24 switching.

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
| `FUN_006c8ec0` | `0x006C8EC0` | `0x015000` | `0x006C8F00` | `ElectricWire` reactive update |
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
| `FUN_006f63a0` | `0x006F63A0` | `0x0424E0` | `0x006F63E0` | consume navigation route/type |
| `FUN_00708760` | `0x00708760` | `0x0548A0` | `0x007087A0` | `ccField` constructor |
| `FUN_00708860` | `0x00708860` | `0x0549A0` | `0x007088A0` | `ccField` destructor |
| `FUN_00708a40` | `0x00708A40` | `0x054B80` | `0x00708A80` | field boundary-clamp wrapper |
| `FUN_00708c30` | `0x00708C30` | `0x054D70` | `0x00708C70` | field classifier wrapper |
| `FUN_00708ca0` | `0x00708CA0` | `0x054DE0` | `0x00708CE0` | field floor-profile wrapper |
| `FUN_00708d60` | `0x00708D60` | `0x054EA0` | `0x00708DA0` | active second-family line accessor |
| `FUN_00709440` | `0x00709440` | `0x055580` | `0x00709480` | construct linked camera/command/player/field graph |
| `FUN_007099e0` | `0x007099E0` | `0x055B20` | `0x00709A20` | `ccField` factory/list attachment |
| `FUN_0076e990` | `0x0076E990` | `0x0BAAD0` | `0x0076E9D0` | construct stage-tagged special-sequence aggregate |
| `FUN_0076ebd0` | `0x0076EBD0` | `0x0BAD10` | `0x0076EC10` | refresh aggregate slot-tagged auxiliary state |
| `FUN_0076ecb0` | `0x0076ECB0` | `0x0BADF0` | `0x0076ECF0` | destroy aggregate-owned backend and buffers |

### Resident lifecycle and scene functions

Resident functions do not use the BTL `+0x40` correction.

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
| `FUN_001ee500` | `0x001EE500` | `0x0EE600` | rematch/stage-switch resource path |
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

- Resolve the exact context scaling and possible source-callback override
  between the snake/chandelier raw damage `0.05` and the final HP delta.
- Establish whether the line-route planner is CPU-only or shared with player
  section crossing.
- Resolve the exact semantic role of line record `+0x2C` after the midpoint
  raycast.
