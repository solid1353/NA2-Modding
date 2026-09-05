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
- **Exploration depth:** the numeric branch inventory of file-block dispatcher
  `FUN_001AC8A0` was exhaustively enumerated: 34 object/control routes plus
  terminator `0x0005`. Every route in that inventory was checked against the
  runtime-record teardown switch `FUN_001A9F10`. Tracing beyond those two
  switches was bounded to each direct parser, the common materializer
  `FUN_001A0B80`, and relevant immediate constructors, destructors, vtables,
  RTTI/name descriptors, finalizers, and consumers. Important bounded paths
  included `FUN_001952F0` for composition children, `FUN_001AD240` for
  post-parse attachment, and `FUN_00197570` for concrete morph blending. This
  was not an exhaustive whole-program call-graph audit.
  Eight exact clean CCS inputs listed below were decoded in
  memory for semantic payload checks. Separately, a chunk-boundary inventory
  exhaustively scanned the 1,732 extracted CCS files in the permitted corpus;
  it established tag presence and the reported absences, but did not decode
  every payload semantically. The maintained explorer executable was inspected
  statically only for independent `0x0800` and `0x2400` corroboration.
- **Confirmed coverage:** 29 numeric routes have a confirmed resident resource
  identity or block role in the table below. Exact embedded class names are
  promoted only for the texture, light, generator, morpher, and stream draw-
  environment families whose constructor/vtable/name chains were recovered.
  The remaining resource labels describe proved layouts and consumers, not
  speculative C++ class names.
- **Unresolved or untested:** file routes `0x0003`, `0x1000`, `0x1100`, `0x1200`, and
  `0x1F00` remain unresolved for the reasons recorded in the ledger. A final
  bounded check found that texture and CLUT construction also assign runtime
  tag `0x1000` while creating a shared `0x38`-byte owner through
  `FUN_0019E770`, `FUN_0019EDE0`, and `FUN_0019D2D0`; no direct relationship to
  file-block handler `FUN_001ADB70` was established, so those two uses are not
  conflated or promoted. No direct consumer was recovered for the `0x1F00`
  nested table.
- **Deliberate exclusions and overlap:** the explicitly excluded mode/resource
  subtree, overlays, and overlay resource trees were not inspected.
- **Evidence limitations:** static evidence is limited to the identified clean resident executable, its
  maintained read-only exports, the listed clean assets, and the identified
  tool build. No emulator execution, runtime injection, or live-memory
  observation validated these mappings; clean assets provide file-level
  corroboration only.

## Evidence identity and address spaces

The clean resident and CCS input identities and resident address conversion are
defined in [Standard game file identities](file_identities.md).

Eight clean, read-only NA2 CCS files were decompressed and parsed in memory for
corroboration. No data was written back to these files:

