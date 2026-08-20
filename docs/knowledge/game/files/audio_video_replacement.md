# Audio and video replacement

This note records the current replacement constraints for the four AFS audio
archives and ten PSS movies in *Narutimate Accel 2 v2.28*. It is a static
research result, not a claim that the game has accepted a generated file at
runtime. The protected files under `@source_na2/` were inspected read-only on
2026-08-20. CriCodecs 1.2.0 was exercised from a checksum-verified release in a
transient directory; no encoder, archive writer, or movie muxer was added to the
maintained project.

Evidence labels in this note have their usual knowledge-base meaning:

- **Observed**: read directly from the source files or maintained project code.
- **Inferred**: a proposed implementation follows from the observed layout but
  still needs a generated-file and runtime test.
- **Unresolved**: the current evidence does not close the question.

## Research coverage

- **Assigned scope:** replacement feasibility for the four top-level AFS audio
  archives and ten shipped PSS movies in NA2 v2.28, including only the disc-image
  size rule, nested archive/codec contracts, PSS stream contract, and resident
  movie selectors needed to bound a safe replacement workflow.
- **Exploration depth:** the clean corpus was parsed exhaustively
  across 170 AFS containers, 9,966 declared indices, all 9,068 AHX members and
  all 246 ADX members. All ten PSS files were length-driven through every
  pack/PES packet and their complete video and private-audio streams; the clean
  ELF's 12-row descriptor table, direct selector calls, subtitle schedules, and
  current image-assembler size guard were traced.
- **Confirmed coverage:** focused transient experiments exercised CriCodecs
  1.2.0 and FFmpeg 9.0.1, including an offline, exact-size
  synthetic `LOGO_C.PSS` whose 90-picture MPEG-2 stream, replacement PCM body,
  packet lattice, timestamps, padding, and complete decode all passed static
  checks. No generated media or tool was retained as a project dependency.
- **Unresolved or untested:** no generated AFS or PSS has been played by the
  game's bundled CRI/movie drivers in PCSX2 or on hardware. A fitting adaptive
  type-`0x11` AHX encoder, the correct ADX version-4 history and loop-padding
  derivation, a maintained PSS writer, and the exact progressive-plus-alternate-
  scan encode path for `NOTICE.PSS` remain open. Computed or indirect calls to
  dormant movie rows also remain unresolved.
- **Deliberate exclusions and overlap:** this task did not implement a writer,
  alter protected source media, enable variable-size ISO/UDF relocation, or
  patch resident subtitles/transitions. Resident movie data was followed only
  far enough to establish replacement constraints; broader subtitle, image
  builder, runtime, and executable-patching work remains with their owning
  tasks. The absent `logo_cT.pss` and `openingT.pss` names are documented only
  to the extent established by the selector/table trace.
- **Evidence limitations:** results are based on one clean `SLPS_258.37` and its
  read-only extracted media, static disassembly/direct-call evidence, corpus
  parsers, and bounded host-side codec/decoder experiments. Those establish file
  structure and offline feasibility, not runtime acceptance, streaming
  bandwidth tolerance, or the absence of unobserved indirect consumers.

## Result

- **Audio is structurally replaceable, but is not yet a turnkey workflow.** The
  archives use fixed, aligned slots and can accept a same-or-smaller encoded
  leaf while retaining the original archive size. CriCodecs 1.2.0 is a useful
  ADX/AHX baseline, but its fixed AHX allocation and incomplete ADX version-4
  fields do not cover every observed profile. An AFS patcher and any chosen
  encoder still need validation against the game's CRI driver.
- **Movie replacement is characterized but not production-ready.** A same-size
  PSS donor can already pass the image assembler's whole-file size guard. New
  content needs either an in-place packet-skeleton writer or a constrained PSS
  muxer; neither exists in the maintained project today. Resident descriptors
  also retain per-movie geometry, transition frames, and six Japanese subtitle
  schedules, so changing only the PSS is not sufficient for arbitrary content.
  The game obtains movie size dynamically from the disc directory; equal size
  is a current builder/image-layout restriction, not a compiled movie limit.
- **The current extracted `.adx` suffix is not codec evidence.** Header scans
  show 9,068 CRI AHX voice/effect files and only 246 CRI ADX files.

## Shared disc-image constraint

The current image assembler permits a replacement only when its byte length
equals both the guarded expected file and the ISO record. See the
[`FileReplacement` size check](../../../../na228_builder/image_assembler/assembler.py)
and the [image assembler contract](../../../../na228_builder/image_assembler/README.md).
Consequently, an audio archive or movie produced by the first implementation
must have exactly the original outer-file size. This is a builder constraint;
the resident movie path does not add a second per-movie size table.

All generated media should be built outside `@source_na2/` and then supplied as
a guarded whole-file replacement. The protected source extraction must remain
unchanged.

### Runtime movie path and size source

The resident opener establishes where the game gets the movie extent:

1. `FUN_001DBD60` passes the selected descriptor's filename to
   `FUN_00105E10`, which delegates to `FUN_001057B0`.
