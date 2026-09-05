# EE runtime memory-map analyzer

`analyze_savestates.py` reads `eeMemory.bin` from PCSX2 savestate directories, validates
NA2's linked-list allocator against its cached globals, identifies the active
MWo3 overlay, and records the task's fixed reservation and upper-memory regions.
It accepts either filesystem paths or configured `@root/...` paths.
It also accepts numeric savestate names retained in
`captures/<recording>/<phase>/sstates/` below the
[owning task's work root](../../../docs/policies/work_directories.md),
deriving the phase and marker number from that structure.

Analyze a savestate directory and write disposable reports below the owning
task's shared log root:

```powershell
python scripts/research/ee_memory_map/analyze_savestates.py `
  '@pcsx2_dev/sstates/SLOP-NA228 (31D4DD8D).01' `
  --output-dir '@task_logs/EE Runtime Memory Map/<run-id>'
```

Run the focused unit tests with:

```powershell
python -m unittest discover scripts/research/ee_memory_map -p 'test_*.py'
```

The script requires a complete 32 MiB `eeMemory.bin` payload. A short payload
is always rejected.
