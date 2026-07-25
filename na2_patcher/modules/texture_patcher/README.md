# Texture patcher engine

This reusable engine interprets feature-owned container, mapping, and strategy
tables and derives fixed-size texture replacements from canonical sources. The
active UI translation package lives under
`na2_patcher/features/localization/texture_patcher/`.

`whole` strategies use the complete donor payload. `mapped` strategies can copy
one or more compatible TEX/CLT pairs, import a bounded indexed-row region, or
replace an indexed texture with a guarded top-left crop after proving every
discarded donor pixel is transparent. A crop may optionally remap pixels to a
declared subset of the donor's own palette by nearest raw RGBA distance. Every
result preserves the original compressed member capacity and is accepted only
when its source, decompressed payload, and fixed-size replacement hashes match
the feature-owned tables.

## Invokes

None. The profile orchestrator applies its fixed-size texture results directly.
