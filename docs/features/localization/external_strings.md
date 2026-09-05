# Compact external strings

The integrated `string_patcher` externalizes only complete replacements whose
final encoded text exceeds the original slot and whose mapping declares
validated pointer references. Placement is recomputed at build time; the
canonical translation table contains no placement markers. T30's complete
`Ultimate` text is externalized through `NA2_BTL@0x209CB4`. The pipeline never
reads or patches `ADV.bin`.

The feature contributes 30 distinct external string fragments to the shared
resident payload selected by the current translation.

The translation importer resolves and validates the canonical mapping data and
pointer inventory once.
The consuming string patcher then:

1. encodes every final replacement and assigns fit-derived overflowing
   mappings to external storage while compiling every fitting mapping inline;
2. contributes the selected complete replacements as named payload fragments;
3. declares symbolic redirects for every inventoried use of those slots.

The payload builder assigns addresses to all selected feature contributions.
The composer resolves the string symbols before their fixed-size pointer writes
pass through `binary_patcher`. Shared loading and reservation are documented in
[Runtime injection](../runtime_injection/implementation.md).

All binary output is generated in memory by the importer, string patcher,
payload builder, composer, and binary patcher. No patched ELF, BIN, or ISO
payload is stored in Git.

## Canonical inputs

- `translation_importer/mappings.tsv` contains guarded source locations and
  text, executable official donor translations, optional user prefixes and
  overrides, and every optional pointer reference.
  Three continuation rows deliberately reuse their containing full-message
  pointer.
Only `mappings.tsv` is covered by the translation importer's contribution to
the configuration-resource fingerprint.
Payload-builder configuration is executable infrastructure rather than feature
data; engine code is covered by the builder-tree fingerprint, while
documentation is not an executable input.

Comparative loader and payload-layout evidence is documented in
[NUN6 external strings](../nun6/localization/external_strings.md).

## Payload contribution

Strings are resolved through the importer, encoded as CP1252 plus a terminator,
deduplicated by exact encoded bytes, and contributed by symbol. No feature owns
its final payload offsets. The selected external strings contain 1,475 encoded
bytes; T364 and T117 deliberately share one identical symbol.
Structured save-progress families preserve their original consecutive
NUL-terminated slots plus an empty terminator, preventing traversal into the
next payload message. The generated payload has no constructor range; the
infrastructure bootstrap loads it once and calls its documented return-only
entry.

## Safety properties

- exact mapping/ref counts and fit-derived placement coverage;
- fixed-length guarded edits only;
- deterministic fragment linking, symbol resolution, payloads, and pointer order;
- rejection of overlaps, stale original bytes, unexpected mappings, malformed
  references, changed source binaries, or memory-envelope overflow;
- no `FLIST` edit unless runtime testing later proves direct `cdrom0:\\PRG\\...`
  lookup insufficient.

The shared runtime-injection feature owns the payload file and loader. The image
assembler owns ISO insertion, fixed image size, directory records, extents,
payload hashes, and final-tree validation.
