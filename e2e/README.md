# NA2 end-to-end tests

This directory contains the main-repository infrastructure, suite definitions,
and configuration for emulator-driven end-to-end tests. Screenshot history is
stored in the nested local Git repository at `captures/`.

## Commands

```powershell
na228 test [suite]
na228 test new <suite> <recording> [game]
```

`na228 test [suite]` is the only test-execution command. Without a suite it
replays all suites; with one it replays only that suite. It starts three
concurrent jobs:

1. the complete permanent project test suite;
2. a preflight-resolved normal E2E Test build followed by the selected replays;
3. a preflight-resolved padded E2E Test build followed by the selected replays.

Each build is prepared once per invocation. Every suite is replayed once
against each ISO, and its normal/padded screenshots are compared as soon as
both replays finish. The pipeline fails if any non-ignored PNG differs. Only
after all jobs and comparisons pass are the normal screenshots, changed-screen
savestates, and reference/current reports published atomically. The already
built normal E2E Test ISO remains active; no third build is performed.

The variants live in `config.json`. `normal` publishes captures; `padded` adds
a fingerprinted 32-byte resident-payload tail and compares against `normal`.
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
`NA v2.28 - E2E Test Padded.ps2` independently. Build actualization writes
only those CRC sections; the one-time card files are not managed by the test
pipeline.

`test new` copies `<recording>.p2m2` from Workshop's shared input-recording
folder into `suites/<suite>/input.p2m2`, creates an empty `ignore.txt`,
optionally captures `_a_reference` screenshots from `[game]`, and always runs
the new suite to publish its current screenshots. There is no separate
reference command.

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
│   ├── grids/                     # multi-capture report pages
│   └── sstates/
│       ├── reference/
│       └── current/
└── .transactions/run-<uuid>/      # transient, ignored
    ├── owner.json
    ├── jobs/tests/
    ├── jobs/normal/suites/<suite>/
    ├── jobs/padded/suites/<suite>/
    └── comparisons/<variant>/<suite>/
```

Each transaction records its owning PID and process start time. A later run
removes only abandoned transactions carrying valid ownership metadata; legacy
directories without metadata and transactions owned by live processes are
preserved.

Build provenance is shared with normal builds under
`logs/na228/builds/<build-id>/` and `logs/na228/builds.tsv`. Output-specific
preflight receipts are `logs/na228/preflight/e2e_test_normal.json` and
`e2e_test_padded.json`.

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
