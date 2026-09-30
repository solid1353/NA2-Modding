# Resident CCS runtime

This document records the reusable runtime behavior around the resident CCS
container and object services in NA2. It is deliberately about the in-memory
runtime, not the static CCS inventory. The names below are descriptive working
identities, not recovered original symbols.

## Research coverage

- **Assigned scope:** the resident CCS/resource-object runtime centered on
container lookup `FUN_001aa450`, object lookup `FUN_001a8f00`, and their load,
parse, publication, reference, playback, and release families: handle
identities, name/ID lookup, special-object traversal, ownership and lifecycle,
async behavior, battle use, container-owned memory, and what a foreign CCS
(such as one from NUN3) must match to load. It is not a static inventory of CCS
files.

- **Exploration depth:** coverage is **bounded**, not exhaustive. It is
instruction-level for the functions listed in the identity table below and
their directly relevant control-flow edges, concentrated in these resident
clusters:

- selected name/query helpers in `0x00114F00..0x00116EF0`;
- play-table construction/teardown in `0x001A09D0..0x001A2520`;
- container lookup, parsing, cross-reference, ownership, and destruction
  functions in `0x001A8C80..0x001AD9C0`, plus the type-`0x0A00` constructor
  `FUN_001b2800` and streamed-block functions
  `FUN_001b4c60..FUN_001b52c0`;
- load-wrapper and queue functions `FUN_001cf060..FUN_001cfd90`;
- residency-manager functions `FUN_003b2ed0..FUN_003b37f0`;
- the stream player and play loop: `FUN_0035cf00`, `FUN_0035cc20`,
  `FUN_0035c930`, `FUN_001ce8a0`, `FUN_001ce410`, `FUN_001cdc20`,
  `FUN_001a0890`, `FUN_001a0120`, `FUN_001a00c0`, `FUN_0019ffc0`,
  `FUN_001a0b80`, `FUN_001a2280`, `FUN_001b4c60`, and `FUN_001b4f80`; and
- every resident halfword load of container version `+0xac`, and the NUN3
  parser entry, header parser, dispatcher, terminator, and model-header parser
  for comparison.

`jal` encodings were searched in the resident ELF and all three NA2 overlays
for `FUN_001a0b80`, `FUN_001ce8a0`, and `FUN_0035cf00`. The chunk-1 version of
every extracted `.CCS` file in NA2, NUN3, NUN4, NUN5, and NUN6 was read. Two
decompressed files (`HOME.CCS` and `STR/D01_10.CCS`) and the namespace tables
of NA2 and NUN3 `1NRTBOD1.CCS` were inspected by hand.

The overlay caller audit was sampled deliberately rather than treated as a full
xref census. BTL coverage includes the stage family
`FUN_006c30c0..FUN_006c31d0`, the `spbattle.ccs` ownership pair
`FUN_006e7860`/`FUN_006e7c80`, and the four-resource sync/queue/resolve/unload
family `FUN_00768f50..FUN_00769160`. Its raw stage pointer table, four-resource
pointer table, and associated literal strings were checked. ETC coverage
includes `FUN_006be290`/`FUN_006be6d0` and deferred caller `FUN_006b9c00`;
the relevant literal strings were checked in the raw overlay. Resident C
exports, the corresponding
ASCII instruction listing, and raw BTL/ETC bytes were cross-checked where
control flow or the retained `MWo3` header made the decompiler display
ambiguous.

- **Confirmed coverage:** the pass established five distinct
handle layers; container and record layouts; case-sensitive normalization,
hash, wildcard, and unchecked-ID contracts; exact versus secondary lookup;
type-`0x0A00` traversal; parser framing and publication; bidirectional
cross-container resolution and unload invalidation; borrowed versus owned
readers and caller handles; the load-wrapper, queue, cancellation, and global
pipeline gate; residency states and its registry-only use count; conditional
container teardown; streamed checkpoint constraints; and concrete BTL/ETC
borrowed/owned caller patterns. The overlay section also distinguishes function
body export/live pairs from encoded absolute data pointers, which are already
live. Later work established the exact file framing and the unused length and
marker fields; the version gates and the retail version census; NUN3 framing
and dispatch parity; the foreign-file matching requirements; that the ultimate
jutsu stream player is the only battle user of the play runtime, with its
request, per-request, play-loop, and teardown lifecycle; the frame-stream tag
set and end/loop markers; the roles of container `+0x24` bit 1, `+0x58`,
`+0x5c`, the playback bits of `+0xa6`, and the play bits of `+0xae`; and the
container-owned allocations.

- **Unresolved or untested:** this pass did not exhaust all resident or
overlay xrefs, reconstruct every type-specific runtime object, or prove every
container/manager field and flag. Still open: residency-manager counter
`+0xb18` (read, no writer found); the frame-tag payload layouts and the version
gates inside track parser `FUN_001a6e00`; a byte-for-byte comparison of the
NUN3 and NA2 tag parsers other than the model header, so NUN3-to-NA2
compatibility is not proven for every tag; whether a real NUN3 file loads and
plays in NA2; the resident cost of a container relative to its decompressed
size; the ultimate jutsu table that supplies the request paths; and what player
flags `+0x27c` and bytes `+0x281`/`+0x2da` are set to by the skill-play owner.
- **Deliberate exclusions and overlap:** the full tag/destructor ledger belongs
  to `ccs_object_types.md`; ROFS/GZLIST path routing, ring transport, and general
  gzip/file services belong to `runtime_services.md`; allocator placement,
  load transients, and sampled capacity belong to
  `../../runtime/ee_memory_map/allocator_and_capacity.md`; the ultimate jutsu
  presentation and contest belong to `../../gameplay/ultimate_jutsu.md`.
  Adventure, static file
  inventory, media replacement, localization renderer/layout, widescreen,
  60-FPS, damage, and substitution work were deliberately excluded to avoid
  overlap with other scoped tasks.
- **Evidence limitations:** all conclusions are static. No live-memory trace,
runtime injection, cancellation/concurrency stress test, malformed-CCS fuzzing,
or end-to-end game execution was performed, and no foreign CCS was loaded.
The retail file census reads headers only; block-level walks cannot be
complete because retail length fields are not exact. Raw binary checks validate selected
overlay operands, strings, hashes, and address translation, but not live RAM
state or higher-level caller serialization. Working identities remain semantic
labels, not recovered original symbols.

## Evidence and scope

The result is static-analysis evidence from the maintained Ghidra 12.1.2
exports. Resident `SLPS_258.37` addresses are live EE virtual addresses. BTL
address conversion follows the canonical reference below. The preserved ETC
baseline likewise omits its `0x40`-byte header, so its displayed code and data
are `0x40` below their live locations.

Absolute pointers encoded inside the overlay payload are different: their
stored values already target live addresses and must not receive another
`+0x40`. Ghidra may name a data symbol from such an encoded live pointer even
though the corresponding bytes appear 0x40 earlier in the preserved display.
Every overlay function body below is given as a preserved export/live pair;
numeric data locations explicitly distinguish preserved bytes from live
addresses.

The resident, BTL, and ETC inputs are identified in
[Standard game file identities](file_identities.md). The ETC evidence view is
`@disassembly/NA2/exports/ETC.BIN/`. NUN3 comparisons use the maintained
`SLUS_217.27` analysis through GhidrAssist MCP; NUN3 addresses are its own
resident addresses. Retail CCS files were read from the read-only extractions
and decompressed in memory only.

The C export loses some argument types and occasionally splits a caller into
adjacent functions. The ASCII listing was used to confirm control-flow details
that matter here, especially required-lookup traps and loader state changes.
No runtime trace was performed.

Low-level ROFS routing, GZLIST semantics, ring transport, gzip, and the broader
background-loader implementation are owned by
[Resident file and resource services](runtime_services.md). This document keeps
the transport facts needed to establish CCS publication, cancellation, and
ownership, then follows the resulting container/object runtime.

## Handle layers

“CCS handle” is ambiguous in callers. There are five distinct layers:

| Layer | Representation | Stable meaning |
| --- | --- | --- |
| Residency entry | 0x2c-byte entry managed by `FUN_003b2fe0` | Name, load state, and signed 16-bit use count for a requested CCS. |
| Load wrapper | 0x34-byte object constructed by `FUN_001cf2b0` | Owns file/read/decompression tasks while a container is being produced. |
| Container | 0xc0-byte object constructed by `FUN_001aa640` | One parsed CCS, linked into the resident global list. This is what `FUN_001aa450` returns. |
| Object record | 0x38-byte directory record | Inline object name, namespace/file string, hash/type metadata, and runtime pointers. |
| Runtime object | pointer at record `+0x2c` | Type-specific constructed object returned by `FUN_001a8f00`. |

The record `+0x30` pointer is a separate, type-specific secondary value. It is
returned by `FUN_001a8c80` and collected by `FUN_001a8e10`; it must not be
confused with the ordinary runtime object at `+0x2c`.

## Working function identities and call edges

These names are suitable semantic labels for later Ghidra work. “Callers” are
representative rather than an exhaustive xref dump.

