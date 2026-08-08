# Release process

The release process produces one Windows x64 ZIP containing the console EXE, an
editable default configuration, and end-user instructions. End users need no
Python installation and supply only one exact clean NA2 ISO and one exact clean
NUN5 ISO.

## End-user contract

1. Extract the complete ZIP into one directory.
2. Put the two supported clean ISOs in that directory. ISO filenames do not
   matter.
3. Optionally edit `Narutimate Accel v2.28.json`, preserving its complete key
   structure and using only `true`, `false`, or nested objects.
4. Double-click the EXE. It validates the external configuration against its
   embedded catalog before hashing either ISO.
5. The program scans sibling `*.iso` files non-recursively, excluding the
   reserved output and staging names, then identifies NA2 and NUN5 by size and
   streaming SHA-256.
6. It refuses missing or duplicate supported source images, modified inputs,
   unsupported hashes, or an existing
   `Narutimate Accel v2.28.iso.building`.
7. It locks both inputs read-only and hashes them again after locking.
8. It applies the selected configuration, creates
   `Narutimate Accel v2.28.iso.building`, verifies the complete staged image and
   its size, then atomically creates or replaces
   `Narutimate Accel v2.28.iso`.
9. It never modifies either input, creates no runtime log files, preserves an
   existing output when a build fails, removes its staging file after failure,
   and waits for Enter before closing.

The ZIP contains the versioned EXE, `Narutimate Accel v2.28.json`, and
`README.txt`. The executable embeds the interpreter, builder engines, catalog,
resources for the complete selectable catalog rather than only the default
selection, payload-builder configuration, precompiled objects for catalog-owned
runtime C sources, and Zopfli runtime. It does not embed the project PS2
toolchain, source ISOs, extracted source trees, or derived game payloads.

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
builder test suite, inventories the full catalog resource closure, builds a
precompiled object for each catalog-owned runtime C source, builds a PyInstaller
one-file console EXE, self-tests the packaged data with both the default and a
transient all-enabled configuration, and atomically updates the configured ZIP
candidate. Temporary packaging state is removed afterward.

Development ZIP candidates are placed under
`@release_candidates/development/`; clean production candidates use
`@release_candidates/`. Published packages are created by the GitHub release
workflow from a tagged commit.

## Release manifest

`na228_builder/release_manifest.json` is authoritative for the product name,
version, executable name, output name, canonical default configuration, external
configuration filename, and supported source identities. The pinned source
identities are:

- NA2: 1,928,429,568 bytes,
  SHA-256 `CA105F7BDBEEAA3275F871C9702B9C77ED985CE140FAE8EAC28CB153E263D0C3`
- NUN5: 1,926,234,112 bytes,
  SHA-256 `2E1B9A885F4E94E6B8C4204F139C53ABD568FE49D6521D4D8921FE9460C07BFF`

Root `product.json` output game title must equal the manifest product name.

The maintained publication command performs the version update and complete
Git/tag sequence:

```powershell
na228 release 0.1.0
```

Omitting the argument publishes the version already declared by the manifest.
The command requires a clean tree, refuses an existing remote version tag,
updates and commits the manifest when necessary, runs the production builder,
pushes the current branch, creates an annotated `v<product_version>` tag, and
pushes the tag. The tagged GitHub workflow then creates the GitHub Release.

## Architecture

- `na228_builder/scripts/app.py` owns external configuration preflight, end-user source
  discovery, hashing, locking, staging cleanup, atomic output replacement,
  console messages, and the Enter pause.
- `na228_builder/scripts/release_runtime.py` loads the sibling configuration against the
  embedded catalog with the two verified source ISOs as root overrides and calls
  the ordinary configuration builder without runtime logs.
- `na228_builder/scripts/source_media.py` gives engines one read-only boundary for files
  from either extracted roots or original ISOs.
- `na228_builder/scripts/cvm.py` reads encrypted `DATA.CVM` members directly using the
  confirmed `cc2fuku` password; it does not extract or modify the container.
- `na228_builder/scripts/build_configuration.py` exposes the same staged-image composition used
  by the normal CLI and the release adapter.
- `scripts/release/build_release.ps1` owns packaging; the GitHub workflow calls
  that same script rather than implementing another packager.

The ordinary `na228`, `na228 b`, and `na228 mt` workflows are unchanged.

## GitHub releases

`.github/workflows/build-release.yml` supports manual dispatch and annotated
`v*` tags. Both paths run the pinned PowerShell builder on
`windows-latest`, calculate a SHA-256 sidecar, and upload the ZIP plus checksum.
A tag must be annotated and exactly equal `v<product_version>`; tagged runs
publish a GitHub Release and mark SemVer suffixes as prereleases.

A production publication sequence, automated by `na228 release [version]`, is:

1. update and validate the release configuration, catalog, and release manifest;
2. run the production builder from a clean committed tree;
3. perform any desired clean-machine/runtime acceptance;
4. create an annotated `v<product_version>` tag;
5. push the commit and tag;
6. verify the workflow artifact or GitHub Release.

The workflow never receives copyrighted game ISOs. Its validation covers the
packaged product and full selectable resource closure; output-image validation
remains a controlled local gate using the canonical source media.
