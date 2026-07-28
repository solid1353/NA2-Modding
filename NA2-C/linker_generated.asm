.ps2
.Open "./data/FILES/SLES_556.05", 0x000FFE80
; ============================================================
; INDICE
;   1. Funcoes originais do motor (engine)
;   2. Battle (ccBTL*)
;   3. Labels nao identificadas (z_un_*)
;   4. String/memoria (libc-like)
;   5. Constantes / enderecos de hook
;   6. Import objects
;   7. Hooks - fixGlobalScrenFx
;   8. Hooks - fixScrenFx (142 enderecos, maior -> menor)
;   9. Hooks - gameplay / mecanicas especiais
;  10. Hooks - UI / texto
; ============================================================
; ============================================================
; 1. FUNCOES ORIGINAIS (engine)
; ============================================================
.definelabel sysCheckedStrCpy,      0x0018CCC0  ; strcpy com checagem de limite
.definelabel sysCheckedStrCat,      0x0018CD30  ; strcat com checagem de limite
.definelabel sysStrToLower,         0x0017EEA8  ; lowercase in-place
.definelabel sysLoadResourceFile,   0x00100300  ; load de arquivo (via FUN_00163e28/FUN_00164230/etc)
.definelabel sysSetScreenFx,        0x0010BDE0
.definelabel sys_malloc,            0x001176C0
.definelabel sys_free,              0x00198610
.definelabel printConsole,          0x0015EED0
.definelabel sysMeasureText,        0x0018B7F0
.definelabel sysDrawString,         0x00389970
.definelabel sysSetFontCursor,      0x00187B10
.definelabel sysDrawChar,           0x0038A210
.definelabel sysLoadFont,           0x001878E0
.definelabel sysCancel,             0x0025C7C0
.definelabel sysRand,               0x00181020
.definelabel sysGetCurrentLanguage, 0x003D4110
.definelabel sysGetLocalizedText,   0x003D10D0
.definelabel un5_sprintf,           0x0017CA60
; ============================================================
; 2. BATTLE (ccBTL*)
; ============================================================
.definelabel ccBTL_MeasureTextWidth,         0x0018CAE0
.definelabel ccBTLPlayerSetAwakening,        0x00310580
.definelabel ccBTLPlayerGetAtkID,            0x0021EBA0
.definelabel ccBTLPLayerGetAtkFrame,         0x00218BB0
.definelabel ccBTLPlayerGetANMState,         0x00218A30
.definelabel ccBTLPlayerPlayVoice,           0x0020ADC0
.definelabel ccBTLPlayerPlayRandVoice,       0x0020AEF0
.definelabel ccBTLPlaySpawnJmpEFF,           0x00210E80
.definelabel ccBTLPlayerCalcSlideDistance,   0x00311C70
.definelabel ccBTLPlayerInitTransform,       0x00211BB0
.definelabel ccBTLPlayerPlayScreenShake,     0x00254BB0
.definelabel ccBTLPlayerUpdateAudioPosition, 0x001DDF50
.definelabel ccBTLPlayerPlayChakraAnimation, 0x003482B0
.definelabel ccBTLPlayerSetOBJState,         0x0021B710
.definelabel ccPlaySE,                       0x0020B130
; ============================================================
; 3. LABELS NAO IDENTIFICADAS (z_un_*) - placeholders
; ============================================================
.definelabel z_un_003856b0, 0x003856B0
.definelabel z_un_001d1480, 0x001D1480
.definelabel z_un_001d14d0, 0x001D14D0
.definelabel z_un_001106b0, 0x001106B0
.definelabel z_un_001105c0, 0x001105C0
.definelabel z_un_00153170, 0x00153170
.definelabel z_un_00152da8, 0x00152DA8
.definelabel z_un_0010f1b0, 0x0010F1B0
.definelabel z_un_00100450, 0x00100450
.definelabel z_un_00171e58, 0x00171E58
.definelabel z_un_0010a280, 0x0010A280
; ============================================================
; 4. STRING/MEMORIA (libc-like)
; Identificadas via engenharia reversa do binario (assembly MIPS/EE core)
; ============================================================
.definelabel sys_strcat,     0x0017CD38  ; strcat
.definelabel sys_strcpy,     0x0017D140  ; strcpy (motor interno, reusado dentro de strcat)
.definelabel sys_strlen,     0x0017D258  ; strlen
.definelabel sys_strcmp,     0x0017CFF8  ; strcmp
.definelabel sys_strcasecmp, 0x0017CC60  ; strcasecmp / stricmp
.definelabel sys_strchr,     0x0017CE68  ; strchr
.definelabel sys_strrchr,    0x0017D8B8  ; strrchr
.definelabel sys_strstr,     0x0017D908  ; strstr
.definelabel sys_strncat,    0x0017D390  ; strncat
.definelabel sys_memcmp,     0x0017D540  ; memcmp
.definelabel sys_memcpy,     0x0017D6F8  ; memcpy
.definelabel sys_strtod,     0x0017E8A8  ; strtod (wrapper publico) -> motor em 0x0017D990
.definelabel sys_strcoll,    0x0017E8F8  ; strcoll (comparacao locale-aware)
.definelabel sys_strtol,     0x0017EC18  ; strtol (wrapper publico) -> motor em 0x0017E9E0
.definelabel sys_strtoul,    0x0017EE78  ; strtoul (wrapper publico, offset a confirmar) -> motor em 0x0017EC48
; ============================================================
; 5. CONSTANTES / ENDERECOS DE HOOK
; ============================================================
BASE_ADDRESS               equ 0x5A01D0
SSK_Moveset_Hook_Address   equ 0x4210E8
NRT_Moveset_Hook_Address   equ 0x41B738
; TODO: NRT_SUBTITLE_BASE ainda sem endereco confirmado.
; O parser do build.py so aceita "0x..." ou decimal em uma linha "equ";
; deixar um placeholder como "<endereço...>" faz essa label ser
; silenciosamente ignorada (nao vira erro, mas tambem nao existe).
; Se algum .org usar NRT_SUBTITLE_BASE antes de confirmar o valor,
; os hooks daquele bloco serao perdidos sem aviso. Descomente e
; preencha antes de usar:
; NRT_SUBTITLE_BASE equ 0x00000000
Render_UJLegend_Hook       equ 0x001A3D40
DBG_PrintCCS_Hook          equ 0x001C2E20
sysWriteTextLan_Hook       equ 0x003D3FE4
; ============================================================
; 6. IMPORT OBJECTS
; ============================================================
; ============================================================
; 7. HOOKS - fixGlobalScrenFx
; ============================================================
; ============================================================
; 8. HOOKS - fixScrenFx (142 enderecos, ordenados do maior para o menor)
; ============================================================
; ============================================================
; 9. HOOKS - GAMEPLAY / MECANICAS ESPECIAIS
; ============================================================
; ============================================================
; 10. HOOKS - UI / TEXTO
; ============================================================

