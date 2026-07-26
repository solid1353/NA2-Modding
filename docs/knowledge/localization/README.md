# Localization knowledge

Cross-workstream localization decisions and status that apply beyond one
specialized area belong here.

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
