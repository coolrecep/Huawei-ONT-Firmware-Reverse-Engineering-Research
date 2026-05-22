# Complete Busybox USB Installation Guide for Huawei HG8245

## 🔍 Step 1: Determine Router Architecture

First, we need to know what CPU architecture your router uses. Based on Huawei HG8245 specifications, it's likely **MIPS** architecture.

### Quick Architecture Check
The router rejected the connection, but Huawei HG8245 typically uses **MIPS** (big-endian) or **MIPS Little-Endian** architecture.

## 📦 Step 2: Download Busybox Binary

### Option A: Download Pre-compiled MIPS Busybox
```bash
# Download MIPS big-endian busybox
wget https://busybox.net/downloads/binaries/1.31.1-defconfig-multiarch-mips/busybox

# OR MIPS little-endian (try this first)
wget https://busybox.net/downloads/binaries/1.31.1-defconfig-multiarch-mipsel/busybox-mipsel

# Alternative sources:
wget https://github.com/mirror/busybox/releases/download/1_35_0/busybox-mips
wget https://github.com/mirror/busybox/releases/download/1_35_0/busybox-mipsel
```

### Option B: Cross-compile (if pre-compiled doesn't work)
```bash
# Install cross-compilation tools
sudo apt-get install gcc-mips-linux-gnu gcc-mipsel-linux-gnu

# Download busybox source
wget https://busybox.net/downloads/busybox-1.35.0.tar.bz2
tar -xjf busybox-1.35.0.tar.bz2
cd busybox-1.35.0

# Configure for MIPS
make defconfig
make menuconfig  # Select MIPS architecture

# Cross-compile
make ARCH=mips CROSS_COMPILE=mips-linux-gnu-
```

## 🖥️ Step 3: Prepare USB Drive

### Format USB Drive
```bash
# Format USB drive as FAT32 (router compatibility)
sudo mkfs.vfat -F 32 /dev/sdX1  # Replace X with your USB device
```

### Create Installation Package
```bash
# Create installation directory
mkdir -p /tmp/busybox_install
cd /tmp/busybox_install

# Copy busybox binary
cp /path/to/busybox-mipsel ./busybox
chmod +x ./busybox

# Create installation script
cat > install_busybox.sh << 'EOF'
#!/bin/sh
echo "=== Busybox Installation Script ==="

# Mount point (adjust if needed)
USB_MOUNT="/mnt/usb"
INSTALL_DIR="/tmp/busybox"

echo "Creating installation directory..."
mkdir -p $INSTALL_DIR

echo "Copying busybox..."
cp /mnt/usb/busybox $INSTALL_DIR/
chmod +x $INSTALL_DIR/busybox

echo "Creating symbolic links..."
$INSTALL_DIR/busybox --install $INSTALL_DIR/

echo "Adding to PATH..."
export PATH="$PATH:$INSTALL_DIR"

echo "Testing busybox..."
$INSTALL_DIR/busybox uname -a
$INSTALL_DIR/busybox ps aux | head -5

echo "Installation complete!"
echo "Busybox installed to: $INSTALL_DIR"
echo "Add to PATH: export PATH=\"\$PATH:$INSTALL_DIR\""
EOF

chmod +x install_busybox.sh
```

## 🔌 Step 4: Install on Router

### Physical USB Installation
1. **Copy files to USB drive**:
   ```bash
   # Copy to USB drive
   sudo cp busybox install_busybox.sh /media/YOUR_USB_DRIVE/
   ```

2. **Insert USB into router**:
   - Plug USB drive into router's USB port
   - Wait 30 seconds for router to detect USB

3. **Connect via Telnet**:
   ```bash
   telnet 192.168.1.1
   # Login as root
   ```

4. **Install busybox on router**:
   ```sh
   # Mount USB drive (common mount points)
   mount /dev/sda1 /mnt
   # OR
   mount /dev/usb1 /mnt
   # OR
   mount -t vfat /dev/sda1 /mnt

   # Run installation script
   cd /mnt
   sh install_busybox.sh

   # Add to PATH permanently
   echo 'export PATH="$PATH:/tmp/busybox"' >> /etc/profile
   echo 'export PATH="$PATH:/tmp/busybox"' >> /root/.profile
   ```

## 🛠️ Step 5: Enhanced Memory Extraction with Busybox

