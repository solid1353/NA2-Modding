# Font screen layouts

## 2026-07-24 weight and spacing refinement

### Command Chart and Practice title boxes

The Command Chart and Practice command-title rows share the same boxed-fit
logic but not the same container geometry. NUN5 wrapper telemetry at caller
`0x003882D0` establishes these separate records:

- Command Chart titles: X `28`, Y `17/117/217`, width `288`, height `20`;
- Practice titles: X `32`, Y `14/114/214`, width `352`, height `20`;
- Practice explanations remain a separate caller family at X `40`, Y
  `42/142/242`, width `364`, height `48`, vertical alignment `1`.

A guarded task-owned NUN5 state probe recorded `FUN_0018ca40`'s live horizontal
denominators before scaling. `Susanoo's Blade` is `142`, `Reverse Halo` is
`115`, and `Fire Style: Phoenix Flower Jutsu @Petal Shower@` is `440`.
Those values exactly equal the sums from the 95-entry packed metric table.
This runtime result rejects both the legacy NA2 results (`135`, `110`, `417`)
and the temporary constant-eight interpretation. The resident helper now
validates plain ASCII once, consumes the shared table, applies the caller's
`box_width / measured_width` factor only on overflow, and restores scale after
the draw.

NA2 reaches the shared UI wrapper at return address `0x00382454`; exact outer
return-address guards distinguish Command Chart `0x0087A930`, Practice title
`0x00878AA0`, and the pre-existing character-body caller. The final current
origins use a common `-0.8` logical-unit visible-ink compensation:
Command Chart X `27.2` with Y offset `-3.8`, and Practice X `31.2` with Y
offset `-6.8`. The width constants remain the exact NUN5 `288` and `352`.

Matched 640x480 captures on worker CRC `D64F4D9F` show:

| Title row | NUN5 ink bounds | Current ink bounds |
| --- | --- | --- |
| Command Chart: `Susanoo's Blade` | `(141,87)-(314,100)` | `(141,87)-(314,99)` |
| Command Chart: `Reverse Halo` | `(141,212)-(279,225)` | `(140,212)-(279,224)` |
| Command Chart: long Petal Shower title | `(141,337)-(488,353)` | `(141,337)-(496,353)` |
| Practice: `Shadowbur Extra Hit` | `(96,83)-(326,96)` | `(96,83)-(325,96)` |
| Practice: `Guard` | `(96,208)-(153,221)` | `(96,208)-(153,221)` |
| Practice: `Linked Attack` | `(96,333)-(245,346)` | `(96,333)-(245,346)` |

The long current title is complete and unclipped. Its eight-pixel right-edge
difference is not a fit error: official NUN5 bytes `0x40` render quote-shaped
glyphs, while the accepted NA2 atlas deliberately preserves literal at-signs.
The occasional one-pixel short-title height or leading-bearing difference is
likewise accepted raster/metric residue, not a container offset. The NUN5
reference screenshot hashes are
`E602195AF1CC4EFD122735DD7F7D08A15ECCC38B88DB1FCF85C5CD966E70E9DE`
and
`983AC7C636C3F5CF47492E87795899592C2B4B50EFA1EE556AC4095052F4CF2E`;
the matched current hashes are
`FE37ABB125396BA6786230A6B580DE4C59EEF20527A4FD5B49B52D98BCC15598`
and
`D10643D42B96D0135C4E25F636EB517042C6ABE28822BEB56DFFD0AE5D084C8F`.
Confidence is **high** for the denominators, caller guards, fit thresholds,
origins, and separation from the unresolved Practice explanation family.

The stage-by-stage v2 reimplementation no longer depends on those retained
outer-return guards. Bounded BTL inspection identifies the actual title-only
draw calls directly. The supplied states independently confirm that the live
MWo3 image begins at `0x006B3F00`, so these file offsets map without the
`-0x40` Ghidra-header adjustment:

- Practice runtime `0x00878A98`, BTL file `0x1C4B98`;
- Command Chart runtime `0x0087A928`, BTL file `0x1C6A28`.

Both sites contain guarded bytes `C4080E0C00000000`, a `jal 0x00382310`
followed by its NOP delay slot. The Practice call occurs before its separate
explanation loop; the Command Chart call precedes two independently guarded
auxiliary-string draws. The v2 implementation therefore redirects only those
two calls to explicit mode entrypoints. Each entrypoint tail-calls one shared
title adapter, which selects the proven geometry above, creates one
single-line shrink-only v2 session, and invokes native `0x00382310` through a
common callback. No Practice explanation or auxiliary Command Chart call is
selected.

The generated v2 resident asset with this adapter is 2,020 bytes and has
SHA-256
`9561B62AAD1E0139B920AED058B2ECB066A9EB7D64092992ECAD60BC1581C8F6`.
Static tests decode both linked BTL hooks, both mode entrypoints, every title
constant, the callback ABI, and the shared-adapter relocations.

The first converted-state capture used the ELF/Ghidra mapping base
`0x006B3EC0` as though it were the live MWo3 base. It therefore wrote each BTL
edit `0x40` bytes too early and produced the hybrid Command word `0x4423D147`
instead of the linked `jal` word `0x0C23D147`. Exact clean context around both
supplied call sites proved that the complete live BTL image begins at
`0x006B3F00`. Corrected guarded states contain `jal 0x008F451C` at
`0x0087A928` and `jal 0x008F48B0` at `0x00878A98`; the failed capture was a
state-conversion error, not a rejected renderer hypothesis.

Hidden task-owned PCSX2 captures on boot CRC `A8A3C4FF` then covered preserved
Command Chart slot 3, all six Practice command slots 2-7, and the accepted
Controls regression. The worker ISO SHA-256 is
`0396D02B559EFC964B05520CC539F074432A57C3796BC1CA3063C3533E32FF1F`;
its 5,488-byte resident payload ends at `0x008F5270` and has SHA-256
`4BD20BE93EA0D0A217A790774C4813863F1F8303FA49117889A6D59D664D097D`.
The corrected Command capture reproduces the prior matched title bounds and
has SHA-256
`FE37ABB125396BA6786230A6B580DE4C59EEF20527A4FD5B49B52D98BCC15598`.
Every Practice page retains the NUN5 title origins while its later explanation
rows remain intentionally unchanged for their separate wrapping family.
Confidence is **high** for the direct hooks, shared adapter, shrink-only
behavior, distinct geometries, state restoration, and separation between
titles and explanations. The user explicitly accepted the Command Chart result
on 2026-07-27. The Practice title result remains agent-validated and awaiting
user acceptance.


### Command Chart relationship rows

