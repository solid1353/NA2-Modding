/* Byte-exact resident shims for accepted secondary-glyph geometry. */
    .set noreorder
    .set noat

    .section .text.glyph_secondary_cell_guard,"ax",@progbits
    .balign 4
    .globl glyph_secondary_cell_guard
    .type glyph_secondary_cell_guard, @function
glyph_secondary_cell_guard:
    sltiu $at,$v0,123                                    # 0x2C41007B
    movz $v0,$zero,$at                                   # 0x0001100A
    lhu $v1,6($a1)                                       # 0x94A30006
    j 0x18707c                                           # 0x08061C1F
    nop                                                  # 0x00000000
    .size glyph_secondary_cell_guard, . - glyph_secondary_cell_guard

    .section .text.glyph_normal_bottom_edge,"ax",@progbits
    .balign 4
    .globl glyph_normal_bottom_edge
    .type glyph_normal_bottom_edge, @function
glyph_normal_bottom_edge:
    andi $v1,$v1,8                                       # 0x30630008
    beq $v1,$zero,.Lglyph_normal_bottom_edge_add         # 0x10600002
    lwc1 $f1,12($s1)                                     # 0xC621000C
    lwc1 $f1,16($s1)                                     # 0xC6210010
.Lglyph_normal_bottom_edge_add:
    cvt.s.w $f1,$f1                                      # 0x46800860
    add.s $f20,$f1,$f0                                   # 0x46000D00
    j 0x187f80                                           # 0x08061FE0
    lw $a0,-13716($gp)                                   # 0x8F84CA6C
    .size glyph_normal_bottom_edge, . - glyph_normal_bottom_edge
