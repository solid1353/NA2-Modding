# Collision and hit-query infrastructure

Static reverse engineering of the clean NA2 v2.28 `BTL.BIN` interaction-query
layer. This document stops at the response-packet handoff boundary. It does
not interpret downstream damage, scaling, status, substitution, animation, or
projectile-specific behavior.

## Research coverage

- **Assigned scope:** the clean NA2 `BTL.BIN` collision and hit-query
infrastructure: shape/volume records, registration and removal, query/result
records, candidate production, participant filtering, response handoff, and
separable stage-boundary queries. The stopping boundary was the first common
response-packet handoff; downstream gameplay application was not followed.

- **Exploration depth:** coverage was **bounded and gap-oriented, not an exhaustive disassembly of the
entire overlay**. The clean `PRG/BTL.BIN` and resident `SLPS_258.37` assets were
checked against their preserved C/text exports, and raw bytes were used whenever
the header-skipped import omitted a body or attached a live target to the wrong
0x40-late symbol. Within the bounded functions below, instruction paths, field
writes, direct callees, and relevant loop bounds were inspected in full unless
the row says “sampled.”

| Area actually explored | Coverage depth and concrete boundary |
| --- | --- |
| Overlay mapping | Complete for the two scoped clean assets and every overlay-local address cited here: full 0x40-byte `MWo3` header, `live = raw + 0x006B3F00`, and `live = preserved export + 0x40`. Encoded direct targets used in this document were normalized against raw bytes. |
| Manager and registries | Full bodies for manager allocation/init/destruction, two-primary and two-by-32 auxiliary registries, high/low auxiliary insertion, cleanup, selective removal, candidate aggregation, and the main frame consumer; constructor callers were sampled to prove both insertion variants without classifying every object type. |
| Resident DD* interaction lists | Full relevant bodies from resident `0x001DCA40..0x001DE1C0`: 0x24 list heads, 0x34 registrations, 0x40 results, global activation chains, generation-safe resolution, all-pairs mask gating, sphere overlap, result emission, and cleanup. BTL registration/update callers were representative rather than exhaustive. |
| Spherical volumes and proximity caches | Full 0x50 record initializer/resolver and direct DD* overlap math; full generic BTL snapshot builder/reset and all direct references recovered for the four cache-count fields. Three inline cache appenders and the two direct proximity consumers were inspected; callers reachable only through computed addresses were not exhaustively enumerated. |
| Result snapshots and candidate masks | Full 0x40 result/snapshot copy and resolver, both bucket classifiers, primary and auxiliary mask producers, manager aggregation, and the three pair-filter families. Fixed loops, mask equations, backlink offsets, and generation checks were traced exactly. |
| Active interaction records | Full resident base initializer, 0x44-definition to 0x68-runtime copy, primary/auxiliary descriptor builders, raw-only installers, and terminal removal blocks. Higher-level activation-wrapper invocation remains indirect/computed and was not recovered. |
| Response boundary | Full ordinary primary/primary, primary/auxiliary, and auxiliary/auxiliary packet wrappers; full common 0x30-packet handoff and contact-reconciliation bodies; representative pending-slot production/consumption. Analysis stops before later gameplay handling. |
| Resident environment geometry | Full relevant environment-object lifecycle, packed object/group/0xA0-triangle hierarchy, segment AABB hierarchy, triangle narrow phase, 0x60 candidate emission/selection, and swept-sphere branch used by the 0x50 resolver. Capacity and unwritten candidate fields were audited directly. |
| BTL triangle caches | Full 0xA0 builder and updater, both coherent raw updater callers, model-name lookups, and resident environment register/unregister ownership edges. Direct-call/reference searches found no edge to the interaction manager or `ccBg*` control. |
| `ccBg*` stage cluster | Full or clean-raw-recovered bodies for `0x006C1BC0`, `0x006C1E50`, `0x006C2310`, `0x006C25B0`, `0x006C28D0`, `0x006C29E0`, `0x006C33C0`, `0x006C3750`, and `0x006C3FD0`, plus four resource callbacks through live `0x006C46D0`. Segment, boundary, vector, selector, query, and teardown fields were mapped; unrelated background rendering was not inspected. |

