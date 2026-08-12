# Graceful stop

`zxc` pauses unfinished work safely:

1. Pause implementation at the next safe boundary.
2. Create a named stash containing only the current task-owned uncommitted work;
   include the exact chat title in the stash name.
3. Write a temporary resume handoff under
   `docs/handoffs/<date>-<task>-resume.md`.
4. Create or update the corresponding `TASKS.md` entry and link it to the
   handoff.
5. Commit only the handoff and `TASKS.md` update.
6. Stop.

The handoff records the exact stash name/reference, what it contains, current
state, completed and remaining work, blockers, validation state, and restore
command.

On resume:

1. Follow the task link, apply the recorded stash, resolve ordinary Git
   conflicts using the stash and handoff, and verify that the paused work was
   recovered correctly.
2. Locate the recorded stash by its immutable commit in
   `git stash list --format="%gd %H %gs"`, drop exactly its current stash
   reference, and verify that the immutable commit no longer appears in the
   list. Preserve every unrelated stash.
3. Delete the temporary handoff and replace its linked `TASKS.md` entry with
   the same unlinked task text.
4. Commit only that cleanup before continuing the resumed implementation.
5. Verify that the handoff path no longer exists and that `TASKS.md` contains
   no reference to it.

Do not continue resumed implementation until this cleanup succeeds. Before
acceptance or completion, repeat the stash, handoff-path, and task-link absence
checks as a final backstop. Keep the unlinked task entry until the work itself
is completed through `task done`.
