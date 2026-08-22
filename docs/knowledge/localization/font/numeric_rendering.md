# Font numeric rendering

## Save/Load ASCII numeric fields

The matched slot-6 pair is preserved under
`@work/Font/inputs/sstates/sjis_digits/slot-06/`. Its embedded screenshots and
EE-memory payloads establish that NA2 emits fullwidth CP932 digits for
`２０２６/０７/１７` and `Play Time ０２７：３９：４５`, while NUN5 emits
ordinary ASCII digits and punctuation.

NA2 `FUN_001e6370` owns all six visible numeric calls. It routes year, month,
day, hour, minute, and second through the fullwidth formatter
`FUN_00378510`; the NUN5 homolog `FUN_001ec0b0` routes its numeric fields
through ASCII formatted output. The compiled-C implementation changes only the
six guarded call blocks at ELF file offsets `0xE660C`, `0xE6650`, `0xE6694`,
`0xE67A4`, `0xE67E8`, and `0xE682C`. Each block now contains argument setup,
a symbolic runtime-injector call, and unavoidable year-return preservation;
all formatting behavior lives in `font_numeric.c`.

The first C entry reads day and year directly from the live record, formats
day through immutable `%02d`, and returns year in `v0`; the hook moves that
return to callee-saved `s6`. The month uses the same C two-digit entry, the
third entry emits the preserved year through `%d`, and the hour C entry
reproduces NUN5's signed `hour < 100 ? hour : 99` rule before `%02d`.
Canonical liveness shows `s6` is saved in the prologue and otherwise unused
until the later seconds calculation, so it safely survives the intervening
native formatting calls. Timer divisors `108000`, `1800`, and `30`, all six
guarded block sizes, and every formatter caller outside `FUN_001e6370` remain
unchanged. The Save/Load-only fullwidth colon at ELF file offset `0x503134`
remains a declarative ASCII-colon edit.

The pre-migration behavior is runtime-proven: the user confirmed correct
`DD/MM/YYYY`, including the four-digit year, on Current CRC `55739D20`.
The first consolidated C candidate at commit `1d796a5` was runtime-rejected on
Current CRC `8A663AA9`: user `ss1` records the menu immediately before Load,
and `ss2` records the broken Load screen. Their task-owned copies and hashes
are retained under
`@work/Font/inputs/sstates/c-migration-load-regression-2026-07-28/`.

Static control-flow comparison identifies the exact defect with high
confidence. All six guarded blocks are mid-function replacements for native
`jal sprintf` calls, but the rejected symbolic rows used non-linking `j26`.
Each compiled C entry returns with `jr ra`; without a new link address, it
returns to the surrounding formatter's caller instead of resuming after the
hook. The corrected candidate uses `jal26` at relocation offset `0x8`, so the
C entry returns to the next instruction and the surrounding Save/Load function
continues. The argument setup, C object, returned-year move into `s6`, block
sizes, and every formatter outside this family remain unchanged. Runtime
acceptance is complete: after the fresh corrected build, the user verified
that Load and Save open without freezing and retain the accepted date/time
presentation. Independent fragment reconstruction is retained in
`@scripts/research/localization/verify_font_renderer.py`. Unit-test coverage now
protects the independently established linking-call contract for all six
Save/Load hooks.

The isolated worker build retained at
`@work/Font/build/save-load-ascii-digits.iso` has boot CRC `F9FC3002`. After a
clean manual launch in the Font-owned PCSX2 copy, the user confirmed that the
Save/Load date and Play Time fields render correctly as ASCII. The patch is
therefore proven for its original ASCII-conversion stage. The later EU date
ordering is separately user-confirmed on Current CRC `55739D20`.

## Battle Settings ASCII time value

The matched slot-1 pair copied read-only from the user's PCSX2 is preserved
under
`@work/Font/inputs/sstates/sjis_digits/slot-01-20260726_115913/` with source
timestamps and SHA-256 provenance. Both embedded screenshots show Battle
Settings with `Time 99`; NA2 emits the value through its fullwidth numeric
path, producing visibly wider digit spacing than NUN5's ordinary ASCII value.

