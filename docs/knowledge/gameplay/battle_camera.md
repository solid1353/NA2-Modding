# Battle camera control

This note records the static BTL camera-controller state machine and the
camera transform fields that can be established without assigning names to
every camera preset. It does not cover Adventure, cutscene cameras, rendering
projection internals, or player-visible camera policy that has not been
runtime-tested.

The source is clean `PRG/BTL.BIN`, size `0x222300`, SHA-256
`56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C`.
The complete file, including its `0x40`-byte MWo3 header, loads at
`0x006B3F00`. The preserved Ghidra baseline omitted that header, so a physical
body displayed at address `g` executes at `g + 0x40`; absolute operands in the
file are already live and must not be shifted again. This mismatch also causes
some direct-call targets to be attached to a false continuation symbol 0x40
after the physical callee, so the findings below use instruction bytes and
field behavior rather than trusting those synthetic call labels.

A disposable Ghidra 12.1.2 import of the complete file at `0x006B3F00`
independently recovered the missing physical ranges and assigned functions at
their live addresses. It was used to audit the baseline, not retained as a
second canonical disassembly.

## Research coverage

- **Assigned scope:** the clean BTL battle-camera controller: resident
publication and lifetime, its eight object slots, request/event-to-mode
mapping, ownership switching, preset selection, stage-edge correction, and the
camera-object vector and smoothing fields reachable from those paths.
- **Exploration depth:** coverage is deep but bounded to the camera cluster and its resident owner. The
controller constructor/destructor and publisher were followed through resident
setup and teardown; all fixed slot loops and numeric mode-dispatch targets
`0..18` were accounted for; the mode-1/2/3 `0xB0` preset families and fixed
mode-4/5/6 records were decoded at their established fields; and raw bytes plus
a disposable correctly based import were used to recover functions hidden by
the maintained import's `0x40` displacement. Surrounding fighter, collision,
and stage code was sampled only where it directly supplied camera inputs.
- **Confirmed coverage:** resident publication/lifetime, all eight slots,
  numeric mode dispatch `0..18`, decoded preset families, and the established
  stage-edge correction path are documented from the scoped trace.
- **Unresolved or untested:** numeric request/mode names, exact eye-versus-target/world-axis semantics,
several preset fields, dynamic transition order, and visible behavior under
stage orientation remain unresolved.
- **Deliberate exclusions and overlap:** Adventure, cutscene cameras,
  projection/render internals, and unproved player-visible policy were
  excluded. Surrounding fighter, collision, and stage code was sampled only
  where it directly supplied camera inputs.
- **Evidence limitations:** no live camera capture, frame stepping, request
  injection, or patch validation was performed. The disposable import is
  supporting analysis only; the maintained read-only disassembly was not
  modified.

## Confirmed class and asset evidence

The overlay embeds runtime type names `ccCamera` and `ccCameraCtrl`, alongside
their `ccGameObj` / `ccGameObjCtrl` bases. It also contains named camera
resources `CAM_camera01`, `OBJ_camera01`, `OBJ_camera01_target`, and
`OBJ_camera1p`, plus formatted names `CAM_%s_camera1` and `CAM_%s_camera2`.
These names prove a camera object/controller family and resource-driven camera
paths; they do not by themselves name individual numeric modes.

## Address map

The following addresses are live addresses from the complete-file import. File
offset is `live - 0x006B3F00`.

| Live address | File offset | Established role |
| --- | --- | --- |
| `0x006DBD60` | `0x27E60` | publish/clear the shared controller pointer |
| `FUN_006DBEB0` | `0x27FB0` | controller construction wrapper |
| `FUN_006DBF00` | `0x28000` | deleting controller teardown wrapper |
| `FUN_006DBF70` | `0x28070` | controller state/slot initializer |
| `FUN_006DBFF0` | `0x280F0` | camera-object construction and registration |
| `FUN_006DC300` | `0x28400` | remove all non-null camera slots |
| `FUN_006DC3B0` | `0x284B0` | per-update dispatch and previous-state commit |
| `FUN_006DC450` | `0x28550` | request-to-mode derivation |
| `FUN_006DC5C0` | `0x286C0` | pending-event-to-request resolver |
| `FUN_006DC900` | `0x28A00` | numeric-mode handler dispatch |
| `FUN_006DC9C0` | `0x28AC0` | reset/return-to-resident-camera request |
| `FUN_006DCA80` | `0x28B80` | active camera ownership switch |
| `FUN_006DCC40` | `0x28D40` | stage-boundary/segment-side probe |
| `FUN_006DCDD0` | `0x28ED0` | handlers for modes 4 through 6 |
| `FUN_006DD130` | `0x29230` | mode-1 preset handler |
| `FUN_006DD530` | `0x29630` | mode-2 preset handler |
| `FUN_006DD9E0` | `0x29AE0` | mode-3 preset handler |

