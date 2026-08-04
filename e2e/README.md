# NA2 end-to-end tests

This directory contains the main-repository infrastructure, suite definitions,
and configuration for emulator-driven end-to-end tests. Screenshot history is
stored in the nested local Git repository at `captures/`.

## Commands

```powershell
na228 test [suite] [-s]
na228 test create <suite> [game]
na228 test rename <suite> <new-suite>
na228 test delete <suite>
```

`na228 test [suite]` is the only test-execution command. Without a suite it
replays all suites; with one it replays only that suite. It starts the complete
permanent project tests and the normal E2E Test build concurrently. After the
normal build resolves, every selected suite replay starts concurrently.

The optional suite selector is user-only. Agents always run bare `na228 test`
so every main-tracked suite participates in the integration gate.

Each build is prepared once per invocation. Permanent tests and build/replay
work run concurrently through the shared portable PCSX2 installation. Replay
jobs use suite-specific recording staging and capture paths. The pipeline
prints periodic job-state progress while this work runs. Only after all jobs
pass are the normal screenshots, changed-screen savestates, and
reference/current reports published atomically.

`-s` adds the shifted E2E Test build and replays the same selected suites
against it. Normal and shifted screenshots are compared as soon as both
replays finish, and any non-ignored difference fails the command. The shifted
lane is also enabled automatically by `test create`.

The variants live in `config.json`. `normal` publishes captures; `shifted`
moves every real resident-payload fragment through a fingerprinted 32-byte
internal layout shift and compares against `normal`. Both payloads serialize
the same fixed reservation envelope, so their MWO3 size/end fields and loader
workload remain identical.
An optional boolean `ignored` field skips an entire variant when `true`;
`ignored: false` keeps it active. This is independent of each suite's
`ignore.txt`, which is always applied to every active variant comparison. The
cross-cutting stability check applies automatically to every selected suite
rather than existing as a separate suite.

The two E2E build roles also carry different `boot_elf_crc_discriminator`
values from `product.json`. Each value changes one aligned zero word outside
all ELF headers, runtime-loaded segments, and file-backed sections. PCSX2
therefore sees distinct CRCs without changing executed data, and the
serial-wide GameSettings file can select `NA v2.28 - E2E Test.ps2` and
`NA v2.28 - E2E Test Shifted.ps2` independently. Build actualization writes
only those CRC sections; the one-time card files are not managed by the test
pipeline.

`test create` creates or completely replaces the named suite. It copies
the matching `<suite>.p2m2` path from Workshop's shared input-recording folder into
`suites/<suite>/input.p2m2`, resets `ignore.txt` to empty, and clears all old
capture history for that suite. When `[game]` is present, its `_a_reference`
replay runs concurrently with the permanent tests and normal/shifted build and
replay pipelines. After every branch succeeds, creation merges the reference
and current evidence and publishes the new capture history once. Without
`[game]`, it runs the test pipeline and publishes current evidence only. There
is no separate reference command.

`test rename` moves both the suite definition and its capture history to the
new relative suite path. It rejects an existing destination. `test delete`
removes both the suite definition and its capture history.

## Layout

```text
e2e/
├── config.json
├── suites/<suite>/
│   ├── input.p2m2
│   └── ignore.txt                 # created empty; slots/ranges may be added
├── captures/<suite>/              # nested local Git repository
│   ├── screenshots/               # flat, ordered by capture
│   │   ├── 001_a_reference.png
│   │   ├── 001_b_current.png
│   │   ├── 001_c_pair.png
│   │   ├── 001_d_blend.png
│   │   └── 001_e_diff.png
│   ├── grids/                     # matching pair/blend/diff report pages
│   │   ├── page_01_c_pair.png
│   │   ├── page_01_d_blend.png
│   │   └── page_01_e_diff.png
│   └── sstates/
│       ├── reference/
│       └── current/
└── .transactions/run-<uuid>/      # transient, ignored
    ├── owner.json
    ├── jobs/tests/
    ├── jobs/normal/suites/<suite>/
    ├── jobs/shifted/suites/<suite>/
    └── comparisons/<variant>/<suite>/
```

Each transaction records its owning PID and process start time. A later run
removes only abandoned transactions carrying valid ownership metadata; legacy
directories without metadata and transactions owned by live processes are
preserved.
When shifted qualification finds differences, the command fails after reducing
its retained transaction to only the mismatching normal/shifted screenshots,
their paired savestates, and each comparison's `report/result.json`.

Grid pages use a `page_` prefix and the same `c_pair`, `d_blend`, and `e_diff`
suffixes as their individual screenshot evidence. Each page number therefore
sorts as one review group containing the contextual pair, 50% overlay, and
amplified pixel diff without being confused with a capture-slot image.
Separate reference-only and current-only grids are not generated because the
pair page already contains both, while the original full-resolution screenshots
remain available individually.

Build provenance is shared with normal builds under
`logs/na228/builds/<build-id>/` and `logs/na228/builds.tsv`. Output-specific
preflight receipts are `logs/na228/preflight/e2e_test_normal.json` and
`e2e_test_shifted.json`.

An optional `ignore.txt` lists decimal capture slots and inclusive ranges, one
entry per line. Zero padding is optional (`4` and `004` are equivalent), `5-8`
selects four slots, and lines beginning with `#` are comments. Matching
`_b_current` screenshots and current savestates are preserved. Ignored slots
are also excluded from every active build-variant comparison. A newly ignored
slot without existing evidence is omitted.

After explicit user verification and approval, commit accepted current
screenshots, savestates, and regenerated reports in the capture repository
together with the corresponding implementation delivery. Until then, generated
capture-history changes remain uncommitted.
