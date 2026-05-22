#!/bin/bash

# Simple Router Crypto Extraction Script
# Uses basic telnet/ssh tools to extract cryptographic information

ROUTER_IP="192.168.1.1"
USERNAME="sUser"
PASSWORD="EP!99R4HLH9E"
OUTPUT_DIR="/home/recep/Masaüstü/Firmware/router_extraction"

echo "=== Huawei HG8245 Router Crypto Extraction ==="
echo "Router: $ROUTER_IP"
echo "User: $USERNAME"
echo "Output: $OUTPUT_DIR"
echo

# Create output directory
mkdir -p "$OUTPUT_DIR"/{configs,memory,processes,libraries}

# Function to execute SSH command
ssh_exec() {
    local cmd="$1"
    local timeout="${2:-30}"
    
    echo "[*] Executing: $cmd"
    timeout "$timeout" sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$USERNAME@$ROUTER_IP" "$cmd" 2>/dev/null
}

# Function to execute Telnet command
telnet_exec() {
    local cmd="$1"
    {
        sleep 2
        echo "$USERNAME"
        sleep 2
        echo "$PASSWORD"
        sleep 2
        echo "$cmd"
        sleep 3
        echo "exit"
    } | timeout 15 telnet "$ROUTER_IP" 2>/dev/null | grep -v "login:" | grep -v "Password:"
}

# Test connections
echo "[*] Testing SSH connection..."
if ssh_exec "echo 'SSH_OK'" | grep -q "SSH_OK"; then
    echo "[+] SSH connection successful"
    USE_SSH=true
else
    echo "[-] SSH failed, trying Telnet..."
    if telnet_exec "echo 'TELNET_OK'" | grep -q "TELNET_OK"; then
        echo "[+] Telnet connection successful"
        USE_SSH=false
    else
        echo "[-] Both SSH and Telnet failed"
        exit 1
    fi
fi

# Execute command based on connection type
exec_cmd() {
    if [ "$USE_SSH" = true ]; then
        ssh_exec "$1"
    else
        telnet_exec "$1"
    fi
}

# 1. System Information
echo "[*] Gathering system information..."
exec_cmd "uname -a" > "$OUTPUT_DIR/configs/uname.txt"
exec_cmd "ps aux" > "$OUTPUT_DIR/configs/ps.txt"
exec_cmd "mount" > "$OUTPUT_DIR/configs/mount.txt"
exec_cmd "df -h" > "$OUTPUT_DIR/configs/df.txt"
exec_cmd "free -m" > "$OUTPUT_DIR/configs/free.txt"
exec_cmd "netstat -tlnp" > "$OUTPUT_DIR/configs/netstat.txt"

# 2. Find crypto processes
echo "[*] Finding crypto processes..."
exec_cmd "ps aux | grep -i crypto" > "$OUTPUT_DIR/processes/crypto_processes.txt"
exec_cmd "ps aux | grep -i cipher" > "$OUTPUT_DIR/processes/cipher_processes.txt"
exec_cmd "ps aux | grep -i decrypt" > "$OUTPUT_DIR/processes/decrypt_processes.txt"
exec_cmd "ps aux | grep -i smp" > "$OUTPUT_DIR/processes/smp_processes.txt"
exec_cmd "ps aux | grep -i capi" > "$OUTPUT_DIR/processes/capi_processes.txt"

# 3. Configuration files
echo "[*] Dumping configuration files..."
exec_cmd "cat /etc/passwd" > "$OUTPUT_DIR/configs/passwd.txt" 2>/dev/null
exec_cmd "cat /etc/shadow" > "$OUTPUT_DIR/configs/shadow.txt" 2>/dev/null
exec_cmd "find /etc -name '*.conf' -exec cat {} \;" > "$OUTPUT_DIR/configs/all_confs.txt" 2>/dev/null
exec_cmd "find /etc -name 'config*' -exec cat {} \;" > "$OUTPUT_DIR/configs/config_files.txt" 2>/dev/null

# 4. Library analysis
echo "[*] Analyzing cryptographic libraries..."
exec_cmd "find /lib /usr/lib -name '*crypto*' -o -name '*cipher*' -o -name '*smp*' -o -name '*capi*'" > "$OUTPUT_DIR/libraries/crypto_libs.txt"
exec_cmd "strings /lib/libhw_smp_capi.so 2>/dev/null | grep -iE 'key|password|secret|decrypt'" > "$OUTPUT_DIR/libraries/smp_capi_strings.txt" 2>/dev/null
exec_cmd "strings /lib/libl3_base_api.so 2>/dev/null | grep -iE 'key|password|secret|decrypt'" > "$OUTPUT_DIR/libraries/l3_base_strings.txt" 2>/dev/null