Refreshed paired ss1 and ss2 isolate the auxiliary relationship text drawn
below each accepted Command Chart title. The preserved NA2 BTL export identifies
the owning row function as `FUN_0087A700`. For each 0x34-byte row record it
draws the title, reads optional text selectors from record bytes `+4` and `+5`,
and renders them independently through `SUB_00382310` at Ghidra addresses
`0x0087A930` and `0x0087A97C`. With the confirmed live BTL base
`0x006B3F00`, those are runtime `0x0087A970` / file `0x1C6A70` and runtime
`0x0087A9BC` / file `0x1C6ABC`. The separate calls cannot wrap the combined
English relationship and cause refreshed ss1 to overflow horizontally.

The structural NUN5 homolog is `FUN_00896E70`. Its branch at
`LAB_008977BC` resolves selector `+4` through `SUB_003D16C0`, copies the
result into a 0x100-byte stack buffer, resolves and appends selector `+5` when
present, then draws the complete buffer once through `SUB_00393ED0`. The
request uses width `308`, height `32`, line limit `2`, and style `9`. Its
native row formula also separates relationship and icon placement: after the
title it draws the combined relationship from `fVar17 + 4` and the icons from
`fVar17 + 44`, while NA2 advances its shared row coordinate by `30` before
the relationship and then draws icons only `20` units below it. This explains
both refreshed cases: ss1 needs one jointly wrapped two-line block, while all
three ss2 single-line rows and their icons share the same repeatable vertical
correction.

The bounded NA2 port therefore hooks only the first exact auxiliary call through
a 36-byte native-register shim, passes the row record and native Y to generated
C, and suppresses only the second exact draw. The C entry resolves both strings
from NA2's live table at `0x008BD1D0`, combines them without modifying canonical
mapping bytes, and wraps at spaces through the shared native-metric v2 helper.
The measured NA2-side request uses X `43.2`, native Y minus `11.5`, width `226`,
height `32`, line advance `30`, glyph height `14`, and a further `-8` Y bias
only when the wrapped result has one line. The native icon loop remains intact.
A first candidate changed its one shared `+20` float constant at BTL file
`0x1C6ACC` to `+16`; this matched rows with relationship text but was wrong for
rows without it. The reason is visible in both preserved homologs. NA2 leaves
its row coordinate at the title base for a plain row, or advances it by `30`
before drawing a relationship, then adds one shared icon offset. NUN5 starts
from a title base six units above NA2's, adds `8` only for a relationship row,
and then adds `44` for icons. Expressed at NA2's unchanged hook coordinate, the
NUN5 targets are therefore `+16` after a relationship and `+38` after a plain
title. The corrected port replaces only the two-instruction `+20` load at
runtime `0x0087A9CC` / BTL file `0x1C6ACC` with a native-register shim and
generated-C selector using record byte `+4`; both icon branches and the
existing additional `+4` for tokens 4 and above remain native.

The first relationship candidate also allocated
`FONT_V2_FLAG_SCALE_LINE_ADVANCE` at `0x10`, which was already owned by
`FONT_V2_FLAG_PREMEASURED`. Every premeasured caller therefore also scaled its
line advance, causing regressions outside Command Chart. The corrected flag is
`0x20`; the Command relationship request becomes `0x3D` instead of `0x1D`,
and the shared prepare check tests `0x20` independently. The user confirmed
that this isolation restores the previously working modal families. This flag
correction does not alter glyph metrics, fitting, wrapping, or any caller box.

Hidden task-owned runtime captures on Current CRC `092FEF8A` used the refreshed
ss1 and ss2 states and the production C hot-reload path for the first
relationship candidate. At 640x480, ss1's
relationship ink is `160,231-396,262` versus NUN5
`162,232-397,262`, and its first relationship icon is
`196,278-212,294` versus `196,278-212,295`. Across ss2, all three blue rows
remain within one raster row of NUN5 and the icon bounds match at Y
`153-170`, `278-294/295`, and `403-420`. A later isolated ss1 capture proves
that the row-aware `+38` plain-row path moves the final input sequence down by
the missing 22 local units and aligns it with the retained NUN5 reference.
Complete post-change ss1 and ss2 captures then exercised the relationship
adapter and row-aware icon selector together: ss1 retains the jointly wrapped
two-line relationship and aligns both relationship and plain input rows, while
all three ss2 relationships remain on one line without overflow and all three
input rows retain their NUN5 Y geometry. Titles, icon records, horizontal icon
spacing, and all other BTL callers remain native.

Those supplied `092FEF8A` states restore an older resident payload than the
later on-disc Current build. Offline `eeMemory.bin` signature recovery proves
that `v2_adapter_call` remains stable at `0x008F4130`, but
`practice_append` is at `0x008F4D68` rather than Current `0x008F4F30`,
`title_callback` is at `0x008F5500` rather than `0x008F56E8`, and the
native-measure callback is at `0x008F4320` rather than `0x008F44C0`.
The earlier `wrap_native = 0x008F5510` identification was wrong: exact
disassembly of the compatible ISO's `228.BIN` places that address inside
`font_v2_prepare`. Calling it as a wrapper trapped the injected Movie-list
candidate, while a clean ss8 reload without injection rendered normally.
The same payload proves `font_v2_wrap_native` spans
`[0x008F5930,0x008F5B38)` (520 bytes) and makes its three measurement calls to
`font_v2_native_measure` at `0x008F4F38`. A corrected wrap-only probe and the
complete ss8 candidate both execute normally with `0x008F5930`. This is a
savestate-specific development constraint, not a production payload
requirement.

Confidence is **high** for the homolog, selectors, call sites, buffer
composition, shared one-/two-line geometry, conditional icon offsets, flag
ownership, and integrated ss1/ss2 runtime behavior. The patch remains
`approved_for_test` pending explicit user acceptance of the composed pair.


### Pause Controls list v2 callers

The retained disabled shared UI helper established the intended Pause Controls
behavior: a shrink-only 216-unit box and a four-unit upward Y correction.
Bounded NA2 BTL inspection isolates two adjacent row calls using the confirmed
live mapping `0x006B3F00 + file offset`:

- the normal row at runtime `0x0087D6D8`, BTL file `0x1C97D8`, guarded by
  `1C090E0C00000000` (`jal 0x00382470` plus NOP);
- the selected row at runtime `0x0087D694`, BTL file `0x1C9794`, guarded by
  `E8090E0C00000000` (`jal 0x003827A0` plus NOP).

NA2 passes normal coordinates in `f12/f13`, but selected coordinates as integer
`a1/a2`, the text in `a3`, and red style `0xFF0000B4` in `t0`. The NUN5
homolog keeps the same row origin for both paths; selection changes style, not
position. The earlier accepted modal-alignment analysis independently proved
that NA2's selected shadow helper needs two local X units of compensation.

