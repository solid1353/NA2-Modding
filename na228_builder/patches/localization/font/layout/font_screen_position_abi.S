/* Render Screen Settings text through NUN5's secondary ASCII font state. */
    .set noreorder
    .set noat

    .section .text.screen_position_text_draw,"ax",@progbits
    .balign 4
    .globl screen_position_text_draw
    .type screen_position_text_draw, @function
screen_position_text_draw:
    addiu $sp,$sp,-192
    sw $ra,188($sp)
    sw $a0,16($sp)
    sw $a1,20($sp)
    sw $a2,24($sp)
    sw $a3,28($sp)
    swc1 $f12,32($sp)
    swc1 $f13,36($sp)

    lui $t0,0x60
    lw $t0,0x7470($t0)
    sw $t0,40($sp)
    beq $t0,$zero,.Ldraw
    nop
    lbu $t1,0x70($t0)
    sw $t1,44($sp)
    lw $t2,0x3c($t0)
    sw $t2,48($sp)
    lw $t2,0x40($t0)
    sw $t2,56($sp)
    ori $t1,$t1,0x8
    sb $t1,0x70($t0)
    sw $zero,0x3c($t0)
    sw $zero,0x40($t0)

.Ldraw:
    lui $t0,%hi(v2_session_pointer)
    lw $t1,%lo(v2_session_pointer)($t0)
    sw $t1,60($sp)
    sw $zero,96($sp)
    lui $t1,0x3f80
    sw $t1,120($sp)
    sw $t1,124($sp)
    addiu $t1,$sp,64
    sw $t1,%lo(v2_session_pointer)($t0)

    lw $a0,16($sp)
    lw $a1,20($sp)
    lw $a2,24($sp)
    lw $a3,28($sp)
    lwc1 $f12,32($sp)
    lwc1 $f13,36($sp)
    jal 0x382310
    nop
    sw $v0,52($sp)

    lui $t0,%hi(v2_session_pointer)
    lw $t1,60($sp)
    sw $t1,%lo(v2_session_pointer)($t0)

    lw $t0,40($sp)
    beq $t0,$zero,.Lreturn
    nop
    lw $t1,44($sp)
    sb $t1,0x70($t0)
    lw $t2,48($sp)
    sw $t2,0x3c($t0)
    lw $t2,56($sp)
    sw $t2,0x40($t0)

.Lreturn:
    lw $v0,52($sp)
    lw $ra,188($sp)
    jr $ra
    addiu $sp,$sp,192
    .size screen_position_text_draw, . - screen_position_text_draw
