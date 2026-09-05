# Development injection

The maintained development injector rebuilds selected EE C or assembly,
pauses PCSX2 through PINE, verifies and writes one guarded transaction into the
reserved `0x008F0000..0x008F3D00` range, clears translated-code state, reads the
writes back, and restores the VM's prior running or paused state. It does not
modify the release `PRG/228.BIN`.

Existing file-backed callers normally continue to target their resident
symbols. Development application may redirect an allowlisted resident entry to
the temporary copy, avoiding rewrites of every caller.

The smoke hook replaces the native no-op call at `0x001085A0` with
`project.hot_reload_message`. The function uses the native renderer at
`0x00379040` to display `HOT RELOAD HH:mm:ss` for 300 rendered frames after an
application.

Use the project `na228 c` and `na228 w` commands rather than invoking the Python
implementation directly. The project command verifies the loaded build and
waits for the resident payload marker before applying a transaction.
