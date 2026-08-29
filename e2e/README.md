# NA2 end-to-end tests

This directory contains main-repository E2E infrastructure and configuration.
Canonical recordings live under `@pcsx2_input_recordings/e2e/`. Accepted
screenshot history is stored in the
nested local Git repository at `captures/`.

## Current command surface

```powershell
na228 e2e <all|suite [args...] ...> [-s]
na228 e2e create <all|suite [args...] ...> [-noref]
na228 e2e rename <suite> <new-suite>
na228 e2e delete <all|suite [args...] ...>
na228 e2e commit [-p]
```

`na228 e2e` owns E2E execution and suite lifecycle. Unit tests are an
independent lane invoked with `na228 test`.

`all` selects the complete maintained suite set. Otherwise, each recognized
suite name begins a selection and subsequent tokens belong to that suite until
the next suite name. This allows one command to run, create, or delete multiple
suites with independent arguments. The generated `movesets` and
`characters/idle` suites accept one physical `character_data.tsv` row or an
inclusive row range, such as `8` or `8-18`; omitting the argument selects every
character row. Other current suites accept no arguments.

`movesets` expands
`@repository/launch_profiles/practice/movesets.tsv` over the fixed base and
specials recordings and publishes per-character base, unique awakening-mode,
and specials grids. Select `movesets/base` or `movesets/specials` to update only
that output family.
`characters/idle` replays every selected character, including second forms, and
combines their idle screenshots into sequential fixed 3×2 pages. A ranged idle
run expands to the complete affected pages so unselected cells are preserved.
The top-level `memory_card` in `config.json` supplies the default card for every
suite. Per-suite settings under `suite_overrides` can replace that card and/or
attach a launch profile; `practice` uses the same generated configuration as
`na228 <game> -l practice naruto`. Memory-card values use the shared
launcher's path rules, and snapshot replay always discards memory-card writes.
Defaults and overrides apply equally to reference and current replays.
`config.json` also references the E2E build configuration by name.

After an E2E run publishes successfully, it compares only the selected
capture paths with `captures/` Git `HEAD`. The console reports `UNCHANGED` when
they match or `CHANGED` with added, modified, and deleted counts for each
changed suite and the total. Dirty capture paths outside the selection are
ignored, including descendant suites below a selected parent. Capture changes
are the regression result and do not make successful
execution fail. The returned object separates `Execution = completed` from
`Regression = changed|unchanged` and includes the same counts.

`e2e create all` replaces all capture history except the nested capture
repository's `.git` metadata. It processes every `.p2m2` recording below
`@pcsx2_input_recordings/e2e/` except the inputs owned by the two generated
character suites, prepares one build, and runs
every suite's Current replay concurrently. NUN5 reference replays run
concurrently by default; use `-noref` to skip reference capture. A suite
selector instead replaces only that suite; selecting either generated character
suite rebuilds only that branch.
`e2e create movesets <range>` and
`e2e create characters/idle <range>` regenerate only the selected character
rows or affected idle pages and preserve grids outside them. The same range
syntax is available when running either suite directly.
`e2e rename` moves the canonical recording and capture history together.
`e2e delete` deletes capture history for each selected suite while preserving
descendant suites and canonical recordings. A generated-suite range deletes
only its selected rows or affected idle pages. Deleting either generated
character suite without arguments clears its capture history, but the code-owned
suite remains available. `e2e delete all` clears all capture history while
preserving canonical recordings and nested capture Git metadata.
`e2e commit` stages all current capture changes and consolidates them into
`Initial commit`: a one-commit repository is amended, while a multi-commit
repository is reset softly to its root and squashed. It then expires reflogs and
runs normal Git garbage collection with immediate pruning. An empty accepted
capture set remains represented by one empty `Initial commit`. With `-p`, it
instead preserves the existing capture commits and adds an `Update captures`
commit. Canonical recording changes remain ordinary main-repository changes.

## Execution and publication

The Current build runs concurrently with reference capture and post-processing.
Each selected suite starts its replay as soon as the build completes.
Independent screenshot-grid, pair, blend, and diff branches share a bounded
task queue; a failed task cancels its active siblings immediately. NUN5 capture
overlaps the Current pipeline and its artifact publication uses the same bounded
scheduling across suites.

