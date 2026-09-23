# NUN3 Hero's Memorial Monument stage

## Research coverage

- **Assigned scope:** identify the clean NUN3 battle-stage archive for Hero's Memorial Monument and describe the data needed for an NA2 port.
- **Exploration depth:** the NUN3 battle-stage pointer array, fourth stage record table, named archive, CCS table, and relevant clean NA2 first-stage structures were inspected statically.
- **Confirmed coverage:** stage identity, archive size and CCS structure, the separate scene-record table, collision resources, and boundary-node names.
- **Unresolved or untested:** exact NUN3 effect-object behavior and whether every native material and animation is compatible with NA2's renderer.
- **Deliberate exclusions and overlap:** this document describes clean game data only. The attempted conversion and build routing belong to [the experiment](attempt.md).
- **Evidence limitations:** the mapping and format findings come from the clean binaries and extracted archives; they do not establish runtime behavior after conversion.

## Stage identity

The NUN3 `BATTLE.BIN` stage table at Ghidra `0x00913410` contains pointers to 32-byte scene records. Its fourth entry points to the record table at live `0x0092D2C0` (Ghidra `0x0092D280`). The first record points to the Shift-JIS name `英雄の慰霊碑` and to `stage/s04.ccs`; that name identifies Hero's Memorial Monument. There are 37 nonzero records before the zero terminator. The stage-specific records are in `BATTLE.BIN`, not in the archive.

Clean NUN3 `STAGE/S04.CCS` is a 626,606-byte gzip stream with a 1,355,476-byte CCS payload. Its compressed SHA-256 is `3720FB38174EE2B61057DECECDE79795936AE41FE51DA5E5F5556DDF22AB2CDB`. The CCS table contains 75 file names and 1,211 object names. The archive has `BLT_bg`, `BLT_obj`, the two paired `DMY_line_010/020` node families, and the `DMY_linemin/max` nodes. It does not contain `BIN_bgdata`.

For the rear boundary, the donor has `DMY_b_cl_3_nor` and `_1` where the clean NA2 first-stage configuration requests `DMY_b_cl_1_nor` and `_1`. The front `DMY_f_cl_1_nor` pair is already named as NA2 expects. Static model names in the donor may occur twice: a group section and a model-object section share the `OBJ_` name. NA2's clean stage static-model records resolve `OBJ_` names to model-object sections.
