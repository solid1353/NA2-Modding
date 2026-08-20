# Frontend Shop and bonus game

Static evidence for ETC Shop inventory, purchase awards, its save-backed bonus
credit, and bonus-game rewards. Adventure is outside this analysis.

The source is clean `ETC.BIN`, SHA-256
`8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74`.
Because the runtime retains its `0x40`-byte MWo3 header, live overlay addresses
are preserved export addresses plus `0x40`; raw encoded absolute operands are
already live.

## Research coverage

- **Assigned scope:** the non-Adventure ETC Shop: inventory categories,
purchase-to-award behavior, the save-backed bonus credit, and bonus-game
reward selection.
- **Exploration depth:** the four category/group pairs, four group counts, four-entry
bonus candidate order, purchase call families, common award dispatcher, and
visible fallback payouts were decoded from the clean fixed tables and direct
call paths. Figure and Voice bundle granularity was cross-checked against the
grouped content tables rather than inferred from UI labels.
- **Confirmed coverage:** the inventory/category mapping, purchase and expense
  flow, award granularity, save-backed bonus credit, and reward/fallback
  selection are established for the identified direct paths.
- **Unresolved or untested:** the localized meter name and semantic labels for
  result codes 0, 1, and 2 remain unresolved. The bonus child's internal
  gameplay and result production are only bounded.
- **Deliberate exclusions and overlap:** Movie and Diorama acquisition, any
  other overlay's awards, Adventure, and wider save serialization belong
  outside this document.
- **Evidence limitations:** coverage is exhaustive for the scoped ETC tables and identified direct purchase,
expense, award, and reward-selection paths, but only bounded around the bonus
child's internal gameplay and result production. Evidence is static: no Shop
session, purchase, bonus-game outcome, cap boundary, or empty-inventory case
was exercised at runtime.

## Inventory groups and purchase awards

The raw four-pair table at live `0x006E38E0` maps Shop categories to the
save-backed content groups:

| Shop category | Group | Content |
| ---: | ---: | --- |
| 0 | 0 | Figures/Dolls |
| 2 | 3 | Skills/Ultimate Jutsu |
| 3 | 2 | Voice |
| 4 | 1 | Music |

Category 1 is absent. The adjacent count table lists `(group 0, 93)`,
`(group 1, 41)`, `(group 2, 155)`, and `(group 3, 168)`. Shop scan
export/live `0x006D3F90/0x006D3FD0` considers only those four groups before
rebuilding categories 0 through 4; Movies and Dioramas are excluded.

The common award dispatcher at export/live `0x006CADF0/0x006CAE30` writes
owned+NEW state 2. Figures and Voices award an entire character bundle, while
Skills and Music award one ID. The dispatcher is not purchase-specific: the
bonus game uses it too.

General purchase export/live `0x006D6CD0/0x006D6D10` serves Music, Voice, and
Figure category callers. Skill purchase uses export/live
`0x006D6DA0/0x006D6DE0`. Both paths select the inventory node, award content,
apply the expense, remove/re-sort the node, and rebuild the list.

## Save-backed bonus credit

The resident primary-currency wrappers read and write profile field `+0x34`
and cap it at 9,999,999. A second resident wrapper pair accesses profile field
`+0xDF8`; only the Shop and profile reset reference it in the maintained
exports.

Shop initialization at export/live `0x006D3270/0x006D32B0` reads the secondary
field into object `+0x20`. Expense export/live `0x006D6E90/0x006D6ED0` adds the
purchase price to this bonus credit, caps it at 99,990,000, persists it, and
subtracts the same price from primary currency. The UI displays
`object+0x20 / 10000` and enables its bonus action at 10,000 or more.

After a successful bonus child result, export/live
`0x006D79E0/0x006D7A20` subtracts 10,000, floors at zero, and persists the
secondary field. Embedded `ANM_shop_bonus01/02`,
`ccList<ccShopBonusTarget>`, and `ccList<ccShopBonusShot>` strings establish
that this is a Shop bonus minigame meter. Its localized on-screen name has not
been recovered, so this document does not invent one.

## Reward selection and fallback

Reward export/live `0x006D1730/0x006D1770` interprets result byte
`object+0x210`. Numeric codes 1 and 2 enter chooser export/live
`0x006C9D20/0x006C9D60`; code 0 follows no content or currency award path.
The binary does not name the result codes.

The chooser considers candidate categories `[4, 0, 3, 2]` and only unclaimed
inventory nodes. Category 2 aggregates character sublists. Code 2 selects the
eligible node with the greatest price; code 1 selects a random eligible node.
A content win calls the common award dispatcher, so Figure and Voice prizes
inherit bulk-by-character semantics, then removes the won node.

When no eligible content exists, code 2 awards 5,000 primary currency and code
1 awards 1,000, subject to the normal 9,999,999 cap.

## Limits

- Evidence is static; no runtime Shop session was captured.
- Outcome-code labels and the localized bonus-meter name remain unresolved.
- No Movie or Diorama acquisition writer appears in the ETC Shop paths.
