# Character Select support list

## Scope and source identity

This record covers the scrollable Character Select support roster and the
first-phase implementation that adds **No Support** to it. Battle transition,
Ultimate Jutsu input blocking, and battle-side support UI are separate scopes.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| NA2 `SLPS_258.37` | `5,273,256` | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |
| NUN5 `SLES_556.05` | `5,340,912` | `20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D` |
| NUN6 A35 `SLUS_556.06` | `5,340,912` | `47C40141A3E1AEB0C96BC28E8DC311938B284D54FD21F4D8BA953C2E16234809` |

The user supplied Slot 1 states at the relevant NUN6 and clean-NA2 screens.
Task-owned copies, paired screenshots, and hashes are retained under
`work/QoL/inputs/savestates` as immutable diagnostic evidence, not build
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
`work/QoL/inputs/runtime` solely for future renderer-regression comparison.

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
2. shifts those populated entries right within the existing 40-slot buffer;
3. prepends each row declared in `ADDITIONAL_SUPPORT_ENTRIES`;
4. updates the count from 33 to 34;
5. accepts declared added IDs at all six Character Select compatibility calls
   and delegates all other IDs to the original helper;
6. resolves added IDs through their declared display record at the four
   Character Select rendering consumers;
7. renders a declared name for an added ID while delegating native selected
   names and their ancillary icons to the original renderer.

The initial declaration contains
`{0x25, 4, 0x5F, "NO SUPPORT", 84}`: No Support with the native available
state, the official NUN5 Leaf display record, and its label's maximum rendered
width. Adding later special entries is a table edit in
`src/qol/character_select_no_support.c`; no further executable list surgery is
required while the total remains within the native 40-slot capacity.

Static confidence is strong: all thirteen guarded call bytes, both population
xrefs, all six compatibility xrefs, all five display/name xrefs, object
offsets, capacity, NA2/NUN5 33-ID sequence, NUN6 34-ID sequence, display
mapping, atlas rectangle, and the NA2/NUN6 compatibility bounds are directly
verified. Selection, the Leaf, and the `NO SUPPORT` renderer are
runtime-confirmed, including the adjusted label fit.