The v2 implementation hooks both BTL calls directly rather than re-enabling
the retained boot-ELF return-address multiplexer. Both adapters use
`caller_y - 4`, a 216-by-20 single-line left-aligned box, and the same
shrink-only fitting. The selected adapter also uses `caller_x + 2`, preserves
the native color, converts the prepared float origin back to the helper's
integer ABI, and tail-calls `0x003827A0`. The unchanged normal adapter
tail-calls `0x00382470`. The shared v2 core owns measurement, horizontal scale,
tracking, active-session publication, and restoration.
The accepted width table measures the two overflowing visible rows as
`Back to Game Mode Screen = 245` and `Back to Character Select = 231`, giving
scales `216/245` and `216/231`. The other four visible rows measure
`77`, `119`, `140`, and `124`, so they remain at scale `1`.

Deterministic generation produces separate normal and selected adapter/callback
fragments. Static tests verify both exact hook guards and targets, both callback
ABIs, the shared four-unit Y correction, selected two-unit X compensation,
216-unit width, 20-unit height/line height, preserved red style, and dependency
only on the accepted v2 core. At this accepted boundary no ss4
confirmation-body or Yes/No site was selected. Confidence is **high** for
caller isolation and the reconstructed contract. The user verified both the
normal ss2 state and corrected selected ss3 state on 2026-07-27; selection no
longer overflows or moves the row.


### Battle quit-confirmation ss4 callers

Clean NA2 BTL bytes and the task-owned ss4 state identify two distinct modal
draw calls. The clean BTL file uses `0x006B3F00 + file offset`:

- file `0x1C4048` / runtime `0x00877F48` is
  `800D0E0C00000000`, the native `jal 0x00383600` Yes/No list
  plus NOP;
- file `0x1C407C` / clean runtime `0x00877F7C` is
  `6C090E0C00000000`, the native `jal 0x003825B0` body draw
  plus NOP.

Earlier retained working notes named BTL `0x1C4008`/`0x1C403C` and ELF
`0x283814`/`0x283960`; direct clean-file guards prove those locations are one
displaced block early. Inside `0x00383600`, the exact selected and unselected
calls are instead ELF files `0x283914` and `0x283A60`, guarded by
`54E40D0C00000000` and `88E60D0C00000000`.

The modal object owns its Yes/No widget at `+0x110` and body widget at
`+0x114`. The list descriptor starts at X/Y `50/24`, uses row extra `12`, and
therefore draws its second row at Y `56`. Retained NUN5 measurements map Yes
to `(64.5,31.5)` and No to `(68.5,49)`. Because either row may be selected,
the smallest exact design scopes the complete list call, then adapts the two
shared inner calls only while that scope is active. The active word is saved
and restored, so nested drawing remains safe; both inner adapters are native
tail calls for every other screen.

The body helper builds its native record at X/Y `48/20`. NUN5 evidence retains
Y `12`; the accepted width table measures the Free Battle first line through
`and` as `420`, while adding `return` reaches `483`. A 420-unit, two-line
greedy wrapper therefore selects the observed break without storing an
authored newline in any canonical mapping. The adapter copies at most 255 source bytes to its
own stack, inserts newline bytes only into that draw-time copy, publishes the
v2 session around the native UI draw, and then discards the copy. Confidence
is **high** for offsets, guards, ABIs, isolation, and mapping neutrality.

Fresh post-change pairs cover all four Battle/Practice and Game
Mode/Character Select combinations. Every Current body starts at screenshot
X `101`, while every NUN5 body starts at X `72`; both first lines start at Y
`381`. Because the renderer uses the adapter's X directly inside the same
modal origin, the shared correction changes its local X from `48` to `19` and
leaves Y `12` unchanged. The same evidence exposes a separate dynamic
text-assembly defect: Battle says `Free Battle`, connective text is duplicated,
and the Japanese destination tail remains. String Translation corrected that
independent assembly in `277ecc1` by splitting the mode head, connective,
destination, and terminator; no canonical mapping gained an authored newline.
The user verified the combined fresh-build result across all four
Battle/Practice and Game Mode/Character Select combinations on 2026-07-27.
The shared quit-confirmation layer is therefore **runtime-proven** with high
confidence.


### Mode Select Return to Title confirmation caller

The 2026-07-29 remade ss1 pair isolates a second consumer of the accepted
C-owned Yes/No mapper. NA2 `FUN_00385C00` draws the confirmation sentence
through dedicated body renderer `FUN_003825B0` at boot-ELF file `0x285E68` /
runtime `0x00385D68`, then draws the live choice object `+0xCC` through
`FUN_00383600` at file `0x285E98` / runtime `0x00385D98`. The body call's
clean eight-byte guard is `6C090E0C00000000`; the choice call's is
`800D0E0C00000000`.

The earlier classification of object `+0xD0` as the visible body was wrong.
Live object inspection while the prompt was visible found its list empty.
Tracing forward identified `FUN_003825B0` as the first actual consumer: it
builds a four-word draw record from constants `DAT_005B1810` X `24` and
`DAT_005B1814` Y `16`, then calls native UI draw `FUN_00379A20`. This explains
why changes to the shared unselected-list adapter had no visible effect.

The existing scoped choice hook reuses Yes `(64.5,31.5)` and No
`(68.5,49)`; the user verified that normal-build top-selector result on
2026-07-29. The bounded body hook reuses the native-body C adapter only when
its exact text is `Return to Title Screen?`, selects a 420-by-40 one-line box
at local `(24,12)`, activates the accepted tracking-zero/plain-space state,
and applies no glyph scale. It deliberately leaves the Collection choice
scope inactive. In fresh 1750-by-1313 native screenshots, NUN5 body ink is
X `194..909`, Y `1042..1078`; unpatched NA2 is X `194..933`, Y
`1056..1091`; the runtime-injected result is X `194..909`, Y `1042..1078`.
Pixel counts are 6,049 versus 6,005, consistent with the small retained raster
difference while geometry is exact. The user verified the exact live body
result on 2026-07-31. Confidence is **verified** for the consumer, guard,
coordinates, and runtime geometry.


### Collection exit-confirmation body and choice list

The replacement 2026-07-30 ss7 pair isolates the Collection exit prompt in
clean NA2 `PRG/ETC.BIN` (200,448 bytes, SHA-256
`8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74`).
The retained Ghidra export identifies two body-draw paths and one bounded
choice-list path:

- clean address `0x006C6540`, file `0x12680`, calls the ordinary body renderer
  for object `+4`; its eight-byte guard is `6C090E0C00000000`;
- clean address `0x006C6560`, file `0x126A0`, calls the complete choice-list
  renderer for object `+8`; its guard is `800D0E0C00000000`;
- the render-state path repeats the body draw at clean address `0x006C8788`,
  file `0x148C8`, with the same `6C090E0C00000000` native-call guard.

The live ETC overlay includes a `0x40`-byte runtime header, placing the first
owner pair at `0x006C6580`/`0x006C65A0` and the render-state body call at
`0x006C87C8`. Editing only the first body hook left the visible prompt
pixel-identical. Exact live inspection then proved that `0x006C87C8` still
contained the native call; redirecting that second consumer through the same
C adapter moved the visible body immediately. Canonical edits therefore keep
both guarded body calls.

