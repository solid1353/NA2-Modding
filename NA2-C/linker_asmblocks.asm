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
.definelabel SSK_Moveset, 0x5a01d0
.definelabel NRT_Moveset, 0x5a0530
.definelabel Render_UJLegend, 0x5a0890
.definelabel DBG_PrintCCS, 0x5a0c60
.definelabel sysWriteTextLan, 0x5a0d20
.definelabel MCD_Apply_Size_Patches, 0x5a0df0
.definelabel ccSetPlayerAwakeningOnStartup, 0x5a0f10
.definelabel CheckPlayerAutoChakra, 0x5a1000
.definelabel fixGlobalScrenFx, 0x5a10b8
.definelabel fixScrenFx, 0x5a10a0
.create "asmblock_1A4ECC.bin", 1724108
.org 0x1a4ecc
    jal fixGlobalScrenFx
.close
.create "asmblock_2590E0.bin", 2461920
.org 0x2590e0
    jal fixGlobalScrenFx
.close
.create "asmblock_89F218.bin", 9040408
.org 0x89f218
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_89D324.bin", 9032484
.org 0x89d324
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_8995A0.bin", 9016736
.org 0x8995a0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_89954C.bin", 9016652
.org 0x89954c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_899190.bin", 9015696
.org 0x899190
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_88C418.bin", 8963096
.org 0x88c418
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_88BD6C.bin", 8961388
.org 0x88bd6c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_88BC00.bin", 8961024
.org 0x88bc00
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_8852CC.bin", 8934092
.org 0x8852cc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_86A92C.bin", 8825132
.org 0x86a92c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_8697AC.bin", 8820652
.org 0x8697ac
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_856668.bin", 8742504
.org 0x856668
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_8552CC.bin", 8737484
.org 0x8552cc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_852FB4.bin", 8728500
.org 0x852fb4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_852C14.bin", 8727572
.org 0x852c14
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_851A48.bin", 8723016
.org 0x851a48
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_8479F0.bin", 8681968
.org 0x8479f0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_834D8C.bin", 8605068
.org 0x834d8c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_82ACE8.bin", 8563944
.org 0x82ace8
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_82A7C0.bin", 8562624
.org 0x82a7c0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_82784C.bin", 8550476
.org 0x82784c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_8241EC.bin", 8536556
.org 0x8241ec
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_8210B4.bin", 8523956
.org 0x8210b4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_8196A0.bin", 8492704
.org 0x8196a0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_816D3C.bin", 8482108
.org 0x816d3c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_814D54.bin", 8473940
.org 0x814d54
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_808F78.bin", 8425336
.org 0x808f78
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_808A34.bin", 8423988
.org 0x808a34
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_8055C8.bin", 8410568
.org 0x8055c8
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_804E98.bin", 8408728
.org 0x804e98
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7FFCE8.bin", 8387816
.org 0x7ffce8
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7FFC78.bin", 8387704
.org 0x7ffc78
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7FF128.bin", 8384808
.org 0x7ff128
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7FE8C4.bin", 8382660
.org 0x7fe8c4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7FE2A8.bin", 8381096
.org 0x7fe2a8
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7FDBF0.bin", 8379376
.org 0x7fdbf0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7FD700.bin", 8378112
.org 0x7fd700
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7FCF88.bin", 8376200
.org 0x7fcf88
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7FBC58.bin", 8371288
.org 0x7fbc58
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7F6FB0.bin", 8351664
.org 0x7f6fb0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7F39EC.bin", 8337900
.org 0x7f39ec
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7F33F4.bin", 8336372
.org 0x7f33f4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7F253C.bin", 8332604
.org 0x7f253c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7F174C.bin", 8329036
.org 0x7f174c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7EB1CC.bin", 8303052
.org 0x7eb1cc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7E867C.bin", 8291964
.org 0x7e867c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7E70A0.bin", 8286368
.org 0x7e70a0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7E1718.bin", 8263448
.org 0x7e1718
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7E15B4.bin", 8263092
.org 0x7e15b4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7D35C4.bin", 8205764
.org 0x7d35c4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7CBE98.bin", 8175256
.org 0x7cbe98
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7C9C20.bin", 8166432
.org 0x7c9c20
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7C90BC.bin", 8163516
.org 0x7c90bc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7C8300.bin", 8160000
.org 0x7c8300
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7C2C64.bin", 8137828
.org 0x7c2c64
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7BD99C.bin", 8116636
.org 0x7bd99c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7BD680.bin", 8115840
.org 0x7bd680
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7BCAA0.bin", 8112800
.org 0x7bcaa0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7B84FC.bin", 8094972
.org 0x7b84fc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7AD434.bin", 8049716
.org 0x7ad434
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7A1F98.bin", 8003480
.org 0x7a1f98
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_792A6C.bin", 7940716
.org 0x792a6c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_784EE8.bin", 7884520
.org 0x784ee8
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_784E70.bin", 7884400
.org 0x784e70
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7822A4.bin", 7873188
.org 0x7822a4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7302FC.bin", 7537404
.org 0x7302fc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_72D784.bin", 7526276
.org 0x72d784
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_72A650.bin", 7513680
.org 0x72a650
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_72A41C.bin", 7513116
.org 0x72a41c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_72A3C8.bin", 7513032
.org 0x72a3c8
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_72A198.bin", 7512472
.org 0x72a198
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_70392C.bin", 7354668
.org 0x70392c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_703284.bin", 7352964
.org 0x703284
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_702210.bin", 7348752
.org 0x702210
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_7001D0.bin", 7340496
.org 0x7001d0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6FA660.bin", 7317088
.org 0x6fa660
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F4D60.bin", 7294304
.org 0x6f4d60
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F35B4.bin", 7288244
.org 0x6f35b4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F32EC.bin", 7287532
.org 0x6f32ec
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F3254.bin", 7287380
.org 0x6f3254
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F30EC.bin", 7287020
.org 0x6f30ec
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F2FFC.bin", 7286780
.org 0x6f2ffc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F2CDC.bin", 7285980
.org 0x6f2cdc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F2C0C.bin", 7285772
.org 0x6f2c0c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F2AE0.bin", 7285472
.org 0x6f2ae0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F28F8.bin", 7284984
.org 0x6f28f8
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F27CC.bin", 7284684
.org 0x6f27cc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F26BC.bin", 7284412
.org 0x6f26bc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6F2598.bin", 7284120
.org 0x6f2598
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6D3E2C.bin", 7159340
.org 0x6d3e2c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6D3D30.bin", 7159088
.org 0x6d3d30
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_6D38EC.bin", 7157996
.org 0x6d38ec
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3CF954.bin", 3995988
.org 0x3cf954
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3CEF14.bin", 3993364
.org 0x3cef14
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3CE7AC.bin", 3991468
.org 0x3ce7ac
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3CD0F4.bin", 3985652
.org 0x3cd0f4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3A6760.bin", 3827552
.org 0x3a6760
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3A47D4.bin", 3819476
.org 0x3a47d4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3A3B7C.bin", 3816316
.org 0x3a3b7c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3A1CC4.bin", 3808452
.org 0x3a1cc4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3A1A3C.bin", 3807804
.org 0x3a1a3c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3A1944.bin", 3807556
.org 0x3a1944
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3A170C.bin", 3806988
.org 0x3a170c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3A1610.bin", 3806736
.org 0x3a1610
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_39FF64.bin", 3800932
.org 0x39ff64
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_39D92C.bin", 3791148
.org 0x39d92c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_39D8D0.bin", 3791056
.org 0x39d8d0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_39D874.bin", 3790964
.org 0x39d874
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_39D2B8.bin", 3789496
.org 0x39d2b8
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_39D268.bin", 3789416
.org 0x39d268
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_39D1EC.bin", 3789292
.org 0x39d1ec
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_39CA2C.bin", 3787308
.org 0x39ca2c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3970BC.bin", 3764412
.org 0x3970bc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_396D1C.bin", 3763484
.org 0x396d1c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_396264.bin", 3760740
.org 0x396264
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_395EB0.bin", 3759792
.org 0x395eb0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3953EC.bin", 3757036
.org 0x3953ec
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_350F94.bin", 3477396
.org 0x350f94
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_342940.bin", 3418432
.org 0x342940
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_342880.bin", 3418240
.org 0x342880
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_315A0C.bin", 3234316
.org 0x315a0c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_3158A0.bin", 3233952
.org 0x3158a0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_29E638.bin", 2745912
.org 0x29e638
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_29D2AC.bin", 2740908
.org 0x29d2ac
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_29D10C.bin", 2740492
.org 0x29d10c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_298BDC.bin", 2722780
.org 0x298bdc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_293064.bin", 2699364
.org 0x293064
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_281854.bin", 2627668
.org 0x281854
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_2129C4.bin", 2173380
.org 0x2129c4
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_211500.bin", 2168064
.org 0x211500
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_1F90B8.bin", 2068664
.org 0x1f90b8
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_1F650C.bin", 2057484
.org 0x1f650c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_1F4D58.bin", 2051416
.org 0x1f4d58
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_1F18F8.bin", 2038008
.org 0x1f18f8
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_1F1868.bin", 2037864
.org 0x1f1868
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_1F17DC.bin", 2037724
.org 0x1f17dc
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_1E548C.bin", 1987724
.org 0x1e548c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_1E1AF0.bin", 1972976
.org 0x1e1af0
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_1E1A44.bin", 1972804
.org 0x1e1a44
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_1E192C.bin", 1972524
.org 0x1e192c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_1E189C.bin", 1972380
.org 0x1e189c
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_105754.bin", 1070932
.org 0x105754
    jal fixScrenFx
    nop
    nop
.close
.create "asmblock_734218.bin", 7553560
.org 0x734218
    jal CheckPlayerAutoChakra
    dmove a0,s0
    ld ra,0x10(sp)
    lq s0,0x0(sp)
    jr ra
    addiu sp,sp,0x20
.close
.create "asmblock_21C86C.bin", 2213996
.org 0x21c86c
    jal ccSetPlayerAwakeningOnStartup
    nop
.close
.create "asmblock_1C5F18.bin", 1859352
.org 0x1c5f18
    jal MCD_Apply_Size_Patches
    nop
    nop
.close
.create "asmblock_1A3D40.bin", 1719616
.org 0x1a3d40
    jal Render_UJLegend
    nop
.close
.create "asmblock_1C2E20.bin", 1846816
.org 0x1c2e20
    jal DBG_PrintCCS
    addiu a0,sp,0xCF
.close
.create "asmblock_3D3FE4.bin", 4014052
.org 0x3d3fe4
    jal sysWriteTextLan
    li a0,0x0
    ld ra,0x20(sp)
    lq s1,0x10(sp)
    lq s0,0x0(sp)
    jr ra
    addiu sp,sp,0xB0
.close