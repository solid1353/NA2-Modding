# General

Project-wide selectable behavior that does not belong to gameplay, rendering,
localization, or quality-of-life categories. Selectable nodes and guarded edits
are owned by `features.general` in `na228_builder/catalog/catalog.modcat`.

## Dedicated save namespace

`general.dedicated_save_namespace` selects two guarded, equal-length boot-ELF
replacements at file offsets `0x2FBAC1` and `0x2FBBF0`. They replace the stock
NA2 memory-card directory name `BISLPS-25837NARUTO5` with the dedicated NA228
name `BASLOP-NA228NARUTO6` without changing the ELF size.

The base configuration enables the setting. Setting it to `false` leaves the
stock directory name intact, so NA228 and NA2 address the same saved data.
Changing the setting does not copy or migrate saves between the two names.

## Imported game title

`general.replace_imported_game_title` replaces the imported NUN5 title
`Naruto Shippuden: Ultimate Ninja 5` with root `settings.title` before the
string patcher decides which strings stay inline and which use linked external
storage. Its catalog definition guards the known six mappings and seven total
occurrences. Setting it to `false` leaves the imported title unchanged.

## Memory-card title

`general.replace_memory_card_title` selects one guarded 64-byte replacement in
the clean boot ELF at `0x2FBAE0`. The `nul_padded_text` adapter encodes both the
original Japanese title and `ＮＡ　ｖ２．２８` as CP932, requires a terminating
NUL, and pads the remainder of the fixed slot with zeroes. Setting it to
`false` leaves the original title intact.

Both title settings are enabled by the base configuration. They are independent
of each other and of `general.dedicated_save_namespace`.