Normalized 640-by-480 captures measure Current's body ink at Y `386..401`
versus NUN5 `381..396`, with the same X origin. Current's selected Yes is at
X `282..317`, Y `123..136`, versus NUN5 X `299..336`, Y `131..144`;
Current's No is at X `284..306`, Y `166..178`, versus NUN5 X `306..334`,
Y `156..168`. Draw telemetry identifies the native Collection inputs as Yes
text `0x00604570` at local `(50,24)` and No text `0x00604568` at local
`(50,56)`. Their Y values are exactly the source keys already handled by the
accepted scoped mapper, whose retained targets are Yes `(64.5,31.5)` and No
`(68.5,49)`. Collection therefore needs no new choice formula.

The bounded implementation routes both body calls through one C adapter using
the native UI-draw ABI, local origin `(24.8,12)`, native horizontal scale, a
400-by-60 box, 20-unit line height, and a two-line limit. It preserves the
literal separator between differently colored words. The choice call scopes
the existing mapper with Collection-local Yes `(64.2,29.85)` and No
`(68.1,48.2)` targets. Every other ETC body/list caller and ordinary Yes/No
list remains native.

At the final 1769-by-1327 live-edit capture, scaled NUN5 black ink targets
X `196..680`, Y `1054..1096`; NA2.28 matches those bounds exactly. Scaled NUN5
red ink targets approximately X `350..649`, Y `1052..1090`; NA2.28 measures
X `350..648`, Y `1053..1089`. The user verified the exact live result on
2026-07-31. Status is **runtime-proven** with verified confidence.


### Collection fixed-cadence list wrapping

The replacement 2026-07-30 ss8-ss10 pairs isolate the Collection Movie and
character-detail lists. Bounded NA2 ETC inspection identifies
`FUN_006B4D30`; its shared active row draw is runtime `0x006B4ED8`, file
`0xFD8`, guarded by
`10E40D0C00000000` (`jal 0x00379040` plus NOP). The NUN5 homolog
`FUN_006C7CA0` replaces the corresponding draw at ETC file `0x1164` with its
boxed renderer at `0x0038A210`.

NUN5 stores the active box width and height in each list structure at
`+0x14/+0x18`. The supplied states prove a 192-by-32 box for ss8 Movie titles,
a 152-by-32 box for the ss9 move list, and a 192-by-32 box for the ss10
relationship list. Every family uses native X, native Y minus 10, two lines,
and a 16-unit line interval. The outer list retains fixed row cadence; wrapped
titles occupy two lines inside their existing row rather than increasing later
row positions. Exact visible breaks include:

- `Sealing Jutsu: Nine` / `Phantom Dragons`;
- `People of Endless` / `Darkness`;
- `Ninja Art: Beast` / `Scroll Replicas`;
- `Fourth Awakened` / `Mode`;
- `Shadow Clone` / `Jutsu`;
- `Unchanging` / `Relationship`.

NA2's ss9 parent at `0x00C8D110` points to list head `0x00C75C00`; the visible
text pointers are `0x006D9BD8` (`Right!`), `0x006D9C00`
(`Shadow Clone Jutsu`), and `0x006D9C40` (`Running Wild`). Its ss10 parent at
`0x00C9BDE0` points to list head `0x00C79EE0`; the visible text pointers are
`0x006DC340`, `0x006DC370`, `0x006DC3A0`, and `0x006DC3C0`. The corresponding
NUN5 parents are `0x00C0BCA0` with width 152 and `0x00C1C630` with width 192.
The NA2 structures do not retain homologous usable box fields at the NUN5
offsets, so copying those offsets is not a valid implementation.

The bounded implementation accepts Movie-title pointers in
`0x003FFAA0..0x003FFC10` plus only the seven exact ss9/ss10 character-detail
pointers above, copies the source to a transient buffer, and reuses
`font_v2_wrap_native` with a two-line limit. It draws each resulting line
through the displaced native renderer at a 16-unit interval. That separate
line draw is required because passing the inserted newline to NA2's native
renderer produces a 25-unit interval on these screens. Short titles, the
highlighted red style, fixed caller cadence, source mappings, and every
other pointer through the shared renderer remain native.

The first shared implementation nevertheless published a 20-unit glyph-quad
override for every recognized pointer. It also exposed the flag-aware
right-edge shim defect described below. The compatible task ISO's payload
SHA-256
`74A2A4BD0E66C0F4C55C5A0F67A2342D2E0DE01768D2D2416B945E64D2C0EB39`
still used the older 88-byte shim at runtime `0x008F57B8`, while rejected
integrated build record `20260730_162124_431_pid9072` linked the 128-byte
flag-aware shim at `0x008F5E30`. The older shim ignored flag `0x40`, so direct
injection appeared correct while the integrated payload squeezed the same
rows. This was a resident-hook difference, not a screenshot-composition
difference or a change in the Collection caller.

The corrected Movie-only branch now returns directly to the displaced native
draw when wrapping produces one line. When wrapping produces two lines, it
retains the proven 192-unit width, native X, Y-minus-10 origin calculation, and
16-unit line interval but does not publish the glyph-quad override. The fixed
right-edge shim now makes that clear flag effective. A supplied-ss8 regression
through the fixed shim reproduced the complete retained accepted right text
panel pixel-for-pixel.

The corrected character-detail branch uses the same separation. It retains
`glyph_height = 20.0` solely in `font_v2_prepare`'s two-line
`rendered_height` calculation, which preserves the accepted vertical centering,
but no longer publishes flag `0x40`; the glyph quads therefore remain native.
Fresh supplied-ss9 and ss10 direct-injection captures through the corrected
shim reproduce the accepted ss9 target and retained ss10 target exactly for
every text group. ss9 target/corrected bounds and dark/red glyph-pixel counts
are identical: `Right!` `(646,241)..(734,267)`, `Shadow Clone Jutsu`
`(648,296)..(871,345)`, and `Running Wild`
`(648,376)..(843,401)`. ss10 likewise matches exactly for
`Great Ball Rasengan`, `Overflowing Power`, `Nine-Tail's Cloak`, and
`Unchanging Relationship`. Non-text animation pixels may differ between fresh
frames; the text evidence is native-resolution. The user explicitly accepted
the ss9 target appearance on 2026-07-30; exact integrated-ISO confirmation of
the corrected payload remains pending.

The supplied ss8 state was reloaded through the standard task-owned direct-PINE
workflow after compiling the canonical C. The retained runtime-injected
candidate at
`work/Font/artifacts/priority5_movie_list/rework_2026-07-30/`
shows the four exact breaks above, native-height one-line rows, and native
glyph geometry on the wrapped rows. Its screenshot SHA-256 is
`E26CA0B3F66E413CE55EBA562C7760E6EF539CE6A6096D327D6006510E0391E5`;
the injected fragment SHA-256 is
`1BBA7F25F2CEB3E887B8AB101D36BAF80AD7B531667DC01566F657E1BE7DC06C`.
The user subsequently verified the exact integrated-ISO result on 2026-07-30.
Confidence is **verified** for the bounded Movie branch and runtime appearance;
status is **runtime proven**. The character-detail branch is
**runtime-injected candidate validated** with a user-accepted target and still
awaits exact integrated-ISO confirmation.


