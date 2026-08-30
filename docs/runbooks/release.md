# Release process

The release process produces one Windows x64 ZIP containing the console EXE,
an editable default configuration, editable character overrides, an inert
catalog reference, and end-user instructions. End users need no Python
installation and supply only one exact clean NA2 ISO and one exact clean NUN5
ISO.

## End-user contract

1. Extract the complete ZIP into one directory.
2. Put the two supported clean ISOs in that directory. ISO filenames do not
   matter.
3. Optionally edit `config.jsonc`. `//` and `/* ... */` comments and trailing
   commas are accepted. A bare setting uses `true` or `false`; a
   typed setting uses the scalar or object value declared by `catalog.modcat`.
   `false` disables any node. Container objects merge recursively through
   `overrides`, while settings and unions are replaced atomically.
4. Optionally edit `character_overrides.tsv`: the `base` substitution cost and
   unsigned character values are literal, explicitly signed character values
   are deltas from the base, and an empty cell inherits its packaged value and
   mode. `0` is literal zero and `+0.0` is a zero delta. IDs, base IDs, and names
   must remain paired as distributed. A directly selected form uses its form
   row; an in-match transformation retains the selected base character's row.
5. Double-click the EXE. It validates the external configuration and character
   overrides against its embedded catalog and character reference before
   hashing either ISO.
6. The program scans sibling `*.iso` files non-recursively, excluding the
   reserved output and staging names, then identifies NA2 and NUN5 by size and
   streaming SHA-256.
7. It refuses missing or duplicate supported source images, modified inputs,
   unsupported hashes, or an existing
   `Narutimate Accel v2.28.iso.building`.
8. It locks both inputs read-only and hashes them again after locking.
9. It applies the selected configuration, creates
   `Narutimate Accel v2.28.iso.building`, verifies the complete staged image and
   its size, then atomically creates or replaces
   `Narutimate Accel v2.28.iso`.
10. It never modifies either input, creates no runtime log files, preserves an
   existing output when a build fails, removes its staging file after failure,
   and waits for Enter before closing.

The ZIP contains exactly the versioned EXE, `config.jsonc`,
`character_overrides.tsv`, `catalog.modcat`, and `README.md`. Release packaging
applies `release.overrides` to `base.features` and writes the resulting complete
`features` tree to `config.jsonc`. It materializes the base and release
character-override layers into `character_overrides.tsv`, including every
reference ID/name row for direct editing. It derives the
external `catalog.modcat` from the canonical project catalog, strips every
patch and implementation detail, and distributes it only as a readable reference. The
executable never reads that external reference. The executable embeds the
interpreter, builder engines, catalog, resources for the complete selectable
catalog rather than only the default selection, payload-builder configuration,
precompiled objects for injection-owned runtime C and assembly sources, and Zopfli runtime.
It does not embed the project PS2 toolchain, source ISOs, extracted source trees,
or derived game payloads.

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

The toolchain is pinned by `@scripts/release/toolchain.json` and
`@scripts/release/requirements.txt`. The builder creates an isolated virtual
environment under `@work/release/temp/`, runs the complete
builder test suite, inventories the full definition resource closure, builds a
precompiled object for each injection-owned runtime C or `.S` source, builds a PyInstaller
one-file console EXE, self-tests the packaged data with the derived default
configuration, and atomically updates the configured ZIP
candidate. Temporary packaging state is removed afterward.

Development ZIPs are placed under `@work/release/development/`; clean
production packages use `@release/`. Published packages are created by the
GitHub release workflow from a tagged commit.

## Release manifest

`game.json` owns the product name. The release manifest owns the version,
canonical default configuration, external configuration filename, and supported
source identities. The executable name is `<product>_<version>.exe`, and the
output image is `<product>.iso`. The pinned source identities are:

- NA2: 1,928,429,568 bytes,
  SHA-256 `CA105F7BDBEEAA3275F871C9702B9C77ED985CE140FAE8EAC28CB153E263D0C3`
- NUN5: 1,926,234,112 bytes,
  SHA-256 `2E1B9A885F4E94E6B8C4204F139C53ABD568FE49D6521D4D8921FE9460C07BFF`

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

- `@builder/scripts/app.py` owns external configuration preflight, end-user source
  discovery, hashing, locking, staging cleanup, atomic output replacement,
  console messages, and the Enter pause.
- `@builder/scripts/release_runtime.py` loads the sibling configuration against the
  embedded catalog with the two verified source ISOs as root overrides and calls
  the ordinary configuration builder without runtime logs.
- `@builder/scripts/source_media.py` gives engines one read-only boundary for files
  from either extracted roots or original ISOs.
- `@builder/scripts/cvm.py` reads encrypted `DATA.CVM` members directly using the
  confirmed `cc2fuku` password; it does not extract or modify the container.
- `@builder/scripts/build_configuration.py` exposes the same staged-image composition used
  by the normal CLI and the release adapter.
- `@scripts/release/build_release.ps1` owns packaging; the GitHub workflow calls
  that same script rather than implementing another packager.

The ordinary `na228`, `na228 b`, and `na228 m` workflows select the
configuration owned by their root `game.json` build target. Cache builds use
their explicitly selected configuration. `release.jsonc` is used only by this
release-packaging pipeline.

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
