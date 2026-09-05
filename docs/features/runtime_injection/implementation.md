# Runtime injection

NA228 links every selected resident code and data fragment into one generated
`PRG/228.BIN`. Features declare symbols, relocations, and guarded hooks; they do
not choose final payload offsets. The runtime injector compiles those
declarations, the payload builder assigns addresses, and the image assembler
installs the shared file and loader.

## Resident layout

The boot ELF reserves `0x008F3D00..0x00940100` for the linked payload. The
current payload occupies `0x008F3D00..0x008F8550`; unused bytes through
`0x00940100` remain reserved so ordinary payload growth does not move the game
heap. The heap user base is therefore fixed at `0x00940120` and its end sentinel
at `0x01FF5FF0`.

The reservation sits above the largest native overlay end, `0x008DD080`.
Overlay space and the high-memory system tail are not payload capacity. The
clean address-space and allocator findings are documented in
[EE address space](../../knowledge/runtime/ee_memory_map/address_space.md),
[allocator behavior](../../knowledge/runtime/ee_memory_map/allocator_and_capacity.md),
and [runtime lifetimes](../../knowledge/runtime/ee_memory_map/runtime_lifetimes.md).

[`observations.tsv`](observations.tsv)
preserves the matched modified and vanilla allocator observations, including
the Active Adventure rows. These measurements establish the reservation's
runtime cost; they are not a description of the unmodified game.

## Hook execution

A guarded game instruction is replaced by `j` or `jal` to a linked resident
symbol. C owns ordinary logic. Assembly owns register-sensitive entry, displaced
instructions, delay slots, tail calls, and rejoins. The runtime-injector module
contract is documented in
[`na228_builder/modules/runtime_injector/README.md`](../../../na228_builder/modules/runtime_injector/README.md).

## Development injection

The separate range `0x008F0000..0x008F3D00` is reserved for temporary direct
injection and is never included in a release image. The maintained injection
tools compile one selected source closure, pause PCSX2 through PINE, verify and
write the exact guarded transaction, clear translated-code state, read the
writes back, and restore the prior VM state.

The visible smoke hook replaces the native no-op call at `0x001085A0` with a
call to `project.hot_reload_message`. It uses the native text renderer at
`0x00379040` to display `HOT RELOAD HH:mm:ss` for 300 rendered frames. The
counter is reset with each application.

Earlier PNACH experiments established two continuing constraints: ordinary
`patch=1` data initializers are reapplied and cannot hold mutable injected
state, and overwriting already translated EE code does not reliably refresh its
host translation. The maintained direct-memory workflow therefore writes the
reserved range once and explicitly clears translated-code state.

## Capacity and stability

The fixed reservation reduces the vanilla heap by `0x63080` bytes. In the
tightest matched observation, the modified build retained `0x759260` bytes of
total allocator free space and a `0x52B4C0` largest contiguous gap. A separate
32-byte payload-growth experiment showed that allowing the heap boundary to
follow the exact payload end can perturb allocation order and later rendering.
Keeping the structural boundary fixed prevents heap-base movement, although it
does not guarantee identical allocation order between builds.
