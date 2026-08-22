# NA2 Game File Reference

This is the canonical human-readable map of the files on the original NA2 disc
and the major families nested inside them. Read it before investigating a game
file and update it when evidence improves a role or resolves an unknown.

This document explains semantics. The
[media-layout inventory index](media/README.md) owns the exact structural
inventories and their provenance. [`analysis_inventory.tsv`](analysis_inventory.tsv)
owns analysis level, size, evidence source, and confidence for important
artifacts.

## Evidence labels

- **Confirmed**: established by a signature, parser, executable reference,
  static analysis, or runtime evidence.
- **Supported**: multiple clues agree, but the exact behavior has not been
  traced or observed end to end.
- **Filename inference**: the role follows from the name and surrounding file
  family only. Treat it as a search lead, not a fact.
- **Unknown**: the format or placement may be known, but the purpose is not.

The shallow inspection recorded here was performed on 2026-07-21 against the
read-only `@source_na2/` extraction, with focused audio/video header research
updated on 2026-08-20. It inspected headers and readable strings, parsed AFS,
AHX/ADX, and MPEG/PSS metadata, searched the boot ELF and overlays for file
references, compared same-named NA2/NUN5 files, and reused the existing Ghidra
and patch evidence. No source file was modified.

The codec classifications follow the local headers and are cross-checked
against vgmstream's [AHX](https://github.com/vgmstream/vgmstream/blob/master/src/meta/ahx.c)
and [ADX](https://github.com/vgmstream/vgmstream/blob/master/src/meta/adx.c)
parsers. Game-specific role assignments below come from the local archive
populations and executable evidence, not from those generic sources. See
[Audio and video replacement](audio_video_replacement.md) for exact profiles,
container constraints, candidate toolchains, and the proposed replacement
workflows.

## Storage hierarchy

```text
NA2 ISO
├── boot/configuration files
├── PRG/                 EE overlays loaded by the boot ELF
├── MODULES/             IOP runtime and device/audio modules
├── PSS/                 multiplexed full-motion videos
└── DATA/
    ├── fixed resources and sound banks
    ├── four AFS audio archives
    └── DATA.CVM         encrypted ROFS wrapper around a resource ISO
        └── 2,310 CCS resources, GZLIST.TXT, and ICON.BIN
```

Archives are recursively extracted beside themselves as `<archive>.files`.
Those directories are extraction views, not additional disc files.

## Root files

| Path | Role | Evidence and limits |
| --- | --- | --- |
| `SYSTEM.CNF` | PS2 boot configuration | **Confirmed.** Plain text selects `SLPS_258.37`, version `1.00`, and NTSC video mode. |
| `SLPS_258.37` | Resident Emotion Engine executable | **Confirmed.** 32-bit little-endian MIPS ELF, entry point `0x00100008`; owns startup and shared game systems and loads the on-demand overlays/resources. It is the only full-program Ghidra target. |
| `FLIST.DIR` | Startup file-location cache list | **Confirmed.** Lists the four AFS archives, `DATA.CVM`, and the three PRG overlays. The resident table has 40 slots and 32-character normalized-name capacity; the clean eight-line file leaves 32 slots, while longer names can overrun a slot. The boot ELF caches disc locations, and ordinary explicit-device lookup still handles files not listed here. |
| `OUT1M.BIN` | One-MiB zero-filled placeholder | **Confirmed content; unknown purpose.** Every byte is zero and the file is identical in NUN5. It is probably reserved/padding media space, but no loader or allocation role has been proven. |

## `DATA/`: fonts, graphics, sound, and archives

| Path | Role | Evidence and limits |
| --- | --- | --- |
| `DATA/GF4.BIN` | GF4 selectable font raster | **Confirmed.** The resident type-1 parser loads its two raster descriptors, and renderer mode 1 selects it together with `GF4C.BIN`. Font experiments and current Localization patches identify its glyph cells and metrics. NA2 is much larger than NUN5 because their GF4 layouts differ. |
| `DATA/GF4C.BIN` | GF4 16-entry RGBA CLUT | **Confirmed.** The resident type-2 parser reads its 32-byte name followed by 64 bytes of palette entries, constructs the render-side CLUT object, and installs it whenever GF4 is selected. Whole-file NUN5 palette substitution remains unsafe for NA2 raster data. |
| `DATA/GRF4.BIN` | 8×8 ruby/annotation glyph atlas | **Confirmed.** Its type-1 descriptor contains 167 4-bpp glyph rasters and a 334-record two-byte-code map. The resident string renderer uses it only for the annotation arm of pipe-delimited inline markup, centering the small glyphs over or beside the base span. It is byte-identical to NUN5. |
| `DATA/SF1.BIN` | SF1 selectable font raster | **Confirmed.** The same resident type-1 parser loads its two raster descriptors, and renderer mode 0 selects it together with `SF1C.BIN`. It is byte-identical to NUN5. |
| `DATA/SF1C.BIN` | SF1 16-entry RGBA CLUT | **Confirmed.** It has the same type-2 name-plus-64-byte-palette layout and render-object construction as GF4C, and is selected with SF1. It is byte-identical to NUN5. |
| `DATA/SNDDATA.BIN` | Sony-style sound bank/program data | **Confirmed at shallow format level.** It contains `IECS`-marked version, header, VAG, sample, set, and program sections. `SNDBASE.IRX` and the boot ELF reference it. It is data, not executable code, and is byte-identical to NUN5. |
| `DATA/PLVOICE.AFS` | Short player/battle voice clips | **Supported by contents.** Its nested archives yield 2,232 mono 24-kHz AHX type-`0x11` clips; median duration is 0.922 s and the longest is 6.309 s. The short vocal population supports the player/battle-call role implied by the filename. It is byte-identical to NUN5. |
| `DATA/RPGVOICE.AFS` | Adventure/RPG dialogue | **Supported by contents.** Its nested archives yield 5,597 mono AHX clips (914 type `0x10`, 4,683 type `0x11`); all but one are 24 kHz. Median duration is 3.104 s and the longest is 14.351 s. The much longer voice population supports dialogue rather than battle barks. It is byte-identical to NUN5. |
| `DATA/SOUND.AFS` | General sound effects and longer audio cues | **Supported by contents.** Its nested archives yield 1,239 mono AHX clips and 73 stereo ADX type-`0x03` clips, all 24 kHz, ranging from 0.289 s to 160.910 s. The mixture fits effects plus longer music/cue material; the exact bank-to-system mapping is not catalogued. It is byte-identical to NUN5. |
| `DATA/STREAM.AFS` | Streamed stereo audio cues | **Supported by contents.** It yields 173 stereo 24-kHz ADX type-`0x03` files, 6.367–40.233 s long with a 13.333 s median. The uniform stereo, longer-form population distinguishes it from voices and ordinary effects. It is byte-identical to NUN5. |
| `DATA/DATA.CVM` | Encrypted resource filesystem | **Confirmed.** `CVMH`/ROFS container built with ROFSBLD 1.52; password `cc2fuku`. Startup mounts it as `VOL`, synchronously loads the root directory, then asynchronously preloads all child-directory metadata before clearing the startup barrier. Splitting it yields a fixed-capacity ISO containing 2,310 CCS resources, `GZLIST.TXT`, and `ICON.BIN`. |

The AFS counts above describe successfully parsed non-empty AHX/ADX files across
all nested AFS levels. The inventory's extracted `.adx` suffix is a shallow CRI
signature classification and must not be treated as the codec. The
[`media/afs_members.tsv`](media/afs_members.tsv) inventory remains authoritative
for exact container, index, offset, and size records.

## `MODULES/`: IOP runtime components

| Path | Role | Evidence and limits |
| --- | --- | --- |
| `MODULES/IOPRP300.IMG` | Base IOP runtime image | **Confirmed.** `RESET`/`ROMDIR` image containing standard services including `SYSMEM`, `LOADCORE`, `SIFCMD`, `SIFMAN`, `THREADMAN`, `MODLOAD`, `FILEIO`, `CDVDMAN`, `CDVDFSV`, and `LOADFILE`. Select an embedded module rather than disassembling the image as one program. |
| `MODULES/CRI_ADXI.IRX` | CRI ADX playback driver | **Confirmed.** IOP IRX whose strings identify `CRI_ADX_Driver`, SPU2 initialization, and CRI ADX Driver 9.69 dated 2005-11-22. It provides the low-level ADX playback side of the audio system. |
| `MODULES/SNDBASE.IRX` | Game sound-control layer | **Confirmed at subsystem level.** IOP IRX referencing MIDI, hybrid synthesis, CD/DVD access, sound effects, seeking, and `BGM2` playback. Exact command protocol and ownership boundaries require targeted disassembly. |
| `MODULES/MODULES.BIN` | IOP peripheral/support executable | **Confirmed format; supported subsystem role.** Despite its `.BIN` suffix it is an IOP ELF/IRX. Embedded names identify or reference SIO2, controller (`padman`), memory-card (`mcman`/`mcserv`), CD/DVD, and sound-related modules. Whether those components are bundled code or dependencies, and its precise loading mechanism, need targeted analysis. |

All four files are byte-identical between NA2 and NUN5. The three executable
IRX inputs already have maintained shared Ghidra baselines; see
[`game-file analysis workflow`](analysis.md).

## `PRG/`: on-demand Emotion Engine overlays

All three files use the `MWo3` overlay format and contain executable MIPS code
plus local data. They are loaded and unloaded on demand into reusable EE memory;
they are not ordinary data files and must not receive unguarded fixed-address
PNACH writes.

| Path | Role | Evidence and limits |
| --- | --- | --- |
| `PRG/ADV.BIN` | Adventure/story-mode overlay | **Supported strongly.** Internal name `ADV_product.bin`; the corresponding resource tree contains adventure characters, events, players, skills, and stages. Use targeted analysis for adventure-mode behavior. |
| `PRG/BTL.BIN` | Battle and practice overlay | **Confirmed at subsystem level.** Internal name `BTL_product.bin`; existing runtime/static work locates battle input, practice settings, combat UI, and battle logic here. |
| `PRG/ETC.BIN` | Frontend/extras overlay | **Confirmed at subsystem level.** Internal name `ETC_product.bin`; existing work locates Home, Collection, save/load menu, and related UI behavior here. Readable resource names include `home.ccs` and Home animation/texture identifiers. |

The NA2 overlays differ structurally from their NUN5 equivalents. Compare
behaviors and functions deliberately; do not treat them as interchangeable
whole-file donors.

## `PSS/`: full-motion video

All ten files are MPEG program streams with an MPEG video stream (`0xE0`), a
private audio stream (`0xBD`), and padding (`0xBE`). They run at approximately
29.97 fps. The private substream is `0xA0` `SShd`/`SSbd` audio: uncompressed
signed 16-bit stereo PCM at 48 kHz with a `0x200` interleave field. Durations
below use the audio PTS span because it is slightly longer than the video span.
The exact profiles and replacement constraints are documented in
[Audio and video replacement](audio_video_replacement.md).

The resident movie player is clocked separately from ordinary 30 Hz gameplay.
FUN_001057B0 saves the renderer's current VBlank threshold, forces the
threshold to one while its MPEG demux/video-decoder and audio-streaming threads
run, and FUN_00105320 restores the saved threshold during cleanup. Therefore a
gameplay change from two VBlanks per scheduler update to one does not require
halving PSS video or audio speed: clean playback already presents through the
one-VBlank movie path. See the
[60 FPS timing research](../../gameplay/framerate.md#prerecorded-pss-video-and-video-speed)
for the complete control-flow evidence and validation requirements.

The boot ELF contains `NOTICE`, `OPENING`, and all seven `DA####` identifiers in
one movie-name table beside cutscene/audio script commands. This confirms that
the numbered files are game-controlled full-motion sequences, but it does not
identify their exact story scenes. That requires visual review.

| Path | Video | Approx. duration | Semantic role |
| --- | ---: | ---: | --- |
| `PSS/LOGO_C.PSS` | 512×448 | 3.50 s | **Filename inference:** short company/logo bumper. |
| `PSS/NOTICE.PSS` | 512×448 | 6.00 s | **Filename inference:** startup notice/warning screen. |
| `PSS/OPENING.PSS` | 512×448 | 88.85 s | **Supported:** opening movie. |
| `PSS/DA2200.PSS` | 512×352 | 205.15 s | **Confirmed movie; exact scene unknown.** Numbered cutscene identifier `DA2200`. |
| `PSS/DA2255.PSS` | 512×352 | 122.32 s | **Confirmed movie; exact scene unknown.** Numbered cutscene identifier `DA2255`. |
| `PSS/DA3195.PSS` | 512×352 | 71.09 s | **Confirmed movie; exact scene unknown.** Numbered cutscene identifier `DA3195`. |
| `PSS/DA3210.PSS` | 512×352 | 25.56 s | **Confirmed movie; exact scene unknown.** Numbered cutscene identifier `DA3210`. |
| `PSS/DA3235.PSS` | 512×352 | 91.04 s | **Confirmed movie; exact scene unknown.** Numbered cutscene identifier `DA3235`. |
| `PSS/DA3250.PSS` | 512×352 | 193.05 s | **Confirmed movie; exact scene unknown.** Numbered cutscene identifier `DA3250`. |
| `PSS/DA3999.PSS` | 512×448 | 215.96 s | **Confirmed movie; exact scene unknown.** Numbered cutscene identifier `DA3999`. |

The resident movie-descriptor table has two additional rows, indices 10 and
11, whose exact strings are `logo_cT.pss` and `openingT.pss`. **Confirmed
static status:** neither file exists in the ISO, and the recovered resident,
ADV, and ETC direct callers select other numeric rows rather than applying a
runtime suffix. These are dormant executable-table entries, not missing members
of the file inventory. Their suffix meaning and retention reason remain
unresolved; see the [selector trace](audio_video_replacement.md#resident-selector-and-dormant-descriptor-rows).

Several PSS files have the same byte size as their NUN5 counterpart but
different contents; others differ in size, and NUN5 lacks `NOTICE.PSS`. The
names alone are therefore not sufficient to assume cross-game video parity.

## Inside `DATA.CVM`

The resident mount, cache, path-routing, sector-I/O, and compression-manifest
contracts are documented in [Resident file and archive services](runtime_services.md).
Generic container/object lookup and lifetime are documented in
[Resident CCS runtime](ccs_runtime.md); confirmed numeric parser-tag identities
are separated into [Resident CCS object-type identities](ccs_object_types.md).

### File families

| Family | Role | Evidence and limits |
| --- | --- | --- |
| `*.CCS` (2,310 files) | CC2 resource containers | **Confirmed.** CCS containers hold named objects such as textures/palettes, models, and animations. Individual containers can combine several resource kinds. Use structural CCS parsing rather than treating them as flat images or text files. |
| `GZLIST.TXT` | Directory-capacity and gzip-size manifest | **Confirmed.** Its first section sizes the resident ROFS directory tree. In each file row, the first numeric value is discarded and the second is retained as the decompressed output size and compression marker; actual compressed read length comes from ROFS. It is metadata, not a semantic asset index. |
| `ICON.BIN` | PS2 save icon payload | **Confirmed.** The resident save path sector-reads the 61,440-byte member, writes its first `0xE920` bytes as `icon00.icn`, and names that file in all three `icon.sys` icon slots. The remaining `0x6E0` bytes are `0xFF` sector padding; internal ICN visual/animation fields remain undecoded. |

### CCS directory map

These labels are intentionally shallow. Filename-driven meanings remain
inferences until a resource is opened or referenced by code.

| Directory | Shallow role |
| --- | --- |
| `3BSC/` | **Unknown character-coded family.** Nine `3*3BSC.CCS` resources; exact acronym and use unresolved. |
| `3EYE/` | **Confirmed in part:** character-specific battle and Victory resources. NA2 and NUN5 contain the same 78 `3???3PCT.CCS` family members; 74 contain one `TEX_name` Victory visual, while four contain no name visual in either game. A 61-member subset also supplies all 72 ordinary awakening-name textures. `ENDDEMO.CCS` supplies the shared Victory background atlas and `WINNER` emblem. Files also occur in paired `3EYE` names whose exact object use remains unresolved. |
| `ADV/` | **Supported:** adventure-mode resources. Subfolders separate `CHAR`, `EVENT`, `PLAYER`, `SKILL`, and `STAGE`. |
| `BUDDY/` | **Filename inference:** support/buddy character resources. |
| `CMN/` | **Supported:** shared/common battle resources including body data, effects, gauge, particles, and shading. |
| `CUTIN/` | **Supported by names:** character-specific cut-in resources. |
| `HOME/` | **Confirmed subsystem:** Home/hub resources used by the ETC overlay. |
| `LOADING/` | **Supported by names:** numbered loading-screen resources. |
| `MODENAME/` | **Supported by names:** mode-name graphics/resources. |
| `PL/` | **Supported:** playable-character body/resources; `PL/MODEL/` contains a parallel model family. |
| `PUPPET/` | **Supported by names:** puppet-character resources. |
| `SCENE/` | **Supported by names:** scene/cutscene resources, including many character-coded entries. |
| `STAGE/` | **Supported by names:** numbered stage resources. |
| `STR/` | **Supported as story/event resources; acronym unresolved.** Contains `ATTENTION.CCS` and large numbered `D##_##`/`D##_##E` families. |

Thirty-one CCS files also live at the inner ISO root. Their names provide a
useful first routing layer:

- combat/UI: `BATTLEGAUGE`, `PRAC`, `SPBATTLE`, `VS`, and `OUGI`;
- selection/settings: `CHARSEL1`, `MAPSEL1`, `MODESEL1`, `OPTION`, and
  `SETTING`;
- hub/extras: `HOME`;
- startup/title: `CONTINUE`, `LOGO`, `LOGO_T`, `TITLE`, `TITLE_P`, `TITLE_T`,
  and `TITLE_T2`;
- unresolved or only filename-inferred: `DBGMENU`, `NAKOKUTI`, `NINMU`,
  `N_RASH` through `N_RASH5`, `STRMCMN`, and `XNINKA`.

Do not infer that a CCS file contains only the screen named by its filename.
For example, existing UI work has shown that some visible layout and label
behavior is owned by an overlay or the boot ELF while the CCS supplies the
associated textures/models.

## Updating this reference

When new evidence appears:

1. Update the relevant role and evidence label here.
2. Keep exact paths, offsets, and sizes in the media TSV inventories.
3. Keep disassembly scope and cohort metadata in
   `analysis_inventory.tsv` and `analysis.md`.
4. Put an unresolved interpretation in an explicitly labelled section of the
   relevant domain-owned knowledge document; promote it here only when the
   evidence supports the stated confidence.
5. Link detailed subsystem findings rather than duplicating their complete
   analysis in this overview.
