/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

    .section .text.v2_glyph_advance,"ax",@progbits
    .balign 4
    .globl v2_glyph_advance
    .type v2_glyph_advance, @function
v2_glyph_advance:
    addiu $sp,$sp,-16                                    # 0x27BDFFF0
    sw $v0,0($sp)                                        # 0xAFA20000
    sw $v1,4($sp)                                        # 0xAFA30004
    lui $v0, %hi(v2_session_pointer)                     # 0x3C020000
    lw $v1, %lo(v2_session_pointer)($v0)                 # 0x8C430000
    beq $v1, $zero, .Lv2_glyph_advance_03C               # 0x10600009
    add.s $f1,$f0,$f2                                    # 0x46020040
    lwc1 $f3,56($v1)                                     # 0xC4630038
    mul.s $f1,$f1,$f3                                    # 0x46030842
    lwc1 $f0,28($s3)                                     # 0xC660001C
    lw $v0,0($sp)                                        # 0x8FA20000
    lw $v1,4($sp)                                        # 0x8FA30004
    addiu $sp,$sp,16                                     # 0x27BD0010
    j 0x1896e0                                           # 0x080625B8
    nop                                                  # 0x00000000
.Lv2_glyph_advance_03C:
    lwc1 $f0,28($s3)                                     # 0xC660001C
    lw $v0,0($sp)                                        # 0x8FA20000
    lw $v1,4($sp)                                        # 0x8FA30004
    addiu $sp,$sp,16                                     # 0x27BD0010
    j 0x1896e0                                           # 0x080625B8
    nop                                                  # 0x00000000
    .size v2_glyph_advance, . - v2_glyph_advance

    .section .text.v2_half_space,"ax",@progbits
    .balign 4
    .globl v2_half_space
    .type v2_half_space, @function
v2_half_space:
    addiu $sp,$sp,-16                                    # 0x27BDFFF0
    sw $v0,0($sp)                                        # 0xAFA20000
    sw $v1,4($sp)                                        # 0xAFA30004
    lui $v0, %hi(v2_session_pointer)                     # 0x3C020000
    lw $v1, %lo(v2_session_pointer)($v0)                 # 0x8C430000
    beq $v1, $zero, .Lv2_half_space_040                  # 0x1060000A
    nop                                                  # 0x00000000
    lwc1 $f4,56($v1)                                     # 0xC4640038
    mul.s $f4,$f3,$f4                                    # 0x46041902
    madd.s $f0,$f2,$f4                                   # 0x4604101C
    swc1 $f0,28($s3)                                     # 0xE660001C
    lw $v0,0($sp)                                        # 0x8FA20000
    lw $v1,4($sp)                                        # 0x8FA30004
    addiu $sp,$sp,16                                     # 0x27BD0010
    j 0x188a84                                           # 0x080622A1
    nop                                                  # 0x00000000
.Lv2_half_space_040:
    madd.s $f0,$f2,$f3                                   # 0x4603101C
    swc1 $f0,28($s3)                                     # 0xE660001C
    lw $v0,0($sp)                                        # 0x8FA20000
    lw $v1,4($sp)                                        # 0x8FA30004
    addiu $sp,$sp,16                                     # 0x27BD0010
    j 0x188a84                                           # 0x080622A1
    nop                                                  # 0x00000000
    .size v2_half_space, . - v2_half_space

    .section .text.v2_newline_advance,"ax",@progbits
    .balign 4
    .globl v2_newline_advance
    .type v2_newline_advance, @function
v2_newline_advance:
    addiu $sp,$sp,-16                                    # 0x27BDFFF0
    sw $v0,0($sp)                                        # 0xAFA20000
    sw $v1,4($sp)                                        # 0xAFA30004
    lui $v0, %hi(v2_session_pointer)                     # 0x3C020000
    lw $v1, %lo(v2_session_pointer)($v0)                 # 0x8C430000
    beq $v1, $zero, .Lv2_newline_advance_054             # 0x1060000F
    lwc1 $f0,64($s3)                                     # 0xC6600040
    add.s $f1,$f1,$f0                                    # 0x46000840
    lui $v0,0xc080                                       # 0x3C02C080
    mtc1 $v0,$f0                                         # 0x44820000
    add.s $f1,$f1,$f0                                    # 0x46000840
    lwc1 $f2,60($v1)                                     # 0xC462003C
    mul.s $f1,$f1,$f2                                    # 0x46020842
    lwc1 $f0,32($s3)                                     # 0xC6600020
    add.s $f0,$f0,$f1                                    # 0x46010000
    swc1 $f0,32($s3)                                     # 0xE6600020
    lw $v0,0($sp)                                        # 0x8FA20000
    lw $v1,4($sp)                                        # 0x8FA30004
    addiu $sp,$sp,16                                     # 0x27BD0010
    j 0x188670                                           # 0x0806219C
    nop                                                  # 0x00000000
