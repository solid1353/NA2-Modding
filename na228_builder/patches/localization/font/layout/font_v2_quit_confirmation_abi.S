/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

    .section .text.v2_quit_selected_adapter,"ax",@progbits
    .balign 4
    .globl v2_quit_selected_adapter
    .type v2_quit_selected_adapter, @function
v2_quit_selected_adapter:
    addiu $sp,$sp,-48                                    # 0x27BDFFD0
    sw $ra,44($sp)                                       # 0xAFBF002C
    sw $a0,16($sp)                                       # 0xAFA40010
    sw $a1,20($sp)                                       # 0xAFA50014
    sw $a2,24($sp)                                       # 0xAFA60018
    sw $a3,28($sp)                                       # 0xAFA7001C
    lui $t0,0x60                                         # 0x3C080060
    ori $t0,$t0,0x59f0                                   # 0x350859F0
    beq $a0, $t0, .Lv2_quit_selected_adapter_078         # 0x10880015
    nop                                                  # 0x00000000
    lui $t0,0x60                                         # 0x3C080060
    ori $t0,$t0,0x59f8                                   # 0x350859F8
    beq $a0, $t0, .Lv2_quit_selected_adapter_078         # 0x10880011
    nop                                                  # 0x00000000
    lui $t0,0x60                                         # 0x3C080060
    ori $t0,$t0,0x4570                                   # 0x35084570
    beq $a0, $t0, .Lv2_quit_selected_adapter_058         # 0x10880005
    nop                                                  # 0x00000000
    lui $t0,0x60                                         # 0x3C080060
    ori $t0,$t0,0x4568                                   # 0x35084568
    bne $a0, $t0, .Lv2_quit_selected_adapter_094         # 0x14880010
    nop                                                  # 0x00000000
.Lv2_quit_selected_adapter_058:
    lui $t0,%hi(v2_quit_active)                          # 0x3C080000
    lw $t0,%lo(v2_quit_active)($t0)                      # 0x8D080000
    addiu $t1,$zero,1                                    # 0x24090001
    beq $t0,$t1,.Lv2_quit_selected_adapter_078           # 0x11090004
    nop                                                  # 0x00000000
    addiu $t1,$zero,3                                    # 0x24090003
    bne $t0,$t1,.Lv2_quit_selected_adapter_094           # 0x15090008
    nop                                                  # 0x00000000
.Lv2_quit_selected_adapter_078:
    mfc1 $t0,$f12                                        # 0x44086000
    mfc1 $t1,$f13                                        # 0x44096800
    jal v2_c_special_choice_selected_adapter             # 0x0C000000
    nop                                                  # 0x00000000
    lw $ra,44($sp)                                       # 0x8FBF002C
    jr $ra                                               # 0x03E00008
    addiu $sp,$sp,48                                     # 0x27BD0030
.Lv2_quit_selected_adapter_094:
    mfc1 $a1,$f13                                        # 0x44056800
    mfc1 $a2,$f12                                        # 0x44066000
    addiu $a3,$sp,32                                     # 0x27A70020
    jal v2_c_quit_selected_map                           # 0x0C000000
    nop                                                  # 0x00000000
    mtc1 $v0,$f12                                        # 0x44826000
    lw $t0,32($sp)                                       # 0x8FA80020
    mtc1 $t0,$f13                                        # 0x44886800
    lw $a0,16($sp)                                       # 0x8FA40010
    lw $a1,20($sp)                                       # 0x8FA50014
    lw $a2,24($sp)                                       # 0x8FA60018
    lw $a3,28($sp)                                       # 0x8FA7001C
    lw $ra,44($sp)                                       # 0x8FBF002C
    addiu $sp,$sp,48                                     # 0x27BD0030
    j 0x379150                                           # 0x080DE454
    nop                                                  # 0x00000000
    .size v2_quit_selected_adapter, . - v2_quit_selected_adapter
