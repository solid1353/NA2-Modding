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

The active profile's `identity.json` declares the clean boot path, output boot
path, `SYSTEM.CNF` path, and guarded CP932 memory-card title. After feature
modules have been composed, the profile composer emits two guarded replacements
and one equal-length file rename:

1. `SYSTEM.CNF` changes `SLPS_258.37` to `SLOP_NA2.28`.
2. The clean boot ELF's 64-byte title slot at `0x2FBAE0` changes from
   `ＮＡＲＵＴＯ－ナルト－　疾風伝ナルティメットアクセル２` to `ＮＡ　ｖ２．２８`.
3. The ISO9660 root directory record changes `SLPS_258.37;1` to
   `SLOP_NA2.28;1`.

The third operation is ISO filesystem metadata, not an ELF string replacement,
so it deliberately does not belong to a feature module. The mandatory image
assembler applies it to both ISO9660 and UDF, logs all four identity edits, and
verifies the declared final tree. No file extent, file size, or ISO size changes.

The internal save-data directory `BISLPS-25837NARUTO5` remains unchanged. This
preserves compatibility with existing saves.

The full-width title form follows the official NUN5 memory-card convention. A
half-width ASCII test copied into a new save correctly but rendered as a blank
title in the USA PS2 BIOS. A longer full-width
`Ｎａｒｕｔｉｍａｔｅ　Ａｃｃｅｌ　ｖ２．２８` test rendered but wrapped at an unattractive
position, so the profile uses the shorter full-width title. Its 16 encoded bytes
are followed by a NUL and 47 zero-padding bytes through the original slot.
The shorter final title still requires acceptance in the PS2 memory-card
browser; this does not weaken the exact static guard or size-preservation proof.

## PCSX2 behavior and accepted consequences

PCSX2 uses its GameDB title for known serials. For a serial absent from the
GameDB, the Game List falls back to the scanned image filename. The local cache
confirmed this for the unknown `SLUS-55606`: `NUN6 A35.iso` appears as
`NUN6 A35`. Because normal project images are intentionally named
`NA2.28 - Current.iso` and `NA2.28 - Previous.iso`, `SLOP-NA228` appears in the
Game List as `NA2.28 - Current` or `NA2.28 - Previous` rather than
`Narutimate Accel v2.28`.

The runtime window title is a separate path. A game started from the populated
Game List has the path's scanned title available, so normal Game List launches
can retain `NA2.28 - Current` or `NUN6 A35`. A direct command-line/`-batch`
launch has no
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

The stable cheat template is `@pcsx2_cheats/SLOP-NA228.pnach`. Actualization derives each
retained image's alphanumeric serial from `SYSTEM.CNF`, creates matching
`@pcsx2_cheats/<serial>_<crc>.pnach` aliases, and removes obsolete managed
aliases without touching unrelated files. On 2026-07-24 the retained Current,
Previous, and Candidate images resolved respectively as `SLOP-NA228`,
`SLUS-NA228`, and `SLPS-22228`, all with CRC `6D94D520`; these identities are
derived state rather than hardcoded workflow configuration.
