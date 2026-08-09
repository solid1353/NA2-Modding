# Content availability and save-backed unlock state

This document records the resident-ELF readers that expose save-backed content
availability to the frontend, Adventure, and battle overlays. It separates the
confirmed data and call contracts from the `qol.content.unlock_all` patch that
overrides those reads.

## Evidence and identity

Static analysis uses the canonical Ghidra 12.1.2 exports under
`@analysis/disassembly/NA2/` for clean `@source/NA2.iso.files/SLPS_258.37`:

- size: `5,273,256` bytes;
- SHA-256: `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`;
- resident segment mapping for the functions below: ELF file offset equals
  runtime address minus `0x000FFF00`.

On 2026-08-10, direct byte inspection compared the extracted `eeMemory.bin`
members of two user-supplied NA v2.28 savestates for serial `SLOP-NA228`, CRC
`7E793241`: SS1 had a fully unlocked save loaded, while SS2 had no loaded save.
The memory values observed in those captures and the static reader contracts
below are **high-confidence facts**. Semantic names for the six grouped tables
remain incomplete and are identified separately as an unresolved mapping.

## Live manager and profile mapping

The ELF initializes `gp` to `0x0060A9F0`. Ghidra's `iGpffffcc10` therefore
resolves to the stable global at `0x00607600`. Both captures contain this
pointer chain:

```text
[0x00607600]             = 0x00CA4700  profile/state manager
[0x00CA4700 + 0x04]      = 0x00C9ED50  live profile pointer
reader base              = 0x00C9ED50 + 0x08 = 0x00C9ED58
```

The heap addresses are observations from these captures, not fixed allocation
contracts. The global address and the manager's `+0x04` field are confirmed by
the resident reader instructions.

`0x006075F8` is a neighboring global whose captured value is directly
`0x00C9ED50`. It is not the manager consumed by these wrappers and must not be
followed through the manager's `+0x04` field. The exact wider role of this
neighboring direct profile pointer remains unproven.

## Resident reader functions

The following role names are the meaningful names used by this documentation;
the canonical export currently retains its `FUN_` symbols.

| Role | Export symbol | Runtime entry | Overridden read call | ELF hook offset | Clean call bytes | Confirmed consumers |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Character unlocked | `FUN_001f54c0` | `0x001F54C0` | `0x001F54D0` | `0xF55D0` | `D08D070C` | resident ELF, `ETC.BIN`, `ADV.BIN` |
| Secondary bit unlocked | `FUN_001f5750` | `0x001F5750` | `0x001F5760` | `0xF5860` | `008E070C` | resident ELF, `ETC.BIN` |
| Small-table availability | `FUN_001f7030` | `0x001F7030` | `0x001F7040` | `0xF7140` | `1C8E070C` | resident ELF, `BTL.BIN` |
| Grouped availability | `FUN_001f70c0` | `0x001F70C0` | `0x001F70D0` | `0xF71D0` | `448E070C` | resident ELF, `ETC.BIN`, `ADV.BIN` |
| Character/jutsu availability | `FUN_001f7210` | `0x001F7210` | `0x001F729C` | `0xF739C` | `D8FD070C` | resident ELF, `BTL.BIN`, `ADV.BIN` |

The character wrapper reads one byte through `FUN_001e3740`, masks bit 0, and
normalizes it to Boolean. Character-select call paths perform their native ID,
metadata, and linked-form filtering outside this reader. A fully unlocked save
can therefore set bit 0 for every stored ID without making every ID a roster
entry.

The secondary wrapper reads a bit from the eight-byte field through
`FUN_001e3800`. The small-table and grouped wrappers return stored bytes through
`FUN_001e3870` and `FUN_001e3910`; their values are not normalized to Boolean.

The jutsu wrapper first accepts only pairs allowed by `FUN_00307ed0` or
`FUN_001ff8d0`. It then derives the character's 24-byte record at
`profile + 0x38 + character_id * 0x18` and calls `FUN_001ff760` for the saved
jutsu bit. The hook at `0x001F729C` is after both metadata gates, so overriding
that call cannot create nonexistent character/jutsu pairs.

## Stored layout and observed values

Offsets in this table are relative to the reader base (`profile + 0x08`).

| Field | Offset | Length/count | SS1 with unlocks | SS2 without loaded save |
| --- | ---: | ---: | --- | --- |
| Character status | `0x900` | 94 bytes | ID 0 is `FF`; IDs 1-93 are `03` | Mostly `00`; `03` at IDs 57-61, 65-70, 73, and 78-87 |
| Secondary bitset | `0x960` | 8 bytes / 64 bits | all `FF` | all `00` |
| Small availability table | `0x968` | 32 bytes | all `FF` | all `00` |
| Group 0 | `0x988` | 93 bytes | index 0 is `03`; remainder `FF` | all `00` |
| Group 1 | `0x9E5` | 41 bytes | all `FF` | all `00` |
| Group 2 | `0xA0E` | 155 bytes | all `FF` | all `00` |
| Group 3 | `0xAA9` | 168 bytes | all `FF` | all `00` |
| Group 4 | `0xB51` | 7 bytes | index 0 is `03`; remainder `FF` | all `00` |
| Group 5 | `0xB58` | 12 bytes | all `FF` | all `00` |

`FUN_001e39b0`, the native grouped-table reset, independently confirms the six
counts as `93`, `41`, `155`, `168`, `7`, and `12`. The paired captures confirm
the fully unlocked byte values. `ETC.BIN` consumes all six groups across Shop,
Collection, and other frontend paths; `ADV.BIN` also consumes grouped values.
The exact semantic label for every group number is not yet reconstructed and
must not be inferred merely from an individual caller.

## Read-only unlock override

Catalog setting `qol.content.unlock_all` selects injection
`i__qol__content__unlock_all__availability`. Each guarded JAL replaces only the
saved-value read inside a resident wrapper and leaves the wrapper and its
callers intact:

- character IDs below 94 report available;
- secondary IDs below 64 report available;
- small-table IDs below 32 return `FF`;
- grouped IDs are bounded by the six native counts and reproduce the SS1
  values, including `03` at group 0/index 0 and group 4/index 0;
- metadata-valid character/jutsu pairs report available after the native gates.

No setter is hooked. The injected functions ignore the live profile pointer and
perform no writes, so the profile's settings, progress, currency, inventory,
statistics, and availability bytes remain unchanged. Disabling the catalog
setting omits the injection and restores native save-dependent reads.

## Rejected character mask and correction

The first character implementation incorrectly treated the value from
`0x006075F8` as the availability manager. Applying the manager chain to that
direct profile pointer loaded `0x002DB117` from `profile + 0x04`; adding the
reader offsets then sampled resident executable bytes rather than the character
status array. Those bytes produced the false masks `FFFFFFFF`, `C1FFFFFF`, and
`3F003D81`.

The rejected mask hid valid characters and admitted the wrong set, which the
user observed as an inadequate and displaced character roster. The corrected
helper returns available for every bounded ID `0..93`, matching bit 0 of all 94
SS1 status bytes while retaining native roster filtering. On 2026-08-10, the
user confirmed in-game that this correction works.
