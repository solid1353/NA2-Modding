# Controls and Practice Font layouts

Font-owned layout evidence for Command Chart, Pause Controls, Special Controls, and Practice screens. The initial grouped findings were established on 2026-07-24; later evidence dates are recorded with their sections.

## Command Chart and Practice title boxes

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


## Practice explanation mixed-text wrapping

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

## Practice Settings left-column completion

Evidence date: 2026-08-02.

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
