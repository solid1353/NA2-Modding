# UI translation layout patches

This patch set holds size-preserving executable changes that are inseparable from
the NUN5 UI container import but do not belong inside `DATA.CVM`.

Its 108 guarded edits are donor-first: 63 copy bytes directly from canonical
NUN5 files (44 from the ELF, 14 from `BTL.BIN`, and five from `ETC.BIN`).
Another 24 store the exact values of NUN5's stage-width formula in NA2's
different inline-record layout. The remaining 21 are documented NA2-specific
ports where the equivalent NUN5 behavior has a different instruction or data
topology, or where NA2 intentionally needs a different value.

## ui_layout_ultimate_jutsu_label: one-part OUGI label

NA2's Ultimate Jutsu banner uses two 64x64 label halves. The official English
NUN5 and Brazilian NUN6 versions both use one 128x64 label and one-part
construction behavior. The whole-container `OUGI.CCS` import supplies that
one-part model, UV, texture, and animation layout.

At BTL file offset `0xB5E80`, NA2 contains `02 00 42 2A`
(`slti v0,s2,2`). `ui_layout_ultimate_jutsu_label` replaces it with `01 00 42 2A`
(`slti v0,s2,1`) to port the donor's one-part behavior into NA2's loop. The
canonical NUN5 ELF, BTL, ETC, and ADV files do not contain that exact four-byte
instruction, so this row correctly remains an authored semantic port rather
than claiming an arbitrary donor copy. It preserves the file size and is
runtime-proven with the imported one-part container.

The executable definition is
`catalog.json -> localization -> ui_layout -> ui_layout_ultimate_jutsu_label`.
Catalog loading validates its operation contract; normal configuration
composition verifies its target identity and destination guard.

Evidence and the broader container/layout analysis are recorded in
`docs/workstreams/ui_translation/context.md`.

## ui_layout_stage_select: localized stage-name rectangles and width fitting

NA2 and NUN5 store the same 24 `(stage_id, index)` pairs in the same order:

- NA2 BTL file offset `0x20FC10`: 24 records of 16 bytes, with an inline
  `(u, v, width, height)` rectangle after the two key words;
- NUN5 BTL file offset `0x215680`: 24 records of 8 bytes containing the two
  matching key words.

NUN5 obtains the localized rectangle separately through `FUN_003d4120`. Its
English language table is the 24-entry rectangle range at NUN5 ELF file offset
`0x4DDB90`. The NUN5 draw path also fits names wider than 214 pixels with
`min(1.0, 214.0 / width)`; copying only the rectangles would therefore preserve
the clipping visible in NA2.

`ui_layout_stage_select` reproduces the localized behavior without adding a jump or
overwriting a code cave. In the NA2 table, every second key word is exactly the
matched loop index. The selected-preview consumer at BTL file offset `0x606BC`
changes from loading that redundant word to `move s0,s1`. The small-thumbnail
consumer at `0x603B8` instead recovers the same index from the existing
`row * 16` byte offset with `srl a0,v1,4`. The freed word in each record stores
the precomputed single-precision NUN5 scale.

The original stage-name code initialized both axes to `1.0` by loading `f14`
and copying it to `f15`. At BTL file offset `0x61570`, the `mtc1` destination
changes from `f14` to `f15` so vertical scale stays at `1.0`; at `0x6157C`,
the former `mov.s f15,f14` becomes `lwc1 f14,4(v1)` so only horizontal scale
receives the precomputed fit. The remaining 24 rectangle fields are copied from
the hash-pinned NUN5 ELF table. Finally, the Random prompt and its companion
sprite at `0x61F40` and `0x61F64` copy NUN5's exact X=`260` instructions in
place of NA2's X=`300` instructions. NUN5 positions OK and Back at effective
X=`388`/`462` by applying regional `-12`/`-8` offsets to nominal
X=`400`/`470`. NA2 lacks those additions, and the NUN5 global loads are not
ABI-compatible with NA2, so two guarded same-register constants at
`0x61EF8`/`0x61F1C` reproduce the effective donor behavior.

The patch is 56 individually guarded edits: 24 rectangle rows copy NUN5's
English ELF table, 24 scale rows store the exact result of NUN5's width formula,
two rows copy NUN5's Random-position instructions, two rows adapt the effective
NUN5 OK/Back anchors, and four code rows adapt NA2's inline-record topology. A
temporary application verified that all 24
stage keys remain unchanged and match NUN5, every rectangle equals the official
English table, every scale equals the NUN5 formula, all changed bytes stay
inside declared ranges, and the 2,237,184-byte BTL size is unchanged. The user
then compared the integrated Slot 3 result with NUN5 and accepted Stage Select
as fixed, promoting `ui_layout_stage_select` to `runtime_proven`. A later guarded paired
Slot 5 capture proves the added OK/Back anchors match the NUN5 footer.

## ui_layout_character_name_rectangles: localized character-name atlas rectangles

