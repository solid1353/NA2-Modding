# PNACH module

Runtime-only and emulator-owned sections remain native PNACH fragments under
`sections/`. The section header, named cheat, subcheat lines, and their commented
enabled/disabled state are preserved exactly. `render.py` assembles them into
the canonical PNACH before actualization.

`Rendering` lives here because EE address `0x00AF3694` is runtime memory not
backed by bytes in the boot ELF.
