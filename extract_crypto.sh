#!/bin/bash

# Huawei HG8245 Cryptographic Extraction Script
echo "=== Huawei HG8245 Crypto Extraction ==="
echo "Date: $(date)"
echo "Working Directory: $(pwd)"
echo

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to analyze a library for crypto functions
analyze_library() {
    local lib_file="$1"
    echo "[*] Analyzing: $(basename "$lib_file")"
    
    if [[ ! -f "$lib_file" ]]; then
        echo "[-] File not found: $lib_file"
        return 1
    fi
    
    echo "  File info: $(file "$lib_file")"
    
    # Try different tools to find symbols
    if command_exists objdump; then
        echo "  [+] Using objdump:"
        objdump -T "$lib_file" 2>/dev/null | grep -i "decrypt\|encrypt\|cipher\|crypto" | head -5 || echo "    No crypto symbols found"
    fi
    
    if command_exists nm; then
        echo "  [+] Using nm:"
        nm -D "$lib_file" 2>/dev/null | grep -i "decrypt\|encrypt\|cipher\|crypto" | head -5 || echo "    No crypto symbols found"
    fi
    
    # Look for interesting strings
    echo "  [+] Interesting strings:"
    strings "$lib_file" 2>/dev/null | grep -i "decrypt\|encrypt\|cipher\|aes\|des\|sha\|md5\|password" | head -10 || echo "    No interesting strings found"
    
    echo
}

# Function to test router connection
test_router() {
    echo "[*] Testing router connection at 192.168.1.1..."
    
    if command_exists curl; then
        response=$(curl -s -m 10 -I "http://192.168.1.1" 2>/dev/null)
        if [[ $? -eq 0 ]]; then
            echo "[+] Router is responding!"
            echo "$response" | head -5
        else
            echo "[-] Router not responding or unreachable"
        fi
    elif command_exists wget; then
        wget -q --timeout=10 --tries=1 "http://192.168.1.1" -O /dev/null 2>/dev/null
        if [[ $? -eq 0 ]]; then
            echo "[+] Router is responding!"
        else
            echo "[-] Router not responding or unreachable"
        fi
    else
        echo "[-] Neither curl nor wget available for testing"
    fi
    echo
}

# Function to search for encrypted passwords
find_passwords() {
    echo "[*] Searching for encrypted passwords..."
    
    # Search in common config locations
    search_dirs=(
        "squashfs-root-recovered/etc"
        "squashfs-root-recovered/config"
        "nand_extracted"
        "."
    )
    
    for dir in "${search_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            echo "  Searching in: $dir"
            find "$dir" -type f \( -name "*.conf" -o -name "*.cfg" -o -name "*.txt" -o -name "*.xml" \) -exec grep -l "password\|passwd\|admin" {} \; 2>/dev/null | head -5 | while read file; do
                echo "    Found in: $file"
                grep -i "password\|passwd\|admin" "$file" 2>/dev/null | head -3 | sed 's/^/      /'
            done
        fi
    done
    echo
}

# Function to create a test decryption program
create_test_program() {
    echo "[*] Creating test decryption program..."
    
    cat > test_decrypt.c << 'EOF'
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        printf("Usage: %s <library> <encrypted_string>\n", argv[0]);
        return 1;
    }
    
    printf("[*] Loading library: %s\n", argv[1]);
    void *handle = dlopen(argv[1], RTLD_LAZY | RTLD_GLOBAL);
    if (!handle) {
        printf("[-] dlopen failed: %s\n", dlerror());
        return 1;
    }
    
    // Mock missing symbols
    int HW_Mobilemng_SetTaskSource() { return 0; }
    int SRV_COMM_GetNewExportType() { return 0; }
    void* SRV_COMM_GetExportValue() { return NULL; }
    void* CAPI_SMP_GetWanInterfaceStatus() { return NULL; }
    
    typedef int (*decrypt_func_t)(const char *in, char *out);
    
    // Try primary function
    decrypt_func_t func1 = (decrypt_func_t)dlsym(handle, "CAPI_SMP_DecryptCipherText");
    if (func1) {
        printf("[+] Found CAPI_SMP_DecryptCipherText\n");
        char out[1024] = {0};
        int result = func1(argv[2], out);
        printf("    Result: %d, Output: '%s'\n", result, out);
    } else {
        printf("[-] CAPI_SMP_DecryptCipherText not found\n");
    }
    
    // Try fallback function
    decrypt_func_t func2 = (decrypt_func_t)dlsym(handle, "WAN_IF_DecryptPPPoEPassWord");
    if (func2) {
        printf("[+] Found WAN_IF_DecryptPPPoEPassWord\n");
        char out[1024] = {0};
        int result = func2(argv[2], out);
        printf("    Result: %d, Output: '%s'\n", result, out);
    } else {
        printf("[-] WAN_IF_DecryptPPPoEPassWord not found\n");
    }
    
    if (!func1 && !func2) {
        printf("[-] No decryption functions found in library\n");
    }
    
    dlclose(handle);
    return 0;
}
EOF
    
    echo "  [+] Test program created: test_decrypt.c"
    
    # Try to compile it
    if command_exists gcc; then
        gcc -o test_decrypt test_decrypt.c -ldl 2>/dev/null
        if [[ $? -eq 0 ]]; then
            echo "  [+] Successfully compiled: test_decrypt"
            
            # Test with some sample strings
            test_strings=("admin" "superonline" "telecomadmin" "password" "123456")
            
            for lib in "squashfs-root-recovered/lib/libhw_smp_capi.so" "squashfs-root-recovered/lib/libl3_base_api.so"; do
                if [[ -f "$lib" ]]; then
                    echo "  [*] Testing library: $(basename "$lib")"
                    for test_str in "${test_strings[@]}"; do
                        echo "    Testing: $test_str"
                        ./test_decrypt "$lib" "$test_str" 2>/dev/null | grep -E "Result:|Output:" | sed 's/^/      /'
                    done
                fi
            done
        else
            echo "  [-] Failed to compile test program"
        fi
    else
        echo "  [-] gcc not available for compilation"
    fi
    
    echo
}

# Main execution
main() {
    echo "Starting cryptographic analysis..."
    echo
    
    # Analyze the main crypto libraries
    echo "=== Library Analysis ==="
    analyze_library "squashfs-root-recovered/lib/libhw_smp_capi.so"
    analyze_library "squashfs-root-recovered/lib/libl3_base_api.so"
    
    # Look for other crypto-related libraries
    echo "=== Other Crypto Libraries ==="
    find squashfs-root-recovered/lib -name "*crypto*" -o -name "*cipher*" -o -name "*smp*" -o -name "*capi*" | head -10 | while read lib; do
        analyze_library "$lib"
    done
    
    # Test router connection
    echo "=== Router Connection Test ==="
    test_router
    
    # Search for passwords
    echo "=== Password Search ==="
    find_passwords
    
    # Create and test decryption program
    echo "=== Decryption Testing ==="
    create_test_program
    
    echo "=== Analysis Complete ==="
    echo "Results saved in current directory"
}

# Run main function
main "$@"
