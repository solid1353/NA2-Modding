# Graceful stop

**Run with:** `zxc`.

`zxc` pauses unfinished work safely:

1. Stop at the next safe boundary.
2. Create a named stash containing only the current task-owned uncommitted work;
   include the workstream and task in the stash name.
3. Write a temporary resume handoff under
   `docs/handoffs/<date>-<task>-resume.md`.
4. Create or update the corresponding `TASKS.md` entry and link it to the
   handoff.
5. Commit only the handoff and `TASKS.md` update. Never commit the
   unfinished implementation.
6. Stop.

The handoff records the exact stash name/reference, what it contains, current
state, completed and remaining work, blockers, validation state, and restore
command.

On resume, follow the task link, apply the recorded stash, resolve ordinary Git
conflicts using the stash and handoff, and verify that the paused work was
recovered correctly before dropping the stash. Then delete the temporary
handoff, remove its task link, commit that cleanup, keep the task entry
until the work itself is complete, and continue normally.