2. Its reader thread enters `FUN_00103990`. That routine prepends the resident
   string `cdrom0:\PSS\`, normalizes the result to uppercase, and appends
   `;1`. It strips the device prefix before calling `FUN_00172900`, the CDVD
   file-search wrapper. For example, `logo_c.pss` becomes the searched path
   `\PSS\LOGO_C.PSS;1`.
3. The returned CD file record supplies both the starting LSN and byte size.
   `FUN_00103990` copies its size field into the stream's remaining-byte
   counter. `FUN_00103EE0` initializes its read and consume counters from that
   value; it does not read a size from the movie descriptor.

The thread reads at most `0x10000` bytes per turn, rounds each physical read
down to whole `0x800`-byte sectors in `FUN_001038E0`, and feeds a fixed
`0x60000`-byte ring buffer. Its main loop continues only while more than four
file bytes remain. With the observed `N * 0x4000 + 4` layout, it therefore reads
all program-stream packs and leaves the four-byte program-end code as the final
unread remainder. Total movie size is not a decoder-buffer allocation.

**Supported conclusion:** a different number of valid `0x4000` packs is not
rejected by a resident hard-coded length. It would still require a new image
operation that safely updates the ISO9660 directory size and, when needed, the
extent/layout (plus any maintained UDF mirror), while retaining the four-byte
tail convention. The current guarded `FileReplacement` intentionally does none
of that, so same-size output remains the appropriate first implementation.

## AFS audio

### Actual codec and archive map

The four top-level AFS files contain 170 AFS archives when their nested
archives are included. Across them there are 9,966 declared indices, 9,480
non-empty members, and 486 null members. Of the non-empty members, 166 are
nested AFS containers and 9,314 are audio files.

| Top-level archive | Outer layout | Leaf audio observed | Channels and rate |
| --- | --- | --- | --- |
| `PLVOICE.AFS` | 93 indices: 72 nested AFS, 21 null | 2,232 AHX type `0x11` | Mono, 24,000 Hz |
| `RPGVOICE.AFS` | 82 indices: 81 nested AFS, 1 null | 914 AHX type `0x10`; 4,683 AHX type `0x11` | Mono; 5,596 at 24,000 Hz and one at 48,000 Hz |
| `SOUND.AFS` | 13 nested AFS, no null outer index | 642 AHX type `0x10`; 597 AHX type `0x11`; 73 ADX type `0x03` | AHX mono; ADX stereo; all 24,000 Hz |
| `STREAM.AFS` | 184 direct indices: 173 audio, 11 null | 173 ADX type `0x03` | Stereo, 24,000 Hz |

The one rate outlier is
`DATA/RPGVOICE.AFS.files/028.afs.files/015.adx`: its header reports AHX type
`0x10`, mono, 48,000 Hz, and 183,798 samples. Its `.adx` name came from the
extractor and does not change the header classification.

**Observed codec contracts:**

- AHX files use CRI's `(c)CRI` marker, version `0x06`, one channel, and type
  `0x10` or `0x11`. No encrypted AHX file was observed.
- ADX files use type `0x03`, an 18-byte frame, 4-bit samples, two channels,
  24,000 Hz, a 500 Hz high-pass field, and version `0x04`. No encrypted ADX file
  was observed.
- 180 ADX files begin coded data at offset 40 and have no loop block: all 173
  `STREAM.AFS` files and seven `SOUND.AFS` files. The other 66 are looped tracks,
  all under `SOUND.AFS.files/000.afs.files`.

The maintained inventory's numeric `.adx` names were assigned by a shallow
`(c)CRI` signature check. Use the parsed header fields above, not the filename
extension, to choose an encoder. The exact container/index/offset/length map
remains in [`media/afs_members.tsv`](media/afs_members.tsv).

### AHX frame, terminator, and fit contract

All 9,068 AHX members have the same 36-byte wrapper shape: coded data begins at
offset 36, the wrapper reports one channel, version `0x06`, and no encryption,
and `(c)CRI` ends at offset 36. Every coded frame begins with the four bytes
`FF F5 E0 C0`. That is an AHX-specific MPEG Layer II header which advertises a
nominal `0x414`-byte frame, but AHX removes unused frame padding and stores
variable-length frames. Boundaries must be derived by parsing the 30 allocation
values, scalefactor-selection fields, scalefactors, and quantized samples. A
plain search for the next four-byte header is unsafe because that value can
occur inside the coded payload.

The complete corpus parses without a missing or extra frame. In every file:

```text
frame_count = ceil(wrapper_sample_count / 1152)
file_size   = 36 + sum(syntax-derived frame sizes) + 17
```

The final frame therefore represents between 0 and 1,151 padded samples. The
17-byte terminator is identical in every file. Its leading zero is outside the
last syntax-derived frame:

```text
00 80 01 00 0C 41 48 58 45 28 63 29 43 52 49 00 00
               A  H  X  E  (  c  )  C  R  I
