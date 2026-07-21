# String patcher engine

This reusable engine validates feature-owned semantic string declarations and
translation imports, compiles them into an in-memory binary-patcher package,
and delegates guarded writes and conflict validation to `binary_patcher`. The
active declarations live under `na2_patcher/features/localization/string_patcher/`.
