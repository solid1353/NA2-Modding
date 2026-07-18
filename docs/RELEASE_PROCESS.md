# Release process

This document is the canonical context and resumption plan for the self-contained
Windows release builder. The implementation is currently work in progress and
is preserved in a Git stash; it is not a validated public release.

**Status: deferred indefinitely.** Do not resume implementation, restore the
release stash, build an EXE, run release parity, or publish anything until the
user explicitly reactivates this task. The documentation and stash exist only
to preserve context meanwhile.

## Current state

- Task: `Develop a release process (unstash, adapt and continue)` under the
  `Project` workstream in `TASKS.md`.
- Stash message: `release process WIP before UI final`.
- Stable stash object: `9625a8f7dc914e48f7e3e6efe605574e126339dd`.
- At the time this document was written, that object was also `stash@{0}`. Use
  the object ID when resuming because the numbered stash reference can move.
- Release work was deliberately stashed so UI Translation could continue
  without release-owned changes in its way.
- UI Translation replacement is now finished and committed as `b491d10`
  (`Finish UI texture replacement`) on `origin/master`, after the user's
  existing `48c347d` task update.
- Applying the stash is not the final integration step: release-owned shared
  files must be reconciled with the accepted UI implementation and the release
  must preserve the blob-pinned profile described below.
- No production EXE, byte-parity result, clean-machine result, accepted version
  tag, or published GitHub Release exists yet.

## Product decision

The release is one click-to-run Windows console EXE. The user does not install
Python and does not supply mappings, blobs, configuration, paths, command-line
arguments, or any other project files. The EXE embeds the Python interpreter,
patcher code, current hash-pinned profile, curated mappings, patch tables,
metadata, the 34 profile-pinned UI blobs, and every other repository-owned
resource needed by the build.

The user supplies only clean supported NA2 and NUN5 ISO files by placing them
beside the EXE. Filenames do not matter. Original or donor game data must not be
embedded in the public EXE except for the already curated, repository-tracked,
hash-pinned UI replacement blobs that are part of the accepted profile. Direct
derivation of those blobs from NUN5 is explicitly deferred to the separate UI
task `Refactor to only include patches, not blobs.` It is not the intended
behavior for this release state.

PyInstaller one-file packaging is the current implementation choice. It bundles
the interpreter, so the end user does not need a Python installation. Early
inspection estimated a compressed EXE in roughly the 15-30 MiB range, but that
is not a measured artifact size and must be replaced with the actual candidate
size once one is built.

## End-user contract

1. Put the release EXE and exactly one clean supported NA2 ISO and one clean
   supported NUN5 ISO in the same directory.
2. Double-click the EXE.
3. The program scans only sibling `*.iso` files, non-recursively. It prefilters
   by size and identifies supported images by streaming SHA-256.
4. It rejects missing inputs, duplicate supported inputs, modified inputs,
   unsupported hashes, an existing final output, or an existing reserved
   staging output.
5. It holds the selected inputs read-only and rechecks them after locking so the
   build cannot silently continue with changed media.
6. It builds `NA2.28.iso.building` beside the EXE.
7. It verifies the complete profile result and expected ISO size, then renames
   the candidate to `NA2.28.iso` only after success.
8. It removes only the staging file it created when a build fails. It never
   modifies, renames, deletes, or overwrites either input ISO.
9. It creates no runtime log files. Progress and errors are printed only in the
   visible console window.
10. It waits for Enter before closing on success, failure, or cancellation.

The intended use is double-clicking, not invoking a CLI. A file picker, manual
path entry, external profile selection, hash bypass, or terminal-only workflow
would violate the product contract.

## Pinned development manifest

The stashed `na2_patcher/release_manifest.json` is schema version 1 and is still
a development manifest:

- Product: `Narutimate Accel v2.28`
- Version: `0.1.0-dev`
- EXE: `NA2.28_v0.1.0-dev.exe`
- Output: `NA2.28.iso`
- Profile: `na2_patcher/profiles/current`
- NA2 size: `1928429568`
- NA2 SHA-256:
  `CA105F7BDBEEAA3275F871C9702B9C77ED985CE140FAE8EAC28CB153E263D0C3`
- NUN5 size: `1926234112`
- NUN5 SHA-256:
  `2E1B9A885F4E94E6B8C4204F139C53ABD568FE49D6521D4D8921FE9460C07BFF`

These identities are release inputs, not timeless facts. Recheck them against
the accepted source media before sealing a release. The manifest version and
EXE name must also be advanced together before publication.

## Accepted UI baseline for release integration

The release must consume the exact accepted state from `b491d10` without
rewriting its UI-owned files:

- `ui_textures_nun5_v1` profile pin:
  `298D33DF7CD48D59BB018E82547C64971A8D6C54606EEC713A4BC65D51D732D3`
- `ui_translation_code_v1` profile pin:
  `37B9FCBFC869A99D25DC4477FF1ECFD91262B0221ECC1E98E884E6A710E4EB53`
- Unchanged `translation_m03_v34` profile pin:
  `8F7F244F286AB3572E674D52B50409E6D5345C70A7D43E69BA2D754D82D0DBE7`
- Current built ISO size: `1928429568`
- Current built ISO SHA-256:
  `C90B6B51AF8D4FB7DAC327DF144D1017653BDF8CC398CD1C837AAB53BC538A4C`
- Current boot ELF/PCSX2 CRC: `273480D7`
- Independently extracted on-disc `PRG/ETC.BIN` size: `200448`
- Independently extracted on-disc `PRG/ETC.BIN` SHA-256:
  `215F9A0F7313C9D3978A8CD5B4BD2317F7D61BD79C9CC4DBD3C280ED311F133C`
- Verified Shop bytes at `PRG/ETC.BIN` offset `0x30308`:
  `A90081013E001A004101C1011E001600`

The UI raw package baseline contains 5 targets, 11 patches, and 82 edits. Its
focused `UI-ETC-001` plan resolves to one exact edit. The UI runtime suite passed
17 tests, the full `na2_patcher` suite passed 42 tests, and the accepted profile
build record is `@logs/na2/builds/20260718_233134_587_pid36704/`.

These results are the integration baseline, not proof that the packaged EXE
passes. Release validation must reproduce the accepted ISO bytes through the
packaged path.

## Architecture in the stash

### End-user application

- `na2_patcher/app.py` owns the click-to-run interaction: application-directory
  discovery, sibling ISO scanning, size/hash identification, duplicate and
  collision rejection, Windows input locking, revalidation, staging cleanup,
  atomic promotion, console output, and the final Enter pause.
- `na2_patcher/release_manifest.json` seals product identity, profile path,
  output name, and the exact supported source ISO identities.
- `na2_patcher/release_runtime.py` adapts the packaged resources and the two
  original ISOs to the ordinary profile compositor. It must remain a thin
  release adapter rather than a second patching implementation.
- `na2_patcher/cvm.py` reads the encrypted DATA.CVM inner ISO directly from the
  original game ISO using the confirmed `cc2fuku` password. That stashed direct
  reader must not be used to replace the accepted 34-blob UI workflow in this
  release. Retain it only where another verified release-root operation actually
  requires it; otherwise treat it as deferred direct-derivation work.

### Shared patcher changes

- `na2_patcher/build_profile.py` is refactored around a reusable
  `build_profile_candidate(...)` operation that composes and verifies one exact
  candidate path. The existing CLI remains responsible for its normal
  `.building` behavior and log-facing output name.
- `na2_patcher/profile.py` gains controlled profile loading for packaged roots
  and supports original ISO roots without weakening normal profile hashing.
- `na2_patcher/modules/raw_binary/engine.py` separates byte-data validation from
  extracted-file loading so release builds can supply target data read from an
  ISO. Its clean error path also needs the stashed `sys` import preserved.
- `na2_patcher/modules/ui_textures/engine.py` currently has an unstaged,
  release-owned mapped-copy implementation required by the committed MAPSEL1
  strategy. Preserve and commit that behavior with release-owned regression
  tests. Do not add direct NUN5 UI derivation to this release state.
- `na2_patcher/modules/translation/engine.py` has release-related refactoring in
  the stash. When integrating it, preserve the current rule that `[S]` is
  intended display text: `shorten` mappings must emit the complete `[S]...`
  value, not strip the prefix.

### Packaging and automation

- `scripts/release/build_release.ps1` is the sole maintained developer/CI entry
  point for producing the EXE. It validates a clean tracked input set for
  production, validates the pinned profile, runs the repository test suite,
  stages only approved resources, builds a one-file console EXE, runs a packaged
  self-test, checks for a Windows PE header and plausible size, and reports the
  candidate SHA-256.
- `scripts/release/toolchain.json` pins Windows x64 and Python `3.14.6`, the
  entry point, manifest, and icon.
- `scripts/release/requirements.txt` pins PyInstaller and every packaging wheel
  by version and SHA-256.
- `.github/workflows/build-release.yml` runs the same PowerShell builder on a
  clean Windows runner. Manual runs upload a short-lived workflow artifact;
  annotated `v*` tags publish the EXE and checksum as a GitHub Release.
