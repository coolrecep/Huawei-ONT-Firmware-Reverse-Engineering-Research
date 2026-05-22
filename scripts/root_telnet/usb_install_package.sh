#!/bin/bash

# USB Installation Package Creator
# Creates complete USB installation package for busybox

echo "=== Creating USB Installation Package ==="

# Create installation directory
INSTALL_DIR="/tmp/busybox_usb_package"
mkdir -p "$INSTALL_DIR"

# Download busybox binary
echo "[*] Downloading busybox for MIPS architecture..."

# Try multiple sources for busybox
BUSYBOX_SOURCES=(
    "https://busybox.net/downloads/binaries/1.35.0/busybox-mipsel"
    "https://busybox.net/downloads/binaries/1.31.1-defconfig-multiarch-mipsel/busybox"
    "https://github.com/mirror/busybox/releases/download/1_35_0/busybox-mipsel"
)

BUSYBOX_DOWNLOADED=false

for source in "${BUSYBOX_SOURCES[@]}"; do
    echo "  Trying: $source"
    if curl -L "$source" -o "$INSTALL_DIR/busybox" 2>/dev/null; then
        if [ -s "$INSTALL_DIR/busybox" ]; then
            echo "  [+] Successfully downloaded busybox"
            chmod +x "$INSTALL_DIR/busybox"
            BUSYBOX_DOWNLOADED=true
            break
        fi
    fi
    echo "  [-] Failed to download from this source"
done

if [ "$BUSYBOX_DOWNLOADED" = false ]; then
    echo "[-] Failed to download busybox from all sources"
    echo "[*] Creating minimal busybox installation script instead"
    echo "#!/bin/sh" > "$INSTALL_DIR/busybox"
    echo "echo 'Busybox download failed. Please download manually.'" >> "$INSTALL_DIR/busybox"
    chmod +x "$INSTALL_DIR/busybox"
fi

# Create installation script
cat > "$INSTALL_DIR/install_busybox.sh" << 'EOF'
#!/bin/sh
echo "=== Busybox USB Installation ==="

# Find USB device
USB_DEVICE=""
for dev in /dev/sda1 /dev/sdb1 /dev/usb1 /dev/sda /dev/sdb; do
    if [ -b "$dev" ]; then
        USB_DEVICE="$dev"
        echo "Found USB device: $dev"
        break
    fi
done

if [ -z "$USB_DEVICE" ]; then
    echo "No USB device found"
    exit 1
fi

# Mount USB
USB_MOUNT="/mnt/usb"
mkdir -p "$USB_MOUNT"

if ! mount "$USB_DEVICE" "$USB_MOUNT" 2>/dev/null; then
    echo "Failed to mount USB device"
    exit 1
fi

echo "USB mounted at $USB_MOUNT"

# Install busybox
INSTALL_DIR="/tmp/busybox"
mkdir -p "$INSTALL_DIR"

if [ -f "$USB_MOUNT/busybox" ]; then
    echo "Installing busybox..."
    cp "$USB_MOUNT/busybox" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/busybox"
    
    # Test busybox
    if "$INSTALL_DIR/busybox" --help >/dev/null 2>&1; then
        echo "Busybox installation successful!"
        
        # Create symbolic links
        "$INSTALL_DIR/busybox" --install -s "$INSTALL_DIR/"
        
        # Add to PATH
        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> /etc/profile
        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> /root/.profile
        export PATH="$PATH:$INSTALL_DIR"
        
        echo "Busybox installed to: $INSTALL_DIR"
        echo "Test: $("$INSTALL_DIR/busybox" uname -a)"
        
    else
        echo "Busybox binary is not working for this architecture"
        echo "Please download the correct architecture binary"
    fi
else
    echo "Busybox not found on USB device"
fi

# Cleanup
umount "$USB_MOUNT" 2>/dev/null
echo "Installation complete"
EOF

chmod +x "$INSTALL_DIR/install_busybox.sh"

# Create enhanced memory extraction script
cat > "$INSTALL_DIR/enhanced_memory_extractor.sh" << 'EOF'
#!/bin/sh
echo "=== Enhanced Memory Extraction with Busybox ==="

# Add busybox to PATH
export PATH="$PATH:/tmp/busybox"

# Check busybox
if ! command -v busybox >/dev/null 2>&1; then
    echo "Busybox not found. Please install first."
    exit 1
fi

echo "Using busybox: $(which busybox)"
echo "Busybox version: $(busybox | head -1)"

# Create output directory
OUTPUT_DIR="/tmp/memory_extraction"
mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

echo "Starting enhanced memory extraction..."

# Enhanced process analysis
echo "=== Process Analysis ==="
busybox ps aux > all_processes.txt
busybox ps aux | busybox grep -E 'smp|crypto|cipher|decrypt|encrypt|capi' > crypto_processes.txt

