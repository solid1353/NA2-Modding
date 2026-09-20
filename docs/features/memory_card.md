# Memory Card

Memory-card save presentation and identity are owned by
`features.memory_card` in `@builder/catalog.modcat`.

## Display only the first save

`features.memory_card.display_only_first_save` retains 12 guarded direct edits
for presentation and navigation. They change the shared Save/Load slot-row
renderer's loop limit from three records to one at boot-ELF virtual address
`0x001E6970` (file offset `0xE6A70`) and replace the handler's Down and Up
input-mask results with zero before either movement branch. The three-slot
occupancy scan, save data, and memory card remain unchanged; vertical input
cannot change the selected slot or play the slot-navigation sound.

The upper frame is reduced from X/Y/width/height `58/10/400/224` to
`146/90/224/96`, placing a compact one-record panel above and visibly detached
from the unchanged lower instruction panel. Within it, the date/play-time block
moves from local X `108`, Y `14` to X `45`, Y `20`. The redundant slot-number
record moves outside the viewport, the row-separator condition is disabled, and
the now-meaningless independent slot-cursor model is not drawn. The lower
instruction panel and all of its contents remain unchanged.

The controller behavior is implemented by one generated-C wrapper at virtual
`0x001E3F08` (file `0xE4008`), the sole call from `FUN_001e3f00` to the clean
visible-controller update `FUN_001e3f20`. It handles only the state-machine
branches needed to select record zero and bypass the removed list, retaining
the native scan, status UI, confirmations, load/save requests, result
resolution, and frame-counter tails. Every unaffected frame delegates exactly
once to `FUN_001e3f20`. When the dedicated namespace is enabled, its version
dialog wraps this controller through the same single hook. The automatic
startup hook at file `0xEA084` replaces the outer call to `FUN_001e3f00`. Its
ordinary silent loading bypasses this wrapper; a supported older save enters
the shared visible flow to obtain upgrade consent.

The native `Load this data?` confirmation remains visible. Yes continues the
record-zero load; No enters Save/Load completion state `8` instead of
reconstructing the removed record list. The startup Continue result mapping at
runtime `0x001E9FB8` (file offset `0xEA0B8`) then uses the existing success path
to enter the main menu without loaded save data.

## Dedicated save namespace

`features.memory_card.dedicated_save_namespace` owns the dedicated directory
name and save format together. Its two guarded, equal-length boot-ELF
replacements at file offsets `0x2FBAC1` and `0x2FBBF0` replace
`BISLPS-25837NARUTO5` with `BASLOP-NA228NARUTO6` without changing the ELF
size. Disabling the setting leaves both the retail namespace and retail record
format intact.

An enabled dedicated save extends each `dataNN` record from `0x2400` to
`0x2600` bytes. The native profile remains `0x2400` bytes in memory and keeps
its native descriptor checksum. Card I/O uses a temporary record with a fixed
`0x200`-byte settings appendix described by
[`@builder/save_appendix.tsv`](../../na228_builder/save_appendix.tsv). The
appendix stores every runtime-editable Mod, Battle, Practice, Battle Mechanics,
Substitution, and Items setting as a stable ID and zero-based value. Its header
identifies the format and schema and protects the complete appendix with
CRC-32.

The existing save operation serializes the appendix while writing the selected
primary and the rolling `data04` backup. Creation, free-space accounting,
missing-primary restoration, and descriptor reconstruction use the extended
record size, so repair copies the complete backup. Compatible saves use the
existing save prompts and operations.

The directory check rounds each file up to a 1 KiB block. Each extended record
therefore uses ten blocks instead of nine, making the complete save-set
requirement 107 blocks instead of 103.

Load validates the complete appendix before copying native profile state or
applying setting values. It rejects malformed records, unsupported versions,
unknown or duplicate IDs, invalid values, and earlier native-only records in
the dedicated namespace. A native-only record reports schema version `0`, and
a readable unsupported appendix reports its stored schema version. The worker's
directory check can reject a save before the record-load hook runs. The wrapper
at ELF file offset `0xE22F8` probes all four records before loading or saving,
so an older primary cannot hide a newer backup. It checks both a directory-size mismatch and an otherwise
valid directory, so equal-length records with a different schema are also
recognized. A confirmed mismatch idles the worker with a separate status before
native corruption/recovery dispatch. Other errors retain native handling.

The supported upgrade is native-only version `0` to schema `1`. Visible loading
and saving show the versions, then ask `Upgrade the existing save data?` with
`Your progress will be kept.` and No selected. Automatic loading enters this
same visible flow for the supported older version. Declining closes without
writing. Accepting requests conversion on the card worker, then rescans and
resumes the existing load or save flow, including its normal confirmations.
Upgrade consent does not authorize saving the current live profile over the
converted progress. Newer versions and unknown formats are never converted;
automatic loading retains its existing failure notice for those versions.

Before writing, conversion reads the descriptor table and all four records,
checks the table structure and every occupied native checksum, builds the new
appendices, and validates them. Each native `0x2400`-byte record is preserved
byte-for-byte, including controller mappings and progress. The descriptor table,
timestamps, and icons are not rewritten. The older format stored none of the
appendix settings, so those values come from configured defaults without
changing the current live settings. There is no generic conversion for an
unknown schema or encoding; another supported upgrade needs an explicit
conversion for that source version.

Only native-only records are written. Already-current records retain their
saved settings; erased empty current records remain erased. The worker uses
exact transfer counts, flushes and closes each write, then checks the file size
and compares a full readback with the converted record. `data04` is written
last. An upgrade failure shows `The save data could not be upgraded.` and
closes without invoking native repair or saving the current profile. The set
is not atomic: a write failure may leave some records upgraded, and no rollback
is provided. A mixture of complete old and current records can be retried.

The visible wrapper shares the existing hook at ELF offset `0xE4008`. It
delegates other frames to the first-save controller when selected, or directly
to the native controller otherwise. Dialog text uses four NUL-terminated line
slots. The version notice uses up to three text lines and the upgrade question
has two, leaving room for the native Yes/No row. The dedicated namespace owns
the wrapper; no second overlapping hook is emitted.

Other invalid appendix failures retain the generic load-failure message.
Configuration values initialize every setting; a valid save then
overrides the stored IDs, while an absent newly introduced ID keeps its
configured default. There is no migration between the retail and dedicated
namespaces.

## Memory-card title

`features.memory_card.replace_memory_card_title` selects one guarded 64-byte
replacement in the clean boot ELF at `0x2FBAE0`. The `nul_padded_text` adapter
encodes both the original Japanese title and `ＮＡ　ｖ２．２８` as CP932,
requires a terminating NUL, and pads the remainder of the fixed slot with
zeroes. Setting it to `false` leaves the original title intact.

The three settings are enabled by the base configuration and remain
independently selectable.
