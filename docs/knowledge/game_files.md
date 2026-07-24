# NA2 Game File Reference

This is the canonical human-readable map of the files on the original NA2 disc
and the major families nested inside them. Read it before investigating a game
file and update it when evidence improves a role or resolves an unknown.

This document explains semantics. It does not duplicate the exact structural
inventories:

- [`media/na2_iso9660.tsv`](media/na2_iso9660.tsv): every outer-disc path,
  extent, byte offset, and size;
- [`media/data_cvm_iso9660.tsv`](media/data_cvm_iso9660.tsv): every path in the
  decrypted `DATA.CVM` ISO payload;
- [`media/afs_members.tsv`](media/afs_members.tsv): every extracted AFS member;
- [`binary_analysis_inventory.tsv`](binary_analysis_inventory.tsv): analysis
  level, size, evidence source, and confidence for important artifacts.

## Evidence labels

- **Confirmed**: established by a signature, parser, executable reference,
  static analysis, or runtime evidence.
- **Supported**: multiple clues agree, but the exact behavior has not been
  traced or observed end to end.
- **Filename inference**: the role follows from the name and surrounding file
  family only. Treat it as a search lead, not a fact.
- **Unknown**: the format or placement may be known, but the purpose is not.

The shallow inspection recorded here was performed on 2026-07-21 against the
read-only `@source_na2/` extraction. It inspected headers and readable strings,
parsed AFS/ADX and MPEG/PSS metadata, searched the boot ELF and overlays for
file references, compared same-named NA2/NUN5 files, and reused the existing
Ghidra and patch evidence. No source file was modified.

