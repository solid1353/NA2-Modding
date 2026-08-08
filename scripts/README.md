# Scripts

This file is the current index for maintained script responsibilities and
entrypoints. User-facing CLI syntax belongs to `na228 help` and `workshop help`;
exact agent procedures belong in the linked runbooks.

## Entry points

- `../na228.ps1`: short user-facing NA2 parser/router.
- `na228/run.ps1`: substantive build, launch, watch, test, worker, release, and
  help dispatch.
- `na228/build.ps1`: shared and worker-output build execution, promotion,
  provenance, and receipts.
- `release/build_release.ps1` and `release/publish_release.ps1`: release
  candidate construction and publication; see
  [`../docs/runbooks/release.md`](../docs/runbooks/release.md).

## Responsibility directories

- `lib/`: NA2 path/configuration loading, Python runtime/package resolution,
  and build/run logging.
- `na228/`: NA2 command implementation, build/promotion, identity, and worker
  path handling.
- `project/`: canonical source extraction, extraction verification, and
  configured read-only maintenance. The procedure is in
  [`../docs/runbooks/source-extraction.md`](../docs/runbooks/source-extraction.md).
- `injection/`: direct-PINE candidate build/apply tooling. Agent use is defined
  by [`../docs/runbooks/runtime-testing.md`](../docs/runbooks/runtime-testing.md).
- `release/`: self-contained release construction and publication.
- `research/menu_input/`, `research/ee_memory_map/`,
  `research/localization/`, and `research/ui_translation/`: reusable preserved
  analysis tools owned by those technical areas.

Shared infrastructure is not duplicated here:

- `@pcsx2_scripts/`: Workshop PCSX2 launch, worker copying, PINE, input-profile,
  savestate, disc-identity, and CRC utilities.
- `@media_scripts/`: Workshop ISO, AFS, and encrypted-CVM extraction tools.
- `@workshop/scripts/ghidra/`: shared headless-Ghidra Java scripts and runtime
  setup.

## Build and validation ownership

- `na228_builder/` owns configuration composition and verified image assembly;
  see [`../na228_builder/README.md`](../na228_builder/README.md).
- `scripts/na228/` owns the user-command implementation and output promotion.
- `e2e/` owns emulator-driven test infrastructure and suite definitions; see
  [`../e2e/README.md`](../e2e/README.md).
- `tests/` owns the current repository-wide permanent-test runner. Component
  documentation may expose narrower existing unit-test invocations where they
  are supported.
- Exact agent runtime and worker-PCSX2 procedures are in
  [`../docs/runbooks/runtime-testing.md`](../docs/runbooks/runtime-testing.md).

Do not reproduce CLI syntax or workflow procedures in this index. Link to the
owning command help, component document, or runbook instead.

## Python package sets

Third-party Python packages are declared in the affected component's maintained
central set. Ordinary NA2 package-bearing scripts use `packages.json` through
`lib/run_python.ps1`; do not call a guessed interpreter, probe/install packages
locally, or add task-local fallback discovery.

`NA228_PYTHON` may identify an explicit compatible runtime. Otherwise the
resolver silently selects a runtime satisfying the complete named package set.

## Adding and retiring scripts

- Place a new script beside the responsibility it supports. Do not add
  implementation files directly under `scripts/`; the root is reserved for this
  index and responsibility directories.
- Promote reusable logic or knowledge before deleting a script. Git history is
  the recovery archive; do not create an archive directory or maintain a
  retirement table without a concrete current compatibility need.
- Recover historical code only into task-owned temporary space, inspect it
  before use, and selectively port needed logic into the maintained owner.