```

Observed encoded-frame distributions are:

| AHX type | Files | Frames | Actual frame bytes | Median | Mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| `0x10` | 1,556 | 107,420 | 395–440 | 408 | 410.115 |
| `0x11` | 7,512 | 404,151 | 14–440 | 407 | 393.706 |

The 30 allocation widths are four bits for bands 0–3, three bits for bands
4–10, and two bits for bands 11–29. All 107,420 type-`0x10` frames use one
allocation vector:

```text
6 6 6 6  4 4  3 3 3 3 3 3  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
```

Type `0x11` is adaptive. Of its 404,151 frames, 305,434 use that default vector
and 98,717 use one of 42,156 other vectors. That includes 3,624 all-zero
allocation frames whose complete syntax is only 14 bytes. Type `0x10` therefore
stays in a narrow, comparatively large range while type `0x11` can collapse
quiet frames to very small payloads. AHX size is content-dependent even when
sample count is unchanged; unlike ADX, target fit cannot be predicted from
duration alone. The two types are not interchangeable space-saving presets.

**Conservative AHX replacement:** convert the source to mono PCM at the target
rate (24 kHz except for the single documented 48 kHz outlier), and deliberately
pad or crop it to the target sample count. Encode the target's exact AHX type,
version `0x06`, and unencrypted wrapper. Parse every generated variable-length
frame, require the fixed terminator, and check the complete encoded size against
the AFS slot only after encoding. A shorter member should update its AFS length
and leave the rest of the fixed slot cleared; do not append arbitrary bytes
after the AHX terminator. Independently decode and compare channel count, rate,
sample count, timing, and waveform before attempting a runtime test. For type
`0x11`, also require an encoder which reproduces adaptive allocation closely
enough to fit the selected slot; a structurally valid fixed-allocation stream
is not an adequate substitute.

### ADX history, loop, and footer contract

The version-4 header stores two signed big-endian predictor-history samples per
channel at offsets `0x18..0x1F`. They are active decoder state, not generic
reserved zeros. Ten NA2 ADX files have a nonzero history: one of the 66 looped
`SOUND` tracks, one non-looped `SOUND` cue, and eight `STREAM` cues. A different
waveform therefore needs history values produced from that waveform; copying a
target's nonzero values can alter its first decoded samples.

For every extended-header file, the 24-byte loop block at `0x20..0x37` has this
big-endian layout:

| Offset | Size | Observed role |
| ---: | ---: | --- |
| `0x20` | 2 | Encoder loop-padding field, observed range 0–31 |
| `0x22` | 2 | Loop marker, always 1 |
| `0x24` | 4 | Loop count/type flag, always 1 |
| `0x28` | 4 | Loop-start sample |
| `0x2C` | 4 | Loop-start file offset |
| `0x30` | 4 | Loop-end sample |
| `0x34` | 4 | Loop-end file offset |

All 66 satisfy `0 <= loop_start < loop_end <= total_samples`; every loop start
is a multiple of 32 samples. With 18 bytes per channel frame, two channels, and
32 samples per frame, their stored byte positions satisfy exactly:

```text
loop_start_offset = data_start + (loop_start_sample / 32) * 36
loop_end_offset   = data_start + ceil(loop_end_sample / 32) * 36
```

Every loop-start offset is also a multiple of `0x800`. The encoder selected a
variable `data_start` from 96 through 2,096 bytes to make that true. Bytes from
the end of the loop block through the six-byte `(c)CRI` marker at
`data_start - 6` are zero; no `AINF` or other auxiliary header is present.

The coded-body size is content-independent for a fixed sample count:

```text
coded_bytes = ceil(total_samples / 32) * 18 * 2
```

It is followed in every file by `80 01`, a big-endian 16-bit zero-padding
length, and exactly that many zero bytes. The 180 non-looping files use 14 zero
bytes, making an 18-byte footer. The 66 looped files use a longer footer so the
complete declared AFS member length is a multiple of `0x800`. All 246 files
match the header/body/footer formula exactly.

**Conservative ADX replacement:** keep the target sample count, or pad/crop the
source deliberately to it; preserve 24 kHz stereo, type `0x03`, frame size 18,
4-bit depth, 500 Hz cutoff, and version `0x04`. Preserve the target loop sample
semantics, but recompute its byte offsets from the generated `data_start` and
recompute initial histories from the new waveform. Then write the `0x8001`
footer so the full member length equals the target length. Because coded size
depends only on sample count, an exact-sample-count replacement has a
predictable fit independent of audio content. A chosen encoder must still be
round-tripped through an independent decoder and tested with `CRI_ADXI.IRX`.

CriCodecs 1.2.0 encoded the inspected non-looped and looped cases to the exact
target length and preserved the looped case's sample and byte positions. It did
not reproduce two opaque-but-live version-4 fields. Re-encoding
`STREAM.AFS.files/039.adx` changed all four nonzero predictor histories from 6
to 0 and measurably changed its first decoded samples. Re-encoding
`SOUND.AFS.files/000.afs.files/001.adx` changed the loop-padding field at
`0x20` from `0x0013` to zero while keeping its other reported loop metadata.
Those fields must be generated correctly or their runtime irrelevance must be
proved before treating the current CLI output as replacement-ready.

### Fixed-slot replacement model

**Observed:** every non-empty AFS member begins on a `0x800` boundary. Each AFS
also has a 48-byte attributes row for every declared index. The space from a
member offset to the next occupied member offset (or to the attributes table
for the last member) is its available slot. Observed unused space ranges from
0 to 2,047 bytes.

**Inferred first implementation:**

1. Resolve the top-level archive, nested AFS index, and leaf index from
   `media/afs_members.tsv`; reject a null index.
2. Read the target header and require an explicit match for codec type,
   channels, sample rate, version, encryption state, and relevant ADX loop
   fields. Do not select a profile from the extracted extension.
3. Encode the replacement and require its complete encoded length to be no
   larger than the target slot capacity.
4. Write the encoded bytes into a generated copy of the innermost archive,
   update only that leaf's length field, and clear the unused remainder of the
   slot. Preserve offsets, alignment, index order, null entries, archive size,
   and every 48-byte attributes row.
5. For a nested archive, keep the generated inner archive's total length
   unchanged. The containing AFS entry therefore needs no offset or length
   change. Repeat outward until the top-level file remains exactly its original
   size.
6. Feed the generated top-level AFS to a guarded `FileReplacement` with the
   full expected original bytes or digest.

If an encoded leaf exceeds its slot, this procedure must fail. Shortening the
content or producing a smaller encoding with the same target profile may solve
the fit. Moving later members or rebuilding an archive is a separate writer
path and must preserve the original AFS variant and outer size; it has not been
validated.

### Candidate tools

- [CriCodecs](https://github.com/Youjose/CriCodecs) 1.2.0 is the strongest
  current starting point, but its output is not yet replacement-ready for every
  NA2 profile. Its
  documented CLI supports WAV-to-AHX/ADX and both AHX modes. A checksum-verified
  Windows release was tested against clean NA2 members. Generated type `0x10`
  and `0x11` files retained wrapper metadata and decoded to the declared PCM
  length; non-looped and looped ADX retained their primary format metadata, and
  the looped case retained exact loop samples and byte positions. The ADX
  history and loop-padding exceptions are documented above.

  CriCodecs' current AHX encoder applies one fixed allocation profile to every
  frame. It also prepends a 480-sample delay for mode `0x11`; 3,088 of NA2's
  7,512 type-`0x11` files would cross an additional 1,152-sample frame boundary
  under that policy. In the decisive silent case
  `RPGVOICE.AFS.files/044.afs.files/031.adx`, the clean 24,000-sample member is
  347 bytes (21 all-zero 14-byte frames), in a `0x800`-byte slot. Re-encoding
  its decoded silence with CriCodecs produced 8,743 bytes and 22 fixed-profile
  frames. It round-tripped to 24,000 silent samples but cannot fit that target.
  Runtime acceptance by `CRI_ADXI.IRX` is also still untested.
- [FFmpeg's ADX encoder](https://github.com/FFmpeg/FFmpeg/blob/master/libavcodec/adxenc.c)
  is not a direct NA2 writer. Its current source emits a fixed 36-byte,
  version-3, non-looping header and an 18-byte standard terminator. The muxer
  can backfill total sample count, but it does not supply NA2's version-4
  histories or extended loop block. Its ADPCM core could be reused only behind
  a separate NA2-aware header/footer writer.
- [vgmstream](https://github.com/vgmstream/vgmstream) is suitable for decoding
  and independent metadata checks. Its
  [AHX parser](https://github.com/vgmstream/vgmstream/blob/master/src/meta/ahx.c)
  distinguishes types `0x10` and `0x11`, while its
  [ADX parser](https://github.com/vgmstream/vgmstream/blob/master/src/meta/adx.c)
  exposes version, frame, loop, and encryption variants.
- [AFSLib](https://github.com/MaikelChan/AFSLib) and
  [AFSPacker](https://github.com/MaikelChan/AFSPacker) document configurable
  AFS alignment and attributes. AFS rebuilds are not the preferred first path:
  the maintained extraction lacks AFSPacker's variant metadata, and an
  apparently valid rebuild could still alter opaque attributes or layout.

The historical tools under `@tools/old/` are reference material, not maintained
or trusted build dependencies.

## PSS movies

### Resident selector and dormant descriptor rows

The clean resident `SLPS_258.37` used for this trace has SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`.
Its load segment maps file offset `0x100` to EE virtual address `0x00100000`.
At ELF file offset `0x300BF0` (virtual `0x00400AF0`) it contains a 12-row movie
descriptor table with a `0x2C`-byte stride. This is larger than the ten-file ISO
population:

| Index | Descriptor filename | ISO file | Statically recovered direct selector |
| ---: | --- | --- | --- |
| 0 | `logo_c.pss` | `PSS/LOGO_C.PSS` | Resident startup |
| 1 | `notice.pss` | `PSS/NOTICE.PSS` | None found |
| 2 | `opening.pss` | `PSS/OPENING.PSS` | Resident startup |
| 3 | `da2200.pss` | `PSS/DA2200.PSS` | None found |
| 4–6 | `da2255.pss` through `da3210.pss` | Corresponding shipped files | Adventure command map |
| 7–9 | `da3235.pss` through `da3999.pss` | Corresponding shipped files | Adventure command map; ETC replay map also selects 7–9 |
| 10 | `logo_cT.pss` | **Absent** | None found |
| 11 | `openingT.pss` | **Absent** | None found |

The exact T-suffixed strings are at file offsets `0x300BC8` and `0x300BD8`
(virtual `0x00400AC8` and `0x00400AD8`). Their descriptor rows begin at file
offsets `0x300DA8` and `0x300DD4` (virtual `0x00400CA8` and `0x00400CD4`). Row
10 matches row 0 field-for-field except for its filename pointer; row 11
likewise matches row 2.

Resident `FUN_001DBC30` at file offset `0x0DBD30` computes
`0x00400AF0 + movie_id * 0x2C` and stores that descriptor. It contains no
suffix-selection branch: choosing a T row would require the caller to supply
numeric ID 10 or 11. Its two wrappers and their direct callers trace as follows:

- Resident startup wrapper `FUN_001DBA00` is called at virtual `0x001DE77C`
  (file `0x0DE87C`) with ID 0 and at virtual `0x001DE7CC` (file `0x0DE8CC`)
  with ID 2.
- `ADV.BIN` SHA-256
  `AD60D9C9D11811CE57A4E64F35226EBB366D580010761A0FD1300DFE621BC34D`
  calls overlay wrapper `FUN_001DBAC0` from Ghidra address `0x007EFB78`
  (complete-file offset `0x13BCB8`, live `0x007EFBB8`). Its recovered command
  map names `DA2255`, `DA3195`, `DA3210`, `DA3235`, `DA3250`, and `DA3999` and
  maps them to IDs 4 through 9.
- `ETC.BIN` SHA-256
  `8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74`
  reaches the same wrapper through the call at Ghidra address `0x006C431C`
  (complete-file offset `0x1045C`, live `0x006C435C`). The three parsed replay
  records supply IDs 7, 8, and 9.
- No direct call to either wrapper was found in `BTL.BIN`, and no other direct
  caller was found in the resident ELF, `ADV.BIN`, or `ETC.BIN` exports.

**Observed:** `logo_cT.pss` and `openingT.pss` are real descriptor-table entries,
not omitted members of the shipped ISO inventory, and no statically recovered
direct path selects IDs 10 or 11. An exact-string search of the maintained
NUN3, NUN5, and NUN6 disassembly exports found no counterpart.

**Supported conclusion:** the two rows are dormant in the recovered direct-call
graph, so the current replacement scope remains the ten present PSS files. The
meaning of the `T` suffix and the reason these rows were retained are
unresolved; the trace is not a runtime proof against a computed indirect call.
Creating either absent file or activating its row would require separate loader
and ISO-layout research, not an ordinary same-size `FileReplacement`.

### Descriptor-authored geometry, transitions, and subtitles

The same `0x2C`-byte resident rows contain playback metadata that does not live
in the PSS. `FUN_001DBD60` copies row offsets `+0x0C..+0x18` into the movie
renderer's signed 16-bit position/size fields, calls the movie opener with the
filename at `+0x00`, and repeatedly compares the decoder's current frame from
`FUN_001052E0` with two transition pairs. The first transition begins after the
frame at `+0x1C` and uses twice the duration at `+0x20`; the second begins at or
after the frame at `+0x24` and uses twice the duration at `+0x28`. A value of
`-1` disables the corresponding startup-movie transition path.

The complete clean-row values are:

| ID / movie | `+0x0C,+0x10,+0x14,+0x18` | Early frame / duration | Late frame / duration | Resident subtitle schedule |
| --- | --- | ---: | ---: | --- |
| 0 `logo_c` | `0, 0, 512, 448` | disabled | disabled | None |
| 1 `notice` | `0, 0, 512, 448` | disabled | disabled | None |
| 2 `opening` | `0, 0, 512, 448` | disabled | disabled | None |
| 3 `da2200` | `0, 20, 512, 352` | `0 / 15` | `6123 / 20` | 21 entries, frames 1372–4634 |
| 4 `da2255` | `0, 20, 512, 352` | `1 / 15` | `3645 / 20` | 6 entries, frames 418–3219 |
| 5 `da3195` | `0, 20, 512, 352` | `1 / 15` | `2105 / 20` | 4 entries, frames 450–1082 |
| 6 `da3210` | `0, 20, 512, 352` | `0 / 15` | `741 / 20` | 4 entries, frames 121–575 |
| 7 `da3235` | `0, 20, 512, 352` | `0 / 15` | `2703 / 20` | 11 entries, frames 23–2715 |
| 8 `da3250` | `0, 20, 512, 352` | `0 / 15` | `5741 / 20` | 29 entries, frames 29–5581 |
| 9 `da3999` | `0, 0, 512, 448` | `0 / 15` | `6447 / 20` | None |
| 10 `logo_cT` | `0, 0, 512, 448` | disabled | disabled | None |
| 11 `openingT` | `0, 0, 512, 448` | disabled | disabled | None |

