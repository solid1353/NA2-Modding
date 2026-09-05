# Field-item names

## Address conventions

The clean NA2 executable and official NUN5 `PRG/TEXTENG.BIN` used below are
identified in [External String Payload](external_string_payload.md#evidence-and-provenance).
The NA2 resident conversion follows
[Standard game file identities](../game/files/file_identities.md). The
preserved NUN5 `TEXTENG.BIN` export maps complete-file offset `x` to export address
`0x008F3CC0 + x`.

## Research coverage

- **Assigned scope:** Identify the resident NA2 field-item name table and its
  corresponding official NUN5 English names, and record the naming evidence
  for selector codes absent from that table.
- **Exploration depth:** The complete 22-row table and its scanner were mapped,
  two state-synchronization callers were identified, and the NUN5 translation
  run was compared in table order.
- **Confirmed coverage:** The table layout, addresses, lookup behavior, and all
  22 resident Japanese-to-English name pairs are established. Code `29` has a
  user-supplied identification and an external UN2 naming reference below.
- **Unresolved or untested:** No clean NA2 or official NUN5 user-facing name is
  established for selector code `29`; codes `02` and `03` have only internal
  BTL identifiers.
- **Deliberate exclusions and overlap:** Item selection, weighting, effects,
  and presentation are owned by their gameplay and UI documents. Other
  localization tables are outside this document.
- **Evidence limitations:** Matching NUN5 table order establishes names only
  for the 22 resident rows; it does not name absent selector codes or prove
  that every item source uses this table.

## Resident field-item name table

The previously unresolved NA2 string range is a field-item name table. Its 22
rows begin at runtime/file `0x005B03F0/0x4B04F0`; each row is an eight-byte
`(u32 item_code, char *name)` pair. The table occupies runtime
`0x005B03F0..0x005B049F`, file `0x4B04F0..0x4B059F`. Its Shift-JIS strings
occupy runtime `0x005B00E0..0x005B03E9`, file
`0x4B01E0..0x4B04E9`, followed by six padding bytes.

Resident `FUN_00373830` at runtime/file `0x00373830/0x273930` scans exactly
22 rows and returns the matching row index or `-1`. Callers
`FUN_0038E6E0` and `FUN_0038E780` use that index while synchronizing the
corresponding per-item state.

The official NUN5 English bank contains a contiguous 22-string translation run
in the same order at complete-file `0x115B0..0x11794`, export
`0x00905270..0x00905454`. This establishes the English names below without
inventing translations from the Japanese text.

| Code | Clean NA2 source name | Official NUN5 English name |
| ---: | --- | --- |
| `09` | `瞬身の巻物` | Scroll of Teleportation |
| `0E` | `アイテムポーチ` | Item Pouch |
| `23` | `風魔手裏剣` | Demon Wind Shuriken |
| `24` | `根性のおもり` | Weight of Determination |
| `25` | `起爆クナイ` | Exploding Kunai |
| `26` | `毒煙玉` | Poison Smoke Bomb |
| `27` | `撒き菱` | Makibishi Spikes |
| `28` | `起爆札` | Paper Bomb |
| `2A` | `呪札　鎧崩し` | Curse Tag: Armor Break |
| `2B` | `千影手裏剣` | 1000-Shadow Shuriken |
| `2C` | `炸裂クナイ` | Burst Kunai |
| `2E` | `起爆シール` | Exploding Seal |
| `2F` | `蝦蟇油` | Toad Oil |
| `30` | `博打玉` | Random Ball |
| `31` | `痺れ玉` | Stun Ball |
| `06` | `上忍の靴` | Shoes of Jonin |
| `07` | `兵糧丸` | Food Pills |
| `08` | `雲隠れの巻物` | Scroll of Hidden Cloud |
| `0A` | `カカシ人形` | Scarecrow |
| `0B` | `亀甲丸` | Tortoiseshell Pills |
| `0C` | `元気丸` | Energy Pills |
| `0D` | `医療パック` | Medical Pack |

The selector can also produce codes `02`, `03`, and `29`, which are absent
from this name table. BTL identifies the first two internally as
`ItemRecoverLife` and `ItemChakraBall`; no clean NA2 or official NUN5
user-facing name was established for code `29` from the binaries.

## Code `29`: Curse Tag: Chakra Points Seal

The user identified NA2 item `0x29` as the Chakra Seal Tag.
[Rampidzier's Ultimate Ninja 2 guide](https://gamefaqs.gamespot.com/ps2/921262-naruto-ultimate-ninja-2/faqs/48890)
lists **Curse Tag: Chakra Points Seal** and describes temporarily preventing
the struck opponent from using chakra. This provides the PS2-series English
name; the association with NA2 code `29` comes from the user's identification,
not from an NA2 or NUN5 name-table entry.

NUN5 `TEXTENG.BIN` string searches for `Chakra`, `Seal`, and `Curse` found no
corresponding item name; an exact byte search for `Chakra Seal` also found no
match. **Curse Tag: Chakra Points Seal** is therefore an externally sourced
UN2 name, not a recovered NUN5 translation.

Pool membership, weighting, and the code-to-gameplay-effect boundary are owned
by [Battle status effects and item-effect lifecycle](../gameplay/battle_items_and_status_effects.md#random-field-item-selection).
