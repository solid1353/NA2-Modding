# Native Character Select support behavior

## Research coverage

- **Assigned scope:** Native Character Select support-roster construction,
  compatibility, identity relationships, selector behavior, display resolution,
  and recommendation records.
- **Exploration depth:** The documented roster tables, compatibility and display
  call sites, linked-attack tables, selector fields, navigation calls, and
  recommendation reader were traced in the clean NA2 binaries and compared
  with the stated NUN5 homologs.
- **Confirmed coverage:** The 33-entry native roster and 40-entry capacity,
  compatibility bound, support-to-character mappings, linked-attack
  relationships, carousel navigation, portrait/name resolution, and separation
  of recommendation records from the scrollable roster are established below.
- **Unresolved or untested:** The meanings of the four recommendation bytes and
  the purpose of the seven spare roster slots are not established.
- **Deliberate exclusions and overlap:** Mod configuration and implementation
  belong to [Character Select](../../features/character_select.md); this
  document records the native data and behavior they may consume.
- **Evidence limitations:** Most findings are static binary and call-site
  evidence; the recommendation experiment establishes only that the changed
  unused byte did not alter the visible support list.

## Scrollable support roster

NA2 `FUN_003bb210` populates the scrollable support list. Its two callers are
at runtime addresses `0x003BB08C` and `0x003BCAB0`, stored at ELF offsets
`0x2BB18C` and `0x2BCBB0`.

The function reads 33 IDs from runtime `0x005D65C0`, writes them at Character
Select object offset `+0x220`, writes their availability states at `+0x248`,
and stores the count at `+0x21C`. It fills the remaining slots through index 39
with sentinel ID `0x24` and state `7`, giving the list a 40-entry capacity.

The clean 40-byte table at ELF offset `0x4D66C0` is:

```text
00 01 20 02 03 04 05 06 07 13 14 15 11 10 12 16
08 09 0A 0F 0D 0E 0B 0C 1B 1E 18 19 1A 1F 1C 1D
21 00 00 00 00 00 00 00
```

The first 33 bytes are the visible native roster. NUN5 has the same function,
bound, and list at its homologous runtime table `0x005DD710`. NA2 also uses
support ID `0x25` to represent No Support in Story Mode, but that ID is absent
from the native Character Select roster.

## Compatibility

Character Select calls the BTL compatibility helper exposed to the main ELF as
`SUB_008858C0`, whose BTL body is `FUN_00885880`. The helper begins with an
unsigned `support_id < 0x24` gate and returns zero immediately for larger IDs.
For a native support ID, it resolves the fighter through resident
`0x001F7E70` when that helper returns an identity other than `-1`, then rejects
matches in a 104-entry support/fighter exclusion table. Otherwise it returns
one. GhidrAssist inspection of `FUN_00885880` confirms that the native check
is an exclusion list, separate from the linked-attack relationship tables.

The red unavailable marker in resident `FUN_003B84D0` uses that same predicate.
The confirmation handler `FUN_003B6910` also requires a selectable fighter
(`1..0x5D`, with resident `0x001F7AA0` and `0x001F7BB0` both returning zero)
and either roster state `4` or a match among the three recommendations returned
by BTL live `0x00885C30`. Thus an otherwise locked recommended support can
still be selected if compatible.

The exclusion table is at live `0x008D1980` (Ghidra byte address `0x008D1940`).
It contains `(support, fighter)` pairs `(0x0C, 0x3F)`, `(0x0C, 0x4C)`,
`(0x1E, 0x3F)`, and `(0x1E, 0x4C)`: Hiruko and Sasori supports are both
excluded for either Sasori or Hiruko. Resident `0x001F7E70` normalizes Sasori's
puppet fighter `0x4B` to `0x3F` before that lookup. These are static MCP code
and table observations.

The clean NA2 main ELF has six calls to this helper:

| Consumer | ELF offset |
| --- | ---: |
| Default support compatibility | `0x2B5088` |
| Initial support-selection transition | `0x2B56FC` |
| Primary confirmation | `0x2B6BEC` |
| Repeated confirmation | `0x2B6F7C` |
| Navigation | `0x2B72B0` |
| Draw eligibility | `0x2B8A38` |

Each site contains the clean call bytes `30 16 22 0C`.

## Support identities and relationships

BTL runtime table `DAT_008d28a0`, stored at complete-file offset `0x21E9A0`
in `BTL.BIN`, contains 34 three-byte rows mapping each native support ID to a
character record and display record. The character and display bytes match in
all 34 rows. Support ID `0x17` maps to character record `0x58`; the other 33
records correspond to playable characters.

Two separate BTL tables define linked attacks. The ten four-byte rows at
Ghidra `DAT_008d2660`, complete-file offset `0x21E760`, store a support ID,
selected character ID, and little-endian linked Ultimate Jutsu ID.
`FUN_00885620` checks all ten rows:

| Selected character | Support IDs |
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
`0x21E980`, store a support ID, selected character ID, ordinary Jutsu ID, and
little-endian linked replacement ID. `FUN_00885ec0` checks all five:

| Selected character | Support IDs |
| --- | --- |
| Naruto (`0x39`) | Gaara (`0x08`), Sai (`0x20`) |
| Shikamaru (`0x44`) | Choji (`0x13`) |
| Tsunade (`0x54`) | Jiraiya (`0x18`) |
| Sasuke (`0x5D`) | Naruto (`0x00`) |

## Selector data and rendering

The Character Select root stores character portrait objects at offsets
`+0x270..+0x3EC`, support portrait objects at `+0x3F0..+0x474`, and player
selector pointers beginning at `+0x478`. The selector-data block begins at root
`+0x24` and ends at `+0x477`, a total size of `0x454` bytes.

Native `FUN_003b83e0` resolves the selected fighter portrait from selector data
`+0x24C + character_id * 4`. Native support-cell renderer `FUN_003b84d0`
visits carousel offsets `-6..6` and wraps each offset modulo the support-list
count. Its selector float at `+0x38` is the horizontal carousel anchor, scaled
by 36 internal pixels when drawing cells.

Resident `FUN_003B49C0(player, support_id)` resets cursor index `+0x30`, page
`+0x34`, and scroll anchor `+0x38` to zero, then scans the 40 roster slots for
the requested ID with availability state `4` or `5`. It assigns the matching
index and page without applying compact-row centering. The native default
selection routine `FUN_003B4E40` uses this setter. Both bodies were inspected
through GhidrAssist.

Horizontal support navigation calls `FUN_003b7280` from two sites. Left passes
direction `2` at runtime `0x003B6C48` (ELF offset `0x2B6D48`); right passes
direction `3` at runtime `0x003B6C8C` (ELF offset `0x2B6D8C`). The native
function decrements or increments the support index and wraps across the two
ends of the list.

## Display resolution

The clean main ELF calls BTL support-to-display helper `0x008859A0` six times.
Its mapping table covers native support IDs only through `0x21`; larger IDs use
the default display record zero.

Four Character Select consumers resolve display records through that helper:

| Consumer | Runtime address | ELF offset |
| --- | ---: | ---: |
| Scrollable-list primary path | `0x003B8724` | `0x2B8824` |
| Scrollable-list available path | `0x003B8774` | `0x2B8874` |
| Selected-name record | `0x003B8B6C` | `0x2B8C6C` |
| Selected large portrait | `0x003B8DD4` | `0x2B8ED4` |

Each contains the clean call bytes `68 16 22 0C`. The selected-name renderer is
called separately at runtime `0x003B9B74`, stored at ELF offset `0x2B9C74`.

## Recommendation records

BTL `FUN_00885c30` reads four recommendation bytes from each of 62
per-character records. Its three-entry consumers are separate from the
33-entry scrollable roster populated by `FUN_003bb210`; changing an unused
recommendation byte did not alter the visible support list.