| Exact symbol / address | Working identity | Direct edges and side effects | Confidence |
| --- | --- | --- | --- |
| `FUN_00114f00` / `0x00114F00` | `ccs_match_name_pattern` | Splits a pattern at `*` and calls `FUN_00115060` for each literal/`?` segment. Matching is case-sensitive and must consume the full source unless the pattern ends in `*`. | High |
| `FUN_00115060` / `0x00115060` | `ccs_match_pattern_segment` | Matches one segment, optionally scanning forward after `*`. Its first-position comparison tests the source byte—not the pattern byte—against `?`, producing the documented first-character asymmetry. | High |
| `FUN_00116ae0` / `0x00116AE0` | `ccs_object_vector_clear` | Frees a batch resolver's pointer array, clears its pointer, and resets its count. | High behavior; medium name |
| `FUN_00116bb0` / `0x00116BB0` | `ccs_resolve_object_batch_optional` | Replaces an output vector with one pointer per `{container_spec,object_name}` pair, caches consecutive container specs, supports `#<decimal-index>` indirection through a caller path table, and stores zero for missing containers or objects. | High behavior; medium name |
| `FUN_00116db0` / `0x00116DB0` | `ccs_find_object_optional` | Calls `FUN_001a8f00(container,name,1)` and leaves its return value in `v0`; the C export incorrectly types this thin wrapper as `void`. | High |
| `FUN_001161a0` / `0x001161A0` | `ccs_unwrap_hash_reference_record` | Returns an ordinary record unchanged. For a `#` record, rejects `+0x2c` values below 5 and otherwise returns the record back-pointer at runtime object `+0x00`. Called by `FUN_001a0b80` while building its per-record play-runtime table. | High |
| `FUN_00116210` / `0x00116210` | `ccs_resolve_external_record_chain` | Follows type-`0x0A00` runtime `+0x10` links to a final record; returns zero for a missing/sentinel intermediate. It has no current-runtime guard, visited set, or hop limit. | High |
| `FUN_001163a0` / `0x001163A0` | `ccs_build_name_query` | Copies at most 30 query bytes into a 32-byte matcher object and stores a wildcard-present byte at `+0x1e`. It has no truncation result. | High |
| `FUN_001a09d0` / `0x001A09D0` | `ccs_play_lock_waiter` | Task named `PlayLock`; waits on the primary task pointer at task `+0x28`, yielding while its `+0x40` state is neither 1 nor 2, and exits when that state becomes 2. It does not build the play-runtime table. | High behavior; medium name |
| `FUN_001a0b80` / `0x001A0B80` | `ccs_build_play_runtime_table` | Allocates one 0x10-byte entry per record, unwraps `#` providers through `FUN_001161a0`, materializes type-specific play resources, optionally builds the streamed checkpoint table at `+0x3c`, clears transient record `+0x34` links, sets container `+0xa6` bit 3, and publishes the table at `+0x60`. | High behavior; medium name |
| `FUN_001a2280` / `0x001A2280` | `ccs_destroy_play_state` | Tears down play/model state, frees the checkpoint table at `+0x3c`, and calls `FUN_001a2520` when `+0x60` is nonzero. | High behavior; medium name |
| `FUN_001a2520` / `0x001A2520` | `ccs_destroy_play_runtime_table` | Destroys table-owned type-specific materializations whose entry `+0x0a` bit 0 is set, frees the table, and clears container `+0x60`. | High behavior; medium name |
| `FUN_001a8c80` / `0x001A8C80` | `ccs_find_secondary` | Calls `FUN_001163a0`, `FUN_001a8f70`, and `FUN_00116030`; returns record `+0x30` or the alternate-table value. Called by `FUN_0036fc50` and many resident scene/object setup paths. | High behavior; medium name |
| `FUN_001a8e10` / `0x001A8E10` | `ccs_collect_secondary_matches` | Calls `FUN_001163a0`, `FUN_00116030`, and `FUN_00115720`; appends entries carrying `(pointer,type)` but deduplicates solely by pointer. `FUN_0036fc50` is a direct caller. | High |
| `FUN_001a8f00` / `0x001A8F00` | `ccs_find_object` | Calls `FUN_001163a0` -> `FUN_001a8f70` -> `FUN_001a8fa0`; returns the exact record's `+0x2c`. Its required flag traps only when no record matched. Called through `FUN_00116db0` and directly throughout BTL/ETC. | High |
| `FUN_001a8f70` / `0x001A8F70` | `ccs_find_record_exact_only` | Rejects wildcard queries and otherwise tail-calls the bucket lookup while forcing its resolver argument to zero in a branch-likely delay slot. No mutation. | High |
| `FUN_001a8fa0` / `0x001A8FA0` | `ccs_find_record_hashed` | Calls `FUN_00116a50` and `thunk_FUN_00116a18`; walks record `+0x24` collision links. Its nonzero fourth-argument branch can call `FUN_00116210`, but `FUN_001a8f70` never enables it. | High |
| `FUN_001a9060` / `0x001A9060` | `ccs_parse_container` | Calls header/index/object parsers `FUN_001ac290`, `FUN_001ac6c0`, and `FUN_001ac8a0`. Called by decode worker `FUN_001cf210` and bulk parser worker `FUN_001ce410`. | High |
| `FUN_001a9790` / `0x001A9790` | `ccs_destroy_container` | For a published or canceled container, unlinks/invalidates, calls `FUN_001a9f10`, releases owned resources, and optionally frees the container. An unlisted non-canceled object skips that full body. Directly called by registry release and overlay owners. | High |
| `FUN_001a9ec0` / `0x001A9EC0` | `ccs_container_owns_record_allocation_address` | Half-open byte-range test over `+0x30 .. +0x30 + count*0x38`; it does not require 0x38-byte record alignment. Called by `FUN_001aa3f0` and unload invalidation. | High |
| `FUN_001a9f10` / `0x001A9F10` | `ccs_destroy_record` | Type-tag destructor dispatch; `#` records skip the dispatch but every record has `+0x2c/+0x30` cleared. Called only from `FUN_001a9790` in this family. | High |
| `FUN_001aa3f0` / `0x001AA3F0` | `ccs_find_record_owner` | Scans `puGpffffca98`, calling `FUN_001a9ec0`; returns the owning container. | High |
| `FUN_001aa450` / `0x001AA450` | `ccs_find_container` | Calls `FUN_001aa510` and case-sensitive `FUN_0017c238`; optional lookup with no mutation. Used by `FUN_00116ef0`, the residency manager, BTL, and ETC. | High |
| `FUN_001aa4b0` / `0x001AA4B0` | `ccs_require_container` | Same search as `FUN_001aa450`, but null-store fail-fast on miss. | High |
| `FUN_001aa510` / `0x001AA510` | `ccs_make_container_key` | Removes directories and the final extension into the caller's fixed buffer. | High |
| `FUN_001aa640` / `0x001AA640` | `ccs_construct_container` | Initializes the temporary relation vector at `+0x6c` and then calls `FUN_001aa7c0` to reset the container and bind its reader. | High |
| `FUN_001aa7c0` / `0x001AA7C0` | `ccs_reset_container_and_bind_reader` | Clears parser/runtime fields and work-list heads, installs a caller reader as borrowed, or allocates a 0x40-byte reader and sets ownership bit `+0xae & 2` when passed zero. | High behavior; medium name |
| `FUN_001aab90` / `0x001AAB90` | `ccs_find_runtime_object_container` | Dereferences runtime object `+0x00`, calls `FUN_001aa3f0` on that record, and returns the owning container in `v0`; the C export mis-types this wrapper as `void`. | High |
| `FUN_001ac6c0` / `0x001AC6C0` | `ccs_read_object_directory` | Allocates and fills namespace strings and 0x38-byte records; installs counts/pointers in the container. | High |
| `FUN_001ac8a0` / `0x001AC8A0` | `ccs_parse_typed_blocks` | Dispatches object tags, observes cancellation, finalizes on tag 5, and publishes the container. | High |
| `FUN_001ac610` / `0x001AC610` | `ccs_match_cross_reference_provider` | Selects a provider hash bucket from the consumer's stored hash, then compares namespace text after byte zero and the inline object name. Returns the first matching provider record. | High |
| `FUN_001acdb0` / `0x001ACDB0` | `ccs_finalize_directory` | Computes hashes, builds buckets, calls cross-reference/finalization passes, and consumes temporary reference data. | High |
| `FUN_001acfc0` / `0x001ACFC0` | `ccs_resolve_cross_container_refs` | Calls `FUN_001ac610` against new and existing directories under synchronization; updates sentinel/type fields and unresolved flags. | High |
| `FUN_001ad230` / `0x001AD230` | reserved finalization hook | Called between cross-reference resolution and dependency finalization, but its complete body is only `jr ra; nop` in this build. | High |
| `FUN_001ad240` / `0x001AD240` | `ccs_finalize_dependencies` | Consumes copy/fixup nodes and the temporary relation vector, builds retained index/link state, and reconciles resolvable global dependency nodes. | High behavior; medium name |
| `FUN_001ad8c0` / `0x001AD8C0` | `ccs_record_from_index_unchecked` | Pure `records + index*0x38` conversion used by type parsers. | High |
| `FUN_001ad9c0` / `0x001AD9C0` | `ccs_finalize_secondary_values` | Walks the container's `+0x50` and `+0x4c` lists and installs the resulting values at each source record's `+0x30`. | High behavior; medium name |
| `FUN_001b4c60` / `0x001B4C60` | `ccs_step_streamed_blocks` | Uses the `+0x3c` checkpoint table to seek the reader and asks `FUN_001b4f80` to parse the selected block range. | High behavior; medium name |
| `FUN_001b4f80` / `0x001B4F80` | `ccs_parse_streamed_block_range` | Dispatches streamed object blocks over an inclusive logical range and records checkpoint markers in `+0x3c`. | High behavior; medium name |
| `FUN_001b9980` / `0x001B9980` | `ccs_find_object_required` | Calls `FUN_001a8f00(container,name,0)` and leaves its return value in `v0`; this wrapper is likewise mis-typed as `void` in the C export. | High |
| `FUN_00116de0` / `0x00116DE0` | `ccs_load_if_absent` | Calls existing-container check, constructs `FUN_001cf2b0`, runs `FUN_001cf3f0`, and detaches wrapper `+0x30`. Returns zero—not the existing handle—when already resident. The BTL `FUN_006c30c0` export caller (live `0x006C3100`) is representative. | High |
| `FUN_00116ef0` / `0x00116EF0` | `ccs_find_path_container_precheck` | Derives a backslash-only, 29-byte key by scanning to literal lowercase `.ccs`, then calls `FUN_001aa450`. It never tests source NUL and preserves the lookup return in `v0` despite its `void` export prototype. | High |
| `FUN_001cf060` / `0x001CF060` | `ccs_load_read_worker` | Streams the opened file into the direct decode reader or compressed-input transport and sets wrapper `+0x2c`. | High |
| `FUN_001cf190` / `0x001CF190` | `ccs_load_gzip_worker` | Runs the gzip bridge, destroys/clears wrapper `+0x10/+0x14`, and sets `+0x2d`. | High |
| `FUN_001cf210` / `0x001CF210` | `ccs_load_decode_worker` | Constructs wrapper `+0x30` over reader `+0x0c`, parses unless already canceled, and sets `+0x2e`. | High |
| `FUN_001cf2b0` / `0x001CF2B0` | `ccs_construct_load_wrapper` | Zeros wrapper ownership/state fields and installs default 0x10000-byte transport blocks with four input/output blocks. | High |
| `FUN_001cf300` / `0x001CF300` | `ccs_destroy_load_wrapper_resources` | Destroys nonzero transport/task/buffer fields and optionally frees the wrapper; deliberately does not inspect or destroy produced container `+0x30`. | High |
| `FUN_001cf3f0` / `0x001CF3F0` | `ccs_run_load_pipeline` | Globally serializes the pipeline, starts read/gzip/decode tasks, and blocks until read and decode finish. Temporary-resource retention depends on flag bit `0x100`. | High |
| `FUN_001cf3d0` / `0x001CF3D0` | `ccs_cancel_load` | Sets wrapper cancel and container `+0xb0`; called by state-4 registry cancellation. | High |
| `FUN_001cf9e0` / `0x001CF9E0` | `ccs_enqueue_unique_load` | Appends a 0x48-byte path node containing an embedded load wrapper, or returns zero when the exact path is already queued. The BTL `FUN_006c3190` export caller (live `0x006C31D0`) is representative. | High |
| `FUN_001cfb50` / `0x001CFB50` | `ccs_load_queue_worker` | Walks the queue, skips already-resident paths, runs one blocking `FUN_001cf3f0` pipeline at a time, records node states, and then clears the global worker pointer. | High |
| `FUN_001cfcd0` / `0x001CFCD0` | `ccs_start_load_queue` | Creates the queue worker only when none is active. Its byte argument enables file-size/progress accounting; it does not change container ownership. | High |
| `FUN_001cfd70` / `0x001CFD70` | `ccs_load_queue_worker_active` | Returns whether the global worker-task pointer is nonzero, not whether queued nodes still exist. | High |
| `FUN_001cfd90` / `0x001CFD90` | `ccs_clear_load_queue` | Cleans retained embedded wrappers and frees every queue node. In the only resident-start mode observed it detaches published containers and leaves them resident. | High |
| `FUN_0019ffc0` / `0x0019FFC0` | `ccs_play_restart` | Rewinds a played container to checkpoint 0, restarts `0x0E00` effects, and reinstantiates `+0x58` generator actions. Called by the play loop and by the `-2` frame marker. | High |
| `FUN_001a00c0` / `0x001A00C0` | `ccs_play_request_stop` | Releases the ring manager when bit 7 is set, sets `+0xa4` stop bit `0x10` when a play task exists, clears `+0x40`, and clears `+0xa6` bit 3. | High |
| `FUN_001a0120` / `0x001A0120` | `ccs_play_loop` | Per-step frame advance, action update, callbacks, and scene submission; on stop, tears down through `FUN_001a2280` and sets `+0xa6` bit 5. | High behavior; medium name |
| `FUN_001a0890` / `0x001A0890` | `ccs_play_start` | Creates the play task at `0x001A0980` and its `PlayLock` companion. Only caller: `FUN_001ce410`. | High |
| `FUN_001b5290` / `0x001B5290` | `ccs_parse_terminator` | Reads one dword and stores it minus one at `+0x94`. | High |
| `FUN_001ce410` / `0x001CE410` | `ccs_play_decode_worker` | `PlayDecode` task: parses each streamed request, builds its play runtime, plays it, and destroys containers by retention count. | High behavior; medium name |
| `FUN_001ce8a0` / `0x001CE8A0` | `ccs_stream_player_run` | Preloads `0x1000` requests, runs the three play tasks under gate value 2, then destroys the containers it loaded. | High behavior; medium name |
| `FUN_0035cf00` / `0x0035CF00` | `sp_skill_play_start` | Builds the stream player and request list for an ultimate jutsu and starts task `SP_Skill_Play`. Called from BTL and ETC. | High |
| `FUN_001e80f0` / `0x001E80F0` | `battle_queue_fighter_ccs` | Builds and loads or queues up to nine per-side fighter paths. | High |
| `FUN_001e86c0` / `0x001E86C0` | `battle_adopt_fighter_ccs` | Fills empty per-side handle slots by name lookup. | High |
| `FUN_003b2fe0` / `0x003B2FE0` | `ccs_residency_acquire` | Finds/creates a name entry, increments its use count, and links it into the manager list. | High |
| `FUN_003b3140` / `0x003B3140` | `ccs_residency_release` | Decrements or forces release, cancels/tears down the container, unlinks, and recycles the entry. | High |
| `FUN_003b3420` / `0x003B3420` | `ccs_residency_not_pending` | For a name, returns true when absent or state 3 and false for an existing non-3 entry. Its null-name branch reports manager/worker activity instead. | High |
| `FUN_003b34e0` / `0x003B34E0` | `ccs_residency_ensure_loaded` | Serializes one load, reuses an existing container or runs the load wrapper, and transitions state 4 to 3/5. | High |
| `FUN_003b36d0` / `0x003B36D0` | `ccs_start_batch_load` | Starts `FUN_003b37f0` only when pending entries exist and no batch worker is active. | High |
| `FUN_003b37f0` / `0x003B37F0` | `ccs_batch_load_worker` | Drains state-1 entries, promotes state 2 for a later pass, updates worker counters, and yields through the task API. | High |