.org 0x5a01d0
    .importobj "./ccSSK_Moveset.o"
.org 0x5a0530
    .importobj "./ccNRT_Moveset.o"
.org 0x5a0890
    .importobj "./ccUJLegend.o"
.org 0x5a0c60
    .importobj "./DBG_PrintCCS.o"
.org 0x5a0d20
    .importobj "./sysWriteTextLan.o"
.org 0x5a0df0
    .importobj "./MCD.o"
.org 0x5a0f10
    .importobj "./BTL_Awakening.o"
.org 0x5a1000
    .importobj "./BTL_Mechanics.o"
.org 0x5a10a0
    .importobj "./sysWidescreen.o"

.org 0x4210e8
    .word SSK_Moveset
.org 0x41b738
    .word NRT_Moveset

.org 0x1a4ecc
    jal fixGlobalScrenFx
.org 0x2590e0
    jal fixGlobalScrenFx
.org 0x89f218
    jal fixScrenFx
    nop
    nop
.org 0x89d324
    jal fixScrenFx
    nop
    nop
.org 0x8995a0
    jal fixScrenFx
    nop
    nop
.org 0x89954c
    jal fixScrenFx
    nop
    nop
.org 0x899190
    jal fixScrenFx
    nop
    nop
.org 0x88c418
    jal fixScrenFx
    nop
    nop
.org 0x88bd6c
    jal fixScrenFx
    nop
    nop
.org 0x88bc00
    jal fixScrenFx
    nop
    nop
.org 0x8852cc
    jal fixScrenFx
    nop
    nop
.org 0x86a92c
    jal fixScrenFx
    nop
    nop
.org 0x8697ac
    jal fixScrenFx
    nop
    nop
.org 0x856668
    jal fixScrenFx
    nop
    nop
.org 0x8552cc
    jal fixScrenFx
    nop
    nop
.org 0x852fb4
    jal fixScrenFx
    nop
    nop
.org 0x852c14
    jal fixScrenFx
    nop
    nop
.org 0x851a48
    jal fixScrenFx
    nop
    nop
.org 0x8479f0
    jal fixScrenFx
    nop
    nop
.org 0x834d8c
    jal fixScrenFx
    nop
    nop
.org 0x82ace8
    jal fixScrenFx
    nop
    nop
.org 0x82a7c0
    jal fixScrenFx
    nop
    nop
.org 0x82784c
    jal fixScrenFx
    nop
    nop
.org 0x8241ec
    jal fixScrenFx
    nop
    nop
.org 0x8210b4
    jal fixScrenFx
    nop
    nop
