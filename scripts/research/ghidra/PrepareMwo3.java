// Prepares an MWo3 payload imported with BinaryLoader for R5900 analysis.
// @category NA2

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.SourceType;

public class PrepareMwo3 extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 3) {
            throw new IllegalArgumentException("Expected: base-address text-length entry-address-or-dash");
        }
        Address base = toAddr(Long.decode(args[0]));
        long textLength = Long.decode(args[1]);
        Memory memory = currentProgram.getMemory();
        MemoryBlock block = memory.getBlock(base);
        if (block == null || !block.getStart().equals(base)) {
            throw new IllegalStateException("MWo3 payload block does not begin at " + base);
        }
        Address split = base.add(textLength);
        if (textLength > 0 && split.compareTo(block.getEnd()) <= 0) {
            memory.split(block, split);
        }
        MemoryBlock text = memory.getBlock(base);
        text.setName("text");
        text.setRead(true);
        text.setWrite(false);
        text.setExecute(true);
        MemoryBlock data = memory.getBlock(split);
        if (data != null && data != text) {
            data.setName("data");
            data.setRead(true);
            data.setWrite(true);
            data.setExecute(false);
        }
        if (!args[2].equals("-")) {
            Address entry = toAddr(Long.decode(args[2]));
            createLabel(entry, "mwo3_entry", true, SourceType.ANALYSIS);
            currentProgram.getSymbolTable().addExternalEntryPoint(entry);
            new DisassembleCommand(entry, null, true).applyTo(currentProgram, monitor);
            if (getFunctionAt(entry) == null) {
                createFunction(entry, "mwo3_entry");
            }
        }
    }
}
