# String patcher engine

This reusable engine validates feature-owned semantic string declarations and
translation imports, chooses inline or compact external placement, compiles all
file-backed edits into one in-memory binary-patcher package, and delegates
guarded writes and conflict validation to `binary_patcher`. It may also return
generated image insertions to the profile compositor. The active declarations
live under `na2_patcher/features/localization/string_patcher/`.