For IDs 3 through 8, row offset `+0x08` is 1 and the parallel pointer table at
virtual `0x00400D00` selects an embedded array of triples
`{start_frame, end_frame, text_pointer}`. The arrays terminate with
`{-1, -1, 0}`. `FUN_001DC1A0` advances through them using the decoded movie
frame, fades each entry in and out, and sends its CP932 text to
`FUN_00379350` near the bottom of the frame. ID 9 has neither the enable flag
nor an array. The schedule pointers for IDs 3 through 8 are respectively
`0x00400020`, `0x00400260`, `0x00400390`, `0x004004F0`, `0x00400790`, and
`0x004008C0`; all other pointer-table entries are null.

**Replacement consequence:** preserving the PSS byte size is only the outer
image constraint. The conservative first workflow must also preserve the
target's geometry, frame rate, frame count, and intended subtitle timing. A
semantically different replacement for `DA2200` through `DA3250` will otherwise
draw the original Japanese captions over new content. A duration-changing
replacement can also start the final transition at the old authored frame.

Supporting arbitrary duration or content therefore requires guarded resident
ELF edits alongside the PSS: update the late transition frame and either
replace the schedule/text, or disable the subtitle gate at row `+0x08` after a
runtime test. Those edits need clean-byte preconditions and are not yet a
maintained replacement feature. The static trace establishes the consumers and
data layout; it does not replace an emulator playback test.

### Observed stream contract

All ten movies are MPEG-2 program streams. Each begins with a pack header
(`0x000001BA`) and contains video PES packets (`0xE0`), private-stream audio
packets (`0xBD`), and padding packets (`0xBE`). More specifically, each file is
exactly `N * 0x4000 + 4` bytes. A 14-byte pack header starts at every `0x4000`
boundary, the first pack alone also has a 15-byte system header (`0xBB`), and
the four-byte program end code `0x000001B9` starts at the final `0x4000`
boundary. Thus the files are also `0x800`-aligned, but `0x4000` is the actual
program-stream pack lattice.

Within an ordinary pack, the header plus four PES packets fill exactly
`0x4000` bytes. Pack-leading PES packets have a `4076`-byte declared length and
the other `0x1000` slots have a `4090`-byte length. The first video packet is
shorter by the one-time system-header size. Terminal partial stream packets and
`0xBE` packets filled with `0xFF` occupy the remaining tail while preserving
the next pack boundary. A sequential length-driven parse reaches the program
end exactly for every file; no byte scan or guessed delimiter is required.

Every private audio PES payload begins with `FF A0 00 00`. Removing that
four-byte per-packet header and concatenating the remainder produces one
`SShd` chunk followed by one `SSbd` chunk. Their numeric fields are
little-endian. Every movie reports format 1, 48,000 Hz, two channels,
`0x200`-byte interleave, and loop start/end `0xFFFFFFFF`. The `SSbd` body is
signed 16-bit little-endian PCM arranged as alternating `0x200`-byte
single-channel blocks: 256 samples of channel 0, 256 samples of channel 1, and
so on. It is not sample-interleaved WAV order, ADX, or PlayStation ADPCM. Each
declared body is a whole number of `0x400`-byte stereo superblocks and therefore
contains `body_bytes / 4` samples per channel.

| Movie | Total bytes | Video sequence | Header aspect | Sequence bit rate | PCM body bytes |
| --- | ---: | --- | --- | ---: | ---: |
| `DA2200.PSS` | 142,704,644 | 512×352 at 30000/1001 fps | 4:3 | 4,000,000 | 39,392,256 |
| `DA2255.PSS` | 100,401,156 | 512×352 at 30000/1001 fps | 4:3 | 5,000,000 | 23,485,440 |
| `DA3195.PSS` | 49,381,380 | 512×352 at 30000/1001 fps | 4:3 | 4,000,000 | 13,650,944 |
| `DA3210.PSS` | 17,743,876 | 512×352 at 30000/1001 fps | 4:3 | 4,000,000 | 4,908,032 |
| `DA3235.PSS` | 63,307,780 | 512×352 at 30000/1001 fps | 4:3 | 4,000,000 | 17,482,752 |
| `DA3250.PSS` | 134,266,884 | 512×352 at 30000/1001 fps | 4:3 | 4,000,000 | 37,066,752 |
| `DA3999.PSS` | 150,224,900 | 512×448 at 30000/1001 fps | 1:1 | 4,000,000 | 41,467,904 |
| `LOGO_C.PSS` | 2,179,076 | 512×448 at 30000/1001 fps | 4:3 | 4,000,000 | 672,768 |
| `NOTICE.PSS` | 4,931,588 | 512×448 at 30000/1001 fps | 4:3 | 5,000,000 | 1,152,000 |
| `OPENING.PSS` | 72,974,340 | 512×448 at 30000/1001 fps | 1:1 | 5,000,000 | 17,059,840 |

