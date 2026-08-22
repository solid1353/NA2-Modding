# Character Select support list

## Scope and source identity

This record covers the scrollable Character Select support roster and the
first-phase implementation that adds **No Support** to it. Battle transition,
Ultimate Jutsu input blocking, and battle-side support UI are separate scopes.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| NA2 `SLPS_258.37` | `5,273,256` | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |
| NUN5 `SLES_556.05` | `5,340,912` | `20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D` |
| NUN6 `SLUS_556.06` | `5,340,912` | `47C40141A3E1AEB0C96BC28E8DC311938B284D54FD21F4D8BA953C2E16234809` |

The user supplied Slot 1 states at the relevant NUN6 and clean-NA2 screens.
Task-owned copies, paired screenshots, and hashes are retained under
`@work/QoL/inputs/savestates` as immutable diagnostic evidence, not build
inputs.

## Native scrollable list

NA2 `FUN_003bb210` populates the actual scrollable support list. It is called
from exactly two sites, at runtime addresses `0x003BB08C` and `0x003BCAB0`.
Both calls are the clean instruction `jal 0x003BB210`, stored at ELF offsets
`0x2BB18C` and `0x2BCBB0` as `84 EC 0E 0C`.

The function reads 33 IDs from runtime `0x005D65C0`, writes the IDs at
Character Select object offset `+0x220`, writes their native availability
states at `+0x248`, and stores the count at `+0x21C`. It then initializes the
remaining slots through index 39 with sentinel ID `0x24` and state `7`, so the
existing list has capacity for 40 entries.

The clean 40-byte table at ELF offset `0x4D66C0` is:

```text
00 01 20 02 03 04 05 06 07 13 14 15 11 10 12 16
08 09 0A 0F 0D 0E 0B 0C 1B 1E 18 19 1A 1F 1C 1D
21 00 00 00 00 00 00 00
```

The first 33 bytes are the visible native roster. NUN5 has the same function,
33-entry bound, and list at its homologous runtime table `0x005DD710`.

## NUN6 additive behavior

NUN6's homologous `FUN_003cde30` uses population bound `0x22` instead of
`0x21`. Its table at runtime `0x005DD710` begins:

```text
25 00 01 20 02 03 04 05 06 07 13 14 15 11 10 12
16 08 09 0A 0F 0D 0E 0B 0C 1B 1E 18 19 1A 1F 1C
1D 21 00 00 00 00 00 00
```

ID `0x25` is prepended at index 0. All 33 NA2/NUN5 IDs remain present,
unchanged and in the same order, at indices 1 through 33. NUN6 therefore adds
one entry; it does not replace a roster item.

NA2 already uses support ID `0x25` for No Support in Story Mode.

## NUN5 Character Select PNACH port

Static analysis on 2026-08-20 mapped the accepted NA2 Character Select
implementation to the verified NUN5 `SLES_556.05`. The main-code ELF mapping
is `runtime = file + 0xFFE80`. The NUN5 native equivalents used by the port are:

| Role | Runtime address |
| --- | ---: |
| Populate support list | `0x003CDE30` |
| Resolve selected character ID | `0x003C7520` |
| Confirm fighter | `0x003C7D50` |
| Draw support cell | `0x0038AD00` |
| Resolve support display ID | `0x008A28A0` |
| Resolve selected support ID | `0x003C77B0` |
| Draw selected support name | `0x003CB640` |
| Set Character Select state | `0x003C80F0` |
| Frame/system pointer slot | `0x00617AFC` |
| Font-renderer pointer slot | `0x00617B70` |
| Set font context | `0x00187AE0` |

The port replaces 18 guarded Character Select sites: six compatibility calls,
two population calls, two fighter-confirmation calls, two state-transition
function entries, four display-ID calls, one support-cell draw, and one
selected-name draw:

| Consumer | Runtime | ELF offset | Clean word |
| --- | ---: | ---: | ---: |
| Default compatibility | `0x003C7A60` | `0x002C7BE0` | `0x0C2289EC` |
| Initial-transition compatibility | `0x003C808C` | `0x002C820C` | `0x0C2289EC` |
| Primary-confirmation compatibility | `0x003C96BC` | `0x002C983C` | `0x0C2289EC` |
| Repeated-confirmation compatibility | `0x003C99DC` | `0x002C9B5C` | `0x0C2289EC` |
| Navigation compatibility | `0x003C9CE8` | `0x002C9E68` | `0x0C2289EC` |
| Draw compatibility | `0x003CB568` | `0x002CB6E8` | `0x0C2289EC` |
| Initial population | `0x003CDCAC` | `0x002CDE2C` | `0x0C0F378C` |
| Refreshed population | `0x003CF6E0` | `0x002CF860` | `0x0C0F378C` |
| Primary fighter confirmation | `0x003C89CC` | `0x002C8B4C` | `0x0C0F1F54` |
| Repeated fighter confirmation | `0x003C8AE4` | `0x002C8C64` | `0x0C0F1F54` |
| Finalize support entry | `0x003CA8D0` | `0x002CAA50` | `0x27BDFFF0` |
| Return from finalized entry | `0x003CABF0` | `0x002CAD70` | `0x27BDFFF0` |
| Primary-list display ID | `0x003CB30C` | `0x002CB48C` | `0x0C228A28` |
| Available-list display ID | `0x003CB50C` | `0x002CB68C` | `0x0C228A28` |
| Selected-name display ID | `0x003CB6F4` | `0x002CB874` | `0x0C228A28` |
| Selected-portrait display ID | `0x003CB984` | `0x002CBB04` | `0x0C228A28` |
| Support-cell draw | `0x003CB358` | `0x002CB4D8` | `0x0C0E2B40` |
| Selected-name draw | `0x003CC734` | `0x002CC8B4` | `0x0C0F2D90` |

The two replaced function entries both retain clean second prologue word
`0xFFBF0000`; the port replaces each with a jump delay-slot `nop`.
Battle-overlay support-call and gauge suppression were not included.

### Rejected overlay placement

Runtime evidence on 2026-08-21 rejected the candidate. NUN5 SS1, preserved with
SHA-256
`7F3B3DF7E147BDC739BBF2533D8404B44ED29765C8F21F0865A6C2068834FB56`,
contains structured live battle data throughout the alleged
`0x008ECE80..0x008F3D00` gap. The recurring payload at
`0x008ECED0..0x008ED930` and its mutable storage at
`0x008ED930..0x008EE1D8` therefore overwrote battle runtime state.

The NUN5 ELF program headers explain the collision. Its resident `PT_LOAD`
starts at `0x00100000` with memory size `0x005C6D00`, ending exactly at
`0x006C6D00`; overlay reservations begin at that same address. The region after
a particular BTL file image is unused file capacity within the overlay
reservation, not free resident memory. No safe fixed-address resident gap
exists for this payload. The broken overlay candidate was removed.

The corrected NUN5 candidate reserves an `0x2000`-byte tail from the game's own
allocator instead. NUN5 allocator initialization at `0x00118CA0` obtains the
same full system block as native code, but the clean `move s6,s0` at
`0x00118D6C` becomes `addiu s6,s0,-0x2000` before the game allocator builds its
sentinels. The observed user base therefore remains `0x00928920`, while the
game heap end moves from `0x01FF5FF0` to `0x01FF3FF0`. The system-owned block
and high-memory system tail do not move.