## Controller layout

The camera controller has capacity for eight camera-object slots.
Initialization and teardown loops independently establish the fixed array at
`+0x40`:

| Offset | Established role |
| --- | --- |
| `+0x00` | side selector; value 1 chooses the first fighter, other values the second |
| `+0x04` | derived camera-mode class |
| `+0x08` | previous derived class |
| `+0x0C` | active preset/variant index |
| `+0x10` | prior or exclusion preset index |
| `+0x14` | current camera request code |
| `+0x18` | previous request code |
| `+0x1C` | pending controller event/state |
| `+0x20` | previous pending event/state |
| `+0x24` | character/preset discriminator consumed by the mode mapper |
| `+0x28` | enables a save/profile-dependent duration counter |
| `+0x2C` | that counter, otherwise cleared each update |
| `+0x30` | output ownership state: resident/default versus BTL camera transition |
| `+0x34` | number of constructed camera slots |
| `+0x38` | selected camera-slot index |
| `+0x3C` | previous camera-slot index |
| `+0x40..+0x5F` | eight camera-object pointers |
| `+0x60` | owning object/list used to register and remove camera objects |

The cleanup loop removes every non-null slot through the `+0x60` owner and
then clears that owner. `FUN_006DBFF0` constructs exactly four initial objects:

| Slot | Allocation | Initialization established statically |
| ---: | ---: | --- |
| 0 | `0x160` | Seeds the vectors at `+0x30` and `+0x80`, then registers the object. |
| 1 | `0x250` | Stores fighter-0/fighter-1 position pointers at `+0x190/+0x194`; seeds related offsets with 140 and 120. |
| 2 | `0x250` | Mirrors slot 1 with the two fighter position pointers swapped. |
| 3 | `0x250` | Applies configuration record `0x00891E90` through the common camera setup path. |

Each successful construction is registered and increments `+0x34`, leaving
that count at four; slots 4 through 7 remain null at constructor return. The
eight-slot capacity therefore must not be reported as eight eagerly allocated
cameras. Allocation failure is not handled gracefully: the returned pointer is
subsequently dereferenced even when the allocator returned zero.

## Shared controller entry points

BTL accesses the current controller through resident global `0x006077E8`
(`$gp - 0x3208`). The complete-file import leaves live `0x006DBD60` as an
undefined 16-byte gap, but the raw instructions are an exact publisher:

```text
sw a0,-0x3208(gp)
jr ra
nop
```

An exhaustive aligned-word scan found this as the only BTL store to that GP
offset. Four adjacent entry points establish the public control surface:

| Live address | File offset | Behavior |
| --- | --- | --- |
| `FUN_006DBD70` | `0x27E70` | Returns true only when a controller exists and ownership state `+0x30` is 1. |
| `FUN_006DBDA0` | `0x27EA0` | Requests reset through `FUN_006DC9C0(controller, 1)`. |
| `FUN_006DBDD0` | `0x27ED0` | Writes the pending controller event at `+0x1C`. |
| `FUN_006DBDF0` | `0x27EF0` | Writes the side selector at `+0x00` and discriminator at `+0x24`. |

The resident battle-session setup and teardown establish the pointer's lifetime.
`FUN_001EF330` allocates `0x68` bytes, passes the allocation and the outer
graph's first owned object to live `FUN_006DBEB0`, stores the returned controller
at session `+0x1C`, and publishes the same value through `0x006DBD60`. The
wrapper runs `FUN_006DBF70` followed by `FUN_006DBFF0`, so the published object
is the controller whose layout and four constructed slots are documented above.

During `FUN_001EEFD0`, the resident calls live `FUN_006DBF00(controller, 1)`,
clears session `+0x1C`, and then calls `0x006DBD60(0)`. Thus the shared pointer
is match-session state: it is published only after construction and explicitly
cleared during teardown. The two resident calls at `0x001EF47C` and
`0x001EF0FC` are the only direct `jal` sites to the publisher in the clean
resident and BTL files.

## Request-to-mode mapping

When request `+0x14` changes from `+0x18`, the controller derives `+0x04`.
Three negative request codes have direct mappings:

| Request | Derived mode |
| ---: | ---: |
| `-5` | 4 |
| `-6` | 5 |
| `-7` | 6 |

