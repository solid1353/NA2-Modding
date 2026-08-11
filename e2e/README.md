# NA2 end-to-end tests

This directory contains main-repository E2E infrastructure, suite definitions,
and configuration. Accepted screenshot/savestate history is stored in the
nested local Git repository at `captures/`.

## Current command surface

```powershell
na228 e2e [-s]
na228 e2e create <suite> [game]
na228 e2e rename <suite> <new-suite>
na228 e2e delete <suite>
na228 e2e commit [-s]
```

`na228 e2e` owns E2E execution and suite lifecycle. Permanent/unit tests are an
independent lane invoked with `na228 test`.

E2E execution is global across the tracked suite set. A suite/capture named in
an agent request identifies expected evidence, not a narrower execution
boundary. The E2E runner retains internal single-suite execution only for suite
creation and its repeatability transaction.

`-s` adds the shifted E2E Test build and replays the same suites against it.
Normal and shifted non-ignored captures must match.

`e2e create` creates or replaces a suite from the matching Workshop recording,
resets `ignore.txt`, optionally captures a reference game, and runs repeatability
capture. `e2e rename` moves the suite definition and capture history together;
`e2e delete` removes both. `e2e commit` stages and commits all current capture
changes as `Update captures`. With `-s`, it instead consolidates the staged
state into `Initial commit`: a one-commit repository is amended, while a
multi-commit repository is reset softly to its root and squashed. The squash
path then expires reflogs, immediately prunes unreachable objects, and
aggressively repacks the repository.

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
