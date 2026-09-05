# NUN6 reference mod

NUN6 is an unofficial modified NUN5 build used as comparative implementation
evidence. Its behavior is not evidence of unmodified retail-game behavior and
is not an implementation specification for NA228.

## Source identity

The analyzed source is the A35 build. Disc identity and PCSX2 title behavior
are documented in [NA228 disc identity](../disc_identity.md). Its encrypted `DATA.CVM`
uses password `Iruka`.

| File | Size | SHA-256 |
| --- | ---: | --- |
| `@source_nun6/SLUS_556.06` | 5,340,912 | `47C40141A3E1AEB0C96BC28E8DC311938B284D54FD21F4D8BA953C2E16234809` |
| `@source_nun6/PRG/ADV.BIN` | — | `5FA4C6ECFA5BC98416A61C7E25B86F71F4FB4B37B1764C6E3996467279DF37D4` |
| `@source_nun6/PRG/BTL.BIN` | — | `D9C05E13B772A44E4A8FEF1E5101966C2748545A122A5F219D8AA992F88758C6` |
| `@source_nun6/PRG/ETC.BIN` | — | `478178C332B68451FA6D4C4308D5700E652C8C35CC59503B8D8ACEC68C3E1894` |
| `@source_nun6/PRG/MOD.BIN` | 804,320 | `6EAB9760D2BD6583630D096EB08FB7F09E299F5E2FB64DF2413E5DC2ED182998` |
| `@source_nun6/PRG/TEXTBRA.BIN` | 312,064 | `07E30831DC9E88BA4E0DDB1B4F3FD8EDD0D8C4D1CF170BD59BFCB17C09E256BF` |

## Disc and PCSX2 identity

NUN6 is version A35 and has CRC `688C83D6`. Its unknown `SLUS-55606` serial
has no PCSX2 GameDB title. The Game List therefore uses the scanned filename,
where `NUN6.iso` appears as `NUN6`; a normal Game List launch can retain that
title in the runtime window. A direct command-line or batch launch has no
scanned-entry title during boot, and PCSX2 2.6.3 displays
`SLUS-55606 [?]`. The marker denotes the missing GameDB or per-path title, not
an ISO or serial-detection failure.
