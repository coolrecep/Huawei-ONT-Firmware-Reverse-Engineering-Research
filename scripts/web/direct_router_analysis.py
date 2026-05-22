#!/usr/bin/env python3
"""
Direct Router Analysis Script
Manually connects to router and extracts cryptographic information
"""

import subprocess
import time
import re

def run_ssh_command(host, user, password, command, timeout=30):
    """Run SSH command directly using subprocess"""
    try:
        # Using sshpass for password authentication
        cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {user}@{host} '{command}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    host = "192.168.1.1"
    user = "sUser"
    password = "EP!99R4HLH9E"
    
    print("=== Direct Router Crypto Analysis ===")
    print(f"Connecting to {host} as {user}")
    
    # Test connection
    print("\n[*] Testing SSH connection...")
    stdout, stderr, code = run_ssh_command(host, user, password, "echo 'CONNECTION_OK'")
    
    if code != 0 or "CONNECTION_OK" not in stdout:
        print(f"[-] SSH connection failed: {stderr}")
        return
    
    print("[+] SSH connection successful!")
    
    # 1. Get system info
    print("\n[*] Getting system information...")
    commands = {
        "system_info": "uname -a",
        "processes": "ps aux | head -20",
        "crypto_libs": "find /lib /usr/lib -name '*crypto*' -o -name '*cipher*' -o -name '*smp*' -o -name '*capi*' 2>/dev/null",
        "smp_lib_check": "ls -la /lib/libhw_smp_capi.so 2>/dev/null",
        "l3_lib_check": "ls -la /lib/libl3_base_api.so 2>/dev/null"
    }
    
    results = {}
    for name, cmd in commands.items():
        print(f"  Executing: {cmd}")
        stdout, stderr, code = run_ssh_command(host, user, password, cmd)
        if code == 0 and stdout:
            results[name] = stdout
            print(f"    Success: {len(stdout)} bytes")
        else:
            print(f"    Failed: {stderr}")
    
    # 2. Extract strings from crypto libraries
    print("\n[*] Extracting strings from crypto libraries...")
    string_commands = {
        "smp_strings": "strings /lib/libhw_smp_capi.so 2>/dev/null | grep -iE 'key|password|secret|decrypt|encrypt|cipher' | head -20",
        "l3_strings": "strings /lib/libl3_base_api.so 2>/dev/null | grep -iE 'key|password|secret|decrypt|encrypt|cipher' | head -20",
        "all_strings": "strings /lib/libhw_smp_capi.so 2>/dev/null | head -50"
    }
    
    for name, cmd in string_commands.items():
        print(f"  Executing: {name}")
        stdout, stderr, code = run_ssh_command(host, user, password, cmd)
        if code == 0 and stdout:
            results[name] = stdout
            print(f"    Found {len(stdout.split())} strings")
        else:
            print(f"    Failed: {stderr}")
    
    # 3. Find crypto processes
    print("\n[*] Finding crypto processes...")
    process_commands = {
        "crypto_procs": "ps aux | grep -iE 'crypto|cipher|decrypt|encrypt|smp|capi' | grep -v grep",
        "smp_procs": "ps aux | grep smp | grep -v grep"
    }
    
    for name, cmd in process_commands.items():
        stdout, stderr, code = run_ssh_command(host, user, password, cmd)
        if code == 0 and stdout:
            results[name] = stdout
            print(f"    Found {len(stdout.splitlines())} processes")
    
    # 4. Test decryption functions
    print("\n[*] Testing decryption functions...")
    test_script = '''
cat > /tmp/test_decrypt.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

int main() {
    void *handle;
    int (*decrypt_func)(const char*, char*);
    char output[1024];
    int result;
    
    printf("Testing CAPI_SMP_DecryptCipherText...\\n");
    handle = dlopen("/lib/libhw_smp_capi.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "CAPI_SMP_DecryptCipherText");
        if (decrypt_func) {
            result = decrypt_func("test", output);
            printf("Result: %d, Output: '%s'\\n", result, output);
        } else {
            printf("Function not found\\n");
        }
        dlclose(handle);
    } else {
        printf("Library load failed\\n");
    }
    
    printf("\\nTesting WAN_IF_DecryptPPPoEPassWord...\\n");
    handle = dlopen("/lib/libl3_base_api.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "WAN_IF_DecryptPPPoEPassWord");
        if (decrypt_func) {
            result = decrypt_func("test", output);
            printf("Result: %d, Output: '%s'\\n", result, output);
        } else {
            printf("Function not found\\n");
        }
        dlclose(handle);
    } else {
        printf("Library load failed\\n");
    }
    
    return 0;
}
EOF
gcc -o /tmp/test_decrypt /tmp/test_decrypt.c -ldl 2>/dev/null
/tmp/test_decrypt
rm -f /tmp/test_decrypt.c /tmp/test_decrypt
'''
    
    stdout, stderr, code = run_ssh_command(host, user, password, test_script, timeout=60)
    if code == 0:
        results["decryption_test"] = stdout
        print("    Decryption test completed")
    else:
        print(f"    Decryption test failed: {stderr}")
    
    # 5. Look for configuration files with passwords
    print("\n[*] Searching for password configurations...")
    config_commands = {
        "wifi_configs": "find /etc -name '*.conf' -exec grep -l 'password\\|psk\\|key' {} \\; 2>/dev/null | head -10",
        "uci_passwords": "uci show 2>/dev/null | grep -i password | head -10",
        "env_vars": "env | grep -iE 'password|key|secret' | head -10"
    }
    
    for name, cmd in config_commands.items():
        stdout, stderr, code = run_ssh_command(host, user, password, cmd)
        if code == 0 and stdout:
            results[name] = stdout
            print(f"    Found configuration data")
    
    # 6. Memory analysis
    print("\n[*] Analyzing process memory...")
    memory_cmd = '''
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
    if [ -f "/proc/$pid/cmdline" ]; then
        cmdline=$(cat /proc/$pid/cmdline | tr '\\0' ' ')
        if echo "$cmdline" | grep -qiE 'crypto|cipher|decrypt|encrypt|smp|capi'; then
            echo "PID $pid: $cmdline"
            # Try to read some memory (may fail due to permissions)
            if [ -r "/proc/$pid/mem" ]; then
                echo "  Memory readable, searching for keys..."
                strings /proc/$pid/mem 2>/dev/null | grep -E '[A-Za-z0-9+/]{32,}=' | head -5 | sed 's/^/    /'
            fi
        fi
    fi
done
'''
    
    stdout, stderr, code = run_ssh_command(host, user, password, memory_cmd, timeout=45)
    if code == 0:
        results["memory_analysis"] = stdout
        print("    Memory analysis completed")
    
    # Save results
    print("\n[*] Saving results...")
    with open("/home/recep/Masaüstü/Firmware/direct_router_analysis.txt", "w") as f:
        f.write("=== Huawei HG8245 Direct Router Analysis ===\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Host: {host}\n\n")
        
        for name, data in results.items():
            f.write(f"=== {name.upper()} ===\n")
            f.write(data)
            f.write("\n\n")
    
    print("[+] Analysis complete! Results saved to direct_router_analysis.txt")
    
    # Print summary
    print("\n=== ANALYSIS SUMMARY ===")
    print(f"System info gathered: {'system_info' in results}")
    print(f"Crypto libraries found: {'crypto_libs' in results and len(results['crypto_libs'].split())}")
    print(f"SMP strings extracted: {'smp_strings' in results}")
    print(f"Crypto processes found: {'crypto_procs' in results}")
    print(f"Decryption test completed: {'decryption_test' in results}")
    print(f"Configuration data found: {'wifi_configs' in results}")
    print(f"Memory analysis completed: {'memory_analysis' in results}")
    
    # Show some key findings
    if 'crypto_libs' in results:
        print(f"\n=== CRYPTO LIBRARIES ===")
        for lib in results['crypto_libs'].split('\n')[:10]:
            if lib.strip():
                print(f"  {lib}")
    
    if 'smp_strings' in results:
        print(f"\n=== SMP CAPI STRINGS ===")
        for string in results['smp_strings'].split('\n')[:10]:
            if string.strip():
                print(f"  {string}")
    
    if 'decryption_test' in results:
        print(f"\n=== DECRYPTION TEST RESULTS ===")
        print(results['decryption_test'])

if __name__ == "__main__":
    main()
