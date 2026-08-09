# Catalog data redesign

Status: design in progress. Implementation is not approved.

This document defines the pending coordinated redesign of catalog implementation
identities, human-readable descriptions, canonical ordering, the bundled
self-documenting release configuration, and consolidation of the current
project design documentation. It is temporary and must be retired when the task
is complete.

## Outcome

- Give edits, injections, hooks, and named payload fragments useful identities.
- Keep implementation definitions outside the selectable catalog tree and
  update catalog references to the redesigned identities.
- Add useful human-readable implementation descriptions without inventing
  undocumented meaning.
- Move catalog-node descriptions into canonical description data and make that
  information available to release users.
- Integrate the useful current content of the project design documents into its
  canonical documentation owners and retire every current design document.
- Preserve executable behavior and binary output.

## Scope

- `na228_builder/catalog/implementation/edits.json`.
- `na228_builder/catalog/implementation/injections.json`.
- Catalog edit and injection references.
- Maintained generators that emit or update affected definitions.
- Canonical ordering tests.
- Edit and injection descriptions.
- Catalog-node description data and the bundled release configuration.
- Documentation made obsolete by information moved during this redesign.
- Canonical integration of the accepted binary-patcher JSON design and useful
  remaining binary-runtime migration documentation.
- Retirement of every current design document under `docs/workstreams/project/`
  when the implemented result has canonical documentation.

## Identity redesign

- Redesign edit and injection identities together.
- Replace opaque root edit and injection IDs with meaningful identities using
  the same `<catalog_path>__<semantic_identity>` format.
- Encode each catalog-path level and the semantic suffix as `snake_case`, with
  `__` separating the levels and suffix.
- Do not repeat catalog-path meaning in the semantic suffix unless it is needed
  to keep the identity clear.
- Give nested hooks and named payload fragments concise local semantic names;
  do not repeat their owning root definition's catalog-path prefix.
- Update every catalog reference and maintained generator affected by renamed
  identities.
- Do not retain redundant identity fields inside definitions when the containing
  JSON key already owns identity.

## Injection ownership

- Each root injection definition remains one cohesive runtime behavior unit.
- Keep related hooks and payload declarations together inside their owning
  injection.
- Do not impose a one-to-one relationship between hooks and payload fragments.
  Several hooks may share one fragment, and one hook may depend on several
  fragments.
- Do not split hooks, payloads, or fragments into separate files.
- Preserve hook guards, targets, offsets, hashes, encodings, symbols, payload
  code, compilation behavior, and runtime behavior.

## Canonical ordering

- Alphabetically serialize root edit and injection definition maps.
- Alphabetically serialize nested named maps whose ordering has no execution
  meaning.
- Order root edit and injection identities by their catalog-derived prefixes.
- Remove `CATALOG_FEATURE_ORDER` and load discovered feature files in
  alphabetical filename order.
- Enforce canonical ordering through permanent repository tests.
- Do not make source ordering a build-loader contract, and do not make the
  loader reject otherwise valid unsorted definitions.

## Catalog file discovery

- Treat root catalog JSON files matching `__*.json` as catalog metadata, not as
  selectable feature files.
- Discover every other root catalog `*.json` as a feature file.

## Definition descriptions

Keep edit, injection, and hook descriptions limited to concise information that
belongs specifically to that definition. Do not place information there when
its canonical owner is feature, component, operational, knowledge, research, or
other documentation, including broader behavior, contracts, procedures,
evidence, analysis, derivations, and history.

## Edit descriptions

- Edit definitions may contain an optional `description` field.
- Add it only when existing documentation contains useful information that
  canonically belongs with that specific edit.
- Use concise plain language describing useful purpose, rationale, or
  provenance.
- Preserve documented meaning faithfully. Do not invent or extrapolate.
- Omit `description` when no useful qualifying information exists.
- A present description must be a nonempty string and must not affect patch
  execution.

Do not transfer content merely because it exists. Exclude:

- opaque evidence IDs, legacy identifiers, and ticket-like codes;
- repetitive context, status notes, review chatter, obsolete history, and
  unrelated evidence;
- disassembly analysis, research evidence, hypotheses, detailed derivations,
  and broader feature history;
- information excluded by the shared definition-description boundary above.

Moving information into an edit description must not leave a duplicate at its
source:

- If all qualifying information from source content is transferred, delete that
  source content.
- If only part is transferred, remove only the transferred portion and preserve
  the rest.
- If nothing is transferred, leave the source content unchanged.

This move-not-copy rule applies to every consulted document.
`binary-runtime-migration-documentation.md` must be retired by this task after
its useful current content has been moved to the appropriate canonical owners.

## Injection descriptions

