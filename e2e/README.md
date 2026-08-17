# NA2 end-to-end tests

This directory contains main-repository E2E infrastructure and configuration.
Canonical recordings live under `pcsx2_files/input_recordings/e2e/`. Accepted
screenshot history is stored in the
nested local Git repository at `captures/`.

## Current command surface

```powershell
na228 e2e [<suite> [<range>]] [-s]
na228 e2e create <all|suite> [<range>] [-noref]
na228 e2e rename <suite> <new-suite>
na228 e2e remove <all|suite>
na228 e2e commit [-p]
```

`na228 e2e` owns E2E execution and suite lifecycle. Unit tests are an
independent lane invoked with `na228 test`.

With no suite selector, E2E execution covers the complete maintained suite set.
Supplying a suite runs only that suite. `movesets` additionally accepts one
physical `character_data.tsv` row or an inclusive row range, such as `8` or
`8-18`; omitting the range selects every character row. Other suites do not
accept a range.

`movesets` is a code-owned generated suite. It expands `resources/movesets.tsv`
over the fixed recordings in `pcsx2_files/input_recordings/e2e/movesets/` and
publishes flat screenshot, pair, blend, and diff artifacts. Select
`movesets/base`, `movesets/specials`, or `movesets/idle` to update only that
output family; each selector accepts the same optional character-data row
range. `base` includes the normal base output and unique awakening modes.
`idle` emits one case for every selected character row, including second forms.

`-s` adds the shifted E2E Test build and replays the same suites against it.
Every normal and shifted capture must match.

`e2e create all` replaces all capture history except the nested capture
repository's `.git` metadata. It processes every `.p2m2` recording below
`pcsx2_files/input_recordings/e2e/` except the `movesets/` inputs owned by the
generated suite, prepares one build, and runs
every suite's normal replay concurrently. NUN5 reference replays run
concurrently by default; use `-noref` to skip reference capture. A suite
selector instead replaces only that suite; selecting `movesets` rebuilds the
generated suite.
`e2e create movesets <range>` regenerates only that character-row selection and
preserves existing moveset grids outside it. The same range syntax is available
when running `movesets` directly.
`e2e rename` moves the canonical recording and capture history together;
`e2e remove` removes capture history for only the named suite while preserving
descendant suites. Removing `movesets` clears its capture history, but the
code-owned suite remains available. `e2e remove all` clears all capture history
while preserving canonical recordings and nested capture Git metadata.
`e2e commit` stages all current capture changes and consolidates them into
`Initial commit`: a one-commit repository is amended, while a multi-commit
repository is reset softly to its root and squashed. It then expires reflogs and
runs normal Git garbage collection with immediate pruning. An empty accepted
capture set remains represented by one empty `Initial commit`. With `-p`, it
instead preserves the existing capture commits and adds an `Update captures`
commit. Canonical recording changes remain ordinary main-repository changes.

## Execution and publication

Build variants run concurrently. Each variant starts its suite replays as soon
as that variant's build completes. Ready
suite/variant comparisons and independent screenshot-grid, pair, blend, and
diff branches share a bounded task queue; a failed task cancels its active
siblings immediately. NUN5 capture overlaps the normal pipeline and its
artifact publication uses the same bounded scheduling across suites.

Each moveset lane batch-resolves its Practice rows, replays all required cases
concurrently, and creates each grid as soon as its captures finish. Every PCSX2
replay in one command—ordinary and generated suites, NUN5 and NA228, and normal,
shifted, and reference work—draws dynamically from one transaction-scoped
16-process pool. Unfinished lanes immediately reuse capacity released by work
that completes earlier. Independent commands use independent pools; builds and
image-processing tasks do not consume PCSX2 permits.

Typed artifacts are generated once and reused when their grids and aggregate
hardlink views are staged. Aggregate preparation runs concurrently per suite.
Canonical publication, rollback, and cleanup remain serial so normal
screenshots, reports, and aggregate views become
visible atomically only after the complete command succeeds. Publication and
rollback retry transient file-reader locks instead of leaving a partially
restored capture directory. Staged output is copied during publication, so a
late publication failure cannot consume the only completed capture set.

Transactions live under `.transactions/<create|run>-<uuid>/`. Active
transactions record the owning PID/start time and the request identity. A failed
command retains its complete and partial suite outputs. Rerunning the same
command automatically continues the newest compatible transaction; suite
selection, movesets range, shifted/reference mode, and recording or generated-suite input
hashes must match. Each build lane revalidates its ISO hash, completed suites
are reused, and only unfinished or incompatible captures run again. Generated
moveset grids also resume at the individual capture and completed-grid level.
Superseded derived stages move under `.attempts/`, while mismatch evidence is
added without removing replay output. The transaction is removed only after
canonical publication succeeds.

The optional shifted variant moves resident-payload layout internally while
preserving the fixed reservation envelope and compares every capture with
normal.

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
├── scripts/movesets.ps1           # generated movesets suite
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
└── movesets/
    ├── base.p2m2
    ├── idle.p2m2
    └── specials.p2m2
```

The generated `captures/movesets/` layout uses `screenshots/`, `pairs/`,
`blends/`, and `diffs/`, plus the ignored `all/`
hardlink aggregate. Screenshot filenames are
`NNN-character-base|idle|specials|mode-<awakening-id>-a-reference.png` and the
corresponding `-b-current.png`. Pair, blend, and diff folders use the same case
name without the tier suffix. The numeric prefix is the physical
`character_data.tsv` row.

A complete generated case containing one screenshot is published as that
original screenshot. Cases containing two or more screenshots use the fixed
3×2 compositor.

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

Build provenance remains under `logs/na228/builds/` and output-specific
preflight receipts under `logs/na228/preflight/`.