The character-name renderers do not obtain their rectangles from
`CHARSEL1.CCS`. NA2 `FUN_0037d410` reads one 96-entry table at EE `0x005D4E70`
(ELF file offset `0x4D4F70`). NUN5's corresponding name helper
`FUN_0038c350` calls localized accessor `FUN_003d45d0`; language index zero in
the accessor's pointer table resolves to the official English range at EE
`0x005DDC50` (ELF file offset `0x4DDDD0`).

Each record is four signed 16-bit values `(u, v, width, height)`. Forty-four of
the 96 English records already match NA2; the other 52 change widths,
coordinates, or blank sentinels to match the imported English name atlases.
Copying the complete 768-byte English range is the minimal complete fix shared
by Character Select, VS, the battle HUD, and Battle Set. The edit is range-hash
guarded at both source and destination and preserves the ELF size.

The nearby NUN5 `FUN_0038c3a0` range at file offset `0x4DC120` is deliberately
not used. It is the separate uniform 38x46 character-portrait grid consumed by
NUN5's counterpart of NA2 `FUN_0037d470`. An earlier test build copied that
range and produced the stacked name fragments captured at runtime; the
localized accessor and call-site pairs disprove that source selection.

## ui_layout_options_labels: localized Options label rectangles

Importing the complete NUN5 `OPTION.CCS` is not sufficient by itself. The main
Options renderer supplies atlas rectangles from the boot ELF:

- NA2 `FUN_0038c160` reads five menu-label records at EE `0x005D52E0` and
  six difficulty-label records at EE `0x005D5310`;
- NUN5 `FUN_0039dba0` obtains the homologous English records through
  `FUN_003d43a0` and `FUN_003d43f0`, whose English tables begin at EE
  `0x005DDB90` and `0x005DDBC0`.

Both renderers use the same five screen positions and `0.9` scales. Their arrow
rectangle is also byte-identical. The remaining difference is the 96-byte
rectangle block: five menu labels, an eight-byte zero separator, and six
difficulty labels. `ui_layout_options_labels` copies that complete official English block from
NUN5 ELF file offset `0x4DDD10` to NA2 ELF file offset `0x4D53E0`. Source and
destination ranges are hash guarded and the ELF size is preserved.

## ui_layout_difficulty_sprite: difficulty-value sprite routing

The NUN5 rectangles alone fix the five main Options labels, but the widest
difficulty value still fragments unless it is drawn through the same alternate
sprite object used by NUN5. The homologous renderers differ in one predicate:

- NA2 `FUN_0038c160` selects the alternate object for indices `0` and `5`;
- NUN5 `FUN_0039dba0` selects it for indices `0`, `4`, and `5`.

At NA2 EE `0x0038C30C` (ELF file offset `0x28C40C`), `ui_layout_difficulty_sprite`
replaces the existing `index == 5` test with `index >= 4`, while retaining the
following `index == 0` test. For the renderer's proven valid domain `0..5`, the
resulting set is exactly `{0, 4, 5}`. The edit changes two instructions, keeps
the original branch targets and delay slots, and preserves the ELF size.

A paused, identity-checked PINE write matched the two original words exactly
and verified the eight-byte readback. After one redraw, the corrupt selected
value became a clean centered `INSANE`; captures of `HARD`, `EASY`, and
`SIMPLE` also rendered cleanly, including both arrow endpoints.

## ui_layout_practice_settings_prompt: localized Practice Settings prompt layout

The VS-screen Practice Settings prompt needs both the English atlas rectangle
and the localized horizontal anchor. The corresponding renderers provide exact
cross-build evidence:

- NA2 `FUN_006c0cc0` uses the static rectangle `(1, 281, 112, 22)` at BTL
  file offset `0x20C9D8` and passes X=`60.0` at file offset `0xCFA0`;
- NUN5 `FUN_006d4170` calls localized accessor `FUN_003d46c0`, whose English
  table resolves to ELF file offset `0x4DE0E0`, and passes X=`100.0`.

`ui_layout_practice_settings_prompt` copies the official NUN5 rectangle `(0, 280, 176, 24)` from its
ELF and copies the structurally equivalent `lui v0,0x42c8` instruction from
NUN5 BTL file offset `0xD500`. Both edits are exactly guarded, preserve BTL
size, and remain confined to the Practice Settings path.

The two edits were applied to a paused Current runtime and read back exactly.
After one redraw, the sprite object reported X=`276`, Y=`356`, size `176x24`,
and UV `(0,280)`. The archived screenshot shows the full label and Square icon
at the same bottom-left position as the NUN5 target.

## ui_layout_vs_confirmation: localized VS confirmation labels, inputs, and prompts

The battle-confirmation Customize screen retains Japanese regional rectangle
tables even after importing the NUN5 VS texture container. `ui_layout_vs_confirmation` copies
the exact English NUN5 rectangles for:

- `Customize Jutsu` and its Circle prompt;
- `Battle Settings` and its Square prompt;
- the two-arrow control;
- all three Jutsu input glyphs;
- the one-part `Jutsu1` and `Jutsu2` labels.