- Injection definitions may contain optional, nonempty human-readable
  descriptions where useful documented information exists.
- Individual hooks may contain descriptions when they have distinct documented
  purposes.
- Do not invent descriptions.

## Catalog and release descriptions

- Move catalog-node descriptions out of executable feature-tree files into
  canonical JSON description data at
  `na228_builder/catalog/__reference.json`.
- Let `__reference.json` partially mirror the catalog tree and contain only
  `description` fields and the ancestor keys needed to reach them. Do not
  duplicate catalog nodes that have no description.
- Require every path supplied by `__reference.json` to exist in the selectable
  catalog. Descriptions are optional, but every present description must be a
  nonempty string.
- Keep repository configurations in their current compact format.
- Name the single bundled release configuration `config.json` and give it a
  distinct self-documenting format. Expand its `features` tree so every
  selectable node contains the reserved boolean field `enabled` and its
  canonical `description` when one exists, alongside its directly nested
  selectable children.
- Keep `overrides` as the other top-level release-configuration field. The
  release loader reads `enabled` values from the annotated `features` tree and
  then applies `overrides` normally.
- Merge `__reference.json` into the bundled release configuration during
  packaging by expanding the structure from the real catalog and overlaying the
  sparse descriptions. Do not bundle a separate reference file and do not
  generate Markdown documentation.
- Validate that removing descriptions and unwrapping every `enabled` value
  produces the same effective selection as the compact merged repository
  configuration.

The bundled structure is:

```json
{
  "features": {
    "localization": {
      "enabled": true,
      "description": "Translated game content.",
      "translated_text": {
        "enabled": true,
        "description": "Imports translated text and applies its derived string patches."
      }
    }
  },
  "overrides": {}
}
```

## Preservation

- Preserve every executable edit operation, target, offset, guard, hash,
  replacement, blob identity, and catalog selection.
- Preserve every injection relationship and executable declaration.
- Preserve catalog behavior, configuration behavior, build behavior, release
  behavior, and binary output except for the approved self-documenting release
  configuration format.

## Documentation consolidation and retirement

- Integrate the accepted current architecture and contracts from
  `binary-patcher-json-design.md` into the canonical builder and component
  documentation. Do not leave that material isolated in a workstream design
  document.
- Review `binary-runtime-migration-documentation.md` and move each piece of
  useful current information to its canonical owner. Edit-specific information
  selected under the description rules belongs in `edits.json`; other durable
  information belongs in the relevant component, feature, research, or
  operational documentation.
- Do not transfer obsolete, redundant, low-value, or purely transitional
  material merely to preserve it.
- After the implementation and documentation are complete, delete
  `binary-patcher-json-design.md`,
  `binary-runtime-migration-documentation.md`, and this design document.
- Update the project workstream index so it contains no links to retired design
  documents.

The canonical destination mapping is:

- Move catalog hierarchy, repository configuration, reference ownership, and
  loader-validation contracts from `binary-patcher-json-design.md` into
  `na228_builder/README.md`.
- Move edit and operation contracts into
  `na228_builder/modules/binary_patcher/README.md`.
- Move injection-unit, hook, and payload contracts into
  `na228_builder/modules/runtime_injector/README.md`.
- Move shared payload-placement contracts into
  `na228_builder/payload_builder/README.md`.
- Move bundled `config.json` and packaging behavior into
  `docs/runbooks/release.md`.
- Move concise definition-local information from
  `binary-runtime-migration-documentation.md` into the corresponding edit,
  injection, or hook descriptions; move selectable-node descriptions into
  `catalog/__reference.json`; move current feature behavior into the existing
  owning `docs/features/` documents; and move only unique durable research
  evidence into an existing appropriate `docs/knowledge/` owner.
- Discard legacy IDs, evidence IDs, migration chatter, duplicated notes,
  obsolete candidates, low-value history, and other content with no current
  canonical value.

## Validation

- Audit one-to-one identity migration for every edit, injection, hook, named
  payload fragment, and catalog reference.
- Prove executable definition values and relationships are unchanged apart from
  renamed identities and approved descriptions.
- Add permanent tests for canonical ordering and optional nonempty description
  validation.
- Run focused catalog, binary-patcher, runtime-injector, generator, and release
  tests.
- Run the full permanent test suite and a real build proving unchanged binary
  output.
- Validate the bundled `config.json` annotated feature tree against the real
  catalog, compact merged repository configuration, and `__reference.json`.
- Validate that all useful current material from the retired design documents
  has a canonical owner and that no current project design document remains.

## Outside this task

- Redesigning binary-patcher operations, targets, repository configuration
  inheritance, or unrelated build behavior.
- Moving or splitting implementation files.
