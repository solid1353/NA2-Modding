Narutimate Accel v2.28

1. Extract every file from this ZIP into one directory.
2. Put one supported clean Narutimate Accel 2 ISO and one supported clean Ultimate Ninja 5 ISO in that directory. Their filenames do not matter.
3. Edit config.json if you want to change which features are enabled.
4. Double-click the EXE.

Configuration

config.json contains features and overrides. Every feature node has an enabled boolean and may include a description. Setting a branch's enabled value to false disables its complete subtree; when it is true, its child enabled values apply. overrides may be empty or may contain only the feature-tree branches you want to change. Every supplied key must exist in the catalog embedded in the EXE.

Output

The program builds Narutimate Accel v2.28.iso.building first. After the complete image is verified, it creates or replaces Narutimate Accel v2.28.iso. A failed build keeps the existing Narutimate Accel v2.28.iso and removes only the temporary building file.
