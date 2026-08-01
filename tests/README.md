# Tests

Production utilities live under `scripts/`; injected C lives under `src/`.
Tests live here and are grouped by the responsibility they verify:

- `builder/`: builder, compositor, module, profile, and image tests.
- `injection/`: direct-PINE build/apply pipeline tests.
- `na228/`: PowerShell build and command workflow tests.
- `pcsx2/`: PCSX2 configuration, actualization, and savestate tests.
- `regression/`: accepted feature regressions, grouped by feature.
- `research/`: maintained research-tool tests.

Run the complete Python and PowerShell suite from the repository root:

```powershell
.\tests\run.ps1
```

`scripts/injection/inject_candidate.ps1` is an operational agent injection
command, not a test. It remains under `scripts/` accordingly.
