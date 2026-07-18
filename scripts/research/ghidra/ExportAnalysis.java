// Exports decompiled C and an ASCII listing for the current program.
// Undefined typed values remain in C; undefined data is omitted from ASCII.
// @category NA2

import ghidra.app.script.GhidraScript;
import ghidra.app.util.Option;
import ghidra.app.util.exporter.AsciiExporter;
import ghidra.app.util.exporter.CppExporter;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.List;

public class ExportAnalysis extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected: export-root");
        }

        String programName = currentProgram.getName();
        File outputDir = new File(args[0], programName);
        outputDir.mkdirs();
        File cFile = new File(outputDir, programName + ".c");
        File asciiFile = new File(outputDir, programName + ".txt");
        File doneFile = new File(outputDir, "export.complete");

        CppExporter cpp = new CppExporter();
        cpp.setExporterServiceProvider(state.getTool());
        if (!cpp.export(cFile, currentProgram, null, monitor)) {
            throw new IllegalStateException("C export failed: " + cpp.getMessageLog());
        }

        AsciiExporter ascii = new AsciiExporter();
        ascii.setExporterServiceProvider(state.getTool());
        List<Option> options = ascii.getOptions(() -> currentProgram);
        boolean changedUndefined = false;
        for (Option option : options) {
            if ("Undefined Data".equals(option.getName().trim())) {
                option.setValue(Boolean.FALSE);
                changedUndefined = true;
            }
        }
        if (!changedUndefined) {
            throw new IllegalStateException("ASCII undefined-data option was not found");
        }
        ascii.setOptions(options);
        if (!ascii.export(asciiFile, currentProgram, null, monitor)) {
            throw new IllegalStateException("ASCII export failed: " + ascii.getMessageLog());
        }

        String marker = "c_bytes=" + cFile.length() + "\n" +
            "ascii_bytes=" + asciiFile.length() + "\n" +
            "ascii_undefined_data=false\n";
        Files.writeString(doneFile.toPath(), marker, StandardCharsets.UTF_8);
    }
}