The rebuilt relocation-bearing payload occupies
`0x01FF4000..0x01FF5308` inside that excluded allocator tail. Its immutable
code, read-only table, and Character Select hooks are recurring extended PNACH
writes; mutable selector buffers at `0x01FF4A60..0x01FF5308` are not. Three
conditional blocks require allocator global `0x00617A84` to contain heap-end
low half `0x3FF0` before any payload or hook write can execute. Hot-reloading
the PNACH into a native process whose heap still ends at `0x01FF5FF0` therefore
changes only the future-boot allocator instruction and cannot write into that
live heap. This leaves 3,304 bytes before the native system-owned end at
`0x01FF5FF0`. Clean-ELF guards, relocation closure, conditional block counts,
payload range, and absence of writes to the mutable buffers are statically
validated. Runtime behavior remains unvalidated pending a clean NUN5 boot and
Character Select to battle test.

NUN5's native font renderer stores tracking at `+0x3C` and horizontal scale at
`+0x80`. Static inspection of `FUN_001891A0` and `FUN_00189640` establishes
that the latter scales both glyph geometry and advances. This renderer-field
mapping remains valid independent of the rejected injection location.

## Selection compatibility and observed runtime failure

The initial list-only injection produced the intended 34-entry roster in a
patched runtime test on 2026-08-14. The added slot rendered through NA2's
fallback character record and the cursor could navigate to it, but pressing OK
did not accept it. That result isolates the failure after list production,
rendering, and navigation.

Character Select separately calls the BTL compatibility helper exposed to the
main ELF as `SUB_008858C0` (BTL Ghidra body `FUN_00885880`). NA2 begins that
helper with an unsigned `support_id < 0x24` gate and returns zero immediately
for `0x25`. NUN6's homolog, exposed as `func_0x008a27b0` (body
`FUN_008a2770`), instead uses `support_id < 0x26`, allowing its added No
Support ID to reach the compatibility logic.

The clean NA2 main ELF contains exactly six calls to the helper. Each stores
the instruction `30 16 22 0C`:

| Consumer | ELF offset |
| --- | ---: |
| Default support compatibility | `0x2B5088` |
| Initial support-selection transition | `0x2B56FC` |
| Primary confirmation | `0x2B6BEC` |
| Repeated confirmation | `0x2B6F7C` |
| Navigation | `0x2B72B0` |
| Draw eligibility | `0x2B8A38` |

The corrected injection routes all six calls through a table-aware wrapper.
The wrapper returns compatible for IDs declared in
`ADDITIONAL_SUPPORT_ENTRIES` and delegates every other ID to the untouched NA2
helper, preserving native per-character compatibility behavior.

User runtime testing then confirmed that OK accepts ID `0x25`. The earlier red
X was the ordinary incompatibility overlay, not No Support artwork.

## Support identities and whitelist

BTL runtime table `DAT_008d28a0` is stored at file offset `0x21E9A0` in the
verified NA2 `BTL.BIN` loaded at `0x006B3F00`. Its 34 three-byte rows map each
native support ID to its corresponding character record and display record.
The character and display bytes are identical in all 34 native rows. Thirty-
three character records match rows in the canonical playable-character
reference; their inverse mapping is recorded in its `support_id` column.
Support ID `0x17` maps to record `0x58`, which has no row in that 74-character
reference. Joining the other records to the canonical builder character
reference establishes the support IDs used by the requested directional
whitelist:

| Selected fighter | Selectable native supports |
| --- | --- |
| Naruto (`0x39`) | Sakura (`0x01`), Sai (`0x20`), Gaara (`0x08`) |
| Sakura (`0x3A`) | Naruto (`0x00`), Chiyo (`0x1B`) |
| Chiyo (`0x3E`) | Sakura (`0x01`) |
| Itachi (`0x47`) | Kisame (`0x0E`) |
| Kisame (`0x48`) | Itachi (`0x0D`) |
| Sasori (`0x3F`) | Deidara (`0x0B`) |
| Deidara (`0x40`) | Sasori (`0x1E`) |
| Sasuke (`0x5D`) | Orochimaru (`0x1C`), Naruto (`0x00`) |
| Orochimaru (`0x59`) | Sasuke (`0x21`) |
| Tsunade (`0x54`) | Jiraiya (`0x18`) |
| Shikamaru (`0x44`) | Choji (`0x13`) |

