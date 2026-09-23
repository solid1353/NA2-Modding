# Hero's Memorial Monument stage attempt

## Status

This attempt is not selected by the builder. The resulting `NA v2.28 - 2026-09-23 03.09.51 - 4568C02D94FE.iso` built successfully, but the user reported that the game returned to the PS2 BIOS mid-fight. The cause has not been established. The first NA2 battle-stage load slot (`STAGE/S01.CCS`) was routed to a converted NUN3 Hero's Memorial Monument archive through the external CCS pack.

## Conversion

The conversion is based on [clean NUN3 stage evidence](nun3_source.md). It retains the donor's models, textures, collision resources, and boundary nodes. A generated `BIN_bgdata` supplies NA2's four boundary records, the two collision-resource records, and generic static-model records for the donor's background, scenery, monument, and river objects. The rear boundary node pair is renamed to the name expected by NA2's boundary constructor.

The conversion does not port NUN3's separate scene-record implementation for ambient animations and reactive props. The result is a static stage attempt, not a behavioral reimplementation of every NUN3 stage effect.

The candidate compressed archive is `hero_memorial_stage.ccs.gz`. The source-guarded derivation is `derive_nun3_memorial_stage.py`, invoked through `@scripts/lib/run_python.ps1` with the clean NUN3 `S04.CCS`, clean NA2 `S01.CCS`, and output path. The attempted build used the checked-in candidate archive and its hashes, not either donor source. Stage Select retained the original first-slot thumbnail and name.
