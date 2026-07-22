# Project release task resume handoff

## Objective

Complete the selected `TASKS.md` Project entry:

> Develop a release process (deferred indefinitely).

Latest user scope:

> do the release task. unfreeze docs, inspect the stash, implement and delete the stash at the end

The user subsequently approved the combined plan with `qwe` and added these
required corrections:

- Move the `Narutimate Accel v2.28` title rewrite out of
  `translation_importer`; it is output identity policy, not an import.
- Remove `translation_importer/config.tsv`; after that move it contains no
  meaningful canonical input.
- Clean the supporting/research material out of
  `na2_patcher/features/localization/binary_patcher/` while retaining its
  executable tables and referenced assets.
- Do all previously discussed release work, then delete the exact release
  stash only after successful integration.

Task/chat title: `Project`.

## State at graceful stop

- Phase: approved execution, stopped before the first repository edit.
- Recommended effort: High.
- Plan approval: approved by the user's `qwe` on 2026-07-22.
- No implementation file has been created, edited, staged, or committed.
- No tests, ISO builds, PyInstaller builds, GitHub publication actions, or
  PCSX2 launches were started in this execution phase.
- No exclusive ISO/build/PCSX2 resource was acquired.
- The release stash remains intact.

## Approved plan

1. Refresh live state and map current APIs plus exact stash contents.
2. Correct title-policy ownership and remove importer config.
3. Clean localization binary-patcher supporting artifacts.
4. Port release runtime, direct ISO/CVM source readers, tests, and current
   profile integration onto the live architecture.
5. Implement the maintained packaging script and GitHub release workflow.
6. Run unit, direct-source, packaged-EXE, and full ISO parity validation.
7. Finalize and unfreeze `docs/RELEASE_PROCESS.md` and remove the matching
   temporary freeze rule from `AGENTS.md` only when the feature is finished.
8. Commit and push Project-owned changes, then permanently drop only the exact
   integrated release stash.

## Confirmed release contract

- One click-to-run Windows console EXE built with PyInstaller one-file.
- The user places exactly one supported clean NA2 ISO and one supported clean
  NUN5 ISO beside the EXE; filenames are irrelevant.
- Scan sibling `*.iso` files non-recursively, prefilter by size, then stream
  SHA-256.
- No arguments, file picker, manual paths, source-hash bypass, Python
  installation, or external project files.
- Hold both inputs read-only and revalidate them after locking.
- Refuse existing `NA2.28.iso` and `NA2.28.iso.building`.
- Build the staging file, fully verify it, then atomically rename it to
  `NA2.28.iso`.
- Never alter input ISOs. Create no runtime logs. Wait for Enter on every exit.
- Embed repository-owned patcher/profile/feature data and runtime dependencies,
  but never source ISOs, extracted source trees, donor data, or UI blobs.
- Preserve the ordinary `na2` build/log/promotion workflow unchanged.
- Use `0.1.0-dev` for the validated development candidate. Implement annotated
  `v*` GitHub release support, but do not mint a production tag without a later
  explicit version decision.

## Stash inspection and disposition

Only known stash:

- Message: `release process WIP before UI final`
- Stable object: `9625a8f7dc914e48f7e3e6efe605574e126339dd`
- It was `stash@{0}` at the stop boundary.

Do not apply or pop it wholesale. It targets retired `modules.tsv`,
`raw_binary`, `translation`, `ui_textures`, `disc_identity`, and shared
`work/temp/release` assumptions.

Selectively port these useful untracked files/concepts from its third parent:

- `.github/workflows/build-release.yml`
- `na2_patcher/app.py`
- `na2_patcher/cvm.py`
- `na2_patcher/release_manifest.json`
- `na2_patcher/release_runtime.py`
- release tests under `na2_patcher/tests/`
- `scripts/release/build_release.ps1`
- `scripts/release/requirements.txt`
- `scripts/release/toolchain.json`

The stashed `docs/RELEASE_PROCESS.md` is superseded by the longer live document.
Discard wholesale shared-file diffs and port only still-valid behavior. Use
`work/Project/temp/release/`, never legacy `work/temp/release/`.

Drop the stable stash object only after the integrated changes are validated,
committed, and pushed. Do not touch any other stash.

## Title-policy correction

Current incorrect state:

- `features/localization/translation_importer/config.tsv` stores title policy,
  mapping version, and a self-pin for `mappings.tsv`.
- `translation_importer.engine` replaces the donor title while resolving
  imported strings.

Required state:

- `translation_importer` imports and validates official donor text without the
  project-title rewrite.
- Profile identity owns the donor/output title declaration.
- `string_patcher` applies the exact title policy after import and before
  encoding/inline or linked placement, with fail-closed coverage.
- Remove the importer config entirely. Table headers define schemas; Git and
  the profile feature hash provide versioning and content pins.
- Release product metadata must derive from or validate against the profile
  output title rather than becoming an independent title authority.

Current title-policy values that must preserve output behavior:

- donor: `Naruto Shippuden: Ultimate Ninja 5`
- output: `Narutimate Accel v2.28`
- target: `SLPS`
- expected mappings: 6
- expected occurrences: 7

