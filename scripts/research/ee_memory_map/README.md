# EE runtime memory-map analyzer

`analyze_savestates.py` reads `eeMemory.bin` from PCSX2 savestate directories, validates
NA2's linked-list allocator against its cached globals, identifies the active
MWo3 overlay, and records the task's fixed reservation and upper-memory regions.
It accepts either filesystem paths or configured `@root/...` paths.
It also accepts numeric marker savestates retained in
`captures/<recording>/<game>/sstates/` below the
[owning task's work root](../../../AGENTS.md#file-and-folder-management) or its
`inputs/` directory, as the
[input-recording workflow](../../../docs/workflows/input_recording_with_markers.md)
places them, deriving the variant from the game directory and the marker number
from the savestate name.

Analyze a savestate directory and write disposable reports below the owning
task's work root:

```powershell
python scripts/research/ee_memory_map/analyze_savestates.py `
  '@pcsx2_savestates/SLOP-NA228 (31D4DD8D).01' `
  --output-dir '@work/EE Runtime Memory Map/logs/ee_memory_map/<run-id>'
```

The script requires a complete 32 MiB `eeMemory.bin` payload. A short payload
is always rejected.
