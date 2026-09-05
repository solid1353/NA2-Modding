# Menu-input analysis tools

These read-only scripts compare clean regional MIPS binaries or Ghidra C
exports to locate face-button tests, calls, and address references. They
support the native relationship map in
[`docs/knowledge/runtime/menu_input/`](../../../docs/knowledge/runtime/menu_input/)
and the selected regional-input evidence in
[`docs/features/localization/`](../../../docs/features/localization/); they do
not patch binaries or generate catalog entries.

Inputs are caller-supplied clean binary modules and, where required, matching
Ghidra C exports. Reports are written to standard output as TSV-like rows or a
small disassembly. For example:

```powershell
python scripts/research/menu_input/analyze_menu_input_exports.py `
  work/menu-input/inputs/na2.c `
  work/menu-input/inputs/nun5.c `
  --changed-masks-only
```

`analyze_menu_input_exports.py` and `analyze_mips_face_button_masks.py` find
regional candidates; `extract_mips_masks_in_ghidra_functions.py` checks named
functions; the remaining scripts disassemble a bounded range or locate direct
calls and split address loads. Their matching is structural and heuristic, so
promote only candidates confirmed against exact clean inputs. Record native
relationships in `function_map.tsv`.
