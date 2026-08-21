# Texture patcher engine

This reusable engine interprets feature-owned container, mapping, and strategy
tables and derives fixed-size texture replacements from canonical sources. The
active UI translation package lives under
`@builder/localization/texture_patcher/`.

`whole` strategies use the complete donor payload and may apply a guarded
upward translation to one bounded region of an 8-bit indexed donor texture
after proving that the discarded rows are transparent. `mapped` strategies can
copy one or more compatible TEX/CLT pairs, import a bounded indexed-row region,
or replace an indexed texture with a guarded top-left crop after proving every
discarded donor pixel is transparent. A crop may optionally remap pixels to a
declared subset of the donor's own palette by nearest raw RGBA distance. Every
result preserves the original compressed member capacity. Source,
decompressed-payload, and fixed-size replacement hashes remain recorded in the
feature-owned tables as provenance and diagnostics, but they do not gate
derivation or ISO builds. Indexed-region translations use the pinned Zopfli
encoder so their replacement bytes do not vary with the host zlib version.

Every build route uses the shared optional derivation cache at
`@cache/texture_patcher/` relative to the active project or release
application directory. Entries are keyed by the actual target and donor
container bytes, applicable strategy and mappings, texture-patcher
implementation, and compression runtime. A hit still verifies the replacement
size and hash; a missing, corrupt, or unwritable cache regenerates normally.
The cache is disposable, is not a build input, and is never packaged into or
required by a release. Build output reports reused and newly derived container
counts, and texture-patcher logs record the result for each container.

## Invokes

None. The configuration orchestrator applies its fixed-size texture results directly.