### Character Select modal selected row, return body, and choice list

The refreshed 2026-07-29 ss5-ss7 pairs isolate two main-ELF callers inside
the Character Select modal family, and the replacement 2026-07-30 ss1 pair
isolates its remaining return-confirmation list caller:

- file `0x2BC984` / runtime `0x003BC884`, guarded by
  `84090E0C00000000`, draws only the selected row in the five-row
  `Back to Game Mode Screen` modal;
- file `0x2BCAAC` / runtime `0x003BC9AC`, guarded by
  `800D0E0C00000000`, draws the complete top Yes/No list for the return
  confirmation;
- file `0x2BCB54` / runtime `0x003BCA54`, guarded by
  `C4080E0C00000000`, draws only the `Return to Game Mode Screen?`
  confirmation body.

The selected-row adapter uses a 240-by-20, single-line, shrink-only box at the
caller's Y and five local units to the right of its incoming X. The original
declarative selected-delay-slot compensation is removed because the symbolic
eight-byte hook replaces that call and delay slot atomically. The final ss5
red-ink bounds are `x=170..466`, exactly matching NUN5. The supplied ss6
Linked Mode state remains unchanged, proving that the selected hook does not
select the adjacent ordinary-row family.

The 2026-08-03 `font/main` captures 50 and 51 isolate the structural fifth row
in both draw states. Capture 51's ordinary black ink is two output pixels below
NUN5, whereas capture 50 proves the selected footer already has the correct
vertical phase. The shared declarative row producer therefore changes only the
fifth-row origin from local Y `116` to `115`. The selected adapter's local
compensation changes from `-2` to `-1`, preserving its final Y at `114`, while
the unchanged ordinary adapter consumes Y `115` directly. Rows one through
four remain on their existing coordinates. This fixes the ordinary footer
without adding or resizing any resident fragment, so every unrelated payload
symbol retains its prior address.

The producer is the row loop in NA2 main-ELF `FUN_003BC780`. When the loop index
is four, its branch at runtime `0x003BC824` adds the footer-only Y term before
the selected call at file `0x2BC984` or the ordinary call at file `0x2BC9BC`.
The existing guarded `localization__font__layout__character_modal_na2_elf_at_002bc924` replacement owns that
block at files `0x2BC924..0x2BC94F`: the first four iterations advance from
local Y `8` by four `24`-unit intervals to `104`, and its instruction at file
`0x2BC940` now loads `11.0` (`lui v0,0x4130`) instead of `12.0`, producing the
fifth-row Y `115`. Confidence is high: clean-ELF disassembly identifies both
draw-state consumers, the guarded replacement isolates the row-four branch,
and captures 50 and 51 independently expose the two final renderer phases.

NUN5 telemetry for the confirmation body is box `(8,8,368,24)`, horizontal
policy `2` (center), vertical policy `1`, and incoming scale `1`. A first C
candidate applied only those box dimensions while retaining NA2's existing
primary/direct renderer setup. It fit, but its letters stayed visibly smaller
and narrower than NUN5. That negative result proves that box math alone does
not select the expected glyph presentation.

The accepted sequence selects the secondary renderer through
`FUN_00186510(renderer,1)`, restores renderer fields `+0x28/+0x2C`, sets the
draw context from the modal object at `+0x74` through `FUN_001866D0`, then
uses the resident v2 measurement to compute the centered left edge inside the
368-unit box. The final callback draws from that prepared left edge through
native left draw `0x00379040`. Calling the native centered primitive instead
is rejected here: it remeasures with obsolete state and shifts the otherwise
correct result left.

For the exact accepted string, both NUN5 and NA2.28 black-ink bounds are
`(151,328)-(484,341)`; dark-pixel counts are `1209` and `1202`. The retained
comparison is
`work/Font/artifacts/priority3/ss7-secondary-renderer-left-edge-comparison.png`.
The user accepted that lower confirmation body as good enough on 2026-07-30.

The same replacement-batch ss1 proves that the body remains correct while the
native top Yes/No list does not share NUN5's relative placement. Redirecting
only file `0x2BCAAC` to the existing
`v2_quit_choices_scope` reuses the already-proven Yes
`(64.5,31.5)` and No `(68.5,49)` map without introducing another C formula or
assembly fragment. A hidden direct-PINE trial loaded the supplied ss1,
installed only that guarded call, and produced a native 640x480 capture. The
modal boxes have different absolute X positions between games, but both
Current rows then have the same X/Y offsets from their respective modal
origins as NUN5. The accepted lower body remains unchanged. This selector
result is agent-validated and awaits explicit user acceptance.

Confidence is **verified** for the three call sites, renderer selection,
coordinate contracts, caller isolation, and supplied-state behavior. User
acceptance currently covers the lower confirmation body, not the new top
selector result.


### Practice explanation mixed-text wrapping

Bounded NA2/NUN5 BTL comparison identifies the Practice explanation loop as a
separate caller family from the title draw immediately before it. NA2 reaches
the loop at BTL file `0x1C4BA0` / runtime `0x00878AA0`; NUN5 instead assembles
one bounded mixed text/tag string, installs a call-local metric/draw callback
pair for controller tokens, and passes the complete result through its wrapping
renderer.

The v2 adapter follows that broad caller logic rather than patching individual
rows. It builds a single 512-byte buffer from the caller's text and token
records, word-wraps it with the accepted proportional metric table, and uses a
364-by-48 box at X `39.2` and caller Y plus `21.2`. The glyph height is 28 and
the independent line advance is 14. The line-count field is zero, meaning
unlimited: the supplied NUN5 `ss3` Flee row proves that this nominal 48-unit
box legitimately carries three explanation lines, so the earlier two-line cap
was rejected before promotion.

The callback map preserves all 13 Practice controller tokens. D-pad directions,
Circle, Triangle, Square, Cross, plus, L1, R1, L2, and R2 use NA2's native icon
table and native draw helper; the adapter selects the caller's primary or
secondary icon object exactly as the original path does and applies the
NUN5-proven per-token Y offsets. Metric and draw callbacks, both icon objects,
renderer tracking, horizontal scale, and the prior active session are restored
after every call.

Supplied Practice slots 2-7 were converted with exact source hashes and guarded
memory edits because a savestate restores its captured BTL overlay and resident
RAM over the worker ISO. The converted task-owned states and manifests are
under
`work/Font/artifacts/autofit_v2/practice_explanations/`. Hidden 640x480
captures show:

