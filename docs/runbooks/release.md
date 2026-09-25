# Release process

The release process produces one Windows x64 ZIP containing the console EXE,
an editable default configuration, editable character overrides, an inert
catalog reference, and end-user instructions. End users need no Python
installation and supply one exact clean NA2 ISO.

## End-user contract

1. Extract the complete ZIP into one directory.
2. Put the supported clean NA2 ISO in that directory. Its filename does not
   matter.
3. Optionally edit `config.jsonc`. `//` and `/* ... */` comments and trailing
   commas are accepted. A bare setting uses `true` or `false`; a
   typed setting uses the scalar or object value declared by `catalog.modcat`.
   `false` disables any node. The root contains `localization`, `music_override`,
   `auto_loading`, `native_16_9_horizontal_scale`, and `default_settings`.
   There is no `features` wrapper. The default settings retain their menu groups.
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
   reserved output and staging names, then identifies NA2 by size and streaming
   SHA-256.
7. It refuses missing or duplicate supported source images, modified inputs,
   unsupported hashes, or an existing
   `Narutimate Accel v2.28.iso.building`.
8. It locks the input read-only and hashes it again after locking.
9. It applies the selected configuration, creates
   `Narutimate Accel v2.28.iso.building`, verifies the complete staged image and
   its size, then atomically creates or replaces
   `Narutimate Accel v2.28.iso`.
10. It never modifies the input, preserves an existing output when a build
    fails, removes its staging file after failure, and waits for Enter before
    closing. A failed run creates or replaces `builder-error.log` with the
    complete exception and traceback. Successful and cancelled runs create no
    log.

The ZIP contains exactly the versioned EXE, `config.jsonc`,
`character_overrides.tsv`, `catalog.modcat`, and `README.md`. Release packaging
applies catalog `release_value` overrides to `base.features`, embeds the complete result as
the packaged `configurations/base.jsonc`, and exports its public fields to
`config.jsonc`. Only entries included through catalog `release: true` metadata
appear in the external config and catalog. Export flattens unmarked parent
groups; the release loader maps public keys back to their internal paths and restores hidden
embedded values before building. It materializes the base character values
into `character_overrides.tsv`, including every
reference ID/name row for direct editing. It derives the
external `catalog.modcat` from the canonical project catalog, strips every
patch and implementation detail, and distributes it only as a readable reference. The
executable never reads that external reference. Its public shape matches
`config.jsonc`; changing or deleting it cannot change validation or patching.
The executable embeds the interpreter, parser, validator, builder engines,
complete catalog, and resources for every selectable node, including all
available languages regardless of the packaged default. It also embeds
payload-builder configuration,
precompiled objects for injection-owned runtime C and assembly sources, and the
reviewed localized CCS assets used to construct
`PRG/228_UI.BIN`. It does not embed the project PS2 toolchain, source ISOs, or
extracted source trees. The loader validates public fields against the embedded
catalog, restores hidden defaults, and validates the complete configuration.

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
environment in a temporary `@release/.build-*` directory, runs the release
application and packaged-runtime tests, inventories the full definition
resource closure, builds a precompiled object for each injection-owned runtime
C or `.S` source, builds a PyInstaller one-file console EXE, self-tests the
packaged data with the derived default configuration, and atomically updates
the configured ZIP candidate. Temporary packaging state is removed afterward.

Development ZIPs are placed under `@release/development/`; clean
production packages use `@release/`. The publication command uploads the exact
validated production ZIP and its SHA-256 sidecar to GitHub.

## Release manifest

`game.json` owns the product name. `na228_builder/resources/release_manifest.json`
owns the version, canonical default configuration, external configuration filename, and supported
source identities. The executable name is `<product>_<version>.exe`, and the
output image is `<product>.iso`. The pinned source identities are:

- NA2: 1,928,429,568 bytes,
  SHA-256 `CA105F7BDBEEAA3275F871C9702B9C77ED985CE140FAE8EAC28CB153E263D0C3`

The maintained publication command performs the version update and complete
Git/tag sequence:

```powershell
na228 release 0.1.0
```

Omitting the argument publishes the version already declared by the manifest.
The command requires a clean tree, refuses a conflicting remote version tag,
updates and commits the manifest when necessary, runs the production builder,
pushes the current branch, creates and pushes an annotated
`v<product_version>` tag, and uploads the package to GitHub. A matching tag
without a release resumes publication.

## Architecture

- `@builder/infrastructure/orchestration/app.py` owns external configuration preflight, end-user source
  discovery, hashing, locking, staging cleanup, atomic output replacement,
  console messages, and the Enter pause.
- `@builder/infrastructure/orchestration/release_runtime.py` loads the sibling configuration against the
  embedded catalog with the verified NA2 source ISO as its root override and
  calls the ordinary configuration builder without runtime logs.
- `@builder/infrastructure/orchestration/source_media.py` gives engines one read-only boundary for files
  from either extracted roots or original ISOs.
- `@builder/infrastructure/orchestration/cvm.py` reads encrypted `DATA.CVM` members directly using the
  confirmed `cc2fuku` password; it does not extract or modify the container.
- `@builder/infrastructure/orchestration/build_configuration.py` exposes the same staged-image composition used
  by the normal CLI and the release adapter.
- `@scripts/release/build_release.ps1` owns packaging;
  `@scripts/release/publish_release.ps1` publishes that exact package.

The ordinary `na228`, `na228 b`, and `na228 m` workflows select the
configuration owned by their root `game.json` build target. Cache builds use
their explicitly selected configuration. Catalog `release_value` overrides
apply only in the release-packaging pipeline.

## GitHub releases

`na228 release` builds and validates the production package locally, writes its
SHA-256 sidecar, creates and pushes the annotated version tag, and uploads both
files to the corresponding GitHub Release. SemVer suffixes are published as
prereleases. GitHub does not rebuild the package.

A production publication sequence, automated by `na228 release [version]`, is:

1. update and validate the release configuration, catalog, and release manifest;
2. run the production builder from a clean committed tree;
3. perform any desired clean-machine/runtime acceptance;
4. create an annotated `v<product_version>` tag;
5. push the commit and tag;
6. upload the validated ZIP and checksum to the GitHub Release.

The publication command never uploads copyrighted game ISOs. Package validation
covers the packaged product and full selectable resource closure; output-image
validation remains a controlled local gate using the canonical source media.