.org 0x8196a0
    jal fixScrenFx
    nop
    nop
.org 0x816d3c
    jal fixScrenFx
    nop
    nop
.org 0x814d54
    jal fixScrenFx
    nop
    nop
.org 0x808f78
    jal fixScrenFx
    nop
    nop
.org 0x808a34
    jal fixScrenFx
    nop
    nop
.org 0x8055c8
    jal fixScrenFx
    nop
    nop
.org 0x804e98
    jal fixScrenFx
    nop
    nop
.org 0x7ffce8
    jal fixScrenFx
    nop
    nop
.org 0x7ffc78
    jal fixScrenFx
    nop
    nop
.org 0x7ff128
    jal fixScrenFx
    nop
    nop
.org 0x7fe8c4
    jal fixScrenFx
    nop
    nop
.org 0x7fe2a8
    jal fixScrenFx
    nop
    nop
.org 0x7fdbf0
    jal fixScrenFx
    nop
    nop
.org 0x7fd700
    jal fixScrenFx
    nop
    nop
.org 0x7fcf88
    jal fixScrenFx
    nop
    nop
.org 0x7fbc58
    jal fixScrenFx
    nop
    nop
.org 0x7f6fb0
    jal fixScrenFx
    nop
    nop
.org 0x7f39ec
    jal fixScrenFx
    nop
    nop
.org 0x7f33f4
    jal fixScrenFx
    nop
    nop
.org 0x7f253c
    jal fixScrenFx
    nop
    nop
.org 0x7f174c
    jal fixScrenFx
    nop
    nop
.org 0x7eb1cc
    jal fixScrenFx
    nop
    nop
.org 0x7e867c
    jal fixScrenFx
    nop
    nop
.org 0x7e70a0
    jal fixScrenFx
    nop
    nop
.org 0x7e1718
    jal fixScrenFx
    nop
    nop
.org 0x7e15b4
    jal fixScrenFx
    nop
    nop
.org 0x7d35c4
    jal fixScrenFx
    nop
    nop
.org 0x7cbe98
    jal fixScrenFx
    nop
    nop
.org 0x7c9c20
    jal fixScrenFx
    nop
    nop
.org 0x7c90bc
    jal fixScrenFx
    nop
    nop
.org 0x7c8300
    jal fixScrenFx
    nop
    nop
.org 0x7c2c64
    jal fixScrenFx
    nop
    nop
.org 0x7bd99c
    jal fixScrenFx
    nop
    nop
.org 0x7bd680
    jal fixScrenFx
    nop
    nop
.org 0x7bcaa0
    jal fixScrenFx
    nop
    nop
.org 0x7b84fc
    jal fixScrenFx
    nop
    nop
.org 0x7ad434
    jal fixScrenFx
    nop
    nop
.org 0x7a1f98
    jal fixScrenFx
    nop
    nop
.org 0x792a6c
    jal fixScrenFx
    nop
    nop
.org 0x784ee8
    jal fixScrenFx
    nop
    nop
.org 0x784e70
    jal fixScrenFx
    nop
    nop
.org 0x7822a4
    jal fixScrenFx
    nop
    nop
.org 0x7302fc
    jal fixScrenFx
    nop
    nop
.org 0x72d784
    jal fixScrenFx
    nop
    nop
.org 0x72a650
    jal fixScrenFx
    nop
    nop
.org 0x72a41c
    jal fixScrenFx
    nop
    nop
.org 0x72a3c8
    jal fixScrenFx
    nop
    nop
.org 0x72a198
    jal fixScrenFx
    nop
    nop
.org 0x70392c
    jal fixScrenFx
    nop
    nop
.org 0x703284
    jal fixScrenFx
    nop
    nop
.org 0x702210
    jal fixScrenFx
    nop
    nop
.org 0x7001d0
    jal fixScrenFx
    nop
    nop
.org 0x6fa660
    jal fixScrenFx
    nop
    nop
.org 0x6f4d60
    jal fixScrenFx
    nop
    nop
.org 0x6f35b4
    jal fixScrenFx
    nop
    nop
.org 0x6f32ec
    jal fixScrenFx
    nop
    nop
.org 0x6f3254
    jal fixScrenFx
    nop
    nop
.org 0x6f30ec
    jal fixScrenFx
    nop
    nop
.org 0x6f2ffc
    jal fixScrenFx
    nop
    nop
.org 0x6f2cdc
    jal fixScrenFx
    nop
    nop
.org 0x6f2c0c
    jal fixScrenFx
    nop
    nop
.org 0x6f2ae0
    jal fixScrenFx
    nop
    nop
.org 0x6f28f8
    jal fixScrenFx
    nop
    nop
.org 0x6f27cc
    jal fixScrenFx
    nop
    nop
.org 0x6f26bc
    jal fixScrenFx
    nop
    nop
