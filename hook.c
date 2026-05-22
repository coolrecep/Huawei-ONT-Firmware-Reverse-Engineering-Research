#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

__attribute__((constructor)) void my_init() {
    const char *input = getenv("PW_TO_DECRYPT");
    if (input) {
        printf("[+] Hook loaded! Decrypting: %s\n", input);
        
        void *handle = dlopen("libhw_smp_capi.so", RTLD_LAZY | RTLD_GLOBAL);
        if (!handle) {
            printf("[-] dlopen libhw_smp_capi.so failed: %s\n", dlerror());
            
            // Try another library that has the fallback
            handle = dlopen("libl3_base_api.so", RTLD_LAZY | RTLD_GLOBAL);
            if (!handle) {
                printf("[-] dlopen libl3_base_api.so failed: %s\n", dlerror());
                exit(1);
            }
        }
        
        typedef int (*decrypt_func_t)(const char *in, char *out);
        decrypt_func_t decrypt_func = (decrypt_func_t)dlsym(handle, "CAPI_SMP_DecryptCipherText");
        
        if (!decrypt_func) {
            printf("[-] CAPI_SMP_DecryptCipherText not found, trying fallback\n");
            decrypt_func = (decrypt_func_t)dlsym(handle, "WAN_IF_DecryptPPPoEPassWord");
            if (!decrypt_func) {
                printf("[-] Fallback also not found!\n");
                exit(1);
            }
        }

        char out_buf[1024] = {0};
        int result = decrypt_func(input, out_buf);
        
        printf("[+] Result code: %d\n", result);
        printf("[+] Decrypted: %s\n", out_buf);
        exit(0);
    }
}
