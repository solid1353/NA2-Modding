# Dialogue localization

## Research coverage

- **Assigned scope:** Historical executable targets that may contain dialogue
  corresponding to official NUN5 text.
- **Exploration depth:** The historical audit matched five ELF file targets;
  their screen contexts and structural family were not traced.
- **Confirmed coverage:** The audit recorded five candidate offsets that
  matched official NUN5 dialogue at that time.
- **Unresolved or untested:** Screen context, reachability, complete structural
  family, and current mapping status remain unresolved.
- **Deliberate exclusions and overlap:** Current localization mappings and mod
  implementation are outside this document.
- **Evidence limitations:** The historical match alone does not establish a
  current mapping row, runtime visibility, or shared ownership among the five
  targets.

## Unresolved executable targets

ELF file targets `0x2FFD40`, `0x2FFD58`, `0x2FFD80`, `0x2FFDB0`, and
`0x2FFDC0` matched official NUN5 dialogue during the historical audit but are
not current mapping rows. Their screen context and complete structural family
remain unverified.