The whitelist injection replaces native compatibility results at all six
already-routed Character Select consumers with this exact table. Declared
special entries remain globally compatible, so No Support (`0x25`) is the only
choice for every fighter absent from the table. Compatibility hooks retain the
same directional table as confirmation protection; rejected entries are absent
rather than visible with red-X overlays.

### Linked relationship tables

The whitelist is the exact union of two typed BTL relationship tables. The
ten four-byte rows at Ghidra `DAT_008d2660`, complete-file offset `0x21E760`,
store `support_id`, selected `character_id`, and a little-endian linked
Ultimate Jutsu ID. `FUN_00885620` checks all ten rows. Grouped by selected
character, those rows are:

| Selected character | `linked_uj` support IDs |
| --- | --- |
| Naruto (`0x39`) | Sakura (`0x01`) |
| Sakura (`0x3A`) | Naruto (`0x00`), Chiyo (`0x1B`) |
| Chiyo (`0x3E`) | Sakura (`0x01`) |
| Sasori (`0x3F`) | Deidara (`0x0B`) |
| Deidara (`0x40`) | Sasori (`0x1E`) |
| Itachi (`0x47`) | Kisame (`0x0E`) |
| Kisame (`0x48`) | Itachi (`0x0D`) |
| Orochimaru (`0x59`) | Sasuke (`0x21`) |
| Sasuke (`0x5D`) | Orochimaru (`0x1C`) |

The five six-byte rows at Ghidra `DAT_008d2880`, complete-file offset
`0x21E980`, store `support_id`, selected `character_id`, the ordinary Jutsu ID,
and its little-endian linked replacement ID. `FUN_00885ec0` checks all five:

| Selected character | `linked_jutsu` support IDs |
| --- | --- |
| Naruto (`0x39`) | Gaara (`0x08`), Sai (`0x20`) |
| Shikamaru (`0x44`) | Choji (`0x13`) |
| Tsunade (`0x54`) | Jiraiya (`0x18`) |
| Sasuke (`0x5D`) | Naruto (`0x00`) |

The inverse support mapping and these relationship support IDs are canonical in
`@resources/character_data.tsv`; empty relationship cells mean that the selected
character has no row in the corresponding linked-attack table.

### Rejected compact-list candidate

The first compact-list candidate copied `0x24C` bytes from the shared selector
data into one private buffer per player and redirected each selector's `+0x74`
data pointer. User runtime testing showed repeated permitted portraits and a
missing Naruto fighter portrait. Slot 1 from that failed runtime is retained as
immutable evidence with SHA-256
`6DDCBCD0B56601B73F63409A240DF742C506C9242942952DDF1DA41124027557`.

The state proves that list construction itself was correct. The Character
Select root was `0x00CA3760`; player selectors were `0x00CD2CD0` and
`0x00CD5080`; their redirected data pointers were `0x008FBA48` and
`0x008FBC94`. Both private lists had count four, IDs
`25 01 20 08`, and available state `4`: No Support, Sakura, Sai, and Gaara for
Naruto.

The repeated cells came from the unchanged native renderer
`FUN_003b84d0`. Its inner loop always visits carousel offsets `-6` through `6`
and wraps every offset modulo the list count at runtime
`0x003B85E8`-`0x003B8618`. A compact count therefore made the renderer draw the
same valid entries repeatedly; it did not indicate corrupt list data.

The missing fighter portrait was a separate truncation error. Native
`FUN_003b83e0` indexes the selected fighter's portrait object at selector data
`+0x24C + character_id * 4`. Naruto's shared slot at `0x00CA3AB4` contained
the valid object pointer `0x00CC6D30`, while the redirected player-zero slot at
`0x008FBD78` contained `0x0000004F` and player one's corresponding slot at
`0x008FBFC4` was zero. The Character Select constructor establishes the full
data extent: character portrait objects occupy root offsets
`0x270`-`0x3EC`, support portrait objects occupy `0x3F0`-`0x474`, and player
selector pointers begin at `0x478`. The complete selector-data block therefore
runs from root `+0x24` through `+0x477`, a size of `0x454` bytes.

