# Unlock all content without loading a save

`features.general.unlock_all` selects patch `general.unlock_all`. It exposes the
content represented by a fully unlocked profile without writing to save data.

The patch replaces seven saved-value reads while preserving their native
wrappers, bounds, metadata checks, and callers:

- all 94 stored character IDs report available, while native roster filtering
  still decides which IDs appear;
- the Character Select R1-form gate receives progression value `0x66`;
- the 64-bit secondary field and 32-entry small table report available;
- the six grouped tables return bounded unlocked values, with Figure entries
  represented by native stable state `3`;
- metadata-valid character/Jutsu pairs report available;
- progress slot `0x6A` reports available, while every other progress-word read
  delegates to the live profile.

Settings, progress, currency, inventory, statistics, and stored availability
bytes remain unchanged. Disabling the setting omits the injection and restores
native save-dependent reads. The reader contracts and native state semantics
are documented in
[Content availability and save-backed unlock state](../../knowledge/game/content_availability.md).

The R1-form hook is at runtime `0x001F7FD4`, ELF offset `0xF80D4`, with clean
call bytes `508F070C`. It changes only the value observed by `FUN_001f7fb0`.
Runtime validation confirmed linked forms without a loaded save.

The grouped-content helper returns state `3` for every bounded Figure ID so the
viewer receives the native viewed-and-unlocked value and renders Figure
pedestals. Runtime validation confirmed the pedestal behavior. Runtime
validation also confirmed Ultimate difficulty through progress slot `0x6A`.

## Optional Demon Wind Bomb assignment

The optional `demon_wind_bomb` boolean controls a guarded Classic Naruto
assignment. Omitting it or setting it to `false` preserves native Jutsu
compatibility. Setting it to `true` admits selector `0x35` only for Classic
Naruto (`0x01`).

The wrapper guards the native special-compatibility call at runtime
`0x001F7254`, ELF offset `0xF7354`, with clean call bytes `34FE070C`. It returns
true only for character `0x01` with selector `0x35`; every other pair delegates
to clean `FUN_001ff8d0`. The downstream availability hook then exposes the
admitted pair without changing saved progress or exposing it to other
characters. Runtime validation of this optional branch remains pending.

## NUN5 PNACH port

The active
[`NUN5.pnach`](../../../pcsx2_files/games/NUN5/NUN5.pnach)
ports the same bounded read overrides to the
[identified clean NUN5 `SLES_556.05`](../../knowledge/game/files/file_identities.md#executables-and-overlays).

| Role | NUN5 wrapper | Saved-value call | Clean word |
| --- | ---: | ---: | ---: |
| Character unlocked | `0x001FBE20` | `0x001FBE30` | `0x0C07A52C` |
| Character Select R1-form progress | `0x001FEA10` | `0x001FEA34` | `0x0C07A6D0` |
| Progress word / Ultimate difficulty | `0x001FE1D0` | `0x001FE1E0` | `0x0C07A6D0` |
| Secondary bit unlocked | `0x001FC0D0` | `0x001FC0E0` | `0x0C07A55C` |
| Small-table availability | `0x001FDA10` | `0x001FDA20` | `0x0C07A578` |
| Grouped availability | `0x001FDAA0` | `0x001FDAB0` | `0x0C07A5A0` |
| Character/Jutsu availability | `0x001FDC00` | `0x001FDC8C` | `0x0C081924` |

NUN5 grouped reset `FUN_001E9720` confirms the same six bounds: `0x5D`, `0x29`,
`0x9B`, `0xA8`, `7`, and `0x0C`. Resident and BTL consumers pass progress ID
`0x6A` through the shared progress wrapper.

The PNACH places 208 immutable helper bytes at
`0x01FF5310..0x01FF53DF`, after the No Support mutable storage and inside the
same allocator-tail reservation. Its progress helper returns 1 only for ID
`0x6A` and performs the native word-bank read for every other ID. The heap-end
guard prevents payload and hook writes before a clean boot establishes the
reservation, and every hook checks both halves of its clean call word before
replacement. Runtime validation confirmed Ultimate difficulty through the
NUN5 port.
