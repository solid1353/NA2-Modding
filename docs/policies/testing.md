# Validation and patch-completion policy

Exact PCSX2, savestate, worker-ISO, injection, and screenshot procedures are in
[`../runbooks/runtime-testing.md`](../runbooks/runtime-testing.md). Current E2E
command behavior and artifact layout are in
[`../../e2e/README.md`](../../e2e/README.md).

## Validation authorization

- Do not use undefined phrases such as `focused validation`, `relevant checks`,
  or `appropriate tests` as authorization.
- Select validation in this order:
  1. an active user instruction or override;
  2. the approved implementation snapshot, which incorporates any applicable
     component rule;
  3. an applicable component policy when no approved snapshot defines it;
  4. the repository default for the change type below.
- The selected level is the complete validation plan. Lower levels do not add
  checks on top of it.
- Name the exact command, suite, route, or component rule planned for each
  validation. A planned validation is not an executed validation. Report the
  exact command actually run and its observed result; otherwise state `not
  run`. Do not invent an additional validation campaign.
- Unit tests and E2E are independently selectable. Choosing one does
  not authorize the other.
- Do not add unit tests whose only purpose is rejecting a retired field,
  interface, or migration input when the canonical schema already excludes it.
  Verify removal during the refactor with searches, one-off scripts, or
  temporary tests removed before completion. Retain tests only for supported
  behavior that must continue working.

## Repository defaults

### Non-patch code changes

- Run the existing unit-test command documented for the changed component.
- If the component has no documented unit-test command, run no validation by
  default. Do not substitute a broader build, integration, PCSX2, or E2E run.
- Documentation-only work runs no executable validation by default.

### Game/runtime patches

A **patch** is a change intended to alter game behavior or runtime output.
Refactors, documentation, and internal tooling are not patches unless they alter
that behavior.

- A patch remains uncommitted until the user accepts its result.
- In Normal mode, only `ver` constitutes acceptance at this boundary.
- For nonvisual patches, use the route specified or agreed during the task. If
  none is specified, default to runtime testing by the user.
- The agent must not claim runtime success until the user confirms it.

### User-provided input recordings

- When the user provides an input recording for the task, replay it before
  implementation through the exact procedure in the runtime-testing runbook.
  Store every produced savestate and screenshot under an explicit task-owned
  capture path; agents must not use the command's default capture path.
- If the implementation changes game logic, build a worker ISO after the other
  selected checks pass, replay the same recording against it into a separate
  task-owned capture path, and compare the task-relevant baseline and candidate
  evidence. If game logic did not change, do not build or replay a candidate
  merely because a recording was provided.
- This replay is agent runtime validation, not user acceptance of the patch.

### Savestates

- Outside maintained E2E and the user-provided input-recording route, agents may
  inspect savestates only as immutable diagnostic evidence. They must not
  create, modify, convert, patch, load, replay, or inject through them for
  validation.
- Maintained E2E is available only when E2E has been selected for a visual
  change. A standalone savestate never validates a nonvisual change; runtime
  evidence produced by replaying a user-provided recording follows the route
  above.

### Build validation

- Build only when the change can affect built bytes. For a refactor claiming
  unchanged output, build before and after with identical inputs and
  configuration, then compare hashes. Otherwise, do not build.
- Agents do not run the default/no-argument `na228` or `na228.ps1` workflow or
  any other normal user build route. They do not create, replace, promote,
  retain, or launch user-facing builds—including `Latest`, `Previous`, and
  Manual—or write their normal build records. Normal builds and their records
  belong to the user.
- Internal PowerShell or Python entrypoints do not bypass these build
  boundaries.
- The only ordinary full-ISO build route for an agent is
  `na228 worker [--configuration <id>]
  work/<chat title>/build/<name>.iso`. The configuration defaults to `test`.
  Build a chat-owned worker ISO only when the selected validation requires
  image assembly. It is an internal agent artifact, never a user testing ground
  or deliverable. Agents launch it only for the user-provided input-recording
  route above; otherwise they do not runtime-execute it. Maintained E2E is a
  separate explicitly selected route.
- An exact shared verified-build registry hit is reusable build evidence: it
  proves the same byte-affecting fingerprint was already fully assembled and
  verified. Do not rebuild merely to repeat that proof. A worker request
  requires a verified matching physical ISO and creates its output as a
  hardlink to the canonical hash-named cache image.
- Agent-authorized builds are final validation steps except for the pre-change
  baseline required by an approved hash-equivalence comparison. Build that
  baseline before implementation with the agreed inputs and configuration.
  Before building the candidate, review the final diff and confirm that all
  in-scope implementation changes are complete and all earlier selected checks
  passed. Do not use repeated builds to discover missing work. If the candidate
  build exposes a failure, fix it, re-review the completed candidate, and then
  rerun the candidate build. Any subsequent implementation change invalidates
  the prior candidate result.
- For hash-equivalence validation, build the baseline and candidate through
  `na228 worker --configuration <id>` with identical configuration and source
  inputs, then compare the SHA-256 values in their retained structured records.
  Delete task-owned worker output links after the selected validation and
  evidence extraction, whether validation passes or fails, unless the user
  explicitly requested retention. The bounded canonical hash-cache image is
  shared build evidence and is not a task-owned disposable copy.

### Visual game changes

Visual changes include fonts, menus, HUD, textures, layout, rendering, removed
UI elements, and similar visible game behavior.

1. Perform only a quick E2E-coverage scan: inspect suite names, definitions, and
   scenario descriptions. Do not inspect the screenshot corpus merely to choose
   a route.
2. Propose existing E2E coverage, provisional new E2E coverage, or runtime
   testing by the user. Use runtime testing when E2E cannot exercise or
   meaningfully prove the behavior. The user chooses the route.
3. When E2E is selected, execution is global across the tracked suite set so
   unintended changes elsewhere can surface.
4. Inspect the complete Git diff in the nested `e2e/captures/` repository, then
   inspect every changed capture or artifact. Unchanged artifacts need no manual
   review unless there is a concrete reason. An expected visual change with no
   corresponding diff is evidence that must be noticed.
5. Iterate until the intended result is achieved, then present the evidence for
   explicit user acceptance.

## Hard and soft validation

- A validation is a hard gate only when failure makes the primary result
  invalid, unsafe, or unusable. Other consistency, regeneration,
  synchronization, or maintenance failures are soft warnings and must not fail
  or discard a valid primary result.
- Do not promote a soft validation into a hard gate without explicit user
  approval.
- A failed validation does not authorize wrappers, fallback systems,
  compatibility layers, manifests, extra checks, or other new machinery.

## Proof, tests, documentation, and Git

- Provisional candidate checks or new E2E coverage may remain with the
  uncommitted candidate while validation is in progress.
- Before user acceptance, do not document the patch behavior as established fact
  or encode it into unit tests.
- After acceptance, finalize useful patch-specific tests and documentation,
  discard rejected candidate checks, then commit the complete feature.
- Unit tests must detect a meaningful regression in accepted behavior or a
  documented safety contract. They must not merely restate fixture, catalog,
  manifest, or table contents; freeze incidental implementation details; or
  reconstruct the implementation and compare it with itself. Cover isolated
  logic, guards, and failure behavior using the smallest practical synthetic
  inputs. Do not rerun production inputs through work already performed and
  guarded by the normal build merely to prove that the build succeeds.
  Real-source, production-scale, or full-pipeline tests require explicit user
  approval and must detect a specific regression that the normal build cannot
  detect.
