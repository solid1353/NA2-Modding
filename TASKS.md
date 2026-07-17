# Tasks

## In Progress

### Project
- Permit agents to read TASKS.md, execute or move contained tasks between "In Progress"/"Backlog" when asked and delete them after execution when the result is approved. If a task to be executed is not perfectly clear, agent should always request clarification. Agent should also choose the best chat for the task or create a new one if needed.
- Update directories in docs (disassembly, utils, ghidra, source, see the latest commit).
- Move pcsx2 up one level, make it self-contained, symlink cheats and update everything.
- Actualize only when pnach is not empty, add logging of enabled cheats to launch command.
- Properly unpack NA2, UN3, UN5, UN6.
- Do I need to disassemble BTL/ETC/other or is ELF enough?
- Re-disassemble NA2.
- Disassemble UN6.
- Re-check everything and make source directory read-only.
- Deal with the "old" directory.

### UI Translation
- Add texture patcher to import assets from UN5.
- Add unarchiving ISOs to a needed extent in sources if the necessary folders are missing, leave an instruction on support for agents.
- Investigate upscaling variants.

### Menu restructuring
- Analyze differences against UN6 and remove adventure mode.

### String translation
- Deal with unresolved (mappings.tsv and ChatGPT's history) and other remainders.

## Backlog

### Project
- Solve concurrent memcard access for pcsx2.
- Come up with /trash cleanup policy.
- Investigate utils/old.
- Develop a release process.
- Refactor.

### Logic
- Improve substitution reliability.
- Add substitution bar.
- Disable support.
- Fix extra hit floating animation (or maybe not?).

### Font
- Research UN5 auto-adjust behavior.
- Resume GF4 renderer work in the dedicated GF4 task, starting from the recorded v22/v23 results rather than another blind resource swap.

### Testing
- Basically everything.

### Unsorted
