# Character identity in battle

This document records the first confirmed Character Select-to-battle identity
mapping. It intentionally lists only names supported by both selector and live
battle evidence; extend it as additional IDs are verified.

## Research coverage

- **Assigned scope:** Character identity from Character Select through the
  battle manager and active fighter, including selector eligibility, linked
  form mappings, and the distinction between match-start selection and
  transformed state.
- **Exploration depth:** Four Practice captures cover Naruto, Sakura, direct
  selection of Nine-Tailed Fourth Awakened State, and an in-match Naruto
  transformation. Static resident-ELF analysis covers the complete hard-coded
  Character Select base/form mapping and its immediate eligibility helpers.
- **Confirmed coverage:** IDs 57, 58, and 73; the relevant manager and fighter
  fields; reciprocal fighter pointers; the match-start versus current-ID
  distinction; all 13 forward selector form pairs; the 12 inverse pairs; and
  the selector's fixed excluded-ID set are established below.
- **Unresolved or untested:** The remaining character IDs have not been
  confirmed by both selector and live-battle evidence. The retail identity and
  intended use of ID 74, and the wider roles of several direct helper callers,
  remain unresolved.
- **Deliberate exclusions and overlap:** Save-backed availability belongs to
  [Content availability](../game/content_availability.md); the complete
  character-data table is a reference and does not expand this document's
  runtime-confirmed set.
- **Evidence limitations:** Runtime findings are bounded to the four stated
  Practice captures; heap pointers are capture-specific, while only the global
  and field offsets are treated as reusable. Static mappings prove code paths
  and numeric relationships, not that every pair is reachable or selectable in
  ordinary play.

## Evidence identity and address conventions

Static findings use the maintained read-only resident analysis. The clean file
identity and address conversion follow
[Retail game file identities](../game/files/file_identities.md). Unless a
manager or fighter field is explicitly described as capture-derived, function
and data addresses below are resident addresses. Original `FUN_` symbols are
retained so the evidence can be located in the maintained analysis.

## Confirmed IDs

| ID | Character | Character Select | Active Practice fighter |
| ---: | --- | --- | --- |
| 57 (`0x39`) | Naruto | Confirmed | Confirmed |
| 58 (`0x3A`) | Sakura | Confirmed | Confirmed |
| 73 (`0x49`) | Nine-Tailed Fourth Awakened State | Confirmed | Confirmed |

The save-backed character-status array stores 94 IDs, `0..93`. Character
Select's playable-entry checks use `1..93`; ID 0 is a special/non-playable
stored entry. See [Content availability](../game/content_availability.md) for
the save-backed domain and unlock-reader contract.

The complete character reference is
[`@resources/character_data.tsv`](../../../resources/character_data.tsv).
Its `awakening_ids` column records the union of the fighter-controller
association list and every non-`0xFFFF` post-effect in that character's
Ultimate-Jutsu records, plus effects applied by hard-coded transformed-form
initialization and character-specific direct or successor paths. The union
records compatible active states for each character and does not imply how the
game normally enters each state.
`support_id` maps a playable character to its
separate native support-roster ID, with a blank cell when no native support
entry maps to that character. `linked_uj` and `linked_jutsu` record the support
IDs associated with that selected character by the two native linked-attack
tables. Blank cells identify characters with no entry in the corresponding
table. Runtime tables contain numeric IDs only.

## Character Select evidence

`FUN_003b4a90` reads the selected character ID from the live roster table.
Changing the selected tile between the two captures changed the table value
from 57 for Naruto to 58 for Sakura. Final selection copies the player choices
to the live manager fields at `+0x4C` and `+0x74`. A second manager copy at
`+0xC8` and `+0xF0` preserves the match-start choices after an in-match
transformation changes the live fields.

### Selector ID filters

`FUN_003b4a90` accepts ordinary candidates only inside `1..93` and applies two
resident filters. `FUN_001f7aa0` returns true for this exact excluded-ID set:

```text
0, 8, 9, 20, 21, 23..33, 44, 45, 74, 88
```

`FUN_001f7bb0` is a useful negative result: its entire body returns zero, so it
currently excludes no ID despite being called beside `FUN_001f7aa0` throughout
the selector family. The playable reference has no row for any ID in the fixed
excluded set. This agreement supports treating `FUN_001f7aa0` as a roster-hole
filter in this path, while the reason each numeric slot exists remains
unresolved.

Held-input bit `0x08` makes `FUN_003b5df0` set the selector object's `+0x18`
field to `1`; `FUN_001f7fb0` can immediately clear it through the independent
progress gate. When `+0x18` remains `1`, `FUN_003b4a90` validates the selected
ID, calls `FUN_001f7c80`, validates the returned candidate with the same range
and filters, and requires `FUN_001f7bc0` to recognize the result as a form ID.
`FUN_001f7bc0` recognizes exactly IDs `47..56` and `73..75`.