- **Confirmed coverage:** the exact manager/registry layouts;
0x50 spherical-volume and 0xA0 triangle formats; the absence of an evidenced
separate spatial broad phase in the resident DD* all-pairs processor; the
distinct hierarchical broad/narrow phases in resident environment queries;
0x40 results and snapshots; fixed candidate-mask reductions and compatibility
equations; 0x44/0x68 interaction records and parallel activation lifecycles;
0x30 response packets and their common handoff; stage family-A/family-B segment
chains, boundary records, builders, queries, and cleanup; and exact live/export/
raw address conventions.

- **Unresolved or untested:** original enum/class/field
names, the semantic meaning of several opaque interaction-record fields,
higher-level indirect callers of the activation wrappers, the writer and wider
meaning of the resident global acceptance gate, any computed-only writers of
the stage selected-index bytes, and the gameplay meaning of stage family and
selector numbers. No direct ownership edge was proven between the BTL triangle
cache and either the interaction manager or `ccBg*`; that negative result is
not proof that no indirect engine-level relation exists.

- **Deliberate exclusions and overlap:** Adventure mode; damage formulas or scaling;
substitution; timing and animation; widescreen/camera; media and localization;
projectile-specific ownership; status effects; and downstream response or
damage-application semantics. Those boundaries also avoided duplicating the
scoped work owned by other concurrent research documents.
- **Evidence limitations:** all validation in this document is static: no runtime allocation capture, mask transition trace,
collision replay, or stage-query probe was performed. Consequently, arithmetic,
field accesses, call edges, capacities, and static negative searches are strong
evidence, while recovered gameplay names and any claim about behavior outside
the inspected call graph remain intentionally limited.

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
`ccBg*` background manager. Those systems are kept separate below.

All findings are static unless explicitly stated otherwise. No runtime probe
was performed for this research pass.

## Inputs and address conventions

| Input | Size | SHA-256 |
| --- | ---: | --- |
| `@source_na2/PRG/BTL.BIN` | `2,237,184` (`0x222300`) | `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` |
| `@source_na2/SLPS_258.37` | `5,273,256` (`0x5076A8`) | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |

The clean file is an `MWo3` image whose complete 0x40-byte header is loaded at
live EE address `0x006B3F00`. Header words give text size `0x001DB6C0`, data
size `0x00046C00`, BSS size `0x00006E80`, and constructor interval
`0x008D6180-0x008D61A4`. The effective BTL reservation ends at `0x008DD080`.

The preserved Ghidra import skipped the header and therefore displays every
overlay payload byte 0x40 below its actual live address:

```text
raw_file_offset = live_address - 0x006B3F00
live_address     = preserved_export_address + 0x40
```

Encoded absolute pointers and `j`/`jal` targets in BTL are already live
addresses. Resident addresses are also unaffected. This distinction matters:
Ghidra frequently assigns the encoded live target to bytes 0x40 later and
creates a false overlapping `FUN_*` label. Tables below use `export -> live`
for a preserved full-body symbol. A live-only entry means the correct raw body
was recovered across an omitted or split export region.

The clean resident main executable was inspected only for the fixed services
called by BTL. Its addresses use the ordinary resident mapping and need no
overlay correction.

See [`../runtime/overlay_abi.md`](../runtime/overlay_abi.md) for the loader and
mapping proof. Function names here are stripped-project labels or descriptive
working names, not original developer symbols.

## Interaction manager and object registries

### Manager lifetime