“Header aspect” is the MPEG sequence field, not a conclusion about how the game
ultimately displays the frame. A replacement should copy the selected target's
value unless a runtime test establishes another supported value.

`DA2200.PSS` has one original-file exception: its `SSbd` declares 39,392,256
body bytes, but concatenating all private-stream payloads yields the 40 bytes of
chunk headers plus only 39,392,230 body bytes. It is short by 26 bytes. The
physical tail is already zero, so the absent portion would only extend silence,
but the mismatch is real and must not be “repaired” accidentally. The other
nine files provide exactly `40 + declared_body_bytes` logical audio bytes.

The video elementary-stream and resident end-timing census is:

| Movie | `0x4000` packs | Video ES bytes | Pictures / GOPs | Resident late transition |
| --- | ---: | ---: | ---: | --- |
| `DA2200.PSS` | 8,710 | 102,474,544 | 6,144 / 410 | frame 6,123; 21 pictures before end |
| `DA2255.PSS` | 6,128 | 76,326,381 | 3,661 / 245 | frame 3,645; 16 pictures before end |
| `DA3195.PSS` | 3,014 | 35,441,915 | 2,126 / 142 | frame 2,105; 21 pictures before end |
| `DA3210.PSS` | 1,083 | 12,719,743 | 762 / 51 | frame 741; 21 pictures before end |
| `DA3235.PSS` | 3,864 | 45,450,345 | 2,724 / 182 | frame 2,703; 21 pictures before end |
| `DA3250.PSS` | 8,195 | 96,418,584 | 5,781 / 386 | frame 5,741; 40 pictures before end |
| `DA3999.PSS` | 9,169 | 107,879,863 | 6,468 / 432 | frame 6,447; 21 pictures before end |
| `LOGO_C.PSS` | 133 | 1,475,181 | 90 / 7 | Disabled |
| `NOTICE.PSS` | 301 | 3,731,602 | 180 / 13 | Disabled |
| `OPENING.PSS` | 4,454 | 55,491,310 | 2,662 / 178 | Disabled |

All elementary streams end exactly with MPEG sequence-end code `0x000001B7`.
They use MPEG-2 Main Profile at Main Level (`profile_and_level_indication`
`0x48`), 4:2:0 chroma, default quantization matrices, VBV size value 112, and
GOPs of at most 15 pictures. A full 15-picture GOP contains one I, four P, and
ten B pictures. Sequence, sequence-extension, and GOP headers repeat at every
GOP. The first GOP is closed and no GOP has `broken_link`; `DA2255` has one
additional closed GOP.

Nine movies declare an interlaced sequence and frame pictures with
`top_field_first = 0`, `repeat_first_field = 0`, `progressive_frame = 0`,
`frame_pred_frame_dct = 0`, and `alternate_scan = 1`. `NOTICE.PSS` is the sole
exception: both its sequence and pictures are progressive, with
`frame_pred_frame_dct = 1`, `chroma_420_type = 1`, and the same alternate scan.

PES timing is authored, not a fixed file-offset decoration. Every video PES has
the optional-header introducer `0x83` and a ten-byte optional-header area,
except for the initial packet's 13-byte area. Packets that begin a relevant
access unit carry PTS only for B pictures or PTS plus DTS for I/P pictures;
continuation packets carry neither. In coded order, video PTS deltas therefore
include `-6006`, `+3003`, and `+12012` ticks. Audio carries a PTS in every PES,
normally advancing by 1,902–1,910 ticks. Pack SCR values also include repeated
values, and four small backwards steps exist across `DA2255`, `DA3210`, and
`DA3999`; requiring simple monotonicity would reject clean originals.

The main `program_mux_rate` is 13,840 for the 4 Mbit/s targets and 16,340 for
the 5 Mbit/s targets, exactly matching the nominal video rate plus 1.536 Mbit/s
PCM in MPEG's 50-byte/s units. A small number of audio-only packs use 3,840.
The initial system-header rate bound changes with the same two target classes.

Audio timestamps have an exact byte-counter relationship in all ten clean
files. Let `logical_byte_offset[i]` be the number of concatenated private-audio
bytes before packet `i`, after removing each packet's four-byte `FF A0 00 00`
subheader but including the 40 bytes of `SShd`/`SSbd` headers. Then:

```text
audio_pts[i] = audio_pts[0]
             + floor((logical_byte_offset[i] * 15 + phase) / 32)
```

Each file has one fixed integer `phase`: 27 for `DA2200`, 13 for `DA2255`, 13
for `DA3195`, 30 for `DA3210`, 25 for `DA3235`, 29 for `DA3250`, 21 for
`DA3999`, 26 for `LOGO_C`, 5 for `NOTICE`, and 26 for `OPENING`. The factor
`15/32` is exactly 90,000 timestamp ticks divided by the 192,000 logical PCM
bytes per second. This formula reproduces every audio PES PTS exactly, including
the otherwise surprising treatment of the 40 chunk-header bytes as part of the
counter. It allows a writer to validate regenerated timestamps without
mistaking the observed 1,902–1,910-tick steps for arbitrary jitter.