- The packaging resource inventory must include all 34 profile-pinned files in
  `na2_patcher/modules/ui_textures/blobs/`, including the retained 577241-byte
  mapped `MAPSEL1.CCS`. It must reject missing, extra, or hash-mismatched blob
  inputs rather than rejecting the blob directory itself. Original ISO files
  and extracted source trees remain forbidden packaging inputs.
- Production candidates are created under `work/temp/release/candidates/`.
  `-Development` allows dirty inputs and uses a development-only candidate
  directory. Neither mode writes directly into the append-only `releases/`
  archive.

The normal public developer workflow must remain unchanged: `_na2.ps1`,
`scripts/na2/build.ps1`, `na2_patcher/build_profile.py`, and
`scripts/na2/launch.ps1` keep their existing responsibilities. The release
adapter reuses the compositor; it does not replace or recombine the `na2`
workflow.

## Complete stashed file inventory

New files:

- `.github/workflows/build-release.yml`
- `docs/RELEASE_PROCESS.md` (the earlier, shorter form of this document)
- `na2_patcher/app.py`
- `na2_patcher/cvm.py`
- `na2_patcher/release_manifest.json`
- `na2_patcher/release_runtime.py`
- `na2_patcher/tests/test_app.py`
- `na2_patcher/tests/test_build_profile_cli.py`
- `na2_patcher/tests/test_cvm.py`
- `na2_patcher/tests/test_ui_texture_mapped_copy.py`
- `scripts/release/build_release.ps1`
- `scripts/release/requirements.txt`
- `scripts/release/toolchain.json`

Modified files:

- `README.md`
- `docs/PROJECT_CONTEXT.md`
- `na2_patcher/build_profile.py`
- `na2_patcher/modules/raw_binary/engine.py`
- `na2_patcher/modules/translation/engine.py`
- `na2_patcher/modules/ui_textures/engine.py`
- `na2_patcher/profile.py`
- `na2_patcher/tests/test_profile.py`
- `na2_patcher/tests/test_raw_binary.py`
- `scripts/README.md`

The stash records 451 inserted and 161 deleted lines across its tracked-file
changes, plus the new files above. Treat this as implementation WIP, not a patch
that can be accepted without review.

## UI Translation integration boundary

Release work stopped specifically to avoid colliding with the active UI
Translation workstream. The following contract must be preserved when resuming:

- Whole-file NUN5 `MAPSEL1.CCS` replacement is not acceptable. NA2 owns the
  stage-picture atlases and 24-stage indexing.
- The UI strategy uses mapped copy for only
  `m/map/tex/mapname01.bmp` and `m/map/tex/mapsel01.bmp`, copying paired TEX and
  CLT component data after component-signature validation while preserving the
  rest of the NA2 payload and structure.
- Mapped strategy may leave unrelated donor visual differences uncovered; it
  must not import those differences or reject the plan solely because they
  exist.
- Existing `indexed_top_rows` behavior must remain intact.
- The accepted release state uses the same 34 profile-pinned UI blobs as the
  normal workflow. Direct NUN5 derivation belongs to the separate future
  blob-retirement task and must not be introduced during this integration.
- After the release stash was created, the shared mapped-copy portion of
  `na2_patcher/modules/ui_textures/engine.py` was left in the UI worktree so the
  UI profile would continue to function. Its focused suite passed 12 tests at
  that boundary.

Because the stash also contains an older release-modified copy of the same
engine, never resolve an apply conflict by choosing the complete stashed file.
Start from the current accepted engine plus its existing unstaged mapped-copy
diff, restore the release-owned mapped-copy regression tests, and omit the
stashed direct-ISO/CVM UI path.

## Safe resumption procedure

1. Re-read `AGENTS.md`, `TASKS.md`, this document, and the live Git status.
2. Confirm that `b491d10` remains the accepted UI baseline and that the profile
   pins above still match. Do not alter its committed UI files unless a release
   integration failure proves a narrowly scoped correction is necessary.
3. Confirm the stash object still exists:

   ```powershell
   git cat-file -t 9625a8f7dc914e48f7e3e6efe605574e126339dd
   git stash list
   ```

4. Preserve all concurrent changes and commits. The stash contains the earlier
   untracked version of this same document, so a blind `git stash apply` will
   collide with `docs/RELEASE_PROCESS.md`. Commit or otherwise safeguard the
   current document and task link first, inspect the stash parents, and restore
   the release files selectively. The current document supersedes the stashed
   copy; do not overwrite it with the shorter version.
5. Reconcile shared files instead of taking either side wholesale. Preserve the
   committed `na2_patcher/profiles/current/modules.tsv`; merge only the
   release-owned mapped-copy engine diff and tests. Update packaging resource
   lists to embed the 34 accepted blobs.
