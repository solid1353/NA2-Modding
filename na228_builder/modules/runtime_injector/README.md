# Runtime injector module

This runtime-injector pipeline validates feature-owned resident code/data fragments,
their internal symbolic relocations, and guarded symbolic game-file hooks.
It contributes fragments to the shared `payload_builder`; after the builder
assigns final addresses, the composer resolves each hook template and this
engine compiles the concrete writes into an in-memory `binary_patcher`
package. A feature never chooses an offset inside `PRG/228.BIN` or owns its
loader, memory reservation, or final runtime address.

Canonical production inputs are the shared
`@builder/modules/targets.tsv` registry, hooks and payload declarations from
`@builder/patches/*.json`, and referenced
repository sources and assets.
Catalog nodes select unified dotted patch IDs.
There is no separate runtime-injector data directory or standalone TSV package
format; the catalog loader is the only declaration parser.

Each patch identity follows its catalog ownership path. The root map and
unordered nested maps are serialized alphabetically. Hooks and named payload
fragments use concise local semantic identities rather than repeating their
owner's catalog path. Optional nonempty patch and hook descriptions hold
only definition-local purpose or provenance and never affect execution.

A `payload` declaration is either a C source, an assembly source, or a static
data/rodata fragment. C and assembly sources contain their path, namespace,
private imports, emitted fragment aliases, and optional ABI metadata. C uses
`kind: "c"` with an exact `.c` suffix; preprocessed EE assembly uses
`kind: "asm"` with an exact `.S` suffix. Static fragments contain their
bytes or guarded blob, alignment, initialization marker, and private
relocations. Shared declarations are stored once in a unified patch at the
lowest common catalog ancestor.

Hooks and payload fragments are not one-to-one: several hooks may target one
fragment, and one hook may depend on multiple fragments. Their guards,
relocations, and symbolic references remain together in the owning injection
unit.

Configuration selection controls hooks. A shared payload declaration
contributes only when its owning patch is selected.
When every hook in a feature is disabled, the internal runtime-injector
invocation contributes no payload or target writes.

## Game hook contract

The PS2 executes linked EE machine code, not C source. The builder compiles
registered `.c` and `.S` sources into relocatable fragments, assigns their
addresses in `PRG/228.BIN`, resolves their internal calls, and encodes each
guarded game-file hook as a concrete `j` or `jal` instruction.

C sources own ordinary logic. Assembly sources own register-sensitive entry
contracts, displaced instructions, delay slots, tail calls, and rejoins. A
`jal` hook behaves as an ordinary call and returns to the following game
instruction. A `j` hook replaces a control-flow block and must declare its
continuation explicitly.

The boot-ELF loader enters through the constructor path at `0x00607314`, loads
the shared `PRG/228.BIN`, calls its initialization entry, and resumes the native
constructor. Individual features own their guarded call sites and resident
symbols; this module owns their compilation and relocation contract, not their
behavior.

## Invokes

- `binary_patcher` for the resolved concrete guarded writes.

## Uses infrastructure

- `payload_builder` for deterministic fragment placement, relocation, and the
  one shared resident payload.
