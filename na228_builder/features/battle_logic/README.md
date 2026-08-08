# Battle logic

The `battle_logic` catalog subtree is the exact static migration of the canonical
PNACH section, including the optional disabled substitution-cost change. The
release configuration enables both battle-behavior nodes and disables
`sub_cost_3_15`. Each node owns its guarded binary edits directly.
