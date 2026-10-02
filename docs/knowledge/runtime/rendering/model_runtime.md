# Model and skeleton runtime

This document investigates the model and skeleton runtime of retail NA2
(`SLPS-25837`): geometry readers and conversion, runtime instances, composition
hierarchy and bone matrices, animation binding and morphs.

## Research coverage

- **Assigned scope:** Mesh conversion and geometry interpretation, rigid/skinned models, skeleton hierarchy, bone matrices, morph integration and animation binding.
- **Exploration depth:** Bounded resident-ELF investigation of every accepted outer geometry route, ordinary/packed strip conversion, registered property conversion and CPU skinning, composition construction and matrix caching, model/animation rebinding, morph command consumers and destructors. Retained header tracing covers extra-pass owner construction, copying, binding, draw gates and destruction. Selected morph producers and both non-packed draw continuations were checked against the target-driven blend loop and property preparation. Instructions and resident bytes corroborate header copies, shared-owner copying, dispatch, packed scaling/influence fields, hierarchy multiplication, CPU weighting and morph arithmetic. Official NUN3 comparison covers the outer header and delegated packed/property/topology readers.
- **Confirmed coverage:** Model/part allocations and dispatch, retained versus temporary geometry, bone ordering and matrix publication, rigid and weighted property geometry, animation-to-node binding, the separate extra-pass blend selector and owned/borrowed snapshots, Q12 morph accumulation, target-count/source-part assumptions, source-buffer mutation and controller storage bounds, and the NUN3/NA2 packed-position scale difference.
- **Unresolved or untested:** Arbitrary mismatched morph-pair reachability and authored morph distributions; the later producer of property geometry's nonnull extra-pass owner; wider indirect consumers and later mutations of retained model state; and safe borrowed-resource lifetime across every owner transition remain unresolved. Full attribute semantics and asset-level maximum supported palette/influence counts are not established here; the selected VU/control/storage and shadow-topology results belong to their linked owners. Whole-file NUN3/NA2 model equivalence is not established; bounded reader agreement does not prove complete asset interpretation.
- **Deliberate exclusions and overlap:** [CCS runtime](../../game/files/ccs_runtime.md) owns container/parser framing and publication; [CCS object types](../../game/files/ccs_object_types.md) owns the tag ledger; [animation runtime](../animation_runtime.md) owns playback timing and interpolation; [texture and material runtime](texture_material_runtime.md) owns material/texture behavior. [Model VU programs](model_vu_programs.md) owns microprograms, strip-control consumers and packed storage bounds; [material render modes](material_render_modes.md) owns packet-state meanings; [shadow rendering](shadow_rendering.md) and [shadow VU program](shadow_vu_program.md) own the topology consumer and selected authored shadow distribution; [composition attachment dynamics](composition_attachment_dynamics.md) owns `0x2300` attachment chains. Complete-file identities remain in [Retail game file identities](../../game/files/file_identities.md).
- **Evidence limitations:** Static inspection of retail NA2 `SLPS_258.37` and official NUN3 `SLUS_217.27`. Working function names below describe behavior; they are not recovered symbols. Decompiler types are checked against instructions where scalar types or branch dispatch matter. This establishes the inspected code's contracts, not complete-file execution or the distribution of geometry modes in retail assets. Unexamined branches remain unknown.

## Evidence conventions

