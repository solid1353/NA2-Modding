# Collision and hit-query infrastructure

Static reverse engineering of the retail NA2 (`SLPS-25837`) `BTL.BIN`
interaction-query layer. This document stops at the response-packet handoff
boundary.

## Research coverage

- **Assigned scope:** the retail NA2 `BTL.BIN` collision and hit-query
  infrastructure: spherical-volume records, registration and removal,
  query/result records, candidate production, participant filtering, the
  response-packet handoff, resident environment triangle queries, and the
  `ccBg*` stage query contracts. Analysis stops at the first common
  response-packet handoff.
- **Exploration depth:** bounded static analysis of resident `SLPS_258.37` and
  `PRG/BTL.BIN`, not an exhaustive disassembly of either; raw bytes were used
  where the preserved import omitted a body or attached a live target to a
  0x40-late label. Within each area, instruction paths, field writes, direct
  callees, and loop bounds were inspected in full unless stated otherwise:
  - manager and registries: full allocation, initialization, destruction,
    registration, cleanup, selective removal, aggregation, and frame-consumer
    bodies; constructor callers sampled.
  - resident DD* lists and spherical volumes: full list, registration, result,
    activation, all-pairs, sphere-overlap, and simple-resolver bodies; BTL
    registration callers representative.
  - sphere snapshot caches: full builder and reset and every direct
    count-field reference; computed-address callers not enumerated.
  - results, snapshots, candidate masks, and the three pair filters: full
    bodies.
  - active interaction records: full base initializer, definition copy,
    descriptor builders, installers, removal blocks, and selected computed
    constructors; structural audit of resident `0x005E0900..0x005FB94F` (166
    primary and 53 auxiliary interfaces).
  - response boundary: full wrappers, common handoff, combiner, packet
    producers, and every anchor callback in the audited table set;
    representative pending-slot paths; tag-store audit of all aligned BTL text
    words.
  - resident environment geometry and BTL triangle caches: full object
    lifecycle, packed hierarchy, both narrow phases, candidate selection,
    builder, updater, and ownership edges.
  - `ccBg*` stage queries: full resolver, clamp, height-envelope query,
    wrappers, and both direct height-wrapper caller paths.
- **Confirmed coverage:** manager and registry layouts; 0x50 spherical-volume
  and 0xA0 triangle formats; the single-pass resident DD* pair processor and
  the hierarchical broad/narrow environment queries; 0x40 results and
  snapshots; candidate-mask reductions and compatibility equations; 0x44/0x68
  interaction records, scalar construction, category-selector consumers,
  computed prefix publication, and activation lifecycles in the audited
  interface set; 0x30 response-packet producers, tag sources, anchor
  callbacks, and the common handoff; the pair filters' timeout-marker gate;
  and the stage resolver, clamp, height-envelope, and wrapper contracts.
- **Unresolved or untested:**
  - original enum, field, and resident query-list type names, and several
    opaque interaction-record fields;
  - interaction interfaces outside the audited resident table interval;
  - packet-tag writers through arbitrary rebasing or generic copies;
  - complete synthetic-record consumers and same-side reuse order;
  - any writer that sets stage line `+0x24` nonzero, and gameplay names for
    the two stage line families and each section;
  - indirect ownership relations between the BTL triangle cache and either
    the interaction manager or `ccBg*`; only direct edges were excluded.
