# NA2 end-to-end tests

This is the main-repository infrastructure for emulator-driven end-to-end game
tests. Its current suites capture visual evidence, and the suite format can
grow to cover runtime state and logic. Suite recordings and ignore lists are
tracked here. `captures/` is a nested local repository that versions each
suite's reference images, latest NA2.28 captures, generated report, and
savestates.

Agents making local NA2.28 visual fixes follow
[`AGENT_GUIDE.md`](AGENT_GUIDE.md).

From the project root:

```powershell
na228 test
na228 test font/main -b
na228 test font/heap_stability
na228 test font/load_save -b
na228 test new <recording>
na228 test new <recording> font/character_select -r nun5
na228 test reference font/main -r nun5
na228 test reference font/main -r nun5 -f
```

`na228 test` runs every suite against the existing Screenshot Test ISO. `-b`
builds Screenshot Test once before the selected suite, or once before the first
suite when all suites run.

`font/heap_stability` is a two-build determinism suite. It builds and replays a
test-only 32-byte resident-payload padding variant, rebuilds and replays the
normal profile, and requires every raw PNG to be byte-identical. The padding is
part of the build fingerprint, does not edit feature inputs, and the normal
Screenshot Test ISO is restored before comparison. This suite publishes no
alternate captures or accepted baseline.

`test new` imports a recording from Workshop's shared input-recording folder.
Without `-r`, it creates a reference-less suite. `-r <reference>` replays the
recording against that game and creates reference captures. A reference-less
suite captures current screenshots and savestates but has no comparison
report. `test reference` uses the suite-tracked `input.p2m2` and requires the
reference game explicitly with `-r`; `-f` is required
only when reference images already exist and would be overwritten.

Each suite definition lives under `suites/<suite>/` with `input.p2m2` and an
optional `ignore.txt`. Suite names may contain relative subfolders such as
`font/load_save` and `font/character_select`. The ignore file lists capture
filenames whose existing `current/` image and current savestate are preserved
during a new run. A newly ignored slot without existing evidence is omitted.

Capture data lives under:

```text
captures/<suite>/
├── reference/             # optional
├── current/
├── report/
└── sstates/
    ├── reference/
    └── current/
```

`current/` is atomically replaced by the latest NA2.28 replay. Git shows which
current images differ from the last committed capture state. The tracked
`report/` compares reference with current and contains pairs, pixel diffs,
blends, and grid pages. Identical comparisons produce no pair, diff, blend, or
grid entry. Reference-less suites omit the report.

After explicit user verification and approval, commit the accepted current
screenshots, savestates, and regenerated report in the capture repository
together with the corresponding implementation delivery. Current captures,
savestates, and report stay uncommitted while a visual fix is still under
review. The previous accepted batch remains available through Git.