# 5. Memory analysis (find PIDs first)
echo "[*] Analyzing process memory..."
exec_cmd "for pid in \$(ls /proc | grep -E '^[0-9]+\$'); do if [ -f \"/proc/\$pid/cmdline\" ]; then cmdline=\$(cat /proc/\$pid/cmdline | tr '\\0' ' '); if echo \"\$cmdline\" | grep -qiE 'crypto|cipher|decrypt|encrypt|smp|capi'; then echo \"\$pid:\$cmdline\"; fi; fi; done" > "$OUTPUT_DIR/processes/crypto_pids.txt"

# Extract memory maps for crypto processes
if [ -s "$OUTPUT_DIR/processes/crypto_pids.txt" ]; then
    while IFS=':' read -r pid cmdline; do
        if [ -n "$pid" ]; then
            echo "[*] Analyzing PID $pid: $cmdline"
            exec_cmd "cat /proc/$pid/maps 2>/dev/null | head -20" > "$OUTPUT_DIR/memory/maps_$pid.txt" 2>/dev/null
            
            # Search for key patterns in memory
            exec_cmd "grep -a -E '[A-Za-z0-9+/]{32,}=' /proc/$pid/mem 2>/dev/null | head -10" > "$OUTPUT_DIR/memory/base64_keys_$pid.txt" 2>/dev/null
            exec_cmd "grep -a -E '[0-9a-fA-F]{32,}' /proc/$pid/mem 2>/dev/null | head -10" > "$OUTPUT_DIR/memory/hex_keys_$pid.txt" 2>/dev/null
        fi
    done < "$OUTPUT_DIR/processes/crypto_pids.txt"
fi

# 6. WiFi passwords
echo "[*] Extracting WiFi information..."
exec_cmd "iwconfig 2>/dev/null" > "$OUTPUT_DIR/configs/iwconfig.txt" 2>/dev/null
exec_cmd "cat /etc/config/wireless 2>/dev/null" > "$OUTPUT_DIR/configs/wireless.txt" 2>/dev/null
exec_cmd "cat /tmp/hostapd.conf 2>/dev/null" > "$OUTPUT_DIR/configs/hostapd.txt" 2>/dev/null
exec_cmd "find / -name '*.conf' -exec grep -l 'wpa\\|psk\\|key' {} \; 2>/dev/null | head -10" > "$OUTPUT_DIR/configs/wifi_configs.txt" 2>/dev/null

# 7. NAND/Flash information
echo "[*] Gathering flash information..."
exec_cmd "cat /proc/mtd" > "$OUTPUT_DIR/memory/mtd.txt" 2>/dev/null
exec_cmd "cat /proc/partitions" > "$OUTPUT_DIR/memory/partitions.txt" 2>/dev/null
exec_cmd "ls -la /dev/mtd* 2>/dev/null" > "$OUTPUT_DIR/memory/mtd_devices.txt" 2>/dev/null

# 8. Environment and running config
echo "[*] Getting environment and running config..."
exec_cmd "env | grep -iE 'key|pass|crypto|cipher'" > "$OUTPUT_DIR/configs/env_vars.txt" 2>/dev/null
exec_cmd "uci show 2>/dev/null" > "$OUTPUT_DIR/configs/uci_config.txt" 2>/dev/null

# 9. Test decryption functions
echo "[*] Testing decryption functions..."
exec_cmd "cat > /tmp/test_crypto.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

