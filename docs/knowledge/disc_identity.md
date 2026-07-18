# Modified disc identity

## Decision

The modified project image uses the synthetic serial `SLPS-22228`. The clean
NA2 source remains `SLPS-25837` and is never modified.

The serial alternatives considered on 2026-07-18 were rejected as follows:

- `SLPS-25838` is assigned to *Taiheiyou no Arashi: Senkan Yamato, Akatsuki ni
  Shutsugeki su* in the installed PCSX2 GameDB.
- `SLPS-00228` is the PlayStation release *Policenauts: Private Collection*.
- `SLPS-22228` was absent from the installed PCSX2 PS2 GameDB and no issued-disc
  match was found during the investigation. The project treats it as a
  synthetic identifier; this is not a claim that Sony formally reserved it.

## Reproducible implementation

The hash-pinned `disc_identity_v1` profile module performs two guarded,
equal-length edits after every file-backed module has been composed:

1. `SYSTEM.CNF` changes `SLPS_258.37` to `SLPS_222.28`.
2. The ISO9660 root directory record changes `SLPS_258.37;1` to
   `SLPS_222.28;1`.

The second edit is ISO filesystem metadata, not an ELF string replacement, so
it deliberately does not belong to the `string_replacements` patch set. The
composer logs both original and replacement bytes and verifies the one declared
tree rename. No file extent, file size, or ISO size changes.

The internal save-data directory `BISLPS-25837NARUTO5` remains unchanged. This
preserves compatibility with existing saves. The separate ELF save-title patch
uses the full-width CP932 title `ＮＡ　ｖ２．２８`.

## PCSX2 behavior and accepted consequences

PCSX2 uses its GameDB title for known serials. For a serial absent from the
GameDB, the Game List falls back to the scanned image filename. The local cache
confirmed this for the unknown `SLUS-55606`: `NUN6 A35.iso` appears as
`NUN6 A35`. Because normal project images are intentionally named `Current.iso`
and `Previous.iso`, `SLPS-22228` appears in the Game List as `Current` or
`Previous` rather than `Narutimate Accel v2.28`.

The runtime window title is a separate path. A game started from the populated
Game List has the path's scanned title available, so normal Game List launches
can retain `Current` or `NUN6 A35`. A direct command-line/`-batch` launch has no
scanned-entry title available during boot. PCSX2 2.6.3 then deliberately formats
an unknown serial as `<serial> [?]`. This was runtime-confirmed as
`SLUS-55606 [?]` for NUN6 A35 and `SLPS-22228 [?]` for the modified project
image. The marker means PCSX2 found no GameDB or
per-path title for that boot path; it is not an ISO or serial-detection error.

`SLPS-22228` is also a separate PCSX2 identity for playtime, covers, save states,
per-game settings, compatibility metadata, and PNACH lookup. The stock
`SLPS-25837` GameDB entry includes compatibility settings that will not be
inherited automatically by the synthetic serial.

The project will **never install, modify, or maintain a custom PCSX2 GameDB
entry** to override this title or copy the stock compatibility entry. Directly
editing `@pcsx2/cache/gamelist.cache` is likewise rejected because it is
generated, machine-local state.

The canonical PNACH remains
`@pcsx2_files/SLPS-25837_C0659AD1.pnach`. Actualization derives the active serial
from `SYSTEM.CNF`, creates `@pcsx2/cheats/SLPS-22228_<crc>.pnach` for the modified
image, and removes obsolete managed aliases without touching unrelated files.