### Hard-coded linked-form mapping

`FUN_001f7c80` is the complete forward mapping used by the selector path. It
accepts either side of each pair and returns the form ID; any other input
returns zero. Names in this table come from the canonical character reference,
while the numeric relationship is observed directly in the clean ELF.

| Base ID | Base character | Form ID | Form character | Inverse in `FUN_001f7e70` |
| ---: | --- | ---: | --- | --- |
| 1 (`0x01`) | Naruto Uzumaki (Classic) | 47 (`0x2F`) | Naruto Uzumaki (Nine-Tailed) | Yes |
| 2 (`0x02`) | Sasuke Uchiha (Classic) | 48 (`0x30`) | Second Stage Sasuke Uchiha | Yes |
| 3 (`0x03`) | Rock Lee (Classic) | 49 (`0x31`) | Loopy Fist Lee | Yes |
| 4 (`0x04`) | Gaara (Classic) | 50 (`0x32`) | Possessed Gaara | Yes |
| 14 (`0x0E`) | Choji Akimichi (Classic) | 51 (`0x33`) | Super Choji | Yes |
| 34 (`0x22`) | Jirobo | 52 (`0x34`) | Second Stage Jirobo | Yes |
| 35 (`0x23`) | Kidomaru | 53 (`0x35`) | Second Stage Kidomaru | Yes |
| 36 (`0x24`) | Tayuya | 54 (`0x36`) | Second Stage Tayuya | Yes |
| 37 (`0x25`) | Sakon | 55 (`0x37`) | Second Stage Sakon | Yes |
| 38 (`0x26`) | Kimimaro | 56 (`0x38`) | Second Stage Kimimaro | Yes |
| 57 (`0x39`) | Naruto Uzumaki | 73 (`0x49`) | Nine-Tailed Fourth Awakened State | Yes |
| 62 (`0x3E`) | Granny Chiyo | 74 (`0x4A`) | Unresolved; no playable-reference row | No |
| 63 (`0x3F`) | Sasori | 75 (`0x4B`) | Sasori (Puppet) | Yes |

`FUN_001f7e70` implements the inverse form-to-base mapping for the 12 rows
marked **Yes** and returns `-1` otherwise. ID 74 is deliberately asymmetric in
the observed helper family: the forward mapper produces it and the form-set
predicate recognizes it, but `FUN_001f7aa0` excludes it and the inverse mapper
omits it. In `FUN_003b4a90`, that exclusion rejects the mapped candidate and
falls back to the original ID. It is therefore a latent or disabled mapping in
this selector path; its character identity and any other consumer are not yet
established.

Direct static callers establish that these mappings are shared beyond the one
selection-return site. `FUN_001f7c80` is directly called by `FUN_001f5500`,
`FUN_003b4750`, `FUN_003b4a90`, and `FUN_003b63d0`. The inverse helper
`FUN_001f7e70` is directly called by `FUN_001d4400`, `FUN_001d5a40`,
`FUN_003b3db0`, `FUN_003bacd0`, and `FUN_003bb3a0`. Their precise per-caller
semantics remain a research frontier rather than an inferred shared role.

## Active-battle identity

The stable global at `0x00607600` points to the live manager. In the two
Practice captures, the manager's fighter pointers and the relevant fighter
fields were:

| Field | Meaning |
| --- | --- |
| manager `+0x4C` | Player 1 current character ID (`u32`) |
| manager `+0x74` | Player 2 current character ID (`u32`) |
| manager `+0xC8` | Player 1 match-start selected character ID (`u32`) |
| manager `+0xF0` | Player 2 match-start selected character ID (`u32`) |
| manager `+0xDE4` | Player 1 fighter pointer |
| manager `+0xDE8` | Player 2/COM fighter pointer |
| fighter `+0x20` | Opponent fighter pointer; reciprocal in both captures |
| fighter `+0x68` | Active character ID (`u32`) |
| fighter `+0x70` | Current chakra resource (`float32`); native substitution also spends it |

In Naruto versus Naruto, manager choices were 57/57 and both live fighter IDs
were 57. In Sakura versus Naruto, manager choices were 58/57 and the
live fighter IDs were 58/57. The heap pointers themselves are capture-specific;
the global, manager offsets, and fighter offsets are the reusable contracts.

Two additional Practice captures distinguish direct form selection from an
in-match transformation. With the Nine-Tailed Fourth Awakened State selected
directly, the match-start, current-manager, and live-fighter IDs were all
73/73. With base Naruto selected for both sides and Player 1 transformed during
the match, the match-start IDs remained 57/57 while the current-manager and
live-fighter IDs became 73/57. The `+0xC8`/`+0xF0` pair is therefore the
selection-time identity source for overrides that must not change during a
transformation.

Runtime screenshots establish the active matchups; extracted EE memory
establishes the selector, manager, pointer, character-ID, and resource values.
