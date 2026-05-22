#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

// Mock missing symbols so dlopen succeeds
int HW_Mobilemng_SetTaskSource() { return 0; }
int SRV_COMM_GetNewExportType() { return 0; }
void* SRV_COMM_GetExportValue() { return NULL; }
void* CAPI_SMP_GetWanInterfaceStatus() { return NULL; }

int main(int argc, char **argv) {
    if (argc < 3) {
        printf("Usage: %s <libTarget> <encrypted_string>\n", argv[0]);
        return 1;
    }

    void *handle = dlopen(argv[1], RTLD_LAZY | RTLD_GLOBAL);
    if (!handle) {
        printf("dlopen error for %s: %s\n", argv[1], dlerror());
        return 1;
    }
    printf("Loaded: %s\n", argv[1]);

    typedef int (*decrypt_func_t)(const char *in, char *out);
    decrypt_func_t decrypt_func = (decrypt_func_t)dlsym(handle, "CAPI_SMP_DecryptCipherText");

    if (!decrypt_func) {
        printf("Function CAPI_SMP_DecryptCipherText not found: %s\n", dlerror());
        
        decrypt_func = (decrypt_func_t)dlsym(handle, "WAN_IF_DecryptPPPoEPassWord");
        if (!decrypt_func) {
            printf("Fallback function WAN_IF_DecryptPPPoEPassWord not found either.\n");
            dlclose(handle);
            return 1;
        }
    }

    printf("Decrypt Function found!\n");
    char out_buf[1024] = {0};
    
    const char *input = argv[argc - 1];
    printf("Input: %s\n", input);
    int result = decrypt_func(input, out_buf);
    
    printf("Result code: %d\n", result);
    printf("Decrypted: %s\n", out_buf);

    return 0;
}
