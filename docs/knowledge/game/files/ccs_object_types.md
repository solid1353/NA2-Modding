# Resident CCS object-type identities

This document is the evidence-backed map from numeric CCS object-block tags to
resident runtime resource identities. It deliberately does not repeat container
loading, publication, hashing, residency, or generic lookup behavior; those are
owned by [Resident CCS runtime](ccs_runtime.md).

Only identities joined directly to a parser branch and then to construction,
destruction, a vtable, or an embedded runtime type name are named here. A
numeric dispatch branch, an object-name prefix, or a third-party tool label is
not by itself a class identity.

## Research coverage

- **Assigned scope:** map resident NA2 CCS numeric file-block and runtime-record
  tags to resource or class identities only where direct parser dispatch,
  construction, destruction, vtable, embedded type-name, or immediate consumer
  evidence supports the mapping. Generic container loading, publication,
  hashing, residency, and lookup remain in `ccs_runtime.md`.
- **Exploration depth:**
  - The branch inventory of file-block dispatcher `FUN_001AC8A0` was
    enumerated exhaustively (34 object/control routes plus terminator
    `0x0005`) and checked against runtime-record teardown switch
    `FUN_001A9F10`. Tracing beyond those switches was bounded to each direct
    parser, the common materializer `FUN_001A0B80`, and the immediate
    constructors, destructors, vtables, RTTI/name descriptors, finalizers and
    consumers, including `FUN_001952F0`, `FUN_001AD240` and `FUN_00197570`;
    it is not a whole-program call-graph audit.
  - Eight clean CCS inputs were decoded for semantic payload checks. A
    chunk-boundary inventory of all 1,732 extracted CCS files established tag
    presence and absence, rechecked by an aligned-word search of 1,731 files;
    texture blocks were walked by the parser's per-level counts to inventory
    texture and CLUT group references.
  - The texture/CLUT group node, the `0x1800` constructor, materializer
    branches, frame command `0x1801`, render-environment binding, model-part
    packet producer and draw queue, and the `0x2200` producers, manager
    initialization, helpers and resident references were followed to their
    consumers.
  - Literal searches for `0x1100`, `0x1200` and `0x1F00` covered all register
    encodings of `addiu` and `ori` (and `slti`/`sltiu` for `0x1F00`) in the
    resident executable, `BTL.BIN` and `ETC.BIN`. The `0x1F00` parser,
    `0x1000`..`0x1200` handlers and `0x2200` layouts were compared with NUN3
    and NUN5, and literal matches counted in NUN5 and NUN6.
  - The maintained explorer executable was read statically for `0x0800` and
    `0x2400` corroboration and its unpromoted name-to-tag labels.
- **Confirmed coverage:** 29 numeric routes have a confirmed resident resource
  identity or block role in the table below. File tag `0x0003` is confirmed as
  the object-section marker. Runtime tag `0x1000` created by texture and CLUT
  construction is confirmed as a shared GS image-transfer group with a
  resident consumer. Resident 8-bit CLUT entries are in CSM1 order. Most
  `0x1800` descriptor fields are mapped to off-screen render-target,
  depth-region, size, composite-pass, and projection scalar parameters;
  its model-geometry queue producer and frame-controlled
  direction/strength are established, with independent named shadow-class
  corroboration. The `0x2200` batch header and ring producer/control fields
  are mapped. Exact embedded class names on file-tag routes are promoted
  only for the texture, light, generator, morpher, and stream draw-
  environment families whose constructor/vtable/name chains were recovered.
  The remaining resource labels describe proved layouts and consumers, not
  speculative C++ class names.
- **Unresolved or untested:** file routes `0x1000`, `0x1100`, `0x1200`, and
  `0x1F00` remain unresolved for the reasons recorded in the ledger. Runtime
  tag `0x1000` from texture and CLUT construction is resolved as an
  image-transfer group, but its relationship to file-block handler
  `FUN_001ADB70` is only an inference. Same-name merging depends on 29
  comparison-key bytes left uninitialized by the inspected allocation and
  construction path; a match also bypasses requesting-record publication.
  The binary and runtime layouts of the `0x1F00` nested table are confirmed
  below, but no direct semantic consumer was
  recovered. The explorer labels `FrameBuffer_Page`, `FrameBuffer_Rect`, and
  `Sprite2Tbl` remain unverified leads for `0x1100`, `0x1200`, and `0x1F00`.
  The exact projection units and VU-side geometry operation of `0x1800` and
  a C++ class name for its CCS-created object remain unresolved. Its frame
  direction input's W component is not initialized by the handler.
  The `0x2200` packet command language, ring activation path, and read-side
  consumer are unresolved; the explorer labels that route `PCM_Audio`.
- **Deliberate exclusions and overlap:** container loading, publication,
  hashing, residency and lookup belong to [Resident CCS runtime](ccs_runtime.md).
  `ADV.BIN` and overlay resource trees were not inspected.
  `BTL.BIN` and `ETC.BIN` were searched for the literal tag forms named
  above and the manager-reference/direct-call encodings in the `0x2200`
  audit. The `BLT_item` string table was followed only to its data
  reference.
- **Evidence limitations:** static evidence is limited to the identified
  clean resident executable, its maintained read-only exports, the listed
  clean assets, the identified tool build, and the maintained NUN3, NUN5,
  and NUN6 analyses used only for
  comparison. Literal searches cannot see a tag built by table lookup or
  arithmetic. No emulator execution, runtime injection, or live-memory
  observation validated these mappings; clean assets provide file-level
  corroboration only.

## Evidence identity and address spaces

