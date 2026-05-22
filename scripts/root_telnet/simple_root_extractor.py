#!/usr/bin/env python3
"""
Simple Root Telnet Memory Extractor
Direct approach for root memory extraction via Telnet
"""

import telnetlib
import time
import re
import os
from pathlib import Path

class RootMemoryExtractor:
    def __init__(self, host="192.168.1.1", port=23):
        self.host = host
        self.port = port
        self.tn = None
        self.output_dir = Path("/home/recep/Masaüstü/Firmware/root_memory_extraction")
        self.output_dir.mkdir(exist_ok=True)
        
    def connect_root(self):
        """Connect to router as root"""
        print(f"[*] Connecting to {self.host}:{self.port} as root...")
        
        try:
            self.tn = telnetlib.Telnet(self.host, self.port, timeout=15)
            
            # Wait for login prompt
            self.tn.read_until(b"login: ", timeout=10)
            self.tn.write(b"root\n")
            
            # Wait for shell prompt
            time.sleep(3)
            response = self.tn.read_very_eager().decode('ascii', errors='ignore')
            
            if "#" in response or "$" in response:
                print("[+] Root connection successful!")
                return True
            else:
                print(f"[-] Root login failed. Response: {response}")
                return False
                
        except Exception as e:
            print(f"[-] Connection failed: {e}")
            return False
    
    def execute_command(self, command, timeout=60):
        """Execute command and return output"""
        if not self.tn:
            return None
            
        try:
            self.tn.write(command.encode('ascii') + b"\n")
            time.sleep(2)
            response = self.tn.read_very_eager().decode('ascii', errors='ignore')
            return response
        except Exception as e:
            print(f"[-] Command execution failed: {e}")
            return None
    
    def dump_all_processes(self):
        """Dump memory from all processes"""
        print("[*] Dumping memory from all processes...")
        
        # Get all PIDs
        ps_result = self.execute_command("ps aux")
        if ps_result:
            with open(self.output_dir / "all_processes.txt", "w") as f:
                f.write(ps_result)
            print(f"  [+] Saved process list")
        
        # Get PIDs
        pid_cmd = "ls /proc | grep -E '^[0-9]+$'"
        pids_result = self.execute_command(pid_cmd)
        
        if pids_result:
            pids = [pid.strip() for pid in pids_result.split('\n') if pid.strip().isdigit()]
            print(f"  [+] Found {len(pids)} processes")
            
            for i, pid in enumerate(pids[:50]):  # Limit to first 50 processes
                print(f"  [*] Processing PID {pid} ({i+1}/{len(pids[:50])})")
                self.dump_process_memory(pid)
                
                if i % 10 == 0:
                    print(f"    Processed {i+1} processes...")
    
    def dump_process_memory(self, pid):
        """Dump memory from specific process"""
        try:
            # Get process info
            cmdline_result = self.execute_command(f"cat /proc/{pid}/cmdline")
            if cmdline_result:
                cmdline = cmdline_result.replace('\0', ' ').strip()
            else:
                cmdline = "unknown"
            
            # Save process info
            with open(self.output_dir / f"info_{pid}.txt", "w") as f:
                f.write(f"PID: {pid}\n")
                f.write(f"Cmdline: {cmdline}\n")
            
            # Get memory maps
            maps_result = self.execute_command(f"cat /proc/{pid}/maps")
            if maps_result:
                with open(self.output_dir / f"maps_{pid}.txt", "w") as f:
                    f.write(maps_result)
            
            # Try to dump memory
            dump_cmd = f"""
if [ -r /proc/{pid}/mem ]; then
    echo "Memory readable for PID {pid}"
    # Dump from different offsets
    for offset in 0x1000 0x10000 0x100000 0x1000000; do
        echo "Dumping from offset $offset..."
        dd if=/proc/{pid}/mem bs=1 skip=$((offset)) count=1048576 2>/dev/null | strings -n 16 | head -20
        echo "---"
    done
else
    echo "Memory not readable for PID {pid}"
fi
"""
            
            dump_result = self.execute_command(dump_cmd, timeout=120)
            if dump_result:
                with open(self.output_dir / f"memory_{pid}.txt", "w") as f:
                    f.write(f"=== PID {pid} Memory Dump ===\n")
                    f.write(f"Cmdline: {cmdline}\n")
                    f.write(f"Dump result:\n")
                    f.write(dump_result)
                    
                    # Look for keys in the dump
                    keys = self.find_keys_in_text(dump_result)
                    if keys:
                        f.write(f"\n=== POTENTIAL KEYS ===\n")
                        for key in keys:
                            f.write(f"KEY: {key}\n")
                        print(f"      [+] Found {len(keys)} potential keys in PID {pid}")
            
        except Exception as e:
            print(f"    [-] Failed to dump PID {pid}: {e}")
    
    def find_keys_in_text(self, text):
        """Find potential encryption keys in text"""
        keys = []
        
        patterns = [
            r'[A-Fa-f0-9]{32}',  # 128-bit hex key
            r'[A-Fa-f0-9]{48}',  # 192-bit hex key
            r'[A-Fa-f0-9]{64}',  # 256-bit hex key
            r'[A-Za-z0-9+/]{32}={0,2}',  # Base64 key
            r'[A-Za-z0-9+/]{44}={0,2}',  # Longer Base64 key
            r'key[=:]\s*[A-Fa-f0-9A-Za-z+/=]{16,}',  # key: value
            r'password[=:]\s*[A-Fa-f0-9A-Za-z+/=]{16,}',  # password: value
            r'secret[=:]\s*[A-Fa-f0-9A-Za-z+/=]{16,}',  # secret: value
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 16:  # Minimum key length
                    keys.append(match)
        
        return list(set(keys))  # Remove duplicates
    
    def extract_configs(self):
        """Extract configuration files"""
        print("[*] Extracting configuration files...")
        
        config_commands = [
            ("passwd", "cat /etc/passwd"),
            ("shadow", "cat /etc/shadow"),
            ("uci_config", "uci show"),
            ("env_vars", "env"),
            ("wireless", "cat /etc/config/wireless"),
            ("network", "cat /etc/config/network"),
            ("system", "cat /etc/config/system"),
        ]
        
        for name, cmd in config_commands:
            result = self.execute_command(cmd)
            if result:
                with open(self.output_dir / f"config_{name}.txt", "w") as f:
                    f.write(result)
                print(f"  [+] Got {name}")
    
    def trigger_crypto_and_dump(self):
        """Trigger crypto operations and dump memory"""
        print("[*] Triggering crypto operations...")
        
        crypto_script = '''
# Create crypto test
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
    
    printf("=== Crypto Test Started ===\\n");
    
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
                printf("Input: %-15s -> Output: '%s'\\n", inputs[i], output);
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
                printf("Input: %-15s -> Output: '%s'\\n", inputs[i], output);
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
    echo "Crypto test compiled"
    /tmp/crypto_test &
    CRYPTO_PID=$!
    echo "Crypto PID: $CRYPTO_PID"
    
    # Wait and dump memory
    sleep 3
    if [ -r /proc/$CRYPTO_PID/mem ]; then
        echo "Dumping crypto process memory..."
        dd if=/proc/$CRYPTO_PID/mem bs=4096 count=200 2>/dev/null | strings -n 32 > /tmp/crypto_mem.txt
        echo "Crypto memory dump:"
        cat /tmp/crypto_mem.txt
    fi
    
    kill $CRYPTO_PID 2>/dev/null
    rm -f /tmp/crypto_test /tmp/crypto_test.c /tmp/crypto_mem.txt
else
    echo "Failed to compile crypto test"
fi
'''
        
        result = self.execute_command(crypto_script, timeout=180)
        if result:
            with open(self.output_dir / "crypto_trigger.txt", "w") as f:
                f.write(result)
            print("  [+] Crypto trigger completed")
            
            # Look for keys in crypto output
            keys = self.find_keys_in_text(result)
            if keys:
                print(f"  [+] Found {len(keys)} keys in crypto output")
                with open(self.output_dir / "crypto_keys.txt", "w") as f:
                    for key in keys:
                        f.write(f"CRYPTO_KEY: {key}\n")
    
    def create_summary(self):
        """Create extraction summary"""
        print("[*] Creating summary...")
        
        summary = f"""
=== Root Memory Extraction Summary ===
Date: {time.strftime('%Y-%m-%d %H:%M:%S')}
Router: {self.host}:{self.port}
Root Access: Yes

=== Files Created ===

Process Information:
- all_processes.txt: Complete process list
- info_*.txt: Individual process information
- maps_*.txt: Memory maps for each process

Memory Dumps:
- memory_*.txt: Memory dumps from processes
- crypto_keys.txt: Keys from crypto operations

Configuration:
- config_*.txt: Various configuration files
- crypto_trigger.txt: Crypto operation results

=== Key Search Results ===

Search all memory dumps for encryption keys:
grep -rE "[0-9a-fA-F]{{32,}}" {self.output_dir}/memory_*.txt
grep -rE "[A-Za-z0-9+/]{{32,}}=" {self.output_dir}/memory_*.txt
grep -riE "key|password|secret" {self.output_dir}/memory_*.txt

=== Analysis Commands ===

To find all potential keys:
find {self.output_dir} -name "*.txt" -exec grep -lE "[0-9a-fA-F]{{32,}}|[A-Za-z0-9+/]{{32,}}=" {{}} \\;

To analyze crypto processes:
grep -E "smp|crypto|cipher" {self.output_dir}/all_processes.txt

To check configuration passwords:
grep -riE "password|key|secret" {self.output_dir}/config_*.txt

=== Memory Statistics ===

Total processes analyzed: {len([f for f in os.listdir(self.output_dir) if f.startswith('memory_')])}
Memory dumps created: {len([f for f in os.listdir(self.output_dir) if f.startswith('memory_')])}
Configuration files: {len([f for f in os.listdir(self.output_dir) if f.startswith('config_')])}

=== Next Steps ===

1. Review memory_*.txt files for encryption keys
2. Check crypto_keys.txt for crypto operation keys
3. Analyze configuration files for encrypted passwords
4. Test extracted keys with decryption functions
5. Document complete key extraction process

"""
        
        with open(self.output_dir / "extraction_summary.txt", "w") as f:
            f.write(summary)
        
        print(f"[+] Summary saved to: {self.output_dir}/extraction_summary.txt")
    
    def run_extraction(self):
        """Run complete extraction process"""
        print("=== Root Memory Extraction ===")
        
        if not self.connect_root():
            print("[-] Failed to connect as root")
            return False
        
        try:
            self.extract_configs()
            self.dump_all_processes()
            self.trigger_crypto_and_dump()
            self.create_summary()
            
            print("\n[+] Root memory extraction completed!")
            print(f"[*] Results saved to: {self.output_dir}")
            
            # Show quick stats
            memory_files = len([f for f in os.listdir(self.output_dir) if f.startswith('memory_')])
            config_files = len([f for f in os.listdir(self.output_dir) if f.startswith('config_')])
            
            print(f"\n=== Quick Stats ===")
            print(f"Memory dumps: {memory_files}")
            print(f"Config files: {config_files}")
            
            # Check for immediate key findings
            if (self.output_dir / "crypto_keys.txt").exists():
                with open(self.output_dir / "crypto_keys.txt", "r") as f:
                    keys = f.readlines()
                    print(f"Crypto keys found: {len(keys)}")
            
            return True
            
        finally:
            if self.tn:
                self.tn.close()

def main():
    extractor = RootMemoryExtractor()
    
    # Try standard port first
    if not extractor.run_extraction():
        print("[-] Standard port failed, trying port 2323...")
        extractor.port = 2323
        extractor.run_extraction()

if __name__ == "__main__":
    main()