## Container and record layouts

### Container fields

These offsets are directly established by construction, parsing, lookup, and
destruction. Unlisted fields remain type-specific or unresolved.

| Offset | Size | Observed role |
| ---: | ---: | --- |
| `+0x00` | 4 | Next container in global singly linked list `puGpffffca98` / `piGpffffca98`. |
| `+0x04` | 0x20 | Inline container name read from the CCS header. `FUN_001aa450` compares its normalized key here. |
| `+0x24` | flags | Bit 0 is initialized as a cross-reference eligibility/unresolved hint. A new container's final value reflects its own unresolved records, but the bit is not reliably cleared on older containers after later resolution. Bit 1 gates the global dependency-group reconciliation pass in `FUN_001ad240`, which revisits every published container's `+0x48` groups. `FUN_001aa7c0` sets it on every container and no resident writer clears it, so the gate is always open in the resident code. |
| `+0x28` | 4 | Hash-bucket array, built by `FUN_001acdb0`. |
| `+0x2c` | 4 | Pointer to the 0x20-byte namespace/file-string table. |
| `+0x30` | 4 | Pointer to the contiguous 0x38-byte object-record array. |
| `+0x34` | 4 | Namespace/file-string count. |
| `+0x38` | 4 | Object-record count and hash-bucket modulus. |
| `+0x3c` | 4 | Optional streamed-block checkpoint table with `+0x98` entries. Built by `FUN_001a0b80`, consumed by `FUN_001b4c60`/`FUN_001b4f80`, and freed by `FUN_001a2280`. |
| `+0x40` | 4 | Play task created by `FUN_001a0890`; cleared by a stop request (`FUN_001a00c0`). |
| `+0x44` | 4 | Head of temporary copy/fixup nodes. `FUN_001ad240` consumes and frees every node, clears each source record's `+0x2c`, and then clears this head. |
| `+0x48` | 4 | Head of retained dependency/group nodes. `FUN_001ad240` allocates each node's `+0x10` index map and participates in later global link reconciliation; record teardown removes and frees the nodes. |
| `+0x4c` | 4 | Head of retained nodes whose source-record secondary value is built by `FUN_001ad9c0` through `FUN_0019b240`. |
| `+0x50` | 4 | Head of retained nodes whose source-record secondary value is built by `FUN_001ad9c0` as an allocated 0x1c-byte object through `FUN_001ada60`. |
| `+0x54` | 4 | Head of retained reference/link nodes scanned by `FUN_001ad240`; when a target record is resolved, its runtime object's `+0x04` receives the node's source record. |
| `+0x58` | 4 | Container-level `0x0D80` generator-action packets: `FUN_001b1920` links a packet here when its animation record ID is zero. Playback reads the list: `FUN_001a0b80` and the restart routine `FUN_0019ffc0` pass it to `FUN_001abbe0`, which instantiates one action runner per packet in the play context's `+0x114` manager. The source records still own and free the nodes. |
| `+0x5c` | 4 | Ordered-controller table built by the `0x1700` parser `FUN_001b2220` (a second table in one container traps). Its `+0x0c` default lightweight slot and `+0x08` default extended descriptor are materialized by `FUN_001a0b80`; `FUN_001b2110(handle,1)` frees both and the table. |
| `+0x60` | 4 | Per-record play-runtime table built by `FUN_001a0b80`. `FUN_001a8c80`/`FUN_001a8e10` select it when `+0xa6` bit 3 is set. Entries are 0x10 bytes; `FUN_001a2520` destroys and clears it. |
| `+0x68` | 4 | Input reader/stream object. It may be borrowed or container-owned. |
| `+0x6c` | 0x0c | Vector of owned temporary relation-block pointers. `FUN_001ad240` converts them into runtime-object `+0x18` structures, frees every block, and clears the vector. Generic destruction also frees any blocks left by an interrupted parse. |
| `+0x78` | 4 | Play context allocated (0x120 bytes) by `FUN_001a0b80` and freed by `FUN_001a2280`. |
| `+0x90` | 4 | Current frame index during playback. |
| `+0x94` | 4 | Type-5 payload dword minus one, written by `FUN_001b5290`: the last frame index of a playback file. |
| `+0x98` | 4 | Header dword written by `FUN_001ac290`, used as the streamed-checkpoint count. In the playback file `STR/D01_10.CCS` it equals the tag-5 payload (`0x13F`), one more than the last frame marker index. It is cleared after parsing when `+0x94` is zero. |
| `+0x9c` / `+0x9e` | 2 each | Signed 8.8 playback rate (`0x100` is one frame per step) and its fractional accumulator. |
| `+0xa4` | 2 | Playback control flags (seek, restart, and stop requests consumed by the play loop and `FUN_001b4c60`). |
| `+0xa0` | 4 | Type-5 block-start reader position, retained for reader states 1 or 2. |
| `+0xa6` | 2 | Runtime flags. Bits 0/1 are parse milestones and bit 3 selects the alternate `+0x60` table. During playback, bits 2 and 4 are set together when the frame stream reaches an end marker, and bit 5 is set after the play loop has torn its play state down. Bit 7 marks a container holding a `0x2200` ring batch. |
| `+0xaa` | 2 | Parser state: 1 while object blocks are being consumed, 2 after the type-5 terminator is finalized. |
| `+0xac` | 2 | Format/header value. It begins at `0x80`, is replaced by a stream value, and must be at least `0x90`. |
| `+0xae` | 2 | Ownership flags. Bit 1 means the container allocated and owns the reader at `+0x68`. Bits 0, 2, and 3 are set by `FUN_001a0b80` when the play context owns its scene environment (`+0x110`), default controller (`+0xf4`), and default extended controller (`+0xf8`); `FUN_001a2280` destroys those and clears the three bits. |
| `+0xb0` | 1 | Cancellation byte. A nonzero value stops object parsing and prevents global-list insertion. |

`FUN_001aa7c0` allocates a 0x40-byte reader through `FUN_001aa940` only when
the caller supplies no reader. It then sets `+0xae` bit 1. Destruction closes
and frees `+0x68` only under that bit, so a caller-supplied reader is borrowed.

Borrowed does not imply that the pointer remains live for the container's full
residency. `LoadDecode` supplies wrapper reader `+0x0c`, so the published
container does not set its ownership bit. On an ordinary flag-0 load,
`FUN_001cf3f0` destroys that reader after parsing and clears only wrapper
`+0x0c`; container `+0x68` is left unchanged and is then stale. Retained
whole-buffer/play-stream owners keep the wrapper alive until their later seek
work and destroy the container before wrapper cleanup. Generic users must not
treat borrowed `+0x68` on an ordinary resident container as a persistent reader
handle.

### Finalization work-list ownership

The directory finalizer runs `FUN_001acfc0`, the no-op `FUN_001ad230`,
`FUN_001ad240`, and `FUN_001ad9c0` in that order. The five linked-list heads at
`+0x44..+0x54` are initialized to zero by `FUN_001aa7c0`; they are ownership
indexes as well as finalization inputs, because surviving nodes remain linked
until their source record's type-specific destructor unlinks them.

The `+0x44` case is the exception: each node names a source record at `+0x00`,
a target record at `+0x08`, and carries 0x30 bytes at `+0x10`. If the target
runtime is neither zero nor sentinel `4`, `FUN_001ad240` copies those 0x30 bytes
to target-runtime `+0x10`. Whether or not the target resolved, it then clears
the source record's runtime pointer, unlinks/frees the node through
`FUN_001a9730`, and finally zeros container `+0x44`. Thus these objects are
parse-time directives, not retained runtime handles.

Temporary relation blocks enter the `+0x6c` vector through `FUN_001b4b40` at
`0x001B4B40`. During `FUN_001ad240`, the block's first record index selects a
runtime object. A successful target receives an allocated 0x0c-byte structure
at runtime `+0x18`, plus filtered 0x10- and 0x1c-byte relation arrays whose
record indexes passed `FUN_0019dc90`. Every input block is freed even when the
target runtime is absent, and the vector is empty on return. The numeric object
tag identities and payload schemas remain owned by `ccs_object_types.md`; the
facts here are only the shared container-lifecycle behavior.

`FUN_001b1920` at `0x001B1920` divides the `0x0D80` generator-action packets by
their animation record ID. A nonzero ID becomes a record pointer and puts the
packet on global pending list `iGpffffcaa4`, from which `FUN_001ad240` moves it
into the resolved animation runtime's `+0x04` chain. ID zero instead links the
packet on container `+0x58` through packet `+0x04`. Finalization does not touch
that list (`FUN_001ad230` is a true no-op); it is read only by playback.
`FUN_001a0b80` and the restart routine `FUN_0019ffc0` hand it to
`FUN_001abbe0`, which allocates one 0x10-byte runner per packet through
`FUN_001ab0b0` in the play context's `+0x114` action manager. These are
generator actions that belong to the whole playback file rather than to one
animation. Record destruction still frees each packet through `FUN_001a93d0`,
which searches the global list and then frees even on a miss, so `+0x58` can
become stale during teardown; nothing reads it after playback has ended.

### Object record fields

`FUN_001ac6c0` allocates `record_count * 0x38`, reads each directory row, and
then reserves record zero by clearing its name and runtime pointer. Type-specific
object destruction begins at record index 1.

That reservation is not enforced. Typed-block parsers convert their numeric IDs
through unchecked `FUN_001ad8c0`, so malformed input can target index 0 and
repopulate its type/runtime fields after the directory clear. Generic teardown
still starts at index 1, leaving such an index-0 runtime out of type-specific
destruction. Well-formed CCS data must keep record zero unconstructed.

The directory parser trusts several fixed-width format invariants. It reads the
0x20-byte container name, each 0x20-byte namespace row, and each 0x1e-byte
object name without forcing a terminator when all bytes in the field are
nonzero. Hashing and comparison later scan for NUL, so valid files must provide
one within each fixed-width name. Each record also contains an unchecked
16-bit namespace index: `FUN_001ac6c0` stores
`namespace_table + index * 0x20` directly at record `+0x20`, without comparing
the index to container `+0x34`. Record count zero is not rejected, even though
the parser unconditionally clears record zero and later lookup uses the count as
the hash-bucket modulus. These are input contracts rather than validations.

| Offset | Size | Observed role |
| ---: | ---: | --- |
| `+0x00` | 0x1e | Inline object name. Lookup normalizes queries into the same 30-byte width. |
| `+0x20` | 4 | Pointer into the container's 0x20-byte namespace/file-string table. A first character `#` marks a cross-container record. |
| `+0x24` | 4 | Next record in the same hash bucket. |
| `+0x28` | 2 | 16-bit object-name hash. |
| `+0x2a` | 2 | Runtime type tag. |
| `+0x2c` | 4 | Constructed runtime object, zero when absent, or sentinel `4` while unresolved. |
| `+0x30` | 4 | Secondary/type-specific value returned by the secondary lookup family. |
| `+0x34` | 4 | Transient back-pointer to the corresponding 0x10-byte play-runtime entry while `FUN_001a0b80` builds type-specific state. The builder clears these links before publishing the table. Other type-specific uses are not ruled out. |

Internal references use numeric record indexes. `FUN_001ad8c0` at
`0x001AD8C0` performs the unchecked conversion
`container->records + index * 0x38`. `FUN_001a9ec0` at `0x001A9EC0` tests
whether an address lies anywhere in that record-array byte interval; it does
not prove that the address is aligned to a record boundary. `FUN_001aa3f0` at
`0x001AA3F0` scans the global container list and therefore identifies the
owning record allocation, not necessarily a valid record. These form the
proven ID/address lookup family; there is no bounds check in `FUN_001ad8c0`
itself.

### Common runtime-object back-pointer