NA2 `FUN_008801e0` is the Battle Settings row sub-renderer called by
`FUN_008807a0`. For the Time row, value `100` takes a separate infinity-symbol
branch. Every other value reaches the fullwidth formatter through the guarded
24-byte BTL call block at file offset `0x1CC3D8` (Ghidra `0x00880298`,
runtime `0x008802D8`). The NUN5 homolog is `FUN_0089cbd0`, called by
`FUN_0089d280`.

`localization__font__numeric_formatting__battle_settings` changes only that ordinary-value block to
set up the value and stack buffer, then call the compiled C entry through a
linking `jal26` runtime-injector hook. The rejected consolidated candidate used
the same non-linking `j26` control-flow error as Save/Load; the correction
changes only the hook encoding. C uses the immutable `%d` bridge. The adjacent
40-byte branch ending at the edit site is independently guarded, so value
`100` continues to render the native infinity symbol. Selector state, the
stored timer value, the other five settings rows, and every other fullwidth
formatter caller remain unchanged. Independent fragment reconstruction is
retained in `@scripts/research/localization/verify_font_renderer.py`. After the
corrected fresh build, the user verified the ordinary below-100 value and the separate
100/infinity behavior. The patch is therefore `runtime_proven`, and unit-test
coverage protects its linking-call contract.

## Ninja Song ASCII dynamic numbers

The paired ss2–ss5 states are copied read-only under
`@work/Font/inputs/sstates/ninja-song/ss2-5/` with exact source filenames,
timestamps, sizes, and SHA-256 provenance. Together they cover the dynamically
generated arithmetic factors, arithmetic total, inline numeric placeholder,
and detail score used by the Ninja Song screens.

NA2 BTL `FUN_00718920` (file function offset `0x64A60`) renders the arithmetic
expression, and `FUN_00718C60` renders the later detail fields. Their NUN5
homologs are `FUN_0072E5B0` and `FUN_0072E9C0`. Five calls in those two NA2
functions reach the same fullwidth CP932 formatter `FUN_00378510`:

- `0x64B28`: left factor, width 3, mode 0;
- `0x64BA8`: right factor, width 3, mode 0;
- `0x64CE4`: total, width 5, mode 0;
- `0x64E4C`: inline value, width 4, mode 1;
- `0x64ED4`: detail score, width 4, mode 0.

The NUN5 formatter homolog preserves the caller ABI but emits ASCII decimal.
Mode 0 left-pads with ASCII spaces to the requested width, mode 1 emits an
unpadded value, and mode 2 left-pads with ASCII zeroes. The shared
`ninja_song_ascii_number` helper reproduces those modes
behind NA2's existing ABI and calls the immutable `%d` formatter at runtime
`0x0017BCA0`. Exactly the five guarded BTL JAL instructions above redirect to
it; no per-screen duplicate formatter is introduced.

The multiplication separator remains reachable. In the copied ss2 runtime
state, its pointer resolves to bytes `20 2A 20` (`" * "`), already supplied by
canonical translation mapping T2195 from `NA2_SLPS@0x504DA0`. The Font patch
therefore guards that mapping but does not rewrite the separator. On
2026-07-27, the user built and tested the integrated change across ss2–ss5 and
declared the task done. Some runtime numeric values were not observed, but
they are not separate strings: all values pass through the same five guarded
call sites and width-aware decimal helper. The patch is therefore
`runtime_proven`; arbitrary unseen decimal values retain the same mode and
padding behavior. Deterministic verification is provided by
`@scripts/research/localization/verify_font_renderer.py` and
`@scripts/research/localization/generate_ninja_song_ascii_numbers.py`.

Controls retains full-width `Linked Attack`, fits the official 19-byte
`Ultimate Jutsu Prep` probe through the shared NUN5 logical-width helper,
leaves `OFF` on the ordinary renderer, and restores local scale immediately
after a fitted draw. Its labels move one local X unit without moving selection
markers. Shared layout wrappers also reproduce the reviewed confirmation
choices, Practice pause-list box and Y origin, confirmation-body placement,
and character-return box. The character modal measures and centers all five
selected and ordinary rows in one local `(8, *, 240, 20)` box; the long footer
shrinks within that box, and the shared structural footer origin is Y `114`.

A clean glyph derivation preserves the GF4 and GF4C file sizes and produces:

