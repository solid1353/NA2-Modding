# Memory Card

Memory-card save presentation and identity are owned by
`features.memory_card` in `@builder/catalog.modcat`.

## Dialogue flow

`features.memory_card.dialogs_rework` enables the shared format/create-data
confirmation flow regardless of `auto_loading`: Save skips the separate
unformatted-card notice, formatting starts with No selected, and the native
confirmation handlers retain the localized controls.

Declining formatting, save-data creation, or overwrite enters native closing
state `9`. The controller waits for the visible panels to finish their normal
shrinking animation before returning completion through state `11`.

One hook at virtual `0x001E3F08` (file `0xE4008`) routes visible Save/Load
updates through the shared controller. The extended-save wrapper adds a
settings-reset notice after a successful load when the appendix schema differs.
Other frames continue to the single-slot controller when `auto_loading` is
enabled, or directly to native `FUN_001E3F20` otherwise. Disabling
`dialogs_rework` bypasses the shared dialogue controller. Each frame advances
only one controller path. Text translation, font layout, and regional buttons
remain localization-owned.

## Automatic loading

`features.memory_card.auto_loading` enables automatic first-save loading and
the single-slot Save/Load interface. Disabling it restores manual loading and
the complete save-slot selection. The base configuration enables it. This is
the only memory-card option editable in release configs; `dialogs_rework`,
`skip_initial_check`, and `extended_save_data` retain their embedded values.

Continue uses a silent generated-C driver for the asynchronous memory-card
worker. It scans port zero, requests record zero when present, internally
answers the native load confirmation Yes, and waits for checksum-verified load
completion. Continue then performs its native cleanup, save-dependent setup,
and main-menu loading. A wrapper at file offset `0xEA0D0` suppresses the
ordinary Save/Load child draw during silent loading.

No card, wrong card type, unformatted card, absent game directory, empty first
record, read/checksum failure, card change, and other terminal worker failures
continue to the main menu without loaded data. Busy worker states are allowed
to finish. An absent mod directory or empty first record reports `No save data
found`; failed reads report `Save data could not be loaded`.

After a successful load, a right-aligned main-menu notice shows the load
result, play time, and saved time. When the appendix schema differs, it also
shows `Mod settings were reset because their format changed.` The notice uses
Mode Select's prompt render context, restores the prior scale and context,
and ends when Mode Select terminates or ten seconds pass.

### First-slot Save/Load interface

The patch retains 12 guarded direct edits for presentation and navigation.
They change the slot-row loop limit from three records to one at virtual
`0x001E6970` (file `0xE6A70`) and replace Down and Up input-mask results
with zero. The card's occupancy scan and stored records are unchanged.

The upper frame changes from X/Y/width/height `58/10/400/224` to
`146/90/224/96`. The date/play-time block moves from local X `108`, Y `14`
to X `45`, Y `20`; the slot number and cursor are hidden and the row separator
is disabled. The lower instruction panel remains unchanged. The empty-slot
label is measured from localized text and centered after its native slide.

The single-slot controller selects record zero and retains the native scan,
status UI, load/save requests, result resolution, and frame-counter tails.
The native `Load this data?` confirmation remains visible. Yes loads record
zero; No completes Save/Load through state `8` and returns to the main menu.

## Skip the initial check

`features.memory_card.skip_initial_check` skips only the blocking card check
before the splash and startup loaders. It replaces `jal 0x001E71B0` at
virtual `0x001E0FA0` (file `0xE10A0`, expected bytes `6C9C070C`) with a
NOP. The memory-card worker and save-data initialization remain intact.
Disabling this option restores the early native check independently of
automatic loading. Fresh-boot validation with and without a card remains
outstanding.

## Extended save data

`features.memory_card.extended_save_data` owns the mod directory, memory-card
title, and settings appendix together. Two guarded 19-byte boot-ELF edits at
`0x2FBAC1` and `0x2FBBF0` replace `BISLPS-25837NARUTO5` with
`BASLOP-NA228NARUTO6`. A guarded 64-byte CP932 title edit at `0x2FBAE0`
replaces the Japanese title with `ＮＡ　ｖ２．２８`. Disabling the option uses
the original directory, title, and native record format, with no appendix.
The mod directory is separate from retail saves; retail saves are not loaded
when extended save data is enabled.

Each mod `dataNN` record is `0x3400` bytes: the native `0x2400`-byte profile
and a fixed `0x1000`-byte settings appendix. The native profile and its
descriptor checksum are unchanged. The appendix stores runtime-editable Mod,
Battle, Practice, Battle Mechanics, Substitution, and Items settings as stable
IDs and zero-based values. With `features.general.new_controls` enabled, it
also stores the Guard and Substitution bindings for each player; native
Guard/Sub actions remain in the native profile.

Normal saves serialize the appendix for the selected primary and rolling
`data04` backup. Creation, free-space accounting, missing-primary restoration,
and descriptor reconstruction use the extended record size, so repair copies
the full backup. Each extended record occupies 13 one-KiB blocks; the full
save-set requirement is 119 blocks. Existing save prompts and results apply.

Loads validate the record size, native checksum, appendix header, CRC-32,
entry count, IDs, and zero padding before applying data. Malformed records use
the existing load failure and recovery handling. A physically valid appendix
with a matching schema loads native progress and preferences, initializes all
mod settings to configured defaults, then applies known saved IDs. Missing
new IDs keep their defaults; unknown retired IDs are ignored. IDs are never
reused. Known IDs with out-of-range values, duplicate IDs, and invalid entry
bounds fail validation.

A physically valid appendix with a different schema loads the native profile,
including progress, preferences, and control mappings, but resets **all**
appendix settings, including Guard and Substitution bindings, to configured
defaults. The ordinary successful-load notice is followed by `Mod settings
were reset because their format changed.` No load path writes the card; the
current format is written on the next ordinary save.

### Save appendix schema

[`@builder/resources/save_appendix.tsv`](../../na228_builder/resources/save_appendix.tsv)
lists every saved setting. Submenu switches in `features.menu_composition` are
build configuration and are not saved. The first line declares
`schema_version`; the table has these columns:

| Column | Meaning |
| --- | --- |
| `id` | Permanent, nonzero, four-digit hexadecimal field ID written to the save |
| `key` | Setting path resolved to its getter, setter, and configured default |
| `label` | Human-readable setting name |
| `values` | Zero-based saved-value order |

The builder rejects duplicate IDs or keys, missing or unresolved settings,
malformed values, invalid defaults, and schemas beyond the 1020-entry
capacity. The TSV participates in the configuration fingerprint.

The `0x10`-byte header holds the `NA2S` identifier, physical format version,
schema version, entry count, and CRC-32. Each entry is a four-byte ID/value
pair; unused bytes are zero. The appendix CRC-32 covers all `0x1000` bytes
with the checksum field treated as zero.

Increase `format_version` only for an incompatible physical layout. Increase
`schema_version` only when an existing ID changes meaning or encoding
incompatibly; adding an ID does not require a bump. A bump resets all appendix
settings on load. Before changing `save_appendix.tsv`'s `schema_version`,
explain why the current schema cannot represent the change and ask for the
user's approval. It remains at version `1` for this implementation.