### Corrected compact-list implementation

The accepted implementation copies the complete `0x454`-byte selector
data block for each player before compacting its support roster. This preserves
both native portrait-object tables while allowing two players to retain
different lists simultaneously.

The clean support-cell draw at runtime `0x003B87C0` (ELF offset `0x2B88C0`,
bytes `10 EF 0D 0C`) is routed through the resident injection. The wrapper
reads the renderer's live selector and carousel-offset registers and calls the
unchanged native cell renderer only for offsets in
`[-selected_index, count - selected_index)`. Every compact entry is therefore
drawn exactly once with the selected entry at the native center position. A
one-entry roster draws one centered, highlighted Leaf cell; the other carousel
positions draw nothing. In the accepted 2026-08-15 baseline, native navigation
wrapped to that same sole entry; the accepted bounded navigation described
below blocks outward edge input before it reaches the native function.

The implementation remains table-driven: every roster contains No Support
followed by only the selected fighter's declared native partners. User runtime
acceptance on 2026-08-15 established the corrected behavior: Naruto retains
his fighter portrait and shows Leaf, Sakura, Sai, and Gaara once each, while a
fighter with no declared partner shows one centered Leaf cell.

## Default, centered, and bounded support navigation

The clean NA2 support selector routes horizontal input to `FUN_003b7280` at two
call sites. Left uses direction `2` at runtime `0x003B6C48` (ELF offset
`0x2B6D48`), and right uses direction `3` at runtime `0x003B6C8C` (ELF offset
`0x2B6D8C`). Both store the clean call bytes `A0 DC 0E 0C`. The native function
decrements or increments the support index and wraps it from the first entry to
the last or from the last entry to the first.

The accepted implementation resets the support index and page to zero after
native fighter confirmation enters support selection. It performs the same
reset when Back returns an ordinary roster from finalized state to support
selection. No Support, the compact list's first entry, is therefore selected by
default.

`FUN_003b84d0` also uses the selector's float at `+0x38` as a horizontal
carousel anchor, multiplying it by 36 internal pixels before drawing the cells.
The `support2.p2m2` baseline had index and page zero at both markers, but the
anchor changed from `0.0` at the misaligned opening marker to `-1.0` after
navigation. At the captured 640-pixel output scale, that one-cell difference is
the observed 45-pixel shift. Resetting only the index and page therefore left
the opening frame anchored to the native recommended support.

The accepted implementation initializes the anchor to
`-((support_count - 1) / 2)` whenever it selects No Support. This places the
complete compact row around the native center immediately, while later native
navigation increments or decrements the same anchor with the selected index so
the row remains stationary.

Only the two horizontal call sites are redirected through a bounded wrapper.
The wrapper ignores left at index zero and right at the last entry, and delegates
every in-range movement to the untouched `FUN_003b7280`. The existing
navigation-compatibility call at ELF offset `0x2B72B0` remains in place, so the
directional roster whitelist still applies after each permitted movement.

A `support.p2m2` replay on 2026-08-23 produced No Support at both
marker 1 (on entering support selection) and marker 2 (after the recorded
left-edge input). The corresponding baseline markers selected Sakura and Gaara.
The user accepted this default-selection and left-edge result on 2026-08-23.

A `support2.p2m2` centered-opening replay produced index zero,
page zero, anchor `-1.0`, and count four at both markers. Both screenshots show
the same support-cell positions and selected Leaf as the good baseline marker
2; marker 2 is byte-identical to that baseline PNG with SHA-256
`282D508AB5D9D9E1943CB57017B8112911708CA664404913503D1D5F3B20E5C4`.
The user accepted the centered-opening result on 2026-08-23.

