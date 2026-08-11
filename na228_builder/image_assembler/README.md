# Image assembler

The image assembler is mandatory build infrastructure, not a feature module.
Modules and the configuration composer produce one closed `AssemblyPlan`; the
assembler alone copies the clean source into the reserved `.building` path,
applies guarded equal-size file replacements, inserts declared files into
verified free extents, mirrors file-tree changes across ISO9660 and UDF, and
reparses the complete result before returning it for promotion.

Digest-only assembly applies and reparses the same guarded operations through a
sparse in-memory overlay, then streams the complete logical image into SHA-256.
It creates neither a `.building` file nor a destination ISO; normal retained
builds continue to use physical staging.

`operations.py` defines immutable file replacements, insertions, renames, and
donor file/range references. `assembler.py` owns atomic staging and final image
verification. `iso9660.py` and `udf.py` implement the physical filesystem
metadata work. Feature packages never own or enable this infrastructure.
