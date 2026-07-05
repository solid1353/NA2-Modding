// Temporary Ghidra script: dump instructions around substitution candidate functions.
// @category NA2

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class DumpSubstitutionCandidates extends GhidraScript {
    private void dumpFunction(String addrText, int maxInstructions) throws Exception {
        Address addr = toAddr(addrText);
        Function f = getFunctionAt(addr);
        println("== " + addrText + " " + (f == null ? "<no function>" : f.getName()) + " ==");
        if (f == null) return;
        int count = 0;
        for (Instruction ins = getInstructionAt(f.getEntryPoint());
             ins != null && f.getBody().contains(ins.getAddress()) && count < maxInstructions;
             ins = ins.getNext(), count++) {
            println(ins.getAddress() + "  " + ins.toString());
        }
    }

    private void dumpRefsTo(String addrText) throws Exception {
        Address addr = toAddr(addrText);
        println("== refs to " + addrText + " ==");
        ReferenceIterator refs = getReferencesTo(addr);
        for (Reference ref : refs) {
            println(ref.getFromAddress() + " -> " + ref.getToAddress() + " " + ref.getReferenceType());
        }
    }

    public void run() throws Exception {
        dumpRefsTo("001910e0");
        dumpRefsTo("001921c0");
        dumpRefsTo("00192740");
        dumpRefsTo("00192ae0");
        dumpRefsTo("00192fb0");
        dumpRefsTo("001c3da0");
        dumpFunction("001910e0", 900);
        dumpFunction("001921c0", 500);
        dumpFunction("00192740", 500);
        dumpFunction("00192ae0", 700);
        dumpFunction("00192fb0", 500);
        dumpFunction("001c3da0", 350);
    }
}
