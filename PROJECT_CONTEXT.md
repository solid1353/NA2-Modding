# PROJECT_CONTEXT.md

Game: Naruto Shippuuden: Narutimate Accel 2
Platform: PlayStation 2
Serial: SLPS-25837
Boot ELF: SLPS_258.37

Goal: practical PCSX2 modding/translation/patching, not a native PC port.

This project currently has two mod parts:

- ISO changes: currently translation-only.
- PCSX2 PNACH changes: currently logic/gameplay/default-setting mods.

## Verified Local State

Original ISO:

- Path: `source/NA2.iso`
- Size: `1,928,429,568`
- SHA256: `CA105F7BDBEEAA3275F871C9702B9C77ED985CE140FAE8EAC28CB153E263D0C3`

Current modded ISO:

- Path: `build/NA2 Mod.iso`
- Size: `1,928,429,568`
- SHA256: `C055242C95D48077B70E1B96E085D792E9930CA7FE528552214FEFCB1F6DF8AF`

Current PNACH:

- Canonical editable PNACH: `cheats/C0659AD1.pnach`
- Actualized PNACH hardlinks live in `cheats/SLPS-25837_<crc>.pnach`.
- Root `cheats/` is a real project folder and the only cheats folder we manage.
- Live PNACH size when inspected: `1059` bytes.

Current PNACH sections:

- Widescreen 16:9
- Skip CC2 intro
- Skip opening
- Sub cost = 3/15
- Disable RPS
- Simple display off
- Practice voice off by default
- Practice support off by default
- Practice command display off by default
- Disable extra hit with aura punishment
- Commented-out Disable extra hit patch

## Working Layout

- `source/`: untouched source media. Do not modify unless explicitly instructed.
- `source/*.files/`: extracted views of original source archives. Treat as read-only reference.
- `build/`: active working outputs, including current modded ISO and current PNACH.
- `releases/`: symlink to `C:\Users\solid\Documents\Mods\NA2\releases`; frozen milestone artifacts only. Append-only; never alter existing contents.
- `logs/`: inventories, hashes, patch records, and investigation notes.
- `scripts/`: repeatable tooling.
- `trash/`: timestamped holding area for deleted/retired workspace items.
- `old/`: user's personal folder. Off-limits unless explicitly instructed.

Scratch/intermediate folders should be created only when needed and named for the task. Extractions of original source archives stay beside the source archive under `source/`.

## Trash Rule

Use `trash/` for project-local removals instead of hard deletion when practical. Trash batches are timestamped and include a manifest/log.

Never trash or delete anything under:

- `source/`
- `release/`
- `trash/`

Use `scripts/move_to_trash.ps1` for safe project-local trash moves.

## Extraction Layout

All extracted original files stay under `source/`, beside the archive they came from.

Current original ISO extraction:

- `source/NA2.iso`
- `source/NA2.iso.files/`

Nested archive convention:

- Keep the archive file at its natural path in the extracted tree.
- Put that archive's extracted contents beside it in a sibling folder named `<archive filename>.files`.
- Repeat the same rule for archives inside archives.

Example:

```text
original/
  NA2.iso
  NA2.iso.files/
    SYSTEM.CNF
    SLPS_258.37
    DATA/
      DATA.CVM
      DATA.CVM.files/
        ...
      SOUND.AFS
      SOUND.AFS.files/
        ...
    PRG/
      BTL.BIN
      ETC.BIN
```

For edited/build versions, do not edit anything under `source/` in place. Copy the needed file or archive into a task/build folder first, then patch that copy through scripts and log the source path and output path.

The `source/` tree should also have Windows read-only attributes applied. Use `scripts/set_original_readonly.ps1` after extracting new original-source content or if attributes need to be restored.

## Current Scripts

- `check_translation_lengths.ps1`: checks CP932 byte lengths for translation tables.
- `extract_afs.ps1`: extracts AFS archives for inspection when needed.
- `inventory_project.ps1`: creates timestamped inventory/hash reports under `logs/`.
- `set_original_readonly.ps1`: applies and verifies Windows read-only attributes under `source/`.
- `move_to_trash.ps1`: moves project-local files/folders to timestamped `trash/` batches and refuses protected folders.
- `check_pcsx2_crc.ps1`: reads PCSX2 logs for the latest boot Game CRC and compares it with a PNACH filename.
- `create_milestone_release.ps1`: creates a new append-only milestone folder under `releases/`; refuses existing names and records a manifest.

## Utils Dump

Top-level `old/` is personal user space and should not be inspected, searched, executed from, modified, moved, deleted, or otherwise touched unless the user explicitly asks for it.

`utils/old/` is an untrusted historical tool/archive dump. It may contain useful tools or source references, but nothing there should be treated as current workflow or executed blindly.