Runtime objects participating in the directory/reference system expose their
provider record pointer at object `+0x00`. This is not merely a convention
inferred from one parser:

- `FUN_001161a0` unwraps a resolved `#` record by returning
  `*(record->+0x2c + 0x00)`;
- `FUN_001a9790` uses the same first word to decide whether a foreign resolved
  reference points into the departing container's record array; and
- the type-`0x0A00` constructor explicitly writes its own record there.

Given an ordinary `FUN_001a8f00` result, the reusable ownership traversal is
therefore `runtime_object -> *(+0x00) record -> FUN_001aa3f0(record)
container`. This invariant does not extend to the type-specific secondary
pointer at record `+0x30`. `FUN_001aab90` at `0x001AAB90` implements this exact
runtime-object-to-container traversal as a convenience wrapper and preserves
the container return value in `v0` despite its `void` C-export prototype.

## Container-name lookup

`FUN_001aa510` at `0x001AA510` derives the lookup key from a path:

- both `/` and `\` reset the basename start;
- the final extension is removed only when its dot occurs strictly after the
  basename's first byte, so a leading-dot basename is preserved;
- the resulting bytes are copied without case folding.

`FUN_001aa450` at `0x001AA450` then walks the global list and compares the key
against container `+0x04` using `FUN_0017c238`, a case-sensitive `strcmp`.
It returns the container or zero. `FUN_001aa4b0` at `0x001AA4B0` is the same
search with a deliberate null-store fail-fast on miss. The two entry points are
therefore optional and required container lookup, respectively.

Publication prepends a container to this list. Duplicate normalized names are
not rejected at insertion, so both lookup functions return the most recently
published matching container. Destruction removes the exact container pointer,
not every same-name entry.

The normalizer does not visibly bound its copy to the 32-byte destination.
The safe normalized basename is therefore at most 31 bytes plus NUL. All
observed format and caller names respect that fixed-width contract, but the
function itself supplies no defensive length check.

## Object-name lookup

### Exact hash path

`FUN_001a8f00` at `0x001A8F00` is the ordinary object lookup:

1. `FUN_001163a0` copies at most 30 query bytes and records whether `*` or `?`
   occurred.
2. `FUN_001a8f70` rejects wildcard-bearing queries on this direct path.
3. `FUN_001a8fa0` hashes the name, selects `hash % record_count`, compares the
   stored 16-bit hash, then performs a case-sensitive full-name comparison.
4. `FUN_001a8f70` forces the hash helper's resolver argument to zero. Ordinary
   direct lookup therefore returns the matched record's own `+0x2c`; it does
   not pass type `0x0A00` through `FUN_00116210`.

The query adapter has no length/error result. It examines and copies at most 30
bytes, zero-fills only when it encounters NUL sooner, and stores its wildcard
flag at byte 30. Wildcards after byte 29 are silently ignored. If the first 30
bytes contain a wildcard but no NUL, byte 30 is nonzero and the wildcard
matcher can scan beyond the 32-byte stack query looking for a terminator. The
safe caller contract, like the valid directory-name contract, is therefore at
most 29 bytes plus NUL.

For a non-wildcard linear match, `FUN_00116120` compares the complete 30-byte
name field, whereas the query adapter zero-fills every byte after its first NUL.
The hash path's string comparison stops at NUL. Consequently, an on-disk object
name with an early NUL but nonzero trailing padding can match exact hash lookup
yet fail the linear/collector family. Consistent CCS names must be both
NUL-terminated and zero-padded through the end of the 0x1e-byte field.

The 16-bit hash in `FUN_00116a50` at `0x00116A50` is:

```text
hash = 0
step = 0
for each signed input byte c until NUL:
    hash ^= step + (c << ((c & 7) + 2))
    step += 0x40f9
return hash & 0xffff
```

`FUN_001acdb0` builds exactly `record_count` buckets. It encodes each row as
`(hash << 16) | record_index`, sorts those unsigned values ascending, then
constructs the chains so equal-hash rows are visited in ascending record-index
order. Duplicate inline object names therefore resolve to the lowest matching
record index; there is no duplicate-name rejection.

The packed directory entry retains only the low 16 bits of `record_index` when
the finalizer later extracts it. A count of 65,536 still fits indexes
`0..65,535`; any larger count wraps subsequent indexes and their addition also
changes the packed high hash half before sorting. No explicit count guard is
present, so `record_count <= 65,536` is a format contract rather than parser
validation.

Reserved record 0 participates in this hash construction even though its name
and runtime pointer were cleared by the directory parser. Consequently, an
empty-string query matches record 0 and returns its zero `+0x2c` without taking
the required lookup's record-miss trap. This is a concrete instance of the
matched-record/null-runtime distinction below.

The third argument to `FUN_001a8f00` controls record-name miss behavior, not
type: zero means required and triggers the null-store fail-fast when no record
matched; nonzero means optional and returns zero on that miss. A matched record
is not validated afterward. Its `+0x2c` may therefore return zero, or sentinel
`4` for an unresolved non-`0x0A00` cross-container record, even on the required
path. The lookup also performs no generic expected-type check. Callers rely on
load order, naming, and their own downstream object expectations.

### Thin and batch wrappers

The resident binary has explicit convenience wrappers despite their misleading
decompiler prototypes. `FUN_00116db0` at `0x00116DB0` passes required flag 1
and is optional; `FUN_001b9980` at `0x001B9980` passes flag 0 and is required.
Both return `FUN_001a8f00`'s `v0` unchanged across their epilogues.

`FUN_00116bb0` at `0x00116BB0` resolves a batch into an output object laid out
as `{pointer_array,count}`. Each 8-byte input row is
`{container_spec,object_name}`. It reuses the preceding container handle when
consecutive rows share the exact same spec pointer. A spec beginning with `#`
is parsed as a decimal index by `FUN_001771d0`; the indexed string from the
caller's fourth-argument table is then passed to `FUN_001aa450`. Other specs
are passed directly. Container and object misses both produce a zero slot, and
`FUN_00116ae0` frees and clears the result vector.

The batch helper's fifth-argument bit 0 does **not** make object resolution
required for normal nonnegative counts. The output count is incremented once
per input row regardless of whether its slot is zero, so its final
`count != requested_count` trap cannot detect a missing container or object.
The `#` table index and result getter `FUN_00116b30` are also unchecked in this
layer. The only direct resident batch caller, `FUN_0030c360`, supplies seven
direct container specs and does not exercise `#` indirection.

### Wildcards and secondary values

`FUN_001a8c80` at `0x001A8C80` searches for the secondary `+0x30` value. It
tries the hash path first without resolving the record, then linearly scans the
record array using `FUN_00116030` when necessary. Wildcard-bearing queries
therefore use this path even though `FUN_001a8f00` rejects them. `*` matches an
arbitrary span. `?` has a static implementation asymmetry in `FUN_00115060`:
at the first byte of the string or of any segment after `*`, the helper tests
the source byte against `?`, so a query `?` behaves literally there; at later
segment positions it is a one-byte wildcard. Matching remains case-sensitive.
Only the fallback linear scan skips records whose `+0x20` namespace begins
with `#`; an exact hash hit has no marker test. The same zero/nonzero
required/optional argument convention applies.

The fallback starts at record index 0. Pattern `*` matches that record's
directory-cleared empty name, so `FUN_001a8c80("*")` normally returns its zero
secondary value before reaching a real object. `FUN_001a8e10("*")` can likewise
append an initial pointer/type entry `(0,0)`. This is another matched-record/null-
value case; the required flag does not reject it.

When container `+0xa6` bit 3 is clear, this routine returns record `+0x30`.
When the bit is set, it returns the corresponding first word of the 0x10-byte
entry in container `+0x60` instead. `FUN_001a8e10` at `0x001A8E10` performs
the same pattern scan across all records and appends entries carrying
`(pointer,type)` to the caller's growable array through `FUN_00115720`.
Uniqueness is tested on the pointer only, not on the full pair.

The alternate table is not parser-owned directory data. `FUN_001a0b80` at
`0x001A0B80` allocates `record_count * 0x10` and initializes each row as:

| Entry offset | Size | Initial/proven role |
| ---: | ---: | --- |
| `+0x00` | 4 | Provider record `+0x30`, later replaceable by a type-specific play resource. This is the value returned by secondary lookup while container bit 3 is set. |
| `+0x04` | 4 | Provider record pointer after `FUN_001161a0` unwraps a `#` record; zero when unresolved. |
| `+0x08` | 2 | Provider record type. `FUN_001a8e10` reports this type with the row's `+0x00` pointer. |
| `+0x0a` | 1 | Ownership/state flags; bit 0 marks type-specific materializations that `FUN_001a2520` must destroy. |
| `+0x0c` | 4 | Initialized to zero; later role is type-specific and unresolved. |

During construction, the provider record's `+0x34` temporarily points back to
its table row. The builder clears those transient links, clears container
`+0xa6` bit 5, sets bit 3, then stores the table at `+0x60`. The stop request
`FUN_001a00c0` clears bit 3 (switching secondary lookup back to record `+0x30`)
and asks the play loop to stop; it does not free the table. Full play-state teardown reaches `FUN_001a2520` through
`FUN_001a2280`, destroys owned rows by recorded type, frees the allocation, and
zeros `+0x60`.

Publication sets bit 3 one store before it writes `+0x60`, with no local lock;
a concurrent secondary lookup in that transient window would select a null
alternate table. Teardown uses the safe reverse order: `FUN_001a2280` clears
bit 3 before calling the table destructor. The setup path therefore relies on
caller serialization until `FUN_001a0b80` returns.

`FUN_001a0890` separately creates the task named `PlayLock` at
`FUN_001a09d0`. That task only waits for the primary play task's `+0x40` state
to reach 2; the static evidence does not show it constructing or owning the
alternate table. On the normal path, the primary task runs
`FUN_001a2280` before publishing that terminal state, so `PlayLock` does not
finish ahead of table teardown.

The same `FUN_001a0b80` pass conditionally builds streamed-reader seek state.
When reader byte `+0x30` is 1 or 2, it allocates `container->+0x98 * 4` bytes at
container `+0x3c`, zeroes the table, and seeds entry zero with the saved reader
position at `+0xa0`. While `FUN_001b4f80` parses streamed blocks, marker
`0xFF01` supplies an index and records the current reader position in that row
when the index is in range. `FUN_001b4c60` later searches these nonzero rows,
seeks through `FUN_001cb2e0`, and resumes block dispatch. `FUN_001a2280` frees
and clears `+0x3c` before tearing down `+0x60`; the generic container destructor
does not own either play-state allocation.

The allocation path rounds even a zero-byte request up to its allocator's
minimum block and the builder unconditionally writes row zero, so `+0x98 == 0`
does not by itself leave `+0x3c` null. That does not make a zero count a valid
streaming contract: marker stores are guarded by `marker_index < +0x98`, but
`FUN_001b4c60` indexes `+0x3c[target]` without comparing `target` with `+0x98`.
Its forward target is capped by `+0x94`, not by the checkpoint count. Safe
streamed data therefore has to keep every playback target, including the
inclusive `+0x94` endpoint, inside the `+0x98` table.

The `0xFF01` payload also replaces `FUN_001b4f80`'s logical range cursor;
ordinary dispatched blocks do not increment that cursor. No check requires
successive marker indexes to increase, so well-formed streamed data must provide
the progression that eventually leaves the requested inclusive range. On a
backward seek, `FUN_001b4c60` scans checkpoint rows downward until it finds a
nonzero position without an explicit lower-bound test. It relies on row zero,
seeded from `+0xa0`, being a nonzero fallback.

### Type-`0x0A00` traversal

`FUN_00116030`, used by the linear/pattern family rather than ordinary direct
hash lookup, normally calls `FUN_00116210` before comparing names.
`FUN_00116210` repeatedly follows records whose type at `+0x2a` is `0x0A00`.
For each hop it reads the current runtime object from record `+0x2c`, reads an
owner/link record from runtime object `+0x10`, reads that record's runtime
object from `+0x2c`, then takes that runtime object's `+0x00` record
back-pointer as the next record. The exact decompiler expression for the
intermediate runtime pointer is
`*(int **)(*(int *)(*(int *)(record+0x2c)+0x10)+0x2c)`; the next record is one
further dereference. A zero or sentinel-4 intermediate pointer makes resolution
fail. If the query
begins with the in-memory word `0x5f545845` (`"EXT_"`), `FUN_00116030`
instead requires the original record to be type `0x0A00` and does not unwrap
it. This is a proven distinction between looking up an external-record object
itself and looking through it.

