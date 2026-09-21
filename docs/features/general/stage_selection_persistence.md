# Stage selection persistence

`features.general.stage_selection_persistence` restores the last highlighted
stage when Free Battle or Practice Stage Select opens again during the current
game session, including after Cancel returns to Character Select. The first
Free Battle setup still opens on the first available stage, while the first
Practice setup still opens on the training field. The selection is not written
to save data and therefore does not persist across game restarts.

The battle manager clears active stage slot `+0x98` while retaining the last
confirmed slot in its native snapshot at `+0x114`. The native Stage Select
initializer restores that snapshot. Clean resident code subsequently replaces
the restored selection with slot `0` when the active slot is `-1`.

The guarded edit changes that sentinel branch to skip the redundant selection
setter. Its existing delay slot and continuation are retained. A guarded update
wrapper runs the native selector update and, when either supported mode returns
Cancel, copies the still-live selector choice into manager snapshot byte
`+0x114` before native cleanup destroys the selector for Free Battle entry type
`1` or Practice entry type `2`.

Practice's resident caller always supplies slot `6` to a second selection
setter after the initializer has restored manager snapshot `+0x114`. A guarded
wrapper at that call uses the snapshot when it contains a valid slot `0..23`
and retains the supplied slot `6` when the snapshot contains its initial
`0xFF` sentinel. The Free Battle path is unchanged: its cleared active slot
uses the existing sentinel branch to retain the initializer's restored choice,
and its first setup still selects slot `0`. Stage confirmation, cancellation,
cleanup, and loading otherwise remain native.