## No-Support-only transition bypass

Native fighter confirmation runs through `FUN_003b52e0`. Character Select has
two confirmation calls at runtime `0x003B5E74` and `0x003B600C` (ELF offsets
`0x2B5F74` and `0x2B610C`, both clean bytes `B8 D4 0E 0C`). The accepted
wrapper calls that native function first. When it leaves the player selector in
state `2` and the active compact roster is exactly one entry containing support
ID `0x25`, the wrapper fixes the support index and page at zero, clears Linked
Mode, and uses native state setter `FUN_003b5670` to enter finalized state `12`.
The selector therefore never renders the support-selection or Linked Mode
screens for a No-Support-only fighter. Any larger roster retains the native
state transition.

The finalized-state Back handler begins at runtime `0x003B8050` (ELF offset
`0x2B8150`, clean prologue `F0 FF BD 27 00 00 BF FF`). Its resident replacement
retains the native ready check at selector offset `0xA0` and native split for
ordinary rosters. A No-Support-only roster instead enters fighter-selection
state `1` directly, so Back also bypasses the otherwise reopened Linked Mode
states. The native secondary-selection branch continues to return directly to
fighter selection for ordinary rosters.

The original `supports.p2m2` replay preserved Naruto's marker-1-through-marker-4
screens and produced player states `1, 5, 9, 12, 1, 12, 12, 12` at markers 1
through 8: the No-Support-only fighter was already finalized at marker 6 and no
intermediate menu rendered. A backward diagnostic first reproduced the clean
marker-8 Back route through states `12, 8, 9, 9`; the accepted candidate
produced `12, 1, 1, 1`, with fighter selection visible from the first marker
after Back. The retained captures and provenance under
`@work/QoL/captures/supports/` exist solely as future regression evidence for
these direct forward and backward transitions.

## Display resolution and official Leaf artwork

The clean main ELF calls BTL support-to-display helper `0x008859A0` six times.
Its live mapping table covers native support IDs only through `0x21`; ID
`0x25` takes the helper's default result, display record zero. This explains
the runtime-observed Classic Naruto list icon and selected portrait after the
compatibility correction.

Character Select has four relevant display consumers, all storing clean
`jal 0x008859A0` as `68 16 22 0C`:

| Consumer | Runtime | ELF offset |
| --- | ---: | ---: |
| Scrollable-list primary path | `0x003B8724` | `0x2B8824` |
| Scrollable-list available path | `0x003B8774` | `0x2B8874` |
| Selected-name record | `0x003B8B6C` | `0x2B8C6C` |
| Selected large portrait | `0x003B8DD4` | `0x2B8ED4` |

The imported official NUN5 `CHARSEL1.CCS` contains a Leaf sprite in
`m\\sel1\\tex\\purecharsel10.bmp` at `(u=241, v=465, w=38, h=46)`. NA2's
Character Select rectangle table identifies that cell as display record
`0x5F`; the build already initializes resources through record `0x5F`. The
injection therefore maps support ID `0x25` to existing record `0x5F`. It does
not reuse NUN6's distinct record `0x60` artwork and adds no generated asset.

The imported NUN5 `char_name01.bmp` does not contain a suitable No Support
name. The single clean call to the selected-name renderer at runtime
`0x003B9B74` (ELF `0x2B9C74`, `A4 E2 0E 0C`) is routed through the same table.
For ID `0x25`, it suppresses the unrelated character-name sprite and draws
`NO SUPPORT` with the resident ASCII font in the existing nameplate. Every
ordinary support delegates to native `FUN_003b8a90` unchanged.

A user runtime screenshot confirmed both the Leaf record and `NO SUPPORT`
renderer on 2026-08-14. At the initial `1.0` horizontal scale, the label began
under the **Linked Character** badge; its vertical placement was acceptable,
but its width and horizontal centering were not. A second runtime screenshot
rejected centering from a manually scaled advance width: the label shifted too
far right and reached the nameplate border. A third screenshot rejected the
follow-up `-8.0` draw offset.

