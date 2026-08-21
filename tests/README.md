# Tests

Production utilities live under `scripts/`; injected C lives under `src/`.
Tests live here and are grouped by the responsibility they verify:

- `na228_builder/`: builder, compositor, module, profile, and image tests.
- `scripts/`: tests mirroring project-owned script components, including
  injection, `na228`, and maintained research tooling.
- `features/`: accepted feature and canonical runtime-contract regressions.
- `e2e/`: E2E infrastructure safety contracts.

The internal unit-test runner is:

```powershell
.\tests\run.ps1
```

The runner executes Python test modules in isolated subprocesses, followed by
PowerShell test scripts in isolated PowerShell processes. Each phase uses up to
the lesser of 8 workers and the available logical processors. Set
`NA228_TEST_WORKERS` to a positive integer to override the worker count; use `1`
for serial debugging. Output is buffered per module or script and reported in
deterministic path order.

`na228 test` invokes this unit-test runner only. E2E is an independent
validation lane invoked globally with `na228 e2e all`.

`scripts/injection/inject_candidate.ps1` is an operational agent injection
command, not a test. It remains under `scripts/` accordingly. Reusable PCSX2 and
media-tool tests mirror their implementations under Workshop `tests/scripts/`.
