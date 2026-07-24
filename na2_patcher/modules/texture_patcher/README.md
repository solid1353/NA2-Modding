# Texture patcher engine

This reusable engine interprets feature-owned container, mapping, and strategy
tables and derives fixed-size texture replacements from canonical sources. The
active UI translation package lives under
`na2_patcher/features/localization/texture_patcher/`.

Mapped packages may copy complete compatible TEX/CLT component ranges, remap a
declared number of top rows into the target palette, or inset the right edge of
one declared raw indexed-texture region. Region coordinates use CCS TEX storage
order, whose rows are bottom-to-top. Every transform preserves the target CCS
structure and fixed member size and is guarded by paired component signatures
and pinned derived hashes.

## Invokes

None. The profile orchestrator applies its fixed-size texture results directly.