- `DATA/GF4.BIN`: 906,678 bytes, SHA-256
  `79BA614746E667A70A068A0A889085D028D8019884182E78041026A77971AA25`.

Executable Font output no longer has an independent final ELF hash: the shared
payload builder assigns its runtime addresses together with every other
resident contribution, then materializes its guarded boot-ELF hooks. The
resident-relocation gate below records the integrated worker result.

## 2026-07-28 accepted Ninja Song numeric C migration

The accepted Ninja Song formatter contract can also be expressed in ordinary
EE C without changing its five BTL callers or public payload symbol. The
native call sites supply the numeric value in `a1`, requested width in `a2`,
destination in `a3`, and padding mode as the fifth EE EABI integer argument in
`t0`. Compiled disassembly confirms the C entry saves those live values before
calling its only external dependency.

The sole retained assembly fragment is a 20-byte ABI bridge for NA2's native
variadic formatter: it moves the C callback's value from `a1` to `a2`, loads
the immutable ASCII `%d` string at `0x006042D3` into `a1`, and tail-calls
`sprintf` at `0x0017BCA0`. The 184-byte C fragment plus this bridge produce a
204-byte numeric asset with SHA-256
`8043B1393F6D901FC91DF6BB4BFC8AB4D2800F7FD9E17CA4EEE2C4C34992A9F6`.
The prior 188-byte handwritten implementation is superseded as executable
input but remains recoverable from Git history.

Static confidence is high: the compiler emits one explicit relocation to the
bridge; its 16-byte decimal buffer is disjoint from the saved-register area;
the accepted space, no-padding, and zero-padding modes are retained; and the
native decimal length remains the public return value. The normal build
promoted Current CRC `12369A62`; the user manually checked the supplied Ninja
Song ss2–ss5 screens and reported that the result is good. Unit tests
were updated only after that acceptance.

This migration does not cover the separately accepted Save/Load date/time and
Battle Settings Time ASCII conversions. Those remain guarded in-place MIPS
instruction patches generated by their dedicated scripts. They are not
standalone resident helpers, but they do encode behavior; therefore the final
structural C cleanup must not classify them as migrated or remove their
generators without an explicit decision.

## 2026-07-30 Battle Settings Jutsu-row renderer

The replacement ss3–ss6 batch isolates one Jutsu-selector caller family. Its
source identities are NA2 `PRG/BTL.BIN` SHA-256
`56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C`
and NUN5 `PRG/BTL.BIN` SHA-256
`7E8518DA7BD4957AF18CB0ABABE67F0E9B37C42C6551375201B15997F0A3DFE3`.
The supplied visible ss5 and ss6 states restore with the selector objects
already constructed, and the final row draw executes after either state
resumes. They therefore validate this draw-time caller directly with no game
input. The user also supplied the exact constructor sequence ss3, Cross, ss4,
Circle, ss5, Cross, ss6, but it was not required for the bounded runtime pass;
ss3 and ss4 are precursors rather than separate defects.

NA2 row compositor `FUN_006BCB70` sets a point and calls the ordinary text
renderer directly. The exact call is BTL file `0x90DC`, Ghidra
`0x006BCF9C`, live MWo3 `0x006BCFDC`, guarded by
`5020060C00000000` (`jal 0x00188140`; NOP). Its left-side point is
`(30 + f21, 16 + f20)` and its right-side point is
`(310 - f21, 16 + f20)`. This path has no width, line-count, or wrapping
contract, which explains why long translated names remain on one line and
overflow.

The initially recorded file offset `0x9178` was wrong: clean BTL bytes there
are unrelated pointer setup, so normal profile composition correctly rejected
the conflicting guard. The preserved export maps Ghidra `0x006BCF9C` to clean
BTL file `0x90DC`; the live `+0x40` relocation affects the runtime address,
not that file offset.

An earlier uncommitted experiment intercepted three presumed Jutsu
constructor/list families independently through
`font_v2_jutsu_primary_entry`, `font_v2_jutsu_secondary_entry`, and
`font_v2_jutsu_list_entry`, with guessed 208-unit wrapping and separate
128-unit boxes. It was rejected and is not retained: those wrappers did not
own the final visible ss5/ss6 text draw. The exact row-compositor call above
supersedes all three and is the only hook required for this defect.

