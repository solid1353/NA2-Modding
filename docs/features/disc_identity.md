# Modified disc identity

## Decision

`features.general.disc_identity` selects the built disc's identity:

| Value | Disc serial | Boot filename |
| --- | --- | --- |
| `"NA2"` | `SLPS-25837` | `SLPS_258.37` |
| `"NUN5"` | `SLES-55605` | `SLES_556.05` |
| `"NA228"` | `SLOP-NA228` | `SLOP_NA2.28` |

The [base configuration](../../na228_builder/configurations/base.jsonc) selects
`"NA228"`. The [release configuration](../../na228_builder/configurations/release.jsonc)
overrides it with `"NUN5"` so consumers see an English game title and a
**Playable** compatibility rating in PCSX2. NUN5 and NA2 receive identical
automatic compatibility fixes. The rating is a database label, not evidence
of different compatibility between these identity choices.

The clean NA2 source remains unchanged. Selecting a disc identity does not
change NA228's in-game title, content, or NTSC video output.

## Reproducible implementation

The catalog setting selects patch `general.disc_identity`, whose image
operation is `select_disc_identity`. The configuration loader resolves its
value to the output boot filename. `"NA228"` uses root `game.json`'s
`output_boot_path`; `"NA2"` retains the source filename and emits no identity
edits. Disabling the setting with `false` also retains the source identity,
following the catalog's standard disabling behavior.

For a changed identity, the product composer emits a guarded replacement of
the boot filename in `SYSTEM.CNF` and an equal-length boot-file rename. The
image assembler applies the rename to both ISO9660 and UDF, logs the edits,
and verifies the final tree. Identity selection preserves file extents, file
sizes, and ISO size.

`SYSTEM.CNF` retains `VMODE = NTSC`, and the identity patch does not alter
NA2's video initialization, which selects NTSC through `SetGsCrt` mode `2`.
The European region label from the NUN5 identity does not convert the game to
PAL. This conclusion is based on code and built-byte inspection, not a
runtime test of the NUN5-labelled build.

## Independent save and title settings

The separate `memory_card.dedicated_save_namespace` catalog setting owns the clean
boot ELF's two 19-byte memory-card directory fields at `0x2FBAC1` and
`0x2FBBF0`. When enabled, its guarded binary edits change
`BISLPS-25837NARUTO5` to `BASLOP-NA228NARUTO6`. It is enabled in the base
configuration. Setting it to `false` leaves the stock name intact, so NA228
shares NA2's save data. Existing `.ps2` memory cards and data remain untouched,
and changing the setting does not migrate data between the two names.

The separate `memory_card.replace_memory_card_title` setting owns the clean boot
ELF's 64-byte CP932 title slot at `0x2FBAE0`. Its fixed-value adapter guards the
original Japanese title and replaces it with `ＮＡ　ｖ２．２８`, with both values
NUL-terminated and zero-padded through the slot. The base configuration enables
it; setting it to `false` leaves the original title intact.

`general.replace_imported_game_title` owns the semantic replacement of
`Naruto Shippuden: Ultimate Ninja 5` in imported strings. Its catalog definition
guards the expected coverage declared in the patch, and the string patcher
substitutes root `game.json`'s `title` before inline or linked-external placement. The
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

With PCSX2's database titles, the consumer-visible comparison is:

| Displayed information | `"NA2"` identity | `"NUN5"` identity |
| --- | --- | --- |
| Game title | NARUTO-ナルト- 疾風伝 ナルティメットアクセル2 | Naruto Shippuuden - Ultimate Ninja 5 |
| Title with English game titles preferred | Naruto Shippuuden - Narutimate Accel 2 | Naruto Shippuuden - Ultimate Ninja 5 |
| Region | Japan (`NTSC-J`) | Europe (`PAL-M5`) |
| Compatibility rating | Unknown | Playable |

The installed PCSX2 database and the
[upstream GameIndex](https://github.com/PCSX2/pcsx2/blob/master/bin/resources/GameIndex.yaml)
were checked on 2026-09-06. Both retail identities declare exactly these fixes:

| Compatibility setting | Value for both identities |
| --- | --- |
| `SoftwareRendererFMVHack` | Enabled |
| `halfPixelOffset` | `2` |
| `nativeScaling` | `2` |
| `vu0ClampMode` | `3` |
| `vu1ClampMode` | `3` |

The VU1 clamp entry addresses character polygon spikes. PCSX2 selects these
database settings by disc serial; the NUN5 identity therefore supplies the
same fixes as NA2 for an NA2-based build, with automatic game fixes enabled.

The synthetic `"NA228"` identity has no database entry and does not inherit
these fixes automatically. Its Game List title falls back to the scanned ISO
filename unless the user assigns a custom title. Build filenames are owned by
the [builder's build contract](../../na228_builder/README.md#build).

The project will **never install, modify, or maintain a custom PCSX2 GameDB
entry** to override this title or copy the stock compatibility entry. Directly
editing `@pcsx2_dev/cache/gamelist.cache` is likewise rejected because it is
generated, machine-local state.

## Serial-wide PCSX2 configuration

The canonical NA2.28 PCSX2 files are
`@pcsx2_files/games/NA228/NA228.pnach` and
`@pcsx2_files/games/NA228/NA228.ini`. The project launcher passes the PNACH
explicitly, while PCSX2 discovers GameSettings recursively.
Ordinary GameSettings sections apply to every CRC; a
`[CRC.<8-hex-crc>.<section>]` section overrides one CRC. A named PNACH group
applies to every CRC unless it declares
`crc = <8-hex-crc>[,<8-hex-crc>...]`.

Configured launches use `@pcsx2_files/games/NA228/NA228.ps2` without rewriting
GameSettings. No CRC-named alias files are generated for NA2.28.

The `NA228` content alias declares `SLOP-NA228` as its canonical local identity.
Every image resolved to that alias uses `SLOP-NA228` for savestate names,
debugger settings, and playtime while retaining its detected serial and CRC for
GameDB fixes, achievements, and diagnostics. Savestate names retain the detected
CRC so incompatible builds do not silently share states. Exact serial-and-CRC
content aliases still take precedence, so the clean NA2 and NUN5 images continue
to use their own local identities.
