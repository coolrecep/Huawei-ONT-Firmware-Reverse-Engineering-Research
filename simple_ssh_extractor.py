#!/usr/bin/env python3
"""
Simple SSH Key Extraction - Direct approach for router key extraction
"""

import subprocess
import time
import re
from pathlib import Path

def run_ssh_command(cmd, timeout=30):
    """Run SSH command with sshpass"""
    try:
        full_cmd = f"sshpass -p 'EP!99R4HLH9E' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ServerAliveInterval=30 sUser@192.168.1.1 '{cmd}'"
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("=== Simple SSH Key Extraction ===")
    
    # Test basic connection
    print("[*] Testing SSH connection...")
    stdout, stderr, code = run_ssh_command("echo 'SSH_TEST'")
    
    if code == 0 and "SSH_TEST" in stdout:
        print("[+] SSH connection successful!")
    else:
        print(f"[-] SSH failed: {stderr}")
        return
    
    # Get basic info
    print("[*] Getting system info...")
    commands = {
        "processes": "ps aux | head -20",
        "crypto_procs": "ps aux | grep -E 'smp|crypto|cipher' | head -10",
        "libs": "ls -la /lib/libhw_smp_capi.so /lib/libl3_base_api.so 2>/dev/null",
        "config": "find /etc -name '*.conf' | head -10",
        "uci": "uci show 2>/dev/null | head -20"
    }
    
    results = {}
    for name, cmd in commands.items():
        stdout, stderr, code = run_ssh_command(cmd)
        if code == 0:
            results[name] = stdout
            print(f"  [+] Got {name}")
        else:
            print(f"  [-] Failed {name}: {stderr}")
    
    # Look for keys in configuration
    print("[*] Searching for keys in configuration...")
    if "uci" in results:
        uci_data = results["uci"]
        key_patterns = [
            r'password[=:]\s*([^\s\n]+)',
            r'key[=:]\s*([^\s\n]+)',
            r'secret[=:]\s*([^\s\n]+)',
            r'psk[=:]\s*([^\s\n]+)'
        ]
        
        keys_found = []
        for pattern in key_patterns:
            matches = re.findall(pattern, uci_data, re.IGNORECASE)
            for match in matches:
                keys_found.append(match)
        
        if keys_found:
            print(f"  [+] Found {len(keys_found)} potential keys in UCI config")
            for i, key in enumerate(keys_found[:10], 1):
                print(f"    {i}. {key}")
    
    # Create and run crypto test
    print("[*] Testing crypto functions...")
    crypto_test = '''
cat > /tmp/simple_crypto_test.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

int HW_Mobilemng_SetTaskSource() { return 0; }
int SRV_COMM_GetNewExportType() { return 0; }
void* SRV_COMM_GetExportValue() { return NULL; }
void* CAPI_SMP_GetWanInterfaceStatus() { return NULL; }

int main() {
    void *handle;
    int (*decrypt_func)(const char*, char*);
    char output[1024];
    
    printf("=== Simple Crypto Test ===\\n");
    
    // Test primary function
    handle = dlopen("/lib/libhw_smp_capi.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "CAPI_SMP_DecryptCipherText");
        if (decrypt_func) {
            printf("Testing CAPI_SMP_DecryptCipherText...\\n");
            int result = decrypt_func("test", output);
            printf("Result: %d, Output: '%s'\\n", result, output);
            
            // Test with common encrypted strings
            const char* test_strings[] = {"admin", "superonline", "password", "123456"};
            for (int i = 0; i < 4; i++) {
                memset(output, 0, sizeof(output));
                result = decrypt_func(test_strings[i], output);
                printf("Input: %-12s -> Result: %d, Output: '%s'\\n", test_strings[i], result, output);
            }
        }
        dlclose(handle);
    }
    
    return 0;
}
EOF

gcc -o /tmp/simple_crypto_test /tmp/simple_crypto_test.c -ldl 2>/dev/null
if [ -f /tmp/simple_crypto_test ]; then
    echo "Crypto test compiled successfully"
    /tmp/simple_crypto_test
    rm -f /tmp/simple_crypto_test /tmp/simple_crypto_test.c
else
    echo "Failed to compile crypto test"
fi
'''
    
    stdout, stderr, code = run_ssh_command(crypto_test, timeout=60)
    if code == 0:
        print("  [+] Crypto test completed")
        results["crypto_test"] = stdout
    else:
        print(f"  [-] Crypto test failed: {stderr}")
    
    # Save results
    print("[*] Saving results...")
    output_dir = Path("/home/recep/Masaüstü/Firmware/simple_ssh_extraction")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "results.txt", "w") as f:
        f.write("=== Simple SSH Key Extraction Results ===\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for name, data in results.items():
            f.write(f"=== {name.upper()} ===\n")
            f.write(data)
            f.write("\n\n")
    
    print(f"[+] Results saved to: {output_dir}")
    
    # Show summary
    print("\n=== SUMMARY ===")
    print(f"Commands executed: {len(results)}")
    print(f"Keys in config: {len(keys_found) if 'keys_found' in locals() else 0}")
    print(f"Crypto test: {'Completed' if 'crypto_test' in results else 'Failed'}")

if __name__ == "__main__":
    main()
