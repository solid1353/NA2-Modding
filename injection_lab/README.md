# NA2 injection lab

Maintained development lab for compiling ordinary C into PS2 EE MIPS, linking
it with Armips, emitting a PNACH for Current Narutimate Accel v2.28, and
explicitly reloading that PNACH through PCSX2's PINE interface.

The imported `NA2-C.zip` source used for the port has SHA-256
`8A4D94465C4F7938DCC2D49D3DAA268BDF800AD7E89112B8E09BAA6EE58D289E`.
The exact `NA2-C/` tree supplied on 2026-07-28 is preserved by Git commit
`087d4970a644819da7241dfcbc8f2cde85b4ce71` and removed from the live tree by
`5da885bee016b8ef06daced2cc0d6de85647b4c2`. Recover it for inspection with
`git archive --format=zip --output=NA2-C-history.zip 087d497 -- NA2-C`; do not
execute it directly.

That snapshot is internally mixed. Its root README, Makefile, and `build.sh`
come from the earlier Midnight Club 3 proof. Its compact `linker.asm`,
`src/test.c`, `src/Main.h`, and supplied `SLPS_258.37` demonstrate the NUN5
adaptation, but `gen_pnach.py` still pins MC3/SLES values (`C0659AD1`,
`SLES_556.05`), and the checked-in generated linker files describe a different,
much larger build. The maintained lab ports the demonstrated mechanism, not
that inconsistent snapshot as a runnable package.

## What the imported VS Code task does

The task named `Gerar PNACH` in `.vscode/tasks.json` only starts
`./gen_pnach.sh` through Git Bash with the source root as its working
directory. The shell wrapper adds the supplied PS2DEV compiler and PS2SDK tools
to `PATH`, then runs `python3 gen_pnach.py`.

The generator:

1. reads game-function addresses from comments in `src/Main.h` and parses
   `linker.asm` for imported objects, labels, assembly blocks, and hooks;
2. compiles the referenced C files with `ee-gcc`;
3. assigns addresses to their `.text`, `.rodata`, `.data`, and `.bss`
   sections and generates Armips linker inputs;
4. runs Armips to resolve the linked code and hook instructions;
5. converts the resulting words into PNACH `patch=1,EE,...` writes; and
6. opens the configured CRC-named PNACH with Python mode `w`, truncating and
   rewriting the existing file at the same path.

There is no PCSX2 API call, process control, or explicit reload command. The
apparent hot reload comes from PCSX2 watching the active PNACH file: the
in-place truncate/write changes the file, PCSX2 reparses it, and its recurring
`patch=1` entries write the new code/data into EE memory. A changed map table
is data, so the game reads the new values on later frames and the selection
changes immediately.

Rewriting code at an already executed address is less reliable because PCSX2
may keep the old host-JIT translation. The maintained lab adds the fixed
dispatcher and alternating code banks described below; that is the part the
imported task does not provide.

The original imported NUN5 payload base `0x003E4410` is not free in clean NA2
and crashed the game. This adaptation targets only the Current ISO identity
derived at build time and uses payload-builder's explicit development
reservation at `0x008F0000-0x008F3D00`.

The source proof inserts its C call into the five-word epilogue beginning at
runtime `0x001D0578`. Archived NUN5 and clean Current contain the identical
words `DFBF0000 27BD0010 03E00008 00000000 00000000` there. The maintained
linker replaces them with `jal injectionLabTick`, a delay-slot `nop`, and the
equivalent moved epilogue. The native `jal WakeupThread` at `0x001D0570`
remains untouched.

The default local runtime is `@pcsx2_dev`, which resolves to the custom PCSX2
runtime copied into `UN Workshop/pcsx2/dev/`. That directory
uses portable mode and a copied, independent set of the user's PCSX2
configuration, BIOS, game settings, and input profiles. Its dedicated PINE port
is separate from stable PCSX2. Launch
`@pcsx2_dev/pcsx2-qtx64-avx2-dev.exe`, start Current with cheats enabled, then
build and install from the repository root:

