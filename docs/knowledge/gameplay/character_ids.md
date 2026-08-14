# Character identity in battle

This document records the first confirmed Character Select-to-battle identity
mapping. It intentionally lists only names supported by both selector and live
battle evidence; extend it as additional IDs are verified.

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

The complete builder reference is
[`na228_builder/resources/character_data.tsv`](../../../na228_builder/resources/character_data.tsv).
Its names and IDs validate per-character configuration; the runtime table
contains numeric IDs only.

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
| fighter `+0x70` | Current substitution resource (`float32`) |

SS1 was Naruto versus Naruto: manager choices were 57/57 and both live fighter
IDs were 57. SS2 was Sakura versus Naruto: manager choices were 58/57 and the
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

## Capture provenance

Both user-supplied states are for `SLOP-NA228`, CRC `7E5D178F`, and were copied
read-only into the task workspace before extraction.

| Capture | Practice matchup | State SHA-256 | Extracted EE-memory SHA-256 |
| --- | --- | --- | --- |
| SS1 | Naruto vs Naruto | `CFC03F62D3E3DB47495736C06CD1705EA3A0CC7E5F46D1830AF968FA65CD88B0` | `04C3EF55C2067C9C7A1ABC602CE717E51AD0A217FFE7BFFCAC07D8871E5FECBA` |
| SS2 | Sakura vs Naruto | `D6C3DEE11CDABBA12F936F52CBF03784113D78B9837B60876464C249500066C8` | `C10DA137A53CA1B52683CD61540D9B8246FEDA377FB1F1ED6841516CB75B7E25` |

The state screenshots establish the active matchups; the extracted EE memory
establishes the selector, manager, pointer, character-ID, and resource values.

The direct-versus-transformed pair is for `SLOP-NA228`, CRC `3755A94A`. It was
copied read-only from the active PCSX2 `sstates` folder into
`work/Battle mechanics/inputs/savestates` before extraction.

| Capture | Meaning | State SHA-256 | Extracted EE-memory SHA-256 |
| --- | --- | --- | --- |
| SS1 | Form ID 73 selected directly for both sides | `4BCB2A8514BF62A27B77E611E415D1FCD34425CF5FA997CA46AE0DD7D604A350` | `ABEE961C109C0CBD3FD74CFCC6878BC2FC0688D4D379D0460E741F74C75840E5` |
| SS2 | Base ID 57 selected for both sides; Player 1 transformed to ID 73 | `77DF55EC2B6AB7066A5823A2E437CD58C9A68ACCD05ACCA171DD2332A9A604B7` | `2ED6B60D178B1371229720D8053661BCCC2758F0922DB198A74673CE86031C8B` |
