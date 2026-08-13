# NA2 end-to-end tests

This directory contains main-repository E2E infrastructure, suite definitions,
and configuration. Accepted screenshot/savestate history is stored in the
nested local Git repository at `captures/`.

## Current command surface

```powershell
na228 e2e [-s]
na228 e2e create <all|suite> [game]
na228 e2e rename <suite> <new-suite>
na228 e2e delete <all|suite>
na228 e2e commit [-p]
```

`na228 e2e` owns E2E execution and suite lifecycle. Unit tests are an
independent lane invoked with `na228 test`.

E2E execution is global across the tracked suite set. A suite/capture named in
an agent request identifies expected evidence, not a narrower execution
boundary. The E2E runner retains internal single-suite execution only for suite
creation and its repeatability transaction.

`-s` adds the shifted E2E Test build and replays the same suites against it.
Every normal and shifted capture must match.

`e2e create all` replaces the complete suite-definition tree and all capture
history except the nested capture repository's `.git` metadata. It processes
every shared `.p2m2` recording except recordings beneath `__*` directories such
as the internal `__generated` staging area, prepares one build, and runs every
suite's normal/repeat replays concurrently. Optional reference-game replays also
run concurrently. A suite selector instead replaces only that suite from its
matching Workshop recording. `e2e rename` moves the
suite definition and capture history together; `e2e delete` removes both for only the
named suite while preserving descendant suites, while `e2e delete all` directly
removes the complete suite tree and all capture history but preserves the nested
capture Git repository. `e2e commit` creates an ordinary `Update E2E suites`
commit containing only changes under `e2e/suites/` in the main repository. It
also stages all current capture changes and consolidates them into
`Initial commit`: a one-commit repository is amended, while a multi-commit
repository is reset softly to its root and squashed. It then expires reflogs and
runs normal Git garbage collection with immediate pruning. An empty accepted
capture set remains represented by one empty `Initial commit`. With `-p`, it
instead preserves the existing capture commits and adds an `Update captures`
commit. Unrelated main-repository changes are excluded from the suite commit.

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
preserving the fixed reservation envelope and compares every capture with
normal.

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
├── suites/<suite>.p2m2
├── captures/<suite>/              # nested Git repository
│   ├── screenshots/
│   ├── pairs/
│   ├── grid-pairs/
│   ├── grid-blends/
│   ├── grid-diffs/
│   └── sstates/{reference,current}/
└── .transactions/run-<uuid>/      # transient, ignored
    ├── owner.json
    ├── retained.json
    ├── jobs/
    └── comparisons/
```

`screenshots/` contains only the interleaved reference and current captures so
image-by-image browsing is not interrupted by generated comparisons. Individual
side-by-side comparisons live in `pairs/`; `grid-pairs/` contains their paged
contact sheets, while `grid-blends/` and `grid-diffs/` contain the paged blend
and amplified-difference views respectively.

Build provenance remains under `logs/na228/builds/` and output-specific
preflight receipts under `logs/na228/preflight/`.