```powershell
.\injection_lab\test.ps1
```

The script verifies Current's serial and CRC, `228.BIN` memory contract, two
independent ELF boundary values, and the complete five-word hook window before
compiling. The generator fails with a nonzero exit when an imported source,
compiler/tool query, linker step, linker label, or hook symbol is missing
instead of accepting a stale or incomplete PNACH. The runner temporarily
replaces only the matching Current PNACH inside `@pcsx2_dev/cheats` and records
enough state to
restore an existing regular file or symbolic link. Edit `src/test.c`, then run
the same command again. The original `NA2-C.zip` proof's VS Code task only runs
its generator and relies on an observed PCSX2 file-watcher path. The maintained
lab does not rely on that behavior. After refreshing the installed regular
PNACH in place, it reads the enabled PINE port from the PCSX2 configuration and
sends the parameterless `ReloadPatches` opcode `0x10`. It requires a synchronous
`OK` reply, meaning the CPU-thread reload completed before the script returns.
This requires the project's reload-enabled PCSX2 build; an ordinary build
rejects the opcode explicitly. `-PinePort <port>` overrides configuration
discovery for an isolated development instance. A source-derived build ID makes
the example print exactly once for each distinct build without emitting its
mutable state as a recurring PNACH write.

PCSX2 can keep executing a cached host translation after PNACH overwrites code
at an address that already ran. The lab avoids that failure with a fixed
dispatcher at `0x008F0000`, an active-entry pointer at `0x008F0010`, and two
alternating C banks: `0x008F0100-0x008F1F00` and
`0x008F1F00-0x008F3D00`. The dispatcher reads the pointer each call, so a new
build enters the inactive bank and is translated fresh. The first dispatcher
build requires one clean game restart; later C rebuilds are reloadable in the
running game.

## Production runtime-injector C mode

The lab can compile one canonical runtime-injector C source through the same
`ee_c_fragments.py` frontend used by normal composition, link its complete
declared fragment closure into the inactive bank, and redirect one explicitly
declared production entry through the fixed dispatcher:

```powershell
.\injection_lab\test.ps1 `
  -ProductionSource font_v2_core `
  -ProductionEntry localization.font.v2.controls_adapter
```

`production_entries.tsv` is the ABI allowlist. The adapter rejects helper
fragments and undeclared entrypoints instead of guessing whether an internal C
function is safe to call directly. It reads source, import, fragment-alias, and
relocation declarations from the canonical Localization `runtime_injector`
package; it does not copy that C or maintain a second production fragment
layout.

Before emitting the PNACH, production mode:

1. hashes the exact `PRG/228.BIN` extracted from the selected Current ISO;
2. finds a retained build record with the same payload SHA-256 and rejects
   matching records whose symbol maps disagree;
3. verifies every symbol-map row used by the adapter against the exact payload
   bytes and recorded fragment hash;
4. resolves only the selected source's declared external imports against that
   exact map;
5. links every declared source fragment into one bank and rejects overflow or
   undeclared dependencies; and
6. guards the production resident entry's first eight bytes before replacing
   them with a tail jump to the dispatcher.

Existing file-backed BTL/ETC/ELF caller hooks remain untouched. The PNACH
changes only the selected resident entry, fixed dispatcher/pointer, and inactive
development bank. Switching between generic and production mode or selecting
a different production entry simply overwrites the development PNACH.
Recompiling alternates banks normally.

This is a development accelerator, not release validation. It requires a
savestate from the same exact Current payload and compatible writable resident
state. A successful hot reload proves only behavior reached through the
selected entry in that running state; it does not prove clean boot, file-backed
hook installation, overlay lifetime, normal payload composition, or unrelated
callers. Final accepted changes still require the normal build/integration
boundary and the user's requested regression check.

