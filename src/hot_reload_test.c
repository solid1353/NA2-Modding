#include "runtime.h"

#ifndef NA2_INJECTION_BUILD_ID
#define NA2_INJECTION_BUILD_ID 0x4E413232u
#endif

static volatile unsigned int last_build_id;

void hotReloadTest(void){
    if (last_build_id != NA2_INJECTION_BUILD_ID) {
        last_build_id = NA2_INJECTION_BUILD_ID;
        eeKernelPrint("NA2.28 C hot reload active\n");
    }
}