# Memory dump for all processes
echo "=== Memory Dump ==="
for pid in $(busybox ls /proc | busybox grep -E '^[0-9]+$'); do
    if [ -d "/proc/$pid" ]; then
        cmdline=$(busybox cat /proc/$pid/cmdline 2>/dev/null | busybox tr '\0' ' ')
        if [ -n "$cmdline" ]; then
            echo "Dumping PID $pid: $cmdline"
            
            # Get process info
            echo "PID: $pid" > "info_$pid.txt"
            echo "Cmdline: $cmdline" >> "info_$pid.txt"
            
            # Memory dump with busybox dd
            if [ -r "/proc/$pid/mem" ]; then
                echo "Memory readable, dumping..."
                for offset in 0x1000 0x10000 0x100000 0x1000000; do
                    echo "Offset $offset:" >> "memory_$pid.txt"
                    busybox dd if="/proc/$pid/mem" bs=1 skip=$((offset)) count=1048576 2>/dev/null | \
                        busybox strings -n 16 | busybox head -30 >> "memory_$pid.txt"
                    echo "---" >> "memory_$pid.txt"
                done
                
                # Extract keys from this memory dump
                busybox grep -E '[0-9a-fA-F]{32,}|[A-Za-z0-9+/]{32,}=' "memory_$pid.txt" | \
                    busybox head -5 >> "keys_$pid.txt"
            else
                echo "Memory not readable" >> "info_$pid.txt"
            fi
        fi
    fi
done

# Crypto operations
echo "=== Crypto Operations ==="
cat > /tmp/crypto_test.c << 'EOFC'
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
    
    printf("=== Crypto Test ===\n");
    
    const char* inputs[] = {"admin", "superonline", "password", "test123", "huawei", "default", "root"};
    
    // Test primary function
    handle = dlopen("/lib/libhw_smp_capi.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "CAPI_SMP_DecryptCipherText");
        if (decrypt_func) {
            printf("Testing CAPI_SMP_DecryptCipherText...\n");
            for (int i = 0; i < 7; i++) {
                memset(output, 0, sizeof(output));
                int result = decrypt_func(inputs[i], output);
                printf("Input: %-15s -> Output: '%s'\n", inputs[i], output);
            }
        }
        dlclose(handle);
    }
    
    // Test fallback function
    handle = dlopen("/lib/libl3_base_api.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "WAN_IF_DecryptPPPoEPassWord");
        if (decrypt_func) {
            printf("\nTesting WAN_IF_DecryptPPPoEPassWord...\n");
            for (int i = 0; i < 5; i++) {
                memset(output, 0, sizeof(output));
                int result = decrypt_func(inputs[i], output);
                printf("Input: %-15s -> Output: '%s'\n", inputs[i], output);
            }
        }
        dlclose(handle);
    }
    
    return 0;
}
EOFC

# Compile and run crypto test
if command -v gcc >/dev/null 2>&1; then
    gcc -o /tmp/crypto_test /tmp/crypto_test.c -ldl 2>/dev/null
    if [ -f /tmp/crypto_test ]; then
        echo "Running crypto test..."
        /tmp/crypto_test &
        CRYPTO_PID=$!
        sleep 3
        
        if [ -r "/proc/$CRYPTO_PID/mem" ]; then
            echo "Dumping crypto process memory..."
            busybox dd if="/proc/$CRYPTO_PID/mem" bs=4096 count=200 2>/dev/null | \
                busybox strings -n 32 > crypto_memory.txt
            
            echo "Crypto keys found:"
            busybox grep -E '[0-9a-fA-F]{32,}|[A-Za-z0-9+/]{32,}=' crypto_memory.txt | \
                busybox head -10
        fi
        
        kill $CRYPTO_PID 2>/dev/null
        rm -f /tmp/crypto_test /tmp/crypto_test.c
    fi
fi

# Collect all keys
echo "=== Collecting All Keys ==="
cat keys_*.txt 2>/dev/null > all_keys.txt
echo "Total keys found: $(busybox wc -l < all_keys.txt)"

echo "Extraction complete!"
echo "Results in: $OUTPUT_DIR"
busybox ls -la "$OUTPUT_DIR"

EOF

chmod +x "$INSTALL_DIR/enhanced_memory_extractor.sh"

# Create README
cat > "$INSTALL_DIR/README.txt" << 'EOF'
Busybox USB Installation Package for Huawei HG8245

=== Files ===
- busybox: Busybox binary for MIPS architecture
- install_busybox.sh: Installation script
- enhanced_memory_extractor.sh: Enhanced memory extraction script
- README.txt: This file

=== Installation Steps ===

1. Copy all files to USB drive (FAT32 format)
2. Insert USB into router
3. Connect via Telnet: telnet 192.168.1.1
4. Login as root
5. Run: sh /mnt/usb/install_busybox.sh
6. Run: sh /mnt/usb/enhanced_memory_extractor.sh

=== Expected Results ===
- Enhanced memory dumping with busybox tools
- Better string extraction and key finding
- Improved process analysis
- Additional forensic capabilities

=== Troubleshooting ===
- If busybox doesn't work: Wrong architecture, try different binary
- If USB doesn't mount: Check /dev/sda1, /dev/sdb1, /dev/usb1
- If permission denied: chmod +x busybox

=== Alternative Method ===
If USB installation fails, use the forum root method:
1. python3 huawei_root_payload_generator.py
2. Install HuaweiFirmwareTool
3. Load payload via ONT Enable Tool
4. Get permanent root access
5. Install busybox with unrestricted access

EOF

echo "[+] USB installation package created in: $INSTALL_DIR"
echo "[*] Contents:"
ls -la "$INSTALL_DIR"

echo
echo "=== Next Steps ==="
echo "1. Copy all files from $INSTALL_DIR to USB drive"
echo "2. Insert USB into router"
echo "3. Connect via Telnet and run installation script"
echo "4. Run enhanced memory extraction"
echo
echo "Files to copy to USB:"
ls -1 "$INSTALL_DIR"
