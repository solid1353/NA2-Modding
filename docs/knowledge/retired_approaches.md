# Retired approaches

This is the canonical record of removed project architectures and experiments
whose failure or replacement still prevents repeated work. Git history remains
the archive for deleted implementations; current component documents describe
only maintained behavior and reusable technical evidence.

## Font implementation

- The `m01`, `m02`, `v22`, `v23`, and semantic-palette packages are not
  implementation parents. Their raw schema-v1 replicas remain recoverable from
  Git commit `55d1163`; donor raster and palette combinations broke NA2 glyph
  semantics or reinterpreted heavily used palette indices.
- The July v1 renderer-metric and layout-wrapper port was removed on 2026-07-28.
  Enabled roots reached every v2 fragment but none of its ten fragments, while
  the runtime injector still linked an unreachable 1,847-byte blob (1,856 bytes
  aligned). Do not restore its hooks, generated blob, builders, tests, or
  tracking rows.
- Character Select's per-string X table and selected-footer exception were
  replaced by one measured, centered row-family contract. The old string
  coordinates encoded examples rather than layout behavior.
- The Save confirmation absolute-position experiment copied NUN5 coordinates
  into a differently sized NA2 modal. Its header edits, initializer hook,
  adapter, and payload were removed; NA2's native positions remain authoritative.
- The Font replay-bundle worker/verifier path was removed after capture and
  comparison moved to the maintained request-based E2E transaction. Do not
  recreate a parallel replay-bundle format.

## Runtime injection

- Injection Lab's generic PNACH mode installed a recurring call at
  `0x001D0578`. Removing its file did not undo the live EE write; switching the
  same session to the production dispatcher invoked a Font entry with unrelated
  registers (`a0 = 0x7`) and caused renderer TLB misses. The generic/production
  mode switch and install/remove state were retired. Current direct-PINE
  transactions use guarded callers and no recurring cheat write.
- Overlay plans have one unversioned `entry_symbols` contract. Schema-version
  dispatch and the schema-v1 `entry_symbol` fallback were removed rather than
  retained as compatibility.

## Build and package workflows

- Pre-`request.json` E2E transaction adoption, the `na228 e2e remove` retirement
  guard, migration of old ISO-name rows in `builds.tsv`, and verified-ISO
  registry schema-v1 migration were removed. Only current inputs are accepted.
- The standalone binary-patcher TSV loader and CLI were removed. Catalog-owned
  declarations build the maintained in-memory patch package directly.
- A physical `string_patcher/strings.tsv` module was never promoted. Derived
  translation rows feed the in-memory binary package without that intermediate
  interface.

## Duplicated gameplay patch

The retired generic Testing feature duplicated four substitution edits already
captured as canonical evidence in
[`gameplay/substitution.md`](gameplay/substitution.md). Its executable rows were
removed; Git history retains the discarded declaration, while the topic record
owns the addresses and runtime conclusions.
