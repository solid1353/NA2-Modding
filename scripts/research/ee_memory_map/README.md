# EE runtime memory-map analyzer

`analyze_savestates.py` extracts `eeMemory.bin` from PCSX2 savestates, validates
NA2's linked-list allocator against its cached globals, identifies the active
MWo3 overlay, and records the task's fixed reservation and upper-memory regions.
It accepts either filesystem paths or configured `@root/...` paths.
It also accepts the numeric savestate names retained below an E2E transaction's
`jobs/<variant>/suites/<suite>/capture/sstates/` tree and derives the variant
and marker number from that structure.

Run the preserved matched capture set and write disposable reports below the
owning task's shared log root:

```powershell
python scripts/research/ee_memory_map/analyze_savestates.py `
  --output-dir '@task_logs/EE Runtime Memory Map/<run-id>'
```

Run the focused unit tests with:

```powershell
python -m unittest discover scripts/research/ee_memory_map -p 'test_*.py'
```

The script deliberately accepts a complete 32 MiB `eeMemory.bin` payload from
Windows `tar` even when that program exits nonzero after its known trailing-zstd
warning. A short payload is always rejected.