- `ss2`: the Manual Linked Attack explanation wraps to two lines;
- `ss3`: Flee wraps to three lines with D-pad, plus, and Cross intact;
- `ss4`: substitution, recovery, and extra-hit rows retain shoulder, face,
  D-pad, and plus icons;
- `ss5`: Circle and D-pad rows align; Current `Charge` versus NUN5
  `Charge Chakra` is a separate text-mapping difference;
- `ss6`: movement rows preserve D-pad, plus, and Cross alignment;
- `ss7`: Shadowblur wraps to two lines while Circle, shoulder, D-pad, and plus
  icons remain aligned.

Across all six pairs, wrapping, line spacing, X/Y placement, and inline-icon
alignment match the NUN5 reference. Separate Controls and Command Chart
captures retain their accepted label and title behavior. The blank 2P Controls
column reproduced from the untouched source state and remains known
state-resume behavior rather than a renderer regression.

The isolated worker ISO has SHA-256
`D624C39F0132FF5ED3BA4D60E99B78113AF85805D3870B072643B9400CC2B10B`
and boot CRC `A85C52F7`. Its 7,536-byte resident payload ends at `0x008F5A70`
and has SHA-256
`47EF54100642B25366FADF4A0D5C12B7255D3CF89456BD3F3DB5ACB056ED1101`.
The generated 4,084-byte v2 asset has SHA-256
`382AD202C1225326B59832BECE7A8AE61A2A69870B18B17D1F606B6C5152BE90`.
Deterministic fragment and relocation tables have SHA-256
`22F728E0C5E4AE279F8DE719636E1301CAB482891DDE6FAECA3BEDEE96D7EC84`
and
`CB45E870106EF9E95C29947922BEC5F4CC640DBCE044CC2AA9AEC8F60BA703C4`.
The grouped comparison sheets are
`work/Font/artifacts/autofit_v2/practice_explanations/report/practice-explanations-02-04.png`
and
`work/Font/artifacts/autofit_v2/practice_explanations/report/practice-explanations-05-07.png`.
The family is runtime-proven and enabled; the grids still await user
acceptance before work begins on another caller family.

Commit `e906ce0` placed the complete helper block at runtime
`0x003D3E00..0x003D4388` (file `0x2D3F00..0x2D4488`) inside the larger
common-zero interval `0x003D3DB6..0x003D5D30`. That interval is zero in the
clean ELF and was zero in all 16 states then sampled. A disposable ISO marker
audit also proved that markers at its start, middle, and end survive after a
fixed five-second boot settle. PINE becomes ready while the large boot ELF is
still being copied, so immediate reads of high file-offset caves can
transiently return zero and are not valid placement evidence. The later
Load-screen evidence below proves that boot-settle and sampled-screen survival
were nevertheless insufficient: the game clears this whole interval during a
transition that the original regression did not cover. Runtime scratch was
placed in the independently state-zero range `0x003FAD18..0x003FAE44`.

A full ten-state guarded regression covered Practice pause, Controls, Command
Chart, command explanation, Practice settings, Practice quit, character
return, Collection quit, Collection movie, and the no-memory-card prompt.
Controls and the wrapper-owned Practice/confirmation families retained their
matched results. Command explanation, Collection movie, and no-memory-card
overflow were separate unresolved caller families at that historical
boundary; their unchanged defects were not regressions from this port. The
later dedicated Collection Movie-list work resolves that family as documented
above. Confidence is **high** for the shared
measurement formula, hook boundaries, caller guards, and matched horizontal
result. That regression did not cover entry into Save/Load and therefore did
not establish persistent ownership of the helper interval.


## 2026-07-30 Linked Mode center-selector isolation

Replacement-batch ss2 identifies the center-screen `Linked Mode`, `Manual`,
and `Auto` selector as main-ELF `FUN_003B8F40`. This is not the adjacent
five-row character-modal family: trial changes to that family left ss2
unchanged, while three exact writes in `FUN_003B8F40` moved only the visible
center modal.

The title path loads local Y `12.0` at runtime `0x003B8FE0` (ELF file
`0x2B90E0`) before its ordinary renderer call. The choice loop loads base Y
`48.0` at runtime `0x003B90A4` (file `0x2B91A4`) and retains a native
`48 + 26*i` formula. Its selected renderer call is at runtime `0x003B90DC`
and its unselected call is at `0x003B90FC`.

NUN5 homolog `FUN_003CBAF0` uses one selected-state-aware
`FUN_00393210` call with local formula `36 + 22*i`. The helper semantics differ
from NA2's separate selected and ordinary renderers, so copying those two
constants directly is not coordinate-equivalent. Supplemental ss2 with
`Manual` selected supplies both NA2 paths in one frame. The earlier
`44 + 26*i` plus selected-only compensation and later `46 + 20*i` candidate
were intermediate geometry trials and are superseded.

The final bounded formula is `45 + 22*i`, with no selected-only compensation,
and the title remains at local Y `8`. The exact clean guards are title
`4041023C`, interval `D041023C`, and base `4042023C`; replacements are
`0041023C`, `B041023C`, and `3442023C`. Final-red captures 18 and 19 show
selected `Auto` and `Manual` red and aligned with NUN5. No adjacent modal is
changed; explicit user acceptance remains pending.

## 2026-08-02 Linked Mode selected-color ABI correction

