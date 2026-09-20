# Free Battle stage persistence

`features.general.free_battle_stage_persistence` restores the last highlighted
Free Battle stage when Stage Select opens again during the current game
session, including after Cancel returns to Character Select. The first Free
Battle setup still opens on the first available stage. The selection is not
written to save data and therefore does not persist across game restarts.

The battle manager clears active stage slot `+0x98` while retaining the last
confirmed slot in its native snapshot at `+0x114`. The native Stage Select
initializer restores that snapshot. Clean resident code subsequently replaces
the restored selection with slot `0` when the active slot is `-1`.

The guarded edit changes that sentinel branch to skip the redundant selection
setter. Its existing delay slot and continuation are retained. A guarded update
wrapper runs the native selector update and, when Free Battle returns Cancel,
copies the still-live selector choice into manager snapshot byte `+0x114`
before native cleanup destroys the selector. Nonnegative active-stage paths
still call the setter, Practice still supplies slot `6`, and stage
confirmation, cancellation, cleanup, and loading otherwise remain native.