Direct pixel measurement on the retained 1902-pixel captures found the initial
label 376 pixels wide and the supposed `0.80` label 384 pixels wide. The latter
therefore was not narrower at all. Those captures and their hashes remain under
`@work/QoL/inputs/runtime` solely for future renderer-regression comparison.

The cause is now established: writing live scale word `0x0060737C` alone does
not activate the accepted Font v2 glyph-quad and glyph-advance hooks. The
accepted implementation calls the existing `font_v2_adapter_call`, which activates a
session while drawing both shadow and foreground. Font v2 measures
`NO SUPPORT` as 112 local units; the table row supplies an 84-unit maximum, so
the adapter derives a true `0.75` horizontal scale. It centers the scaled result
at calibrated left/right nameplate centers `131.5` and `380.5`, with no manual
draw offset. The user accepted that fitted-and-centered result in runtime on
2026-08-14.

## Rejected recommendation-record path

The BTL function `FUN_00885c30` reads four recommendation bytes from each of
62 per-character records. Those bytes are not the 33-entry scrollable roster.
An earlier candidate populated their unused fourth byte and raised four
three-entry consumers. The user ran that candidate and observed no visible
change. That result is consistent with the now-established separation between
the recommendation records and `FUN_003bb210`, the actual list producer. All
five unrelated edits have been removed.

## Current injection

`qol.character_select.no_support` now selects one resident C injection. Both
native calls to `FUN_003bb210` are redirected to the same wrapper. The wrapper:

1. calls the untouched native function, preserving all 33 IDs and their
   native availability states;
2. copies the complete selector-data block for each player so fighter and
   support portrait objects remain intact;
3. prepends each row declared in `ADDITIONAL_SUPPORT_ENTRIES`, then retains only
   native IDs declared for the selected fighter;
4. clears unused list slots and clamps an out-of-range support cursor to the
   first compact entry;
5. selects the first compact entry and centers the complete compact row whenever
   native fighter confirmation enters support selection and when Back returns
   there from finalized state;
6. blocks horizontal movement beyond either compact-list edge while delegating
   every in-range movement to native navigation;
7. accepts declared added IDs at all six Character Select compatibility calls
   and accepts native IDs only through the same directional roster table;
8. resolves added IDs through their declared display record at the four
   Character Select rendering consumers;
9. renders a declared name for an added ID while delegating native selected
   names and their ancillary icons to the original renderer;
10. draws each compact entry once instead of repeating it across the native
   13-position carousel; and
11. bypasses both intermediate support menus in both directions when No Support
   is the roster's only entry.

The initial declaration contains
`{0x25, 4, 0x5F, "NO SUPPORT", 84}`: No Support with the native available
state, the official NUN5 Leaf display record, and its label's maximum rendered
width. Adding later special entries is a table edit in
`src/qol/character_select_no_support.c`; no further executable list surgery is
required while the total remains within the native 40-slot capacity.

Static confidence is strong: all declared guards, both population xrefs, all
six compatibility xrefs, all display/name and compact-cell xrefs, both fighter
confirmation calls, both horizontal-navigation calls and their native wrap
path, the finalized-state Back handler, object offsets, capacity, NA2/NUN5
33-ID sequence, NUN6 34-ID sequence, display mapping, atlas rectangle, and the
NA2/NUN6 compatibility bounds are directly verified. Selection, the Leaf, the
fitted `NO SUPPORT` renderer, the compact roster, and both No-Support-only
transition directions are runtime-confirmed. The default selection and
left-edge guard are runtime-confirmed through `support.p2m2`; the matching
opening and post-navigation anchors are runtime-confirmed through `support2.p2m2`.
The user accepted both results on 2026-08-23.
