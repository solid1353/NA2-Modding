# Binary patcher module

This internal engine applies selected guarded edits to verified clean binaries.
`@builder/catalog/edits.json` owns production edit roots; feature files under
`@builder/catalog/` assign their IDs to selectable leaves. A root is either one
primitive edit, one fixed-stride table replacement, or a semantic group with
named primitive and table children under its `edits` map. The catalog loader
expands table records before this module receives them. The TSV files in
`operations/` define each primitive operation's allowed fields and basic types.
Root and child maps are serialized
alphabetically. Every root identity uses the `e__` prefix and its catalog
ownership path; grouped child identities name the semantic edit within
that root. Catalog settings reference root identities through their single
`patches` array.

A primitive edit may contain a nonempty `description` when concise purpose or
provenance belongs specifically to that edit. Its description is logged as the
concrete edit reason but never changes execution. A group description labels
the organizational root and is not a concrete log reason. Broader feature
behavior, research, analysis, procedures, and history remain in their canonical
documentation.

## Invokes

None. `binary_patcher` is the terminal module-level executor for concrete
guarded file edits.

## Safety model

- All persisted paths are relative.
- Every input target is checked by size and SHA-256.
- Every destination range is checked by exact bytes or a range SHA-256.
- Catalog authoring uses `destination_offset` for one address or a unique
  `destination_offsets` list for at least two. The catalog loader normalizes
  both forms to the nonempty list this module receives. Multiple offsets expand
  into independently guarded and logged concrete edits with otherwise
  identical behavior.
- A catalog `replace_table` records one target, table base, stride, field offset,
  and semantic record map. The catalog loader validates its fixed record shape
  and expands it into ordinary guarded `replace` edits; the binary patcher has
  no table-specific execution path.
- A grouped root contains a nonempty, one-level map of semantic child edits.
  The catalog loader expands it before operation validation, so the binary
  patcher receives the same concrete edit model as a flat primitive root.
  Destination ranges from different children must not overlap; ordered chains
  remain separate roots.
- A `replace` edit declares exactly one of a static `replacement_hex` or an
  adapter. Adapters in `adapters.py` either convert a validated typed catalog
  value or encode fixed readable values selected by a bare setting. Fixed-value
  adapters produce both the destination guard and replacement bytes without
  weakening the ordinary guarded-replacement contract.
- `nul_padded_text` encodes fixed readable text with a declared codec and exact
  slot length, requires room for a NUL terminator, and zero-pads both guarded
  and replacement values to that length.
- Copy sources are covered by the complete source target's size and SHA-256.
- Configuration selection determines which catalog nodes apply; the engine's
  synthetic groups and patches are internal execution objects only.
- Patch ranges may overlap; ordered composition accepts compatible chains and rejects guard conflicts.
- Concrete edits are simulated in deterministic order before output creation. Already-satisfied
  writes and guarded chains are allowed; incompatible staged bytes are rejected as conflicts.
- JSON source order is a maintained serialization convention, not an execution
  contract. The loader derives execution order from catalog selection and the
  composer resolves edits by target and destination offset.
- Outputs must be new, stay outside input roots, and preserve target sizes.
- Every applied edit and before/after file hash is logged.
- Do not use fixed-address PNACH writes against on-demand overlays such as
  `BTL.BIN` or `ETC.BIN`; test those edits by patching the file and rebuilding.

## Production use

The catalog loader expands grouped roots and fixed-stride tables, validates
every resulting primitive against its operation manifest, resolves the shared
target registry, and constructs the engine's in-memory package.
Normal builds do not load separate binary-patcher TSV data packages. Build logs
retain the selected edit inventory and before/after hashes beneath the
configuration build record.