.org 0x6f2598
    jal fixScrenFx
    nop
    nop
.org 0x6d3e2c
    jal fixScrenFx
    nop
    nop
.org 0x6d3d30
    jal fixScrenFx
    nop
    nop
.org 0x6d38ec
    jal fixScrenFx
    nop
    nop
.org 0x3cf954
    jal fixScrenFx
    nop
    nop
.org 0x3cef14
    jal fixScrenFx
    nop
    nop
.org 0x3ce7ac
    jal fixScrenFx
    nop
    nop
.org 0x3cd0f4
    jal fixScrenFx
    nop
    nop
.org 0x3a6760
    jal fixScrenFx
    nop
    nop
.org 0x3a47d4
    jal fixScrenFx
    nop
    nop
.org 0x3a3b7c
    jal fixScrenFx
    nop
    nop
.org 0x3a1cc4
    jal fixScrenFx
    nop
    nop
.org 0x3a1a3c
    jal fixScrenFx
    nop
    nop
.org 0x3a1944
    jal fixScrenFx
    nop
    nop
.org 0x3a170c
    jal fixScrenFx
    nop
    nop
.org 0x3a1610
    jal fixScrenFx
    nop
    nop
.org 0x39ff64
    jal fixScrenFx
    nop
    nop
.org 0x39d92c
    jal fixScrenFx
    nop
    nop
.org 0x39d8d0
    jal fixScrenFx
    nop
    nop
.org 0x39d874
    jal fixScrenFx
    nop
    nop
.org 0x39d2b8
    jal fixScrenFx
    nop
    nop
.org 0x39d268
    jal fixScrenFx
    nop
    nop
.org 0x39d1ec
    jal fixScrenFx
    nop
    nop
.org 0x39ca2c
    jal fixScrenFx
    nop
    nop
.org 0x3970bc
    jal fixScrenFx
    nop
    nop
.org 0x396d1c
    jal fixScrenFx
    nop
    nop
.org 0x396264
    jal fixScrenFx
    nop
    nop
.org 0x395eb0
    jal fixScrenFx
    nop
    nop
.org 0x3953ec
    jal fixScrenFx
    nop
    nop
.org 0x350f94
    jal fixScrenFx
    nop
    nop
.org 0x342940
    jal fixScrenFx
    nop
    nop
.org 0x342880
    jal fixScrenFx
    nop
    nop
.org 0x315a0c
    jal fixScrenFx
    nop
    nop
.org 0x3158a0
    jal fixScrenFx
    nop
    nop
.org 0x29e638
    jal fixScrenFx
    nop
    nop
.org 0x29d2ac
    jal fixScrenFx
    nop
    nop
.org 0x29d10c
    jal fixScrenFx
    nop
    nop
.org 0x298bdc
    jal fixScrenFx
    nop
    nop
.org 0x293064
    jal fixScrenFx
    nop
    nop
.org 0x281854
    jal fixScrenFx
    nop
    nop
.org 0x2129c4
    jal fixScrenFx
    nop
    nop
.org 0x211500
    jal fixScrenFx
    nop
    nop
.org 0x1f90b8
    jal fixScrenFx
    nop
    nop
.org 0x1f650c
    jal fixScrenFx
    nop
    nop
.org 0x1f4d58
    jal fixScrenFx
    nop
    nop
.org 0x1f18f8
    jal fixScrenFx
    nop
    nop
.org 0x1f1868
    jal fixScrenFx
    nop
    nop
.org 0x1f17dc
    jal fixScrenFx
    nop
    nop
.org 0x1e548c
    jal fixScrenFx
    nop
    nop
.org 0x1e1af0
    jal fixScrenFx
    nop
    nop
.org 0x1e1a44
    jal fixScrenFx
    nop
    nop
.org 0x1e192c
    jal fixScrenFx
    nop
    nop
.org 0x1e189c
    jal fixScrenFx
    nop
    nop
.org 0x105754
    jal fixScrenFx
    nop
    nop
.org 0x734218
    jal CheckPlayerAutoChakra
    dmove a0,s0
    ld ra,0x10(sp)
    lq s0,0x0(sp)
    jr ra
    addiu sp,sp,0x20
.org 0x21c86c
    jal ccSetPlayerAwakeningOnStartup
    nop
.org 0x1c5f18
    jal MCD_Apply_Size_Patches
    nop
    nop
.org 0x1a3d40
    jal Render_UJLegend
    nop
.org 0x1c2e20
    jal DBG_PrintCCS
    addiu a0,sp,0xCF
.org 0x3d3fe4
    jal sysWriteTextLan
    li a0,0x0
    ld ra,0x20(sp)
    lq s1,0x10(sp)
    lq s0,0x0(sp)
    jr ra
    addiu sp,sp,0xB0

.Close