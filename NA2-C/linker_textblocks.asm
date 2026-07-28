.ps2
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
BASE_ADDRESS               equ 0x5A01D0
SSK_Moveset_Hook_Address   equ 0x4210E8
NRT_Moveset_Hook_Address   equ 0x41B738
Render_UJLegend_Hook       equ 0x001A3D40
DBG_PrintCCS_Hook          equ 0x001C2E20
sysWriteTextLan_Hook       equ 0x003D3FE4
.create "textblocks.bin", 0x5a01d0
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
.close