Observed examples include AFS tools, CCS tools, Ghidra/EmotionEngine material, Kuriimu, PS2Dis, PSS tools, StudioCCS variants, and many unknown `.bin` files. Inspect and select a tool for a specific task before using it.

## Release Folder Rule

`releases/` is for milestone outputs only. Existing contents are frozen.

Allowed:

- Create a new uniquely named milestone file/folder.

Not allowed:

- Modify an existing release file.
- Overwrite an existing release file.
- Rename, move, or delete anything under `releases/`.
- Auto-pick a different name after a collision.

If an intended `releases/` output path already exists, stop immediately and inspect/report manually.

Every release PNACH must match the PCSX2 CRC for the boot ELF inside the paired release ISO. Before calling a release valid, check the ISO/ELF CRC against the PNACH filename suffix. If the CRC does not match, warn. If it cannot be verified, say so explicitly.

## CRC / PNACH Notes

PCSX2 cheat filenames include the game CRC, for example:

`SLPS-25837_BCB73695.pnach`

If the boot ELF inside the ISO changes, PCSX2 may report a different CRC. Actualize creates a matching `cheats/SLPS-25837_<crc>.pnach` hardlink to `cheats/C0659AD1.pnach`.

PCSX2 should use the project root `cheats/` folder for this mod workflow.

Known PCSX2 paths from prior notes:

- Log: `C:\Games\Emulators\PCSX2 2.6.2\logs\emulog.txt`
- Game settings: `C:\Games\Emulators\PCSX2 2.6.2\gamesettings`
- Cheats: project root `cheats/`

Known log pattern:

`ELF Loading: cdrom0:\SLPS_258.37;1, Game CRC = 870F8722, EntryPoint = 0x00100008`

## Prior GPT Handoff Notes

The following are transferred notes/hypotheses from earlier ChatGPT work. Treat them as leads, not verified facts, unless re-confirmed locally.

Original observed PCSX2 CRC from prior notes: `C0659AD1`

File role hypotheses:

- `SLPS_258.37`: main PS2 ELF/executable. May contain code and embedded strings. Replacing it can change PCSX2 Game CRC.
- `BTL.BIN`: battle/practice data. Claimed to contain battle UI/practice/settings strings.
- `ETC.bin`: misc/extras/collection/shop-ish data. Claimed to contain collection/shop/extras strings, item names, some jutsu/location/name/title strings.
- `ADV.bin`: adventure/master/story-ish data. Prior translated ADV reportedly crashed; do not include or modify unless explicitly requested.
- `GF4.BIN`, `GF4C.BIN`, `GRF4.BIN`, `SF1.BIN`, `SF1C.BIN`: likely graphics/font/resource containers; not confirmed safe string targets.
- `logo.ccs`: likely startup/logo texture/animation data, not normal string translation.
- PSS files: movie/video files. Do not delete/rename blindly.
- AFS files: archives, not directly playable audio streams. Extract first, then inspect contained files.

Prior package mentioned:

- `narutimate_translation_latest_all_v6_substantial.zip`
- Claimed contents: `BTL.BIN`, `ETC.bin`, `SLPS_258.37`, `translation_v6_log.tsv`
- Claimed stats: 238 exact replacements, 14 offset-based replacements, 17 already-present strings.

Prior known PNACH patch notes:

- RPS Disable / Consume Circle
- Intro/logo PSS skip
- Opening skip
- Widescreen

Prior warnings:

- Do not continue blind startup/logo PNACH guessing; prior static guesses reportedly caused black screens/hangs.
- Do not include `ADV.bin` unless explicitly requested.

## Translation Strategy

- Preserve byte budgets unless a pointer relocation/free-space strategy is explicitly developed.
- Use exact replacements where possible.
- Use offset-based replacements only when logged and justified.
- For string patches, check CP932/Shift-JIS byte length before writing.
- Some visible Japanese may be textures/CCS, not text.

## CVM Notes

DATA.CVM password: cc2fuku.

## Actualize Workflow

When asked to actualize, use the ISO in `build/` by default. Calculate the PCSX2-style ELF CRC from the boot ELF inside that ISO, rename `pcsx2/gamesettings/SLPS-25837_********.ini` to match the actual CRC, and create `cheats/SLPS-25837_<crc>.pnach` as a hardlink to `cheats/C0659AD1.pnach` if it does not already exist.

## Release Workflow

Release root is `C:\Users\solid\Documents\Mods\NA2\releases`, exposed through the root `releases/` symlink. Before release, ask for the release name and confirm the release file list and ISO source. Default ISO source is the ISO in `build/`. Then actualize, extract/copy the current release files to `releases/<release_name>/`, and stop if any target path already exists.

Current release file list is tracked in `release_files.txt`: `BTL.BIN`, `ETC.BIN`, boot ELF `SLPS_258.37`, actualized game settings INI, and actualized PNACH.



