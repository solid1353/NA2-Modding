# Controls Font layouts

Font-owned layout evidence for Command Chart relationship rows, Pause Controls, and Special Controls.

## Command Chart relationship rows

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
request passes right edge `308`, height `32`, line limit `2`, and style `9`.
`SUB_00393ED0` folds its already composed X input into that right edge before
calling the word wrapper. The sole NUN5 BTL float pair at file `0x1FAD34` is
title-local X `4` followed by relationship-local X `20`; a 16-unit container
term reaches the outer wrapper with those values, and the object contributes
the final 8 units to visible origins `28` and `44`. The word wrapper therefore
receives `308 - (16 + 4) = 288` for titles but
`308 - (16 + 20) = 272` for relationships. A hidden task-owned runtime probe
at the exact `FUN_0018C4F0` call confirmed both widths with tracking `0`, scale
X/Y `1`, and descriptor `0x00B592D0`. The former `288` relationship result
subtracted only the stored row-local value and omitted the already composed
container term. The native row formula also separates relationship and icon
placement: after the title it draws the combined relationship from
`fVar17 + 4` and the icons from `fVar17 + 44`, while NA2 advances its shared
row coordinate by `30` before the relationship and then draws icons only `20`
units below it. This explains both refreshed cases: ss1 needs one jointly
wrapped two-line block, while all three ss2 single-line rows and their icons
share the same repeatable vertical correction.

The bounded NA2 port therefore hooks only the first exact auxiliary call through
a 36-byte native-register shim, passes the row record and native Y to generated
C, and suppresses only the second exact draw. The C entry resolves both strings
from NA2's live table at `0x008BD1D0`, combines them without modifying canonical
mapping bytes, and wraps at spaces through the shared native-metric v2 helper.
The NA2-side port uses visible X `44`, native Y minus `11.5`, width `272`,
height `32`, line advance `30`, glyph height `14`, and a further `-7.2` Y bias
only when the wrapped result has one line. The accepted ASCII width table
measures `Consume Chakra/Take Down` at `252`,
`Consume Chakra/Charge/Jump` at `272`, and the latter plus ` OK` at `303`.
It also measures `Chakra Gauge 1+/Nor. Ultimate` at `275`,
`Chakra Gauge 2+/Awk. Ultimate` at `281`, and
`Chakra Gauge 3/Rev. Ultimate` at `267`. Width `272` therefore reproduces all
observed NUN5 boundaries: it retains the complete `/Jump` line and breaks
before `OK`, breaks the 1+/Nor. and 2+/Awk. forms before `Ultimate`, and keeps
the 3/Rev. form through `Ultimate` before breaking at `Jutsu`. The former
`226`, `264`, and `288` relationship widths were empirical or incomplete
derivations, while `308` incorrectly treated the right edge as a width. The
native icon loop remains intact.
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


## Pause Controls list v2 callers

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


## Special Controls explanatory-body wrapper

Evidence date: 2026-07-27.

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

## Special Controls selector glyph geometry

Evidence date: 2026-08-01.

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