All NA2 addresses below are resident EE addresses in retail `SLPS_258.37`; see
[address conventions](../../game/files/file_identities.md#address-conventions). A record is the container's `0x38`-byte directory entry;
its type and runtime pointer are `+0x2a` and `+0x2c`. Geometry resources,
object descriptors and instantiated scene children are different allocations.

## Model loader and geometry routes

**Observation, high confidence:** `FUN_001b0c40` (`0x001B0C40..0x001B13FC`)
publishes tag `0x0800`. A zero part count publishes a null runtime pointer;
otherwise it allocates `0x60 + part_count * 0x40` bytes. The part table begins
at model `+0x60`, with a halfword count at `+0x5e`. Model `+0x00` points back
to its record; `+0x44` is a file float; `+0x48` contains decoded runtime
flags; `+0x4c` holds a signed-halfword header value converted to float (divided
by 256 for version `>=0x122`); `+0x54` is another file float when version
`>=0x111`, otherwise `1.0`.

The geometry selector is `(file_flags >> 1) & 7`, not the value used in the
decompiler's internal `s2` branch. Instructions `0x001B0F10..0x001B0F64`
and `0x001B1220..0x001B1304` establish this dispatch:

| File selector | Runtime flag added | Part prefix before delegated geometry | Converter |
| --- | --- | --- | --- |
| 0 | none | record ID whose record is cleared; dependency record ID at part `+0x04`; dword count at `+0x08` | `FUN_001b0790` |
| 1 | none | fail-fast null store | No accepted route established |
| 2 | `0x04` | dependency ID, count at `+0x08`, second count at `+0x2c` | `FUN_001aff20` |
| 3 | `0x10` | no common prefix read in this branch | `FUN_00181760`; stores result at `+0x30`, adds model flags `0x4a01` |
| 4 | `0x08` | resolves record ID zero as dependency; clears `+0x08` | `FUN_0018d740` |
| 5..7 | none | fail-fast null store | No accepted route established |

The source contains an internal `s2==3` route to `FUN_001add80`, but the
examined outer selector dispatch never assigns `s2=3`. Its reader contract is
not proof of reachability through this loader.

**Observation:** version `<0x100` masks file flags to eight bits. Version
`<0x121` consumes one extra byte, clears the optional byte-list count and
masks the second flag halfword to its low nibble; newer versions consume two
bytes. A nonzero byte-list count allocates 64 bytes, reads that many bytes,
zero-fills the remainder to 64 and aligns the reader to four bytes; the
pointer/count are model `+0x58/+0x5c`. This path has no visible count<=64
guard. Version `>=0x123` copies bits 2..3 of the second extra byte into
model byte `+0x53` bits 0..1. These select the model-owned extra-pass blend
entry described below; they are not the ordinary blend selector at `+0x5d`.

## Retained header state and instance lifetime

**Observation, high confidence:** source-model `+0x50` low 24 bits,
`+0x53 & 3` and float `+0x54` are copied into a distinct `0x18`-byte owner
at runtime model `+0x40`. `FUN_001992a0` first clears this pointer and runtime
ownership word `+0x1c`. After constructing all runtime parts, it can borrow
source property-geometry kind 2's `+0x38` owner from the **first part**, adding
runtime flags `0x8180` (`0x001993F0..0x0019943C`). With flags `&0x84 != 0`
and a null owner, it instead allocates a new owner and sets runtime ownership
bit `0x10000`. Only that owned case copies header width multiplier `+0x54`
to owner `+0x08`, color `+0x50 & 0xffffff` to `+0x0c`, and passes
`+0x53 & 3` to `FUN_001c44f0` (`0x00199444..0x001994CC`). A borrowed owner
does not receive these header assignments in this constructor.

`FUN_001c4510` initializes owner `+0x00` from table `0x005B5940`, width
multiplier to 1.0, color to zero and owner `+0x10` to 1. `FUN_001c44f0`
replaces only its first 64-bit word with `table[selector & 0xff]`; the
constructor restricts the supplied selector to 0..3. Table bytes establish
those entries as `0x44`, `0x48`, `0x42`, `0x09`. This is a two-bit **selector**,
not two independently demonstrated enable flags. Its extra-pass blend/state
meaning and the width/color consumers are owned by
[Extra model-owned blend state and FRAME restoration](material_render_modes.md#extra-model-owned-blend-state-and-frame-restoration).
Ordinary selection separately calls `FUN_001987a0` with source byte `+0x5d`
and writes runtime model `+0x30`; neither selector assignment writes the other
state in the inspected helpers.

**Ownership observation:** independently constructed runtime models that
allocate this owner get independent header snapshots. They are not references to the source
header's color/selector/width fields, and `FUN_00198290` copies flags/scale
to the draw context without refreshing them. Runtime destructor
`FUN_00199190` destroys its part table, then frees runtime `+0x40` only when
ownership bit `0x10000` is set. In the borrowed property case, source geometry
destructor `FUN_00181a30` frees geometry `+0x38`
(`0x00181A68..0x00181A78`); the runtime wrapper owns only itself. The inspected
property converter `FUN_00181ad0` finishes by clearing `+0x38`, so borrowing
a nonnull owner requires a later producer that is not yet identified here.
These destructors do not establish a reference count or make destruction of
the borrowed source safe while its instance still uses it. Later owner
mutations and wider indirect consumers are not exhaustively established.

**Observation — copied instances and binding:** `FUN_00198e30` is a distinct
runtime-copy path. It copies the existing instance's `+0x40` pointer, then
clears the new instance's ownership word `+0x1c`
(`0x00198F34..0x00198F3C`, corroborated by instruction bytes). It does
not reconstruct this owner from source `+0x50/+0x53/+0x54` or duplicate it.
Thus independent `FUN_001992a0` construction and copying an existing instance
have different owner lifetimes: the latter borrows the former's snapshot.
The copy also borrows the child array and copies scale/flags, while constructing
a separate runtime part table. `FUN_00196f80` can similarly copy a scene
node's primary/secondary runtime-model pointers and clear its corresponding
ownership bits. `FUN_00196990` destroys those models only for an owning node.
No reference-count increment appears in these inspected copy paths.

`FUN_00196620` installs an incoming runtime model at scene node `+0x94` and
clears scene ownership of it. Its branch requiring both models' flags
`&0x804 != 0` rebuilds the incoming bone mapping by record-name matching;
it does not refresh the incoming
extra-pass header snapshot or compare morph geometry. Scene construction
`FUN_00196b40` instead makes a new runtime model through `FUN_001992a0`.
Consequently scene attachment alone does not imply independent model storage.

**Observation — extra-pass gate:** `FUN_001982b0` snapshots global descriptor
`DAT_00602c08` into draw context `+0x248`. `FUN_001910e0` adds the extra-pass
request only when context model flag `0x80` is set, that descriptor is nonnull
and its halfword `+0x1c` is nonzero (`0x001914F4..0x00191524`). The header
selector does not replace these gates. Ordinary parts then reach
`FUN_001c3da0`; the packed delegate reaches `FUN_001c3750` when that request
bit is set. Whole-model admission remains owned by
[Visibility](visibility.md#ordinary-model-draw-boundary), and the selected
extra-pass VU operations by [Shared direction-offset programs](model_vu_programs.md#shared-direction-offset-programs).

## Ordinary geometry and strip conversion

**Observation, high confidence:** `FUN_001b0790`
(`0x001B0790..0x001B0C3C`) traps if runtime flags include `0x804`. It
always reads `count` signed XYZ halfword triples into part `+0x14`, aligns
to four bytes and updates six aggregate integer extrema. It then reads the
following arrays in order:

| Runtime condition | Input consumption | Part field |
| --- | --- | --- |
| `0x40` clear | one dword per vertex; also copies each dword's high byte to a separate byte array | `+0x18`; byte array `+0x24` |
| `0x200` clear | one dword per vertex; when flag `0x01` is set, discards the words after reading | `+0x1c` when retained |
| `0x400` clear | one dword per vertex | `+0x20` |

The byte array is used as strip-control data by `FUN_001b0140`: it walks
runs beginning with values 1 or 2 and continuing through zero markers;
depending on parity, it reverses the corresponding geometry/attribute run or
adds a duplicate vertex and reallocates the arrays. Thus the post-conversion
part count can differ from the file count. Conversion runs only when model
flag `0x02000000` is set and `0x04000000` is clear. The outer loader sets
these from the second header halfword's mode fields and bit `0x2000`.

The ordinary loader keeps these arrays and separately builds the packet at
part `+0x10`. `FUN_00194110` determines its size (stored as a halfword at
`+0x0c`); `FUN_00193ef0` initializes it, then `FUN_00193d80`,
`FUN_00193c80`, `FUN_00193b50` and `FUN_00193a70` insert geometry and
the respective arrays. The low 16 runtime-flag bits select packet layout.
The meaning of every attribute bit and the VU interpretation require the
downstream consumer; array width alone does not establish it.
Material binding, draw-time UV changes and packed material offsets are owned
by [Texture and material runtime](texture_material_runtime.md).

## Triangle topology conversion

**Observation:** selector 4 enters `FUN_0018d740` with no ordinary vertex
prefix. It reads two dwords: point count and index count. For nonzero point
count, it consumes one signed XYZ halfword triple per point into an eight-byte
temporary stride and updates the outer extrema, then aligns to four bytes.
It reads `index_count / 3` triples of dword point indexes. The integer quotient
is explicit; the examined loop has no separate read for a remainder.

The converter calls `FUN_0018e530` per triangle and `FUN_0018e240` three times
with cyclic permutations of the triangle indexes. It constructs triangle and
edge-related packet data at file part `+0x34`, byte length `+0x38`, and a
halfword count at `+0x0c`, then releases its temporary points/topology arrays.
Ordinary position/attribute pointers stay null. Several construction limits
can discard this packet and return 1; successful packet publication returns 0.
The outer model loader does not branch on that return. Container finalization's
secondary-model attachment, described below, is therefore a distinct contract
from the ordinary/packed mesh routes. The geometric meaning of every generated
edge/plane record and its complete draw consumer are owned by
[Shadow rendering](shadow_rendering.md#geometry-inputs-and-renderer-ownership)
and [Shadow VU program](shadow_vu_program.md), including
[Selected authored shadow topology](shadow_vu_program.md#selected-authored-shadow-topology).

## Packed geometry, influences and matrix palette

**Observation, high confidence:** selector 2 enters `FUN_001aff20`, which
constructs a `0x10`-byte polymorphic geometry object at part `+0x30` through
`FUN_001b0100`. The finished packet pointer and qword count are geometry
object `+0x08/+0x0c`. Part `+0x10/+0x14/+0x18/+0x1c/+0x20/+0x28`
remain null. Temporary reader arrays are freed by `FUN_001af150` or
`FUN_001ae0e0` after packet publication.

| Part second count `+0x2c` | Reader and consumed payload | Converter |
| --- | --- | --- |
| zero | `FUN_001af1f0`: one dword selecting a matrix; `vertex_count` XYZ signed-halfword triples; align to four; one dword per vertex; one further dword per vertex transformed as `(word & 0x0fff0fff) << 4` | `FUN_001af9d0`, batches of at most `0x36` vertices |
| nonzero | `FUN_001ae190`: eight-byte influence entries, grouped into one list per logical vertex; one dword per declared influence; one dword per vertex transformed with the same mask/shift | `FUN_001ae950`, batches chosen by `FUN_001ae770`/`FUN_001ae7d0` |

`FUN_001ae190` stores each logical vertex as a `0x10`-byte temporary
record containing influence-pointer, attribute-pointer, UV-word-pointer and
influence count. Byte 7 bit 1 of each eight-byte influence terminates its
list; the reader continues while that bit is clear (`0x001AE34C..0x001AE36C`).
The first six influence bytes are signed XYZ halfwords. The converter emits
three halfwords per influence: `(halfword_at_6 & 0x1ff) << 4`,
`0x50 + 4 * (byte_7 >> 2)`, and the list count for the first influence
(1 for subsequent influences). Exact instruction evidence is
`0x001AEB08..0x001AEB38`.

**Inference, high confidence:** the low nine bits encode an influence weight,
and the upper six bits of byte 7 encode a matrix-palette index. This follows
from the influence grouping and generated weight/index stream together with
the draw-time matrix upload below. It does not establish normalization or the
maximum supported influences per vertex. The selected downstream accumulation
rule is owned by [Packed influence evaluation](model_vu_programs.md#packed-influence-evaluation).

Both converters emit positions as float XYZ multiplied by model
`+0x44 / 4096.0`. This scalar is established by the caller's divide and the
converters' signed-halfword loads, `cvt.s.w`, `mul.s` and `swc1`
(`0x001AFC70..0x001AFCC8`, `0x001AEC6C..0x001AECC8`). The nonzero
branch emits influence data, positions, per-influence dwords, then transformed
per-vertex UV words. The zero branch emits positions, per-vertex dwords and
UV words, with one shared matrix selector `0x50 + 4 * selector`.
Before conversion, the same `0x02000000`/`0x04000000` gate can run strip
normalization (`FUN_001af450` or `FUN_001ae430`), including run reversal
or duplication. The packets therefore need not retain original vertex order.

`FUN_001ae770` counts complete logical-vertex lists until
`3 * (influences_so_far + vertices_so_far) + 1 > 0xda` or the input ends;
`FUN_001ae7d0` sums the influence counts in the selected span. The vertex
that crosses the threshold is included in the returned batch
(`0x001AE790..0x001AE7CC`). This is a packet batching rule, not an established
per-vertex influence limit. The decompiler omits the caller's third argument
in some displays; the helper's instructions explicitly compare against `a2`.

**Observation:** runtime model `FUN_001992a0` stores the composition child
array/count at `+0x10/+0x14`, part count at `+0x16`, and copied model flags
at `+0x18`. Draw dispatcher `FUN_001910e0` sends flag-`0x04` models to
`FUN_0018ffb0`. That producer uploads one 64-byte matrix per palette entry,
using command `0x6c000050 | ((count & 0x3f) << 18)`. With model byte-list
count `+0x5c==0`, it uses the composition child order; otherwise each byte at
model `+0x58` selects a child index. A null child emits an identity matrix.
A nonnull child has its accumulated matrix refreshed and combined with the
draw context by `FUN_00152020`. The uploaded matrix addresses start at
`0x50` and advance by four vector slots, matching the generated index field.
No range check on the byte-list index was visible in these branches.
[Packed palette and influence storage bounds](model_vu_programs.md#packed-palette-and-influence-storage-bounds)
distinguishes representable storage from enforced admission; its
[source strip controls](model_vu_programs.md#source-strip-controls-and-their-selected-consumers)
section owns the selected control interpretation. Those results do not supply
an omitted CPU bounds check.

**Observation — bounds limitation:** `FUN_001aff20` does not propagate the
temporary converters' extrema into the outer loader's six extrema passed in
register `t0`. Its inspected body reads no fifth argument, and both temporary
destructors only free arrays. The outer loader still expands that extrema
buffer for flags `0x804` and calls `FUN_0019b3a0`; `FUN_001992a0`
also clears its ordinary bounds pointer for the same flags. This
establishes the scoped data flow; it does not establish how all packed models
are culled elsewhere. [Visibility](visibility.md) owns that question.

## Composition hierarchy and matrix lifetime

**Observation, high confidence:** `FUN_001b1560` constructs a composition
descriptor with halfword child count at `+0x08`, child record array at `+0x0c`
and one `0x30`-byte initial transform per child at `+0x14`. Version
`>=0x110` reads nine floats per child: position at transform `+0x00`, Euler
rotation at `+0x10` converted from degrees to radians, and scale at `+0x20`.
Older versions keep the initialized transform from `FUN_001b1860`: zero
position/rotation and unit scale.

Container finalization `FUN_001ad240`, specifically
`0x001AD354..0x001AD450`, allocates a signed-halfword parent table at
composition `+0x10`. It compares each child's descriptor `+0x04` parent
record against the entire child-record array. A match becomes that child
index; no match becomes `-1`. This relation is by record identity, not a bone
name or position in the file. The later finalization pass can remove a
flag-`0x08` geometry child, attach its model as its parent's secondary model
and adjust subsequent parent indexes; the published composition is therefore
not necessarily the original file child list.

`FUN_001952f0` constructs the scene composition with child pointer array
`+0x98` and count `+0x9c`. It resolves wrappers and instantiates `0x0100`,
`0x0d00` and `0x0e00` child types. For `0x0100`, the constructor allocates
a scene child of `0xb0` bytes and initializes it through `FUN_00196a60`;
`FUN_00196b40` binds its primary runtime model at `+0x94` and optional
secondary runtime model at `+0x9c`.
`FUN_00195600` then writes each child's parent pointer at `+0x80`: parent
index `-1` selects the containing composition, otherwise the indexed child.
The composition's optional `0x2300` attachment chains, which `FUN_001952f0`
constructs after evaluating its children, are described in [Composition attachment dynamics](composition_attachment_dynamics.md).

| Scene-node field | Established contract |
| --- | --- |
| `+0x00..+0x3f` | Accumulated 4x4 matrix |
| `+0x40..+0x7f` | Local 4x4 matrix |
| `+0x80` | Parent scene-node pointer; zero for an unattached root |
| byte `+0x8d` | Matrix dirty flag |
| halfword `+0x8e` | Instantiated object type |
| `+0x90` | Source object record |

`FUN_0019cd80` initializes both matrices to identity, clears the parent and
sets dirty to 1. `FUN_00195510` applies composition initial transforms via
`FUN_0019cb70`; that helper writes the local matrix and sets dirty to 1.
Its instructions load the scale diagonal, pass the rotation vector in `a2`
to `FUN_001525b0`, then add translation through `FUN_00152270`.
`FUN_001525b0` applies the Z, Y and X rotation helpers in that order
(`0x001525C8..0x001525F8`). This call/axis order comes from the instructions,
not the caller decompiler's incomplete argument display.

**Observation — cache algorithm:** `FUN_0019c7c0`
(`0x0019C7C0..0x0019C8C4`) follows parent links upward, storing node pointers
in VU0 memory and remembering the highest dirty node. It starts from the
accumulated matrix of that node's clean parent, or the local matrix when no
parent exists, then walks back toward the requested child. Each local column
is multiplied by the parent matrix's four columns using `vmulax`, `vmadday`,
`vmaddaz`, `vmaddw`; the result goes to node `+0x00..+0x30` and dirty is
cleared. In column-vector notation this is `world = parent_world * local`.
It has no visible cycle detection or hierarchy-depth guard in the inspected
66-instruction body. This is a bounded algorithm observation, not a malformed
file execution result.

An unattached scene node is handled separately by `FUN_00190f40`: it copies
the local matrix to the accumulated matrix and clears dirty. The same
root/parent distinction is used for each palette child in `FUN_0018ffb0`.
Thus bone matrices use the ordinary scene-node hierarchy rather than a
separate skeleton-matrix allocation in these paths.

**Observation — rebinding:** `FUN_001a1c80` temporarily publishes scene-child
pointers in resolved records' `+0x30` fields. It allocates a new runtime model
`+0x10` array in the order of the source model's composition (`model +0x40`),
copies that composition's records' published pointers, then clears the temporary
publications. Runtime ownership bit `+0x1c & 0x40` marks the replacement array.
The helper does not write the runtime child-count halfword. This establishes
an explicit mapping between model bone order and materialized scene nodes;
an arbitrary scene array is not automatically the model's palette order.

## Property geometry and CPU skinning

**Observation, high confidence:** file selector 3 uses `FUN_00181760` to read
a dependency record ID and dword property count, then a 12-byte header per
property. Each temporary property occupies `0x14` bytes, with selector byte
`+0`, element-type byte `+1`, flags byte `+2`, count dword `+4`, computed byte
length `+0x0c` and payload pointer `+0x10`. `FUN_00181520` calculates bytes as
`(flags & 0x0f) * element_width * repetitions`; repetitions are 1 when
`flags & 0x10` is set, otherwise the count. It consumes rounded-up dwords and
zeroes unused bytes in the last word.

| Element-type byte | Width in bytes established by this reader |
| --- | --- |
| `0x00`, `0x07` | 1 |
| `0x01`, `0x08` | 2 |
| `0x02`, `0x09`, `0x0e`, `0x21` | 4 |
| `0x03`, `0x0a`, `0x20` | 8 |
| `0x22` | 64 |

The property selector and element type are independent fields. Their numeric
values must not be interchanged. Unknown element types have no established
width contract from the decompiler.

`FUN_005d6950` registers kind 1 with factory `FUN_00181930`; both registration
and reader use `gp-0x359c` for the registry head (instructions
`0x005D6958..0x005D6988`, `0x00181840..0x00181874`). The factory constructs
a `0x3c`-byte geometry object with tag 2 and vtable `0x005D9D80`. Its `+0x0c`
slot is `FUN_00181ad0`, so the following converter is a registered reader
consumer, not merely a nearby candidate. The reader releases all temporary
property payloads after applying it.

| Property selector | Converter result |
| --- | --- |
| `0x11` | Halfword geometry indexes at object `+0x10`; count at `+0x0c`, also copied to file part `+0x08`. |
| `0x05` | Byte control array at object `+0x18`. |
| `0x04` | Separate four-byte-per-index array at file part `+0x20`, copied without numeric conversion. |
| `0x21` | Rigid vertices: extracts XYZ halfwords into object `+0x28`; consecutive equal `byte_7 >> 2` bone indexes become `{bone_index, run_count}` halfword pairs at `+0x24`. Vertex/run counts are `+0x1c/+0x20`. |
| `0x22` | Eight-byte weighted influences retained at `+0x34`; influence count at `+0x30`, logical vertex count at `+0x2c` from byte 7 bit 1 terminators. File part `+0x2c` receives the influence count. |
| `0x24`, `0x25` | Three-byte vectors expanded to four-byte entries at object `+0x14`, rigid entries first, then one per weighted influence. Fourth byte is zero. |

The converter puts these geometry arrays in one allocation rooted at object
`+0x10`; its attribute allocation size uses rigid vertices plus **influences**,
not logical weighted vertices. `FUN_00182160` creates an eight-byte runtime
wrapper whose first word borrows the source geometry object. Its destructor
`FUN_00182220` releases the wrapper, while source destructor `FUN_00181a30`
owns the geometry allocation.

**Observation — evaluated geometry:** for runtime model flag `0x0800`,
`FUN_001910e0` builds a matrix workspace through `FUN_00192040` and prepares
each part through `FUN_001921c0` (`0x001921C0..0x00192694`). The latter
allocates float positions and vectors for `rigid_count + weighted_vertex_count`.
Rigid XYZ is scaled by model scalar `/4096`, given homogeneous W=1, and
multiplied by its run's bone matrix. Its three signed attribute bytes are
converted as byte `/64`, given W=0 and transformed by that matrix.

Weighted XYZ uses the same position scale. Each influence selects matrix
`byte_7 >> 2` and adds `matrix * position * ((halfword_6 & 0x1ff)/256)`
to the position accumulator. The three signed vector bytes are transformed
with W=0 and added **without that weight multiplication**. At byte 7 bit 1,
the position is emitted and the vector sum is normalized by its length, then
both accumulators are reset. Instructions `0x001924C8..0x00192574` establish
the different accumulation rules; `0x00192578..0x00192600` establishes the
terminator and normalization. No position-weight-sum normalization is present
in this loop. The direction-vector treatment supports interpreting properties
`0x24/0x25` as normals; that is a high-confidence inference from the consumer.

The workspace uses the runtime model child array, refreshes each child's world
matrix and emits identity for null children. `FUN_00192040` first calls matrix
inversion helper `FUN_00190bc0` on the matrix addressed by context `+0x110`,
then forms `workspace_matrix = inverse(context_matrix) * child_world` through
`FUN_00152020`. It also fills identity entries
below the geometry object's recorded highest bone index when that index exceeds
the child count. The converter records the highest index itself, not index+1;
the fill loop uses a strict less-than comparison. This is the observed bound,
not proof that a missing highest-index bone is initialized. After conversion,
`FUN_001921c0` sets draw flags `0x7000`, scalar 1.0 and passes indexes/control
data to `FUN_00193270`, then frees the float allocation.

## Animation binding to scene nodes

**Observation:** `FUN_001a29d0` builds an animation's record/track pairs and
signed-halfword parent relation map. `FUN_001b99b0` separately builds the
player's 16-byte entries at `player +0xfc`: runtime target `+0`, resolved
record `+4`, type halfword `+8`, flags byte `+0x0a`, evaluator allocation
`+0x0c`. It uses temporary source/resolved record `+0x34` publications while
binding, and clears them before returning.

With player flag `+0xf7 & 2` clear, existing `0x0100` scene children are bound
through source-record identity in the player's composition list `+0xe4`.
With it set, `0x0100/0x0e00` targets are matched to available children by the
record-name matching helpers, including the player `+0xf6` name offset.
Unbound entries whose flags request ownership are materialized separately;
`0x0100` construction makes a scene node and runtime model, while `0x0800`
construction makes a model without a scene-child array. Models requiring bone
rebinding receive an allocated array ordered by their source composition,
populated through the same temporary record publications.

Entry flag `0x02` applies the animation's parent map through `FUN_001ba810`:
`-1` attaches to the player node, otherwise to the indexed runtime target.
Consequently playback can construct or reparent a scene hierarchy independently
of the source composition constructor. Entry flag `0x01` controls target
allocation/destruction. Matching a prior animation can copy its target/type
and flags, but ownership-marked entries are materialized again later in the
binding function; copying a handle alone does not prove it survives the switch.
The full matching, blend and evaluator-lifetime contract belongs to
[Animation runtime](../animation_runtime.md#animation-to-animation-blending).

`FUN_001b8410` evaluates `0x0102` translation, rotation, scale and opacity into
work matrices, composes them and writes the `0x0100` target's local matrix.
`FUN_001b9430` copies 16 words to node `+0x40..+0x7c` and sets byte `+0x8d`
to 1. A target attachment at `+0xa0` can replace scale components and multiply
translation by its scalar before composition; alternate-output handling can
substitute a separately looked-up transform. Streamed `0x0101` transforms use
`FUN_001b5900` and `FUN_0019cb70`, which also dirties the local matrix.
Both routes therefore feed the hierarchy cache used by bone uploads. Curve
timing, rotation interpolation and blend pose composition belong to
[Animation evaluation](../animation_runtime.md#typed-curve-evaluation).

## Morph control and geometry ownership

**Observation, high confidence:** playback construction `FUN_001a0b80` and
animation binding `FUN_001b99b0` materialize `0x1900` as a `0x114`-byte
controller through `FUN_001ba850`, with vtable `0x005D9E10` and a zero count
halfword at `+0x10`. An object descriptor's `+0x14` controller-record reference
binds the materialized controller to scene node `+0x98`. During part drawing,
`FUN_001910e0` calls the controller's vtable `+0x0c` after part preparation and
before producing modified geometry. That slot resolves to `FUN_00197570`.

`FUN_00197b30` writes each eight-byte morph entry as source runtime model at
controller `+0x14 + index*8` and float weight at `+0x18 + index*8`;
`FUN_00197b20` publishes the count. The setter's five-instruction body proves that
weight arrives in `f12`, despite the decompiler's incomplete signature.
Streamed `0x1901` processing `FUN_001b56e0` consumes source-ID/weight pairs,
resolves source models and compacts missing sources out of the controller.
Typed `0x1902` evaluation instead uses each key's bound player-entry index and
omits zero weights (`0x001B91B8..0x001B9258`). This typed branch does not perform
the streamed reader's missing-source check.

`FUN_00198230` starts each part with borrowed positions and attributes, clears
draw ownership `+0x222` and copies the packet pointer to context `+0x228`.
For a nonzero controller count, `FUN_00197570` calls `FUN_00198030`. On the
first position edit that helper allocates an aligned destination, returns the
borrowed input separately, sets ownership bit 1, replaces context `+0x230`
and clears `+0x228`. Later edits in the same part use the existing destination
as both input and output. This separates the first morph destination from the
base position array, while permitting subsequent modifiers to accumulate.
The inspected controller hook is in the non-packed `FUN_001910e0` branch;
its flag-`0x04` delegate `FUN_0018ffb0` has no corresponding hook. Moreover,
packed source geometry retains no part `+0x14` halfword positions. These
observations do not establish a general morph contract for every geometry mode.

### Selected morph admission and topology assumptions

**Observation, high confidence:** both non-packed draw continuations invoke
the controller through context `+0x200` after `FUN_00198230` and before the
flag-`0x0800` property preparation (`0x00191780..0x001917B8`,
`0x00191C58..0x00191C90`). Context initialization `FUN_001982b0` copies that
controller pointer from scene node `+0x98`; it does not inspect controller
sources or compare geometry. The streamed and typed source-list producers
establish different pointer/weight gates, not a topology check:

| Inspected path | Enforced condition | Geometry conditions not compared in that path |
| --- | --- | --- |
| Streamed `FUN_001b56e0` and lookup `FUN_001b56b0` | A target pointer exists; retain each nonnull source-table pointer. Missing target still consumes every pair. | Model kind, part count, vertex count, scalar compatibility or strip correspondence. The lookup indexes the 16-byte table at container `+0x60` and reads its first pointer; its 11-instruction body does not check an entry type or index bound. |
| Typed `0x1902`, `FUN_001b8410` | Omit exactly zero evaluated weights; use the key's halfword player-entry index to obtain the source pointer. | Source pointer validity, source type, part/count/format correspondence (`0x001B91B8..0x001B9258`). |
| `FUN_00197b30/FUN_00197b20` | Store source pointer/float at the requested index; publish count as a halfword. | Entry-index capacity, source validity or geometry. Bodies are five and two instructions respectively. |
| `FUN_00197570` position branch | Controller count is nonzero and `FUN_00198030` obtains a destination. | Source part existence, source position format/length, target vertex-count positivity or topology equality. |

The morpher reads target count `N` from context `+0x22c`, and for every
source reads positions from runtime `parts + 0x40*target_part_index + 0x14`
(`0x00197898..0x001978C4`). Its blend loop advances each source and
the base by six bytes per target vertex; the endpoint is destination
`+6*N` (`0x00197A48..0x00197AE4`, corroborated by resident bytes). It never loads
the selected source part's count to bound that blend. Source part/count fields
are used separately when rescaling **all** source parts, not to admit the
current pair.

**Inference, high confidence:** this loop assumes that each selected source
has the addressed part and enough readable signed-halfword XYZ triples for
the target's ordinal vertex sequence. It does not require count equality:
when a source has more triples, the loop reads only the target-length prefix.
Matching vertex identity/order is an authored requirement for meaningful
blending, not an inspected admission predicate. Independent strip conversion
can reverse or duplicate vertices, so even equal file counts do not establish
equal post-conversion correspondence. The source's triangle indexes, strip
controls, material or normals are not substituted into the target here.
The inner loop tests its destination endpoint after its first iteration;
there is no target-count-zero precheck after the nonzero-controller gate.
This describes the instructions' assumption, not an observed malformed-asset
outcome or proof that such a pair is reachable from retail assets.

**Observation — format boundary:** the arithmetic is unconditionally six-byte
signed-halfword XYZ. `FUN_00198030` chooses a six- or twelve-byte destination
allocation from context flag `0x1000`, but that allocation choice does not
change the morpher's six-byte stride. Packed and selector-4 source parts do
not retain the ordinary position buffer. Property geometry stores its rigid
and weighted coordinates inside its separate geometry object; the controller
hook has no explicit property-format rejection. Subsequent `FUN_001921c0`
replaces context positions/vectors from that object's own arrays, then gathers
them through its indexes. It does not consume the controller's modified
position pointer as its geometry input. These paths establish neither a
packed/property/topology morph adaptation nor an authored unsupported pairing.

**Storage observation:** the controller's `0x114`-byte allocation has room for
32 eight-byte entries beginning at `+0x14`. The blend helper temporarily
advances workspace cursor `+0x1c0` by `0x100`, then writes sixteen bytes per
retained source (`0x00197884..0x00197894`, `0x00197A2C..0x00197A40`). That
reserved span holds 16 such records. Neither inspected source-list producer,
setter nor blend setup clamps count to 16 or 32. These are different storage
bounds, not a demonstrated safe count for every retail controller. Authored
counts and wider workspace use remain unmeasured here.

### Shared mutation and draw-local results

The morpher obtains every source's position pointer from the **same part
index** as the target. If a source model's scalar differs from the draw
context scalar, it rescales every source part's signed-halfword positions by
`source_scalar / target_scalar`, truncates to integers and stores halfwords
back into those source arrays. It then writes the target scalar into both
the source resource `+0x44` and runtime model `+0x0c`. Thus morph application
can alter shared source geometry; the separate destination does not make the
whole operation read-only with respect to sources.

**Observation — copied scalar lifetime:** the rescale comparison uses the
source resource's current `+0x44`, while its ratio uses this source runtime
instance's copied `+0x0c`. After mutation it writes the target scalar to the
resource and that instance only (`0x001978D4..0x001978FC`,
`0x001979F8..0x00197A04`). `FUN_0019a0c0` initially borrows source positions,
so independently constructed instances can share those arrays while retaining
separate scalar copies. The morpher does not enumerate other instances,
refresh their scalar copies, recompute bounds, or reverse its source changes
on exit. Later aliasing consequences depend on the actual owner order; no
complete retail morph distribution or lifecycle ordering is established.

An explicit duplication path is separate from initial borrowing:
`FUN_00198b10` delegates part duplication to `FUN_00199ac0`. With request
bit 1, model flag `0x04` clear and a nonnull position pointer, the latter
duplicates positions and strip controls, marks runtime-part ownership bit 1,
and rebuilds an existing packet with ownership bit `0x100` after array changes.
Thus later runtime parts can own private positions. The morpher still updates
the source resource scalar through the instance's record; private position
storage alone does not isolate that header mutation. Complete call-site use
of these duplication requests is not established here.

The streamed producer retains zero-weight sources, whereas the typed producer
omits them. A retained zero weight still reaches pointer collection and scalar
rescaling before Q12 blending; zero arithmetic contribution therefore does
not imply absence of source mutation. No weight-sum or normalized-weight
admission appears in the inspected producers or loop.

**Observation — geometry output lifetime:** each `FUN_00198230` resets context
ownership and reborrows the current part's base arrays. The first position edit
clears its retained packet pointer; `FUN_00192fb0` then reconstructs the part
packet from current context arrays. `FUN_00193d80` emits references to the
position/control buffers rather than copying all their vertices into the
packet. Thus the controller's destination is draw-local and does not replace
runtime-part `+0x14`; source rescaling separately persists in borrowed source
arrays. Scene drawing `FUN_00190f40` restores its workspace cursor after the
draw, and the morpher restores its own scratch cursor at `0x00197AE8..0x00197AEC`.
Allocated packet/buffer retirement is owned by
[Render submission](render_submission.md), rather than controller destruction.

**Observation — morph arithmetic:** float weights are converted by `vftoi12`
to Q12 integers. For each XYZ halfword triple, the code subtracts the current
base from every source with `psubh`, accumulates weight times difference with
`pmaddh`, shifts the sum right by 12, then adds the base with saturating
`paddsh` and packs the result (`0x00197A70..0x00197AE4`). The nominal operation
is `base + sum(weight * (source - base))`, with weights replicated into
halfwords after Q12 conversion. Halfword wrapping, integer truncation and the
final signed-halfword saturating add can differ from that unbounded float
formula. The code does not normalize the sum of weights. The controller
operation does not update normals alongside these positions. Its other,
flag-`0x80000` UV-projection branch belongs
to [Texture and material runtime](texture_material_runtime.md).

**Ownership observation:** `FUN_0019a0c0` copies source part pointers into
runtime parts and virtually clones any polymorphic geometry at part `+0x30`.
`FUN_00198f70` frees runtime arrays only when their ownership bits request it;
bit `0x20000` owns the geometry clone. `FUN_00199190` owns any replacement bone
array marked by `0x40`, then destroys its runtime part table through that
destructor. Source-model `FUN_001a9570/FUN_001a9620` separately owns the source
part arrays and geometry objects. The source models stored in morph entries
are borrowed: controller destruction does not substitute for these model
destructors. Controller destructor `FUN_0019f630`, identified by vtable slot
`0x005D9E18`, frees only the controller allocation when requested.

Playback cleanup `FUN_001a2520` and typed-player cleanup `FUN_001b7750`
destroy ownership-marked `0x1900` controllers and `0x0800` runtime models as
separate table entries. The controller destructor does not traverse its
borrowed source list; these cleanup branches do not provide an independent
reference count for that list. Animation switching and target/evaluator
lifetime remain owned by [Restart, hold and removal boundaries](../animation_runtime.md#restart-hold-and-removal-boundaries).

## Bounded official NUN3 comparison

**Observation:** official NUN3 resident `SLUS_217.27` outer loader
`FUN_001660a0` uses the same `0x60 + count*0x40` model allocation, selector
`(file_flags >> 1) & 7`, accepted selector values 0/2/3/4 and corresponding
part-prefix widths. Its internal branch numbered 3 is likewise not assigned
by the examined outer selector. This comparison concerns the inspected reader
paths, not every asset from either game.

| Compared contract | NA2 evidence/result | NUN3 evidence/result |
| --- | --- | --- |
| Packed zero second-count payload | `FUN_001af1f0` reads matrix selector, signed XYZ triples, dword attributes and masked/shifted dword UV values. | `FUN_00164960` consumes those same fields in that order; batches at most `0x36` vertices. |
| Packed nonzero second-count payload | `FUN_001ae190/950`: eight-byte entries, byte 7 bit 1 list terminator, per-influence dwords, per-vertex UV dwords; low-nine-bit field shifted left four and matrix index `0x50 + 4*(byte_7 >> 2)`. | `FUN_00164960` consumes the same field widths/grouping and emits the same weight/index encoding. |
| Packed position multiplier | Model `+0x44 / 4096`: caller instructions `0x001AFF94..0x001AFFA4`, `0x001B0040..0x001B0050`. | Model `+0x44 / 256`: `0x001649EC..0x00164A0C`, `0x0016536C..0x00165398`. |
| Packed extrema | Converters keep temporary extrema; `FUN_001aff20` does not propagate them to the outer buffer. | `FUN_00164960` updates its fifth argument's six extrema in both branches. |
| Strip normalization modes | `FUN_001b0c40` decodes the additional header fields; ordinary and both packed routes can reorder/duplicate strips. | `FUN_001660a0` does not decode those NA2 mode fields; its packed converter has no corresponding normalization call. |
| Header dword at model `+0x50` | `FUN_001b0c40` retains its low 24 bits and, for version `>=0x123`, separately sets byte `+0x53` bits 0..1 from extra-byte bits 2..3. | `FUN_001660a0` retains the whole dword; it has no corresponding extra-byte assignment. |
| Property framing | `FUN_00181760/1520`: dependency ID/count, 12-byte property header, width/multiplicity calculation and rounded dword payload. | `FUN_0017e9c0/e750` agrees on these reads and calculations for the listed element types. Its selected converter was not compared here. |
| Triangle topology input | `FUN_0018d740`: two counts, signed XYZ triples, align four, integer(index_count/3) dword-index triples. | `FUN_00140b50` agrees on that input sequence and cyclic per-triangle helper calls. Complete generated packet equality was not established. |

**Inference, high confidence:** an identical packed coordinate triple and
identical header scalar produce positions 16 times larger in the inspected
NUN3 converter than in NA2. Therefore byte-consumption agreement alone does
not establish equal mesh interpretation. This does not show whether any given
official asset compensates through its header scalar, hierarchy or authored
coordinate values. Whole-file loading, VU behavior and animation/model pairing
remain separate evidence requirements.
