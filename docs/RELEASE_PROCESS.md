# Release process

This document is the canonical context and resumption plan for the self-contained
Windows release builder. The implementation is currently work in progress and
is preserved in a Git stash; it is not a validated public release.

## Current state

- Task: `Develop a release process (unstash, adapt and continue)` under the
  `Project` workstream in `TASKS.md`.
- Stash message: `release process WIP before UI final`.
- Stable stash object: `9625a8f7dc914e48f7e3e6efe605574e126339dd`.
- At the time this document was written, that object was also `stash@{0}`. Use
  the object ID when resuming because the numbered stash reference can move.
- Release work was deliberately stashed so UI Translation could continue
  without release-owned changes in its way.
- The release must be integrated last, after the current UI profile and data are
  stable. Applying the stash is not the final integration step: shared files
  must be reconciled with the then-current UI implementation.
- No production EXE, byte-parity result, clean-machine result, accepted version
  tag, or published GitHub Release exists yet.

## Product decision

The release is one click-to-run Windows console EXE. The user does not install
Python and does not supply mappings, blobs, configuration, paths, command-line
arguments, or any other project files. The EXE embeds the Python interpreter,
patcher code, current hash-pinned profile, curated mappings, patch tables,
metadata, and every non-original resource needed by the build.

The user supplies only clean supported NA2 and NUN5 ISO files by placing them
beside the EXE. Filenames do not matter. Original or donor game data must not be
embedded in the public EXE. In particular, the intended release path derives UI
donor data directly from the clean NUN5 ISO instead of shipping pre-extracted
NUN5 UI blobs.

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
  original game ISO using the confirmed `cc2fuku` password. It avoids extracting
  donor trees beside the user media.

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
- `na2_patcher/modules/ui_textures/engine.py` gains direct NA2/NUN5 ISO authoring
  through `Iso9660` and `CvmIso` while retaining the extracted-root workflow.
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
- The packaging resource audit rejects original ISO files and
  `na2_patcher/modules/ui_textures/blobs/` content from the staged EXE.
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
- Direct NUN5 derivation applies to ISO-root release builds. Normal
  extracted-root builds still require their profile-pinned UI blobs until the
  UI workstream deliberately completes the blob-retirement contract.
- After the release stash was created, the shared mapped-copy portion of
  `na2_patcher/modules/ui_textures/engine.py` was left in the UI worktree so the
  UI profile would continue to function. Its focused suite passed 12 tests at
  that boundary.

Because the stash also contains an older release-modified copy of the same
engine, never resolve an apply conflict by choosing the complete stashed file.
Start from the current accepted UI engine and port only the release-owned
direct-ISO/CVM behavior that is still missing.

## Safe resumption procedure

1. Re-read `AGENTS.md`, `TASKS.md`, this document, and the live Git status.
2. Confirm that the release task is approved and that UI Translation has a
   stable committed handoff. Do not poll or invent unrelated work while waiting.
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
5. Reconcile shared files instead of taking either side wholesale. The highest
   risk files are `na2_patcher/modules/ui_textures/engine.py`,
   `na2_patcher/profiles/current/modules.tsv`, translation behavior, and any
   profile/resource lists used by packaging.
6. Keep `[S]` display text intact and keep ordinary extracted-root builds
   working. Adapt the release resource inventory to the final UI result.
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
- Run raw-binary, profile, translation, and UI suites against both normal
  extracted roots and the direct ISO-root release path where applicable.
- Confirm mapped-copy UI behavior and current MAPSEL1 strategy remain intact.

### Packaged artifact validation

- Build with the exact pinned Windows/Python/package toolchain.
- Confirm the packaged self-test passes and the output is a Windows PE file.
- Audit bundled resources: no ISO, extracted original game tree, donor UI blob,
  machine-specific path, log, or unpinned input may be present.
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
  ISOs. Size-only or file-level comparison is insufficient.
- Confirm failure paths leave no final output, no `.building` file, and no
  runtime log.
- Confirm success leaves exactly `NA2.28.iso` in addition to the EXE and input
  ISOs, with no extracted donor data or other side products.
- Verify the built ISO's boot ELF/PCSX2 CRC and ensure any paired release PNACH
  filename matches it. If the canonical PNACH is empty, confirm no runtime patch
  dependency is being omitted.

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
- Final UI resource inventory after blob retirement and the exact shared-engine
  merge needed against the accepted UI commit.
- Full output ISO SHA-256 and byte parity with the normal builder.
- Clean-machine behavior, antivirus/SmartScreen friction, and console lifetime.
- Final release version, executable filename, annotated tag, and release notes.
- Final boot ELF/PCSX2 CRC and whether a non-empty PNACH must accompany the ISO.

Until those gates pass, describe the work as a stashed release implementation,
not as a finished or distributable release.