### Create Advanced Extraction Script
```bash
# Create enhanced extraction script using busybox tools
cat > enhanced_memory_extractor.sh << 'EOF'
#!/bin/sh
echo "=== Enhanced Memory Extraction with Busybox ==="

# Add busybox to PATH
export PATH="$PATH:/tmp/busybox"

# Check busybox installation
if ! command -v busybox >/dev/null 2>&1; then
    echo "Busybox not found in PATH"
    exit 1
fi

echo "Busybox version: $(busybox | head -1)"

# Create output directory
mkdir -p /tmp/memory_extraction
cd /tmp/memory_extraction

# Enhanced process listing
echo "=== Enhanced Process Analysis ==="
busybox ps aux > all_processes_enhanced.txt
busybox ps -o pid,ppid,cmd > process_tree.txt

# Find crypto processes with enhanced patterns
echo "=== Finding Crypto Processes ==="
busybox ps aux | busybox grep -E 'smp|crypto|cipher|decrypt|encrypt|capi|hw_' > crypto_processes.txt

# Get all PIDs
for pid in $(busybox ls /proc | busybox grep -E '^[0-9]+$'); do
    if [ -d "/proc/$pid" ]; then
        echo "Processing PID: $pid"
        
        # Get enhanced process info
        cmdline=$(busybox cat /proc/$pid/cmdline | busybox tr '\0' ' ')
        echo "PID $pid: $cmdline" >> process_details.txt
        
        # Enhanced memory maps
        if [ -f "/proc/$pid/maps" ]; then
            busybox cat "/proc/$pid/maps" > "maps_$pid.txt"
        fi
        
        # Enhanced memory dump with busybox dd
        if [ -r "/proc/$pid/mem" ]; then
            echo "Dumping memory for PID $pid"
            
            # Use busybox dd for better memory dumping
            for offset in 0x1000 0x10000 0x100000 0x1000000 0x10000000; do
                echo "Dumping from offset $offset..." >> "memory_$pid.txt"
                busybox dd if="/proc/$pid/mem" bs=1 skip=$((offset)) count=2097152 2>/dev/null | \
                    busybox strings -n 16 | busybox head -50 >> "memory_$pid.txt"
                echo "---" >> "memory_$pid.txt"
            done
            
            # Look for keys in memory dump
            busybox grep -E '[0-9a-fA-F]{32,}|[A-Za-z0-9+/]{32,}=' "memory_$pid.txt" | \
                busybox head -10 >> "keys_$pid.txt"
        fi
    fi
done

# Enhanced crypto operations
echo "=== Enhanced Crypto Operations ==="
cat > /tmp/crypto_test_enhanced.c << 'EOFC'
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
    
    printf("=== Enhanced Crypto Test ===\n");
    
    // Test with more inputs
    const char* test_inputs[] = {
        "admin", "superonline", "password", "test123", "huawei",
        "default", "root", "telecomadmin", "123456", "config",
        "keytest", "secret123", "encr2023", "hgw8245", "router"
    };
    
    // Test primary function
    handle = dlopen("/lib/libhw_smp_capi.so", RTLD_LAZY);
    if (handle) {
        decrypt_func = dlsym(handle, "CAPI_SMP_DecryptCipherText");
        if (decrypt_func) {
            printf("Testing CAPI_SMP_DecryptCipherText...\n");
            for (int i = 0; i < 15; i++) {
                memset(output, 0, sizeof(output));
                int result = decrypt_func(test_inputs[i], output);
                printf("Input: %-15s -> Result: %d, Output: '%s'\n", 
                       test_inputs[i], result, output);
                
                // Print memory addresses
                printf("Input addr: %p, Output addr: %p\n", 
                       (void*)test_inputs[i], (void*)output);
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
            for (int i = 0; i < 10; i++) {
                memset(output, 0, sizeof(output));
                int result = decrypt_func(test_inputs[i], output);
                printf("Input: %-15s -> Result: %d, Output: '%s'\n", 
                       test_inputs[i], result, output);
            }
        }
        dlclose(handle);
    }
    
    return 0;
}
EOFC

# Compile and run enhanced crypto test
if command -v gcc >/dev/null 2>&1; then
    gcc -o /tmp/crypto_test_enhanced /tmp/crypto_test_enhanced.c -ldl 2>/dev/null
    if [ -f /tmp/crypto_test_enhanced ]; then
        echo "Enhanced crypto test compiled"
        /tmp/crypto_test_enhanced &
        CRYPTO_PID=$!
        echo "Enhanced crypto PID: $CRYPTO_PID"
        
        # Enhanced memory dump with busybox
        sleep 3
        if [ -r "/proc/$CRYPTO_PID/mem" ]; then
            echo "Enhanced memory dump with busybox..."
            busybox dd if="/proc/$CRYPTO_PID/mem" bs=8192 count=500 2>/dev/null | \
                busybox strings -n 32 > enhanced_crypto_memory.txt
            
            echo "Enhanced crypto keys:"
            busybox grep -E '[0-9a-fA-F]{32,}|[A-Za-z0-9+/]{32,}=' enhanced_crypto_memory.txt | \
                busybox head -20
        fi
        
        kill $CRYPTO_PID 2>/dev/null
        rm -f /tmp/crypto_test_enhanced /tmp/crypto_test_enhanced.c
    else
        echo "Failed to compile enhanced crypto test"
    fi
else
    echo "GCC not available"
fi

# Enhanced key search
echo "=== Enhanced Key Search ==="
echo "Searching all memory dumps for encryption keys..."

for file in memory_*.txt; do
    if [ -f "$file" ]; then
        echo "Searching in $file..."
        busybox grep -E '[0-9a-fA-F]{32,}|[A-Za-z0-9+/]{32,}=' "$file" | \
            busybox head -5 >> all_keys_found.txt
    fi
done

# Enhanced configuration extraction
echo "=== Enhanced Configuration Extraction ==="
busybox find /etc -name '*.conf' -exec busybox cat {} \; > all_configs.txt 2>/dev/null
busybox find /tmp -name '*.conf' -exec busybox cat {} \; >> all_configs.txt 2>/dev/null

echo "Enhanced extraction complete!"
echo "Results in: /tmp/memory_extraction"
busybox ls -la /tmp/memory_extraction/

EOF

chmod +x enhanced_memory_extractor.sh
```

