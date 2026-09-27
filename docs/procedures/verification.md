# Verification

`ver` accepts the current result across every repository changed by the task
and starts one verification-and-delivery operation. Continue it until commit
and push, explicit cancellation, or a hard blocker. A report does not complete
`ver`; the only planned pause is waiting for the user's decision on findings.

For code changes, run `na228 test`. Set `NA228_TEST_WORKERS` to a positive
integer to override the worker count; use `1` for serial debugging. Inspect
every failure and whether the accepted behavior needs new tests.

New tests are optional. Propose one only when it would catch a concrete
regression in accepted behavior or check a documented safety contract that
existing tests miss. Explain its benefit. Do not propose one merely because
code changed or `ver` was given. If approved, assert the outcome with the
smallest practical isolated input. Avoid tests that restate source data,
freeze incidental implementation details, mirror the implementation, or
rerun the production pipeline.
Use fixed test inputs and expectations; never use values from user-editable
project configurations in tests, because the user can change them at any time.

If tests fail or a new test has a clear benefit, report all findings together.
For each failing test, state what it checks and whether it protects accepted
behavior or a documented safety contract. Recommend fixing it if it does;
otherwise recommend removing it. If its purpose is unclear or misguided, say so instead of inventing a reason to keep it. For each proposed new test, explain what
it would detect. Identify failures caused by another task's uncommitted
changes in the report.

Wait for the user's decision on that report. Then make the agreed changes,
rerun affected checks, and continue the same `ver` operation. Report and wait
again only if new findings require a decision.

When no findings need a decision, commit and push. In Design mode, first
promote useful design content and delete the design document, then exit after
pushing.