This traversal assumes a valid acyclic graph. Once the current record is type
`0x0A00`, `FUN_00116210` dereferences that record's own `+0x2c` and then
runtime `+0x10` without first rejecting current runtime zero or sentinel `4`.
Only the later intermediate runtime is checked for those two values. The loop
also has no visited set or hop limit, so a cycle of type-`0x0A00` links does not
terminate. The parser/load graph, not this helper, must enforce both invariants.

The type parser `FUN_001b2800` at `0x001B2800` makes this identity explicit. It
allocates a 0x20-byte runtime object, writes `"EXT"` into the record name,
stores the record back-pointer at runtime `+0x00`, and stores two directory
record links at runtime `+0x04` and `+0x10`. If it replaces a type-`0x2000`
placeholder, it preserves four additional words in runtime `+0x08`, `+0x14`,
`+0x18`, and `+0x1c` before freeing the placeholder.

The rewrite touches exactly name bytes 0, 1, and 2; it does not write byte 3.
The `"EXT_"` bypass recognized by `FUN_00116030` therefore depends on the
original directory name already containing `_` at byte 3. Without that input
convention, the constructed name does not enter the special no-unwrapping path.

The `#` namespace marker and type `0x0A00` are related reference mechanisms but
are not the same test: `#` is read from record `+0x20`; `0x0A00` is the type tag
at `+0x2a`.

## Parsing, type dispatch, and publication

`FUN_001a9060` at `0x001A9060` is the synchronous container parser used by the
decode worker. It reads the decompressed stream strictly in order:

| Part | What `FUN_001a9060` and its helpers read |
| --- | --- |
| Chunk 1 | A dword whose low halfword must be `1` (a first dword equal to `CCSF` traps), a discarded length dword, the discarded `CCSF` dword, then `FUN_001ac290`: 0x20-byte container name, version halfword `+0xac`, one discarded halfword, dword `+0x98`, an extension count, and that many discarded dwords. |
| Chunk 2 | Low halfword `2`, discarded halfword and length, then `FUN_001ac6c0`: namespace count, record count, 0x20-byte namespace rows, and one 0x20-byte row per record (0x1e-byte name plus 16-bit namespace index). |
| Chunk 3 | Low halfword `3`, discarded halfword and length. |
| Object blocks | `FUN_001ac8a0`: repeated 8-byte headers (16-bit tag, discarded halfword, discarded length dword) and tag-specific payloads until tag 5. |
| Tag 5 | `FUN_001b5290` reads one payload dword `n` and stores `n - 1` at `+0x94`; the directory is then finalized and published. |
| Frame stream | Present only in playback files; read later by `FUN_001b4f80`, see [Streamed playback](#streamed-playback-sp-skill-play). |

`CCSF` is observed payload, not a signature validated by this routine. The
version check `version >= 0x90` is the only header value test; the extension
words are consumed but not retained.

Neither the parser nor the dispatcher uses a block's length dword or its high
marker halfword. Each tag parser must consume exactly its own payload, because
the next header is read from wherever that parser stopped. There is no
skip-by-length path, so an unknown tag, or a known tag whose payload layout
differs from what the NA2 parser expects, cannot be stepped over.

**Retail-file observation.** Retail NA2 files do not keep the unused fields
exact. In the decompressed `HOME.CCS`, the `0x0800` block at offset `0x2383C`
declares `0x386` payload dwords, but the next block header starts four bytes
before the offset that length implies. Walks that follow declared lengths
across the NA2 CCS files lose synchronization after some `0x0300` and `0x0800`
blocks. Chunk-3 and tag-5 headers often carry high halfword `0x0000` instead of
`0xCCCC`. All 2,310 retail NA2 files have one extension dword, which gives a
chunk-1 length of `0x0D` dwords.

`FUN_001ac8a0` at `0x001AC8A0` dispatches the typed blocks. The complete
tag-to-parser/destructor ledger and the separately proven object identities are
owned by [Resident CCS object-type identities](ccs_object_types.md); they are
not duplicated here. An unrecognized tag takes the same deliberate null-store
failure path used by required lookups. This runtime pass relies only on the
special traversal behavior proved for type `0x0A00` above.

After the dispatcher returns, `FUN_001a9060` clears `+0x98` when `+0x94` is
zero, so a file whose tag-5 payload is `1` keeps no checkpoint count.

At the terminator, `FUN_001acdb0` at `0x001ACDB0` computes every record hash,
sorts temporary `(hash,index)` values, builds collision chains, installs the
bucket array at container `+0x28`, resolves dependencies, and marks parser
state 2. The container is inserted at the head of the global list only if its
cancel byte `+0xb0` remains zero. Publication and cross-container resolution
are surrounded by `FUN_00167da0` / `FUN_00167df0` synchronization calls.

## Cross-container references

`FUN_001acfc0` at `0x001ACFC0` resolves records whose namespace/file string at
`+0x20` begins with `#` and whose runtime pointer is sentinel `4`.
`FUN_001ac610` matches a candidate by both:

- the namespace strings with their first marker character skipped; and
- the inline object name.

On a match, resolution copies only the provider record's type `+0x2a` and
runtime pointer `+0x2c`. It does not copy provider `+0x30`. A resolved `#`
record is therefore transparent to ordinary `FUN_001a8f00` object access but
not to the secondary family: the exact `FUN_001a8c80` path can match the `#`
record yet returns that record's own usually-zero `+0x30`, while its fallback
scan and `FUN_001a8e10` skip `#` rows. The play-runtime builder is a separate
case: `FUN_001a0b80` explicitly unwraps the provider record and snapshots its
secondary value into table `+0x60`.

`FUN_001ac610` validates only the hash, namespace text after byte zero, and
inline object name. It does not require the candidate to be a direct
non-`#` provider, nor does it reject provider runtime zero or sentinel `4`.
The caller treats any name match as success and copies that value; it does not
set its unresolved hint merely because the copied pointer remains `4`. A zero
provider runtime likewise turns the consumer from sentinel `4` into zero and
removes it from later resolution attempts. Cross-reference chaining and
provider readiness are therefore load-format/order contracts, not validated
features of this resolver.

Duplicate providers are resolved by traversal order rather than rejected.
Inside one provider directory, `FUN_001ac610` walks the same collision chain as
ordinary hash lookup, so the lowest matching record index wins. When a new
container's record searches already-published providers, `FUN_001acfc0` walks
the global list from its head and stops at the first match; on the normal
prepend-publication path, that is the most recently published matching older
container. Load order can therefore select among otherwise identical provider
records or containers.

Before matching, the new-container pass overwrites the first byte of each
non-sentinel record's namespace string with ASCII space. Resolution then runs
in both directions: older containers whose bit 0 makes them eligible are tested
against the new directory, and the new container's unresolved records are
tested against every older container. The new container's bit 0 reflects its
own remaining unresolved records. Resolution into an older container does not
reliably clear that older container's bit, so it is a sticky hint rather than
an exact current unresolved-status bit.

Record `+0x20` is a shared pointer into the namespace table, not a private
string copy. The first-byte rewrite is consequently a namespace-row mutation:
every record carrying the same 16-bit namespace index observes it. No check
prevents one shared row from being referenced by records with different current
resolution states. Correct input must keep those uses compatible; the finalizer
does not preserve independent marker bytes per record.

`FUN_001a9790` performs the inverse operation on unload. It scans every
remaining container's `#` records; when the referenced object's back-pointer
falls inside the departing container's record array, the surviving record is
reset to runtime sentinel `4`, its type is cleared to zero, and unresolved
state is propagated. This prevents a cross-container record from retaining a
live-looking pointer into freed record storage.

## Format versions and foreign CCS files

### Version gates in the NA2 parsers

Container `+0xac` holds the chunk-1 version halfword. Besides the header check,
these resident parsers read it and change what they consume or how they
interpret it. Thresholds are the first version that takes the newer path.

| Parser | File tag | Version thresholds |
| --- | --- | --- |
| `FUN_001ac290` | chunk 1 | `0x90` required; lower traps |
| `FUN_001b2670` | `0x0100` | `0x96`, `0x122` |
| `FUN_001b3450` | `0x0200` | `0x120` |
| `FUN_001b3c70` | `0x0300` | `0x90`, `0x92` |
| `FUN_001b3810` | `0x0400` | `0x90`, `0x92` |
| `FUN_001a29d0` | `0x0700` | passes the version to track parser `FUN_001a6e00`; its internal gates were not enumerated |
| `FUN_001b0c40` | `0x0800` | `0x100`, `0x111`, `0x121`, `0x122`, `0x123` |
| `FUN_001b1560` | `0x0900` | `0x110` |
| `FUN_001b1b30` | `0x0D90` | `0x123` |
| `FUN_001b2e50` | `0x0E00` | `0x122` |
| `FUN_001b5400` | frame tag `0x0201` | `0x120` |
| `FUN_001b6e40` | frame tag `0x1A01` | `0x111` |

The list comes from every resident halfword load of container `+0xac` plus the
comparisons that reuse the loaded value in `FUN_001b0c40`. The per-type meaning
of each gated field belongs to
[Resident CCS object-type identities](ccs_object_types.md).

**Inference:** NA2 accepts every version from `0x90` through at least `0x123`
and reads older layouts on purpose. No gate above `0x123` exists, so a newer
version would be parsed with the `0x123` layout.

### Versions in the retail files

Chunk-1 versions of every `.CCS` file in each extracted retail disc:

| Game | Files | Versions |
| --- | ---: | --- |
| NA2 | 2,310 | `0x123` except `STR/ATTENTION.CCS` (`0x120`) |
| NUN3 | 2,400 | 2,348 `0x123`; 41 `0x111` (card images and `XLANGUAGE.CCS`); 10 `0x120` (`1CMNBOD1.CCS`, eight `RPGF/FRPG*.CCS`, `STR/ATTENTION.CCS`); 1 `0x122` (`RPGF/FRPGPKN.CCS`) |
| NUN4 | 4,031 | 4,029 `0x123`, 2 `0x120` |
| NUN5 | 3,552 | 3,551 `0x123`, 1 `0x120` |
| NUN6 | 1,320 | 1,310 `0x123`; 9 `0x111` (the `DTU`, `FOR`, and `HNX` `3EYE`/`BOD1` files); 1 `0x120` |

Every file in all five games falls inside the range NA2 accepts.

### NUN3's parser compared with NA2's

The NUN3 resident parser `FUN_0015F680` (SLUS_217.27) reads the same chunk-1,
chunk-2, and chunk-3 framing, with the same `CCSF` trap, `version >= 0x90`
check, and ignored length and marker fields. Its block dispatcher `FUN_00162CA0`
has exactly the same 34 object/control routes and terminator `5` as NA2's
`FUN_001ac8a0`, and traps on any other tag. Its terminator handler
`FUN_0016AAF0` reads one dword and stores it minus one, as NA2's does. NUN3's
container is a different, larger structure (version at `+0x20c`), so only the
file format is shared, not the runtime layout.

NUN3's parsers test the version at the same thresholds as the NA2 table above
(`0x90`/`0x92` for textures and palettes, `0x96`/`0x122` for objects, `0x120`
for materials, `0x110` for compositions, `0x123` for generators, `0x122` for
effects, and `0x100`/`0x111`/`0x121`/`0x122` for models). For the `0x0800`
model header, both games read the same fields under the same gates; NA2
additionally decodes more of the flag bits it reads (for example a 2-bit field
from the second extra byte at version `0x123`), which changes interpretation,
not the number of bytes consumed.

**Inference (medium confidence):** a NUN3 CCS is readable by the NA2 parser at
the framing and dispatch level. This comparison covered the dispatchers, the
header parser, the terminator, and the model-header parser; the other tag
parsers and every sub-parser were compared only by their version gates, not
byte for byte. The retail-length inaccuracy above means a length-walking tool
cannot prove byte compatibility either; only a parser that consumes each
payload the way NA2 does can.

### What a foreign file must match

These requirements follow from the runtime behavior documented elsewhere in
this file:

- **Load path.** The file must be listed in `GZLIST.TXT` with its decompressed
  size, or the resident file directory rejects it; see
  [Resident file directory](../../runtime/ee_memory_map/allocator_and_capacity.md#resident-file-directory).
- **Container name.** Lookup compares the path's extensionless basename with
  the 0x20-byte name inside chunk 1, not with the file name on disc. A file
  loaded under one path but carrying another header name is published under the
  header name, and later path-based lookups miss it.
- **Cross-container references.** A `#` record resolves only when a published
  container holds a record with the same object name and a namespace string
  that matches after the first byte. Retail files write the source path there,
  for example ` c\1nrt\max\1nrtbod1.max` in `PL/1NRTBOD1.CCS`. NA2's ultimate
  jutsu stream `STR/D01_10.CCS` refers to `#c\1nrt\max\1nrtbod1.max`,
  `#c\2nrt\max\2nrtbod1.max`, and `#c\1cmn\max\1cmnbod1.max`. NUN3's
  `1NRTBOD1.CCS` carries the same body namespace strings as NA2's, plus an extra
  ` x\name\nrt\name.bmp` row.
- **Object names.** Game code finds objects by exact, case-sensitive record name
  (`FUN_001a8f00`), with no type check. A replacement must keep every name the
  consuming code or stream asks for, with a type that consumer can use.
- **Memory.** Every parsed object stays in the arena until the container is
  destroyed; see [CCS memory](#ccs-memory).

## Loading and cancellation

`FUN_00116de0` at `0x00116DE0` is a convenient load-if-absent wrapper used by
overlays. It first checks the global container list through `FUN_00116ef0` and
`FUN_001aa450`; if absent, it builds a 0x34-byte load wrapper, calls
`FUN_001cf3f0`, detaches the produced container pointer from wrapper `+0x30`,
and normally destroys the wrapper. If the precheck finds an existing container,
the function returns zero rather than returning or retaining that container.
All resident calls observed pass load flags zero.

That zero is not a recoverable load-error result. The file-open boundary
`FUN_001be450` takes a deliberate null-store fail-fast path when opening fails,
and the CCS parser uses the same style for rejected framing/tags. In the proven
API, zero from `FUN_00116de0` means the precheck found an existing container;
missing or malformed input is expected to trap rather than return zero.

That zero-only observation matters: after detaching `+0x30`,
`FUN_00116de0` calls `FUN_001cf300(wrapper,1)` only when its flags argument is
exactly zero. A nonzero call loses the heap wrapper pointer without destroying
it; flag `0x100` additionally leaves its retained transport resources attached.
No resident nonzero caller was found, so this convenience entry point is not a
safe general retained-load interface despite forwarding the flags.

The precheck `FUN_00116ef0` at `0x00116EF0` has a sharper input contract than
the general normalizer: it resets its temporary key only at `\`, caps the
effective key at 29 bytes, and scans for a literal lowercase `.ccs` without a
NUL-termination test. Its callers must supply such a suffix; uppercase `.CCS`
or a missing suffix makes the scan continue beyond the input string. The
resulting key then passes through `FUN_001aa450`'s normalizer. This absence check
occurs before the global pipeline gate and is not atomic with publication; no
second check in `FUN_001cf3f0` prevents two concurrent callers from passing it.
If both do, their pipelines run serially but both can publish; the later
container is prepended and shadows the earlier same-name container in
subsequent lookup.

`FUN_001cf3f0` at `0x001CF3F0` proves that file loading is internally
asynchronous but externally blocking on this path. It creates named worker
tasks for:

- `LoadRead` -> `FUN_001cf060`;
- optional `LoadGzip` -> `FUN_001cf190`; and
- `LoadDecode` -> `FUN_001cf210`.

The 0x34-byte wrapper's proven coordination fields are `+0x28` cancel, `+0x2c`
read done, `+0x2d` gzip done, `+0x2e` decode done, and `+0x30` produced
container. The decode worker allocates the 0xc0-byte container, binds its
reader, and calls `FUN_001a9060`. A global byte `cGpffffcaf8` serializes active
pipelines. The coordinator waits until read and decode completion are both set;
on compressed input, ordinary cleanup also waits for gzip completion.

The global is a mode byte rather than merely a Boolean. These are its only
static writers in the resident binary: `FUN_001cf3f0` acquires it as 1 for the
ordinary `LoadRead`/`LoadDecode` pipeline, while `FUN_001ce8a0` acquires it as
2 around its `PlayRead`/`PlayGzip`/`PlayDecode` batch. Both wait for zero under
the same synchronization pair and clear it on exit, so either family excludes
the other's publication-facing work.

The constructor `FUN_001cf2b0` and cleanup `FUN_001cf300` establish the full
shared wrapper layout:

| Wrapper offset | Size | Proven role |
| ---: | ---: | --- |
| `+0x00` | 4 | Open file handle from `FUN_001be450`; closed and cleared by the coordinator after read/decode completion. |
| `+0x04` | 4 | File-list metadata dword from `FUN_001be9b0`; zero selects the direct reader path and nonzero selects the gzip path. |
| `+0x08` | 4 | Compressed-input transport, present only on the gzip path. |
| `+0x0c` | 4 | Reader consumed by `LoadDecode` and borrowed by container `+0x68`. On compressed input this is the gzip output reader. |
| `+0x10` | 4 | Gzip bridge object connecting `+0x08` to `+0x0c`; `LoadGzip` destroys and clears it on normal completion. |
| `+0x14` | 4 | `LoadGzip` task handle; that worker clears it before exiting. |
| `+0x18` | 4 | Input transport block size, initialized to `0x10000`. |
| `+0x1c` | 4 | Output transport block size, initialized to `0x10000`. |
| `+0x20` | 2 | Input transport block count, initialized to 4. |
| `+0x22` | 2 | Output transport block count, initialized to 4. |
| `+0x24` | 4 | Aligned transport buffer allocation. |
| `+0x28` | 1 | Cooperative cancel request. |
| `+0x2c` | 1 | `LoadRead` completion. |
| `+0x2d` | 1 | `LoadGzip` completion. |
| `+0x2e` | 1 | `LoadDecode` completion. |
| `+0x30` | 4 | Produced container; deliberately not owned by generic wrapper cleanup. |

`LoadRead` sends file bytes directly to `+0x0c` when `+0x04` is zero and to
`+0x08` otherwise. `LoadDecode` always constructs the container over `+0x0c`.
Thus compression changes the transport graph but not the parser-facing reader
or container constructor contract.

The coordinator clears `cGpffffcaf8` immediately after read and decode are
complete and the file handle is closed. On the ordinary compressed path it
waits for `+0x2d` and destroys `+0x08` only afterward. A following pipeline can
therefore enter while the preceding gzip worker is in its completion/cleanup
tail; the gate covers the read/decode/publication interval, not every retained
transport object's lifetime.

When flag bit `0x100` is clear, `FUN_001cf3f0` releases its temporary
buffers/readers before returning. Exact flag value `0x100` selects a whole-file
buffer path, and the bit suppresses that ordinary cleanup so
`FUN_001cf300` can release the retained wrapper resources later.
`FUN_001cf300` does not destroy wrapper `+0x30`: callers must detach the
container or destroy it explicitly.

`FUN_001cf300` also does not zero the resource pointers it destroys. It is a
one-shot destructor, not a reset operation. Observed callers either free the
wrapper itself or immediately discard its enclosing queue node; retaining the
storage and invoking cleanup again would revisit stale pointers.
It is not a cancellation or join primitive either: it does not close file
handle `+0x00`, and the read/decode worker handles are not fields it can wait on
or destroy. Proven callers reach it only after their coordinator has completed
those workers and closed the file.

`FUN_001ce8a0` is the proven owner for exact flag `0x100`: it keeps each wrapper
in a bounded slot array, later explicitly destroys any nonzero wrapper `+0x30`,
and then calls `FUN_001cf300(wrapper,1)`. Across resident and representative
BTL/ETC call sites in this slice, direct coordinator flags are only 0 or exact
`0x100`; every observed `FUN_00116de0` and queue submission uses 0. No mixed-bit
caller was found.

`FUN_001cf3d0` at `0x001CF3D0` cancels an active wrapper by setting wrapper
`+0x28` and, if already allocated, container `+0xb0`. The parser checks that
byte between object blocks. Cancellation observed before the terminator stops
parsing without finalization or publication. Cancellation may race with a
container that has already published; `FUN_003b34e0` handles that case by
explicitly destroying wrapper `+0x30`. Wrapper cleanup alone never owns that
container teardown. Cancellation is cooperative: `FUN_001cf060` and
`FUN_001cf190` have no direct cancel-byte test, while `FUN_001cf210` checks
before parsing and `FUN_001ac8a0` checks between object blocks. The coordinator
still waits for read and decode completion.

The separate queue begins at `FUN_001cf9e0`. It compares exact paths with
case-sensitive `strcmp`, returns zero for a duplicate, and otherwise appends a
0x48-byte node. The path is stored as a borrowed pointer rather than copied, so
the caller must keep it valid until the worker has consumed the node.

| Queue-node offset | Size | Proven role |
| ---: | ---: | --- |
| `+0x00` | 4 | Next node; global head/tail are `puGpffffcafc` / `puGpffffcb00`. |
| `+0x04` | 4 | Borrowed exact path pointer. |
| `+0x08` | 4 | Load flags forwarded to `FUN_001cf3f0`. |
| `+0x0c` | 2 | State: 0 queued, 1 loading, 2 one-shot pipeline returned for a previously absent path, 3 already resident. State 2 is not a separately checked success result. |
| `+0x10` | 4 | File-size estimate used only by optional aggregate-progress accounting. |
| `+0x14` | 0x34 | Embedded load wrapper. |
| `+0x44` | 4 | Embedded wrapper `+0x30`: produced container after a new load. |

`FUN_001cfcd0` starts `FUN_001cfb50` only when no queue worker is active. Its
argument value 1 asks the worker to pre-scan missing files and maintain byte
totals for `FUN_001cfae0`; it does not select synchronous behavior, ownership,
or cancellation. The worker processes nodes serially, using a blocking
`FUN_001cf3f0` invocation for each missing path. This makes the queue deferred
at its public boundary but not internally parallel. The worker's task `+0x28`
points to the active node, task `+0x2c` is its stop field, and task `+0x30`
holds the progress-accounting mode. No resident writer to that stop field was
found in this family. Because `FUN_001cf3f0` exposes no success value, the
worker marks state 2 unconditionally after it returns and implements neither a
publication check nor a retry.

Completed nodes and their embedded wrappers remain linked after the worker
clears the global task pointer. `FUN_001cfd70` therefore means only “worker
active”; false does not mean that the queue list has been freed. Callers wait
for false, resolve newly published containers by name, and then call
`FUN_001cfd90`. Cleanup calls `FUN_001cf300` with a non-positive free argument
so the embedded wrapper itself is not separately freed, then frees the outer
node.

Before wrapper cleanup, `FUN_001cfd90` consults byte `cGpffffcb08`. Zero clears
node `+0x44`, detaching and retaining the published container; nonzero instead
destroys a nonzero `+0x44` through `FUN_001a9790`. `FUN_001cfcd0` resets this
byte to zero on every observed resident start, and no resident nonzero writer
was found. The destroy branch is therefore present but dormant in the proven
resident API path. `FUN_001cfd90` itself does not check that the worker is
inactive; safe ordering is a caller contract.

There is also a genuinely deferred batch path. `FUN_003b36d0` starts worker
`FUN_003b37f0` when registry entries are pending. That worker processes state-1
entries through `FUN_003b34e0`, waits/yields through the resident task API, and
converts deferred state-2 entries to state 1 for a later pass.

## Residency use count and release

The low-level 0xc0-byte container has no proven reference count. Immediate
callers of `FUN_001a9790(container,1)` destroy it. One managed sharing mechanism
exists a layer above in the 0x2c-byte residency entry:

| Entry offset | Role |
| ---: | --- |
| `+0x00..+0x1f` | Inline requested name used by `strcmp`. |
| `+0x20` | Load state. |
| `+0x21` | Allocation origin: 0 free inline slot, 1 checked-out inline slot, 2 heap overflow entry. |
| `+0x22` | Signed 16-bit use count. |
| `+0x24` | Previous entry. |
| `+0x28` | Next entry. |

`FUN_003b2fe0` at `0x003B2FE0` acquires an entry. A new request starts with
use count 1 and state 1 or 2 according to the caller's deferred flag. Acquiring
an existing nonzero-state entry increments `+0x22`. The signed 16-bit count has
no visible overflow or underflow guard. `FUN_003b34e0` marks an entry state 4,
looks for the bare key, appends literal `.ccs` for a missing container's load,
and marks state 3 when settled. `FUN_003b3420` returns true for a missing named
entry as well as for state 3; it is therefore a not-pending test, not a strict
existence-and-ready test.

Registry keys are not passed through `FUN_001aa510`: lookup uses a direct
case-sensitive `strcmp`, and insertion copies the caller's exact string through
the unbounded `strcpy` at `FUN_0017c380`. The inline field has room for 31 bytes
plus NUL. A longer key overwrites the adjacent state, allocation-origin,
use-count, and link fields. The missing-load path copies the same key to a
32-byte stack buffer and appends four-byte suffix `.ccs`, reducing that path's
safe key limit to 27 bytes plus NUL. Because the suffix is unconditional, the
manager's intended key is extensionless; supplying `.ccs` already present asks
the loader for a doubled suffix. Neither path checks these contracts.

Exact registry identity also differs from normalized container identity. For
example, `foo` and `dir/foo` occupy separate residency entries and separate use
counts, but both are normalized by `FUN_001aa450` to container key `foo`.
Final release through either alias can destroy the one shared container while
the other entry still has users. Higher-level callers must use one canonical
extensionless bare registry key per container.

The observed state meanings and transitions are:

| State | Observed role |
| ---: | --- |
| 0 | Inactive/suppressed linked entry. Acquisition returns it unchanged without incrementing the use count or starting a load; ordinary named release skips it unless forced. No resident state-0 writer was found. |
| 1 | Pending for the current batch pass. |
| 2 | Deferred; converted to state 1 for a future batch invocation. |
| 3 | Settled/ready. |
| 4 | Load in progress. |
| 5 | Cancellation marker written during final state-4 release. That release normally unlinks the entry immediately; the batch worker also has a defensive state-5 release scan. |

`FUN_003b3140` at `0x003B3140` is release. Unless forced, it decrements the use
count and retains the entry while the result is positive. At zero it either:

- cancels state-4 loading through `FUN_003b33b0` / `FUN_001cf3d0`, producing
  state 5; or
- finds the loaded container by name and calls `FUN_001a9790(container,1)`.

It then unlinks and recycles/frees the residency entry: marker-1 entries return
to the 64-entry inline pool and marker-2 overflow entries are freed. An existing
state-0 entry is also exceptional on acquire: `FUN_003b2fe0` returns it without
incrementing `+0x22`, and `FUN_003b3650` does not call the load path. Its
producer and higher-level purpose are not present in the resident call graph.
`FUN_003b33b0`, called only by this state-4 release in the resident
binary, is the sole observed state-5 writer. Because `FUN_003b3140` continues
directly into unlinking afterward, no ordinary path was found that leaves a
state-5 entry persistently linked; the worker's state-5 scan is defensive in
the proven call graph.

The manager itself has flags at `+0x00` (bit 0 serializes one load; bit 2 marks
the batch worker), stop/cancel bytes at `+0x01/+0x02`, active-entry count at
`+0x04`, list head/tail at `+0x08/+0x0c`, 64 inline entries at
`+0x10..+0xb0f`, cached free entry at `+0xb10`, active wrapper at `+0xb14`, and
signed activity counters at `+0xb18/+0xb1a`. Only `FUN_003b3420` reads
`+0xb18`, testing whether it is positive in the null-name aggregate activity
query; no resident writer was found. `+0xb1a` is the proven batch-worker count,
incremented by `FUN_003b36d0` and decremented by `FUN_003b37f0`.
`FUN_003b37f0` is singleton-bound through `pbGpffffcde4`; it does
not consume the manager pointer passed to `FUN_003b36d0`.
`FUN_003b36d0` stores its second argument's low byte in the worker task: zero
makes a completed worker wait for external acknowledgement (or manager abort),
while nonzero permits immediate teardown.

This use count covers only clients that participate in this residency manager.
Direct container holders are not included, and adopting an already-resident
container does not discover such owners. Final registry release destroys the
matching container regardless of outside direct handles. It is therefore not a
universal CCS reference count.

The residency entry also stores no container pointer. Ensure-loaded and final
release each call `FUN_001aa450` again with the entry name. If another
same-normalized-name container is prepended between those operations, release
destroys that current head-most match rather than necessarily the instance the
entry originally adopted or caused to load; the older duplicate can remain
resident. Name uniqueness and serialized publication are higher-level
contracts, not properties of the residency entry.

### Low-level destruction

`FUN_001a9790` at `0x001A9790` first looks for the container in the global list.
It enters the full teardown body only when it was found there or when its
cancellation byte `+0xb0` is nonzero. That body invalidates foreign references,
releases `+0x5c`, conditionally closes the owned `+0x68` reader, frees temporary
allocations, and calls `FUN_001a9f10` for records 1 through
`record_count - 1`. It then frees the hash buckets, record table, and string
table. An unlisted, non-canceled object skips the body and reaches only `+0x6c`
vector destruction and the optional final container free. Every resident
static caller observed passes a positive second argument and therefore frees
the 0xc0-byte allocation.

This generic destructor does not inspect or clear container `+0x60` and does
not call `FUN_001a2280` or `FUN_001a2520`. The play-runtime table and any rows
it owns therefore belong to the separate play-state lifecycle; ordinary
container destruction is not a substitute for stopping that task and reaching
its teardown. The normal primary-play exit establishes the correct ordering,
but `FUN_001a9790` itself does not enforce it.

`FUN_001a9f10` at `0x001A9F10` dispatches destruction by record `+0x2a` and
then clears both `+0x30` and `+0x2c`. A `#` record skips only the type-specific
destructor dispatch; its two fields are still cleared, so a referencing
container drops the reference without destroying the provider's object. The
dispatch uses type-specific destructors, direct frees, and virtual destructors;
there is no generic object-level refcount visible in this family.

## Streamed playback (SP Skill Play)

### Who plays CCS files

The play-runtime builder `FUN_001a0b80` has exactly one caller in the resident
executable and none in `BTL.BIN`, `ETC.BIN`, or `ADV.BIN` (searched by `jal`
encoding): the `PlayDecode` worker `FUN_001ce410`. That worker belongs to the
persistent stream player run by `FUN_001ce8a0`, whose only caller is the task
body `FUN_00359b50` created by `FUN_0035cf00` under the task name
`SP_Skill_Play`. `FUN_0035cf00` is called once from `BTL.BIN` (the `jal` at
preserved `0x0076A0CC`, live `0x0076A10C`), the ultimate jutsu presentation
described in [Ultimate jutsu](../../gameplay/ultimate_jutsu.md#skill-play-admission),
and once from `ETC.BIN` `FUN_006c0ab0` (preserved `0x006C0AB0`, live
`0x006C0AF0`).

**Observation:** the ultimate jutsu cutscene is the only battle use of the
play runtime. Stage, fighter, HUD, and other battle containers are never given a
play context, a `+0x60` table, or checkpoints; battle code builds its own
objects from them through name lookups. The `+0xa6` bit-3 alternate secondary
lookup therefore applies only to a container that is being played.

The transport side of the player (its rings, `PlayRead`, `PlayGzip`, and the
0x14-byte request rows at player `+0x130`) is documented in
[Persistent three-task pipeline](runtime_services.md#persistent-three-task-pipeline).

### Request list

`FUN_0035cf00` allocates the 0x2E0-byte player, sets both rings to four
0x10000-byte blocks, and stores the request list built by `FUN_0035cc20` at
player `+0x2d4` (count at `+0x2d8`). Each 8-byte request is `{path, flags}`:

- rows with flag `0x1000` for the entry's list of resident paths plus its main
  path (the main path comes first unless the skill value is `0x20`);
- then one or more rows for the entry's stream path, the first with flag
  `0x400` and any further rows with flag `0`.

When `FUN_0035c930` finds the requested skill in its override table, the stream
path becomes the matched string and the main path becomes the same string with
`.ccs` replaced by `e.ccs`. The retail `STR` directory holds such pairs, for
example `D01_10.CCS` (5,579,180 bytes decompressed) and `D01_10E.CCS` (413,428
bytes). **Inference:** in that case the smaller `E` file is loaded as an
ordinary resident container and the base file is streamed.

`FUN_001ce8a0` then:

1. For every `0x1000` row whose container is not already published
   (`FUN_001aa450`), runs an ordinary flag-0 one-shot load and keeps the wrapper
   in slot array `+0xf0` (at most 16 wrappers; another traps). Already-resident
   containers are only borrowed.
2. For every other row, registers a request through `FUN_001cdc20`. A row with
   flag `0x100` (or with player byte `+0x2da` set) is first loaded whole through
   a flag-`0x100` one-shot load; its container comes from that wrapper.
3. Waits for pipeline gate `cGpffffcaf8` to be free and takes it with value 2,
   allocates the two 0x40000-byte rings (alignment 0x80), and starts
   `PlayDecode`, `PlayRead`, and `PlayGzip`.
4. Waits until every request has been read and decoded, destroys containers of
   rows flagged `0x80`, then destroys every container still held by a slot
   wrapper (`FUN_001a9790`) and frees the wrappers.
5. Waits for the read and decode tasks to finish and releases the gate. The
   task body then calls `FUN_001cde10` to destroy the player.

A consequence of step 1 and step 4: containers the player loaded itself are
destroyed when the cutscene ends, while containers that were already resident
stay resident.

### Per-request lifecycle in `PlayDecode`

`FUN_001ce410` walks the requests with cursor `+0x278`:

1. A streamed request gets a new 0xC0-byte container bound to the player's
   decoded-ring reader (`+0x08`) and is parsed by `FUN_001a9060`. It is
   published to the global list like any other container, so its `#` records
   resolve against the fighter and effect containers already resident.
2. `FUN_001a0b80(container, 0x00609160, 0)` builds the play runtime, and the
   player's `+0x88` callback runs (`FUN_0035a070` for skill play).
3. While the request's flag `0x400` is set, the worker sets flag `0x4000` and
   yields. This holds the first stream request until the owner releases it.
4. `FUN_001a0890` creates the play task and its `PlayLock` companion with flags
   `player +0x27c | 4 | (request index << 16)`.
5. The worker waits for container `+0xa6` bit 5. It asks the play task to stop
   (`FUN_001a00c0`) when the stream has ended and player flags `+0x27c` carry
   neither bit 0 (which makes the play loop restart instead of ending) nor bit
   2, or when player byte `+0x281` is 1 or 3.
6. After playback, the retention byte of every request up to the current one
   is counted down. A request whose byte has reached zero has its container
   destroyed by `FUN_001a9790(container,1)`. `FUN_001cdc20` initializes that
   byte to the low four flag bits, so a flag-0 stream request is destroyed right
   after its own playback; flags `0x80` and `0x100` use sentinels `0xfe` and
   `0xff` that are never counted down.
7. The cursor advances, or jumps to the end when `+0x281` is 2 or more.

### The play task

`FUN_001a0890` creates the task at `0x001A0980` (priority `0x1b`, 0x1000-byte
stack), which calls `FUN_001a0120`. Each step of that loop:

- advances the frame stream through `FUN_001b4c60`, using rate `+0x9c`;
- updates the `+0x114` generator-action manager with the same rate
  (`FUN_001abc70`);
- calls the per-frame callback (`FUN_0035b740` for skill play) and the
  per-object callback at container `+0x7c`;
- updates and submits the scene through `FUN_001a0a40`; and
- yields once.

When a stop is requested, the loop releases the `0x2200` ring manager if
container bit 7 is set, runs the end callback (`FUN_0035af20` for skill play),
tears the play state down through `FUN_001a2280`, writes task state 2, and sets
container `+0xa6` bit 5. The container itself is not destroyed here; the
request retention in `PlayDecode` decides that.

`FUN_001a2280` frees the checkpoint table, releases the `+0x4c` light
secondaries from the scene, frees the play context's object lists, destroys the
`+0x60` table through `FUN_001a2520`, destroys controllers and the draw
environment the context owns (container `+0xae` bits 0, 2, and 3), destroys the
`+0x114` action manager, and frees the play context.

### Frame stream

A playback file continues after its tag-5 block with frame blocks that use the
same 8-byte header. `FUN_001b4f80` reads them over an inclusive frame range and
dispatches this second tag set; any other tag traps:

| Frame tag | Handler |
| ---: | --- |
| `0xFF01` | Frame marker: its payload dword becomes the frame cursor and is recorded in the checkpoint table. |
| `0x0005` | Terminator again (`FUN_001b5290`), met when playback seeks back to checkpoint 0. |
| `0x0101` | `FUN_001b5900` |
| `0x0108` | `FUN_001b69b0` (also receives the frame cursor) |
| `0x0201` | `FUN_001b5400` (version gate `0x120`) |
| `0x0502` | `FUN_001b5d50` |
| `0x0601`, `0x0602`, `0x0604`, `0x0606`, `0x0608` | `FUN_001b5f70`, `FUN_001b6020`, `FUN_001b61e0`, `FUN_001b64a0`, `FUN_001b6810` |
| `0x0802`, `0x0803` | `FUN_001b6ab0`, `FUN_001b6c60` |
| `0x1801` | `FUN_001b57f0` |
| `0x1901` | `FUN_001b56e0` |
| `0x1A01`, `0x1B01`, `0x1C01`, `0x1D01` | `FUN_001b6e40` (version gate `0x111`), `FUN_001b6fd0`, `FUN_001b71a0`, `FUN_001b7340` |
| `0x2201` | `FUN_001b52d0` |

**Inference:** the high byte of each frame tag matches the file object tag it
animates (`0x01` object, `0x02` material, `0x05` camera, `0x06` light, `0x08`
model, `0x18`/`0x19` controllers and morphers, `0x1A`-`0x1D` draw environment,
`0x22` ring batch). The frame payloads were not decoded.

A frame marker with payload `-1` ends the stream: `FUN_001b4c60` sets container
`+0xa6` bits 2 and 4. Payload `-2` does the same and then calls `FUN_0019ffc0`,
which rewinds to checkpoint 0, restarts animated effects, and reinstantiates the
`+0x58` generator actions, so the stream loops.

**Retail-file observation:** in the decompressed `STR/D01_10.CCS`, the tag-5
block at `0x12060` carries payload `0x13F`, header `+0x98` is also `0x13F`, the
first frame marker (index 0) follows at `0x1206C`, and the last marker, at the
end of the 5,579,180-byte stream, has payload `-1`. Its namespace table refers to
fighter and effect containers through `#` rows such as
`#c\1nrt\max\1nrtbod1.max` and `#e\00\max\e00hit01.max`.

## CCS memory

Allocator placement, load transients, and sampled battle capacity are owned by
[EE allocator](../../runtime/ee_memory_map/allocator_and_capacity.md#ccs-load-cost).
The container-owned allocations established here are:

| Allocation | Size | Owner and lifetime |
| --- | --- | --- |
| Container | 0xC0 | Decode worker or `PlayDecode`; freed by `FUN_001a9790(container,1)`. |
| Namespace table | `namespace_count * 0x20` | `FUN_001ac6c0`; freed by container destruction. |
| Record array | `record_count * 0x38` | `FUN_001ac6c0`; freed by container destruction. |
| Hash buckets | one word per record | `FUN_001acdb0`; freed by container destruction. |
| Type objects | per parser | Allocated while parsing; freed by `FUN_001a9f10` per record. |
| Owned reader | 0x40 | Only when the container was given no reader. |
| Play context, `+0x60` table (`record_count * 0x10`), checkpoints (`+0x98 * 4`), and materialized play objects | per file | Only for a played container; freed by `FUN_001a2280`. |

Every container parse runs inside the parser's high-placement scope, so all
parse-time allocations above come from the top of the arena. The play-time
allocations in `FUN_001a0b80` run on the `PlayDecode` thread outside that scope.

## Representative overlay callers

### Battle setup (resident)

The order of battle preparation is owned by
[Battle lifecycle](../../gameplay/battle_lifecycle.md#resident-setup-order).
Its CCS mechanics are:

- `FUN_001e9520(1)` queues every missing battle container through
  `FUN_001cf9e0` and starts one `LoadBg` worker with `FUN_001cfcd0(1)`; with
  argument 0 it loads each one synchronously through `FUN_00116de0` instead.
  Each path is first checked with `FUN_001aa450`, so an already-resident
  container is not reloaded.
- `FUN_001e80f0(manager, side, mask, deferred)` builds up to nine fighter paths
  per side into 30-byte buffers at manager `+0xa3c + side*0x134` onward, using
  `%s%s` with prefixes `pl/`, `3eye/`, and `cutin/` and the filename tables
  documented in [Character asset tables](../character_assets.md). Mask bit 0
  selects the `1???bod1` table and bit 1 the `2???bod1` table.
- `FUN_001e86c0` later adopts the published containers by name into the
  per-side handle slots at manager `+0xa18..+0xa38 + side*0x134`.
- `FUN_001e8960` destroys a side's selected slots with `FUN_001a9790` and also
  clears the other side's slot when it holds the same container.
  `FUN_001e8e20` destroys one slot only when the other side does not share it.

**Observation:** in a mirror match both sides adopt the same published
container, because adoption is a name lookup; the release functions guard that
sharing explicitly rather than through a reference count.

### BTL.BIN

`FUN_006c30c0` (Ghidra/export `0x006C30C0`, live `0x006C3100`) selects a stage
path from the table at raw BTL offset `0x001DCB10`, preserved byte/display
location `0x008909D0`, and live address `0x00890A10`. Its 24 encoded pointer
values are already-live addresses for `stage/s01.ccs` through
`stage/s24.ccs`; they are not adjusted again. The caller then invokes
optional `FUN_001aa450`, and falls back to synchronous
`FUN_00116de0(path,0)` when the container is absent. The resulting container is
stored in the BTL global `uGpffffcdf0`. `FUN_006c3120` (Ghidra/export
`0x006C3120`, live `0x006C3160`) destroys the stored container with
`FUN_001a9790(handle,1)` and clears the slot. `FUN_006c3190` (Ghidra/export
`0x006C3190`, live `0x006C31D0`) submits the same stage path to the resident
queued-loader family through `FUN_001cf9e0`. `FUN_006c31d0` (Ghidra/export
`0x006C31D0`, live `0x006C3210`) is the corresponding required-container
lookup.

`FUN_006e7860` (Ghidra/export `0x006E7860`, live `0x006E78A0`) is a clearer
caller-level ownership example. It first looks up `spbattle.ccs`, loads only on
a miss, stores the handle at object `+0x00`, and sets owns byte `+0x123` only for
the newly loaded case. `FUN_006e7c80` (Ghidra/export `0x006E7C80`, live
`0x006E7CC0`) calls `FUN_001a9790` only when that byte is set, then clears the
pointer and flag. A found resident container is therefore explicitly borrowed.

`FUN_00768f50` (Ghidra/export `0x00768F50`, live `0x00768F90`) applies the
same distinction across four paths: `shade.ccs`, `gauge.ccs`, `strmcmn.ccs`,
and `ougi.ccs`. It synchronously loads only misses and marks those rows in an
ownership bitmask. `FUN_00769010` (Ghidra/export `0x00769010`, live
`0x00769050`) is the deferred variant, enqueueing misses and setting the same
bits. `FUN_007690d0` (Ghidra/export `0x007690D0`, live `0x00769110`) resolves
all four handles after queue completion, while `FUN_00769160` (Ghidra/export
`0x00769160`, live `0x007691A0`) destroys only handles whose ownership bits
were set. Synchronous and deferred acquisition therefore share one explicit
caller-owned release ledger.

The BTL data operands in these examples were audited separately from the body
addresses. The stage-family instructions encode the already-live table address
`0x00890A10`; its 24 words encode live string pointers
`0x00890890..0x00890A00`. `FUN_006e7860` encodes the live `spbattle.ccs`
pointer `0x00896D48` (raw `0x001E2E48`, preserved bytes `0x00896D08`). The
four-path family encodes live table address `0x008A59E0` (raw `0x001F1AE0`,
preserved bytes `0x008A59A0`); its words are live pointers
`0x008A59A0..0x008A59D0`, whose string bytes occupy raw
`0x001F1AA0..0x001F1AD0` / preserved `0x008A5960..0x008A5990`. Its encoded
`0x008DA9C0` destination is a live BSS handle-array address beyond the file,
not another payload table. The remaining named BTL state in this section is
accessed GP-relatively. None of these encoded data operands takes an additional
header adjustment.

For object access, `FUN_006c3ea0` (Ghidra/export `0x006C3EA0`, live
`0x006C3EE0`) selects one of two name globals from event codes `0x21`/`0x22`
and performs required `FUN_001a8f00(*container_slot,name,0)`. This is
representative of BTL's common pattern: retain a container handle in owning
state, then repeatedly obtain type-specific runtime objects by required or
optional name lookup.

### ETC.BIN

`FUN_006b57d0` (Ghidra/export `0x006B57D0`, live `0x006B5810`) performs
optional `FUN_001aa450(uGpffffc4c8)` and stores the container at object `+0x10`.
`FUN_006b58f0` (Ghidra/export `0x006B58F0`, live `0x006B5930`) then performs
required `FUN_001a8f00(object->container,uGpffffc828,0)`. `FUN_006b9420`
(Ghidra/export `0x006B9420`, live `0x006B9460`) shows the stricter form, using
required `FUN_001aa4b0` before a required object lookup.

The standalone ETC export identifies those operands only as resident-populated
GP globals; their concrete strings are not statically initialized inside
`ETC.BIN`. Assigning names from nearby overlay data would therefore be
speculative. Several adjacent ETC decompiler fragments also leave the lookup
return in `v0` for the following fragment rather than showing a C assignment;
the call and arguments are reliable, but the split C consumer is not.

`FUN_006be6d0` (Ghidra/export `0x006BE6D0`, live `0x006BE710`) demonstrates
mixed ownership in one object: it stores an optional shared-container lookup at
`+0x408`, then uses load-if-absent for `strmcmn.ccs` at `+0x40c` and
`pl/1cmnbod1.ccs` at `+0x410`. `FUN_006be290` (Ghidra/export `0x006BE290`,
live `0x006BE2D0`) destroys `+0x40c/+0x410` but not `+0x408`. Because there
is no prelookup/adoption for the two owned fields, either remains zero when its
container was already resident; only `+0x408` deliberately holds a borrowed
pre-existing container.

These ETC instructions also encode already-live data pointers. For
`FUN_006be6d0`, `pl/1cmnbod1.ccs` is live `0x006E2C20`, raw `0x0002ED20`, and
preserved/display `0x006E2BE0`; `strmcmn.ccs` is live `0x006E2C30`, raw
`0x0002ED30`, and preserved/display `0x006E2BF0`. The strings were confirmed
directly in the hashed raw `ETC.BIN`; none of the encoded pointers receives
another `+0x40`.

`FUN_006b9c00` (Ghidra/export `0x006B9C00`, live `0x006B9C40`) is a concrete
deferred caller. On a selected-name miss it releases its prior owned container
at `+0x18`, queues the new path through `FUN_001cf9e0`, starts the worker with
`FUN_001cfcd0(0)`, waits on `FUN_001cfd70`, resolves the published handle with
`FUN_001aa450`, and cleans the queue through `FUN_001cfd90`.

## Negative results and confidence

- **High confidence:** container list/key behavior; case sensitivity; required
  versus optional miss behavior; record sizes and offsets; hash construction;
  wildcard rejection on `FUN_001a8f00`; numeric index conversion; publication,
  cancellation, cross-container invalidation, and destruction flow.
- **High confidence:** the residency entry at `0x003B2FE0`/`0x003B3140`, rather
  than the low-level container, owns the observable use count.
- **High confidence:** file I/O/decompression/decode use worker tasks, while
  `FUN_001cf3f0` waits for their completion before returning.
- **High confidence:** the file framing, the ignored length and marker fields,
  the version gates, the play-runtime call graph (`FUN_001a0b80` has one caller),
  and the stream player's load and destruction order.
- **Medium confidence:** NUN3-to-NA2 file compatibility beyond framing,
  dispatch, the terminator, and the model header.
- **Medium confidence:** descriptive names such as “secondary value,” because
  the meaning of record `+0x30` varies by type even though its lookup behavior
  is exact.
- No generic object type assertion was found in `FUN_001a8f00`; no complete,
  evidence-backed mapping from numeric tags to clean class names was established.
- No object-level retain/release counter was found in the lookup/record family.
  Registry participants are tracked at residency-entry lifetime, while direct
  holders rely on caller-owned flags and explicit cross-container invalidation.
- Global-list insertion and dependency resolution are visibly synchronized;
  `FUN_001a9790` itself has no visible matching lock in this static slice, so
  caller-side unload serialization remains unproven.
- The analysis did not cover Adventure or any media-replacement, localization,
  widescreen, frame-rate, damage, or substitution path.