6. Keep `[S]` display text intact, keep ordinary extracted-root builds working,
   and remove or disable the stashed direct-NUN5 UI path for this release state.
7. Run focused tests first, then the complete validation gates below.
8. Leave the stash in place until the restored implementation is committed and
   the user accepts the result. Dropping it is a separate destructive cleanup
   action.

## Validation gates before calling it a release

### Source and unit validation

- Validate every enabled `na2_patcher/profiles/current/` module and hash pin.
- Run the entire `na2_patcher/tests` suite.
- Run focused app tests for non-recursive discovery, case-insensitive `.iso`
  handling, hash rejection, duplicates, collisions, input preservation,
  rechecking after lock, failure cleanup, output size, and Enter-on-exit.
- Run CVM tests, including encrypted reads, wrong-password rejection, bounds,
  and parity with available extracted references.
- Run raw-binary, profile, translation, and UI suites against the accepted
  profile-pinned blob workflow. Direct ISO-root UI derivation is out of scope.
- Confirm mapped-copy UI behavior and current MAPSEL1 strategy remain intact.

### Packaged artifact validation

- Build with the exact pinned Windows/Python/package toolchain.
- Confirm the packaged self-test passes and the output is a Windows PE file.
- Audit bundled resources: the exact 34 pinned UI blobs must be present; no ISO,
  extracted original game tree, machine-specific path, log, extra blob, or
  unpinned input may be present.
- Confirm the EXE runs on a clean supported Windows machine without Python or
  repository files installed.
- Record the actual EXE size and SHA-256; replace the early size estimate with
  measured evidence.

### Full ISO parity gate

- Hash both clean input ISOs before and after the run and prove they are
  unchanged.
- Build from the same accepted profile through the normal developer compositor
  and through the packaged EXE.
- Require byte-for-byte equality and matching SHA-256 between the two output
  ISOs. The current expected baseline is size `1928429568` and SHA-256
  `C90B6B51AF8D4FB7DAC327DF144D1017653BDF8CC398CD1C837AAB53BC538A4C`;
  size-only or file-level comparison is insufficient.
- Confirm failure paths leave no final output, no `.building` file, and no
  runtime log.
- Confirm success leaves exactly `NA2.28.iso` in addition to the EXE and input
  ISOs, with no extracted donor data or other side products.
- Verify the built ISO's boot ELF/PCSX2 CRC is `273480D7` for this baseline and
  ensure any paired release PNACH filename matches it. The canonical PNACH was
  empty at UI handoff and had no aliases; confirm that remains true and that no
  runtime patch dependency is being omitted.

### Reproducibility and publication gate

- Use a clean committed state whose profile, module inputs, release manifest,
  documentation, and packaging inventory agree.
- Build locally in production mode and record version, Git commit, EXE size,
  and SHA-256.
- Create an annotated `v<product_version>` tag; lightweight tags are rejected.
- Push the commit and tag only after the repository approval gate.
- Confirm GitHub Actions builds the same named candidate, uploads the EXE plus
  `.sha256`, and publishes them on the annotated tag. A SemVer prerelease suffix
  must create a GitHub prerelease.
- Keep any accepted frozen external artifact append-only under `releases/`; do
  not overwrite an existing name.

## GitHub release sequence

1. Finish and verify every enabled profile module, integrating UI Translation
   last.
2. Update `product_version` and `executable_name` together in the release
   manifest.
3. Run `scripts/release/build_release.ps1` locally in production mode.
4. Complete the clean-machine and full ISO parity gates.
5. Commit the exact profile, module data, runtime, packaging scripts, workflow,
   manifest, tests, and documentation.
6. Create and push an annotated tag named `v<product_version>`.
7. Confirm the GitHub Release contains exactly the versioned EXE and its
   checksum and that both match the accepted local evidence.

The GitHub runner does not need game media. It can validate and package the
sealed code/data, but the copyrighted-source end-to-end ISO parity test remains
a local release gate.

## Known uncertainties and decisions still requiring evidence

- Actual packaged EXE size and startup behavior.
- Whether Python `3.14.6` and every pinned wheel are available and stable on the
  chosen GitHub runner when implementation resumes.
- Exact packaging manifest entries and hashes for all 34 accepted UI blobs.
- Whether any stashed direct ISO/CVM code remains necessary outside the deferred
  UI blob-retirement work.
- Full output ISO SHA-256 and byte parity with the normal builder.
- Clean-machine behavior, antivirus/SmartScreen friction, and console lifetime.
- Final release version, executable filename, annotated tag, and release notes.
- Final boot ELF/PCSX2 CRC and whether a non-empty PNACH must accompany the ISO.

Until those gates pass, describe the work as a stashed release implementation,
not as a finished or distributable release.
