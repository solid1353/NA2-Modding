# Validation and patch-completion policy

**Applies when:** selecting or running validation, changing game/runtime
behavior, using E2E, requesting user runtime verification, or deciding when a
patch may be documented, tested, committed, and pushed.

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
- Name the exact command, suite, route, or component rule that authorizes each
  validation. Do not invent an additional validation campaign.
- Permanent/unit tests and E2E are independently selectable. Choosing one does
  not authorize the other.

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
- In Normal mode, only `ver` constitutes acceptance for this commit boundary
  and acts as a one-time override.
- For nonvisual patches, use the route specified or agreed during the task. If
  none is specified, default to runtime testing by the user.
- The agent must not claim runtime success until the user confirms it.

### Savestates

- Outside maintained E2E, agents may inspect savestates only as immutable
  diagnostic evidence. They must not create, modify, convert, patch, load,
  replay, or inject through them for validation.
- Maintained E2E is the only agent-executed savestate path, and it is available
  only when E2E has been selected for a visual change.
- A savestate never validates a nonvisual change.

### Build validation

- Agents do not run the default/no-argument `na228` or `na228.ps1` workflow or
  any other normal user build route. They do not create, replace, promote,
  retain, or launch a user-facing build such as `Latest`, `Previous`, or Manual
  Test, or write its normal build record. Normal builds and their records belong
  to the user.
- Internal PowerShell or Python entrypoints do not bypass these build
  boundaries.
- `na228 build -d` validates the development configuration against the real
  source ISO through the builder's compose-only path. It checks configuration,
  catalog and patch guards, compilation and linking, derived changes, and
  composition conflicts without staging or retaining an ISO or build record.
- A dry run does not prove image assembly, boot, or runtime behavior. Run it
  only when the agreed validation plan explicitly includes `na228 build -d`; it
  is not an automatic additional check.
- The only ordinary full-ISO build route for an agent is
  `na228 worker work/<task>/build/<name>.iso`. Build a task-owned worker ISO only
  when the selected validation requires image assembly. It is an internal agent
  artifact, never a user testing ground or deliverable. Agents do not launch or
  runtime-execute it. Maintained E2E is a separate explicitly selected route.
- Agent-authorized builds are final validation steps, not development or
  diagnostic tools. Before building, review the final diff and confirm that all
  in-scope implementation changes are complete and all earlier selected checks
  passed. Do not build while implementation remains incomplete or use repeated
  builds to discover missing work. If a final build exposes a failure, fix that
  failure, re-review the completed candidate, and only then rerun the selected
  build validation. Any subsequent implementation change invalidates the prior
  build result.
- Delete a worker ISO after the selected validation and evidence extraction,
  whether validation passes or fails. Do not build an ISO merely to prepare
  user verification; the user uses their normal build and run workflow.

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

- A validation is a hard gate only when failure means the primary result is
  invalid, unsafe, or unusable.
- Auxiliary consistency, regeneration, synchronization, or maintenance failures
  are soft warnings when the primary operation succeeded.
- An auxiliary failure must not fail or discard a valid, usable primary result.
- Do not promote a soft validation into a hard gate without explicit user
  approval.
- A failed validation does not authorize wrappers, fallback systems,
  compatibility layers, manifests, extra checks, or other new machinery.

## Proof, tests, documentation, and Git

- Automated checks, E2E evidence, screenshots, compilation, and plan approval do
  not replace user acceptance of a patch.
- Provisional candidate checks or new E2E coverage may remain with the
  uncommitted candidate while validation is in progress.
- Before user acceptance, do not document the patch behavior as established fact
  or encode it into permanent tests.
- After acceptance, finalize useful patch-specific tests and documentation,
  discard rejected candidate checks, then commit and push the complete feature.
- Permanent tests must detect a meaningful regression in accepted behavior or a
  documented safety contract. They must not merely restate fixture, catalog,
  manifest, or table contents; freeze incidental implementation details; or
  reconstruct the implementation and compare it with itself. Cover isolated
  logic, guards, and failure behavior using the smallest practical synthetic
  inputs. Do not rerun production inputs through work already performed and
  guarded by the normal build merely to prove that the build succeeds.
  Real-source, production-scale, or full-pipeline tests require explicit user
  approval and must detect a specific regression that the normal build cannot
  detect.
- Disassembly findings and other reusable general knowledge must be promoted on
  the schedule required by the research policy even while patch acceptance is
  pending. This records research evidence, not established candidate behavior,
  and does not claim or imply that the patch works. Keep facts, inferences,
  hypotheses, and confidence distinct.
