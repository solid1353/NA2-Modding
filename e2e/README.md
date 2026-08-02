# NA2 end-to-end tests

This is the main-repository infrastructure for emulator-driven end-to-end game
tests. Its current suites perform visual regression, and the suite format can
grow to cover runtime state and logic. Suite recordings and metadata are
tracked here. `captures/` is a nested independent repository with no remote
during MVP; it versions reference, approved, and pending screenshots. Reports
remain local and untracked. Savestates are agent-only and remain as one
untracked latest batch per suite.

From the parent project root, use the integrated commands:

```powershell
na228 test
na228 test NUN5_font_full -b
na228 test new <recording>
na228 test reference NUN5_font_full
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

Create a missing capture suite's NUN5 reference screenshots without a force
flag. Regenerate an existing capture suite's references only with `-f`:

```powershell
.\e2e\scripts\reference.ps1 -Suite NUN5_font_full
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
`reports/`, plus one agent-only `sstates/` directory at the suite root. A run
keeps only screenshots that differ from, or are absent from, the approved set
under `pending/screenshots/`, and atomically replaces the suite-level
savestate batch when the replay produced one. Approval moves selected
screenshots out of the pending review set and never changes savestates. All
pairwise and three-way reports contain changed comparisons only.