### Rebuild automatically on save

Start the generic lab watcher with its default source directory:

```powershell
.\injection_lab\watch.ps1
```

The default `SourcePath` is the complete `injection_lab/src` directory. It
watches that tree recursively, plus `linker.asm` and `gen_pnach.py`. In VS
Code, run `Tasks: Run Task` and choose `Injection Lab: Watch src`.

For canonical runtime-injector C, provide its path and an allowlisted entry:

```powershell
.\injection_lab\watch.ps1 `
  -SourcePath .\na2_patcher\features\localization\runtime_injector\sources\font_v2_core.c `
  -ProductionEntry localization.font.v2.controls_adapter
```

The watcher infers the production source ID from `c_sources.tsv`; a path cannot
bypass the canonical declaration. Production mode also watches
`c_sources.tsv`, `c_imports.tsv`, `c_fragments.tsv`, and
`production_entries.tsv`.

`SourcePath` may name the supported source file or its containing source
directory. Directories are hashed recursively. Omitting it selects the lab's
`src` directory; production mode accepts a directory only when it contains the
canonical source selected by `ProductionEntry`.

Both modes run one guarded build immediately. After a save, the watcher waits
for its inputs to remain unchanged for 400 ms and invokes `test.ps1` serially.
Saves during a build queue one follow-up build; builds never overlap. A failed
compile, install, or PINE reload prints the complete child output and leaves
the watcher running for the next save.

In VS Code, run `Tasks: Run Task` and choose
`Injection Lab: Watch production Font`, then select the entry to exercise.
Stop its dedicated terminal with Ctrl+C. The task does not start automatically
when the repository opens and does not guess an entry.

Successful rebuilds alternate banks and explicitly reload patches through
PINE. Stop one watcher before starting another; the lab does not enforce a
restart or cleanup boundary when switching modes or production entries.
Watcher success has the same narrow development meaning as a manual hot
reload; it is not release or runtime acceptance.

To compile and validate without installing:

```powershell
.\injection_lab\test.ps1 -BuildOnly
```

Production mode accepts the same switch:

```powershell
.\injection_lab\test.ps1 -BuildOnly `
  -ProductionSource font_v2_core `
  -ProductionEntry localization.font.v2.controls_adapter
```

The installer replaces the exact CRC alias with one generated regular PNACH.
Every later build rewrites that file and requests the explicit PINE reload.
Stop the watcher with Ctrl+C. There is no separate removal or restoration
workflow.

While the install record identifies a regular file inside the PCSX2 cheats
directory, normal `na2` actualization preserves the file instead of replacing
it with the canonical cheat symlink. The lab state never becomes a launch
gate. Without a valid install record, regular files at
NA2.28-managed CRC aliases are treated as orphaned lab artifacts and repaired
to canonical symlinks, or removed when the canonical PNACH is empty. Corrupt
or stale lab state is ignored by actualization, while unrelated game
identities remain untouched.

Ordinary `patch=1` PNACH writes are reapplied continuously. Mutable state must
not be initialized through those recurring writes. The adapted object keeps
its build ID in `.bss`; the generator reserves that address but emits no PNACH
write for it.

## Local dependencies

The repository tracks the lab source but not its imported toolchain, extracted
ELF inputs, object files, or generated PNACH/linker outputs. The local
toolchain must use this layout:

```text
@ps2_msys/1.0/local/ps2dev/
├── ee/bin/       # ee-gcc, ee-nm, ee-objdump
└── ps2sdk/bin/   # armips
```

`test.ps1` derives `data/FILES/SLOP_NA2.28` and `data/FILES/228.BIN` from the
verified Current ISO on every build. The ignored `data/`, `obj/`, and `build/`
directories are reproducible outputs and must not be committed. The imported
`@ps2_msys/` tree is a local shared dependency and is not redistributed by
this repository.

The original proof of concept was based on:
https://youtu.be/-N2QR7W1_kM
