# NA2 end-to-end tests

This directory contains main-repository E2E infrastructure, suite definitions,
and configuration. Accepted screenshot/savestate history is stored in the
nested local Git repository at `captures/`.

## Current command surface

```powershell
na228 e2e [<suite> [<range>]] [-s]
na228 e2e create <all|suite> [<range>] [-noref]
na228 e2e rename <suite> <new-suite>
na228 e2e delete <all|suite>
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
over the two fixed recordings in `pcsx2_files/input_recordings/movesets/` and
publishes only flat contact sheets. It has no `.p2m2` definition under
`e2e/suites/`.

`-s` adds the shifted E2E Test build and replays the same suites against it.
Every normal and shifted capture must match.

`e2e create all` replaces the complete suite-definition tree and all capture
history except the nested capture repository's `.git` metadata. It processes
every shared `.p2m2` recording except recordings beneath `__*` directories and
the `movesets/` inputs owned by the generated suite, prepares one build, and runs
every suite's normal replay concurrently. NUN5 reference replays run
concurrently by default; use `-noref` to skip reference capture. A suite
selector instead replaces only that suite from its
matching Workshop recording; selecting `movesets` rebuilds the generated suite.
`e2e create movesets <range>` regenerates only that character-row selection and
preserves existing moveset grids outside it. The same range syntax is available
when running `movesets` directly.
`e2e rename` moves the
suite definition and capture history together; `e2e delete` removes both for only the
named suite while preserving descendant suites. Deleting `movesets` removes its
capture history, but the code-owned suite remains available. `e2e delete all` directly
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

Build variants run concurrently. Each variant starts its suite replays as soon
as that variant's build completes. Ready
suite/variant comparisons and independent screenshot-grid, pair, blend, and
diff branches share a bounded task queue; a failed task cancels its active
siblings immediately. NUN5 capture overlaps the normal pipeline and its
artifact publication uses the same bounded scheduling across suites.

Each moveset lane batch-resolves its Practice rows, replays all required cases
concurrently, and creates each grid as soon as its captures finish. The shared
16-process budget is divided across concurrent moveset lanes, so normal,
shifted, and reference work overlap without each claiming 16 PCSX2
instances independently.

Typed artifacts are generated once and reused when their grids and aggregate
hardlink views are staged. Aggregate preparation runs concurrently per suite.
Canonical publication, rollback, and cleanup remain serial so normal
screenshots, changed-screen savestates, reports, and aggregate views become
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
├── suites/<suite>.p2m2
├── scripts/movesets.ps1           # generated movesets suite
├── captures/<suite>/              # nested Git repository
│   ├── base-all/                  # ignored hardlink aggregate
│   ├── base-screenshots/
│   ├── base-blends/
│   ├── base-diffs/
│   ├── base-pairs/
│   ├── grid-all/                  # ignored hardlink aggregate
│   ├── grid-screenshots/
│   ├── grid-blends/
│   ├── grid-diffs/
│   ├── grid-pairs/
│   └── sstates/{reference,current}/
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

The generated `captures/movesets/` layout contains only
`grid-screenshots/`. Its flat filenames are
`NNN-character-base|specials|mode-<awakening-id>-a-reference.png` and the
corresponding `-b-current.png`; the numeric prefix is the physical
`character_data.tsv` row.

Every one-image-per-slot view uses the `base-` prefix, and every paged
contact-sheet view uses `grid-`. The typed folders are canonical and tracked.
`base-all/` and `grid-all/` are ignored, regenerated hardlink views over
those canonical artifacts, so they consume no duplicate image storage. Pair
views remain only in `base-pairs/` and `grid-pairs/`; both aggregate views
exclude them to keep scrolling focused on the less repetitive variants. Within
the base filenames, the full labels sort as `a_reference`, `b_current`,
`c_blend`, `d_diff`, and `e_pair`.

`grid-screenshots/` builds reference and current screenshots as separate page
series named `page_<n>_a_reference.png` and `page_<n>_b_current.png`.
`grid-all/` reuses those pages alongside `page_<n>_c_blend.png` and
`page_<n>_d_diff.png`.

Build provenance remains under `logs/na228/builds/` and output-specific
preflight receipts under `logs/na228/preflight/`.
