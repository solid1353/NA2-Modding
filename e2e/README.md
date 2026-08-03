# NA2 end-to-end tests

This directory contains the main-repository infrastructure, suite definitions,
and configuration for emulator-driven end-to-end tests. Screenshot history is
stored in the nested local Git repository at `captures/`.

## Commands

```powershell
na228 test [suite]
na228 test create <suite> <recording> [game]
na228 test rename <suite> <new-suite>
na228 test delete <suite>
```

`na228 test [suite]` is the only test-execution command. Without a suite it
replays all suites; with one it replays only that suite. It starts three
concurrent jobs:

The optional suite selector is user-only. Agents always run bare `na228 test`
so every main-tracked suite participates in the integration gate.

1. the complete permanent project test suite;
2. a preflight-resolved normal E2E Test build followed by the selected replays;
3. a preflight-resolved padded E2E Test build followed by the selected replays.

Each build is prepared once per invocation. Permanent tests and variant builds
run concurrently, while emulator replays are serialized because they share one
portable PCSX2 installation. Every selected suite is replayed once against each
ISO, and its normal/padded screenshots are compared as soon as both replays
finish. The pipeline prints periodic job-state progress while this work runs.
It fails if any non-ignored PNG differs. Only after all jobs and comparisons
pass are the normal screenshots, changed-screen savestates, and
reference/current reports published atomically. The already built normal E2E
Test ISO remains active; no third build is performed.

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

`test create` creates or completely replaces the named suite. It copies
`<recording>.p2m2` from Workshop's shared input-recording folder into
`suites/<suite>/input.p2m2`, resets `ignore.txt` to empty, and clears all old
capture history for that suite. It then optionally captures `_a_reference`
screenshots from `[game]` and always runs the suite to publish its new current
screenshots. There is no separate reference command.

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
    ├── jobs/padded/suites/<suite>/
    └── comparisons/<variant>/<suite>/
```

Each transaction records its owning PID and process start time. A later run
removes only abandoned transactions carrying valid ownership metadata; legacy
directories without metadata and transactions owned by live processes are
preserved.

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
