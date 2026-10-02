# Material draw modes and GS state

This document investigates native material draw-mode selection and draw-time GS
state in retail NA2 (`SLPS-25837`). It owns mode flags, all ALPHA, TEST and
ZBUF state composition and restoration, and the material-specific portions of
draw packets. Unless explicitly qualified, addresses are resident
`SLPS_258.37` EE addresses; see
[address conventions](../../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** Native draw-mode flag selection, GS state composition and
  restoration, and per-material packet contracts.
- **Exploration depth:** Static tracing of shared state composition/setters/reset,
  model/effect mode producers, ordinary and packed model packets, three
  optional-pass families and scoped restoration. Raw VU words establish four
  representative packed state kicks; eight retail model headers establish a
  bounded initial-selector sample. A direct model-selector
  call scan covers resident, BTL and ETC imports.
- **Confirmed coverage:** Blend-table words and exceptional selectors;
  independent TEST, depth-mask, primitive and sampling contributions; model
  versus per-material alpha/order selection; packed fixed-count state retention;
  optional-pass gates, separate blend owners and explicit FRAME reset/alpha
  clear packets; scoped owner-pointer and packed-color restoration.
- **Unresolved or untested:** Whole-roster mode distribution, indirect and
  other-overlay selector callers, every packed continuation's retained state,
  authored names/reachability of optional passes, and visible outcomes. A
  universal restoration of preceding GS state is not established.
- **Deliberate exclusions and overlap:** [Texture and material runtime](texture_material_runtime.md)
  owns resource binding and UV updates; [Model runtime](model_runtime.md) owns
  geometry conversion and skeletons; [Model VU programs](model_vu_programs.md)
  owns microprogram arithmetic; [Render submission](render_submission.md) owns
  allocation, ordering and DMA lifetime; [Shadow rendering](shadow_rendering.md)
  owns off-screen shadow targets and compositing.
- **Evidence limitations:** Static inspection establishes code and emitted
  values, not visual results or reachability of every mode. Ghidra's resident
  program is `r5900:LE:32:default`; embedded VU words were decoded separately
  from EE instructions. Important decompiler omissions were checked against
  instructions, and mapped mirrors were removed from the direct-call count.

## Evidence conventions

Overlay import addresses must be distinguished from their live load addresses.
Function names are Ghidra identities, not recovered retail source symbols.

## Shared draw context and state composition

**Observation, high confidence.** `FUN_0010C7A0`
(`0x0010C7A0..0x0010C9C0`) composes six 64-bit words and one 32-bit software
flag word. Its input is the shared draw context, not a render material or the
larger model working context. Instructions establish the following contract:

| Input field | Composition |
| --- | --- |
| halfword `+0x114` | Indexes eight-byte blend entries at `0x005B5940`; no local index-range check. |
| word `+0x118` | Upper 32 bits of FRAME; lower bits come from `FUN_001099C0` on the display owner. |
| byte `+0x11E` | Shifted left 3 into primitive attributes. |
| byte `+0x123` | Shifted left 7 into primitive attributes. |
| texture pointer `+0x128` | Nonzero adds `0x10`; `+0x11D==0` selects software flag `0x80`, otherwise adds primitive `0x100` and selects software flag `0x100`. |
| byte `+0x121` | Zero selects TEST `0x30000`; nonzero selects `0x50000`. |
| byte `+0x11F` | Nonzero adds `0x4000` and `((value-1)&1)<<15` to TEST. |
| byte `+0x122` | Zero sets ZBUF bit 32; nonzero leaves the display-derived base/format without that added mask. |

Primitive attributes start at `0x40`. Output offsets are `+0x00=0`,
`+0x08=blend`, `+0x10=TEST`, `+0x18=primitive attributes`, `+0x20=FRAME`,
`+0x28=ZBUF`, and `+0x30=software texture flags`. Instructions
`0x0010C7D4..0x0010C838`, `0x0010C85C..0x0010C8DC`, and
`0x0010C914..0x0010C994` corroborate shifts, selection and storage.

FRAME's low word is selected by display byte `+0x2AF`: nonzero uses display
`+0x310`, zero uses `+0x400`, both masked to 32 bits by `FUN_001099C0`.
ZBUF combines signed display halfword `+0x1A4` divided by 32 with truncation
toward zero, and `(display_byte_1AD&0xF)<<24`, before adding the requested
write mask. These display fields differ from the model producers' already
composed display ZBUF at `+0x1B0`.

`FUN_001830A0` calls this composer into its scratch `+0x140`, ORs the returned
software texture flags into the requested draw flags, and emits FOGCOL, ALPHA_1,
TEST_1, ZBUF_1 and FRAME_1. A textured packet additionally emits TEXFLUSH,
TEX0_1, TEX1_1, MIPTBP1_1 and CLAMP_1. It reserves `0x2A0` bytes without a
context texture or `0x2F0` with one; allocation failure clears both current
scratch globals rather than constructing a partial draw. Texture/CLUT resource
preparation is owned by the linked texture document.

GS register identities and field positions here are checked against
[PS2SDK's GS register definitions](https://github.com/ps2dev/ps2sdk/blob/master/common/include/gs_gp.h).
Thus the shared context fields select interpolation, texture-coordinate mode,
destination-alpha test, depth comparison and depth-write mask independently of
the blend-table index.

### Reset and texture sampling contributions

`FUN_0010D6A0` resets shared context blend index `+0x114`, FRAME mask `+0x118`,
texture pointer `+0x128`, and mode bytes `+0x11E/+0x11F/+0x121/+0x122/+0x123`
to zero irrespective of its reset mask. Mask bit `4` additionally clears
`+0x11D` and the 64-bit TEX1 contribution at `+0x130`, then calls
`FUN_0010D5C0(context,1,5)` and `FUN_0010D630(context,0xFF18,0)`.
Instructions `0x0010D7AC..0x0010D850` distinguish the conditional sampling reset
from the unconditional mode reset.

The first setter writes TEX1 MMAG bit 5 and MMIN bits 6..8, masking its inputs
to one and three bits. The second writes L bits 19..20 and the low twelve bits
of K at bits 32..43. Thus this reset contributes MMAG `1`, MMIN `5`, L `0`,
and K bits `0xF18`; it does not copy a texture's sampling word. Model-working
setup retains only `0x00000FFF001801C0` from that shared word: MMIN, L and K,
excluding MMAG. Ordinary and packed model texture packets OR this masked word
with texture `+0x10`. The shared draw producer `FUN_001830A0` instead emits
the texture's TEX1 word alone, while effect producer `FUN_00195A90` ORs the
full shared `+0x130` word with it. These are distinct composition contracts.

The small setter family establishes the CPU inputs independently of their
callers: `FUN_0010C9E0` stores the low halfword blend index;
`FUN_0010CA10` stores the low byte controlling depth writes;
`FUN_0010CA40` stores the low byte selecting depth comparison;
`FUN_0010CA70` stores the full FRAME mask;
`FUN_0010CAA0` stores the texture-coordinate selector; and
`FUN_0010CAD0` stores the interpolation byte. Their complete instruction bodies
are `0x0010C9E0..0x0010CAF4`. They store truncated values rather than imposing
a common boolean interface.

A bounded font caller, `FUN_00188140`, resets with mask zero, selects TEST
through owner byte `+0x70` bit 7, sets texture-coordinate selector to one,
binds texture owner `0x00618A70`, and takes blend index from owner halfword
`+0x52`. It repeats that setup after its embedded callback before continuing
text submission. It saves/restores the active draw/list environment and scratch
cursor, while the reset/setter sequence replaces shared draw state. Font
geometry and metrics belong to [Font renderer metrics](../../localization/font/renderer_metrics.md).

## Blend selection and model state producers

**Observation, high confidence.** Eleven aligned eight-byte values inspected at
`0x005B5940..0x005B5997` are:

| Index | Packed ALPHA value | `(A,B,C,D,FIX)` bit fields |
| --- | --- | --- |
| 0 | `0x44` | `(0,1,0,1,0)` |
| 1 | `0x48` | `(0,2,0,1,0)` |
| 2 | `0x42` | `(2,0,0,1,0)` |
| 3 | `0x09` | `(1,2,0,0,0)` |
| 4 | `0x54` | `(0,1,1,1,0)` |
| 5 | `0x58` | `(0,2,1,1,0)` |
| 6 | `0x52` | `(2,0,1,1,0)` |
| 7 | `0x64` | `(0,1,2,1,0)` |
| 8 | `0x68` | `(0,2,2,1,0)` |
| 9 | `0x62` | `(2,0,2,1,0)` |
| 10 | `0x00000080000000A4` | `(0,1,2,2,128)` |

This is an inspected interval, not an asserted declaration of the complete
table's extent. The following bytes contain addresses. No player-facing names
are assigned to these numeric selectors.

`FUN_001987A0` masks its selector to eight bits and copies the selected word to
runtime model `+0x30`. Selectors 0 and 4 call `FUN_001983C0(model,1,1)` and
clear model `+0x22` bit 0; every other selector calls that helper with final
argument zero and sets bit 0. Instructions `0x001987A4..0x00198824` establish
these exact two exceptional values. The selector has no local bounds check.

`FUN_001983C0` updates packed model TEST word `+0x24` by selector:

| Helper selector | Update |
| --- | --- |
| 0 | Clears bit 16, then ORs supplied value shifted left 16. |
| 1 | Clears low four bits and bits 12..13, then ORs `0x100B` for nonzero supplied value or `0x1001` for zero. |
| 2 | Clears bits 14..15, then ORs `0x4000` and supplied value shifted left 15. |

Only selector 1 normalizes its value to a boolean branch. These masks do not
establish a malformed-input interface contract. Model constructor
`FUN_001992A0` starts TEST at `0x50000`, clears `+0x22`, and calls the blend
selector with parsed model byte `+0x5D`; resulting ordinary defaults are
`0x5100B` for selectors 0/4 and `0x51001` otherwise. This also ties the
blend choice to a file-model header rather than the render material's texture
pointer. `FUN_00198730` separately packs caller-supplied ALPHA bit fields and
sets model `+0x22` bit 0 from its final argument, without changing TEST.

**Observation, high confidence.** Model-working-context setup
`FUN_001982B0` / `FUN_00198340` captures the active draw/list environment at
`+0x1FC`, its camera renderer at `+0x1F8`, shared context at `+0x1F4`, three
optional owners at `+0x248/+0x24C/+0x250`, and alpha at `+0x114`. It starts
primitive state `+0x120` at `0x2C`, with an antialias contribution in bit 7,
and masks shared context `+0x130` into
working `+0x140` for later TEX1 composition. `FUN_00198290` copies runtime
model flags into working `+0x20C`, mode byte into `+0x208`, and model scale
into `+0x210`. `FUN_001910E0` subsequently copies model ALPHA `+0x30` to
working `+0x130` and model TEST `+0x24` to working `+0x138`. Identical offset
numbers in these distinct allocations must not be treated as identical fields.

### Bounded retail model-header sample

**Observation, high confidence.** Parser `FUN_001B0C40` reads the model
header's `+0x14` halfword, which follows the geometry flags and part count,
into `s8` and stores `s8&3` at parsed model `+0x5D`
(`0x001B0CC4..0x001B0CD4`, `0x001B1050`, `0x001B1080`); those low two bits
select the initial model blend index. The higher bits have separate
conversion and draw-dispatch roles owned by the model/VU documents. All eight
sampled retail model headers (the six body models, the `2NRTBOD1.CCS` weapon
model and `MDL_1nrt00t0 eye1` at decompressed offset `0x34A0` of
`PL/1NRTBOD1.CCS`, whose `0x0800` header names record `0x72` and has
`+0x14` halfword `0x0000`; see
[Model VU programs](model_vu_programs.md#representative-retail-body-payloads))
give initial selector 0 despite differing higher bits. They do not establish an
all-resource distribution or later runtime selector values.

## Ordinary per-material packets

**Observation, high confidence.** `FUN_001910E0` computes each ordinary part's
working alpha as material `+0x10` times working-context `+0x114`, stores it at
`+0x118`, and ordinarily skips values below `1/128`. In the branch with no
optional passes it groups parts into a direct chain and an ordered chain.
A part goes to the ordered group if alpha is below `127/128`, model mode byte
bit 0 is set, or its texture flags contain `8`; otherwise it sets working alpha
to exactly `1.0` and uses the direct group. Instructions
`0x00191BB4..0x00191BE0` and `0x00191CA0..0x00191D20` corroborate the float
thresholds and independent flag decisions. The optional-pass branch uses one
chain and marks the whole chain for ordering when any included part requires
it. One owner-selected pass can bypass the per-part alpha skip.

`FUN_00192740` allocates a `0x100`-byte per-part packet. It emits
`0x6C0C4020`, an A+D packet header, eleven register/value pairs, then VU parameter
and entrypoint words. Its established register slots relative to the allocation
are:

| Value / register offset | State |
| --- | --- |
| `+0x20 / +0x28` | Zero / TEXFLUSH (`0x3F`). |
| `+0x30 / +0x38` | Texture CLAMP / CLAMP_1; NOP register when texture absent. |
| `+0x40 / +0x48` | Texture with separately cached CLUT / TEX0_1; NOP when absent. |
| `+0x50 / +0x58` | Texture mip base/width word / MIPTBP1_1; NOP when absent. |
| `+0x60 / +0x68` | Working `+0x140` OR texture `+0x10` / TEX1_1; NOP when absent. |
| `+0x70 / +0x78` | Working `+0x130` / ALPHA_1. |
| `+0x80 / +0x88` | Composed TEST / TEST_1. |
| `+0x90 / +0x98` | Display-derived depth state / ZBUF_1. |
| `+0xA0 / +0xA8` | Working fog value shifted left 56 / FOG (`0x0A`). |
| `+0xB0 / +0xB8` | Working fog color / FOGCOL (`0x3D`). |
| `+0xC0 / +0xC8` | Working primitive attributes / PRIM (`0x00`). |

Model flag `0x400` suppresses the texture pointer in this producer. With a
texture it ORs primitive state with `0x50`; without one it adds bit `0x40` only
when alpha differs from exactly `1.0`. When model mode bit 0 is clear, it adds
`int(texture_byte_3A * working_alpha)<<4` to TEST by OR, not by replacing the
existing reference field. No local clamp to eight bits is visible.

If composed TEST bit 16 is clear, the producer clears bits 16..18, ORs
`0x30000`, and sets ZBUF bit 32. Otherwise it retains TEST and the display's
depth state. This turns the disabled-depth request into an always-pass depth
test with writes masked. Instructions and bytes
`0x00192938..0x001929B8` corroborate the exact branch and masks. Texture
binding/UV rewrites remain in the texture owner; descriptor and VU entrypoint
selection remain in [Model VU programs](model_vu_programs.md#initial-upload-boundaries).

## Packed material packets and selection asymmetry

**Observation, high confidence.** `FUN_0018FFB0` emits one ALPHA/TEST/ZBUF/fog
state block for its model chain, using the **first part's material** to compute
working alpha and texture-derived TEST reference. It does not repeat that
calculation for every part. Its final direct-versus-ordered decision likewise
uses this alpha, the model mode byte and the first material's texture flags.
The ordinary path above performs the corresponding decisions per material.

Each packed part still emits its own material-offset VU parameters and chooses
one of two state packet lengths. A material pointer different from the previous
part's pointer, with a nonzero texture, emits `0x6C064026` and six pairs:
TEXFLUSH, TEX0_1, TEX1_1, MIPTBP1_1, CLAMP_1 and PRIM. The other branch emits
`0x6C014026` and one PRIM pair, with working primitive attributes OR `0x40`.
The six-pair branch ORs PRIM with `0x50`. Instructions
`0x00190930..0x001909E8` establish both the pointer comparison and these different
primitive values; `0x00190A48` records the current material as the previous one.

### Fixed GIF count and retained texture state

The initial upload `0x6C0C4020` installs one GIF header with NLOOP eleven at
VU slot `0x20`, followed by ALPHA, TEST, ZBUF, FOG and FOGCOL at
`0x21..0x25` and six NOP-register pairs at `0x26..0x2B`
(`0x0019070C..0x0019072C`, `0x00190824..0x00190880`). Per-part uploads replace
those last six slots directly; they do not contain a second GIF header.
A long upload writes TEXFLUSH at `0x26` through PRIM at `0x2B`. A short
upload replaces **only `0x26`** with its PRIM pair, retaining `0x27..0x2B`.
The header's eleven-pair count is unchanged.

Raw VU pairs in four representative packed bodies establish a full state
packet kick, with `IADDIU vi2,vi0,0x20` followed by `XGKICK vi2`:

| Body stream | Address of address setup | Address of state kick |
| --- | --- | --- |
| `0x003C86C0` | `0x003C8760` | `0x003C8780` |
| `0x003C9580` | `0x003C9620` | `0x003C9630` |
| `0x003CA210` | `0x003CA2B0` | `0x003CA2D0` |
| `0x003CADD0` | `0x003CAE68` | `0x003CAE78` |

Lower words are `0x10020020` and `0x800016FC`. Decoding uses PCSX2
`DebugTools/DisVUmicro.h`, `DisVUops.h` and operand definitions in `VUops.cpp`,
as in the linked VU owner. No state-slot stores occur between address setup
and these kicks.

**Inference, bounded to this packet contract:** after a long textured upload,
a following short upload retains the later textured PRIM at `0x2B`. That
later write follows the short branch's PRIM at `0x26` when the eleven-pair
packet is consumed. Reading only the short branch's OR `0x40` would miss this
state dependency. A first short upload instead has the initialized NOPs in
the remaining slots. This establishes retained register-write order, not a
visible result, every continuation's state history, or safety of arbitrary
textured/untextured material sequences.

Geometry REF tags, matrix uploads and UV interpretation are owned by the linked
model and VU documents. This document does not repeat their descriptor census
or infer character-specific descriptor selection.

## Optional material pass contracts

**Observation, high confidence.** The optional owners captured by model setup
are independent of the current render material. `FUN_001910E0` builds a local
pass mask before choosing ordinary or packed drawing:

| Local pass bit | Established gate | Packet family |
| --- | --- | --- |
| `1` | Model flag `0x80`, nonzero owner `+0x248`, owner halfword `+0x1C != 0`. | Ordinary `FUN_001C3DA0`; packed `FUN_001C3750` / `FUN_001C3A20`. |
| `2` | Model flags `&0x805 != 0` and `&0x8000 != 0`, owner `+0x24C` halfword `+0x1C != 0`, and texture `+0x10 != 0`. | Ordinary `FUN_0018F900`; packed `FUN_0018F610`. |
| `4` | Model flag `0x100`, nonzero owner `+0x250`, owner halfword `+0x1C != 0`. | Context-two rectangle and clear below. |

Instructions `0x00191350..0x001913A0` and `0x001914F4..0x00191554` establish
these gates. The dispatcher first rejects whole-model alpha below `1/128`;
local pass bit 1 only bypasses the later per-part alpha skip. None of these
numeric gates establishes an authored effect's player-facing name.

Two packet producers consume working owner `+0x24C` and a supplied descriptor
whose texture/CLUT pointers are
at `+0x10/+0x14`, blend selector at byte `+0x1E`, and TEST selector at byte
`+0x1F`:

| Producer | VU state upload | ALPHA | TEST | Depth writes |
| --- | --- | --- | --- | --- |
| `FUN_0018F610`, `0x120` bytes | `0x6C0D4030` | Blend table indexed by descriptor `+0x1E`. | `0x50000` when `+0x1F==0`, otherwise `0x53001`. | Display ZBUF without added mask. |
| `FUN_0018F900`, `0x210` bytes, first block | `0x6C0D4020` | Current model ALPHA. | Ordinary material reference/depth composition described above. | Ordinary material rule. |
| `FUN_0018F900`, second block | `0x6C0D4030` | Descriptor blend-table entry. | `0x51001` when `+0x1F==0`, otherwise `0x53001`. | ZBUF bit 32 set. |

Both descriptor blocks OR the texture's TEX1 word with working `+0x140`, use
PRIM's low three working bits OR `0x50`, and build RGBAQ from owner `+0x20`
and `int(owner_float_28*128)<<24`, with Q `1.0`. Model flag `0x20000`
additionally multiplies that alpha contribution by working `+0x118`.
`FUN_0018F610` can emit five texture-register NOPs when the descriptor texture
is absent; `FUN_0018F900`'s second block dereferences that texture directly.
The differing zero-selector TEST defaults and depth masks are visible in
these producers and must not be inferred from a shared pass label.

### Extra model-owned blend state and FRAME restoration

`FUN_001C3DA0` emits an additional `0x100`-byte packet for a model pass.
Its eight-pair state upload is `0x6C094040`. ALPHA comes from runtime model
`+0x40`'s first 64-bit word, or blend entry zero when that owner is absent.
`FUN_001C44F0` writes this word from the blend table; constructor
`FUN_001992A0` supplies parsed model byte `+0x53 & 3` when creating the owner.
This selects a separate pass's blend state from the ordinary model `+0x30`.
The constructor makes the `0x18`-byte owner when model flags `&0x84 != 0`
and no existing owner was supplied. Its owned-instance initialization copies
parsed model float `+0x54` to owner `+0x08`, parsed `+0x50` low 24 color bits
to owner `+0x0C`, and the separate blend selector to owner `+0x00`
(`0x00199444..0x001994CC`).

The producer uses TEST `(working_TEST&0xC000)|0x50000`, retaining destination-
alpha bits but replacing alpha/depth-test fields, and display ZBUF without an
added depth-write mask. It emits the selected display FRAME low 32 bits with
mask `0xFF000000` in its high 32 bits, protecting alpha while permitting color
writes. PRIM is `(working_PRIM&7)|0x40`. Instructions
`0x001C3E44..0x001C3E60`, `0x001C3EB8..0x001C3EF4` and
`0x001C3F30..0x001C3FCC` corroborate owner selection and state composition.

A separate two-qword DMA packet at allocation `+0xD0` contains one FRAME_1
write: the same selected display word's low 32 bits, with upper mask zero
(`0x001C40E0..0x001C4130`). The function links its state packet ahead of the
supplied part chain and this FRAME packet after the supplied geometry tail.
This restores a known display FRAME configuration; it does not capture and
restore an arbitrary preceding FRAME mask. Other state written by this pass
has no corresponding restoration packet inside this function.

The packed counterpart `FUN_001C3A20` allocates `0x110` bytes, composes the
same eight GS state pairs, and appends a three-qword FRAME-reset sequence at
allocation `+0xE0`. `FUN_001C3750` puts a fourteen-qword REF to this state block
before REF tags for every packed part, then a three-qword REF to `+0xE0`.
Thus the packed extra pass brackets all its parts with the same known FRAME
mask/reset contract. VU geometry operations and direction offsets belong to
the linked VU document.

Both extra-pass producers obtain color, alpha and width from `FUN_001C4290`.
A supplied color of `0x80000000` selects model-owner color or zero when absent.
Owner `+0x08` scales width; owner `+0x10` bit 0 controls the width/alpha
adjustment when projected width falls below the supplied threshold. Alpha
starts from descriptor float `+0x18 * 128`, and model flag `0x40000` multiplies
it by working material alpha. The ordinary producer normalizes width by
`model_scale*64` unless flag `0x1000` is set; the packed producer uploads width
and width/64 separately. These parameter differences do not change their
shared ALPHA/TEST/FRAME composition.

### Context-two composition and alpha clearing

`FUN_0018E9F0` emits a `0x140`-byte textured rectangle packet using GS context
two. It selects the current display FRAME_2 low word, masks depth writes,
centers XYOFFSET_2 from display dimensions, copies camera SCISSOR_2, clears
FBA_2, and emits the descriptor texture's TEX0_2/TEX1_2/CLAMP_2/MIPTBP1_2.
TEST_2 is `0x71001`; ALPHA_2 comes from the separate table at `0x005BEEA0`
indexed by descriptor byte `+0x2C`. Missing texture or computed alpha below
one causes an early return before packet allocation.
Four aligned entries inspected at `0x005BEEA0..0x005BEEBF` are `0x54`,
`0x58`, `0x52`, `0x52`; the following address starts the VU descriptor table.
The draw reads an eight-bit index without a local bounds check, so this
interval does not establish an accepted public selector range.

`FUN_0018F160` emits a `0xC0`-byte context-two clear/setup packet. Its FRAME_2
uses display color base `+0x19C`, display width, and upper mask `0x00FFFFFF`,
protecting RGB and permitting alpha writes. It sets XYOFFSET_2 to zero,
SCISSOR_2 to raw `0x0FFF00000FFF0000`, FBA_2 and TEST_2 to zero, ALPHA_2 to
blend entry zero, and RGBAQ to zero before emitting rectangle endpoints.
The SCISSOR fields are eleven bits, so their effective endpoints are `0..2047`;
the raw twelfth bit in each upper endpoint is padding, as corroborated by
PCSX2 `GS/GSRegs.h`.
These are constructed defaults rather than saved GS words. The ordinary
producer places `FUN_0018E9F0` before its optional chain and the clear packet
after it; the packed producer places the clear before its chain and the
textured rectangle after it. Neither sequence proves restoration of all
preceding context-two state.

## Scoped CPU state and restoration boundaries

**Observation, high confidence.** `FUN_0035C110` saves optional-owner globals
`0x00602A60` and `0x00602C08`. Nonzero descriptor pointers at its asset owner
`+0x100/+0xFC` temporarily replace these globals with descriptor `+0x10/+0x08`.
It calls `FUN_003556C0`, then restores both saved pointers
(`0x0035C158..0x0035C1A0`). Model-working setup snapshots these globals into
`+0x24C/+0x248`; packets therefore retain the selected pass owners while the
global draw environment can be restored for subsequent producers.

Scene dispatcher `FUN_001BB790` temporarily substitutes a camera renderer
([renderer coordinates](renderer_coordinates.md#refresh-and-binding-order))
and, when scene descriptor `+0x20` differs from `0x80000000`, overrides shared
lighting color. Color save calls
`FUN_0010D310`, which converts shared floats `+0x70/+0x74/+0x78` times 255
to integers and packs their contributions. Restoration calls `FUN_0010D430`
on that packed color, converting back through `FUN_0019F380` and writing the
three shared floats. This is restoration through a packed color representation,
not an exact saved-float snapshot. The dispatcher also sets shared `+0xC8`
to scene `+0x100` for traversal and clears it afterwards, without saving a
previous pointer.

`FUN_00190F40` obtains a model working block, invokes child modifier callbacks,
submits model/shadow work, and restores the scratch cursor. The scratch and
coordinate lifecycle is owned by the linked renderer document. It does not
save model ALPHA/TEST fields or reconstruct earlier GS state. Within the
inspected family, persistent model setters, scoped CPU-owner restoration, and
explicit register-setting packets are separate mechanisms; a general GS
push/pop contract has not been established.

## Mode propagation and bounded direct callers

`FUN_00194BA0` iterates a scene composition and forwards one blend selector to
each `0x0100` child's primary runtime model and each `0x0E00` effect descriptor.
Effect selector `FUN_00196260` has a different exceptional set: only selector
zero clears effect mode bit 0 and chooses `0x100B` TEST low state; every nonzero
selector sets the bit and chooses `0x1001`. Model selector 4's exceptional
handling must therefore not be assumed for effects. Full effect frame/alpha
behavior is owned by [Texture and material runtime](texture_material_runtime.md#effect-texture-frames).

The effect's TEST reference contribution has different arithmetic from the
model's float-derived reference: when effect mode bit 0 is clear,
`FUN_00195A90` ORs `((texture_byte_3A*integer_alpha+64)>>7)<<4` into descriptor
TEST, using its already bounded integer draw alpha. Its subsequent TEST-bit-16
branch uses the same `0xFFF8FFFF` clearing mask, `0x30000` replacement and
ZBUF write-mask bit as the ordinary model producer
(`0x00195F04..0x00195FBC`). Numeric blend selection alone therefore does not
determine the emitted TEST reference or depth-write behavior.

`FUN_00196260` stores the selected `0x005B5940` blend-table word in effect
draw descriptor `+0x48` and configures TEST state through `FUN_001962F0`;
`FUN_00195A90` emits ALPHA from `+0x48` and TEST from `+0x50`. Its
opaque/list-order decision uses integer-alpha threshold `0x80`, draw-mode bit
`+0x58 & 1` and texture flag `+0x30 & 8`. The frame-derived integer alpha
itself is owned by
[Texture and material runtime](texture_material_runtime.md#draw-time-resource-and-state-consumers).

The wrapper `FUN_001BC050` replaces `a0` with scene-child `+0x94` and forwards
the caller's untouched `a1` to `FUN_001987A0` when that model exists
(`0x001BC058..0x001BC068`). Its decompiler omits the forwarded selector. The
analogous `FUN_00196560` forwards untouched `a1/a2` to `FUN_001983C0`
(`0x00196568..0x00196578`).

A direct-call byte search for JAL `E8 61 06 0C` found seven resident call
sites after removing mapped memory mirrors, matching the seven direct xrefs,
and none in BTL or ETC. The seven sites are constructor `0x0019934C`, composition `0x00194C14`, wrapper
`0x001BC064`, generic owner `0x00355FFC`, and three sites in
`FUN_003592C0` (`0x003594DC`, `0x00359538`, `0x003595CC`). The latter chooses
0 or 10 from a table-driven owner state while updating renderer priority and
scene alpha. That establishes a selector-10 code path, not a player-facing name
or a particular character's use. Indirect calls and other overlays are not
covered by this direct-call scan.
