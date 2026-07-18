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
                    ? "@source/NA2.iso.files/SLPS_258.37"
                    : "@source/NA2.iso.files/PRG/" + name;
                break;
            case "NUN5":
                alias = name.equals("SLES_556.05")
                    ? "@source/NUN5.iso.files/SLES_556.05"
                    : "@source/NUN5.iso.files/PRG/" + name;
                break;
            case "NUN6":
                alias = name.equals("SLUS_556.06")
                    ? "@source/NUN6 A35.iso.files/SLUS_556.06"
                    : "@source/NUN6 A35.iso.files/PRG/" + name;
                break;
            case "shared":
                alias = "@source/NA2.iso.files/MODULES/" + name;
                break;
            default:
                throw new IllegalArgumentException("Unknown target: " + target);
        }
        currentProgram.setExecutablePath(alias);
    }
}
