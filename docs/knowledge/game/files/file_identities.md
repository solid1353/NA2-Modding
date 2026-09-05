# Retail game file identities

This document owns the hashes of complete, unmodified retail game files cited
by project documentation. Domain documents identify their inputs by linking
here instead of repeating hashes.

## Research coverage

- **Assigned scope:** Complete-file identities and shared address conventions
  for unmodified retail game files used by project research.
- **Exploration depth:** Every complete retail game-file hash currently cited
  in human documentation is consolidated below; sizes and address mappings are
  included where the existing research records them.
- **Confirmed coverage:** The listed hashes identify the exact clean inputs used
  by the linked research, and the recorded load mappings convert the scoped ELF
  and overlay addresses.
- **Unresolved or untested:** Sizes or load mappings shown as unavailable have
  not been established by the cited documentation.
- **Deliberate exclusions and overlap:** Modded game-file identities belong to
  feature documentation. Operational manifests retain hashes required by tools.
  Generated artifacts, extracted byte ranges, runtime captures, and external
  tools retain their evidence hashes in their owning documents.
- **Evidence limitations:** A matching hash establishes byte identity only; it
  does not establish a file's behavior, provenance, or runtime use.

## Executables and overlays

| Game | File | Size | SHA-256 |
| --- | --- | ---: | --- |
| NA2 v2.28 | `@source_na2/SLPS_258.37` | 5,273,256 | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |
| NA2 v2.28 | `@source_na2/PRG/ADV.BIN` | — | `AD60D9C9D11811CE57A4E64F35226EBB366D580010761A0FD1300DFE621BC34D` |
| NA2 v2.28 | `@source_na2/PRG/BTL.BIN` | 2,237,184 | `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` |
| NA2 v2.28 | `@source_na2/PRG/ETC.BIN` | 200,448 | `8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74` |
| NUN5 | `@source_nun5/SLES_556.05` | 5,340,912 | `20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D` |
| NUN5 | `@source_nun5/PRG/ADV.BIN` | — | `7E2AF55362141BB1B055247CD7EF7EDAE290F3C0095701BC51467F096A2D00B8` |
| NUN5 | `@source_nun5/PRG/BTL.BIN` | 2,253,184 | `7E8518DA7BD4957AF18CB0ABABE67F0E9B37C42C6551375201B15997F0A3DFE3` |
| NUN5 | `@source_nun5/PRG/ETC.BIN` | 171,776 | `BDB6BDA1F9D335047586A263E478486C8E7924B91FA972B6F3E58CAEC5EA0778` |
| NUN5 | `@source_nun5/PRG/TEXTENG.BIN` | 199,936 | `3E42D2DDFFE770B05DD41E2C5937380133E255C9CE32CA2F037E34C65A8E571E` |

## NA2 supporting files

| File | Size | SHA-256 |
| --- | ---: | --- |
| `@source_na2/FLIST.DIR` | 124 | `4F500B226613858648E2502F04FA84E04D3420DBE066B86E019EC7E10E90AA0C` |
| `@source_na2/DATA/DATA.CVM.files/DATA.CVM.iso.files/GZLIST.TXT` | 103,848 | `40912F3C8999BCC7754757271CFF35F8C22FB9797EE5D008B10AB60FE48B97CE` |
| `@source_na2/DATA/DATA.CVM.files/DATA.CVM.iso.files/ICON.BIN` | 61,440 | `80D7F62704FC9F59DEF83ED8AF68C0A26609215C2C398F2CA2EBBB99057CF017` |
| `@source_na2/MODULES/MODULES.BIN` | 315,392 | `0CDEA9EF15E3FFE8B70B6305A67F9A37015FF12B08815EE4CA16358A4C93BA9D` |

## CCS research inputs

Paths are below `DATA/DATA.CVM.files/DATA.CVM.iso.files/`. Decompressed sizes
are recorded only for files whose research used the decompressed payload.

