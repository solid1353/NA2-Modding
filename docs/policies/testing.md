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
- In Normal mode, only exact `ver` constitutes acceptance for this commit
  boundary and acts as a one-time override.
- For nonvisual patches, use the route specified or agreed during the task. If
  none is specified, default to runtime testing by the user.
- The agent must not claim runtime success until the user confirms it.

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
  documented safety contract. Do not freeze incidental implementation details
  or reconstruct the implementation and compare it with itself.
- Disassembly findings and other reusable general knowledge may be documented at
  any time, with facts, inferences, hypotheses, and confidence kept distinct.
