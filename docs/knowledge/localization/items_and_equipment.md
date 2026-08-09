# Item and equipment localization

## Unresolved string range

Possible unmapped item or equipment strings occupy ELF file range
`0x4B01E0-0x4B04D0`. The legacy scratch ELF overwrote them with test text, so
recover candidates only from clean NA2 and official NUN5 sources.