NUN5's Jutsu helper offsets its 62x26 label by 26 pixels and the three input
glyphs by 40 pixels. NA2's static draw path lacks those additions. A 16-byte
NA2 helper is installed in verified loaded zero padding at BTL file offset
`0x30`, the label path calls it at `0x9188`, and the two structurally equivalent
40-pixel accumulator instructions are copied from NUN5 BTL offsets `0x974C`
and `0x9750` into `0x91BC..0x91C3`. The localized 160x24 Battle Settings prompt
is drawn at the official X=`94` through the constant at `0xCFD8`.

NUN5 passes X=`260` for `Customize Jutsu`. The final guarded test proves that
this exact value is valid once the open-selector state is corrected: the full
Circle prompt remains on-screen and matches NUN5. `ui_layout_vs_confirmation` therefore copies
only the X-immediate halfword from NUN5 BTL `0xD6A8` into NA2 `0xCF70`, keeping
NA2's required `v0` destination register rather than copying an incompatible
whole instruction.

The bottom legends use a separate boot-ELF table. NUN5 ELF `0x4DE9F0` contains
complete Cross/OK `(1,1,56,22)` and Triangle/Back `(1,25,64,22)` records; NA2
ELF `0x4D4790` contains two 70x22 regional records and its BTL wrapper draws an
additional glyph. The patch copies the complete 16-byte NUN5 table and disables
the redundant NA2 glyph arguments at BTL `0xD014` and `0xD038`.

Because NA2 and NUN5 advance that shared sprite differently, identical nominal
anchors do not produce identical raster positions. Two paired calibration runs
located the exact NA2-compatible constants: `400/470` rendered 15/10 pixels
right of NUN5, while `384/460` rendered 5/3 pixels left. NA2 `388/462`, written
at `0xCFFC` and `0xD020`, aligns both legends at `dx=0,dy=0`.

All 19 edits are byte-guarded. The final hidden, muted isolated run preserved
both Jutsu labels, the two-arrow and Circle controls, the full bottom prompts,
and the accepted open-selector arrows. The user accepted the NUN5-first paired
screen as perfect.

The earlier submenu-suppression wrapper remains rejected: NUN5 retains the
Jutsu1/Jutsu2 graphics beneath the open selector, while suppression removed
them and exposed unrelated atlas data. No such hook is retained.

This patch changes texture selection, placement, and submenu visibility only.
It does not change or evaluate command-name text or font rendering.

## ui_layout_round_label: localized Round label layout

NA2 constructs `Round` from two Japanese 38x38 glyph rectangles at X=`216`,
Y=`44`, and scale `1.4`. NUN5 uses one English 94x30 rectangle at X=`256`,
Y=`24`, with scale `1.2` and a Y=`64` render constant.

`ui_layout_round_label` copies the exact NUN5 rectangle from ELF file offset `0x4DE110`,
zeros the unused second-glyph record, ports the differently stored X/Y fields,
and copies the four structurally equivalent scale/render instruction ranges
from NUN5 BTL into NA2 offsets `0xCCB4`, `0xCD5C`, `0xCD64`, and `0xCDA4`.
Eight guarded live writes were read back exactly. The resulting one-part label
matches the paired NUN5 capture; small frame-to-frame outline differences are
the screen's normal pulsation.

## ui_layout_jutsu_selector_arrows: localized open Jutsu-selector arrows

The open Jutsu selector is a separate state from the accepted closed
confirmation screen. NA2 `FUN_006bd4d0` incorrectly retains the two horizontal
draw calls used by its closed-state sibling and draws its green-arrow record
without rotation. NUN5 homolog `FUN_006d0850` omits both horizontal draws,
loads `+pi/2` and `-pi/2` for the upper and lower indicators, and clears the
sprite rotation after each draw.

The whole NUN5 VS texture import makes NA2's old `(139,257,38,22)` source
rectangle invalid: it samples lettering rather than the Japanese atlas's
downward triangle. Guarded live testing first copied NUN5's official
`(145,385,22,38)` right-facing source and wrote the exact NUN5 `+pi/2` and
`-pi/2` values into NA2's live sprite object. The rotation field read back
exactly, but both rendered arrows still pointed right. Persistent and
draw-scoped control-field transplants either had no effect or corrupted the
sprite, proving that this NA2 draw path does not consume NUN5's rotation mode.

The accepted correction keeps `VS.CCS` as a byte-for-byte whole NUN5 donor and
scopes the compatibility state to each arrow draw. BTL `0x9ABC..0x9B23`, which
held the unwanted horizontal blocks, now contains a branch plus a compact
helper; normal execution resumes at `0x9B38`, so the helper consumes no shared
header cave. The helper enables NA2 sprite mode 1, applies the lower flip when
the copied NUN5 angle is negative, draws the localized record, flushes while
mode 1 remains active, and then restores mode 0.

