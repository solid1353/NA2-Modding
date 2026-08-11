# NUN5 startup and test loading resume

Paused from the `Memory` task with `zxc` on 2026-08-11.

## Restore

Apply both task-only stashes without `--index`:

1. In `D:\Games\Modding\UN Modding\NA2 Modding`:
   - name: `zxc Memory - NUN5 startup and test loading configuration - 2026-08-11`
   - current reference: `stash@{0}`
   - immutable commit: `7c17c4a9c603beeb66e67798e86ab37b765273f4`
   - command: `git stash apply 7c17c4a9c603beeb66e67798e86ab37b765273f4`
   - contents: `docs/features/qol.md`, `docs/knowledge/game/startup.md`, and
     `na228_builder/configurations/test.json`
2. In `D:\Games\Modding\UN Modding\UN Workshop`:
   - name: `zxc Memory - NUN5 E2E startup PNACH - 2026-08-11`
   - current reference: `stash@{0}`
   - immutable commit: `55d1a5095fce12fb83f600694e9ebebf6bd77df6`
   - command: `git stash apply 55d1a5095fce12fb83f600694e9ebebf6bd77df6`
   - contents: `pcsx2_shared/cheats/source/SLES-55605_C071D4C1.pnach`

Verify the four restored paths before dropping either stash. Locate the matching
current reference with `git stash list --format="%gd %H %gs"`, then drop only
that reference. Do not touch unrelated staged policy work in the NA2 repository.

## Current state

- The Workshop PNACH ports the NA228 input-free startup flow to NUN5 for E2E:
  silent English selection, splash/title suppression, silent record-zero load,
  failure-to-menu fallback, and hidden Save/Load UI.
- The user reported that the NUN5 startup port works. Its NA2 knowledge entry
  still says runtime verification is pending and must be corrected before
  acceptance delivery.
- The NA2 `test.json` candidate sets only
  `qol.startup.faster_loading: false`. The real Manual build rejected it because
  the current override merger validates the partial object as a complete atomic
  union branch.
- `docs/features/qol.md` currently describes that invalid candidate as working;
  it must not remain as established behavior until the configuration loads.
- The six agent-policy failures were reported in short form to the `Docs` task
  (`019fda44-d91a-76d0-92c1-f25be19b6848`). No policy correction belongs to
  these stashes.

## Completed evidence

- The NUN5 PNACH has 131 total writes: 112 loader words, five English-selector
  words, six startup hooks, and eight pre-existing writes.
- Static validation matched all seven clean hook words and the 448-byte loader
  SHA-256 `0701F97F71AE8F021005C722F49C585026D3F353F65F45392F871847FD387468`.
- The user explicitly reported successful NUN5 runtime verification.
- `.\tests\run.ps1` passed 208 Python tests and all PowerShell tests, but that
  suite did not load the repository `test.json` and therefore did not validate
  the candidate.
- The user's `na bm` run failed during configuration loading with
  `features.qol.startup` receiving only `{ "faster_loading": false }` where one
  complete startup union branch was required.

## Remaining work

1. Restore and verify both stashes.
2. Correct intersection override semantics so fields declared in the shared
   object of `shared & (branch_a | branch_b)` merge independently while the
   branch-specific union remains atomic.
3. Add meaningful regression coverage for the shared-field override and for
   loading the canonical repository configurations; inspect and remove or fix
   any test that cannot detect a real supported-behavior regression.
4. Keep `test.json` limited to disabling `faster_loading`, then correct the QoL
   documentation only after the real configuration loads.
5. Update the NUN5 knowledge entry from candidate/unverified wording to the
   user's confirmed runtime result.
6. Use the validation route current policy and user authorization select at
   resume time. Do not run a normal build, PCSX2, or E2E without that authority.
7. Stage only the restored task paths and wait for `ver` before committing the
   game/runtime changes.

There is no technical blocker; work is paused only by `zxc`.
