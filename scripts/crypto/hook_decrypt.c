#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

// Mock symbols to avoid relocation errors
int HW_Mobilemng_SetTaskSource() { return 0; }
int SRV_COMM_GetNewExportType() { return 0; }
void* SRV_COMM_GetExportValue() { return NULL; }
void* CAPI_SMP_GetWanInterfaceStatus() { return NULL; }

typedef int (*decrypt_func_t)(const char *in, char *out);

void __attribute__((constructor)) init() {
    void *handle = dlopen("/lib/libhw_smp_capi.so", RTLD_LAZY);
    if (!handle) return;

    decrypt_func_t decrypt_func = (decrypt_func_t)dlsym(handle, "CAPI_SMP_DecryptCipherText");
    if (!decrypt_func) {
        dlclose(handle);
        return;
    }

    char output[1024];
    const char* targets[] = {
        "$2e-%/VNb~@!iMi_Q\\e*<X~<)LV7QkLJ>sVOE$:(0)\\U[2.7Ly9Fr/ZQLg-'g4sc>F.f5`D4][r{R'L}~<E5!QJ)MdjLpIt|\"MF+E&$",
        "$2c'7c'V@!eT/f~v4witR>@PZf3yk4YO^\"rC&mpD\"%k\\#CZS![J.{4=*0]Fj;MIEK}P\\aS!WILt5=7/&yXd=vdEoclQ*B%Tn%tkO\\:$"
    };

    printf("\n=== Decryption Hook Started ===\n");
    for (int i = 0; i < 2; i++) {
        memset(output, 0, sizeof(output));
        int result = decrypt_func(targets[i], output);
        printf("Target %d: %s\n", i+1, output);
    }
    printf("=== Decryption Hook Finished ===\n\n");

    dlclose(handle);
}