The four angle words and `(145,385,22,38)` rectangle are exact NUN5 copies.
Only the helper and its two call redirects are authored NA2-specific glue,
because leaving NUN5 mode state active damages unrelated objects and restoring
it before the flush discards the queued primitive. The final isolated capture
has matching upper/lower arrows, no horizontal arrows, no bottom fragment, and
no collateral label changes. The user accepted the paired result as perfect;
confidence and runtime status are verified. No label text, command text, font,
or gameplay-input data is changed.

## ui_layout_command_scroll_arrows: localized command-list scroll arrows

Command Menu and Command Chart share the same scroll-indicator draw method:
NA2 `FUN_00878820` and NUN5 `FUN_00894f60`. Both render one `TEX_xselect`
record twice, rotating the first draw by pi for the opposite direction. Paired
Slots 5 and 6 reuse the same sprite object, so their green-garbage defect has
one data root rather than two independent layouts.

NA2 BTL offset `0x21D648` selects `(194,195,20,20)`, which samples green text
fragments from the imported NUN5 atlas. `ui_layout_command_scroll_arrows` copies the exact NUN5 BTL
record `(1,225,20,22)` from `0x2214D8`, selecting the orange vertical-scroll
triangle. The existing positions and pulse are retained; small capture-to-
capture Y differences remain normal animation. The user verified the integrated
Current build on both Command Menu and Command Chart and accepted both screens
as good, promoting the shared correction to runtime-proven/verified.

Detailed function, address, side-effect, and negative-result evidence for both
patches is preserved in `docs/knowledge/localization/ui/battle.md`.

## ui_layout_item_status_paired: localized paired item-status labels

Paired item effects use two foreground rows, a shared bubble, and a three-rank
offset table. `ui_layout_item_status_paired` copies the official NUN5 records `0x8E..0x94` and
`0x9B..0x9C` plus the complete rank table. The remaining writes are an
NA2-specific ABI port: they add anisotropic sprite scaling, preserve NA2's
object layout, and reproduce the donor width normalization, centering, row
spacing, rotation, clamp, and common origin.

The patch was reconstructed from homologous boot-ELF and BTL functions and
validated against the accepted paired item checkpoint. Controller, foreground
labels, and white-bubble bounds match NUN5; a one-pixel top-edge difference is
normal pulse timing. Numeric, single, and fixed-status layouts are separate
classes. The pair helper now exposes explicit caller-owned anchor, row, and
angle-output arguments so the bounded numeric port can reuse it without
changing the pair result.

The same resident sprite renderer also owns the transition geometry used by
all four item classes. Its first NA2 port correctly preserved the NUN5 scale in
`f22` and alpha in `f21`, but the final centered-offset calculation still
negated `f21`. At partial alpha, that scaled each local half-width/half-height
offset and made the foreground appear to slide into and out of a stationary
bubble. `ui_layout_item_status_paired_27` copies NUN5's exact `neg.s f2,f22` instruction from
ELF file `0x284418` to NA2 file `0x2772F4`. Alpha continues to fade normally,
while local geometry remains constant; fully visible placement is unchanged.

## ui_layout_item_status_numeric: localized numeric item-status labels

Numeric item effects share one class for Health, Chakra, Recovery, and their
one-, two-, and three-digit values. `ui_layout_item_status_numeric` copies the complete official
NUN5 records `0x81`, `0x82`, and `0x8D`, then routes the NA2 numeric top and
lower label callers through the ABI-safe item helper with the donor anchors and
rotation behavior.

The six digit-position writes are an NA2-specific coordinate port, not literal
donor copies. NUN5 establishes a negative-50 X origin and adds
`14/23/32`, `18/28`, or `24`; the NA2 helper already represents that origin,
so the equivalent local constants are `-36/-27/-18`, `-32/-22`, and `-26`.
Literal NUN5 instructions would apply the origin twice. The final numeric Slot
3 checkpoint matches Health, Chakra, and Recovery against NUN5, while the
settled paired Slot 7 regression remains intact.

Detailed function boundaries, file/runtime mappings, reconstructed behavior,
side effects, evidence, and the rejected whole-function donor transplant are
preserved in `docs/knowledge/localization/ui/battle.md`.

## ui_layout_item_status_single: localized single item-status labels

Single item effects use one foreground label and the same common bubble
controller as the paired and numeric classes. `ui_layout_item_status_single` copies the complete
official NUN5 records `0x96..0x9A`. The object-code-to-record tables are already
identical in NA2 and NUN5, so no mapping data is authored or duplicated.

The remaining changes are a bounded NA2 ABI port. They replace NA2's regional
`(+33,+42)` foreground origin with NUN5's `(0,+33)` origin and set the
quarter-turn after resource lookup only for donor records `0x82` and `0x99`.
The homologous NA2 wrapper is retained; calling its lower renderer directly was
rejected because that uses a different argument contract. The shared scale
helper retains the accepted pair path while assigning the traced NUN5 single
scales: `1.90625` for code `0x09` and `1.0` for every other single label.

