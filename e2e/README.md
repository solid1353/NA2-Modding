# NA2 end-to-end tests

This is the main-repository infrastructure for emulator-driven end-to-end game
tests. Its current suites perform visual regression, and the suite format can
grow to cover runtime state and logic. Suite recordings and metadata are
tracked here. `captures/` is a nested independent repository with no remote
during MVP; it versions reference and approved screenshots while pending
captures, reports, and all paired savestates remain local and untracked.

From the parent project root, use the integrated commands:

```powershell
na228 test
na228 test NUN5_font_full -b
na228 test new <recording>
na228 test reference NUN5_font_full -f
na228 test approve NUN5_font_full -s 2,4,18-21
na228 test approve NUN5_font_full -a
```

`na228 test` runs every suite against the existing Screenshot Test ISO. `-b`
builds that ISO once before the selected suite, or once before the first suite
when all suites run.

Create a suite by replaying its recording against NUN5 and publishing the
completed capture as its reference set:

```powershell
.\e2e\scripts\new_suite.ps1 -Recording NUN5_font_full
```

Regenerate an existing suite's NUN5 reference screenshots only with the
explicit force flag:

```powershell
.\e2e\scripts\reference.ps1 -Suite NUN5_font_full -f
```

Run the complete recording against the existing Screenshot Test build:

```powershell
.\e2e\scripts\run.ps1 -Suite NUN5_font_full
```

Use `-b` to build Screenshot Test once before replaying:

```powershell
.\e2e\scripts\run.ps1 -Suite NUN5_font_full -b
```

Approve selected pending slots, or explicitly approve the whole batch:

```powershell
.\e2e\scripts\approve.ps1 -Suite NUN5_font_full -Slots 2,4,18-21
.\e2e\scripts\approve.ps1 -Suite NUN5_font_full -All
```

Each definition lives under `suites/<recording-name>/` with `input.p2m2` and
`screens.tsv`. Its expanded capture data lives under
`captures/<recording-name>/`, with `references/`, `approved/`, `pending/`, and
`reports/`. Every screenshot tier keeps its paired `sstates/` directory.
Approval copies only selected pending screenshots and matching savestates into
`approved/`; if a selected pending savestate is absent, the obsolete approved
state for that slot is removed. Pending evidence is kept for review, and all
available pairwise and three-way reports are regenerated.
