Narutimate Accel v2.28

1. Extract every file from this ZIP into one directory.
2. Put one supported clean Narutimate Accel 2 ISO and one supported clean Ultimate Ninja 5 ISO in that directory. Their filenames do not matter.
3. Edit Narutimate Accel v2.28.json if you want to change which features are enabled.
4. Double-click the EXE.

Configuration

Narutimate Accel v2.28.json contains features and overrides. features is the base selection. overrides may be empty or may contain only the feature-tree branches you want to change. true enables a node, false disables it, and an object configures nested nodes individually. Every supplied key must exist in the catalog embedded in the EXE, and leaves must be true or false.

Output

The program builds Narutimate Accel v2.28.iso.building first. After the complete image is verified, it creates or replaces Narutimate Accel v2.28.iso. A failed build keeps the existing Narutimate Accel v2.28.iso and removes only the temporary building file.