Resident address conversion follows
[Retail game file identities](file_identities.md#address-conventions). Eight
clean NA2 CCS files were decompressed and parsed in memory for corroboration:
`PL/1KHWBOD1.CCS`, `PL/2DDRBOD1.CCS`, `PL/2HKGCHA1.CCS`, `PL/2TEWCHA1.CCS`,
`BUDDY/2ASWBDY0.CCS`, `SCENE/PPT2310_ST00.CCS`, `SCENE/PPTS04.CCS`, and
`XNINKA.CCS`. Their sizes and hashes are listed under
[CCS research inputs](file_identities.md#ccs-research-inputs).

The first sample contains `OBJ_`, `MAT_`, `TEX_`, `CLT_`, `MDL_`, `CMP_`,
and `BOX_` records on the numeric routes reported below. The two additional
`PL` samples supply `HIT_`, `PAC_`, `PGE_`, and `EFF_` examples.
`2DDRBOD1.CCS` supplies composition-child attachment metadata, and
`2ASWBDY0.CCS` supplies `BIN_...scr` examples. `PPT2310_ST00.CCS` supplies a
controller table over `LYR_` records plus its default extended-controller
parameters, while `PPTS04.CCS` supplies position-only and position-plus-Euler
`DMY_` examples. `XNINKA.CCS` supplies `ANM_`, `CAM_`, external `OBJ_`, and
transitional `0x2000` examples. These names corroborate identities reached
independently from resident code. They do not establish an identity by
themselves.

All function, vtable, descriptor, and string addresses below are resident EE
virtual addresses. For this resident executable the Ghidra/export VMA is also
the address at which resident code would execute in live EE memory; no
live-memory observation is claimed. The clean ELF's first `PT_LOAD` maps file
offset `0x00000100` to resident VMA `0x00100000`. The one raw word used below,
concrete `ccMorpher` vtable slot `+0x0C`, is at file offset `0x004D9F1C` and
contains resident function VMA `0x00197570`; the same slot is resident VMA
`0x005D9E1C`. No other address below is a file offset. Overlay inspection was
limited to the byte searches identified in Research coverage; no overlay
resource tree was inspected.

The parser reads a **file block tag** from the CCS stream. A branch may then
write a **runtime record tag** at object-record `+0x2A`; the two address spaces
and the two uses of a number must not be conflated. The ledger below reports a
teardown branch only when `FUN_001A9F10` explicitly tests that runtime value.

## Confirmed identities

| File/runtime tag | Confirmed identity | Direct evidence | Confidence |
| ---: | --- | --- | --- |
| `0x0100` | Model-instance/object descriptor | File-tag dispatch calls `FUN_001B2670`, which allocates a `0x24`-byte runtime object, publishes tag `0x0100`, and stores three record links. `FUN_00115BA0` independently requires runtime tag `0x0100`, resolves that object, classifies its `+0x0C` dependency under selector `MDL`, then walks the resolved model's part table and classifies its record dependencies under `MAT`. Clean sample records on this route are named `OBJ_...`. This proves an object descriptor that instantiates or binds a model; it does not establish an embedded C++ class name. | **High** |
| `0x0200` | Material resource | File-tag dispatch calls `FUN_001B3450`, which allocates a `0x18`-byte runtime object, publishes tag `0x0200`, stores a linked resource record at `+0x08`, and links the object through container `+0x50`. In `FUN_00115BA0`, each model part's corresponding record is classified by selector `MAT`; resolving that record yields an object whose `+0x08` record is in turn classified as `TEX`. Clean sample records on the `0x0200` route are named `MAT_...`. The parser shape, model-part consumer, and material-to-texture dependency agree. | **High** |
| `0x0300` | Texture-chunk family: `ccTexChunk`, with a `ccSamplingTexChunk` variant | File-tag dispatch in `FUN_001AC8A0` calls `FUN_001B3C70`. Its ordinary branch allocates `0x48` bytes and calls `FUN_001B4470`, which installs the vtable/descriptor pointer `0x005D9E90`. That descriptor resolves through `0x005B59B0` to embedded name `ccTexChunk` at `0x003D1918`. The alternate `0x50`-byte construction path calls `FUN_0019E080`, which first installs the same base pointer and then replaces it with `0x005D9E70`; that descriptor resolves through `0x005BF8D8` to `ccSamplingTexChunk` at `0x003FB5E0`. Both paths publish runtime tag `0x0300`. `FUN_001A9F10` tears the object down virtually through the vtable at object `+0x40`, slot `+0x08`. | **High** |
| `0x0400` | CLUT/palette resource | File-tag dispatch calls `FUN_001B3810`. It allocates `0x28` bytes through `FUN_001B3C40`, publishes tag `0x0400`, consumes packed color words, and prepares the palette storage used by the texture path. Texture construction in `FUN_0019EAB0` stores this dependency at texture `+0x3C`; `FUN_0019E760` returns that field, and `FUN_00115BA0` classifies the referenced record under selector `CLT`. Clean sample records on this route are named `CLT_...`. The prepared 8-bit palette is resident in GS CSM1 order: file entry `i` is at resident slot `i` with bits 3 and 4 swapped. All 256 entries of a loaded `CLT_s_menu` matched that order in a runtime memory capture. The CLUT's transfer descriptor at `+0x10` uses the same `0x20`-byte layout as texture level descriptors. No resident C++ class name was recovered. | **High** |
| `0x0500` | Camera/view resource | File-tag dispatch calls `FUN_001B35B0`, which publishes tag `0x0500` and a small record-backed descriptor. When `FUN_001A0B80` materializes that record it allocates `0x50` bytes and calls `FUN_0019C690`; the constructed view object stores the source record, initializes a `45.0` field at `+0x0C`, and owns a matrix at `+0x10`. `FUN_001A0A40` updates that matrix through `FUN_0019C540` from position and rotation inputs before passing the object to the render path. The alternate playback owner likewise stores the selected `0x0500` object as its active view at `+0x10C`, and `FUN_001B9740` selects it by record name. The clean record is `CAM_camera01`. These operations establish a camera/view resource, but no resident C++ class name. | **High** |
| `0x0600` | `ccLight` family: `ccDistantLight`, `ccDirectLight`, `ccSpotLight`, and `ccOmniLight` | File-tag dispatch calls `FUN_001B3600`, which stores two selector bytes and publishes tag `0x0600`. `FUN_001AD9C0` passes that exact descriptor to `FUN_0019B240`. Its shared constructor installs base descriptor `0x005D9E60`, which resolves through `0x005BF830` to embedded `ccLight` at `0x00602A70`. The first selector byte then selects the concrete allocation and replaces the descriptor as shown below. `FUN_001A9F10` destroys the resulting secondary object virtually through object `+0xA4`, slot `+0x08`, matching the installed polymorphic layout. | **High** |
| `0x0700` | Animation/track resource | File-tag dispatch calls `FUN_001B1470`, which allocates `count * 4 + 0x2C` bytes, publishes tag `0x0700`, records the frame/count fields, and calls `FUN_001A29D0`. That constructor parses nested tracks through `FUN_001A6E00`, builds record/track pairs and cross-indexes, and feeds the adjacent quaternion/vector interpolation and transform-evaluation path. Clean sample records on this route are named `ANM_...`. The runtime behavior proves an animation-track resource without proving a C++ class name. | **High** |
| `0x0800` | Model/mesh resource | File-tag dispatch calls `FUN_001B0C40`, whose constructed object contains a variable table of `0x40`-byte model-part entries plus geometry buffers and strip/index data. `FUN_00115BA0` reaches this object from the `MDL` dependency of a `0x0100` model instance, reads the part count at `+0x5E`, and walks those `0x40`-byte entries to reach `MAT` dependencies. Clean sample records on this route are named `MDL_...`; the maintained explorer independently decodes the same route as model geometry and triangle strips. The resident parser and consumer, rather than the tool label, establish the identity. | **High** |
| `0x0900` | Scene-object composition/aggregate resource | File-tag dispatch calls `FUN_001B1560`. It publishes tag `0x0900`, stores an array of child record references, and constructs one `0x30`-byte transform per child; newer streams supply position, Euler angles converted from degrees to radians, and scale. Playback construction in `FUN_001952F0` allocates the aggregate runtime, resolves each child, and constructs supported child types `0x0100`, `0x0D00`, and `0x0E00` into its child array before running aggregate finalization. Clean records on this route use `CMP_...` names. This proves a scene composition, not a direct correspondence to any embedded `ccBg*Clump` class name. | **High** |
| `0x0A00` | External-object reference wrapper | File-tag dispatch calls `FUN_001B2800`. It allocates a `0x20`-byte wrapper, publishes runtime tag `0x0A00`, and overwrites the target record name's first three bytes with `EXT`, preserving the remainder used by `EXT_...` names. `FUN_00116210` repeatedly follows records of this type through the wrapper's linked-record field; `FUN_00116030` treats an `EXT_` query specially by requiring the original record to remain type `0x0A00` instead of unwrapping it. `FUN_001A9F10` directly frees the wrapper. | **High** |
| `0x0B00` | Model-linked hit/collision mesh resource | File-tag dispatch calls `FUN_001B3040`. For nonzero geometry it publishes tag `0x0B00`, keeps a linked model record, reads triangle triplets, transforms them through `FUN_001ABEB0`, builds a `0xA0`-byte-per-triangle spatial buffer, and computes the aggregate minima and maxima stored at the buffer head. Container finalization in `FUN_001AD240` walks the dedicated `+0x54` list and installs each hit record into its linked resource's runtime descriptor at `+0x04`. In clean `2HKGCHA1.CCS`, the route's target is `HIT_2hkgwal0_hit` and its linked record is `MDL_2hkgwal0`. The geometry, spatial bounds, model attachment, and corroborating names establish the hit/collision role; no C++ class name is claimed. | **High** |
| `0x0C00` | Axis-aligned bounding-box resource | File-tag dispatch calls `FUN_001ADBF0`. It allocates `0x40` bytes, publishes tag `0x0C00`, stores one linked record, copies the six input floats into two homogeneous XYZ endpoints at `+0x10` and `+0x20`, and computes their component-wise midpoint at `+0x30`. Clean sample records on this route use `BOX_...` names and include `bbox`. The explicit min/max-shaped construction establishes the resource role; no C++ class name is claimed. | **High** |
| `0x0D00` | Transform-only scene-child node | File-tag dispatch calls `FUN_001B1890`, which publishes tag `0x0D00` and links a target record to a second record. When a `0x0900` composition contains that target, `FUN_001952F0` allocates a `0xA0`-byte child and calls `FUN_001964E0`; the constructor initializes the common transform layout through `FUN_0019CD80`, and `FUN_00196540` marks the child itself as runtime type `0x0D00`. The animation-command path in `FUN_001B5A60` applies position, Euler rotation, and scale directly through `FUN_0019CB70`, with none of the frame or draw behavior used for `0x0E00` children. This proves a transform-only composition node. No non-excluded clean sample block or resident C++ class name was recovered, so the narrower labels “dummy” and “locator” are not assigned. | **High** |
| `0x0D80` | Animation-attached effect-generator action packet | File-tag dispatch calls `FUN_001B1920`, which publishes tag `0x0D80` and builds a variable packet whose header links a target record to an animation record and whose `0x18`-byte entries carry generator, attachment, and auxiliary record references plus command bytes. `FUN_001AD240` moves these packets onto the linked animation runtime's `+0x04` list. `FUN_001ABBE0` walks that exact list; `FUN_001AB0B0` iterates each packet's entries and passes their generator records to `FUN_001AACF0`, which materializes the corresponding generator. In clean `2TEWCHA1.CCS`, `PAC_ptewcha11` links to `ANM_ptewcha11` and its entries reference `PGE_...` and `OBJ_...` records. This proves the animation-attached generator-action role without a C++ class name. | **High** |
| `0x0D90` | `ccGenerator2` particle/effect-generator definition | File-tag dispatch calls `FUN_001B1B30`, which publishes tag `0x0D90` and constructs a variable parameter descriptor with child-resource entries. The direct `0x0D80` consumer `FUN_001AACF0` resolves such a record and passes its descriptor to `FUN_00352A10`; that path allocates a `0x220`-byte object through `FUN_0034B720`, installs descriptor `0x005DCA80`, and populates it from the parser descriptor in `FUN_0034BBB0`. The installed descriptor resolves through `0x005C8C88` to embedded `ccGenerator2` at `0x005A6608`. The consumer also registers referenced `0x0900`, `0x0E00`, and `0x0700` children with the generator runtime. Clean records use `PGE_...` names. | **High** |
| `0x0E00` | Animated textured-effect resource | File-tag dispatch calls `FUN_001B2E50`, which publishes tag `0x0E00`, stores a texture record at descriptor `+0x08`, a frame/count field at `+0x16`, and a variable table of packed per-frame triples. `FUN_001952F0` materializes this tag as a `0x100`-byte scene child through `FUN_00195980`; `FUN_00195A10` marks runtime type `0x0E00`, while `FUN_00195760` advances/evaluates frames and reaches the draw path. Independently, `FUN_00115BA0` follows the descriptor's `+0x08` dependency under selector `TEX` and then follows its palette under `CLT`. Clean targets such as `EFF_2hkgwal3` and `EFF_2tewbom0` link to `TEX_...` records. The construction, frame evaluation, texture/palette dependency, draw path, and names establish an animated textured effect; no C++ class name is claimed. | **High** |
| `0x1300` | Position-only dummy marker resource | File-tag dispatch calls `FUN_001B36A0`, which allocates a `0x20`-byte descriptor, publishes tag `0x1300`, and stores the three input floats as a homogeneous XYZ position at descriptor `+0x10`. The independent teardown branch directly frees that descriptor. In clean `PPTS04.CCS`, every block on this route has exactly four payload dwords: a target record followed by XYZ; examples include `DMY_tyo_r0` at `(0, 2000, 1030)` and `DMY_dummy_010` at `(-300, 1100, 660)`. The parser shape, lifetime, and clean records establish a position-only dummy marker, but no C++ class name or downstream specialized object was found. | **High** |
| `0x1400` | Position-and-Euler dummy marker resource | File-tag dispatch calls `FUN_001B3730`, which allocates a `0x30`-byte descriptor, publishes tag `0x1400`, stores a homogeneous XYZ position at `+0x10`, and converts three following Euler components from degrees to radians into the homogeneous vector at `+0x20`. The teardown branch directly frees the descriptor. Clean `PPTS04.CCS` blocks have exactly seven payload dwords; `DMY_dummy_100` carries position `(-785.9584, -229.4614, 235)` and Euler degrees `(0, 0, 60)`. The parser conversion, lifetime, and clean records establish the transform-marker role without a C++ class name. | **High** |
| `0x1700` | Lightweight ordered-controller binding | File-tag dispatch calls `FUN_001B2220`, which builds one shared controller table at container `+0x5C`. Kind-zero entries assign referenced records runtime tag `0x1700` and an eight-byte descriptor whose `+0x04` halfword is the table slot; a default slot is built when the entry has no record. `FUN_001A0B80` materializes each tagged record as a `0x40`-byte controller, initializes its list storage through `FUN_00110340`, and calls `FUN_0010A1D0` with that exact slot and the shared playback context. `FUN_0010A1D0` registers the controller in the ordered list processed by `FUN_00109D50`; cleanup uses `FUN_0010A0F0`. Clean `PPT2310_ST00.CCS` binds this form to `LYR_sky`, `LYR_bg`, `LYR_clr`, `LYR_clr01`, and `LYR_board`. This proves a lightweight scheduled-controller binding without proving an embedded C++ class name. | **High** |
| `0x1800` | Off-screen model-geometry projection/composite controller | Kind-one entries in `FUN_001B2220` create `0x1800` controller slots in the same shared table, and direct file-tag parser `FUN_001B1FF0` fills either a referenced record's `0x18`-byte descriptor or the default slot with six halfwords, two bytes, and a trailing word. `FUN_001A0B80` materializes that descriptor as a `0x180`-byte runtime object through `FUN_0018B570`, copies the trailing word to runtime `+0x170`, and initializes the direction at `+0x160` and strength at `+0x174`. The constructor embeds the `FUN_0010A1D0` ordered-controller base and registers a global controller node. `FUN_001A2000` binds the controller to the render environment; model-part producer `FUN_0018CF70` builds geometry packets and queues them through `FUN_0018B700` for the off-screen pass. Cleanup calls `FUN_0018B4C0` and frees the allocation. Clean `PPT2310_ST00.CCS` supplies halfwords `960, 0, 256, 256, 896, 0`, bytes `3, 0`, and projection scalar `0x447A0000` (`1000.0`). The [parameter fields and queue](#0x1800-descriptor-fields-and-off-screen-pass) establish this resource role; exact projection units, the VU-side operation, and a C++ class name remain unresolved. | **High** |
| `0x1900` | `ccMorpher`, derived from `ccModifier` | File-tag dispatch calls `FUN_001B2190`, which builds an eight-byte descriptor from a target record and a linked record and publishes runtime tag `0x1900`. `FUN_001A0B80` directly tests that tag, allocates `0x114` bytes, first installs descriptor `0x005D9DF0` at object `+0x0C`, and then replaces it with `0x005D9E10`. The first descriptor resolves through `0x005BF7F8` to embedded `ccModifier` at `0x003FB580`; the concrete descriptor resolves through `0x005BF810` to `ccMorpher` at `0x003FB590`. In the clean executable, concrete vtable slot `+0x0C` at resident `0x005D9E1C` is `FUN_00197570`; it applies the weighted source list installed through `FUN_00197B20` and `FUN_00197B30` to blend packed vertex positions into model geometry. `FUN_001B56E0` and the `0x1902` command branch in `FUN_001B8410` populate that list from materialized playback objects. Playback cleanup in `FUN_001A2520` calls the concrete object's virtual destructor through object `+0x0C`, slot `+0x08`. | **High** |
| `0x1A00` | `ccStreamOutlineParam`, derived from `ccDrawEnvCtrl` | The direct parser publishes runtime tag `0x1A00`. `FUN_001A0B80` tests that tag, allocates `0x40` bytes, installs the `ccDrawEnvCtrl` base descriptor and then concrete descriptor `0x005D9EF0` at object `+0x04`; the descriptor resolves through `0x005BF980` to embedded `ccStreamOutlineParam` at `0x003FB6F0`. | **High** |
| `0x1B00` | `ccStreamCelShadeParam`, derived from `ccDrawEnvCtrl` | The direct parser publishes runtime tag `0x1B00`. `FUN_001A0B80` tests that tag, allocates `0x40` bytes, installs the same base and then concrete descriptor `0x005D9EE0` at object `+0x04`; it resolves through `0x005BF968` to embedded `ccStreamCelShadeParam` at `0x003FB6D0`. | **High** |
| `0x1C00` | `ccStreamToneShadeParam`, derived from `ccDrawEnvCtrl` | The direct parser publishes runtime tag `0x1C00`. `FUN_001A0B80` tests that tag, allocates `0x48` bytes, installs the same base and then concrete descriptor `0x005D9ED0` at object `+0x04`; it resolves through `0x005BF950` to embedded `ccStreamToneShadeParam` at `0x003FB6A0`. | **High** |
| `0x1D00` | `ccStreamFBSBlurParam` | The direct parser publishes runtime tag `0x1D00`. `FUN_001A0B80` tests that tag, allocates `0x48` bytes, and installs descriptor `0x005D9EC0` at object `+0x00`; it resolves through `0x005BF930` to embedded `ccStreamFBSBlurParam` at `0x003FB680`. | **High** |
| `0x2000` | Transitional pre-object metadata overlay/carrier | File-tag dispatch calls `FUN_001B2510`, which reads a target, one scalar field, and three nullable record references. If the target is already runtime type `0x0100`, `0x0E00`, or `0x0A00`, it writes the applicable fields directly into that descriptor. If the target is still untyped, it allocates a temporary `0x14`-byte carrier and publishes runtime tag `0x2000`. The later `0x0100`, `0x0A00`, and `0x0E00` parsers explicitly recognize that tag, recover the saved fields, free the carrier, and replace it with their final descriptors. Clean `XNINKA.CCS` includes this sequence for records such as `OBJ_xback01` and `OBJ_sun01`. This proves a parse-order-independent metadata overlay, not a stable standalone object class. | **High** |
| `0x2200` | Global packet-ring batch | File-tag dispatch calls `FUN_001B44B0`. The parser reads batch and per-packet counts, marks the owning container with flag `0x80`, and requests `0x400`-stride ring slots through `FUN_001090C0`. It copies each packet into an available slot and commits it with `FUN_00109000`; otherwise it consumes the same stream words. Playback brackets use of the fixed manager at `DAT_00602A04` with `FUN_00109330` and `FUN_00109240`, which set command bits and signal its semaphore. This proves a block-only packet batch for the synchronized global ring. The [batch and manager evidence](#0x2200-batch-and-global-ring) does not establish a packet command language, audio decoder, or class name, and no block occurred in the inspected non-excluded sample corpus. | **High** |
| `0x2300` | Scene-composition child-attachment parameter block | File-tag dispatch calls `FUN_001B4B40`, which preserves the whole payload as a block-only entry under container `+0x6C`; it does not publish an object record. `FUN_001AD240` later interprets the payload as a target composition, two entry counts, and fixed-size child-reference/parameter records. It resolves each child through `FUN_0019DC90`, replaces record links with indices in the target `0x0900` composition, and installs compact `0x10`- and `0x1C`-byte-per-entry arrays at composition descriptor `+0x18`. `FUN_001952F0` passes that exact field to `FUN_00189B60`, which constructs the runtime attachments against resolved scene children. Clean `2DDRBOD1.CCS` targets `CMP_2ddrh00t0 trall`; its first attachment names `OBJ_2ddrh00t0 bone03` and carries floats `(0.85, 0.9, 0.2)`. The child-attachment role is direct, but no standalone runtime tag or class exists for the block. | **High** |
| `0x2400` | Opaque binary-blob resource | File-tag dispatch calls `FUN_001B4BC0`, which allocates one descriptor containing the target record, exact byte length, and an inline byte-for-byte payload at `+0x08`, then publishes tag `0x2400`. `FUN_003913C0` independently resolves named `BIN_stfdata` records through `FUN_001A8F00`, reads that same length at `+0x04`, and copies the bytes from `+0x08` into its owned buffer before processing them. Clean `2ASWBDY0.CCS` records `BIN_asw0scr`, `_atk`, `_ent`, `_ext`, and `_wit` use this route with payloads from 12 to 936 bytes. This proves a generic opaque binary resource and its resident data/length ABI. It does not prove that every payload is a script or connect the route to a named C++ class. | **High** |

The `0x0600` concrete selector chain is exact; unknown selector values return no
secondary object:

| First selector byte | Allocation | Installed descriptor | Descriptor/name link | Embedded class name |
| ---: | ---: | ---: | --- | --- |
| `1` | `0xE0` | `0x005D9E50` | `0x005BF8B8` -> `0x003FB5D0` | `ccDistantLight` |
| `2` | `0x160` | `0x005D9E40` | `0x005BF898` -> `0x003FB5C0` | `ccDirectLight` |
| `3` | `0x160` | `0x005D9E30` | `0x005BF878` -> `0x003FB5B0` | `ccSpotLight` |
| `4` | `0xD0` | `0x005D9E20` | `0x005BF858` -> `0x003FB5A0` | `ccOmniLight` |

For `0x1A00` through `0x1C00`, the base descriptor installed before the
concrete one is `0x005D9F00`; it resolves through `0x005BF938` to
`ccDrawEnvCtrl` at `0x003FB6B8`. The corresponding play-runtime cleanup calls
the virtual destructor through object `+0x04`, slot `+0x0C`. `0x1D00` uses its
own vtable at object `+0x00` and cleanup slot `+0x08`. The file-record teardown
still directly frees the small parser descriptors, so the two lifetimes are
distinct.

`0x0A00` is an object-reference mechanism, not proof that the wrapper is the
embedded RTTI class `ccExtObjLinker`. No constructor/vtable chain from this
parser branch to that name was established. It is also distinct from a `#`
namespace entry: `#` selects cross-container ownership behavior, while
`0x0A00` selects wrapper traversal.

## Numeric dispatch ledger

`FUN_001AC8A0` is the resident file-block dispatcher. The teardown column is
from the independent runtime-record switch in `FUN_001A9F10`; allocator names
are retained as original symbols because their semantic roles are not all
known. `Unresolved` means that the numeric route is proved but a concrete
runtime class/resource name is not.

| File tag | Direct parser | Runtime-record teardown branch | Identity status |
| ---: | --- | --- | --- |
| `0x0003` | `FUN_001ADA90` | None | **Object-section marker; a repeated marker is a header-only no-op. See [the section marker](#file-tag-0x0003-object-section-marker).** |
| `0x0100` | `FUN_001B2670` | `FUN_001A9390` | **Confirmed model-instance/object descriptor; see above.** |
| `0x0200` | `FUN_001B3450` | free `+0x30`, then `FUN_001A9290` | **Confirmed material resource; see above.** |
| `0x0300` | `FUN_001B3C70` | virtual destructor at object `+0x40`, slot `+0x08` | **Confirmed texture-chunk family; see above.** |
| `0x0400` | `FUN_001B3810` | `FUN_0019EF60` | **Confirmed CLUT/palette resource; see above.** |
| `0x0500` | `FUN_001B35B0` | `FUN_0019C160` on `+0x30`, then `FUN_001A9270` | **Confirmed camera/view resource; see above.** |
| `0x0600` | `FUN_001B3600` | virtual destructor at secondary object `+0xA4`, slot `+0x08`, then `FUN_001A9210` | **Confirmed `ccLight` family; see above.** |
| `0x0700` | `FUN_001B1470` | `FUN_0019D3A0` | **Confirmed animation/track resource; see above.** |
| `0x0800` | `FUN_001B0C40` | `FUN_001A9570` | **Confirmed model/mesh resource; see above.** |
| `0x0900` | `FUN_001B1560` | `FUN_001951A0` on `+0x30`, then `FUN_001A9450` | **Confirmed scene-object composition/aggregate resource; see above.** |
| `0x0A00` | `FUN_001B2800` | direct free through `FUN_00105650` | **Confirmed external-object reference wrapper; see above.** |
| `0x0B00` | `FUN_001B3040` | `FUN_001A92F0` | **Confirmed model-linked hit/collision mesh resource; see above.** |
| `0x0C00` | `FUN_001ADBF0` | `FUN_001A9730` | **Confirmed axis-aligned bounding-box resource; see above.** |
| `0x0D00` | `FUN_001B1890` | `FUN_001A9430` | **Confirmed transform-only scene-child node; see above.** |
| `0x0D80` | `FUN_001B1920` | `FUN_001A93D0` | **Confirmed animation-attached effect-generator action packet; see above.** |
| `0x0D90` | `FUN_001B1B30` | `FUN_001A93B0` | **Confirmed `ccGenerator2` particle/effect-generator definition; see above.** |
| `0x0E00` | `FUN_001B2E50` | `FUN_001A9370` | **Confirmed animated textured-effect resource; see above.** |
| `0x1000` | `FUN_001ADB70` | pointer clear only | Unresolved file block: publishes the numeric tag with a null descriptor and consumes, but does not preserve, the counted dwords. The same runtime tag written by texture/CLUT construction is the [image-transfer group](#runtime-tag-0x1000-from-texture-and-clut-construction-image-transfer-group). |
| `0x1100` | `FUN_001ADB20` | No explicit branch | Unresolved legacy marker: reads 16 bytes, uses only the target record to publish the numeric tag, and creates no descriptor. |
| `0x1200` | `FUN_001ADAA0` | No explicit branch | Unresolved legacy marker: publishes the numeric tag and consumes, but does not preserve, the counted eight-byte entries. |
| `0x1300` | `FUN_001B36A0` | direct free through `FUN_00105650` | **Confirmed position-only dummy marker; see above.** |
| `0x1400` | `FUN_001B3730` | direct free through `FUN_00105650` | **Confirmed position-and-Euler dummy marker; see above.** |
| `0x1700` | `FUN_001B2220` | direct free through `FUN_00117000` | **Confirmed lightweight ordered-controller binding; see above.** |
| `0x1800` | `FUN_001B1FF0` | direct free through `FUN_00117000` | **Confirmed extended parameterized ordered-controller binding; see above.** |
| `0x1900` | `FUN_001B2190` | direct free through `FUN_00117000` | **Confirmed `ccMorpher`, derived from `ccModifier`; see above.** |
| `0x1A00` | `thunk_FUN_001B4600` | direct free through `FUN_00117000` | **Confirmed `ccStreamOutlineParam`; see above.** |
| `0x1B00` | `thunk_FUN_001B4820` | direct free through `FUN_00117000` | **Confirmed `ccStreamCelShadeParam`; see above.** |
| `0x1C00` | `thunk_FUN_001B4920` | direct free through `FUN_00117000` | **Confirmed `ccStreamToneShadeParam`; see above.** |
| `0x1D00` | `thunk_FUN_001B4A20` | direct free through `FUN_00117000` | **Confirmed `ccStreamFBSBlurParam`; see above.** |
| `0x1F00` | `FUN_001B2930` | direct free through `FUN_00105650` | Unresolved variable nested table: publication and ownership are proved, but no independent consumer, constructor, vtable, RTTI link, or non-excluded sample was found. |
| `0x2000` | `FUN_001B2510` | direct free through `FUN_00117000` | **Confirmed transitional pre-object metadata overlay/carrier; see above.** |
| `0x2200` | `FUN_001B44B0` | No explicit branch | **Confirmed global packet-ring batch; no runtime record is published.** |
| `0x2300` | `FUN_001B4B40` | No explicit branch | **Confirmed scene-composition child-attachment parameter block; no runtime record is published.** |
| `0x2400` | `FUN_001B4BC0` | direct free through `FUN_00105650` | **Confirmed opaque binary-blob resource; see above.** |

File tag `0x0005` is the stream terminator handled inside `FUN_001AC8A0`, not
an object-type mapping. An unrecognized file tag reaches the deliberate
null-store failure path. The terminator's container-finalization behavior is
documented in [Resident CCS runtime](ccs_runtime.md#parsing-type-dispatch-and-publication).

### `0x2200` batch and global ring

**Observation — file payload:** `FUN_001B44B0` reads a 16-byte header and
then `packet_count * words_per_packet` dwords. Header offsets are relative
to the payload:

| Offset | Width | Parser-observed role |
| ---: | ---: | --- |
| `+0x00` | `8` | Read but not interpreted or retained by this parser. |
| `+0x08` | `4` | Packet count. |
| `+0x0C` | `4` | Dwords per packet. |

The parser sets container flag `+0xA6` bit `0x80`, calls the manager's
count-snapshot helper `FUN_001092B0`, and publishes the container as its
current owner at `gp-0x3564`. It requests each slot through `FUN_001090C0`,
copies that packet's dwords, and commits through `FUN_00109000`. An
unavailable slot causes the same words to be consumed and discarded.
There is no object-record publication. Frame command `0x2201` reaches the
same producer through `FUN_001B52D0`, allowing attachment only when the
global owner is zero or the current container; its separate stream schema
belongs to [Resident CCS runtime](ccs_runtime.md).

**Observation — manager state:** `FUN_001B45E0` returns `DAT_00602A04`,
whose initial pointer is `0x006091B0`. Constructor `FUN_001093C0`, called
by the resident static initializer at `0x005D6910`, clears its buffer,
command-target pointer, count, and indices, and sets its semaphore to `-1`.
The fields used by the bounded producer/control path are:

| Manager offset | Width | Observed use |
| ---: | ---: | --- |
| `+0x00` | `4` | Ring-buffer pointer; initialized to zero. |
| `+0x04` | `4` | Semaphore passed to `SignalSema`; initialized to `-1`. |
| `+0x08` | `4` | Command-target pointer required by slot, commit, and playback-control helpers; initialized to zero. |
| `+0x0C` | `2` | Queued count. `FUN_001090C0` refuses a slot when it equals `0x100`; commit increments it. |
| `+0x0E` | `2` | Write index. A slot is `buffer + index * 0x400`; commit advances it modulo `0x100`. |
| `+0x10` | `2` | Initialized to zero; no read-side use recovered. |
| `+0x12` | `2` | Count snapshot; initialized to `-1`, then set from `+0x0C` by `FUN_001092B0` while negative. |
| `+0x16` | `2` | Initialized to `0x3F`; interpretation unresolved. |
| `+0x18` | `4` | Unavailable-slot counter incremented for a missing buffer or count `0x100` while the command target exists. |

Playback controls `FUN_00109330` and `FUN_00109240` OR bits `1` and `2`
into command target `+0x2C` and signal the semaphore. Teardown
`FUN_00109160` clears the global container owner, ORs bit `4` into that
target, clears manager `+0x08`, and signals. These operations prove a
synchronized control protocol, but not what a consumer does with packets.
Bit `1` is requested at entry to streamed playback `FUN_001A0120`.
Bit `2` is requested by stop helper `FUN_001A00C0` and two stop/exit paths
in `FUN_001A0120`; all these requests require container flag `+0xA6`
bit `0x80`. These caller contexts do not establish the consumer's meanings
for the bits or any packet opcode.

**Observation — activation reference audit:** the getter is a two-instruction
return with `lw v0,-0x7FEC(gp)` in its delay slot. At resident
`gp = 0x0060A9F0`, that load addresses `0x00602A04`. Searching the resident
bytes for immediate `0x8014` across all four-byte encodings recovered five
aligned GP-relative loads of this pointer: `0x001A00E0`, `0x001A01E0`,
`0x001A0328`, `0x001A07B8`, and the getter at `0x001B45E4`. The other two
aligned matches were an arithmetic instruction and an unrelated `ori`
constant, not accesses to the pointer. These five loads agree with the
preserved xrefs and lead only to the known producer/playback controls.
Mapped mirror addresses were counted once.
The same immediate search in `BTL.BIN` yielded one aligned `lwc1` through
register `v0`, not a manager-pointer access; `ETC.BIN` yielded none.

Exact encoded `jal` searches across the resident program, `BTL.BIN`, and
`ETC.BIN` recovered the following direct calls. Neither overlay contains
one of these encodings. Resident mirror mappings were deduplicated.

| NA2 callee | Resident direct call sites | Recovered context |
| --- | ---: | --- |
| `FUN_00109000` | `2` | File `0x2200` and frame `0x2201` commit. |
| `FUN_001090C0` | `2` | The same two producers' slot requests. |
| `FUN_00109160` | `1` | Teardown wrapper `FUN_001091E0`. |
| `FUN_001091E0` | `0` | Registered as a destructor through an address construction instead. |
| `FUN_00109240` | `3` | `FUN_001A00C0` and two paths in `FUN_001A0120`. |
| `FUN_001092B0` | `1` | File `0x2200` count snapshot. |
| `FUN_00109330` | `1` | Entry to `FUN_001A0120`. |
| `FUN_001093C0` | `1` | Static initialization at `0x005D6910`. |
| `FUN_001B45E0` | `2` | File `0x2200` and frame `0x2201` manager retrieval. |

The exact `0x006091B0` pointer bytes occur at `0x00602A04`. Auditing aligned
instructions with low half `0x91B0` recovered the manager's two address
constructions in the static initializer: one before constructor call
`0x005D6910`, the other before registration of destructor `FUN_001091E0`
through `FUN_00119A60` at `0x005D6930`. The registration node is
`0x006091A0`; `FUN_00119A60` links the node and saves the destructor and
object pointer. The initializer then returns. Ghidra has this initializer
as data, so these calls and operands were checked from raw instruction bytes
rather than a recovered function. No buffer allocation or command-target
publication appears in this initializer.

**Observation — comparison:** the NUN3 frame producer and NUN5 file producer
reach the same manager layout and slot/commit contract:

| Retail program | Producer inspected | Slot | Commit | Manager constructor |
| --- | --- | --- | --- | --- |
| NUN3 `SLUS_217.27` | Frame `0x2201`: `FUN_0016AB30` | `FUN_00108D10` | `FUN_00108C90` | `FUN_00108F40` |
| NUN5 `SLES_556.05` | File `0x2200`: `FUN_001B87A0` | `FUN_00109230` | `FUN_00109170` | `FUN_00109530` |

Both constructors clear buffer `+0x00` and command target `+0x08`, set
semaphore `+0x04` to `-1`, and initialize the same count/index/snapshot
halfwords. Both slot helpers require a command target, reject a missing
buffer or count `0x100`, and use a `0x400`-byte stride. Both commits advance
the write index modulo `0x100`, increment the count, and signal the
semaphore. This comparison corroborates the producer contract; it does
not supply an activation or consumer path.
Raw instruction bytes also show NUN3 constructing manager `0x006A5C70` at call site
`0x00675D4C`, then registering destructor `FUN_00108DC0`; NUN5 constructs
manager `0x006198B0` at `0x005E3B10`, then registers `FUN_00109350`.
Both inspected initializer tails return after registration, without
publishing a buffer or command target.

**Observation — generic command-target lead:** `FUN_00108F20` initializes
two DMA tags and stores a callback at target `+0x18` and its argument at
`+0x1C`. Its inspected caller `FUN_00104850` builds GS transfer/draw packets
and supplies callback `FUN_00104FE0`. That callback conditionally calls
`FUN_00101370` on a global object and clears a separate global. Neither
function joins this target to CCS manager `+0x08`; adjacency and shared
field accessors do not establish a CCS packet consumer.
An exact encoded-call audit recovered only `0x00104F5C` for this constructor
in the resident program and no calls in `BTL.BIN` or `ETC.BIN`.

**Evidence limitations:** the inspected constructor and direct CCS
producer/playback/teardown paths do not allocate the ring buffer or create
its command target. No activation path, read-side consumer, packet opcode
decoder, or PCM/sample interpretation was recovered. The reference audits
cover the specified immediate, pointer, and direct-call encodings in the
named programs; they do not exclude indirect calls, addresses obtained
through other objects, or an uninspected path. They do not establish that
the ring is never activated. In the state produced by the inspected
constructor, slot retrieval returns zero because `+0x08` is zero, so the
producer consumes and discards its declared words. A writer that installs
the buffer/semaphore/command target and a consumer joined to that manager
are still needed before packet semantics can be assigned.

The `0x400`-byte stride fits at most `0x100` dwords, but both producer loops
trust their declared
words-per-packet without enforcing that limit. The absence of clean
non-excluded `0x2200` blocks prevents payload corroboration. The explorer's
`PCM_Audio` label therefore remains an unverified lead.

### `0x1800` descriptor fields and off-screen pass

**Observation:** constructor `FUN_0018B570` and its caller
`FUN_001A0B80` consume the `0x18`-byte descriptor as follows:

| Descriptor offset | Width | Use |
| ---: | ---: | --- |
| `+0x04` | `2` | Ordered-controller slot passed to `FUN_0010A1D0`. |
| `+0x06`, `+0x08` | `2` each | VRAM X/Y. `FUN_0018B410` passes them to `FUN_00112AE0` with pixel format `0` (`PSMCT32`) and stores the result at object `+0x156`. |
| `+0x0A`, `+0x0C` | `2` each | Width and height. `FUN_0018B410` stores their base-2 logarithms at object `+0x15A` and `+0x15B`. |
| `+0x0E`, `+0x10` | `2` each | Second VRAM X/Y. They are passed to `FUN_00112950` with format `0x31` (`PSMZ24`), shifted left by five, and stored at `+0x158`. |
| `+0x12` | `1` | Copied to `+0x15E`: the number of composite passes in `FUN_0018BF90`. |
| `+0x13` | `1` | Copied to `+0x15F`: the multiplier for the per-pass offsets from table `0x003FB500` in `FUN_0018BF90`. |
| `+0x14` | `4` | Projection scalar. The materializer copies it to runtime `+0x170` at `0x001A0DB4` (default object) and `0x001A1300` (named object). `FUN_001A2000` copies it to render environment `+0xE0`; `FUN_0018CF70` uses that value in vector scaling while constructing the geometry packet. `FUN_0018B570` itself does not read it. |

The constructor also links the object into a global list at `gp-0x356C`.
`FUN_0018B8E0` walks that list and calls `FUN_0018B930` for each object with
queued draw packets at `+0x150`. `FUN_0018B930` first builds GS setup through
`FUN_0018C800`, using the `+0x158` address with format `0x31` and the logarithmic
size. It then runs `FUN_0018C4C0` and `FUN_0018CC00` with the `+0x156` address
in format `0`, and splices each queued packet into the object's DMA chain.
`FUN_0018BF90` then uses the `+0x156` target as `TEX0_1` and draws textured
rectangles through `UV` and `XYZ2` vertex pairs. It draws one rectangle per
composite pass. Mode byte `+0x15C` values `2` and `3` use one neutral-gray
pass. In other modes, the `RGBAQ` color is black with alpha `0x80` or has
alpha from object byte `+0x15D`, initialized to `0x20`.

Clean `PPT2310_ST00.CCS` values therefore describe a 256×256 `PSMCT32` target
at VRAM coordinates `(960, 0)`, a `PSMZ24` region at `(896, 0)`, three
composite passes, offset multiplier `0`, and projection scalar `1000.0`.

**Observation — frame controls and binding:** both `FUN_001A0B80`
materialization branches initialize runtime direction `+0x160` to the VU
`vf0` vector `(0, 0, 0, 1)` and runtime strength `+0x174` to zero. Frame tag
`0x1801` calls `FUN_001B57F0`, which reads a 20-byte payload: target ID,
three Euler angles in degrees, and one scalar word. It chooses the target's
play object through `FUN_001B56B0`, falling back to the default extended
controller at play-context `+0xF8` when that resolution returns zero. The
angles are converted to radians and used to transform an input whose
initialized XYZ components are `(0, 0, -1)` into runtime `+0x160`; the final
word is stored at `+0x174`. The input's fourth component at stack `+0xAC`
is not initialized by this handler. `FUN_0010BA40` reaches `FUN_00151FF0`,
which reads and multiplies all four components, so a definite input W value
cannot be assigned from this code.

When `FUN_001A2000` draws a model entry with a nonzero controller pointer,
it installs that pointer at render-environment `+0xCC`, copies its direction
to `+0xD0..+0xDC` and projection scalar to `+0xE0`, and converts its strength
to byte `+0xE4` as `(int(clamp(strength, 0, 1) * 256) + 1) >> 1`.
The producer skips strength byte zero and caps larger values at `0x80`.
The zero-initialized strength therefore suppresses this geometry pass until
a frame control or another owner supplies a nonzero value.

**Observation — model geometry producer:** `FUN_00190F40` reaches
`FUN_0018CF70` through its scene object's auxiliary pointer at `+0x9C`
when flag byte `+0xA8` bit `0x20` is set. `FUN_0018CF70` requires the active
controller, a nonzero mode byte `+0x15C`, a nonempty referenced geometry
region (`part +0x34/+0x38`), and nonzero strength. It constructs a `0x170`-byte
VIF/DMA packet referencing the microprogram at `0x003C3CA0` and the part's
geometry buffer. At `0x0018D6F8` it calls
`FUN_0018B700(controller, strength_byte, packet_head, packet_tail)`.
This is a direct model-geometry producer for the same controller consumed
by `FUN_0018B930`; it is not inferred from the explorer label.
The general model-part branch of `FUN_001B0C40` calls `FUN_0018D740`, which
derives the `+0x34/+0x38` geometry packet from packed XYZ vertices and
triangle-index triplets. If its geometry preparation fails, it leaves both
fields zero. This independently joins the auxiliary buffer to file tag
`0x0800` model geometry.

`FUN_0018B7B0` selects a bucket by the strength byte. The object has fifteen
inline `0x10`-byte bucket slots at `+0x50..+0x13F`, list head `+0x150`,
and count `+0x154`. Equal keys reuse a bucket. A new key uses another slot
while the count is below fifteen; after that, it chooses an existing nearby
key instead of allocating. Each bucket stores its next link at `+0x00`, key
at `+0x04`, packet head at `+0x08`, and tail at `+0x0C`.
`FUN_0018B700` appends DMA chains to that bucket. `FUN_0018B930` drains the
buckets into the off-screen controller chain and clears both head and count
at the end of the pass.

**Observation — named shadow-class use:** constructor `FUN_0039B050`
allocates a separate `0x3C`-byte owner and installs vtable `0x005DD220`.
Its first entry is descriptor `0x005D6078`, whose name pointer is
`0x005B3840`, the embedded string `ccBgDrawShadowAnm`. Its initializer
`FUN_0039ABB0` allocates a `0x160`-byte controller and constructs it through
`FUN_0018B650`. Its ordered base, global-list node, queue, and render
parameters match the layout through `+0x15F` initialized by `FUN_0018B570`.
The initializer sets its render-target/depth coordinates, composite-pass
count, offset multiplier, and alpha. Draw method
`FUN_0039AAE0` temporarily binds that controller at render-environment
`+0xCC` and its owner's scalar at `+0xE0`, draws the owned animation through
`FUN_001BB790`, and restores both fields. The named class therefore uses
this controller family for shadow animation. Its vtable belongs to the
separate owner, not the `0x180`-byte object materialized from file tag
`0x1800`; the tag cannot be renamed to `ccBgDrawShadowAnm`.

**Inference:** `0x1800` renders its queued draws into a small off-screen
target. It then composites that target back as darkened, alpha-blended
rectangles, which fits a soft shadow or silhouette overlay. The
[explorer label](#negative-results-and-labels-not-promoted) `Shadow` agrees.
The geometry producer, direction, projection scalar, strength control, and
named shadow-class use support that interpretation more directly than the
file label. The exact operation of microprogram `0x003C3CA0` remains
unresolved: the maintained resident analysis exposes no function at that
address. The confirmed name above therefore states the observed
projection/composite role rather than a specific VU projection algorithm.

### File tag `0x0003`: object-section marker

**Observation:** `FUN_001A9060` reads a three-part header for chunk 3: the
16-bit ID, a discarded halfword, and a discarded length dword. It requires the
ID to be `3` and then calls `FUN_001AC8A0`. The dispatcher reads the same
three-part header for each block and ignores the high halfword. It reads the
length at `0x001AC910`, converts dwords to bytes at `0x001AC924`, and passes
that value in `a1` to each parser; whether it is used is parser-specific.
`FUN_001B1920`, `FUN_001B2930`, `FUN_001B4B40`, and `FUN_001B4BC0`
use it for counted payload reads or allocation. There is no generic seek to
the declared end of a block. The `0x0003` branch calls `FUN_001ADA90`, which
is only `jr ra`. A second `0x0003` header inside the object stream consumes exactly its
eight header bytes. It publishes nothing and leaves the parser in object-block
state.

**Clean-file observation:** every one of the 1,731 non-excluded NA2 CCS files
has exactly one section-3 header immediately after chunk 2, and each has length
`0`. In 1,683 files the high halfword is `0x0000`, and in 48 it is `0xCCCC`.
An aligned-word scan found nine other `0xCCCC0003` words. None is followed by a
valid block chain, and each lies inside another block's payload. Walks that
followed block lengths found no in-stream repeat of the marker where the walk
remained synchronized.

**Confirmed identity:** file tag `0x0003` is the object-section marker. Its
dispatcher route makes a repeated marker a harmless no-op. Why the route exists
is not established; tolerance of repeated or concatenated section markers is
only a hypothesis.

### Unresolved `0x1F00` binary and runtime layouts

**Observation:** `FUN_001B2930` is a two-pass parser. It first copies the complete payload to a
temporary buffer and computes the exact output size, then makes one
`FUN_00117700` allocation, resolves record IDs through `FUN_001AD8C0`, installs
runtime tag `0x1F00` and the allocation pointer at record `+0x2A` and `+0x2C`,
and frees the temporary buffer. Apart from resolved record pointers, every
pointer written into the result targets that same allocation. The independent
`FUN_001A9F10` teardown branch therefore frees only the allocation root through
`FUN_00105650`.

The input payload starts with this header; offsets are relative to the copied
payload:

| Offset | Width | Parser-observed role |
| ---: | ---: | --- |
| `+0x00` | `4` | Target record ID passed to `FUN_001AD8C0`. |
| `+0x04` | `2` | Group count. |
| `+0x06` | `2` | Record-ID table count; the parser advances past this many four-byte entries before reading the first group. |
| `+0x08` | `4 * record-ID table count` | Record-ID table. Each group selects one entry by index and resolves it through `FUN_001AD8C0`. |

Each group follows the record-ID table and the preceding variable-length
group. Its input representation is:

| Group-relative offset | Width | Parser-observed role |
| ---: | ---: | --- |
| `+0x00` | `2` | Index into the header's record-ID table. |
| `+0x02` | `2` | Ignored by this parser; it is neither tested nor copied. |
| `+0x04` | `2` | Four-byte-pair count. |
| `+0x06` | `2` | Item count. |
| `+0x08` | `4 * pair count` | Opaque pairs of two halfwords, copied without interpretation. |
| variable | variable | `item count` consecutive items in the format below. |

Each input item has a 12-byte fixed header followed by one required and one
conditional array:

| Item-relative offset | Width | Parser-observed role |
| ---: | ---: | --- |
| `+0x00` | `2` | Element count. |
| `+0x02` | `2` | Flags. Bit `0x1000` alone is tested here. |
| `+0x04` | `4` | Four opaque bytes copied individually. |
| `+0x08` | `4` | Two opaque halfwords. |
| `+0x0C` | `4 * element count` | Primary array, copied as two halfwords per element. |
| following primary array | `2 * element count`, rounded up to a four-byte boundary | Conditional secondary halfword array, present only when flags include `0x1000`. |

The single runtime allocation begins with two parallel group tables followed by
the packed groups. For group count `N`, its root layout is:

| Runtime offset | Width | Parser-observed role |
| ---: | ---: | --- |
| `+0x00` | `4` | Resolved target record pointer. |
| `+0x04` | `2` | Group count `N`; `+0x06` is not written by this parser. |
| `+0x08` | `4` | Pointer to the resolved-group-record array at `+0x0C + 4*N`. |
| `+0x0C` | `4 * N` | Pointers to the `N` packed group descriptors. |
| `+0x0C + 4*N` | `4 * N` | Resolved record pointer selected for each group. |
| `+0x0C + 8*N` | variable | First packed group descriptor. |

Each packed group starts with an eight-byte header and `0x10` bytes per item;
its copied halfword-pair array follows the fixed item descriptors. Each item
descriptor stores a pointer to its primary array, the element count and flags,
the four opaque bytes, and the two opaque halfwords. If bit `0x1000` is set,
the secondary halfword array immediately follows that item's primary array and
the next region is four-byte aligned. These pointer and packing relationships
are confirmed structure; what the pairs, flags other than `0x1000`, opaque
fields, and arrays mean remains unknown.

**Bounded negative result:** byte searches across all register encodings
of the aligned MIPS `addiu` literal form of `0x1F00` found primary-resident
instruction uses only in `FUN_001A9F10` at `0x001A9F98`, dispatcher
`FUN_001AC8A0` at `0x001AC964`, and
parser `FUN_001B2930` at `0x001B2A64`. The corresponding `ori`, `slti`, and
`sltiu` searches found no aligned primary-resident instruction match. This
supports the absence of a direct literal-tag consumer, but does not exclude
a table-driven consumer or code that constructs the value by
another instruction sequence. The same zero-register `addiu` and `ori` search
found no match in the NA2 `BTL.BIN` or `ETC.BIN` overlays. `ADV.BIN` is
excluded. NUN5 and NUN6 each have exactly three aligned matches in their boot
ELFs. NUN3 has five aligned matches. Three are teardown `FUN_00160000`,
dispatcher `FUN_00162CA0`, and parser `FUN_00167F50`, which has the same
two-pass layout. The other two NUN3 matches, `FUN_001AF1E0` and
`FUN_001B3860`, use `0x1F00` as an unrelated numeric argument. No related game
supplied a consumer in this bounded audit. The route remains semantically
unresolved rather than being assigned a class or resource name.

### Runtime tag `0x1000` from texture and CLUT construction: image-transfer group

This subsection concerns runtime tag `0x1000` written by texture and CLUT
construction. File-block handler `FUN_001ADB70` also writes that runtime value;
the relationship between the two is covered at the end.

**Observation — stream field.** When container version `+0xAC` is at least
`0x92`, both texture parser `FUN_001B3C70` and CLUT parser `FUN_001B3810` read
one extra record ID after their own target (and, for textures, after the CLUT
ID). If that record resolves to a record with a non-empty name, the texture
path calls `FUN_0019E770(texture, record)` and the CLUT path calls
`FUN_0019EDE0(clut, record)`.

**Observation — group node.** When the record's runtime pointer `+0x2C` is
still the unmaterialized sentinel `4`, both helpers first search a global
singly linked list rooted at `gp-0x3570` for a node whose bytes
`+0x08..+0x25` equal the record's first 30 name bytes. Without a match they
allocate `0x38` bytes, construct the node with `FUN_0019D2D0`, store it at
record `+0x2C`, and write runtime tag `0x1000` at record `+0x2A`. A match
jumps directly to member attachment: it uses the matched node but leaves
the requesting record's pointer at `4` and its tag unchanged. When the record
is already materialized, the helpers attach using its existing pointer.
The node layout used by the resident code is:

| Node offset | Role |
| ---: | --- |
| `+0x08` | Name comparison key. `FUN_0019D2D0` writes only the record name's first byte here. |
| `+0x28` | List of member textures; eight-byte links added by `FUN_0019D180`. |
| `+0x2C` | List of member CLUTs; eight-byte links added by `FUN_0019D130`. |
| `+0x30` | Next node in the `gp-0x3570` global list. |

Disassembly at `0x0019D2DC..0x0019D2E0` confirms a single `lb`/`sb` name-byte
copy. The constructor does not initialize node `+0x00` as a source-record
backpointer. Its `FUN_00117150` allocation reaches `FUN_001180D0` and
`FUN_001186A0` or `FUN_00118610`; those paths write allocator metadata before
the returned payload and do not clear it. Neither allocation nor construction
initializes the other 29 comparison-key bytes. The exact bytes present in a
particular allocation were not observed, so same-name matching remains
dependent on prior memory contents.

The texture stores the node at texture `+0x2C` and sets texture byte `+0x3B`
bit `0x02`. The CLUT stores it at CLUT `+0x14` and sets CLUT byte `+0x20` bit
`0x02`. Texture destructor `FUN_0019E9C0`, the concrete `ccTexChunk` vtable
slot `+0x08`, tests that bit and calls `FUN_0019D0A0` to unlink the texture.
The CLUT counterpart is `FUN_0019D010`. When both member lists are empty,
either unlink path frees the node through `FUN_0019D200`. The record-teardown
branch in `FUN_001A9F10` only clears the record pointer. The members therefore
own the node's lifetime through a reference-counting pattern.

**Observation — consumer.** Resident `FUN_00372DF0` resolves the record
`BLT_strbreak` through `FUN_001A8F00`, which returns record `+0x2C`, and stores
the result at `gp-0x3288`. `FUN_003730C0` then uses that node in this order:

1. `FUN_0019CE00(node, context)` calls every member texture's virtual slot
   `+0x10`, which is `FUN_001190D0` in the `ccTexChunk` vtable at
   `0x005D9E90`. For every member CLUT it calls `FUN_0010F9B0` on that CLUT's
   transfer descriptor at `+0x10`.
2. `FUN_0019CF60(node)` sets bit `0x02` of byte `+0x0E` in every member
   texture's `0x20`-byte per-level transfer descriptors at texture `+0x28`.
   It sets the same bit in every member CLUT's descriptor.
3. `FUN_001BB790` runs the draw path.
4. `FUN_0019CEB0(node)` clears those bits.

`FUN_0010F940` and `FUN_0010F9B0` submit a descriptor only while bit `0x02` is
clear. Submission path `FUN_0010FA10` builds a GS packet that writes registers
`0x50`, `0x51`, `0x52`, and `0x53` (`BITBLTBUF`, `TRXPOS`, `TRXREG`, and
`TRXDIR`) before the image data transfer.

**Confirmed identity (high confidence):** when texture or CLUT construction
assigns runtime tag `0x1000`, the record refers to a shared GS image-transfer
group. Attached textures and CLUTs can have their uploads submitted together
and then suppressed as a set. No embedded C++ class name or vtable was
found for the node.

**Clean-file corroboration:** a walk of the non-excluded NA2 CCS corpus that
decodes texture blocks with the parser's per-level counts found 3,631 non-zero
group references. They occur in texture/CLUT pairs, except for one texture-only
group. Every referenced record name begins with `BLT_`, for example
`BLT_obj`, `BLT_bg`, and `BLT_item`. Clean `STRMCMN.CCS` contains the
texture-only group `BLT_strbreak` that `FUN_00372DF0` resolves, with member
`TEX_strbreak`. In GS terminology, `BLT_` matches the `BITBLTBUF` transfer
that the consumer submits. This name correspondence is corroboration only.

**Relationship to file tag `0x1000` (inference, not established):**
`FUN_001ADB70` writes the same runtime tag but sets record `+0x2C` to `0`, not to
a node. A later texture or CLUT naming that record would therefore take the
reuse branch with a null node, and `FUN_0019D180` or `FUN_0019D130` would
dereference address `0x28` or `0x2C`. The file block therefore cannot safely
precede group members in the same stream. It may be a legacy placeholder for
the same group record. No clean non-excluded NA2 block uses file tag `0x1000`.
The shared number and the pointer-only teardown are consistent with that
reading, but they do not prove it.

## Negative results and labels not promoted

- The dispatch set and differing destructor families do not provide class
  names for the unresolved rows. In particular, the second virtual layout at
  `0x0600` proves only that a separate polymorphic secondary object exists.
- The embedded `ccExtObjLinker` name exists in the resident executable, but no
  direct constructor/vtable chain joins it to the `0x0A00` parser branch, so
  that class name is not assigned above. The `ccLight` family is
  assigned only because the `0x0600` selector-to-constructor chain is direct.
- Embedded `ccAnmCtrlInterpObj` and `ccAnmCtrlInterpBase` descriptors also
  exist, but the inspected `0x1700` and `0x1800` materializers construct
  non-vtable controller layouts and never install either descriptor. The
  controller resource roles are therefore named above, but neither numeric tag
  inherits those nearby RTTI class names.
- Other embedded particle names, including `ccParticleManager`,
  `ccHigeParticleGenerator`, and `ccHigeParticleManager`, are not assigned to
  the routes above. The only exact generator RTTI chain reached from the
  `0x0D90` descriptor installs `ccGenerator2`.
- Embedded background-system names containing `Clump` are not connected to
  the `0x0900` parser or its aggregate runtime by a constructor/vtable chain.
  They do not supply a class name for the confirmed composition resource.
- A read-only chunk-boundary scan covered 1,732 extracted CCS files outside
  every path containing the excluded tokens. It found no file blocks for
  `0x0D00`, `0x1000`, `0x1100`, `0x1200`, `0x1F00`, or `0x2200`. This is a
  useful absence result for the inspected non-excluded corpus, not proof that
  the resident parser branches are unreachable in every release or input.
  Block lengths are not a reliable walk key for every type. For example,
  texture blocks can declare more words than `FUN_001B3C70` consumes. The
  parser follows its own per-level counts instead. The absence was therefore
  rechecked with a superset search of every four-byte-aligned word in the 1,731
  non-excluded decompressed files. That search found no `0xCCCC` word for
  `0x0D00`, `0x1100`, `0x1200`, or `0x1F00`. The only `0x1000` and `0x2200`
  matches were 30 and 20 words inside texture pixel data in `HOME.CCS`,
  `HOME/IFKKW.CCS`, `SCENE/PPT6000_1DDR.CCS`, `STR/D64_25E.CCS`, and
  `STR/D70_20E.CCS`. Their length fields are implausible, such as
  `0xCCCCCCCC`, and none starts a valid block chain. The search cannot see a
  block whose high halfword is not `0xCCCC`, which the dispatcher would also
  accept. Where length-following walks remained synchronized, the only block
  in that form was the chunk-3 header.
- The three legacy markers `0x1000`, `0x1100`, and `0x1200` publish numeric
  record tags but preserve no payload object. No consumer, materializer, or
  class-name chain was recovered for them, so assigning semantic names from
  their sizes or adjacency would be speculative. Unlike the `0x1000`
  handler's explicit null publication, `FUN_001ADB20` and `FUN_001ADAA0`
  leave record `+0x2C` unchanged when writing tags `0x1100` and `0x1200`.
  Searches across all register encodings of `addiu` and `ori` found aligned
  primary-resident CCS uses only in the dispatcher and parsers. Every other
  aligned code match was inspected: `0x1100` seeds the random state in
  `FUN_0017FD90` and `FUN_00180060`; `FUN_001406E0` and `FUN_001404E0`
  pass `0x1100` and `0x1200` to the two-word service-marker updater
  `FUN_001413B8`; matches in the RPC wrapper block `FUN_00162B68` through
  `FUN_00165DB0` construct buffer address `0x00611100`, used in calls to
  `FUN_001624D0`, rather than a CCS tag. The narrower zero-register overlay
  search found one aligned `BTL.BIN` match: a `0x1100`-byte allocation.
  `ETC.BIN` had no match. NUN3's
  dispatcher `FUN_00162CA0` routes all three tags to handlers,
  `FUN_001643C0`, `FUN_00164370`, and `FUN_001642E0`, with the same stub
  behavior, so the older game supplies no fuller form.
- `0x1F00` is adjacent to `0x1900` in neither the dispatcher nor any proved
  runtime relationship. A raw clean-binary audit of the complete
  `ccMorpher` vtable identified its concrete blend method `FUN_00197570`, and
  both recovered source-list population paths feed it materialized playback
  objects without reading a `0x1F00` descriptor. The nested-table shape alone
  therefore does not justify calling `0x1F00` morph data.
- The maintained `CCSFileExplorer.exe` 3.0.0.0 (487,936 bytes, SHA-256
  `4F0764E6B44FDD40DBD9A7BA0E32DF8F24CC72019BA93B3BD35742A02CC8B2E8`)
  labels `0x2400` behavior as script/function data with Puppet handling.
  Static reflection did not reveal a resident constructor, destructor, vtable,
  or RTTI link for a script class on that route, so only the resident-proved
  generic blob identity is promoted. The tool's script label remains a useful
  unpromoted lead. Its independent model/geometry decoding of `0x0800` is only
  corroboration for the resident parser and consumer evidence cited above.
- The same tool build has a name-to-tag table. In its IL, each `ldstr` label is
  followed by an `ldc.i4` block tag. Relevant entries include:

  | Tag | Tool label |
  | ---: | --- |
  | `0x0003` | `Setup` |
  | `0x0D00` | `Particle` |
  | `0x1000` | `Blit_Group` |
  | `0x1100` | `FrameBuffer_Page` |
  | `0x1200` | `FrameBuffer_Rect` |
  | `0x1800` | `Shadow` |
  | `0x1F00` | `Sprite2Tbl` |
  | `0x2000` | `AnimationObject` |
  | `0x2200` | `PCM_Audio` |
  | `0x2300` | `Dynamics` |

  The tool also contains the literal record names `BLT_bg` and `BLT_obj`. None
  of these label strings exists in the resident executable. `Setup` and
  `Blit_Group` agree with the resident section-marker and image-transfer-group
  findings above. The other labels are only leads. The resident
  shapes fit some of them without proving them. `0x1200` consumes counted
  eight-byte entries, which could hold four halfword rectangle fields.
  `0x1000` consumes a counted dword list. `0x1F00` holds groups of
  halfword-pair arrays. `0x0D00` is a transform-only composition node rather
  than a proven particle object.
- Object-name prefixes such as `OBJ_`, `MAT_`, `TEX_`, `CLT_`, `ANM_`,
  `HIT_`, `PAC_`, `PGE_`, `EFF_`, and `EXT_` are lookup/name conventions.
  Only `EXT_` participates directly in type-sensitive code. The other prefixes
  are reported only where resident construction and consumption independently
  establish the resource role.
- Sample offsets were used only to validate decompressed chunk boundaries; none
  is presented as a resident or live address. No live object instances or
  overlay-specific consumers were examined. Resource roles above are therefore
  resident static identities, not claims about every on-disk variant or
  live-instance state.