int main() {
    void *handle;
    int (*decrypt_func)(const char*, char*);
    char output[1024];
    
    // Test primary library
    handle = dlopen(\"/lib/libhw_smp_capi.so\", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, \"CAPI_SMP_DecryptCipherText\");
        if (decrypt_func) {
            int result = decrypt_func(\"test\", output);
            printf(\"CAPI_SMP_DecryptCipherText test: result=%d, output=%s\\n\", result, output);
        }
        dlclose(handle);
    }
    
    // Test fallback library  
    handle = dlopen(\"/lib/libl3_base_api.so\", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, \"WAN_IF_DecryptPPPoEPassWord\");
        if (decrypt_func) {
            int result = decrypt_func(\"test\", output);
            printf(\"WAN_IF_DecryptPPPoEPassWord test: result=%d, output=%s\\n\", result, output);
        }
        dlclose(handle);
    }
    
    return 0;
}
EOF

gcc -o /tmp/test_crypto /tmp/test_crypto.c -ldl 2>/dev/null && /tmp/test_crypto
rm -f /tmp/test_crypto.c /tmp/test_crypto" > "$OUTPUT_DIR/libraries/decryption_test.txt" 2>/dev/null

# 10. Create summary
echo "[*] Creating extraction summary..."
cat > "$OUTPUT_DIR/extraction_summary.txt" << EOF
=== Huawei HG8245 Router Crypto Extraction Summary ===
Date: $(date)
Router IP: $ROUTER_IP
Connection Method: $([ "$USE_SSH" = true ] && echo "SSH" || echo "Telnet")

=== Files Extracted ===

System Information:
- uname.txt: System information
- ps.txt: Running processes
- mount.txt: Mounted filesystems
- df.txt: Disk usage
- free.txt: Memory usage
- netstat.txt: Network connections

Crypto Processes:
- crypto_processes.txt: Processes with 'crypto' in name
- cipher_processes.txt: Processes with 'cipher' in name
- decrypt_processes.txt: Processes with 'decrypt' in name
- smp_processes.txt: SMP-related processes
- capi_processes.txt: CAPI-related processes
- crypto_pids.txt: PIDs of crypto processes

Configuration Files:
- passwd.txt: System password file
- shadow.txt: System shadow file
- all_confs.txt: All .conf files
- config_files.txt: All config files
- iwconfig.txt: Wireless configuration
- wireless.txt: Wireless settings
- hostapd.txt: HostAPD configuration
- wifi_configs.txt: WiFi configuration files
- env_vars.txt: Environment variables with crypto keywords
- uci_config.txt: UCI configuration

Libraries:
- crypto_libs.txt: List of crypto-related libraries
- smp_capi_strings.txt: Strings from libhw_smp_capi.so
- l3_base_strings.txt: Strings from libl3_base_api.so
- decryption_test.txt: Live decryption test results

Memory Analysis:
- mtd.txt: MTD partition information
- partitions.txt: Partition information
- mtd_devices.txt: MTD device list
- maps_*.txt: Memory maps for crypto processes
- base64_keys_*.txt: Base64-encoded keys found in memory
- hex_keys_*.txt: Hex-encoded keys found in memory

=== Analysis Results ===

Total config files: $(find "$OUTPUT_DIR/configs" -name "*.txt" | wc -l)
Total process files: $(find "$OUTPUT_DIR/processes" -name "*.txt" | wc -l)
Total memory files: $(find "$OUTPUT_DIR/memory" -name "*.txt" | wc -l)
Total library files: $(find "$OUTPUT_DIR/libraries" -name "*.txt" | wc -l)

=== Next Steps ===

1. Review the extracted files for encryption keys and algorithms
2. Analyze memory dumps for plaintext passwords
3. Test the decryption functions with extracted encrypted strings
4. Cross-reference configuration files with cryptographic implementations

EOF

echo
echo "[+] Extraction completed successfully!"
echo "[*] Results saved to: $OUTPUT_DIR"
echo "[*] Summary: $OUTPUT_DIR/extraction_summary.txt"
echo
echo "=== Quick Findings ==="
echo "Crypto libraries found: $(wc -l < "$OUTPUT_DIR/libraries/crypto_libs.txt")"
echo "Crypto processes found: $(wc -l < "$OUTPUT_DIR/processes/crypto_pids.txt")"
echo "Config files extracted: $(find "$OUTPUT_DIR/configs" -name "*.txt" | wc -l)"

# Show some interesting findings
echo
echo "=== Interesting Findings ==="
if [ -s "$OUTPUT_DIR/libraries/smp_capi_strings.txt" ]; then
    echo "Found strings in libhw_smp_capi.so:"
    head -5 "$OUTPUT_DIR/libraries/smp_capi_strings.txt" | sed 's/^/  /'
fi

if [ -s "$OUTPUT_DIR/processes/crypto_pids.txt" ]; then
    echo "Found crypto processes:"
    head -3 "$OUTPUT_DIR/processes/crypto_pids.txt" | sed 's/^/  /'
fi

echo
echo "Extraction complete. Review files in $OUTPUT_DIR for detailed analysis."