| Game | File | File size | Decompressed size | SHA-256 |
| --- | --- | ---: | ---: | --- |
| NA2 v2.28 | `PL/1KHWBOD1.CCS` | 87,260 | 542,528 | `C7AC6C0B723727C7D8BD58EEA87F1EC16DDF1241A697454D3FCC652B6084BA54` |
| NA2 v2.28 | `PL/2DDRBOD1.CCS` | 826,268 | 1,687,292 | `CF002388614403169B7681969DCBDC2C4212CABC42D56E41E722E0BCA3B92789` |
| NA2 v2.28 | `PL/2HKGCHA1.CCS` | 36,040 | 83,568 | `B05EDA70F5519F83F7A4740ABAED569152431CE6EB9D281CB5AE0EBD728E438C` |
| NA2 v2.28 | `PL/2TEWCHA1.CCS` | 29,591 | 66,632 | `06D11D0D46CFCDBB42F67739082C5B023E282CC71A26D70533000F672F36AF2D` |
| NA2 v2.28 | `BUDDY/2ASWBDY0.CCS` | 49,569 | 78,376 | `1E681EF47C9AC55155F868F3F69E7EB7F4A5D58A743C14C534627F44CE40A029` |
| NA2 v2.28 | `SCENE/PPT2310_ST00.CCS` | 385,282 | 1,499,860 | `5E6D69FD8E5098121D0325486E92323A1E8BE129F738E92DBC6EA78E262ED6B1` |
| NA2 v2.28 | `SCENE/PPTS04.CCS` | 440,211 | 1,240,424 | `0AB4D80EDBF6231DBD13208ABC6335BE3981EEDE5F2898274762C52040E4E15B` |
| NA2 v2.28 | `XNINKA.CCS` | 68,535 | 273,172 | `DE2ADA4D3EAA54D8DE64DCDEDDEDB5CDB77A34145B8BD073A8E199B5136932E1` |
| NA2 v2.28 | `3EYE/ENDDEMO.CCS` | 74,520 | — | `FB9DAF4CE604B0986F2D2F66D6E61EA61B96AE5A1192DF125D672E9F806C4E7E` |
| NA2 v2.28 | `3EYE/3HAK3PCT.CCS` | 9,978 | — | `3E8D2824415B78D08363B3A28C8354ADDBA99D17DA96C00CECAB83D7263349D9` |
| NA2 v2.28 | `3EYE/3SKN3PCT.CCS` | 14,794 | — | `2BFE5B4EF601F06057D5F56D73D92A8F10DBDEC95B9A08CB7E92B4D0F2F7977C` |
| NUN5 | `3EYE/ENDDEMO.CCS` | 79,749 | — | `8819196236C61D6CC95AABF602451EEC4869B15710A3B6372E0373252AFC2252` |
| NUN5 | `3EYE/3HAK3PCT.CCS` | 10,947 | — | `9C1622B53B098EDC6F38435A858B12BE2833666F8043252A0A56617B3E7036F2` |
| NUN5 | `3EYE/3SKN3PCT.CCS` | 15,922 | — | `3618E055EBF19B2A48C1657955A8E6539AE9C96BB486BBA8EAD7AE217E14B722` |

## Address conventions

The preserved NA2 and NUN5 BTL and ETC projects omit the `0x40`-byte MWo3
header when mapping code. Their archived live bases are:

| Game | Overlay | Archived live base |
| --- | --- | ---: |
| NA2 v2.28 | `PRG/BTL.BIN` | `0x006B3F00` |
| NA2 v2.28 | `PRG/ETC.BIN` | `0x006B3F00` |
| NUN5 | `PRG/BTL.BIN` | `0x006C6D00` |
| NUN5 | `PRG/ETC.BIN` | `0x006C6D00` |

A preserved Ghidra address is the archived live address minus `0x40`.
Complete-file offsets include the header. Direct MIPS call targets and absolute
data operands are already runtime addresses, so resolve them to a complete-file
offset by subtracting the archived live base without applying the header shift
again. For example, NA2 runtime operand `0x008C42D8` maps to file offset
`0x2103D8`, not `0x210418`.

For the boot ELFs, the relevant `PT_LOAD` mappings place NA2 file offset
`0x100` and NUN5 file offset `0x180` at runtime `0x00100000`.