| Preserved full-body export | Live | Raw | Established behavior |
| ---: | ---: | ---: | --- |
| `FUN_00776A90` | `0x00776AD0` | `0x0C2BD0` | Allocates `0x3330` bytes through resident `0x00117150`, calls live `0x00777130`, and publishes the returned manager through `iGpffffce54`. The exporter omitted the post-allocation instructions; the clean raw bytes preserve them. |
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
`FUN_007AFFC0` / live `0x007B0000`, raw `0x0FC100`. Ghidra incorrectly split
its continuation at displayed `FUN_007B0000`; raw address `0x0FC160`, live
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
would exceed the evidence. A decompiler-wide search for direct accesses to the
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
overwrite one another but cannot replace a nearer member of the first 32.
`FUN_001BF620` chooses the smallest `+0x20`, publishes the initialized and
selected portions at resident globals `0x0061F6A0..0x0061F6FC`, copies chosen
`+0x00..+0x0C` to endpoint 2, and returns chosen `+0x20`. It copies
`+0x24..+0x2C` and `+0x4C` even though the segment path does not initialize
them, while skipping `+0x34..+0x3C`; consumers must not assume a fully fresh
0x60-byte public record. Side-channel word `0x0061F6E8`, repeatedly read by
BTL, is specifically the chosen primitive's flags, not an unspecified query
token.

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
`+0x60`, and `+0x64` before applying source values. Builders separately consume
definition `+0x28` to fill runtime `+0x24` through an unresolved helper reached
at live `0x00781040`; it is not part of this constructor's copy sequence, and
the exact transformation is not established. The helper's correct raw body
begins at the bytes corresponding to preserved display `0x00781000`; the
apparent empty `FUN_00781040` export is 0x40 late and does not prove a no-op.
Only the compatibility uses of runtime `+0x60/+0x64` and the
type/category-like use of byte `+0x2C` are established here. Other gameplay
meanings are deliberately left unnamed.

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

Both activation edges use clean-raw leaves omitted from the preserved C
export. Each wrapper first requires the prepared-descriptor byte at header
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

This is the missing nonzero write to primary `+0x208` / auxiliary `+0x908`
and flags bit 0 at `+0x20C/+0x90C`. Each leaf has only its corresponding
direct wrapper callsite above; no literal or direct-call xref to either wrapper
occurs in the clean overlay, so their higher-level invocation is indirect or
relocated and remains unresolved. The preserved label `FUN_00789600` is not
the primary leaf: it is a 0x40-late fragment inside the next large body. The
nearby live `0x00780E00` routine remains the distinct resident-submission
bridge described above.

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

All three pair filters reject while resident `0x001EC290()` returns 1. That
resident body is exactly `return *(s32 *)0x00607674 != 0`: it reads no pair,
mask, record, or geometry state. No writer for `0x00607674` was recovered in
the inspected resident body, and the BTL export has no direct reference to
that address. Its wider state-machine meaning is therefore unknown, but its
collision-facing effect is an engine-global acceptance disable rather than a
per-object filter.

### Primary versus primary

The filter reads each active record only when pointer `+0x208` is nonnull and
flags `+0x20C` bit 0 is set. It then applies:

