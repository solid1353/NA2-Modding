# Feature packages

Feature packages own reproducible declarative capability data independently of
profiles and reusable engines.

Each feature contains exactly:

- one root `README.md` containing all feature and module-specific documentation;
- one or more direct module directories named for registered engines under
  `na2_patcher/modules/`.

The feature folder name is its identity. There is no feature manifest, module
catalog, or selection table. A profile row enables every module directory the
feature owns; omission disables the feature.

The profile pins one deterministic aggregate hash covering every canonical
module input in the feature. Documentation, engine code, and non-input helpers
are excluded. Paths, derived module IDs, and module order are not repeated in
profile metadata.
