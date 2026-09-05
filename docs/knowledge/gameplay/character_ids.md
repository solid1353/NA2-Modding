# Character identity in battle

This document records the first confirmed Character Select-to-battle identity
mapping. It intentionally lists only names supported by both selector and live
battle evidence; extend it as additional IDs are verified.

## Research coverage

- **Assigned scope:** Character identity from Character Select through the
  battle manager and active fighter, including the distinction between
  match-start selection and transformed state.
- **Exploration depth:** Four Practice captures cover Naruto, Sakura, direct
  selection of Nine-Tailed Fourth Awakened State, and an in-match Naruto
  transformation.
- **Confirmed coverage:** IDs 57, 58, and 73; the relevant manager and fighter
  fields; reciprocal fighter pointers; and the match-start versus current-ID
  distinction are established below.
- **Unresolved or untested:** The remaining character IDs have not been
  confirmed by both selector and live-battle evidence in this document.
- **Deliberate exclusions and overlap:** Save-backed availability belongs to
  [Content availability](../game/content_availability.md); the complete
  character-data table is a reference and does not expand this document's
  runtime-confirmed set.
- **Evidence limitations:** The findings are bounded to the four stated
  Practice captures; heap pointers are capture-specific, while only the global
  and field offsets are treated as reusable.

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
