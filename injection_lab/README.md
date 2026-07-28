# NA2 injection lab

Maintained development lab for compiling ordinary C into PS2 EE MIPS, linking
it with Armips, and emitting a reloadable PNACH for Current Narutimate Accel
v2.28.

The original imported NUN5 payload base `0x003E4410` is not free in clean NA2
and crashed the game. This adaptation targets only the Current ISO identity
derived at build time and uses payload-builder's explicit development
reservation at `0x008F0000-0x008F3D00`.

Start Current with cheats enabled, then build and install from the repository
root:

```powershell
.\injection_lab\test.ps1
```

The script verifies Current's serial and CRC, `228.BIN` memory contract, two
independent ELF boundary values, and exact hook bytes before compiling. It
temporarily replaces only the matching Current PNACH alias and records enough
state to restore an existing regular file or symbolic link. Edit `src/test.c`,
then run the same command again. The original `NA2-C.zip` proof's VS Code task
only runs its generator; the generator triggers PCSX2's observed automatic
refresh by truncating and rewriting the active CRC-named regular PNACH in
place. This lab preserves its guarded build/install separation, but refreshes
the installed regular PNACH using that same write pattern instead of replacing
the filesystem object. If a PCSX2 configuration does not reload it, select
`System` -> `Reload Cheats/Patches` as a fallback. A source-derived build ID
makes the example print exactly once for each distinct build without emitting
its mutable state as a recurring PNACH write.

To compile and validate without installing:

```powershell
.\injection_lab\test.ps1 -BuildOnly
```

To remove the test and restore any pre-existing regular PNACH:

```powershell
.\injection_lab\test.ps1 -Remove
```

The installer records and temporarily replaces only the exact CRC alias. After
the first guarded install, later builds truncate and rewrite that same regular
file so PCSX2's file watcher can observe the change. It refuses refresh or
cleanup if another process or user changed the installed PNACH. Removal
restores the previous file or managed symbolic link, including its relative
target, but already-applied memory writes remain until Current is restarted.
While that guarded install record is active, normal `na2` actualization
recognizes and preserves the exact recorded Current PNACH instead of replacing
it with the canonical cheat symlink. Unknown, stale, or tampered regular PNACH
files still fail closed.

Ordinary `patch=1` PNACH writes are reapplied continuously. Mutable state must
not be initialized through those recurring writes. The adapted object keeps
its build ID in `.bss`; the generator reserves that address but emits no PNACH
write for it.

## Local dependencies

The repository tracks the lab source but not its imported toolchain, extracted
ELF inputs, object files, or generated PNACH/linker outputs. The local
toolchain must use this layout:

```text
injection_lab/msys/1.0/local/ps2dev/
├── ee/bin/       # ee-gcc, ee-nm, ee-objdump
└── ps2sdk/bin/   # armips
```

`test.ps1` derives `data/FILES/SLOP_NA2.28` from the verified Current ISO on
every build. The ignored `data/`, `obj/`, and `build/` directories are
reproducible outputs and must not be committed. The imported `msys/` tree is a
local dependency and is not redistributed by this repository.

The original proof of concept was based on:
https://youtu.be/-N2QR7W1_kM
