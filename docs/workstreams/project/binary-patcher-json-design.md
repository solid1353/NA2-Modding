# Binary patcher JSON redesign

Status: design in progress.

This document records only the decisions accepted during the binary-patcher
JSON redesign discussion. It is not a JSON schema or an implementation plan.

## Agreed decisions

- Migrate the binary-patcher definitions from TSV to JSON after the data model
  has been simplified.
- Preserve every existing `description`. Descriptions will be optional at any
  JSON level.
- Represent group identity with the JSON key. Do not retain separate
  `group_id` or `name` fields.
- Represent patch identity with the JSON key. Do not retain separate `patch_id`
  or `name` fields.
- Remove group-level and patch-level `enabled` fields. Enabling will be handled
  separately by a design that has not yet been settled.
- Remove patch `confidence` and `status`.
- Existing patches included in the current migration may temporarily contain
  `"proven": false`. Presence means that the patch still needs proof. Remove
  the field when that patch is proven; never set it to `true`. Do not add the
  field to newly created patches. Remove the concept entirely after the
  migrated set is proven.
- Move useful `evidence_id`, `review_notes`, and edit `reason` content to the
  appropriate documentation, discard stale or duplicated content, and remove
  those fields from executable data.
- Remove edit `order`. It changes no current binary-patcher or runtime-injector
  edit output; current edit identity and target offsets already produce the
  same sequence.
- Represent edit identity with the JSON key. Do not retain a separate
  `edit_id` field.
- Blob edits store a SHA-256 guard for the expected destination range. Replace
  and copy edits store the expected destination bytes directly.
- Remove copy-source `source_expected_hex` and `source_expected_sha256`. The
  complete source target is already verified by size and SHA-256 before its
  range is copied.
- Preserve the `fill` operation and its single-byte fill value.
- Remove `blob_offset`. Every blob must contain exactly the replacement payload
  used by its edit rather than exposing a slice of a shared blob.

## Still under discussion

- The JSON structure and the replacement enabling mechanism.
- Whether blob references retain a separate `blob_sha256` in addition to
  canonical feature/package hashing.
- Which other remaining edit fields should survive.
- The migration and validation procedure beyond the temporary `proven` rule.
