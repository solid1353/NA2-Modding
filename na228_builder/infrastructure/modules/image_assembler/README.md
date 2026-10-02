# Image assembler

The image assembler is a mandatory infrastructure module. It is always enabled,
rather than selected as a feature.
Modules and the configuration composer produce one closed `AssemblyPlan`; the
assembler alone copies the clean source into an exact caller-owned candidate,
applies guarded equal-size file replacements, inserts declared files into
verified free extents, mirrors file-tree changes across ISO9660 and UDF, and
reparses the complete result before returning it for promotion.

`operations.py` defines immutable file replacements, insertions, and renames.
`assembler.py` normalizes and validates the plan's paths once, and owns
candidate creation and final image verification. `iso9660.py` and `udf.py`
implement the physical filesystem metadata work on those normalized paths.
Feature packages never own or enable this infrastructure.

## Mod directory

Every file the build adds lives in the root `228` directory: the resident
payload `228/228.BIN`, the texture pack `228/UI.BIN`, the loading splash
`228/SPL.CCS`, and `228/MANIFEST.TSV`. The composer writes the manifest
from the assembly plan as tab-separated `source_path`, `output_path`,
`source_sha256`, and `output_sha256` rows, one per changed source file; the
output path differs only for the renamed boot ELF.

An insertion whose parent directory does not exist creates that directory under
an existing one. The assembler places the new directory in one verified-zero
sector, appends its record to the parent, and rebuilds every path-table copy and
the path-table size. Existing path-table rows keep their order, which in NA2 is
disc order rather than name order; new directories follow the existing rows at
their level. In UDF it adds a directory File Entry and a data block with the
parent FID, appends the directory FID to its parent, increments the parent's
link count, and updates the integrity directory and file counts. New files are
placed in verified-zero extents without increasing the image size, and both
filesystems are reparsed to verify matching paths, extents, sizes, hashes, and
path tables.

`FLIST` is unchanged. The boot-ELF bootstrap loads the payload through the
generic PRG loader, whose `cdrom0:\PRG\` prefix it switches to `228\` for that
one load and restores before the payload entrypoint runs. The texture pack and
splash are opened through explicit `CDV:228/` paths, which bypass the cached
directory list.
