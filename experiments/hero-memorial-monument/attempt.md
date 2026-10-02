# Hero's Memorial Monument stage attempt

## Status

This attempt is not selected by the builder. The resulting `NA v2.28 - 2026-09-23 03.09.51 - 4568C02D94FE.iso` built successfully, but the user reported that the game returned to the PS2 BIOS mid-fight. The cause has not been established. The first NA2 battle-stage load slot (`STAGE/S01.CCS`) was routed to a converted NUN3 Hero's Memorial Monument archive through the external CCS pack.

## Research coverage

- **Assigned scope:** identify the clean NUN3 battle-stage archive for Hero's Memorial Monument, describe the data needed for an NA2 port, and record the conversion attempt.
- **Exploration depth:** the NUN3 battle-stage pointer array, fourth stage record table, named archive, CCS table, and relevant clean NA2 first-stage structures were inspected statically.
- **Confirmed coverage:** stage identity, archive size and CCS structure, the separate scene-record table, collision resources, and boundary-node names.
- **Unresolved or untested:** the cause of the mid-fight return to the BIOS, exact NUN3 effect-object behavior, and whether every native material and animation is compatible with NA2's renderer.
- **Deliberate exclusions and overlap:** NUN3 battle stages in general are owned by [battle stage knowledge](../../docs/knowledge/gameplay/stages.md#nun3-battle-stages-compared-with-na2).
- **Evidence limitations:** the mapping and format findings come from the clean binaries and extracted archives; they do not establish runtime behavior after conversion.

## NUN3 source

The NUN3 `BATTLE.BIN` stage table at Ghidra `0x00913410` contains pointers to 32-byte scene records. Its fourth entry points to the record table at live `0x0092D2C0` (Ghidra `0x0092D280`). The first record points to the Shift-JIS name `英雄の慰霊碑` and to `stage/s04.ccs`; that name identifies Hero's Memorial Monument. There are 37 nonzero records before the zero terminator. The stage-specific records are in `BATTLE.BIN`, not in the archive.

Clean NUN3 `STAGE/S04.CCS` is a 626,606-byte gzip stream with a 1,355,476-byte CCS payload. Its compressed SHA-256 is `3720FB38174EE2B61057DECECDE79795936AE41FE51DA5E5F5556DDF22AB2CDB`. The CCS table contains 75 file names and 1,211 object names. The archive has `BLT_bg`, `BLT_obj`, the two paired `DMY_line_010/020` node families, and the `DMY_linemin/max` nodes. It does not contain `BIN_bgdata`.

For the rear boundary, the donor has `DMY_b_cl_3_nor` and `_1` where the clean NA2 first-stage configuration requests `DMY_b_cl_1_nor` and `_1`. The front `DMY_f_cl_1_nor` pair is already named as NA2 expects. Static model names in the donor may occur twice: a group section and a model-object section share the `OBJ_` name. NA2's clean stage static-model records resolve `OBJ_` names to model-object sections.

## Conversion

The conversion is based on the [NUN3 source](#nun3-source) above. It retains the donor's models, textures, collision resources, and boundary nodes. A generated `BIN_bgdata` supplies NA2's four boundary records, the two collision-resource records, and generic static-model records for the donor's background, scenery, monument, and river objects. The rear boundary node pair is renamed to the name expected by NA2's boundary constructor.

The conversion does not port NUN3's separate scene-record implementation for ambient animations and reactive props. The result is a static stage attempt, not a behavioral reimplementation of every NUN3 stage effect.

The candidate compressed archive is `hero_memorial_stage.ccs.gz`. The source-guarded derivation is `derive_nun3_memorial_stage.py`, invoked through `@scripts/lib/run_python.ps1` with the clean NUN3 `S04.CCS`, clean NA2 `S01.CCS`, and output path. The attempted build used the checked-in candidate archive and its hashes, not either donor source. Stage Select retained the original first-slot thumbnail and name.