- **Deliberate exclusions and overlap:** downstream response handling belongs
  to [Hit response](hit_response.md); damage formulas and scaling to
  [Damage](damage.md); substitution to [Substitution](substitution.md);
  projectile ownership to [Projectiles](projectiles.md); status effects to
  [Battle items and status effects](battle_items_and_status_effects.md);
  fighter consumption of collision results to
  [Target selection](target_selection.md#collision-candidates-and-routing-order);
  movement floor, side, and ceiling queries to
  [Movement and physics](movement_and_physics.md#floor-side-surfaces-and-limits);
  polygon attribute words to
  [Stage surface attributes](stage_surface_attributes.md); stage line
  layouts, builders, and the cached line attribute to
  [Stages](stages.md#line-construction), and their selected-index writers to
  [Stages](stages.md#selected-index-writers-and-neighboring-aliases); the
  timeout marker to
  [Match outcomes](match_outcomes.md#terminal-detector-and-classifier); and
  object ownership to [Battle entities](battle_entities.md).
- **Evidence limitations:** all evidence is static; no runtime allocation,
  mask transition, collision result, or stage query was captured. Arithmetic,
  field accesses, call edges, capacities, and static negative searches are
  strong evidence; gameplay names and behavior outside the inspected call
  graph are not established, and conditional uninitialized or null-input
  paths do not show that ordinary play reaches them.

## Result

The collision-facing BTL code is a staged interaction system rather than one
monolithic `check_hit` routine:

```text
BTL 0x50-byte shape/submission records
    -> resident DD* query-list services
    -> linked resident result records
    -> BTL 0x40-byte result snapshots
    -> per-object candidate masks
    -> manager per-side aggregates
    -> fighter/fighter, fighter/auxiliary, or auxiliary/auxiliary filters
    -> virtual response-packet builders
    -> common packet handoff
    -> downstream gameplay handling (outside this document)
```

The BTL layer proves registration, result traversal, snapshotting, relationship
checks, mask compatibility, response dispatch, and lifecycle cleanup. Its
resident callees additionally prove that the common 0x50-byte record is a
spherical volume and that the resident query pass performs global active-pair
enumeration, directional-mask filtering, and direct sphere/sphere overlap.
There is no evidenced separate spatial broad phase in that processor.

A second, separable `ccBg*` cluster implements stage/background boundary and
height-envelope queries. A BTL triangle-cache builder updates primitive
hierarchies registered through the resident environment chain, but no direct
edge connects those hierarchies to either the interaction manager or the
`ccBg*` stage queries. Those systems are kept separate below.

## Inputs and address conventions

Input identities and address conversion are defined in
[Retail game file identities](../game/files/file_identities.md#address-conventions);
BTL image layout and loading belong to [Overlay ABI](../runtime/overlay_abi.md).
The resident executable was inspected only for the services BTL calls.

Because preserved labels sit 0x40 below live addresses, the preserved label at
an encoded live target is frequently a false 0x40-late fragment of a different
body. Where a function is named as `export` / live, the export is the
preserved full-body label; a live-only entry means the body was recovered from
raw bytes across an omitted or split export region. Function names are
analysis labels or descriptive working names, not original developer symbols.

## Interaction manager and object registries

### Manager lifetime

| Preserved full-body export | Live | Raw | Established behavior |
| ---: | ---: | ---: | --- |
| `FUN_00776A90` | `0x00776AD0` | `0x0C2BD0` | Allocates `0x3330` bytes through resident `0x00117150`, calls live `0x00777130`, and publishes the returned manager through `iGpffffce54`. The preserved export omits the post-allocation instructions; the raw bytes contain them. |
| `FUN_007770F0` | `0x00777130` | `0x0C3230` | Initializes the manager and its embedded subsystems; installs the pointer at manager `+0x3320` and clears the two pending-result slots at `+0xB80/+0xB90`. |
| `FUN_00777460` | `0x007774A0` | `0x0C35A0` | Manager destruction path. |
| `FUN_00776AE0` | `0x00776B20` | `0x0C2C20` | Invokes the manager destructor through `manager->(+0x3320)->+0x08`, clears `iGpffffce54`, and brackets the operation with a resident-global busy bit. |
| `FUN_00778360` | `0x007783A0` | `0x0C44A0` | Full registry cleanup: destroys two primary objects and all 64 auxiliary objects, then clears pointers and generations. |

Three manager update wrappers are visible at exports `FUN_00776B80`,
`FUN_00776BD0`, and `FUN_00776C20` (live `0x00776BC0`, `0x00776C10`, and
`0x00776C60`). Each invokes three subordinate update functions when the global
manager exists. Their exact phase names are not established.

### Registry layout

| Manager offset | Layout | Established use |
| ---: | --- | --- |
| `+0x000`, `+0x008` | two `{object*, generation}` pairs | Primary fighter-side objects. |
| `+0x010` | 32 eight-byte entries | Auxiliary registry for selector/side 0. |
| `+0x110` | 32 eight-byte entries | Auxiliary registry for selector/side 1. |
| `+0x11D0`, `+0x11D4` | two `u32` | Current primary-object candidate masks. |
| `+0x11D8`, `+0x11DC` | two `u32` | OR-aggregated auxiliary candidate masks. |
| `+0xB60`, `+0xB70` | two vec4-sized temporary areas | Packet-handoff geometry inputs; a missing packet vector receives the float sentinel `10000.0` in its final word. |
| `+0xB80`, `+0xB90` | two 0x10-byte slots | Pending interaction-result records, described at the handoff boundary below. |
| `+0x3320` | pointer | Destructor/manager interface pointer used by the global release path. |

Primary registration is the full body `FUN_00778750` (export) / live
`0x00778790`, raw `0x0C4890`. It indexes the manager pair directly as
`manager + side * 8`; an occupied slot enters an assertion/fault path rather
than returning a recoverable failure. On success it writes the manager pair,
issues a generation from resident global `0x00604EE8`, and writes these object
fields:

| Primary object offset | Value |
| ---: | --- |
| `+0x0C` | manager pointer |
| `+0x120` | side/slot index |
| `+0x124` | generation |
| `+0x128` | self pointer |

A representative direct caller is `FUN_00776240` / live `0x00776280`, whose
callsite is live `0x007762C8`.

Two auxiliary insertion bodies begin at live `0x00778630` (raw `0x0C4730`)
and live `0x007786E0` (raw `0x0C47E0`). Their prologues were omitted or
misclassified by the preserved export; the displayed `FUN_00778630` and
`FUN_007786E0` labels point 0x40 into those bodies and must not be treated as
their starts.

Both bodies select the 32-entry registry as
`manager + 0x10 + object[+0x958] * 0x100`, issue a generation from the separate
resident global `0x00604EEC`, write the manager entry, and initialize:

| Auxiliary object offset | Value |
| ---: | --- |
| `+0x78` | selected registry slot |
| `+0x7C` | generation |
| `+0x80` | self pointer |

When a caller supplies an output tuple, it receives
`{slot, generation, object}`. Both generation counters skip `-1` before
issuing it and increment after a successful insertion, so `-1` remains the
vacant/invalid generation sentinel. Live `0x00778630` scans free slots from 31
down to 0; live `0x007786E0` scans from 0 up to 31. If no free slot exists,
the body returns without a status value and without modifying the object or
optional output tuple. Numerous specialized object
constructors call the latter. Their gameplay identities are intentionally not
classified here.

The high-to-low insertion has one recovered direct callsite, live
`0x007B55C4`, in `FUN_007B4D70` / live `0x007B4DB0`. The low-to-high insertion
has 21 direct callsites; live `0x0079F75C` in `FUN_0079F5B0` / live
`0x0079F5F0` is representative. These caller addresses document registration
coverage without assigning excluded object-specific ownership semantics.

`FUN_00778360` calls primary-object virtual cleanup at interface offsets
`+0x18C` and `+0x228`, and auxiliary destruction at auxiliary interface
offset `+0x08`. It writes null pointers and generation `-1` into every vacated
manager entry. This is strong registration/removal evidence independent of any
unrecovered original class names.

Selective removal is `FUN_0077CE50` (export) / live `0x0077CE90`, raw
`0x0C8F90`. It removes primaries whose object `+0x14` has bit 1 set and
auxiliaries whose object `+0x8B0` has bit 1 set, invokes their virtual teardown,
and clears the same pointer/generation pairs. `FUN_00778920` / live
`0x00778960`, raw `0x0C4A60`, calls it during the update phase reached from the
live `0x00776BC0` manager wrapper.

## Resident query-list boundary

The relevant imported resident addresses are live addresses; they do not use
the BTL `+0x40` correction.

| Resident address | Caller-visible behavior | Confidence |
| ---: | --- | --- |
| `0x001DD8D0` | Constructs a 0x24-byte query-list head. | High |
| `0x001DD920` | Destroys/resets a list head, deactivating it when needed, freeing registrations/results, and optionally freeing the head itself. | High |
| `0x001DD9D0` | Activates a list head by appending it to the resident global active-list chain; activates its registrations as well. | High |
| `0x001DDA50` | Deactivates a list head, unlinks it from the global active-list chain, deactivates its registrations, and clears per-pass head words `+0x04/+0x08`. | High |
| `0x001DDB70` | Allocates and appends a 0x34-byte registration node around a 0x50-byte spherical-volume record and two directional masks. | High |
| `0x001DDCC0` | Removes one registration from its owner list, deactivates it first when necessary, destroys/frees its owned state, and decrements the list-head registration count. | High |
| `0x001DDD80` | Returns the 1-based registration node from a list head's `+0x18` chain. | High |
| `0x001DD1A0` | Returns the 1-based 0x40-byte result from a registration node's `+0x14` chain. | High |
| `0x001DCCC0` | Activates one registration by appending it to the global active-registration chain. | High |
| `0x001DCD10` | Deactivates one registration and unlinks it from that global chain. | High |
| `0x001DD1E0` | Appends a directional 0x40-byte result to a registration and mirrors it to the owner list through `0x001DDE00`. | High |
| `0x001DDE00` | Appends the mirrored 0x40-byte result to a list head's result chain and updates its summary/count. | High |
| `0x001DE1C0` | Clears prior results, enumerates active registrations, applies the directional-mask gate, performs sphere/sphere overlap, and emits directional results. | High |
| `0x001DCA40` | Validates the result's referenced list handle through `0x001DCBF0`, then returns that handle's owner at `+0x1C`. | High |
| `0x001DCBF0` | Returns result `+0x14` only when its current generation `handle+0x20` still equals result `+0x34`; otherwise returns null. | High |
| `0x001BEBE0` | Activates or deactivates a 0x50-byte spherical-volume record in a separate resident global record chain. | High |
| `0x001BEC60` | Resolves one active 0x50 record against compatible active spheres and, when enabled, against environment triangles; returns a two-bit hit summary. | High |
| `0x001BEEB0` | Constructs a resident environment-query object of at least 0x98 bytes. | High |
| `0x001BEFA0` | Sets environment object `+0x08` and registers the object in the resident environment chain when inactive. | High |
| `0x001BF020` | Unregisters an environment object from that chain and clears its active/next state. | High |
| `0x001BEF30` | Destructor wrapper that unregisters an active environment object and optionally frees it. | High |
| `0x001BF100` | Directed segment/environment query over two vec4 endpoints; returns nearest travel distance, overwrites endpoint 2 with the hit point, or returns float `-1.0` for no hit. | High |
| `0x001C1260` | Swept-sphere/environment helper used by `0x001BEC60`; applies accepted triangle corrections to an output vec4 and returns `-1.0` when none are found. | High |

One construction family proves three adjacent 0x24-byte list heads at owner
`+0xDD0`, `+0xDF4`, and `+0xE18`. Each is fed from two-element arrays of
0x50-byte records at owner `+0xBD0`, `+0xC80`, and `+0xD30`; the arrays use a
fixed-record constructor with element size `0x50` and count 2. Callers submit
each record through `0x001DDB70` and then activate the list through
`0x001DD9D0`.

Representative BTL record producers show the same interface:

- `FUN_007A2030` (export) / live `0x007A2070`, raw `0x0EE170`, updates the
  record at primary object `+0x1070`, including words at record `+0x04`,
  `+0x10`, `+0x18`, and `+0x1C`; changes its state through `0x001BEBE0`;
  submits it to the list at object `+0xF30`; then calls `0x001DDA50`.
- `FUN_007B0090` / live `0x007B00D0`, raw `0x0FC1D0`, updates the record at
  auxiliary object `+0xB40`, copies a vec4 to record `+0x20`, submits it to
  the list at object `+0x140`, then calls `0x001DDA50`.

The corresponding auxiliary removal/rebuild body begins at export
`FUN_007AFFC0` / live `0x007B0000`, raw `0x0FC100`. The preserved import
splits its continuation at displayed `FUN_007B0000`; raw address `0x0FC160`, live
`0x007B0060`, calls `0x001DDCC0(object+0x140,
0x001DDD80(object+0x140,2))`. The body then refreshes two object-local words
and calls `0x001DD9D0` on the list. This is a representative registration-2
removal followed by list reactivation, not a separate function at the
preserved split label.

The resident bodies establish that these are spherical-volume records, though
the original class/field names remain unknown. `FUN_001BEA30` initializes one,
and both the simple active-record resolver `FUN_001BEC60` and the query-list
processor `FUN_001DE1C0` consume this layout:

| 0x50 record offset | Established use |
| ---: | --- |
| `+0x00` | active flag |
| `+0x04` | directional/receive mask, tested against another record or registration mask |
| `+0x08` | environment primitive-selection mask; zero disables the environment query |
| `+0x0C` | environment mask match mode, initialized to 1 |
| `+0x10` | reciprocal directional mask |
| `+0x14` | next pointer in the simple active-record chain |
| `+0x18` | radius, initialized to `1.0` |
| `+0x1C` | center z-bias/vertical offset |
| `+0x20..+0x2C` | center vec4 |
| `+0x30..+0x3C` | accumulated correction/result vec4 |
| `+0x40` | aggregate accepted environment-primitive flags written when `FUN_001BEC60` runs its environment branch |
| `+0x44..+0x4F` | not initialized or accessed by the inspected resident collision bodies |

The overlap calculation subtracts the two `+0x20` centers, adds the difference
of `+0x1C` to the z component, computes Euclidean length, and accepts when
`radiusA + radiusB - distance >= 0`. It then normalizes the separation vector
and produces a penetration correction. This is direct spherical-volume math,
not merely an inferred primitive name.

`FUN_001BEC60(record)` is the per-record resolver for the separate simple
active-record chain at resident head `0x006074A8` (tail `0x006074AC`, count
`0x006074A4`). It resets record `+0x30..+0x3C`, tests each other active record
with directional gate `(record+0x04 & other+0x10) != 0`, and on sphere overlap
adds a full `(penetration + 0.1)` correction to the caller's `+0x30` vec4. It
ORs the compatible counterpart masks into resident summary `0x006074D0`.

`FUN_001BEA30` initializes `+0x04/+0x08` to `0xFFFFFFFF`, `+0x0C` to 1,
radius `+0x18` to `1.0`, the center from the resident zero-vector constant,
and correction `+0x30` from the resident zero vector. It writes only through
`+0x3F`; the 0x50-byte allocation's final 0x10 bytes are not generally
constructor-initialized.

When record `+0x08` is nonzero, the same resolver clears `+0x40` and calls
`FUN_001C1260(radius, correction, effective_center, mask, 0, match_mode)`.
That helper reaches resident `FUN_001BF3C0` / `FUN_001C00B0`, which use the
same object/group/primitive AABBs but perform sphere-versus-triangle plane,
edge, and vertex tests. Accepted candidates add surface-normal correction to
record `+0x30`; `FUN_001BF7D0` reduces their primitive flags into record
`+0x40`. When `+0x08` is zero, this environment branch is skipped and
`+0x40` is not refreshed. `FUN_001BEC60` returns bit 0 for any simple sphere
overlap and bit 1 for any environment correction, so observed returns range
from 0 through 3.

The last two arguments to `0x001DDB70` become directional masks on its
registration node: argument 3 is written to node `+0x30`, and argument 4 to
node `+0x2C`. The individual mask bits are not named here.

The representative primary setup at export `FUN_007A2030` / live
`0x007A2070` selects either `(record+0x04, record+0x10) =
(0x00088900, 0x00000080)` or `(0x00044090, 0x00000800)`, sets radius
`+0x18 = 30.0` and z-bias `+0x1C = 0`, deactivates the simple record, and
passes `(record+0x10, record+0x04)` as arguments 3 and 4 to
`0x001DDB70`. It then deactivates the owner list. Thus registration setup does
not itself make either the simple-record chain or DD* list participate; those
activation steps are explicit and separable.

### Manager sphere snapshot caches

BTL also derives compact sphere snapshots from the resident query-list
registrations. The complete body is preserved as `FUN_00778250` / live
`0x00778290`, raw `0x0C4390`; displayed `FUN_00778290` is its 0x40-late split
artifact. Its effective ABI is:

```text
snapshot_spheres(manager, list, side, bank, include_inactive)
```

It selects `manager + side * 0x1020 + bank * 0x810`, then walks the list's
1-based registrations through resident `0x001DDD80`. An inactive list is
ignored unless `include_inactive` is nonzero. For each registration it follows
node `+0x24` to the 0x50-byte volume record and appends one 0x20-byte cache
entry, stopping when the shared count reaches 64:

| Cache-entry offset | Established value |
| ---: | --- |
| `+0x00..+0x0C` | record center vec4 `+0x20..+0x2C`, with record z-bias `+0x1C` added to cached z at `+0x08` |
| `+0x10` | record radius `+0x18` |
| `+0x14..+0x1F` | not written by this builder |

The four physical caches are:

| Side | Bank | Manager-relative entry array | Manager-relative count |
| ---: | ---: | ---: | ---: |
| 0 | 0 | `+0x1220` | `+0x1A20` |
| 0 | 1 | `+0x1A30` | `+0x2230` |
| 1 | 0 | `+0x2240` | `+0x2A40` |
| 1 | 1 | `+0x2A50` | `+0x3250` |

The full reset/update body is `FUN_0077E670` / live `0x0077E6B0`, raw
`0x0CA7B0`; displayed `FUN_0077E6B0` is an interior label. It zeros all four
counts before invoking primary and auxiliary update callbacks. The manager
wrapper `FUN_00776B80` / live `0x00776BC0` calls it at live `0x00776BE0`.
Full cleanup at live `0x007783A0` also zeros all four counts.

The main per-frame relationship consumer at live `0x0077D260` rebuilds the
caches after its dispatch work. Its live callsites `0x0077D848` and
`0x0077D8C0` snapshot each primary list at object `+0xF30` into bank 0 and
each auxiliary list at object `+0x140` into the bank selected by
`FUN_0077FD10` / live `0x0077FD50`; both paths pass
`include_inactive = 0`. A specialized primary path at live `0x007A2D9C`
passes 1, proving that forced snapshots of inactive lists are intentional.

Specialized object callbacks can append entries directly as well. One
representative complete body is `FUN_0082D380` / live `0x0082D3C0`, raw
`0x1794C0`: it selects side through object `+0x958`, selects a bank from
whether object `+0x948` is nonzero, copies object vec4 `+0xD40` as the center,
and writes radius `1.0`. Similar inline appenders are visible in
`FUN_00830B90` / live `0x00830BD0` and `FUN_00831DB0` / live `0x00831DF0`.
Unlike the generic builder, these inline stores have no visible `count < 64`
check. Their surrounding state gates may enforce the capacity invariant, but
that has not been proved; therefore 64 is a proven generic-builder limit and
physical array capacity, not a universal checked precondition at every writer.

These snapshots are genuine query inputs, not merely debug state. For example,
`FUN_006F1380` / live `0x006F13C0`, raw `0x03D4C0`, scans the selected
auxiliary cache, shifts cached x or z by `0.9 * radius` according to an
object-local four-way selector, computes distance through resident
`0x001806F0`, and accepts when
`distance < 1.8 * cached_radius + query_radius`. This establishes a
registration-derived proximity-query cache. No inspected call connects that
distance test to the central mask dispatcher or the resident DD* pair
processor, so classifying these four caches as the main collision broad phase
would exceed the evidence. A program-wide search for direct accesses to the
four count locations found only two consumer bodies—live `0x006F13C0` and
live `0x006F16D0`, both distance/proximity tests. The remaining direct
references are builders, the specialized appenders above, reset, and cleanup;
indirect accesses cannot be excluded by that search.

### Resident list and registration layouts

The 0x24-byte list head is:

| Offset | Established use |
| ---: | --- |
| `+0x00` | active flag (`0x001DD9D0` sets 1; `0x001DDA50` sets 0) |
| `+0x04` | OR of emitted result counterpart/category masks (`result+0x04`) |
| `+0x08` | emitted list-level result count |
| `+0x0C` | registration count |
| `+0x10` | next active list |
| `+0x14` | list-level result chain, freed before a new pass |
| `+0x18` | first 0x34-byte registration node |
| `+0x1C` | caller-owned gameplay/object pointer returned by `0x001DCA40` |
| `+0x20` | nonzero generation allocated by `0x001DD8D0` |

The resident global active-list state is fully addressable:

| Resident address | Established use |
| ---: | --- |
| `0x006075B0` | active-list count |
| `0x006075B4` | first active 0x24-byte list head |
| `0x006075B8` | last active list head |
| `0x006075BC` | generation source used by `0x001DD8D0` for list `+0x20` |

`0x001DD9D0` is the list-level activation operation. If the head is not
already active, it sets head `+0x00 = 1`, clears `+0x10`, appends the head to
the chain at `0x006075B4..0x006075B8`, and increments `0x006075B0`. If the
head already owns registrations through `+0x18`, it calls resident
`FUN_001DCE20`, which activates the eligible registration chain. Conversely,
`0x001DDA50` clears the active flag, unlinks the head from that global chain,
decrements `0x006075B0`, calls resident `FUN_001DCFA0` to deactivate the
head's registration chain, and clears head result-summary words `+0x04/+0x08`.
This establishes a two-level lifecycle rather than a single undifferentiated
registry.

`0x001DDB70` allocates this 0x34-byte registration node:

| Offset | Established use |
| ---: | --- |
| `+0x00` | active-registration flag/state |
| `+0x04` | activation-eligibility flag, initialized to 1 and required by bulk list activation |
| `+0x08` | owns-record flag when `0x001DDB70` had to allocate the 0x50 record |
| `+0x0C` | OR-accumulated result-category word |
| `+0x10` | result count |
| `+0x14` | first 0x40-byte result |
| `+0x18` | next globally active registration |
| `+0x1C/+0x20` | previous/next registration within its owner list |
| `+0x24` | 0x50-byte spherical-volume record pointer |
| `+0x28` | owner list-head pointer |
| `+0x2C/+0x30` | two directional compatibility/category masks |

Active registration nodes have their own resident global state, separate from
the list-head chain:

| Resident address | Established use |
| ---: | --- |
| `0x006075A4` | active-registration count |
| `0x006075A8` | first active 0x34-byte registration node |
| `0x006075AC` | last active registration node |

`0x001DCCC0` appends one eligible node to this chain and marks node `+0x00`
active; `0x001DCD10` unlinks one active node and clears that state. The
list-chain helpers `FUN_001DCE20` and `FUN_001DCFA0` apply those operations
across a list's registration chain; `FUN_001DCE20` skips nodes whose `+0x04`
is not 1. `FUN_001DE1C0` enumerates this active-registration chain, not the
active-list chain, when producing pair results.

When no record pointer is supplied, `0x001DDB70` allocates 0x50 bytes,
initializes them with `0x001BEA30`, and records ownership at node `+0x08`.
`0x001DDCC0` repairs the list's doubly linked registration chain through node
`+0x1C/+0x20`, invokes the registration destructor with a free flag, and
decrements list `+0x0C`. If node `+0x00 == 1`, it first calls the resident
registration-deactivation helper `FUN_001DCD10`, which removes the node from
the global active-registration chain.

BTL's auxiliary-object initializer is `FUN_0077F2B0` (export) / live
`0x0077F2F0`, raw `0x0CB3F0`. It makes the owner linkage explicit by writing
the object self pointer to list-head owner fields `+0x15C`, `+0x180`, `+0x1A4`,
and `+0x1C8`, which are respectively `+0x1C` within list heads at `+0x140`,
`+0x164`, `+0x188`, and `+0x1AC`. It also writes object class word `+0x0C = 5`.
This explains both resident `0x001DCA40` owner resolution and BTL's repeated
class-5 tests without requiring an inferred ownership convention.

The primary constructor beginning at export `FUN_007853D0` / live
`0x00785410`, raw `0x0D1510`, calls `0x001DD8D0` on five heads at live call
sites `0x00785800`, `0x0078580C`, `0x00785818`, `0x00785824`, and
`0x00785830`, corresponding to primary offsets `+0xF30`, `+0xF54`, `+0xF78`,
`+0xF9C`, and `+0xFC0`. That constructor does not install the object pointer
in those heads' owner field. In contrast, the auxiliary initializer does so
explicitly. Together with the classifiers below, this supports an observed
null-owner versus auxiliary-owner tagging convention; it does not prove that
every null owner elsewhere in the engine denotes a primary object.

### Resident pair processor

`FUN_001DE1C0` is called from resident frame dispatcher `FUN_001F03E0`. It
clears prior results, walks globally active registration nodes belonging to
different owner lists, rejects inactive records, then applies the directional
mask gate:

```text
(A.node.mask2C & B.node.mask30) != 0
or (A.node.mask30 & B.node.mask2C) != 0
```

For a mask-compatible pair it immediately performs the spherical distance and
radius-sum test described above. On overlap, the two directional-mask results
choose one-sided full correction or reciprocal half corrections, and
`FUN_001DD1E0` / `FUN_001DDE00` append 0x40-byte directional result records.
The zero-distance case chooses a signed separation axis before correction.

For each emitted direction, the receiving registration's record `+0x30`
accumulates the correction vector. If both cross-mask directions are enabled,
each side receives half of the separation in opposite directions and each
gets a result. If only one cross-mask direction is enabled, the corresponding
receiver gets the full correction and the single result. `0x001DD1E0`
increments registration `+0x10` and ORs the counterpart mask into registration
`+0x0C`; its call to `0x001DDE00` performs the analogous update at list-head
`+0x08/+0x04`.

This is an all-pairs active-registration traversal followed by mask filtering
and direct sphere/sphere overlap. No spatial tree, grid, sweep, AABB rejection,
or separate geometry broad phase appears in this processor. It is therefore
accurate to describe the enumeration/mask gate and spherical overlap as one
resident pair-processing pass, not as a proven broad-phase/narrow-phase split.
Fighters also read these resident results directly; that consumer belongs to
[Target selection](target_selection.md#collision-candidates-and-routing-order).

### Resident segment/environment broad and narrow phases

The separate resident `FUN_001BF100` path does have an evidenced hierarchical
broad/narrow structure. Its effective interface is:

```text
distance = segment_query(start_vec4, end_vec4,
                         mask_a, match_mode_a,
                         mask_b, match_mode_b)
```

The environment-object lifecycle is separate from the 0x24/0x34 DD* query
lists. `FUN_001BEEB0` initializes the object, `FUN_001BEFA0(object, mode)`
stores `mode` at `+0x08` and appends an inactive object to the global chain,
and `FUN_001BF020` unlinks it. Established object fields are:

| Environment-object offset | Established use |
| ---: | --- |
| `+0x00` | active flag |
| `+0x04` | next environment object |
| `+0x08` | registration-supplied transform mode/flag; nonzero enables local-space transformation |
| `+0x0C` | pointer to aggregate/group/primitive bounds data |
| `+0x10..+0x3F` | local-to-world transform consumed for candidate point/normal output |
| `+0x40..+0x4F` | object origin/translation vec4 |
| `+0x50..+0x8F` | second transform initialized as a 4x4 identity; the collision query consumes its first three vec4 rows as world-to-local and supplies a fixed homogeneous row |
| `+0x90` | enabled-group bit mask, initialized to `0xFFFFFFFF` |
| `+0x96` | halfword reset on unregister; exact role unknown |

Object `+0x0C` points to a packed variable-length hierarchy. Its root begins
with AABB minima at `+0x00/+0x04/+0x08`, maxima at
`+0x10/+0x14/+0x18`, group count at `+0x1C`, and the first group at `+0x20`.
Each group repeats that 0x20-byte header with a primitive count at group
`+0x1C`, followed by `count` consecutive 0xA0 primitives. The next group
therefore begins at `current_group + 0x20 + count * 0xA0`. This is a packed
AABB hierarchy, not a pointer tree.

It clears candidate count `0x006074C8`, copies both endpoints to scratch, and
walks the environment-object chain with active count `0x006074B0`, head
`0x006074B4`, and tail `0x006074B8` through object `+0x04`.
`FUN_001BF230` subtracts object
origin `+0x40`, optionally transforms
the segment through the object matrix when object `+0x08` is nonzero, computes
the local segment AABB, and carries the two query masks forward.

`FUN_001BF8C0` then performs these progressively narrower tests:

1. segment AABB against the object's aggregate AABB;
2. an object `+0x90` group-enable bit plus segment AABB against that group's
   AABB;
3. segment AABB against each 0xA0-byte primitive AABB;
4. the two caller-selected mask predicates against primitive flags `+0x0C`;
5. directed plane crossing followed by three edge half-space tests with a
   `-0.001` tolerance.

The final arithmetic is triangle intersection: primitive vertices are at
`+0x20/+0x30/+0x40`, plane normal at `+0x50`, and the three edge-test vectors
at `+0x60/+0x70/+0x80`. Accepted hits become 0x60-byte candidate records. The
fields established by writes and `FUN_001BF620` are:

| Candidate offset | Established content |
| ---: | --- |
| `+0x00..+0x0C` | world hit-point vec4; copied back to query endpoint 2 |
| `+0x10..+0x1C` | normalized world-space surface direction/normal |
| `+0x20` | segment travel distance used to rank candidates |
| `+0x24` | written only by the swept-sphere narrow phase with branch-class value 1, 2, or 3; the segment path does not initialize it |
| `+0x28` | written only by the swept-sphere narrow phase with a feature selector observed from 0 through 3; exact names are unproved |
| `+0x2C` | not written by either inspected narrow phase, although the winner copier transfers it |
| `+0x30` | environment-object pointer |
| `+0x34..+0x3C` | not written by the inspected narrow phases and deliberately skipped by the winner copier |
| `+0x40` | group index |
| `+0x44` | primitive index within the group |
| `+0x48` | primitive `+0x0C` flags |
| `+0x4C` | not written by either inspected narrow phase, although the winner copier transfers it |
| `+0x50..+0x5C` | primitive-local plane-normal vec4 |

The first 32 candidates occupy 0x60-byte slots beginning at `0x0061EAA0`.
Both inspected narrow phases send every subsequent accepted hit to the single
overflow scratch slot at `0x0061F640`; their total count still increments, but
`FUN_001BF620` clamps its selection count to 32. Excess hits can therefore
overwrite one another; even an overflow hit closer than every retained hit
cannot win. `FUN_001BF620` scans the retained candidates in ascending index
order and replaces the selected index on `candidate_distance <= best_distance`
at `0x001BF670..0x001BF680`. Equal distances therefore select the last such
candidate among the first 32. It publishes the selected fields at resident
globals `0x0061F6A0..0x0061F6FC`; the caller `FUN_001BF100` invokes that
publisher at `0x001BF1CC`, copies the published point to endpoint 2 at
`0x001BF1DC/0x001BF1E0`, and loads the published distance for return at
`0x001BF1E8`. With no candidates, the wrapper instead returns `-1.0` at
`0x001BF1F4/0x001BF1F8`, leaving endpoint 2 and the public record unchanged.

The publisher copies
`+0x24..+0x2C` and `+0x4C` even though the segment path does not initialize
them, while skipping `+0x34..+0x3C`; consumers must not assume a fully fresh
0x60-byte public record. Side-channel word `0x0061F6E8`, repeatedly read by
BTL, is specifically the chosen primitive's flags, not an unspecified query
token. The flag word's authored and geometric parts belong to
[Stage surface attributes](stage_surface_attributes.md#authored-word-and-geometric-class),
and fighter floor, side, and ceiling probes that consume it to
[Movement and physics](movement_and_physics.md#floor-side-surfaces-and-limits).

## Query-result and snapshot records

BTL traverses resident results by calling `0x001DDD80(list, index)` to select a
registration and then `0x001DD1A0(registration, 1)`. Results form a linked
chain through result `+0x30`.
The BTL-visible fields are:

| Result offset | Established use |
| ---: | --- |
| `+0x00` | receiving registration's `+0x30` mask |
| `+0x04` | counterpart registration's `+0x30` mask; exact value used for BTL bucket classification |
| `+0x08` | counterpart sphere radius |
| `+0x0C` | center-to-center distance used by the accepted overlap test |
| `+0x10` | `max(distance - counterpart radius - receiver radius, 0)`; normally zero for a result emitted by this overlap pass |
| `+0x14` | counterpart owner list-head/handle pointer |
| `+0x20..+0x2C` | counterpart effective-center vec4; z includes its record `+0x1C` bias |
| `+0x30` | next-result pointer |
| `+0x34` | snapshot of counterpart list generation `handle+0x20` |

`0x001DD1E0` first calls `0x001DDE00` when the receiving registration has a
non-null owner list at registration `+0x28`, then allocates the
registration-local copy. Consequently, list head `+0x14` and registration
`+0x14` contain separate 0x40-byte records with the same observed payload,
not two links to one allocation.

`FUN_00785300` (export) / live `0x00785340`, raw `0x0D1440`, copies those
fields into a 0x40-byte BTL snapshot, stores `0x001DCBF0(result)` at snapshot
`+0x30`, and caches the referenced list handle's generation word `handle+0x20`
at snapshot `+0x34`.

The snapshot resolver is a live-only body at `0x007853C0`, raw `0x0D14C0`:

```text
cached = snapshot[+0x30]
if cached == 0:                         return 0
if cached[+0x20] != snapshot[+0x34]:    return 0
return cached[+0x1C]
```

The generation check prevents a stale snapshot from resolving through a
reused resident list handle. The preserved `FUN_007853C0` symbol is a later
zero-return stub created by the import shift, not this body.

Two classifier functions consume the same category set:

| Result `+0x04` | Snapshot bucket | Additional distinction |
| ---: | ---: | --- |
| `0x80000` or `0x40000` | 3 or 6 | Bucket 3 when owner resolution fails; bucket 6 for a qualifying resolved owner. |
| `0x8000` or `0x4000` | 1 | None. |
| `0x800` or `0x80` | 0 or 4 | Bucket 0 when owner resolution fails; bucket 4 for a qualifying resolved owner. |
| `0x200` or `0x20` | 7 | None. |
| anything else | none | Result ignored by these classifiers. |

The auxiliary classifier is `FUN_0077F5B0` / live `0x0077F5F0`, raw
`0x0CB6F0`; it selects bucket 6 or 4 exactly when resident `0x001DCA40`
returns nonzero, otherwise bucket 3 or 0. The primary classifier is
`FUN_0078E0D0` / live `0x0078E110`, raw `0x0DA210`; it selects the higher
bucket only when the resolved object's word `+0x0C` equals 5. Each accepted
result overwrites the corresponding 0x40-byte snapshot, so these functions
preserve the last accepted result in a bucket rather than an unbounded result
array.

## Candidate-mask production

### Primary objects

`FUN_0078E330` (export) / live `0x0078E370`, raw `0x0DA470`, refreshes four
families of snapshots and produces the primary candidate mask at object
`+0xFE4`. The list/result-mask families visible in this routine are:

| List head | Result/category word | Snapshot block | Exact source-to-output reductions at `+0xFE4` |
| ---: | ---: | ---: | --- |
| `+0xFC0` | `+0xFC4` | `+0xA80` | source `0x20/0x200 -> 0x80000000`; source `0x80/0x800 -> 0x40000000` |
| `+0xF54` | `+0xF58` | `+0x840` | `0x20/0x200 -> 0x08000000`; `0x80/0x800 -> 0x00000001`; `0x40/0x400 -> 0x20000000` |
| `+0xF30` | `+0xF34` | `+0x600` | `0x40000/0x80000 -> 0x00020000`; `0x80/0x800 -> 0x40` when the generation-checked bucket-4 owner has class word `+0x0C == 5`, and `-> 0x08` when bucket 0 is nonempty; `0x10/0x100 -> 0x10`; `0x4000/0x8000 -> 0x20` |
| `+0xF9C` | `+0xFA0` | `+0xCC0` | `0x40000/0x80000 -> 0x00080000`; `0x80/0x800 -> 0x00100000` |

The output bits are derived from exact pairs in the source result/category
words and, for `0x40`, from a generation-checked owner relation. This table
records the produced masks without assigning gameplay names to them.

### Auxiliary objects

`FUN_0077F760` / live `0x0077F7A0`, raw `0x0CB8A0`, refreshes three query
families and writes the auxiliary candidate mask at object `+0x1D0`:

| List head | Result/category word | Snapshot block | Exact source-to-output reductions at `+0x1D0` |
| ---: | ---: | ---: | --- |
| `+0x188` | `+0x18C` | `+0x430` | source `0x80/0x800 -> 0x10000` for a resolved class-5 owner, and `-> 0x8000` when bucket 0 is nonempty |
| `+0x140` | `+0x144` | `+0x1F0` | `0x40000/0x80000 -> 0x40000`; `0x10/0x100 -> 0x80`; `0x80/0x800 -> 0x800` for a class-5 owner and `-> 0x400` when bucket 0 is nonempty; `0x4000/0x8000 -> 0x100` |
| `+0x1AC` | `+0x1B0` | `+0x670` | `0x80/0x800 -> 0x100000`; `0x40000/0x80000 -> 0x80000` |

Some output bits require a nonempty snapshot bucket; others require a resolved
owner with object class word `+0x0C == 5`. The first two auxiliary families
also suppress same-side owner relations by comparing resolved owner
`+0x958` with the current auxiliary `+0x958`. The mask is therefore not merely
a copy of resident category bits: it is BTL's higher-level candidate summary.

### Manager aggregation and frame caller

`FUN_0077CFD0` / live `0x0077D010`, raw `0x0C9110`, is the manager aggregator.
When its battle-state gate accepts and manager flag `+0xA74` bit 0 is clear,
it:

1. rebuilds each present primary object and copies `object+0xFE4` to manager
   `+0x11D0/+0x11D4`;
2. rebuilds every present auxiliary object and ORs `object+0x1D0` into manager
   `+0x11D8/+0x11DC` by side.

When the gate rejects, it zeros manager and object candidate masks. The
full-body frame wrapper `FUN_0077CE00` / live `0x0077CE40`, raw `0x0C8F40`,
calls the aggregator at encoded live `0x0077D010`, processes pending manager
results through encoded live `0x0077BA90`, then calls the main interaction
consumer at live `0x0077D260`.

The consumer is `FUN_0077D220` (export) / live `0x0077D260`, raw `0x0C9360`.
It clears per-object result flags, calls the central dispatcher with its fourth
argument zero, consumes or clears candidate masks based on the result, and
then continues into later gameplay handling. This document does not follow
that later handling.

## Active interaction records

### Definition-to-runtime copy

`FUN_00772AB0` (export) / live `0x00772AF0`, raw `0x0BEBF0`, constructs one
runtime interaction record from a fixed definition. Definition indexing proves
a 0x44-byte source stride; runtime indexing proves a 0x68-byte destination
stride. It first calls resident base initializer `0x00210B10(destination)`.

The resident initializer is a complete 0xA8-byte body at
`0x00210B10..0x00210BB7` (resident addresses are not shifted). It writes the
same opaque resident pointer to runtime `+0x00/+0x04/+0x08`, then establishes
these directly observed defaults before the BTL constructor applies its
definition values:

| Runtime field | Resident default |
| ---: | ---: |
| `u16 +0x0C/+0x0E` | `0`, `1` |
| `u32 +0x10/+0x14` | `1`, `0` |
| `s8 +0x18`, bytes `+0x19/+0x1A` | `-1`, `0`, `0` |
| words `+0x1C/+0x20/+0x24` | `0` |
| float `+0x28` | `1.0` |
| byte `+0x2C/+0x2D`, `u16 +0x2E` | `0`, `1`, `1` |
| `u16 +0x30/+0x32` | `0x7FFF`, `0x7FFF` |
| words `+0x34/+0x38` | `0`, `0` |
| float `+0x3C` | `1.5` |
| eight `u16 +0x40..+0x4E` | all `0xFFFF` |
| word `+0x50` | `0` |

In particular, the 16-byte definition copy into runtime `+0x40..+0x4F`
replaces eight sentinel-initialized halfword slots. It is therefore not
evidence for a vec4 or shape record; the slots' exact semantics remain
unrecovered.

| Definition source | Runtime destination | Copy/initialization behavior |
| ---: | ---: | --- |
| `+0x00` | `+0x04` | word copy |
| `+0x08` | `+0x10` | word copy |
| `+0x0C` | `+0x14` | word copy |
| `+0x10` | `+0x56` | `u16` copy |
| `+0x12` | `+0x54` | `u16` copy |
| `+0x14` | `+0x2C` | low byte of signed 16-bit source |
| `+0x16` | `+0x2D` | low byte of signed 16-bit source |
| `+0x18` | `+0x28` | word copy |
| `+0x1C` | `+0x5C` | word copy |
| `+0x20` | `+0x60` | word copy; used as a compatibility mask by filters |
| `+0x24` | `+0x64` | word copy; used as a compatibility mask by filters |
| `+0x2C` | `+0x2E` | `u16` copy |
| `+0x2E` | `+0x30` | `u16` copy |
| `+0x30` | `+0x32` | `u16` copy |
| `+0x32..+0x41` | `+0x40..+0x4F` | 16-byte copy |

The constructor clears runtime `+0x30`, `+0x32`, `+0x54`, `+0x58`, `+0x5C`,
`+0x60`, and `+0x64` before applying source values. Builders separately fill
runtime float `+0x24`; this is not part of the constructor's copy sequence:

| Builder | Established runtime `+0x24` construction |
| --- | --- |
| Auxiliary live `0x00780C60`, raw `0x0CCD60` | `definition.float28 * auxiliary.floatAE0`. Its helper live `0x00781040`, raw `0x0CD140`, consists of `lwc1 f0,0xAE0(a0); jr ra; nop`. The preserved import defines no function at its display address `0x00781000`; the empty displayed `FUN_00781040` is a different, 0x40-late location. |
| Primary live `0x007878B0`, raw `0x0D39B0` | `definition.float28 * nested_object.float24`. When byte `+0x389` is nonzero and resident `0x003083A0` returns nonzero for the pointer stored at primary `+0x31C`, the builder follows that pointer and then its `+0xA4C` pointer to the multiplier object. A zero helper result or a zero `+0x389` uses a null pointer before the `+0x24` load. The raw branch therefore does not supply a neutral multiplier fallback. |

The primary selection/multiply instructions are live `0x0078798C..0x007879DC`,
raw `0x0D3A8C..0x0D3ADC`; the multiply and result store are specifically live
`0x007879D8/0x007879DC`. Resident `0x003083A0`, ELF
file `0x2084A0`, returns 1 only when its argument and the word at
`gp-0x339C` are both nonzero, otherwise 0. Its instructions through
`0x003083C8` do not dereference the argument or check a type or marker.
These observations establish the construction arithmetic and
pointer path only; downstream interpretation
of record `+0x24` belongs to [hit response](hit_response.md) and is not repeated
here.

The compatibility uses of runtime `+0x60/+0x64` and the category-like use of
byte `+0x2C` are established here. The following auxiliary consumer also
recovers how two previously opaque halfwords choose that byte; their original
gameplay names remain unknown.

### Selected runtime-field consumers

Auxiliary updater live `0x00780510` reads the active descriptor's record pointer
at object `+0x920`; its continuation was read from raw bytes. At live
`0x007806D0..0x007806E4`, it loads record `s16 +0x56`: value 0 selects live `0x007806F4`, value 1 selects live `0x007809A4`, and other values
skip both construction branches and reach the common descriptor-end check.
This is a selector for two record-update forms, not proof of an original enum.

| Selected field | Observed collision-facing use |
| --- | --- |
| runtime `s16 +0x54` | Alternate source for runtime category byte `+0x2C`; `lh` followed by `sb` at live `0x00780730/0x00780734` and `0x007809F0/0x007809F4` retains only its low byte. |
| descriptor `s16 +0x3E` (object `+0x93E`) | Saved original category source, copied back with `lh`/`sb` at live `0x00780720/0x00780724` and `0x00780A00/0x00780A04`. The builder originally obtained it by sign-extending record byte `+0x2C`. |
| runtime `s16 +0x56 == 0` | Uses the saved original category when incremented descriptor counter `+0x30` equals saved `s16 +0x24`; otherwise uses the alternate `+0x54` category. |
| runtime `s16 +0x56 == 1` | Uses signed halfword `+0x95A` of the entity at context `+0x44` only when context `+0x48` is zero; otherwise uses zero. A zero result restores the saved category, clears the prepared byte, and sets record `+0x2E = 1`, `+0x30/+0x32 = 0x7FFF`; a nonzero result uses the alternate category. |

The record pointer is **reloaded through the descriptor**, rather than kept as
an immutable construction result. Both branches pass the context, first-bank
header, and record to auxiliary interface slot `+0x4C`, then reload descriptor
`+0x20` and write its record float `+0x24`, call the resident-submission bridge
live `0x00780E00`, and invoke slot `+0x50`. The callback sites are live
`0x00780750/0x00780820` and `0x00780A54/0x00780A94`. Consequently, the order of
category construction, callback, scalar write, submission, and callback is
established, but effects of an unresolved callback cannot be inferred from the
base builder. The base table's slots `+0x4C/+0x50` select verified no-op leaves
at live `0x00780C50/0x00780C40`; unresolved effects concern derived targets.
The bridge copies exactly the first `0x54` bytes to scratch;
record halfwords `+0x54/+0x56` lie outside that copy even though their selected
category at `+0x2C` lies inside it. Later application of the submitted prefix
belongs to [hit response](hit_response.md).

The updater's terminal block clears the active header and descriptor state,
including its saved category/scalar, as described below. It does not clear or
free the record allocation at that block. Its earlier gates can return before
the counter increment or category rewrite, so these stores do not occur on
every update. The auxiliary path is confirmed; equivalent semantics for every
primary or derived callback, selector values outside 0/1, the original field
names, and complete writers of `+0x54/+0x56` remain unresolved.

### Computed construction and prefix publication

An auxiliary update path constructs records without calling the 0x44-definition
copy. Full export `FUN_0082FDF0`, live `0x0082FE30`, uses object `+0x958` as
the side index and object `s16 +0xBD8` as its branch selector. Raw bytes through
live `0x00830264` establish the complete producer, including these computed
destinations:

| Selector | Live destination | Selected writes after resident `0x00210B10` |
| ---: | --- | --- |
| `0x93` | `0x008DC4D0 + side * 0x54` | 0x54-byte prefix: word `+0x04` receives the literal resource-name pointer, `+0x10 = 1`, `+0x14 = 0xC000`, float `+0x24 = auxiliary.floatAE0`, byte `+0x2C = 0x10`, halfword `+0x2E = 1`; object `+0xB2C = 4`. |
| `0x93` | `0x008DC400 + side * 0x68` | Extended record: clears `+0x54/+0x58/+0x5C/+0x60/+0x64`; also clears `u16 +0x48`, writes `+0x14 = 0xC000`, `+0x24 = auxiliary.floatAE0`, `+0x2C = 0x10`, and `+0x2E/+0x30/+0x32 = 1`. |
| `0x31` | `0x008DC900 + side * 0x68` | Same extended-field clears and `u16 +0x48 = 0`; writes `+0x14 = 0xC000`, `+0x24 = auxiliary.floatAE0`, word `+0x28 = 0`, byte `+0x2C = 2`, `+0x2E = 5`, and `+0x30/+0x32 = 1`. |
| `0x3B` | `0x008DCDA0 + side * 0x68` | Same extended-field clears; writes `+0x14 = 0xC000`, `+0x24 = auxiliary.floatAE0`, `+0x2C = 0x10`, and `+0x2E/+0x30/+0x32 = 1`. |

This producer has a concrete callback edge. Resident table `0x005E8A20` slot
`+0x10` publishes live `0x00830AD0`. Its six-way jump table at live
`0x008CDB30` selects `0x00830B0C` for object `+0xBDC == 0`; that path invokes
auxiliary slot `+0x98` and calls the producer at `0x00830B30`. The table's
literal RTTI name is `ccSkillKSM000`, through live descriptor `0x008CF120`
and string `0x008BBA78`. This identifies the encoded table, not a player-facing
move or proof that a particular instance reaches each selector.

The prefix has an evidenced publication path in live `0x00831DF0`, resident
table slot `+0x18`. It requires object `+0xBDC == 3`, the pointed structure
`*(object+0xB04)+0x6C > 1`, an accepted object `+0x90` selector, and nonzero
list result count `+0x148`; the earlier branches bypass the publication if
those gates fail. At live `0x00831F90..0x00832008`, it selects the 0x54-byte
prefix above and a destination `0x008DB030 + side * 0x68`, runs the resident
initializer on the destination, clears its extended fields, then copies
exactly `0x54` bytes. At `0x00832010..0x00832054`, it clears first-bank
descriptor accumulators, publishes that destination at object `+0x920`,
stores object `+0x990` as context `+0x91C`, snapshots the category/scalar and
`+0x2E`, forces record `+0x2E = 1`, and sets prepared byte `+0x940 = 1`.
The ordinary activation slot subsequently consumes this descriptor as
[documented below](#active-descriptor-headers); reaching preparation does not
prove that the ordinary updater's separate activation gates accept it.

Neither this prefix copy nor its explicit extended-field clears writes runtime
halfword `+0x56`. The resident initializer also stops before it. The fresh
overlay's BSS clear establishes initial storage contents, but this individual
publication does not establish a fresh value for a reused record's `+0x56`.
The global storage's overlay lifetime belongs to
[overlay ABI](../runtime/overlay_abi.md#fun_00100270-cache-bss-constructors).
The category byte `record+0x2C` is still distinct from the response tag getter's
object byte `+0xAE5`; no inspected store or copy joins those two fields.

There is also a concrete shared destination: primary producer live
`0x0082F260`, selector `s16 +0x10D8 == 0x31`, initializes the same
`0x008DC900 + side * 0x68` address, with its side read from primary `+0x350`.
Its continuation at live `0x0082F790..0x0082F860` writes category 2 and
`+0x2E = 1`, rather than the auxiliary producer's 5, and supplies its own
resource pointer, mask, and scalar source. This proves aliasing between those
selected constructors; it does not prove their ordering, simultaneous reachability,
or a concurrent overwrite. Complete consumers and cleanup of the other extended
destinations, additional pointer-table aliases, and instance-level reuse remain
unresolved. Broader object behavior is outside this document.

### Active descriptor headers

Primary and auxiliary objects use parallel active-record headers:

| Relative header field | Primary absolute | Auxiliary absolute | Established use |
| ---: | ---: | ---: | --- |
| `+0x00` | `+0x200` | `+0x900` | header self pointer installed on activation, cleared on removal |
| `+0x04` | `+0x204` | `+0x904` | activated context copied from descriptor `+0x1C`, cleared on removal |
| `+0x08` | `+0x208` | `+0x908` | active runtime-record pointer |
| `+0x0C` | `+0x20C` | `+0x90C` | flags; bit 0 is required for filters to treat the record as active |
| `+0x10` | `+0x210` | `+0x910` | runtime-record pointer in the 0x44-byte active descriptor |
| `+0x14` | `+0x214` | `+0x914` | definition pointer |
| `+0x18` | `+0x218` | `+0x918` | signed definition index |
| `+0x1C` | `+0x21C` | `+0x91C` | context/token |
| `+0x20` | `+0x220` | `+0x920` | runtime-record pointer repeated by builder |
| `+0x24` | `+0x224` | `+0x924` | saved runtime `u16 +0x2E`; builder forces runtime `+0x2E = 1` |
| `+0x28..+0x34` | `+0x228..+0x234` | `+0x928..+0x934` | cleared builder fields |
| `+0x38` | `+0x238` | `+0x938` | snapshot of runtime record `+0x24` |
| `+0x3C` | `+0x23C` | `+0x93C` | runtime record `u16 +0x54` |
| `+0x3E` | `+0x23E` | `+0x93E` | sign-extended runtime record byte `+0x2C` |
| `+0x40` | `+0x240` | `+0x940` | builder writes 1 |

The full descriptor builders are `FUN_00787870` / live `0x007878B0`, raw
`0x0D39B0`, for primary objects and `FUN_00780C20` / live `0x00780C60`, raw
`0x0CCD60`, for auxiliary objects. `FUN_00780280` / live `0x007802C0`, raw
`0x0CC3C0`, is a representative explicit-definition producer: after selecting
the definition/runtime entries and building the descriptor, it sets auxiliary
`+0x941 = 1` and ORs candidate mask `+0x1D0` with `0x80`.
`FUN_007803C0` / live `0x00780400`, raw `0x0CC500`, builds a synthetic/default
record with byte `+0x2C = 0x12`, submits it through live `0x00780E00`, and
invokes auxiliary virtual callback `+0x44`. Live `0x00780E00` (full export
`FUN_00780DC0`, raw `0x0CCF00`) is a resident-submission bridge, not the active
descriptor installer: it mutates runtime-record words `+0x10/+0x14`, derives
auxiliary `+0xAD8` from record `+0x30`, copies a 0x54-byte record prefix to
scratch `0x008DAFD0`, and calls resident `0x00233110`. Adjacent gameplay
arithmetic is outside this document.

Both activation edges use raw-only leaves omitted from the preserved export. Each wrapper first requires the prepared-descriptor byte at header
`+0x40`, then passes the header, descriptor context `+0x1C`, and descriptor
runtime-record pointer `+0x20` to its installer:

| Path | Wrapper export/live/raw | Installer callsite live | Installer live/raw |
| --- | --- | ---: | ---: |
| primary | `FUN_00787820` / `0x00787860` / `0x0D3960` | `0x00787884` | `0x00789600` / `0x0D5700` |
| auxiliary | `FUN_0077FCF0` / `0x0077FD30` / `0x0CBE30` | `0x0077FD54` | `0x00780DD0` / `0x0CCED0` |

The two 0x28-byte installer bodies are byte-identical and perform exactly:

```text
header[+0x00] = header
header[+0x04] = header[+0x1C]
header[+0x08] = header[+0x20]
header[+0x0C] |= 1
```

This is the nonzero write to primary `+0x208` / auxiliary `+0x908` and flags
bit 0 at `+0x20C/+0x90C`. Each leaf has only its corresponding direct wrapper
callsite above. The higher-level edge is ordinary virtual dispatch through
tables stored in the resident ELF, so neither a literal search restricted to
BTL nor ordinary cross-references find it:

| Participant interface | Resident method-table evidence | Recovered dispatch |
| --- | --- | --- |
| Primary object `+0x110` | Base table `0x005FB4D0`; slot `+0x88` at `0x005FB558` contains live wrapper `0x00787860`. Primary constructor live `0x00785410` installs this table. Table RTTI `0x008CE878` names `ccSkill` through resident string `0x006059C0`; specialized primary tables repeat the slot, for example `0x005E0900+0x88`. | Normal update continuation has `jalr` sites live `0x00795F5C` and `0x00795F74`, raw `0x0E205C/0x0E2074`, passing object `+0x200` and `+0x3B0` respectively. Both load the interface at `+0x110` and its slot `+0x88`. |
| Auxiliary object `+0x50` | Table `0x005FB920`; slot `+0x48` at `0x005FB968` contains live wrapper `0x0077FD30`. RTTI `0x008CE9B0` points to name `ccSkillObj` at live `0x008AE638`, raw `0x1FA738`. The auxiliary teardown body live `0x0077EFC0` reinstalls this base table; specialized table `0x005E24C0` contains the same slot at `0x005E2508`. | Full updater export `FUN_007812E0`, live `0x00781320`, raw `0x0CD420`, has `jalr` sites live `0x00781394` and `0x007813AC`, raw `0x0CD494/0x0CD4AC`, passing object `+0x900` and `+0x990`. It requires object byte `+0x00` bit 1 and clear byte `+0xAE4` bit 0 on this branch; the alternate `+0xA20` bit-0 branch invokes another slot instead. |

Thus the wrappers accept the header supplied as argument 2; they are not
hard-coded to the first bank. The primary and auxiliary second-bank active
fields are respectively `+0x3B0/+0x3B4/+0x3B8/+0x3BC` and
`+0x990/+0x994/+0x998/+0x99C`, with the same relative installer layout.
Which later consumer uses each bank is a separate question from proving their
activation. The ordinary pair filters above read the first bank.

A resident absolute-pointer census found 166 ordinary-address occurrences of
the primary wrapper between `0x005E0988` and `0x005FB558`, and 53 of the
auxiliary wrapper between `0x005E2508` and `0x005FB968`. A structural
audit of ordinary resident bytes `0x005E0900..0x005FB94F` placed those entries
in 166 primary interfaces and 53 auxiliary interfaces, including the base
tables. All inspected primary activation slots `+0x88` contain live
`0x00787860`; all inspected auxiliary slots `+0x48` contain live `0x0077FD30`.
No derived activation override occurs in that bounded table set.

The audit checked interface boundaries and neighboring method slots rather
than treating every RTTI-bearing table as a full interaction interface. For
example, `ccSkillBlur` at resident `0x005EB860` and `ccEffParabolaObj` at
`0x005ED750` each have a short interface ending before `+0x88`; reading that
offset crosses into the next table and produces a false override. The actual
following primary interfaces start at `0x005EB890` (`ccSkillFOR000`) and
`0x005ED780` (`ccSkillCYB000`), and retain the primary installer. Representative
other primary tables include `0x005F0C20` (`ccSkillNRW001`) and `0x005F8E90`
(`ccSkillSAK000`); auxiliary tables include `0x005E24C0`
(`ccSkillObjKBW001Anb`) and `0x005F84C0` (`ccSkillHKG001Wall`). These are literal
RTTI names, not assigned player-facing move names. The audit does not establish
runtime execution, count distinct instantiated classes, or exclude additional
interfaces outside the stated resident interval.

Two explicit primary paths also prepare and immediately activate the first
bank. Export `FUN_007B4B10`, live `0x007B4B50`, raw `0x100C50`, and export
`FUN_007CB7B0`, live `0x007CB7F0`, raw `0x1178F0`, call the primary builder
with definition index 0 and header `+0x200` when their second argument is zero,
then invoke `+0x110` table slot `+0x88` at live `0x007B4B94/0x007CB834`
(raw `0x100C94/0x117934`). Their surrounding specialized gameplay is outside
this document. Same-number slot loads from an auxiliary `+0x50` interface
are different methods; a slot number alone does not identify an activation edge.

The preserved label `FUN_00789600` is not the primary leaf: it is a 0x40-late
fragment inside the next large body. The nearby live `0x00780E00` routine
remains the distinct resident-submission bridge described above. Runtime
relocation is not needed to explain either activation call chain.

The auxiliary updater/remover `FUN_007804D0` / live `0x00780510`, raw
`0x0CC610`, clears `+0x900/+0x904/+0x908`, flag bits 0 and 1 at `+0x90C`, and
related descriptor fields when its lifecycle gate ends. Its primary counterpart
is the full body `FUN_00788BE0` (export) / live `0x00788C20`, raw `0x0D4D20`;
the displayed `FUN_00788C20` is a 0x40-late split inside that body. At its
terminal gate, the primary body clears `+0x200/+0x204/+0x208`, flag bits 0, 1,
and 2 at `+0x20C`, words `+0x21C/+0x220/+0x228/+0x22C/+0x230/+0x234/+0x238`,
and bytes `+0x240/+0x241`; it writes `u16 +0x224 = 1` and
`u16 +0x23C/+0x23E = 0xFFFF`. These stores are direct static evidence for the
primary remove/reset state, but the conditions leading to them are outside this
document's timing scope. Together the descriptor builders, live-only
installers, filter reads, and updater/removers establish parallel
prepare/activate/consume/remove lifecycles without following those timing
conditions.

## Central relationship and compatibility filters

`FUN_007792A0` (export) / live `0x007792E0`, raw `0x0C53E0`, reads the two
primary manager slots and dispatches in this exact short-circuit order:

1. primary 0 versus primary 1: `FUN_007793A0` / live `0x007793E0`;
2. primary 0 versus the opposite 32-entry auxiliary registry:
   `FUN_007795D0` / live `0x00779610`;
3. primary 1 versus the other auxiliary registry: same function;
4. the two auxiliary registries, 32 by 32: `FUN_007799A0` / live
   `0x007799E0`.

The first accepted pair returns 1; exhaustion returns 0. The fourth argument
suppresses ordinary response handoff when nonzero, but it is **not** a global
side-effect-free probe flag: special `0x100/0x200` cross-mask classes dispatch
before consulting it. The only direct caller recovered for this dispatcher is
the main frame consumer at live `0x0077D260`, which passes zero.

All three pair filters reject while resident `FUN_001EC290` at `0x001EC290`
returns 1. That five-instruction body is exactly
`return *(s32 *)0x00607674 != 0`: it reads no pair, mask, record, or geometry
state. `0x00607674` is the timeout marker, set by the terminal detector when
the battle countdown expires and cleared by battle initialization, so all
three filters reject from timeout until the next initialization
([Match outcomes](match_outcomes.md#terminal-detector-and-classifier)).
Other readers of the marker are the start-menu admission path
([Pause and replay](pause_and_replay.md#start-menu-admission-timeout-marker-check)),
the fighter coordinator
([Battle entities](battle_entities.md#coordinator-timeout-marker-check)), and
the end sequence ([Match outcomes](match_outcomes.md#inner-end-sequence)).

### Primary versus primary

The filter reads each active record only when pointer `+0x208` is nonnull and
flags `+0x20C` bit 0 is set. It then applies:

1. the timeout-marker gate: `0x001EC290() == 1` rejects the candidate;
2. a candidate gate: both manager masks have any bit in `0x001A0000`, or both
   have bit `0x08`;
3. an identity/relationship gate: either the OR of runtime record `+0x60`
   contains bit `0x04`, or signed identity fields at
   `*(primary+0x31C)+0x98C` differ;
4. compatibility:

```text
(A.mask60 & B.mask60 & 0x80000000) != 0
and ((A.mask60 & B.mask64) != 0 or (B.mask60 & A.mask64) != 0)
and (A.mask60 & B.mask60 & 0x04) == 0
```

Bit `0x04` therefore has two distinct collision-facing roles in this primary
pair path. With neither record setting it, the signed `+0x98C` identities must
differ. With exactly one record setting it, equal identities pass that
relationship gate. With both setting it, ordinary compatibility rejects the
pair regardless of identity. The candidate, high-bit, and cross-mask gates
still apply in every accepted case; this is a field-use contract, not an
original gameplay name for the bit.

An ordinary accepted pair calls the primary/primary response wrapper at live
`0x0077A750` (full body export `FUN_0077A710`, raw `0x0C6850`) and clears
manager `+0x11D0/+0x11D4`.

### Primary versus auxiliary

The filter walks exactly 32 opposite-side entries. It combines the selected
manager primary mask (`+0x11D0` or `+0x11D4`) with auxiliary `+0x1D0` and
validates relationship-specific snapshot backlinks through the generation
checked resolver:

| Primary candidate bit | Auxiliary candidate bit | Primary snapshot used |
| ---: | ---: | ---: |
| `0x40` | `0x400` | `+0x700` |
| `0x100000` | `0x40000` | `+0xDC0` |
| `0x20000` | `0x100000` | `+0xE40` |
| overlapping `0x80000` | overlapping `0x80000` | `+0xE40` |

The resolved backlink must equal the current auxiliary candidate. Let
`x = primary.mask60 & auxiliary.mask64` and
`y = auxiliary.mask60 & primary.mask64`. Active-record masks then classify
cross-mask intersections exactly as follows:

```text
class 1: ((x | y) & 0x300) == 0x300
class 2: (x & y & 0x100) == 0x100
class 3: (x & y & 0x200) == 0x200
```

Those special classes call live `0x00779E90` (full body
`FUN_00779E50`, raw `0x0C5F90`) before the fourth-argument suppression check.
The routine derives a midpoint-like vec4 from primary `+0x210` and an input
position, then selects class-specific response behavior. “Contact point” is a
plausible interpretation, not proven geometry output.

The ordinary path applies the high-bit compatibility expression used above,
including the same mutual `0x04` exclusion, then calls live `0x0077A550` (full body
`FUN_0077A510`, raw `0x0C6650`). On successful handoff it consumes the relevant
primary and auxiliary candidate masks.

### Auxiliary versus auxiliary

The filter performs a fixed 32-by-32 traversal. Its relationship gates require
reciprocal generation-checked backlinks for these candidate combinations:

| Candidate relationship | Snapshot offsets |
| --- | --- |
| shared `0x800` relation | candidate A `+0x2F0`, candidate B `+0x2F0` |
| `0x100000` versus `0x40000` | `+0x770` versus `+0x370`, in both directions |
| shared `0x80000` relation | candidate A `+0x7F0`, candidate B `+0x7F0` |

It then uses the same active-record cross-mask class logic and ordinary
high-bit compatibility family, including mutual `0x04` rejection. Special
classes are dispatched before that ordinary exclusion and call live `0x0077A080`
(full body `FUN_0077A040`, raw `0x0C6180`), which derives a midpoint-like vec4
from the two auxiliary positions at `+0x30`. Ordinary acceptance calls live
`0x0077A220` (full body `FUN_0077A1E0`, raw `0x0C6320`). Unlike the
primary/primary and primary/auxiliary ordinary paths, this filter does not
explicitly clear either auxiliary candidate mask after acceptance.

“Primary”, “auxiliary”, “candidate A”, and “candidate B” are used where static
direction is known. “Attacker” and “target” are intentionally avoided because
the filters themselves include reciprocal compatibility and do not establish
a universal gameplay direction.

Manager auxiliary aggregates `+0x11D8/+0x11DC` are produced by the upstream
aggregator but are not read by this dispatcher. The dispatcher walks the
individual auxiliary masks directly. The aggregates therefore belong to a
different manager consumer or summary role, not this pair-filter call chain.

## Response-packet handoff boundary

The three ordinary response wrappers are:

| Pair | Full-body export | Live | Raw |
| --- | ---: | ---: | ---: |
| auxiliary/auxiliary | `FUN_0077A1E0` | `0x0077A220` | `0x0C6320` |
| primary/auxiliary | `FUN_0077A510` | `0x0077A550` | `0x0C6650` |
| primary/primary | `FUN_0077A710` | `0x0077A750` | `0x0C6850` |

Across pair types they:

1. validate object side/slot/generation/self tuples against the manager;
2. resolve the backing gameplay object and require `(object+0x14 & 3) == 0`;
3. copy selected active-record word `+0x10` into each backing primary's
   `+0xF0C` through live-only `0x00787D80` (raw `0x0D3E80`);
4. invoke object virtual preparation callbacks;
5. ask each participant to fill a 48-byte stack response packet (auxiliary
   interface `+0x8C`; primary interface `+0x240` in the observed paths);
6. order the participants by side and call the common handoff at live
   `0x0077B350` (`FUN_0077B310` export, raw `0x0C7450`);
7. invoke participant post-handoff callbacks.

The helper at `0x00787D80` selects auxiliary active pointer `+0x908` when
argument 2 is nonnull, otherwise primary `+0x208`, then clears and fills primary
`+0xF0C` from that record's `+0x10`. All six encoded wrapper calls target this
leaf: live `0x0077A3AC/0x0077A3BC`, `0x0077A654/0x0077A664`, and
`0x0077A7C0/0x0077A7D0`. The adjacent live `0x00787DB0` routine is a separate
list-deactivation/reset callback, published at the base primary table's
`+0x1F4`; it must not be substituted for these pre-packet calls. The common
handoff invokes that slot later, as described below.

The primary/primary wrapper additionally calls `FUN_0077CD20` (export) / live
`0x0077CD60`, raw `0x0C8E60`, before producing packets. When both active
records share bit `0x01` at runtime `+0x60`, this helper may swap the two
participant resource vec4s at `resource+0x30` according to signed orientation
field `resource+0x98C`. This is a pre-packet collision-position side effect;
the static branch does not establish attacker/target direction.

The common handoff copies optional packet vec4s at packet `+0x20..+0x2C` into
manager `+0xB60/+0xB70`, calls the geometry/packet combiner at live
`0x00773210`, mirrors accepted vec4s into participant-owned fields
`*(primary+0x31C)+0x30..+0x3C`, and invokes primary virtual callbacks at
interface offset `+0x1F4`. This is the last shared collision-facing seam before
later gameplay-specific consumers.

Each response packet is exactly 0x30 bytes in these wrappers. Proven fields are
byte `+0x00` (mode/valid tag), vec4 `+0x10` (anchor/reference), and vec4
`+0x20` (resolved/current position). Before examining the tag, the common
handoff overwrites each packet `+0x20` vec4 from its ordered participant
`+0x330`. Tag 1 copies that vec4 to the corresponding manager temporary;
otherwise the manager temporary's final word receives float `10000.0`.

The complete combiner body accesses no packet bytes other than tag `+0x00`
and the two vec4s at `+0x10/+0x20`. Packet bytes `+0x01..+0x0F` therefore
remain producer-private or padding in this collision-facing seam; no semantics
for them are inferred here.

### Packet producers and tag source

The shared primary packet producer is export `FUN_00787C30`, live
`0x00787C70`, raw `0x0D3D70`; the auxiliary producer is export `FUN_00780170`,
live `0x007801B0`, raw `0x0CC2B0`; both continue past their resident
`0x003083A0` calls through displays `0x00787C30..0x00787D17` and
`0x00780170..0x00780253`. Neither producer initializes the full 0x30-byte packet. Each performs its
participant preparation, invokes an anchor callback with `packet+0x10`, invokes
a tag getter, and writes the getter's low byte to `packet+0x00`.

| Participant | Shared builder slot | Preparation slot | Anchor slot | Tag slot and exact getter |
| --- | ---: | ---: | ---: | --- |
| Primary interface at object `+0x110` | `+0x240` | `+0x244` | `+0x238` | `+0x23C` contains live `0x00787D60`, raw `0x0D3E60`: `lbu v0,0xFEC(a0); jr ra; nop`. |
| Auxiliary interface at object `+0x50` | `+0x8C` | `+0x90` | `+0x84` | `+0x88` contains live `0x007802A0`, raw `0x0CC3A0`: `lbu v0,0xAE5(a0); jr ra; nop`. |

All 166 primary and 53 auxiliary interfaces in the bounded resident audit
retain their respective packet builder and tag getter. Anchor and preparation
slots do vary. Consequently, tag 1 at the common handoff means the producer's
object byte equals 1; the getter does not canonicalize other nonzero values.
The tag is neither a return value from the sphere-overlap test nor evidence
that the producer initialized `packet+0x20`: the common handoff always replaces
that vec4 from the ordered primary participant's `+0x330` before testing tags.
The semantic names and complete writer sets of `+0xFEC/+0xAE5` remain separate
unresolved questions.

The primary producer's backing-entity gate skips only its initial resident
preparation calls; its later preparation/anchor/tag callbacks still run. The
auxiliary producer similarly proceeds to both descriptor callbacks and its
packet callbacks after that gate. Therefore a failed backing-entity predicate
does not, by itself, clear or prevent production of the packet tag.

The aligned direct-byte-access audit additionally recovers these tag writers:
the base primary constructor writes 1 at live `0x00785A94`, raw `0x0D1B94`;
the leaf live `0x007C6120`, raw `0x112220`, writes primary `+0xFEC = 0` and
returns; and constructor live `0x007D6290`, raw `0x122390`, writes it to zero
at live `0x007D6308`. The leaf is slot `+0x22C` of table `0x005F6340`
(`ccSkillJRB001`); the constructor installs table `0x005F2EA0`
(`ccSkillFIR001`) after calling the base constructor. Auxiliary initialization
writes `+0xAE5 = 0` at live `0x0077F45C`, raw `0x0CB55C`, and the scoped
specialized path at live `0x007C5DCC`, raw `0x111ECC`, also clears it. No
nonzero auxiliary tag store was found among these direct byte accesses. This
audit does not exclude wider overlapping stores or computed-address writers,
and does not establish a universal tag invariant for every object lifetime.

### Tag lifetime and non-byte access bounds

A separate byte audit covers all 486,832 aligned text words in live
`0x006B3F40..0x0088F5FC` (display `0x006B3F00..0x0088F5BC`). It checks
halfword, word, scalar-float, doubleword, and quadword store displacements that
overlap primary `+0xFEC` or auxiliary `+0xAE5`, and conservatively includes
`swl/swr/sdl/sdr` within the containing word or doubleword. It finds **no
overlapping wider or partial store** in that text interval. It also finds no
`addi/addiu/daddi/daddiu` formation of either exact byte address from a base
register. This extends the direct-byte writer audit; it does not identify every
rebased alias or generic copy that could eventually reach a tag.

The nearby auxiliary word at `+0xAE0` is a separate scalar. For example,
primary-to-auxiliary binding leaf live `0x0077FBC0` writes it with `swc1` at
`0x0077FC6C`, and the computed record producer above reads it with `lwc1`.
Both are four-byte accesses ending at `+0xAE3`. The common update control
at `+0xAE4` uses byte loads/stores, including live
`0x0078113C/0x0078117C/0x007811C8`; those do not overwrite `+0xAE5`.
Likewise the primary counter at `+0xFE8` uses four-byte accesses ending at
`+0xFEB`. These are concrete neighboring owners and widths, not additional
tag producers.

The primary zero-writing leaf has two concrete virtual invocation paths.
The raw continuation of live `0x0078E700` loads primary interface `+0x22C`
and calls it at `0x0078E8E8` or `0x0078E964`, after alternative branches
selected through slot `+0x204`. When table `0x005F6340` is installed, its
`+0x22C` entry at `0x005F656C` selects live `0x007C6120`, whose complete leaf
is `sb zero,0xFEC(a0); jr ra; nop`. This resolves the indirect edge to the
known tag writer without a direct call xref. Neither callsite alone establishes
that a particular instance reaches a later accepted pair or packet handoff.

The auxiliary zero store at `0x007C5DCC` is inside successful construction,
not an unclassified per-update write. Live entry `0x007C5D20` requires the
primary's `+0x1DC == 0x0E`, allocates `0xDB0` bytes, calls the base auxiliary
constructor, and installs table `0x005F6590`. Its literal RTTI name is
`ccSkillJRB001Rock`, through live descriptor `0x008CFD98` and string
`0x008BC210`. The zero store precedes table slot `+0x78` at `0x007C5E7C`.
That slot selects the complete binding leaf `0x0077FBC0`: it copies the
primary manager/slot/generation/self tuple, side and backing pointers, prepares
both headers, supplies the scalar, and optionally builds definition 0.
Its final slot `+0x0C` selects the verified no-op `0x0077FD00` in this table.
Neither binding body nor that callback writes the tag.

If the manager exists, the same constructor then calls low-to-high auxiliary
insertion at `0x007C5EAC`, passing primary `+0xFF0` as the output tuple; those
tuple writes begin after the primary's tag byte. The auxiliary table retains
the common activation, packet builder, tag getter, and the already documented
Rock anchor. Its deleting destructor live `0x007C5040` releases embedded
records, calls base auxiliary destruction, and optionally frees the object;
the inspected cleanup contains no tag reset. Consequently, this scoped
construction/publication/packet/cleanup chain supplies no nonzero tag producer.
Allocation-failure fallthrough, intervening arbitrary aliases, and later
callback effects remain bounded uncertainties; no ordinary-play outcome or
universal auxiliary-zero invariant follows from this trace.

### Anchor callback family

The bounded table set supplies **20 distinct primary anchor callbacks**
(146 tables use the base and 20 use 19 other callbacks) and **8 distinct
auxiliary callbacks** (46 base, 7 other). Every distinct callback body was
inspected through its return, including raw continuations that the preserved
import omits after calls it marks non-returning. The table counts identify static
interfaces, not instantiated objects or observed moves. The exact callback
targets below are live addresses; their preserved displays are 0x40 earlier.

The primary base callback at live `0x007938C0`, raw `0x0DF9C0`, calls
`0x001DDD80(primary+0xF30,1)` and copies the resulting registration's
volume `+0x20` center into the packet anchor. It first stores VU `vf0`,
`(0,0,0,1)`, to the output. No registration leaves that value; a registration
with null volume instead stores a zero quadword, `(0,0,0,0)`. It does not add
the sphere's `+0x1C` z-bias, so this anchor differs from the effective center
used by the resident overlap pass when that bias is nonzero.

In the following table, **base** means that same first-registration-center
sequence, inlined in the callback. Signed x adjustments use a positive offset
when primary float `+0x348 > 0`, otherwise a negative offset, except where a
different source is stated. `H(entity)` is exactly resident
`0x002163A0(0.5,entity) = entity.floatE4 * 0.5 * entity.float2F0`; it is a
recovered scalar expression, not an assigned anatomical measurement. Its
primary callers use zero when their existing backing-entity gate fails.

| Primary live callback | Literal RTTI example | Confirmed anchor construction |
| ---: | --- | --- |
| `0x007938C0` | `ccSkillKBW001` and 145 other tables | Base center sequence. |
| `0x007A0D70` | `ccSkillNRW001`, `ccSkillNRT001B` | Base, then signed x offset 12. |
| `0x007AD4D0` | `ccSkillSAK000` | Base, then signed x offset `primary.float1038 - 15`. |
| `0x007ECE80` | `ccSkillGUW001` | Base, then signed x offset `primary.float1008 - 55`. |
| `0x007CDEE0` | `ccSkillKMM001` | Base, then signed x offset `0.7 * primary.float1008` and z addition `0.5 * primary.float100C`. |
| `0x007A6F20`, `0x007DA820` | `ccSkillNEJ001`, `ccSkillHNB001` | Base, signed x offset `0.8 * primary.float1008`, then z addition `H(backing_entity)`. |
| `0x007E85C0` | `ccSkillNEW000` | Base, signed x offset `0.8 * primary.float1248`, then z addition `H(backing_entity)`. |
| `0x007AB120` | `ccSkillHNT001` | Base; x subtracts 90 when `+0x348 < 0`, then adds 144 for positive `+0x348` or subtracts 144 otherwise; z adds `H(backing_entity)`. |
| `0x0081E330` | `ccSkillKIB001New3` | Copies backing entity `+0x30` to primary `+0x10B0`, calls live `0x0081F5D0` to refresh two local center vec4s at `+0x1030/+0x1080`, then uses base plus signed x offset 100 and z offset 70. |
| `0x008207B0` | `ccSkillASM001` | Base plus x offset 25 selected by backing entity float `+0x48`, and z offset 10. |
| `0x00824DC0` | `ccSkillGAR001New3` | Backing entity `+0x30` position, x offset 170 selected by its float `+0x48`, and z addition `H(backing_entity)`. |
| `0x0086AED0` | `ccSkillSSW001` | Backing entity `+0x30` position, x offset 125 selected by primary float `+0x1130`, and z offset 70. |
| `0x0085F320` | `ccSkillHNW001` | Backing entity `+0x30` position, signed x offset 175, and z offset 70. |
| `0x007F7B80` | `ccSkillTYO001` | Copies backing entity `+0x30` position, then adjusts x by primary float `+0xFF4`, negated when backing entity float `+0x48 <= 0`. |
| `0x0082ACB0` | `ccSkillANK001` | Resolves `OBJ_2cmn00t0 l hand` from primary `+0x320`, refreshes the returned object's transform, copies its `+0x30` position, then adds x offset 70 selected by backing entity float `+0x48` and z offset -5. |
| `0x008747B0` | `ccSkillROW001` | Resolves `OBJ_2cmn00t0 l foot` through primary `+0x324`, refreshes the returned object's transform, and copies its `+0x30`; uses base when lookup returns null. |
| `0x0080FE20` | `ccSkillANB000` | Resolves the resource name held at primary `+0x1034` from `+0x320`; subtracts backing entity position from the resolved position, then adds that displacement to primary `+0x330`. Additional state-conditioned side effects occur before return. |
| `0x00862DA0` | `ccSkillKIW001` | Searches list-level results from primary `+0xF30` through resident `0x001DDDC0`; accepts a class-5 owner or category bits intersecting `0x880/0xC0000`, copies the result center, and for class 5 offsets x by counterpart radius plus primary float `+0x10A8` according to orientation. Output y is overwritten with primary float `+0x4E4`. |
| `0x007D72E0` | `ccSkillFIR001` | Performs forward and possible reverse resident environment segments from primary `+0x330`, updates that primary position and the backing entity position when eligible, then uses the selected position plus signed x offset `primary.float1018` and z offset `primary.float101C`. |

The resource-transform branches in `0x0082ACB0`, `0x008747B0`, and
`0x0080FE20` copy the object's four local transform rows `+0x40..+0x7F` to
`+0x00..+0x3F` and clear byte `+0x8D` when object `+0x80` is zero; otherwise
they call resident `0x0019C7C0`. The first and third callbacks also temporarily
substitute primary `+0x320` into backing entity `+0xE70`, call resident
`0x0024D3C0`, and restore that word. These are real producer side effects;
anchor production is not uniformly a read-only vector getter. Their broader
model/update contracts are outside this collision seam.

The `ccSkillFIR001` callback's segment contract is specifically
`0x001BF100(start,end,0x40000001,1,0,-1)`. The first endpoint is displaced by
175 along the sign selected from primary `+0x348`; a first hit causes the
reverse query, and a second hit adds a 30-unit signed x offset. It copies the
chosen vec4 to primary `+0x330`, forces primary `+0x33C = 1.0`, and may copy it
to backing entity `+0x30` with entity `+0x3C = 1.0`. This establishes environment
reconciliation before the common combiner, without classifying the later
response or damage outcome.

The auxiliary base live `0x0077F0D0`, raw `0x0CB1D0`, also selects registration
1, from list `+0x140`. With a registration present, it starts from the volume
center. If `auxiliary.floatAB0 * auxiliary.floatAB4 > 0`, it instead uses
auxiliary position `+0x30`, adds half `+0xAB4` to z, and adds or subtracts half
`+0xAB0` to x according to float `+0x48`. Otherwise it adjusts the sphere
center's x by `0.9 * radius` with that same sign choice. It does not add volume
z-bias.

| Auxiliary live callback | Literal RTTI example | Confirmed difference from base |
| ---: | --- | --- |
| `0x0077F0D0` | `ccSkillObjKBW001Anb` and 45 other tables | Base construction above. |
| `0x008404C0` | `ccSkillObjTMW001Tornade` | First-registration center, then x offset 200 selected by auxiliary float `+0x48`. |
| `0x0083BAB0` | `ccSkillObjITW001Gokakyu` | First-registration center, x offset 150 selected by `+0x48`, and resource-transform update when auxiliary `+0xAFC` is nonnull. |
| `0x00814AB0` | `ccSkillObjWaterDragon` | First-registration center without the base's radius/span adjustment. |
| `0x00827A90` | `ccSklObjSEC001` | Copies auxiliary vec4 `+0xD80`; x offset 190 uses float `+0x48` of the entity at `+0x948`, or `+0x944` when `+0x948` is null; z adds 150. |
| `0x007CA360` | `ccSkillSKV001Gate` | Base, then sets z to auxiliary float `+0x38 + H(entity at +0x9D4)` when `+0x9D8` is null, otherwise uses `+0x38`. |
| `0x007C5440` | `ccSkillJRB001Rock` | Base plus auxiliary vec4 `+0xAC0`, then forces output w=1. |
| `0x007B3640` | `ccSkillHKG001Wall` | Base; adjusts x by auxiliary float `+0xB38`, adding when auxiliary x is below `+0x9F0` and subtracting otherwise; replaces z using the same `+0x9D4/+0x9D8` scalar branch as the Gate callback. |

There are concrete conditional-initialization limits. Auxiliary base
`0x0077F0D0` first writes `vf0` to the output, but its no-registration branch
then copies an uninitialized stack vec4 over that output at live
`0x0077F208..0x0077F210`. If a registration has null volume and its span-product
branch is nonpositive, the callback still loads radius through that null volume
pointer. Several primary entity-position callbacks likewise initialize their
stack source only when the backing-entity gate accepts, yet continue into
arithmetic and output on failure. `ccSkillKIW001` initializes result-center
x/z/w only on an accepted result, while its exhausted path still copies those
stack words. These are static path observations, not evidence that the missing
inputs occur in ordinary play or cause an observed failure.

### Contact reconciliation

The combiner is `FUN_007731D0` (export) / live `0x00773210`. When both packet
tags are zero it writes the midpoint of the two packet `+0x10` anchors to
manager `+0xB00`. Other tag combinations reconcile the two packet `+0x20`
positions, call resident segment/environment query `0x001BF100` where needed,
mutate packet `+0x20`, and write the selected or midpoint vec4 to manager
`+0xB00`. Its helper `FUN_00773040` / live `0x00773080`, raw `0x0BF180`, builds
a horizontal x segment at input z+5, calls `0x001BF100`, writes a corrected
position, and returns a signed x displacement. Bytes through live
`0x00773207` corroborate this direction; it is not the combiner's separate
vertical segment query. These routines establish a contact/result
reconciliation phase; they still do not expose upstream candidate-overlap math.

The helper's geometry contract is exact. With half-width `w = width * 0.5`,
displacement input `d`, direction `s`, input position `p`, and anchor `a`, its
query runs from `(p.x,p.y,p.z+5,1)` to
`(a.x + s * (d+w),p.y,p.z+5,1)` using masks `(1,0,0,-1)`. On a hit it uses
the clipped endpoint; on a miss it keeps the requested endpoint. It then
subtracts `s*w` from x, restores the output's original y/z, writes the vec4,
and returns `s * (output.x-a.x)`. The width supplied by the combiner is
`entity.floatE8 * entity.float2F0`, through resident `0x002163C0(1.0,entity)`.
The helper advances its scratch allocator by exactly 0x20 bytes and restores
the old pointer before returning.

For producer tags 0/1, the combiner and handoff have this collision-facing
contract:

| Ordered packet tags | Combiner geometry and output | Backing position writeback |
| --- | --- | --- |
| `0,0` | Midpoint of the two anchors, w=1; skips the geometry branch. | Neither packet position is copied back. |
| `1,0` or `0,1` | Reconciles the tagged participant against the other anchor, including the vertical and horizontal environment queries; emits the tagged participant's corrected anchor. | Only the tag-1 participant receives corrected packet `+0x20`. |
| `1,1` | Reconciles both positions, performs the paired horizontal adjustment and vertical checks, aligns anchor z, and emits their midpoint with w=1. | Both participants receive corrected packet `+0x20`. |

The manager `+0xB60/+0xB70` snapshots are made **before** the combiner;
they retain pre-reconciliation position values for tag 1. The position
writeback occurs afterward, and both primary `+0x1F4` callbacks run regardless
of tag. The combiner tests tags as zero/nonzero and later sums their numeric
byte values, while the outer handoff's snapshots/writeback require equality
to 1. No single general truth-value convention covers arbitrary tag bytes;
the matrix is deliberately restricted to the established direct 0/1 writers.

### Pending-result slots

Manager slots `+0xB80` and `+0xB90` are each 0x10 bytes:

| Slot offset | Observed content |
| ---: | --- |
| `+0x00` | participant/object A pointer |
| `+0x04` | participant/object B pointer |
| `+0x08` | runtime-record pointer consumed through temporary copies |
| `+0x0C` | active byte |

A confirmed producer is the full body `FUN_0077BBC0` (export) / live
`0x0077BC00`, raw `0x0C7D00`; preserved `FUN_0077BC00` is a split 0x40 bytes
into that body. On its equal-branch path it builds two mirrored entries. For
each direction it selects a slot from participant resource byte `+0x60` bit 0,
writes the participant and counterpart pointers at slot `+0x00/+0x04`, stores
a pointer to a copied 0x54-byte temporary record at `+0x08`, and sets byte
`+0x0C = 1`. Its representative encoded caller is live call site
`0x0077C670`, raw `0x0C8770`, inside `FUN_0077C230` (export) / live
`0x0077C270`. The rest of that specialized gameplay path is deliberately not
characterized here.

`FUN_0077BA50` (export) / live `0x0077BA90`, raw `0x0C7B90`, temporarily
mutates fields in that source,
copies record data through resident `0x0017A420`, calls resident `0x00233110`,
restores the source, and clears all four slot fields. One copy length is 0x54;
another observed call uses 0xA8 across the paired scratch area. Its downstream
gameplay semantics are outside scope. No damage field, formula, or application
routine is documented here.

## Separable stage/background queries

Adjacent literal names `ccBgObject`, `ccList2<ccBgObject>`, `ccBgSystem`, and
`ccBgControl` identify the `0x006C*` cluster as background/stage infrastructure
with high confidence. The queries operate on the `ccBgControl` held at
`ccField+0x70`. Its first and second line families (descriptor types
`0x25/0x26` and `0x23/0x24`), their 0x30-byte line records, the 0x40-byte
boundary records, the builders, per-stage line counts, and the cached line
attribute belong to [Stages](stages.md#line-construction). This section owns
the query contracts. Each family has, per section 0 or 1, a count byte, a
selected-index byte (`+0xA8E/+0xA8F` for the first family,
`+0xA9A/+0xA9B` for the second), and a head-pointer table. Boundary records
are held in the pointer vector at control `+0xA80` (capacity `+0xA80`, size
`+0xA84`, data `+0xA88`). Original names for the sections and the two families
are unrecovered.

Raw bytes add these builder facts to the Stages description. The
second-family builder, `FUN_006C3710` / live `0x006C3750`, raw `0x00F850`,
runs continuously through live `0x006C3ED4`; it takes an assertion path for
descriptor types other than `0x23/0x24`, clears line `+0x24/+0x2C`, and
appends its boundary record through the live-only vector-insert helper
`0x006C4040` (raw `0x010140`). Resource callbacks live `0x006C4580` and
`0x006C45E0` call it at live `0x006C45B0` and `0x006C4610`; live `0x006C4640`
and `0x006C46A0` call the first-family builder, live `0x006C33C0`, at live
`0x006C4670` and `0x006C46D0`. All four obtain the control through live
`0x006C1640` and, when it returns null, call resident `0x003947C0` on the
descriptor instead of building lines.

Line `+0x24` is a line flag, not a reserved word: the nearest-line queries
require it to equal 1 when the querying object's `+0xBB4` contains `0x800`
([Stages](stages.md#geometry-driven-navigation-graph)). Both builders leave it
zero, and no writer of a nonzero value has been identified.

### Stage query functions

In this section x and z name vec4 components 0 and 2; static code does not
establish the engine's axis names.

| Query | Core export / live / raw | `ccField` wrapper export / live / raw |
| --- | --- | --- |
| Height envelope (floor profile) | `FUN_006C2570` / `0x006C25B0` / `0x00E6B0` | `FUN_00708CA0` / `0x00708CE0` / `0x054DE0` |
| Boundary clamp | `FUN_006C22D0` / `0x006C2310` / `0x00E410` | `FUN_00708A40` / `0x00708A80` / `0x054B80` |
| Piecewise boundary resolver | `FUN_006C1E10` / `0x006C1E50` / `0x00DF50` | `FUN_00709090` / `0x007090D0` / `0x0551D0` |
| Boundary-record access | `FUN_006C3F90` / `0x006C3FD0` / `0x0100D0`, bounds-checked | not documented |

**Height envelope.** `FUN_006C2570` takes `(control, section, query_vec4,
output_vec4)` and reads the section's selected chain in each family. It starts
with no result and a minimum of `32767.0`. It checks the second-family chain
first, accepting the first line whose endpoints satisfy the strict interval
`A.x < query.x < B.x`; it linearly interpolates z and then scans every line of
the first-family chain, retaining the lowest interpolated z. The output copies
input x/y, writes the chosen z or the `-32768.0` no-result sentinel, and writes
w=1. Endpoints are excluded, reversed-x lines are not handled, and cached line
attribute `+0x2C` is not read. The preserved label `FUN_006C25B0` is a false
start 0x40 inside this routine. When `ccField+0x70` is null, the wrapper
returns the copied input with z=`-32768.0`, w=1; otherwise it calls the core
query.

**Boundary clamp.** `FUN_006C22D0` selects a caller-indexed 0x40-byte boundary
record from the vector at control `+0xA80` and compares input x with the x of
record endpoints `+0x10` and `+0x20`. Below the first it copies the whole
`+0x10` vec4 to the input; above the second it copies the whole `+0x20` vec4;
either clamp returns 0, and an input inside the interval returns 1. The wrapper
passes its second argument through as the record index, works on a copy,
optionally returns the clamped vector, and returns 1 when `ccField+0x70` is
null.

**Piecewise boundary resolver.** `FUN_006C1E10` takes `(control, inout_vec4,
record_A_index, record_B_index)`. It refreshes record B `+0x38` from the
absolute difference between the x floats reached through B `+0x30/+0x34`, then
computes `ratio = abs(B.first.x - query.x) / B.span` and
`candidate_x = A.first.x + A.span * ratio`. A query on or before B's first x
copies A's first endpoint; a ratio above 1 or candidate x beyond A's second x
copies A's second endpoint. Otherwise it walks A's nested endpoint-pair vector
(count `+0x04`, pointer array `+0x08`; each 0x20-byte member is two vec4s at
`+0x00/+0x10`), linearly interpolates z across the pair that contains
candidate x, or snaps to the nearer adjacent endpoint in the terminal fallback.
All paths mutate the supplied vec4 in place and return no status. The
numerator-zero case leaves ratio at zero, but nothing guards a zero B span when
the numerator is nonzero; valid resources therefore appear to carry a nonzero
x span (inference). The wrapper validates a record index against `ccField+0x7C`
and returns success or failure around the core mutation.

**Cached line attribute.** The midpoint pass `FUN_006C1B80` / live
`0x006C1BC0`, raw `0x00DCC0`, queries each line through resident
`0x001BF100(…,1,0,0,-1)` and stores the published primitive flags at line
`+0x2C`; [Stages](stages.md#line-construction) owns that pass. Its static
source path is resident `0x001BFF80/0x001BFF84` (primitive `+0x0C` to candidate
`+0x48`), `0x001BF7A4/0x001BF7B0` (publication at `0x0061F6E8`), and BTL stores
at live `0x006C1CCC/0x006C1CD0` (first family) and `0x006C1DE4/0x006C1DE8`
(second family). The cached word therefore inherits the resident query's
32-candidate limit and equal-distance tie order. Attribute meanings belong to
[Stage surface attributes](stage_surface_attributes.md#attribute-data-flow).

**Height-wrapper callers.** A direct-call scan of BTL finds two calls to the
height-envelope wrapper:

| Caller path | Height-query call live/raw | Established selector source |
| --- | --- | --- |
| Export `FUN_0078D5F0`, live `0x0078D630`, raw `0x0D9730` | `0x0078D700` / `0x0D9800` | Reads input header byte `+0x189`; when it is nonzero and resident `0x003083A0` returns nonzero for the pointer stored at header `+0x11C`, it uses signed halfword `backing_entity+0x9F6`. Otherwise it selects 0. The helper checks only a non-null argument and its global gate, as documented in [Definition-to-runtime copy](#definition-to-runtime-copy). Caller live `0x0078CFD0`, raw `0x0D90D0`, passes primary `+0x200` as this header, so that pointer is primary `+0x31C`. The returned surface component is compared with the candidate position. |
| Export `FUN_0082E810`, live `0x0082E850`, raw `0x17A950` | `0x0082E9B4` / `0x17AAB4` | Preserves and forwards its second argument. Both direct callers, live `0x008336BC` and `0x00833844` (raw `0x17F7BC/0x17F944`), obtain it with `lh` from `*(object+0x11D0)+0x9F6`. Their specialized object behavior is outside this document. |

Both paths therefore consume the backing entity's section field as signed
16-bit data. The wrapper and selected-chain accessors do not range-check that
selector; their two-section pointer arrays require a valid index. This is a
caller/data contract, not evidence that either player's registry slot selects
the geometry. Stage-authored line names and section relationships belong to
[Stages](stages.md#line-construction).

The line-marker names suggest a line-envelope purpose (inference) but do not
name either family's gameplay role. This cluster neither implements nor calls
the primary/auxiliary compatibility filters above.

The writers of the selected-index bytes and the neighboring aliases belong to
[Stages](stages.md#selected-index-writers-and-neighboring-aliases): only the
control initializer's zero stores are traced, so each populated section uses
head 0.

## Local triangle geometry cache

`FUN_00772BD0` (export) / live `0x00772C10`, raw `0x0BED10`, builds a 0xA0-byte
cache from three vec4 vertices:

| Cache offset | Derived content |
| ---: | --- |
| `+0x00/+0x04/+0x08` | componentwise AABB minima |
| `+0x0C` | primitive category/selection flags consumed by resident `FUN_001BF8C0` |
| `+0x10/+0x14/+0x18` | componentwise AABB maxima |
| `+0x1C` | negative dot of derived normal and vertex 0; plane-constant interpretation is high confidence |
| `+0x20/+0x30/+0x40` | copied vertices 0, 1, and 2 |
| `+0x50` | vec4 produced by resident `0x001C0E10(v0,v1,v2,...)`; normal interpretation is high confidence from later dot use |
| `+0x60/+0x70/+0x80` | normalized edge vectors |
| `+0x90/+0x94/+0x98` | edge lengths |
| `+0x9C` | not written by the BTL builder and not read by the inspected resident segment/triangle or swept-sphere/triangle narrow phases |

This layout is byte-for-byte the 0xA0 triangle primitive consumed by the
resident segment path. `FUN_001BF8C0` advances primitives at 0xA0 stride and
reads the fields above for AABB rejection, mask selection, directed
line/plane intersection, and three edge half-space tests. The related resident
swept-sphere path `FUN_001C00B0` also consumes the edge vectors and lengths.
This establishes the record format and geometric purpose independently of the
ownership path established next.

`FUN_00772F10` / live `0x00772F50`, raw `0x0BF050`, updates 0xA0-stride
records from vertex data and calls the builder at encoded live `0x00772C10`.
Raw-byte inspection recovers two direct calls that the preserved export's
control flow omitted:

| Caller full-body export | Caller live/raw | Updater callsite live/raw | Established arguments |
| --- | --- | --- | --- |
| `FUN_007B3F00` | `0x007B3F40` / `0x100040` | `0x007B41B0` / `0x1002B0` | takes the object returned by resident `0x001BAB40`, follows `result+0x3C` then `+0x0C` for the hierarchy pointer, and supplies scalar `caller+0xB08 - caller+0x38` |
| `FUN_007CB050` | `0x007CB090` / `0x117190` | `0x007CB318` / `0x117418` | follows the same returned-object path and supplies scalar `caller+0xDE8 - caller+0x38` |

The raw continuations then consume the updated resource and transform data;
the preserved C export incorrectly ends each path immediately after
`0x001BAB40`.

The resident resource helpers close the environment-ownership edge:

- `0x001BAB40` resolves an entry or a type-`0x100` entry's nested model by
  name. The two raw callers request live strings `0x008AF560`
  (`MDL_2hkgwal0`) and `0x008B0940` (`MDL_2rsm00t0 hit00`), then follow the
  resolved model's `+0x3C` environment-object pointer and pass that object's
  `+0x0C` hierarchy to live `0x00772F50`.
- Resident `0x001BAC60` walks the same resource collection and registers its
  environment objects through `0x001BEFA0`: type `0x800` uses entry-object
  `+0x3C`; type `0x100` uses entry-object `+0x94`, then nested-model `+0x3C`.
  Resident `0x001BAEE0` performs the inverse walk through `0x001BF020`.
- `FUN_007B3E90` / live `0x007B3ED0`, raw `0x0FFFD0`, brackets the resource
  at caller `+0xAF0` with `0x001BAEE0` and `0x001BAC60`; the first updater
  caller resolves from that same `+0xAF0` collection. `FUN_007CAE00` / live
  `0x007CAE40`, raw `0x116F40`, does the same for caller `+0xDC0`, which is
  the second updater caller's collection.

Thus these BTL rebuilds mutate 0xA0 primitives in hierarchies owned by resident
environment objects and registered for the resident segment/swept-sphere
queries. This does not connect them to the DD* interaction-list processor.

Two apparent xrefs at preserved displays `0x00886FEC` and `0x00888704` do not
call this triangle builder. Their encoded target is live `0x00772BD0`, which is
an omitted 0x40-byte battle-state predicate at raw `0x0BECD0`: it returns true
only when resident global `iGpffffcc64`, its `+0x08` pointer, and nested state
`+0x14 == 3` satisfy the tested chain. The preserved
import incorrectly attached that live target to the triangle builder's export
label. Raw-byte disassembly resolves the conflict. No direct pointer or call
edge from this BTL builder/updater to the interaction manager or the `ccBg*`
stage manager was recovered; its proven owner is the separate resident
environment-object chain.

## Evidence strength, hypotheses, and negative results

| Finding | Evidence | Confidence |
| --- | --- | --- |
| Complete overlay mapping and `+0x40` preserved-import shift | Retail file header, loader/runtime mapping, raw JAL targets | High |
| Two-primary plus 64-auxiliary registry layout | Registration bodies, fixed loops, cleanup writes | High |
| 0x44 definition and 0x68 runtime interaction-record strides | Indexed builders and exact copy body | High |
| 0x40 query snapshot with generation-safe owner resolution | Raw copy and omitted resolver bodies | High |
| Candidate aggregation and filter order | Direct raw call graph and fixed loops | High |
| Descriptor activation through resident virtual tables | Base-table entries, constructor/teardown table writes, and both normal-update bank callsites | High |
| Auxiliary record `+0x54/+0x56` selects category construction | Raw instruction-byte continuation, signed halfword reads, low-byte stores, descriptor reloads, and callback order | High within the shared auxiliary updater |
| Computed prefix publication leaves record `+0x56` untouched | Resident initializer, 0x54 copy length, explicit extended clears, and descriptor pointer store | High within the selected publication |
| Selected primary and auxiliary synthetic constructors share storage | Both side-index equations reach live `0x008DC900`; call order and simultaneous use were not established | High for address aliasing only |
| Mask equations and backlink offsets | Direct filter loads, bitwise tests, resolver calls | High |
| Response wrappers produce two 48-byte packets and reach common handoff | Stack allocation, virtual calls, direct JAL | High |
| Pre-packet helper publishes record `+0x10` rather than deactivating a list | All six encoded calls to live `0x00787D80` and its complete leaf; separate `+0x1F4` callback pointer to live `0x00787DB0` | High |
| No constant-displacement wider/partial tag store or exact tag-address formation occurs in scoped BTL text | Byte scan of 486,832 aligned text words; arbitrary rebasing and generic copies remain outside the result | High for the stated negative only |
| Submission records are 0x50-byte spherical volumes | Resident initialization and direct radius/distance overlap bodies | High |
| Resident DD* layer performs a distinct geometric broad/narrow split | All-pairs traversal proceeds from mask gate directly to sphere overlap | Not established; evidence favors a single pass |
| Resident segment/environment layer has hierarchical broad/narrow phases | Object/group/primitive AABBs followed by directed triangle tests | High |
| Midpoint vectors are final contact points | Arithmetic is proven; semantic role is not | Medium-low hypothesis |
| BTL 0xA0 triangle record matches the resident environment primitive format | Identical stride/fields and resident field-by-field consumption | High |
| BTL triangle updater rebuilds primitives installed in the resident environment chain | `0x001BAB40` model lookup, environment object `+0x0C` dataflow, and paired `0x001BAEE0/0x001BAC60` unregister/register wrappers | High |
| Height-query selector consumes entity stage section | Both direct wrapper callers and signed `+0x9F6` selector loads | High |
| Stage first/second line families have recovered original gameplay names | No name-to-family proof | Unproven |

Additional useful negative results:

- the preserved labels at encoded internal live targets are frequently
  0x40-late fragments, not alternate function variants;
- resident body inspection establishes `0x001DDA50` as list deactivation and
  unlinking, not a generic result-clear operation;
- result-category and compatibility bits are exact, but their original enums
  and gameplay names are not recovered;
- BTL call sites themselves contain no primitive-overlap math; the imported
  resident processor contains direct sphere/sphere math but no spatial
  partition, sweep-and-prune, tree, or grid in the inspected pass;
- not every candidate relation is directional, so a universal
  attacker/target interpretation would be misleading.

## `ccSkillHNW001` interaction records and accepted-event route

In this section, unprefixed BTL addresses are live and `D` marks a preserved
Ghidra address (live minus `0x40`). [Battle entities](battle_entities.md#ccskillhnw001-skill-actor)
owns the actor's identity, creation and local states;
[Combo accounting](combo_accounting.md#repeated-event-contribution-in-ccskillhnw001)
owns its pending-hit contribution.

### Borrowed interaction records

The descriptor row for resource `165` is at `0x008ADE08` (`D 0x008ADDC8`).
It stores count `4` and fixed definition pointer `0x008ACB10`
(`D 0x008ACAD0`). The count belongs to the row beginning four bytes before
the pointer table's indexing base. Definitions have stride `0x44`; mutable
runtime records have stride `0x68`, as in
[Definition-to-runtime copy](#definition-to-runtime-copy).

The auxiliary owner's preallocation helper `D 0x0077DDD0` / `0x0077DE10`
maps fighter selectors `+0x184/+0x186` to resource indices and allocates an
absent entry for both sides. For index `165`, count `4` requests `0x1A0`
bytes in each admitted side bank. These entries live at owner
`+0xBA8+side*0x314+index*4`; repeated admission retains an existing pointer.
Setup and session ownership belong to
[Battle lifecycle](battle_lifecycle.md#setup-helpers-after-fighter-publication).
Owner destruction `D 0x00777460` loops over both sides and all `0xC5`
entries, frees nonnull pointers and clears their slots (returning bytes
`D 0x007774A0..0x00777507`).

HNW activation at `D 0x0085D6AC..0x0085D6C3` calls descriptor builder
`D 0x00787870` / `0x007878B0` with actor, context `actor+0x3B0`, header
`actor+0x200`, and index `3`. The builder stores the borrowed runtime pointer
`bank[index]+3*0x68` at actor `+0x210`, the fixed definition pointer
`definition+3*0x44` at `+0x214`, and index `3` at `+0x218`. It initializes
that mutable record from the definition and repeats its pointer in the
descriptor. Raw bytes `D 0x00787870..0x00787A07` preserve both pointer
calculations and the continuation omitted after the linked-fighter
predicate. These stores borrow the auxiliary owner's allocation; the builder
does not create an actor-local copy. Earlier common binding at
`D 0x0078E840..0x0078E863` invokes the same builder with index `0` when the
fixed definition pointer exists, initializing the first runtime record
before HNW's activation selects record `3`.

HNW update state `2` writes halfwords `+0x30/+0x32` through the **first**
runtime record of the side/resource entry (`D 0x0085E490..0x0085E508`),
distinct from the activation's selected record `3`. No per-actor copy or
unique ownership of either record is established. Later mutations through
other aliases and simultaneous reuse remain unresolved. The descriptor
contract is in [Active descriptor headers](#active-descriptor-headers).

### Accepted-event callback and descriptor update

The HNW event receiver `0x0085D9B0` (`D 0x0085D970`) occupies primary table
slot `+0x1A0` at resident `0x005E21C0`. The common actor accepted-event
helper starts at `D 0x00787A10` / `0x00787A50` and ends by invoking that
slot with the actor as `a0`, at `D 0x00787C08`. Its guarded-target branch
also reaches the callback join. Its ordinary branch first performs the
accepted-event tally and accumulated-word flush described by
[Match outcomes](battle_statistics.md#accepted-ninjutsu-and-combo-flushing).
Bytes `D 0x00787A10..0x00787A77` and disassembly through `D 0x00787C2C`
establish this indirect route; it does not require a direct JAL to the HNW
receiver. The full collision and authored-registration admission predicates
into this common helper remain incompletely explored.

The common active-descriptor updater has true entry `D 0x00788BE0` /
`0x00788C20`. Its entry requires actor `+0x20C` bit `0`; two returning
continuations call the accepted-event helper at `D 0x007891EC` and
`D 0x007894CC`. The first local branch also requires signed runtime record
`+0x30` nonzero and signed `+0x2E < 2` before its two preceding
descriptor-service calls. The second calls the helper after an optional
increment of header `+0x18`; that increment is skipped when a valid linked
target has nonzero `+0x95A`, but the helper call still follows. Bytes
`D 0x00789170..0x00789203` and `D 0x00789470..0x007894D3` establish these
joins. They do not enumerate the updater's earlier admission conditions or
prove that every receiver invocation corresponds to a newly delivered
authored event.

The receiver compares word actor `+0x230` with signed-halfword threshold
`+0x224` before setting `+0x1174`, and forms a descriptor pointer as
`actor+0x21C` at `D 0x0085D994`. These fields belong to the active
interaction descriptor. The comparison does not establish a timer or a
duration in frames or seconds.
