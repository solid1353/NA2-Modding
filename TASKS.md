# Tasks

## In Progress

### Project
- Disassemble executable binaries in Ghidra:
  - NA2: ELF, ADV.BIN, BTL.BIN, ETC.BIN.
  - NUN5: ELF, ADV.BIN, BTL.BIN, ETC.BIN, TEXTENG.BIN, TEXTFRN.BIN, TEXTGER.BIN, TEXTITA.BIN, TEXTSPA.BIN.
  - NUN6: ELF, ADV.BIN, BTL.BIN, ETC.BIN, MOD.BIN, TEXTBRA.BIN.
  - Shared identical IOP modules (analyze once): CRI_ADXI.IRX, MODULES.BIN, SNDBASE.IRX.

### UI Translation
- Add texture patcher to import assets from NUN5 (investigate NUN5 DATA.CVM unpacked and stripped first?).
- Investigate upscaling variants.

### Menu restructuring
- Analyze differences against NUN6 and remove adventure mode.

### String translation
- Deal with unresolved (mappings.tsv and ChatGPT's history) and other remainders (like chakra pickup message in battle).

## Backlog

### Project
- Solve concurrent memcard access for pcsx2.
- Develop a release process.
- Add explicit profile selection to the `na2` build-only and build-and-launch workflows.

### Logic
- Improve substitution reliability.
- Add substitution bar.
- Disable support.
- Fix extra hit floating animation (or maybe not?).

### Font
- Research NUN5 auto-adjust behavior.
- Resume GF4 renderer work in the dedicated GF4 task, starting from the recorded v22/v23 results rather than another blind resource swap.

### Testing
- Basically everything.

### Unsorted