For all seven `DA` movies and `OPENING`, the first audio PTS is 6,006 ticks
(two nominal video frames) before the first video PTS; `LOGO_C` and `NOTICE`
start both streams at the same PTS. PCM duration is not simply video picture
count divided by frame rate: the seven `DA` audio bodies extend 0.137–0.166
seconds past that duration, while `LOGO_C` extends 0.501 seconds, `NOTICE` is
0.006 seconds shorter, and `OPENING` extends 0.031 seconds. A replacement should
therefore match the target PCM sample count and initial stream offset directly,
not derive either from video duration.

### Replacement paths

**Path 1 — packet-skeleton rewrite (preferred first experiment):** preserve an
original movie's `0x4000` pack lattice, stream-slot order, pack SCR values,
pack/system rate fields, and total size. Encode an MPEG-2 elementary video
stream with the target's dimensions, frame rate, aspect, coding flags, GOP
shape, picture count, and rate ceiling. Prepare signed 16-bit stereo PCM at
48,000 Hz, deinterleave it into alternating `0x200`-byte channel blocks, and
match the target's declared sample count.

Repacketizing must attach PTS/DTS to the new elementary stream's actual picture
starts; retaining timestamp bytes at their old file offsets is unsafe when
compressed picture sizes differ. The target timestamp sequence is reusable
only when the replacement retains the corresponding picture/GOP order. Audio
PTS and slot timing can remain target-matched when its sample count is exact.
Convert exhausted terminal stream capacity to valid `0xBE` padding, splitting
the last stream packet within its pack if needed, and retain the final program
end code. The replacement must fail if either stream cannot fit. For
`DA2200.PSS`, either reproduce the original 26-byte zero-tail omission or make
an explicitly tested terminal-packet adjustment. This path still needs a
purpose-built parser/writer and runtime proof.

**Path 2 — constrained full mux:** generate a PS2-style stream with the same
stream IDs, `SShd`/`SSbd` PCM contract, `0x4000` pack lattice, disc alignment,
timing behavior, padding, and exact outer size. This supports more extensive
edits but has more unknowns. No maintained open-source tool was found that was
both a complete PSS video/audio creator and directly suitable for this
repository. For example,
[PssMux](https://github.com/wagrenier/PssMux) injects audio from one PSS into
another rather than creating the full target stream, while
[PSSpectrum](https://github.com/Ailyth99/PSSpectrum) delegates creation to the
proprietary PS2STR tool. Neither closes the maintained muxer gap.
[PS2-PSS-Tools](https://github.com/Silentwarior112/PS2-PSS-Tools) likewise
documents a PS2STR-based workflow rather than providing an open muxer, and its
published recipe targets compressed PS2 ADPCM audio rather than NA2's observed
48 kHz `SShd`/`SSbd` PCM stream.

Appending arbitrary bytes to reach the original file length is not an accepted
solution. Padding must remain syntactically valid and precede the program end
code. If a valid stream is larger than the target, lower its bit rate or shorten
its content; ISO/UDF relocation or a variable-size replacement pipeline is a
separate project mechanism and is outside this research task.

## Validation required before enabling replacement

### Audio

1. Decode the generated AHX/ADX independently and compare codec type, channel
   count, sample rate, sample count, version, loop fields, and encryption state
   with the selected target contract.
2. Parse the generated AFS recursively and prove that all offsets, null indices,
   non-target payloads, attributes rows, alignment, and outer length are
   unchanged.
3. Assemble from a clean base and verify the generated ISO record is still at
   the guarded expected offset and size.
4. Exercise the exact cue in PCSX2 through completion and repetition; check for
   silence, truncation, pitch/rate errors, corruption of adjacent cues, and
   archive-load failures.

### Movies

1. Parse every pack/PES packet; verify legal lengths, marker bits, stream IDs,
   target-matched SCR/PTS/DTS cadence, every `0x4000` boundary, final program
   end, and exact file length. Do not impose PTS or SCR monotonicity that the
   clean targets themselves do not have.
2. Decode the complete generated movie independently and check frame count,
   GOP/picture flags, PCM duration and block interleave, A/V synchronization,
   and absence of decoder errors.
3. Test startup movies and story-triggered movies separately in PCSX2, including
   normal completion and skip behavior. Real-hardware playback remains useful
   for confirming disc-streaming bandwidth.

## Remaining unknowns

- Which encoder or CriCodecs change can reproduce NA2's adaptive type-`0x11`
  allocations and timing closely enough to fit the target slot and satisfy the
  bundled CRI driver. CriCodecs 1.2.0's fixed allocation and extra 480-sample
  pre-roll do not cover the full corpus.
- The exact writer-side derivation and runtime significance of ADX version-4
  predictor histories and the extended-header field at `0x20`; CriCodecs 1.2.0
  currently zeroes both in inspected cases.
- The exact timestamp-generation policy and decoder tolerance needed when a
  newly encoded stream's compressed picture sizes move access-unit boundaries.