| Input below `@source_na2/DATA/DATA.CVM.files/DATA.CVM.iso.files` | Compressed size | Decompressed size |
| --- | ---: | ---: |
| `PL/1KHWBOD1.CCS` | 87,260 | 542,528 |
| `PL/2DDRBOD1.CCS` | 826,268 | 1,687,292 |
| `PL/2HKGCHA1.CCS` | 36,040 | 83,568 |
| `PL/2TEWCHA1.CCS` | 29,591 | 66,632 |
| `BUDDY/2ASWBDY0.CCS` | 49,569 | 78,376 |
| `SCENE/PPT2310_ST00.CCS` | 385,282 | 1,499,860 |
| `SCENE/PPTS04.CCS` | 440,211 | 1,240,424 |
| `XNINKA.CCS` | 68,535 | 273,172 |

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
`0x005D9E1C`. No other address below is a file offset. No overlay or overlay
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
| `0x0400` | CLUT/palette resource | File-tag dispatch calls `FUN_001B3810`. It allocates `0x28` bytes through `FUN_001B3C40`, publishes tag `0x0400`, consumes packed color words, and prepares the palette storage used by the texture path. Texture construction in `FUN_0019EAB0` stores this dependency at texture `+0x3C`; `FUN_0019E760` returns that field, and `FUN_00115BA0` classifies the referenced record under selector `CLT`. Clean sample records on this route are named `CLT_...`. No resident C++ class name was recovered. | **High** |
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
| `0x1800` | Extended parameterized ordered-controller binding | Kind-one entries in `FUN_001B2220` create `0x1800` controller slots in the same shared table, and direct file-tag parser `FUN_001B1FF0` fills either a referenced record's `0x18`-byte descriptor or the default slot with six halfwords, two bytes, and a trailing word. `FUN_001A0B80` materializes that descriptor as a `0x180`-byte runtime object through `FUN_0018B570`. The constructor embeds the same `FUN_0010A1D0` ordered-controller base, registers an additional global controller node, and passes four descriptor halfwords to `FUN_0018B410`; cleanup calls `FUN_0018B4C0` and frees the allocation. Clean `PPT2310_ST00.CCS` supplies a default descriptor with halfwords `960, 0, 256, 256, 896, 0`, bytes `3, 0`, and trailing word `0x447A0000`. This establishes an extended parameterized controller binding; the individual parameter meanings and a C++ class name remain unresolved. | **High** |
| `0x1900` | `ccMorpher`, derived from `ccModifier` | File-tag dispatch calls `FUN_001B2190`, which builds an eight-byte descriptor from a target record and a linked record and publishes runtime tag `0x1900`. `FUN_001A0B80` directly tests that tag, allocates `0x114` bytes, first installs descriptor `0x005D9DF0` at object `+0x0C`, and then replaces it with `0x005D9E10`. The first descriptor resolves through `0x005BF7F8` to embedded `ccModifier` at `0x003FB580`; the concrete descriptor resolves through `0x005BF810` to `ccMorpher` at `0x003FB590`. In the clean executable, concrete vtable slot `+0x0C` at resident `0x005D9E1C` is `FUN_00197570`; it applies the weighted source list installed through `FUN_00197B20` and `FUN_00197B30` to blend packed vertex positions into model geometry. `FUN_001B56E0` and the `0x1902` command branch in `FUN_001B8410` populate that list from materialized playback objects. Playback cleanup in `FUN_001A2520` calls the concrete object's virtual destructor through object `+0x0C`, slot `+0x08`. | **High** |
| `0x1A00` | `ccStreamOutlineParam`, derived from `ccDrawEnvCtrl` | The direct parser publishes runtime tag `0x1A00`. `FUN_001A0B80` tests that tag, allocates `0x40` bytes, installs the `ccDrawEnvCtrl` base descriptor and then concrete descriptor `0x005D9EF0` at object `+0x04`; the descriptor resolves through `0x005BF980` to embedded `ccStreamOutlineParam` at `0x003FB6F0`. | **High** |
| `0x1B00` | `ccStreamCelShadeParam`, derived from `ccDrawEnvCtrl` | The direct parser publishes runtime tag `0x1B00`. `FUN_001A0B80` tests that tag, allocates `0x40` bytes, installs the same base and then concrete descriptor `0x005D9EE0` at object `+0x04`; it resolves through `0x005BF968` to embedded `ccStreamCelShadeParam` at `0x003FB6D0`. | **High** |
| `0x1C00` | `ccStreamToneShadeParam`, derived from `ccDrawEnvCtrl` | The direct parser publishes runtime tag `0x1C00`. `FUN_001A0B80` tests that tag, allocates `0x48` bytes, installs the same base and then concrete descriptor `0x005D9ED0` at object `+0x04`; it resolves through `0x005BF950` to embedded `ccStreamToneShadeParam` at `0x003FB6A0`. | **High** |
| `0x1D00` | `ccStreamFBSBlurParam` | The direct parser publishes runtime tag `0x1D00`. `FUN_001A0B80` tests that tag, allocates `0x48` bytes, and installs descriptor `0x005D9EC0` at object `+0x00`; it resolves through `0x005BF930` to embedded `ccStreamFBSBlurParam` at `0x003FB680`. | **High** |
| `0x2000` | Transitional pre-object metadata overlay/carrier | File-tag dispatch calls `FUN_001B2510`, which reads a target, one scalar field, and three nullable record references. If the target is already runtime type `0x0100`, `0x0E00`, or `0x0A00`, it writes the applicable fields directly into that descriptor. If the target is still untyped, it allocates a temporary `0x14`-byte carrier and publishes runtime tag `0x2000`. The later `0x0100`, `0x0A00`, and `0x0E00` parsers explicitly recognize that tag, recover the saved fields, free the carrier, and replace it with their final descriptors. Clean `XNINKA.CCS` includes this sequence for records such as `OBJ_xback01` and `OBJ_sun01`. This proves a parse-order-independent metadata overlay, not a stable standalone object class. | **High** |
| `0x2200` | Global producer/consumer ring packet batch | File-tag dispatch calls `FUN_001B44B0`. The parser reads batch and per-packet counts, marks the owning container with flag `0x80`, prepares the fixed global manager reached through `DAT_00602A04`, and for every packet requests a `0x400`-stride ring slot through `FUN_001090C0`. It copies the requested dwords into an available slot and commits it with `FUN_00109000`; if no slot is available, it consumes the same stream words without publishing partial state. The playback path tests the same container flag and brackets use of that manager with `FUN_00109330` and `FUN_00109240`, whose semaphore and ring-state updates establish a synchronized producer/consumer lifetime. This proves a block-only packet batch for the global ring. The packet command language and a class name remain unresolved, and no block occurred in the inspected non-excluded sample corpus. | **High** |
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
| `0x0003` | `FUN_001ADA90` | None | Unresolved control block; handler is empty, consumes no payload, and publishes no record in the inspected code. |
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
| `0x1000` | `FUN_001ADB70` | pointer clear only | Unresolved legacy marker: publishes the numeric tag with a null descriptor and consumes, but does not preserve, the counted dwords. |
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
| `0x2200` | `FUN_001B44B0` | No explicit branch | **Confirmed global producer/consumer ring packet batch; no runtime record is published.** |
| `0x2300` | `FUN_001B4B40` | No explicit branch | **Confirmed scene-composition child-attachment parameter block; no runtime record is published.** |
| `0x2400` | `FUN_001B4BC0` | direct free through `FUN_00105650` | **Confirmed opaque binary-blob resource; see above.** |

File tag `0x0005` is the stream terminator handled inside `FUN_001AC8A0`, not
an object-type mapping. An unrecognized file tag reaches the deliberate
null-store failure path. The terminator's container-finalization behavior is
documented in [Resident CCS runtime](ccs_runtime.md#parsing-type-dispatch-and-publication).

## Negative results and labels not promoted

- The dispatch set and differing destructor families do not provide class
  names for the unresolved rows. In particular, the second virtual layout at
  `0x0600` proves only that a separate polymorphic secondary object exists.
- The embedded `ccExtObjLinker` name exists in the resident executable, but no
  direct constructor/vtable chain joins it to the `0x0A00` parser branch in
  this pass, so that class name is not assigned above. The `ccLight` family is
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
- The three legacy markers `0x1000`, `0x1100`, and `0x1200` publish numeric
  record tags but preserve no payload object. No consumer, materializer, or
  class-name chain was recovered for them, so assigning semantic names from
  their sizes or adjacency would be speculative.
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
