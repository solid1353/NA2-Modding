# Release process

The release process produces one self-contained Windows x64 console EXE. End
users need no Python installation and supply only one exact clean NA2 ISO and
one exact clean NUN5 ISO beside the EXE.

## End-user contract

1. Put the EXE and the two supported clean ISOs in one directory. ISO filenames
   do not matter.
2. Double-click the EXE.
3. The program scans sibling `*.iso` files non-recursively, prefilters by size,
   then identifies NA2 and NUN5 by streaming SHA-256.
4. It refuses missing or duplicate supported images, modified inputs, unsupported
   hashes, an existing `NA2.28.iso`, or an existing
   `NA2.28.iso.building`.
5. It locks both inputs read-only and hashes them again after locking.
6. It applies the embedded current profile directly from the two ISOs, creates
   `NA2.28.iso.building`, verifies the complete staged image and its size, then
   atomically renames it to `NA2.28.iso`.
7. It never modifies either input, creates no runtime log files, removes its
   staging file after failure, and waits for Enter before closing.

The executable embeds the interpreter, patcher engines, current profile,
feature inputs, payload-builder configuration, and Zopfli runtime. It does not
embed original/donor ISOs, extracted source trees, or derived game payloads.

## Developer build

The sole developer and CI entry point is:

```powershell
& scripts/release/build_release.ps1
```

A production build requires a clean Git tree. For local validation of
uncommitted release work:

```powershell
& scripts/release/build_release.ps1 -Development
```

The toolchain is pinned by `scripts/release/toolchain.json` and
`scripts/release/requirements.txt`. The builder creates an isolated virtual
environment under the configured Project task temporary root, runs the complete
patcher test suite, stages only canonical release data, builds a PyInstaller
one-file console EXE, runs its embedded-data self-test, and atomically updates
the configured candidate path. Temporary packaging state is removed afterward.

Development candidates are placed under
`@release_candidates/development/`; clean production candidates use
`@release_candidates/`. Neither path is the append-only external
`releases/` archive.

## Release manifest

`na2_patcher/release_manifest.json` is authoritative for the product name,
version, executable name, output name, embedded profile, and supported source
identities. The pinned source identities are:

- NA2: 1,928,429,568 bytes,
  SHA-256 `CA105F7BDBEEAA3275F871C9702B9C77ED985CE140FAE8EAC28CB153E263D0C3`
- NUN5: 1,926,234,112 bytes,
  SHA-256 `2E1B9A885F4E94E6B8C4204F139C53ABD568FE49D6521D4D8921FE9460C07BFF`

The profile's `identity.json` output game title must equal the manifest product
name.

The maintained publication command performs the version update and complete
Git/tag sequence:

```powershell
na2 release 0.1.0
```

Omitting the argument publishes the version already declared by the manifest.
The command requires a clean tree, refuses an existing remote version tag,
updates and commits the manifest when necessary, runs the production builder,
pushes the current branch, creates an annotated `v<product_version>` tag, and
pushes the tag. The tagged GitHub workflow then creates the GitHub Release.

## Architecture

- `na2_patcher/app.py` owns end-user discovery, hashing, locking, collision
  refusal, staging cleanup, promotion, console messages, and the Enter pause.
- `na2_patcher/release_runtime.py` loads the embedded current profile with the
  two verified source ISOs as root overrides and calls the ordinary profile
  builder without runtime logs.
- `na2_patcher/source_media.py` gives engines one read-only boundary for files
  from either extracted roots or original ISOs.
- `na2_patcher/cvm.py` reads encrypted `DATA.CVM` members directly using the
  confirmed `cc2fuku` password; it does not extract or modify the container.
- `na2_patcher/build_profile.py` exposes the same staged-image composition used
  by the normal CLI and the release adapter.
- `scripts/release/build_release.ps1` owns packaging; the GitHub workflow calls
  that same script rather than implementing another packager.

The ordinary `na2`, `na2 -b`, and `na2 -t` workflows are unchanged.

## Validation evidence

The integrated development candidate was built on Windows x64 with Python
3.14.6, PyInstaller 6.21.0, and the exact hash-pinned requirements.

- full patcher suite: 126/126 passed
- EXE size: 9,907,358 bytes
- EXE SHA-256:
  `EACCED2C942A97E7C70B76E6D34857671953F1EF28F4DD429820023EB2A8A9DB`
- packaged self-test: passed with five current-profile module invocations
- isolated end-user run: exit 0; no runtime files other than
  `NA2.28.iso`
- output ISO size: 1,928,429,568 bytes
- output ISO SHA-256:
  `EC4A67D44B4B325A76E2FFAACAE55EFF3FFB6DC8AFAB4F9FAFB3313E3970A38F`
- normal current-profile ISO SHA-256:
  `EC4A67D44B4B325A76E2FFAACAE55EFF3FFB6DC8AFAB4F9FAFB3313E3970A38F`

The packaged output is therefore byte-identical to the normal current-profile
image. The test used read-only hard links to the exact clean sources and proved
the inputs remained the same files. Clean-machine testing and code signing are
publication gates, not prerequisites for keeping the implemented development
pipeline.

## GitHub releases

`.github/workflows/build-release.yml` supports manual dispatch and annotated
`v*` tags. Both paths run the pinned PowerShell builder on
`windows-latest`, calculate a SHA-256 sidecar, and upload the EXE plus checksum.
A tag must be annotated and exactly equal `v<product_version>`; tagged runs
publish a GitHub Release and mark SemVer suffixes as prereleases.

A production publication sequence, automated by `na2 release [version]`, is:

1. update and validate the current profile and release manifest;
2. run the production builder from a clean committed tree;
3. perform any desired clean-machine/runtime acceptance;
4. create an annotated `v<product_version>` tag;
5. push the commit and tag;
6. verify the workflow artifact or GitHub Release.

The workflow never receives copyrighted game ISOs. Its validation covers the
embedded product and packaging; byte-parity validation remains a controlled
local gate using the canonical source media.