Paired Slot 10 proves simultaneous `Invisible` and `Substitution Jutsu`
placement. Slot 12 proves the same implementation for poison/status effects.
Both match NUN5 bubble bounds, label centers, and clipping at 640x480; remaining
differences are battle animation timing. Record `0x99` was not present in the
captured set, so its branch is statically verified from both complete draw
functions and the patch is runtime-proven with high confidence rather than
marked verified.

## ui_layout_item_status_fixed: localized fixed item-status labels

The fixed two-label item class always draws records `0x8E` and `0x8D`. Those
official rectangles are already supplied by the donor-backed paired and numeric
item patches, so this patch adds no texture data or duplicate table copy.

NA2 placed the two records with fixed regional offsets `(+38,+11)` and
`(+18,+25)`. NUN5 centers each record from its live rectangle width and uses Y
offsets `+20` and `+37`. `ui_layout_item_status_fixed` routes both NA2 draw sites through the
existing runtime-proven shared item-width helper, with zero X bias and local Y
biases `+2` and `+17` over that helper's established `+18/+20` row bases. The
fixed renderer ignores the helper's angle output, preserving its original
uniform draw path.

A controlled synthetic checkpoint changed the sole paired object in matched
Slot 7 to each game's real fixed-class vtable; the NUN5 object also received its
traced fixed scale. The resulting `Status Effect` / `Recovery` labels have the
same center relative to the white bubble in both games. The remaining whole
object delta is the expected one-frame pulse/update difference. Because the
checkpoint uses a transformed live object rather than a naturally spawned
fixed notification, the runtime-proven patch retains high confidence.

## ui_layout_item_pickup_doll: localized substitution-doll pickup

The battle pickup effect uses the resident `TEX_xselect` sprite pool and both
games retain logical record ID `0x0A` in the matched Slot 4 live object. The
restored NA2 sprite briefly contains record `0x2E` geometry, but the next
per-frame update replaces it from NA2 record `0x0A`. That record's
`(161,193,30,30)` rectangle samples the green `Recovery` label after the NUN5
atlas import. NUN5 record `0x0A` instead uses `(161,225,30,30)` and selects the
doll icon.

`ui_layout_item_pickup_doll` therefore copies the complete official NUN5 record
`0x0A` from ELF file offset `0x4B80C8` over homologous NA2 record `0x0A` at
`0x4B0BD8`. The rejected cross-index copy into NA2 record `0x2E` changed only
the transient restored descriptor and produced no visible change in a fresh
normal build. No renderer, animation, item-selection, or gameplay code changes.

## ui_layout_mash_prompts: localized battle Mash prompt rectangles

The battle prompt object stores its main label ID at `+0x2F` and supplemental
controller-glyph IDs from `+0x30`. NUN5 routes main IDs below seven through a
regional boot-ELF accessor; NA2 directly indexes a Japanese seven-record table
inside `BTL.BIN`. With the NUN5 battle texture already imported, NA2's first
record samples the English Mash artwork vertically and clips it.

`ui_layout_mash_prompts` copies the complete 56-byte official NUN5 English table from boot
ELF offset `0x4DE630` to NA2 BTL offset `0x1DB730`. It is one exact guarded
donor edit: no literal replacement, code hook, object-layout change, or stored
asset is required. A paired guarded savestate test rendered both Mash labels
horizontally at the NUN5 positions.

The adjacent NA2 BTL range at `0x1DB770` is the controller-glyph table, not a
second copy of the main-label table. A rejected live test against that range
left Mash unchanged and corrupted the Cross panels, proving the semantic
boundary. Exact renderer functions, address mappings, object fields, records,
and negative evidence are preserved in
`docs/knowledge/localization/ui/battle.md`.

## ui_layout_victory_names: localized Victory character-name layouts

NA2 and NUN5 use homologous Victory update and draw functions, but their
rectangle-provider ABIs differ. NA2 BTL returns pointers to 24-byte prebuilt
Japanese records. NUN5 BTL selects one of two official frame templates and
fills its width from the localized boot-ELF table. For Naruto, NUN5 atlas
widths `156, 192` become renderer widths `154, 190`; NA2's records contain
`236, 173`.

`ui_layout_victory_names` keeps the NA2 pointer-return ABI and generates all 78 unique
compatible records from the exact NUN5 templates plus each English width minus
the renderer's two-pixel border. Zero-only NUN5 aliases remain untouched, and
all shared-pointer rows agree whenever they provide a nonzero width. Direct
donor copies cannot represent the synthesized records because they do not
exist as final data in NUN5. The generator verifies both ELFs and both BTL
files before updating the guarded replacements; no handwritten placement
permutation or stored binary asset is used.

