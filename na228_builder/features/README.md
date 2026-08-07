# Feature packages

Feature packages own reproducible declarative capability data independently of
profiles and reusable engines.

Each feature contains:

- the structurally required root `README.md`, used as a concise feature
  contract and index;
- one or more direct module directories named for registered engines under
  `na228_builder/modules/`.

Substantial feature/module documentation may live under the repository root
`docs/` hierarchy and be linked from the feature README.

The feature folder name is its identity. There is no feature manifest, module
catalog, or selection table. A profile row enables every module directory the
feature owns; omission disables the feature.

The profile pins one deterministic aggregate hash covering every canonical
module input in the feature. Documentation, engine code, and non-input helpers
are excluded. Paths, derived module IDs, and module order are not repeated in
profile metadata.
