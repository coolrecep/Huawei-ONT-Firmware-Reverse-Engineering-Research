#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <string.h>

int main() {
    printf("Testing loaded libhw_smp_capi.so...\n");
    void *handle = dlopen("./squashfs-root-recovered/lib/libhw_smp_capi.so", RTLD_LAZY);
    if (!handle) {
        printf("Failed to load libhw_smp_capi.so: %s\n", dlerror());
        return 1;
    }
    
    int (*decrypt)(const char *, char *) = dlsym(handle, "CAPI_SMP_DecryptCipherText");
    if (!decrypt) {
        printf("Symbol not found.\n");
        return 1;
    }
    
    char out[1024] = {0};
    int res = decrypt("$2c'7c'V@!eT/f~v4witR>@PZf3yk4YO^\"rC&mpD\"%k\\#CZS![J.{4=*0]Fj;MIEK}P\\aS!WILt5=7/&yXd=vdEoclQ*B%Tn%tkO\\:$", out);
    printf("Res: %d\nOut: %s\n", res, out);
    return 0;
}
