# Modified disc identity

## Decision

The active modified project profile uses the synthetic alphanumeric serial
`SLOP-NA228`. The clean NA2 source remains `SLPS-25837` and is never modified.

The serial alternatives considered on 2026-07-18 were rejected as follows:

- `SLPS-25838` is assigned to *Taiheiyou no Arashi: Senkan Yamato, Akatsuki ni
  Shutsugeki su* in the installed PCSX2 GameDB.
- `SLPS-00228` is the PlayStation release *Policenauts: Private Collection*.
- `SLPS-22228` was absent from the installed PCSX2 PS2 GameDB and no issued-disc
  match was found during the investigation. The project previously used it as
  a synthetic identifier; this is not a claim that Sony formally reserved it.

## Reproducible implementation

Root `settings.json` declares the product title and explicit output boot path.
The builder supports the fixed clean NA2 boot path `SLPS_258.37` and root
`SYSTEM.CNF` directly. After feature modules have been composed, the product
composer emits one guarded replacement and one equal-length file rename:

1. `SYSTEM.CNF` changes `SLPS_258.37` to `SLOP_NA2.28`.
2. The ISO9660 root directory record changes `SLPS_258.37;1` to
   `SLOP_NA2.28;1`.

The second operation is ISO filesystem metadata, not an ELF string replacement,
so it deliberately does not belong to a feature module. The mandatory image
assembler applies it to both ISO9660 and UDF, logs the identity edits, and
verifies the declared final tree. No file extent, file size, or ISO size changes.

The separate `general.dedicated_save_namespace` catalog setting owns the clean
boot ELF's two 19-byte memory-card directory fields at `0x2FBAC1` and
`0x2FBBF0`. When enabled, its guarded binary edits change
`BISLPS-25837NARUTO5` to `BASLOP-NA228NARUTO6`. It is enabled in the base
configuration. Setting it to `false` leaves the stock name intact, so NA228
shares NA2's save data. Existing `.ps2` memory cards and data remain untouched,
and changing the setting does not migrate data between the two names.

The separate `general.replace_memory_card_title` setting owns the clean boot
ELF's 64-byte CP932 title slot at `0x2FBAE0`. Its fixed-value adapter guards the
original Japanese title and replaces it with `ＮＡ　ｖ２．２８`, with both values
NUL-terminated and zero-padded through the slot. The base configuration enables
it; setting it to `false` leaves the original title intact.

`general.replace_imported_game_title` owns the semantic replacement of
`Naruto Shippuden: Ultimate Ninja 5` in imported strings. Its catalog definition
guards the known six mappings and seven occurrences, and the string patcher
substitutes root `settings.title` before inline or linked-external placement. The
base configuration enables it; setting it to `false` leaves the imported title
unchanged. It is independent of both memory-card settings.

The full-width title form follows the official NUN5 memory-card convention. A
half-width ASCII test copied into a new save correctly but rendered as a blank
title in the USA PS2 BIOS. A longer full-width
`Ｎａｒｕｔｉｍａｔｅ　Ａｃｃｅｌ　ｖ２．２８` test rendered but wrapped at an unattractive
position, so the memory-card-title patch uses the shorter full-width title. Its
16 encoded bytes are followed by a NUL and 47 zero-padding bytes through the
original slot.
The shorter final title still requires acceptance in the PS2 memory-card
browser; this does not weaken the exact static guard or size-preservation proof.

## PCSX2 behavior and accepted consequences

PCSX2 uses its GameDB title for known serials. For a serial absent from the
GameDB, the Game List falls back to the scanned image filename. The local cache
confirmed this for the unknown `SLUS-55606`: `NUN6_A35.iso` appears as
`NUN6 A35`. Because normal project images are intentionally named
`Narutimate Accel v2.28 - Latest.iso` and
`Narutimate Accel v2.28 - Previous.iso`, `SLOP-NA228` appears in the Game List
under those corresponding names.

The runtime window title is a separate path. A game started from the populated
Game List has the path's scanned title available, so normal Game List launches
can retain `Narutimate Accel v2.28 - Latest` or `NUN6 A35`. A direct
command-line/`-batch` launch has no
scanned-entry title available during boot. PCSX2 2.6.3 then deliberately formats
an unknown serial as `<serial> [?]`. This was runtime-confirmed as
`SLUS-55606 [?]` for NUN6 A35 and `SLPS-22228 [?]` for an earlier modified
project identity. The active `SLOP-NA228` identity has not been separately
runtime-checked for this title behavior. The marker means PCSX2 found no GameDB
or per-path title for that boot path; it is not an ISO or serial-detection
error.

`SLOP-NA228` is also a separate PCSX2 identity for playtime, covers, save states,
per-game settings, compatibility metadata, and PNACH lookup. The stock
`SLPS-25837` GameDB entry includes compatibility settings that will not be
inherited automatically by the synthetic serial.

The project will **never install, modify, or maintain a custom PCSX2 GameDB
entry** to override this title or copy the stock compatibility entry. Directly
editing `@pcsx2_stable/cache/gamelist.cache` is likewise rejected because it is
generated, machine-local state.

The stable serial-wide cheat file is `@pcsx2_cheats/SLOP-NA228.pnach`.
It applies across CRC changes; optional group-level `crc =` metadata limits
individual groups. On 2026-07-24 the retained Current,
Previous, and Candidate images resolved respectively as `SLOP-NA228`,
`SLUS-NA228`, and `SLPS-22228`, all with CRC `6D94D520`; these identities are
derived state rather than hardcoded workflow configuration.

## Serial-wide PCSX2 configuration

The canonical NA2.28 PCSX2 files are
`@pcsx2_cheats/SLOP-NA228.pnach` and
`@pcsx2_game_settings/SLOP-NA228.ini`. PCSX2 discovers both recursively.
Ordinary GameSettings sections apply to every CRC; a
`[CRC.<8-hex-crc>.<section>]` section overrides one CRC. A named PNACH group
applies to every CRC unless it declares
`crc = <8-hex-crc>[,<8-hex-crc>...]`.

The serial-wide memory-card base is `NA v2.28.ps2`; configured launches select
the catalog-derived build card without rewriting GameSettings. No CRC-named
alias files are generated for NA2.28.

## PCSX2 identity log pattern

The clean-source historical `emulog.txt` identity line is:

```text
ELF Loading: cdrom0:\SLPS_258.37;1, Game CRC = 870F8722, EntryPoint = 0x00100008
```

After the product identity is assembled, the corresponding form is:

```text
ELF Loading: cdrom0:\SLOP_NA2.28;1, Game CRC = <crc>, EntryPoint = 0x00100008
```