## 🚀 Step 6: Run Enhanced Extraction

### Execute on Router
```sh
# After installing busybox
cd /mnt
sh enhanced_memory_extractor.sh

# Check results
ls -la /tmp/memory_extraction/
cat /tmp/memory_extraction/all_keys_found.txt
```

## 📋 Step 7: Download Results

### Transfer Results Back
```bash
# On your computer, create download directory
mkdir -p /home/recep/Masaüstü/Firmware/busybox_extraction

# Download results via Telnet (one by one)
telnet 192.168.1.1
# Login as root
# Then for each file:
cat /tmp/memory_extraction/all_keys_found.txt > /tmp/download.txt
exit

# On your computer:
nc -l 12345 > all_keys_found.txt

# On router again:
cat /tmp/memory_extraction/all_keys_found.txt > /dev/tcp/YOUR_COMPUTER_IP/12345
```

## 🔧 Alternative: Use ONT Enable Tool

If USB installation fails, use the forum method:

1. **Generate root payload**:
   ```bash
   python3 huawei_root_payload_generator.py
   ```

2. **Install HuaweiFirmwareTool**:
   ```bash
   git clone https://github.com/0xuserpag3/HuaweiFirmwareTool
   cd HuaweiFirmwareTool
   # Follow compilation instructions
   ```

3. **Load payload** via ONT Enable Tool
4. **Get permanent root access** on ports 23/2323
5. **Install busybox** with unrestricted access

## 🎯 Expected Results

With busybox installed, you'll get:
- **Enhanced memory dumping** with better dd implementation
- **Improved string extraction** with busybox strings
- **More reliable process analysis**
- **Better file operations** for configuration extraction
- **Additional tools** for forensic analysis

## 📝 Troubleshooting

### Common Issues:
1. **Wrong architecture**: Try both mips and mipsel binaries
2. **USB not mounting**: Check `/dev/sda1`, `/dev/usb1`, `/dev/sdb1`
3. **Permission denied**: Ensure USB is formatted as FAT32
4. **Busybox not executable**: `chmod +x busybox`
5. **Path issues**: Use full path `/tmp/busybox/busybox`

### Verification Commands:
```sh
# Test busybox installation
/tmp/busybox/busybox --help
/tmp/busybox/busybox uname -a
/tmp/busybox/busybox ps aux | head -3
```

This comprehensive guide should help you install busybox and perform enhanced memory extraction for key recovery.
