# NA2 end-to-end tests

This directory contains main-repository E2E infrastructure, suite definitions,
and configuration. Accepted screenshot/savestate history is stored in the
nested local Git repository at `captures/`.

## Current command surface

```powershell
na228 test [suite] [-s]
na228 test create <suite> [game]
na228 test rename <suite> <new-suite>
na228 test delete <suite>
```

This is the current implementation interface. `na228 test [suite]` starts the
permanent project tests and E2E build/replay pipeline together. Project policy
treats permanent tests and E2E as independently selectable validation;
`TASKS.md` tracks the implementation work to split those lanes and move E2E
under a dedicated `na228 e2e` command family.

Without a suite, the current command replays all suites. Agent E2E validation is
global across the tracked suite set; a suite/capture named in an agent request
identifies expected evidence, not a narrower execution boundary.

`-s` adds the shifted E2E Test build and replays the same suites against it.
Normal and shifted non-ignored captures must match.

`test create` creates or replaces a suite from the matching Workshop recording,
resets `ignore.txt`, optionally captures a reference game, and runs repeatability
capture. `test rename` moves the suite definition and capture history together;
`test delete` removes both.

## Execution and publication

Each invocation prepares a build once and runs suite replays concurrently.
Suite-creation repeatability uses two normal replays from the same discard-write
memory-card baseline. Capture publication is atomic: normal screenshots,
changed-screen savestates, and reports are published only after the complete
current command succeeds.

Transactions live under `.transactions/run-<uuid>/`. Active transactions record
the owning PID/start time. Failed comparisons retain only the evidence needed to
review the failure; later runs clean inactive retained transactions.

The optional shifted variant moves resident-payload layout internally while
preserving the fixed reservation envelope and compares its captures with normal.
Suite `ignore.txt` entries apply to active comparisons and preserve previously
accepted current evidence for ignored slots.

## Review and acceptance

Agent review is canonical in [`AGENT_GUIDE.md`](AGENT_GUIDE.md): inspect the
complete Git diff in `captures/`, then inspect every changed artifact. Do not
manually scan unchanged history without a concrete reason.

Generated capture-history changes remain uncommitted until the user accepts the
patch. After acceptance, commit the nested capture history and corresponding
main-repository implementation as one coherent delivery.

## Layout

```text
e2e/
├── config.json
├── suites/<suite>/
│   ├── input.p2m2
│   └── ignore.txt
├── captures/<suite>/              # nested Git repository
│   ├── screenshots/
│   ├── grids/
│   └── sstates/{reference,current}/
└── .transactions/run-<uuid>/      # transient, ignored
    ├── owner.json
    ├── retained.json
    ├── jobs/
    └── comparisons/
```

Build provenance remains under `logs/na228/builds/` and output-specific
preflight receipts under `logs/na228/preflight/`.