Clean main ELF SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`
proves that the selected Linked Mode call at file `0x2B91DC` supplies exactly
four arguments: `a0=object`, `a1=draw_x`, `a2=draw_y`, and `a3=text`. The
pre-call block at `0x2B91C4..0x2B91D8` never initializes `t0`.

The native callee `FUN_00382610` forwards selected state `1` to
`FUN_00379040`. That state renders the gray pass and then packed red
`0xFF0000D4`. By contrast, the Pause selected callback legitimately receives a
fifth packed-color argument in `t0` before tail-calling `FUN_003827A0`.
Reusing that callback for Linked Mode treated undefined caller-saved `t0` as a
color; the integrated capture exposed the result as blue selected `Auto`.

The bounded correction is deliberately color-only. The existing Linked metric
session, centered `1.05` scale, computed draw origin, title position, shared
choice base, and row interval remain unchanged. The typed Linked entry ignores
incoming `t0` and supplies `0xFF0000D4` to the retained callback. This preserves
the user-reviewed geometry while restoring the native selected red. A future
renderer refactor may instead use a dedicated tail callback to `FUN_00382610`,
but it must first prove byte-equivalent visible geometry; it is not part of
this correction.

## 2026-07-30 Character Select ordinary-row metric session

Supplemental ss1 reopens only the five-row player-mode list inside
main-ELF `FUN_003BC780`. NA2 draws its selected entry through
`FUN_00382610` at runtime `0x003BC884` and every ordinary entry through
`FUN_00382470` at runtime `0x003BC8BC` (ELF file `0x2BC9BC`, clean guard
`1C090E0C00000000`). NUN5 homolog `FUN_003CF3F0` instead routes both states
through one `FUN_00393210` helper, with native local Y values `0`, `24`, `48`,
`72`, and `106`.

The existing selected hook already enters the accepted 240-unit v2 metric
session and applies a five-local-unit X correction. Ordinary rows bypassed that
session, so their Y bounds were already exact but their visible widths were
eight or nine pixels too large and their left edges were six pixels too far
left. A second caller-specific C entry now gives only the ordinary draw the
same metric session and X correction, then returns through the original
ordinary callback. It does not alter the row table, selected renderer, Linked
Mode, or confirmation callers.

At 640x480, the three ordinary comparison rows now have exact NUN5 bounds:
`(259..377,206..219)`, `(257..379,236..249)`, and
`(246..390,266..279)`. The selected first row remains on its prior accepted
path. This proves that the discrepancy was session selection rather than
per-row Y drift or a need for individual scale constants. Confidence is high;
explicit user acceptance of the refreshed five-row list remains pending.

## 2026-07-27 Special Controls explanatory-body wrapper

The remade paired ss1 state proves the selector and lower explanatory block are
one Special Controls acceptance case. Exact NA2 wrapper telemetry records only
the lower block at BTL file `0x1C3D38`, runtime `0x00877C38`: caller
`0x003825F8`, outer caller `0x00877C40`, text pointer `0x008BCD60`, style
pointer `0x00E5E430`, and native local coordinates X `24`, Y `16`. The clean
eight-byte guard is `6C090E0C00000000`, native `jal 0x003825B0` plus NOP.

NUN5 does not store a newline in the source string. Its source at
`0x008F47C0` is `A feature to display the special controls for the game.`,
while the live transient buffer at `0x00DE82E1` contains
`A feature to display the special controls\nfor the game.`. The associated
live record contains scale `1.0`, box width `400`, box height `60`, and line
limit `2`. The accepted v2 metric table measures the text through `controls`
as `370` units and through the following `for` as `405`, which independently
explains the exact NUN5 break before `for`.

The bounded implementation therefore redirects only BTL file `0x1C3D38` to a
caller-specific adapter generated from the same shared v2 body builder as the
accepted quit modal. It copies at most 255 bytes to its stack, wraps at draw
time inside a 400-by-60 two-line box, and draws at local X `24`, Y `12` with
20-unit line height. T1880 remains canonical and unbroken, and the shared UI
renderer remains untouched. An exact-guarded task-owned state installed the
linked trial payload at `0x008F6000`, redirected only the five session-aware
core hooks plus this body call, and produced the same break and line origins as
the supplied NUN5 reference. Confidence is high; user acceptance was not
established by this evidence.

The later matched OFF-highlight ss1 pair exposed a separate selector-state
regression in the already shared selected/unselected hooks. The first state
showed selected ON and unselected OFF, so the original guards recognized only
ON in the selected helper and only OFF in the unselected helper. Highlighting
OFF swaps those consumer roles: selected receives pointer `0x006059F8` and
unselected receives `0x006059F0`; both guards missed and fell back to native
placement. The corrected adapters recognize both pointers in both roles and
keep coordinates attached to the text row: ON `(66,31)`, OFF `(59,49)`.
An exact-guarded converted copy of the new state redirected only ELF calls
`0x283914` and `0x283A60` to a task-local linked payload and matched the NUN5
OFF-highlight selector while retaining the accepted wrapped body. Focused
tests now verify the branch target for each ON pointer loads X `66`, while
each OFF fallthrough loads X `59`; this prevents another role-swap regression.

## 2026-08-01 Special Controls selector glyph geometry

The replacement slot-1 pair was saved three seconds apart. Current state
SHA-256 `A8343BC0400BCD3FB1C21CF607308FA880C31C25825569062861A688DEA004CC`
uses CRC `2DA77DC7`; NUN5 state SHA-256
`D07EB61EF3D19ADE18B8A1D116D71ACFCAB5371569FAD4CEC946086506328853`
uses CRC `C071D4C1`. Their embedded 640x480 screenshots have SHA-256
`A61393D3321402BD8AB497250E5869FE3FCB6290FD40724A78ED6A8298C94205`
and `B7609673D90CA521B88711D6D8793333FF88E1CBA6215B56D12A67B56722CD7A`
respectively. The pair shows selected ON and ordinary OFF. Both Current words
start at the intended row origin but their ink ends two pixels early to the
right and bottom.

The correction remains inside the two already-owned calls at ELF files
`0x283914` and `0x283A60`. Both adapters recognize both text pointers, so the
formula follows selected versus ordinary rendering when the selection swaps;
it does not follow ON versus OFF. The selected path adds one local X unit and
uses scale `1.02`; the ordinary path uses scale `1.01`; both request glyph
height `26` through the existing session-scoped renderer state. The session is
restored after each native callback, and no string bytes are written. A guarded
hidden-worker candidate against the matching Current ISO produces the retained
comparison
`work/Font 3/outputs/comparisons/settings/ss1_onoff_state_split_s102_u101_h26_nun5_top_candidate_bottom_zoom.png`:
NUN5 is above, the candidate is below, and the crop is nearest-neighbor 8x.
The selected and ordinary core-glyph bounds align with NUN5 while all unrelated
choice pointers continue through their prior native paths. Confidence is
**high**; integrated user acceptance remains pending.

## 2026-08-01 global selected-style default

The first candidate covered only NA2 runtime `0x00379150`. User isolation
testing proved that it corrected roughly half of the game while the selected
`Back to Game Mode Screen` row in the Character Select five-row modal retained
NA2's displacement. Clean call tracing shows that row enters runtime
`0x00382610`, which calls separate state-aware selected primitive
`0x00379040`. The two-central-primitive candidate fixed additional screens,
but the supplied `Save data?` comparison remained displaced because shared
save/load runtime `0x001E6CE0` inlines both selected passes and calls neither
central primitive.

The complete boundary requires a function-level semantic scan, not a search
for one instruction encoding. Across clean `SLPS_258.37`, `ADV.BIN`,
`BTL.BIN`, and `ETC.BIN`, exactly six functions combine gray `0xFF808080`, an
X `-1.0`/Y `-2.0` selected pass, and the text renderer. All six are in the
boot ELF:

- `FUN_00379040` / runtime `0x00379040`: state-aware central primitive;
- `FUN_00379150` / runtime `0x00379150`: caller-colored central primitive;
- `FUN_00379C30` / runtime `0x00379C30`: fixed two-choice primitive;
- `FUN_001E6060` / runtime `0x001E6060`: shared two-record list component;
- `FUN_001E6370` / runtime `0x001E6370`: three-record save/load slot row;
- `FUN_001E6CE0` / runtime `0x001E6CE0`: shared Save/Load, overwrite, and
  return-to-title Yes/No component.

The overlays contain callers but no seventh implementation. NUN5 homologs
`FUN_001EBEE0` and `FUN_001ECAD0` replace the corresponding NA2 two-choice
logic with NUN5 helper `FUN_00392920`, which creates selected markup with
shadow enabled. NUN5 `FUN_001EC0B0`, however, retains the manual three-record
sequence; normalizing NA2 `FUN_001E6370` is intentional because the requested
result is one global stable-origin rule, not a claim that every NUN5 caller was
internally rewritten.

The implementation applies one formula through three storage-ABI adapters:
shadow `(x+1,y+2)`, selected glyph `(x,y)`. Boot-ELF files `0x279168` and
`0x279278`, guarded by `80CA848F80FF0234`, call the same 48-byte register
adapter after the central primitives save X/Y in `f21/f20`. Seven exact gray
record-draw calls in `FUN_001E6060`, `FUN_001E6370`, and `FUN_001E6CE0` call
one 56-byte record adapter before their untouched native `(-1,-2)` step.
Boot-ELF file `0x279D30`, guarded by `A0FFBD275000BFFF`, redirects the fixed
two-choice primitive to a 208-byte dispatcher: selected rows use corrected
`FUN_00379150`, ordinary rows use native `FUN_00378F50`, and the original
renderer context, record pointers, order, and colors are preserved.

NUN5's larger renderer and markup helpers remain binary-incompatible with
NA2, so no NUN5 machine-code block is transplanted. No string bytes are
written. Every screen-specific Font patch is temporarily disabled while the
user verifies this isolated global behavior; no agent runtime or screenshot
test is performed.

## 2026-08-02 Practice Settings left-column completion

The paired 2026-07-31 Practice Settings inputs are retained under
`work/Font/inputs/sstates/batches/2026-07-31-practice-settings-ss1/` and
`work/Font/inputs/sstates/batches/2026-07-31-practice-settings-ss3/`, with
matching extracted screenshots and provenance in their sibling input trees.
The ss1 state selects `Attack`; ss3 selects `Extra Hit Counter`.

Both pairs established one template-level left-column origin error across
selected and ordinary labels, not unique row defects. The overhaul now routes
the exact Practice heading and loop label callers through shared page formulas
while keeping the right value and explanation families separate. The final
main replay includes the corrected page without a large position, width, wrap,
or style discrepancy.

## 2026-08-02 structural Collection-family completion

Collection uses these relevant list families:

- ordinary characters: Figure, Ultimate Jutsu, and character-specific Music;
- legacy characters: Ultimate Jutsu only;
- Diorama;
- Movie;
- global Music;
- the Characters index where applicable.

Figure remains the only narrow character-detail list and uses the `152`-unit
profile. Relationship and Movie rows use the wider `192`-unit profile. One
shared ETC hook classifies them from native call geometry; no character, row,
or string whitelist remains. Fitting rows enter the same bounded renderer
session at family X `+1.2` and one-line Y `-4.0`, with zero tracking and fixed
horizontal scale `1.0`; they do not publish a glyph-height override, so their
native vertical glyph size remains unsquished. Only measured overflow enters
the two-line compositor. Figure/Music character headers share one origin
formula, and ordinary/legacy Ultimate Jutsu headers share another.

The `font/music` E2E batch exposed why this session boundary must include
fitting one-line rows: the previous direct native-draw return measured with
NUN5 proportional metrics but retained NA2's extra renderer tracking, causing
progressive horizontal divergence and clipping the longest titles. Routing
those rows through the session removes only that tracking. Across all seven
paired captures, selected-row top and bottom bounds remain unchanged from the
pre-change NA2 captures; selected-row widths match NUN5 exactly or differ by
one antialiasing pixel. The complete normal/padded `font/music` replay passes.

Raw NUN5 ETC records are not safe byte donors: homologous list records assign
different meanings to fields at `+0x14/+0x18` and shift live resource fields.
Port NUN5 classification and layout semantics instead of entire records or
tables.

The earlier representative paired batch is retained at
`work/Font/inputs/sstates/batches/2026-07-31-collection-ss4-8/`, with hashes and
source aliases in `provenance.tsv`:

- ss4: Naruto character-specific Music;
- ss5: Naruto Classic Ultimate Jutsu;
- ss6: Diorama;
- ss7: global Music;
- ss8: Sasori ordinary-character Ultimate Jutsu.

Matching screenshots are under
`work/Font/inputs/screenshots/batches/2026-07-31-collection-ss4-8/`. That tree
also retains `character-index_NA228.png`; the user reported no Font defect on
the Characters index, so it remains reference-only. Synchronized final-red
font2 cases 1-7 cover Sakura and legacy-character variants plus Movie without a
large Font defect; later desynchronized cases are excluded from evidence.

## Matched-screen baseline

Ten timestamp-matched NUN5/NA2 savestate pairs supplied on 2026-07-24 provided
the initial cross-screen baseline. Their embedded 640x480 screenshots were
measured with fixed dark-ink bounds on manually verified crops. Those
measurements support relative screen comparison, not replacement of renderer
metrics recovered from code.

| Screen family | Initial NA2 result | Durable conclusion |
| --- | --- | --- |
| Practice pause list | Long label clipped | Caller needed fitting or corrected advances. |
| Control Settings | Long and short rows made the correct fit decisions | Existing boxed-fit boundary passed. |
| Command Chart | Long move name clipped | Caller needed fitting or corrected advances. |
| Practice explanations | Descriptions clipped on one line | Caller needed wrapping and layout behavior. |
| Practice Settings | Rows fit at the wrong local origin | Positioning was caller-local. |
| Quit confirmation | Body clipped; choices were misaligned | Body wrapping and shared modal layout were separate concerns. |
| Character Select confirmation | Choices matched the same modal defect | The repeated defect was shared, not screen-specific. |
| Collection confirmation | Choices matched the same modal defect | The repeated defect was shared, not screen-specific. |
| Collection Movie list | Long entries did not wrap | List-specific wrapping was required. |
| No-memory-card prompt | Only three clipped lines were visible | System-prompt wrapping was required. |

Across 20 identical black-text samples, median NA2 differences from NUN5 were
-2 pixels in visible width, -2 pixels in visible height, `0.850782x` total
dark-ink pixels, and `1.018280x` dark-ink density inside the smaller bounds.
The font was therefore not a uniformly enlarged or uniformly heavier raster.
String-dependent width errors and caller-dependent vertical offsets proved
that one global scale, tracking, X, or Y correction could not establish
parity.

The three confirmation screens reproduced the same choice geometry: NUN5
placed `Yes` and `No` about 25 pixels apart vertically, while NA2 placed them
about 43 pixels apart and shifted both left. This justified one shared modal
correction. The baseline also separated raster appearance from missing
wrapping: improving glyphs alone could not fix Practice explanations,
confirmation bodies, Collection lists, or system prompts. Earlier screens with
different scrolling-help animation phases were excluded from alignment
comparisons. The domain sections above record the resulting caller-family
implementations and accepted outcomes.
