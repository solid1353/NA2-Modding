// Writes a compact, path-portable summary for a completed Ghidra import.
// @category NA2

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import java.io.File;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;

public class WriteAnalysisSummary extends GhidraScript {
    private String clean(String value) {
        return value.replace('\t', ' ').replace('\r', ' ').replace('\n', ' ');
    }
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 5) {
            throw new IllegalArgumentException("Expected: output-path source-alias sha256 format load-base");
        }
        currentProgram.setExecutablePath(args[1]);
        long functionCount = 0;
        for (Function ignored : currentProgram.getFunctionManager().getFunctions(true)) functionCount++;
        long instructionCount = 0;
        for (Instruction ignored : currentProgram.getListing().getInstructions(true)) instructionCount++;
        File output = new File(args[0]);
        output.getParentFile().mkdirs();
        try (PrintWriter writer = new PrintWriter(output, StandardCharsets.UTF_8)) {
            writer.println("program\tsource\tsha256\tformat\tlanguage\tcompiler\timage_base\tload_base\tmemory_blocks\tfunctions\tinstructions");
            writer.printf("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%d%n",
                clean(currentProgram.getName()), clean(args[1]), clean(args[2]), clean(args[3]),
                clean(currentProgram.getLanguageID().getIdAsString()),
                clean(currentProgram.getCompilerSpec().getCompilerSpecID().getIdAsString()),
                currentProgram.getImageBase(), clean(args[4]), currentProgram.getMemory().getBlocks().length,
                functionCount, instructionCount);
        }
    }
}