The current `[S]` prefix remains intended display text and must not be stripped.

## Localization binary-patcher cleanup

Observed total: 148,452 bytes.

Executable package content (about 107,913 bytes) to retain:

- `targets.tsv`
- `groups.tsv`
- `patches.tsv`
- `edits.tsv`
- four referenced files under `assets/`

Supporting content (40,539 bytes) to relocate/promote:

- `evidence.tsv`
- `fresh_function_map.tsv`
- `runtime_tests.tsv`
- `generate_nun5_donor.py`

Move the reusable generator to an appropriate maintained
`scripts/research/localization/` location. Promote tabular evidence to a
coherent `docs/knowledge/` location and update links. The disabled
`experiments` package rows should not remain executable inputs; preserve useful
conclusions in confirmed knowledge or `docs/HYPOTHESES.md`, then remove the
disabled rows. Retain the 86 genuine declarative patches unless the live data
proves a row is only the disabled experiment.

## Live architecture findings

- Current module types: `translation_importer`, `string_patcher`,
  `texture_patcher`, `binary_patcher`.
- Profiles use `features.tsv`, `roots.tsv`, and `identity.tsv`; there is no
  profile module table.
- `module_pipeline.py` prepares importer/string artifacts and one linked
  `PRG/228.BIN` payload.
- `image_assembler/` exclusively stages, mutates, verifies, and updates both
  ISO9660 and UDF.
- Translation importer already accepts extracted folders or outer ISO paths.
- Texture patcher still requires extracted `DATA.CVM.files/DATA.CVM.iso` plus
  header and therefore needs the direct CVM source boundary.
- Binary patcher verifies target data from extracted roots and needs a safe
  provider/data boundary for original-ISO release roots.
- The stashed CVM reader is useful but imports the retired `.iso9660`; update it
  to use `na2_patcher.image_assembler.iso9660` and avoid a second outer-ISO
  parser.
- The stashed release runtime calls obsolete profile/build APIs and must be
  redesigned rather than restored verbatim.
- `build_profile.py` should expose one reusable candidate operation so the CLI
  and release adapter share composition and verification while release mode
  suppresses log creation.

## Release identities preserved in the stash

- NA2 size: `1928429568`
- NA2 SHA-256:
  `CA105F7BDBEEAA3275F871C9702B9C77ED985CE140FAE8EAC28CB153E263D0C3`
- NUN5 size: `1926234112`
- NUN5 SHA-256:
  `2E1B9A885F4E94E6B8C4204F139C53ABD568FE49D6521D4D8921FE9460C07BFF`
- Development version: `0.1.0-dev`
- Candidate EXE: `NA2.28_v0.1.0-dev.exe`
- Output: `NA2.28.iso`

Recheck all identities against live canonical sources before sealing them.

## Git and workspace state at stop

- HEAD: `ba758a94e4077413830acd2e00ed48e4b8d39657`
- Branch: `master`
- Tracking: `master...origin/master`
- Worktree was clean at the final status check.
- Owned staged paths: none.
- Owned unstaged paths before this handoff: none.
- Concurrent paths requiring preservation: none shown at the final check.

Files read during inspection include:

- `AGENTS.md`
- `TASKS.md`
- `docs/RELEASE_PROCESS.md`
- `project-paths.json`
- `na2_patcher/profile.py`
- `na2_patcher/build_profile.py`
- `na2_patcher/module_pipeline.py`
- `na2_patcher/project_paths.py`
- current profile TSVs
- translation importer, string patcher, binary patcher, texture patcher, and
  image-assembler source files
- localization binary-patcher tables/support files
- the release stash inventory and its app/CVM/runtime/manifest contents

## Processes and exclusive resources

- No Project-owned Python, PowerShell, PyInstaller, ISO build, or PCSX2 process
  was started.
- Several pre-existing PowerShell/Python processes were visible and were not
  touched.
- No `pcsx2-qt` process appeared in the bounded process check.
- Build/ISO/PCSX2 ownership must be checked once again immediately before the
  eventual parity gate; do not take over another task's singleton resource.

## Needed user input

Nothing. The plan is approved. A final production SemVer/tag remains outside
this implementation; build and validate the `0.1.0-dev` candidate.

## Remaining uncertainties

- Exact cleanest provider interface shared by binary and texture source reads.
- Current availability/hashes for the pinned Python/PyInstaller Windows
  toolchain and GitHub action versions; verify against primary sources during
  implementation.
- Actual packaged EXE size/hash/startup behavior.
- Full normal-versus-packaged ISO byte parity and final boot identity.
- Literal second-machine testing may remain a documented limitation if only an
  isolated repo-free local directory is available.

## Exact first action on resume

Read live `AGENTS.md`, `TASKS.md`, this handoff, Git status/history, and the
stash object. Validate that the approved scope and stash identity have not
drifted. If safe, delete this handoff and automatically commit/push that
deletion as required by the resume policy, then continue with the title-policy
and importer-config correction before touching the release runtime.
