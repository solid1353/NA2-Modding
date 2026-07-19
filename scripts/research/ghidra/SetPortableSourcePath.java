// Replaces Ghidra's imported machine path with the canonical project alias.
// @category NA2

import ghidra.app.script.GhidraScript;

public class SetPortableSourcePath extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected: target");
        }
        String target = args[0];
        String name = currentProgram.getName();
        String alias;
        switch (target) {
            case "NA2":
                alias = name.equals("SLPS_258.37")
                    ? "@source_na2/SLPS_258.37"
                    : "@source_na2/PRG/" + name;
                break;
            case "NUN3":
                if (name.equals("SLUS_217.27")) {
                    alias = "@source_nun3/SLUS_217.27";
                }
                else if (name.endsWith(".IRX")) {
                    alias = "@source_nun3/MODULES/" + name;
                }
                else {
                    alias = "@source_nun3/PRG/" + name;
                }
                break;
            case "NUN5":
                alias = name.equals("SLES_556.05")
                    ? "@source_nun5/SLES_556.05"
                    : "@source_nun5/PRG/" + name;
                break;
            case "NUN6":
                alias = name.equals("SLUS_556.06")
                    ? "@source_nun6/SLUS_556.06"
                    : "@source_nun6/PRG/" + name;
                break;
            case "shared":
                alias = "@source_na2/MODULES/" + name;
                break;
            default:
                throw new IllegalArgumentException("Unknown target: " + target);
        }
        currentProgram.setExecutablePath(alias);
    }
}
