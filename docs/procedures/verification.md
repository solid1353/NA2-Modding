# Verification

`ver` accepts the current result across every repository changed by the task
and starts one verification-and-delivery operation. Continue it until commit
and push, explicit cancellation, or a hard blocker. Resolve findings
independently without waiting for the user's review or approval.

For code changes, run `na228 test`. Set `NA228_TEST_WORKERS` to a positive
integer to override the worker count; use `1` for serial debugging. Inspect
every failure and whether the accepted behavior needs new tests.

New tests are optional. Add one only when it would catch a concrete
regression in accepted behavior or check a documented safety contract that
existing tests miss. Do not add one merely because code changed or `ver` was
given. Assert the outcome with the smallest practical isolated input. Avoid
tests that restate source data, freeze incidental implementation details,
mirror the implementation, or rerun the production pipeline.

Use fixed test inputs and expectations; never use values from user-editable
project configurations in tests, because the user can change them at any time.

For each failing test, determine what it checks and whether it protects accepted
behavior or a documented safety contract. Fix it if it does; otherwise remove
it. Apply the same quality criteria to relevant existing tests encountered
during verification, including passing ones, and improve or remove poorly
designed tests where appropriate. Do not invent a reason to keep a test whose
purpose is unclear or misguided.

Make the necessary changes, rerun affected checks, and continue the same `ver`
operation. Resolve new findings in the same way.

When verification is complete, commit and push. Report the findings and changes
together, explaining test removals and what any new tests detect. Identify
failures caused by another task's uncommitted changes.

In Design mode, first promote useful design content and delete the design
document, then exit after pushing.
