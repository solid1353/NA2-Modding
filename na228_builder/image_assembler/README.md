# Image assembler

The image assembler is mandatory build infrastructure, not a feature module.
Modules and the configuration composer produce one closed `AssemblyPlan`; the
assembler alone copies the clean source into an exact caller-owned candidate,
applies guarded equal-size file replacements, inserts declared files into
verified free extents, mirrors file-tree changes across ISO9660 and UDF, and
reparses the complete result before returning it for promotion.

`operations.py` defines immutable file replacements, insertions, renames, and
donor file/range references. `assembler.py` owns candidate creation and final image
verification. `iso9660.py` and `udf.py` implement the physical filesystem
metadata work. Feature packages never own or enable this infrastructure.

## Resident payload insertion

The current assembly plan inserts generated `PRG/228.BIN` into a verified-zero
extent without increasing the image size. The ISO9660 `PRG` directory occupies
one sector at extent 265; its logical size grows from 264 to 306 bytes when the
42-byte `228.BIN;1` record is added. The assembler mirrors the entry in UDF,
preserves nonzero tail bytes, and reparses both filesystems to verify matching
paths, extents, sizes, and payload hashes.

`FLIST` is unchanged. The boot-ELF loader requests `cdrom0:\\PRG\\228.BIN`
directly, and the native cache-miss path performs an ordinary disc lookup.