1. a resident global gate: `0x001EC290() == 1` rejects the candidate;
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
with its pair-specific exclusion bit, then calls live `0x0077A550` (full body
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
high-bit compatibility family. Special classes call live `0x0077A080`
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
3. transition/clear an embedded query list through live `0x00787DB0`
   (`FUN_00787D70` export, raw `0x0D3EB0`);
4. invoke object virtual preparation callbacks;
5. ask each participant to fill a 48-byte stack response packet (auxiliary
   interface `+0x8C`; primary interface `+0x240` in the observed paths);
6. order the participants by side and call the common handoff at live
   `0x0077B350` (`FUN_0077B310` export, raw `0x0C7450`);
7. invoke participant post-handoff callbacks.

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

The combiner is `FUN_007731D0` (export) / live `0x00773210`. When both packet
tags are zero it writes the midpoint of the two packet `+0x10` anchors to
manager `+0xB00`. Other tag combinations reconcile the two packet `+0x20`
positions, call resident segment/environment query `0x001BF100` where needed,
mutate packet `+0x20`, and write the selected or midpoint vec4 to manager
`+0xB00`. Its helper `FUN_00773040` / live `0x00773080`, raw `0x0BF180`, builds
a short vertical segment, calls `0x001BF100`, writes a corrected position, and
returns a signed displacement. These routines establish a contact/result
reconciliation phase; they still do not expose upstream candidate-overlap math.

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
with high confidence. An outer control object holds the inner system pointer at
`+0x70`.

### Background-system fields

| Inner-system offset | Established layout |
| ---: | --- |
| `+0x10` | next family-B boundary slot/record count; live `0x006C3750` uses it as a 0/1 index and increments it after insertion |
| `+0x20/+0x30` | vec4 left/right aggregate extrema selected from the fixed line-min/line-max markers by x comparison |
| `+0xA30` | interface/vtable-like pointer; destructor writes `0x005DD6A0` |
| `+0xA40/+0xA50` | vec4s resolved from `DMY_linemin01` / `DMY_linemax01` |
| `+0xA60/+0xA70` | vec4s resolved from `DMY_linemin02` / `DMY_linemax02` |
| `+0xA80/+0xA84/+0xA88` | pointer-vector capacity/size/data for 0x40-byte boundary records |
| `+0xA8C/+0xA8D` | family A counts for selectors 0/1 |
| `+0xA8E/+0xA8F` | family A selected indices |
| `+0xA90/+0xA94` | family A pointer tables |
| `+0xA98/+0xA99` | family B counts for selectors 0/1 |
| `+0xA9A/+0xA9B` | family B selected indices |
| `+0xA9C/+0xAA0` | family B pointer tables |

The neutral labels “family A/B” and “selector 0/1” avoid an unsupported player,
side, minimum, or maximum interpretation.

### Segment-node and boundary-record layouts

The 0x30-byte linked segment node is established by its builder and consumers:

| Offset | Field |
| ---: | --- |
| `+0x00` | endpoint A vec4 |
| `+0x10` | endpoint B vec4 |
| `+0x20` | next-node pointer |
| `+0x24` | zero/reserved word |
| `+0x28` | selector 0 or 1 |
| `+0x2C` | cached resident-query word, initialized to zero |

The 0x40-byte boundary record has:

| Offset | Field |
| ---: | --- |
| `+0x00` | pointer to a 0x0C capacity/size/data vector of 0x20-byte endpoint-pair pointers |
| `+0x10` | lower/first endpoint vec4 |
| `+0x20` | upper/second endpoint vec4 |
| `+0x30` | pointer to this record's `+0x10` endpoint (dereferenced as its x float) |
| `+0x34` | pointer to this record's `+0x20` endpoint (dereferenced as its x float) |
| `+0x38` | absolute x span between the two pointed endpoints |

The nested container stores count at `+0x04` and a pointer array at `+0x08`;
each allocated 0x20-byte member is exactly two vec4 endpoints at `+0x00/+0x10`.
Allocation, clean-raw construction, queries, and teardown all agree on these
sizes.

The complete boundary builder is `FUN_006C3710` / live `0x006C3750`, raw
`0x00F850`; displayed `FUN_006C3750` is the usual 0x40-late fragment. The
preserved export omitted most of its body, but the clean raw function runs
continuously through live `0x006C3ED4`. Its effective steps are:

1. Allocate and initialize the 0x40 record and its empty 0x0C endpoint-pair
   vector.
2. Use current system `+0x10` as slot 0 or 1, write family-B count
   `system[+0xA98 + slot] = 1`, allocate its one-entry pointer table at
   `+0xA9C + slot * 4`, and allocate `floor(resource_count / 2)` consecutive
   0x30-byte segment nodes. Descriptor type `0x23` or `0x24` chooses the
   resource-name base; other types take the assertion path.
3. Resolve each pair of generated marker names against the system resource,
   allocate a 0x20 endpoint pair, copy each resolved marker's vec4 at `+0x10`,
   append that pointer to the record's nested vector, and mirror the endpoints
   into one 0x30 segment node. Nodes are linked through `+0x20`, store the
   current slot at `+0x28`, and clear `+0x24/+0x2C`.
4. Copy the resolved boundary endpoints to record `+0x10/+0x20`, set
   `+0x30 = record+0x10` and `+0x34 = record+0x20`, and compute `+0x38` as
   their absolute x difference.
5. Append the record pointer to the system `+0xA80` vector through the
   live-only vector-insert helper `0x006C4040` (raw `0x010140`), then increment
   system `+0x10`.
6. Resolve fixed markers `DMY_linemin01`, `DMY_linemax01`,
   `DMY_linemin02`, and `DMY_linemax02` into `+0xA40..+0xA70`, selecting the
   lower x line-min vec4 into system `+0x20` and the higher x line-max vec4
   into `+0x30`.

Family B therefore assumes an even resource-element count: it allocates
`floor(count / 2)` nodes but advances through elements in steps of two, and no
odd-count guard is visible. Family A does not share that precondition; live
`0x006C33C0` allocates one 0x30 node per resource element.

Four resource callbacks provide the representative registration edge. The
full bodies `FUN_006C4540` / live `0x006C4580`, raw `0x010680`, and
`FUN_006C45A0` / live `0x006C45E0`, raw `0x0106E0`, call family B at live
callsites `0x006C45B0` and `0x006C4610`. `FUN_006C4600` / live
`0x006C4640`, raw `0x010740`, and `FUN_006C4660` / live `0x006C46A0`, raw
`0x0107A0`, call family A at live callsites `0x006C4670` and `0x006C46D0`.
Each obtains the current inner system through live `0x006C1640`; when that
returns null it calls resident `0x003947C0` on the supplied descriptor instead
of building a chain. The encoded builder targets are live `0x006C3750` and
`0x006C33C0`; the same-number preserved labels at those targets are interior
split artifacts.

### Stage query functions

| Full-body export | Live | Raw | Established behavior |
| ---: | ---: | ---: | --- |
| `FUN_006C1B80` | `0x006C1BC0` | `0x00DCC0` | Walks all family/selector chains, queries a vertical segment from midpoint z+100 to z-100 through resident `0x001BF100(…,1,0,0,-1)`, and on a non-`-1.0` result stores the chosen environment primitive's flags from `0x0061F6E8` at node `+0x2C`. |
| `FUN_006C1E10` | `0x006C1E50` | `0x00DF50` | In-place piecewise boundary resolver over two indexed 0x40-byte records; interpolates or clamps x/z and writes the supplied vec4. |
| `FUN_006C22D0` | `0x006C2310` | `0x00E410` | Clamps a vec4 to record `+0x10` or `+0x20` when x lies outside them; returns 0 when clamped and 1 when already inside. |
| `FUN_006C2570` | `0x006C25B0` | `0x00E6B0` | Height-envelope query over the selected family chains, detailed below. |
| `FUN_006C2890` | `0x006C28D0` | `0x00E9D0` | Initializes both families and reserves two slots in the boundary-record vector. |
| `FUN_006C29A0` | `0x006C29E0` | `0x00EAE0` | Frees nested boundary records, every family chain/table, and an owned object. Called by outer destructor `FUN_00708860`. |
| `FUN_006C3380` | `0x006C33C0` | `0x00F4C0` | Builds family-A 0x30-byte segment chains for descriptor types `0x25/0x26`; resolves marker names `DMY_line_010/020` and `DMY_linemin01/02`, `DMY_linemax01/02`. |
| `FUN_006C3710` | `0x006C3750` | `0x00F850` | Builds family-B segment chains and the nested 0x40 boundary record, inserts it into `+0xA80`, initializes self-referential endpoint/span fields, and refreshes fixed line extrema; recovered from the clean raw body. |
| `FUN_006C3F90` | `0x006C3FD0` | `0x0100D0` | Bounds-checked boundary-record vector accessor. |

`FUN_006C2570` takes `(system, selector, query_vec4, output_vec4)`. It starts
with no result and a minimum of `32767.0`. It checks the selected family-B
chain first, accepting the first node whose endpoints satisfy the strict
interval `A.x < query.x < B.x`; it linearly interpolates z and then proceeds to
family A. It scans all selected family-A nodes and retains the lowest
interpolated z. The output copies input x/y, writes the chosen z or the
`-32768.0` no-result sentinel, and writes w=1. Endpoints are excluded and this
path does not handle reversed-x segments.

`FUN_006C1E10` takes `(system, inout_vec4, record_A_index,
record_B_index)`. It refreshes record B `+0x38` from the absolute difference
between the x floats reached through B `+0x30/+0x34`, then computes
`ratio = abs(B.first.x - query.x) / B.span` and
`candidate_x = A.first.x + A.span * ratio`. A query on or before B's first x
copies A's first endpoint; a ratio above 1 or candidate x beyond A's second x
copies A's second endpoint. Otherwise it walks A's nested 0x20-byte endpoint
pairs, linearly interpolates z across the pair that contains candidate x, or
snaps to the nearer adjacent endpoint in the terminal fallback. All paths
mutate the supplied vec4 in place and return no status. The numerator-zero
case leaves ratio at zero, but there is no explicit guard against a zero B
span when the numerator is nonzero; valid resources therefore appear to carry
a nonzero x span.

The outer wrapper is `FUN_00708CA0` / live `0x00708CE0`, raw `0x054DE0`.
When outer `+0x70` is null, it returns the copied input with z=`-32768.0`, w=1;
otherwise it calls the core query. A representative caller at live
`0x0078D700` compares an object's candidate z with the returned surface z.

Other wrappers are `FUN_00708A40` / live `0x00708A80`, raw `0x054B80`, for
the clamp query, and `FUN_00709090` / live `0x007090D0`, raw `0x0551D0`, for
the piecewise resolver. The latter validates a record index against outer
`+0x7C` and returns success/failure around the core mutation.

Useful limitations:

- the cached node word `+0x2C` is not read by the height-envelope query;
- an aligned clean-raw load/store audit found only zeroing stores to the
  selected-index families, at live `0x006C2904` (`+0xA8E`) and
  `0x006C2918` (`+0xA9A`) in the initializer. Direct references elsewhere are
  loads at live `0x006C2610`, `0x006C274C`, `0x00708D78`, and `0x00708DB8`;
  a writer reached solely through a computed address cannot be excluded;
- the marker names support line-envelope intent but do not establish exact
  stage gameplay names for either family;
- this cluster does not implement or call the primary/auxiliary compatibility
  filters above.

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
Clean-raw inspection recovers two direct calls that the preserved export's
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
| Complete overlay mapping and `+0x40` preserved-import shift | Clean file header, loader/runtime mapping, raw JAL targets | High |
| Two-primary plus 64-auxiliary registry layout | Registration bodies, fixed loops, cleanup writes | High |
| 0x44 definition and 0x68 runtime interaction-record strides | Indexed builders and exact copy body | High |
| 0x40 query snapshot with generation-safe owner resolution | Raw copy and omitted resolver bodies | High |
| Candidate aggregation and filter order | Direct raw call graph and fixed loops | High |
| Mask equations and backlink offsets | Direct filter loads, bitwise tests, resolver calls | High |
| Response wrappers produce two 48-byte packets and reach common handoff | Stack allocation, virtual calls, direct JAL | High |
| Submission records are 0x50-byte spherical volumes | Resident initialization and direct radius/distance overlap bodies | High |
| Resident DD* layer performs a distinct geometric broad/narrow split | All-pairs traversal proceeds from mask gate directly to sphere overlap | Not established; evidence favors a single pass |
| Resident segment/environment layer has hierarchical broad/narrow phases | Object/group/primitive AABBs followed by directed triangle tests | High |
| Midpoint vectors are final contact points | Arithmetic is proven; semantic role is not | Medium-low hypothesis |
| BTL 0xA0 triangle record matches the resident environment primitive format | Identical stride/fields and resident field-by-field consumption | High |
| BTL triangle updater rebuilds primitives installed in the resident environment chain | `0x001BAB40` model lookup, environment object `+0x0C` dataflow, and paired `0x001BAEE0/0x001BAC60` unregister/register wrappers | High |
| Stage family A/B correspond to named min/max or player sides | No selector write/name proof | Unproven |

Additional useful negative results:

- the preserved Ghidra symbols at encoded internal live targets are frequently
  0x40-late fragments, not alternate function variants;
- resident body inspection establishes `0x001DDA50` as list deactivation and
  unlinking, not a generic result-clear operation;
- result-category and compatibility bits are exact, but their original enums
  and gameplay names are not recovered;
- BTL call sites themselves contain no primitive-overlap math; the imported
  resident processor contains direct sphere/sphere math but no spatial
  partition, sweep-and-prune, tree, or grid in the inspected pass;
- not every candidate relation is directional, so a universal
  attacker/target interpretation would be misleading;
- no runtime capture verified object allocations, mask transitions, or query
  results in this pass.

This document is the canonical disposition of the scoped static analysis. No
supporting scratch artifact or generated patch is required for the findings.