The ADX metadata parser follows the channel/sample-rate fields documented by
the [FFmpeg CRI ADX demuxer](https://ffmpeg.org/doxygen/trunk/libavformat_2adxdec_8c_source.html);
[CRIWARE](https://game.criware.com/) independently identifies ADX as its game
audio middleware. Game-specific role assignments below come from the local
archive populations and executable evidence, not from those generic sources.

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
| `FLIST.DIR` | Startup file-location cache list | **Confirmed.** Lists the four AFS archives, `DATA.CVM`, and the three PRG overlays. The boot ELF resolves these paths early and caches their disc locations; ordinary filesystem lookup still handles files not listed here. |
| `OUT1M.BIN` | One-MiB zero-filled placeholder | **Confirmed content; unknown purpose.** Every byte is zero and the file is identical in NUN5. It is probably reserved/padding media space, but no loader or allocation role has been proven. |

## `DATA/`: fonts, graphics, sound, and archives

| Path | Role | Evidence and limits |
| --- | --- | --- |
| `DATA/GF4.BIN` | Main glyph atlas and font data | **Confirmed.** Font experiments and the current Localization font patches identify its cell bitmap data and descriptors. NA2 is much larger than NUN5 because the two games use different font layouts. |
| `DATA/GF4C.BIN` | GF4 companion color/palette table | **Supported.** The 104-byte structured companion changes how GF4 pixels are interpreted; unsafe palette-swap tests confirm that it is coupled to GF4. Its complete field semantics remain unknown. |
| `DATA/GRF4.BIN` | GF4-family graphics support resource | **Supported format family; exact function unknown.** Its header follows the same named resource pattern, and it is byte-identical to NUN5. No executable or glyph-table role has been isolated. |
| `DATA/SF1.BIN` | Secondary font/graphics resource | **Supported format family; exact function unknown.** It uses the same named resource envelope as GF4, is byte-identical to NUN5, and has no executable signature. |
| `DATA/SF1C.BIN` | SF1 companion table | **Supported.** It is a 104-byte companion with the same envelope as GF4C and is byte-identical to NUN5. Individual fields remain unresolved. |
| `DATA/SNDDATA.BIN` | Sony-style sound bank/program data | **Confirmed at shallow format level.** It contains `IECS`-marked version, header, VAG, sample, set, and program sections. `SNDBASE.IRX` and the boot ELF reference it. It is data, not executable code, and is byte-identical to NUN5. |
| `DATA/PLVOICE.AFS` | Short player/battle voice clips | **Supported by contents.** Its nested archives yield 2,232 mono 24-kHz ADX clips; median duration is 0.922 s and the longest is 6.309 s. The short vocal population supports the player/battle-call role implied by the filename. It is byte-identical to NUN5. |
| `DATA/RPGVOICE.AFS` | Adventure/RPG dialogue | **Supported by contents.** Its nested archives yield 5,597 mono ADX clips; median duration is 3.104 s and the longest is 14.351 s. The much longer voice population supports dialogue rather than battle barks. It is byte-identical to NUN5. |
| `DATA/SOUND.AFS` | General sound effects and longer audio cues | **Supported by contents.** Its nested archives yield 1,312 ADX files: 1,239 mono and 73 stereo, all 24 kHz, ranging from 0.289 s to 160.910 s. The mixture fits effects plus longer music/cue material; the exact bank-to-system mapping is not catalogued. It is byte-identical to NUN5. |
| `DATA/STREAM.AFS` | Streamed stereo audio cues | **Supported by contents.** It yields 173 stereo 24-kHz ADX files, 6.367–40.233 s long with a 13.333 s median. The uniform stereo, longer-form population distinguishes it from voices and ordinary effects. It is byte-identical to NUN5. |
| `DATA/DATA.CVM` | Encrypted resource filesystem | **Confirmed.** `CVMH`/ROFS container built with ROFSBLD 1.52; password `cc2fuku`. Splitting it yields a fixed-capacity ISO containing 2,310 CCS resources, `GZLIST.TXT`, and `ICON.BIN`. |

The AFS counts above describe successfully parsed non-empty ADX files across
all nested AFS levels. `media/afs_members.tsv` remains authoritative for exact
container, index, offset, and size records.

## `MODULES/`: IOP runtime components

| Path | Role | Evidence and limits |
| --- | --- | --- |
| `MODULES/IOPRP300.IMG` | Base IOP runtime image | **Confirmed.** `RESET`/`ROMDIR` image containing standard services including `SYSMEM`, `LOADCORE`, `SIFCMD`, `SIFMAN`, `THREADMAN`, `MODLOAD`, `FILEIO`, `CDVDMAN`, `CDVDFSV`, and `LOADFILE`. Select an embedded module rather than disassembling the image as one program. |
| `MODULES/CRI_ADXI.IRX` | CRI ADX playback driver | **Confirmed.** IOP IRX whose strings identify `CRI_ADX_Driver`, SPU2 initialization, and CRI ADX Driver 9.69 dated 2005-11-22. It provides the low-level ADX playback side of the audio system. |
| `MODULES/SNDBASE.IRX` | Game sound-control layer | **Confirmed at subsystem level.** IOP IRX referencing MIDI, hybrid synthesis, CD/DVD access, sound effects, seeking, and `BGM2` playback. Exact command protocol and ownership boundaries require targeted disassembly. |
| `MODULES/MODULES.BIN` | IOP peripheral/support executable | **Confirmed format; supported subsystem role.** Despite its `.BIN` suffix it is an IOP ELF/IRX. Embedded names identify or reference SIO2, controller (`padman`), memory-card (`mcman`/`mcserv`), CD/DVD, and sound-related modules. Whether those components are bundled code or dependencies, and its precise loading mechanism, need targeted analysis. |

All four files are byte-identical between NA2 and NUN5. The three executable
IRX inputs already have maintained shared Ghidra baselines; see
[`binary_analysis.md`](binary_analysis.md).

## `PRG/`: on-demand Emotion Engine overlays

All three files use the `MWo3` overlay format and contain executable MIPS code
plus local data. They are loaded and unloaded on demand into reusable EE memory;
they are not ordinary data files and must not receive unguarded fixed-address
PNACH writes.

| Path | Role | Evidence and limits |
| --- | --- | --- |
| `PRG/ADV.BIN` | Adventure/story-mode overlay | **Supported strongly.** Internal name `ADV_product.bin`; the corresponding resource tree contains adventure characters, events, players, skills, and stages. Use targeted analysis for adventure-mode behavior. |
| `PRG/BTL.BIN` | Battle and practice overlay | **Confirmed at subsystem level.** Internal name `BTL_product.bin`; existing runtime/static work locates battle input, practice settings, combat UI, and battle logic here. |
| `PRG/ETC.BIN` | Frontend/extras overlay | **Confirmed at subsystem level.** Internal name `ETC_product.bin`; existing work locates Home, Shop, Collection, save/load menu, and related UI behavior here. Readable resource names include `home.ccs` and Home animation/texture identifiers. |

The NA2 overlays differ structurally from their NUN5 equivalents. Compare
behaviors and functions deliberately; do not treat them as interchangeable
whole-file donors.

## `PSS/`: full-motion video

All ten files are MPEG program streams with an MPEG video stream (`0xE0`), a
private audio stream (`0xBD`), and padding (`0xBE`). They run at approximately
29.97 fps. Durations below use the audio PTS span because it is slightly longer
than the video span.

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

Several PSS files have the same byte size as their NUN5 counterpart but
different contents; others differ in size, and NUN5 lacks `NOTICE.PSS`. The
names alone are therefore not sufficient to assume cross-game video parity.

## Inside `DATA.CVM`

### File families

| Family | Role | Evidence and limits |
| --- | --- | --- |
| `*.CCS` (2,310 files) | CC2 resource containers | **Confirmed.** CCS containers hold named objects such as textures/palettes, models, and animations. Individual containers can combine several resource kinds. Use structural CCS parsing rather than treating them as flat images or text files. |
| `GZLIST.TXT` | CCS compression/member-count manifest | **Confirmed.** Plain text records directory names and CCS counts. Existing UI work also established its relationship to gzip-wrapped CCS payloads. It is metadata, not a complete semantic asset index. |
| `ICON.BIN` | Fixed binary icon/resource table | **Unknown beyond structure.** It is a 61,440-byte non-executable binary referenced by the boot ELF. No parser or runtime evidence currently establishes what its records display or control. |

### CCS directory map

These labels are intentionally shallow. Filename-driven meanings remain
inferences until a resource is opened or referenced by code.

| Directory | Shallow role |
| --- | --- |
| `3BSC/` | **Unknown character-coded family.** Nine `3*3BSC.CCS` resources; exact acronym and use unresolved. |
| `3EYE/` | **Confirmed in part:** character-specific battle resources. The 61 `3???3PCT.CCS` containers supply all 72 ordinary awakening-name textures selected by the resident ELF's mode-1 panel compositor. Files also occur in paired `3EYE` names whose exact object use remains unresolved. |
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
- hub/extras: `HOME` and `SHOP`;
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
   `binary_analysis_inventory.tsv` and `binary_analysis.md`.
4. Put an unresolved interpretation in `docs/HYPOTHESES.md`; promote it here
   only when the evidence supports the stated confidence.
5. Link detailed subsystem findings rather than duplicating their complete
   analysis in this overview.