.Lv2_newline_advance_054:
    add.s $f1,$f1,$f0                                    # 0x46000840
    lw $v0,0($sp)                                        # 0x8FA20000
    lw $v1,4($sp)                                        # 0x8FA30004
    addiu $sp,$sp,16                                     # 0x27BD0010
    j 0x18860c                                           # 0x08062183
    nop                                                  # 0x00000000
    .size v2_newline_advance, . - v2_newline_advance

    .section .text.v2_plain_space,"ax",@progbits
    .balign 4
    .globl v2_plain_space
    .type v2_plain_space, @function
v2_plain_space:
    addiu $sp,$sp,-16                                    # 0x27BDFFF0
    sw $v0,0($sp)                                        # 0xAFA20000
    sw $v1,4($sp)                                        # 0xAFA30004
    lui $v0, %hi(v2_session_pointer)                     # 0x3C020000
    lw $v1, %lo(v2_session_pointer)($v0)                 # 0x8C430000
    beq $v1, $zero, .Lv2_plain_space_048                 # 0x1060000C
    lwc1 $f0,4($s3)                                      # 0xC6600004
    add.s $f1,$f0,$f1                                    # 0x46010040
    lui $v0,0xc0c0                                       # 0x3C02C0C0
    mtc1 $v0,$f2                                         # 0x44821000
    add.s $f1,$f1,$f2                                    # 0x46020840
    lwc1 $f2,56($v1)                                     # 0xC4620038
    mul.s $f1,$f1,$f2                                    # 0x46020842
    lw $v0,0($sp)                                        # 0x8FA20000
    lw $v1,4($sp)                                        # 0x8FA30004
    addiu $sp,$sp,16                                     # 0x27BD0010
    j 0x1892f4                                           # 0x080624BD
    nop                                                  # 0x00000000
.Lv2_plain_space_048:
    add.s $f1,$f0,$f1                                    # 0x46010040
    lw $v0,0($sp)                                        # 0x8FA20000
    lw $v1,4($sp)                                        # 0x8FA30004
    addiu $sp,$sp,16                                     # 0x27BD0010
    j 0x1892f4                                           # 0x080624BD
    nop                                                  # 0x00000000
    .size v2_plain_space, . - v2_plain_space

    .section .text.v2_right_edge,"ax",@progbits
    .balign 4
    .globl v2_right_edge
    .type v2_right_edge, @function
v2_right_edge:
    addiu $sp,$sp,-16                                    # 0x27BDFFF0
    sw $v0,0($sp)                                        # 0xAFA20000
    sw $v1,4($sp)                                        # 0xAFA30004
    lui $v0, %hi(v2_session_pointer)                     # 0x3C020000
    lw $v1, %lo(v2_session_pointer)($v0)                 # 0x8C430000
    beq $v1, $zero, .Lv2_right_edge_06C                  # 0x10600015
    add.s $f21,$f1,$f0                                   # 0x46000D40
    lwc1 $f2,56($v1)                                     # 0xC4620038
    mul.s $f2,$f1,$f2                                    # 0x46020882
    add.s $f21,$f2,$f0                                   # 0x46001540
    lwc1 $f0,32($s1)                                     # 0xC6200020
    lw $v0,32($v1)                                       # 0x8C620020
    andi $v0,$v0,0x40                                    # 0x30420040
    beq $v0, $zero, .Lv2_right_edge_058                  # 0x10400008
    nop                                                  # 0x00000000
    lwc1 $f1,104($v1)                                    # 0xC4610068
    add.s $f20,$f0,$f1                                   # 0x46010500
    lw $v0,0($sp)                                        # 0x8FA20000
    lw $v1,4($sp)                                        # 0x8FA30004
    addiu $sp,$sp,16                                     # 0x27BD0010
    j 0x187f80                                           # 0x08061FE0
    lw $a0,-13716($gp)                                   # 0x8F84CA6C
.Lv2_right_edge_058:
    lw $v0,0($sp)                                        # 0x8FA20000
    lw $v1,4($sp)                                        # 0x8FA30004
    addiu $sp,$sp,16                                     # 0x27BD0010
    j 0x187f78                                           # 0x08061FDE
    nop                                                  # 0x00000000
.Lv2_right_edge_06C:
    lwc1 $f0,32($s1)                                     # 0xC6200020
    lw $v0,0($sp)                                        # 0x8FA20000
    lw $v1,4($sp)                                        # 0x8FA30004
    addiu $sp,$sp,16                                     # 0x27BD0010
    j 0x187f78                                           # 0x08061FDE
    nop                                                  # 0x00000000
    .size v2_right_edge, . - v2_right_edge
