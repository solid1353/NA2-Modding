# Memory Card

Memory-card save presentation and identity are owned by
`features.memory_card` in `@builder/catalog.modcat`.

## Automatic loading

`features.memory_card.auto_loading` selects one patch for automatic first-save
loading and the single-slot Save/Load interface. `true` enables both behaviors;
`false` restores manual loading and the complete save-slot selection. The base
configuration enables it. This option remains editable in release configs.
`skip_initial_check`, `dedicated_save_namespace`, and `replace_memory_card_title`
are hidden from release exports and retain their embedded release values.

The automatic-loading part replaces Continue's per-frame visible-controller
update with a silent generated-C driver for the
same asynchronous memory-card worker and redirects the Save/Load child draw at
file offset `0xEA0D0` to a wrapper that suppresses ordinary silent loading.
It scans port zero, requests record
zero when present, internally resolves the native load confirmation as Yes,
waits through checksum-verified load completion, and then lets Continue perform
its unchanged cleanup, save-dependent setup, and main-menu loading.

Automatic loading treats no card, a wrong card type, an unformatted card, no
game directory, an empty first record, read/checksum failure, a card change, and
other non-success terminal worker results as no-load completion, except for a
supported older save awaiting upgrade consent. In those no-load cases,
the existing guarded result mapping enters the main menu without
loaded data. It does not synthesize a timeout while the native worker reports a
busy state.

For a supported version `0` save, automatic loading switches to the shared
visible Save/Load controller and enables its child draw. That controller owns
the upgrade confirmation and subsequent load flow described in
[Dedicated save namespace](#dedicated-save-namespace). The silent driver's
phase word marks visible-controller states with `0x100`; the marker is removed
before each native update and restored while it is pending. A successful load
publishes the ordinary loaded notification. Declining or failing the upgrade
closes through the native no-load result without a duplicate notification.

When the dedicated save has a readable but unsupported schema, automatic
loading reports `The existing save data uses version {found}. Version
{required} is required.` A native-only record reports version `0`. Other load
failures retain `Save data could not be loaded`.
The version warning uses three right-aligned lines, breaking after `data` and
after the first sentence, with 24 units between lines.
The same version result is consumed on scan, confirmation, and read failures,
including a directory-size rejection before the normal record read begins.

The main-menu notification is drawn after Mode Select's presentation, using its
prompt render context. It keeps a unit horizontal font scale for its
measurement and text draws, restores the previous scale and font context, and
remains in the menu's layer during the shared exit transition. The notification
ends when the Mode Select controller reaches its terminal state or its
ten-second display time expires.

### First-slot Save/Load interface

The same patch retains 12 guarded direct edits
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

## Skip the initial check

The `features.memory_card.skip_initial_check` patch skips
only the blocking card check before the splash and startup loaders. It replaces
`jal 0x001E71B0` at boot-ELF virtual address `0x001E0FA0` (file offset
`0xE10A0`, expected bytes `6C9C070C`) with a NOP. The persistent memory-card
worker and save-data initialization remain intact. The later Continue flow
still scans the card and loads save data through its own worker session.
This Boolean is independent of `auto_loading`: disabling it restores the early
native check, while disabling `auto_loading` restores manual loading and all
save slots. Fresh-boot runtime validation with and without a card remains
outstanding.

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
[`@builder/resources/save_appendix.tsv`](../../na228_builder/resources/save_appendix.tsv). The
appendix stores every runtime-editable Mod, Battle, Practice, Battle Mechanics,
Substitution, and Items setting as a stable ID and zero-based value.

The existing save operation serializes the appendix while writing the selected
primary and the rolling `data04` backup. Creation, free-space accounting,
missing-primary restoration, and descriptor reconstruction use the extended
record size, so repair copies the complete backup. Compatible saves use the
existing save prompts and operations.

The directory check rounds each file up to a 1 KiB block. Each extended record
therefore uses ten blocks instead of nine, making the complete save-set
requirement 107 blocks instead of 103.

Load validates the complete appendix before copying native profile state or
applying setting values. It rejects malformed records, padding or checksums,
unsupported versions,
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
A valid loaded save resets all settings to their configured defaults, then
applies every stored value. An absent newly introduced ID keeps its configured
default. There is no migration between the retail and dedicated
namespaces.

### Save appendix schema

The appendix contains every runtime-editable setting below
`features.default_settings`. The submenu switches in `features.menu_composition`
are build configuration and are not saved.

The first line declares `schema_version`. The table has four columns:

| Column | Meaning |
| --- | --- |
| `id` | Permanent, nonzero, four-digit hexadecimal field ID written to the save |
| `key` | Setting path resolved by the builder to its existing getter, setter, and configured default |
| `label` | Human-readable setting name |
| `values` | Zero-based saved-value order, written as ` \| ` choices or an inclusive `start to end by step` range |

IDs are grouped by Mod, Battle, Practice, Battle Mechanics, Substitution, and
Items. Never reuse or renumber an ID. The builder rejects duplicate IDs or
keys, unresolved or omitted settings, malformed value sequences, defaults
outside their declared values, and maps that exceed the fixed appendix
capacity. The TSV is a referenced build resource, so its exact contents are
included in the configuration fingerprint.

The appendix header contains the `NA2S` identifier, physical format version,
schema version, entry count, and CRC-32. Each entry is a four-byte ID/value
pair. Unused bytes are zero. The native descriptor checksum covers only the
native record; the appendix CRC-32 covers the whole appendix with its checksum
field treated as zero.

Increase `format_version` only when the physical appendix header, entry, or
checksum layout becomes incompatible. Increase `schema_version` only when an
existing ID changes meaning or encoding incompatibly. Adding a new ID does not
increase it. Before increasing `save_appendix.tsv`'s `schema_version`, the
agent must explicitly explain why the current schema cannot represent the
change, ask the user for approval, and stop until approval is given.

## Memory-card title

`features.memory_card.replace_memory_card_title` selects one guarded 64-byte
replacement in the clean boot ELF at `0x2FBAE0`. The `nul_padded_text` adapter
encodes both the original Japanese title and `ＮＡ　ｖ２．２８` as CP932,
requires a terminating NUL, and pads the remainder of the fixed slot with
zeroes. Setting it to `false` leaves the original title intact.

All four memory-card settings are enabled by the base configuration. Only
`auto_loading` is exposed in the release config.