Request 1 asks the selected fighter-side subsystem for a three-valued state:
return 0 maps to mode 2, return 1 maps to mode 1, and return 2 maps to mode 3.
All other requests pass through a discriminator mapper using `+0x24` and
`+0x14`. Confirmed explicit discriminator results include modes 7 through 18;
unrecognized values return `-1` and leave the prior class unchanged. The
numeric classes are established control values, not recovered camera names.

The complete-file import resolves the mapper exactly:

| Discriminator | Derived mode |
| --- | ---: |
| `0x10` | 8 |
| `0x21` | 9 |
| `0x27` | 10 |
| `0x2C` | 11 |
| `0x89` | 12 |
| `0x34` | 13 |
| `0x39` | 14 |
| `0x2E` | 15 |
| `0x59`, `0x8F`, or `3` | 16 |
| `1`, `0x1C`, `0x6B`, `0x71`, `0x75`, `0x95`, or `0xAB` | 7 |
| other bounded character-like ID whose metadata byte `+0x04` is set | 17 |
| request `-4`, independent of discriminator | 18 |

The pending event at `+0x1C` is itself converted to a request by
`FUN_006DC5C0`. Stable literal mappings are event `2 -> 5`, `6 -> -1`,
`7 -> -4`, `8 -> -5`, `9 -> -6`, and `10 -> -7`. Events 3, 4, and 5 map to
requests 2, 3, and 4 only while at least one fighter-side `+0xB00` field is
nonzero. Event 1 uses a second discriminator mapper and live fighter state, so
it is deliberately not reduced to one constant request.

The per-update commit copies current to previous fields (`+0x04 -> +0x08`,
`+0x0C -> +0x10`, `+0x14 -> +0x18`, `+0x1C -> +0x20`), clears the pending
event, and either increments or clears `+0x2C` according to `+0x28` and a
resident profile predicate.

## Camera ownership switching

The resident battle object returned through `FUN_001EC2F0` exposes its default
camera at `+0x14`. Controller state `+0x30` governs which object has active byte
`+0x60`:

- state 0 reactivates the resident/default camera, clears the BTL cameras, and
  resets transition fields;
- state 1 deactivates the resident camera and activates the selected BTL slot;
  when the slot index changed, the new object is registered through the
  controller's `+0x60` owner;
- state `-1` follows a separate registration transition, then clears the same
  selection fields.

This proves explicit ownership handoff rather than two simultaneously active
camera outputs. The exact visual distinction between states 1 and `-1`
requires a runtime trace.

## Preset orientation and non-repetition

Several mode handlers select a short preset ID from table families using the
resident 64-bit LCG wrapper `FUN_0017B798`. They first choose an orientation
from the fighters' relative coordinates or state, reduce the random result
modulo that orientation's candidate count, and add one before indexing. The
chosen short is stored at controller `+0x0C`. If it equals `+0x10`, the previous
preset is cleared to `-1`, preventing the same exclusion value from surviving
the transition.

The four overlay-local tables are byte-exact. Each is laid out as two
signed-short candidate counts followed by interleaved candidates for the two
orientations:

| Live address | File offset | Signed-short contents |
| --- | --- | --- |
| `0x00895F40` | `0x1E2040` | `3, 3, 1, 2, 4, 5, 6, 7` |
| `0x00895F50` | `0x1E2050` | `2, 2, 10, 11, 12, 13, 0, 0` |
| `0x00895F60` | `0x1E2060` | `3, 3, 1, 2, 3, 4, 7, 8` |
| `0x00895F70` | `0x1E2070` | `3, 3, 0, 1, 2, 3, 4, 5` |

Pointer families at live `0x00895F80`, `0x00895FA0`, and `0x00895FC0`
select these or equivalent resident constant tables according to modes 1
through 4. This is why the header-skipped baseline appeared to index class-name
strings: those strings physically begin 0x40 bytes later.

### Mode handlers and preset records

Modes 1 through 3 select fixed-size `0xB0` records. Modes 4 through 6 use one
fixed record each:

| Mode | Handler | Record source |
| ---: | --- | --- |
| 1 | `FUN_006DD130` | `0x00891F40 + preset * 0xB0` |
| 2 | `FUN_006DD530` | `0x00892990 + preset * 0xB0` |
| 3 | `FUN_006DD9E0` | `0x008931D0 + preset * 0xB0` |
| 4 | `FUN_006DCDD0` | fixed `0x008936A0` |
| 5 | `FUN_006DCDD0` | fixed `0x00893750` |
| 6 | `FUN_006DCDD0` | fixed `0x00893800` |

