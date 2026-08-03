# Tests

Production utilities live under `scripts/`; injected C lives under `src/`.
Tests live here and are grouped by the responsibility they verify:

- `builder/`: builder, compositor, module, profile, and image tests.
- `injection/`: direct-PINE build/apply pipeline tests.
- `na228/`: PowerShell build and command workflow tests.
- `regression/`: accepted feature regressions and E2E infrastructure safety
  contracts.
- `research/`: maintained research-tool tests.

The public integration command is `na228 test`; it runs this permanent suite
alongside the normal/padded ISO and replay pipelines. The internal permanent
runner remains:

```powershell
.\tests\run.ps1
```

`scripts/injection/inject_candidate.ps1` is an operational agent injection
command, not a test. It remains under `scripts/` accordingly.
Reusable PCSX2 and media-tool tests live with their implementations in the
Workshop repository.