The resident update, draw, and two-part centering code is instruction-level
equivalent across both games. A stale NA2 savestate resumes into a different
animation phase and texture replacement does not reconstruct its loaded CCS,
so that route is rejected as runtime acceptance. Exact function ranges,
file/runtime mappings, reconstruction, alias evidence, and the remaining
normal-entry runtime requirement are preserved in
`docs/knowledge/localization/ui/victory.md`.

## ui_layout_settings_footers: localized settings footer anchors

The Battle and Practice Settings footers are rendered inside BTL rather than
by the shared resident Options functions. NA2 `FUN_008807a0` and
`FUN_00882250` draw Select at X=`230`, while the homologous NUN5
`FUN_0089d280` and `FUN_0089f130` draw both Select components at X=`200`.
`ui_layout_settings_footers` therefore copies all four exact same-register NUN5 instructions.

NUN5 loads nominal X=`400`/`470` for OK/Back and then adds per-call runtime
offsets `-12`/`-8`. NA2 has no equivalent additions. Copying only the nominal
NUN5 instructions would leave the legends visibly too far right, so the two
NA2 call sites use authored effective anchors X=`388`/`462`. These are the same
NA2-compatible anchors already proven for the analogous confirmation footer.

The eight writes are confined to the two Settings draw functions. Guarded
task-owned slot-6 and slot-10 states rendered Select, OK, and Back at the NUN5
positions without changing the accepted Customize Jutsu footer. Exact function
ranges, file/runtime mappings, reconstructed behavior, and evidence are
preserved in `docs/knowledge/localization/ui/battle.md`.

## ui_layout_battle_results: localized Battle Results summary layout

The whole NUN5 `XNINKA.CCS` import supplies the English Battle Results artwork,
but NA2 retained Japanese result-label rectangles, moving-cloud widths, footer
records, title offset, and rank-stamp geometry. `ui_layout_battle_results` imports the
complete six-record NUN5 result table, paired title/cloud rectangles, Display
Details rectangle, and complete five-cloud motion/geometry table. The five
cloud positions, speeds, and heights were already equal; the NUN5 widths keep
each moving object inside the localized cloud strip instead of traversing
animated `Ninja Song` letters.

The shared five-value rank selector reads the complete NUN5 English rectangle
table installed by `ui_layout_battle_hud_name_rectangles`, while the visible layer samples five
corresponding 44-row cells in the packed `XNINKA.CCS` label column. The earlier
authored centered-renderer replacement and whole-column upward translation
obscured the untouched per-value behavior. At the user's request, both
rank-specific corrections are disabled for matched baseline capture:
`ui_layout_battle_results_11` is absent and `UI-NINKA-001` imports the complete official
NUN5 container with the unmodified donor atlas. Every other Battle Results
layout edit remains active.

The remaining code edits use exact same-register NUN5 instructions where
possible. Display Details Y uses a compact NA2 sequence because the NUN5
language-accessor call cannot be copied, and the shared Next low half is
cleared after importing NUN5's integral anchor. A fresh hidden transition from
task-owned slot 1 proves the moving clouds, labels, footer, and stamp frame
without relying on an already-constructed stale screen. Complete function
ranges, file/runtime mappings, reconstruction, live object fields, side
effects, and negative evidence are preserved in
`docs/knowledge/localization/ui/battle.md`.

## ui_layout_collection_submenu: localized Collection submenu layout

The whole NUN5 `HOME.CCS` import supplies the complete English `Previous Page`
and `Next Page` artwork. NA2 still draws those pixels through two ETC-owned
tables sized for its Japanese atlas: centers X=`100` and X=`220` at Y=`360`,
and two 118x24 source rectangles. NUN5's homologous tables use centers X=`87`
and X=`233` and two 144x24 rectangles. The narrower NA2 rectangle clips
`Previous Page` to `Previous Pa`.

`ui_layout_collection_submenu` copies both complete tables from NUN5: 32 placement bytes from
NUN5 ETC offset `0x281C0` to NA2 offset `0x2E930`, then 16 rectangle bytes from
NUN5 offset `0x29A60` to NA2 offset `0x30A80`. Both page controls remain paired
exactly as the original draw loop expects; no authored replacement bytes or
text/font changes are involved.

The imported NUN5 category titles have a separate mismatch. NA2's Characters
and Movie rectangles are 34 pixels high, crossing into the next 28-pixel NUN5
atlas row, while NA2's Music rectangle begins below the imported English Music
row. The NA2 and NUN5 placement vectors are already identical. Three exact
NUN5 ELF copies therefore replace only the source rectangles:

- Characters: `(1,1,192,34)` -> `(0,0,192,28)` at NA2 ETC `0x30490`;
- Movie: `(1,37,136,34)` -> `(0,28,96,28)` at NA2 ETC `0x30498`;
- Music: `(1,83,80,37)` -> `(0,56,96,28)` at NA2 ETC `0x304A0`.

