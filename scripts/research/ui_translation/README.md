# UI runtime capture

`ui_runtime.py` captures controlled PCSX2 runtime evidence for the NUN5-to-NA2
UI translation investigation. It can archive matching manual F1 states without
touching a running emulator, or connect to PCSX2's local PINE server for a new
single capture or targeted read-only memory inspection. It does not launch
PCSX2 or automate controller input.

The normal comparison has two targets:

- `nun5`: the official English reference at `@source/NUN5.iso`.
- `current`: the current project image selected by `project-paths.json`.

Vanilla NA2 is not part of the routine capture path. Use it only when a result
cannot be explained from NUN5 and Current plus the unpacked static sources.

## Safety model

- Project roots and the Current image are resolved through the shared Python
  project-path loader.
- Target serial and ELF CRC must match the live PINE identity.
- Texture replacements, 16:9 output, and widescreen patches are rejected so
  two captures cannot silently use different rendering conditions.
- PINE captures require PCSX2 to be paused. PINE exposes status but has no pause
  command, so pause with `Space` before invoking `capture`.
- `import-pairs` validates matching NUN5 and Current filenames for every slot,
  copies the F1 states by default, and records `manual_f1_import` rather than
  claiming a live PINE identity. `--consume-states` is explicit and destructive.
- A capture is first copied and verified under
  `@work/ui_translation/runtime_cases/`. Only after that succeeds is the newly
  generated slot state removed from `@pcsx2/sstates/`; pass
  `--keep-slot-state` to retain it there.
- Runtime writes require an exact serial/CRC match, neutral rendering settings,
  paused PCSX2, an exact expected-byte range, and complete readback. A failed
  write attempts to restore the guarded bytes before reporting failure.

## Workflow

Check both targets before starting:

```powershell
python scripts/research/ui_translation/ui_runtime.py settings --target all
```

To archive already-created matching F1 pairs while preserving the source
states, provide one stable case name for each slot:

```powershell
python scripts/research/ui_translation/ui_runtime.py import-pairs `
  --pair 1:mode_select `
  --pair 2:options `
  --pair 3:collection_characters
```

Run PCSX2 normally, reach a stable screen, pause it with `Space`, then capture:

```powershell
python scripts/research/ui_translation/ui_runtime.py capture `
  --target nun5 --case character_select
```

Repeat with Current:

```powershell
python scripts/research/ui_translation/ui_runtime.py capture `
  --target current --case character_select
```

Each successful capture contains:

- `state.p2s`: the exact savestate;
- `screenshot.png`: PCSX2's embedded savestate screenshot;
- `manifest.json`: expected target identity, optional live PINE identity, ISO
  hash, rendering settings, state and screenshot hashes, dimensions, capture
  method, and repository-relative provenance.

For targeted read-only runtime inspection:

```powershell
python scripts/research/ui_translation/ui_runtime.py read `
  --target current --address 0x00100000 --width 32 --count 4
```

For a concrete, reversible runtime hypothesis, take both expected and
replacement bytes from pinned files and patch only while PCSX2 is paused:

```powershell
python scripts/research/ui_translation/ui_runtime.py patch `
  --target current `
  --address 0x005D4E70 `
  --expected-file "@source/NUN5.iso.files/SLES_556.05" `
  --expected-offset 0x4DC120 `
  --replacement-file "@source/NUN5.iso.files/SLES_556.05" `
  --replacement-offset 0x4DDDD0 `
  --length 0x300
```

Run the focused tests with:

```powershell
python scripts/research/ui_translation/test_ui_runtime.py
```