`FUN_006D90A0` proves the relevant `0xB0` record contract:

| Record offset | Established use |
| --- | --- |
| `+0x00/+0x01` | Enable the two anchor-pointer channels stored at object `+0x190/+0x194`. |
| `+0x02/+0x03` | Choose supplied versus inline initial vectors for the two channels. |
| `+0x04/+0x05` | Enable initial vectors copied to object `+0x170/+0x180`. |
| `+0x06/+0x07` | Enable optional vectors at record `+0x70/+0x80`, copied to object `+0x1A0/+0x1B0`. |
| `+0x08` | Copied to object control byte `+0x161`. |
| `+0x0C` | Copied to object flags `+0x164`. |
| `+0x10/+0x14` | Select which supplied anchor pointer is used when the corresponding channel is enabled. |
| `+0x18..+0x2C` | Six words copied to object `+0x228..+0x23C`. |
| `+0x50/+0x60` | Inline initial homogeneous vectors. |
| `+0x70/+0x80` | Optional homogeneous vectors gated by bytes `+0x06/+0x07`. |
| `+0x90/+0xA0` | Homogeneous vectors always copied to object `+0x1E0/+0x1F0`. |

Modes 7 through 18 have distinct live handlers rather than falling through a
generic default:

| Mode | Live handler | File offset |
| ---: | --- | --- |
| 7 | `FUN_006DA940` | `0x26A40` |
| 8 | `FUN_006DAB10` | `0x26C10` |
| 9 | `FUN_006DB030` | `0x27130` |
| 10 | `FUN_006DB410` | `0x27510` |
| 11 | `FUN_006DAC50` | `0x26D50` |
| 12 | `FUN_006DAED0` | `0x26FD0` |
| 13 | `FUN_006DB600` | `0x27700` |
| 14 | `FUN_006DBAF0` | `0x27BF0` |
| 15 | `FUN_006DB220` | `0x27320` |
| 16 | `FUN_006DB870` | `0x27970` |
| 17 | `FUN_006DA060` | `0x26160` |
| 18 | `FUN_006DA6B0` | `0x267B0` |

The selector has deterministic corrections around stage edges. A boundary
probe obtains the current stage limits, tests the proposed side against them,
and, when still ambiguous, performs two resident segment queries from a point
75 units above the subject. It returns side code 1 or 2 when one direction is
blocked. Camera handlers then force candidate 1 on the corresponding side
instead of using the random modulo result. The behavior is a collision/boundary
avoidance rule; exact screen-left/screen-right labels depend on stage
orientation and are not assigned here.

The preserved Ghidra C misleadingly labels some preset tables as
`s_ccDummyCamera` or `s_ccCamera01`: the encoded operand is already a live
address, while the header-skipped display attaches that value to the string
located 0x40 later in the raw image. Translating the operand back to physical
file bytes reveals packed short tables, not reads from the type-name strings.

## Camera-object vectors and smoothing

The main camera-object family stores two homogeneous vectors at `+0x30` and
`+0x80`. Configuration can source each vector from a direct pointer, a supplied
vector, or an inline value. It also stores additive/transition vectors at
`+0x1A0`, `+0x1B0`, `+0x1C0`, `+0x1D0`, `+0x1E0`, `+0x1F0`, `+0x200`, and
`+0x210`, with duration/counter fields around `+0x228..+0x244`.

Two update paths smooth the first and second vectors independently. Their
interpolation coefficients are selected from configuration fields according
to fighter separation, relative height, and fighter state. Direct override
floats at object `+0x68` and `+0x6C` replace the computed first- and
second-vector coefficients when nonzero. Separate position smoothing limits
each per-update coordinate delta to `[-300, 300]`, then applies `1/8` to the
first vector and `1/4` to the second. Initialization bytes bypass smoothing and
copy the source vector directly.

Another established path derives a camera placement from both fighters, stage
configuration at object `+0x194`, an angular field at `+0x174`, and a distance
term. It constrains one output component to at most `2500.0` and another to a
configuration ceiling. The exact world-axis labels are withheld because the
decompiler's vector temporaries are not sufficient to distinguish camera eye,
look-at target, and coordinate convention without a runtime capture.

## Limits and next evidence

- The fixed eight-slot controller and its switching/mapping behavior are high
  confidence static results.
- Numeric modes and request codes remain numeric unless a resource or runtime
  transition identifies them.
- The corrected temporary import fills the physical gaps used here, but the
  maintained disassembly remains header-skipped; future work against it must
  still translate raw targets before extending the call graph.
- No runtime camera capture or patch was used.
