# Localization knowledge

Cross-workstream localization decisions and status that apply beyond one
specialized area belong here.

## Index

- [Localization feature documentation](../../features/localization/README.md)
- [External string payload](external_string_payload.md)
- [Font knowledge](font/README.md)
- [UI knowledge](ui/README.md)
- [Substitution behavior](substitution.md)
- [Localization and asset hypotheses](hypotheses.md)
- [Legacy 2022 artifact audit](legacy_2022_artifacts.md)

## Intentional exclusions

### Shop

Shop is intentionally omitted from Mode Select and is not a maintained
localization target. Shop-owned translations, texture imports, layout patches,
tests, and detailed maintenance documentation were removed together in the
Git commit carrying this policy. Git history is the recovery archive.

The QoL `Remove Shop` patch remains the shipped default. The disabled
`Restore Shop` cheat remains available for deliberate inspection. Strings
owned by Game Mode Select or Collection remain maintained even when their text
mentions Shop.

## Battle and Practice quit-confirmation assembly

Paired Battle and Practice states for both return destinations prove that the
BTL modal assembles its body from four independently selected strings:

`mode head + connective + destination + terminator`

The mode head is T63 (`Battle`) or T64 (`Practice`), the shared connective is
T66, and T67 terminates the question. The destination is not the T68/T69 pause
menu label. The modal selects separate short BTL slots at `0x208DA0`
(`Character Select`) and `0x208DC0` (`Game Mode Select`), represented by T2201
and T2202. T63/T64 must resolve only through the donor's `%1`; including the
text before `%2` duplicates T66 at runtime. This split produces all four NUN5
sentences without storing newlines in canonical mappings; draw-time wrapping
remains renderer-owned.
