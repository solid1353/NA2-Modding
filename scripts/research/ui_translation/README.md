# UI translation research tools

`match_assembly_function.py` compares one preserved Ghidra assembly function
against another build by normalized instruction structure. It accepts both the
`text:006bcfd0   ...` overlay export form and the truncated
`SECTION4:0038...` boot-ELF form, so existing exports can be reused without
another disassembly.

```powershell
python scripts/research/ui_translation/match_assembly_function.py `
  "work/UI translation/disassembly_refs/NA2/BTL/BTL.BIN.txt" `
  FUN_006bcfd0 `
  "work/UI translation/disassembly_refs/NUN5/BTL/BTL.BIN.txt"
```

## Offline memory triage

`scan_memory.py` searches an extracted EE RAM snapshot for exactly one ASCII,
hex, little-endian `u32`, or float pattern and prints matching addresses.
`inspect_sprite_objects.py` scans the same snapshot for likely 0xF8-byte CC2
sprite objects and reports their screen geometry, source dimensions, resource
pointer, and `TEX_`/`CLT_` name.

```powershell
python scripts/research/ui_translation/scan_memory.py `
  work/ui-translation/inputs/eeMemory.bin --ascii TEX_TITLE

python scripts/research/ui_translation/inspect_sprite_objects.py `
  work/ui-translation/inputs/eeMemory.bin --name title --limit 20
```

Both tools are read-only and write tabular results to standard output. They
support the runtime object and selector findings under
[`docs/knowledge/localization/ui/`](../../../docs/knowledge/localization/ui/).
They use structural filters rather than type metadata, so every candidate must
be confirmed in the matching game state before it becomes canonical evidence.

## UI texture authoring

`texture_derivation.py` owns mapped texture derivation, exact-size
compression, and preview output used when intentionally authoring new localized
UI assets. It reads CCS sections through the builder's
`na228_builder/infrastructure/ccs.py` parser. It is research tooling and is
never imported by the builder. Run it through the maintained Python wrapper:

```powershell
& scripts/lib/run_python.ps1 `
  -PackageSet ui_texture_research `
  -Module scripts.research.ui_translation.texture_derivation `
  -ArgumentList @(
    'verify',
    '--package', 'scripts/research/ui_translation/ui_texture_data'
  )
```

The Victory texture generator derives canonical source inputs without storing
CCS or binary blobs:

```powershell
python scripts/research/ui_translation/generate_victory_texture_mappings.py --write
```

It classifies the Victory CCS recipes. `texture_derivation.py` keeps the
ENDDEMO emblem's donor meshes and animations with its atlas, remapping object
references to NA2 while retaining the fixed compressed capacity. Character-name
rectangle construction is owned by the injected Victory implementation, not
shared descriptor edits. See [Victory evidence](../../../docs/knowledge/localization/ui/victory.md)
and [UI integration](../../../docs/features/localization/ui_layout.md).