Each generated character lane batch-resolves its Practice cases, replays all
required cases concurrently, and creates each grid as soon as its captures
finish. Every PCSX2
replay in one command—ordinary and generated suites plus NUN5 and NA228
work—draws dynamically from one transaction-scoped
16-process pool. Unfinished lanes immediately reuse capacity released by work
that completes earlier. Independent commands use independent pools; builds and
image-processing tasks do not consume PCSX2 permits.

Typed artifacts are generated once and reused when their grids and aggregate
hardlink views are staged. Aggregate preparation runs concurrently per suite.
Canonical publication, rollback, and cleanup remain serial so Current
screenshots, reports, and aggregate views become
visible atomically only after the complete command succeeds. Publication and
rollback retry transient file-reader locks instead of leaving a partially
restored capture directory. Staged output is copied during publication, so a
late publication failure cannot consume the only completed capture set.

Transactions live under `.transactions/<create|run>-<uuid>/`. Active
transactions record the owning PID/start time and the request identity. A failed
command retains its complete and partial suite outputs. Rerunning the same
command automatically continues the newest compatible transaction; suite
selection, generated character range, reference mode, and recording or
generated-suite input hashes must match. Each build lane revalidates its ISO
hash, completed suites are reused, and only unfinished or incompatible captures
run again. Generated
character grids also resume at the individual capture and completed-grid level.
Superseded derived stages move under `.attempts/` without removing replay
output. The transaction is removed only after canonical publication succeeds.

## Review and acceptance

Agent review is canonical in the
[E2E validation workflow](../docs/workflows/e2e_validation.md): inspect the
complete Git diff in `captures/`, then inspect every changed artifact. Do not
manually scan unchanged history without a concrete reason.

Generated capture-history changes remain uncommitted until the user accepts the
patch. After acceptance, commit the nested capture history and corresponding
main-repository implementation as one coherent delivery.

## Layout

```text
e2e/
├── config.json
├── scripts/movesets.ps1           # generated character suites
├── captures/<suite>/              # nested Git repository
│   ├── all/                       # ignored hardlink aggregate
│   ├── screenshots/
│   ├── blends/
│   ├── diffs/
│   └── pairs/
└── .transactions/<kind>-<uuid>/   # resumable, ignored
    ├── owner.json
    ├── request.json
    ├── retained.json
    ├── jobs/
    ├── reference-captures/
    ├── comparisons/
    ├── evidence/
    └── .attempts/
```

```text
pcsx2_files/input_recordings/e2e/
├── <folder>/<suite>.p2m2          # ordinary suites, recursively discovered
├── characters/
│   └── idle.p2m2
└── movesets/
    ├── base.p2m2
    └── specials.p2m2
```

Generated output is split between `captures/movesets/` and
`captures/characters/idle/`. Both use `screenshots/`, `pairs/`, `blends/`, and
`diffs/`, plus the ignored `all/` hardlink aggregate. Moveset screenshot names
are `NNN_character_base|specials|mode_<awakening-id>_a_reference.png` and the
corresponding `_b_current.png`; the numeric prefix is the physical
`character_data.tsv` row. Idle screenshots are paginated as
`page_<n>_a_reference.png` and `page_<n>_b_current.png`. Pair, blend, and diff
folders use the same case name without the tier suffix.

A complete moveset case containing one screenshot is published as that original
screenshot. Cases containing two or more screenshots use the fixed 3×2
compositor. Idle pages always use the compositor, including a final page with
only one character.

Existing `sstates/` directories are legacy capture history. Screenshot-only
replays do not generate or update them.

Only grids are retained. The typed `screenshots/`, `pairs/`, `blends/`, and
`diffs/` folders are canonical and tracked. `all/` is an ignored regenerated
hardlink view, so it consumes no duplicate image storage; it excludes pairs to
keep scrolling focused on the less repetitive variants.

Screenshot, blend, and diff grid pages use a fixed horizontal 3×2 layout. Their
slots fill in ascending order; missing and unused slots remain black instead of
shifting later images. Pair grids retain their existing layout and side-by-side
reference/current cells. Pair, blend, and diff cells contain no embedded
headers.

`screenshots/` builds reference and current screenshots as separate page
series named `page_<n>_a_reference.png` and `page_<n>_b_current.png`.
`all/` reuses those pages alongside `page_<n>_c_blend.png` and
`page_<n>_d_diff.png`.

Build provenance remains under `@logs/na228/builds/` and output-specific
preflight receipts under `@logs/na228/preflight/`.
