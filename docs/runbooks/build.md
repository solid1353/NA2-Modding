# Build and launch

Build commands use the maintained dependency resolver and configured project
paths. Use `na228 help` for the complete command syntax.

## Commands

```powershell
na228 build [config] [-f]
```

Every top-level JSON under `configurations/` is discovered automatically. A
configuration without an alias uses its filename stem as its command selector.
Root `project.json` assigns `b`, `j`, `t`, and `e` to the base, Japanese, test, and
E2E configurations; those configurations are selected only by their aliases.
`na228 <config>` launches the newest cached build. Prefixing the selector with
`b` builds or reuses it before launch, and `na228 build <config>` builds without
launching. Selectors must not conflict with commands, sources, or another
selector's build and watch forms. Bare `na228` is equivalent to `na228 bb`.
Passing `-f` to `na228 build` or a launch containing a build token ignores each
applicable reusable registry hit, performs a fresh verified build, and replaces
the matching cached image with a newly timestamped artifact even when its bytes
are unchanged. A launch without a build token rejects `-f`.

## Launch profiles

The `-l <profile>` launcher option is optional. Without it, the base fields
apply. A selected direct profile inherits every base field it does not override.
Profile names are not a closed set. A configured profile may own executable
argument handling in `@repository/launch_profiles/<profile>/launch.ps1`.
Profiles without that script are settings-only and accept no profile arguments.
Executable profiles return their additional Workshop launch parameters through
a `LaunchParameters` dictionary.

## Logs and cached images

The public `na228` development commands present configuration failures as one
concise path/value/expectation message. Their existing `latest.log` and
`rolling.log` records retain the corresponding traceback under
`technical_details`; catalog-authoring and internal failures remain developer
errors and keep their existing presentation.

Completed operational invocations maintain `@logs/na228/latest.log` and the
newest 20 bounded sections in `@logs/na228/rolling.log`. Help output is not
logged. Persistent command logs omit transcript boilerplate, normalize
configured roots to aliases, and record mode, timing, outcome, ISO result, and
the configuration record when applicable.

All configurations share one byte-affecting fingerprint registry under
`@logs/na228/preflight/`. A miss is assembled and verified at a unique path
under `@build/.incoming/`, then moved to
`@build/NA v2.28 - <local timestamp> - <12-character SHA-256 prefix>.iso` and
registered. A later build removes stale incoming candidates left by interrupted
processes without touching live builds.

Distinct fingerprints and configurations that produce the same full SHA-256
reuse the existing ISO. The registry points every matching entry to that one
file; it does not rename, copy, or hardlink the image.

`@logs/na228/preflight/registry.json` stores byte-affecting fingerprint state,
configuration, full ISO SHA-256, verification time, verified image size, and path;
`preflight/records/<fingerprint>/` stores reusable structured provenance when
configuration logging succeeds. A log write failure is reported as a warning;
it does not invalidate a verified ISO.
The registry retains at most 15 unique ISOs. Pruning removes every fingerprint
and provenance record that refers to an evicted image. A missing or corrupt
registry causes a complete verified build and is recreated only after success.

When [`NA228_TASK_WORK_ROOT`](../../AGENTS.md#file-and-folder-management)
is set, builds keep their operational and structured records below the acting
chat's `logs/` directory.

## Build inputs

The build-resource fingerprint covers base and selected JSON configurations,
character overrides, `.modcat` sources, edits, injections, settings and paths,
shared targets, the character reference, applicable binary operations,
referenced assets and sources, and selected localization TSV inputs.
Release packaging inventories the same
closure for every selectable catalog node, including disabled nodes.
Documentation is not an executable builder input.
The release manifest's `title` is included in the ordinary build fingerprint;
its release version and packaging fields do not affect that fingerprint.

Preflight fingerprints the canonical NA2 source ISO, ISO-composing Python code,
the exact selected configuration resources, product/path configuration, active
Python/Zlib versions, and the EE compiler components whenever selected C
sources require them. `@builder/infrastructure/orchestration/module_pipeline.py` prepares
internal invocations and shared payload contributions;
`@builder/infrastructure/orchestration/build_configuration.py` composes them;
`@builder/infrastructure/orchestration/composer.py` closes typed image operations; and
`@builder/infrastructure/modules/image_assembler/` alone stages and verifies the ISO.

The preflight dependency closure covers every input capable of changing the
selected ISO. A build-affecting input or dependency change updates that closure
and its existing invalidation coverage in the same change.

The development injector reads unified definitions under `@builder/patches/`
with `@builder/configurations/base.jsonc` and
`@builder/configurations/overrides/base.character_overrides.tsv`.