NUN5 homolog `FUN_006CFE70` replaces that direct draw with
`FUN_00389EA0` at Ghidra `0x006D02DC`. It passes a `186 x 32` box, line
limit `2`, horizontal policy `0`, vertical policy `1`, and wrapping mode `1`.
Relative to the NA2 native point, its box origin is X `-7` on the left, X
`-4` on the right, and Y `-10` on both sides. The callee copies the text,
wraps it to the requested width and line limit, and then delegates to
`FUN_0018B1B0`; that final renderer applies start-horizontal and
center-vertical placement and advances once per produced line.

The bounded C implementation hooks only live `0x006BCFDC`, copies the source
into a 256-byte stack buffer, and measures/wraps that copy at 186 units and two
lines. The first fresh candidate proved the caller isolation:
`Naruto Uzumaki Combo Attack` became `Naruto Uzumaki` / `Combo Attack`, but
relying on the shared newline hook produced an 18-pixel row step instead of
NUN5's 20. The corrected callback owns both line draws directly; a 16-unit
game-space Y step produces the exact 20-pixel NUN5 step at 640x480.

The remaining vertical overflow was glyph-quad geometry rather than line
spacing. Setting the secondary descriptor or renderer mode before
`FUN_00188140` was ineffective because that draw path resets the selector
before the per-glyph emitter. The existing layout-session right-edge shim at
ELF file `0x88070`, runtime `0x00187F70`, is the correct bounded boundary.
Session flag `0x40` makes only a selected caller take its bottom edge from
`FontV2Session.glyph_height`. A 2026-07-30 differential check exposed that the
first flag-aware shim did not actually preserve the intended native path: its
conditional branch placed the session `glyph_height` load in the MIPS delay
slot, so that load executed even when flag `0x40` was clear. The corrected shim
leaves a NOP in that delay slot and loads `glyph_height` only after the branch
falls through. Every session without the flag now retains the displaced native
bottom edge and continues at `0x00187F78` through the accepted
primary/secondary helper.
The flagged path rejoins at `0x00187F80` and preserves displaced delay-slot
word `0x8F84CA6C` (`lw a0,-0x3594(gp)`). Omitting that load makes the row text
disappear, which was a useful rejected transport result rather than a renderer
hypothesis.

The replacement ss1–ss2 evidence supplied on 2026-07-31 established the
selective-wrap boundary and the 16-unit wrapped-line interval. Those historical
captures led through a `0.96` scale and `-6.5` Y candidate, but the 2026-08-02
overhaul superseded those constants. That accepted family measured before
drawing and published scale `1.0` for both branches. Fitting rows used the
native glyph path through a session with X offsets `-5.6` on the left and
`-4.0` on the right plus one-line Y offset `-1.6`; wrapped rows used Y offset
`-5.7`, glyph height `22.0`, and the retained 16-unit line interval. Only
measured overflow selected that multiline branch, preserving the verified
`Explosive Destruction` / `Formation` break without vertically collapsing
fitting labels.

The user verified the final whole-Font hot-reloaded Jutsu selector on
2026-07-31, including fitting one-line and wrapped two-line rows. Canonical
fragment reconstruction passed afterward. Confidence is high for this caller
family; this verification establishes the live displayed result and does not
claim a separate integrated-ISO runtime pass.

### 2026-08-22 Jutsus E2E alignment candidate

The maintained three-page Jutsus replay exposed residual origin differences
in that otherwise accepted family. Before correction, the measured title starts
were one output pixel right of NUN5; fitting one-line rows were three output
pixels low and wrapped rows were one output pixel low. The shared family now
uses left X `-6.4`, right X `-4.0`, fitting-row Y `-4.0`, and wrapped-block Y
`-6.5`. The `186 x 32` box, two-line limit, 16-unit wrapped-line interval, and
wrapped glyph height `22.0` remain unchanged, preserving the intentional
non-collapsed font height.

