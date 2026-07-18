# Disc identity

This module gives the modified project image the synthetic serial
`SLPS-22228`. It performs two equal-length edits during profile composition:

- `SYSTEM.CNF`: `SLPS_258.37` to `SLPS_222.28`;
- the ISO9660 root directory identifier: `SLPS_258.37;1` to
  `SLPS_222.28;1`.

The original source image remains untouched. The boot ELF payload is still
composed under its clean-source name before the final directory identifier is
renamed, so existing translation and raw-binary modules do not need duplicate
targets. The final ISO size, boot ELF size, and extent remain unchanged.

The game's hard-coded save directory `BISLPS-25837NARUTO5` is deliberately not
changed, preserving compatibility with existing saves.
