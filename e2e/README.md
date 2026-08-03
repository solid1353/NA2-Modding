# NA2 end-to-end tests

This is the main-repository infrastructure for emulator-driven end-to-end game
tests. Its current suites perform visual regression, and the suite format can
grow to cover runtime state and logic. Suite recordings and metadata are
tracked here. `captures/` is a nested independent repository with no remote
during MVP; it versions reference, approved, and pending screenshots. Reports
remain local and untracked. Savestates are agent-only and remain as untracked
`references`, `approved`, and `pending` batches per suite.

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

`test new` imports its recording from Workshop's shared input-recording folder.
`test reference` replays the existing suite's tracked `input.p2m2`. It creates
a missing or empty capture structure without a force flag; `-f` is required
only when reference screenshots already exist and would be overwritten:

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

Each definition lives under `suites/<recording-name>/` with `input.p2m2`,
`screens.tsv`, and an optional `ignore.txt`. The ignore file lists screenshot
filenames that are omitted from pending comparisons while their captured
savestates remain available. Its expanded capture data lives under
`captures/<recording-name>/`, with `references/`, `approved/`, `pending/`, and
`reports/`, plus agent-only `sstates/references/`, `sstates/approved/`, and
`sstates/pending/` directories. The three screenshot tiers contain their PNG
files directly. A run keeps only
screenshots that differ from, or are absent from, the approved set under
`pending/`, and atomically replaces `sstates/pending/` when the replay produced
states. Every captured pending savestate is retained even when its screenshot
is pixel-identical and omitted. Approval moves selected screenshots and their
available states into the approved tiers. All
pairwise and three-way reports contain changed comparisons only.