The first alignment replay incorrectly retained fixed horizontal scale `1.0`.
That bypassed the existing shrink contract after `font_v2_wrap_retry` widened
its threshold to keep an overflowing title within two lines. Page 01 therefore
still rendered long two-line rows too wide. The corrected adapter uses
`FONT_V2_FLAG_SHRINK_X` for both branches: fitting rows retain scale `1.0`,
while any measured line wider than `186` uses `186 / measured_width`. This is
the shared boxed-renderer behavior, not a string-specific scale or coordinate.

The corrected `na228 e2e jutsus` replay completed successfully and regenerated
exactly the 12 Jutsus screenshot, pair, blend, and diff pages. Across all three
pages, fitting and wrapped rows retain NUN5's starts, line bands, and line
breaks. On page 01, `Earth Style: Gushing Rock` changed from 239 output pixels
to NUN5's 223, `Explosive Destruction` changed from 240 to NUN5's 229, and the
short fitting rows remained unscaled. The remaining title pixels in the diff
grids are the intentional taller glyph raster and shading. The user visually
approved this corrected result and accepted it through `ver` on 2026-08-22.

## 2026-07-31 Settings and Ninja Song page templates

The matched Font 3 ss1–ss3 batch uses NUN5, not NUN6, as the layout reference.
The Settings screens are loop-rendered page templates rather than collections
of unique rows. Battle Settings uses one label call at BTL file `0x1CC368` and
two native value branches at `0x1CC424` and `0x1CC598`; Practice Settings uses
one heading call at `0x1CE528`, one label call at `0x1CE56C`, and one value call
at `0x1CE5D4`. The guarded redirects therefore cover every row emitted by each
loop without identifying any translated string or visible row.

Direct donor verification corrected the compact-value theory. NUN5 BTL's
header records load base `0x006C6D00`, placing `FUN_0089CBD0` at file
`0x1D5ED0`. Its ordinary Battle values call boxed renderer `FUN_00389DF0`
with X `304`, width `104`, one line, and centered horizontal placement.
Practice values make the same X `304`, width `104` call at `0x0089ECA8`.
The special Battle time branch is the relevant renderer difference: NUN5 sets
the ASCII-font bit for value 100 and clears it for ordinary decimal values,
whereas NA2 clears the bit for both branches before the shared draw.

The shared Settings value adapter therefore keeps every value inside the one
104-unit box; the rejected 79-unit fit and character-indexed advance override
are removed. When Current reaches the adapter with the ASCII-font bit clear
and a nonnumeric value, the adapter temporarily selects the same ASCII mode
used by NUN5, applies one `-1.0` local-unit raster-phase correction, draws, and
restores the exact incoming renderer byte. Digit-leading values retain the
ordinary native mode but use one numeric session formula: horizontal scale
`1.02`, glyph height `26.0`, X offset `1.8`, and Y offset `1.875`. This
compensates for the already accepted ASCII formatter's glyph geometry without
changing its bytes. A value containing an ASCII space retains the separately
accepted descriptive-phrase fit. Battle and Practice labels retain separate
page baselines plus one shared selected-state offset. These are page/state and
value-class formulas, not per-row coordinates or visible-string identities.

Ninja Song arithmetic is likewise one function-level redirect, not a set of
token or row hooks. NA2 `FUN_00718920` is replaced from BTL file `0x64A60` by
one call to `font_v2_ninja_arithmetic_template`; the template reads the native
12-byte row record and renders all fifteen entries. The full table confirms
three structural outputs: expanded arithmetic, total-only, and N/A. NA2 carries
the total-only routing through its existing indices `9`, `10`, and `13`; the
replacement preserves that routing instead of creating row patches.

Fresh hidden-worker ss1–ss3 injection runs proved the Settings loops and the
continuously redrawn Ninja formulas. At 640x480, the final Practice phrase and
heading bounds match NUN5 exactly; short Settings values also match, and the
remaining ordinary-label differences are at most one raster pixel. Fresh ss1
capture `20260731224409` isolates the corrected Battle mode. Across four
neutral-ink thresholds, every one of the nine glyph starts differs from NUN5
by no more than `0.56` output pixel. At threshold 128, NUN5 bounds are
`(396,105)-(491,117)` and the normalized current bounds are
`(396.00,104.44)-(491.56,117.78)`, covering horizontal and vertical position
as well as width. Fresh ss2 capture `20260731224508` has zero changed pixels
against accepted capture `20260731205126` in the descriptive phrase and all
five visible short-value text regions. The user accepted that Practice result
and the special Battle value before supplying the additional numeric case.

