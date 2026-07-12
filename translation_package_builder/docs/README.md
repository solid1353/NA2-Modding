# NA2 Translation Package Builder v6

Builds a self-contained translation package from clean NA2 files and official
UN5 `PRG/TEXTENG.BIN` strings.

This revision also patches the NA2 executable string tables used by the
Practice and Shop interfaces. It fixes the bad `Chakra -> Q` baseline entry,
translates the reported Practice labels/values, Shop character names and
Yes/No choices, and adds the missing Shop help strings.

The builder:

- preserves the existing safe BTL/ETC translation baseline;
- replaces verified matching entries with official UN5 English wording;
- patches verified fixed strings in clean `SLPS_258.37`;
- reads no translation TSV files;
- never edits an ISO;
- writes `NA2_APPLY__TRANSLATION__*.zip` to Downloads.

The generated package contains exactly:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`
- `SLPS_258.37`

Stylized menu headers, button legends and purchase badges that are stored as
images are outside this text-package pass.
