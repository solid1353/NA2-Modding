# NUN6 external-string reference

The analyzed [NUN6 source](../source.md#source-identity) retains NUN5's five
language slots but makes only the first non-null, `TextBra.bin`. It adds
`MOD.BIN`, redirects the NUN5 loader's filename and destination to that module,
and transfers control into resident MOD code.

| File | Kind | Load base | File bytes | Reserved end |
| --- | ---: | ---: | ---: | ---: |
| `TEXTBRA.BIN` | 4 | `0x008F3D00` | `0x4C300` | `0x00940000` |
| `MOD.BIN` | 8 | `0x00940000` | `0xC45E0` | below `0x00A28900` |

NUN6 redirects four NUN5 metadata pointers:

| Runtime pointer location | NUN5 value | NUN6 value |
| ---: | ---: | ---: |
| `0x005BB2B0` | `0x005DDA10` | `0x00968E80` |
| `0x005BB490` | `0x005DDC50` | `0x0095A2A0` |
| `0x005BB870` | `0x005DE550` | `0x0095B2A0` |
| `0x005BB930` | `0x005DE8B0` | `0x0095AAA0` |

NUN6 also changes the homologous resident-boundary instruction pairs and final
marker together. This is useful precedent that a larger resident image requires
a coordinated boundary change, but its main and overlay layout is not directly
reusable in NA2.
