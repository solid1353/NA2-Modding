# Catalog data redesign

Status: design in progress. Implementation is not approved.

This document defines the pending coordinated redesign of catalog implementation
identities, human-readable descriptions, canonical ordering, release catalog
documentation, and consolidation of the current project design documentation.
It is temporary and must be retired when the task is complete.

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
- Catalog-node description data and release documentation.
- Documentation made obsolete by information moved during this redesign.
- Canonical integration of the accepted binary-patcher JSON design and useful
  remaining binary-runtime migration documentation.
- Retirement of every current design document under `docs/workstreams/project/`
  when the implemented result has canonical documentation.

## Identity redesign

- Redesign edit and injection identities together.
- Replace opaque edit IDs with meaningful identities.
- Replace opaque injection, hook, and named payload-fragment IDs with meaningful
  behavioral identities.
- Update every catalog reference and maintained generator affected by renamed
  identities.
- Do not retain redundant identity fields inside definitions when the containing
  JSON key already owns identity.

The exact naming scheme is unresolved. It must be designed explicitly before
implementation approval and must not be inferred from the discarded candidate.

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
- Enforce canonical ordering through permanent repository tests.
- Do not make source ordering a build-loader contract, and do not make the
  loader reject otherwise valid unsorted definitions.

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
- information that belongs in its existing documentation context rather than
  with one edit.

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
  canonical JSON description data.
- Bundle the description data with releases so users can discover the available
  selectable nodes.
- Produce human-readable catalog documentation from the canonical description
  data.

The description-file path, JSON structure, and generated documentation format
are unresolved and must be designed before implementation approval.

## Preservation

- Preserve every executable edit operation, target, offset, guard, hash,
  replacement, blob identity, and catalog selection.
- Preserve every injection relationship and executable declaration.
- Preserve catalog behavior, configuration behavior, build behavior, release
  behavior, and binary output except for the separately designed addition of
  release catalog documentation.

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
- Validate the release bundle's description data and generated catalog
  documentation against their canonical source.
- Validate that all useful current material from the retired design documents
  has a canonical owner and that no current project design document remains.

## Outside this task

- Redesigning binary-patcher operations, targets, configurations, or build
  behavior.
- Moving or splitting implementation files.
