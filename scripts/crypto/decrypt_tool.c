#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

typedef int (*decrypt_func_t)(const char *in, char *out);

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <ciphertext>\n", argv[0]);
        return 1;
    }

    void *handle = dlopen("./libhw_smp_capi.so", RTLD_LAZY);
    if (!handle) {
        fprintf(stderr, "Error loading libhw_smp_capi.so: %s\n", dlerror());
        return 1;
    }

    decrypt_func_t decrypt_func = (decrypt_func_t)dlsym(handle, "CAPI_SMP_DecryptCipherText");
    if (!decrypt_func) {
        fprintf(stderr, "Error finding symbol CAPI_SMP_DecryptCipherText: %s\n", dlerror());
        dlclose(handle);
        return 1;
    }

    char output[1024];
    memset(output, 0, sizeof(output));

    int result = decrypt_func(argv[1], output);
    printf("Result: %d\n", result);
    printf("Decrypted: %s\n", output);

    dlclose(handle);
    return 0;
}