Movie and Music also expose the common `Play` control. NA2 helper
`FUN_006b44b0` selects `(120,24,72,24)` from ETC offset `0x2E790`; with the
NUN5 HOME atlas this starts 24 pixels before the English control and displays
only `Pl...`. NUN5 homolog `FUN_006c7250` obtains `(144,24,72,24)` through
localized accessor `FUN_003d4210`. The sixth edit copies that exact record from
NUN5 ELF offset `0x4DDC70`. The adjacent Stop record remains unchanged because
it was not visible in the reviewed states.

A later paired character-viewer capture isolates the four lower controls. NA2
places Rotate, Move, Zoom In, and Zoom Out on one row at Y=`360`; NUN5's exact
four-record table places Zoom In/Zoom Out at Y=`339` and Move/Rotate at
Y=`364`. The NUN5 rectangle block also widens both Zoom labels from 108 to 112
pixels and moves Zoom Out to its English-atlas U coordinate. Edits seven and
eight copy the complete 64-byte position block and 32-byte rectangle block
from NUN5 ETC offsets `0x283D0` and `0x29A90` to NA2 ETC offsets `0x2EB40`
and `0x30AB0`. The separate accepted Back path remains untouched.

Static provenance and the draw-path
reconstruction and paired Characters/Movie/Music evidence are recorded in
`docs/knowledge/localization/ui/collection.md`. All eight operations derive bytes from
canonical NUN5 files and preserve ETC size. Runtime acceptance remains pending.

## ui_layout_mode_select: localized Mode Select layout

The whole NUN5 `MODESEL1.CCS` import supplies the English START artwork, but
NA2's static rectangle still selected only `(1,397,206,22)` and drew it at
X=`130`. That truncates the 254-pixel English label visible in preserved slot 1.
NUN5 `FUN_003972e0` obtains rectangle `(1,393,254,26)` from localized accessor
`FUN_003d4bc0` (English table entry at ELF offset `0x4DE318`) and draws it at
X=`150`.

`ui_layout_mode_select` copies that exact eight-byte rectangle into NA2 ELF offset
`0x504710`. The X constant at NA2 offset `0x285F28` is an authored
same-register port from `130` to `150`: the corresponding NUN5 instruction
writes `v1`, while NA2's following instruction consumes `v0`, so copying the
four instruction bytes verbatim would be incorrect.

The same paired slot showed OK and Back shifted right. NUN5 loads nominal
X=`400`/`470` and then applies signed regional offsets `-12`/`-8` before
calling its shared compositor. NA2 has no equivalent additions, so exact donor
loads would preserve the defect. Two additional guarded NA2 constants at ELF
offsets `0x285EE0` and `0x285F04` express the official effective anchors
X=`388`/`462` while retaining NA2's ABI.

All four edits preserve ELF size. A guarded task-owned slot-1 render placed
both prompts within +1 pixel X/Y of NUN5, the normal pulse-phase variance.
The user accepted the final Mode Select footer on 2026-07-26.
The complete function mapping, behavior reconstruction, side effects, and
donor-copy limitation are preserved in
`docs/knowledge/localization/ui/options.md`.

## ui_layout_controls_vibration: localized Controls Vibration-label rectangle

The whole NUN5 `CMN/GAUGE.CCS` import supplies the English `TEX_xmenu`
artwork, but NA2's boot-ELF table still selects the Japanese rectangle
`(1,69,42,22)` at file offset `0x4D53C0`. NUN5's localized table selects
`(64,88,64,20)` at file offset `0x4DEA28`.

`ui_layout_controls_vibration` copies that exact eight-byte NUN5 rectangle into the homologous
NA2 table. It changes only the graphical Vibration label selection; surrounding
OFF/On text and font rendering are outside scope. Both ranges are guarded and
the ELF size is preserved.

## ui_layout_character_select_footer: localized Character Select footer anchors

The complete NUN5 `CHARSEL1.CCS` import already supplies the English
`Select Color` and `Random` artwork. Their screen positions come from the
boot-ELF Character Select footer compositor:

- NA2 `FUN_003bc470` draws `Random` at X=`300` and `Select Color` at X=`160`;
- NUN5 homolog `FUN_003cf0d0` draws the same two records at X=`260` and
  X=`100`.

`ui_layout_character_select_footer` copies the two exact NUN5 `lui v0` instructions into NA2 ELF
offsets `0x2BC600` and `0x2BC624`. Both homologs use `v0` for these calls, so
no register adaptation or authored literal is needed. NUN5 also adds regional
offsets `-12`/`-8` to nominal OK/Back X=`400`/`470`; NA2 issues those separate
calls without the additions. Two authored same-register constants at NA2 ELF
offsets `0x2BC5B8` and `0x2BC5DC` therefore encode the equivalent effective
anchors X=`388`/`462`. Guarded patched copies of the preserved state were
rendered by the task-owned hidden clone: all four footer groups land at the
NUN5 positions within normal one-pixel pulse variance. Exact boundaries,
mappings, reconstruction, and runtime evidence are preserved in
`docs/knowledge/localization/ui/character_select.md`.

## ui_layout_common_prompts: localized shared common prompts

