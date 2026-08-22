# Repository bloat reduction

Status: approved design; no open decisions

## Scope

Reduce bloat across NA2-Modding and UN-Workshop by removing approved obsolete
code, tests, workflows, and duplicated documentation while preserving useful
research tools and protected evidence.

## Approved changes

### Generated ISO retention and role hardlinks

- Change the verified ISO registry retention cap from 20 to 15 entries and trim
  older cache ISOs through the maintained registry pruning path.
- Keep `Latest`, `Previous`, and `Manual` as hardlinks to canonical verified
  cache images. They are not disposable duplicate outputs.
- The standalone role files have an established cause: registry pruning removes
  an old fingerprint, filters its image hash out of `registry["images"]`, and
  unlinks the canonical cache pathname even when a role path remains linked to
  the same NTFS file record. NTFS preserves the role file, but it is then the
  only remaining link and no longer has a registered cache counterpart.
- Repair the pruning behavior so current configured role outputs keep or regain
  a registered canonical cache hardlink even when their originating fingerprint
  ages out. Repair existing standalone role files only after hashing and
  verifying them, and replace paths atomically. Do not delete a role ISO merely
  because its cache link is missing.

### Dead code and workflows

Delete the following unequivocally unused helpers, preserving unrelated dirty
changes in every affected file:

- `New-VisualRegressionTierStage`, `New-VisualRegressionGridStage`, and
  `New-VisualRegressionReport`;
- `Get-Na2BuildTarget`;
- `compile_ee_c` and `compile_ee_assembly`;
- `resolve_source_ref`;
- `content_sha256`, `load_base_paths`, and `target_file`;
- the test-only `member_image_offset` and `insert_files` wrappers, retargeting
  any useful tests to maintained interfaces.

Delete the dead Font replay-bundle workflow:

- `verify_font_replay_bundle.ps1` and `verify_font_replay_bundle.py`;
- stale documentation references to the already removed
  `replay_font_recording_worker.ps1`.

Remove the 25 self-only functions identified in the current Font verifier
(1,506 lines in the audit), while preserving the five unrelated additions in
the dirty file. Before removal, classify each candidate under the policy
refinement below: code with a real current use is promoted into a documented,
maintained path and stripped of unreachable or superseded branches; all other
candidate code is deleted after its findings are promoted.

### Research-script lifecycle policy

Scripts may begin as undocumented task-local scratch code. Before the task
ends, delete them after promoting their findings, or promote them into an
existing tooling area, document their current use in the same change, and
remove unreachable or superseded code.

Apply the approved wording to the existing canonical owner:

```diff
--- a/docs/policies/repository.md
+++ b/docs/policies/repository.md
@@ -89,4 +89,6 @@
-- Optional reusable analysis/research tools belong in an existing tooling area;
-  task-local scratch tools remain under the task and are deleted when no longer
-  useful. See the implementation boundary in root
+- Research scripts may start as undocumented task-local scratch code. Before the
+  task ends, delete them after promoting their findings, or promote them into an
+  existing tooling area, document their current use in the same change, and
+  remove unreachable or superseded code. See the implementation boundary in
+  root
   [`AGENTS.md`](../../AGENTS.md#implementation-boundaries).
```

### Obsolete compatibility and architectures

Remove the following retired branches and architectures:

- the retired `na228 e2e remove` command guard and its test;
- adoption of pre-`request.json` E2E transactions;
- migration support for the old `builds.tsv` filename;
- registry schema-v1 migration;
- overlay-plan schema versioning entirely: remove the `schema_version` field,
  version dispatch in `build.py`, its version-specific tests, and the
  corresponding fallback in `watch.ps1`; retain the single unversioned
  `entry_symbols` format, `watch.ps1`, and runtime injection;
- the old standalone binary-patcher TSV/CLI workflow, while retaining its
  maintained in-memory patching engine;
- the proposed physical `string_patcher/strings.tsv` interface, while retaining
  the maintained derived-import consumer.

### Bad tests

Remove the previously identified bad tests and fixtures in these categories:

- UI catalog mirrors that merely duplicate production data;
- the stage-formula self-comparison;
- the Workshop media retirement test;
- Font retirement-only assertions;
- compiler snapshots and duplicated tables that do not protect an ABI or a
  maintained behavioral guard.

Keep `test_repository_grouped_edit_maps_are_alphabetical`. Alphabetical catalog
ordering is an intentional maintenance contract, not incidental formatting, so
the test should continue to enforce it.

### Documentation

Remove stale or duplicated operational documentation only after preserving its
current value. Do not delete retirement notes wholesale. Consolidate them into
one canonical, heavily condensed retirement record under `docs/knowledge/`
(choose the exact filename during implementation), retaining only the negative
evidence and historical decisions that prevent repeated mistakes. Remove the
distributed retirement notes after that promotion.

## Retained and protected material

### Workshop disassembly archive

`UN Workshop/work/disassembly` is protected research evidence and is completely
outside cleanup scope. Do not delete, rewrite, compact, or otherwise modify it.

### Research and experimentation tools

Keep these tools because the audit did not establish that they are obsolete:

- `UN Workshop/scripts/pcsx2/patch_savestate_memory.py`, which takes a source
  savestate plus a patch plan and produces a separate experimental output;
- `scripts/research/menu_input/`;
- `measure_font_capture_regions.ps1` and
  `measure_font_capture_regions.py`;
- `inspect_sprite_objects.py`;
- `scan_memory.py`.

These tools are not approved for deletion. Add minimal documentation for each
tool or coherent tool group covering purpose, inputs, outputs, one
representative invocation, limitations, and the maintained knowledge or
artifact it supports.

## Separately deferred `work/` cleanup

Delete all four NA worktrees during the separate `work/` cleanup. Nothing in
them is to be preserved or migrated. Exclude them from the tracked-code cleanup;
when the separate cleanup begins, verify the resolved targets and follow the
repository's worktree cleanup procedure.
