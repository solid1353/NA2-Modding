# Builder catalog and configuration redesign
Status: approved and implemented.
This document records the accepted builder catalog and configuration design. It is not a JSON schema.
## Scope
- Introduce one repository-wide `catalog.json` as the master definition of the complete feature hierarchy and its executable patch data.
- Migrate only binary-patcher and runtime-injector executable data to the catalog for now.
- Keep texture-patcher, translation-importer, targets, and operation definitions in TSV for now.
- Represent retained translation and texture behavior as selectable catalog leaves; their executable TSV data remains outside the catalog and is invoked internally when the corresponding leaf is enabled.
- Do not create separate module-data or patch-data JSON files.
- Do not represent modules in the catalog or configurations. Builder engines remain internal implementation details.
- Do not introduce schemas, schema versions, or migrations while this design is changing.
## Catalog hierarchy
- `catalog.json` has no `features` root wrapper. Its top-level keys are actual feature keys.
- Eliminate groups as a concept.
- Catalog nodes may nest directly to any depth; there is no fixed feature/group/patch hierarchy and no `children` wrapper.
- Use meaningful, stable `snake_case` keys. Do not retain opaque IDs, generated sequence IDs, or separate ID/name fields.
- Preserve every existing `description`. The field is optional at any catalog level and ignored by the parser.
- Keep enablement out of the catalog.
- The reserved catalog fields are `description`, `proven`, `edits`, `hooks`, and `payload`. Every other key is a directly nested selectable node.
- A selectable patch is an ordinary meaningful node in the hierarchy. There is no `patches` wrapper, separate `patch_id`, or patch-name field.
- Binary edits, hooks, and payload declarations may coexist in the same selectable node. There is no module discriminator or module-owned wrapper around them.
- In canonical patch field order, binary `edits` appear before injected-code data.
## Ownership and extraction
- Keep every declaration inside the patch that owns it by default.
- Extract a declaration only when more than one patch actually consumes that declaration.
- Place extracted shared data at the smallest common catalog owner of all consumers, not automatically at the catalog root.
- Keep a source's private imports, emitted fragments, relocations, and other private declarations inside that source or its owning patch.
- Keep patch-specific hooks and binary edits inside their patch.
- Do not preserve separate registries merely because the previous TSV representation used separate tables.
- Shared injected-code declarations live in `payload` at the nearest common selectable owner of their consumers.
## Executable fields
- Remove `enabled`, `confidence`, and `status` from executable definitions.
- Migrated executable patches may temporarily contain `"proven": false`. Presence means the patch still needs proof. Remove the field when the patch is proven; never set it to `true`; never add it to new patches. Remove the concept after the migrated set is proven.
- Move useful `evidence_id`, `review_notes`, and `reason` content to the appropriate documentation, discard stale or duplicated content, and remove those fields from executable data.
## Configurations
- Replace profiles with configurations named `test`, `release`, and `development`.
- Configurations are the sole owners of enablement and contain no canonical definitions, patch data, or module information.
- Configurations have no `features` root wrapper. Their top-level feature keys correspond directly to the catalog's top-level selectable keys.
- A configuration value corresponding to a catalog node is `true`, `false`, or an object.
- `true` enables the node's complete selectable catalog subtree.
- `false` disables the node's complete selectable catalog subtree.
- An object configures that node's direct selectable children individually.
- An object is forbidden for a lowest-level selectable catalog node; leaves must be `true` or `false`.
- Whenever a configuration descends with an object, its keys must match that catalog node's direct selectable child keys exactly. Missing and extra keys are invalid.
- Configurations contain no `enabled` or `description` fields.
```json
{
  "battle_logic": true,
  "localization": {
    "font_layout": {
      "command_relationships": true,
      "character_modal": false
    },
    "textures": false
  }
}
```
## Targets
- Keep shared target definitions outside `catalog.json` in one flat `targets.tsv` registry. Catalog edits and hooks reference targets by ID.
- The current registry path is `na228_builder/features/targets.tsv`, but restructuring may move it; the final path is not fixed.
## Binary edits
- Store binary edits under the owning patch's `edits` object before injected-code data.
- Represent edit identity with a meaningful JSON key. Do not retain a separate `edit_id` field.
- Remove edit `order`; it changes no current binary-patcher or runtime-injector output.
- Preserve an explicit `operation` discriminator. The parser reads it directly and never infers an operation from object shape.
- Preserve `destination_target_id` on each edit.
- Every edit stores exactly one destination guard. Compact replace/copy ranges use `expected_hex`; existing large replace/copy ranges and blob replacements use `expected_sha256` so the original range is not duplicated inline.
- Remove copy-source `source_expected_hex` and `source_expected_sha256`; the complete source target is already verified by size and SHA-256.
- Preserve `fill` and its single-byte fill value.
- Remove `blob_offset`; each blob contains exactly one edit's replacement payload.
- Preserve `blob_sha256` as an independent guard that guarantees the asset has not changed.
- Retain `length` for copy and fill edits. Derive replace length from its replacement bytes and blob length from the exact blob file size.
## Binary operation contracts
- Define runtime manifests named `replace.tsv`, `copy.tsv`, `blob.tsv`, and `fill.tsv` under the binary-patcher engine's `operations/` directory.
- The filename defines the operation name. Every manifest is independently complete and lists the operation's full allowed field set, including common edit fields, using `field`, `required`, and `type` columns.
- Use the manifests for generic required-field, unknown-field, and basic-type validation.
- Keep operation execution and behavioral checks such as target existence and range bounds in code handlers.
- Do not introduce manifest inheritance or schema versions.
## Injected code and hooks
- Runtime-injection target changes are hooks, not generic edits.
- Store every patch-specific hook inside its owning patch; extract only declarations genuinely consumed by multiple patches.
- Represent hook identity with a meaningful JSON key. Do not retain a separate hook or edit ID field.
- Hooks have no `operation` field because the containing structure already defines them as hooks.
- Preserve hook encoding because current hooks use both non-linking `j26` and linking `jal26` encodings.
- The runtime-injection engine continues resolving payload symbols after final payload placement and turning resolved hooks into guarded concrete binary replacements for application.
- `payload` directly maps meaningful payload IDs to declarations. A C source declaration contains `kind: "c"`, its repository-relative `path`, `namespace`, private `imports`, and its emitted `fragments`. A static fragment declaration contains its fragment kind, order, alignment, inline value or guarded blob, optional relocations, and optional initialization marker.
- C-fragment ABI and purpose metadata lives on the specific emitted fragment. Static adapter ABI metadata lives on that adapter declaration; it names its source only when ownership cannot be inferred from nesting.
- Static-fragment relocations remain inside the fragment that owns them. Source imports remain inside the source that owns them.
## Validation
- The loader rejects duplicate JSON keys, invalid selectable keys, configuration/catalog structural mismatches, objects at configuration leaves, non-false `proven` values, unknown binary-operation fields, missing required fields, malformed types, invalid targets, bad ranges, and bad asset hashes.
- Migration equivalence covers all binary edits, enabled selections, runtime fragments, runtime hooks, the linked resident payload, exported symbols, and resolved hook writes before removal of the superseded TSV inputs.
