# Legacy Package History

Normal builds now use hash-pinned modules from `na2_patcher/profiles/current/`.
This folder temporarily retains the font m01 compatibility ZIP required for
`GF4.BIN`. Prior packages remain available through Git history after retirement.

- Use unique filenames and never overwrite an older package. When a package has
  a `vNN` version, place it after the `YYYYMMDD_HHMMSS` timestamp.
- Legacy explicit `f`, `t`, and `ft` commands may still select `NA2_APPLY__*`
  inputs during the migration; the default workflow never selects newest files.
- Builder ZIP installation and generated translation TSVs are no longer part of
  normal builds.
- Copy explicitly accepted frozen references to `milestones/packages/`; ordinary
  package history stays here.