The complete NUN5 `CMN/GAUGE.CCS` import supplies the English common-prompt
artwork, but NA2 `FUN_0037c980` still centers its case-4 Cancel prompt using
three Japanese rectangle widths totaling 182 logical pixels. NUN5 homolog
`FUN_0038bb10` uses localized records 6, 4, and 5 totaling 80 pixels around
the same caller anchor.

`ui_layout_common_prompts` copies those three exact NUN5 records into the corresponding NA2
static slots: the localized Triangle icon, 56-pixel Cancel label, and empty
tail. The shared correction therefore applies to every case-4 common-prompt
caller rather than compensating only the Options screen. A guarded patched
copy of the preserved Options state rendered the final Cancel bounds within
one pixel of NUN5 in both axes, consistent with normal pulse timing.

Battle Results exposed the same shared compositor's record 2: NA2 retained a
70-pixel Next label while NUN5 uses the complete 66-pixel English record.
The fourth edit copies that exact NUN5 record; `ui_layout_battle_results` supplies its NUN5
screen anchor.

The Options-root caller also exposes the same regional footer-anchor difference
already proven on Mode Select and the two Settings screens. NUN5 loads nominal
OK/Back X=`400`/`470` and applies `-12`/`-8` before calling the shared
compositor; NA2 calls it with the unadjusted values. Two authored
same-register ports use the equivalent effective X=`388`/`462` values at NA2
ELF offsets `0x28C878` and `0x28C89C`. A guarded task-owned slot-1 render
matches the NUN5 prompt positions without changing the accepted Cancel
geometry or any text/font behavior.

The Collection state renderer is a separate consumer with a second nominal
Cross/Triangle position table. NA2 `FUN_006c8290` reads X=`380`/`460` from ETC
offsets `0x2F010`/`0x2F018`; NUN5 homolog `FUN_006dbaa0` reads the same nominal
values and applies the same regional `-12`/`-8` offsets before drawing.
Because the donor table itself is byte-identical, two authored ETC adaptations
store the equivalent effective X=`368`/`452` values in NA2. A guarded
task-owned Slot 2 render matches the NUN5 Collection-root footer.

Collection Music uses the different HOME action helper `FUN_006b44b0` and the
nominal table at ETC `0x2E7E0`. NUN5 homolog `FUN_006c7250` applies
state-specific localized geometry: Cross `-12`, width-derived Play `-24`,
Triangle/Back `-8`, and a width-derived Stop layout. Its GP-relative regional
globals and language accessors are not ABI-compatible with NA2, so
`ui_layout_common_prompts` ports the arithmetic through one four-instruction tail-call
wrapper in load-preserved MWO3 header padding. The helper's four compositor
calls use exact deltas `-12`, `-24`, `-8`, and `-2`; the Play and Stop labels
use local X offsets `-59` and `-40`. State 4 also copies the exact NUN5
`(144,48,76,24)` Stop rectangle. A guarded task-owned Slot 3 render matches
the NUN5 Play/Back anchors. A guarded task-owned ss10 render also matches the
NUN5 Triangle/Stop anchor and preserves the matched Cross/Play group; the user
explicitly accepted that final comparison on 2026-07-27. The earlier
Slot 2 failure of this helper remains useful evidence that the two Collection
footer families are distinct, not evidence against the helper's actual HOME
consumers.

Exact mappings, reconstruction, side effects, and runtime evidence are
preserved in `docs/knowledge/localization/ui/options.md`,
`docs/knowledge/localization/ui/collection.md`, and
`docs/knowledge/localization/ui/battle.md`.

## ui_layout_options_footers: shared Controls and Music footer anchors

The complete NUN5 common-UI import supplies the localized Select footer
artwork, but both NA2 Options renderers place the paired Select icon and legend
at X=`230`. Their NUN5 homologs place both calls at X=`200`:

- NA2 Controls `FUN_00388b90` / NUN5 `FUN_0039a450`;
- NA2 Music Options `FUN_0038a1f0` / NUN5 `FUN_0039bb00`.

`ui_layout_options_footers` copies all four exact NUN5 `lui v0,0x4348` anchor instructions
over the corresponding guarded NA2 `lui v0,0x4366` instructions. The broad
correction keeps each icon and legend paired, applies consistently to both
screens, and leaves vertical placement and internal spacing unchanged. Both
renderers also load nominal OK/Back X=`400`/`470` directly while their NUN5
homologs apply the same regional `-12`/`-8` offsets. Two authored
same-register constants in each renderer reproduce the effective donor anchors
X=`388`/`462` without copying ABI-incompatible GP-relative loads. Guarded
task-owned Music and Control Settings states reproduce both complete NUN5
footer placements.
The complete homolog mappings, reconstruction, runtime evidence, and rejected
wrong-table probe are preserved in
`docs/knowledge/localization/ui/options.md`.

All UI companion definitions are direct children of
`catalog.json -> localization -> ui_layout`. Their selection is mirrored under
the same path in each configuration.