The supplemental slot-1 pair saved at `23:02` uses Current CRC `2DA70D8F`
against NUN5 CRC `C071D4C1`, with state SHA-256 values
`7B853DCB30B142B78374208426138AEF12FEF5DF895465E141B1B569CD3E54AE`
and `FC9978C8946E8E71055197FC202ED784ABFFADA365B05E0E0EA3F246207485CE`.
Both display Battle Time `10`. Before the numeric formula, Current's
threshold-128 ink occupied `(432,104)-(455,114)` while NUN5 occupied
`(433,105)-(457,117)`. Fresh guarded capture `20260731233506`, normalized to
640x480, matches NUN5 bounds `(433,105)-(457,117)` at thresholds 96 and 128.
The four nonnumeric values on the same page retain their exact pre-change
bounds and occupied columns at both thresholds. This supersedes the rejected
numeric ASCII-mode switch, which matched height but compressed the two-digit
span from 25 pixels to 18. The user verified the exact supplemental
Time 10 result on 2026-07-31; the Settings row family is runtime-proven.

The maintained 2026-08-22 Ninja Song E2E run supersedes the earlier incomplete
objective evidence. NUN5 `FUN_0072E5B0` at BTL file `0x678F0` proves the
expanded expression geometry: factor X offsets `30`, `90`, and `120`; unit
resource box `(176,-6,52,32)`; equals X `226`; and total box
`(256,0,64,20)`. Its descriptor selects the localized unit resource with
`unit_index + 4`. The NA2 template maps descriptor unit `2` to the proven
`timer counts` text, suppresses descriptor unit `4` where NUN5 draws no `%`,
left-aligns both timer lines in the donor box, and preserves the three native
output classes. Totals strip formatter padding and use one right-edge formula,
so the captured `1`, `100`, and `150` end at the same donor column.

The objective boundary is the complete visible row block at NA2 BTL file
`0x64630`, not the earlier detail-only call at `0x64E98`. One adapter positions
the existing red index, one-byte marker, and prose independently. NUN5's
homologous draw uses index X `80`, prose X `112`, prose Y `rowY - 6`, and a
`320 x 32` two-line box. Current retains the intentional taller ASCII raster
through local Y-phase compensation but uses the same `320`-unit wrap and box
width. The maintained grid proves the donor breaks after `Extra Hit`, keeps
objectives 14 and 16 on one line, and uses no prefixed or substituted prose.

The post-objective bonus fields are a third data-driven family. NA2
`FUN_00718C60` at BTL file `0x64DA0` and NUN5 `FUN_0072E9C0` both consume the
native 12-byte row selected after the fight; different results can therefore
display different strings at different vertical positions. One function-level
replacement reads that row, formats its descriptor, and applies NUN5's shared
`288 x 32` two-line label box and `96 x 20` right-aligned total box. Rows 17,
18, 22, 25, 26, and 27 insert the row's unpadded inline number into the label;
the remaining rows format their descriptor directly. The total strips native
left padding and includes BODY's two-unit inter-digit advance in its measured
width, so every digit count uses the same right edge. No bonus string, row
index, or captured Y position selects a layout correction.

The integrated E2E run executed the current payload and produced all five
planned Ninja Song states. Objective anchors, N/A rows, arithmetic columns,
unit-label structure, and total right edges are runtime-proven. The accepted
tracked reference and current grids use the same E2E memory-card configuration
and synchronized deterministic markers. Diagnostic savestates established the
matching runtime row origins only; their embedded screenshots were not used as
visual-parity evidence.

The maintained replay visibly exercises T88 `2 items carried bonus` and T2194
`100% Health bonus`. Their label spans match NUN5 exactly; their two- and
three-digit totals both end at output X `508`. Other fight-dependent bonus
strings are not granted E2E translation coverage, but they execute the same
row-driven renderer and geometry. Remaining pixel differences are the
intentional taller glyph raster and shading plus the animated panel/title
phase. The user visually accepted the complete result through `ver` on
2026-08-22.
